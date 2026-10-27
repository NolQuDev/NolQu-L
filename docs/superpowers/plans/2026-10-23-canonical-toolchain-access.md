# Canonical Toolchain Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Each task carries RED/GREEN evidence and independent spec/quality review; no automatic commits.

**Goal:** make verified C0.31 usable end-to-end through the public CLI, projects, installation and MCP without host compilation.
**Architecture:** opt-in `--backend canonical` uses unchanged pinned C0 components and their existing atomic wrapper; default R0 behavior remains. A small private shell helper isolates canonical orchestration from the existing R0 driver.
**Tech Stack:** Bash/coreutils and existing x86_64 ELF seeds; Linux util-linux setsid only for canonical terminal stdin execution; Python for the existing MCP server and unittest/MCP SDK verification; QEMU on this ARM64 host. Python supplies no canonical compiler/source semantics.
**Spec:** `docs/superpowers/specs/2026-10-23-canonical-toolchain-access-design.md`.

## Global Constraints

- Work only in the supplied staging root until the controller integrates after the immutable baseline completes; original main is read-only.
- Preserve VERSION `1.0.2a1`, CHANNEL `dev`, all seven bootstrap seed/pin pairs and C0 frontend/backend sources.
- Default backend remains `nasm`/R0; canonical is explicit. Preserve `nql/nqlc` executables and `nolqul/nolqulc` inward aliases, no removed names.
- Reuse existing canonical wrapper; no host compiler/assembler/linker/LLVM/Python semantics or fallback.
- Do not promote Full Compiler, self-hosting, Verified, general types/modules or Assembly-Level/Safety targets.
- No commit, branch mutation, main edit, merge, push or public release. No subagents from implementers.
- Fresh implementer per task; spec compliance and quality both need independent verdicts. Keep reports in this plan's SDD workspace and actual raw receipts in the evidence directory.

## Review Focus

1. Interrupted check/run must reap owned wrapper/runner descendants and clean temporary output (Task 1).
2. A valid program that prints or exits nonzero must be compiled/checked without execution (Tasks 1 and 4).
3. Backend/profile/tool/pin/binary changes must invalidate project cache success (Task 3).
4. Relocated canonical-only install must work when R0/NASM/linker/Python are unavailable (Task 3).
5. Missing/malformed inputs and unsupported modes must fail truthfully without touching prior output, lying about artifacts or changing bootstrap flags (Tasks 1 and 4). MCP stdin/process ownership is a separate measured Task 2 blocker.

### Task 1: Public Canonical Compiler Driver

**Files:** modify `nqlc`; create `tools/nql_c0_driver.sh`, `tests/compiler/test_canonical_cli.py`.
**Consumes:** unchanged `bootstrap/compiler/c0/x86_64-linux/compile-source.sh [--compiler-profile] input.nql output` and verified C0.31 seeds.
**Produces:** `nqlc/nolqulc --backend canonical [--compiler-profile] [--check|--run] input.nql [-o output] [-- args]`.

- [ ] Write `CanonicalCliTests.test_real_compile_and_run` using actual `fn main()` source, explicit output, native/QEMU execution and exact expected result. Run against untouched nqlc: assertion FAIL for unsupported backend, not a missing dependency.
- [ ] Implement backend parsing and private sourced helper `run_canonical_pipeline` called after common flag validation/version loading and before any R0 lookup, Python text validation, warning analysis or generic temporary allocation. Resolve helper script-relative for repository and installed layouts. It consumes parsed nqlc globals and exits with the actual compile/runtime status.
- [ ] Add real compile/check/run, source-located semantic/syntax failure, output preservation, pin tampering in an isolated copied installation, source/output alias, unsupported-option, dry-run, compiler-profile, stdin/stdout/status, response-file/path-space, signal cleanup and forbidden-host-tool tests. Check compares native ELF bytes to direct canonical wrapper and checks static/non-RWX/NX shape.
- [ ] Run the new module GREEN; run existing complete `tests/compiler/toolchain_cli.sh` and CLI layout/project methods from MCP tests. Save exact argv, return codes, raw streams and before/after owned-file identities. Self-review and return a report; independent task review follows.

