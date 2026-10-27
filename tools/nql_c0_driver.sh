#!/usr/bin/env bash
# Private, sourced by nqlc after common validation. All options come from nqlc.

canonical_fail() { printf 'error: canonical backend: %s\n' "$1" >&2; exit 1; }
canonical_unsupported() { canonical_fail "option '$1' is not supported"; }

canonical_signal() {
    [[ $canonical_signal_status -ne 0 ]] || canonical_signal_status="$1"
    [[ $canonical_registering -eq 1 ]] || exit "$canonical_signal_status"
}

canonical_cleanup() {
    local status=$?
    trap - EXIT
    trap '' HUP INT TERM PIPE
    if [[ -n "$canonical_active" ]]; then
        if [[ "$canonical_active_kind" == session ]]; then
            kill -KILL -- "-$canonical_active" 2>/dev/null || :
            # Before setsid establishes its group, this PID still shares the
            # driver's group. Kill that owned PID too; never kill our group.
            kill -KILL "$canonical_active" 2>/dev/null || :
            wait "$canonical_active" 2>/dev/null || :
        elif [[ "$canonical_active_kind" == compile ]]; then
            # Let the unchanged wrapper remove its candidate and workspace.
            # Its own children have separate groups managed by its traps.
            kill -TERM -- "-$canonical_active" 2>/dev/null || :
            wait "$canonical_active" 2>/dev/null || :
        fi
        kill -KILL -- "-$canonical_active" 2>/dev/null || :
        wait "$canonical_active" 2>/dev/null || :
    fi
    canonical_restore_monitor
    if [[ -n "$canonical_candidate" ]] && ! rm -f -- "$canonical_candidate"; then
        printf 'error: canonical backend: cannot remove candidate %s\n' "$canonical_candidate" >&2
        [[ $status -ne 0 ]] || status=1
    fi
    if [[ -n "$TMP_DIR" ]] && ! rm -rf -- "$TMP_DIR"; then
        printf 'error: canonical backend: cannot remove temporary directory %s\n' "$TMP_DIR" >&2
        [[ $status -ne 0 ]] || status=1
    fi
    exit "$status"
}

canonical_restore_monitor() {
    case "$canonical_monitor_restore" in
        on) set -m ;;
        off) set +m ;;
    esac
    canonical_monitor_restore=""
}

canonical_run_owned() {
    local status=0
    canonical_active_kind="$1"
    shift
    canonical_registering=1
    if [[ "$canonical_active_kind" == run && -t 0 ]]; then
        canonical_active_kind=session
        if [[ $- == *m* ]]; then canonical_monitor_restore=on; else canonical_monitor_restore=off; fi
        # With monitor mode off the child is not a group leader. util-linux
        # setsid therefore execs without forking: $! remains the runtime PID,
        # PGID and SID. Inherited tty descriptors work without stealing the
        # caller's controlling terminal or changing its foreground owner.
        set +m
        "$canonical_setsid" "$@" <&0 &
        canonical_active=$!
    else
        # Monitor mode gives only this owned command a new process group.
        # Explicit stdin redirection avoids asynchronous /dev/null substitution.
        "$@" <&0 &
        canonical_active=$!
    fi
    canonical_registering=0
    [[ $canonical_signal_status -eq 0 ]] || exit "$canonical_signal_status"
    wait "$canonical_active" || status=$?
    kill -KILL -- "-$canonical_active" 2>/dev/null || :
    canonical_restore_monitor
    canonical_registering=1
    canonical_active=""
    canonical_registering=0
    [[ $canonical_signal_status -eq 0 ]] || exit "$canonical_signal_status"
    return "$status"
}

canonical_finish() {
    local status="$1" end_ms
    if [[ $time_mode -eq 1 && $quiet -eq 0 ]]; then
        end_ms="$(now_ms)"
        printf 'total: %sms\n' "$((end_ms - start_ms))" >&2
    fi
    exit "$status"
}

canonical_print_command() { printf '%q ' "$@" >&2; printf '\n' >&2; }

