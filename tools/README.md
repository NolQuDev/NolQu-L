# NolQu-L Legacy And Inspection Tooling

This directory contains public-tool orchestration as well as retained Python,
NolQu-L and LLVM compatibility/inspection tools. `nql_c0_driver.sh` is the private
Bash helper for `nqlc --backend canonical`; it invokes the unchanged pinned C0
source wrapper under `bootstrap/` and supplies no compiler semantics. The legacy
bridge tools remain for regression history and output-oracle comparisons.

No file here is Machine-Level Foundation, Stage 0, or proof of self-hosting.
New canonical compiler work belongs under `bootstrap/`.

## Retained Tools

- `nql_ir_dump_parser.nql`: canonical maintained exported-IR parser source
- `nq_ir_dump_parser.nq`: legacy symlink to `nql_ir_dump_parser.nql`
- `nq_ir_dump_parser.py`: byte-for-byte reference oracle for that parser
- `nql_ir_json_to_llvm.nql`: canonical source for the historical migration target
- `nq_ir_json_to_llvm.nq`: legacy symlink to `nql_ir_json_to_llvm.nql`
- `nq_ir_json_to_llvm.py`: current legacy IR-to-LLVM bridge
- `nq_llvm_bootstrap.py`: frozen source-level LLVM translator
- `nolqu_mcp.py`: architecture-aware development integration; never a canonical compiler stage
- `nql_c0_driver.sh`: private canonical CLI compile/check/run orchestration

The [canonical toolchain guide](../docs/compiler/CANONICAL_TOOLCHAIN.md) covers
the opt-in C0.31 subset, canonical-only installation and checksum stream example.

## NolQu-L MCP

The MCP exposes `nql_*`, `compile_nql`, canonical bootstrap, C0 probe,
artifact inspection, migration verification, and self-test operations. Legacy
`nq_*` command tools are not registered; the MCP invokes only `nql` and `nqlc`.
Formatter, linter, documentation, and compile-database wrappers are marked
`experimental` until their CLI contracts are implemented and verified.

`build_c0_frontend` and `run_c0_frontend_probe` are experimental `BUILD` tools
for the B0-built C0.31 source-to-AST component. `c0_frontend` is available to
artifact/hash/linkage inspection. The combined `run_c0_probe` retains the
C0.25 emitter and bounded-generation checks, then verifies the current component gates.
`build_c0_backend` and `run_c0_backend_probe` are also experimental `BUILD`
tools, for the B0-built C0.31 NQAF-to-ELF component (`c0_backend` in artifact
inspection). Its probe requires both pinned artifacts and exercises semantic
validation, checked arithmetic, malformed ASTs and atomic publication. The
C0.28 gate additionally verifies signed comparisons, nested branches/loops,
lexical scope, early returns, delimiter corruption and the 64-block bound.
The C0.29 function gate additionally verifies forward/nested/recursive calls,
mutable parameters, full-length callee resolution, argument evaluation order,
independent AST arity bounds, 64 active frames, and diagnostic I/O failures.
`function_calls_verified` and `parameter_scope_verified` in the backend probe are
false unless the pinned components and runtime gate all pass.
The C0.30 gate verifies call statements, exact physical AST links and single
ownership, checked byte-memory access, shared runtime storage and stream I/O.
`call_statements_verified`, `byte_memory_verified` and `stream_io_verified` also
remain false unless their respective pinned component gates pass.
The combined probe advances only when emitter, frontend and backend pass.
C0.31 also requires the complete capacity/profile/generation gate and validates
raw evidence, actual sources, selected artifacts, six component comparisons and
18 named oracle selectors on each of B/C. Separate `capacity_verified`,
`compiler_profile_verified` and `component_generation_verified` flags fail
closed on missing, changed, partial or unsuccessful evidence. Metadata alone
does not run a compiler or verify those flags. One combined invocation shares
its fresh proof; no persistent success cache is used. All 120 existing tool
names remain available. The access patch adds only optional `backend` and
`compiler_profile` inputs as described below; old required fields and legacy
string return schemas remain. See `bootstrap/compiler/c0/CAPACITY.md` for the
installed identities and completed pre/postinstallation verification.
`c0_version`, `frontend_version`, and `backend_version` identify the distinct
components; a backend failure cannot be hidden by predecessor success.
Neither result promotes Full Compiler or self-hosting. The grammar and NQAF
format are documented in `bootstrap/compiler/c0/FRONTEND.md`; scalar runtime
semantics and code generation in `bootstrap/compiler/c0/BACKEND.md`, and
structured NQAF/2 control flow in `bootstrap/compiler/c0/CONTROL_FLOW.md`, and
NQAF/3 function/ABI contracts in `bootstrap/compiler/c0/FUNCTIONS.md`, and
NQAF/4 and byte/stream runtime in `bootstrap/compiler/c0/RUNTIME_IO.md`.
Reload a running MCP server after upgrading this module to discover the new
tools; the existing process does not hot-reload Python definitions.

