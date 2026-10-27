#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

if [[ $# -ne 1 ]]; then
    printf 'usage: run_suite.sh <suite-script>\n' >&2
    exit 1
fi

suite_script="$1"
suite_tmp_parent="${TMP_DIR:-}"

if [[ -n "$suite_tmp_parent" ]]; then
    mkdir -p "$suite_tmp_parent"
    suite_tmp="$(mktemp -d "$suite_tmp_parent/nq-tests.XXXXXX")"
else
    suite_tmp="$(mktemp -d)"
fi

cleanup_suite_tmp() {
    if [[ -n "${suite_tmp:-}" && -d "${suite_tmp}" ]]; then
        rm -rf "${suite_tmp}"
    fi
}

trap cleanup_suite_tmp EXIT

ROOT_DIR="$ROOT_DIR" TMP_DIR="$suite_tmp" bash "$suite_script"
