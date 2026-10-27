#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/bootstrap/test_run_native_evidence.py" -v
printf 'PASS native-invocation-evidence\n'
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/machine_foundation.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/stage0.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/bootstrap_compiler_b0.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/core_compiler_c0.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/c0_source_byte_tokenizer.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/c0_source_token_parser.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/c0_frontend.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/c0_backend.sh"
ROOT_DIR="$ROOT_DIR" "$ROOT_DIR/tests/shared/run_suite.sh" \
    "$ROOT_DIR/tests/bootstrap/c0_capacity.sh"
