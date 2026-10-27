#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/tests/shared/lib.sh"

C0_SEED="$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0.seed"
C0_HASH="$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0.sha256"
C0_SOURCE="$ROOT_DIR/bootstrap/compiler/c0/compiler.nq"
TOKENIZER_SOURCE="$ROOT_DIR/bootstrap/compiler/c0/source_byte_tokenizer.nql"
CLASSIFIER_INVALID_SOURCE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_classify_ascii_invalid.nql"
TOKEN_PUSH_INVALID_SOURCE="$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_byte_token_push_invalid.nql"

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

[[ -f "$TOKENIZER_SOURCE" ]] || fail_test "c0-source-byte-tokenizer-source"
[[ -x "$C0_SEED" ]] || fail_test "c0-source-byte-tokenizer-seed"
grep -q '^# C0\.25 stream compiler\.' "$C0_SOURCE" || \
    fail_test "c0-source-byte-tokenizer-milestone"

expected_seed_hash="$(awk 'NF >= 1 { print $1; exit }' "$C0_HASH")"
actual_seed_hash="$(sha256sum "$C0_SEED" | awk '{ print $1 }')"
[[ "$actual_seed_hash" == "$expected_seed_hash" ]] || \
    fail_test "c0-source-byte-tokenizer-seed-hash"

tokenizer_a="$TMP_DIR/source-byte-tokenizer-a"
tokenizer_b="$TMP_DIR/source-byte-tokenizer-b"
if ! run_output_bounded "$C0_SEED" < "$TOKENIZER_SOURCE" > "$tokenizer_a"; then
    fail_test "c0-source-byte-tokenizer-build"
fi
if ! run_output_bounded "$C0_SEED" < "$TOKENIZER_SOURCE" > "$tokenizer_b"; then
    fail_test "c0-source-byte-tokenizer-rebuild"
fi
cmp -s "$tokenizer_a" "$tokenizer_b" || \
    fail_test "c0-source-byte-tokenizer-deterministic"
[[ "$(sha256sum "$tokenizer_a" | awk '{ print $1 }')" == \
    "132372400176567973f1f288e3ebbf8fd872abc6e65fbc08b1612c88ca03908f" ]] || \
    fail_test "c0-source-byte-tokenizer-artifact-hash"
chmod 0755 "$tokenizer_a" "$tokenizer_b"

readelf -h "$tokenizer_a" | grep -q 'Machine:.*Advanced Micro Devices X86-64' || \
    fail_test "c0-source-byte-tokenizer-machine"
if readelf -lW "$tokenizer_a" | grep -q ' INTERP '; then
    fail_test "c0-source-byte-tokenizer-interpreter"
fi
readelf -lW "$tokenizer_a" | awk '
    $1 == "GNU_STACK" { found = 1; if ($7 ~ /E/) exit 1 }
    END { if (!found) exit 1 }
' || fail_test "c0-source-byte-tokenizer-stack"

sample_input="$TMP_DIR/source-byte-tokenizer.in"
sample_output="$TMP_DIR/source-byte-tokenizer.out"
sample_error="$TMP_DIR/source-byte-tokenizer.err"
sample_expected="$TMP_DIR/source-byte-tokenizer.expected"
printf 'fn 42+\n' > "$sample_input"
printf '\x03\x04\x00\x02\x05\x03\x02\x0f\x05\x01' \
    > "$sample_expected"
dd if=/dev/zero bs=1 count=39 status=none >> "$sample_expected"

if ! run_output_bounded "$tokenizer_a" < "$sample_input" > "$sample_output" 2> "$sample_error"; then
    fail_test "c0-source-byte-tokenizer-run"
fi
[[ ! -s "$sample_error" ]] || fail_test "c0-source-byte-tokenizer-stderr"
cmp -s "$sample_output" "$sample_expected" || \
    fail_test "c0-source-byte-tokenizer-records"
[[ "$(wc -c < "$sample_output")" -eq 49 ]] || \
    fail_test "c0-source-byte-tokenizer-output-size"

