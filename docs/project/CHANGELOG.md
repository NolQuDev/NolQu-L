# Changelog

## Unreleased

### Added

- Retain bounded supervisor lifecycle and last-live deadline observations in host
  test receipts. Known cleanup requests remain distinct from an unobserved target
  signal sender; aborts during observation preserve failure evidence. Existing
  limits, target results, historical receipts and canonical compiler bytes stay
  unchanged. The original native timeout and historical SIGKILL remain open.

- Retain optional CPU time and largest-waited-child RSS from each private test
  supervisor after cleanup. New controls cover actual allocations, descendants,
  isolation, ordinary/signal exits and unavailable accounting. These host
  observations add no memory cap and do not diagnose the historical SIGKILL.

### Fixed

- Reject bootstrap materializer/stream-adapter outputs that alias required
  source, pin, wrapper or predecessor inputs. Recheck before exact-destination
  publication and preserve pinned rebuild bytes and failed-output cleanup.
- Consume complete ELF inspection reports before searching them. LLVM readelf
  broken pipes can no longer invert positive or negative bootstrap checks;
  inspector errors remain controlled failures. Add portable alias/publication
  regressions and a required real-hardlink Linux check.
- Reject executable GNU_STACK permissions in combined or separate flag fields
  across all four Core gates, including the `R E` form. ELF inspection test
  launchers preserve Python paths containing spaces and clean up their private
  process group and suite files on timeout or cancellation.

- Correct active feature/project status pages that still described the full
  Linux suite as unrun or used earlier checkpoint counts as current. Record
  matching finite compiler results through PRoot and Termux Python/QEMU while
  retaining their traced context and the unrun native qualification gate.
- Keep supervisor metadata ingestion bounded to a 4 KiB regular-file JSON
  control. Malformed, missing, oversized, symlink, directory and FIFO controls
  retain a failed invocation and its stream identities before a controlled
  host error. This repairs evidence loss and an out-of-deadline FIFO read;
  it does not explain the historical comparison-backend SIGKILL.
- Align current validation/roadmap with the published Alpha 1 and fresh
  eleven-gate baseline. Native execution of the newer differential profile
  remains NOT RUN; Alpha 2, Stable and security qualification are not implied.

## 1.0.0-alpha.1 — 2026-10-29

First public Alpha source snapshot and optional offline qualification bundle.
Release notes: [1.0.0-alpha.1](../releases/1.0.0-alpha.1.md).
Development continues on the `dev` channel.

### Fixed

- Clarify NolQu-Lang as the full name and NolQu-L as the short form, with L
  already meaning Language. Remove redundant name suffixes from active
  references, and correct stale CLI terminology. Command/artifact identifiers,
  historical version labels and canonical source/seed/pin bytes are preserved.
- Bind offline host-smoke success to the complete check inventory and unchanged
  initial bundle manifest; recheck native Termux context after execution when
  required. Partial checks or a changed manifest cannot publish a passing result.
- Use English for remaining MCP messages, comments, readiness labels and
  language/test examples. Document lookup accepts English headings and version
  wording while retaining exact historical input aliases. Compiler semantics,
  canonical source/artifact identities and release maturity are unchanged.
- Publish a complete English translation of the Nine Pillars from Concept v10
  Assembly-Level, preserving all original sections, requirements, exceptions
  and examples. README, documentation and contributor navigation expose the
  same principles page; implementation maturity is unchanged.
- Repair documentation links that contained local `/root/Nolqu` paths so they
  open the matching files or directories on GitHub. Historical removed command
  names remain text rather than links to nonexistent files.

### Changed

- Use `Main` for integration, `Dev` for Alpha development, and reserve an empty
  `Stable` for future RC/final work. CI checks the populated branch's version role;
  creating the branches does not promote the current Alpha or publish a release.
- Keep internal master prompts, concept attachments, agent plans and session
  reports outside public source snapshots. Public summaries use this changelog,
  implementation contracts and `VALIDATION.md`; a required publication path
  check also rejects already-tracked internal files. Earlier Git history is
  unchanged by removing files from the current branch.
- Current version metadata and CLI display use `1.0.0-alpha.1` at the maintainer's
  request. `v1.0.0-alpha.1` is the intended tag spelling if a tag is later made.
  This is a development naming reset from `1.0.2a1`, not a claim of SemVer upgrade,
  stable compatibility or an official published release. Historical version
  records and canonical compiler sources/seeds/pins remain unchanged.

