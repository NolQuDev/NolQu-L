# NolQu-L — C0.32 reliability continuation

Evidence date: 2026-10-26T13:02:06.981669+00:00. Authoritative isolated
worktree: `/home/Axelly/.codex/worktrees/4878/NolquASM`. Original working directory was preserved. This report concerns
the host evidence continuation; the earlier C032_SESSION_REPORT.md remains the
compiler/formatter checkpoint. No commit, merge, push or release was performed.

## 0. UPDATE CLASSIFICATION & RELEASE IMPACT

```text
Requested Mode: continue unfinished NolQu-L development
Initial Class: Patch / Repair investigation
Actual Update Class: Minor Development
Reason for Reclassification: additive host per-invocation retention after the actual evidence-loss gap was established
Risk Level: HIGH (proof-bound host process/evidence boundary)
Primary Scope: per-call evidence retention and missing post-formatter full regression
Affected Subsystems: host test helper, bootstrap test dispatch, proof inputs, documentation
Public Contract Impact: language/CLI/runtime/ABI unchanged; experimental internal test option added
Bootstrap Impact: source/seed/pin/topology preserved; helper/gate identities require fresh proof
Security/Trust Impact: stronger observability; no sandbox/signing/attestation claim
Compatibility Impact: default execution retained; tested enabled kwargs/status/bytes preserved
Version Impact: NONE; VERSION1.0.2a1, CHANNELdev
Release Maturity: DEVELOPMENT / alpha; host feature EXPERIMENTAL
RFC Required: NO; no language/ABI/stage redesign
ADR Required: no formal ADR number; internal decision recorded in NATIVE_TEST_EVIDENCE.md and plan
Migration Required: NO; opt-in only
Changelog Required: YES, Unreleased host-test addition
Rollback/Revert Required: NO regression requiring rollback; remove observer branch/control/dispatch together if needed
Release Blocking Issues: C032-SIGNAL-01 OPEN; broader Full Compiler/Safety/release maturity incomplete
Release Performed: NO
Version Bump: NONE
```

Impact axes: syntax, semantics, type/Safety, frontend, IR, backend, runtime,
stdlib, source/behavior compatibility and ABI/binary: NONE because their source
and pins were untouched. CLI/tooling: MEDIUM internally through a test-only flag.
Bootstrap/reproducibility/security-trust: HIGH for newly bound host proof, with
unchanged machine artifacts. Host resource cost: MEDIUM (explicit byte-copy/hash/
fsync); generated program cost unchanged. Documentation: MEDIUM. Migration: NONE.

## 1. BASELINE TEST

Baseline commit: `66b92a4ce9e5491e570d292fe1b0320f04ba1907`.
The actual commit and dirty-tree snapshot are retained in the input ledger;
no clean-tree claim is made. Full baseline bound457 files. New product changes
began only after all serial baseline phases completed.

Commands actually executed (cwd `/home/Axelly/.codex/worktrees/4878/NolquASM`):

```sh
env C031_WORK=/tmp/nql-c032-reliability-20261026-ems1vhfz/normal-baseline/generations NQL_CANONICAL_RECEIPTS=/tmp/nql-c032-reliability-20261026-ems1vhfz/normal-baseline/main-public/cli NQL_PROJECT_RECEIPTS=/tmp/nql-c032-reliability-20261026-ems1vhfz/normal-baseline/main-public/project make -k test
.venv-mcp/bin/python -B -W error::ResourceWarning -m unittest discover -s tests/mcp -v
.venv-mcp/bin/python -B -W error::ResourceWarning tests/security/test_bounded_runner.py -v
NQL_ASSURANCE_OUTPUT=/tmp/nql-c032-reliability-20261026-ems1vhfz/normal-baseline/security-assurance .venv-mcp/bin/python -B -W error::ResourceWarning tests/security/test_native_assurance.py -v
make release-check
```

