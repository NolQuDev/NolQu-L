# C0.31 Compiler-Source Capacity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile and execute both actual C0 component sources through the canonical source-driven pipeline, with coherent capacity and resource checks and preserved predecessor behavior.

**Architecture:** Add an explicit B0 compiler-runtime profile, then widen C0's indexed storage and NQAF representation without changing successful legacy output. Separate AST identity from native frame slots, carry runtime profile explicitly, and verify candidate generations before advancing the pinned component set.

**Tech Stack:** Stage0-readable x86_64 machine source, B0-compatible flat NolQu-L, direct Linux syscalls, standalone ELF64, Bash orchestration and Python unittest oracles; QEMU for execution/debugger probes on this aarch64 host.

**Spec:** [C0.31 Compiler-Source Capacity](../specs/2026-10-13-c031-compiler-capacity-design.md), subordinate to [the revised authority](../../../NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md) and [the concept](../../../NolQu-LConcept.docx).

**Status: COMPLETE for the experimental C0.31 capacity milestone, 2026-10-23.** Execution approved on 2026-10-14 in an isolated copy of the actual dirty tree. Tasks 1-6 completed their regression/review gates. Whole-change review then reopened and repaired B0's broken-stderr/unmap double-fault path, with four RED/GREEN cases and preserved default bytes. Task 7 completed fresh eight-command prevalidation, independent SPEC/QUALITY/whole-change approval, coherent canonical seed/pin installation and the exact eight promoted-phase commands. Final document/resource checks and independent whole-change closure also passed. All seven tasks are complete within this bounded contract. No public release, commit, merge or push is claimed. Execution ledger: `.superpowers/sdd/2026-10-13-c031-compiler-capacity/progress.md`. Actual receipts and rollback are under `/tmp/nql-c031-execution-20261014.SWSw0P`.

## Global Constraints

- Authority reconciliation (2026-10-16): the Assembly-Level master and v10 concept add design targets, not an instruction to repeat completed milestones or change the canonical pipeline. The spec records their relationship. Continue this capacity plan; do not add assembly syntax, volatile/atomics, FFI or full Safety claims to it.

- Canonical build: machine -> Stage0 -> B0 -> C0. Host Python/assembly tools may inspect and test, never supply a semantic compilation stage or promoted binary.
- Source 262,144 bytes; tokens/nodes 65,536 each; NQAF/5 header/records 32 bytes with u32 spans/IDs; source excludes the 16-byte NQSC envelope.
- Default byte arena 65,536 bytes; compiler profile 16,777,216 bytes, mapped RW/NX. Source size alone must not select that profile.
- Control depth 64, parameters 6, user call depth 64, function frame 4,096 bytes/512 i64 slots. Large global node IDs cannot become stack offsets.
- Wide ELF cap 8,388,608; code below 0x600000; helpers [0x600000,0x604000); diagnostic data [0x604000,0x800000).
- Preserve successful NQAF/1..4 and default B0 ELF bytes. Preserve B0/C0's distinct successful intrinsic return and arithmetic semantics.
- Syntax/semantic/capacity errors: exit 1, no artifact. C0 runtime arithmetic/range: 70; I/O/resource failures: 74. No recursive failure on broken stderr.
- Use the exact disjoint arena regions in the spec, including sentinel entries. All counters, intermediate decodes and fixups must retain their required width.
- No new language syntax, general allocator, optimizer, modules, public CLI naming changes, VERSION/CHANNEL bump or Full Compiler/self-hosting promotion.
- Preserve the dirty checkout. No automatic commit, branch switch, reset, merge, push or release. Historical Astra publishing approval is not NolQu-L publishing approval.
- Before execution, use the worktree skill to establish an isolated workspace containing the actual dirty/untracked sources. A worktree at HEAD alone omits the current bootstrap tree; verify copied identities before work. Do not stage unrelated files to make isolation convenient.
- Every task requires RED -> minimal implementation -> GREEN, then separate spec-compliance and code-quality reviews. Fix findings before advancing; missing review is not a passed review.

## Review Focus