max_input="$TMP_DIR/source-byte-tokenizer-max.in"
max_output="$TMP_DIR/source-byte-tokenizer-max.out"
max_expected="$TMP_DIR/source-byte-tokenizer-max.expected"
printf '0123456789abcdef' > "$max_input"
printf '%b' \
    '\x02\x05\x00\x0a\x04\x0a\x06' \
    > "$max_expected"
dd if=/dev/zero bs=1 count=42 status=none >> "$max_expected"
if ! run_output_bounded "$tokenizer_a" < "$max_input" > "$max_output"; then
    fail_test "c0-source-byte-tokenizer-max-bound"
fi
cmp -s "$max_output" "$max_expected" || \
    fail_test "c0-source-byte-tokenizer-max-records"
[[ "$(od -An -tu1 -N1 "$max_output" | tr -d ' ')" == "2" ]] || \
    fail_test "c0-source-byte-tokenizer-max-count"
[[ "$(wc -c < "$max_output")" -eq 49 ]] || \
    fail_test "c0-source-byte-tokenizer-max-output-size"

punctuation_input="$TMP_DIR/source-byte-tokenizer-punctuation.in"
punctuation_output="$TMP_DIR/source-byte-tokenizer-punctuation.out"
punctuation_expected="$TMP_DIR/source-byte-tokenizer-punctuation.expected"
printf '(){};+*-/=,' > "$punctuation_input"
printf '%b' \
    '\x0b\x0a\x00\x01\x0b\x01\x01\x0c\x02\x01\x0d\x03\x01' \
    '\x0e\x04\x01\x0f\x05\x01\x10\x06\x01\x11\x07\x01' \
    '\x12\x08\x01\x13\x09\x01\x14\x0a\x01' \
    > "$punctuation_expected"
dd if=/dev/zero bs=1 count=15 status=none >> "$punctuation_expected"
if ! run_output_bounded "$tokenizer_a" < "$punctuation_input" > "$punctuation_output"; then
    fail_test "c0-source-byte-tokenizer-punctuation-run"
fi
cmp -s "$punctuation_output" "$punctuation_expected" || \
    fail_test "c0-source-byte-tokenizer-punctuation-kinds"

classes_input="$TMP_DIR/source-byte-tokenizer-classes.in"
classes_output="$TMP_DIR/source-byte-tokenizer-classes.out"
classes_expected="$TMP_DIR/source-byte-tokenizer-classes.expected"
printf 'Az_09 \t\r\n' > "$classes_input"
printf '%b' \
    '\x01\x04\x00\x05' \
    > "$classes_expected"
dd if=/dev/zero bs=1 count=45 status=none >> "$classes_expected"
if ! run_output_bounded "$tokenizer_a" < "$classes_input" > "$classes_output"; then
    fail_test "c0-source-byte-tokenizer-classes-run"
fi
cmp -s "$classes_output" "$classes_expected" || \
    fail_test "c0-source-byte-tokenizer-class-kinds"

boundaries_input="$TMP_DIR/source-byte-tokenizer-boundaries.in"
boundaries_output="$TMP_DIR/source-byte-tokenizer-boundaries.out"
boundaries_expected="$TMP_DIR/source-byte-tokenizer-boundaries.expected"
printf '12a a12' > "$boundaries_input"
printf '%b' \
    '\x03\x05\x00\x02\x04\x02\x01\x04\x04\x03' \
    > "$boundaries_expected"
dd if=/dev/zero bs=1 count=39 status=none >> "$boundaries_expected"
if ! run_output_bounded "$tokenizer_a" < "$boundaries_input" > "$boundaries_output"; then
    fail_test "c0-source-byte-tokenizer-boundaries-run"
fi
cmp -s "$boundaries_output" "$boundaries_expected" || \
    fail_test "c0-source-byte-tokenizer-boundaries"

invalid_input="$TMP_DIR/source-byte-tokenizer-invalid.in"
invalid_output="$TMP_DIR/source-byte-tokenizer-invalid.out"
invalid_error="$TMP_DIR/source-byte-tokenizer-invalid.err"
printf '@' > "$invalid_input"
set +e
run_output_bounded "$tokenizer_a" < "$invalid_input" \
    > "$invalid_output" 2> "$invalid_error"
