#!/usr/bin/env bash
set -euo pipefail

source "${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/tests/shared/lib.sh"

source_path="$ROOT_DIR/bootstrap/compiler/c0/frontend.nql"
b0="$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/b0.seed"
frontend="$TMP_DIR/c0-frontend"

row="$(awk -F '\t' '$1 == "core-frontend" { print $2 "\t" $3 "\t" $4 }' "$ROOT_DIR/bootstrap/manifest.tsv")"
[[ "$row" == $'PASS\tbootstrap/compiler/c0/x86_64-linux/c0-frontend.seed\ttests/bootstrap/c0_frontend.sh' ]]

[[ -f "$source_path" ]] || { printf 'FAIL c0-frontend-source-missing\n' >&2; exit 1; }
run_output "$b0" --compiler-profile "$source_path" -o "$frontend"
run_output "$b0" --compiler-profile "$source_path" -o "$TMP_DIR/c0-frontend-again"
cmp "$frontend" "$TMP_DIR/c0-frontend-again"
read -r expected_hash expected_name < "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-frontend.sha256"
[[ "$expected_name" == c0-frontend.seed ]]
[[ "$(sha256sum "$frontend" | cut -d ' ' -f 1)" == "$expected_hash" ]]
cmp "$frontend" "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed"
python3 "$ROOT_DIR/tests/bootstrap/test_c0_frontend.py" "$frontend"
C0_FRONTEND="$frontend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_capacity_frontend.py"
C0_FRONTEND="$frontend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_control_flow.py" \
    ControlFlowTests.test_ast_delimiters_and_version \
    ControlFlowTests.test_malformed_source_and_nesting_limit
C0_FRONTEND="$frontend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_functions.py" \
    FunctionTests.test_frontend_ast_contract \
    FunctionTests.test_frontend_syntax_errors
C0_FRONTEND="$frontend" python3 "$ROOT_DIR/tests/bootstrap/test_c0_runtime_io.py" FrontendRuntimeTests

readelf -h "$frontend" | grep -q 'Machine:.*Advanced Micro Devices X86-64'
if readelf -lW "$frontend" | grep -q ' INTERP '; then
    printf 'FAIL c0-frontend-interpreter\n' >&2
    exit 1
fi
if readelf -lW "$frontend" | grep -q ' DYNAMIC '; then
    printf 'FAIL c0-frontend-dynamic-linkage\n' >&2
    exit 1
fi
readelf -lW "$frontend" | awk '
    $1 == "GNU_STACK" { found = 1; if ($7 ~ /E/) exit 1 }
    END { if (!found) exit 1 }
'
printf 'PASS c0-frontend\n'