| Baseline gate | Total / passed | Failed / skipped / timeout / uncontrolled crash | Elapsed |
| --- | --- | --- | --- |
| main (marker count, not unique test methods) | 1079 / 1079 | 0 / 0 / 0 / 0 | 4489.999s |
| MCP |124 /124 methods|0 /0 /0 /0|626.415s|
| runner controls |11 /11 methods|0 /0 /0 /0|5.946s|
| assurance |4 methods,594 invocations|0 /0 /0 /0|369.463s|
| release metadata |9 /9 checks|0 /0 /0 /0|5.486s|

Counts overlap and are not summed into a fictitious unique total. Negative
controls' intentional signals/timeouts are expected assertions, not unexplained
compiler crashes. All457 baseline inputs remained identical before/after.

Failed experiment retained separately: full main under `/system/bin/strace -f
-ttt -T -s256 -e trace=process,signal,memory` exited2 after3462.776s,225 markers,
with one `TimeoutExpired` at the unchanged15s concurrent frontend materializer
case (14 frontend methods took896.826s). The same exact method passed untraced
in2.152s. No expected result, timeout, retry policy or compiler source was changed
to hide that failure. Tracing overhead is an instrumentation limit, not a compiler
performance benchmark or explanation of the earlier ordinary-9.

Pre-existing: C032-SIGNAL-01 remains OPEN. The dependency Pydantic lifespan warning
was already present and remains a warning; no package change/filter hides it.

## 2. BASELINE BOOTSTRAP

| Stage | Status / evidence |
| --- | --- |
| Machine-Level Foundation | PASS: machine_foundation.sh, self decoding/hash |
| Stage0 | PASS: stage0.sh, predecessor reconstruction/symbols/hash |
| Bootstrap Compiler B0 | PASS: bootstrap_compiler_b0.sh, Stage0 build/hash |
| Core Compiler / components | PASS: emitter C0.25 and C0.32 frontend/backend gates; actual component B=C |
| Full Compiler | NOT IMPLEMENTED |
| Self-hosting public nqlc | NOT IMPLEMENTED |
| Verified public nqlc | NOT IMPLEMENTED |

The normal baseline generation receipt contains722 stages,275 checks,475 artifacts
and two named oracle runs. Component equality is bounded component evidence,
not promotion of the final three stages.

## 3. EVALUASI KESIAPAN

**BELUM SIAP untuk stable/security promotion atau feature expansion yang mengabaikan
reliability blocker.** The scoped host change is validated under the stated cases.

- Stability: current full baseline passes; original old-backend-9 cause is unknown.
- Memory/resource: process/FD cleanup cases are exercised; no universal leak or
  allocation-failure guarantee. New read FDs have explicit ownership and closure.
- Error handling: original returncodes/streams/exceptions remain available; archive
  failure is a distinct NativeEvidenceError; missing terminal record stays incomplete.
- Architecture: host observation is separate from compiler semantics, canonical stage
  outputs and strict generation stage/check labels. No new stage/dependency was added.
- Bootstrap:7 pinned artifacts stay unchanged; changed host inputs receive fresh proof.
- Pipeline: lexer/parser/indexed AST/name-scope-arity/scalar i64/direct ELF/runtime
  substrate are implemented for C0.32; general types, ownership/borrow/lifetime,
  full Safety, canonical optimizing IR and Full Compiler remain partial/planned.
- CLI/toolchain: nql/nqlc and long aliases preserved; R0 default and explicit
  canonical path unchanged. Internal evidence environment option is experimental.
- Testing: real host17 controls, actual x86/QEMU14 comparisons plus two exact-error
  supplemental comparisons and full relevant
  regressions; finite corpus/defined-semantics oracles, not exhaustive security proof.
- Compatibility: no source, public ABI, project format or artifact break.
- Technical debt: unknown historical signal attribution, limited kernel telemetry,
  no coverage-guided NolQu-L sanitizer instrumentation, incomplete Full Compiler/Safety.

## 4. RENCANA PERUBAHAN

