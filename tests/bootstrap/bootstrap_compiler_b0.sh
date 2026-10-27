#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/tests/shared/lib.sh"

B0_DIR="$ROOT_DIR/bootstrap/compiler/b0"
B0_TARGET_DIR="$B0_DIR/x86_64-linux"
MANIFEST="$ROOT_DIR/bootstrap/manifest.tsv"
MATERIALIZER="$B0_TARGET_DIR/materialize.sh"
SEED="$B0_TARGET_DIR/b0.seed"
HASH="$B0_TARGET_DIR/b0.sha256"
REFERENCE_ASM="$B0_TARGET_DIR/b0.reference.asm"
RETURN7_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/return7.nql"
RETURN23_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/return23_spaced.nql"
WRITE_STRING_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/write_string.nql"
WRITE_LITERAL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/write_literal_dynamic.nql"
ARITHMETIC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/arithmetic.nql"
EXPRESSION_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/expression_semantic.nql"
COMPARISON_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/comparison.nql"
IF_ELSE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/if_else.nql"
IF_ELSE_SEMANTIC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/if_else_semantic.nql"
IF_ELSE_FALSE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/if_else_false_semantic.nql"
WHILE_SEMANTIC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/while_semantic.nql"
WHILE_FALSE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/while_false_semantic.nql"
WHILE_STATE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/while_state_semantic.nql"
BYTE_MEMORY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_semantic.nql"
BYTE_MEMORY_ZERO_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_zero.nql"
BYTE_MEMORY_WIDTH_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_width.nql"
BYTE_MEMORY_BOUNDARY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_boundary.nql"
BYTE_MEMORY_CONST_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_const_oob.nql"
BYTE_MEMORY_RUNTIME_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_runtime_oob.nql"
BYTE_MEMORY_STORE_RUNTIME_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_memory_store_runtime_oob.nql"
BYTE_LOAD_LOCAL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_load_local.nql"
BYTE_STORE_MALFORMED_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/byte_store_malformed.nql"
IO_ROUNDTRIP_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_roundtrip.nql"
IO_CONST_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_const_oob.nql"
IO_RUNTIME_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_runtime_oob.nql"
IO_OUTPUT_RUNTIME_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_output_runtime_oob.nql"
IO_WRITE_FAILURE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_write_failure.nql"
IO_ERROR_WRITE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_error_write.nql"
IO_ERROR_WRITE_FULL_RANGE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_error_write_full_range.nql"
IO_ERROR_WRITE_CONST_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_error_write_const_oob.nql"
IO_MALFORMED_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_malformed.nql"
IO_BOUNDARY_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_boundary.nql"
INPUT_READ_LOCAL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/input_read_local.nql"
IO_NESTED_CONST_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_nested_const_oob.nql"
IO_OUTPUT_NESTED_CONST_OOB_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_output_nested_const_oob.nql"
IO_BROKEN_PIPE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_broken_pipe.nql"
IO_SECOND_OUTPUT_PATCH_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_second_output_patch.nql"
IO_FULL_RANGE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_full_range.nql"
IO_NEGATIVE_RANGE_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/io_negative_range.nql"
UNKNOWN_CALL_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/unknown_call.nql"
UNKNOWN_CALL_SEMANTIC_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/unknown_call_semantic.nql"
UNKNOWN_ASSIGNMENT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/unknown_assignment.nql"
TYPE_MISMATCH_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/type_mismatch.nql"
DIV_ZERO_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/div_zero.nql"
DIV_ZERO_EXPRESSION_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/div_zero_expression.nql"
DIV_OVERFLOW_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/div_overflow_expression.nql"
OUTPUT_LIMIT_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/output_limit.nql"
INVALID_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/invalid_token.nql"
MISSING_MAIN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/missing_main.nql"
LEXER_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/lexer_core0.nql"
UNTERMINATED_STRING_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/unterminated_string.nql"
UNCLOSED_BLOCK_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/unclosed_block.nql"
LEFTOVER_TOKEN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/leftover_token.nql"
DUPLICATE_MAIN_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/b0/duplicate_main.nql"

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

manifest_row="$(awk -F '\t' '$1 == "bootstrap-compiler" { print $2 "\t" $3 "\t" $4 }' "$MANIFEST")"
expected_manifest_row=$'PASS\tbootstrap/compiler/b0/x86_64-linux/b0.seed\ttests/bootstrap/bootstrap_compiler_b0.sh'
[[ "$manifest_row" == "$expected_manifest_row" ]] || \
    fail_test "b0-manifest-pass"
printf 'PASS b0-manifest-pass\n'

[[ -d "$B0_DIR" ]] || fail_test "b0-scaffold-directory"
[[ -f "$B0_DIR/README.md" ]] || fail_test "b0-scaffold-readme"
[[ -f "$B0_DIR/compiler.nql0" ]] || fail_test "b0-scaffold-source"
[[ -x "$MATERIALIZER" ]] || fail_test "b0-scaffold-materializer"
printf 'PASS b0-scaffold-layout\n'

[[ -x "$SEED" ]] || fail_test "b0-seed-is-executable"
printf 'PASS b0-seed-is-executable\n'

[[ -f "$HASH" ]] || fail_test "b0-hash-present"
printf 'PASS b0-hash-present\n'

grep -Fq '%define INPUT_CAP 327680' "$REFERENCE_ASM" || \
    fail_test "b0-c018-input-capacity"
awk 'BEGIN {
    suffix = "\nfn main() { return 7 }\n"
    printf "#"
    for (i = 1; i < 327680 - length(suffix); i++) printf "x"
    printf "%s", suffix
}' > "$TMP_DIR/b0.input-cap-exact.nql"
[[ "$(wc -c < "$TMP_DIR/b0.input-cap-exact.nql")" -eq 327680 ]] || \
    fail_test "b0-input-cap-exact-fixture-size"
run_output "$SEED" "$TMP_DIR/b0.input-cap-exact.nql" \
    -o "$TMP_DIR/b0.input-cap-exact.out" \
    > "$TMP_DIR/b0.input-cap-exact.stdout" \
    2> "$TMP_DIR/b0.input-cap-exact.stderr"
[[ ! -s "$TMP_DIR/b0.input-cap-exact.stdout" ]] || \
    fail_test "b0-input-cap-exact-stdout"
[[ ! -s "$TMP_DIR/b0.input-cap-exact.stderr" ]] || \
    fail_test "b0-input-cap-exact-stderr"
chmod 0755 "$TMP_DIR/b0.input-cap-exact.out"
set +e
run_output_bounded 5 "$TMP_DIR/b0.input-cap-exact.out" >/dev/null
input_cap_exact_status=$?
set -e
[[ "$input_cap_exact_status" -eq 7 ]] || \
    fail_test "b0-input-cap-exact-run (expected 7, got $input_cap_exact_status)"

{
    printf '#'
    head -c 327680 /dev/zero | tr '\0' x
} > "$TMP_DIR/b0.input-cap-overflow.nql"
[[ "$(wc -c < "$TMP_DIR/b0.input-cap-overflow.nql")" -eq 327681 ]] || \
    fail_test "b0-input-cap-overflow-fixture-size"
set +e
run_output "$SEED" "$TMP_DIR/b0.input-cap-overflow.nql" \
    -o "$TMP_DIR/b0.input-cap-overflow.out" \
    > "$TMP_DIR/b0.input-cap-overflow.stdout" \
    2> "$TMP_DIR/b0.input-cap-overflow.stderr"
input_cap_overflow_status=$?
set -e
[[ "$input_cap_overflow_status" -eq 1 ]] || \
    fail_test "b0-input-cap-overflow-status (expected 1, got $input_cap_overflow_status)"
[[ ! -s "$TMP_DIR/b0.input-cap-overflow.stdout" ]] || \
    fail_test "b0-input-cap-overflow-stdout"
[[ ! -e "$TMP_DIR/b0.input-cap-overflow.out" ]] || \
    fail_test "b0-input-cap-overflow-output"
grep -Fq 'error[B0-IO-003]: input exceeds 327680-byte limit' \
    "$TMP_DIR/b0.input-cap-overflow.stderr" || \
    fail_test "b0-input-cap-overflow-diagnostic"
printf 'PASS b0-c018-input-capacity-boundary\n'

grep -Fq '%define BYTE_ACCESS_CAP 5376' "$REFERENCE_ASM" || \
    fail_test "b0-c024-byte-access-capacity"
printf 'PASS b0-c024-byte-access-capacity\n'

awk 'BEGIN {
    print "fn main() { let i = 0"
    for (n = 0; n < 5376; n++) print "byte_store(i, 0)"
    print "return 0 }"
}' > "$TMP_DIR/b0.byte-access-cap-exact.nql"
run_output "$SEED" "$TMP_DIR/b0.byte-access-cap-exact.nql" \
    -o "$TMP_DIR/b0.byte-access-cap-exact.out" \
    > "$TMP_DIR/b0.byte-access-cap-exact.stdout" \
    2> "$TMP_DIR/b0.byte-access-cap-exact.stderr"
[[ ! -s "$TMP_DIR/b0.byte-access-cap-exact.stdout" ]] || \
    fail_test "b0-byte-access-cap-exact-stdout"
[[ ! -s "$TMP_DIR/b0.byte-access-cap-exact.stderr" ]] || \
    fail_test "b0-byte-access-cap-exact-stderr"
set +e
run_output_bounded 5 "$TMP_DIR/b0.byte-access-cap-exact.out" >/dev/null
byte_access_cap_exact_status=$?
set -e
[[ "$byte_access_cap_exact_status" -eq 0 ]] || \
    fail_test "b0-byte-access-cap-exact-run (expected 0, got $byte_access_cap_exact_status)"

awk 'BEGIN {
    print "fn main() { let i = 0"
    for (n = 0; n < 5377; n++) print "byte_store(i, 0)"
    print "return 0 }"
}' > "$TMP_DIR/b0.byte-access-cap-overflow.nql"
set +e
run_output "$SEED" "$TMP_DIR/b0.byte-access-cap-overflow.nql" \
    -o "$TMP_DIR/b0.byte-access-cap-overflow.out" \
    > "$TMP_DIR/b0.byte-access-cap-overflow.stdout" \
    2> "$TMP_DIR/b0.byte-access-cap-overflow.stderr"
byte_access_cap_overflow_status=$?
set -e
[[ "$byte_access_cap_overflow_status" -eq 1 ]] || \
    fail_test "b0-byte-access-cap-overflow-status (expected 1, got $byte_access_cap_overflow_status)"
[[ ! -s "$TMP_DIR/b0.byte-access-cap-overflow.stdout" ]] || \
    fail_test "b0-byte-access-cap-overflow-stdout"
