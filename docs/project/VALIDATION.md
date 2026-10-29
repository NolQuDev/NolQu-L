# Development validation status

Current metadata: `1.0.0-alpha.1`, channel `dev`.
[The first Alpha prerelease](https://github.com/NolQuDev/NolQu-L/releases/tag/v1.0.0-alpha.1)
was published on 2026-10-29 from
`26ad9b80b5a3164a20854ce3e3798642fba3f15e`. This does not promote Stable,
Full Compiler, formal self-hosting or whole-language security qualification.

## Current verification checkpoint — 2026-10-30

Source revision `78aa35b693e97aa4d3524d8900473eb93d2edc26` completed exact-source
Linux qualification on both
[Main](https://github.com/NolQuDev/NolQu-L/actions/runs/40891390906) and
[Dev](https://github.com/NolQuDev/NolQu-L/actions/runs/40891457841) after the
supervisor metadata repair and resource-accounting addition. Each run passed
all eleven gates: 1,084 main PASS markers, 129 MCP methods, nineteen runner
controls, twenty Android host controls on Linux and seventeen release controls.
Actual component generations retained 722 stages, 275 checks, 475 artifact
records and six equality comparisons. Counts overlap and are not a unique-test
sum. The retained Main artifact ZIP SHA-256 is
`930ea850ec5fd3ce8cb5ef50e6d89b824b08e70290448b8ccba9ebb14222fec6`.
Earlier incomplete-integration statements below describe those earlier steps;
they do not mean that the current full Linux suite was left unrun.

Before this documentation repair, all 404 selected public paths, executable
modes and symlink target bytes matched that revision. The same independently
copied offline bundle then ran once through each local runtime:

| Execution environment | Actual finite-profile result | Native Termux status |
| --- | --- | --- |
| Fedora Python/QEMU in PRoot, Android aarch64 | 15 checks, 326 invocations, 96 oracle matches, both sensitivity detections; exit 0 | Traced; not native-qualified |
| Termux Python/QEMU binaries, Android aarch64 | 15 checks, 326 invocations, 96 oracle matches, both sensitivity detections; exit 0 | Traced; not native-qualified |
| Untraced native Termux | NOT RUN for this profile | Qualification remains open |

Both runtime contexts were traced at their initial and final snapshots. Their
326 corresponding exit codes, 978 exact input/stdout/stderr streams and 107
generated ELF files matched byte-for-byte. All captured streams and supervisor
controls were checked against their retained identities. Waited-child CPU/RSS
observations were available for every invocation on each runtime; these are
host observations, not guest memory bounds, leak proof, signal attribution or
a controlled performance comparison.

The bundle manifest SHA-256 is
`8c472809444d2acc06d9cedf11c749bd4784460b122c5fbad2bf6ed4d11c4eec`;
the shared 48-case corpus SHA-256 remains
`8fd66ecef1738a31044b39ed03926271a68cabfd49e9008294c81906608def9d`.
These finite runs do not replace the full native suite or its filesystem
qualification. C032-SIGNAL-01 remains OPEN; no sender or cause was identified.
No compiler source/seed/pin, VERSION, CHANNEL or published Alpha 1 artifact
changes in this documentation repair. Alpha 2 and Stable are not promoted.

## Alpha 2 readiness investigation — 2026-10-29

Fresh baseline run
[40849891154](https://github.com/NolQuDev/NolQu-L/actions/runs/40849891154)
tested that exact Alpha 1 revision before the supervisor metadata repair.
All eleven gates passed: 1,084 main PASS markers, 129 MCP methods, twenty
Android host controls on Linux, seventeen release controls, real hard-link
tests, finite assurance and release checks. The offline profile retained
326 invocations, 96 differential matches and two sensitivity detections.
Canonical input identities were unchanged. Counts overlap and are not a
unique-test sum. The retained artifact ZIP SHA-256 is
`d301da0aceb5ef4eebd2e4a9f279f656de979ee499132bb548c9ab7b966108f6`.

The new host repair addresses a separate reproducible defect: malformed
supervisor metadata escaped before the invocation manifest was written.
Nonregular metadata could also block outside the execution deadline. Three
regression methods fail on the old reader (thirteen rejecting subcases), then
pass after bounded, regular-file ingestion and controlled failure retention.
All fifteen runner control methods pass locally. This is host evidence handling,
not a compiler semantic or canonical-artifact change. Any repair commit still
requires its own exact-source full qualification before integration.

Actual untraced native Termux execution of the new smoke+differential profile
is still **NOT RUN** in this investigation. Earlier thirteen-check native
smoke receipts do not qualify that newer profile or the full native suite.
Native Alpha 2 qualification is **NOT READY**; no Alpha 2 version, tag or release
is created by these checks. Historical C032-SIGNAL-01 remains OPEN and still
blocks stronger stable/security claims. The published Alpha 1 tag/assets stay
unchanged; a later release needs new versioned artifacts and its own gates.

## Supervisor resource accounting continuation — 2026-10-29

The next internal addition starts from exact revision
`397d18e7726b9a75712eba36e6da07c424b24dde`, whose full eleven-gate
[Main](https://github.com/NolQuDev/NolQu-L/actions/runs/40882914399) and
[Dev](https://github.com/NolQuDev/NolQu-L/actions/runs/40882931172) receipts
were audited before further edits. Its 1,084 main markers, 129 MCP methods
and fifteen runner controls are the unchanged-source baseline for this work.

The private supervisor now collects optional waited-child CPU/RSS observations
after cleanup. Four added methods first produced six missing-field assertion
failures, then passed; all nineteen runner methods pass locally with
ResourceWarning treated as error. They cover real allocation, ordinary/signal
exit, waited grandchildren, isolation, interrupted cleanup and explicit accounting
failure. This is experimental host evidence, not a compiler semantic, memory
limit, native qualification or retrospective diagnosis. Exact-source full CI
is still required before integrating any addition; successful Linux observations
cannot stand in for the unrun native profile. The
[resource contract](../../tests/security/README.md#waited-child-resource-accounting)
defines units, scope and unavailable states. Canonical source/seed identities,
Alpha 1 release assets, VERSION and CHANNEL are preserved.

## Compiler and bootstrap

Machine Foundation, Stage 0, B0 and the bounded Core components have real
predecessor builds, artifacts and SHA-256 pins in
[`bootstrap/manifest.tsv`](../../bootstrap/manifest.tsv). The active source
frontend/backend are C0.32; the separate bounded emitter remains C0.25.
Full Compiler, formal self-hosting `nqlc`, and Verified `nqlc` remain
`NOT_IMPLEMENTED`. Component-generation equality is limited to its recorded
inputs and is not formal verified self-hosting.

The historical comparison-backend SIGKILL (`C032-SIGNAL-01`) remains OPEN:
later successful runs did not identify its sender or cause. Two older missing
metadata records (`C032-RETENTION-01`) remain PARTIAL. Preserved private logs
are not reconstructed or relabeled as new evidence.

## Linux qualification on 2026-10-27

Run [40496383463](https://github.com/NolQuDev/NolQu-L/actions/runs/40496383463)
tested commit `3a5d1e23c62ce02d1fee00ccdda2b8693ef8149d` on Ubuntu x86_64.

| Gate | Actual result |
| --- | --- |
| CI controls | PASS |
| Five real hard-link methods | PASS |
| `make -j1 test` | FAIL; 289 PASS markers before the CLI stopped |
| Complete MCP discovery | FAIL; 127 methods, 1 failure and 8 error records |
| Bounded runner controls | PASS |
| Android host controls | PASS on Linux; not an Android qualification |
| Finite assurance | PASS |
| Release metadata/files | FAIL |

The first executed run is FAILED. Its artifact retained the exact commands,
streams, generation receipts and dependency versions. Canonical input identity
was unchanged. Main stopped because a bare executable name was searched on
`PATH`; MCP rejected a changed host fixture pin and an absent optional design
document; the file gate also expected that removed document. Follow-up fixes
require their own exact-commit run. Passing targeted checks does not turn this
failed run into PASS.

Run [40499493109](https://github.com/NolQuDev/NolQu-L/actions/runs/40499493109)
tested the cleaned 397-file snapshot at
`f0c680251b2a25623444a43b371bfdaecdbff247`. Nine of ten command gates passed,
including publication controls/path checks, real hardlinks, all 127 MCP methods
and the nine release checks. Main still failed on three signal-cleanup subcases:
the outer host supervisor retained adopted zombies until the entire suite
finished. A real orphan-while-target-live reproducer failed before its wait-loop
repair, then all 12 runner controls passed. Full main still requires a new run
with that repair; neither failed run is reclassified.

Run [40502246740](https://github.com/NolQuDev/NolQu-L/actions/runs/40502246740)
subsequently qualified the Alpha source on `Dev` at
`13450398d8edb6fef081dad56d78eeb725d0f856`: all ten command gates exited zero.
The full main suite printed 1,083 PASS markers; complete MCP discovery ran
127 methods successfully. CI controls (11), publication controls (4), real
hard-link methods (5), runner controls (12), Android host controls on Linux (12),
finite assurance and nine release checks passed. Counts overlap and are not
a sum of unique tests. Canonical input identities were unchanged throughout.
The retained ZIP SHA-256 is
`ea207f3c6ffc0571fe0a9bb9e764a0eb3de73ec75fd9933cc65a29df1c2be009`.

This closes the current Linux host/CLI qualification failures for that source
tree. It does not qualify every Android filesystem capability, attribute the
historical SIGKILL, or promote Full Compiler/self-hosting/security maturity.

The same source tree was integrated into `Main` at
`f2562b6bd6ec4b29687bb5572e24fd59ecf9ab05`. Run
[40502990465](https://github.com/NolQuDev/NolQu-L/actions/runs/40502990465)
also passed all ten gates, with 1,083 main PASS markers and all 127 MCP methods.
Its canonical inputs were unchanged; retained streams match their recorded
lengths and SHA-256 identities. The ZIP SHA-256 is
`28dcf8e8769234ea9ef0e2ec38b7b69e129612c85a86baa72b2880834d47c88c`.

## Native Termux scope

Development uses Termux private storage. Actual hard-link creation is denied
on the tested Android host; Linux hard-link results do not erase that limit.
Native smoke completed 13 checks/32 invocations, and finite assurance completed
594 invocations. The evidence, smoke, descriptor, decoder and cleanup controls
cover their documented finite cases. The full native suite is not qualified.
No unsupported sanitizer, coverage percentage or exhaustive fuzz claim is made.

## Publication and release boundaries

Public changes belong in [CHANGELOG.md](CHANGELOG.md), implementation contracts
and this concise status record. Internal prompts, concept attachments, plans,
session reports, credentials and raw work evidence follow
[PUBLICATION.md](PUBLICATION.md). Removing them from a branch does not erase
earlier Git history. SBOM, artifact signing and formal provenance are
NOT IMPLEMENTED. Required full qualification and open signal attribution still
block stable/security-qualified promotion.