1. Fragmented NQSC magic/header and valid-prefix input without EOF must neither lose source bytes nor emit premature AST. Task 2 owns the transport tests.
2. A long source in profile 0 must still reject byte offset 65,536, while a shadowing user function must not allocate an intrinsic arena. Task 4 owns both cases.
3. Long identifiers, high source offsets and user node ID 513 must not alias truncated lexemes or old intrinsic IDs. Tasks 2 and 3 own these checks.
4. Broken stderr, failed mapping and failed cleanup must terminate without retry recursion, leaked child processes or replacing an old output. Tasks 1, 4 and 5 own these paths.
5. Concurrent wrappers, hardlinked outputs, stale pins and interrupted publication must remain fail-closed. Task 5 owns the filesystem/parallel-process checks; Task 7 owns MCP evidence invalidation.

## File Boundaries And Interfaces

Keep `frontend.nql` and `backend.nql` as B0-compatible `fn main()` components;
do not split them into imports or helper functions that the predecessor cannot
compile. Their interface is bytes on fd 0/1 and diagnostics on fd 2, not a Python
API. The independent reference assembly documents named machine routines.

| File or group | Responsibility | Task |
| --- | --- | --- |
| `bootstrap/compiler/b0/compiler.nql0`, `x86_64-linux/b0.reference.asm`, `README.md` | machine-authored explicit compiler profile, independent reference and contract | 1 |
| `tests/bootstrap/fixtures/c031/predecessor/` | immutable B0.7r/C0.30 source and hash evidence | 1 |
| `tests/bootstrap/c031_support.py`, `test_c031_support.py` | candidate invocation, predecessor reconstruction and wire-format test oracle | 1 |
| `tests/bootstrap/c031_debugger.py`, `test_c031_debugger.py` | test-only bounded QEMU debugger and syscall fault/register evidence | 1 |
| `tests/bootstrap/test_b0_compiler_profile.py` | B0 profile positive, negative and default-parity tests | 1 |
| `bootstrap/compiler/c0/frontend.nql`, `FRONTEND.md` | wide syntax/storage and NQSC/NQAF serialization | 2 |
| `tests/bootstrap/test_c0_capacity_frontend.py` | frontend capacity/transport tests | 2 |
| `bootstrap/compiler/c0/backend.nql`, `BACKEND.md` | versioned validation, native slots, wide offsets/diagnostics | 3 |
| `tests/bootstrap/test_c0_capacity_backend.py` | malformed wide IR, semantic and native-output checks | 3 |
| `bootstrap/compiler/c0/backend.nql`, `RUNTIME_IO.md` | explicit mapped-runtime code generation and cleanup | 4 |
| `tests/bootstrap/test_c0_compiler_profile.py` | C0 runtime profile and fault tests | 4 |
| `bootstrap/compiler/c0/x86_64-linux/compile-source.sh` | non-semantic framing and atomic executable publication | 5 |
| `tests/bootstrap/test_c0_capacity_pipeline.py` | wrapper/materializer isolation, failure and concurrency | 5 |
| `tests/bootstrap/test_c0_component_generations.py`, `c0_capacity.sh` | actual compiler workload, deterministic A/B/C evidence and gate | 6 |
| B0/C0 pins, `bootstrap/manifest.tsv`, suite runners, MCP and authority docs | coherent promotion after candidate verification | 7 |

C0 materializers and existing test gates change alongside their owning component
in Tasks 2/3. Task 5 checks their publication behavior; it must not be the first
time a wide component is built with `--compiler-profile`.

Common **test-only** API in `c031_support.py`:

```python
def run_native(binary: Path, data: bytes = b"", *, args: tuple[str, ...] = (),
               timeout: float = 15.0, **kwargs) -> subprocess.CompletedProcess[bytes]: ...
def build_predecessors(destination: Path) -> dict[str, Path]: ...
def decode_nqaf(data: bytes) -> tuple[dict[str, int | bytes], list[tuple[int, ...]]]: ...
def encode_profile_source(source: bytes) -> bytes: ...
```

`build_predecessors` returns keys `b0`, `frontend`, `backend`, reconstructs B0
with pinned Stage0 and C0.30 with that B0, and verifies source/artifact hashes.
`decode_nqaf` returns header fields `version`, `source_length`, `node_count`,
`root_id`, `token_count`, `dialect`, `runtime_profile`, `source`; nodes normalize
to `(kind, flags, offset, length, left, right, next)`. It checks reserved bytes
and exact framing; graph assertions use iterative traversal, not Python recursion.
`encode_profile_source` returns exactly `b'NQSC\x01\x01' + bytes(10) + source`.

