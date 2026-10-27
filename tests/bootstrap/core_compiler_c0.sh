#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/tests/shared/lib.sh"

C0_DIR="$ROOT_DIR/bootstrap/compiler/c0"
C0_TARGET_DIR="$C0_DIR/x86_64-linux"
B0_SEED="$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/b0.seed"
MANIFEST="$ROOT_DIR/bootstrap/manifest.tsv"
SOURCE="$C0_DIR/compiler.nq"
SEED="$C0_TARGET_DIR/c0.seed"
HASH="$C0_TARGET_DIR/c0.sha256"
MATERIALIZER="$C0_TARGET_DIR/materialize.sh"
COMPILER_ADAPTER="$C0_TARGET_DIR/compile.sh"
SUCCESSOR_SOURCE="$C0_DIR/successor.nq"
SUCCESSOR_SEED="$C0_TARGET_DIR/c0-successor.seed"
SUCCESSOR_HASH="$C0_TARGET_DIR/c0-successor.sha256"
SUCCESSOR_MATERIALIZER="$C0_TARGET_DIR/materialize-successor.sh"
RETURN7_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return7.nq"
RETURN2_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return2.nq"
RETURN23_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return23_spaced.nq"
RETURN255_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return255.nq"
INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/invalid.nq"
RETURN256_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return256.nq"
SPLIT_KEYWORD_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/split_keyword.nq"
SPLIT_DIGITS_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/split_digits.nq"
SPLIT_MAIN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/split_main.nq"
SPLIT_RETURN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/split_return.nq"
MISSING_FN_SEPARATOR_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/missing_fn_separator.nq"
MISSING_RETURN_SEPARATOR_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/missing_return_separator.nq"
RETURN_PRECEDENCE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return_precedence.nq"
RETURN_LEFT_ASSOC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/return_left_assoc.nq"
DIV_ZERO_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/div_zero.nq"
TRAILING_TOKEN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/trailing_token.nq"
MUL_OVERFLOW_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/mul_overflow.nq"
LOCAL_BASIC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/local_basic.nq"
LOCAL_EXPRESSION_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/local_expression.nq"
LOCAL_CHAIN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/local_chain.nq"
DUPLICATE_LOCAL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/duplicate_local.nq"
UNKNOWN_LOCAL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/unknown_local.nq"
MALFORMED_LET_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/malformed_let.nq"
LOCAL_LIMIT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/local_limit.nq"
WRITE_TEXT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/write_text.nq"
WRITE_BINARY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/write_binary.nq"
WRITE_ZERO_ESCAPE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/write_zero_escape.nq"
WRITE_CONCAT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/write_concat.nq"
INVALID_STRING_ESCAPE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/invalid_string_escape.nq"
UNTERMINATED_STRING_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/unterminated_string.nq"
WRITE_PAYLOAD_LIMIT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/write_payload_limit.nq"
RUNTIME_INPUT_BYTE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_input_byte.nq"
RUNTIME_BYTE_STORE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_store.nq"
RUNTIME_INPUT_RANGE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_input_range.nq"
RUNTIME_WRITE_MIX_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_write_mix.nq"
RUNTIME_LOAD_ARITHMETIC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_load_arithmetic.nq"
RUNTIME_STORE_COPY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_store_copy.nq"
RUNTIME_STORE_WRAP_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_store_wrap.nq"
RUNTIME_BYTE_LOAD_AT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_load_at.nq"
RUNTIME_BYTE_LOAD_AT_SCAN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_load_at_scan.nq"
RUNTIME_BYTE_LOAD_AT_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_load_at_invalid.nq"
RUNTIME_BYTE_STORE_AT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_store_at.nq"
RUNTIME_BYTE_STORE_AT_COPY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_store_at_copy.nq"
RUNTIME_BYTE_STORE_AT_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_store_at_invalid.nq"
RUNTIME_WHILE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_while_decrement.nq"
RUNTIME_WHILE_ZERO_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_while_zero.nq"
RUNTIME_WHILE_SEQUENTIAL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_while_sequential.nq"
RUNTIME_NESTED_WHILE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_nested_while.nq"
RUNTIME_WHILE_LET_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_while_let.nq"
RUNTIME_OUTPUT_ROUNDTRIP_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_roundtrip.nq"
RUNTIME_OUTPUT_MEMORY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_memory.nq"
RUNTIME_OUTPUT_ZERO_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_zero.nq"
RUNTIME_OUTPUT_WHILE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_while.nq"
RUNTIME_LITERAL_ORDER_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_literal_order.nq"
RUNTIME_OUTPUT_RANGE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_range.nq"
RUNTIME_OUTPUT_MALFORMED_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_malformed.nq"
RUNTIME_OPERATION_CAPACITY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_operation_capacity.nq"
RUNTIME_OUTPUT_CAPACITY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_output_capacity.nq"
RUNTIME_ASSERT_RANGE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_assert_range.nq"
RUNTIME_ASSERT_RANGE_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_assert_range_invalid.nq"
RUNTIME_PARSE_U8_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_u8.nq"
RUNTIME_PARSE_U8_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_u8_invalid.nq"
RUNTIME_PARSE_U8_THEN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_u8_then.nq"
RUNTIME_PARSE_U8_THEN_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_u8_then_invalid.nq"
RUNTIME_PARSE_STMTS_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts.nq"
RUNTIME_PARSE_STMTS_INPUT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_input.nq"
RUNTIME_PARSE_STMTS_PARSER_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_parser.nq"
RUNTIME_PARSE_STMTS_BOUNDARY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_boundary.nq"
RUNTIME_PARSE_STMTS_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_invalid.nq"
RUNTIME_PARSE_STMTS_DESTINATION_INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_destination_invalid.nq"
RUNTIME_PARSE_STMTS_RETURN_EMITTER_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_return_emitter.nq"
RUNTIME_PARSE_STMTS_PARSER_EMITTER_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_parser_emitter.nq"
RUNTIME_PARSE_STMTS_INPUT_EMITTER_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_parse_stmts_input_emitter.nq"
SUCCESSOR_PARSE_STMTS_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/successor_parse_stmts.nq"
SUCCESSOR_SELF_EMIT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/successor_self_emit.nq"
SUCCESSOR_PARSE_STMTS_STORE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/successor_parse_stmts_store.nq"
SUCCESSOR_PARSE_STMTS_TWO_STORES_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/successor_parse_stmts_two_stores.nq"
SUCCESSOR_WHILE_CLEAR_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/c0/successor_while_clear.nq"

fail_test() {
    printf 'FAIL %s\n' "$1" >&2
    exit 1
}

run_output_bounded() {
    local duration="$1"
    local exe="$2"
    shift 2
    if [[ "$(uname -m)" == "x86_64" ]]; then
        timeout "$duration" "$exe" "$@"
    else
        timeout "$duration" qemu-x86_64 "$exe" "$@"
    fi
}

assert_load_segments_disjoint() {
    local artifact="$1"
    local label="$2"
    local program_headers rx_vaddr rx_filesz rw_vaddr

    program_headers="$(readelf -lW "$artifact")" || \
        fail_test "$label-readelf"
    rx_vaddr="$(awk '$1 == "LOAD" && $7 == "R" && $8 == "E" { print $3; exit }' \
        <<< "$program_headers")"
    rx_filesz="$(awk '$1 == "LOAD" && $7 == "R" && $8 == "E" { print $5; exit }' \
        <<< "$program_headers")"
    rw_vaddr="$(awk '$1 == "LOAD" && $7 == "RW" { print $3; exit }' \
        <<< "$program_headers")"
    [[ -n "$rx_vaddr" && -n "$rx_filesz" && -n "$rw_vaddr" ]] || \
        fail_test "$label-load-layout"
    (( rx_vaddr + rx_filesz <= rw_vaddr )) || \
        fail_test "$label-load-overlap"
}

