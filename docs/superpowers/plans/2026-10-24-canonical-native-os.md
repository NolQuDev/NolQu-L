# Canonical Native OS Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile and run an actual NolQu-L native file reader using process arguments and raw Linux syscalls, preserving canonical bootstrap and legacy behavior.

**Architecture:** Add contextual unsafe scopes and four bounded experimental intrinsics to the existing source frontend and independently validating direct-ELF backend. Keep compiler sources in the flat sixteen-local B0 language. Validate the complete capability, then promote the coherent source/seed/pin/proof set into the existing isolated worktree.

**Tech Stack:** NolQu-L/B0, indexed NQAF, direct x86_64 Linux ELF/syscalls; Python only for test oracles/MCP, shell only for existing orchestration, QEMU for actual guest execution on this aarch64 host.

**Spec:** `docs/superpowers/specs/2026-10-24-canonical-native-os-design.md`

## Global Constraints

- Public VERSION/CHANNEL remain 1.0.2a1/dev. C0.32 is an experimental capability designation, not a public release.
- Original `/home/Axelly/Downloads/NolquASM` is read-only. Existing detached worktree `/home/Axelly/.codex/worktrees/4878/NolquASM` is retained; no new worktree, commit, push, merge, publish or evidence deletion.
- Implementation root is `/tmp/nql-next-compiler-v7wdgsfr/candidate`; evidence root is `/tmp/nql-next-compiler-v7wdgsfr`. Parent controls promotion and rollback snapshots. Do not mutate worktree compiler files before candidate acceptance.
- Compiler sources remain one flat B0-compatible `fn main()` with sixteen locals; source262144/token65536/node65536/control64/call64/frame4096 bounds stay fixed. B0 source327680/output589824/dynamic-byte-access5376 bounds stay fixed.
- Frozen Machine, Stage0, B0, monolithic-C0 and successor sources/seeds/pins remain unchanged. Only FE/BE seeds and their matching pins may change after actual deterministic A1/A2 evidence and reviews.
- No source interpretation, rewriting, codegen or link semantics in Python, LLVM, R0, assembler, linker or host compiler. Test-only byte/wire/machine inspection is allowed.
- Four exact intrinsic interfaces: `arg_count()`; `arg_copy(index,offset,capacity)`; `byte_address(offset,count)`; `syscall6(number,frame_offset)`. User functions resolve first, even wrong arity; variables are a separate namespace.
- Unsafe/source/wire/runtime semantics, NQAF/6 dialect5/kinds45/46 and error statuses are exactly the spec. Existing NQAF/1..5 and successful old AST/ELF bytes remain compatible.
- No claim of full Safety, Full Compiler, self-hosting, native CLI/MCP migration, hardware-native x86 execution or release readiness. Existing proof flags and new `unsafe_blocks_verified`, `process_arguments_verified`, `syscall_abi_verified` stay false unless a complete fresh identity-bound proof succeeds.
- Existing MCP120 tools/8resources/5prompts and all required input/return schemas remain compatible. Preserve the previous process-boundary implementation unless evidence requires a reviewed change.
- Every task has RED/GREEN evidence, immutable before/after snapshots and separate spec/quality review. Never fabricate test counts or promote partial pins. No nested agents or model overrides.

## Review Focus

1. Forged scope markers or calls shared across owners must not grant unsafe permission; mutation tests must reject before ELF output.
2. User functions named like new intrinsics, including wrong arity and high node IDs, must retain ordinary resolution and old transport where applicable.
3. Argv containing empty/non-UTF8/spaced values must copy exact bytes including NUL without partial publication or environment traversal.
4. The kernel's fourth/sixth arguments must use r10/r9 under nested six-argument user calls and both arena profiles, with preserved callee-saved registers and aligned stacks.
5. Short I/O, EINTR, closed descriptors, missing files and profile cleanup must produce actual observable outcomes; a superficial getpid test is insufficient.

## Execution And Baseline

All four authority identities and full text are retained under `authority/`; no missing document is inferred. Read the spec plus current C0 FRONTEND/BACKEND/FUNCTIONS/RUNTIME_IO/CAPACITY before relevant edits. Reuse the just-completed access baseline only while guarded identities match: main1078, MCP112, release9, previous full-source public builds and one combined probe. Task RED runs prove the new capability is actually missing. This plan delivers one whole milestone; task boundaries are internal review gates, not separate user deliveries.