### CI

- Linux qualification at `13450398` passes all ten gates: 1,083 main PASS
  markers, 127 MCP methods, real hard-link protection, finite assurance,
  publication controls and nine release checks. Results and scope are recorded
  in [VALIDATION.md](VALIDATION.md); no stable/security/self-host promotion.
- Add experimental sequential Linux qualification for real hard-link protection,
  compiler regressions, MCP, finite assurance and retained failure evidence.
  Native Android coverage stays separate. Workflow availability is not a passing
  CI result or stable/self-host promotion; see `docs/compiler/LINUX_CI.md`.

### Added

- Offer `run --differential` in the offline Termux host bundle: the existing
  independent 48-program corpus runs on both runtime profiles, with exact
  full-width results, byte-effect order and two sensitivity controls. Schema-2
  bundles include the verified oracle; old bundles retain ordinary smoke.
  Linux controls remain separate from actual native Termux qualification.
- A finite independent differential compiler gate in `make test` and
  `make bootstrap-test`: 48 defined scalar/call/control/byte-effect programs
  under both runtime profiles, full-width signed result checks, exact effect
  order, two real wrong-result sensitivity controls and bounded retained
  evidence. Compiler syntax, ABI, source/seeds/pins and release version remain
  unchanged; this does not qualify the Full Compiler or full NolQu-L Safety.

- Experimental offline Android host smoke bundles with independent pinned seed
  copies, actual native-Termux context checks and retained bounded invocations.
  The optional profile does not promote a compiler stage or add a target backend.

- Experimental host-test invocation evidence through `NQL_NATIVE_EVIDENCE_DIR`: exact available byte blobs, PID/start observations, distinct signal/timeout outcomes and 17 FD/path/cancellation controls. Compiler source/seed/ABI unchanged; historical comparison-backend SIGKILL remains OPEN.

- experimental canonical C0.32 native process arguments, checked arena addresses,
  explicit invariant-bearing `unsafe` blocks and raw Linux/x86_64 `syscall6`
- standalone NolQu-L `examples/canonical/native_cat.nql` for literal file/stdin
  binary copying with explicit I/O progress and descriptor ownership
- host-only deterministic native-boundary assurance profile, retained corpus,
  bounded failure detection and independent expected-behavior checks under
  `tests/security/`; this is finite testing, not complete security qualification
- canonical x86_64 Linux Machine-Level Foundation under `bootstrap/`, including
  a raw ELF64 seed, auditable hexadecimal manifest, SHA-256 identity, and
  non-canonical assembly review aid
- canonical Stage 0 symbolic flat-binary emitter built directly by `hex0.seed`,
  with deterministic symbol resolution, self-reconstruction, bounded resource
  use, diagnostics, and runnable ELF generation
- `make machine-foundation`, `make stage0`, `make stage0-test`, and
  `make bootstrap-test` for deterministic seed reconstruction,
  self-reconstruction, syscall/error, and ELF invariant checks
- `bootstrap/manifest.tsv` for explicit predecessor-stage status without
  claiming unimplemented bootstrap generations
