#!/usr/bin/env bash
set -euo pipefail
source "${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/tests/shared/lib.sh"
export PYTHONDONTWRITEBYTECODE=1
PYTHONPATH="$ROOT_DIR/tests/bootstrap${PYTHONPATH:+:$PYTHONPATH}" \
python3 -B -W error::ResourceWarning -m unittest -v \
    test_c0_native_frontend.NativeFrontendTests \
    test_c0_native_backend.NativeBackendTests \
    test_c0_native_runtime.NativeRuntimeTests \
    test_c0_native_program.NativeProgramTests
printf 'PASS c0-native-os\n'