append_canonical_write_lines() {
    local artifact="$1"
    local output="$2"
    local -a bytes
    local byte index escaped

    mapfile -t bytes < <(od -An -tu1 -v "$artifact" | tr -s ' ' '\n' | sed '/^$/d')
    for ((index = 0; index < ${#bytes[@]}; index++)); do
        if (( index % 255 == 0 )); then
            printf 'write("' >> "$output"
        fi
        byte="${bytes[index]}"
        case "$byte" in
            0) escaped='\0' ;;
            9) escaped='\t' ;;
            10) escaped='\n' ;;
            13) escaped='\r' ;;
            34) escaped='\"' ;;
            92) escaped='\\' ;;
            *)
                if (( byte >= 32 && byte <= 126 )); then
                    printf -v escaped '\\%03o' "$byte"
                    printf -v escaped '%b' "$escaped"
                else
                    printf -v escaped '\\x%02x' "$byte"
                fi
                ;;
        esac
        printf '%s' "$escaped" >> "$output"
        if (( index % 255 == 254 || index + 1 == ${#bytes[@]} )); then
            printf '")\n' >> "$output"
        fi
    done
}

bootstrap_row="$(awk -F '\t' '$1 == "bootstrap-compiler" { print $2 "\t" $3 "\t" $4 }' "$MANIFEST")"
expected_bootstrap_row=$'PASS\tbootstrap/compiler/b0/x86_64-linux/b0.seed\ttests/bootstrap/bootstrap_compiler_b0.sh'
[[ "$bootstrap_row" == "$expected_bootstrap_row" ]] || \
    fail_test "c0-predecessor-bootstrap-pass"
printf 'PASS c0-predecessor-bootstrap-pass\n'

core_row="$(awk -F '\t' '$1 == "core-compiler" { print $2 "\t" $3 "\t" $4 }' "$MANIFEST")"
expected_core_row=$'PASS\tbootstrap/compiler/c0/x86_64-linux/c0.seed\ttests/bootstrap/core_compiler_c0.sh'
[[ "$core_row" == "$expected_core_row" ]] || fail_test "c0-manifest-pass"
printf 'PASS c0-manifest-pass\n'

[[ -f "$SOURCE" ]] || fail_test "c0-source-present"
[[ -x "$SEED" ]] || fail_test "c0-seed-is-executable"
[[ -f "$HASH" ]] || fail_test "c0-hash-present"
[[ -x "$MATERIALIZER" ]] || fail_test "c0-materializer-present"
[[ -x "$COMPILER_ADAPTER" ]] || fail_test "c0-compiler-adapter-present"
[[ -f "$SUCCESSOR_SOURCE" ]] || fail_test "c0-successor-source-present"
successor_source_size="$(wc -c < "$SUCCESSOR_SOURCE")"
[[ "$successor_source_size" -gt 0 ]] || fail_test "c0-successor-source-nonempty"
[[ "$successor_source_size" -le 9984 ]] || \
    fail_test "c0-successor-source-within-c0-input-capacity"
[[ -x "$SUCCESSOR_SEED" ]] || fail_test "c0-successor-seed-is-executable"
[[ -f "$SUCCESSOR_HASH" ]] || fail_test "c0-successor-hash-present"
[[ -x "$SUCCESSOR_MATERIALIZER" ]] || fail_test "c0-successor-materializer-present"
printf 'PASS c0-layout\n'

if find "$C0_DIR" -type f \( -name '*.py' -o -name '*.asm' -o -name '*.c' \
    -o -name '*.cc' -o -name '*.cpp' -o -name '*.rs' -o -name '*.ll' \) | grep -q .; then
    fail_test "c0-no-host-toolchain-source"
fi
printf 'PASS c0-no-host-toolchain-source\n'

run_output "$B0_SEED" "$SOURCE" -o "$TMP_DIR/c0.from-b0.one" \
    > "$TMP_DIR/c0.b0.stdout" 2> "$TMP_DIR/c0.b0.stderr"
[[ ! -s "$TMP_DIR/c0.b0.stdout" ]] || fail_test "c0-b0-build-stdout"
[[ ! -s "$TMP_DIR/c0.b0.stderr" ]] || fail_test "c0-b0-build-stderr"
cmp -s "$SEED" "$TMP_DIR/c0.from-b0.one" || fail_test "c0-built-by-b0"
printf 'PASS c0-built-by-b0\n'

run_output "$B0_SEED" "$SOURCE" -o "$TMP_DIR/c0.from-b0.two" >/dev/null
cmp -s "$TMP_DIR/c0.from-b0.one" "$TMP_DIR/c0.from-b0.two" || \
    fail_test "c0-deterministic-predecessor-build"
printf 'PASS c0-deterministic-predecessor-build\n'

"$MATERIALIZER" "$TMP_DIR/c0.materialized.one" >/dev/null
"$MATERIALIZER" "$TMP_DIR/c0.materialized.two" >/dev/null
cmp -s "$SEED" "$TMP_DIR/c0.materialized.one" || fail_test "c0-materialized-canonical"
cmp -s "$TMP_DIR/c0.materialized.one" "$TMP_DIR/c0.materialized.two" || \
    fail_test "c0-deterministic-materialization"
printf 'PASS c0-deterministic-materialization\n'

mat_root="$TMP_DIR/materializer-root"
mkdir -p "$mat_root/bootstrap/compiler/b0/x86_64-linux" \
    "$mat_root/bootstrap/compiler/c0/x86_64-linux"
cp "$B0_SEED" "$mat_root/bootstrap/compiler/b0/x86_64-linux/b0.seed"
cp "$SOURCE" "$mat_root/bootstrap/compiler/c0/compiler.nq"
cp "$MATERIALIZER" "$mat_root/bootstrap/compiler/c0/x86_64-linux/materialize.sh"
chmod 0755 "$mat_root/bootstrap/compiler/b0/x86_64-linux/b0.seed" \
    "$mat_root/bootstrap/compiler/c0/x86_64-linux/materialize.sh"
printf '%064d  c0.seed\n' 0 \
    > "$mat_root/bootstrap/compiler/c0/x86_64-linux/c0.sha256"
printf 'old-c0-output' > "$mat_root/bootstrap/compiler/c0/x86_64-linux/c0.seed"
set +e
"$mat_root/bootstrap/compiler/c0/x86_64-linux/materialize.sh" \
    > "$TMP_DIR/c0.materializer-bad-hash.stdout" \
    2> "$TMP_DIR/c0.materializer-bad-hash.stderr"
materializer_bad_hash_status=$?
set -e
[[ "$materializer_bad_hash_status" -eq 1 ]] || \
    fail_test "c0-materializer-bad-hash-status (expected 1, got $materializer_bad_hash_status)"
printf 'old-c0-output' > "$TMP_DIR/c0.materializer-old.expected"
cmp -s "$TMP_DIR/c0.materializer-old.expected" \
    "$mat_root/bootstrap/compiler/c0/x86_64-linux/c0.seed" || \
    fail_test "c0-materializer-bad-hash-preserves-output"
grep -Fq 'C0 hash mismatch' "$TMP_DIR/c0.materializer-bad-hash.stderr" || \
    fail_test "c0-materializer-bad-hash-diagnostic"
if find "$mat_root/bootstrap/compiler/c0/x86_64-linux" -maxdepth 1 \
    -name '.c0.seed.tmp.*' -print -quit | grep -q .; then
    fail_test "c0-materializer-bad-hash-temp-cleanup"
fi
printf 'PASS c0-materializer-bad-hash-atomic\n'

mkdir "$TMP_DIR/c0.materializer-target-dir"
set +e
"$MATERIALIZER" "$TMP_DIR/c0.materializer-target-dir" \
    > "$TMP_DIR/c0.materializer-dir.stdout" \
    2> "$TMP_DIR/c0.materializer-dir.stderr"
materializer_dir_status=$?
set -e
[[ "$materializer_dir_status" -eq 1 ]] || \
    fail_test "c0-materializer-directory-status (expected 1, got $materializer_dir_status)"
grep -Fq 'output path' "$TMP_DIR/c0.materializer-dir.stderr" || \
    fail_test "c0-materializer-directory-diagnostic"
if find "$TMP_DIR/c0.materializer-target-dir" -mindepth 1 -print -quit | grep -q .; then
    fail_test "c0-materializer-directory-no-temp-entry"
fi
printf 'PASS c0-materializer-rejects-directory-output\n'

expected_hash="$(awk '{ print $1 }' "$HASH")"
actual_hash="$(sha256sum "$SEED")"
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || fail_test "c0-hash"
printf 'PASS c0-hash\n'

run_output "$SEED" < "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.successor.from-c0.one" \
    2> "$TMP_DIR/c0.successor.from-c0.stderr"
[[ ! -s "$TMP_DIR/c0.successor.from-c0.stderr" ]] || \
    fail_test "c0-successor-build-stderr"
run_output "$SEED" < "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.successor.from-c0.two"
cmp -s "$SUCCESSOR_SEED" "$TMP_DIR/c0.successor.from-c0.one" || \
    fail_test "c0-successor-built-by-c0"
cmp -s "$TMP_DIR/c0.successor.from-c0.one" \
    "$TMP_DIR/c0.successor.from-c0.two" || \
    fail_test "c0-successor-deterministic-build"
expected_successor_hash="$(awk '{ print $1 }' "$SUCCESSOR_HASH")"
actual_successor_hash="$(sha256sum "$SUCCESSOR_SEED")"
actual_successor_hash="${actual_successor_hash%% *}"
[[ "$actual_successor_hash" == "$expected_successor_hash" ]] || \
    fail_test "c0-successor-hash"
printf 'PASS c0-successor-built-by-c0\n'

"$SUCCESSOR_MATERIALIZER" "$TMP_DIR/c0.successor.materialized.one" >/dev/null
"$SUCCESSOR_MATERIALIZER" "$TMP_DIR/c0.successor.materialized.two" >/dev/null
cmp -s "$SUCCESSOR_SEED" "$TMP_DIR/c0.successor.materialized.one" || \
    fail_test "c0-successor-materialized-canonical"
cmp -s "$TMP_DIR/c0.successor.materialized.one" \
    "$TMP_DIR/c0.successor.materialized.two" || \
    fail_test "c0-successor-deterministic-materialization"
printf 'PASS c0-successor-materialization\n'

for successor_valid_case in 0:0 7:7 00:0 42:42 099:99 100:100 255:255; do
    successor_source_value="${successor_valid_case%%:*}"
    successor_expected_value="${successor_valid_case#*:}"
    printf 'fn main(){\nreturn %s}\n' "$successor_source_value" \
        > "$TMP_DIR/c0.successor.source-$successor_source_value"
    printf 'fn main(){\nreturn %s}\n' "$successor_source_value" \
        > "$TMP_DIR/c0.successor.direct-source-$successor_source_value.nq"
    run_output "$SEED" \
        < "$TMP_DIR/c0.successor.direct-source-$successor_source_value.nq" \
        > "$TMP_DIR/c0.successor.direct-$successor_source_value"
    set +e
    run_output "$SUCCESSOR_SEED" \
        < "$TMP_DIR/c0.successor.source-$successor_source_value" \
        > "$TMP_DIR/c0.successor.output-$successor_source_value.one" \
        2> "$TMP_DIR/c0.successor.output-$successor_source_value.stderr"
    successor_compile_one_status=$?
    run_output "$SUCCESSOR_SEED" \
        < "$TMP_DIR/c0.successor.source-$successor_source_value" \
        > "$TMP_DIR/c0.successor.output-$successor_source_value.two" \
        2> "$TMP_DIR/c0.successor.output-$successor_source_value.two.stderr"
    successor_compile_two_status=$?
    set -e
    [[ "$successor_compile_one_status" -eq 0 ]] || \
        fail_test "c0-successor-source-$successor_source_value-compile (expected 0, got $successor_compile_one_status)"
    [[ "$successor_compile_two_status" -eq 0 ]] || \
        fail_test "c0-successor-source-$successor_source_value-recompile (expected 0, got $successor_compile_two_status)"
    [[ ! -s "$TMP_DIR/c0.successor.output-$successor_source_value.stderr" ]] || \
        fail_test "c0-successor-source-$successor_source_value-stderr"
    [[ ! -s "$TMP_DIR/c0.successor.output-$successor_source_value.two.stderr" ]] || \
        fail_test "c0-successor-source-$successor_source_value-recompile-stderr"
    cmp -s "$TMP_DIR/c0.successor.direct-$successor_source_value" \
        "$TMP_DIR/c0.successor.output-$successor_source_value.one" || \
        fail_test "c0-successor-source-$successor_source_value-output-parity"
    cmp -s "$TMP_DIR/c0.successor.output-$successor_source_value.one" \
        "$TMP_DIR/c0.successor.output-$successor_source_value.two" || \
        fail_test "c0-successor-source-$successor_source_value-output-deterministic"
    chmod 0755 "$TMP_DIR/c0.successor.output-$successor_source_value.one"
    set +e
    run_output_bounded 5 \
        "$TMP_DIR/c0.successor.output-$successor_source_value.one" \
        > "$TMP_DIR/c0.successor.run-$successor_source_value.stdout" \
        2> "$TMP_DIR/c0.successor.run-$successor_source_value.stderr"
    successor_output_status=$?
    set -e
    [[ "$successor_output_status" -eq "$successor_expected_value" ]] || \
        fail_test "c0-successor-source-$successor_source_value-run (expected $successor_expected_value, got $successor_output_status)"
    [[ ! -s "$TMP_DIR/c0.successor.run-$successor_source_value.stdout" ]] || \
        fail_test "c0-successor-source-$successor_source_value-run-stdout"
    [[ ! -s "$TMP_DIR/c0.successor.run-$successor_source_value.stderr" ]] || \
        fail_test "c0-successor-source-$successor_source_value-run-stderr"
done
if cmp -s "$TMP_DIR/c0.successor.output-0.one" \
    "$TMP_DIR/c0.successor.output-255.one"; then
    fail_test "c0-successor-source-dependent-output"
fi

printf 'fn main(){\ninput_read(32,96)\nreturn 7}\n' \
    > "$TMP_DIR/c0.successor.input-read.source"
run_output "$SEED" < "$TMP_DIR/c0.successor.input-read.source" \
    > "$TMP_DIR/c0.successor.input-read.direct"
set +e
run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$TMP_DIR/c0.successor.input-read.source" \
    > "$TMP_DIR/c0.successor.input-read.output.one" \
    2> "$TMP_DIR/c0.successor.input-read.compile.stderr"
successor_input_compile_status=$?
run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$TMP_DIR/c0.successor.input-read.source" \
    > "$TMP_DIR/c0.successor.input-read.output.two" \
    2> "$TMP_DIR/c0.successor.input-read.recompile.stderr"
successor_input_recompile_status=$?
set -e
[[ "$successor_input_compile_status" -eq 0 ]] || \
    fail_test "c0-successor-input-read-compile (expected 0, got $successor_input_compile_status)"
[[ "$successor_input_recompile_status" -eq 0 ]] || \
    fail_test "c0-successor-input-read-recompile (expected 0, got $successor_input_recompile_status)"
[[ ! -s "$TMP_DIR/c0.successor.input-read.compile.stderr" ]] || \
    fail_test "c0-successor-input-read-compile-stderr"
[[ ! -s "$TMP_DIR/c0.successor.input-read.recompile.stderr" ]] || \
    fail_test "c0-successor-input-read-recompile-stderr"
cmp -s "$TMP_DIR/c0.successor.input-read.direct" \
    "$TMP_DIR/c0.successor.input-read.output.one" || \
    fail_test "c0-successor-input-read-output-parity"
cmp -s "$TMP_DIR/c0.successor.input-read.output.one" \
    "$TMP_DIR/c0.successor.input-read.output.two" || \
    fail_test "c0-successor-input-read-output-deterministic"
chmod 0755 "$TMP_DIR/c0.successor.input-read.output.one"
set +e
printf 'NolQu-L' | run_output_bounded 5 \
    "$TMP_DIR/c0.successor.input-read.output.one" \
    > "$TMP_DIR/c0.successor.input-read.run.stdout" \
    2> "$TMP_DIR/c0.successor.input-read.run.stderr"
successor_input_run_status=$?
set -e
[[ "$successor_input_run_status" -eq 7 ]] || \
    fail_test "c0-successor-input-read-run (expected 7, got $successor_input_run_status)"
[[ ! -s "$TMP_DIR/c0.successor.input-read.run.stdout" ]] || \
    fail_test "c0-successor-input-read-run-stdout"
[[ ! -s "$TMP_DIR/c0.successor.input-read.run.stderr" ]] || \
    fail_test "c0-successor-input-read-run-stderr"
set +e
run_with_invalid_standard_fd 0 run_output_bounded 5 "$TMP_DIR/c0.successor.input-read.output.one"  \
    > "$TMP_DIR/c0.successor.input-read.closed.stdout" \
    2> "$TMP_DIR/c0.successor.input-read.closed.stderr"
successor_input_closed_status=$?
set -e
[[ "$successor_input_closed_status" -eq 74 ]] || \
    fail_test "c0-successor-input-read-closed-status (expected 74, got $successor_input_closed_status)"
[[ ! -s "$TMP_DIR/c0.successor.input-read.closed.stdout" ]] || \
    fail_test "c0-successor-input-read-closed-stdout"
printf 'runtime: input_read failed\n' \
    > "$TMP_DIR/c0.successor.input-read.closed.expected"
cmp -s "$TMP_DIR/c0.successor.input-read.closed.expected" \
    "$TMP_DIR/c0.successor.input-read.closed.stderr" || \
    fail_test "c0-successor-input-read-closed-diagnostic"

run_output "$SEED" < "$SUCCESSOR_SELF_EMIT_FIXTURE" \
    > "$TMP_DIR/c0.successor.parse-stmts.direct"
chmod 0755 "$TMP_DIR/c0.successor.parse-stmts.direct"
set +e
run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$SUCCESSOR_PARSE_STMTS_FIXTURE" \
    > "$TMP_DIR/c0.successor.parse-stmts.output.one" \
    2> "$TMP_DIR/c0.successor.parse-stmts.compile.stderr"
successor_parse_stmts_compile_status=$?
run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$SUCCESSOR_PARSE_STMTS_FIXTURE" \
    > "$TMP_DIR/c0.successor.parse-stmts.output.two" \
    2> "$TMP_DIR/c0.successor.parse-stmts.recompile.stderr"
successor_parse_stmts_recompile_status=$?
set -e
[[ "$successor_parse_stmts_compile_status" -eq 0 ]] || \
    fail_test "c0-successor-parse-stmts-compile (expected 0, got $successor_parse_stmts_compile_status)"
[[ "$successor_parse_stmts_recompile_status" -eq 0 ]] || \
    fail_test "c0-successor-parse-stmts-recompile (expected 0, got $successor_parse_stmts_recompile_status)"
[[ ! -s "$TMP_DIR/c0.successor.parse-stmts.compile.stderr" ]] || \
    fail_test "c0-successor-parse-stmts-compile-stderr"
[[ ! -s "$TMP_DIR/c0.successor.parse-stmts.recompile.stderr" ]] || \
    fail_test "c0-successor-parse-stmts-recompile-stderr"
cmp -s "$TMP_DIR/c0.successor.parse-stmts.direct" \
    "$TMP_DIR/c0.successor.parse-stmts.output.one" || \
    fail_test "c0-successor-parse-stmts-output-parity"
cmp -s "$TMP_DIR/c0.successor.parse-stmts.output.one" \
    "$TMP_DIR/c0.successor.parse-stmts.output.two" || \
    fail_test "c0-successor-parse-stmts-output-deterministic"
chmod 0755 "$TMP_DIR/c0.successor.parse-stmts.output.one"
set +e
printf 'fn main(){\nreturn 7}\n' | run_output_bounded 5 \
    "$TMP_DIR/c0.successor.parse-stmts.output.one" \
    > "$TMP_DIR/c0.successor.parse-stmts.valid.stdout" \
    2> "$TMP_DIR/c0.successor.parse-stmts.valid.stderr"
successor_parse_stmts_valid_status=$?
set -e
[[ "$successor_parse_stmts_valid_status" -eq 0 ]] || \
    fail_test "c0-successor-parse-stmts-valid-run (expected 0, got $successor_parse_stmts_valid_status)"
[[ ! -s "$TMP_DIR/c0.successor.parse-stmts.valid.stdout" ]] || \
    fail_test "c0-successor-parse-stmts-valid-stdout"
[[ ! -s "$TMP_DIR/c0.successor.parse-stmts.valid.stderr" ]] || \
    fail_test "c0-successor-parse-stmts-valid-stderr"
set +e
printf 'not NolQu-L\n' | run_output_bounded 5 \
    "$TMP_DIR/c0.successor.parse-stmts.output.one" \
    > "$TMP_DIR/c0.successor.parse-stmts.invalid.stdout" \
    2> "$TMP_DIR/c0.successor.parse-stmts.invalid.stderr"
successor_parse_stmts_invalid_status=$?
set -e
[[ "$successor_parse_stmts_invalid_status" -eq 1 ]] || \
    fail_test "c0-successor-parse-stmts-invalid-run (expected 1, got $successor_parse_stmts_invalid_status)"
[[ ! -s "$TMP_DIR/c0.successor.parse-stmts.invalid.stdout" ]] || \
    fail_test "c0-successor-parse-stmts-invalid-stdout"
printf 'runtime: invalid source\n' \
    > "$TMP_DIR/c0.successor.parse-stmts.invalid.expected"
cmp -s "$TMP_DIR/c0.successor.parse-stmts.invalid.expected" \
    "$TMP_DIR/c0.successor.parse-stmts.invalid.stderr" || \
    fail_test "c0-successor-parse-stmts-invalid-diagnostic"

run_output "$SEED" < "$SUCCESSOR_WHILE_CLEAR_FIXTURE" \
    > "$TMP_DIR/c0.successor.while-clear.direct"
chmod 0755 "$TMP_DIR/c0.successor.while-clear.direct"
set +e
run_output_bounded 5 "$TMP_DIR/c0.successor.while-clear.direct" \
    > "$TMP_DIR/c0.successor.while-clear.direct.stdout" \
    2> "$TMP_DIR/c0.successor.while-clear.direct.stderr"
successor_while_clear_direct_status=$?
run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$SUCCESSOR_WHILE_CLEAR_FIXTURE" \
    > "$TMP_DIR/c0.successor.while-clear.output.one" \
    2> "$TMP_DIR/c0.successor.while-clear.compile.stderr"
successor_while_clear_compile_status=$?
run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$SUCCESSOR_WHILE_CLEAR_FIXTURE" \
    > "$TMP_DIR/c0.successor.while-clear.output.two" \
    2> "$TMP_DIR/c0.successor.while-clear.recompile.stderr"
successor_while_clear_recompile_status=$?
set -e
[[ "$successor_while_clear_direct_status" -eq 7 ]] || \
    fail_test "c0-successor-while-clear-direct-run (expected 7, got $successor_while_clear_direct_status)"
[[ ! -s "$TMP_DIR/c0.successor.while-clear.direct.stdout" ]] || \
    fail_test "c0-successor-while-clear-direct-stdout"
[[ ! -s "$TMP_DIR/c0.successor.while-clear.direct.stderr" ]] || \
    fail_test "c0-successor-while-clear-direct-stderr"
[[ "$successor_while_clear_compile_status" -eq 0 ]] || \
    fail_test "c0-successor-while-clear-compile (expected 0, got $successor_while_clear_compile_status)"
[[ "$successor_while_clear_recompile_status" -eq 0 ]] || \
    fail_test "c0-successor-while-clear-recompile (expected 0, got $successor_while_clear_recompile_status)"
[[ ! -s "$TMP_DIR/c0.successor.while-clear.compile.stderr" ]] || \
    fail_test "c0-successor-while-clear-compile-stderr"
[[ ! -s "$TMP_DIR/c0.successor.while-clear.recompile.stderr" ]] || \
    fail_test "c0-successor-while-clear-recompile-stderr"
cmp -s "$TMP_DIR/c0.successor.output-7.one" \
    "$TMP_DIR/c0.successor.while-clear.output.one" || \
    fail_test "c0-successor-while-clear-dead-loop-output"
cmp -s "$TMP_DIR/c0.successor.while-clear.output.one" \
    "$TMP_DIR/c0.successor.while-clear.output.two" || \
    fail_test "c0-successor-while-clear-output-deterministic"
chmod 0755 "$TMP_DIR/c0.successor.while-clear.output.one"
set +e
run_output_bounded 5 "$TMP_DIR/c0.successor.while-clear.output.one" \
    > "$TMP_DIR/c0.successor.while-clear.run.stdout" \
    2> "$TMP_DIR/c0.successor.while-clear.run.stderr"
successor_while_clear_run_status=$?
set -e
[[ "$successor_while_clear_run_status" -eq 7 ]] || \
    fail_test "c0-successor-while-clear-run (expected 7, got $successor_while_clear_run_status)"
[[ ! -s "$TMP_DIR/c0.successor.while-clear.run.stdout" ]] || \
    fail_test "c0-successor-while-clear-run-stdout"
[[ ! -s "$TMP_DIR/c0.successor.while-clear.run.stderr" ]] || \
    fail_test "c0-successor-while-clear-run-stderr"

for post_parser_store_case in one two; do
    case "$post_parser_store_case" in
        one) post_parser_store_fixture="$SUCCESSOR_PARSE_STMTS_STORE_FIXTURE" ;;
        two) post_parser_store_fixture="$SUCCESSOR_PARSE_STMTS_TWO_STORES_FIXTURE" ;;
    esac
    run_output "$SEED" < "$post_parser_store_fixture" \
        > "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct"
    chmod 0755 "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct"
    set +e
    printf 'fn main(){\nreturn 7}\n' | run_output_bounded 5 \
        "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct" \
        > "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct.stdout" \
        2> "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct.stderr"
    post_parser_store_direct_status=$?
    run_output_bounded 5 "$SUCCESSOR_SEED" \
        < "$post_parser_store_fixture" \
        > "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.one" \
        2> "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.compile.stderr"
    post_parser_store_compile_status=$?
    run_output_bounded 5 "$SUCCESSOR_SEED" \
        < "$post_parser_store_fixture" \
        > "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.two" \
        2> "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.recompile.stderr"
    post_parser_store_recompile_status=$?
    set -e
    [[ "$post_parser_store_direct_status" -eq 0 ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-direct-run (expected 0, got $post_parser_store_direct_status)"
    [[ ! -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct.stdout" ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-direct-stdout"
    [[ ! -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.direct.stderr" ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-direct-stderr"
    [[ "$post_parser_store_compile_status" -eq 0 ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-compile (expected 0, got $post_parser_store_compile_status)"
    [[ "$post_parser_store_recompile_status" -eq 0 ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-recompile (expected 0, got $post_parser_store_recompile_status)"
    [[ ! -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.compile.stderr" ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-compile-stderr"
    [[ ! -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.recompile.stderr" ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-recompile-stderr"
    cmp -s "$TMP_DIR/c0.successor.parse-stmts.output.one" \
        "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.one" || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-dead-output"
    cmp -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.one" \
        "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.two" || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-deterministic"
    chmod 0755 "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.one"
    set +e
    printf 'fn main(){\nreturn 7}\n' | run_output_bounded 5 \
        "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.output.one" \
        > "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.run.stdout" \
        2> "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.run.stderr"
    post_parser_store_run_status=$?
    set -e
    [[ "$post_parser_store_run_status" -eq 0 ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-run (expected 0, got $post_parser_store_run_status)"
    [[ ! -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.run.stdout" ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-run-stdout"
    [[ ! -s "$TMP_DIR/c0.successor.parse-stmts-$post_parser_store_case-store.run.stderr" ]] || \
        fail_test "c0-successor-parse-stmts-$post_parser_store_case-store-run-stderr"
done

for successor_store_case in one-store three-stores; do
    case "$successor_store_case" in
        one-store)
            successor_store_expected=42
            printf 'fn main(){\nbyte_store(3,9)\nreturn 42}\n' \
                > "$TMP_DIR/c0.successor.$successor_store_case.source"
            ;;
        three-stores)
            successor_store_expected=7
            printf 'fn main(){\nbyte_store(0,0)\nbyte_store(255,255)\nbyte_store(42,099)\nreturn 7}\n' \
                > "$TMP_DIR/c0.successor.$successor_store_case.source"
            ;;
    esac
    set +e
    run_output_bounded 5 "$SUCCESSOR_SEED" \
        < "$TMP_DIR/c0.successor.$successor_store_case.source" \
        > "$TMP_DIR/c0.successor.$successor_store_case.output.one" \
        2> "$TMP_DIR/c0.successor.$successor_store_case.stderr"
    successor_store_compile_status=$?
    run_output_bounded 5 "$SUCCESSOR_SEED" \
        < "$TMP_DIR/c0.successor.$successor_store_case.source" \
        > "$TMP_DIR/c0.successor.$successor_store_case.output.two" \
        2> "$TMP_DIR/c0.successor.$successor_store_case.two.stderr"
    successor_store_recompile_status=$?
    set -e
    [[ "$successor_store_compile_status" -eq 0 ]] || \
        fail_test "c0-successor-$successor_store_case-compile (expected 0, got $successor_store_compile_status)"
    [[ "$successor_store_recompile_status" -eq 0 ]] || \
        fail_test "c0-successor-$successor_store_case-recompile (expected 0, got $successor_store_recompile_status)"
    [[ ! -s "$TMP_DIR/c0.successor.$successor_store_case.stderr" ]] || \
        fail_test "c0-successor-$successor_store_case-stderr"
    [[ ! -s "$TMP_DIR/c0.successor.$successor_store_case.two.stderr" ]] || \
        fail_test "c0-successor-$successor_store_case-recompile-stderr"
    cmp -s "$TMP_DIR/c0.successor.output-$successor_store_expected.one" \
        "$TMP_DIR/c0.successor.$successor_store_case.output.one" || \
        fail_test "c0-successor-$successor_store_case-dead-store-output"
    cmp -s "$TMP_DIR/c0.successor.$successor_store_case.output.one" \
        "$TMP_DIR/c0.successor.$successor_store_case.output.two" || \
        fail_test "c0-successor-$successor_store_case-deterministic"
done

printf 'runtime: invalid source\n' \
    > "$TMP_DIR/c0.successor-invalid.expected"
for successor_invalid_case in \
    empty wrong-fn missing-fn-space wrong-main missing-left-paren \
    missing-right-paren missing-left-brace missing-layout-newline wrong-return missing-return-space \
    no-digits first-nondigit embedded-nondigit overflow missing-right-brace \
    missing-newline trailing four-digit store-wrong-name store-missing-comma \
    store-first-overflow store-second-overflow store-missing-newline fourth-store \
    input-wrong-offset input-wrong-count input-leading-zero-offset \
    input-leading-zero-count input-duplicate store-after-input \
    parser-without-input parser-wrong-source parser-wrong-destination \
    parser-leading-zero-source parser-leading-zero-destination \
    parser-duplicate parser-store-third while-wrong-condition \
    while-wrong-body while-missing-close; do
    case "$successor_invalid_case" in
        empty) : > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        wrong-fn) printf 'fm main(){\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-fn-space) printf 'fnmain(){\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        wrong-main) printf 'fn nope(){\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-left-paren) printf 'fn main){\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-right-paren) printf 'fn main({\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-left-brace) printf 'fn main()\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-layout-newline) printf 'fn main(){return 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        wrong-return) printf 'fn main(){\nret 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-return-space) printf 'fn main(){\nreturn42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        no-digits) printf 'fn main(){\nreturn }\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        first-nondigit) printf 'fn main(){\nreturn x}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        embedded-nondigit) printf 'fn main(){\nreturn 4x}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        overflow) printf 'fn main(){\nreturn 256}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-right-brace) printf 'fn main(){\nreturn 42\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        missing-newline) printf 'fn main(){\nreturn 42}' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        trailing) printf 'fn main(){\nreturn 42}\nx' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        four-digit) printf 'fn main(){\nreturn 0255}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        store-wrong-name) printf 'fn main(){\nbyte_stare(1,2)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        store-missing-comma) printf 'fn main(){\nbyte_store(1 2)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        store-first-overflow) printf 'fn main(){\nbyte_store(256,2)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        store-second-overflow) printf 'fn main(){\nbyte_store(1,256)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        store-missing-newline) printf 'fn main(){\nbyte_store(1,2)return 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        fourth-store) printf 'fn main(){\nbyte_store(1,1)\nbyte_store(2,2)\nbyte_store(3,3)\nbyte_store(4,4)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        input-wrong-offset) printf 'fn main(){\ninput_read(0,96)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        input-wrong-count) printf 'fn main(){\ninput_read(32,95)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        input-leading-zero-offset) printf 'fn main(){\ninput_read(032,96)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        input-leading-zero-count) printf 'fn main(){\ninput_read(32,096)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        input-duplicate) printf 'fn main(){\ninput_read(32,96)\ninput_read(32,96)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        store-after-input) printf 'fn main(){\ninput_read(32,96)\nbyte_store(1,2)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-without-input) printf 'fn main(){\nbyte_parse_stmts(32,0)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-wrong-source) printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(0,0)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-wrong-destination) printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,1)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-leading-zero-source) printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(032,0)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-leading-zero-destination) printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,00)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-duplicate) printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nbyte_parse_stmts(32,0)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        parser-store-third) printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nbyte_store(4,184)\nbyte_store(5,60)\nbyte_store(9,15)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        while-wrong-condition) printf 'fn main(){\nwhile byte_load(2) {\nbyte_store(1,0)\n}\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        while-wrong-body) printf 'fn main(){\nwhile byte_load(1) {\nbyte_store(1,1)\n}\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
        while-missing-close) printf 'fn main(){\nwhile byte_load(1) {\nbyte_store(1,0)\nreturn 42}\n' > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" ;;
    esac
    set +e
    run_output_bounded 5 "$SUCCESSOR_SEED" \
        < "$TMP_DIR/c0.successor.invalid-$successor_invalid_case" \
        > "$TMP_DIR/c0.successor.invalid-$successor_invalid_case.stdout" \
        2> "$TMP_DIR/c0.successor.invalid-$successor_invalid_case.stderr"
    successor_invalid_status=$?
    set -e
    [[ "$successor_invalid_status" -eq 1 ]] || \
        fail_test "c0-successor-invalid-$successor_invalid_case-status (expected 1, got $successor_invalid_status)"
    [[ ! -s "$TMP_DIR/c0.successor.invalid-$successor_invalid_case.stdout" ]] || \
        fail_test "c0-successor-invalid-$successor_invalid_case-no-artifact"
    cmp -s "$TMP_DIR/c0.successor-invalid.expected" \
        "$TMP_DIR/c0.successor.invalid-$successor_invalid_case.stderr" || \
        fail_test "c0-successor-invalid-$successor_invalid_case-diagnostic"