`unsafe` recognizes only identifier followed by `{` at a statement boundary. In its header, whitespace/blank lines precede the first comment; after `#` or `//`, horizontal whitespace is allowed before the exact case-sensitive `safety:` tag. Explanation must contain a non-whitespace non-comment-marker character on that line or subsequent comment lines before the first token. A tag after an unrelated first comment does not qualify. This fixes a lexical choice left to the builder without introducing `unsafe fn`.

### Task 1: Frontend Unsafe/Native Source Contract

**Files:**
- Modify: `bootstrap/compiler/c0/frontend.nql`, `tests/bootstrap/c031_support.py`.
- Create: `tests/bootstrap/test_c0_native_frontend.py`.

**Interfaces:**
- Consumes: raw source or unchanged NQSC/1; current indexed parser/statement-chain conventions.
- Produces: NQAF/6 32-byte header/records, dialect5, profile0/1, kind45 opener/kind46 close; legacy output unchanged. New parser C0P-014 and semantic C0S-001 errors emit no AST.
- New frontend test class `NativeFrontendTests` uses `C0_FRONTEND` like existing candidate-aware tests. Test-only `decode_nqaf` accepts /6 dialect5 only, retaining /5 dialect1..4 and strict reserved fields.

- [x] Write failing tests `test_unsafe_scope_and_header`, `test_native_transport_and_shadows`, `test_raw_calls_need_owning_unsafe_scope`, `test_nested_scope_limits`, `test_legacy_output_unchanged`, `test_frontend_errors_and_offsets`. Assert exact kinds/anchors/owned graph, /6 selection, all four arities through source syntax, global forward shadows, contextual identifier compatibility, no AST on malformed/missing/empty invariant or raw call outside scope.
- [x] Run these tests against the frozen installed frontend, retain RED command/streams/status under evidence `task1/`.
- [x] Implement contextual parser scopes with depth64 and bounded side metadata; document free arena intervals before writes. After parse resolve exact global function shadows, classify new calls by owning statement unsafe depth, select /6 only for actual new operations/scopes. No new public lexer keyword and no trusted expression-position shortcut.
- [x] Compile full frontend through unchanged B0 `--compiler-profile` to evidence candidate executable, run the six new tests plus existing frontend/control-flow/functions syntax tests appropriate to changed paths. Record exact source size, locals, bounds and observed A artifact hash; don't edit seed/pin yet.
- [x] Snapshot changed files and diff against baseline, write task report with RED/GREEN and self-review, obtain separate spec/quality review. No commit.

### Task 2: Independently Validating Backend And Native ABI

**Files:**
- Modify: `bootstrap/compiler/c0/backend.nql`.
- Create: `tests/bootstrap/test_c0_native_backend.py`, `tests/bootstrap/test_c0_native_runtime.py`, `tests/bootstrap/c032_support.py`, `tests/bootstrap/fixtures/c032/predecessor/{frontend.nql,backend.nql,hashes.json}`.
- Modify: `tests/bootstrap/test_c0_native_frontend.py` only to replace the soon-to-be-promoted installed comparison baseline with the frozen C0.31 reference.

**Interfaces:**
- Consumes: Task1 frozen FE candidate and NQAF/6 grammar, /1..5 compatibility, spec raw frame48 ABI.
- Produces: real standalone ELF; new raw intrinsic tags distinct from user node IDs, conditional argv capture/runtime helpers; C0B-010/1 for raw permission; C0R-008/70 index and C0R-009/74 copy capacity; existing C0R-004/70 range (including arg_copy capacity <= 0).
- Candidate-aware test classes `NativeBackendTests`, `NativeRuntimeTests` use `C0_FRONTEND`, `C0_BACKEND`; actual `run_native`/`Guest`, no synthetic pass claims.