[[ ! -e "$TMP_DIR/b0.byte-access-cap-overflow.out" ]] || \
    fail_test "b0-byte-access-cap-overflow-output"
grep -Fq 'error[B0-CG-005]' "$TMP_DIR/b0.byte-access-cap-overflow.stderr" || \
    fail_test "b0-byte-access-cap-overflow-diagnostic"
printf 'PASS b0-c024-byte-access-capacity-boundary\n'

grep -Fq '%define OUTPUT_CAP 589824' "$REFERENCE_ASM" || \
    fail_test "b0-c021-output-capacity"
printf 'PASS b0-c021-output-capacity\n'

"$MATERIALIZER" "$TMP_DIR/b0.materialized" >/dev/null
cmp -s "$SEED" "$TMP_DIR/b0.materialized" || \
    fail_test "b0-built-by-stage0"
printf 'PASS b0-built-by-stage0\n'

"$MATERIALIZER" "$TMP_DIR/b0.materialized.one" >/dev/null
"$MATERIALIZER" "$TMP_DIR/b0.materialized.two" >/dev/null
cmp -s "$TMP_DIR/b0.materialized.one" "$TMP_DIR/b0.materialized.two" || \
    fail_test "b0-deterministic-two-materializations"
printf 'PASS b0-deterministic-two-materializations\n'

expected_hash="$(awk '{ print $1 }' "$HASH")"
actual_hash="$(sha256sum "$SEED")"
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || fail_test "b0-hash"
printf 'PASS b0-hash\n'

if command -v nasm >/dev/null 2>&1; then
    (
        cd "$ROOT_DIR"
        nasm -f bin -o "$TMP_DIR/b0.reference.seed" \
            bootstrap/compiler/b0/x86_64-linux/b0.reference.asm
    )
    cmp -s "$SEED" "$TMP_DIR/b0.reference.seed" || \
        fail_test "b0-reference-assembly-parity"
    printf 'PASS b0-reference-assembly-parity\n'
else
    printf 'SKIP b0-reference-assembly-parity (nasm unavailable)\n'
fi

if grep -Eiq '(nasm|(^|[^[:alpha:]])ld([^[:alpha:]]|$)|python|llvm|gcc|clang|rustc|nolquc|(^|[^[:alpha:]])nq([^[:alpha:]]|$))' \
    "$MATERIALIZER"; then
    fail_test "b0-scaffold-no-host-toolchain-reference"
fi
printf 'PASS b0-scaffold-no-host-toolchain-reference\n'

run_output "$SEED" --help > "$TMP_DIR/b0.help.stdout" 2> "$TMP_DIR/b0.help.stderr"
printf 'usage: b0 <input.nql> -o <output>\n' > "$TMP_DIR/b0.help.expected"
cmp -s "$TMP_DIR/b0.help.expected" "$TMP_DIR/b0.help.stdout" || \
    fail_test "b0-help"
[[ ! -s "$TMP_DIR/b0.help.stderr" ]] || fail_test "b0-help-stderr"
printf 'PASS b0-help\n'

run_output "$SEED" --lex "$LEXER_FIXTURE" \
    > "$TMP_DIR/b0.lex.stdout" 2> "$TMP_DIR/b0.lex.stderr"
cat > "$TMP_DIR/b0.lex.expected" <<'EXPECTED'
KW fn
IDENT main
PUNCT (
PUNCT )
PUNCT {
KW let
IDENT answer
PUNCT =
INT 42
KW if
IDENT answer
PUNCT ==
INT 42
PUNCT {
IDENT write
PUNCT (
STRING ok
PUNCT )
PUNCT }
KW else
PUNCT {
KW while
IDENT answer
PUNCT <=
INT 42
PUNCT {
KW return
INT 0
PUNCT }
PUNCT }
PUNCT }
EXPECTED
cmp -s "$TMP_DIR/b0.lex.expected" "$TMP_DIR/b0.lex.stdout" || \
    fail_test "b0-lex-token-stream"
[[ ! -s "$TMP_DIR/b0.lex.stderr" ]] || fail_test "b0-lex-stderr"
printf 'PASS b0-lex-keywords\n'
printf 'PASS b0-lex-identifiers\n'
printf 'PASS b0-lex-integers\n'
printf 'PASS b0-lex-strings\n'
printf 'PASS b0-lex-comments-whitespace\n'

set +e
run_output "$SEED" --lex "$INVALID_FIXTURE" \
    > "$TMP_DIR/b0.lex-invalid.stdout" 2> "$TMP_DIR/b0.lex-invalid.stderr"
lex_invalid_status=$?
set -e
[[ "$lex_invalid_status" -eq 1 ]] || \
    fail_test "b0-lex-invalid-character-status (expected 1, got $lex_invalid_status)"
[[ ! -s "$TMP_DIR/b0.lex-invalid.stdout" ]] || fail_test "b0-lex-invalid-character-stdout"
grep -Fq 'error[B0-LEX-001]' "$TMP_DIR/b0.lex-invalid.stderr" || \
    fail_test "b0-lex-invalid-character-diagnostic"
printf 'PASS b0-lex-invalid-character\n'
printf 'PASS b0-lex-progress-on-invalid-input\n'

set +e
run_output "$SEED" --lex "$UNTERMINATED_STRING_FIXTURE" \
    > "$TMP_DIR/b0.lex-string.stdout" 2> "$TMP_DIR/b0.lex-string.stderr"
lex_string_status=$?
set -e
[[ "$lex_string_status" -eq 1 ]] || \
    fail_test "b0-lex-unterminated-string-status (expected 1, got $lex_string_status)"
[[ ! -s "$TMP_DIR/b0.lex-string.stdout" ]] || fail_test "b0-lex-unterminated-string-stdout"
grep -Fq 'error[B0-LEX-002]' "$TMP_DIR/b0.lex-string.stderr" || \
    fail_test "b0-lex-unterminated-string-diagnostic"
printf 'PASS b0-lex-unterminated-string\n'

run_output "$SEED" --parse "$RETURN7_FIXTURE" \
    > "$TMP_DIR/b0.parse-return.stdout" 2> "$TMP_DIR/b0.parse-return.stderr"
printf 'PARSE OK\n' > "$TMP_DIR/b0.parse.expected"
cmp -s "$TMP_DIR/b0.parse.expected" "$TMP_DIR/b0.parse-return.stdout" || \
    fail_test "b0-parse-return-stdout"
[[ ! -s "$TMP_DIR/b0.parse-return.stderr" ]] || fail_test "b0-parse-return-stderr"
printf 'PASS b0-parse-return\n'

run_output "$SEED" --parse "$LEXER_FIXTURE" \
    > "$TMP_DIR/b0.parse-core0.stdout" 2> "$TMP_DIR/b0.parse-core0.stderr"
cmp -s "$TMP_DIR/b0.parse.expected" "$TMP_DIR/b0.parse-core0.stdout" || \
    fail_test "b0-parse-core0-stdout"
[[ ! -s "$TMP_DIR/b0.parse-core0.stderr" ]] || fail_test "b0-parse-core0-stderr"
printf 'PASS b0-parse-let\n'
printf 'PASS b0-parse-call\n'
printf 'PASS b0-parse-binary-precedence\n'
printf 'PASS b0-parse-if-else\n'
printf 'PASS b0-parse-while\n'

run_output "$SEED" --parse "$WHILE_SEMANTIC_FIXTURE" \
    > "$TMP_DIR/b0.parse-assignment.stdout" 2> "$TMP_DIR/b0.parse-assignment.stderr"
cmp -s "$TMP_DIR/b0.parse.expected" "$TMP_DIR/b0.parse-assignment.stdout" || \
    fail_test "b0-parse-assignment-stdout"
[[ ! -s "$TMP_DIR/b0.parse-assignment.stderr" ]] || \
    fail_test "b0-parse-assignment-stderr"
printf 'PASS b0-parse-assignment\n'

run_output "$SEED" --parse "$BYTE_MEMORY_FIXTURE" \
    > "$TMP_DIR/b0.parse-byte-memory.stdout" \
    2> "$TMP_DIR/b0.parse-byte-memory.stderr"
cmp -s "$TMP_DIR/b0.parse.expected" "$TMP_DIR/b0.parse-byte-memory.stdout" || \
    fail_test "b0-parse-byte-memory-stdout"
[[ ! -s "$TMP_DIR/b0.parse-byte-memory.stderr" ]] || \
    fail_test "b0-parse-byte-memory-stderr"
printf 'PASS b0-parse-byte-memory-calls\n'

set +e
run_output "$SEED" --parse "$MISSING_MAIN_FIXTURE" \
    > "$TMP_DIR/b0.parse-missing.stdout" 2> "$TMP_DIR/b0.parse-missing.stderr"
parse_missing_status=$?
set -e
[[ "$parse_missing_status" -eq 1 ]] || \
    fail_test "b0-parse-missing-main-status (expected 1, got $parse_missing_status)"
[[ ! -s "$TMP_DIR/b0.parse-missing.stdout" ]] || fail_test "b0-parse-missing-main-stdout"
grep -Fq 'error[B0-PARSE-001]' "$TMP_DIR/b0.parse-missing.stderr" || \
    fail_test "b0-parse-missing-main-diagnostic"
printf 'PASS b0-parse-missing-main\n'

set +e
run_output "$SEED" --parse "$UNCLOSED_BLOCK_FIXTURE" \
    > "$TMP_DIR/b0.parse-unclosed.stdout" 2> "$TMP_DIR/b0.parse-unclosed.stderr"
parse_unclosed_status=$?
set -e
[[ "$parse_unclosed_status" -eq 1 ]] || \
    fail_test "b0-parse-unclosed-block-status (expected 1, got $parse_unclosed_status)"
[[ ! -s "$TMP_DIR/b0.parse-unclosed.stdout" ]] || fail_test "b0-parse-unclosed-block-stdout"
grep -Fq 'error[B0-PARSE-001]' "$TMP_DIR/b0.parse-unclosed.stderr" || \
    fail_test "b0-parse-unclosed-block-diagnostic"
printf 'PASS b0-parse-unclosed-block\n'

set +e
run_output "$SEED" --parse "$LEFTOVER_TOKEN_FIXTURE" \
    > "$TMP_DIR/b0.parse-leftover.stdout" 2> "$TMP_DIR/b0.parse-leftover.stderr"
parse_leftover_status=$?
set -e
[[ "$parse_leftover_status" -eq 1 ]] || \
    fail_test "b0-parse-leftover-token-status (expected 1, got $parse_leftover_status)"
