#!/usr/bin/env bash
set -euo pipefail

source "${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/tests/shared/lib.sh"
export PYTHONDONTWRITEBYTECODE=1

python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/bootstrap/test_c0_capacity_frontend.py" -v
python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/bootstrap/test_c0_capacity_backend.py" -v
python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/bootstrap/test_c0_compiler_profile.py" -v
printf 'PASS c0-capacity\n'

python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/bootstrap/test_c0_component_generations.py" -v
printf 'PASS c0-component-generations\n'