| Priority / problem | Root cause / change / files | Why now / risk / required tests |
| --- | --- | --- |
|1: close missing current main result|full post-formatter main was NOT RUN; unchanged source serial baseline|establish actual baseline, HIGH assurance; full relevant gates|
|2: retain failure evidence|run_native returned status/streams without PID/start or durable transient input/exe; helper/control/dispatch|future failures must be diagnosable; HIGH; RED retention then real process, fd, timeout/cancel, path tests|
|3: fresh proof|helper and run_tests are proof-bound; existing receipts cannot certify new bytes|retain fail-closed identity graph; main/MCP/combined generation/assurance/release|
|4: documentation/retention|old current references had pre-formatter-only main status|sync actual results, threat/invariant map, limitation and next blocker|

Plan: docs/superpowers/plans/2026-10-26-native-evidence.md. No new language feature.

## 5. IMPLEMENTASI

Changed `tests/bootstrap/c031_support.py` (old8038 bytes ->23778),
`tests/bootstrap/test_run_native_evidence.py`, `tests/bootstrap/run_tests.sh`,
`docs/compiler/NATIVE_TEST_EVIDENCE.md`, plan and current evidence documentation.
No compiler source, seed, pin, VERSION or CHANNEL was changed.

Actual execution branch:

```python
archive = os.environ.get("NQL_NATIVE_EVIDENCE_DIR")
if archive is not None:
    return _run_native_observed(command, binary, runner, timeout, options, archive)
return subprocess.run(command, timeout=timeout, **options)
```

The observer retains private SHA256 blobs and atomic begin/launched/result
records; target/adapter/supplied stdin bytes precede launch. Popen kwargs,
input/check/capture handling, timeout exception and negative status remain distinct.
Raw file-read descriptors use open(NONBLOCK/CLOEXEC), fstat regular-file validation,
read and finally-close. Kernel logical paths handle symlinks/parent components and
unlinked proc-FD executables; opened-path and cwd hints are best-effort metadata.
Unusable later PATH entries do not become guest failures; archive corruption
remains fatal. No archive descriptor is left open across spawn.

Error handling preserves result/original_error on NativeEvidenceError, marks
unobserved streams/proc fields explicitly, and never invents a zero guest status.
One explicit bootstrap invocation runs17 host controls before existing stage gates.
All existing stage invocations remain present.

## 6. FITUR BARU

Feature: experimental **host-test** per-call evidence, not a language construct.
API: precreate a trusted absolute directory; set `NQL_NATIVE_EVIDENCE_DIR`.
Semantics: retain exact available byte inputs/outputs and process observations;
absent flag retains the ordinary run path. Machine/runtime cost: host copies,
hashes, fsync and metadata; no generated-program operation change. Invalid archive
fails before launch; post-launch observation failure reaps the owned process under
the original policy and raises a separate evidence exception. See17 NE test IDs.

## 7. BUG YANG DITEMUKAN

| Bug / priority | Cause / status / regression |
| --- | --- |
| Original C032-SIGNAL-01, reliability priority HIGH | OPEN: frozen old backend-9; missing original PID/start/sender; no compiler repair claimed |
| Draft empty archive writes current directory | FIXED before integration; explicit empty rejection; NE07 RED/GREEN |
| R1 P1 FIFO open waits before type check | FIXED in unpublished draft; NONBLOCK/read-type guard; NE11 |
| R2 P2 override/decoy executable retention | FIXED in draft; logical path/child cwd lookup and exact blobs; NE12/13 |
| R3 P2 directory FD leaks, including blob reader | FIXED in draft; raw FD owner/finally; NE14 all three cases |
| R4 P2 unused PATH error aborts valid call | FIXED in draft; path errors separated from fatal archive integrity; NE15/NE07 |
| R5 P2 open/unlinked proc FD bytes lost | FIXED in draft; no mandatory canonical filename; NE16 |
| R6 P2 deleted parent cwd rejects valid launch | FIXED in draft; optional hint/conditional anchoring; NE17 |