Tests select candidates using `B0_COMPILER`, `C0_FRONTEND`, `C0_BACKEND`; unset
means the corresponding pinned path. A set-but-invalid path must fail, never
fall back. Adapt `test_c0_frontend.py` and `test_c0_backend.py` to accept these
variables while retaining their current positional binary override. Other C0
suites already support these names. No production environment pin bypass.

## Execution And Evidence Rules

Before any code edit, capture a full baseline in the execution workspace with
exit receipts: `make -k test`, `.venv-mcp/bin/python -m unittest discover -s tests/mcp -v`,
`make release-check`. Check all seven seed pins and copy the starting hash ledger.
The previous documentation-only session's 1,082 PASS log and 37 MCP tests are
historical evidence, not a fresh post-implementation result. Its combined shell
exit receipt was lost; do not invent one.

Keep candidate binaries and logs under a unique `C031_WORK` from `mktemp -d`;
use `CAND="$C031_WORK/candidates"`. Record stdout, stderr, command, exit status,
source hashes and artifact hashes separately. `run_native` drains both streams
and bounds each process; large boundary cases use an explicit 120-second limit,
generation builds 1,200 seconds. A timeout is a failure requiring diagnosis.

After each feature task, run the complete existing regression gates in a separate
validation copy with that task's candidate sources, seeds and provisional hash
files installed as one consistent set. Provisional pins are test inputs, not
promotion. This is necessary because existing materializer gates intentionally
reject stale pins. Never weaken those gates or call their expected rejection a
compiler regression. The authoritative seed set stays untouched until Task 7.

Source snapshots and test fixtures are bytes, not a new compiler. Only the pinned
Stage0 and the selected B0/C0 executables produce candidate machine artifacts.
Reference NASM/ELF inspection belongs to an explicitly separate audit lane.
Take the command's status before log-processing commands can mask it.

### Task 1: Explicit B0 Compiler Profile

**Files:** B0 and shared test files listed above; existing `tests/bootstrap/bootstrap_compiler_b0.sh` for candidate validation. Do not promote `b0.seed`/`b0.sha256` yet.

**Interfaces:** Consumes Stage0 and B0.7r source semantics. Produces `$CAND/b0.seed` accepting `--compiler-profile` and the common test API. Generated programs expose checked 16 MiB byte memory with cleanup; default B0 outputs retain their previous bytes.

- [x] **Step 1: Preserve predecessor evidence and add the first RED tests.**
  Copy `compiler.nql0`, `frontend.nql`, `backend.nql` into the predecessor fixture
  directory as `b0.nql0`, `frontend.nql`, `backend.nql`; add a JSON hash ledger
  `hashes.json` with `sources` keyed by those three filenames and `artifacts`
  keyed by `b0.seed`, `c0-frontend.seed`, `c0-backend.seed`. Values are SHA-256
  strings. Source hashes must match the spec; the B0 machine-source hash is
  `4c115dfa566f1368d2a35371163709af4d5802ab6c2bfa488f685a982493ef8c`.
  Add `B0ProfileTests.test_profile_byte_above_legacy_bound` with these assertions:

  ```python
  source = b"fn main(){byte_store(65536,42);return byte_load(65536)}"
  result, output = self.compile_b0(source, profile=True)
  self.assertEqual((result.returncode, result.stderr), (0, b""))
  self.assertEqual(run_native(output).returncode, 42)
  self.assertNotEqual(self.compile_b0(source, profile=False)[0].returncode, 0)
  ```

  Define `compile_b0(self, source: bytes, *, profile: bool) ->
  tuple[subprocess.CompletedProcess[bytes], Path]` using `run_native`, a temporary
  `.nql` file and `-o output`; return the process and its temporary output path.
  Shared helper tests must first prove exact 16/32-byte header handling,
  corrupt snapshot rejection and set-but-missing candidate-path rejection.
  Implement the minimal test plumbing before the compiler RED run below so a
  missing helper/import cannot masquerade as the intended unsupported feature.
- [x] **Step 2: Observe RED on pinned B0.** Run
  `python3 tests/bootstrap/test_b0_compiler_profile.py B0ProfileTests.test_profile_byte_above_legacy_bound`.
  Expect unsupported CLI/profile, not a missing import or broken fixture.