invalid_status=$?
set -e
[[ "$invalid_status" -eq 1 ]] || \
    fail_test "c0-source-byte-tokenizer-invalid-status"
[[ ! -s "$invalid_output" ]] || \
    fail_test "c0-source-byte-tokenizer-invalid-output"
printf 'runtime: invalid source\n' > "$TMP_DIR/source-byte-tokenizer-invalid.expected"
cmp -s "$invalid_error" "$TMP_DIR/source-byte-tokenizer-invalid.expected" || \
    fail_test "c0-source-byte-tokenizer-invalid-diagnostic"

printf '\200' > "$invalid_input"
set +e
run_output_bounded "$tokenizer_a" < "$invalid_input" \
    > "$invalid_output" 2> "$invalid_error"
invalid_status=$?
set -e
[[ "$invalid_status" -eq 1 ]] || \
    fail_test "c0-source-byte-tokenizer-non-ascii-status"
[[ ! -s "$invalid_output" ]] || \
    fail_test "c0-source-byte-tokenizer-non-ascii-output"
cmp -s "$invalid_error" "$TMP_DIR/source-byte-tokenizer-invalid.expected" || \
    fail_test "c0-source-byte-tokenizer-non-ascii-diagnostic"

classifier_invalid_output="$TMP_DIR/source-byte-classifier-invalid.out"
classifier_invalid_error="$TMP_DIR/source-byte-classifier-invalid.err"
set +e
run_output_bounded "$C0_SEED" < "$CLASSIFIER_INVALID_SOURCE" \
    > "$classifier_invalid_output" 2> "$classifier_invalid_error"
classifier_invalid_status=$?
set -e
[[ "$classifier_invalid_status" -eq 1 ]] || \
    fail_test "c0-source-byte-classifier-invalid-operand-status"
[[ ! -s "$classifier_invalid_output" ]] || \
    fail_test "c0-source-byte-classifier-invalid-operand-output"
printf 'input:2:28: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/source-byte-classifier-invalid.expected"
cmp -s "$classifier_invalid_error" \
    "$TMP_DIR/source-byte-classifier-invalid.expected" || \
    fail_test "c0-source-byte-classifier-invalid-operand-diagnostic"

token_push_invalid_output="$TMP_DIR/source-byte-token-push-invalid.out"
token_push_invalid_error="$TMP_DIR/source-byte-token-push-invalid.err"
set +e
run_output_bounded "$C0_SEED" < "$TOKEN_PUSH_INVALID_SOURCE" \
    > "$token_push_invalid_output" 2> "$token_push_invalid_error"
token_push_invalid_status=$?
set -e
[[ "$token_push_invalid_status" -eq 1 ]] || \
    fail_test "c0-source-byte-token-push-invalid-operand-status"
[[ ! -s "$token_push_invalid_output" ]] || \
    fail_test "c0-source-byte-token-push-invalid-operand-output"
printf 'input:2:30: error[C0-001]: invalid C0 program\n' \
    > "$TMP_DIR/source-byte-token-push-invalid.expected"
cmp -s "$token_push_invalid_error" \
    "$TMP_DIR/source-byte-token-push-invalid.expected" || \
    fail_test "c0-source-byte-token-push-invalid-operand-diagnostic"

token_capacity_source="$TMP_DIR/source-byte-token-capacity.nql"
token_capacity_binary="$TMP_DIR/source-byte-token-capacity"
{
    printf 'fn main() {\n    byte_store(0, 10)\n    byte_store(1, 0)\n'
    for _ in $(seq 1 16); do
        printf '    byte_token_push(0, 1, 127)\n'
    done
    printf '    output_write(127, 49)\n    return 0\n}\n'
} > "$token_capacity_source"
if ! run_output_bounded "$C0_SEED" < "$token_capacity_source" \
    > "$token_capacity_binary"; then
    fail_test "c0-source-byte-token-capacity-build"
