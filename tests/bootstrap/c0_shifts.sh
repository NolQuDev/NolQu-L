#!/usr/bin/env bash
set -euo pipefail
source "${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/tests/shared/lib.sh"
export PYTHONDONTWRITEBYTECODE=1
python3 -B -W error::ResourceWarning "$ROOT_DIR/tests/bootstrap/test_c0_shifts.py" -v
printf 'PASS c0-shifts\n'
