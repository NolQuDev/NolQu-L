#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEX_PATH="$SCRIPT_DIR/hex0.hex"
HASH_PATH="$SCRIPT_DIR/hex0.sha256"
OUTPUT_PATH="${1:-$SCRIPT_DIR/hex0.seed}"

fail() {
    printf 'materialize: error: %s\n' "$1" >&2
    exit 1
}

[[ -f "$HEX_PATH" ]] || fail "missing byte manifest '$HEX_PATH'"
[[ -f "$HASH_PATH" ]] || fail "missing hash manifest '$HASH_PATH'"

output_dir="$(dirname "$OUTPUT_PATH")"
[[ -d "$output_dir" ]] || fail "output directory '$output_dir' does not exist"

read -r expected_hash expected_name < "$HASH_PATH" || fail "cannot read '$HASH_PATH'"
[[ "$expected_hash" =~ ^[0-9a-f]{64}$ ]] || fail "invalid SHA-256 in '$HASH_PATH'"
[[ "$expected_name" == "hex0.seed" ]] || fail "hash manifest must name hex0.seed"

temp_path="$(mktemp "$output_dir/.hex0.seed.tmp.XXXXXX")" || \
    fail "cannot create temporary output in '$output_dir'"

cleanup() {
    rm -f -- "$temp_path"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

: > "$temp_path"
line_number=0
pending_nibble=""

while IFS= read -r line || [[ -n "$line" ]]; do
    ((line_number += 1))
    line="${line%%#*}"
    for ((column = 0; column < ${#line}; column += 1)); do
        byte="${line:column:1}"
        case "$byte" in
            [0-9a-fA-F])
                if [[ -z "$pending_nibble" ]]; then
                    pending_nibble="$byte"
                else
                    printf '%b' "\\x${pending_nibble}${byte}" >> "$temp_path"
                    pending_nibble=""
                fi
                ;;
            ' '|$'\t'|$'\r')
                ;;
            *)
                fail "invalid byte manifest character at $HEX_PATH:$line_number:$((column + 1))"
                ;;
        esac
    done
done < "$HEX_PATH"

[[ -z "$pending_nibble" ]] || fail "odd number of hexadecimal nibbles in '$HEX_PATH'"

actual_hash="$(sha256sum "$temp_path")" || fail "cannot hash reconstructed seed"
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || \
    fail "seed hash mismatch: expected $expected_hash, got $actual_hash"

chmod 0755 "$temp_path" || fail "cannot mark reconstructed seed executable"
mv -f -- "$temp_path" "$OUTPUT_PATH" || fail "cannot install '$OUTPUT_PATH'"
trap - EXIT HUP INT TERM

printf 'materialize: verified %s  %s\n' "$actual_hash" "$OUTPUT_PATH"