- [x] **Step 3: Implement the machine-authored profile.** Update B0 `_start`
  argument handling, compile-time range selection, generated prologue/access/
  stream/exit templates and error finalization in canonical `.nql0`, with the
  corresponding independently maintained reference. Preserve `source -o out`;
  accept the profile before input, after input or after the output pair, never
  between `-o` and its operand. Reject duplicate profile and use with lex/parse.
  Keep fast literal/write compilation working in the profile, with any acquired
  mapping routed through the same single cleanup path. Default templates stay
  byte-identical. Generated private mapping state must not consume user locals.
- [x] **Step 4: Add resource/ABI and compatibility tests, then implement only
  missing profile behavior.** `test_profile_bounds_and_zero_initialization`
  checks 65,535, 65,536, 16,777,215, 16,777,216 and negative/dynamic indices;
  `test_profile_stream_retry_and_cleanup` checks read EINTR, short writes,
  bad FDs, mapping/unmapping failure, preserved return status and broken stderr.
  `test_default_fixture_bytes_match_b07r` compares bytes/status/streams for all
  existing B0 fixtures against `build_predecessors`, including invalid inputs.
  Validate legacy B0 range/return semantics separately from C0 semantics.
- [x] **Step 5: Make fault evidence repeatable.** Extract the inspected QEMU
  debugger approach from the retained C0.30 review into `c031_debugger.py` as a
  bounded context-managed `Guest(binary: Path, data: bytes = b"")`. Expose
  `regs()`, `setregs(**values)`, `bp(address, enabled=True)`, `until(address)`,
  `inject(result)`, `short_write(count)`, `finish()`, `close()`. Use generated
  template/disassembly offsets, not old C0.30 hardcoded addresses. Verify
  instruction bytes at each injection site; never patch/promote artifact bytes.
  `test_c031_debugger.py` must reject EOF, bad packets, startup/port collisions
  and timeout without hanging, and reap every child/close every socket. A
  missing debugger execution capability blocks this evidence, not a fake PASS.
- [x] **Step 6: Verify GREEN and independent reference parity.** Reconstruct
  the candidate with Stage0 into temporary output, twice; compare bytes and
  inspect ELF. Run `B0_COMPILER="$CAND/b0.seed" python3 -m unittest discover -s tests/bootstrap -p 'test_b0_compiler_profile.py' -v`,
  plus `test_c031_support.py`, `test_c031_debugger.py`, and the complete baseline
  in the provisional validation copy. Review spec compliance, then code quality,
  and checkpoint actual results. No authoritative pin or commit yet.

### Task 2: Wide Frontend And Profile Transport

**Files:** `bootstrap/compiler/c0/frontend.nql`, `FRONTEND.md`, `x86_64-linux/materialize-frontend.sh`; `tests/bootstrap/c0_frontend.sh`, `test_c0_frontend.py`, `test_c0_capacity_frontend.py`, shared oracle.

**Interfaces:** Consumes Task 1 B0 profile and raw source or NQSC/1 stdin. Produces `$CAND/c0-frontend.seed`; old-size plain input emits exact NQAF/1..4, larger input or explicit profile emits NQAF/5. No backend dependency for syntax tests.

- [x] **Step 1: Add RED transport/capacity assertions.**

  ```python
  source = b"fn main(){return 7}".ljust(8193, b" ")
  result = run_native(frontend, source)
  self.assertEqual((result.returncode, result.stderr), (0, b""))
  header, nodes = decode_nqaf(result.stdout)
  self.assertEqual((header["version"], header["source_length"],
                    header["runtime_profile"]), (5, 8193, 0))
  self.assertEqual(header["source"], source)
  ```

  Name it `CapacityFrontendTests.test_source_crosses_legacy_limit`. Add
  `test_explicit_profile_forces_v5` expecting profile 1 for a small source.
- [x] **Step 2: Run the two tests against C0.30.**
  `python3 tests/bootstrap/test_c0_capacity_frontend.py CapacityFrontendTests.test_source_crosses_legacy_limit CapacityFrontendTests.test_explicit_profile_forces_v5`.
  Expect C0P-002/raw-header rejection; record RED before source edits.
- [x] **Step 3: Widen the complete frontend state.** In `fn main()`, migrate
  input/lookahead, token records, AST, operator/operand/call/block stacks and
  inactive writes to the spec's regions. Decode/store u32 values through all
  scratch state, retaining B0's 16-local grammar. Parse NQSC before source,
  exclude the header from coordinates and size, and serialize legacy records
  only after determining that all old bounds hold. Make the frontend materializer
  and its gate build with B0 `--compiler-profile`; preserve their hash checks.
