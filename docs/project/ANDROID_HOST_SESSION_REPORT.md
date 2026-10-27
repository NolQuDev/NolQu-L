# NolQu-L native host and CI preparation record

Source-cut record: 2026-10-27, before the first Linux CI push. Subsequent runner
results belong to the exact GitHub commit/run and its retained artifact; this
record does not predict them. Active workspace is native Termux private storage,
with observed TracerPid0. Earlier PRoot runs remain historical.

## 0. Update classification and release impact

Requested mode: continue development, use native Termux plus Linux CI, push to
NolQuDev/NolQu-L, and use version1.0.0-alpha.1. Host fixes are Patch/Repair;
the additive CI work is Minor Development, risk HIGH for evidence/publication.
Scope: host evidence, smoke integrity, process cleanup, portability fixtures,
CI and documentation. Compiler syntax/semantics/ABI and bootstrap topology are
unchanged. Public version display deliberately changes from1.0.2a1 to
1.0.0-alpha.1 at the maintainer's request. CHANNEL remains dev; maturity ALPHA.
This is a documented naming reset, not a SemVer upgrade from the old label.
RFC not required; internal decisions are in the Android design and Linux CI
plan, without an invented accepted ADR. No source/ABI migration or rollback
is required. Historical labels, hashes and receipts are preserved. Changelog
updated. No official release/tag or stable/self-host promotion is performed.

## 1. Baseline test

Native initial command: make -j1 test, exit2, zero PASS markers. Its first17
evidence-control methods produced2 failure records and19 subtest/error records
because Android Python omits os.link; these are overlapping unittest records,
not a fabricated unique failure count. No compiler crash or timeout was observed.
The immutable native-baseline-main.json and raw streams remain in the private
session evidence. Pre-migration1080-marker and MCP124-method successes describe
their earlier host/helper revisions, not this native run.

## 2. Baseline bootstrap

Machine Foundation, Stage0, B0 and Core emitter/components have real artifacts,
predecessor builders, pins and prior passing gates in bootstrap/manifest.tsv.
Fresh native runs reached the C0.32 capacity backend before host-oracle failures.
Full Compiler, formal self-host nqlc and Verified nqlc remain NOT IMPLEMENTED.
The manifest is not promoted or rewritten for a host migration.

## 3. Readiness evaluation

BELUM SIAP for full native qualification or stable release. Scoped native smoke
and assurance work, but actual hard-link creation is denied even in a private
directory. Source and malformed-AST checks are present; full-language Safety,
ownership/lifetime, modules and Full Compiler remain incomplete. Current Core
pipeline has lexer/parser/indexed AST, bounded i64/name/native-scope validation,
direct ELF codegen and checked runtime helpers. General type/Safety inference
and an optimizer for this canonical path are not implemented. Host tooling
is separate from the syscall-only compiler artifacts. Resource evidence is
finite testing, not a proof of absence of leaks or all possible hangs.

## 4. Change plan

Priority order: reproduce native publication failure; restore complete atomic
evidence; repair verified-runner loading/report publication/adapter hashing;
repair actual host FD/inspection/MCP environment assumptions; add Linux hard-link
qualification; review and push an explicit source snapshot. Reasons and risk
are recorded in the dated Android/Linux plans. Required tests are focused
RED/GREEN controls, impacted subsystem checks, relevant full gates, hashes and
independent review. Large language features stay frozen during this work.

## 5. Implementation

- c031_support._native_blob replaces unsupported hard links with closed staging,
  directory flock, complete-file rename and exact existing-blob validation.
- nql_android_smoke compiles the source bytes verified against its initial
  manifest; unchecked cached pyc cannot replace them. Report staging is unique,
  fsynced and owned-cleaned. Adapter hashing reads bounded chunks from one
  regular descriptor without sharing the guest stream-size limit.
- Standard-FD fixtures preserve actual Linux closure; Android uses wrong access
  modes to reach the same guest EBADF/status/diagnostic after runtime startup.
- Stage0 compares entry-address hex case-insensitively, preserving numeric value.
  Android disassembly uses real ndisasm instruction boundaries; GNU Linux oracle
  stays in place. Pipe parsing avoids large text files, with deadline/owned cleanup.
- MCP uses Python pidfd APIs first, or declared libc bindings when absent.
  Self-probe, identity checks and private process ownership remain required.
  Native stdio configuration explicitly supplies the Termux exec shim and TMPDIR.
