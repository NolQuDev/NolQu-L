#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="$(<"$ROOT_DIR/VERSION")"
CHANNEL="$(<"$ROOT_DIR/CHANNEL")"

fail() {
    printf 'FAIL %s\n' "$1" >&2
    exit 1
}

pass() {
    printf 'PASS %s\n' "$1"
}

[[ -n "$VERSION" ]] || fail "version-empty"
pass "version-present"

[[ "$CHANNEL" == "dev" || "$CHANNEL" == "stable" ]] || fail "channel-invalid"
pass "channel-valid"

if [[ "$CHANNEL" == "stable" && "$VERSION" =~ (a|b|rc) ]]; then
    fail "stable-channel-pre-release-version"
fi
pass "channel-version-policy"

NQL_VERSION_OUTPUT="$("$ROOT_DIR/nql" --version)"
[[ "$(printf '%s\n' "$NQL_VERSION_OUTPUT" | sed -n '1p')" == "nql     $VERSION" ]] || fail "nql-version-mismatch"
[[ "$(printf '%s\n' "$NQL_VERSION_OUTPUT" | sed -n '2p')" == "nqlc    $VERSION (x86_64-linux)" ]] || fail "nqlc-version-mismatch"
[[ "$("$ROOT_DIR/nolqulc" --version)" == "nolqulc $VERSION (x86_64-linux)" ]] || fail "nolqulc-version-mismatch"
pass "nql-version"

[[ "$(make -s -C "$ROOT_DIR" show-version)" == "$VERSION" ]] || fail "make-show-version-mismatch"
pass "make-show-version"

[[ "$(make -s -C "$ROOT_DIR" show-channel)" == "$CHANNEL" ]] || fail "make-show-channel-mismatch"
pass "make-show-channel"

grep -q "# NolQu-L $VERSION" "$ROOT_DIR/README.md" || fail "readme-version-mismatch"
pass "readme-version"

grep -q "## $VERSION -" "$ROOT_DIR/docs/project/CHANGELOG.md" || grep -q "## Unreleased" "$ROOT_DIR/docs/project/CHANGELOG.md" || fail "changelog-missing-version"
pass "changelog-version"