[[ ! -s "$TMP_DIR/b0.parse-leftover.stdout" ]] || fail_test "b0-parse-leftover-token-stdout"
grep -Fq 'error[B0-PARSE-001]' "$TMP_DIR/b0.parse-leftover.stderr" || \
    fail_test "b0-parse-leftover-token-diagnostic"
printf 'PASS b0-parse-leftover-token\n'

set +e
run_output "$SEED" --parse "$DUPLICATE_MAIN_FIXTURE" \
    > "$TMP_DIR/b0.parse-duplicate.stdout" 2> "$TMP_DIR/b0.parse-duplicate.stderr"
parse_duplicate_status=$?
set -e
[[ "$parse_duplicate_status" -eq 1 ]] || \
    fail_test "b0-parse-duplicate-function-status (expected 1, got $parse_duplicate_status)"
[[ ! -s "$TMP_DIR/b0.parse-duplicate.stdout" ]] || fail_test "b0-parse-duplicate-function-stdout"
grep -Fq 'error[B0-PARSE-001]' "$TMP_DIR/b0.parse-duplicate.stderr" || \
    fail_test "b0-parse-duplicate-function-diagnostic"
printf 'PASS b0-parse-duplicate-function\n'

run_output "$SEED" "$RETURN7_FIXTURE" -o "$TMP_DIR/return7.one" \
    > "$TMP_DIR/b0.return7.stdout" 2> "$TMP_DIR/b0.return7.stderr"
[[ ! -s "$TMP_DIR/b0.return7.stdout" ]] || fail_test "b0-compile-return7-stdout"
[[ ! -s "$TMP_DIR/b0.return7.stderr" ]] || fail_test "b0-compile-return7-stderr"
printf 'PASS b0-no-executable-bytes-on-stdout\n'
[[ -x "$TMP_DIR/return7.one" ]] || fail_test "b0-compile-return7-executable"
set +e
run_output "$TMP_DIR/return7.one" >/dev/null 2>"$TMP_DIR/return7.one.stderr"
return7_status=$?
set -e
[[ "$return7_status" -eq 7 ]] || \
    fail_test "b0-compile-return7-run (expected 7, got $return7_status)"
printf 'PASS b0-compile-return7\n'

run_output "$SEED" "$RETURN23_FIXTURE" -o "$TMP_DIR/return23.out" \
    > "$TMP_DIR/b0.return23.stdout" 2> "$TMP_DIR/b0.return23.stderr"
[[ ! -s "$TMP_DIR/b0.return23.stdout" ]] || fail_test "b0-codegen-return-literal-stdout"
[[ ! -s "$TMP_DIR/b0.return23.stderr" ]] || fail_test "b0-codegen-return-literal-stderr"
[[ -x "$TMP_DIR/return23.out" ]] || fail_test "b0-codegen-return-literal-executable"
set +e
run_output "$TMP_DIR/return23.out" >/dev/null 2> "$TMP_DIR/return23.stderr"
return23_status=$?
set -e
[[ "$return23_status" -eq 23 ]] || \
    fail_test "b0-codegen-return-literal-run (expected 23, got $return23_status)"
[[ ! -s "$TMP_DIR/return23.stderr" ]] || fail_test "b0-codegen-return-literal-run-stderr"
cmp -s "$TMP_DIR/return7.one" "$TMP_DIR/return23.out" && \
    fail_test "b0-codegen-return-literal-not-canned"
printf 'PASS b0-codegen-return-literal\n'

run_output "$SEED" "$RETURN7_FIXTURE" -o "$TMP_DIR/return7.two" >/dev/null
cmp -s "$TMP_DIR/return7.one" "$TMP_DIR/return7.two" || \
    fail_test "b0-deterministic-return7"
printf 'PASS b0-deterministic-return7\n'
printf 'PASS b0-deterministic-two-builds\n'

if command -v readelf >/dev/null 2>&1; then
    readelf -l "$TMP_DIR/return7.one" > "$TMP_DIR/return7.readelf"
    grep -q 'GNU_STACK' "$TMP_DIR/return7.readelf" || \
        fail_test "b0-return7-gnu-stack"
    ! grep -q 'Requesting program interpreter' "$TMP_DIR/return7.readelf" || \
        fail_test "b0-return7-no-interpreter"
    printf 'PASS b0-return7-elf-static\n'
    printf 'PASS b0-codegen-elf-static\n'
    printf 'PASS b0-codegen-non-executable-stack\n'
else
    printf 'SKIP b0-return7-elf-static (readelf unavailable)\n'
    printf 'SKIP b0-codegen-elf-static (readelf unavailable)\n'
    printf 'SKIP b0-codegen-non-executable-stack (readelf unavailable)\n'
fi

run_output "$SEED" "$WRITE_STRING_FIXTURE" -o "$TMP_DIR/write-string.one" \
    > "$TMP_DIR/b0.write-string.stdout" 2> "$TMP_DIR/b0.write-string.stderr"
[[ ! -s "$TMP_DIR/b0.write-string.stdout" ]] || fail_test "b0-codegen-write-string-stdout"
[[ ! -s "$TMP_DIR/b0.write-string.stderr" ]] || fail_test "b0-codegen-write-string-stderr"
[[ -x "$TMP_DIR/write-string.one" ]] || fail_test "b0-codegen-write-string-executable"
run_output "$TMP_DIR/write-string.one" > "$TMP_DIR/write-string.run.stdout" \
    2> "$TMP_DIR/write-string.run.stderr"
printf 'B0\n' > "$TMP_DIR/write-string.expected"
cmp -s "$TMP_DIR/write-string.expected" "$TMP_DIR/write-string.run.stdout" || \
    fail_test "b0-codegen-write-string-output"
[[ ! -s "$TMP_DIR/write-string.run.stderr" ]] || fail_test "b0-codegen-write-string-run-stderr"
printf 'PASS b0-codegen-write-string\n'

set +e
run_output "$SEED" "$WRITE_LITERAL_FIXTURE" -o "$TMP_DIR/write-literal.out" \
    > "$TMP_DIR/b0.write-literal.stdout" 2> "$TMP_DIR/b0.write-literal.stderr"
write_literal_compile_status=$?
set -e
[[ "$write_literal_compile_status" -eq 0 ]] || \
    fail_test "b0-codegen-write-literal-compile-status (expected 0, got $write_literal_compile_status)"
[[ ! -s "$TMP_DIR/b0.write-literal.stdout" ]] || fail_test "b0-codegen-write-literal-stdout"
[[ ! -s "$TMP_DIR/b0.write-literal.stderr" ]] || fail_test "b0-codegen-write-literal-stderr"
[[ -x "$TMP_DIR/write-literal.out" ]] || fail_test "b0-codegen-write-literal-executable"
set +e
run_output "$TMP_DIR/write-literal.out" > "$TMP_DIR/write-literal.run.stdout" \
    2> "$TMP_DIR/write-literal.run.stderr"
write_literal_status=$?
set -e
[[ "$write_literal_status" -eq 5 ]] || \
    fail_test "b0-codegen-write-literal-run (expected 5, got $write_literal_status)"
printf 'Core-0 dynamic\n' > "$TMP_DIR/write-literal.expected"
cmp -s "$TMP_DIR/write-literal.expected" "$TMP_DIR/write-literal.run.stdout" || \
    fail_test "b0-codegen-write-literal-output"
[[ ! -s "$TMP_DIR/write-literal.run.stderr" ]] || fail_test "b0-codegen-write-literal-run-stderr"
printf 'PASS b0-codegen-write-literal\n'

run_output "$SEED" "$WRITE_STRING_FIXTURE" -o "$TMP_DIR/write-string.two" >/dev/null
cmp -s "$TMP_DIR/write-string.one" "$TMP_DIR/write-string.two" || \
    fail_test "b0-deterministic-write-string"
printf 'PASS b0-deterministic-write-string\n'

run_output "$SEED" "$ARITHMETIC_FIXTURE" -o "$TMP_DIR/arithmetic.out" >/dev/null
set +e
run_output "$TMP_DIR/arithmetic.out" >/dev/null 2> "$TMP_DIR/arithmetic.stderr"
arithmetic_status=$?
set -e
[[ "$arithmetic_status" -eq 14 ]] || \
    fail_test "b0-codegen-arithmetic-run (expected 14, got $arithmetic_status)"
[[ ! -s "$TMP_DIR/arithmetic.stderr" ]] || fail_test "b0-codegen-arithmetic-stderr"
printf 'PASS b0-codegen-arithmetic\n'

run_output "$SEED" "$EXPRESSION_FIXTURE" -o "$TMP_DIR/expression.out" \
    > "$TMP_DIR/b0.expression.stdout" 2> "$TMP_DIR/b0.expression.stderr"
[[ ! -s "$TMP_DIR/b0.expression.stdout" ]] || fail_test "b0-codegen-semantic-expression-stdout"
[[ ! -s "$TMP_DIR/b0.expression.stderr" ]] || fail_test "b0-codegen-semantic-expression-stderr"
[[ -x "$TMP_DIR/expression.out" ]] || fail_test "b0-codegen-semantic-expression-executable"
set +e
run_output "$TMP_DIR/expression.out" >/dev/null 2> "$TMP_DIR/expression.stderr"
expression_status=$?
set -e
[[ "$expression_status" -eq 1 ]] || \
    fail_test "b0-codegen-semantic-expression-run (expected 1, got $expression_status)"
[[ ! -s "$TMP_DIR/expression.stderr" ]] || fail_test "b0-codegen-semantic-expression-run-stderr"
printf 'PASS b0-codegen-semantic-expression\n'

run_output "$SEED" "$COMPARISON_FIXTURE" -o "$TMP_DIR/comparison.out" >/dev/null
set +e
run_output "$TMP_DIR/comparison.out" >/dev/null 2> "$TMP_DIR/comparison.stderr"
comparison_status=$?
set -e
[[ "$comparison_status" -eq 1 ]] || \
    fail_test "b0-codegen-comparison-run (expected 1, got $comparison_status)"
[[ ! -s "$TMP_DIR/comparison.stderr" ]] || fail_test "b0-codegen-comparison-stderr"
printf 'PASS b0-codegen-comparison\n'

run_output "$SEED" "$IF_ELSE_FIXTURE" -o "$TMP_DIR/if-else.one" >/dev/null
set +e
run_output "$TMP_DIR/if-else.one" >/dev/null 2> "$TMP_DIR/if-else.stderr"
if_else_status=$?
set -e
[[ "$if_else_status" -eq 9 ]] || \
    fail_test "b0-codegen-if-else-run (expected 9, got $if_else_status)"
[[ ! -s "$TMP_DIR/if-else.stderr" ]] || fail_test "b0-codegen-if-else-stderr"
printf 'PASS b0-codegen-if-else\n'

