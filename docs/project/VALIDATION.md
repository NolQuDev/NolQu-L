# Development validation status

Current metadata: `1.0.0-alpha.1`, channel `dev`.
[The first Alpha prerelease](https://github.com/NolQuDev/NolQu-L/releases/tag/v1.0.0-alpha.1)
was published on 2026-10-29 from
`26ad9b80b5a3164a20854ce3e3798642fba3f15e`. This does not promote Stable,
Full Compiler, formal self-hosting or whole-language security qualification.

## Host Runner Limit Contract

The host-only `BoundedRunner` validates its policy before creating an evidence
directory. `timeout` and `budget` must be finite positive builtin integers or
floats; booleans, NaN, infinities and unrepresentable time integers are rejected.
`output_limit` must be a positive builtin integer and `max_input` a nonnegative
builtin integer. Invalid policies raise a domain-specific `ValueError`; they
are not coerced, clamped or replaced with defaults. Zero permitted input and
fractional positive seconds remain supported.

The runner controls exercise invalid policy rejection without filesystem
effects, actual binary/status behavior under valid limits, and the existing
timeout, signal, cancellation, cleanup and retained-evidence paths. These are
host reliability checks, not a memory sandbox, canonical compiler change or
attribution of the historical `C032-SIGNAL-01`, which remains OPEN.

## C0.37 Checked Shift Qualification Contract

[SHIFTS.md](../../bootstrap/compiler/c0/SHIFTS.md) defines SH01..SH06: eager
full64-bit values, checked count0..63, signed right shift, independent /10
validation and prior-source byte compatibility. The18-method scoped shift
suite, actual B/C named shift oracle and exact source/permission inventories
are required on the matched pair. Deliberately incorrect shift/count variants
must fail independent assertions. Metadata alone cannot qualify shifts.
Fresh Native receipts, full Linux gates and independent HIGH-risk review are
required; earlier C0.36 counts below remain historical. This contract records
requirements, not unexecuted test results or a stable/security qualification.

## C0.36 Short-Circuit Qualification Contract

[SHORT_CIRCUIT.md](../../bootstrap/compiler/c0/SHORT_CIRCUIT.md) defines
normalized i64 truth, conditional RHS effects, static validation of both
operands, exact keyword migration, NQAF/9 dialect8, machine cost and
SC01..SC06. All earlier checks remain required. The new scoped logical suite,
its complete marker and an additional named actual B/C oracle are required
proof inputs; metadata-only reads retain `short_circuit_verified=false`.
Review, exact-source Linux CI and actual untraced Native proof must be reported
separately. Absent/skipped/truncated tests or stale identities fail closed.
No full-language Safety, Stable, Full Compiler or formal self-hosting promotion
is implied. Current capacity, ABI, version and historical open incidents remain.

An earlier C0.36 cohort passed all eleven Linux gates: 1,090 main PASS markers
retained all 1,089 baseline markers; 140 MCP methods passed. Its separate Native
probe completed in 1,681.0 seconds with TracerPid 0 at both ends. Review then
identified two proof gaps: a shortened test source could define its own suite
count, and logical assertions could themselves skip oracle checks. Those
successful runs remain execution evidence, not closure of the discovered gaps.
The corrected gate requires the exact sixteen-method inventory. The named B/C
oracle now uses independent checks, including selected output and `1 and 0`;
a deliberate always-skip AND mutation must fail in both profiles. The changed
proof inputs require fresh Linux and Native qualification before integration.

The component receipt records 722 stages, 275 checks, 475 artifacts and six
comparisons, with 45 ordered named methods on each B/C pair. Each qualification
must check all 2,641 recorded artifact/stream files and 48 source identities.
These parent counts do not count every inner temporary oracle image separately.

Five alternating samples on the retained 83,849-byte C0.35 frontend source show
Native backend median 1.443719 to 1.589191 seconds (+10.08%); its AST and ELF
remain byte-identical. Independent compiler review accepted this explicit
compile-time cost for the bounded validation/emission work. This is one measured
workload, with no runtime speedup or peak-memory claim.

A separate deterministic seed0xC036 campaign compares72 truth/effect cases
across two profiles and logical/explicit-if forms:72 raw streams and6 ELF
pairs match across PRoot and Native. Coverage is not measured; no exhaustive
fuzzing, applicable NolQu-L sanitizer or whole-language Safety claim is made.
The current scope stays experimental; historical C032-SIGNAL-01 remains OPEN.

## C0.35 Bitwise Qualification Contract

The experimental pair adds signed i64 `&`, `^`, `|` and unary `~` through
independent NQAF/8 validation. [BITWISE.md](../../bootstrap/compiler/c0/BITWISE.md)
defines precedence, eager effects, NEGATE-only minimum permission, machine cost,
threat boundaries and BW01..BW06 test mapping. Existing Alpha metadata, ABI,
bootstrap topology and capacity bounds remain unchanged.

Qualification requires all nine backend suites, including twelve bitwise
methods, and 44 ordered named oracles on each actual B/C pair. Missing bitwise
markers, truncated/skipped suites, omitted oracles or changed inputs fail
closed; metadata-only reads keep `bitwise_verified=false`. The finite integer
oracle uses seed `0xC035` and compares 82 full-width values per profile inside
generated programs. Independent raw-call packets and exact instruction
sequences supplement malformed-wire tests. Sixteen retained C0.34 unary
AST/ELF comparisons cover both profiles separately from older corpus hashes.

Complete exact-source Linux CI and actual untraced Native proof must be
reported separately. A passing compiler gate does not qualify the whole
language's Safety, Full Compiler, self-hosting or Stable. The historical
C032-SIGNAL-01 remains OPEN; historical retention is PARTIAL and denied Native
real-hardlink creation still limits the full Native MCP suite. This contract
adds no release or replacement of previously published artifacts.

## C0.34 Validation Scope

The experimental component pair adds checked prefix negation and NQAF/7. Its
semantics, independent literal ownership, threat boundaries, test mapping and
paired upgrade are in [UNARY_NEGATION.md](../../bootstrap/compiler/c0/UNARY_NEGATION.md).
All eleven scoped unary methods passed in PRoot and actual Native Termux; the
Native receipt reports TracerPid 0 at both ends. Independent review added 72
finite checks, including malformed wire, a 65536-node packet and slot limits,
without a concrete correctness finding. Separate B0 rebuilds in both execution
modes produced identical component bytes. These scoped results are complemented by the complete proof below.

The complete proof requires all eight backend suites, including eleven unary
methods, and 43 named oracles for each actual B/C component pair. Missing unary
markers, stale counts or omitted oracles fail closed. The old invalid `return -1`
fixture is now a positive unary case in both profiles; malformed `return -` stays
negative. Candidate wrong-code caused by confusing call arity with literal tags
was reproduced, repaired and covered before publication. Failed candidates and
streams remain private evidence. C0.33 is the retained baseline, not evidence
for the new source/pins. No release/version change or Stable promotion occurs;
C032-SIGNAL-01 remains OPEN and historical retention remains PARTIAL.

### Complete C0.34 Compiler Qualification

Compiler-bearing revision `cb47007b45e18aa477a33bff3671eb708abde853` passed
all eleven exact-source Linux gates on
[push](https://github.com/NolQuDev/NolQu-L/actions/runs/41355788389) and
[PR](https://github.com/NolQuDev/NolQu-L/actions/runs/41355794471). Each archive
records 1,088 main PASS markers, retaining all 1,087 C0.33 baseline markers,
135 MCP methods, 26 runner controls, 20 Android controls on Linux, 19 release
controls and six real-hardlink methods. The existing finite Linux assurance
profile also passes 15 checks, 326 invocations and 96 oracle comparisons.
These overlapping counts are not summed as unique tests.

The original actual Native job completed exit 0 in 1,304 seconds with all three
component gates passing. The original validator accepted 722 stages, 275 checks,
475 artifacts, six equal comparisons and 43 named oracle methods per B/C pair.
All 2,641 raw files and 46 bound input identities were checked; TracerPid was 0
at both ends. An MCP transport error near 1,200 seconds did not stop that job;
its actual final bridge receipt and streams were recovered without rerunning
gates. Full Compiler and formal self-hosting flags remain false.

A separate deterministic unary campaign (seed `0xC034`, 300-second overall
run budget, 20-second individual invocation timeout) passes 180 checks and
396 invocations in each of PRoot and actual Native Termux. It covers 54 defined
programs in both runtime profiles and source/wire rejection controls. All 1,188
streams and 108 generated ELF pairs match byte-for-byte across modes. The six
component comparison identities also match Linux and Native. This is finite
mutation/differential evidence without coverage instrumentation. Installed CLI
checks pass in both modes with an identical output ELF.

Independent scoped reviews found no concrete remaining issue: compiler core
72 checks; host proof consumer nine methods, 51 boundary probes and three
negative-test sensitivity mutations. Their scope does not establish formal
absence of bugs or diagnose the historical signal incident. Documentation-only
follow-up qualification is tracked on [Testing](https://github.com/NolQuDev/NolQu-L/tree/Testing);
its compiler/proof input bytes remain those of the revision above.

## Retained C0.33 Validation Scope

The preceding experimental component pair adds structural return analysis; its
contract, required gates, compatibility boundary and test mapping are in
[RETURN_FLOW.md](../../bootstrap/compiler/c0/RETURN_FLOW.md). Nine scoped
return-flow methods have passed in PRoot and untraced Native Termux, with
legacy AST/ELF corpus parity. Exact-revision qualification is tracked in
[PR #8](https://github.com/NolQuDev/NolQu-L/pull/8); the retained C0.32 baseline
below does not qualify changed C0.33 component bytes.

The original Native negative fixture requiring a redundant outer return after
an unsafe body's direct return is migrated to positive tests in both profiles;
an incomplete unsafe-body path remains rejected. The MCP capacity consumer also
requires the actual 29-method suite, with a negative control for the stale
28-method count. Failed first-candidate logs remain evidence. These repairs do
not close the historical signal incident or reconstruct missing old artifacts.

The complete Native component run subsequently passed its executable tests but
failed proof consumption because four original machine-trace JSON files had
mode 0600 under the host's private umask. The exporter now sets 0644 explicitly;
an actual two-profile mmap test fails before this repair and passes afterward
in Native Termux and PRoot. The regression creates traces under umask 077 and
restores the enclosing mask. The consumer's mode/identity contract is unchanged;
the failed proof remains evidence. PR #8 tracks qualification of the repaired
exporter alongside the component pair.

## Retained C0.32 Baseline — 2026-11-01

Source revision `75b2309f570530adfd9e62ddb6b33431581a4a3c` on `Testing`
completed exact-source Linux qualification on both
[push](https://github.com/NolQuDev/NolQu-L/actions/runs/41276651835) and
[PR](https://github.com/NolQuDev/NolQu-L/actions/runs/41276654513).
All eleven gates passed: 1,086 main PASS markers, 135 MCP methods, twenty-six
runner controls, twenty Android host controls on Linux, nineteen release
controls and six real hard-link methods. Actual component generations retained
722 stages, 275 checks, 475 artifact records and six equality comparisons.
Counts overlap and are not a unique-test sum. The retained push artifact ZIP
SHA-256 is `614a3de304755df8c3da15631731eb0ba9b0d82c492d2c8b6693e9098f468930`.

Before this documentation update, all 410 selected public paths, executable
modes and symlink target bytes matched that revision. A freshly prepared
schema-2 bundle matching the Linux profile then ran sequentially in both local
execution modes:

| Execution environment | Actual finite-profile result | Native Termux status |
| --- | --- | --- |
| Fedora Python/QEMU in PRoot, Android aarch64 | 15 checks, 326 invocations, 96 oracle matches, both sensitivity detections; exit 0 | Traced; separate PRoot evidence |
| Native Termux Python/QEMU, Android aarch64 | 15 checks, 326 invocations, 96 oracle matches, both sensitivity detections; exit 0 | Untraced at both snapshots; finite profile PASS |

The Native profile and its terminal-bridge receipt each record `TracerPid 0`
before and after execution. The PRoot caller remains traced at both snapshots.
The two profiles' 326 corresponding exit codes, 978 input/stdout/stderr streams
and 107 generated ELF files matched byte-for-byte, using identity audits and
direct 128 KiB chunk comparison. All retained streams and completed supervisor
controls were checked; waited-child CPU/RSS observations were available for
every invocation in each profile. These are host observations, not guest memory
bounds, leak proof, signal attribution or a controlled performance comparison.

The bundle manifest SHA-256 is
`5e00d53841b63644d97a3c1875a474a0c0ba7fc894683e9edcfdd4b226a7523a`;
the 48-case corpus SHA-256 is
`8fd66ecef1738a31044b39ed03926271a68cabfd49e9008294c81906608def9d`.
Only the bounded host runner differs from the earlier copied bundle below;
its compiler seed pins are unchanged. Each run retained the existing 600-second
profile budget, 15-second invocation bound, 8 MiB per stream and 3 MiB input bound.

This closes the earlier NOT RUN gap for this finite Native profile. Full Native
qualification remains blocked: the complete MCP run has 134 passing methods
out of 135, with four error subcases in one method because Android denies real
hard-link creation. Linux's passing real-hardlink gate does not remove that
host limit. Historical C032-SIGNAL-01 remains OPEN and C032-RETENTION-01 remains
PARTIAL; later passing runs do not reconstruct missing evidence or identify
the original signal's sender/cause. No compiler source/seed/pin, VERSION,
CHANNEL, published release asset or bootstrap stage is changed by this update.

## Earlier verification checkpoint — 2026-10-30

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
The 2026-11-01 Native smoke+differential profile completed 15 checks/326
invocations and 96 oracle matches. Earlier Native smoke completed 13 checks/32
invocations, and finite assurance completed 594 invocations at its recorded
checkpoint. The evidence, smoke, descriptor, decoder and cleanup controls cover
their documented finite cases. The full native suite is not qualified.
No unsupported sanitizer, coverage percentage or exhaustive fuzz claim is made.

## Publication and release boundaries

Public changes belong in [CHANGELOG.md](CHANGELOG.md), implementation contracts
and this concise status record. Internal prompts, concept attachments, plans,
session reports, credentials and raw work evidence follow
[PUBLICATION.md](PUBLICATION.md). Removing them from a branch does not erase
earlier Git history. SBOM, artifact signing and formal provenance are
NOT IMPLEMENTED. Required full qualification and open signal attribution still
block stable/security-qualified promotion.