- [x] Freeze the exact old C0.31 sources from `task1-before/files/bootstrap/compiler/c0/frontend.nql` and `task2-before/files/bootstrap/compiler/c0/backend.nql` into the new predecessor fixtures, plus observed source/artifact/B0 hashes. Implement test-only `build_c031_predecessors(destination)` in `c032_support.py` to validate the strict fixture ledger and frozen B0 identity, rebuild both old components via unchanged B0 `--compiler-profile`, verify old artifacts exactly, and atomically publish into an empty owned destination. Keep old c031/B0.7r/C0.30 fixtures untouched. Add `test_frozen_c031_baseline_is_independent` checking actual old artifact hashes and changed fixture rejection before execution, and `test_frozen_c031_byte_parity` comparing complete old/new AST/ELF bytes across representative legacy dialects, shadows, unsafe condition variables, wide offsets and both profiles. Wire native frontend/backend legacy parity to this independent baseline, not `INSTALLED`, so promotion cannot turn comparisons into self-comparisons. Retain both profiles and wide legacy corpus. Include helper/fixtures in Task3/4 generation/proof input identities.
- [x] Write RED tests `test_wire_scope_ownership_mutations`, `test_legacy_versions_cannot_enable_native_ops`, `test_source_header_is_independently_validated`, `test_shadow_resolution_and_arity`, `test_argv_exact_bytes_and_bounds`, `test_raw_errors_and_frame_range`, `test_six_register_file_mmap`, `test_callee_saved_and_alignment`, `test_arena_profiles_and_cleanup`, `test_raw_io_progress`. Verify old backend rejects actual new wire and cannot produce expected native output.
- [x] Validate /6 fields, kind45/46 anchors/source invariant/topology/scopes before code emission; reject /7, /5dialect5, crossed functions/scopes, skipped/shared/aliased statements/expressions, forged source header and illegal reserved fields. For /6 only, independently scan actual matching source braces ignoring line comments, require kind46 to anchor that brace, and require raw call anchors inside a real owning unsafe interval; test a genuine closing record moved after a source-outside raw call. Permission derives from actual owning traversal, never physical expression location or producer flag.
- [x] Implement four new intrinsics using unused documented wide helper interval; preserve successful legacy ELF bytes. Capture kernel rsp in r12 only when argv needed; retain r15 depth, rbx arena, r14 mapped ownership and callee-saved/16-byte ABI. Keep arg_count alone arena-free, checked spans before pointer formation/kernel access, argument scan before any copy, raw syscall rax return and explicit r10/r9.
- [x] Build backend through B0 profile; run new backend/runtime tests plus old backend/control-flow/functions/runtime/profile/capacity suites with Task1 FE and new BE. Actual six-word file-backed mmap offset65536/write/munmap/close, ENOSYS/EBADF, zero-length real syscall, invalid frame before kernel, binary/spaced/empty/non-UTF8 args, nested six-arg calls and both profiles must pass. Guest debugger/disassembly validates registers, stack, callee-save and real instruction path; no claimed hardware execution.
- [x] In `test_six_register_file_mmap`, when test-only `C032_NATIVE_EVIDENCE_DIR` is set, retain `mmap-profile0.json` and `mmap-profile1.json` with actual pre/post syscall registers, syscall RIP, before/after expected file bytes, outcomes and source/wire/ELF fingerprints, plus matching `.nql`, `.nqaf`, `.elf` artifacts (modes preserved). No stdout noise or fabricated organic EINTR claim. Generation oracle runs will set a fresh owned directory; Task4 independently consumes this evidence.
- [x] Retain machine/wire/source artifacts, diff/report, source-size/local/bounds checks and separate spec/quality review. Keep seeds/pins unchanged until Task3.

### Task 3: Native Utility, Coherent Bootstrap And Public Integration

**Files:**
- Create: `examples/canonical/native_cat.nql`, `tests/bootstrap/test_c0_native_program.py`, `tests/bootstrap/c0_native_os.sh`.
- Modify: `tests/bootstrap/test_c0_component_generations.py`, `tests/bootstrap/c0_backend.sh`, `tests/bootstrap/c031_debugger.py`, `Makefile`, `tests/compiler/test_canonical_cli.py`, `tests/compiler/test_canonical_project.py`, `bootstrap/compiler/c0/x86_64-linux/c0-{frontend,backend}.{seed,sha256}`.

