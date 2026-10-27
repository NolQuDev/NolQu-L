# C0.31 Component Capacity And Generations

The C0.31 source/artifact hashes, counts and completed installation below are
retained historical evidence. Current frontend/backend source is
experimental C0.32; [NATIVE_OS.md](NATIVE_OS.md) defines its native additions and
measured execution gates and open assurance limits. Do not apply C0.31 B/C hashes to changed
C0.32 sources or infer fresh verification from either version label.

The following initial C0.32 checkpoint precedes the later diagnostic formatter
repair. Both full sources use one B0-compatible main with sixteen locals:
frontend 80300 bytes, tokens 17900, nodes 15739; backend 199852 bytes, tokens 47114,
nodes 40939. Their complete source transport remains NQAF/5 dialect4/profile1;
the compiler implementation itself needs no successor/native syntax. Actual
double B0 builds produced equal A1/A2 bytes for each component:

| Initial C0.32 checkpoint | Bytes | SHA-256 |
| --- | ---: | --- |
| frontend source | 80300 | `7bae219723806641efb9055747452930740f93d8929dbc701dec5bc91b07fbb3` |
| backend source | 199852 | `71473df97d7df5ce4cde89137813374ca139ac070ec3e4aab97747246196ae85` |
| A frontend | 124215 | `9da819d6ea3017d39135532f0b4c3f0cd3105d31e4450802302bb9422e2f5e5b` |
| A backend | 315593 | `303d2b21bcac54d4961acf451968f09a657a15b833a699ba368148f2dc43b65d` |
| B/C frontend | 6361360 | `65e2f7de291a0dd735424014d28def990cdeaa46697b5d196edda17c9f1a79bc` |
| B/C backend | 6475137 | `da2abbe63d97e2cfddfde798c791b44b9cc459b0295ed6df7de61a6a4495b0b8` |

The completed C0.32 standalone generation module passed six methods in 648.759s:
722 stage records, 275 checks, 475 artifacts and six component comparisons,
including 41 named oracle methods on each B/C pair, no skips. Receipt SHA-256:
`9d3349af18eb8226012d6019ba98f22bcd426971ef2788ed2bcfbc3b9fdccf23`;
the actual receipt is
`/tmp/nql-next-compiler-v7wdgsfr/task3-generations/test_actual_sources_build_and_rebuild-8i_fqk0g/receipt.json`.
Public canonical `nqlc --compiler-profile` compilation of each complete source
also matches its new B/C artifact. These observed results do not replace fresh
full main/MCP/release, protocol, combined-proof or whole-change acceptance.

All prior source/token/node, depth, arity, frame, ELF and B0 limits stay fixed.
Frozen C0.31 source fixtures reconstruct the old comparison pair through B0,
independent of the candidate installed seeds. The capacity/profile/generation
flags plus intended unsafe/argv/syscall flags require a complete fresh
identity-bound proof; Full Compiler/self-hosting/Verified remain false.

### Current C0.32 Post-Diagnostic Identity

The source-only C0R-008/009 formatter repair changes four emitted immediates;
old identities above remain historical. Current backend source is199908 bytes,
SHA-256 `bc230a170b8742a26b98b03d6cc36c5878a9a38c0dd4c4fbc0450b70eb64157f`.
Two B0 builds produce the same315593-byte selected backend,
SHA-256 `b169f9ee8890d306c080f299980c352bbabc5518052355dd0148a7878b9f51b1`.
Frontend source/selected/full hashes above remain unchanged.

Fresh installed SDK proof observes722 stages/275 checks, validates475 artifacts
and compares41 named oracles on both B/C pairs. The current6475137-byte full
backend B==C hash is
`c789a3442691dd4f51f51ecb594265ff7b106a45313b8f6e91c7ec233bd29f85`.
Both frontend and backend B/C executable files, exact source inputs, AST and
raw streams are separately retained at
`/tmp/nql-next-compiler-v7wdgsfr/current-generation-images/receipt.json`.
The public canonical CLI builds B; actual B components build C. Bounds, B0,
wire grammar of these compiler sources and success-path semantics remain fixed.