The original failing test was `CapacityBackendTests.test_legacy_byte_parity_and_limits`
under `make -k test` (`/tmp/nql-next-compiler-v7wdgsfr/main-full/receipt.json`).
Its source was `fn add(a,b){return a+b} fn main(){return add(2,add(3,4))}`.
The frozen C0.30 comparison backend returned -9 with empty stderr where normal
compilation required status0 and an ELF; the candidate returned0. The full gate
exited2. Original victim PID/start/input/executable package and signal sender were
not retained. No OOM, Android policy or compiler defect attribution is established.
Reproduction rate: NOT ESTABLISHED. Quarantined: NO. Tracking: C032-SIGNAL-01 in
this report and the prior signal review. Exit criterion: matching attributable
failure evidence and a verified fix or explicit justified reliability decision;
later passing runs alone do not close it.

The observer now retained four current matches with the exact frozen executable
SHA256 `46a08a95224f7171b7fd9b948fecaf1e7b6e819c4a8b4b8471b980361d708405`
and NQAF input SHA256 `6de68ecce4acdca6f252053bf8c353672120d1eac423997888977b9c3ebd2ed2`.
All four returned0. Raw records, process observations and blobs are indexed by
`final-native-archive-audit.json`; this proves retention of current executions.

A draft text-mode control initially passed bytes to `text=True`; the unchanged
Python execution path rejects that combination too. The control was corrected
to valid text input. The 9-PASS/1-ERROR draft result remains in the ledger and
is not counted as a product failure fixed by changing execution semantics.

All draft failures and review reports are retained, not rewritten as past passes.
These were unpublished host-helper defects, not confirmed released NolQu-L
vulnerabilities or explanations of the historical signal. No bug is silently
quarantined and no release blocker is marked DEFERRED.

## 8. HASIL TEST SETELAH IMPLEMENTASI

Exact final serial commands (cwd is the authoritative worktree; assurance output
was set to the final-validation/security-assurance directory by the controller):

```sh
env NQL_NATIVE_EVIDENCE_DIR=/tmp/nql-c032-reliability-20261026-ems1vhfz/final-validation/native-calls C031_WORK=/tmp/nql-c032-reliability-20261026-ems1vhfz/final-validation/generations NQL_CANONICAL_RECEIPTS=/tmp/nql-c032-reliability-20261026-ems1vhfz/final-validation/main-public/cli NQL_PROJECT_RECEIPTS=/tmp/nql-c032-reliability-20261026-ems1vhfz/final-validation/main-public/project make -k test
/home/Axelly/.codex/worktrees/4878/NolquASM/.venv-mcp/bin/python -B -W error::ResourceWarning -m unittest discover -s tests/mcp -v
/home/Axelly/.codex/worktrees/4878/NolquASM/.venv-mcp/bin/python -B /tmp/nql-next-compiler-v7wdgsfr/verify_combined_probe.py /home/Axelly/.codex/worktrees/4878/NolquASM /tmp/nql-c032-reliability-20261026-ems1vhfz/final-validation/combined-proof
/home/Axelly/.codex/worktrees/4878/NolquASM/.venv-mcp/bin/python -B -W error::ResourceWarning tests/security/test_native_assurance.py -v
make release-check
```

| Gate | Total / passed | Failed / skipped / timeout / uncontrolled crash | Elapsed |
| --- | --- | --- | --- |
| full observed main |1080 /1080 markers|0 /0 /0 /0|5461.709s|
| integrated host controls |17 /17 methods|0 /0 /0 /0|12.851s (wrapper14.080s)|
| actual adapter smoke |14 /14 comparisons|0 /0 /0 /0|receipt-bound|
| actual adapter exact-error supplement |2 /2 comparisons|0 /0 /0 /0|1.455s|
| MCP default path |124 /124 methods|0 /0 /0 /0|598.664s|
| fresh combined proof |one actual combined probe; full relevant component gates|0 /0 /0 /0|1617.216s|
| bounded assurance |4 methods;594 invocations|0 /0 /0 /0|366.852s|
| release metadata |9 /9 checks|0 /0 /0 /0|10.577s|