run_output "$SEED" "$IF_ELSE_SEMANTIC_FIXTURE" -o "$TMP_DIR/if-else-semantic.out" \
    > "$TMP_DIR/b0.if-else-semantic.stdout" 2> "$TMP_DIR/b0.if-else-semantic.stderr"
[[ ! -s "$TMP_DIR/b0.if-else-semantic.stdout" ]] || \
    fail_test "b0-codegen-semantic-if-else-stdout"
[[ ! -s "$TMP_DIR/b0.if-else-semantic.stderr" ]] || \
    fail_test "b0-codegen-semantic-if-else-stderr"
[[ -x "$TMP_DIR/if-else-semantic.out" ]] || \
    fail_test "b0-codegen-semantic-if-else-executable"
set +e
run_output "$TMP_DIR/if-else-semantic.out" >/dev/null \
    2> "$TMP_DIR/if-else-semantic.stderr"
if_else_semantic_status=$?
set -e
[[ "$if_else_semantic_status" -eq 13 ]] || \
    fail_test "b0-codegen-semantic-if-else-run (expected 13, got $if_else_semantic_status)"
[[ ! -s "$TMP_DIR/if-else-semantic.stderr" ]] || \
    fail_test "b0-codegen-semantic-if-else-run-stderr"
printf 'PASS b0-codegen-semantic-if-else\n'

run_output "$SEED" "$IF_ELSE_FALSE_FIXTURE" -o "$TMP_DIR/if-else-false.out" >/dev/null
set +e
run_output "$TMP_DIR/if-else-false.out" >/dev/null 2> "$TMP_DIR/if-else-false.stderr"
if_else_false_status=$?
set -e
[[ "$if_else_false_status" -eq 7 ]] || \
    fail_test "b0-codegen-semantic-if-else-false (expected 7, got $if_else_false_status)"
[[ ! -s "$TMP_DIR/if-else-false.stderr" ]] || \
    fail_test "b0-codegen-semantic-if-else-false-stderr"
printf 'PASS b0-codegen-semantic-if-else-false\n'

run_output "$SEED" "$WHILE_SEMANTIC_FIXTURE" -o "$TMP_DIR/while-semantic.one" \
    > "$TMP_DIR/b0.while-semantic.stdout" 2> "$TMP_DIR/b0.while-semantic.stderr"
[[ ! -s "$TMP_DIR/b0.while-semantic.stdout" ]] || \
    fail_test "b0-codegen-while-backedge-stdout"
[[ ! -s "$TMP_DIR/b0.while-semantic.stderr" ]] || \
    fail_test "b0-codegen-while-backedge-stderr"
[[ -x "$TMP_DIR/while-semantic.one" ]] || \
    fail_test "b0-codegen-while-backedge-executable"
set +e
run_output_bounded 5 "$TMP_DIR/while-semantic.one" >/dev/null \
    2> "$TMP_DIR/while-semantic.run.stderr"
while_semantic_status=$?
set -e
[[ "$while_semantic_status" -eq 6 ]] || \
    fail_test "b0-codegen-while-backedge-run (expected 6, got $while_semantic_status)"
[[ ! -s "$TMP_DIR/while-semantic.run.stderr" ]] || \
    fail_test "b0-codegen-while-backedge-run-stderr"
printf 'PASS b0-codegen-while-backedge\n'

run_output "$SEED" "$WHILE_FALSE_FIXTURE" -o "$TMP_DIR/while-false.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/while-false.out" >/dev/null \
    2> "$TMP_DIR/while-false.stderr"
while_false_status=$?
set -e
[[ "$while_false_status" -eq 9 ]] || \
    fail_test "b0-codegen-while-zero-iteration (expected 9, got $while_false_status)"
[[ ! -s "$TMP_DIR/while-false.stderr" ]] || \
    fail_test "b0-codegen-while-zero-iteration-stderr"
printf 'PASS b0-codegen-while-zero-iteration\n'

run_output "$SEED" "$WHILE_SEMANTIC_FIXTURE" -o "$TMP_DIR/while-semantic.two" >/dev/null
cmp -s "$TMP_DIR/while-semantic.one" "$TMP_DIR/while-semantic.two" || \
    fail_test "b0-codegen-deterministic-loop-branches"
printf 'PASS b0-codegen-deterministic-loop-branches\n'

run_output "$SEED" "$WHILE_STATE_FIXTURE" -o "$TMP_DIR/while-state.one" \
    > "$TMP_DIR/b0.while-state.stdout" 2> "$TMP_DIR/b0.while-state.stderr"
[[ ! -s "$TMP_DIR/b0.while-state.stdout" ]] || \
    fail_test "b0-codegen-while-state-stdout"
[[ ! -s "$TMP_DIR/b0.while-state.stderr" ]] || \
    fail_test "b0-codegen-while-state-stderr"
set +e
run_output_bounded 5 "$TMP_DIR/while-state.one" >/dev/null \
    2> "$TMP_DIR/while-state.run.stderr"
while_state_status=$?
set -e
[[ "$while_state_status" -eq 3 ]] || \
    fail_test "b0-codegen-while-state-run (expected 3, got $while_state_status)"
[[ ! -s "$TMP_DIR/while-state.run.stderr" ]] || \
    fail_test "b0-codegen-while-state-run-stderr"
run_output "$SEED" "$WHILE_STATE_FIXTURE" -o "$TMP_DIR/while-state.two" >/dev/null
cmp -s "$TMP_DIR/while-state.one" "$TMP_DIR/while-state.two" || \
    fail_test "b0-codegen-while-state-deterministic"
printf 'PASS b0-codegen-while-state\n'

run_output "$SEED" "$BYTE_MEMORY_FIXTURE" -o "$TMP_DIR/byte-memory.one" \
    > "$TMP_DIR/b0.byte-memory.stdout" 2> "$TMP_DIR/b0.byte-memory.stderr"
[[ ! -s "$TMP_DIR/b0.byte-memory.stdout" ]] || \
    fail_test "b0-codegen-byte-memory-stdout"
[[ ! -s "$TMP_DIR/b0.byte-memory.stderr" ]] || \
    fail_test "b0-codegen-byte-memory-stderr"
[[ -x "$TMP_DIR/byte-memory.one" ]] || \
    fail_test "b0-codegen-byte-memory-executable"
set +e
run_output_bounded 5 "$TMP_DIR/byte-memory.one" >/dev/null \
    2> "$TMP_DIR/byte-memory.run.stderr"
byte_memory_status=$?
set -e
[[ "$byte_memory_status" -eq 46 ]] || \
    fail_test "b0-codegen-byte-memory-run (expected 46, got $byte_memory_status)"
[[ ! -s "$TMP_DIR/byte-memory.run.stderr" ]] || \
    fail_test "b0-codegen-byte-memory-run-stderr"
run_output "$SEED" "$BYTE_MEMORY_FIXTURE" -o "$TMP_DIR/byte-memory.two" >/dev/null
cmp -s "$TMP_DIR/byte-memory.one" "$TMP_DIR/byte-memory.two" || \
    fail_test "b0-codegen-byte-memory-deterministic"
printf 'PASS b0-codegen-byte-memory-mutable\n'

run_output "$SEED" "$BYTE_MEMORY_ZERO_FIXTURE" -o "$TMP_DIR/byte-memory-zero.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/byte-memory-zero.out" >/dev/null \
    2> "$TMP_DIR/byte-memory-zero.stderr"
byte_memory_zero_status=$?
set -e
[[ "$byte_memory_zero_status" -eq 0 ]] || \
    fail_test "b0-codegen-byte-memory-zero-init (expected 0, got $byte_memory_zero_status)"
[[ ! -s "$TMP_DIR/byte-memory-zero.stderr" ]] || \
    fail_test "b0-codegen-byte-memory-zero-init-stderr"
printf 'PASS b0-codegen-byte-memory-zero-init\n'

run_output "$SEED" "$BYTE_MEMORY_WIDTH_FIXTURE" -o "$TMP_DIR/byte-memory-width.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/byte-memory-width.out" >/dev/null \
    2> "$TMP_DIR/byte-memory-width.stderr"
byte_memory_width_status=$?
set -e
[[ "$byte_memory_width_status" -eq 127 ]] || \
    fail_test "b0-codegen-byte-memory-width (expected 127, got $byte_memory_width_status)"
[[ ! -s "$TMP_DIR/byte-memory-width.stderr" ]] || \
    fail_test "b0-codegen-byte-memory-width-stderr"
printf 'PASS b0-codegen-byte-memory-width\n'

run_output "$SEED" "$BYTE_MEMORY_BOUNDARY_FIXTURE" \
    -o "$TMP_DIR/byte-memory-boundary.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/byte-memory-boundary.out" >/dev/null \
    2> "$TMP_DIR/byte-memory-boundary.stderr"
byte_memory_boundary_status=$?
set -e
[[ "$byte_memory_boundary_status" -eq 37 ]] || \
    fail_test "b0-codegen-byte-memory-boundary-layout (expected 37, got $byte_memory_boundary_status)"
[[ ! -s "$TMP_DIR/byte-memory-boundary.stderr" ]] || \
    fail_test "b0-codegen-byte-memory-boundary-layout-stderr"
printf 'PASS b0-codegen-byte-memory-boundary-layout\n'

run_output "$SEED" "$BYTE_LOAD_LOCAL_FIXTURE" -o "$TMP_DIR/byte-load-local.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/byte-load-local.out" >/dev/null \
    2> "$TMP_DIR/byte-load-local.stderr"
byte_load_local_status=$?
set -e
[[ "$byte_load_local_status" -eq 37 ]] || \
    fail_test "b0-codegen-byte-load-local-resolution (expected 37, got $byte_load_local_status)"
[[ ! -s "$TMP_DIR/byte-load-local.stderr" ]] || \
    fail_test "b0-codegen-byte-load-local-resolution-stderr"
printf 'PASS b0-codegen-byte-load-local-resolution\n'

printf 'old-output' > "$TMP_DIR/byte-memory-const-oob.out"
set +e
run_output "$SEED" "$BYTE_MEMORY_CONST_OOB_FIXTURE" \
    -o "$TMP_DIR/byte-memory-const-oob.out" \
    > "$TMP_DIR/b0.byte-memory-const-oob.stdout" \
    2> "$TMP_DIR/b0.byte-memory-const-oob.stderr"
byte_memory_const_oob_status=$?
set -e
[[ "$byte_memory_const_oob_status" -eq 1 ]] || \
    fail_test "b0-codegen-byte-memory-const-oob-status (expected 1, got $byte_memory_const_oob_status)"