The original main1079 checkpoint predates the formatter repair. A fresh unchanged
post-formatter baseline now passes1079; the host evidence revision passes1080,
with every baseline label retained, fresh MCP/proof/assurance and unchanged compiler
source/pins. The [reliability report](../../../docs/project/VALIDATION.md)
distinguishes those receipts from the
[original session report](../../../docs/project/VALIDATION.md). The earlier
unexplained comparison-backend SIGKILL remains OPEN; component equality is not
stable/security qualification or Full Compiler/self-hosting promotion.

The rest of this document records the **completed C0.31 capacity milestone**,
not C0.32 final acceptance.

Status: COMPLETE for the experimental compiler-source capacity milestone;
coherently installed with complete pre/postinstallation gates VERIFIED.
Independent spec, quality and final whole-change reviews approved the installed
source/pin set and completed evidence. This
does not establish Full Compiler, public nqlc self-hosting or the later Verified
bootstrap stage.

This document records the public contracts, measured failures and artifact
identities. Detailed implementation notes and raw receipts remain internal.
Evidence for this
implementation is under
`/tmp/nql-c031-execution-20261014.SWSw0P/task6.bqAEOO`.

## Exact Sources And Provenance

Both complete C0.31 `.nql` files were snapshotted and compiled without source
rewriting, splitting, imports, new helper functions or predecessor features.
Each remains a B0-compatible flat `fn main()` with sixteen locals. The canonical
path remains Machine -> Stage0 -> B0 -> C0, targeting syscall-only x86_64 Linux
ELF64. Host Python launches processes, copies their actual bytes, frames NQSC,
decodes/checks NQAF/ELF and compares hashes. It does not supply compiler semantics
or successful artifact bytes. No host assembler/linker produces these builds.

| Historical C0.31 input | Source bytes | SHA-256 |
| --- | ---: | --- |
| `frontend.nql` | 63904 | `f5ede77065a06498df9dfb6add43cf016d3eb38e8081dd44fa8a37d904fb6725` |
| `backend.nql` | 165737 | `1f90c6fcd92c076caf4897151e9c62551e9d77f5fd75d225ac033bb9df47d6ca` |

The installed B0 is `bebc7b23c8395ee312580b067644c3eb7556494db024dfd592404165a5336768`.
Its reviewed private stderr-failure state prevents a second diagnostic if
cleanup also fails. Historical c658/183b/7c9f candidates remain retained;
the repair changes the A runtime prefix, not either NolQu-L source or B/C code.
It builds each component twice with explicit `--compiler-profile`:

```text
B0 + exact full sources -> A1 / A2 (require identical component bytes)
A frontend/backend + NQSC-framed same full sources -> B frontend/backend
B frontend/backend + NQSC-framed same full sources -> C frontend/backend
Require B frontend == C frontend and B backend == C backend.
Execute A, B and C on the common corpus; run the named broad oracles on B/C.
```

A is B0-generated, B/C are C0-generated; A==B is not required. The harness never
normalizes binaries. Each comparison records both actual sizes/hashes and the
first differing zero-based byte offset, including prefix-only divergence.
Frozen B0.7r/C0.30 sources are reconstructed through pinned Stage0/B0 by
`c031_support.build_predecessors`, verified against the immutable hash ledger,
and archived in each final generation run. Old successful scalar/control/runtime
AST and ELF goldens remain independent parity oracles.

## Measured Workload And Costs

For the source identities above, actual NQAF/5 wire observations are:

| Source | Tokens excluding EOF | Nodes | Wire bytes | Dialect / profile |
| --- | ---: | ---: | ---: | --- |
| frontend | 14212 | 12607 | 467360 | 4 / 1 |
| backend | 38947 | 33773 | 1246505 | 4 / 1 |

Installed A and fresh B/C sizes/hashes verified by prevalidation:

| Component | Bytes | SHA-256 |
| --- | ---: | --- |
| A frontend | 99256 | `46aaa86e226c54d1b9429c25696699bc2d4747d84b12f79ac6b0c21971cbfa7c` |
| A backend | 261451 | `af8820eaff28b467dd148b2a48d966b775c4f170bb19fe223bc8a77c7b3559f9` |
| B/C frontend | 6349683 | `e0c698ab1ad259bb0441beddfafad90e42c75c16df819e21c41c76c55fd9c2cd` |
| B/C backend | 6445930 | `72ed5667796fde9503101201418d6b8eaa2b89b6094979915ccdc83f7b704373` |