### Task 2: MCP Process Boundary Repair

**Files:** modify only `_run_result` and its private process helpers in `tools/nolqu_mcp.py`; create `tests/mcp/test_process_boundary.py`.
**Consumes:** unchanged private `_run_result(cmd, timeout, cwd, env, stdin, capability, artifacts, changed_files)` interface and structured result/audit helpers.
**Produces:** isolated command stdin and bounded owned-process cleanup, without new MCP tools or public argument changes.

- [ ] Add actual RED tests demonstrating inherited protocol input and live child after timeout, with fixture cleanup even on assertion failure. Preserve explicit text/byte stdin behavior. The measured prior-state receipt is `/tmp/nql-canonical-cli-20261023.5odyvxyg/mcp-boundary-audit/receipt.json`.
- [ ] Make no-input commands receive DEVNULL; explicit input remains a pipe. Replace direct-child-only timeout handling with bounded cleanup of the owned command/process tree, including nested process groups used by canonical shell wrappers. Reap the direct child and retain existing timeout/error/status/output-limiter/audit behavior. Handle exception paths without swallowing interruption. Use Python standard-library orchestration only, no new runtime dependency or compiler semantics.
- [ ] Cover ordinary success/nonzero/OS errors, explicit input, child/grandchild groups, TERM-resistant children, interruption cleanup, retained partial output/clear timeout diagnosis as appropriate, and an unrelated process that must remain alive. Tests must isolate/properly clean their own children and must not pollute the MCP server's process-global child ownership.
- [ ] Run the new module GREEN then all original MCP tests from a fresh process. Keep all46 old selectors, eight resources, five prompts and120 tool names. Freeze this task's MCP bytes/test and raw evidence. Independent spec/quality review is required before dependent MCP feature work; no CLI/project/installer/authority edits from this worker.

### Task 3: Canonical Project Workflow And Relocatable Installation

**Files:** modify `nql`, `install.sh`; create `tests/compiler/test_canonical_project.py`.
**Consumes:** Task 1 CLI contract; all its files are read-only to this worker.
**Produces:** canonical project init/build/run/check/test and optional `install.sh --canonical-only` workflow with relocated components.

- [ ] Write and run a failing project-lifecycle test: `nql init app --backend canonical` must create valid C0 source and persistent backend configuration. Record real unsupported-option RED before edits.
- [ ] Implement explicit backend/profile project option propagation and `[build] backend` selection; reject invalid/duplicate build selection. Canonical init includes a passing `tests/smoke.nql`. Preserve existing default template/dispatch, including legacy NASM/LLVM routes. For source-running canonical invocations route to nqlc rather than R0; `--` retains program arguments.
- [ ] Implement cache identity using selected backend/profile, source/manifest and actual driver/component/pin bytes, and validate executable mode/output digest before reuse. Test backend/profile changes, changed source/helper/pin/binary/mode, stale/missing components and advisory cache-write failure. Report a cache hit as cached rather than inventing a literal `0ms` elapsed time. Backend-like program arguments after `--` never select a compiler. Reject multi-unit canonical build/check instead of concatenation.
- [ ] Extend installer with combined default and canonical-only mode, copied bootstrap provenance/assets/helper and unchanged public names/aliases. In a fresh PREFIX/DESTDIR with no R0/NASM/linker/Python available, install, change to unrelated cwd, compile/check/run and run a fresh canonical project. Test unknown options, installed pin rejection, relocation/path spaces and uninstall cleanup without touching global prefixes.
- [ ] Run the new project/install module and all Task 1 tests GREEN; rerun existing project/alias CLI regression coverage. Save receipts/diffs, self-review and return report for independent task review.

### Task 4: Truthful MCP Compilation And Integrated Verification