done
printf 'runtime: output_write failed\n' \
    > "$TMP_DIR/c0.successor-output-error.expected"
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$TMP_DIR/c0.successor.source-42" \
     2> "$TMP_DIR/c0.successor-output-closed.stderr"
successor_output_closed_status=$?
set -e
[[ "$successor_output_closed_status" -eq 74 ]] || \
    fail_test "c0-successor-output-closed-status (expected 74, got $successor_output_closed_status)"
cmp -s "$TMP_DIR/c0.successor-output-error.expected" \
    "$TMP_DIR/c0.successor-output-closed.stderr" || \
    fail_test "c0-successor-output-closed-diagnostic"
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$SUCCESSOR_SEED" \
    < "$TMP_DIR/c0.successor.input-read.source" \
     2> "$TMP_DIR/c0.successor-input-output-closed.stderr"
successor_input_output_closed_status=$?
set -e
[[ "$successor_input_output_closed_status" -eq 74 ]] || \
    fail_test "c0-successor-input-output-closed-status (expected 74, got $successor_input_output_closed_status)"
cmp -s "$TMP_DIR/c0.successor-output-error.expected" \
    "$TMP_DIR/c0.successor-input-output-closed.stderr" || \
    fail_test "c0-successor-input-output-closed-diagnostic"
file "$SUCCESSOR_SEED" | grep -Fq 'ELF 64-bit LSB executable, x86-64' || \
    fail_test "c0-successor-elf64-x86-64"
if readelf -l "$SUCCESSOR_SEED" | grep -q 'INTERP'; then
    fail_test "c0-successor-no-interpreter"
fi
readelf -lW "$SUCCESSOR_SEED" | \
    awk '$1 == "GNU_STACK" { found=1; if ($7 ~ /E/) exit 1 } END { exit !found }' || \
    fail_test "c0-successor-non-executable-stack"
assert_load_segments_disjoint "$SUCCESSOR_SEED" "c0-successor"
printf 'PASS c0-successor-load-segments-disjoint\n'
successor_split_output_count="$(grep -Fxc 'output_write(0,1)' "$SUCCESSOR_SOURCE" || true)"
[[ "$successor_split_output_count" -eq 2 ]] || \
    fail_test "c0-successor-split-return-tail-output-count"
successor_fixed_tail_count="$(grep -Fxc 'write("\0\0\0\xb8<\0\0\0\x0f\x05")' "$SUCCESSOR_SOURCE" || true)"
[[ "$successor_fixed_tail_count" -eq 2 ]] || \
    fail_test "c0-successor-split-return-tail-literal-count"
for successor_removed_store in \
    'byte_store(4,184)' 'byte_store(5,60)' \
    'byte_store(9,15)' 'byte_store(10,5)'; do
    if grep -Fxq "$successor_removed_store" "$SUCCESSOR_SOURCE"; then
        fail_test "c0-successor-split-return-tail-removed-store"
    fi
done
printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nwhile byte_load(1) {\nwrite(' \
    > "$TMP_DIR/c0.successor-rebuild-prefix.expected"
successor_rebuild_prefix_size="$(wc -c < "$TMP_DIR/c0.successor-rebuild-prefix.expected")"
head -c "$successor_rebuild_prefix_size" "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.successor-rebuild-prefix.actual"
cmp -s "$TMP_DIR/c0.successor-rebuild-prefix.expected" \
    "$TMP_DIR/c0.successor-rebuild-prefix.actual" || \
    fail_test "c0-successor-rebuild-probe-first-construct"
set +e
run_output_bounded 5 "$TMP_DIR/c0.successor.parse-stmts.direct" \
    < "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.successor-rebuild-probe.stdout" \
    2> "$TMP_DIR/c0.successor-rebuild-probe.stderr"
successor_rebuild_probe_status=$?
set -e
[[ "$successor_rebuild_probe_status" -eq 0 ]] || \
    fail_test "c0-successor-rebuild-probe-status (expected 0, got $successor_rebuild_probe_status)"
cmp -s "$TMP_DIR/c0.successor.parse-stmts.direct" \
    "$TMP_DIR/c0.successor-rebuild-probe.stdout" || \
    fail_test "c0-successor-rebuild-probe-self-image"
[[ ! -s "$TMP_DIR/c0.successor-rebuild-probe.stderr" ]] || \
    fail_test "c0-successor-rebuild-probe-stderr"
run_output_bounded 5 "$TMP_DIR/c0.successor.parse-stmts.direct" \
    < "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.successor-rebuild-probe.two.stdout" \
    2> "$TMP_DIR/c0.successor-rebuild-probe.two.stderr"
cmp -s "$TMP_DIR/c0.successor-rebuild-probe.stdout" \
    "$TMP_DIR/c0.successor-rebuild-probe.two.stdout" || \
    fail_test "c0-successor-rebuild-probe-deterministic"
[[ ! -s "$TMP_DIR/c0.successor-rebuild-probe.two.stderr" ]] || \
    fail_test "c0-successor-rebuild-probe-two-stderr"
printf 'PASS c0-successor-complete-bounded-generation\n'

run_output "$SEED" < "$SUCCESSOR_SELF_EMIT_FIXTURE" \
    > "$TMP_DIR/c0.successor.self-emit.direct"
chmod 0755 "$TMP_DIR/c0.successor.self-emit.direct"
assert_load_segments_disjoint \
    "$TMP_DIR/c0.successor.self-emit.direct" \
    "c0-successor-self-emit"
sed -n '1,10p' "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.successor.self-emit.source"
append_canonical_write_lines \
    "$TMP_DIR/c0.successor.self-emit.direct" \
    "$TMP_DIR/c0.successor.self-emit.source"
printf 'byte_store(3,0)\nbyte_store(2,0)\n}\n' \
    >> "$TMP_DIR/c0.successor.self-emit.source"
awk '
    $0 == "while byte_load(2) {" { capture = 1 }
    capture { print }
' "$SUCCESSOR_SOURCE" >> "$TMP_DIR/c0.successor.self-emit.source"
cmp -s "$SUCCESSOR_SOURCE" "$TMP_DIR/c0.successor.self-emit.source" || \
    fail_test "c0-successor-self-emit-source-canonical"

set +e
run_output_bounded 5 "$TMP_DIR/c0.successor.self-emit.direct" \
    < "$TMP_DIR/c0.successor.self-emit.source" \
    > "$TMP_DIR/c0.successor.self-emit.generation-c" \
    2> "$TMP_DIR/c0.successor.self-emit.generation-c.stderr"
successor_self_emit_c_status=$?
set -e
[[ "$successor_self_emit_c_status" -eq 0 ]] || \
    fail_test "c0-successor-self-emit-generation-c-status (expected 0, got $successor_self_emit_c_status)"
[[ ! -s "$TMP_DIR/c0.successor.self-emit.generation-c.stderr" ]] || \
    fail_test "c0-successor-self-emit-generation-c-stderr"
cmp -s "$TMP_DIR/c0.successor.self-emit.direct" \
    "$TMP_DIR/c0.successor.self-emit.generation-c" || \
    fail_test "c0-successor-self-emit-generation-c-identity"
chmod 0755 "$TMP_DIR/c0.successor.self-emit.generation-c"

run_output_bounded 5 "$TMP_DIR/c0.successor.self-emit.generation-c" \
    < "$TMP_DIR/c0.successor.self-emit.source" \
    > "$TMP_DIR/c0.successor.self-emit.generation-d" \
    2> "$TMP_DIR/c0.successor.self-emit.generation-d.stderr"
[[ ! -s "$TMP_DIR/c0.successor.self-emit.generation-d.stderr" ]] || \
    fail_test "c0-successor-self-emit-generation-d-stderr"
cmp -s "$TMP_DIR/c0.successor.self-emit.generation-c" \
    "$TMP_DIR/c0.successor.self-emit.generation-d" || \
    fail_test "c0-successor-self-emit-generation-d-identity"

printf 'runtime: output_write failed\n' \
    > "$TMP_DIR/c0.successor.self-emit-output-error.expected"
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$TMP_DIR/c0.successor.self-emit.direct" \
    < "$TMP_DIR/c0.successor.self-emit.source" \
     2> "$TMP_DIR/c0.successor.self-emit-output-closed.stderr"
successor_self_emit_output_closed_status=$?
set -e
[[ "$successor_self_emit_output_closed_status" -eq 74 ]] || \
    fail_test "c0-successor-self-emit-output-closed-status (expected 74, got $successor_self_emit_output_closed_status)"
cmp -s "$TMP_DIR/c0.successor.self-emit-output-error.expected" \
    "$TMP_DIR/c0.successor.self-emit-output-closed.stderr" || \
    fail_test "c0-successor-self-emit-output-closed-diagnostic"

sed '0,/\\x7fELF/s//\\x7eELF/' \
    "$TMP_DIR/c0.successor.self-emit.source" \
    > "$TMP_DIR/c0.successor.self-emit-invalid.source"
set +e
run_output_bounded 5 "$TMP_DIR/c0.successor.self-emit.direct" \
    < "$TMP_DIR/c0.successor.self-emit-invalid.source" \
    > "$TMP_DIR/c0.successor.self-emit-invalid.stdout" \
    2> "$TMP_DIR/c0.successor.self-emit-invalid.stderr"
successor_self_emit_invalid_status=$?
set -e
[[ "$successor_self_emit_invalid_status" -eq 1 ]] || \
    fail_test "c0-successor-self-emit-invalid-status (expected 1, got $successor_self_emit_invalid_status)"
[[ ! -s "$TMP_DIR/c0.successor.self-emit-invalid.stdout" ]] || \
    fail_test "c0-successor-self-emit-invalid-no-artifact"
cmp -s "$TMP_DIR/c0.successor-invalid.expected" \
    "$TMP_DIR/c0.successor.self-emit-invalid.stderr" || \
    fail_test "c0-successor-self-emit-invalid-diagnostic"
printf 'PASS c0-successor-bounded-generation-parity\n'

file "$SEED" | grep -Fq 'ELF 64-bit LSB executable, x86-64' || \
    fail_test "c0-elf64-x86-64"
if readelf -l "$SEED" | grep -q 'INTERP'; then
    fail_test "c0-no-interpreter"
fi
readelf -lW "$SEED" | awk '$1 == "GNU_STACK" { found=1; if ($7 ~ /E/) exit 1 } END { exit !found }' || \
    fail_test "c0-non-executable-stack"
printf 'PASS c0-static-machine-artifact\n'

run_output "$SEED" < "$RETURN7_FIXTURE" \
    > "$TMP_DIR/c0.return7.one" 2> "$TMP_DIR/c0.return7.stderr"
[[ ! -s "$TMP_DIR/c0.return7.stderr" ]] || fail_test "c0-return7-compile-stderr"
chmod 0755 "$TMP_DIR/c0.return7.one"
set +e
run_output_bounded 5 "$TMP_DIR/c0.return7.one" >/dev/null 2> "$TMP_DIR/c0.return7.run.stderr"
return7_status=$?
set -e
[[ "$return7_status" -eq 7 ]] || \
    fail_test "c0-return7-run (expected 7, got $return7_status)"
[[ ! -s "$TMP_DIR/c0.return7.run.stderr" ]] || fail_test "c0-return7-run-stderr"
file "$TMP_DIR/c0.return7.one" | grep -Fq 'ELF 64-bit LSB executable, x86-64' || \
    fail_test "c0-successor-elf64-x86-64"
if readelf -l "$TMP_DIR/c0.return7.one" | grep -q 'INTERP'; then
    fail_test "c0-successor-no-interpreter"
fi
readelf -lW "$TMP_DIR/c0.return7.one" | \
    awk '$1 == "GNU_STACK" { found=1; if ($7 ~ /E/) exit 1 } END { exit !found }' || \
    fail_test "c0-successor-non-executable-stack"
printf 'PASS c0-compile-return7\n'

run_output "$SEED" < "$RETURN23_FIXTURE" \
    > "$TMP_DIR/c0.return23" 2> "$TMP_DIR/c0.return23.stderr"
[[ ! -s "$TMP_DIR/c0.return23.stderr" ]] || fail_test "c0-return23-compile-stderr"
chmod 0755 "$TMP_DIR/c0.return23"
set +e
run_output_bounded 5 "$TMP_DIR/c0.return23" >/dev/null 2> "$TMP_DIR/c0.return23.run.stderr"
return23_status=$?
set -e
[[ "$return23_status" -eq 23 ]] || \
    fail_test "c0-return23-run (expected 23, got $return23_status)"
cmp -s "$TMP_DIR/c0.return7.one" "$TMP_DIR/c0.return23" && \
    fail_test "c0-semantic-output-varies-with-source"
printf 'PASS c0-whitespace-and-semantic-lowering\n'

run_output "$SEED" < "$RETURN_PRECEDENCE_FIXTURE" > "$TMP_DIR/c0.precedence"
chmod 0755 "$TMP_DIR/c0.precedence"
set +e
run_output_bounded 5 "$TMP_DIR/c0.precedence" >/dev/null
precedence_status=$?
set -e
[[ "$precedence_status" -eq 14 ]] || \
    fail_test "c0-expression-precedence (expected 14, got $precedence_status)"

run_output "$SEED" < "$RETURN_LEFT_ASSOC_FIXTURE" > "$TMP_DIR/c0.left-assoc"
chmod 0755 "$TMP_DIR/c0.left-assoc"
set +e
run_output_bounded 5 "$TMP_DIR/c0.left-assoc" >/dev/null
left_assoc_status=$?
set -e
[[ "$left_assoc_status" -eq 14 ]] || \
    fail_test "c0-expression-left-associativity (expected 14, got $left_assoc_status)"
printf 'PASS c0-expression-precedence-and-associativity\n'

for local_case in \
    "$LOCAL_BASIC_FIXTURE:7:basic" \
    "$LOCAL_EXPRESSION_FIXTURE:15:expression" \
    "$LOCAL_CHAIN_FIXTURE:20:chain"; do
    local_fixture="${local_case%%:*}"
    local_rest="${local_case#*:}"
    local_status_expected="${local_rest%%:*}"
    local_name="${local_rest#*:}"
    set +e
    run_output "$SEED" < "$local_fixture" \
        > "$TMP_DIR/c0.local-$local_name" \
        2> "$TMP_DIR/c0.local-$local_name.stderr"
    local_compile_status=$?
    set -e
    [[ "$local_compile_status" -eq 0 ]] || \
        fail_test "c0-local-$local_name-compile (expected 0, got $local_compile_status)"
    [[ ! -s "$TMP_DIR/c0.local-$local_name.stderr" ]] || \
        fail_test "c0-local-$local_name-compile-stderr"
    chmod 0755 "$TMP_DIR/c0.local-$local_name"
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.local-$local_name" >/dev/null
    local_status=$?
    set -e
    [[ "$local_status" -eq "$local_status_expected" ]] || \
        fail_test "c0-local-$local_name-run (expected $local_status_expected, got $local_status)"
done
run_output "$SEED" < "$LOCAL_CHAIN_FIXTURE" > "$TMP_DIR/c0.local-chain.two"
cmp -s "$TMP_DIR/c0.local-chain" "$TMP_DIR/c0.local-chain.two" || \
    fail_test "c0-local-deterministic-output"
printf 'PASS c0-multiple-local-statements-and-expressions\n'

for local_error_case in \
    "$DUPLICATE_LOCAL_FIXTURE:3:9:duplicate" \
    "$UNKNOWN_LOCAL_FIXTURE:2:12:unknown" \
    "$MALFORMED_LET_FIXTURE:2:11:malformed-let" \
    "$LOCAL_LIMIT_FIXTURE:10:9:limit"; do
    local_error_fixture="${local_error_case%%:*}"
    local_error_rest="${local_error_case#*:}"
    local_error_line="${local_error_rest%%:*}"
    local_error_rest="${local_error_rest#*:}"
    local_error_col="${local_error_rest%%:*}"
    local_error_name="${local_error_rest#*:}"
    set +e
    run_output "$SEED" < "$local_error_fixture" \
        > "$TMP_DIR/c0.local-$local_error_name.stdout" \
        2> "$TMP_DIR/c0.local-$local_error_name.stderr"
    local_error_status=$?
    set -e
    [[ "$local_error_status" -eq 1 ]] || \
        fail_test "c0-local-$local_error_name-status (expected 1, got $local_error_status)"
    [[ ! -s "$TMP_DIR/c0.local-$local_error_name.stdout" ]] || \
        fail_test "c0-local-$local_error_name-no-artifact"
    printf 'input:%s:%s: error[C0-001]: invalid C0 program\n' \
        "$local_error_line" "$local_error_col" \
        > "$TMP_DIR/c0.local-$local_error_name.expected"
    cmp -s "$TMP_DIR/c0.local-$local_error_name.expected" \
        "$TMP_DIR/c0.local-$local_error_name.stderr" || \
        fail_test "c0-local-$local_error_name-diagnostic"
done
printf 'PASS c0-local-binding-diagnostics-and-bound\n'

for write_case in \
    "$WRITE_TEXT_FIXTURE:9:text" \
    "$WRITE_BINARY_FIXTURE:7:binary" \
    "$WRITE_ZERO_ESCAPE_FIXTURE:0:zero-escape" \
    "$WRITE_CONCAT_FIXTURE:3:concat"; do
    write_fixture="${write_case%%:*}"
    write_rest="${write_case#*:}"
    write_status_expected="${write_rest%%:*}"
    write_name="${write_rest#*:}"
    set +e
    run_output "$SEED" < "$write_fixture" \
        > "$TMP_DIR/c0.write-$write_name" \
        2> "$TMP_DIR/c0.write-$write_name.compile.stderr"
    write_compile_status=$?
    set -e
    [[ "$write_compile_status" -eq 0 ]] || \
        fail_test "c0-write-$write_name-compile (expected 0, got $write_compile_status)"
    [[ ! -s "$TMP_DIR/c0.write-$write_name.compile.stderr" ]] || \
        fail_test "c0-write-$write_name-compile-stderr"
    case "$write_name" in
        text)
            write_hash_expected=cefa8d3934d4f9d50107d023ed68e12481fef372d117a99b56658daf9372f0a4
            ;;
        binary)
            write_hash_expected=fbb0b92dc79ad3b364ded05c8afb339d2c062ee4e133c559f814edc95ac5952d
            ;;
        zero-escape)
            write_hash_expected=d2a7d91b592141e256d8a01efeb4a6105c7e0b605cece2180578ae60488f8727
            ;;
        concat)
            write_hash_expected=d843551dd806eb2508e3197ccdc4a60995895e545819530aa60300704a59dab0
            ;;
    esac
    write_hash_actual="$(sha256sum "$TMP_DIR/c0.write-$write_name")"
    write_hash_actual="${write_hash_actual%% *}"
    [[ "$write_hash_actual" == "$write_hash_expected" ]] || \
        fail_test "c0-write-$write_name-artifact-identity"
    chmod 0755 "$TMP_DIR/c0.write-$write_name"
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.write-$write_name" \
        > "$TMP_DIR/c0.write-$write_name.stdout" \
        2> "$TMP_DIR/c0.write-$write_name.run.stderr"
    write_status=$?
    set -e
    [[ "$write_status" -eq "$write_status_expected" ]] || \
        fail_test "c0-write-$write_name-run (expected $write_status_expected, got $write_status)"
    [[ ! -s "$TMP_DIR/c0.write-$write_name.run.stderr" ]] || \
        fail_test "c0-write-$write_name-run-stderr"
