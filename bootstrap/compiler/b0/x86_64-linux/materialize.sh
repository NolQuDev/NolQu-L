#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
STAGE0_PATH="$ROOT_DIR/bootstrap/stage0/x86_64-linux/stage0.seed"
SOURCE_PATH="$SCRIPT_DIR/../compiler.nql0"
HASH_PATH="$SCRIPT_DIR/b0.sha256"
OUTPUT_PATH="${1:-$SCRIPT_DIR/b0.seed}"

fail() {
    printf 'materialize-b0: error: %s\n' "$1" >&2
    exit 1
}

[[ -x "$STAGE0_PATH" ]] || fail "missing executable Stage 0 seed '$STAGE0_PATH'"
[[ -f "$SOURCE_PATH" ]] || fail "missing B0 source '$SOURCE_PATH'"
[[ -f "$HASH_PATH" ]] || fail "missing hash manifest '$HASH_PATH'"

output_dir="$(dirname "$OUTPUT_PATH")"
[[ -d "$output_dir" ]] || fail "output directory '$output_dir' does not exist"

read -r expected_hash expected_name < "$HASH_PATH" || fail "cannot read '$HASH_PATH'"
[[ "$expected_hash" =~ ^[0-9a-f]{64}$ ]] || fail "invalid SHA-256 in '$HASH_PATH'"
[[ "$expected_name" == "b0.seed" ]] || fail "hash manifest must name b0.seed"

if [[ "$(uname -m)" == "x86_64" ]]; then
    runner=("$STAGE0_PATH")
elif command -v qemu-x86_64 >/dev/null 2>&1; then
    runner=(qemu-x86_64 "$STAGE0_PATH")
else
    fail "x86_64 execution unavailable; install qemu-x86_64 on this host"
fi

temp_path="$(mktemp "$output_dir/.b0.seed.tmp.XXXXXX")" || \
    fail "cannot create temporary output in '$output_dir'"

cleanup() {
    rm -f -- "$temp_path"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

if ! "${runner[@]}" < "$SOURCE_PATH" > "$temp_path"; then
    fail "Stage 0 could not reconstruct '$SOURCE_PATH'"
fi

actual_hash="$(sha256sum "$temp_path")" || fail "cannot hash reconstructed B0"
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || \
    fail "B0 hash mismatch: expected $expected_hash, got $actual_hash"

chmod 0755 "$temp_path" || fail "cannot mark reconstructed B0 executable"
mv -f -- "$temp_path" "$OUTPUT_PATH" || fail "cannot install '$OUTPUT_PATH'"
trap - EXIT HUP INT TERM

printf 'materialize-b0: verified %s  %s\n' "$actual_hash" "$OUTPUT_PATH"
