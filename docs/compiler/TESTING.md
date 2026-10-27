# NolQu-L Testing

## Current Testing Model

NolQu-L uses several test layers rather than one monolithic suite.

## Main Test Entry Point

Run bootstrap, Reference R0 and frozen compatibility suites with:

```bash
make test
```

Run only the Reference R0 and frozen compatibility suites with:

```bash
./tests/compiler/run_tests.sh
```

`make test` runs canonical bootstrap checks before the Reference Compiler R0
suite. Run only the canonical checks with `make bootstrap-test`.
MCP and release gates are separate and must also run for tooling/integration changes:

```bash
.venv-mcp/bin/python -m unittest discover -s tests/mcp -v
make release-check
```

## Test Layers

- `tests/bootstrap/machine_foundation.sh`: canonical seed reconstruction,
  self-decoding, syscall errors, and ELF invariants
- `tests/bootstrap/stage0.sh`: predecessor reconstruction, symbolic patches,
  self-reconstruction, runnable ELF generation, limits, and resource cleanup
- `tests/bootstrap/c0_frontend.sh`: B0 rebuild parity, NQAF/1..4 syntax,
  precedence, functions and call-statement ownership
- `tests/bootstrap/c0_backend.sh`: pinned AST-to-ELF, control flow, functions,
  checked byte/stream runtime and invalid-input/resource gates
- `tests/mcp/`: capability boundaries, canonical status, revised-authority
  resources and fresh-process stdio protocol from an unrelated directory
- `tests/compiler/smoke.sh`: quick user-visible feature checks
- `tests/compiler/regression.sh`: regressions in the main compiler path
- `tests/compiler/diagnostics.sh`: parser and semantic diagnostics
- `tests/llvm/smoke.sh`: maintenance suite for the frozen bootstrap LLVM subset
- `tests/ir/bridge.sh`: export-ir, JSON, and IR-to-LLVM bridge checks
- `tests/ir/diagnostics.sh`: malformed IR and bridge failure diagnostics
- `tests/ir/parity.sh`: semantic parity checks between NASM and `ir-llvm`
- `tests/meta/release_check.sh`: version, doc, and project-metadata consistency

## Testing Priorities

- prove every canonical bootstrap stage from concrete artifacts
- preserve Reference Compiler R0 behavior
- keep legacy LLVM tests green without growing their architectural role
- make semantic rules visible through examples and tests
- keep docs and release metadata aligned with the actual repo state

## Practical Rule

If a user-visible semantic change lands, it should normally update:

- docs
- examples when relevant
- tests

## Related Docs

- [SEMANTICS.md](../language/SEMANTICS.md)
- [FEATURE_STATUS.md](../language/FEATURE_STATUS.md)
- [RELEASING.md](../project/RELEASING.md)
