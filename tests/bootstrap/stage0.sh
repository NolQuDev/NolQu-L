#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/tests/shared/lib.sh"

MACHINE_DIR="$ROOT_DIR/bootstrap/machine/x86_64-linux"
STAGE0_DIR="$ROOT_DIR/bootstrap/stage0/x86_64-linux"
HEX0="$MACHINE_DIR/hex0.seed"
SEED="$STAGE0_DIR/stage0.seed"
SOURCE="$STAGE0_DIR/stage0.hex"
MATERIALIZER="$STAGE0_DIR/materialize.sh"
ELF_FIXTURE="$ROOT_DIR/tests/bootstrap/fixtures/minimal_elf.nql0"

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

assert_stage0_failure() {
    local name="$1"
    local expected_message="$2"
    local source_path="$3"
    local status

    set +e
    run_output "$SEED" < "$source_path" \
        > "$TMP_DIR/$name.stdout" 2> "$TMP_DIR/$name.stderr"
    status=$?
    set -e

    [[ "$status" -eq 1 ]] || fail_test "$name-status (expected 1, got $status)"
    [[ ! -s "$TMP_DIR/$name.stdout" ]] || fail_test "$name-unexpected-stdout"
    printf '%s\n' "$expected_message" > "$TMP_DIR/$name.expected-stderr"
    assert_files_equal "$name-diagnostic" \
        "$TMP_DIR/$name.expected-stderr" "$TMP_DIR/$name.stderr"
}

assert_stage0_failure_contains() {
    local name="$1"
    local expected_text="$2"
    local source_path="$3"
    local status

    set +e
    run_output "$SEED" < "$source_path" \
        > "$TMP_DIR/$name.stdout" 2> "$TMP_DIR/$name.stderr"
    status=$?
    set -e

    [[ "$status" -eq 1 ]] || fail_test "$name-status (expected 1, got $status)"
    [[ ! -s "$TMP_DIR/$name.stdout" ]] || fail_test "$name-unexpected-stdout"
    grep -Fq -- "$expected_text" "$TMP_DIR/$name.stderr" || \
        fail_test "$name-diagnostic"
    printf 'PASS %s\n' "$name"
}

[[ -x "$SEED" ]] || fail_test "stage0-is-executable"
printf 'PASS stage0-is-executable\n'

"$MATERIALIZER" "$TMP_DIR/stage0.materialized" >/dev/null
assert_files_equal "stage0-materialize-byte-parity" \
    "$SEED" "$TMP_DIR/stage0.materialized"

run_output "$HEX0" < "$SOURCE" > "$TMP_DIR/stage0.from-hex0"
assert_files_equal "stage0-built-by-machine-seed" \
    "$SEED" "$TMP_DIR/stage0.from-hex0"

if grep -Eiq '(nasm|(^|[^[:alpha:]])ld([^[:alpha:]]|$)|python|llvm)' \
    "$MATERIALIZER"; then
    fail_test "stage0-canonical-build-host-tool-reference"
fi
printf 'PASS stage0-canonical-build-has-no-compiler-tool\n'

if command -v nasm >/dev/null 2>&1; then
    nasm -f bin "$STAGE0_DIR/stage0.reference.asm" \
        -o "$TMP_DIR/stage0.reference"
    assert_files_equal "stage0-reference-assembly-parity" \
        "$SEED" "$TMP_DIR/stage0.reference"
else
    printf 'SKIP stage0-reference-assembly-parity (nasm unavailable)\n'
fi

run_output "$SEED" < "$SOURCE" > "$TMP_DIR/stage0.self"
assert_files_equal "stage0-self-reconstruction" "$SEED" "$TMP_DIR/stage0.self"

: | run_output "$SEED" > "$TMP_DIR/empty.out"
[[ ! -s "$TMP_DIR/empty.out" ]] || fail_test "stage0-empty-input"
printf 'PASS stage0-empty-input\n'