**Files:** modify `tools/nolqu_mcp.py`, `tests/compiler/run_tests.sh`, `README.md`, `tools/README.md`, `docs/project/STATE_OF_PROJECT.md`, both authority masters; create `tests/mcp/test_canonical_toolchain.py`, `docs/compiler/CANONICAL_TOOLCHAIN.md`. Controller owns the already staged `examples/canonical/checksum.nql`; exercise/document it without rewriting it.
**Consumes:** Tasks 1/3 CLI/project/install contracts and Task 2's reviewed MCP process executor/structured results.
**Produces:** optional backend selection on existing tools and a verified documented workflow; no new tool names or bootstrap stage.

- [ ] Add failing unit tests for optional backend forwarding/validation and compile-without-output execution prevention in `compile_nql`, legacy `compile_file` and `run_pipeline_step(..., "full")`. Add a real fresh SDK stdio test invoking `compile_nql` with canonical source/output from an unrelated cwd. Mock-only results never count as compilation evidence.
- [ ] Add optional backend to `compile_nql`, `nql_init/build/run/test/check` and optional `compiler_profile=False` to `compile_nql` and `nql_build/run/test/check`. Keep existing default/required arguments and names. Validate backend before execution, propagate arguments safely, and return structured errors on malformed flag quoting. Full/default compilation explicitly supplies an output, whereas checking/IR modes keep their existing output contract. A failed compile reports no newly built artifacts. Correct pipeline check/full descriptions to match behavior.
- [ ] Register both new compiler unittest modules in the main suite with explicit PASS markers only on success; retain every baseline marker. Add concise user instructions and actual maturity/compatibility boundaries. Fix the obsolete STATE_OF_PROJECT current-direction capacity blocker using measured current facts.
- [ ] Run new MCP tests then complete MCP discovery GREEN; verify all 120 existing tool names, eight resources and five prompts remain available with compatible old required fields and only optional schema additions. Exercise real runtime output/failure and ELF inspection on the produced artifact.
- [ ] After independent task review and actual unchanged-root baseline completion, the controller integrates only owned verified files into the isolated worktree, checks exact baseline-name retention and runs complete `make -k test`, full MCP discovery, `make release-check`, seven hashes, real relocated install tests and a fresh combined C0 probe. From an unrelated cwd also rebuild both complete current compiler sources through public `nqlc --backend canonical --compiler-profile`, compare actual output bytes to the retained C0.31 B identities, and execute the documented stream example through the public/MCP path. These are component-generation/access checks, not Full Compiler/self-hosting promotion. Run final whole-change review. Record actual results, rollback, remaining language limits and final classification; no version bump or external operation.

## Preflight Resolution

Tasks 1/3 share a public CLI contract, not write ownership; Task 3 owns installed copying of Task 1's private helper. Task 2 is an independently measured process-boundary repair with no CLI dependency and no shared write scope with Task 1. Tasks 2/4 sequentially modify distinct MCP regions; Task 4 snapshots/reuses the reviewed executor rather than replacing it. Tasks 1/4 share compiler arguments; Task 4 tests the real CLI as well as unit forwarding. Tasks 3/4 share persistent project backend selection; MCP omission honors manifest defaults. Only Task 4 edits suite registration/docs. The baseline remains immutable while staging progresses; integration waits for its actual terminal result. No task can declare Full Compiler or release success. The controller keeps dirty-snapshot diffs because HEAD omits inherited untracked compiler files. This extra repair task is justified by measured resource/protocol failures, not artificial delivery fragmentation.

## Evidence-Based Terminal Ownership Ruling

The actual controlling-PTY probe `task1/round1/receipts/round1-assess-setsid-pty` in the milestone evidence directory demonstrated that a directly parented util-linux `setsid` runtime with job control disabled preserves terminal input and foreground ownership while enabling bounded driver-PID and terminal Ctrl-C cleanup. Adopt this explicit Linux host-orchestration requirement for canonical terminal stdin execution only; compile/check and piped execution retain their existing dependency boundary. The final production helper must cover the measured ownership invariant and missing-utility failure, rather than retain the rejected Bash foreground heuristics. No bootstrap source/seed/pin, source semantics, or Python runtime is added. Installer/docs/tests must disclose this bounded runtime requirement.
