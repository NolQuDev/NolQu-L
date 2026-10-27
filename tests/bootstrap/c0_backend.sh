#!/usr/bin/env bash
set -euo pipefail

source "${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/tests/shared/lib.sh"

stage="$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux"
source_path="$ROOT_DIR/bootstrap/compiler/c0/backend.nql"
b0="$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/b0.seed"
backend="$TMP_DIR/c0-backend"

row="$(awk -F '\t' '$1 == "core-backend" { print $2 "\t" $3 "\t" $4 }' "$ROOT_DIR/bootstrap/manifest.tsv")"
[[ "$row" == $'PASS\tbootstrap/compiler/c0/x86_64-linux/c0-backend.seed\ttests/bootstrap/c0_backend.sh' ]]

[[ -f "$source_path" ]] || { printf 'FAIL c0-backend-source-missing\n' >&2; exit 1; }
run_output "$b0" --compiler-profile "$source_path" -o "$backend"
run_output "$b0" --compiler-profile "$source_path" -o "$TMP_DIR/c0-backend-again"
cmp "$backend" "$TMP_DIR/c0-backend-again"
for component in frontend backend; do
    read -r expected_hash expected_name < "$stage/c0-$component.sha256"
    [[ "$expected_name" == "c0-$component.seed" ]]
    [[ "$(sha256sum "$stage/c0-$component.seed" | cut -d ' ' -f 1)" == "$expected_hash" ]]
done
cmp "$backend" "$stage/c0-backend.seed"
python3 "$ROOT_DIR/tests/bootstrap/test_c0_backend.py" "$backend"
C0_BACKEND="$backend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_control_flow.py"
printf 'PASS c0-control-flow\n'
C0_BACKEND="$backend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_functions.py"
printf 'PASS c0-functions\n'
C0_BACKEND="$backend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_runtime_io.py" RuntimeTests
printf 'PASS c0-runtime-io\n'
C0_BACKEND="$backend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_capacity_backend.py"
printf 'PASS c0-capacity-backend\n'
C0_BACKEND="$backend" bash "$ROOT_DIR/tests/bootstrap/c0_native_os.sh"

readelf -h "$backend" | grep -q 'Machine:.*Advanced Micro Devices X86-64'
if readelf -lW "$backend" | grep -Eq ' (INTERP|DYNAMIC) '; then
    printf 'FAIL c0-backend-host-linkage\n' >&2
    exit 1
fi
readelf -lW "$backend" | awk '
    $1 == "GNU_STACK" { found = 1; if ($7 ~ /E/) exit 1 }
    END { if (!found) exit 1 }
'
printf 'PASS c0-backend\n'