printf '41 42 # ignored\r\n43\n' | run_output "$SEED" > "$TMP_DIR/raw.out"
printf 'ABC' > "$TMP_DIR/raw.expected"
assert_files_equal "stage0-raw-byte-comments-crlf" \
    "$TMP_DIR/raw.expected" "$TMP_DIR/raw.out"

printf ':start\n90 e9 @start\n' | run_output "$SEED" > "$TMP_DIR/backward.out"
printf '\x90\xe9\xfa\xff\xff\xff' > "$TMP_DIR/backward.expected"
assert_files_equal "stage0-backward-rel32" \
    "$TMP_DIR/backward.expected" "$TMP_DIR/backward.out"

printf '%s\n' '&end $end e9 @end 0f0b :end c3' | \
    run_output "$SEED" > "$TMP_DIR/forward.out"
printf '\x17\x00\x40\x00\x00\x00\x00\x00' \
    > "$TMP_DIR/forward.expected"
printf '\x17\x00\x00\x00\x00\x00\x00\x00' \
    >> "$TMP_DIR/forward.expected"
printf '\xe9\x02\x00\x00\x00\x0f\x0b\xc3' \
    >> "$TMP_DIR/forward.expected"
assert_files_equal "stage0-forward-symbol-patches" \
    "$TMP_DIR/forward.expected" "$TMP_DIR/forward.out"

printf '%s\n' ':A 90 :a 91 $A $a' | \
    run_output "$SEED" > "$TMP_DIR/case-sensitive.out"
printf '\x90\x91\x00\x00\x00\x00\x00\x00\x00\x00' \
    > "$TMP_DIR/case-sensitive.expected"
printf '\x01\x00\x00\x00\x00\x00\x00\x00' \
    >> "$TMP_DIR/case-sensitive.expected"
assert_files_equal "stage0-symbols-case-sensitive" \
    "$TMP_DIR/case-sensitive.expected" "$TMP_DIR/case-sensitive.out"

name63="$(printf 'a%.0s' {1..63})"
printf ':%s @%s\n' "$name63" "$name63" | \
    run_output "$SEED" > "$TMP_DIR/name63.out"
printf '\xfc\xff\xff\xff' > "$TMP_DIR/name63.expected"
assert_files_equal "stage0-symbol-max-boundary" \
    "$TMP_DIR/name63.expected" "$TMP_DIR/name63.out"

run_output "$SEED" < "$ELF_FIXTURE" > "$TMP_DIR/minimal-a"
run_output "$SEED" < "$ELF_FIXTURE" > "$TMP_DIR/minimal-b"
assert_files_equal "stage0-deterministic-codegen" \
    "$TMP_DIR/minimal-a" "$TMP_DIR/minimal-b"
[[ "$(stat -c '%s' "$TMP_DIR/minimal-a")" -eq 219 ]] || \
    fail_test "stage0-generated-elf-size"
printf 'PASS stage0-generated-elf-size\n'

chmod 0755 "$TMP_DIR/minimal-a"
run_output "$TMP_DIR/minimal-a" > "$TMP_DIR/minimal.stdout"
printf 'S0\n' > "$TMP_DIR/minimal.expected"
assert_files_equal "stage0-generated-elf-runs" \
    "$TMP_DIR/minimal.expected" "$TMP_DIR/minimal.stdout"

readelf -h "$TMP_DIR/minimal-a" | \
    grep -qi 'Entry point address:.*0x4000b0' || \
    fail_test "stage0-generated-elf-entry"
printf 'PASS stage0-generated-elf-entry\n'
readelf -h "$TMP_DIR/minimal-a" | \
    grep -q 'Machine:.*Advanced Micro Devices X86-64' || \
    fail_test "stage0-generated-elf-machine"
printf 'PASS stage0-generated-elf-machine\n'
if readelf -W -l "$TMP_DIR/minimal-a" | grep -q 'INTERP'; then
    fail_test "stage0-generated-elf-static"
