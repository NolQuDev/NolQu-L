#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MACHINE_DIR="$SCRIPT_DIR/../../machine/x86_64-linux"
HEX0_PATH="$MACHINE_DIR/hex0.seed"
SOURCE_PATH="$SCRIPT_DIR/stage0.hex"
HASH_PATH="$SCRIPT_DIR/stage0.sha256"
OUTPUT_PATH="${1:-$SCRIPT_DIR/stage0.seed}"

fail() {
    printf 'materialize-stage0: error: %s\n' "$1" >&2
    exit 1
}

[[ $# -le 1 ]] || fail 'usage: materialize.sh [output]'

validate_output() {
    local protected
    [[ ! -d "$OUTPUT_PATH" ]] || fail "output path '$OUTPUT_PATH' is a directory"
    for protected in "$SOURCE_PATH" "$HASH_PATH" "$HEX0_PATH" "${BASH_SOURCE[0]}"; do
        [[ ! "$OUTPUT_PATH" -ef "$protected" ]] || \
            fail "output would replace required input '$protected'"
    done
}

validate_output

[[ -x "$HEX0_PATH" ]] || fail "missing executable machine seed '$HEX0_PATH'"
[[ -f "$SOURCE_PATH" ]] || fail "missing Stage 0 byte manifest '$SOURCE_PATH'"
[[ -f "$HASH_PATH" ]] || fail "missing hash manifest '$HASH_PATH'"

output_dir="$(dirname -- "$OUTPUT_PATH")"
[[ -d "$output_dir" ]] || fail "output directory '$output_dir' does not exist"

read -r expected_hash expected_name < "$HASH_PATH" || fail "cannot read '$HASH_PATH'"
[[ "$expected_hash" =~ ^[0-9a-f]{64}$ ]] || fail "invalid SHA-256 in '$HASH_PATH'"
[[ "$expected_name" == "stage0.seed" ]] || fail "hash manifest must name stage0.seed"

if [[ "$(uname -m)" == "x86_64" ]]; then
    runner=("$HEX0_PATH")
elif command -v qemu-x86_64 >/dev/null 2>&1; then
    runner=(qemu-x86_64 "$HEX0_PATH")
else
    fail "x86_64 execution unavailable; install qemu-x86_64 on this host"
fi

temp_path="$(mktemp -- "$output_dir/.stage0.seed.tmp.XXXXXX")" || \
    fail "cannot create temporary output in '$output_dir'"

cleanup() {
    rm -f -- "$temp_path"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

if ! "${runner[@]}" < "$SOURCE_PATH" > "$temp_path"; then
    fail "hex0 could not reconstruct '$SOURCE_PATH'"
fi

actual_hash="$(sha256sum "$temp_path")" || fail "cannot hash reconstructed Stage 0"
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || \
    fail "Stage 0 hash mismatch: expected $expected_hash, got $actual_hash"

chmod 0755 "$temp_path" || fail "cannot mark reconstructed Stage 0 executable"
validate_output
mv -fT -- "$temp_path" "$OUTPUT_PATH" || fail "cannot install '$OUTPUT_PATH'"
trap - EXIT HUP INT TERM

printf 'materialize-stage0: verified %s  %s\n' "$actual_hash" "$OUTPUT_PATH"