**Regression detected: NO** in these current-source gates. All1079
baseline PASS labels remain; exactly one dispatch marker was added. Counts are
not unique test totals and overlapping suites are not summed. Runner11 stayed
unchanged and its completed baseline is retained; no redundant rerun is claimed.
Gates bound460 execution input files before/after. Documentation-only final sync
is recorded separately; runtime/proof input identities remain unchanged.

## 9. BOOTSTRAP VERIFICATION

Compiler A: selected profile components built by B0 (A1=A2). Compiler B: actual
full source compilation. Compiler C: same full source rebuilt by B. B vs C:
byte-for-byte identical for both components, with hashes independently checked.

| Component | A1 bytes / SHA256 | B and C bytes / SHA256 | B vs C |
| --- | --- | --- | --- |
| frontend | 124215 / `9da819d6ea3017d39135532f0b4c3f0cd3105d31e4450802302bb9422e2f5e5b` | 6361360 / `65e2f7de291a0dd735424014d28def990cdeaa46697b5d196edda17c9f1a79bc` | identical |
| backend | 315593 / `b169f9ee8890d306c080f299980c352bbabc5518052355dd0148a7878b9f51b1` | 6475137 / `c789a3442691dd4f51f51ecb594265ff7b106a45313b8f6e91c7ec233bd29f85` | identical |

Fresh combined MCP probe validates722 stages/275 checks, two oracle runs and
475 artifact labels, including retained native artifacts. Formal Full Compiler,
self-hosting nqlc and verified nqlc stay NOT IMPLEMENTED.

## 10. RESOURCE / MEMORY VALIDATION

File descriptors: closed/wrong-direction streams, external stdin non-consumption,
passed-FD offset preservation, before/after directory and blob FD cleanup, unrelated
sibling survival. Subprocess: ordinary exit/signal/timeout/cancellation/spawn failure;
owned handle reaped in exercised cases. Temporary files: bytes survive caller
TemporaryDirectory cleanup; unique call dirs/atomic blobs/JSON tested concurrently.
No host-wide leak, peak-RSS, allocator-failure or arbitrary descendant guarantee.

At execution close, before the later archival experiment, the main sidecar audit found 3771 completed invocations;
1364 unique blobs, 1325852120 unique byte payloads.
Integrity audit validates references/hashes/modes. It found 0
incomplete records and 0 ordinary signal outcomes in that
archive. Controlled host test archives are separate. A later cross-directory
hardlink archival experiment failed on this host and lost two early metadata files
(`call-_1q_nvza/begin.json` and `launched.json`). Its controlled probe also exposed
an unexpected alias that overwrote `call-_1bx7b2a/result.json` with29 control bytes.
The terminal was restored from the independent retained-v2 copy after matching
its original audit SHA256 `13fe3d0cc8c8a664ec44091d3e96bc42a7259cf5bd09e054266dd49816fb2666`.
No early metadata was fabricated. The failed partial archives are not final proof;
subsequent retention uses independent byte copies only. This archival incident
is separate from compiler execution and C032-SIGNAL-01 and keeps retention PARTIAL.
Recovery details and the failed control are preserved in retention-recovery.json
and retention-link-investigation.json. The pre-archive zero-incomplete count
must not be read as a claim that every later begin/launched file survived.
The execution-close audit retained
4 old-backend nested-call tuples with
exact executable/input blobs and actual PID/start/status. That improves future
reproduction; it does not reconstruct the missing historical victim.

## 11. DIAGNOSTIC VALIDATION