fi
printf 'PASS stage0-generated-elf-static\n'
generated_stack_flags="$(readelf -W -l "$TMP_DIR/minimal-a" | \
    awk '$1 == "GNU_STACK" { print $7 }')"
[[ "$generated_stack_flags" != *E* ]] || \
    fail_test "stage0-generated-elf-non-executable-stack"
printf 'PASS stage0-generated-elf-non-executable-stack\n'

seed_stack_flags="$(readelf -W -l "$SEED" | \
    awk '$1 == "GNU_STACK" { print $7 }')"
[[ "$seed_stack_flags" != *E* ]] || fail_test "stage0-seed-non-executable-stack"
printf 'PASS stage0-seed-non-executable-stack\n'
if readelf -W -l "$SEED" | grep -q 'INTERP'; then
    fail_test "stage0-seed-no-interpreter"
fi
printf 'PASS stage0-seed-no-interpreter\n'

printf 'zz\n' > "$TMP_DIR/invalid-token.src"
assert_stage0_failure "stage0-invalid-token" \
    'stage0: byte 0: error: invalid token; expected hexadecimal byte, :label, @label, &label, or $label' \
    "$TMP_DIR/invalid-token.src"

printf '0' > "$TMP_DIR/truncated.src"
assert_stage0_failure "stage0-truncated-hex" \
    'stage0: byte 0: error: truncated hexadecimal byte; add the second hexadecimal digit' \
    "$TMP_DIR/truncated.src"

printf ':9bad\n' > "$TMP_DIR/malformed.src"
assert_stage0_failure "stage0-malformed-symbol" \
    'stage0: byte 0: error: malformed symbol; use [A-Za-z_][A-Za-z0-9_]*' \
    "$TMP_DIR/malformed.src"

name64="$(printf 'a%.0s' {1..64})"
printf ':%s\n' "$name64" > "$TMP_DIR/name64.src"
assert_stage0_failure "stage0-symbol-too-long" \
    'stage0: byte 0: error: symbol exceeds 63 bytes; shorten the symbol name' \
    "$TMP_DIR/name64.src"

printf ':foo :foo\n' > "$TMP_DIR/duplicate.src"
assert_stage0_failure "stage0-duplicate-label" \
    'stage0: byte 5: error: duplicate label; define each symbol exactly once' \
    "$TMP_DIR/duplicate.src"

printf '@missing\n' > "$TMP_DIR/undefined.src"
assert_stage0_failure "stage0-undefined-label" \
    'stage0: byte 0: error: undefined label; add a matching :label definition' \
    "$TMP_DIR/undefined.src"

awk 'BEGIN { for (i = 0; i <= 4096; i++) printf ":L%d\n", i }' \
    > "$TMP_DIR/too-many-labels.src"
assert_stage0_failure_contains "stage0-too-many-labels" \
    'error: more than 4096 labels; split the bootstrap unit' \
    "$TMP_DIR/too-many-labels.src"

awk 'BEGIN { print ":x"; for (i = 0; i < 262145; i++) print "$x" }' \
    > "$TMP_DIR/output-too-large.src"
assert_stage0_failure_contains "stage0-output-limit" \
    'error: output exceeds 2097152 bytes; split the bootstrap unit' \
    "$TMP_DIR/output-too-large.src"

head -c 4194305 /dev/zero > "$TMP_DIR/input-too-large.src"
assert_stage0_failure "stage0-input-limit" \
    'stage0: error: input exceeds 4194304 bytes; split the bootstrap unit' \
    "$TMP_DIR/input-too-large.src"

set +e
run_output "$SEED" unexpected \
    > "$TMP_DIR/argument.stdout" 2> "$TMP_DIR/argument.stderr"
argument_status=$?
set -e
[[ "$argument_status" -eq 1 ]] || fail_test "stage0-argument-status"
[[ ! -s "$TMP_DIR/argument.stdout" ]] || fail_test "stage0-argument-stdout"
printf '%s\n' \
    'stage0: error: command-line arguments are not supported; use stdin and stdout' \
    > "$TMP_DIR/argument.expected"