- root `VERSION` file as release metadata
- root `CHANNEL` file for `stable` vs `dev`
- [ROADMAP.md](ROADMAP.md) for release planning
- [ARCHITECTURE.md](../compiler/ARCHITECTURE.md) for codebase structure
- [LICENSE](../../LICENSE), [TRADEMARK.md](../community/TRADEMARK.md), [CONTACT.md](../community/CONTACT.md), [CONTRIBUTING.md](../community/CONTRIBUTING.md), and [SECURITY.md](../community/SECURITY.md) for project legal/contact/governance metadata
- [CODE_OF_CONDUCT.md](../community/CODE_OF_CONDUCT.md) and [AUTHORS.md](../community/AUTHORS.md) for collaboration policy and authorship metadata
- [SUPPORT.md](../community/SUPPORT.md) and [GOVERNANCE.md](../community/GOVERNANCE.md) for support flow and project-authority metadata
- [FAQ.md](../community/FAQ.md) and [STYLE_GUIDE.md](../community/STYLE_GUIDE.md) for common project answers and contribution/documentation style guidance
- [COMPATIBILITY.md](COMPATIBILITY.md) and [PACKAGING.md](PACKAGING.md) for backend/platform expectations and distribution layout notes
- [INSTALL.md](INSTALL.md) and [BACKENDS.md](../compiler/BACKENDS.md) for setup workflow and focused backend-role documentation
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) and [TESTING.md](../compiler/TESTING.md) for repo-layout and test-model documentation
- [COMMANDS.md](COMMANDS.md) and [IR.md](../compiler/IR.md) for workflow reference and exported-IR documentation
- [TERMINOLOGY.md](../language/TERMINOLOGY.md) and [DECISIONS.md](../language/DECISIONS.md) for shared project vocabulary and explicit design-decision tracking
- [KNOWN_LIMITATIONS.md](../language/KNOWN_LIMITATIONS.md) and [ERRORS.md](../language/ERRORS.md) for explicit limitation tracking and error-model documentation
- [ROADMAP_SHORT.md](ROADMAP_SHORT.md) and [STATE_OF_PROJECT.md](STATE_OF_PROJECT.md) for compact direction and project-status summaries
- [REPO_INDEX.md](REPO_INDEX.md) and [MAINTAINER_CHECKLIST.md](MAINTAINER_CHECKLIST.md) for doc navigation and maintainer workflow
- [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md) and [DESIGN_PRINCIPLES.md](../language/DESIGN_PRINCIPLES.md) for release drafting and concise philosophy reference
- [LABELS.md](LABELS.md) and [.github/CODEOWNERS](../../.github/CODEOWNERS) for lightweight GitHub triage and ownership metadata

### Bootstrap

- C0.32 frontend/backend pins come from independent B0 rebuilds; actual full-source
  B/C component images are byte-identical, with both runtime profiles and retained
  old named oracles. NQAF/6 adds native-scope validation while successful old
  formats remain compatible. Full Compiler/self-hosting/Verified are not promoted.
- the original C0.32 execution checkpoint passed 1079 main PASS markers,
  124 MCP methods and nine release checks, retaining earlier labels. The reliability
  continuation now passes 1080 markers with every 1079-label post-formatter baseline
  result retained, plus fresh MCP 124, combined generation proof and 594 assurance
  invocations. Compiler sources/pins, protocol schemas and public command names
  remain unchanged. No public version bump or release; the historical SIGKILL is OPEN.

### Fixed

- The host-test supervisor reaps adopted exited children while its command is
  still running, preserving cleanup checks for nested compiler tests and exact
  target exit/signal reporting.
- GitHub qualification defines runner paths in step scope, where the runner
  context is available; local controls cover the validation failure.
- Reference Compiler R0 states its existing absolute-addressing default
  explicitly, avoiding NASM 3 deprecation output during successful quiet builds.
- Direct execution selects the generated file in the current directory when
  its output name has no slash, preserving `PATH` isolation.
- Host-test evidence publication works without Android Python's unavailable
  `os.link`, using directory-locked complete-file rename and existing-blob
  validation. Native descriptor/path controls and GNU/LLVM entry-address hex
  formatting retain their original numeric and behavior oracles.
- Native Android fault fixtures preserve guest `EBADF` tests through host runtime
  startup. MCP command cleanup can bind runtime libc pidfd APIs when Python omits
  them, preserving identity-safe cleanup and rejection when pidfds are unavailable.
- Native MCP stdio launch retains the standard Termux exec preload. Wide-branch
  inspection uses native x86 disassembly on Android while preserving the existing
  GNU Linux oracle and rejection of opcode bytes inside immediates.
- Optional Android smoke executes pinned runner source rather than unchecked
  cached bytecode, preserves terminal failure reporting after a rename error,
  and hashes large regular adapters separately from guest stream limits.

- C0.32 argument index/capacity diagnostics now use exactly one location
  separator. Strict regression assertions failed on both profiles before the
  four-immediate source fix; independent B0 rebuilds and runtime review verify
  the replacement backend pin. Unreleased, with no public version bump.
- candidate-only contextual parsing of a condition variable named `unsafe` now
  preserves legacy AST/ELF behavior; native runtime helper addresses use the
  measured wide-image pool origin. Neither defect is attributed to a released
  version; permanent regression tests cover the corrections.