[[ ! -s "$TMP_DIR/b0.byte-memory-const-oob.stdout" ]] || \
    fail_test "b0-codegen-byte-memory-const-oob-stdout"
grep -Fq "$BYTE_MEMORY_CONST_OOB_FIXTURE:2:12: error[B0-CG-008]" \
    "$TMP_DIR/b0.byte-memory-const-oob.stderr" || \
    fail_test "b0-codegen-byte-memory-const-oob-diagnostic"
printf 'old-output' > "$TMP_DIR/byte-memory-const-oob.expected"
cmp -s "$TMP_DIR/byte-memory-const-oob.expected" \
    "$TMP_DIR/byte-memory-const-oob.out" || \
    fail_test "b0-codegen-byte-memory-const-oob-preserves-output"
printf 'PASS b0-codegen-byte-memory-const-oob\n'

run_output "$SEED" "$BYTE_MEMORY_RUNTIME_OOB_FIXTURE" \
    -o "$TMP_DIR/byte-memory-runtime-oob.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/byte-memory-runtime-oob.out" \
    > "$TMP_DIR/byte-memory-runtime-oob.stdout" \
    2> "$TMP_DIR/byte-memory-runtime-oob.stderr"
byte_memory_runtime_oob_status=$?
set -e
[[ "$byte_memory_runtime_oob_status" -eq 70 ]] || \
    fail_test "b0-codegen-byte-memory-runtime-oob-status (expected 70, got $byte_memory_runtime_oob_status)"
[[ ! -s "$TMP_DIR/byte-memory-runtime-oob.stdout" ]] || \
    fail_test "b0-codegen-byte-memory-runtime-oob-stdout"
printf 'B0 runtime: byte-memory index out of bounds\n' \
    > "$TMP_DIR/byte-memory-runtime-oob.expected"
cmp -s "$TMP_DIR/byte-memory-runtime-oob.expected" \
    "$TMP_DIR/byte-memory-runtime-oob.stderr" || \
    fail_test "b0-codegen-byte-memory-runtime-oob-diagnostic"
printf 'PASS b0-codegen-byte-memory-runtime-oob\n'

run_output "$SEED" "$BYTE_MEMORY_STORE_RUNTIME_OOB_FIXTURE" \
    -o "$TMP_DIR/byte-memory-store-runtime-oob.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/byte-memory-store-runtime-oob.out" \
    > "$TMP_DIR/byte-memory-store-runtime-oob.stdout" \
    2> "$TMP_DIR/byte-memory-store-runtime-oob.stderr"
byte_memory_store_runtime_oob_status=$?
set -e
[[ "$byte_memory_store_runtime_oob_status" -eq 70 ]] || \
    fail_test "b0-codegen-byte-memory-store-runtime-oob-status (expected 70, got $byte_memory_store_runtime_oob_status)"
[[ ! -s "$TMP_DIR/byte-memory-store-runtime-oob.stdout" ]] || \
    fail_test "b0-codegen-byte-memory-store-runtime-oob-stdout"
cmp -s "$TMP_DIR/byte-memory-runtime-oob.expected" \
    "$TMP_DIR/byte-memory-store-runtime-oob.stderr" || \
    fail_test "b0-codegen-byte-memory-store-runtime-oob-diagnostic"
printf 'PASS b0-codegen-byte-memory-store-runtime-oob\n'

runtime_message_count="$(grep -aoF 'B0 runtime: byte-memory index out of bounds' \
    "$TMP_DIR/byte-memory.one" | wc -l)"
[[ "$runtime_message_count" -eq 1 ]] || \
    fail_test "b0-codegen-byte-memory-single-handler (expected 1 message, got $runtime_message_count)"
printf 'PASS b0-codegen-byte-memory-single-handler\n'

set +e
run_output "$SEED" "$BYTE_STORE_MALFORMED_FIXTURE" \
    -o "$TMP_DIR/byte-store-malformed.out" \
    > "$TMP_DIR/b0.byte-store-malformed.stdout" \
    2> "$TMP_DIR/b0.byte-store-malformed.stderr"
byte_store_malformed_status=$?
set -e
[[ "$byte_store_malformed_status" -eq 1 ]] || \
    fail_test "b0-codegen-byte-store-malformed-status (expected 1, got $byte_store_malformed_status)"
[[ ! -s "$TMP_DIR/b0.byte-store-malformed.stdout" ]] || \
    fail_test "b0-codegen-byte-store-malformed-stdout"
[[ ! -e "$TMP_DIR/byte-store-malformed.out" ]] || \
    fail_test "b0-codegen-byte-store-malformed-output"
if grep -Fq 'error[B0-CG-008]' "$TMP_DIR/b0.byte-store-malformed.stderr"; then
    fail_test "b0-codegen-byte-store-malformed-not-bounds"
fi
grep -Fq 'error[B0-CG-001]' "$TMP_DIR/b0.byte-store-malformed.stderr" || \
    fail_test "b0-codegen-byte-store-malformed-diagnostic"
printf 'PASS b0-codegen-byte-store-malformed\n'

run_output "$SEED" --parse "$IO_ROUNDTRIP_FIXTURE" \
    > "$TMP_DIR/b0.parse-io.stdout" 2> "$TMP_DIR/b0.parse-io.stderr"
cmp -s "$TMP_DIR/b0.parse.expected" "$TMP_DIR/b0.parse-io.stdout" || \
    fail_test "b0-parse-runtime-io-stdout"
[[ ! -s "$TMP_DIR/b0.parse-io.stderr" ]] || \
    fail_test "b0-parse-runtime-io-stderr"
printf 'PASS b0-parse-runtime-io\n'

run_output "$SEED" "$IO_ROUNDTRIP_FIXTURE" -o "$TMP_DIR/io-roundtrip.one" \
    > "$TMP_DIR/b0.io-roundtrip.stdout" 2> "$TMP_DIR/b0.io-roundtrip.stderr"
[[ ! -s "$TMP_DIR/b0.io-roundtrip.stdout" ]] || \
    fail_test "b0-codegen-runtime-io-compile-stdout"
[[ ! -s "$TMP_DIR/b0.io-roundtrip.stderr" ]] || \
    fail_test "b0-codegen-runtime-io-compile-stderr"
printf 'NQ\000L\377\n' > "$TMP_DIR/io-roundtrip.input"
set +e
run_output_bounded 5 "$TMP_DIR/io-roundtrip.one" \
    < "$TMP_DIR/io-roundtrip.input" \
    > "$TMP_DIR/io-roundtrip.output" 2> "$TMP_DIR/io-roundtrip.stderr"
io_roundtrip_status=$?
set -e
[[ "$io_roundtrip_status" -eq 6 ]] || \
    fail_test "b0-codegen-runtime-io-status (expected 6, got $io_roundtrip_status)"
cmp -s "$TMP_DIR/io-roundtrip.input" "$TMP_DIR/io-roundtrip.output" || \
    fail_test "b0-codegen-runtime-io-byte-parity"
[[ ! -s "$TMP_DIR/io-roundtrip.stderr" ]] || \
    fail_test "b0-codegen-runtime-io-stderr"
run_output "$SEED" "$IO_ROUNDTRIP_FIXTURE" -o "$TMP_DIR/io-roundtrip.two" >/dev/null
cmp -s "$TMP_DIR/io-roundtrip.one" "$TMP_DIR/io-roundtrip.two" || \
    fail_test "b0-codegen-runtime-io-deterministic"
printf 'PASS b0-codegen-runtime-io-roundtrip\n'
printf 'PASS b0-codegen-runtime-io-deterministic\n'

set +e
run_output_bounded 5 "$TMP_DIR/io-roundtrip.one" < /dev/null \
    > "$TMP_DIR/io-eof.stdout" 2> "$TMP_DIR/io-eof.stderr"
io_eof_status=$?
set -e
[[ "$io_eof_status" -eq 0 ]] || \
    fail_test "b0-codegen-runtime-input-eof-status (expected 0, got $io_eof_status)"
[[ ! -s "$TMP_DIR/io-eof.stdout" ]] || \
    fail_test "b0-codegen-runtime-input-eof-stdout"
[[ ! -s "$TMP_DIR/io-eof.stderr" ]] || \
    fail_test "b0-codegen-runtime-input-eof-stderr"
printf 'PASS b0-codegen-runtime-input-eof\n'

set +e
run_with_invalid_standard_fd 0 run_output_bounded 5 "$TMP_DIR/io-roundtrip.one"  \
    > "$TMP_DIR/io-read-failure.stdout" 2> "$TMP_DIR/io-read-failure.stderr"
io_read_failure_status=$?
set -e
[[ "$io_read_failure_status" -eq 74 ]] || \
    fail_test "b0-codegen-runtime-input-error-status (expected 74, got $io_read_failure_status)"
[[ ! -s "$TMP_DIR/io-read-failure.stdout" ]] || \
    fail_test "b0-codegen-runtime-input-error-stdout"
printf 'B0 runtime: input_read failed; check standard input\n' \
    > "$TMP_DIR/io-read-failure.expected"
cmp -s "$TMP_DIR/io-read-failure.expected" "$TMP_DIR/io-read-failure.stderr" || \
    fail_test "b0-codegen-runtime-input-error-diagnostic"
printf 'PASS b0-codegen-runtime-input-error\n'

run_output "$SEED" "$IO_WRITE_FAILURE_FIXTURE" -o "$TMP_DIR/io-write-failure.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/io-write-failure.out" \
    > "$TMP_DIR/io-write-failure.stdout" 2> "$TMP_DIR/io-write-failure.stderr"
io_write_success_status=$?
set -e
[[ "$io_write_success_status" -eq 0 ]] || \
    fail_test "b0-codegen-runtime-output-success-status (expected 0, got $io_write_success_status)"
printf 'N' > "$TMP_DIR/io-write-failure.expected-output"
cmp -s "$TMP_DIR/io-write-failure.expected-output" "$TMP_DIR/io-write-failure.stdout" || \
    fail_test "b0-codegen-runtime-output-success"
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$TMP_DIR/io-write-failure.out" \
     2> "$TMP_DIR/io-write-failure-closed.stderr"
io_write_failure_status=$?
set -e
[[ "$io_write_failure_status" -eq 74 ]] || \
    fail_test "b0-codegen-runtime-output-error-status (expected 74, got $io_write_failure_status)"
printf 'B0 runtime: output_write failed; check standard output\n' \
    > "$TMP_DIR/io-write-failure-closed.expected"
cmp -s "$TMP_DIR/io-write-failure-closed.expected" \
    "$TMP_DIR/io-write-failure-closed.stderr" || \
    fail_test "b0-codegen-runtime-output-error-diagnostic"