**Interfaces:**
- Consumes: reviewed FE/BE source/candidate binaries; raw OS contract from Tasks1/2.
- Produces: actual file/stdin utility, integrated canonical CLI/project/install tests, coherent observed FE/BE seed/pin pairs; generation receipt extended with native direct checks and named independent selectors.

- [x] Write RED public/native utility tests before implementation. No files copies stdin; multiple literal filenames copy in order; `-` is stdin; initial `--` terminates option interpretation; paths/spaces/non-UTF8 and binary data survive; missing/unreadable/closed output errors nonzero; acquired descriptors close on recoverable errors. Add focused short-write/EINTR guest tests to pin caller loops rather than relying on unobserved host timing.
- [x] Implement actual source utility with explicit unsafe invariants, openat/read/write/close, caller EINTR/partial write loops, no source rewriting or installed extra tool names. Use only existing source grammar plus new scopes/intrinsics, no placeholder.
- [x] Rebuild both full components twice via unchanged B0 and require A1==A2. Snapshot old seeds/pins; install only actual matching FE/BE candidate pairs into candidate tree after task reviews and proof. No foundation pin changes.
- [x] Extend actual A->B->C tests with NQAF6 parsing/permission/runtime/native utility corpus and named independent native frontend/backend/runtime tests, retain all existing selectors/goldens and B==C requirement. Set `C032_NATIVE_EVIDENCE_DIR` to a fresh B/C-owned subdirectory for each named oracle run and bind both profile machine artifacts in the receipt. Freeze new exact stage/check/oracle sets from the test definition for Task4's independent consumer; never infer success from mere process exit. Run all generation tests and retain full raw artifacts.
- [x] Integrate native suite in ordinary `make test`/canonical backend path without changing assertions or skipping old legacy tests. Public nqlc canonical check/compile/run and nql canonical project/cache profile behavior must exercise new source. Add `test_native_permission_diagnostic_preserves_output` for source C0S-001/no artifact replacement, and `test_native_invariant_edit_invalidates_cache` so a previously valid build cannot hide a removed required invariant behind a stale cached executable. Test combined and canonical-only relocated install using existing executable names/aliases, actual files and explicit QEMU invocation where needed.
- [x] Retain candidate integration diff/report, observed pins, complete A/B/C receipts and separate spec/quality review. No commit/promotion to W yet.

### Task 4: Truthful Proof, Documentation And Whole-Milestone Acceptance

**Files:**
- Modify: `tools/nolqu_mcp.py`, `tests/mcp/test_nolqu_mcp.py`, `tests/mcp/test_canonical_toolchain.py`, `bootstrap/compiler/c0/{README,FRONTEND,BACKEND,CAPACITY,RUNTIME_IO}.md`, `docs/compiler/CANONICAL_TOOLCHAIN.md`, `docs/language/{FEATURE_STATUS,KNOWN_LIMITATIONS}.md`, `docs/project/{STATE_OF_PROJECT,ROADMAP_SHORT}.md`, `README.md`, `examples/README.md`, both `NOLQU_MAJOR_DEVELOPMENT_*.md`, canonical helper descriptions only where C0.31 is represented as current.
- Create: `bootstrap/compiler/c0/NATIVE_OS.md`, `examples/canonical/README.md`.
- Parent-owned: plan ledger, reports, exact promotion/rollback manifest and final development report.

**Interfaces:**
- Consumes: Task3 frozen actual stage/check/oracle contract, new components and source IDs.
- Produces: identity-bound fail-closed six proof flags (`capacity_verified`, `compiler_profile_verified`, `component_generation_verified`, `unsafe_blocks_verified`, `process_arguments_verified`, `syscall_abi_verified`), compatible tool/resource/prompt schemas, honest current C0.32 docs.

