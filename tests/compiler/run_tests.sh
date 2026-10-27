#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export ROOT_DIR

"$ROOT_DIR/nql" --build-compiler >/dev/null

"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/compiler/smoke.sh"
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/compiler/toolchain_cli.sh"
python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/compiler/test_canonical_cli.py" -v
printf 'PASS canonical-cli-backend\n'
python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/compiler/test_canonical_project.py" -v
printf 'PASS canonical-project-backend\n'
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/compiler/regression.sh"
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/compiler/diagnostics.sh"
bash "$ROOT_DIR/tests/compiler/error_handling_check.sh"
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/llvm/smoke.sh"
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/ir/bridge.sh"
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/ir/diagnostics.sh"
"$ROOT_DIR/tests/shared/run_suite.sh" "$ROOT_DIR/tests/ir/parity.sh"