### Known Issues

- an earlier full run's frozen comparison backend received unexplained SIGKILL;
  the later identical-input serial pass does not fix or explain it. Stable and
  security-qualified promotion remain blocked pending attribution and required
  assurance. See [the session record](VALIDATION.md).
- combined installation from an unbuilt foreign cwd still needs the normal
  legacy `make compiler` prerequisite; canonical-only relocation does not need it.

### Improved

- formal project naming and architecture now follow NolQu-L Concept v2
- the existing NASM compiler is explicitly Reference Compiler R0, not Stage 0
- LLVM/Python tooling is explicitly frozen outside the canonical bootstrap chain
- `nq --backend llvm` now uses the frontend/IR bridge for user-facing LLVM output, supports `--emit <path>` for LLVM IR, and keeps `--dump-tokens`, `--dump-ir`, and `--export-ir` as frontend inspection artifacts under the LLVM backend
- `make ir-json` and the user-facing LLVM bridge now parse exported IR through `tools/nq_ir_dump_parser.nq`; the Python parser remains as a byte-for-byte oracle until deletion criteria are met
- `Makefile` now exposes `show-version`, `show-channel`, `dev`, and `stable`
- README, releasing notes, and release checks now treat legal/contact/trademark docs as first-class project metadata
- the project license is now explicitly open-source under MIT instead of a temporary conservative placeholder

## 1.0.2a1 - 2026-03-26

Second major update cycle begins with LLVM backend bootstrap work.

### Added

- experimental `--backend llvm` path in the wrapper
- `tools/nq_llvm_bootstrap.py` for the first LLVM IR generation path
- `examples/llvm/llvm_basic.nq` as a minimal LLVM-backed example
- `tests/llvm/smoke.sh` and `make llvm-smoke` for LLVM backend coverage
- `tools/nq_ir_dump_parser.py`, `make ir-json`, and `tests/ir/bridge.sh` for the next bridge step from exported IR dump to structured JSON
- `tools/nq_ir_json_to_llvm.py` and `make ir-llvm` for the first structured IR-to-LLVM lowering pass on a narrow subset, now extended to local/global slots, basic string print, basic array literal/indexing/update, basic `for` loops, plus the basic control flow used by `if`, `while`, and simple recursion
- [CORE_LANGUAGE.md](../language/CORE_LANGUAGE.md) and [FEATURE_STATUS.md](../language/FEATURE_STATUS.md) to separate stable language surface from experiments and syntax-only features
- [LANGUAGE.md](../language/LANGUAGE.md) now reflects the same `core`, `experimental`, and `syntax-only` split instead of presenting all parser features as equally stable
- README, architecture, roadmap, and LLVM bridge docs documented the
  then-current transition away from duplicate source parsing; this direction
  is now superseded by the canonical machine bootstrap recorded above
