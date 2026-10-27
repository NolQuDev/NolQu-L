#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/tests/shared/lib.sh"

C0_SEED="$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0.seed"
C0_SOURCE="$ROOT_DIR/bootstrap/compiler/c0/compiler.nq"
TOKENIZER_SOURCE="$ROOT_DIR/bootstrap/compiler/c0/source_byte_tokenizer.nql"
PARSER_SOURCE="$ROOT_DIR/bootstrap/compiler/c0/source_token_parser.nql"

fail_test() {
    printf 'FAIL %s\n' "$1" >&2
    exit 1
}

run_output_bounded() {
    local executable="$1"
    if [[ "$(uname -m)" == "x86_64" ]]; then
        timeout 5 "$executable"
    else
        timeout 5 qemu-x86_64 "$executable"
    fi
}

assert_invalid_parser_input() {
    local input="$1"
    local label="$2"
    local output="$TMP_DIR/$label.out"
    local error="$TMP_DIR/$label.err"
    local status

    set +e
    run_output_bounded "$parser_a" < "$input" > "$output" 2> "$error"
    status=$?
    set -e
    [[ "$status" -eq 1 ]] || fail_test "$label-status"
    [[ ! -s "$output" ]] || fail_test "$label-partial-output"
    cmp -s "$error" "$invalid_expected" || fail_test "$label-diagnostic"
}

compile_stage() {
    local source="$1"
    local output="$2"
    local label="$3"

    if ! run_output_bounded "$C0_SEED" < "$source" > "$output"; then
        fail_test "$label-build"
    fi
    chmod 0755 "$output"
}

[[ -f "$PARSER_SOURCE" ]] || fail_test "c0-source-token-parser-source"
[[ -f "$TOKENIZER_SOURCE" ]] || fail_test "c0-source-token-parser-tokenizer-source"
[[ -x "$C0_SEED" ]] || fail_test "c0-source-token-parser-seed"
grep -q '^# C0\.25 stream compiler\.' "$C0_SOURCE" || \
    fail_test "c0-source-token-parser-milestone"
[[ "$(sha256sum "$PARSER_SOURCE" | awk '{ print $1 }')" == \
    "f8f44089cc28d61847105f4cb267fcf92e23d2e430a8878137d278f8f85ffa8f" ]] || \
    fail_test "c0-source-token-parser-source-hash"

tokenizer="$TMP_DIR/source-token-parser-tokenizer"
parser_a="$TMP_DIR/source-token-parser-a"
parser_b="$TMP_DIR/source-token-parser-b"
compile_stage "$TOKENIZER_SOURCE" "$tokenizer" "c0-source-token-parser-tokenizer"
compile_stage "$PARSER_SOURCE" "$parser_a" "c0-source-token-parser"
compile_stage "$PARSER_SOURCE" "$parser_b" "c0-source-token-parser-rebuild"
cmp -s "$parser_a" "$parser_b" || fail_test "c0-source-token-parser-deterministic"
[[ "$(sha256sum "$parser_a" | awk '{ print $1 }')" == \
    "f03e85e4966b2439f3fbeccd22bc1b57c0dd7feaa1638bb76ce7ebc6bc4fc357" ]] || \
    fail_test "c0-source-token-parser-artifact-hash"

readelf -h "$parser_a" | grep -q 'Machine:.*Advanced Micro Devices X86-64' || \
    fail_test "c0-source-token-parser-machine"
if readelf -lW "$parser_a" | grep -q ' INTERP '; then
    fail_test "c0-source-token-parser-interpreter"
fi
readelf -lW "$parser_a" | awk '
    $1 == "GNU_STACK" { found = 1; if ($7 ~ /E/) exit 1 }
    END { if (!found) exit 1 }
' || fail_test "c0-source-token-parser-stack"

invalid_expected="$TMP_DIR/source-token-parser-invalid.expected"
printf 'runtime: invalid source\n' > "$invalid_expected"

compact_source="$TMP_DIR/source-token-parser-compact.in"
compact_tokens="$TMP_DIR/source-token-parser-compact.tokens"
compact_output="$TMP_DIR/source-token-parser-compact.out"
compact_error="$TMP_DIR/source-token-parser-compact.err"
compact_expected="$TMP_DIR/source-token-parser-compact.expected"
printf 'foo+42' > "$compact_source"
printf '%b' \
    '\x03\x04\x00\x03\x0f\x03\x01\x05\x04\x02' \
    > "$compact_expected"
dd if=/dev/zero bs=1 count=39 status=none >> "$compact_expected"
printf '%b' '\x01\x01\x00\x03' >> "$compact_expected"
if ! run_output_bounded "$tokenizer" < "$compact_source" > "$compact_tokens"; then
    fail_test "c0-source-token-parser-compact-tokenize"
fi
if ! run_output_bounded "$parser_a" < "$compact_tokens" \
    > "$compact_output" 2> "$compact_error"; then
    fail_test "c0-source-token-parser-compact-run"
fi
[[ ! -s "$compact_error" ]] || fail_test "c0-source-token-parser-compact-stderr"
cmp -s "$compact_output" "$compact_expected" || \
    fail_test "c0-source-token-parser-compact-records"
[[ "$(wc -c < "$compact_output")" -eq 53 ]] || \
    fail_test "c0-source-token-parser-output-size"