assert_files_equal "stage0-argument-diagnostic" \
    "$TMP_DIR/argument.expected" "$TMP_DIR/argument.stderr"

exec 3<"$TMP_DIR"
set +e
run_output "$SEED" <&3 \
    > "$TMP_DIR/read.stdout" 2> "$TMP_DIR/read.stderr"
read_status=$?
set -e
exec 3<&-
[[ "$read_status" -eq 1 ]] || fail_test "stage0-read-failure-status"
[[ ! -s "$TMP_DIR/read.stdout" ]] || fail_test "stage0-read-failure-stdout"
printf '%s\n' \
    'stage0: error: cannot read standard input; check the input stream' \
    > "$TMP_DIR/read.expected"
assert_files_equal "stage0-read-failure-diagnostic" \
    "$TMP_DIR/read.expected" "$TMP_DIR/read.stderr"

exec 4</dev/null
set +e
printf '00' | run_output "$SEED" >&4 2> "$TMP_DIR/write.stderr"
write_status=$?
set -e
exec 4<&-
[[ "$write_status" -eq 1 ]] || fail_test "stage0-write-failure-status"
printf '%s\n' \
    'stage0: error: cannot write standard output; check the output stream' \
    > "$TMP_DIR/write.expected"
assert_files_equal "stage0-write-failure-diagnostic" \
    "$TMP_DIR/write.expected" "$TMP_DIR/write.stderr"

if [[ "$(uname -m)" == "x86_64" ]] && command -v strace >/dev/null 2>&1; then
    strace -qq -e trace=mmap,munmap,open,openat -o "$TMP_DIR/resource.trace" \
        "$SEED" < /dev/null > /dev/null
elif command -v qemu-x86_64 >/dev/null 2>&1; then
    qemu-x86_64 -strace "$SEED" < /dev/null \
        > /dev/null 2> "$TMP_DIR/resource.trace"
else
    : > "$TMP_DIR/resource.trace"
fi

if [[ -s "$TMP_DIR/resource.trace" ]]; then
    [[ "$(grep -c 'mmap(' "$TMP_DIR/resource.trace")" -eq 3 ]] || \
        fail_test "stage0-resource-mmap-count"
    [[ "$(grep -c 'munmap(' "$TMP_DIR/resource.trace")" -eq 3 ]] || \
        fail_test "stage0-resource-munmap-count"
    if grep -Eq '(^| )open(at)?\(' "$TMP_DIR/resource.trace"; then
        fail_test "stage0-resource-unexpected-open"
    fi
    printf 'PASS stage0-resource-cleanup\n'
else
    printf 'SKIP stage0-resource-cleanup (syscall tracer unavailable)\n'
fi

printf '0' > "$TMP_DIR/resource-error.src"
set +e
if [[ "$(uname -m)" == "x86_64" ]] && command -v strace >/dev/null 2>&1; then
    strace -qq -e trace=mmap,munmap -o "$TMP_DIR/resource-error.trace" \
        "$SEED" < "$TMP_DIR/resource-error.src" \
        > /dev/null 2> "$TMP_DIR/resource-error.stderr"
    resource_error_status=$?
elif command -v qemu-x86_64 >/dev/null 2>&1; then
    qemu-x86_64 -strace "$SEED" < "$TMP_DIR/resource-error.src" \
        > /dev/null 2> "$TMP_DIR/resource-error.trace"
    resource_error_status=$?
else
    : > "$TMP_DIR/resource-error.trace"
    resource_error_status=1
fi
set -e

if [[ -s "$TMP_DIR/resource-error.trace" ]]; then
    [[ "$resource_error_status" -eq 1 ]] || \
        fail_test "stage0-resource-error-status"
    [[ "$(grep -c 'mmap(' "$TMP_DIR/resource-error.trace")" -eq 3 ]] || \
        fail_test "stage0-resource-error-mmap-count"
    [[ "$(grep -c 'munmap(' "$TMP_DIR/resource-error.trace")" -eq 3 ]] || \
        fail_test "stage0-resource-error-munmap-count"
    printf 'PASS stage0-resource-error-cleanup\n'