Current-source actual-adapter comparison covers malformed parse, unknown binding,
unsafe raw call outside boundary, checked overflow and closed input. Enabled and
disabled stderr bytes/status match exactly; raw blobs and comparison receipt are
retained at `/tmp/nql-c032-reliability-20261026-ems1vhfz/actual-adapter` and `actual-adapter-negative`. The first smoke's
seven-argument syscall case checked only arity rejection (C0P-012); the separate
two-argument source proves C0S-001. The earlier receipt was preserved unchanged.
Actual captured examples (each ends with LF):

```text
input:1:37: error[C0R-001]: integer overflow or division by zero; check operands
input:1:18: error[C0P-006]: expected operand; use identifier, decimal or grouped expression
input:1:18: error[C0B-003]: undeclared local; declare the name before use
B0 runtime: input_read failed; check standard input
input:1:18: error[C0S-001]: raw native call outside unsafe scope; wrap its owning statement in unsafe
input:1:18: error[C0P-001]: invalid byte; use ASCII identifiers and decimal expressions
```

No new language diagnostic code was introduced.
The language's existing C0P/C0B/C0S/C0R errors remain separate from host
NativeEvidenceError. Source/AST invalid paths produce no unintended executable.

## 12. COMPATIBILITY REPORT

Backward compatibility: preserved for public source/CLI/ABI; no breaking change.
Migration: none. Internal observation is opt-in/EXPERIMENTAL and adds explicit host
I/O/failure behavior. Version impact: none.

| Axis | Status | Evidence / migration |
| --- | --- | --- |
| Source syntax | Compatible | compiler source/pins unchanged |
| Source semantics | Compatible | actual adapter expected results, main and B/C oracles |
| CLI/tooling | Compatible public; additive internal test flag | CLI35/project32 retained in main |
| Standard library/API | N/A change | no library edit |
| ABI/FFI | Preserved | source/pins/machine bytes unchanged |
| Binary/object artifact | Preserved | selected and full B=C hashes above |
| Runtime behavior | Preserved | byte/status equivalence and existing native suites |
| Bootstrap chain | Preserved | no stage/trust-root addition |
| Reproducibility | Preserved | current bound proof and byte comparisons |
| Diagnostic contract | Preserved | raw stderr/status comparisons |
| Project/module format | Preserved | nql.toml/cache/CLI paths unchanged |

## 13. FINAL ARCHITECTURE STATUS

CURRENT (unchanged canonical experimental path):

```text
*.nql -> canonical frontend lexer/parser -> NQAF/1..6 indexed AST
      -> backend validation/name-scope-arity/scalar i64/checked codegen
      -> direct syscall-only x86_64 Linux ELF -> executable
```

Host test observation surrounds execution only. Default public nqlc still uses
Reference Compiler R0 unless canonical is explicitly selected. TARGET Full
Compiler adds the still-unimplemented general type/Safety/ownership/IR/runtime
foundations; that target is not displayed as current implementation.

## 14. FINAL BOOTSTRAP CHAIN STATUS

```text
Machine-Level Foundation PASS
 -> Stage0 PASS
 -> Bootstrap Compiler PASS
 -> Core Compiler / C0.32 components PASS
 -> Full Compiler NOT IMPLEMENTED
 -> Self-Hosting nqlc NOT IMPLEMENTED
 -> Verified nqlc NOT IMPLEMENTED
```

## 14A. RELEASE / CHANGELOG STATUS

```text
Release Ready: NO
Release Candidate: NONE
Blocking Reasons: historical unknown-9; incomplete Full Compiler/Safety/stable qualification
Version Impact: NONE
Maturity: DEVELOPMENT / alpha; host option EXPERIMENTAL
Changelog Updated: Unreleased Added, host-test evidence
Migration Guide: not required
Deprecations / Removals: NONE
Known Issues: C032-SIGNAL-01 OPEN; stated telemetry/coverage/retention limits
Review Gate: independent bounded review5 READY; human maintainer approval not inferred
CI Gate: local required commands PASS; hosted CI/rulesets not verified or claimed
Artifact Hashes: retained actual source/seed/component/evidence hashes
Provenance: NOT IMPLEMENTED as release attestation
Signing: NOT IMPLEMENTED
SBOM: NOT IMPLEMENTED
Support Lifecycle: unchanged DEVELOPMENT
Security Advisory: not required for a confirmed released vulnerability; none established in this scope
Release Gate: BLOCKED; no promotion/merge/publish
```