- Linux CI has real hard-link preflight, existing named controls, sequential
  gates, pinned actions, read-only token access and retained failures. Final
  canonical identity validation happens before publishing PASSED.

## 6. New capabilities

Optional experimental host smoke and Linux qualification; no new language
syntax or ABI. Linux qualification uses .github/scripts/linux_qualification.py
with a new output directory. A Linux host and actual hard-link support are
required. Native Android rejection is explicit, not a passing qualification.
Host dependencies and cost/budget limits are documented in LINUX_CI.md.

## 7. Bugs and limitations found

| Finding | Status / evidence |
| --- | --- |
| Unavailable os.link broke native evidence publication | FIXED; NE18 and publication/concurrency controls |
| Unchecked cached runner bytecode bypassed source verification | FIXED; AB10 RED/GREEN |
| Stale staging masked a failed report | FIXED; AB11 RED/GREEN |
| Adapter file size incorrectly shared stream cap | FIXED; AB12 actual8MiB+1 adapter |
| Linux redundant closed-FD close hid intended write oracle | FIXED; NE19 RED/GREEN |
| Android startup refilled closed standard FDs | FIXED test setup; NE20 and actual guest FD cases |
| Python Android omitted available libc pidfd wrappers | FIXED; real process/timeout/fail-closed controls |
| SDK environment omitted exec shim/TMPDIR | Configuration and fixture repaired; final SDK rerun pending at source cut |
| Decoder reader-start failure escaped cleanup | FIXED; real child constructor/submit RED/GREEN |
| Qualification wrote PASSED before final hash check | FIXED; OSError/KeyboardInterrupt RED/GREEN |
| Native hard-link creation denied | BLOCKED host capability; real inode tests remain required on Linux |
| C032-SIGNAL-01 earlier unexplained comparison-backend SIGKILL | OPEN; later passes do not establish the original cause |
| C032-RETENTION-01 two older metadata records lost | PARTIAL; no fabricated reconstruction |

An initial native GNU inspector could decode only ARM; an initial disk-stream
ndisasm variant hit the inherited32MiB file limit (attributed host SIGXFSZ).
Both failures are retained. The final pipe version passes actual wide-branch
and inside-immediate controls without increasing runner limits.

## 8. Tests after implementation, as actually executed

| Gate | Actual result at this source cut |
| --- | --- |
| Android smoke controls |12 methods PASS, including AB10–AB12 |
| Evidence controls in latest native main attempt |20 methods PASS |
| Copied native smoke |13 checks /32 invocations PASS, untraced Termux |
| Existing bounded runner controls |11 methods PASS |
| Finite assurance |4 methods /594 invocations PASS; no timeout/signal/supervisor failure |
| Decoder/boundary/cleanup targeted tests |4 methods PASS |
| Profile real-error/empty-range FD controls |2 methods PASS |
| New CI controls after review fix |7 methods PASS |
| Version release-check |9 checks PASS at1.0.0-alpha.1 |
| Four installed CLI version commands |PASS at1.0.0-alpha.1 |
| Native full main latest retained attempt before later fixes |exit2 after230 PASS markers; not a full-suite PASS |
| Native full MCP latest discovery before final TMPDIR fix |127 methods,11 error records:4 hard-link subtests and7 SDK/temp failures |
| Native toolchain CLI after version edit |exit1 after40 PASS markers; incomplete, no success claim |
| Actual GitHub Linux job |NOT RUN at source cut |

Counts overlap and must not be summed as unique tests. New final-check controls
found and fixed an introduced host reporting regression. Regression detected:
YES during development; those specific regressions have RED/GREEN proof. No
compiler semantic regression was established, but full relevant qualification
is still pending; there is no claim that every historical test remains green
on the current native host. No required test is quarantined or retried into PASS.

## 9. Bootstrap verification

Installed C0.32 frontend/backend and B0/emitter pins are unchanged. Earlier
component B/C equality remains evidence for its bound inputs, not formal
Verified nqlc. The old61-file proof now has51 identical files and10 deliberate
host-fixture changes; its closure is not reused to prove new host code. A fresh
Linux job will retain its actual generation comparisons and named-oracle results.

## 10. Resource and memory validation

