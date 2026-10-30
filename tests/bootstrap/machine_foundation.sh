#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/tests/shared/lib.sh"

MACHINE_DIR="$ROOT_DIR/bootstrap/machine/x86_64-linux"
SEED="$MACHINE_DIR/hex0.seed"
MATERIALIZER="$MACHINE_DIR/materialize.sh"

fail_test() {
    printf 'FAIL %s\n' "$1" >&2
    exit 1
}

assert_files_equal() {
    local name="$1"
    local expected="$2"
    local actual="$3"
    cmp -s "$expected" "$actual" || fail_test "$name"
    printf 'PASS %s\n' "$name"
}

assert_failure() {
    local name="$1"
    local expected_status="$2"
    local expected_message="$3"
    shift 3

    local stdout_path="$TMP_DIR/$name.stdout"
    local stderr_path="$TMP_DIR/$name.stderr"
    local status

    set +e
    "$@" >"$stdout_path" 2>"$stderr_path"
    status=$?
    set -e

    [[ "$status" -eq "$expected_status" ]] || \
        fail_test "$name-status (expected $expected_status, got $status)"
    [[ ! -s "$stdout_path" ]] || fail_test "$name-unexpected-stdout"
    printf '%s\n' "$expected_message" > "$TMP_DIR/$name.expected-stderr"
    assert_files_equal "$name-diagnostic" "$TMP_DIR/$name.expected-stderr" "$stderr_path"
}

[[ -x "$SEED" ]] || fail_test "seed-is-executable"
printf 'PASS seed-is-executable\n'

"$MATERIALIZER" "$TMP_DIR/hex0.materialized" >/dev/null
assert_files_equal "materialize-byte-parity" "$SEED" "$TMP_DIR/hex0.materialized"

mkdir -p "$TMP_DIR/materialize-invalid"
cp "$MATERIALIZER" "$MACHINE_DIR/hex0.sha256" \
    "$TMP_DIR/materialize-invalid/"
printf '0g\n' > "$TMP_DIR/materialize-invalid/hex0.hex"
printf 'old-output' > "$TMP_DIR/materialize-invalid/output"
set +e
"$TMP_DIR/materialize-invalid/materialize.sh" \
    "$TMP_DIR/materialize-invalid/output" \
    >"$TMP_DIR/materialize-invalid/stdout" \
    2>"$TMP_DIR/materialize-invalid/stderr"
invalid_materialize_status=$?
set -e
[[ "$invalid_materialize_status" -eq 1 ]] || \
    fail_test "materialize-invalid-status"
printf 'old-output' > "$TMP_DIR/materialize-invalid/expected"
cmp -s "$TMP_DIR/materialize-invalid/expected" \
    "$TMP_DIR/materialize-invalid/output" || \
    fail_test "materialize-invalid-preserves-output"
grep -q 'invalid byte manifest character' \
    "$TMP_DIR/materialize-invalid/stderr" || \
    fail_test "materialize-invalid-diagnostic"
if compgen -G "$TMP_DIR/materialize-invalid/.hex0.seed.tmp.*" >/dev/null; then
    fail_test "materialize-invalid-temp-cleanup"
fi
printf 'PASS materialize-invalid-is-atomic\n'

mkdir -p "$TMP_DIR/materialize-hash"
cp "$MATERIALIZER" "$MACHINE_DIR/hex0.hex" \
    "$TMP_DIR/materialize-hash/"
printf '%064d  hex0.seed\n' 0 > "$TMP_DIR/materialize-hash/hex0.sha256"
printf 'old-output' > "$TMP_DIR/materialize-hash/output"
set +e
"$TMP_DIR/materialize-hash/materialize.sh" \
    "$TMP_DIR/materialize-hash/output" \
    >"$TMP_DIR/materialize-hash/stdout" \
    2>"$TMP_DIR/materialize-hash/stderr"
hash_materialize_status=$?
set -e
[[ "$hash_materialize_status" -eq 1 ]] || \
    fail_test "materialize-hash-status"
printf 'old-output' > "$TMP_DIR/materialize-hash/expected"
cmp -s "$TMP_DIR/materialize-hash/expected" \
    "$TMP_DIR/materialize-hash/output" || \
    fail_test "materialize-hash-preserves-output"
grep -q 'seed hash mismatch' "$TMP_DIR/materialize-hash/stderr" || \
    fail_test "materialize-hash-diagnostic"
if compgen -G "$TMP_DIR/materialize-hash/.hex0.seed.tmp.*" >/dev/null; then
    fail_test "materialize-hash-temp-cleanup"
fi
printf 'PASS materialize-hash-is-atomic\n'

if command -v nasm >/dev/null 2>&1; then
    nasm -f bin "$MACHINE_DIR/hex0.reference.asm" -o "$TMP_DIR/hex0.reference"
    assert_files_equal "reference-assembly-parity" "$SEED" "$TMP_DIR/hex0.reference"