fi
chmod 0755 "$token_capacity_binary"
token_capacity_output="$TMP_DIR/source-byte-token-capacity.out"
token_capacity_error="$TMP_DIR/source-byte-token-capacity.err"
if ! run_output_bounded "$token_capacity_binary" \
    > "$token_capacity_output" 2> "$token_capacity_error"; then
    fail_test "c0-source-byte-token-capacity-run"
fi
[[ ! -s "$token_capacity_error" ]] || \
    fail_test "c0-source-byte-token-capacity-stderr"
expected_capacity_records="16"
for _ in $(seq 1 16); do
    expected_capacity_records="$expected_capacity_records 10 0 1"
done
actual_capacity_records="$(od -An -tu1 -v "$token_capacity_output" | xargs)"
[[ "$actual_capacity_records" == "$expected_capacity_records" ]] || \
    fail_test "c0-source-byte-token-capacity-records"

token_overflow_source="$TMP_DIR/source-byte-token-overflow.nql"
token_overflow_binary="$TMP_DIR/source-byte-token-overflow"
{
    printf 'fn main() {\n    byte_store(0, 10)\n    byte_store(1, 0)\n'
    for _ in $(seq 1 17); do
        printf '    byte_token_push(0, 1, 127)\n'
    done
    printf '    output_write(127, 49)\n    return 0\n}\n'
} > "$token_overflow_source"
if ! run_output_bounded "$C0_SEED" < "$token_overflow_source" \
    > "$token_overflow_binary"; then
    fail_test "c0-source-byte-token-overflow-build"
fi
chmod 0755 "$token_overflow_binary"
token_overflow_output="$TMP_DIR/source-byte-token-overflow.out"
token_overflow_error="$TMP_DIR/source-byte-token-overflow.err"
set +e
run_output_bounded "$token_overflow_binary" \
    > "$token_overflow_output" 2> "$token_overflow_error"
token_overflow_status=$?
set -e
[[ "$token_overflow_status" -eq 1 ]] || \
    fail_test "c0-source-byte-token-overflow-status"
[[ ! -s "$token_overflow_output" ]] || \
    fail_test "c0-source-byte-token-overflow-output"
cmp -s "$token_overflow_error" \
    "$TMP_DIR/source-byte-tokenizer-invalid.expected" || \
    fail_test "c0-source-byte-token-overflow-diagnostic"

empty_output="$TMP_DIR/source-byte-tokenizer-empty.out"
empty_expected="$TMP_DIR/source-byte-tokenizer-empty.expected"
dd if=/dev/zero bs=1 count=49 status=none > "$empty_expected"
if ! run_output_bounded "$tokenizer_a" < /dev/null > "$empty_output"; then
    fail_test "c0-source-byte-tokenizer-empty-run"
fi
cmp -s "$empty_output" "$empty_expected" || \
    fail_test "c0-source-byte-tokenizer-empty-records"

overflow_input="$TMP_DIR/source-byte-tokenizer-overflow.in"
overflow_output="$TMP_DIR/source-byte-tokenizer-overflow.out"
overflow_error="$TMP_DIR/source-byte-tokenizer-overflow.err"
printf 'abcdefghijklmnopq' > "$overflow_input"
set +e
run_output_bounded "$tokenizer_a" < "$overflow_input" \
    > "$overflow_output" 2> "$overflow_error"
overflow_status=$?
set -e
[[ "$overflow_status" -eq 1 ]] || \
    fail_test "c0-source-byte-tokenizer-overflow-status"
[[ ! -s "$overflow_output" ]] || \
    fail_test "c0-source-byte-tokenizer-overflow-output"
printf 'runtime: invalid source\n' > "$TMP_DIR/source-byte-tokenizer-overflow.expected"
cmp -s "$overflow_error" "$TMP_DIR/source-byte-tokenizer-overflow.expected" || \
    fail_test "c0-source-byte-tokenizer-overflow-diagnostic"

printf 'PASS c0-source-byte-tokenizer\n'