for path in \
    "$ROOT_DIR/bootstrap/README.md" \
    "$ROOT_DIR/bootstrap/manifest.tsv" \
    "$ROOT_DIR/bootstrap/machine/x86_64-linux/hex0.seed" \
    "$ROOT_DIR/bootstrap/machine/x86_64-linux/hex0.hex" \
    "$ROOT_DIR/bootstrap/machine/x86_64-linux/hex0.sha256" \
    "$ROOT_DIR/bootstrap/machine/x86_64-linux/hex0.reference.asm" \
    "$ROOT_DIR/bootstrap/machine/x86_64-linux/materialize.sh" \
    "$ROOT_DIR/bootstrap/stage0/README.md" \
    "$ROOT_DIR/bootstrap/stage0/x86_64-linux/stage0.seed" \
    "$ROOT_DIR/bootstrap/stage0/x86_64-linux/stage0.hex" \
    "$ROOT_DIR/bootstrap/stage0/x86_64-linux/stage0.sha256" \
    "$ROOT_DIR/bootstrap/stage0/x86_64-linux/stage0.reference.asm" \
    "$ROOT_DIR/bootstrap/stage0/x86_64-linux/materialize.sh" \
    "$ROOT_DIR/bootstrap/compiler/b0/README.md" \
    "$ROOT_DIR/bootstrap/compiler/b0/compiler.nql0" \
    "$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/b0.seed" \
    "$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/b0.sha256" \
    "$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/b0.reference.asm" \
    "$ROOT_DIR/bootstrap/compiler/b0/x86_64-linux/materialize.sh" \
    "$ROOT_DIR/bootstrap/compiler/c0/README.md" \
    "$ROOT_DIR/bootstrap/compiler/c0/compiler.nq" \
    "$ROOT_DIR/bootstrap/compiler/c0/frontend.nql" \
    "$ROOT_DIR/bootstrap/compiler/c0/FRONTEND.md" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-frontend.sha256" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/materialize-frontend.sh" \
    "$ROOT_DIR/bootstrap/compiler/c0/backend.nql" \
    "$ROOT_DIR/bootstrap/compiler/c0/BACKEND.md" \
    "$ROOT_DIR/bootstrap/compiler/c0/RUNTIME_IO.md" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-backend.seed" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-backend.sha256" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/materialize-backend.sh" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/compile-source.sh" \
    "$ROOT_DIR/bootstrap/compiler/c0/successor.nq" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0.seed" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0.sha256" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-successor.seed" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/c0-successor.sha256" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/materialize.sh" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/materialize-successor.sh" \
    "$ROOT_DIR/bootstrap/compiler/c0/x86_64-linux/compile.sh" \
    "$ROOT_DIR/tests/bootstrap/README.md" \
    "$ROOT_DIR/tests/bootstrap/run_tests.sh" \
    "$ROOT_DIR/tests/bootstrap/machine_foundation.sh" \
    "$ROOT_DIR/tests/bootstrap/stage0.sh" \
    "$ROOT_DIR/tests/bootstrap/bootstrap_compiler_b0.sh" \
    "$ROOT_DIR/tests/bootstrap/core_compiler_c0.sh" \
    "$ROOT_DIR/tests/bootstrap/c0_frontend.sh" \
    "$ROOT_DIR/tests/bootstrap/test_c0_frontend.py" \
    "$ROOT_DIR/tests/bootstrap/c0_backend.sh" \
    "$ROOT_DIR/tests/bootstrap/test_c0_backend.py" \
    "$ROOT_DIR/tests/bootstrap/test_c0_runtime_io.py" \
    "$ROOT_DIR/tests/bootstrap/fixtures/minimal_elf.nql0" \
    "$ROOT_DIR/tests/bootstrap/fixtures/c0/return2.nq" \
    "$ROOT_DIR/tests/bootstrap/fixtures/c0/return65.nq" \
    "$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_assert_range.nq" \
    "$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_assert_range_invalid.nq" \
    "$ROOT_DIR/tests/bootstrap/fixtures/c0/runtime_literal_order.nq" \
    "$ROOT_DIR/docs/README.md" \
    "$ROOT_DIR/examples/README.md" \
    "$ROOT_DIR/examples/core/README.md" \
    "$ROOT_DIR/examples/semantics/README.md" \
    "$ROOT_DIR/examples/llvm/README.md" \
    "$ROOT_DIR/tests/README.md" \
    "$ROOT_DIR/tests/compiler/README.md" \
    "$ROOT_DIR/tests/llvm/README.md" \
    "$ROOT_DIR/tests/ir/README.md" \
    "$ROOT_DIR/tests/meta/README.md" \
    "$ROOT_DIR/tests/shared/README.md" \
    "$ROOT_DIR/tools/README.md" \
    "$ROOT_DIR/.github/ISSUE_TEMPLATE/bug_report.md" \
    "$ROOT_DIR/.github/ISSUE_TEMPLATE/feature_request.md" \
    "$ROOT_DIR/.github/ISSUE_TEMPLATE/config.yml" \
    "$ROOT_DIR/.github/CODEOWNERS" \
    "$ROOT_DIR/.github/PULL_REQUEST_TEMPLATE.md" \
    "$ROOT_DIR/examples/core/hello.nq" \
    "$ROOT_DIR/examples/core/arrays.nq" \
    "$ROOT_DIR/examples/llvm/llvm_basic.nq" \
    "$ROOT_DIR/examples/llvm/llvm_fact.nq" \
    "$ROOT_DIR/examples/llvm/llvm_fact_local.nq" \
    "$ROOT_DIR/examples/llvm/llvm_func_local.nq" \
    "$ROOT_DIR/examples/llvm/llvm_if.nq" \
    "$ROOT_DIR/examples/llvm/llvm_func.nq" \
    "$ROOT_DIR/examples/llvm/llvm_while.nq" \
    "$ROOT_DIR/examples/semantics/functions.nq" \
    "$ROOT_DIR/examples/semantics/branching.nq" \
    "$ROOT_DIR/docs/project/ROADMAP.md" \
    "$ROOT_DIR/docs/language/CORE_LANGUAGE.md" \
    "$ROOT_DIR/docs/language/FEATURE_STATUS.md" \
    "$ROOT_DIR/docs/compiler/ARCHITECTURE.md" \
    "$ROOT_DIR/docs/compiler/LLVM_BRIDGE.md" \
    "$ROOT_DIR/docs/compiler/LLVM_BOOTSTRAP_POLICY.md" \
    "$ROOT_DIR/docs/compiler/LLVM_BOOTSTRAP_STATUS.md" \
    "$ROOT_DIR/docs/project/RELEASING.md" \
    "$ROOT_DIR/LICENSE" \
    "$ROOT_DIR/docs/community/TRADEMARK.md" \
    "$ROOT_DIR/docs/community/CONTACT.md" \
    "$ROOT_DIR/docs/community/CONTRIBUTING.md" \
    "$ROOT_DIR/docs/community/SECURITY.md" \
    "$ROOT_DIR/docs/community/CODE_OF_CONDUCT.md" \
    "$ROOT_DIR/docs/community/AUTHORS.md" \
    "$ROOT_DIR/docs/community/SUPPORT.md" \
    "$ROOT_DIR/docs/community/GOVERNANCE.md" \
    "$ROOT_DIR/docs/community/FAQ.md" \
    "$ROOT_DIR/docs/community/STYLE_GUIDE.md" \
    "$ROOT_DIR/docs/project/COMPATIBILITY.md" \
    "$ROOT_DIR/docs/project/PACKAGING.md" \
    "$ROOT_DIR/docs/project/INSTALL.md" \
    "$ROOT_DIR/docs/compiler/BACKENDS.md" \
    "$ROOT_DIR/docs/project/PROJECT_STRUCTURE.md" \
    "$ROOT_DIR/docs/compiler/TESTING.md" \
    "$ROOT_DIR/docs/project/COMMANDS.md" \
    "$ROOT_DIR/docs/compiler/IR.md" \
    "$ROOT_DIR/docs/language/TERMINOLOGY.md" \
    "$ROOT_DIR/docs/language/DECISIONS.md" \
    "$ROOT_DIR/docs/language/KNOWN_LIMITATIONS.md" \
    "$ROOT_DIR/docs/language/ERRORS.md" \
    "$ROOT_DIR/docs/project/ROADMAP_SHORT.md" \
    "$ROOT_DIR/docs/project/STATE_OF_PROJECT.md" \
    "$ROOT_DIR/docs/project/REPO_INDEX.md" \
    "$ROOT_DIR/docs/project/MAINTAINER_CHECKLIST.md" \
    "$ROOT_DIR/docs/project/RELEASE_NOTES_TEMPLATE.md" \
    "$ROOT_DIR/docs/project/LABELS.md" \
    "$ROOT_DIR/docs/language/DESIGN_PRINCIPLES.md" \
    "$ROOT_DIR/tools/nq_llvm_bootstrap.py"; do
    [[ -f "$path" ]] || fail "missing-$(basename "$path")"
done
pass "required-files"