Source copies cost their complete byte lengths; explicit transport adds 16 bytes.
NQAF/5 uses `32 + source_bytes + 32*node_count`, maximum 2,359,328 bytes. The
compiler profile explicitly maps 16,777,216 RW/NX bytes; this bound is not measured
RSS. Default program byte storage remains 65,536, independently of source width.
In C0-generated programs, only resolved byte/stream intrinsics allocate the
selected program arena; the B0 compiler bridge has its separate documented profile.

Source/token/node limits remain 262144/65536/65536. Frames remain 4096 bytes/512
i64 slots; arity is 6, control depth 64 and user call depth 64. Wide ELF cap remains
8,388,608 bytes; code ends before 0x600000, helpers occupy [0x600000,0x604000), and
diagnostic data [0x604000,0x800000). Internal emitted gaps are deterministic zero
bytes, not removed before comparison. B0 source/output/dynamic-byte-access limits
remain 327680/589824/5376. No capacity increase was needed for this dependency fix.

The runner retains distinct source snapshots, raw producer streams, generated
artifact copies and receipts, so temporary/evidence disk cost exceeds one image.
No peak-RSS, savings, throughput or leak percentage is claimed. Actual elapsed
times belong to their command receipts and are not optimization comparisons.

## Execution And Failure Coverage

`test_c0_component_generations.py` runs the exact workload and common corpus.
The direct checks include all three existing scalar/control/runtime byte-golden
groups, concrete execution, wide spans/nodes, profile/default bounds, streams,
MAX/MIN and long leading zeros, MAX+1/huge-invalid literal diagnostics, checked
program arithmetic, and malformed legacy/wide framing/anchors.

Each B/C pair additionally runs 18 unchanged candidate-aware named methods from
the existing frontend/backend/profile/runtime suites. They cover version/profile/
dialect/reserved/length mutations; IDs, graph ownership and statement order;
long identifiers and high/intrinsic IDs; legacy predecessor parity; fragmented
headers and streams, EOF and short reads without EOF; bad descriptors and empty
end ranges. The exact selector list is `GENERATION_ORACLES`; each oracle receipt
binds the actual B/C executable hashes, test/helper identities, command, selected
environment, raw streams, status, timeout and cleanup. Missing, failed, timed-out
or skipped oracles cannot produce overall verification.

The final standalone run passes all six top-level tests and all 215 recorded
checks: 71 direct checks on each of A/B/C plus one complete 18-method oracle
subprocess on each of B/C. Its outer receipt is
`component-generations-final-green.json`, SHA-256
`e0b4e5f9598eba68f4e44dbcb7a88c77028ee453fbd330facca819426f841589`.
Its detailed generation receipt is
`test_actual_sources_build_and_rebuild-dhxfjxcn/receipt.json`, SHA-256
`4741f1124d5c8352f93d65481a9a592e60532dcfa662040e4970accc46586828`.

The original C0-built backend trapped on a valid MAX literal in its own decimal
accumulator, and trapped on oversized literals instead of returning C0B-005.
Measured 26 B/C failures were returned to the controller before the scoped fix.
The [backend note](BACKEND.md) describes operand guards before eager arithmetic;
the original `4c46` candidate and RED receipts remain historical evidence.
Valid MIN is `(0-9223372036854775807-1)`, not unary negative-literal syntax.
Invalid decimals require located C0B-005/1 and no ELF; malformed literal spelling
requires C0B-006/1. Valid compiled expressions that overflow at execution retain
C0R-001/70. Resource/descriptor errors retain 74.

Integrity tests reject changed source/test identities, truncated/mutated/extended
generated executables, and actual producers exiting 74 with partial or complete
ELF stdout. QEMU probes verify current-image syscall instructions and registers;
one writes eight real bytes then receives an injected error, another completes
output then receives injected munmap failure. These are fault-injection results,
not natural kernel failures. Guest child/socket cleanup is checked; fatal signals
and skipped munmap rely on final OS reclamation, not an asserted userspace release.

No nonzero/partial output is accepted or chmodded as a successful artifact.
Inputs and artifacts are rehashed; receipts are evidence, never a persistent
success cache. Each invocation builds fresh A/B/C. Temporary executables,
predecessor builds, oracle workspaces and owned children/sockets are cleaned on
failure and success; logs and nonexecutable evidence copies are retained when
`C031_WORK` is supplied. Generation and oracle processes have 1200-second bounds;
large individual boundary checks use 120 seconds. A timeout is a failure.