- [x] **Step 4: Add independent boundary and malformed-input tests.** Cover
  source 262,144/262,145; token 65,536/65,537; high spans and identifier lengths
  65,535/65,536; exact AST count/storage limits using the oracle, without calling
  lexer counts AST counts. Test NQSC prefix lengths 0..15, unknown/zero profile,
  flags, reserved bytes, nested magic, and byte-at-a-time header/payload reads.
  Use C0P-013 for malformed envelopes; retain the existing C0P-010 trailing-source
  diagnostic (the design's code allocation was corrected before implementation).
  `test_fragmented_profile_header_keeps_source_offsets` checks source-relative
  locations; `test_waits_for_eof_after_valid_prefix` must observe no output before
  EOF. Feed and drain concurrently so large-output tests cannot deadlock.
- [x] **Step 5: Preserve old coverage without preserving obsolete limits.**
  Run the frozen C0.30 source limits against the predecessor. For candidates,
  old over-limit syntax becomes /5 positive tests and new one-over bounds become
  negatives. Keep every legacy grammar/encoding/malformed case and exact /1..4
  AST fingerprint; use iterative ownership/physical-chain assertions.
- [x] **Step 6: Verify GREEN.** Run
  `C0_FRONTEND="$CAND/c0-frontend.seed" python3 tests/bootstrap/test_c0_capacity_frontend.py -v`,
  the existing frontend/control/function/runtime syntax suites, double B0 build,
  and full provisional regression gates. Require both actual component sources
  to produce syntax-valid /5 AST here, not yet executable components. Complete
  separate spec and quality reviews; checkpoint, no authoritative promotion.

### Task 3: Wide Backend, Native Slots And Locations

**Files:** `bootstrap/compiler/c0/backend.nql`, `BACKEND.md`, `x86_64-linux/materialize-backend.sh`; `tests/bootstrap/c0_backend.sh`, `test_c0_backend.py`, `test_c0_capacity_backend.py`, shared wire oracle.

**Interfaces:** Consumes Task 2 NQAF/5 and legacy formats; produces `$CAND/c0-backend.seed` emitting profile-0 ELF for valid wide inputs. Profile-1 runtime emission belongs to Task 4 and is not claimed as completed here.

- [x] **Step 1: Add and run RED `CapacityBackendTests.test_wide_source_executes`.**
  Compile the 8,193-byte Task 2 source and assert ELF magic, then
  `(exit_code, stdout, stderr) == (7, b'', b'')`. Run
  `python3 tests/bootstrap/test_c0_capacity_backend.py CapacityBackendTests.test_wide_source_executes`
  with `C0_FRONTEND` set to the candidate and backend still C0.30. Expect old
  version/framing rejection, not a source failure.
- [x] **Step 2: Implement versioned validation and storage.** Read header size
  before derived accesses; expose one internal record view with version-specific
  stride/field offsets. Apply the spec's backend regions and dialect rules,
  single ownership, exact statement chain, postorder and anchor validation.
  Keep old-format caps. Use `<4sBBHIIIIBBHI` and `<BBHIIIIIII` in the test oracle
  only; each is exactly 32 bytes. Zero/reserved fields stay independently checked.
- [x] **Step 3: Implement wide semantic/native state.** Build the function-entry
  index, distinguish intrinsic targets from all user IDs, resolve lexical names,
  assign per-function permanent slots and per-statement/condition temporaries.
  Count permanent slots before temporaries, but expose each binding only after
  its initializer. Keep all parent/call-argument values live until consumed.
  Preserve /1..4 node-ID slots and old ELF layout. Widen code/prefix/fixup offsets,
  add a line-start index and full decimal coordinates; check every write/patch.
  The backend materializer/gate now use the explicit B0 profile.
- [x] **Step 4: Test independent rejection boundaries.** Add
  `test_wide_header_and_graph_mutations`: invalid dialect/profile/reserved/count,
  short/trailing streams, wrapping spans, duplicate owners/cycles and moved
  physical links all return 1 with empty output. Exercise node 65,536 and node
  cap + 1 with constructed ASTs independently of lexer limits; a later native
  slot error must not be misreported as invalid IR. Maximal parser and maximal
  native-output fixtures are separate contracts.
- [x] **Step 5: Test runtime and scaling correctness.** Add
  `test_high_global_ids_use_local_frames`, `test_frame_slots_exact_and_overflow`,
  `test_live_nested_call_arguments`, `test_intrinsic_ids_do_not_alias_user_nodes`,
  `test_runtime_location_above_four_digits`, `test_wide_code_and_rel32_bounds`.
  Assert exact values, preserved argument order, located C0B-007 with empty ELF
  on frame overflow, unchanged depth 64/65, and genuine backwards loop fixups.
  Name lookup must distinguish long exact lexemes and user builtin shadows.
- [x] **Step 6: Verify GREEN and parity.** Run
  `python3 tests/bootstrap/test_c0_capacity_backend.py -v` with both candidate
  environment paths, then all existing backend/control/function/runtime suites,
  predecessor AST/ELF byte comparisons, double builds and full provisional gates.
  Review validation/ABI contracts separately from implementation quality before
  starting mapped profile codegen. Do not publish a profile-1 capability yet.

### Task 4: C0 Mapped Compiler Runtime

**Files:** `bootstrap/compiler/c0/backend.nql`, `RUNTIME_IO.md`, the intermediate-profile paragraph in `BACKEND.md`; `tests/bootstrap/test_c0_compiler_profile.py`, the temporary Task-3-only unsupported-profile methods in `test_c0_backend.py` and `test_c0_capacity_backend.py`, shared debugger tests. Retain all other legacy assertions.

**Interfaces:** Consumes fully validated /5 header `runtime_profile`; produces checked profile-1 executables usable as the next compiler generation. Profile 0 retains 64 KiB, regardless of source size.

- [x] **Step 1: Add and run RED `CompilerProfileTests.test_profile_byte_above_legacy_bound`.**
  Feed the Task 1 byte-store source through NQSC into the candidate frontend,
  compile and execute. Assert exit 42, empty stderr; the unprofiled source must
  instead fail at runtime with C0R-004/70. Run the named test before changing
  the backend templates and record the actual failure.
- [x] **Step 2: Implement profile-specific startup and cleanup templates.** Map
  16 MiB RW/NX only when intrinsic resolution requires it; preserve runtime base,
  SysV alignment, callee-saves and return status. Every acquired mapping reaches
  unmap once on normal or error exits. Cleanup failures use arena-independent
  C0R-007 at input:1:1 and exit 74. A failed stderr write cleans up without
  recursion. Default helpers and predecessor output must not be rewritten.
- [x] **Step 3: Add and satisfy failure/ownership tests.**
  `test_large_default_source_keeps_64k` pads source over 8 KiB and proves /5
  profile 0 still rejects offset 65,536. `test_user_shadow_does_not_map_arena`
  proves exact user-first resolution, even on wrong arity. Cover zero-initialized
  high memory, full/empty ranges, negative/overflow indices, short read/EOF,
  retry EINTR, partial writes, failed diagnostic prefix/suffix, mmap/munmap faults,
  arithmetic/depth errors after acquisition and callee-saved registers. Use the
  Task 1 debugger to count actual acquired/released mappings and assert cleanup
  on broken stderr; record injection rather than claiming natural kernel signals.
- [x] **Step 4: Verify GREEN.** Run
  `python3 tests/bootstrap/test_c0_compiler_profile.py -v` with candidate paths,
  the wide/default backend suites and complete provisional regression gates.
  Inspect no interpreter/dynamic libraries and non-executable stack/mapping.
  Obtain separate spec and code-quality reviews, including all exit branches;
  retain source/artifact hashes with the runtime evidence.

### Task 5: Profile-Aware Atomic Source Pipeline

**Files:** `bootstrap/compiler/c0/x86_64-linux/compile-source.sh`, both C0 materializers; `tests/bootstrap/test_c0_capacity_pipeline.py`.

**Interfaces:** `compile-source.sh [--compiler-profile] input.nql output` preserves raw mode and prepends only the exact NQSC header in profile mode. Compiler seeds/manifests remain resolved relative to the script, not cwd or test environment variables.

- [x] **Step 1: Add and run RED `CapacityPipelineTests.test_profile_wrapper_from_unrelated_cwd`.**
  In a temporary installation containing candidate scripts/seeds/manifests, invoke
  the new profile form from a different directory with spaced paths. Assert the
  high-byte fixture exits 42. Run
  `python3 tests/bootstrap/test_c0_capacity_pipeline.py CapacityPipelineTests.test_profile_wrapper_from_unrelated_cwd`.
  Expect the old wrapper's usage error before editing it.
- [x] **Step 2: Implement framing and publication.** Parse the optional leading
  profile flag, validate inputs/outputs as before, and frame with `printf` plus
  byte copying only. Check both producer and frontend exit statuses. Preserve
  unique TMPDIR workspace, candidate output beside its destination, protected
  path/hardlink checks and pin verification. Remove AST/workspace before final
  rename; failed compilation/cleanup deletes the candidate and preserves the old
  output. Publication commits the new file; a later signal is not rollback.
- [x] **Step 3: Add and satisfy negative/concurrency tests.** Cover unknown and
  duplicate flags; missing/unreadable source; non-directory output parent;
  output aliasing input, seed, manifest and script via hardlinks/symlinks;
  stale/missing pins; framing failure; semantic failure; stdout write and
  intermediate cleanup failure. Assert old output bytes/mode unchanged, no
  surviving owned temporary files, and appropriate nonzero status. Two concurrent
  builds must use disjoint intermediates and produce a complete valid final file.
  HUP/INT/TERM tests record 129/130/143 and reap subprocesses, not just the shell.
- [x] **Step 4: Verify GREEN.** Run the full pipeline test module, existing
  materializer atomicity/concurrency tests and full provisional regression gates.
  Review the non-semantic transport boundary separately from filesystem/process
  correctness. No new public nqlc mode or environment pin override is introduced.

### Task 6: Actual Compiler Workload And Component Generations

**Files:** `tests/bootstrap/test_c0_component_generations.py`, `tests/bootstrap/c0_capacity.sh`, `bootstrap/compiler/c0/CAPACITY.md`.

**Interfaces:** Consumes candidate B0/frontend/backend plus exact current component sources. Produces test evidence for A -> B -> C, never a Full Compiler flag. Shell gate prints `PASS c0-capacity` and `PASS c0-component-generations` only after the corresponding subprocesses exit 0.

- [x] **Step 1: Add the generation test and establish predecessor RED.**
  `ComponentGenerationTests.test_actual_sources_build_and_rebuild` must compile
  both complete current sources using frontend/backend executables selected by
  environment, with explicit profile framing. On C0.30 it fails C0P-002 before
  producing an artifact. Do not reduce the source or replace it with a toy fixture.
- [x] **Step 2: Implement test-only generation orchestration.** Build each
  component twice with candidate B0 profile to obtain A and compare exact bytes.
  A frontend/backend compile both sources to B; B compile the same source bytes
  to C. Require B/C byte equality and real execution of both resulting components
  on legacy, wide, malformed and runtime corpora. Assert status/stdout/stderr and
  artifact hashes separately, retaining the first differing offset on divergence.
  Helpers only launch stages/read artifacts; they never synthesize compiler code.
- [x] **Step 3: Make evidence corruption fail.** Test truncated/mutated generation
  artifacts and nonzero producer status with nonempty stdout; these must fail
  verification rather than compare normalized/partial output. No persistent
  success cache: receipts bind all source, seed and test identities for that run.
  Temporary copies, children and debugger sockets close on all failed paths.
- [x] **Step 4: Run GREEN and characterize remaining limits honestly.** Run
  `python3 tests/bootstrap/test_c0_component_generations.py -v` and
  `ROOT_DIR="$PWD" bash tests/bootstrap/c0_capacity.sh` in the candidate validation
  copy. Actual compiler-source failure returns to the owning earlier task; no
  host fallback or automatic capacity escalation. Document real sizes/hashes,
  commands, statuses, resource evidence and any remaining blocker in CAPACITY.md.
- [x] **Step 5: Review then regress.** Independent spec and code-quality reviews
  check provenance and evidence consumption, not just equality assertions. Run
  the full provisional regression/MCP/release gates before preparing promotion.

### Task 7: Coherent Integration, Pins And Truthful MCP Status

**Files:** `bootstrap/compiler/b0/x86_64-linux/{b0.seed,b0.sha256,materialize.sh}`;
`bootstrap/compiler/c0/x86_64-linux/c0-{frontend,backend}.{seed,sha256}`;
`bootstrap/manifest.tsv`, `tests/bootstrap/{run_tests.sh,README.md}`;
`tools/nolqu_mcp.py`, `tests/mcp/test_nolqu_mcp.py`;
`bootstrap/compiler/{b0,c0}/README.md`, C0 contract docs, CAPACITY.md and the revised authority.

**Interfaces:** Existing canonical MCP tool names/signatures stay intact. Add evidence-backed capacity/profile/component-generation fields to existing probe results; retain `full_compiler_verified=False`, `self_hosting_verified=False`, and later stage statuses `NOT_IMPLEMENTED`.

- [x] **Step 1: Add and run MCP RED assertions.** Existing frontend/backend
  probe tests must now expect source/token/node capacities 262144/65536/65536,
  /5 support, default byte capacity 65536 and compiler-profile capacity 16777216.
  Add `test_c031_capacity_evidence_fails_closed` and
  `test_c031_generation_evidence_does_not_promote_full_compiler`. Missing gate,
  corrupt seed, changed source identity, nonzero exit or timeout must leave new
  verification booleans false. Matching filenames/version comments alone prove
  no capability. Before changing MCP implementation, run
  `env PYTHONPATH=tests/mcp .venv-mcp/bin/python -m unittest -v test_nolqu_mcp.NolQuMcpCoreTests.test_c031_capacity_evidence_fails_closed test_nolqu_mcp.NolQuMcpCoreTests.test_c031_generation_evidence_does_not_promote_full_compiler`.
- [x] **Step 2: Integrate gates and evidence.** Include `c0_capacity.sh` in the
  bootstrap runner without deleting a prior gate. Existing materializers retain
  pinned verification. Extend current probes to execute and inspect the relevant
  real gates; include separate `capacity_verified`, `compiler_profile_verified`,
  `component_generation_verified` and actual source/artifact identities. Update
  history with the next measured blocker, not a guessed completed stage. Label
  component versions C0.31 while retaining the C0.25 emitter distinction.
- [x] **Step 3: Verify MCP GREEN and the complete candidate set before promotion.**
  Rerun the two RED tests, expecting PASS with truthful failure-state assertions.
  In the provisional validation tree, run `make -k test`, configured full MCP
  unittest discovery, `make release-check`, all bootstrap hashes and the combined
  canonical probe. Preserve logs and exact exit receipts; fail on any missing
  expected gate or newly skipped test. Initialization/resource/tool discovery
  from an unrelated cwd must still pass with all existing tools present.
- [x] **Step 4: Complete whole-change review, then promote only the verified set.**
  Review machine provenance, memory maps, cleanup, serialization, frame lifetime,
  fixups, tests and documentation. Resolve actionable findings and rerun their
  affected gates. Only then update the B0/frontend/backend seeds and hash files
  from the reviewed candidates together with profile-aware sources/materializers.
  No pin is calculated from an unreviewed host-built reference artifact. Keep
  predecessor sources/hash evidence and record rollback for the complete set.
- [x] **Step 5: Rerun the exact final gates after promotion.** All commands in
  Step 3 must pass against promoted bytes, with documented additional gate count
  rather than a hardcoded expected total. Reconnect MCP or run a fresh process;
  old loaded server code is not proof of the new behavior. Update authority and
  CAPACITY.md with actual results; mark tasks done only from receipts. Stop with
  uncommitted changes and the next measured blocker. No merge/push/release.

## Plan Review And Handoff

Coverage: spec predecessor bridge -> Task 1; transport/storage/AST -> Task 2;
validation/slots/structural scaling -> Task 3; mapped runtime -> Task 4;
publication -> Task 5; actual workload/generations -> Task 6; compatibility,
review, regression, MCP and coherent promotion -> Task 7. The five Review Focus
conditions have named owning tests above. Full Compiler remains outside scope.

Self-review checks interface names against current files, candidate/materializer
ordering, immutable predecessor evidence, review gates and rollback scope. The
plan does not introduce hidden host compilation, discard negative IR coverage,
claim future test results, or authorize commits on the dirty main checkout.

Recommended execution: subagent-driven, sequential tasks with fresh spec and
quality reviewers, because the predecessor/profile/AST/ABI interfaces are tightly
coupled and a mistake can invalidate bootstrap evidence. Native execution is
also possible with the same test and independent review gates. Review this plan
and select the execution method before product changes begin.