canonical_guard_output() {
    local resolved protected protected_resolved
    [[ ! -d "$output" ]] || canonical_fail "output '$output' is a directory"
    resolved="$(readlink -m -- "$output")" || canonical_fail "cannot resolve output '$output'"
    # The wrapper compiles to an owned candidate. Guard the final destination
    # with its same component/source protections plus the active public files.
    for protected in "${inputs[0]}" "$SCRIPT" "$canonical_driver" \
        "$TOOL_DIR"/{nql,nqlc,nolqul,nolqulc} \
        "$canonical_public_dir"/{nql,nqlc,nolqul,nolqulc} \
        "$canonical_root"/{nql,nqlc,nolqul,nolqulc} \
        "$wrapper" "$canonical_root/bootstrap/manifest.tsv" \
        "$canonical_root/bootstrap/compiler/c0"/{frontend,backend}.nql \
        "$canonical_root/bootstrap/compiler/c0/x86_64-linux"/c0-{frontend,backend}.{seed,sha256}; do
        protected_resolved="$(readlink -m -- "$protected")" || canonical_fail "cannot resolve '$protected'"
        [[ ! "$output" -ef "$protected" && "$resolved" != "$protected_resolved" ]] || \
            canonical_fail "output would replace protected file '$protected'"
    done
}

