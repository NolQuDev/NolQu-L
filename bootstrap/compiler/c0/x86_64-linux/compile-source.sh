#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
fail() { printf 'c0-source: error: %s\n' "$1" >&2; exit 1; }
profile=0
if [[ "${1:-}" == --compiler-profile ]]; then
    profile=1
    shift
fi
[[ $# == 2 && "$1" != --* && "$2" != --* ]] || \
    fail 'usage: compile-source.sh [--compiler-profile] <input.nql> <output>'
input="$1"
output="$2"
[[ "$input" == *.nql ]] || fail "input '$input' is not a NolQu-L .nql file"
[[ -f "$input" && -r "$input" ]] || fail "cannot read source '$input'"
output_dir="$(dirname -- "$output")"
[[ -d "$output_dir" ]] || fail "output directory '$output_dir' does not exist"
protected_paths=("$input" "$0" "$SCRIPT_DIR/compile-source.sh" "$ROOT_DIR/bootstrap/manifest.tsv"
                 "$SCRIPT_DIR"/c0-{frontend,backend}.{seed,sha256}
                 "$SCRIPT_DIR"/../{frontend,backend}.nql)
check_output() {
    local protected resolved protected_resolved
    [[ ! -d "$output" ]] || fail "output '$output' is a directory"
    resolved="$(readlink -m -- "$output")" || fail "cannot resolve '$output'"
    for protected in "${protected_paths[@]}"; do
        protected_resolved="$(readlink -m -- "$protected")" || fail "cannot resolve '$protected'"
        [[ ! "$output" -ef "$protected" && "$resolved" != "$protected_resolved" ]] || \
            fail "output would replace '$protected'"
    done
}
check_output

for component in frontend backend; do
    seed="$SCRIPT_DIR/c0-$component.seed"
    manifest="$SCRIPT_DIR/c0-$component.sha256"
    [[ -x "$seed" && -f "$manifest" ]] || fail "missing $component seed or manifest"
    read -r expected name < "$manifest" || fail "cannot read '$manifest'"
    [[ "$expected" =~ ^[0-9a-f]{64}$ && "$name" == "c0-$component.seed" ]] || fail "invalid manifest '$manifest'"
    actual="$(sha256sum -- "$seed")" || fail "cannot hash '$seed'"
    [[ "${actual%% *}" == "$expected" ]] || fail "$component seed hash mismatch"
done
runner=()
if [[ "$(uname -m)" != x86_64 ]]; then
    command -v qemu-x86_64 >/dev/null 2>&1 || fail 'install qemu-x86_64 on this host'
    runner=(qemu-x86_64)
fi

work=""
temp=""
active=""
registering=0
signal_status=0
# Each asynchronous command owns its process group, including runner children.
set -m
on_signal() {
    [[ "$signal_status" != 0 ]] || signal_status="$1"
    [[ "$registering" == 1 ]] || exit "$signal_status"
}
cleanup() {
    local status=$? failed=0
    trap - EXIT
    trap '' HUP INT TERM
    set +e
    if [[ -n "$active" ]]; then
        kill -KILL -- "-$active" 2>/dev/null
        wait "$active" 2>/dev/null
    fi
    if [[ -n "$temp" ]] && ! rm -f -- "$temp"; then
        printf "c0-source: error: cannot remove candidate '%s'\n" "$temp" >&2
        failed=1
    fi
    if [[ -n "$work" && -d "$work" ]]; then
        if ! rm -f -- "$work/module.nqaf" "$work/source.nqsc"; then
            printf "c0-source: error: cannot remove '%s/module.nqaf' or '%s/source.nqsc'\n" "$work" "$work" >&2
            failed=1
        fi
        if ! rmdir -- "$work"; then
            printf "c0-source: error: cannot remove workspace '%s'\n" "$work" >&2
            failed=1
        fi
    fi
    [[ "$status" != 0 || "$failed" == 0 ]] || status=1
    exit "$status"
}
run_owned() {
    local status=0
    registering=1
    "$@" <&0 &
    active=$!
    registering=0
    [[ "$signal_status" == 0 ]] || exit "$signal_status"
    wait "$active" || status=$?
    # A failed runner may leave descendants after its direct child has exited.
    kill -KILL -- "-$active" 2>/dev/null || :
    registering=1
    active=""
    registering=0
    [[ "$signal_status" == 0 ]] || exit "$signal_status"
    return "$status"
}
trap cleanup EXIT
trap 'on_signal 129' HUP
trap 'on_signal 130' INT
trap 'on_signal 143' TERM
# Defer signals until newly allocated paths have been registered for cleanup.
registering=1
work="$(mktemp -d -- "${TMPDIR:-/tmp}/c0-source.XXXXXX")" || fail 'cannot create temporary workspace'
temp="$(mktemp -- "$output_dir/.c0-source.XXXXXX")" || fail 'cannot create temporary executable'
registering=0
[[ "$signal_status" == 0 ]] || exit "$signal_status"
source_path="$input"
if [[ "$profile" == 1 ]]; then
    printf 'NQSC\001\001\000\000\000\000\000\000\000\000\000\000' > "$work/source.nqsc" || exit $?
    run_owned cat -- "$input" >> "$work/source.nqsc" || exit $?
    source_path="$work/source.nqsc"
fi
run_owned "${runner[@]}" "$SCRIPT_DIR/c0-frontend.seed" < "$source_path" > "$work/module.nqaf" || exit $?
run_owned "${runner[@]}" "$SCRIPT_DIR/c0-backend.seed" < "$work/module.nqaf" > "$temp" || exit $?
run_owned chmod 0755 "$temp" || fail 'cannot mark output executable'
run_owned rm -f -- "$work/module.nqaf" "$work/source.nqsc" || fail "cannot remove intermediates in '$work'"
run_owned rmdir -- "$work" || fail "cannot remove workspace '$work'"
work=""
check_output
run_owned mv -fT -- "$temp" "$output" || fail "cannot publish '$output'"
temp=""