done
printf 'NolQu-L\n' > "$TMP_DIR/c0.write-text.expected"
printf 'A\000B\n' > "$TMP_DIR/c0.write-binary.expected"
printf 'A\000B' > "$TMP_DIR/c0.write-zero-escape.expected"
printf 'ABC' > "$TMP_DIR/c0.write-concat.expected"
for write_name in text binary zero-escape concat; do
    cmp -s "$TMP_DIR/c0.write-$write_name.expected" \
        "$TMP_DIR/c0.write-$write_name.stdout" || \
        fail_test "c0-write-$write_name-output"
done
run_output "$SEED" < "$WRITE_CONCAT_FIXTURE" > "$TMP_DIR/c0.write-concat.two"
cmp -s "$TMP_DIR/c0.write-concat" "$TMP_DIR/c0.write-concat.two" || \
    fail_test "c0-write-deterministic-artifact"
printf 'PASS c0-write-string-runtime-output\n'

run_output "$SEED" < "$RUNTIME_INPUT_BYTE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-input.one" \
    2> "$TMP_DIR/c0.runtime-input.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-input.compile.stderr" ]] || \
    fail_test "c0-runtime-input-compile-stderr"
run_output "$SEED" < "$RUNTIME_INPUT_BYTE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-input.two"
cmp -s "$TMP_DIR/c0.runtime-input.one" "$TMP_DIR/c0.runtime-input.two" || \
    fail_test "c0-runtime-input-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-input.one"
set +e
printf 'A' | run_output_bounded 5 "$TMP_DIR/c0.runtime-input.one" >/dev/null
runtime_input_status=$?
set -e
[[ "$runtime_input_status" -eq 65 ]] || \
    fail_test "c0-runtime-input-byte-run (expected 65, got $runtime_input_status)"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-input.one" </dev/null >/dev/null
runtime_eof_status=$?
set -e
[[ "$runtime_eof_status" -eq 0 ]] || \
    fail_test "c0-runtime-input-eof-run (expected 0, got $runtime_eof_status)"
set +e
run_with_invalid_standard_fd 0 run_output_bounded 5 "$TMP_DIR/c0.runtime-input.one"  \
    > "$TMP_DIR/c0.runtime-input-error.stdout" \
    2> "$TMP_DIR/c0.runtime-input-error.stderr"
runtime_input_error_status=$?
set -e
[[ "$runtime_input_error_status" -eq 74 ]] || \
    fail_test "c0-runtime-input-error-run (expected 74, got $runtime_input_error_status)"
[[ ! -s "$TMP_DIR/c0.runtime-input-error.stdout" ]] || \
    fail_test "c0-runtime-input-error-no-stdout"
printf 'runtime: input_read failed\n' \
    > "$TMP_DIR/c0.runtime-input-error.expected"
cmp -s "$TMP_DIR/c0.runtime-input-error.expected" \
    "$TMP_DIR/c0.runtime-input-error.stderr" || \
    fail_test "c0-runtime-input-error-diagnostic"

runtime_broken_pipe_path="$TMP_DIR/c0.runtime-input.broken-pipe"
mkfifo "$runtime_broken_pipe_path"
(exec 3< "$runtime_broken_pipe_path") &
runtime_broken_pipe_pid=$!
exec {runtime_broken_pipe_fd}> "$runtime_broken_pipe_path"
wait "$runtime_broken_pipe_pid"
set +e
run_with_invalid_standard_fd 0 run_output_bounded 5 "$TMP_DIR/c0.runtime-input.one"  \
    >/dev/null 2>&$runtime_broken_pipe_fd
runtime_broken_pipe_status=$?
set -e
exec {runtime_broken_pipe_fd}>&-
[[ "$runtime_broken_pipe_status" -eq 74 ]] || \
    fail_test "c0-runtime-input-broken-pipe-status (expected 74, got $runtime_broken_pipe_status)"

run_output "$SEED" < "$RUNTIME_BYTE_STORE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-store" \
    2> "$TMP_DIR/c0.runtime-store.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-store.compile.stderr" ]] || \
    fail_test "c0-runtime-store-compile-stderr"
chmod 0755 "$TMP_DIR/c0.runtime-store"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-store" >/dev/null
runtime_store_status=$?
set -e
[[ "$runtime_store_status" -eq 77 ]] || \
    fail_test "c0-runtime-byte-store-run (expected 77, got $runtime_store_status)"

run_output "$SEED" < "$RUNTIME_STORE_COPY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-store-copy.one" \
    2> "$TMP_DIR/c0.runtime-store-copy.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-store-copy.stderr" ]] || \
    fail_test "c0-runtime-store-copy-compile-stderr"
run_output "$SEED" < "$RUNTIME_STORE_COPY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-store-copy.two"
cmp -s "$TMP_DIR/c0.runtime-store-copy.one" \
    "$TMP_DIR/c0.runtime-store-copy.two" || \
    fail_test "c0-runtime-store-copy-deterministic-artifact"
runtime_store_copy_hash="$(sha256sum "$TMP_DIR/c0.runtime-store-copy.one")"
runtime_store_copy_hash="${runtime_store_copy_hash%% *}"
[[ "$runtime_store_copy_hash" == \
    "a0f8310d9bd0b056350fcb5b52bb03d42c4824e2176b1e280fe1ce14d840d243" ]] || \
    fail_test "c0-runtime-store-copy-artifact-identity"
chmod 0755 "$TMP_DIR/c0.runtime-store-copy.one"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-store-copy.one" >/dev/null
runtime_store_copy_status=$?
set -e
[[ "$runtime_store_copy_status" -eq 77 ]] || \
    fail_test "c0-runtime-store-copy-run (expected 77, got $runtime_store_copy_status)"

run_output "$SEED" < "$RUNTIME_BYTE_LOAD_AT_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-load-at.one" \
    2> "$TMP_DIR/c0.runtime-byte-load-at.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-byte-load-at.compile.stderr" ]] || \
    fail_test "c0-runtime-byte-load-at-compile-stderr"
run_output "$SEED" < "$RUNTIME_BYTE_LOAD_AT_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-load-at.two"
cmp -s "$TMP_DIR/c0.runtime-byte-load-at.one" \
    "$TMP_DIR/c0.runtime-byte-load-at.two" || \
    fail_test "c0-runtime-byte-load-at-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-byte-load-at.one"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-byte-load-at.one" >/dev/null
runtime_byte_load_at_status=$?
set -e
[[ "$runtime_byte_load_at_status" -eq 90 ]] || \
    fail_test "c0-runtime-byte-load-at-run (expected 90, got $runtime_byte_load_at_status)"

run_output "$SEED" < "$RUNTIME_BYTE_LOAD_AT_SCAN_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-load-at-scan.one" \
    2> "$TMP_DIR/c0.runtime-byte-load-at-scan.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-byte-load-at-scan.compile.stderr" ]] || \
    fail_test "c0-runtime-byte-load-at-scan-compile-stderr"
run_output "$SEED" < "$RUNTIME_BYTE_LOAD_AT_SCAN_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-load-at-scan.two"
cmp -s "$TMP_DIR/c0.runtime-byte-load-at-scan.one" \
    "$TMP_DIR/c0.runtime-byte-load-at-scan.two" || \
    fail_test "c0-runtime-byte-load-at-scan-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-byte-load-at-scan.one"
printf 'fn main(){\nreturn 42}\n' \
    > "$TMP_DIR/c0.runtime-byte-load-at-scan.input"
run_output_bounded 5 "$TMP_DIR/c0.runtime-byte-load-at-scan.one" \
    < "$TMP_DIR/c0.runtime-byte-load-at-scan.input" \
    > "$TMP_DIR/c0.runtime-byte-load-at-scan.stdout" \
    2> "$TMP_DIR/c0.runtime-byte-load-at-scan.stderr"
cmp -s "$TMP_DIR/c0.runtime-byte-load-at-scan.input" \
    "$TMP_DIR/c0.runtime-byte-load-at-scan.stdout" || \
    fail_test "c0-runtime-byte-load-at-scan-output"
[[ ! -s "$TMP_DIR/c0.runtime-byte-load-at-scan.stderr" ]] || \
    fail_test "c0-runtime-byte-load-at-scan-stderr"

set +e
run_output "$SEED" < "$RUNTIME_BYTE_LOAD_AT_INVALID_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-load-at-invalid.stdout" \
    2> "$TMP_DIR/c0.runtime-byte-load-at-invalid.stderr"
runtime_byte_load_at_invalid_status=$?
set -e
[[ "$runtime_byte_load_at_invalid_status" -eq 1 ]] || \
    fail_test "c0-runtime-byte-load-at-invalid-status (expected 1, got $runtime_byte_load_at_invalid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-byte-load-at-invalid.stdout" ]] || \
    fail_test "c0-runtime-byte-load-at-invalid-no-artifact"
printf 'input:2:21: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-byte-load-at-invalid.expected"
cmp -s "$TMP_DIR/c0.runtime-byte-load-at-invalid.expected" \
    "$TMP_DIR/c0.runtime-byte-load-at-invalid.stderr" || \
    fail_test "c0-runtime-byte-load-at-invalid-diagnostic"
printf 'PASS c0-runtime-byte-load-at\n'

run_output "$SEED" < "$RUNTIME_BYTE_STORE_AT_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-store-at.one" \
    2> "$TMP_DIR/c0.runtime-byte-store-at.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-byte-store-at.compile.stderr" ]] || \
    fail_test "c0-runtime-byte-store-at-compile-stderr"
run_output "$SEED" < "$RUNTIME_BYTE_STORE_AT_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-store-at.two"
cmp -s "$TMP_DIR/c0.runtime-byte-store-at.one" \
    "$TMP_DIR/c0.runtime-byte-store-at.two" || \
    fail_test "c0-runtime-byte-store-at-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-byte-store-at.one"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-byte-store-at.one" >/dev/null
runtime_byte_store_at_status=$?
set -e
[[ "$runtime_byte_store_at_status" -eq 91 ]] || \
    fail_test "c0-runtime-byte-store-at-run (expected 91, got $runtime_byte_store_at_status)"

run_output "$SEED" < "$RUNTIME_BYTE_STORE_AT_COPY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-store-at-copy.one" \
    2> "$TMP_DIR/c0.runtime-byte-store-at-copy.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-byte-store-at-copy.compile.stderr" ]] || \
    fail_test "c0-runtime-byte-store-at-copy-compile-stderr"
run_output "$SEED" < "$RUNTIME_BYTE_STORE_AT_COPY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-store-at-copy.two"
cmp -s "$TMP_DIR/c0.runtime-byte-store-at-copy.one" \
    "$TMP_DIR/c0.runtime-byte-store-at-copy.two" || \
    fail_test "c0-runtime-byte-store-at-copy-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-byte-store-at-copy.one"
printf 'NQL!' > "$TMP_DIR/c0.runtime-byte-store-at-copy.input"
run_output_bounded 5 "$TMP_DIR/c0.runtime-byte-store-at-copy.one" \
    < "$TMP_DIR/c0.runtime-byte-store-at-copy.input" \
    > "$TMP_DIR/c0.runtime-byte-store-at-copy.stdout" \
    2> "$TMP_DIR/c0.runtime-byte-store-at-copy.stderr"
cmp -s "$TMP_DIR/c0.runtime-byte-store-at-copy.input" \
    "$TMP_DIR/c0.runtime-byte-store-at-copy.stdout" || \
    fail_test "c0-runtime-byte-store-at-copy-output"
[[ ! -s "$TMP_DIR/c0.runtime-byte-store-at-copy.stderr" ]] || \
    fail_test "c0-runtime-byte-store-at-copy-stderr"

set +e
run_output "$SEED" < "$RUNTIME_BYTE_STORE_AT_INVALID_FIXTURE" \
    > "$TMP_DIR/c0.runtime-byte-store-at-invalid.stdout" \
    2> "$TMP_DIR/c0.runtime-byte-store-at-invalid.stderr"
runtime_byte_store_at_invalid_status=$?
set -e
[[ "$runtime_byte_store_at_invalid_status" -eq 1 ]] || \
    fail_test "c0-runtime-byte-store-at-invalid-status (expected 1, got $runtime_byte_store_at_invalid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-byte-store-at-invalid.stdout" ]] || \
    fail_test "c0-runtime-byte-store-at-invalid-no-artifact"
printf 'input:2:22: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-byte-store-at-invalid.expected"
cmp -s "$TMP_DIR/c0.runtime-byte-store-at-invalid.expected" \
    "$TMP_DIR/c0.runtime-byte-store-at-invalid.stderr" || \
    fail_test "c0-runtime-byte-store-at-invalid-diagnostic"
printf 'PASS c0-runtime-byte-store-at\n'

run_output "$SEED" < "$RUNTIME_STORE_WRAP_FIXTURE" \
    > "$TMP_DIR/c0.runtime-store-wrap.one" \
    2> "$TMP_DIR/c0.runtime-store-wrap.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-store-wrap.stderr" ]] || \
    fail_test "c0-runtime-store-wrap-compile-stderr"
run_output "$SEED" < "$RUNTIME_STORE_WRAP_FIXTURE" \
    > "$TMP_DIR/c0.runtime-store-wrap.two"
cmp -s "$TMP_DIR/c0.runtime-store-wrap.one" \
    "$TMP_DIR/c0.runtime-store-wrap.two" || \
    fail_test "c0-runtime-store-wrap-deterministic-artifact"
runtime_store_wrap_hash="$(sha256sum "$TMP_DIR/c0.runtime-store-wrap.one")"
runtime_store_wrap_hash="${runtime_store_wrap_hash%% *}"
[[ "$runtime_store_wrap_hash" == \
    "4796953d7990479f78154e87b78e69b3b9cc206c1e738ca439ceb0f70b39df3a" ]] || \
    fail_test "c0-runtime-store-wrap-artifact-identity"
chmod 0755 "$TMP_DIR/c0.runtime-store-wrap.one"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-store-wrap.one" >/dev/null
runtime_store_wrap_status=$?
set -e
[[ "$runtime_store_wrap_status" -eq 255 ]] || \
    fail_test "c0-runtime-store-wrap-run (expected 255, got $runtime_store_wrap_status)"
printf 'PASS c0-runtime-byte-assignment\n'

run_output "$SEED" < "$RUNTIME_ASSERT_RANGE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-assert-range.one" \
    2> "$TMP_DIR/c0.runtime-assert-range.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-assert-range.compile.stderr" ]] || \
    fail_test "c0-runtime-assert-range-compile-stderr"
run_output "$SEED" < "$RUNTIME_ASSERT_RANGE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-assert-range.two"
cmp -s "$TMP_DIR/c0.runtime-assert-range.one" \
    "$TMP_DIR/c0.runtime-assert-range.two" || \
    fail_test "c0-runtime-assert-range-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-assert-range.one"