else
    printf 'SKIP reference-assembly-parity (nasm unavailable)\n'
fi

run_output "$SEED" < "$MACHINE_DIR/hex0.hex" > "$TMP_DIR/hex0.self"
assert_files_equal "seed-self-decode" "$SEED" "$TMP_DIR/hex0.self"

printf '48 65 6c 6c 6f 0a # trailing comment\n' | \
    run_output "$SEED" > "$TMP_DIR/lowercase.out"
printf 'Hello\n' > "$TMP_DIR/lowercase.expected"
assert_files_equal "lowercase-whitespace-comment" \
    "$TMP_DIR/lowercase.expected" "$TMP_DIR/lowercase.out"

printf '4E\t6F\r\n' | run_output "$SEED" > "$TMP_DIR/uppercase.out"
printf 'No' > "$TMP_DIR/uppercase.expected"
assert_files_equal "uppercase-crlf" "$TMP_DIR/uppercase.expected" "$TMP_DIR/uppercase.out"

printf '00 ff 7F\n' | run_output "$SEED" > "$TMP_DIR/binary.out"
printf '\x00\xff\x7f' > "$TMP_DIR/binary.expected"
assert_files_equal "binary-byte-output" "$TMP_DIR/binary.expected" "$TMP_DIR/binary.out"

: | run_output "$SEED" > "$TMP_DIR/empty.out"
[[ ! -s "$TMP_DIR/empty.out" ]] || fail_test "empty-input"
printf 'PASS empty-input\n'

printf '4142\n' > "$TMP_DIR/redirect.hex"
run_output "$SEED" < "$TMP_DIR/redirect.hex" > "$TMP_DIR/redirect.out"
printf 'AB' > "$TMP_DIR/redirect.expected"
assert_files_equal "stdin-stdout-redirect" \
    "$TMP_DIR/redirect.expected" "$TMP_DIR/redirect.out"

printf 'PIPE' > "$TMP_DIR/pipe.expected"
if printf '50495045' | run_output "$SEED" | cmp -s "$TMP_DIR/pipe.expected" -; then
    printf 'PASS stdout-pipe\n'
else
    fail_test "stdout-pipe"
fi

assert_failure "invalid-hex" 1 \
    "hex0: error: invalid hexadecimal byte" \
    bash -c 'printf "0g" | "$1" "$2"' _ \
    "$(if [[ "$(uname -m)" == "x86_64" ]]; then printf '%s' env; else printf '%s' qemu-x86_64; fi)" \
    "$SEED"

assert_failure "odd-nibble" 1 \
    "hex0: error: odd number of hexadecimal nibbles" \
    bash -c 'printf "a" | "$1" "$2"' _ \
    "$(if [[ "$(uname -m)" == "x86_64" ]]; then printf '%s' env; else printf '%s' qemu-x86_64; fi)" \
    "$SEED"

exec 3<"$TMP_DIR"
set +e
run_output "$SEED" <&3 >"$TMP_DIR/read-failure.stdout" 2>"$TMP_DIR/read-failure.stderr"
read_status=$?
set -e
exec 3<&-
[[ "$read_status" -eq 1 ]] || fail_test "read-failure-status"
printf 'hex0: error: cannot read standard input\n' > "$TMP_DIR/read-failure.expected"
assert_files_equal "read-failure-diagnostic" \
    "$TMP_DIR/read-failure.expected" "$TMP_DIR/read-failure.stderr"

exec 4</dev/null
set +e
printf '00' | run_output "$SEED" >&4 2>"$TMP_DIR/write-failure.stderr"
write_status=$?
set -e
exec 4<&-
[[ "$write_status" -eq 1 ]] || fail_test "write-failure-status"
printf 'hex0: error: cannot write standard output\n' > "$TMP_DIR/write-failure.expected"
assert_files_equal "write-failure-diagnostic" \
    "$TMP_DIR/write-failure.expected" "$TMP_DIR/write-failure.stderr"

read_elf_reports "$SEED"
grep -q 'Machine:.*Advanced Micro Devices X86-64' <<< "$elf_header" || \
    fail_test "elf64-x86-64"
printf 'PASS elf64-x86-64\n'

stack_flags="$(awk '$1 == "GNU_STACK" { print $7 }' <<< "$elf_program_headers")"
[[ "$stack_flags" != *E* ]] || fail_test "non-executable-stack"
printf 'PASS non-executable-stack\n'

if grep -q 'INTERP' <<< "$elf_program_headers"; then
    fail_test "no-dynamic-interpreter"
fi
printf 'PASS no-dynamic-interpreter\n'

grep -q $'^machine-foundation\tPASS\t' "$ROOT_DIR/bootstrap/manifest.tsv" || \
    fail_test "manifest-machine-foundation-pass"
grep -q $'^stage-0\t' "$ROOT_DIR/bootstrap/manifest.tsv" || \
    fail_test "manifest-stage0-row"
printf 'PASS manifest-machine-foundation-status\n'