CODEOWNERS has the actual default owner @Nadzil. This work does not fabricate a
human review, release authority, protected-branch configuration or support date.
Retention: PARTIAL local evidence; no numeric retention period is invented.

| Governance item | Actual status |
| --- | --- |
| Review Required / Status | HIGH-risk independent code review5 READY on exact helper/control hashes; documentation/receipt self-review; optional second report-script review NOT RUN after review service usage limit; no human/merge approval inferred |
| CI Required Checks | main, MCP124, actual combined generation proof, assurance594, release9, host17 and actual adapter16 comparisons |
| CI Status | all stated local execution checks PASS; hosted required-check configuration NOT VERIFIED |
| Flaky Test Status | C032-SIGNAL-01 OPEN, cause unknown, no quarantine or retry-based closure |
| Dependency/Supply-Chain Impact | existing stdlib Python/QEMU/shell host dependencies only; no package or canonical compiler dependency added; broad advisory scan NOT RUN |
| Tests Required / Executed | exact commands/counts and separate overlapping scopes in sections1/8; no skipped required local execution check |
| Performance/Resource Impact | optional host copies/hashes/fsync/storage; main elapsed 4489.999s baseline vs 5461.709s observed, one sample each; no variance/isolation or causal speed claim; compiler artifact sizes unchanged |
| Support Lifecycle Impact | unchanged DEVELOPMENT; support duration/release authority/target tier NOT FORMALLY DEFINED |
| Security Advisory Required | no confirmed released vulnerability established; no advisory/backport/release performed |
| Known Limitations / Next Measured Blocker | historical signal lacks original victim/sender package; current retention closes future evidence loss only; Full Compiler/Safety/stable qualification still incomplete |

## 15. RINGKASAN AKHIR SESI

- **Apa yang berubah?** Test-only per-call retention,17 real host controls,16
  actual adapter comparisons, one
  bootstrap dispatch marker, current bound evidence and documentation.
- **Dampak?** Stronger host observability and cleanup/path handling; compiler,
  language, Safety modes, ABI and artifact bytes preserved. Host I/O cost is explicit;
  no compiler/runtime speed improvement is claimed.
- **Baseline tetap hijau?** Yes, all1079 labels retained in current main.
- **Regression?** None detected by the executed gates; draft regressions fixed before
  integration, their RED/GREEN reports preserved.
- **Pre-existing failure?** Historical old-backend-9 OPEN; traced timeout experiment
  understood/retained; Pydantic warning unchanged.
- **Bug di luar scope?** Existing legacy installer prerequisite and historical token
  helper framing limits remain documented in the prior C032 report; no new fix claimed.
  An additional local-link sweep found89 unresolved absolute `/root/Nolqu/` references
  in existing README/changelog content; all89 also occur in HEAD. This is existing
  documentation debt (DEFERRED-NONBLOCKING), not a compiler regression. The broad
  sweep exited1; a separate comparison verifies every newly added relative link.
  Raw classification is in documentation-link-audit.json. No old evidence link
  or removed historical command was rewritten to manufacture a passing broad sweep.
- **Bootstrap di tahap mana?** C0.32 components, including B=C evidence; final three
  canonical milestones NOT IMPLEMENTED.
- **Belum selesai?** Historical signal origin; full language/Safety/self-host promotion,
  continuous fuzz/sanitizer/hosted release qualification and signed provenance.
- **Prioritas berikutnya?** Preserve/review any new signal package, obtain actual
  matching host telemetry if available, close reliability decision with evidence;
  then advance Full Compiler foundations by measured dependency. No speculative
  compiler repair or feature expansion is substituted for unknown cause.