set +e
printf '7' | run_output_bounded 5 "$TMP_DIR/c0.runtime-assert-range.one" \
    > "$TMP_DIR/c0.runtime-assert-range.valid.stdout" \
    2> "$TMP_DIR/c0.runtime-assert-range.valid.stderr"
runtime_assert_valid_status=$?
set -e
[[ "$runtime_assert_valid_status" -eq 55 ]] || \
    fail_test "c0-runtime-assert-range-valid-status (expected 55, got $runtime_assert_valid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-assert-range.valid.stdout" ]] || \
    fail_test "c0-runtime-assert-range-valid-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-assert-range.valid.stderr" ]] || \
    fail_test "c0-runtime-assert-range-valid-stderr"
printf 'runtime: invalid source\n' > "$TMP_DIR/c0.runtime-assert-range.expected"
set +e
printf 'x' | run_output_bounded 5 "$TMP_DIR/c0.runtime-assert-range.one" \
    > "$TMP_DIR/c0.runtime-assert-range.invalid.stdout" \
    2> "$TMP_DIR/c0.runtime-assert-range.invalid.stderr"
runtime_assert_invalid_status=$?
set -e
[[ "$runtime_assert_invalid_status" -eq 1 ]] || \
    fail_test "c0-runtime-assert-range-invalid-status (expected 1, got $runtime_assert_invalid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-assert-range.invalid.stdout" ]] || \
    fail_test "c0-runtime-assert-range-invalid-stdout"
cmp -s "$TMP_DIR/c0.runtime-assert-range.expected" \
    "$TMP_DIR/c0.runtime-assert-range.invalid.stderr" || \
    fail_test "c0-runtime-assert-range-invalid-diagnostic"
set +e
printf 'x' | run_with_invalid_standard_fd 2 run_output_bounded 5 "$TMP_DIR/c0.runtime-assert-range.one" \
    >/dev/null
runtime_assert_closed_stderr_status=$?
set -e
[[ "$runtime_assert_closed_stderr_status" -eq 1 ]] || \
    fail_test "c0-runtime-assert-range-closed-stderr-status (expected 1, got $runtime_assert_closed_stderr_status)"

set +e
run_output "$SEED" < "$RUNTIME_ASSERT_RANGE_INVALID_FIXTURE" \
    > "$TMP_DIR/c0.runtime-assert-range-bounds.stdout" \
    2> "$TMP_DIR/c0.runtime-assert-range-bounds.stderr"
runtime_assert_bounds_status=$?
set -e
[[ "$runtime_assert_bounds_status" -eq 1 ]] || \
    fail_test "c0-runtime-assert-range-bounds-status (expected 1, got $runtime_assert_bounds_status)"
[[ ! -s "$TMP_DIR/c0.runtime-assert-range-bounds.stdout" ]] || \
    fail_test "c0-runtime-assert-range-bounds-no-artifact"
printf 'input:2:32: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-assert-range-bounds.expected"
cmp -s "$TMP_DIR/c0.runtime-assert-range-bounds.expected" \
    "$TMP_DIR/c0.runtime-assert-range-bounds.stderr" || \
    fail_test "c0-runtime-assert-range-bounds-diagnostic"
printf 'PASS c0-runtime-byte-assert-range\n'

set +e
run_output "$SEED" < "$RUNTIME_PARSE_U8_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-u8.one" \
    2> "$TMP_DIR/c0.runtime-parse-u8.compile.stderr"
runtime_parse_compile_status=$?
set -e
[[ "$runtime_parse_compile_status" -eq 0 ]] || \
    fail_test "c0-runtime-parse-u8-compile (expected 0, got $runtime_parse_compile_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-u8.compile.stderr" ]] || \
    fail_test "c0-runtime-parse-u8-compile-stderr"
run_output "$SEED" < "$RUNTIME_PARSE_U8_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-u8.two"
cmp -s "$TMP_DIR/c0.runtime-parse-u8.one" \
    "$TMP_DIR/c0.runtime-parse-u8.two" || \
    fail_test "c0-runtime-parse-u8-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-parse-u8.one"
for runtime_parse_valid in 0:0 7:7 00:0 42:42 099:99 100:100 255:255; do
    runtime_parse_source="${runtime_parse_valid%%:*}"
    runtime_parse_expected="${runtime_parse_valid#*:}"
    set +e
    printf '%s\n' "$runtime_parse_source" | \
        run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-u8.one" \
        > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_source.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_source.stderr"
    runtime_parse_status=$?
    set -e
    [[ "$runtime_parse_status" -eq "$runtime_parse_expected" ]] || \
        fail_test "c0-runtime-parse-u8-$runtime_parse_source-run (expected $runtime_parse_expected, got $runtime_parse_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_source.stdout" ]] || \
        fail_test "c0-runtime-parse-u8-$runtime_parse_source-stdout"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_source.stderr" ]] || \
        fail_test "c0-runtime-parse-u8-$runtime_parse_source-stderr"
done

printf 'runtime: invalid source\n' > "$TMP_DIR/c0.runtime-parse-u8.expected"
for runtime_parse_invalid in empty nondigit overflow missing-newline trailing four-digit; do
    case "$runtime_parse_invalid" in
        empty) : > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" ;;
        nondigit) printf 'x\n' > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" ;;
        overflow) printf '256\n' > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" ;;
        missing-newline) printf '42' > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" ;;
        trailing) printf '42\nx' > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" ;;
        four-digit) printf '0255\n' > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" ;;
    esac
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-u8.one" \
        < "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.input" \
        > "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.stderr"
    runtime_parse_status=$?
    set -e
    [[ "$runtime_parse_status" -eq 1 ]] || \
        fail_test "c0-runtime-parse-u8-$runtime_parse_invalid-status (expected 1, got $runtime_parse_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.stdout" ]] || \
        fail_test "c0-runtime-parse-u8-$runtime_parse_invalid-stdout"
    cmp -s "$TMP_DIR/c0.runtime-parse-u8.expected" \
        "$TMP_DIR/c0.runtime-parse-u8.$runtime_parse_invalid.stderr" || \
        fail_test "c0-runtime-parse-u8-$runtime_parse_invalid-diagnostic"
done
set +e
run_output "$SEED" < "$RUNTIME_PARSE_U8_INVALID_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-u8-range.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-u8-range.stderr"
runtime_parse_range_status=$?
set -e
[[ "$runtime_parse_range_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-u8-range-status (expected 1, got $runtime_parse_range_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-u8-range.stdout" ]] || \
    fail_test "c0-runtime-parse-u8-range-no-artifact"
printf 'input:2:25: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-parse-u8-range.expected"
cmp -s "$TMP_DIR/c0.runtime-parse-u8-range.expected" \
    "$TMP_DIR/c0.runtime-parse-u8-range.stderr" || \
    fail_test "c0-runtime-parse-u8-range-diagnostic"
printf 'PASS c0-runtime-byte-parse-u8\n'

set +e
run_output "$SEED" < "$RUNTIME_PARSE_U8_THEN_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-u8-then.one" \
    2> "$TMP_DIR/c0.runtime-parse-u8-then.compile.stderr"
runtime_parse_then_compile_status=$?
set -e
[[ "$runtime_parse_then_compile_status" -eq 0 ]] || \
    fail_test "c0-runtime-parse-u8-then-compile (expected 0, got $runtime_parse_then_compile_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-u8-then.compile.stderr" ]] || \
    fail_test "c0-runtime-parse-u8-then-compile-stderr"
run_output "$SEED" < "$RUNTIME_PARSE_U8_THEN_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-u8-then.two"
cmp -s "$TMP_DIR/c0.runtime-parse-u8-then.one" \
    "$TMP_DIR/c0.runtime-parse-u8-then.two" || \
    fail_test "c0-runtime-parse-u8-then-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-parse-u8-then.one"
for runtime_parse_then_valid in 0:0 7:7 00:0 42:42 099:99 100:100 255:255; do
    runtime_parse_then_source="${runtime_parse_then_valid%%:*}"
    runtime_parse_then_expected="${runtime_parse_then_valid#*:}"
    set +e
    printf '%s}\n' "$runtime_parse_then_source" | \
        run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-u8-then.one" \
        > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_source.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_source.stderr"
    runtime_parse_then_status=$?
    set -e
    [[ "$runtime_parse_then_status" -eq "$runtime_parse_then_expected" ]] || \
        fail_test "c0-runtime-parse-u8-then-$runtime_parse_then_source-run (expected $runtime_parse_then_expected, got $runtime_parse_then_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_source.stdout" ]] || \
        fail_test "c0-runtime-parse-u8-then-$runtime_parse_then_source-stdout"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_source.stderr" ]] || \
        fail_test "c0-runtime-parse-u8-then-$runtime_parse_then_source-stderr"
done

printf 'runtime: invalid source\n' > "$TMP_DIR/c0.runtime-parse-u8-then.expected"
for runtime_parse_then_invalid in \
    empty no-digits nondigit wrong-terminator overflow missing-terminator \
    missing-newline trailing four-digit; do
    case "$runtime_parse_then_invalid" in
        empty) : > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        no-digits) printf '}\n' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        nondigit) printf 'x}\n' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        wrong-terminator) printf '42]\n' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        overflow) printf '256}\n' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        missing-terminator) printf '42\n' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        missing-newline) printf '42}' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        trailing) printf '42}\nx' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
        four-digit) printf '0255}\n' > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" ;;
    esac
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-u8-then.one" \
        < "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.input" \
        > "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.stderr"
    runtime_parse_then_status=$?
    set -e
    [[ "$runtime_parse_then_status" -eq 1 ]] || \
        fail_test "c0-runtime-parse-u8-then-$runtime_parse_then_invalid-status (expected 1, got $runtime_parse_then_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.stdout" ]] || \
        fail_test "c0-runtime-parse-u8-then-$runtime_parse_then_invalid-stdout"
    cmp -s "$TMP_DIR/c0.runtime-parse-u8-then.expected" \
        "$TMP_DIR/c0.runtime-parse-u8-then.$runtime_parse_then_invalid.stderr" || \
        fail_test "c0-runtime-parse-u8-then-$runtime_parse_then_invalid-diagnostic"
done
set +e
run_output "$SEED" < "$RUNTIME_PARSE_U8_THEN_INVALID_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-u8-then-range.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-u8-then-range.stderr"
runtime_parse_then_range_status=$?
set -e
[[ "$runtime_parse_then_range_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-u8-then-range-status (expected 1, got $runtime_parse_then_range_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-u8-then-range.stdout" ]] || \
    fail_test "c0-runtime-parse-u8-then-range-no-artifact"
printf 'input:2:35: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-parse-u8-then-range.expected"
cmp -s "$TMP_DIR/c0.runtime-parse-u8-then-range.expected" \
    "$TMP_DIR/c0.runtime-parse-u8-then-range.stderr" || \
    fail_test "c0-runtime-parse-u8-then-range-diagnostic"
printf 'PASS c0-runtime-byte-parse-u8-then\n'

set +e
run_output "$SEED" < "$RUNTIME_PARSE_STMTS_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts.one" \
    2> "$TMP_DIR/c0.runtime-parse-stmts.compile.stderr"
runtime_parse_stmts_compile_status=$?
set -e
[[ "$runtime_parse_stmts_compile_status" -eq 0 ]] || \
    fail_test "c0-runtime-parse-stmts-compile (expected 0, got $runtime_parse_stmts_compile_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts.compile.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-compile-stderr"
run_output "$SEED" < "$RUNTIME_PARSE_STMTS_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts.two"
cmp -s "$TMP_DIR/c0.runtime-parse-stmts.one" \
    "$TMP_DIR/c0.runtime-parse-stmts.two" || \
    fail_test "c0-runtime-parse-stmts-deterministic-artifact"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts.one"