else
    printf 'SKIP stage0-resource-error-cleanup (syscall tracer unavailable)\n'
fi

mkdir -p "$TMP_DIR/atomic/bootstrap/stage0/x86_64-linux"
mkdir -p "$TMP_DIR/atomic/bootstrap/machine/x86_64-linux"
cp "$MATERIALIZER" "$STAGE0_DIR/stage0.sha256" \
    "$TMP_DIR/atomic/bootstrap/stage0/x86_64-linux/"
cp "$HEX0" "$TMP_DIR/atomic/bootstrap/machine/x86_64-linux/"
printf '0g\n' > "$TMP_DIR/atomic/bootstrap/stage0/x86_64-linux/stage0.hex"
printf 'old-output' > "$TMP_DIR/atomic/output"
set +e
"$TMP_DIR/atomic/bootstrap/stage0/x86_64-linux/materialize.sh" \
    "$TMP_DIR/atomic/output" \
    > "$TMP_DIR/atomic/stdout" 2> "$TMP_DIR/atomic/stderr"
atomic_status=$?
set -e
[[ "$atomic_status" -eq 1 ]] || fail_test "stage0-materialize-invalid-status"
grep -Fq 'hex0 could not reconstruct' "$TMP_DIR/atomic/stderr" || \
    fail_test "stage0-materialize-invalid-diagnostic"
printf 'old-output' > "$TMP_DIR/atomic/expected"
assert_files_equal "stage0-materialize-invalid-preserves-output" \
    "$TMP_DIR/atomic/expected" "$TMP_DIR/atomic/output"
if compgen -G "$TMP_DIR/atomic/.stage0.seed.tmp.*" >/dev/null; then
    fail_test "stage0-materialize-invalid-temp-cleanup"
fi
printf 'PASS stage0-materialize-invalid-temp-cleanup\n'

mkdir -p "$TMP_DIR/hash/bootstrap/stage0/x86_64-linux"
mkdir -p "$TMP_DIR/hash/bootstrap/machine/x86_64-linux"
cp "$MATERIALIZER" "$SOURCE" \
    "$TMP_DIR/hash/bootstrap/stage0/x86_64-linux/"
cp "$HEX0" "$TMP_DIR/hash/bootstrap/machine/x86_64-linux/"
printf '%064d  stage0.seed\n' 0 \
    > "$TMP_DIR/hash/bootstrap/stage0/x86_64-linux/stage0.sha256"
printf 'old-output' > "$TMP_DIR/hash/output"
set +e
"$TMP_DIR/hash/bootstrap/stage0/x86_64-linux/materialize.sh" \
    "$TMP_DIR/hash/output" \
    > "$TMP_DIR/hash/stdout" 2> "$TMP_DIR/hash/stderr"
hash_status=$?
set -e
[[ "$hash_status" -eq 1 ]] || fail_test "stage0-materialize-hash-status"
grep -Fq 'Stage 0 hash mismatch' "$TMP_DIR/hash/stderr" || \
    fail_test "stage0-materialize-hash-diagnostic"
printf 'old-output' > "$TMP_DIR/hash/expected"
assert_files_equal "stage0-materialize-hash-preserves-output" \
    "$TMP_DIR/hash/expected" "$TMP_DIR/hash/output"
if compgen -G "$TMP_DIR/hash/.stage0.seed.tmp.*" >/dev/null; then
    fail_test "stage0-materialize-hash-temp-cleanup"
fi
printf 'PASS stage0-materialize-hash-temp-cleanup\n'

grep -q $'^stage-0\tPASS\t' "$ROOT_DIR/bootstrap/manifest.tsv" || \
    fail_test "manifest-stage0-pass"
printf 'PASS manifest-stage0-pass\n'