spaced_source="$TMP_DIR/source-token-parser-spaced.in"
spaced_tokens="$TMP_DIR/source-token-parser-spaced.tokens"
spaced_output="$TMP_DIR/source-token-parser-spaced.out"
spaced_expected="$TMP_DIR/source-token-parser-spaced.expected"
printf 'a + 7' > "$spaced_source"
printf '%b' \
    '\x03\x04\x00\x01\x0f\x02\x01\x05\x04\x01' \
    > "$spaced_expected"
dd if=/dev/zero bs=1 count=39 status=none >> "$spaced_expected"
printf '%b' '\x01\x01\x00\x03' >> "$spaced_expected"
run_output_bounded "$tokenizer" < "$spaced_source" > "$spaced_tokens" || \
    fail_test "c0-source-token-parser-spaced-tokenize"
run_output_bounded "$parser_a" < "$spaced_tokens" > "$spaced_output" || \
    fail_test "c0-source-token-parser-spaced-run"
cmp -s "$spaced_output" "$spaced_expected" || \
    fail_test "c0-source-token-parser-spaced-records"

identifier_digits_source="$TMP_DIR/source-token-parser-identifier-digits.in"
identifier_digits_tokens="$TMP_DIR/source-token-parser-identifier-digits.tokens"
printf 'foo42+7' > "$identifier_digits_source"
run_output_bounded "$tokenizer" < "$identifier_digits_source" \
    > "$identifier_digits_tokens" || \
    fail_test "c0-source-token-parser-identifier-digits-tokenize"
run_output_bounded "$parser_a" < "$identifier_digits_tokens" > /dev/null || \
    fail_test "c0-source-token-parser-identifier-digits-run"

for valid_source_text in 'foo' '42' 'foo-42' 'foo+bar' '42+foo' \
    'a+1*b-2/c' 'a + 1 * b'; do
    label="$(printf '%s' "$valid_source_text" | od -An -tx1 | tr -d ' \n')"
    source_file="$TMP_DIR/source-token-parser-valid-$label.in"
    token_file="$TMP_DIR/source-token-parser-valid-$label.tokens"
    output_file="$TMP_DIR/source-token-parser-valid-$label.out"
    expected_file="$TMP_DIR/source-token-parser-valid-$label.expected"
    printf '%s' "$valid_source_text" > "$source_file"
    run_output_bounded "$tokenizer" < "$source_file" > "$token_file" || \
        fail_test "c0-source-token-parser-valid-$label-tokenize"
    run_output_bounded "$parser_a" < "$token_file" > "$output_file" || \
        fail_test "c0-source-token-parser-valid-$label-run"
    cp "$token_file" "$expected_file"
    printf '%b' '\x01\x01\x00' >> "$expected_file"
    dd if="$token_file" bs=1 count=1 status=none >> "$expected_file"
    cmp -s "$output_file" "$expected_file" || \
        fail_test "c0-source-token-parser-valid-$label-records"
done

for invalid_source_text in 'foo-+42' 'foo+42+' 'foo 42' '+foo' 'foo=42' \
    '(foo)'; do
    label="$(printf '%s' "$invalid_source_text" | od -An -tx1 | tr -d ' \n')"
    source_file="$TMP_DIR/source-token-parser-invalid-$label.in"
    token_file="$TMP_DIR/source-token-parser-invalid-$label.tokens"
    printf '%s' "$invalid_source_text" > "$source_file"
    run_output_bounded "$tokenizer" < "$source_file" > "$token_file" || \
        fail_test "c0-source-token-parser-invalid-$label-tokenize"
    assert_invalid_parser_input "$token_file" \
        "c0-source-token-parser-invalid-$label"
done

empty_tokens="$TMP_DIR/source-token-parser-empty.tokens"
printf '' | run_output_bounded "$tokenizer" > "$empty_tokens" || \
    fail_test "c0-source-token-parser-empty-tokenize"
assert_invalid_parser_input "$empty_tokens" "c0-source-token-parser-empty"

zero_length_tokens="$TMP_DIR/source-token-parser-zero-length.tokens"
cp "$compact_tokens" "$zero_length_tokens"
printf '\0' | dd of="$zero_length_tokens" bs=1 seek=3 conv=notrunc status=none
assert_invalid_parser_input "$zero_length_tokens" \
    "c0-source-token-parser-zero-length"

invalid_offset_tokens="$TMP_DIR/source-token-parser-invalid-offset.tokens"
cp "$compact_tokens" "$invalid_offset_tokens"
printf '\x10' | dd of="$invalid_offset_tokens" bs=1 seek=2 conv=notrunc status=none
assert_invalid_parser_input "$invalid_offset_tokens" \
    "c0-source-token-parser-invalid-offset"

overflow_count_tokens="$TMP_DIR/source-token-parser-overflow-count.tokens"
cp "$compact_tokens" "$overflow_count_tokens"
printf '\x11' | dd of="$overflow_count_tokens" bs=1 seek=0 conv=notrunc status=none
assert_invalid_parser_input "$overflow_count_tokens" \
    "c0-source-token-parser-overflow-count"

even_poison_source="$TMP_DIR/source-token-parser-even-poison.in"
even_poison_tokens="$TMP_DIR/source-token-parser-even-poison.tokens"
printf 'a+' > "$even_poison_source"
run_output_bounded "$tokenizer" < "$even_poison_source" > "$even_poison_tokens" || \
    fail_test "c0-source-token-parser-even-poison-tokenize"
printf '%b' '\x04\x02\x01' | dd of="$even_poison_tokens" bs=1 seek=7 \
    conv=notrunc status=none
assert_invalid_parser_input "$even_poison_tokens" \
    "c0-source-token-parser-even-poison"

printf 'PASS c0-source-token-parser\n'