for runtime_parse_stmts_valid in \
    direct-return full-return one-store three-stores input-read parse-stmts \
    parse-stmts-store parse-stmts-two-stores while-clear-after-parser; do
    case "$runtime_parse_stmts_valid" in
        direct-return)
            runtime_parse_stmts_expected=255
            printf 'return 255}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        full-return)
            runtime_parse_stmts_expected=42
            printf 'fn main(){\nreturn 42}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        one-store)
            runtime_parse_stmts_expected=42
            printf 'byte_store(3,9)\nreturn 42}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        three-stores)
            runtime_parse_stmts_expected=7
            printf 'byte_store(0,0)\nbyte_store(255,255)\nbyte_store(42,099)\nreturn 7}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        input-read)
            runtime_parse_stmts_expected=7
            printf 'fn main(){\nbyte_store(1,2)\ninput_read(32,96)\nreturn 7}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        parse-stmts)
            runtime_parse_stmts_expected=7
            printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nreturn 7}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        parse-stmts-store)
            runtime_parse_stmts_expected=7
            printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nbyte_store(1,2)\nreturn 7}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        parse-stmts-two-stores)
            runtime_parse_stmts_expected=7
            printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nbyte_store(1,2)\nbyte_store(2,3)\nreturn 7}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
        while-clear-after-parser)
            runtime_parse_stmts_expected=7
            printf 'input_read(32,96)\nbyte_parse_stmts(32,0)\nwhile byte_load(1) {\nbyte_store(1,0)\n}\nreturn 7}\n' \
                > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input"
            ;;
    esac
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts.one" \
        < "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.input" \
        > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.stderr"
    runtime_parse_stmts_status=$?
    set -e
    [[ "$runtime_parse_stmts_status" -eq "$runtime_parse_stmts_expected" ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_valid-run (expected $runtime_parse_stmts_expected, got $runtime_parse_stmts_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.stdout" ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_valid-stdout"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_valid.stderr" ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_valid-stderr"
done

run_output "$SEED" < "$RUNTIME_PARSE_STMTS_INPUT_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-input"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts-input"
set +e
printf 'fn main(){\ninput_read(32,96)\nreturn 0}\n' | \
    run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-input.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-input.stderr"
runtime_parse_stmts_input_status=$?
set -e
[[ "$runtime_parse_stmts_input_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-input-flag (expected 1, got $runtime_parse_stmts_input_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-input.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-input-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-input.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-input-stderr"

run_output "$SEED" < "$RUNTIME_PARSE_STMTS_PARSER_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts-parser"
set +e
printf 'fn main(){\ninput_read(32,96)\nbyte_parse_stmts(32,0)\nreturn 0}\n' | \
    run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-parser" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-parser.stderr"
runtime_parse_stmts_parser_status=$?
set -e
[[ "$runtime_parse_stmts_parser_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-parser-flag (expected 1, got $runtime_parse_stmts_parser_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-stderr"

printf 'runtime: invalid source\n' > "$TMP_DIR/c0.runtime-parse-stmts.expected"
run_output "$SEED" < "$RUNTIME_PARSE_STMTS_RETURN_EMITTER_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts-return-emitter"
sed -n '1,9p' "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.input"
printf 'return 0}\n' >> "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.input"
printf '\0\0\1\1\1' \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.expected"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-return-emitter" \
    < "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.stderr"
runtime_parse_stmts_return_emitter_status=$?
set -e
[[ "$runtime_parse_stmts_return_emitter_status" -eq 0 ]] || \
    fail_test "c0-runtime-parse-stmts-return-emitter-status (expected 0, got $runtime_parse_stmts_return_emitter_status)"
cmp -s "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.expected" \
    "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.stdout" || \
    fail_test "c0-runtime-parse-stmts-return-emitter-metadata"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-return-emitter-stderr"
readelf -lW "$TMP_DIR/c0.runtime-parse-stmts-return-emitter" \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.readelf"
grep -Eq 'LOAD +0x[0-9a-f]+ +0x0000000000403000 +0x0000000000403000 +0x000000 +0x004000 +RW +0x1000' \
    "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.readelf" || \
    fail_test "c0-runtime-parse-stmts-return-emitter-private-bss"

sed '0,/\\x7fELF/s//\\x7eELF/' \
    "$TMP_DIR/c0.runtime-parse-stmts-return-emitter.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter-invalid.input"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-return-emitter" \
    < "$TMP_DIR/c0.runtime-parse-stmts-return-emitter-invalid.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-return-emitter-invalid.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-return-emitter-invalid.stderr"
runtime_parse_stmts_return_emitter_invalid_status=$?
set -e
[[ "$runtime_parse_stmts_return_emitter_invalid_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-return-emitter-invalid-status (expected 1, got $runtime_parse_stmts_return_emitter_invalid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-return-emitter-invalid.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-return-emitter-invalid-no-output"
cmp -s "$TMP_DIR/c0.runtime-parse-stmts.expected" \
    "$TMP_DIR/c0.runtime-parse-stmts-return-emitter-invalid.stderr" || \
    fail_test "c0-runtime-parse-stmts-return-emitter-invalid-diagnostic"

chmod 0755 "$TMP_DIR/c0.successor.parse-stmts.direct"
sed -n '1,10p' "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.input"
append_canonical_write_lines \
    "$TMP_DIR/c0.successor.parse-stmts.direct" \
    "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.input"
printf 'byte_store(3,0)\nbyte_store(2,0)\n}\nreturn 0}\n' \
    >> "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.input"
set +e
run_output_bounded 5 "$TMP_DIR/c0.successor.parse-stmts.direct" \
    < "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.stderr"
runtime_parse_stmts_parser_emitter_canonical_status=$?
set -e
[[ "$runtime_parse_stmts_parser_emitter_canonical_status" -eq 0 ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-canonical-status (expected 0, got $runtime_parse_stmts_parser_emitter_canonical_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-canonical-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-canonical.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-canonical-stderr"

run_output "$SEED" < "$RUNTIME_PARSE_STMTS_PARSER_EMITTER_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter"
sed -n '1,10p' "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.input"
append_canonical_write_lines \
    "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter" \
    "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.input"
printf 'byte_store(3,0)\nbyte_store(2,0)\n}\nreturn 0}\n' \
    >> "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.input"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter" \
    < "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.stderr"
runtime_parse_stmts_parser_emitter_status=$?
set -e
[[ "$runtime_parse_stmts_parser_emitter_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-flag (expected 1, got $runtime_parse_stmts_parser_emitter_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-stderr"
readelf -lW "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.readelf"
grep -Eq 'LOAD +0x[0-9a-f]+ +0x0000000000403000 +0x0000000000403000 +0x000000 +0x004000 +RW +0x1000' \
    "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.readelf" || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-private-bss"

awk 'NR == 11 { sub(/\\x7fELF/, "\\x7eELF") } { print }' \
    "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-invalid.input"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter" \
    < "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-invalid.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-invalid.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-invalid.stderr"
runtime_parse_stmts_parser_emitter_invalid_status=$?
set -e
[[ "$runtime_parse_stmts_parser_emitter_invalid_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-invalid-status (expected 1, got $runtime_parse_stmts_parser_emitter_invalid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-invalid.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-invalid-no-output"
cmp -s "$TMP_DIR/c0.runtime-parse-stmts.expected" \
    "$TMP_DIR/c0.runtime-parse-stmts-parser-emitter-invalid.stderr" || \
    fail_test "c0-runtime-parse-stmts-parser-emitter-invalid-diagnostic"

run_output "$SEED" < "$RUNTIME_PARSE_STMTS_INPUT_EMITTER_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-input-emitter"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts-input-emitter"
sed -n '1,10p' "$SUCCESSOR_SOURCE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.prefix"
append_canonical_write_lines \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter" \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.prefix"
printf 'byte_store(3,0)\nbyte_store(2,0)\n}\n' \
    >> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.prefix"
awk '
    $0 == "while byte_load(2) {" { capture = 1 }
    capture { print }
    capture && $0 == "}" { exit }
' "$SUCCESSOR_SOURCE" > "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.tail"
grep -Fxq 'while byte_load(2) {' \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.tail" || \
    fail_test "c0-runtime-parse-stmts-input-emitter-tail"
cp "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.prefix" \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.input"
sed -n '1,$p' "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.tail" \
    >> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.input"
printf 'return 0}\n' >> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.input"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-input-emitter" \
    < "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.stderr"
runtime_parse_stmts_input_emitter_status=$?
set -e
[[ "$runtime_parse_stmts_input_emitter_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-input-emitter-flag (expected 1, got $runtime_parse_stmts_input_emitter_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-input-emitter-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-input-emitter-stderr"

cp "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.prefix" \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.input"
sed '0,/\\x7fELF/s//\\x7eELF/' \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter.tail" \
    >> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.input"
printf 'return 0}\n' \
    >> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.input"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-input-emitter" \
    < "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.input" \
    > "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.stderr"
runtime_parse_stmts_input_emitter_invalid_status=$?
set -e
[[ "$runtime_parse_stmts_input_emitter_invalid_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-input-emitter-invalid-status (expected 1, got $runtime_parse_stmts_input_emitter_invalid_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-input-emitter-invalid-no-output"
cmp -s "$TMP_DIR/c0.runtime-parse-stmts.expected" \
    "$TMP_DIR/c0.runtime-parse-stmts-input-emitter-invalid.stderr" || \
    fail_test "c0-runtime-parse-stmts-input-emitter-invalid-diagnostic"

run_output "$SEED" < "$RUNTIME_PARSE_STMTS_BOUNDARY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-parse-stmts-boundary" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-boundary.compile.stderr"
[[ -s "$TMP_DIR/c0.runtime-parse-stmts-boundary" ]] || \
    fail_test "c0-runtime-parse-stmts-boundary-artifact"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-boundary.compile.stderr" ]] || \
    fail_test "c0-runtime-parse-stmts-boundary-compile-stderr"
chmod 0755 "$TMP_DIR/c0.runtime-parse-stmts-boundary"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts-boundary" \
    > "$TMP_DIR/c0.runtime-parse-stmts-boundary.stdout" \
    2> "$TMP_DIR/c0.runtime-parse-stmts-boundary.stderr"
runtime_parse_stmts_boundary_status=$?
set -e
[[ "$runtime_parse_stmts_boundary_status" -eq 1 ]] || \
    fail_test "c0-runtime-parse-stmts-boundary-run (expected 1, got $runtime_parse_stmts_boundary_status)"
[[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-boundary.stdout" ]] || \
    fail_test "c0-runtime-parse-stmts-boundary-stdout"
printf 'runtime: invalid source\n' \
    > "$TMP_DIR/c0.runtime-parse-stmts-boundary.expected"
cmp -s "$TMP_DIR/c0.runtime-parse-stmts-boundary.expected" \
    "$TMP_DIR/c0.runtime-parse-stmts-boundary.stderr" || \
    fail_test "c0-runtime-parse-stmts-boundary-diagnostic"

for runtime_parse_stmts_invalid in \
    empty wrong-statement missing-left-paren missing-comma first-overflow \
    second-overflow missing-store-newline bad-return return-overflow \
    fourth-store trailing input-wrong-count input-leading-zero-offset \
    input-leading-zero-count input-duplicate store-after-input \
    parser-without-input parser-wrong-source parser-wrong-destination \
    parser-leading-zero-source parser-leading-zero-destination \
    parser-duplicate parser-store-third while-wrong-condition \
    while-wrong-body while-missing-close; do
    case "$runtime_parse_stmts_invalid" in
        empty) : > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        wrong-statement) printf 'input_read(0,1)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        missing-left-paren) printf 'byte_store 1,2)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        missing-comma) printf 'byte_store(1 2)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        first-overflow) printf 'byte_store(256,2)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        second-overflow) printf 'byte_store(1,256)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        missing-store-newline) printf 'byte_store(1,2)return 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        bad-return) printf 'ret 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        return-overflow) printf 'return 256}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        fourth-store) printf 'byte_store(1,1)\nbyte_store(2,2)\nbyte_store(3,3)\nbyte_store(4,4)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        trailing) printf 'return 0}\nx' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        input-wrong-count) printf 'input_read(32,95)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        input-leading-zero-offset) printf 'input_read(032,96)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        input-leading-zero-count) printf 'input_read(32,096)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        input-duplicate) printf 'input_read(32,96)\ninput_read(32,96)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        store-after-input) printf 'input_read(32,96)\nbyte_store(1,2)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-without-input) printf 'byte_parse_stmts(32,0)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-wrong-source) printf 'input_read(32,96)\nbyte_parse_stmts(0,0)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-wrong-destination) printf 'input_read(32,96)\nbyte_parse_stmts(32,1)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-leading-zero-source) printf 'input_read(32,96)\nbyte_parse_stmts(032,0)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-leading-zero-destination) printf 'input_read(32,96)\nbyte_parse_stmts(32,00)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-duplicate) printf 'input_read(32,96)\nbyte_parse_stmts(32,0)\nbyte_parse_stmts(32,0)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        parser-store-third) printf 'input_read(32,96)\nbyte_parse_stmts(32,0)\nbyte_store(4,184)\nbyte_store(5,60)\nbyte_store(9,15)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        while-wrong-condition) printf 'while byte_load(2) {\nbyte_store(1,0)\n}\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        while-wrong-body) printf 'while byte_load(1) {\nbyte_store(1,1)\n}\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
        while-missing-close) printf 'while byte_load(1) {\nbyte_store(1,0)\nreturn 0}\n' > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" ;;
    esac
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.runtime-parse-stmts.one" \
        < "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.input" \
        > "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.stderr"
    runtime_parse_stmts_status=$?
    set -e
    [[ "$runtime_parse_stmts_status" -eq 1 ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_invalid-status (expected 1, got $runtime_parse_stmts_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.stdout" ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_invalid-stdout"
    cmp -s "$TMP_DIR/c0.runtime-parse-stmts.expected" \
        "$TMP_DIR/c0.runtime-parse-stmts.$runtime_parse_stmts_invalid.stderr" || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_invalid-diagnostic"
done
for runtime_parse_stmts_range_case in \
    "$RUNTIME_PARSE_STMTS_INVALID_FIXTURE:source:27" \
    "$RUNTIME_PARSE_STMTS_DESTINATION_INVALID_FIXTURE:destination:28"; do
    runtime_parse_stmts_range_fixture="${runtime_parse_stmts_range_case%%:*}"
    runtime_parse_stmts_range_detail="${runtime_parse_stmts_range_case#*:}"
    runtime_parse_stmts_range_name="${runtime_parse_stmts_range_detail%%:*}"
    runtime_parse_stmts_range_column="${runtime_parse_stmts_range_detail#*:}"
    set +e
    run_output "$SEED" < "$runtime_parse_stmts_range_fixture" \
        > "$TMP_DIR/c0.runtime-parse-stmts-range-$runtime_parse_stmts_range_name.stdout" \
        2> "$TMP_DIR/c0.runtime-parse-stmts-range-$runtime_parse_stmts_range_name.stderr"
    runtime_parse_stmts_range_status=$?
    set -e
    [[ "$runtime_parse_stmts_range_status" -eq 1 ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_range_name-range-status (expected 1, got $runtime_parse_stmts_range_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-parse-stmts-range-$runtime_parse_stmts_range_name.stdout" ]] || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_range_name-range-no-artifact"
    printf 'input:2:%s: error[C0-001]: invalid C0 program\n' \
        "$runtime_parse_stmts_range_column" \
        > "$TMP_DIR/c0.runtime-parse-stmts-range.expected"
    cmp -s "$TMP_DIR/c0.runtime-parse-stmts-range.expected" \
        "$TMP_DIR/c0.runtime-parse-stmts-range-$runtime_parse_stmts_range_name.stderr" || \
        fail_test "c0-runtime-parse-stmts-$runtime_parse_stmts_range_name-range-diagnostic"
done
printf 'PASS c0-runtime-byte-parse-stmts\n'

for runtime_while_case in \
    "$RUNTIME_WHILE_FIXTURE:0:decrement" \
    "$RUNTIME_WHILE_ZERO_FIXTURE:0:zero" \
    "$RUNTIME_WHILE_SEQUENTIAL_FIXTURE:0:sequential"; do
    runtime_while_fixture="${runtime_while_case%%:*}"
    runtime_while_rest="${runtime_while_case#*:}"
    runtime_while_expected="${runtime_while_rest%%:*}"
    runtime_while_name="${runtime_while_rest#*:}"
    run_output "$SEED" < "$runtime_while_fixture" \
        > "$TMP_DIR/c0.runtime-while-$runtime_while_name.one" \
        2> "$TMP_DIR/c0.runtime-while-$runtime_while_name.stderr"
    [[ ! -s "$TMP_DIR/c0.runtime-while-$runtime_while_name.stderr" ]] || \
        fail_test "c0-runtime-while-$runtime_while_name-compile-stderr"
    run_output "$SEED" < "$runtime_while_fixture" \
        > "$TMP_DIR/c0.runtime-while-$runtime_while_name.two"
    cmp -s "$TMP_DIR/c0.runtime-while-$runtime_while_name.one" \
        "$TMP_DIR/c0.runtime-while-$runtime_while_name.two" || \
        fail_test "c0-runtime-while-$runtime_while_name-deterministic-artifact"
    runtime_while_hash="$(sha256sum "$TMP_DIR/c0.runtime-while-$runtime_while_name.one")"
    runtime_while_hash="${runtime_while_hash%% *}"
    case "$runtime_while_name" in
        decrement)
            runtime_while_hash_expected=27a36045a38b957f1bb7b277e31842338f0de8fb620a14075325eff45601c930
            ;;
        zero)
            runtime_while_hash_expected=0c0c7ee6a9aadf3337b94fedd1ec56f95672c4f303f3dfa09cc3d6436a23393a
            ;;
        sequential)
            runtime_while_hash_expected=b6c2d660810c4b5bf74c809e3412026f7abe6936e9bd0b8a8075ffed2734463b
            ;;
    esac
    [[ "$runtime_while_hash" == "$runtime_while_hash_expected" ]] || \
        fail_test "c0-runtime-while-$runtime_while_name-artifact-identity"
    chmod 0755 "$TMP_DIR/c0.runtime-while-$runtime_while_name.one"
    set +e
    run_output_bounded 5 "$TMP_DIR/c0.runtime-while-$runtime_while_name.one" \
        >/dev/null
    runtime_while_status=$?
    set -e
    [[ "$runtime_while_status" -eq "$runtime_while_expected" ]] || \
        fail_test "c0-runtime-while-$runtime_while_name-run (expected $runtime_while_expected, got $runtime_while_status)"
done
printf 'PASS c0-runtime-while-control-flow\n'

set +e
run_output "$SEED" < "$RUNTIME_NESTED_WHILE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-nested-while.stdout" \
    2> "$TMP_DIR/c0.runtime-nested-while.stderr"
runtime_nested_while_status=$?
set -e
[[ "$runtime_nested_while_status" -eq 1 ]] || \
    fail_test "c0-runtime-nested-while-status (expected 1, got $runtime_nested_while_status)"
[[ ! -s "$TMP_DIR/c0.runtime-nested-while.stdout" ]] || \
    fail_test "c0-runtime-nested-while-no-artifact"
printf 'input:4:9: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-nested-while.expected"
cmp -s "$TMP_DIR/c0.runtime-nested-while.expected" \
    "$TMP_DIR/c0.runtime-nested-while.stderr" || \
    fail_test "c0-runtime-nested-while-diagnostic"
printf 'PASS c0-runtime-nested-while-rejected\n'

set +e
run_output "$SEED" < "$RUNTIME_WHILE_LET_FIXTURE" \
    > "$TMP_DIR/c0.runtime-while-let.stdout" \
    2> "$TMP_DIR/c0.runtime-while-let.stderr"
runtime_while_let_status=$?
set -e
[[ "$runtime_while_let_status" -eq 1 ]] || \
    fail_test "c0-runtime-while-let-status (expected 1, got $runtime_while_let_status)"
[[ ! -s "$TMP_DIR/c0.runtime-while-let.stdout" ]] || \
    fail_test "c0-runtime-while-let-no-artifact"
printf 'input:3:9: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-while-let.expected"
cmp -s "$TMP_DIR/c0.runtime-while-let.expected" \
    "$TMP_DIR/c0.runtime-while-let.stderr" || \
    fail_test "c0-runtime-while-let-diagnostic"
printf 'PASS c0-runtime-loop-body-subset-enforced\n'

for runtime_output_case in \
    "$RUNTIME_OUTPUT_ROUNDTRIP_FIXTURE:roundtrip" \
    "$RUNTIME_OUTPUT_MEMORY_FIXTURE:memory" \
    "$RUNTIME_OUTPUT_ZERO_FIXTURE:zero" \
    "$RUNTIME_OUTPUT_WHILE_FIXTURE:while"; do
    runtime_output_fixture="${runtime_output_case%%:*}"
    runtime_output_name="${runtime_output_case#*:}"
    run_output "$SEED" < "$runtime_output_fixture" \
        > "$TMP_DIR/c0.runtime-output-$runtime_output_name.one" \
        2> "$TMP_DIR/c0.runtime-output-$runtime_output_name.compile.stderr"
    [[ ! -s "$TMP_DIR/c0.runtime-output-$runtime_output_name.compile.stderr" ]] || \
        fail_test "c0-runtime-output-$runtime_output_name-compile-stderr"
    run_output "$SEED" < "$runtime_output_fixture" \
        > "$TMP_DIR/c0.runtime-output-$runtime_output_name.two"
    cmp -s "$TMP_DIR/c0.runtime-output-$runtime_output_name.one" \
        "$TMP_DIR/c0.runtime-output-$runtime_output_name.two" || \
        fail_test "c0-runtime-output-$runtime_output_name-deterministic-artifact"
    runtime_output_hash="$(sha256sum \
        "$TMP_DIR/c0.runtime-output-$runtime_output_name.one")"
    runtime_output_hash="${runtime_output_hash%% *}"
    case "$runtime_output_name" in
        roundtrip)
            runtime_output_hash_expected=c949a7820dd759d9420e60608550d071f5d63591c7f33f9682731eed224dafae
            ;;
        memory)
            runtime_output_hash_expected=2d84286922fb430d00c5c89f5afdb5226e58cbf2dc2c736c48eb02733d6de094
            ;;
        zero)
            runtime_output_hash_expected=383396f7604d33f25a9fc05d8b072052504c9d1ece15769661acdb6f3eb0a93d
            ;;
        while)
            runtime_output_hash_expected=2e323094de1dfd0f15932cd5e6039f2d183534418778a501e018a4ca65c9fe46
            ;;
    esac
    [[ "$runtime_output_hash" == "$runtime_output_hash_expected" ]] || \
        fail_test "c0-runtime-output-$runtime_output_name-artifact-identity"
    chmod 0755 "$TMP_DIR/c0.runtime-output-$runtime_output_name.one"
done

set +e
run_output "$SEED" < "$RUNTIME_LITERAL_ORDER_FIXTURE" \
    > "$TMP_DIR/c0.runtime-literal-order.one" \
    2> "$TMP_DIR/c0.runtime-literal-order.compile.stderr"
runtime_literal_order_compile_status=$?
set -e
[[ "$runtime_literal_order_compile_status" -eq 0 ]] || \
    fail_test "c0-runtime-literal-order-compile (expected 0, got $runtime_literal_order_compile_status)"
[[ ! -s "$TMP_DIR/c0.runtime-literal-order.compile.stderr" ]] || \
    fail_test "c0-runtime-literal-order-compile-stderr"
run_output "$SEED" < "$RUNTIME_LITERAL_ORDER_FIXTURE" \
    > "$TMP_DIR/c0.runtime-literal-order.two"
cmp -s "$TMP_DIR/c0.runtime-literal-order.one" \
    "$TMP_DIR/c0.runtime-literal-order.two" || \
    fail_test "c0-runtime-literal-order-deterministic-artifact"
runtime_literal_order_hash="$(sha256sum \
    "$TMP_DIR/c0.runtime-literal-order.one" | awk '{ print $1 }')"
[[ "$runtime_literal_order_hash" == \
    a4cc347ba1b5e25d48bdacd134456328b73beb600583c7e6e3479cd81ea2ffc3 ]] || \
    fail_test "c0-runtime-literal-order-artifact-identity"
chmod 0755 "$TMP_DIR/c0.runtime-literal-order.one"
printf 'Q' > "$TMP_DIR/c0.runtime-literal-order.stdin"
printf 'pre:Q:post' > "$TMP_DIR/c0.runtime-literal-order.expected"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-literal-order.one" \
    < "$TMP_DIR/c0.runtime-literal-order.stdin" \
    > "$TMP_DIR/c0.runtime-literal-order.stdout" \
    2> "$TMP_DIR/c0.runtime-literal-order.run.stderr"
runtime_literal_order_status=$?
set -e
[[ "$runtime_literal_order_status" -eq 81 ]] || \
    fail_test "c0-runtime-literal-order-status (expected 81, got $runtime_literal_order_status)"
cmp -s "$TMP_DIR/c0.runtime-literal-order.expected" \
    "$TMP_DIR/c0.runtime-literal-order.stdout" || \
    fail_test "c0-runtime-literal-order-bytes"
[[ ! -s "$TMP_DIR/c0.runtime-literal-order.run.stderr" ]] || \
    fail_test "c0-runtime-literal-order-stderr"
printf 'PASS c0-runtime-literal-order\n'

printf 'NQ-L' > "$TMP_DIR/c0.runtime-output-roundtrip.stdin"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-output-roundtrip.one" \
    < "$TMP_DIR/c0.runtime-output-roundtrip.stdin" \
    > "$TMP_DIR/c0.runtime-output-roundtrip.stdout" \
    2> "$TMP_DIR/c0.runtime-output-roundtrip.run.stderr"
runtime_output_roundtrip_status=$?
set -e
[[ "$runtime_output_roundtrip_status" -eq 78 ]] || \
    fail_test "c0-runtime-output-roundtrip-status (expected 78, got $runtime_output_roundtrip_status)"
cmp -s "$TMP_DIR/c0.runtime-output-roundtrip.stdin" \
    "$TMP_DIR/c0.runtime-output-roundtrip.stdout" || \
    fail_test "c0-runtime-output-roundtrip-bytes"
[[ ! -s "$TMP_DIR/c0.runtime-output-roundtrip.run.stderr" ]] || \
    fail_test "c0-runtime-output-roundtrip-stderr"

printf 'A\000\377' > "$TMP_DIR/c0.runtime-output-memory.expected"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-output-memory.one" \
    > "$TMP_DIR/c0.runtime-output-memory.stdout" \
    2> "$TMP_DIR/c0.runtime-output-memory.run.stderr"
runtime_output_memory_status=$?
set -e
[[ "$runtime_output_memory_status" -eq 255 ]] || \
    fail_test "c0-runtime-output-memory-status (expected 255, got $runtime_output_memory_status)"
cmp -s "$TMP_DIR/c0.runtime-output-memory.expected" \
    "$TMP_DIR/c0.runtime-output-memory.stdout" || \
    fail_test "c0-runtime-output-memory-bytes"
[[ ! -s "$TMP_DIR/c0.runtime-output-memory.run.stderr" ]] || \
    fail_test "c0-runtime-output-memory-stderr"

set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-output-zero.one" \
    > "$TMP_DIR/c0.runtime-output-zero.stdout" \
    2> "$TMP_DIR/c0.runtime-output-zero.run.stderr"
runtime_output_zero_status=$?
set -e
[[ "$runtime_output_zero_status" -eq 7 ]] || \
    fail_test "c0-runtime-output-zero-status (expected 7, got $runtime_output_zero_status)"
[[ ! -s "$TMP_DIR/c0.runtime-output-zero.stdout" ]] || \
    fail_test "c0-runtime-output-zero-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-output-zero.run.stderr" ]] || \
    fail_test "c0-runtime-output-zero-stderr"

printf 'CBA' > "$TMP_DIR/c0.runtime-output-while.expected"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-output-while.one" \
    > "$TMP_DIR/c0.runtime-output-while.stdout" \
    2> "$TMP_DIR/c0.runtime-output-while.run.stderr"
runtime_output_while_status=$?
set -e
[[ "$runtime_output_while_status" -eq 0 ]] || \
    fail_test "c0-runtime-output-while-status (expected 0, got $runtime_output_while_status)"
cmp -s "$TMP_DIR/c0.runtime-output-while.expected" \
    "$TMP_DIR/c0.runtime-output-while.stdout" || \
    fail_test "c0-runtime-output-while-order"
[[ ! -s "$TMP_DIR/c0.runtime-output-while.run.stderr" ]] || \
    fail_test "c0-runtime-output-while-stderr"

runtime_output_machine_hex="$(od -An -v -tx1 \
    "$TMP_DIR/c0.runtime-output-memory.one" | tr -d ' \n')"
case "$runtime_output_machine_hex" in
    *0f054885c00f8e*4801c64829c275e8*) ;;
    *) fail_test "c0-runtime-output-complete-write-loop" ;;