`compile_nql(..., backend="canonical", compiler_profile=False)` selects real C0
compilation. Omitting backend retains `nasm`. Ordinary compilation always requests
an output (default: `.nolqu-mcp/build/<source-stem>` under the MCP root), preventing
implicit execution and public tool-name collisions. Explicit `flags="--run"`
still requests execution; the source precedes `--` and its literal runtime tail.
Named outputs keep their requested paths. Check/IR stdout modes keep
their CLI contracts; canonical IR/assembly/object modes are unsupported. Output
paths are root confined, malformed flag quoting returns a structured error, and
only successful observed file publication appears in `artifacts`. Failure never
labels a preserved old output as a new artifact. `compile_file` and
`run_pipeline_step(..., "full")` also suppress implicit execution and retain
string results; pipeline `parse` runs `--check`, not a parse-only guarantee.

`nql_init(..., backend="canonical")` persists only `[build] backend`.
`nql_build/run/test/check` accept `backend=""` and `compiler_profile=False`;
an omitted backend honors the manifest, then defaults to `nasm` if absent.
Profile is forwarded only when true and never persisted/inferred. Canonical
`nql_build` validates cache identity; canonical `nql_run` recompiles through
`nqlc --run` on every invocation, including after a cache hit. This incurs actual
frontend/backend compilation and publication work before execution.

MCP orchestration requires the Python MCP SDK on Linux with procfs, subreaper
support and pidfds. Commands receive EOF when no input was supplied, keeping
protocol stdin private; explicit input and process-tree cleanup use the reviewed
executor. Public canonical CLI compilation itself uses Bash/GNU coreutils and
QEMU on ARM, with util-linux `setsid` needed only for terminal input runs.

Tool capabilities are explicit:

```text
READ_ONLY  WRITE  BUILD  DESTRUCTIVE  REMOTE  UNSAFE_SHELL
```

Destructive operations require `confirm=true`. Remote and arbitrary-shell
operations additionally require `NOLQU_MCP_ALLOW_REMOTE=1` and
`NOLQU_MCP_ALLOW_UNSAFE_SHELL=1`, respectively. Dedicated tools are the normal
interface; `exec_shell` is an explicit fallback, not the default execution
path.

Command results include `ok`, `exit_code`, `stdout`, `stderr`, `duration_ms`,
`timed_out`, `changed_files`, and `artifacts`. Output is bounded by
`NOLQU_MCP_MAX_OUTPUT_BYTES`, `NOLQU_MCP_MAX_STDOUT_BYTES`, and
`NOLQU_MCP_MAX_STDERR_BYTES`. File edits use same-directory temporary files,
`fsync`, atomic rename, and optional `expected_sha256` concurrency guards.

Audit events are appended to `.nolqu-mcp/audit.jsonl` and can be read through
`mcp_audit_log`. Set `NOLQU_MCP_AUDIT=0` only when local auditing must be
disabled explicitly.

Architecture resources use `nolqu://...` URIs. Official workflow prompts are
available for C0 development, regression investigation, codegen review,
bootstrap audit, and release preparation.
The section-backed resources read `NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md`
from the repository root, match complete top-level headings, and do not fall
back to obsolete development documents. That internal attachment is optional
and excluded from public snapshots. When absent, those resources explicitly
return `ERROR` instead of claiming the design text is available. Public change
notes and contracts live under `docs/` and `bootstrap/`.

Generated messages use English. Section lookup prefers `33. FFI AND ABI` and
also accepts the original heading as an input alias. C0 version lookup accepts
English and historical wording. Selected source text is returned without
translation, subject to the existing output limit. Legacy input fixtures
preserve exact original text.

Tests use the configured MCP interpreter:

```sh
.venv-mcp/bin/python -m unittest discover -s tests/mcp -v
```

This includes actual stdio initialization and resource/prompt/tool discovery
from an unrelated working directory. Python here is development tooling, not
a semantic bootstrap stage.

## Maintenance Rule

- keep existing valid tests green
- fix crashes, diagnostics, and compatibility regressions when necessary
- do not add new core language semantics here
- do not describe Python-to-NolQu-L bridge migration as self-hosting
- delete a legacy tool only after no supported command, test, or document needs it

## Historical Flow

```text
Reference Compiler R0 exported IR
-> nql_ir_dump_parser.nql
-> nq_ir_json_to_llvm.py
-> LLVM compatibility output
```

This flow remains testable but is not a successor to Stage 0.