## REQUIRED SECURITY ASSURANCE REPORT

```text
Security Review Scope: host invocation/byte retention/FD-path-error boundary, unchanged compiler identities
Threat Model Updated: YES, scoped source-backed model +11-file identity snapshot
Affected Security Invariants / Test IDs: NE-I01..NE-I11; NE01..NE17
Relevant Attack Surfaces / Trust Boundaries: caller data/argv/fds -> owned child -> private archive -> separately bound proof
Test Profiles Executed: PR + EXTENDED local; no official RELEASE promotion
Fuzz Targets/Corpus/Budget: existing source+NQAF+defined-semantic assurance594, corpus SHA256 1f30672e7085104130363f346c4b07f069306fb7f2f1a6ce62da0162db516bee, seed 1313950770;24 seed-source profile cases/132 source mutations/360 wire rejections/12 semantic-oracle cases; internal600s/per-target5s,8MiB per stream,3MiB input; no RSS limit; finite mutation, no coverage percentage
Sanitizer/Static Analysis: real execution with ResourceWarning-as-error, manual source/FD review, syntax/diff checks; NolQu-L ASan/UBSan/MSan instrumentation unsupported here; TSan not run/no concurrency-safety claim
Negative/Boundary/Resource:17 host controls and existing relevant compiler/runtime/CLI suites
Differential/Metamorphic: actual adapter14 plus2 supplemental exact-error comparisons, enabled/disabled equivalence, actual B=C/named oracles, existing pure semantic assurance
Confirmed Vulnerabilities: none established by this bounded work; not a clean repository scan
Open Security Risks/Mitigations: unknown old signal, restricted kernel/cgroup telemetry, finite coverage, same-UID archive control and non-attestation limits; separate post-run hardlink archival incident with recovered terminal and two lost early metadata files; independent copies replace cross-directory links
Regression Tests Created: NE01..NE17 include reproduced draft R1..R6 classes
Required Security Gate: BLOCKED for stable/security qualification; scoped executed checks PASS
Unrun/Unsupported Checks: coverage-guided fuzz, sanitizer-instrumented NolQu-L, broad dependency advisory scan, privileged kernel OOM tracing, hosted CI/rulesets, full stable release qualification
Release Security Decision: NO RELEASE; raw receipts/current identities retained; original cause not inferred
```

Evidence root: `/tmp/nql-c032-reliability-20261026-ems1vhfz`. Final controller receipt: `/tmp/nql-c032-reliability-20261026-ems1vhfz/final-validation/receipt.json`.
Retained review5: `e55993b28f5224b74ddfa60c6261106a73af454c5e38d74271f49a71f73750c2`.
Current helper: `e5da31149ea5bec3d9ccf3f99f2fa8bddd681ce376d37df9d28a50d9440693f4`.
Source-backed threat model is stored separately in the Codex Security persistent
artifact collection; it is a scoped model, not a completed repository scan.

The available raw evidence now has an independent materialized byte snapshot under
`.superpowers/sdd/2026-10-26-native-evidence/retained-copy/` in the authoritative
worktree. Its `materialized-manifest.json` covers26382 entries, including all3771
terminal records matching the execution-close audit and1364 blobs matching their
hash names. The original link representation remains in the earlier manifest;
8738 entries were materialized/replaced to avoid host link aliasing. The materialized
manifest SHA256 is `e6d99abbb0c06a1152854b229cdba755516f82fe5a56fbaac683b6df657b5870`.
The two lost early records are explicit in the receipt. Failed `retained/` and
`retained-v2/` directories are historical attempts, not the final snapshot.
Subsequent documentation-only updates and closure receipts are retained separately.
Retention remains local and PARTIAL, with no signing, immutability against same-UID
writes, or promised retention interval. Full execution/proof inputs remain exactly
bound after docs.
