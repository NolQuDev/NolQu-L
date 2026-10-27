#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C0_PATH="$SCRIPT_DIR/c0.seed"
HASH_PATH="$SCRIPT_DIR/c0.sha256"

fail() {
    printf 'c0: error: %s\n' "$1" >&2
    exit 1
}

if [[ $# -ne 2 ]]; then
    fail 'usage: compile.sh <input.nq> <output>'
fi

input_path="$1"
output_path="$2"
[[ -x "$C0_PATH" ]] || fail "missing executable C0 seed '$C0_PATH'"
[[ -f "$HASH_PATH" ]] || fail "missing hash manifest '$HASH_PATH'"
[[ -f "$input_path" ]] || fail "input file '$input_path' does not exist"
[[ -r "$input_path" ]] || fail "input file '$input_path' is not readable"
[[ ! -d "$output_path" ]] || fail "output path '$output_path' is a directory"

read -r expected_hash expected_name < "$HASH_PATH" || fail "cannot read '$HASH_PATH'"
[[ "$expected_hash" =~ ^[0-9a-f]{64}$ ]] || fail "invalid SHA-256 in '$HASH_PATH'"
[[ "$expected_name" == "c0.seed" ]] || fail "hash manifest must name c0.seed"
actual_hash="$(sha256sum "$C0_PATH")" || fail "cannot hash '$C0_PATH'"
actual_hash="${actual_hash%% *}"
[[ "$actual_hash" == "$expected_hash" ]] || \
    fail "C0 seed hash mismatch: expected $expected_hash, got $actual_hash"

output_dir="$(dirname "$output_path")"
[[ -d "$output_dir" ]] || fail "output directory '$output_dir' does not exist"

if [[ "$(uname -m)" == "x86_64" ]]; then
    runner=("$C0_PATH")
elif command -v qemu-x86_64 >/dev/null 2>&1; then
    runner=(qemu-x86_64 "$C0_PATH")
else
    fail "x86_64 execution unavailable; install qemu-x86_64 on this host"
fi

temp_path="$(mktemp "$output_dir/.c0.tmp.XXXXXX")" || \
    fail "cannot create temporary output in '$output_dir'"

cleanup() {
    rm -f -- "$temp_path"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

status=0
"${runner[@]}" < "$input_path" > "$temp_path" || status=$?
if [[ "$status" -ne 0 ]]; then
    exit "$status"
fi

chmod 0755 "$temp_path" || fail "cannot mark output executable"
mv -fT -- "$temp_path" "$output_path" || fail "cannot install '$output_path'"
trap - EXIT HUP INT TERM