- [LLVM_BOOTSTRAP_POLICY.md](../compiler/LLVM_BOOTSTRAP_POLICY.md) now defines what changes are acceptable in the bootstrap LLVM parser and what work should move to the IR bridge instead
- [LLVM_BOOTSTRAP_STATUS.md](../compiler/LLVM_BOOTSTRAP_STATUS.md) now freezes the currently maintained bootstrap subset so it cannot quietly grow into a second language surface
- `tests/llvm/smoke.sh` is now explicitly marked as a maintenance suite for the frozen bootstrap subset rather than the main feature-growth path
- `tests/ir/parity.sh` now compares representative program output between the stable NASM backend and the IR-to-LLVM bridge, including globals + recursion, local-array function cases, branch/array combinations, mixed global-array call flows, loop-driven stateful helper calls, nested helper-chain stack flows, recursion that mutates global array state, deeper `else if` chains with side effects, `else if` control flow combined with recursion, `for` loops that call helpers, branch, recurse, and mutate global state, plus single-loop and nested-loop `break`/`continue` flow across both `while` and `for`
- `parse_for`/`parse_continue` and the IR-to-LLVM bridge now agree on `continue` semantics for `for` loops via a dedicated continue label, which fixes hangs in nested `for` + `continue` cases and keeps parity green on nested `for` loop control flow
- docs and tests now state explicitly that locals are currently function-scoped rather than block-scoped, with regression/parity coverage to keep that behavior visible and intentional
- roadmap and feature-status docs now explicitly defer block-scoped locals until Nolqu is ready for a larger semantic-model change
- examples now include loop-control with helper/global-state flow and recursive array/loop flow so the active supported surface is easier to see from user-facing programs
- the language reference now includes a compact "Current Semantic Rules" section so active rules like function-scoped locals and loop-control behavior are explicit in one place
- [SEMANTICS.md](../language/SEMANTICS.md) now gives a short semantic summary separate from the full syntax reference
- examples and tests now cover stronger argument patterns, including the current 8-parameter limit and passing arrays through ordinary function calls
- examples and tests now also cover nested function calls inside argument lists so argument evaluation patterns are no longer represented only by flat calls
- examples and tests now also lock down left-to-right argument evaluation order instead of leaving it implicit
- argument coverage now also includes recursive and stateful argument expressions in a single call, so evaluation-order semantics are tested beyond trivial helper cases
- examples and tests now explicitly cover zero-argument calls so the current argument model is locked from the empty case up through the 8-parameter limit
- argument diagnostics and docs now state the current boundaries explicitly: positional-only calls, no default/named/variadic arguments, and compile-time rejection of wrong argument counts
- examples, tests, and docs now also state that array arguments are shared mutable values in the current model, so callee-side mutation is visible to the caller
- `tests/ir/diagnostics.sh` now checks failure-path parity for `--export-ir` and verifies unsupported-feature diagnostics in the IR-to-LLVM bridge, including malformed-IR structure and stack-state invariant errors such as bad labels, missing function markers, incomplete string export metadata, invalid operand-state transitions, and invalid ABI-style parameter offsets, plus source-line-aware bridge errors, op/name context, and function-context reporting

### Improved

- root version metadata advanced to `1.0.2a1`
- project channel reopened to `dev`
- architecture and roadmap docs now describe the backend split between stable NASM and experimental LLVM
- the LLVM bootstrap subset now includes assignment, basic `if/else`, `while`, simple integer functions with locals, nested calls, `return`, basic recursion, and basic function-call validation
- roadmap and README now state the longer-term goal of growing Nolqu toward a more serious native-language toolchain
- added [LLVM_BRIDGE.md](../compiler/LLVM_BRIDGE.md) for the
  historical Python-to-IR LLVM migration, now frozen as legacy compatibility
- the wrapper and Makefile exposed IR export for the historical LLVM bridge;
  the dump includes readable symbol names for named IR ops

## 1.0.1 - 2026-03-26

Stable patch release for the `1.0.x` line.

### Improved

- root version metadata finalized at `1.0.1`
- release channel moved from `dev` to `stable`
- the `1.0.1` cycle now lands as a stable release after the alpha, beta, and release-candidate hardening passes

## 1.0.1rc1 - 2026-03-26

First release candidate for the `1.0.1` release line.

### Improved

- root version metadata advanced to `1.0.1rc1`
- release status moved from beta to release candidate while staying on the `dev` channel
- README and release notes synchronized for final pre-stable verification

## 1.0.1b2 - 2026-03-26

Second beta for the `1.0.1` release line.

### Improved

- root version metadata advanced to `1.0.1b2`
- beta release status carried forward cleanly on the `dev` channel
- README and release notes synchronized for the new beta iteration

## 1.0.1b1 - 2026-03-26

First beta for the `1.0.1` release line.

### Improved

- root version metadata advanced to `1.0.1b1`
- release status moved from alpha to beta while staying on the `dev` channel
- README and release docs now describe the project as being on the beta path toward `rc` and `1.0.1`

## 1.0.1a8 - 2026-03-26

Release-polish alpha for the `1.0.1` line.

### Added

- `tests/meta/release_check.sh` for version, channel, wrapper, and doc consistency checks
- `make release-check` as a dedicated pre-release workflow target

### Improved

- root version metadata advanced to `1.0.1a8`
- `make dev` and `make stable` now include release-consistency verification
- release docs now explicitly require `release-check` before moving toward beta, rc, or stable

## 1.0.1a7 - 2026-03-26

Release-discipline and test-organization hardening release.

### Added

- modular test layout with `tests/compiler/smoke.sh`, `tests/compiler/regression.sh`, and `tests/compiler/diagnostics.sh`
- [RELEASING.md](RELEASING.md) for release workflow guidance
- `Makefile` targets for `smoke`, `examples`, `set-dev`, and `set-stable`