printf 'PASS b0-codegen-runtime-output-error\n'

run_output "$SEED" --parse "$IO_ERROR_WRITE_FIXTURE" \
    > "$TMP_DIR/b0.parse-error-write.stdout" \
    2> "$TMP_DIR/b0.parse-error-write.stderr"
cmp -s "$TMP_DIR/b0.parse.expected" "$TMP_DIR/b0.parse-error-write.stdout" || \
    fail_test "b0-parse-error-write-stdout"
[[ ! -s "$TMP_DIR/b0.parse-error-write.stderr" ]] || \
    fail_test "b0-parse-error-write-stderr"
printf 'PASS b0-parse-error-write\n'

run_output "$SEED" "$IO_ERROR_WRITE_FIXTURE" -o "$TMP_DIR/io-error-write.out" \
    > "$TMP_DIR/b0.io-error-write.stdout" 2> "$TMP_DIR/b0.io-error-write.stderr"
[[ ! -s "$TMP_DIR/b0.io-error-write.stdout" ]] || \
    fail_test "b0-codegen-error-write-compile-stdout"
[[ ! -s "$TMP_DIR/b0.io-error-write.stderr" ]] || \
    fail_test "b0-codegen-error-write-compile-stderr"
set +e
run_output_bounded 5 "$TMP_DIR/io-error-write.out" \
    > "$TMP_DIR/io-error-write.stdout" 2> "$TMP_DIR/io-error-write.stderr"
io_error_write_status=$?
set -e
[[ "$io_error_write_status" -eq 0 ]] || \
    fail_test "b0-codegen-error-write-status (expected 0, got $io_error_write_status)"
[[ ! -s "$TMP_DIR/io-error-write.stdout" ]] || \
    fail_test "b0-codegen-error-write-stdout"
printf 'E' > "$TMP_DIR/io-error-write.expected"
cmp -s "$TMP_DIR/io-error-write.expected" "$TMP_DIR/io-error-write.stderr" || \
    fail_test "b0-codegen-error-write-stderr"
printf 'PASS b0-codegen-error-write\n'

set +e
run_with_invalid_standard_fd 2 run_output_bounded 5 "$TMP_DIR/io-error-write.out" \
    > "$TMP_DIR/io-error-write-closed.stdout"
io_error_write_failure_status=$?
set -e
[[ "$io_error_write_failure_status" -eq 74 ]] || \
    fail_test "b0-codegen-error-write-failure-status (expected 74, got $io_error_write_failure_status)"
[[ ! -s "$TMP_DIR/io-error-write-closed.stdout" ]] || \
    fail_test "b0-codegen-error-write-failure-stdout"
printf 'PASS b0-codegen-error-write-failure\n'

run_output "$SEED" "$IO_ERROR_WRITE_FULL_RANGE_FIXTURE" \
    -o "$TMP_DIR/io-error-write-full-range.out" >/dev/null
run_output_bounded 5 "$TMP_DIR/io-error-write-full-range.out" \
    > "$TMP_DIR/io-error-write-full-range.stdout" \
    2> "$TMP_DIR/io-error-write-full-range.stderr"
[[ ! -s "$TMP_DIR/io-error-write-full-range.stdout" ]] || \
    fail_test "b0-codegen-error-write-full-range-stdout"
[[ "$(wc -c < "$TMP_DIR/io-error-write-full-range.stderr")" -eq 65536 ]] || \
    fail_test "b0-codegen-error-write-full-range-size"
head -c 65536 /dev/zero > "$TMP_DIR/io-error-write-full-range.expected"
cmp -s "$TMP_DIR/io-error-write-full-range.expected" \
    "$TMP_DIR/io-error-write-full-range.stderr" || \
    fail_test "b0-codegen-error-write-full-range-bytes"
printf 'PASS b0-codegen-error-write-full-range\n'

set +e
run_output "$SEED" "$IO_ERROR_WRITE_CONST_OOB_FIXTURE" \
    -o "$TMP_DIR/io-error-write-const-oob.out" \
    > "$TMP_DIR/io-error-write-const-oob.stdout" \
    2> "$TMP_DIR/io-error-write-const-oob.stderr"
io_error_write_const_oob_status=$?
set -e
[[ "$io_error_write_const_oob_status" -eq 1 ]] || \
    fail_test "b0-codegen-error-write-const-oob-status (expected 1, got $io_error_write_const_oob_status)"
[[ ! -s "$TMP_DIR/io-error-write-const-oob.stdout" ]] || \
    fail_test "b0-codegen-error-write-const-oob-stdout"
[[ ! -e "$TMP_DIR/io-error-write-const-oob.out" ]] || \
    fail_test "b0-codegen-error-write-const-oob-output"
grep -Fq 'error[B0-CG-008]' "$TMP_DIR/io-error-write-const-oob.stderr" || \
    fail_test "b0-codegen-error-write-const-oob-diagnostic"
printf 'PASS b0-codegen-error-write-const-oob\n'

run_output "$SEED" "$IO_SECOND_OUTPUT_PATCH_FIXTURE" \
    -o "$TMP_DIR/io-second-output-patch.out" >/dev/null
set +e
run_with_invalid_standard_fd 1 run_output_bounded 5 "$TMP_DIR/io-second-output-patch.out" \
     2> "$TMP_DIR/io-second-output-patch.stderr"
io_second_output_patch_status=$?
set -e
[[ "$io_second_output_patch_status" -eq 74 ]] || \
    fail_test "b0-codegen-runtime-second-output-patch-status (expected 74, got $io_second_output_patch_status)"
cmp -s "$TMP_DIR/io-write-failure-closed.expected" \
    "$TMP_DIR/io-second-output-patch.stderr" || \
    fail_test "b0-codegen-runtime-second-output-patch-diagnostic"
printf 'PASS b0-codegen-runtime-second-output-patch\n'

run_output "$SEED" "$IO_BROKEN_PIPE_FIXTURE" -o "$TMP_DIR/io-broken-pipe.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/io-broken-pipe.out" \
    2> "$TMP_DIR/io-broken-pipe.stderr" | head -c 1 > /dev/null
io_broken_pipe_statuses=("${PIPESTATUS[@]}")
set -e
io_broken_pipe_status="${io_broken_pipe_statuses[0]}"
[[ "$io_broken_pipe_status" -eq 74 ]] || \
    fail_test "b0-codegen-runtime-broken-pipe-status (expected 74, got $io_broken_pipe_status)"
cmp -s "$TMP_DIR/io-write-failure-closed.expected" \
    "$TMP_DIR/io-broken-pipe.stderr" || \
    fail_test "b0-codegen-runtime-broken-pipe-diagnostic"
printf 'PASS b0-codegen-runtime-broken-pipe\n'

run_output "$SEED" "$IO_BOUNDARY_FIXTURE" -o "$TMP_DIR/io-boundary.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/io-boundary.out" \
    > "$TMP_DIR/io-boundary.stdout" 2> "$TMP_DIR/io-boundary.stderr"
io_boundary_status=$?
set -e
[[ "$io_boundary_status" -eq 0 ]] || \
    fail_test "b0-codegen-runtime-io-boundary-status (expected 0, got $io_boundary_status)"
printf 'Z' > "$TMP_DIR/io-boundary.expected"
cmp -s "$TMP_DIR/io-boundary.expected" "$TMP_DIR/io-boundary.stdout" || \
    fail_test "b0-codegen-runtime-io-boundary-output"
[[ ! -s "$TMP_DIR/io-boundary.stderr" ]] || \
    fail_test "b0-codegen-runtime-io-boundary-stderr"
printf 'PASS b0-codegen-runtime-io-boundary\n'

run_output "$SEED" "$IO_FULL_RANGE_FIXTURE" -o "$TMP_DIR/io-full-range.out" >/dev/null
run_output_bounded 5 "$TMP_DIR/io-full-range.out" \
    > "$TMP_DIR/io-full-range.stdout" 2> "$TMP_DIR/io-full-range.stderr"
[[ "$(wc -c < "$TMP_DIR/io-full-range.stdout")" -eq 65536 ]] || \
    fail_test "b0-codegen-runtime-io-full-range-size"
head -c 65536 /dev/zero > "$TMP_DIR/io-full-range.expected"
cmp -s "$TMP_DIR/io-full-range.expected" "$TMP_DIR/io-full-range.stdout" || \
    fail_test "b0-codegen-runtime-io-full-range-bytes"
[[ ! -s "$TMP_DIR/io-full-range.stderr" ]] || \
    fail_test "b0-codegen-runtime-io-full-range-stderr"
printf 'PASS b0-codegen-runtime-io-full-range\n'

run_output "$SEED" "$INPUT_READ_LOCAL_FIXTURE" -o "$TMP_DIR/input-read-local.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/input-read-local.out" >/dev/null \
    2> "$TMP_DIR/input-read-local.stderr"
input_read_local_status=$?
set -e
[[ "$input_read_local_status" -eq 23 ]] || \
    fail_test "b0-codegen-input-read-local-resolution (expected 23, got $input_read_local_status)"
[[ ! -s "$TMP_DIR/input-read-local.stderr" ]] || \
    fail_test "b0-codegen-input-read-local-resolution-stderr"
printf 'PASS b0-codegen-input-read-local-resolution\n'

for nested_fixture in "$IO_NESTED_CONST_OOB_FIXTURE" \
    "$IO_OUTPUT_NESTED_CONST_OOB_FIXTURE"; do
    nested_name="$(basename "$nested_fixture" .nql)"
    set +e
    run_output "$SEED" "$nested_fixture" -o "$TMP_DIR/$nested_name.out" \
        > "$TMP_DIR/$nested_name.stdout" 2> "$TMP_DIR/$nested_name.stderr"
    nested_status=$?
    set -e
    [[ "$nested_status" -eq 1 ]] || \
        fail_test "b0-codegen-runtime-$nested_name-status (expected 1, got $nested_status)"
    [[ ! -s "$TMP_DIR/$nested_name.stdout" ]] || \
        fail_test "b0-codegen-runtime-$nested_name-stdout"
    [[ ! -e "$TMP_DIR/$nested_name.out" ]] || \
        fail_test "b0-codegen-runtime-$nested_name-output"
    grep -Fq 'error[B0-CG-008]' "$TMP_DIR/$nested_name.stderr" || \
        fail_test "b0-codegen-runtime-$nested_name-diagnostic"
done
printf 'PASS b0-codegen-runtime-io-nested-const-oob\n'

