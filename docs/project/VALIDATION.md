# Development validation status

Current metadata: `1.0.0-alpha.1`, channel `dev`. No tag, official release,
stable promotion, or whole-language security qualification is implied.

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