run_canonical_pipeline() {
    local flag source_path wrapper compile_output diagnostic_line status=0
    local -a profile_flags=() runner=()
    [[ $emit_asm -eq 0 ]] || canonical_unsupported '-S'
    [[ $emit_obj -eq 0 ]] || canonical_unsupported '-c'
    [[ $emit_ir -eq 0 ]] || canonical_unsupported '--emit-ir'
    [[ $dump_ir -eq 0 ]] || canonical_unsupported '--dump-ir'
    [[ $dump_ast -eq 0 ]] || canonical_unsupported '--dump-ast'
    [[ $debug_info -eq 0 ]] || canonical_unsupported '-g'
    [[ "$opt_level" != -O1 ]] || canonical_unsupported '-O1'
    [[ $warn_suppress -eq 0 ]] || canonical_unsupported '-w'
    [[ $werror -eq 0 ]] || canonical_unsupported '-Werror'
    [[ $wall -eq 0 ]] || canonical_unsupported '-Wall'
    for flag in "${disabled_warnings[@]}"; do canonical_unsupported "-Wno-$flag"; done
    [[ $pedantic -eq 0 ]] || canonical_unsupported '--pedantic'
    [[ $save_temps -eq 0 ]] || canonical_unsupported '--save-temps'
    [[ "$error_format" == text ]] || canonical_unsupported '--error-format'
    [[ "$max_errors" == 20 ]] || canonical_unsupported '--max-errors'
    [[ $jobs -eq 1 ]] || canonical_unsupported '-j'
    [[ $gen_deps -eq 0 ]] || canonical_unsupported '-M'
    [[ $emit_ccdb -eq 0 ]] || canonical_unsupported '--emit-ccdb'
    [[ ${#inputs[@]} -eq 1 ]] || canonical_fail 'only one compilation unit is supported'
    source_path="${inputs[0]}"
    [[ "$source_path" == *.nql ]] || canonical_fail "input '$source_path' must be a .nql file"
    [[ -f "$source_path" && -r "$source_path" ]] || canonical_fail "cannot read source '$source_path'"
    [[ $output_seen -eq 0 || -n "$output" ]] || canonical_fail '-o requires a nonempty output file name'

    canonical_root="$(cd -- "$(dirname -- "$canonical_driver")/.." && pwd)" || \
        canonical_fail 'cannot locate canonical assets'
    wrapper="$canonical_root/bootstrap/compiler/c0/x86_64-linux/compile-source.sh"
    [[ -x "$wrapper" ]] || canonical_fail "compiler wrapper not found: '$wrapper'"
    [[ $compiler_profile -eq 0 ]] || profile_flags=(--compiler-profile)
    if [[ $run_after -eq 1 && "$(uname -m)" != x86_64 ]]; then
        command -v qemu-x86_64 >/dev/null 2>&1 || canonical_fail 'qemu-x86_64 not found for running x86_64 binaries'
        runner=(qemu-x86_64)
    fi
    canonical_setsid=""
    if [[ $run_after -eq 1 && $dry_run -eq 0 && -t 0 ]]; then
        canonical_setsid="$(type -P setsid)" || \
            canonical_fail 'setsid (util-linux) is required for canonical run with terminal stdin'
    fi
    [[ "$source_path" == /* ]] || source_path="$PWD/$source_path"
    # Implicit script execution keeps the established default output name;
    # explicit --run and --check use private, disposable executables.
    if [[ $output_seen -eq 0 && $check_only -eq 0 && $explicit_run -eq 0 ]]; then
        output="${inputs[0]##*/}"
        output="${output%.nql}"
    fi
    if [[ -n "$output" ]]; then
        [[ "$output" == /* ]] || output="$PWD/$output"
        canonical_guard_output
        [[ -d "$(dirname -- "$output")" ]] || canonical_fail "output directory does not exist: '$output'"
    fi
    if [[ $dry_run -eq 1 ]]; then
        compile_output="${output:-$TMP_ROOT/nqlc-canonical.<temporary>/program}"
        canonical_print_command "$wrapper" "${profile_flags[@]}" "$source_path" "$compile_output"
        if [[ $run_after -eq 1 ]]; then
            if [[ -t 0 ]]; then
                canonical_print_command setsid "${runner[@]}" "$compile_output" "${run_args[@]}"
            else
                canonical_print_command "${runner[@]}" "$compile_output" "${run_args[@]}"
            fi
        fi
        exit 0
    fi

    canonical_active=""
    canonical_active_kind=""
    canonical_candidate=""
    canonical_monitor_restore=""
    canonical_signal_status=0
    canonical_registering=0
    trap canonical_cleanup EXIT
    trap 'canonical_signal 129' HUP
    trap 'canonical_signal 130' INT
    trap 'canonical_signal 143' TERM
    trap 'canonical_signal 141' PIPE
    set -m
    canonical_registering=1
    TMP_DIR="$(mktemp -d -- "$TMP_ROOT/nqlc-canonical.XXXXXX")" || canonical_fail 'cannot create temporary directory'
    if [[ -n "$output" ]]; then
        canonical_candidate="$(mktemp -- "$(dirname -- "$output")/.nqlc-canonical.XXXXXX")" || \
            canonical_fail 'cannot create temporary executable'
        compile_output="$canonical_candidate"
    else
        output="$TMP_DIR/program"
        compile_output="$output"
    fi
    canonical_registering=0
    [[ $canonical_signal_status -eq 0 ]] || exit "$canonical_signal_status"
    start_ms="$(now_ms)"
    stage_begin '[1/1] canonical compilation (pinned C0 frontend/backend)'
    canonical_run_owned compile "$wrapper" "${profile_flags[@]}" "$source_path" "$compile_output" \
        2> "$TMP_DIR/diagnostics" || status=$?
    # Only compiler diagnostics are source-located here. Runtime streams stay
    # directly connected to the caller, including arbitrary binary stderr.
    while IFS= read -r diagnostic_line || [[ -n "$diagnostic_line" ]]; do
        case "$diagnostic_line" in
            input:*) printf '%s:%s\n' "${inputs[0]}" "${diagnostic_line#input:}" >&2 ;;
            *) printf '%s\n' "$diagnostic_line" >&2 ;;
        esac
    done < "$TMP_DIR/diagnostics"
    [[ $status -eq 0 ]] || canonical_finish "$status"
    stage_end
    if [[ $run_after -eq 1 ]]; then
        canonical_run_owned run "${runner[@]}" "$compile_output" "${run_args[@]}" || status=$?
    fi
    if [[ -n "$canonical_candidate" ]]; then
        # Publication is the last fallible compile operation. In particular,
        # diagnostics cleanup failure must leave an existing output intact.
        rm -rf -- "$TMP_DIR" || canonical_fail "cannot remove temporary directory $TMP_DIR"
        TMP_DIR=""
        canonical_guard_output
        canonical_run_owned publish mv -fT -- "$canonical_candidate" "$output" || \
            canonical_fail "cannot publish '$output'"
        canonical_candidate=""
    fi
    canonical_finish "$status"
}