### Improved

- root version metadata advanced to `1.0.1a7`
- release/channel workflow is now easier to inspect and switch
- regression runner now delegates to smaller test scripts instead of one large shell file

## 1.0.1a6 - 2026-03-26

First large patch release after `1.0.0`.

### Added

- chained `else if` support in the parser
- compiler-side `--dump-tokens` mode
- compiler-side `--dump-ir` mode
- branching example program for the new control-flow syntax

### Improved

- CLI help and versioning now reflect the larger `a6` release
- wrapper now rejects invalid `--run`/`--emit` combinations with dump-only modes
- wrapper now keeps compiler and generated artifacts under `build/`
- repo now includes a root `Makefile` for common build/test/run workflows
- regression coverage now includes chained branching and compiler debug dumps

## 1.0.1a5 - 2026-03-26

Output and local-scope hardening release.

### Improved

- parser now rejects duplicate local `var` declarations inside functions
- CLI now supports `--emit <file.asm>` to control generated assembly output

### Added

- regression test for duplicate local variable declarations
- regression test for try/catch flow
- regression test for `--emit`

## 1.0.1a4 - 2026-03-26

Structural validation hardening release.

### Improved

- parser now rejects duplicate function names
- parser now rejects duplicate parameter names
- parser now guards loop nesting against `MAX_LOOP`
- parser now guards try nesting against `MAX_TRY`
- CLI now exposes explicit `--check` compile-only mode

### Added

- regression tests for duplicate function names
- regression tests for duplicate parameter names
- regression tests for loop nesting overflow
- regression tests for `--check`

## 1.0.1a3 - 2026-03-26

Parser validation hardening release.

### Improved

- parser now rejects `return` outside functions
- parser now rejects function declarations that exceed `MAX_PARAMS`
- added regression coverage for nested function calls and local stack usage

### Added

- regression tests for `return outside function`
- regression tests for parameter overflow
- stress test for nested calls with locals

## 1.0.1a2 - 2026-03-26

Function-call validation hardening release.

### Improved

- parser now rejects calls to undefined functions
- parser now rejects calls with the wrong number of arguments
- function-call validation fails early before codegen

### Added

- regression tests for undefined-function and wrong-arity errors

## 1.0.1a1 - 2026-03-26

Hardening release focused on stability.

### Improved

- clearer parser message for unexpected top-level statements
- parser now stops after the first hard error instead of spamming follow-up errors
- safer token helpers when parser position moves out of range

### Fixed

- token buffer overflow now fails explicitly instead of risking out-of-bounds writes
- IR buffer overflow now fails explicitly instead of silently truncating IR
- constant folding no longer underflows on very small IR programs
- dead-code elimination now respects more structural boundaries
- release/optimizer path revalidated against recursion and array cases

## 1.0.0 - 2026-03-26

First stable baseline for Nolqu.

### Added

- Core language baseline documentation in [LANGUAGE.md](../language/LANGUAGE.md)
- Project overview and usage docs in [README.md](../../README.md)
- CLI wrapper `nq` with:
  - `--help`
  - `--version`
  - `--build-compiler`
  - `--run`
- Example programs under `examples/`
- Smoke/regression tests under `tests/`

### Compiler

- Function arguments and stack-based calls
- Return values in `rax`
- Local variables via `rbp` stack frame
- Simple stable ABI for 1.0.0
- Recursive functions
- Arrays and array indexing
- Parser error exit with non-zero status

### Fixed

- Lexer dispatch alignment bug affecting `]`
- Function registration bug that broke function lookup and recursion
- Symbol insertion hashing bug that caused false undefined-variable errors
- Array parser token-restore issues
- tightened module handling in the frontend:
  - unknown module qualifiers in `demo.ping()` style calls are now rejected
  - duplicate module names are now rejected
  - duplicate function declarations inside module bodies now fail without cascade parser errors
- fixed the NASM array allocator so successive arrays use correct heap offsets, and added a runtime guard for fixed-heap exhaustion
- oversized single array literals are now rejected at compile time before reaching the fixed heap guard
- NASM and LLVM bridge array load/store paths now trap with a clear runtime error on out-of-bounds access