esac

printf 'runtime: output_write failed\n' \
    > "$TMP_DIR/c0.runtime-output-error.expected"
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$TMP_DIR/c0.runtime-output-memory.one" \
     2> "$TMP_DIR/c0.runtime-output-closed.stderr"
runtime_output_closed_status=$?
set -e
[[ "$runtime_output_closed_status" -eq 74 ]] || \
    fail_test "c0-runtime-output-closed-status (expected 74, got $runtime_output_closed_status)"
cmp -s "$TMP_DIR/c0.runtime-output-error.expected" \
    "$TMP_DIR/c0.runtime-output-closed.stderr" || \
    fail_test "c0-runtime-output-closed-diagnostic"

set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$TMP_DIR/c0.runtime-literal-order.one" \
    < "$TMP_DIR/c0.runtime-literal-order.stdin" \
     2> "$TMP_DIR/c0.runtime-literal-closed.stderr"
runtime_literal_closed_status=$?
set -e
[[ "$runtime_literal_closed_status" -eq 74 ]] || \
    fail_test "c0-runtime-literal-closed-status (expected 74, got $runtime_literal_closed_status)"
cmp -s "$TMP_DIR/c0.runtime-output-error.expected" \
    "$TMP_DIR/c0.runtime-literal-closed.stderr" || \
    fail_test "c0-runtime-literal-closed-diagnostic"

runtime_output_broken_pipe_path="$TMP_DIR/c0.runtime-output.broken-pipe"
mkfifo "$runtime_output_broken_pipe_path"
(exec 3< "$runtime_output_broken_pipe_path") &
runtime_output_broken_pipe_pid=$!
exec {runtime_output_broken_pipe_fd}> "$runtime_output_broken_pipe_path"
wait "$runtime_output_broken_pipe_pid"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-output-memory.one" \
    >&$runtime_output_broken_pipe_fd \
    2> "$TMP_DIR/c0.runtime-output-broken-pipe.stderr"
runtime_output_broken_pipe_status=$?
set -e
exec {runtime_output_broken_pipe_fd}>&-
[[ "$runtime_output_broken_pipe_status" -eq 74 ]] || \
    fail_test "c0-runtime-output-broken-pipe-status (expected 74, got $runtime_output_broken_pipe_status)"
cmp -s "$TMP_DIR/c0.runtime-output-error.expected" \
    "$TMP_DIR/c0.runtime-output-broken-pipe.stderr" || \
    fail_test "c0-runtime-output-broken-pipe-diagnostic"

set +e
run_with_invalid_standard_fd 1 run_with_invalid_standard_fd 2 run_output_bounded 5 "$TMP_DIR/c0.runtime-output-memory.one"
runtime_output_no_diagnostic_status=$?
set -e
[[ "$runtime_output_no_diagnostic_status" -eq 74 ]] || \
    fail_test "c0-runtime-output-no-diagnostic-status (expected 74, got $runtime_output_no_diagnostic_status)"
printf 'PASS c0-runtime-output-write\n'

set +e
run_output "$SEED" < "$RUNTIME_OUTPUT_RANGE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-output-range.stdout" \
    2> "$TMP_DIR/c0.runtime-output-range.stderr"
runtime_output_range_status=$?
set -e
[[ "$runtime_output_range_status" -eq 1 ]] || \
    fail_test "c0-runtime-output-range-status (expected 1, got $runtime_output_range_status)"
[[ ! -s "$TMP_DIR/c0.runtime-output-range.stdout" ]] || \
    fail_test "c0-runtime-output-range-no-artifact"
printf 'input:2:23: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-output-range.expected"
cmp -s "$TMP_DIR/c0.runtime-output-range.expected" \
    "$TMP_DIR/c0.runtime-output-range.stderr" || \
    fail_test "c0-runtime-output-range-diagnostic"
printf 'PASS c0-runtime-output-range-bound\n'

set +e
run_output "$SEED" < "$RUNTIME_OUTPUT_MALFORMED_FIXTURE" \
    > "$TMP_DIR/c0.runtime-output-malformed.stdout" \
    2> "$TMP_DIR/c0.runtime-output-malformed.stderr"
runtime_output_malformed_status=$?
set -e
[[ "$runtime_output_malformed_status" -eq 1 ]] || \
    fail_test "c0-runtime-output-malformed-status (expected 1, got $runtime_output_malformed_status)"
[[ ! -s "$TMP_DIR/c0.runtime-output-malformed.stdout" ]] || \
    fail_test "c0-runtime-output-malformed-no-artifact"
printf 'input:2:19: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-output-malformed.expected"
cmp -s "$TMP_DIR/c0.runtime-output-malformed.expected" \
    "$TMP_DIR/c0.runtime-output-malformed.stderr" || \
    fail_test "c0-runtime-output-malformed-diagnostic"
printf 'PASS c0-runtime-output-syntax-error\n'

run_output "$SEED" < "$RUNTIME_OPERATION_CAPACITY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-operation-capacity" \
    2> "$TMP_DIR/c0.runtime-operation-capacity.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-operation-capacity.compile.stderr" ]] || \
    fail_test "c0-runtime-operation-capacity-compile-stderr"
chmod 0755 "$TMP_DIR/c0.runtime-operation-capacity"
printf 'A' > "$TMP_DIR/c0.runtime-operation-capacity.stdin"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-operation-capacity" \
    < "$TMP_DIR/c0.runtime-operation-capacity.stdin" \
    > "$TMP_DIR/c0.runtime-operation-capacity.stdout" \
    2> "$TMP_DIR/c0.runtime-operation-capacity.run.stderr"
runtime_operation_capacity_status=$?
set -e
[[ "$runtime_operation_capacity_status" -eq 65 ]] || \
    fail_test "c0-runtime-operation-capacity-status (expected 65, got $runtime_operation_capacity_status)"
[[ ! -s "$TMP_DIR/c0.runtime-operation-capacity.stdout" ]] || \
    fail_test "c0-runtime-operation-capacity-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-operation-capacity.run.stderr" ]] || \
    fail_test "c0-runtime-operation-capacity-stderr"

printf 'fn main(){\n' > "$TMP_DIR/c0.runtime-operation-bound-exact.nq"
for _ in {1..40}; do
    printf 'write("")\n' >> "$TMP_DIR/c0.runtime-operation-bound-exact.nq"
done
printf 'return 0}\n' >> "$TMP_DIR/c0.runtime-operation-bound-exact.nq"
run_output "$SEED" < "$TMP_DIR/c0.runtime-operation-bound-exact.nq" \
    > "$TMP_DIR/c0.runtime-operation-bound-exact.out" \
    2> "$TMP_DIR/c0.runtime-operation-bound-exact.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-operation-bound-exact.stderr" ]] || \
    fail_test "c0-runtime-operation-bound-exact-stderr"
chmod 0755 "$TMP_DIR/c0.runtime-operation-bound-exact.out"
run_output_bounded 5 "$TMP_DIR/c0.runtime-operation-bound-exact.out" \
    > "$TMP_DIR/c0.runtime-operation-bound-exact.stdout" \
    2> "$TMP_DIR/c0.runtime-operation-bound-exact.run.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-operation-bound-exact.stdout" ]] || \
    fail_test "c0-runtime-operation-bound-exact-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-operation-bound-exact.run.stderr" ]] || \
    fail_test "c0-runtime-operation-bound-exact-run-stderr"

sed '$i write("")' "$TMP_DIR/c0.runtime-operation-bound-exact.nq" \
    > "$TMP_DIR/c0.runtime-operation-bound-overflow.nq"
set +e
run_output "$SEED" < "$TMP_DIR/c0.runtime-operation-bound-overflow.nq" \
    > "$TMP_DIR/c0.runtime-operation-bound-overflow.stdout" \
    2> "$TMP_DIR/c0.runtime-operation-bound-overflow.stderr"
runtime_operation_bound_overflow_status=$?
set -e
[[ "$runtime_operation_bound_overflow_status" -eq 1 ]] || \
    fail_test "c0-runtime-operation-bound-overflow-status (expected 1, got $runtime_operation_bound_overflow_status)"
[[ ! -s "$TMP_DIR/c0.runtime-operation-bound-overflow.stdout" ]] || \
    fail_test "c0-runtime-operation-bound-overflow-no-artifact"
printf 'input:42:9: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-operation-bound-overflow.expected"
cmp -s "$TMP_DIR/c0.runtime-operation-bound-overflow.expected" \
    "$TMP_DIR/c0.runtime-operation-bound-overflow.stderr" || \
    fail_test "c0-runtime-operation-bound-overflow-diagnostic"
printf 'PASS c0-runtime-operation-record-bound\n'

run_output "$SEED" < "$RUNTIME_OUTPUT_CAPACITY_FIXTURE" \
    > "$TMP_DIR/c0.runtime-output-capacity" \
    2> "$TMP_DIR/c0.runtime-output-capacity.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-output-capacity.compile.stderr" ]] || \
    fail_test "c0-runtime-output-capacity-compile-stderr"
chmod 0755 "$TMP_DIR/c0.runtime-output-capacity"
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$TMP_DIR/c0.runtime-output-capacity" \
    < /dev/null  2> "$TMP_DIR/c0.runtime-output-capacity.run.stderr"
runtime_output_capacity_status=$?
set -e
[[ "$runtime_output_capacity_status" -eq 74 ]] || \
    fail_test "c0-runtime-output-capacity-status (expected 74, got $runtime_output_capacity_status)"
cmp -s "$TMP_DIR/c0.runtime-output-error.expected" \
    "$TMP_DIR/c0.runtime-output-capacity.run.stderr" || \
    fail_test "c0-runtime-output-capacity-diagnostic"
printf 'PASS c0-runtime-operation-metadata-capacity\n'

readelf -lW "$TMP_DIR/c0.runtime-input.one" > "$TMP_DIR/c0.runtime-input.readelf"
runtime_load_count="$(awk '$1 == "LOAD" { count++ } END { print count + 0 }' \
    "$TMP_DIR/c0.runtime-input.readelf")"
[[ "$runtime_load_count" -eq 2 ]] || \
    fail_test "c0-runtime-load-count (expected 2, got $runtime_load_count)"

runtime_rx_count="$(awk '$1 == "LOAD" && $2 == "0x000000" && \
    $3 == "0x0000000000400000" && $4 == "0x0000000000400000" && \
    $5 == $6 && $7 == "R" && $8 == "E" && $9 == "0x1000" { count++ } \
    END { print count + 0 }' "$TMP_DIR/c0.runtime-input.readelf")"
[[ "$runtime_rx_count" -eq 1 ]] || \
    fail_test "c0-runtime-exact-rx-load"

runtime_rx_memsz="$(awk '$1 == "LOAD" && $7 == "R" && $8 == "E" { print $6 }' \
    "$TMP_DIR/c0.runtime-input.readelf")"
runtime_rx_memsz_hex="${runtime_rx_memsz#0x}"
[[ -n "$runtime_rx_memsz_hex" ]] || fail_test "c0-runtime-rx-size-present"
(( 0x$runtime_rx_memsz_hex <= 0x1000 )) || \
    fail_test "c0-runtime-load-segments-overlap"

runtime_rw_count="$(awk '$1 == "LOAD" && $2 == "0x001000" && \
    $3 == "0x0000000000401000" && $4 == "0x0000000000401000" && \
    $5 == "0x000000" && $6 == "0x000100" && $7 == "RW" && \
    $8 == "0x1000" { count++ } END { print count + 0 }' \
    "$TMP_DIR/c0.runtime-input.readelf")"
[[ "$runtime_rw_count" -eq 1 ]] || \
    fail_test "c0-runtime-exact-rw-bss-load"

if awk '$1 == "LOAD" && (($7 ~ /W/ && $7 ~ /E/) || \
    ($7 == "R" && $8 ~ /W/ && $8 ~ /E/)) { found=1 } END { exit !found }' \
    "$TMP_DIR/c0.runtime-input.readelf"; then
    fail_test "c0-runtime-no-rwx-load"
fi
awk '$1 == "GNU_STACK" { found=1; if ($7 ~ /E/) exit 1 } END { exit !found }' \
    "$TMP_DIR/c0.runtime-input.readelf" || \
    fail_test "c0-runtime-non-executable-stack"
printf 'PASS c0-runtime-byte-memory-and-input\n'

set +e
run_output "$SEED" < "$RUNTIME_INPUT_RANGE_FIXTURE" \
    > "$TMP_DIR/c0.runtime-range.stdout" \
    2> "$TMP_DIR/c0.runtime-range.stderr"
runtime_range_status=$?
set -e
[[ "$runtime_range_status" -eq 1 ]] || \
    fail_test "c0-runtime-input-range-status (expected 1, got $runtime_range_status)"
[[ ! -s "$TMP_DIR/c0.runtime-range.stdout" ]] || \
    fail_test "c0-runtime-input-range-no-artifact"
printf 'input:2:21: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.runtime-range.expected"
cmp -s "$TMP_DIR/c0.runtime-range.expected" \
    "$TMP_DIR/c0.runtime-range.stderr" || \
    fail_test "c0-runtime-input-range-diagnostic"
printf 'PASS c0-runtime-input-range-bound\n'

run_output "$SEED" < "$RUNTIME_WRITE_MIX_FIXTURE" \
    > "$TMP_DIR/c0.runtime-write-mix" \
    2> "$TMP_DIR/c0.runtime-write-mix.compile.stderr"
[[ ! -s "$TMP_DIR/c0.runtime-write-mix.compile.stderr" ]] || \
    fail_test "c0-runtime-write-mix-compile-stderr"
chmod 0755 "$TMP_DIR/c0.runtime-write-mix"
printf 'Z' > "$TMP_DIR/c0.runtime-write-mix.stdin"
set +e
run_output_bounded 5 "$TMP_DIR/c0.runtime-write-mix" \
    < "$TMP_DIR/c0.runtime-write-mix.stdin" \
    > "$TMP_DIR/c0.runtime-write-mix.stdout" \
    2> "$TMP_DIR/c0.runtime-write-mix.run.stderr"
runtime_write_mix_status=$?
set -e
[[ "$runtime_write_mix_status" -eq 0 ]] || \
    fail_test "c0-runtime-write-mix-status (expected 0, got $runtime_write_mix_status)"
[[ ! -s "$TMP_DIR/c0.runtime-write-mix.stdout" ]] || \
    fail_test "c0-runtime-write-mix-stdout"
[[ ! -s "$TMP_DIR/c0.runtime-write-mix.run.stderr" ]] || \
    fail_test "c0-runtime-write-mix-stderr"
printf 'PASS c0-runtime-empty-literal-order\n'

for runtime_reject_case in \
    "$RUNTIME_LOAD_ARITHMETIC_FIXTURE:2:25:load-arithmetic"; do
    runtime_reject_fixture="${runtime_reject_case%%:*}"
    runtime_reject_rest="${runtime_reject_case#*:}"
    runtime_reject_line="${runtime_reject_rest%%:*}"
    runtime_reject_rest="${runtime_reject_rest#*:}"
    runtime_reject_col="${runtime_reject_rest%%:*}"
    runtime_reject_name="${runtime_reject_rest#*:}"
    set +e
    run_output "$SEED" < "$runtime_reject_fixture" \
        > "$TMP_DIR/c0.runtime-$runtime_reject_name.stdout" \
        2> "$TMP_DIR/c0.runtime-$runtime_reject_name.stderr"
    runtime_reject_status=$?
    set -e
    [[ "$runtime_reject_status" -eq 1 ]] || \
        fail_test "c0-runtime-$runtime_reject_name-status (expected 1, got $runtime_reject_status)"
    [[ ! -s "$TMP_DIR/c0.runtime-$runtime_reject_name.stdout" ]] || \
        fail_test "c0-runtime-$runtime_reject_name-no-artifact"
    printf 'input:%s:%s: error[C0-001]: invalid C0 program\n' \
        "$runtime_reject_line" "$runtime_reject_col" \
        > "$TMP_DIR/c0.runtime-$runtime_reject_name.expected"
    cmp -s "$TMP_DIR/c0.runtime-$runtime_reject_name.expected" \
        "$TMP_DIR/c0.runtime-$runtime_reject_name.stderr" || \
        fail_test "c0-runtime-$runtime_reject_name-diagnostic"
done
printf 'PASS c0-runtime-c03a-subset-boundaries\n'