Actually exercised: owned staging cleanup, existing-output preservation, invalid
blob rejection, concurrent cooperating publishers, standard-FD failures, bounded
process/descendant cleanup, cancellation, decoder startup failures and finite
guest streams. No claim of whole-project leak freedom, RSS bounds, allocator
fault-injection completeness, or universal power-loss durability. The runtime
libc bridge uses pidfds; it does not replace them with PID-only signaling.

## 11. Diagnostic validation

Controls compare actual source-located C0P/C0B/C0S rejections, runtime bounds and
arithmetic diagnostics, exact status and empty output on invalid input. Native
host failures are separately recorded, including AttributeError for unavailable
os.link, PermissionError for inaccessible/tmp, and coreutils Permission denied
for real hard-link creation. Host errors are not mislabeled compiler diagnostics.

## 12. Compatibility report

| Axis | Status / reason |
| --- | --- |
| Source syntax/semantics |Compatible; canonical compiler bytes/sources unchanged |
| CLI/tooling |Version display changes deliberately; new experimental CI tooling |
| Standard library/API |Unchanged; none added here |
| ABI/FFI |Compatible; no generated calling convention change |
| Binary/artifact |Canonical seeds/pins preserved |
| Runtime behavior |Unchanged; host fault fixtures corrected |
| Bootstrap chain |Preserved; no new canonical dependency |
| Reproducibility |Existing pins preserved; fresh host proof required |
| Diagnostic contract |Compiler codes/locations preserved |
| Project/module format |Preserved |

No source/ABI breaking change. Raw version-string consumers need the new
alpha label; old historical version labels are not rewritten or replaced.

## 13. Actual architecture

CURRENT canonical source path: .nql -> C0 frontend -> validated NQAF/1..6 ->
C0 semantic/native-scope checks and direct x86_64 emission -> ELF64 executable.
Shell handles files/atomic publication. QEMU is the aarch64 host execution
adapter. R0/NASM and LLVM/Python compatibility paths remain separately identified.
TARGET Full Compiler/type/Safety/IR/optimizer/library architecture is unfinished.

## 14. Final bootstrap chain at source cut

Machine Foundation PASS -> Stage0 PASS -> B0 PASS -> Core emitter/components
PASS for their implemented bounded contracts and preserved pins. Full Compiler,
Self-Hosting nqlc and Verified nqlc: NOT IMPLEMENTED. Fresh complete Linux
qualification remains NOT TESTED at this cut. Native full qualification: BLOCKED.

## 14A. Release/changelog status

Release Ready NO. Version1.0.0-alpha.1, CHANNELdev; no tag or official release.
Changelog updated. Independent static CI review completed with one P2 corrected
and re-reviewed; it is not runtime qualification. GitHub CI required, not run
at this cut. SBOM/provenance/signing NOT IMPLEMENTED. Support stays DEVELOPMENT.
No confirmed vulnerability advisory is produced from these host correctness
repairs. Release blockers include required qualification and C032-SIGNAL-01.

## 15. Session outcome and next blocker

Native execution and finite smoke/assurance are real. Host evidence and CI
reporting defects are repaired with retained regressions. Full native tests
are not all green. Next: push the exact reviewed product snapshot, execute the
Linux gates, inspect failures without changing oracles, then retain the result.
Full language/Safety/self-hosting work resumes only after its relevant foundation
is stable. Prior unexplained signal/retention gaps remain explicitly open.

## Security assurance

Security review scope: host loader/publication/cleanup and CI evidence boundary.
Threat model updated in the Android design and Linux CI notes. Test profiles:
targeted controls plus finite EXTENDED assurance; RELEASE qualification NOT RUN.
Corpus native-boundary-v1 SHA256
1f30672e7085104130363f346c4b07f069306fb7f2f1a6ce62da0162db516bee;
mutation seed0x4e514c32,594 invocations,5s/call and600s total budget. No coverage
percentage or coverage-guided fuzz claim. No NolQu-L ASan/UBSan/MSan/TSan
instrumentation is available; native guards and QEMU probes are finite alternatives.
Static Python/Bash/YAML checks and independent read-only review are scoped evidence.
Defined metamorphic oracles passed in assurance; optimizer comparison unavailable.
No new HIGH/CRITICAL vulnerability is established by this limited work, which is
not a repository-wide security scan. Public source publication excludes private
host state; a credential-pattern check is not a complete secret audit. Required
Security Gate BLOCKED for release/full qualification, so neither VERIFIED nor
SECURITY QUALIFIED is claimed. Signing, formal provenance and SBOM are absent.