printf 'old-output' > "$TMP_DIR/io-const-oob.out"
set +e
run_output "$SEED" "$IO_CONST_OOB_FIXTURE" -o "$TMP_DIR/io-const-oob.out" \
    > "$TMP_DIR/b0.io-const-oob.stdout" 2> "$TMP_DIR/b0.io-const-oob.stderr"
io_const_oob_status=$?
set -e
[[ "$io_const_oob_status" -eq 1 ]] || \
    fail_test "b0-codegen-runtime-io-const-oob-status (expected 1, got $io_const_oob_status)"
[[ ! -s "$TMP_DIR/b0.io-const-oob.stdout" ]] || \
    fail_test "b0-codegen-runtime-io-const-oob-stdout"
grep -Fq "$IO_CONST_OOB_FIXTURE:2:17: error[B0-CG-008]" \
    "$TMP_DIR/b0.io-const-oob.stderr" || \
    fail_test "b0-codegen-runtime-io-const-oob-diagnostic"
printf 'old-output' > "$TMP_DIR/io-const-oob.expected"
cmp -s "$TMP_DIR/io-const-oob.expected" "$TMP_DIR/io-const-oob.out" || \
    fail_test "b0-codegen-runtime-io-const-oob-preserves-output"
printf 'PASS b0-codegen-runtime-io-const-oob\n'

run_output "$SEED" "$IO_RUNTIME_OOB_FIXTURE" -o "$TMP_DIR/io-runtime-oob.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/io-runtime-oob.out" \
    > "$TMP_DIR/io-runtime-oob.stdout" 2> "$TMP_DIR/io-runtime-oob.stderr"
io_runtime_oob_status=$?
set -e
[[ "$io_runtime_oob_status" -eq 70 ]] || \
    fail_test "b0-codegen-runtime-input-range-status (expected 70, got $io_runtime_oob_status)"
cmp -s "$TMP_DIR/byte-memory-runtime-oob.expected" "$TMP_DIR/io-runtime-oob.stderr" || \
    fail_test "b0-codegen-runtime-input-range-diagnostic"
printf 'PASS b0-codegen-runtime-input-range\n'

run_output "$SEED" "$IO_OUTPUT_RUNTIME_OOB_FIXTURE" \
    -o "$TMP_DIR/io-output-runtime-oob.out" >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/io-output-runtime-oob.out" \
    > "$TMP_DIR/io-output-runtime-oob.stdout" \
    2> "$TMP_DIR/io-output-runtime-oob.stderr"
io_output_runtime_oob_status=$?
set -e
[[ "$io_output_runtime_oob_status" -eq 70 ]] || \
    fail_test "b0-codegen-runtime-output-range-status (expected 70, got $io_output_runtime_oob_status)"
cmp -s "$TMP_DIR/byte-memory-runtime-oob.expected" \
    "$TMP_DIR/io-output-runtime-oob.stderr" || \
    fail_test "b0-codegen-runtime-output-range-diagnostic"
printf 'PASS b0-codegen-runtime-output-range\n'

run_output "$SEED" "$IO_NEGATIVE_RANGE_FIXTURE" -o "$TMP_DIR/io-negative-range.out" \
    >/dev/null
set +e
run_output_bounded 5 "$TMP_DIR/io-negative-range.out" \
    > "$TMP_DIR/io-negative-range.stdout" 2> "$TMP_DIR/io-negative-range.stderr"
io_negative_range_status=$?
set -e
[[ "$io_negative_range_status" -eq 70 ]] || \
    fail_test "b0-codegen-runtime-negative-range-status (expected 70, got $io_negative_range_status)"
cmp -s "$TMP_DIR/byte-memory-runtime-oob.expected" \
    "$TMP_DIR/io-negative-range.stderr" || \
    fail_test "b0-codegen-runtime-negative-range-diagnostic"
printf 'PASS b0-codegen-runtime-negative-range\n'

set +e
run_output "$SEED" "$IO_MALFORMED_FIXTURE" -o "$TMP_DIR/io-malformed.out" \
    > "$TMP_DIR/b0.io-malformed.stdout" 2> "$TMP_DIR/b0.io-malformed.stderr"
io_malformed_status=$?
set -e
[[ "$io_malformed_status" -eq 1 ]] || \
    fail_test "b0-codegen-runtime-io-malformed-status (expected 1, got $io_malformed_status)"
[[ ! -e "$TMP_DIR/io-malformed.out" ]] || \
    fail_test "b0-codegen-runtime-io-malformed-output"
if grep -Fq 'error[B0-CG-008]' "$TMP_DIR/b0.io-malformed.stderr"; then
    fail_test "b0-codegen-runtime-io-malformed-not-bounds"
fi
grep -Fq 'error[B0-CG-001]' "$TMP_DIR/b0.io-malformed.stderr" || \
    fail_test "b0-codegen-runtime-io-malformed-diagnostic"
printf 'PASS b0-codegen-runtime-io-malformed\n'

run_output "$SEED" "$IF_ELSE_FIXTURE" -o "$TMP_DIR/if-else.two" >/dev/null
cmp -s "$TMP_DIR/if-else.one" "$TMP_DIR/if-else.two" || \
    fail_test "b0-codegen-deterministic-labels"
printf 'PASS b0-codegen-deterministic-labels\n'

printf 'old-output' > "$TMP_DIR/codegen-error.out"
set +e
run_output "$SEED" "$UNKNOWN_CALL_FIXTURE" -o "$TMP_DIR/codegen-error.out" \
    > "$TMP_DIR/b0.unknown-call.stdout" 2> "$TMP_DIR/b0.unknown-call.stderr"
unknown_call_status=$?
set -e
[[ "$unknown_call_status" -eq 1 ]] || \
    fail_test "b0-codegen-unknown-call-status (expected 1, got $unknown_call_status)"
[[ ! -s "$TMP_DIR/b0.unknown-call.stdout" ]] || fail_test "b0-codegen-unknown-call-stdout"
grep -Fq 'error[B0-CG-002]' "$TMP_DIR/b0.unknown-call.stderr" || \
    fail_test "b0-codegen-unknown-call-diagnostic"
printf 'old-output' > "$TMP_DIR/codegen-error.expected"
cmp -s "$TMP_DIR/codegen-error.expected" "$TMP_DIR/codegen-error.out" || \
    fail_test "b0-codegen-unknown-call-preserves-output"
printf 'PASS b0-codegen-unknown-call\n'
printf 'PASS b0-error-preserves-old-output\n'

set +e
run_output "$SEED" "$UNKNOWN_CALL_SEMANTIC_FIXTURE" -o "$TMP_DIR/unknown-call-semantic.out" \
    > "$TMP_DIR/b0.unknown-call-semantic.stdout" \
    2> "$TMP_DIR/b0.unknown-call-semantic.stderr"
unknown_call_semantic_status=$?
set -e
[[ "$unknown_call_semantic_status" -eq 1 ]] || \
    fail_test "b0-codegen-semantic-unknown-call-status (expected 1, got $unknown_call_semantic_status)"
[[ ! -s "$TMP_DIR/b0.unknown-call-semantic.stdout" ]] || \
    fail_test "b0-codegen-semantic-unknown-call-stdout"
[[ ! -e "$TMP_DIR/unknown-call-semantic.out" ]] || \
    fail_test "b0-codegen-semantic-unknown-call-output"
grep -Fq 'error[B0-CG-002]' "$TMP_DIR/b0.unknown-call-semantic.stderr" || \
    fail_test "b0-codegen-semantic-unknown-call-diagnostic"
printf 'PASS b0-codegen-semantic-unknown-call\n'

set +e
run_output "$SEED" "$UNKNOWN_ASSIGNMENT_FIXTURE" -o "$TMP_DIR/unknown-assignment.out" \
    > "$TMP_DIR/b0.unknown-assignment.stdout" \
    2> "$TMP_DIR/b0.unknown-assignment.stderr"
unknown_assignment_status=$?
set -e
[[ "$unknown_assignment_status" -eq 1 ]] || \
    fail_test "b0-codegen-unknown-assignment-status (expected 1, got $unknown_assignment_status)"
[[ ! -s "$TMP_DIR/b0.unknown-assignment.stdout" ]] || \
    fail_test "b0-codegen-unknown-assignment-stdout"
[[ ! -e "$TMP_DIR/unknown-assignment.out" ]] || \
    fail_test "b0-codegen-unknown-assignment-output"
grep -Fq "$UNKNOWN_ASSIGNMENT_FIXTURE:3:5: error[B0-CG-007]" \
    "$TMP_DIR/b0.unknown-assignment.stderr" || \
    fail_test "b0-codegen-unknown-assignment-diagnostic"
printf 'PASS b0-codegen-unknown-assignment\n'

set +e
run_output "$SEED" "$TYPE_MISMATCH_FIXTURE" -o "$TMP_DIR/type-mismatch.out" \
    > "$TMP_DIR/b0.type-mismatch.stdout" 2> "$TMP_DIR/b0.type-mismatch.stderr"
type_mismatch_status=$?
set -e
[[ "$type_mismatch_status" -eq 1 ]] || \
    fail_test "b0-codegen-type-mismatch-status (expected 1, got $type_mismatch_status)"
[[ ! -s "$TMP_DIR/b0.type-mismatch.stdout" ]] || fail_test "b0-codegen-type-mismatch-stdout"
[[ ! -e "$TMP_DIR/type-mismatch.out" ]] || fail_test "b0-codegen-type-mismatch-output"
grep -Fq 'error[B0-CG-003]' "$TMP_DIR/b0.type-mismatch.stderr" || \
    fail_test "b0-codegen-type-mismatch-diagnostic"
printf 'PASS b0-codegen-type-mismatch\n'

set +e
run_output "$SEED" "$DIV_ZERO_FIXTURE" -o "$TMP_DIR/div-zero.out" \
    > "$TMP_DIR/b0.div-zero.stdout" 2> "$TMP_DIR/b0.div-zero.stderr"
div_zero_status=$?
set -e
[[ "$div_zero_status" -eq 1 ]] || \
    fail_test "b0-codegen-div-zero-status (expected 1, got $div_zero_status)"
[[ ! -s "$TMP_DIR/b0.div-zero.stdout" ]] || fail_test "b0-codegen-div-zero-stdout"
[[ ! -e "$TMP_DIR/div-zero.out" ]] || fail_test "b0-codegen-div-zero-output"
grep -Fq 'error[B0-CG-004]' "$TMP_DIR/b0.div-zero.stderr" || \
    fail_test "b0-codegen-div-zero-diagnostic"
printf 'PASS b0-codegen-div-zero\n'

set +e
run_output "$SEED" "$DIV_ZERO_EXPRESSION_FIXTURE" -o "$TMP_DIR/div-zero-expression.out" \
    > "$TMP_DIR/b0.div-zero-expression.stdout" 2> "$TMP_DIR/b0.div-zero-expression.stderr"