Oracle scratch directories use a unique private `c031-oracle-*` directory
directly under `/tmp`, keeping nested Guest Unix-socket paths short. Long evidence
paths are used for receipts/artifact archives, not the debugger socket workspace.
An earlier expanded run failed on AF_UNIX path length; that failed receipt is
retained and is not compiler-regression evidence.

## Commands And Remaining Gates

The installed coherent set runs directly, without test-only candidate overrides:

```bash
python3 tests/bootstrap/test_c0_component_generations.py -v
ROOT_DIR="$PWD" bash tests/bootstrap/c0_capacity.sh
```

Each invocation creates unique per-test evidence directories under `C031_WORK`;
see the report for exact candidate paths and observed command receipts. The shell gate prints
`PASS c0-capacity` only after capacity frontend/backend/profile subprocesses
exit 0, and `PASS c0-component-generations` only after the complete standalone
generation/integrity module exits 0. Production wrapper pin checks are unchanged.

The shell gate passed 18 frontend-capacity, 28 backend-capacity, 20 compiler-profile
and 6 generation/integrity tests. Its fresh generation run again passed all 215
checks and both 18-method B/C oracle subprocesses. Terminal receipt
`capacity-gate-final-green.json` has SHA-256
`732a09b59ba6ba87b65abba63e4a01b49b5e773a21668f6a88e6496e24e764b5`;
the report records exact streams, elapsed times and the second generation receipt.

The preceding shell-gate receipt records the historical Task 6 candidate run.
Current installed identities and completed prevalidation are recorded below.
Actual compiler failure returns to its owning task; no host fallback, source
reduction, skipped check or automatic capacity expansion is permitted. Rollback
must restore the matching complete source/script/metadata/pin set.

## Canonical Installation Evidence

The completed fresh prevalidation has eight commands, all exit0/no timeout:
protocol discovery, full MCP, full `make -k test`, B0 profile, source pipeline,
release checks, seven bootstrap hashes and the real combined canonical probe.
Main passed1076 gates with all1073 baseline names/multiplicities retained;
MCP46, B0profile16, pipeline27 and release9 passed without skips. The fresh
probe verified215 checks/554 stage records, six equal component comparisons and
18 named oracle methods on each of B/C. Expected negative cases retain their
required nonzero status; not every individual stage is supposed to exit0.

Receipt: `/tmp/nql-c031-execution-20261014.SWSw0P/validation-task7-pre-v2-20261023-receipts.json`,
SHA-256 `89d0eac846519c3118d73ee595cbf21830356d438ae91bd50e6d8e08b4d3850c`.
Controller audit SHA-256
`0dae6ae9b0acd3edfc342ce1907b97deed685ec9df2a9ce2bdf324b9fddfb60d`;
fresh combined probe SHA-256
`e3486d81db5cf923b6591eeed9c01c3ac9f4554912d0c6892707ae3025926523`.
All three independent prepromotion reviews approved the reviewed set. Canonical
materializers then rebuilt B0 through Stage0 and both A components through B0,
checking each expected pin before atomic publication. Only those three seeds
and hash files changed; all four other seed/pin pairs remain unchanged.
The exact eight promoted-phase commands also completed successfully below.

The actual installed source wrapper was also invoked from `/tmp` on both
complete sources, with no candidate selection overrides. Both commands exited0
and produced the B frontend/backend identities in the table above. Receipt and
actual executables: `/tmp/nql-c031-execution-20261014.SWSw0P/installed-direct-selfcompile/`.
This directly exercises the usable installed path, not just a staged test copy.

Existing frontend/backend probes advertise the C0.31 source/probe contract:
262144 source bytes, 65536 tokens/nodes, NQAF/1..5, default program arena 65536
and explicit compiler-profile arena 16777216. These metadata values do not
verify a deployed artifact. `capacity_verified`, `compiler_profile_verified`
and `component_generation_verified` remain false unless a fresh complete run
passes the real frontend, backend and capacity gates. Full Compiler and
self-hosting flags remain false, with later stages NOT_IMPLEMENTED.