- [x] Write RED tests rejecting partial/missing/wrong native checks or oracle selections, stale source/seed/pin identities, malformed receipt, missing machine artifacts, false subprocess success, duplicate/omitted proof stages. Existing required schemas and old proof coverage stay fixed; new optional fields are additive.
- [x] Update independent proof consumer to validate exact native additions alongside old sets, actual raw streams/artifacts and before/after IDs; memoize only within unchanged request scope. Keep all new flags false on timeout/failure/partial evidence and Full Compiler/self-hosting/Verified false. Preserve prior process-boundary functions unless a concrete reviewed need arises.
- [x] Document actual tested scope/errors/arena addresses/ABI, old-vs-current facts and authority reconciliation; retain historical C0.31 evidence/hash sections. No fabricated coverage/performance/resource saving or broad unsafe guarantees. Keep Python/LLVM legacy/orchestration limitations explicit.
- [x] Run full candidate main, MCP and release suites, no skips; compare all old baseline tests retained. Capture fresh protocol120/8/5/required schemas. Complete actual public full FE/BE source compilation, relocated install/native utility tests, one fresh combined canonical probe with all six flags and cleanup/identity evidence.
- [x] After task and complete-change reviews, parent verifies owned input guards, writes rollback copies/modes, and promotes the exact coherent owned source/seed/pin/schema/docs set to W. Run required post-promotion checks with dependency rulings for safe retained unchanged evidence; any changed runtime/proof tests get fresh runs. No main changes or push.
- [ ] Obtain independent whole-change review against immutable before/after package including untracked owned files; resolve findings with evidence. Mark COMPLETE only after all spec acceptance criteria pass, then produce the seven-category development report distinguishing implemented/tested/verified/release-ready.

## Rollback And Recovery

Evidence baseline `baseline-tree.json` seals the candidate's starting files/modes/symlinks. Each task owns a before/after snapshot; reviews use those diffs rather than the dirty HEAD-only diff. On failure retain artifacts, correct source/test defect and rerun affected checks; never erase RED/failure history or weaken assertions. Seed/pin rollback restores both full component pairs and the matching proof/schema/source set. Cross-task ABI/format issues are controller rulings recorded in the ledger, not silent contract changes. All previous completed work and evidence remain intact.

## Self-Review

Spec sections map to Tasks1 syntax/permission/wire, 2 independent validation/runtime/ABI, 3 utility/bootstrap/public integration, 4 proof/acceptance/docs. The five Review Focus classes have named tests in their owning task. No task claims whole compiler completion; no legacy removal or version increment is planned. The test decoder is test-only; it cannot emit production compiler bytes. Source/wire/runtime signatures and six proof flag names agree across tasks. All source or runtime changes remain contingent on measured frozen predecessor and generation evidence.


## Execution Closure And Security Addendum — 2026-10-25

Task1/2/3 and Task4 source/proof implementation reviews Approved; exact43-file
set integrated into the existing isolated worktree with rollback copies.
Actual final gates: main1079 PASS (1078 retained), MCP124 methods (112 retained),
release9, installed SDKcombinedproof722stages275checks16retained native artifacts.
Required protocol schemas120tools8resources5prompts preserved. No commit, push,
release or VERSION/CHANNEL change. See docs/project/C032_SESSION_REPORT.md.

The last whole-completion item remains unchecked: a frozen C030 comparison
backend received unexplained SIGKILL on an earlier full run. Independent
read-only investigation cannot attribute it from retained metadata. A later
identical-input serial pass is evidence, not a fix. Readiness remains PARTIAL
for stable/security promotion under the user's updated no-retry-as-resolution
policy. Source review approval is not withdrawn or inflated into release approval.

Supplemental host-only deterministic assurance adds real detection controls,
persistent corpus and exact expected behavior; see tests/security/README.md.
A later diagnostic audit found duplicated location separators for C0R-008/009.
The separately classified/reviewed source fix changes four emitted immediates,
with strict RED/GREEN, unchanged B0 A1/A2 and coherent backend source/seed/pin
publication. It changes neither native ABI nor CLI/selectors/proof code.
Post-repair MCP124, actual proof722/275, impacted public5, runner controls11,
four retained B/C images and assurance594 pass. Full main1079 remains the
pre-repair observation; no full-main post-repair run is claimed. The assurance
300s budget failure is retained, with measured600s configuration correction
and unchanged-case completion335.867s. Final identities and limitations are in
the session report. Overall completion/qualification remains PARTIAL while
the original SIGKILL is OPEN. Coverage-guided fuzzing, memory instrumentation
and external dependency rescan are not claimed.