div_zero_expression_status=$?
set -e
[[ "$div_zero_expression_status" -eq 1 ]] || \
    fail_test "b0-codegen-div-zero-expression-status (expected 1, got $div_zero_expression_status)"
[[ ! -s "$TMP_DIR/b0.div-zero-expression.stdout" ]] || \
    fail_test "b0-codegen-div-zero-expression-stdout"
[[ ! -e "$TMP_DIR/div-zero-expression.out" ]] || \
    fail_test "b0-codegen-div-zero-expression-output"
grep -Fq 'error[B0-CG-004]' "$TMP_DIR/b0.div-zero-expression.stderr" || \
    fail_test "b0-codegen-div-zero-expression-diagnostic"
printf 'PASS b0-codegen-div-zero-expression\n'

set +e
run_output "$SEED" "$DIV_OVERFLOW_FIXTURE" -o "$TMP_DIR/div-overflow.out" \
    > "$TMP_DIR/b0.div-overflow.stdout" 2> "$TMP_DIR/b0.div-overflow.stderr"
div_overflow_status=$?
set -e
[[ "$div_overflow_status" -eq 1 ]] || \
    fail_test "b0-codegen-div-overflow-status (expected 1, got $div_overflow_status)"
[[ ! -s "$TMP_DIR/b0.div-overflow.stdout" ]] || fail_test "b0-codegen-div-overflow-stdout"
[[ ! -e "$TMP_DIR/div-overflow.out" ]] || fail_test "b0-codegen-div-overflow-output"
grep -Fq 'error[B0-CG-006]' "$TMP_DIR/b0.div-overflow.stderr" || \
    fail_test "b0-codegen-div-overflow-diagnostic"
printf 'PASS b0-codegen-div-overflow\n'

set +e
run_output "$SEED" "$OUTPUT_LIMIT_FIXTURE" -o "$TMP_DIR/output-limit.out" \
    > "$TMP_DIR/b0.output-limit.stdout" 2> "$TMP_DIR/b0.output-limit.stderr"
output_limit_status=$?
set -e
[[ "$output_limit_status" -eq 1 ]] || \
    fail_test "b0-codegen-output-limit-status (expected 1, got $output_limit_status)"
[[ ! -s "$TMP_DIR/b0.output-limit.stdout" ]] || fail_test "b0-codegen-output-limit-stdout"
[[ ! -e "$TMP_DIR/output-limit.out" ]] || fail_test "b0-codegen-output-limit-output"
grep -Fq 'error[B0-CG-005]' "$TMP_DIR/b0.output-limit.stderr" || \
    fail_test "b0-codegen-output-limit-diagnostic"
printf 'PASS b0-codegen-output-limit\n'

awk 'BEGIN {
    printf "fn main() { return 1"
    for (i = 1; i < 32746; i++) printf "+1"
    print " }"
}' > "$TMP_DIR/b0.output-cap-near.nql"
run_output "$SEED" "$TMP_DIR/b0.output-cap-near.nql" \
    -o "$TMP_DIR/output-cap-near.out" \
    > "$TMP_DIR/b0.output-cap-near.stdout" \
    2> "$TMP_DIR/b0.output-cap-near.stderr"
[[ ! -s "$TMP_DIR/b0.output-cap-near.stdout" ]] || \
    fail_test "b0-codegen-output-cap-near-stdout"
[[ ! -s "$TMP_DIR/b0.output-cap-near.stderr" ]] || \
    fail_test "b0-codegen-output-cap-near-stderr"
output_cap_near_size="$(wc -c < "$TMP_DIR/output-cap-near.out")"
[[ "$output_cap_near_size" -eq 589808 ]] || \
    fail_test "b0-codegen-output-cap-near-size (expected 589808, got $output_cap_near_size)"
printf 'PASS b0-codegen-output-cap-near\n'

awk 'BEGIN {
    printf "fn main() { return 1"
    for (i = 1; i < 32747; i++) printf "+1"
    print " }"
}' > "$TMP_DIR/b0.output-cap-overflow.nql"
set +e
run_output "$SEED" "$TMP_DIR/b0.output-cap-overflow.nql" \
    -o "$TMP_DIR/output-cap-overflow.out" \
    > "$TMP_DIR/b0.output-cap-overflow.stdout" \
    2> "$TMP_DIR/b0.output-cap-overflow.stderr"
output_cap_overflow_status=$?
set -e
[[ "$output_cap_overflow_status" -eq 1 ]] || \
    fail_test "b0-codegen-output-cap-overflow-status (expected 1, got $output_cap_overflow_status)"
[[ ! -s "$TMP_DIR/b0.output-cap-overflow.stdout" ]] || \
    fail_test "b0-codegen-output-cap-overflow-stdout"
[[ ! -e "$TMP_DIR/output-cap-overflow.out" ]] || \
    fail_test "b0-codegen-output-cap-overflow-output"
grep -Fq 'error[B0-CG-005]' "$TMP_DIR/b0.output-cap-overflow.stderr" || \
    fail_test "b0-codegen-output-cap-overflow-diagnostic"
printf 'PASS b0-codegen-output-cap-overflow\n'

mat_root="$TMP_DIR/materializer-root"
mkdir -p "$mat_root/bootstrap/compiler/b0/x86_64-linux" "$mat_root/bootstrap/stage0/x86_64-linux"
cp "$ROOT_DIR/bootstrap/stage0/x86_64-linux/stage0.seed" \
    "$mat_root/bootstrap/stage0/x86_64-linux/stage0.seed"
cp "$B0_DIR/compiler.nql0" "$mat_root/bootstrap/compiler/b0/compiler.nql0"
cp "$MATERIALIZER" "$mat_root/bootstrap/compiler/b0/x86_64-linux/materialize.sh"
chmod +x "$mat_root/bootstrap/compiler/b0/x86_64-linux/materialize.sh"
printf '0000000000000000000000000000000000000000000000000000000000000000  b0.seed\n' \
    > "$mat_root/bootstrap/compiler/b0/x86_64-linux/b0.sha256"
printf 'old-output' > "$TMP_DIR/materializer-old.out"
set +e
"$mat_root/bootstrap/compiler/b0/x86_64-linux/materialize.sh" \
    "$TMP_DIR/materializer-old.out" > "$TMP_DIR/b0.hash-mismatch.stdout" \
    2> "$TMP_DIR/b0.hash-mismatch.stderr"
hash_mismatch_status=$?
set -e
[[ "$hash_mismatch_status" -eq 1 ]] || \
    fail_test "b0-hash-mismatch-status (expected 1, got $hash_mismatch_status)"
grep -Fq 'hash mismatch' "$TMP_DIR/b0.hash-mismatch.stderr" || \
    fail_test "b0-hash-mismatch-diagnostic"
printf 'old-output' > "$TMP_DIR/materializer-old.expected"
cmp -s "$TMP_DIR/materializer-old.expected" "$TMP_DIR/materializer-old.out" || \
    fail_test "b0-hash-mismatch-preserves-old-output"
if find "$TMP_DIR" -maxdepth 1 -name '.b0.seed.tmp.*' | grep -q .; then
    fail_test "b0-error-removes-temp-file"
fi
printf 'PASS b0-error-removes-temp-file\n'
printf 'PASS b0-hash-mismatch-preserves-old-output\n'

set +e
run_output "$SEED" "$RETURN7_FIXTURE" -o "$TMP_DIR/missing-dir/out" \
    > "$TMP_DIR/b0.write-failure.stdout" 2> "$TMP_DIR/b0.write-failure.stderr"
write_failure_status=$?
set -e
[[ "$write_failure_status" -eq 1 ]] || \
    fail_test "b0-write-failure-status (expected 1, got $write_failure_status)"
[[ ! -s "$TMP_DIR/b0.write-failure.stdout" ]] || fail_test "b0-write-failure-stdout"
grep -Fq 'error[B0-IO-001]' "$TMP_DIR/b0.write-failure.stderr" || \
    fail_test "b0-write-failure-diagnostic"
printf 'PASS b0-write-failure-diagnostic\n'

for _ in $(seq 1 64); do
    run_output "$SEED" --help >/dev/null 2>&1
done
printf 'PASS b0-fd-cleanup-success\n'

for _ in $(seq 1 64); do
    set +e
    run_output "$SEED" "$INVALID_FIXTURE" -o "$TMP_DIR/fd-error.out" >/dev/null 2>&1
    fd_error_status=$?
    set -e
    [[ "$fd_error_status" -eq 1 ]] || fail_test "b0-fd-cleanup-error-status"
done
printf 'PASS b0-fd-cleanup-error\n'

printf 'old-output' > "$TMP_DIR/invalid.out"
set +e
run_output "$SEED" "$INVALID_FIXTURE" -o "$TMP_DIR/invalid.out" \
    > "$TMP_DIR/b0.invalid.stdout" 2> "$TMP_DIR/b0.invalid.stderr"
invalid_status=$?
set -e
[[ "$invalid_status" -eq 1 ]] || \
    fail_test "b0-invalid-token-status (expected 1, got $invalid_status)"
[[ ! -s "$TMP_DIR/b0.invalid.stdout" ]] || fail_test "b0-invalid-token-stdout"
grep -Fq 'error[B0-LEX-001]' "$TMP_DIR/b0.invalid.stderr" || \
    fail_test "b0-invalid-token-diagnostic"
printf 'old-output' > "$TMP_DIR/invalid.expected"
cmp -s "$TMP_DIR/invalid.expected" "$TMP_DIR/invalid.out" || \
    fail_test "b0-invalid-token-preserves-output"
printf 'PASS b0-invalid-token\n'

set +e
run_output "$SEED" "$MISSING_MAIN_FIXTURE" -o "$TMP_DIR/missing-main.out" \
    > "$TMP_DIR/b0.missing-main.stdout" 2> "$TMP_DIR/b0.missing-main.stderr"
missing_main_status=$?
set -e
[[ "$missing_main_status" -eq 1 ]] || \
    fail_test "b0-missing-main-status (expected 1, got $missing_main_status)"
[[ ! -e "$TMP_DIR/missing-main.out" ]] || fail_test "b0-missing-main-output"
grep -Fq 'error[B0-CG-001]' "$TMP_DIR/b0.missing-main.stderr" || \
    fail_test "b0-missing-main-diagnostic"
printf 'PASS b0-missing-main\n'

[[ "$manifest_row" == "$expected_manifest_row" ]] || \
    fail_test "b0-bootstrap-compiler-promoted"
printf 'PASS b0-bootstrap-compiler-promoted\n'