The consumer checks the reviewed generation test/gate identities, exact required
stage/check/artifact/comparison sets, all B/C oracle selectors and outcomes,
before/after source/script/seed identities, retained artifact bytes and raw
stream hashes. Matching filenames, version comments, equal status codes or an
ok-only mock are insufficient. Display truncation never supplies parsed proof;
the raw files are inspected independently before cleanup. Missing, changed,
partial, timed-out or skipped evidence fails closed.

One combined invocation can share its fresh proof between the two components;
there is no persistent success cache. A subsequent call executes gates again.
The aggregate deadline is 2400 seconds, with a private Linux child subreaper for
owned descendant cleanup, including oracle processes in separate sessions.
Cooperative interruption precedes bounded escalation. Metadata resources do
not compile or claim fresh verification. Compact gate logs and generation
receipt metadata remain in `.nolqu-mcp/evidence`; large invocation scratch is
removed. Retained logs are never consumed as a shortcut to later success.

`bootstrap/manifest.tsv` remains byte-identical: its existing stage/artifact/gate
paths still describe this installation; it has no version/hash column. Full
Compiler/self-hosting/Verified rows remain NOT_IMPLEMENTED. A complete original
C0.30 rollback bundle was fresh-extracted and checked (225 entries, file
bytes/modes and symlink targets),
including the public docs and design/plan status. Receipt
`/tmp/nql-c031-execution-20261014.SWSw0P/task7-c030-v3-rollback.json`, SHA-256
`ce0620722ce35e66612b086aa5e265378f147aa0a0b2232e2e062d88bb691bda`.
No rollback was performed. Three old seeds mixed with new sources/scripts are
not a coherent rollback. Public VERSION1.0.2a1 and CHANNELdev are unchanged;
public `nqlc` remains R0/NASM, not a canonical Full Compiler replacement.

## Verified Postinstallation Run

The promoted-phase runner first checked the actual official seed bytes against
the reviewed candidates, then copied the installed tree without any provisional
staging. All eight commands again exited0, with no timeout, missing gate or skip.
Both before/after input and pin guards are true. Main1076 has the exact same
PASS-name multiset as prevalidation, retaining all1073 baseline entries. MCP46,
B0profile16, pipeline27, release9 and all7 hash pairs pass. The fresh unrelated-
cwd protocol still exposes all120 exact input schemas,8 resources and5 prompts.

Receipt: `/tmp/nql-c031-execution-20261014.SWSw0P/validation-task7-post-20261023-receipts.json`,
SHA-256 `98350a556a1ace5953970aa91f69bbd82800f6830ae72ca7f3b07ca26de5868a`.
Controller audit SHA-256
`87864ad112abd1c522e24d6e5769601c64d8c1cbafcf1ac913e6a1a2b2ddc42b`;
fresh combined probe SHA-256
`3bb1506c782e167f6ad19ea55fc7963bd0b06b81db9aa91ce5aba391909f66b7`.
Its generation receipt is
`4fcb516db9e145374d3a32e83617ec4dd3ec6f4419f34ff3e85dce59d7c3deb5`.
The new proof again verifies215 checks/554 stages, six comparisons and both
18-method B/C oracle runs. A1/A2 and B/C identities match the table above.
All three real gates report completed cleanup and the temporary workspace was
removed; compact evidence remains. No persistent success cache was consumed.

These are repeated correctness checks, not a performance benchmark. Source-
located faults, range checks and controlled cleanup are tested guarantees, not
a general leak proof, native-kernel fault proof, full ownership checker or all
Assembly-Level target capabilities. The existing nonfatal MCP Pydantic lifespan
warning remains visible in the logs. No public release/version change is made.

## Final Milestone Closure

The independent final whole-change review, retained with the internal records,
approved C0.31 capacity and Task 7 closure, with no actionable findings remaining.
Its report SHA-256 is
`d95f1eccbd3b9ca655c500830bba631bde71ec41df539e24018d3af49924d79b`.
It checked completed promoted receipts, actual installed bytes, direct wrapper
use, coherent rollback and the final documentation delta. Six focused MCP
authority/resource/metadata tests and all nine release checks also passed after
the documentation updates; the ledger records their bound raw receipts.

All seven implementation tasks are complete within this bounded contract.
This closure does not replace the public R0/NASM CLI or implement the Full
Compiler, full language self-hosting, later Verified stage, or Assembly-Level
design targets. The next separate compiler objective is the canonical Full
Compiler/public CLI transition with its own acceptance and compatibility gates.