for string_error_case in \
    "$INVALID_STRING_ESCAPE_FIXTURE:2:13:invalid-escape" \
    "$UNTERMINATED_STRING_FIXTURE:2:11:unterminated" \
    "$WRITE_PAYLOAD_LIMIT_FIXTURE:2:267:payload-limit"; do
    string_error_fixture="${string_error_case%%:*}"
    string_error_rest="${string_error_case#*:}"
    string_error_line="${string_error_rest%%:*}"
    string_error_rest="${string_error_rest#*:}"
    string_error_col="${string_error_rest%%:*}"
    string_error_name="${string_error_rest#*:}"
    set +e
    run_output "$SEED" < "$string_error_fixture" \
        > "$TMP_DIR/c0.string-$string_error_name.stdout" \
        2> "$TMP_DIR/c0.string-$string_error_name.stderr"
    string_error_status=$?
    set -e
    [[ "$string_error_status" -eq 1 ]] || \
        fail_test "c0-string-$string_error_name-status (expected 1, got $string_error_status)"
    [[ ! -s "$TMP_DIR/c0.string-$string_error_name.stdout" ]] || \
        fail_test "c0-string-$string_error_name-no-artifact"
    printf 'input:%s:%s: error[C0-001]: invalid C0 program\n' \
        "$string_error_line" "$string_error_col" \
        > "$TMP_DIR/c0.string-$string_error_name.expected"
    cmp -s "$TMP_DIR/c0.string-$string_error_name.expected" \
        "$TMP_DIR/c0.string-$string_error_name.stderr" || \
        fail_test "c0-string-$string_error_name-diagnostic"
done
printf 'PASS c0-string-diagnostics-and-payload-bound\n'

awk 'BEGIN {
    print "fn main() {"
    for (line = 0; line < 16; line++) {
        printf "    write(\""
        for (i = 0; i < 255; i++) printf "%c", 97 + line
        print "\")"
    }
    print "    write(\"abcdefghijklmnop\")"
    print "    return 0"
    print "}"
}' > "$TMP_DIR/c0.literal-cap-exact.nq"
run_output "$SEED" < "$TMP_DIR/c0.literal-cap-exact.nq" \
    > "$TMP_DIR/c0.literal-cap-exact.out" \
    2> "$TMP_DIR/c0.literal-cap-exact.compile.stderr"
[[ ! -s "$TMP_DIR/c0.literal-cap-exact.compile.stderr" ]] || \
    fail_test "c0-literal-cap-exact-compile-stderr"
chmod 0755 "$TMP_DIR/c0.literal-cap-exact.out"
awk 'BEGIN {
    for (line = 0; line < 16; line++) {
        for (i = 0; i < 255; i++) printf "%c", 97 + line
    }
    printf "abcdefghijklmnop"
}' > "$TMP_DIR/c0.literal-cap-exact.expected"
run_output_bounded 5 "$TMP_DIR/c0.literal-cap-exact.out" \
    > "$TMP_DIR/c0.literal-cap-exact.stdout" \
    2> "$TMP_DIR/c0.literal-cap-exact.run.stderr"
cmp -s "$TMP_DIR/c0.literal-cap-exact.expected" \
    "$TMP_DIR/c0.literal-cap-exact.stdout" || \
    fail_test "c0-literal-cap-exact-output"
[[ ! -s "$TMP_DIR/c0.literal-cap-exact.run.stderr" ]] || \
    fail_test "c0-literal-cap-exact-run-stderr"

sed 's/write("abcdefghijklmnop")/write("abcdefghijklmnopq")/' \
    "$TMP_DIR/c0.literal-cap-exact.nq" > "$TMP_DIR/c0.literal-cap-overflow.nq"
set +e
run_output "$SEED" < "$TMP_DIR/c0.literal-cap-overflow.nq" \
    > "$TMP_DIR/c0.literal-cap-overflow.stdout" \
    2> "$TMP_DIR/c0.literal-cap-overflow.stderr"
literal_cap_overflow_status=$?
set -e
[[ "$literal_cap_overflow_status" -eq 1 ]] || \
    fail_test "c0-literal-cap-overflow-status (expected 1, got $literal_cap_overflow_status)"
[[ ! -s "$TMP_DIR/c0.literal-cap-overflow.stdout" ]] || \
    fail_test "c0-literal-cap-overflow-no-artifact"
printf 'input:18:28: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.literal-cap-overflow.expected"
cmp -s "$TMP_DIR/c0.literal-cap-overflow.expected" \
    "$TMP_DIR/c0.literal-cap-overflow.stderr" || \
    fail_test "c0-literal-cap-overflow-diagnostic"
printf 'PASS c0-literal-capacity-boundary\n'

run_output "$SEED" < "$RETURN255_FIXTURE" > "$TMP_DIR/c0.return255"
chmod 0755 "$TMP_DIR/c0.return255"
set +e
run_output_bounded 5 "$TMP_DIR/c0.return255" >/dev/null
return255_status=$?
set -e
[[ "$return255_status" -eq 255 ]] || \
    fail_test "c0-u8-maximum-run (expected 255, got $return255_status)"
printf 'PASS c0-u8-maximum\n'

run_output "$SEED" < "$RETURN7_FIXTURE" > "$TMP_DIR/c0.return7.two"
cmp -s "$TMP_DIR/c0.return7.one" "$TMP_DIR/c0.return7.two" || \
    fail_test "c0-deterministic-successor-output"
printf 'PASS c0-deterministic-successor-output\n'

set +e
run_output "$SEED" < "$INVALID_FIXTURE" \
    > "$TMP_DIR/c0.invalid.stdout" 2> "$TMP_DIR/c0.invalid.stderr"
invalid_status=$?
set -e
[[ "$invalid_status" -eq 1 ]] || \
    fail_test "c0-invalid-status (expected 1, got $invalid_status)"
[[ ! -s "$TMP_DIR/c0.invalid.stdout" ]] || fail_test "c0-invalid-no-artifact"
printf 'input:2:11: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.invalid.expected"
cmp -s "$TMP_DIR/c0.invalid.expected" "$TMP_DIR/c0.invalid.stderr" || \
    fail_test "c0-invalid-diagnostic"
printf 'PASS c0-invalid-source-diagnostic\n'

for split_case in \
    "$SPLIT_KEYWORD_FIXTURE:1:1" \
    "$SPLIT_MAIN_FIXTURE:1:4" \
    "$SPLIT_RETURN_FIXTURE:2:5" \
    "$SPLIT_DIGITS_FIXTURE:2:14" \
    "$MISSING_FN_SEPARATOR_FIXTURE:1:1" \
    "$MISSING_RETURN_SEPARATOR_FIXTURE:2:5"; do
    split_fixture="${split_case%%:*}"
    split_location="${split_case#*:}"
    split_name="$(basename "$split_fixture" .nq)"
    set +e
    run_output "$SEED" < "$split_fixture" \
        > "$TMP_DIR/c0.$split_name.stdout" 2> "$TMP_DIR/c0.$split_name.stderr"
    split_status=$?
    set -e
    [[ "$split_status" -eq 1 ]] || \
        fail_test "c0-$split_name-status (expected 1, got $split_status)"
    [[ ! -s "$TMP_DIR/c0.$split_name.stdout" ]] || \
        fail_test "c0-$split_name-no-artifact"
    printf 'input:%s: error[C0-001]: invalid C0 program\n' "$split_location" \
        > "$TMP_DIR/c0.$split_name.expected"
    cmp -s "$TMP_DIR/c0.$split_name.expected" "$TMP_DIR/c0.$split_name.stderr" || \
        fail_test "c0-$split_name-diagnostic"
done
printf 'PASS c0-token-boundaries-enforced\n'

# Token 134 must not overwrite the recorded one-byte length of token 6 (`a`).
# The long separator pushes the later token offsets above 1024 while keeping
# the whole valid program below both fixed lexer bounds.
token_layout_fixture="$TMP_DIR/c0.token-layout-high-offset.nq"
printf 'fn main(){let a=0' > "$token_layout_fixture"
printf '%*s' 1100 '' >> "$token_layout_fixture"
printf 'return a' >> "$token_layout_fixture"
for _ in {1..70}; do
    printf '+0' >> "$token_layout_fixture"
done
printf '}\n' >> "$token_layout_fixture"
run_output "$SEED" < "$token_layout_fixture" \
    > "$TMP_DIR/c0.token-layout-high-offset.out" \
    2> "$TMP_DIR/c0.token-layout-high-offset.stderr" || \
    fail_test "c0-token-table-layout-high-offset-compile"
[[ ! -s "$TMP_DIR/c0.token-layout-high-offset.stderr" ]] || \
    fail_test "c0-token-table-layout-high-offset-stderr"
chmod 0755 "$TMP_DIR/c0.token-layout-high-offset.out"
set +e
run_output_bounded 5 "$TMP_DIR/c0.token-layout-high-offset.out" >/dev/null
token_layout_status=$?
set -e
[[ "$token_layout_status" -eq 0 ]] || \
    fail_test "c0-token-table-layout-high-offset-run (expected 0, got $token_layout_status)"
printf 'PASS c0-token-table-layout-high-offset\n'

set +e
run_output "$SEED" < "$RETURN256_FIXTURE" \
    > "$TMP_DIR/c0.return256.stdout" 2> "$TMP_DIR/c0.return256.stderr"
return256_status=$?
set -e
[[ "$return256_status" -eq 1 ]] || \
    fail_test "c0-u8-overflow-status (expected 1, got $return256_status)"
[[ ! -s "$TMP_DIR/c0.return256.stdout" ]] || fail_test "c0-u8-overflow-no-artifact"
printf 'input:2:12: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/c0.return256.expected"
cmp -s "$TMP_DIR/c0.return256.expected" "$TMP_DIR/c0.return256.stderr" || \
    fail_test "c0-u8-overflow-diagnostic"
printf 'PASS c0-u8-return-bound\n'

for malformed_case in \
    "$DIV_ZERO_FIXTURE:2:14:unsupported-division" \
    "$TRAILING_TOKEN_FIXTURE:2:14:trailing-token" \
    "$MUL_OVERFLOW_FIXTURE:2:17:multiplication-overflow"; do
    malformed_fixture="${malformed_case%%:*}"
    malformed_rest="${malformed_case#*:}"
    malformed_line="${malformed_rest%%:*}"
    malformed_rest="${malformed_rest#*:}"
    malformed_col="${malformed_rest%%:*}"
    malformed_name="${malformed_rest#*:}"
    set +e
    run_output "$SEED" < "$malformed_fixture" \
        > "$TMP_DIR/c0.$malformed_name.stdout" \
        2> "$TMP_DIR/c0.$malformed_name.stderr"
    malformed_status=$?
    set -e
    [[ "$malformed_status" -eq 1 ]] || \
        fail_test "c0-$malformed_name-status (expected 1, got $malformed_status)"
    [[ ! -s "$TMP_DIR/c0.$malformed_name.stdout" ]] || \
        fail_test "c0-$malformed_name-no-artifact"
    printf 'input:%s:%s: error[C0-001]: invalid C0 program\n' \
        "$malformed_line" "$malformed_col" > "$TMP_DIR/c0.$malformed_name.expected"
    cmp -s "$TMP_DIR/c0.$malformed_name.expected" \
        "$TMP_DIR/c0.$malformed_name.stderr" || \
        fail_test "c0-$malformed_name-diagnostic"
done
printf 'PASS c0-malformed-expression-diagnostics\n'

awk 'BEGIN {
    source = "fn main(){return 7}\n"
    printf "%s", source
    for (i = length(source); i < 9984; i++) printf " "
}' > "$TMP_DIR/c0.input-cap-exact.nq"
[[ "$(wc -c < "$TMP_DIR/c0.input-cap-exact.nq")" -eq 9984 ]] || \
    fail_test "c0-input-cap-exact-fixture-size"
run_output "$SEED" < "$TMP_DIR/c0.input-cap-exact.nq" \
    > "$TMP_DIR/c0.input-cap-exact.out" \
    2> "$TMP_DIR/c0.input-cap-exact.stderr"
[[ ! -s "$TMP_DIR/c0.input-cap-exact.stderr" ]] || \
    fail_test "c0-input-cap-exact-compile-stderr"
chmod 0755 "$TMP_DIR/c0.input-cap-exact.out"
set +e
run_output_bounded 5 "$TMP_DIR/c0.input-cap-exact.out" >/dev/null
input_cap_exact_status=$?
set -e
[[ "$input_cap_exact_status" -eq 7 ]] || \
    fail_test "c0-input-cap-exact-run (expected 7, got $input_cap_exact_status)"

awk 'BEGIN { for (i = 0; i < 9984; i++) printf "a"; print "" }' \
    > "$TMP_DIR/c0.input-cap-overflow.nq"
[[ "$(wc -c < "$TMP_DIR/c0.input-cap-overflow.nq")" -eq 9985 ]] || \
    fail_test "c0-input-cap-overflow-fixture-size"

awk 'BEGIN {
    printf "fn main(){return 0"
    for (i = 0; i < 252; i++) printf "+0"
    print "}"
}' > "$TMP_DIR/c0.token-cap-exact.nq"
run_output "$SEED" < "$TMP_DIR/c0.token-cap-exact.nq" \
    > "$TMP_DIR/c0.token-cap-exact.out" \
    2> "$TMP_DIR/c0.token-cap-exact.stderr" || \
    fail_test "c0-token-cap-exact-compile"
[[ ! -s "$TMP_DIR/c0.token-cap-exact.stderr" ]] || \
    fail_test "c0-token-cap-exact-stderr"
chmod 0755 "$TMP_DIR/c0.token-cap-exact.out"
set +e
run_output_bounded 5 "$TMP_DIR/c0.token-cap-exact.out" >/dev/null
token_cap_exact_status=$?
set -e
[[ "$token_cap_exact_status" -eq 0 ]] || \
    fail_test "c0-token-cap-exact-run (expected 0, got $token_cap_exact_status)"

awk 'BEGIN {
    printf "fn main(){return 0"
    for (i = 0; i < 252; i++) printf "+0"
    print "}x"
}' > "$TMP_DIR/c0.token-cap-overflow.nq"

for limit_case in \
    "$TMP_DIR/c0.token-cap-overflow.nq:1:524:token-limit" \
    "$TMP_DIR/c0.input-cap-overflow.nq:1:9985:input-limit"; do
    limit_fixture="${limit_case%%:*}"
    limit_rest="${limit_case#*:}"
    limit_line="${limit_rest%%:*}"
    limit_rest="${limit_rest#*:}"
    limit_col="${limit_rest%%:*}"
    limit_name="${limit_rest#*:}"
    set +e
    run_output "$SEED" < "$limit_fixture" \
        > "$TMP_DIR/c0.$limit_name.stdout" 2> "$TMP_DIR/c0.$limit_name.stderr"
    limit_status=$?
    set -e
    [[ "$limit_status" -eq 1 ]] || \
        fail_test "c0-$limit_name-status (expected 1, got $limit_status)"
    [[ ! -s "$TMP_DIR/c0.$limit_name.stdout" ]] || \
        fail_test "c0-$limit_name-no-artifact"
    printf 'input:%s:%s: error[C0-001]: invalid C0 program\n' \
        "$limit_line" "$limit_col" > "$TMP_DIR/c0.$limit_name.expected"
    cmp -s "$TMP_DIR/c0.$limit_name.expected" "$TMP_DIR/c0.$limit_name.stderr" || \
        fail_test "c0-$limit_name-diagnostic"
done
printf 'PASS c0-lexer-resource-bounds\n'

mkdir "$TMP_DIR/c0.adapter-target-dir"
set +e
"$COMPILER_ADAPTER" "$RETURN7_FIXTURE" "$TMP_DIR/c0.adapter-target-dir" \
    > "$TMP_DIR/c0.adapter-dir.stdout" 2> "$TMP_DIR/c0.adapter-dir.stderr"
adapter_dir_status=$?
set -e
[[ "$adapter_dir_status" -eq 1 ]] || \
    fail_test "c0-adapter-directory-status (expected 1, got $adapter_dir_status)"
grep -Fq 'output path' "$TMP_DIR/c0.adapter-dir.stderr" || \
    fail_test "c0-adapter-directory-diagnostic"
if find "$TMP_DIR/c0.adapter-target-dir" -mindepth 1 -print -quit | grep -q .; then
    fail_test "c0-adapter-directory-no-temp-entry"
fi
printf 'PASS c0-adapter-rejects-directory-output\n'

printf 'old-output' > "$TMP_DIR/c0.adapter.out"
set +e
"$COMPILER_ADAPTER" "$MALFORMED_LET_FIXTURE" "$TMP_DIR/c0.adapter.out" \
    > "$TMP_DIR/c0.adapter.stdout" 2> "$TMP_DIR/c0.adapter.stderr"
adapter_status=$?
set -e
[[ "$adapter_status" -eq 1 ]] || \
    fail_test "c0-adapter-invalid-status (expected 1, got $adapter_status)"
printf 'old-output' > "$TMP_DIR/c0.adapter.expected"
cmp -s "$TMP_DIR/c0.adapter.expected" "$TMP_DIR/c0.adapter.out" || \
    fail_test "c0-adapter-preserves-old-output"
cmp -s "$TMP_DIR/c0.invalid.expected" "$TMP_DIR/c0.adapter.stderr" || \
    fail_test "c0-adapter-invalid-diagnostic"
if find "$TMP_DIR" -maxdepth 1 -name '.c0.tmp.*' -print -quit | grep -q .; then
    fail_test "c0-adapter-cleans-temporary-output"
fi
printf 'PASS c0-atomic-failure-preserves-output\n'

adapter_root="$TMP_DIR/adapter-root"
mkdir -p "$adapter_root"
cp "$COMPILER_ADAPTER" "$SEED" "$HASH" "$adapter_root/"
chmod 0755 "$adapter_root/compile.sh" "$adapter_root/c0.seed"
printf 'tampered' >> "$adapter_root/c0.seed"
printf 'old-output' > "$TMP_DIR/c0.adapter-tampered.out"
set +e
"$adapter_root/compile.sh" "$RETURN7_FIXTURE" "$TMP_DIR/c0.adapter-tampered.out" \
    > "$TMP_DIR/c0.adapter-tampered.stdout" \
    2> "$TMP_DIR/c0.adapter-tampered.stderr"
adapter_tampered_status=$?
set -e
[[ "$adapter_tampered_status" -eq 1 ]] || \
    fail_test "c0-adapter-tampered-status (expected 1, got $adapter_tampered_status)"
[[ ! -s "$TMP_DIR/c0.adapter-tampered.stdout" ]] || \
    fail_test "c0-adapter-tampered-stdout"
printf 'old-output' > "$TMP_DIR/c0.adapter-tampered.expected"
cmp -s "$TMP_DIR/c0.adapter-tampered.expected" \
    "$TMP_DIR/c0.adapter-tampered.out" || \
    fail_test "c0-adapter-tampered-preserves-output"
grep -Fq 'C0 seed hash mismatch' "$TMP_DIR/c0.adapter-tampered.stderr" || \
    fail_test "c0-adapter-tampered-diagnostic"
if find "$TMP_DIR" -maxdepth 1 -name '.c0.tmp.*' -print -quit | grep -q .; then
    fail_test "c0-adapter-tampered-temp-cleanup"
fi
printf 'PASS c0-adapter-verifies-seed-hash\n'

"$COMPILER_ADAPTER" "$RETURN7_FIXTURE" "$TMP_DIR/c0.adapter.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/c0.adapter.out" >/dev/null
adapter_success_status=$?
set -e
[[ "$adapter_success_status" -eq 7 ]] || \
    fail_test "c0-adapter-success (expected 7, got $adapter_success_status)"
printf 'PASS c0-compiler-adapter-success\n'
