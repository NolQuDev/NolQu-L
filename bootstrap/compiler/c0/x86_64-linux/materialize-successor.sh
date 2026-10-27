#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_PATH="$SCRIPT_DIR/../successor.nq"
COMPILER_PATH="$SCRIPT_DIR/compile.sh"
HASH_PATH="$SCRIPT_DIR/c0-successor.sha256"
OUTPUT_PATH="${1:-$SCRIPT_DIR/c0-successor.seed}"

fail() {
    printf 'materialize-c0-successor: error: %s\n' "$1" >&2
    exit 1
}

[[ -f "$SOURCE_PATH" ]] || fail "missing successor source '$SOURCE_PATH'"
[[ -x "$COMPILER_PATH" ]] || fail "missing C0 compiler adapter '$COMPILER_PATH'"
[[ -f "$HASH_PATH" ]] || fail "missing hash manifest '$HASH_PATH'"
[[ ! -d "$OUTPUT_PATH" ]] || fail "output path '$OUTPUT_PATH' is a directory"

output_dir="$(dirname "$OUTPUT_PATH")"
[[ -d "$output_dir" ]] || fail "output directory '$output_dir' does not exist"

read -r expected_hash expected_name < "$HASH_PATH" || fail "cannot read '$HASH_PATH'"
[[ "$expected_hash" =~ ^[0-9a-f]{64}$ ]] || fail "invalid SHA-256 in '$HASH_PATH'"
[[ "$expected_name" == "c0-successor.seed" ]] || \
    fail 'hash manifest must name c0-successor.seed'

temp_path="$(mktemp "$output_dir/.c0-successor.tmp.XXXXXX")" || \
    fail "cannot create temporary output in '$output_dir'"

cleanup() {
    rm -f -- "$temp_path"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

"$COMPILER_PATH" "$SOURCE_PATH" "$temp_path" || \
    fail "C0 could not compile '$SOURCE_PATH'"

actual_hash="$(sha256sum "$temp_path")" || fail 'cannot hash successor artifact'
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || \
    fail "successor hash mismatch: expected $expected_hash, got $actual_hash"

chmod 0755 "$temp_path" || fail 'cannot mark successor executable'
mv -fT -- "$temp_path" "$OUTPUT_PATH" || fail "cannot install '$OUTPUT_PATH'"
trap - EXIT HUP INT TERM

printf 'materialize-c0-successor: verified %s  %s\n' "$actual_hash" "$OUTPUT_PATH"
