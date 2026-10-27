# C0 Byte And Stream Runtime

## C0.32: Native Arguments And Explicit Raw Operations

The current candidate adds `arg_count()` and checked byte-preserving
`arg_copy(index,offset,capacity)`, plus unsafe `byte_address(offset,count)` and
`syscall6(number,frame_offset)`. [NATIVE_OS.md](NATIVE_OS.md) is their exact
contract: lexical invariant/permission, NQAF/6 source correspondence, frame ABI,
diagnostics, helper offsets and scoped evidence. The monolithic C0.25 remains
unchanged; final main/MCP/combined-proof execution gates pass. An earlier
unexplained comparison-backend SIGKILL remains OPEN; stable/security readiness
is PARTIAL. See the current [assurance profile](../../../tests/security/README.md).
The full-main result predates the later four-immediate C0R-008/009 formatter
repair. Post-repair canonical/MCP/public/assurance gates pass within the
[session report's scope](../../../docs/project/VALIDATION.md);
post-repair full main was not rerun.

Arg-count alone needs no byte arena. The other new operations use the existing
64 KiB default or explicit 16 MiB RW/NX profile, without increasing any bound.
Copy validates destination before index, scans through NUL before any copy and
reports C0R-008/70 for an invalid index or C0R-009/74 for insufficient positive
capacity. Zero/negative capacity and invalid address/frame spans retain
C0R-004/70. Pointer exposure still requires unsafe caller reasoning about all
later kernel effects; checked spans are not lifetime or ownership validation.

The raw helper reads six little-endian words from a checked 48-byte span into
rdi/rsi/rdx/r10/r8/r9, passes the number in rax and returns raw rax. It performs
one syscall even for zero count, with no errno conversion or retry. Existing
fixed stream helpers below retain their complete-write/EINTR and empty-range
behavior; these are distinct interfaces. The native source utility handles
read/write EINTR/partial progress itself and closes acquired descriptors once,
including fd0. See the [example guide](../../../examples/canonical/README.md).

Only explicit raw caller code can now open arbitrary descriptors; the compiler
process still consumes fd0 and emits fd1/fd2. There is no general allocator or
full Safety guarantee. Returning helpers preserve rbp/rbx/r12-r15, and controlled
runtime failures retain mapped cleanup/failed-stderr behavior. Arbitrary raw
syscalls and fatal signals cannot promise universal resource release.

## C0.31: Explicit Mapped Profile

The completed Task 7 MCP contract exposes default byte capacity 65536 and
compiler-profile capacity 16777216 separately. `compiler_profile_verified`
requires fresh complete evidence; source width, version metadata and prior
logs do not enable it. The C0.31 runtime/ABI and source identities below are
historical evidence; the native additions above supersede their capability scope.
[CAPACITY.md](CAPACITY.md) records the integration boundary.

The coherent C0.31 seeds and sources implement the mapped-runtime part of the
[binding capacity design](CAPACITY.md).
Fresh prevalidation and the same final postinstallation checks passed;
CAPACITY.md records actual receipts. Source presence alone does not establish
component-generation or self-hosting claims. Candidate-stage notes below are
historical and are superseded by the current installation evidence.
The following C0.30 sections retain the historical default runtime contract.

NQAF/5 storage width and runtime profile are independent. Profile 0 keeps the
65,536-byte zeroed stack arena and predecessor executable bytes. Explicit profile
1 selects a 16,777,216-byte anonymous/private Linux mapping with read/write
permissions and no execute permission, only after exact user-first resolution
finds an arena-using intrinsic. A shadowing user function wins even on wrong
arity; no intrinsic fallback or generated arena allocation follows that error.
The fixed stream helpers and compiler open no descriptors and expose no general
allocator; C0.32 raw caller code has the separate explicit effects above.

The five intrinsic results, checked arithmetic, left-to-right argument order,
4,096-byte function frames and 64-function depth contract are unchanged.
Byte indices are nonnegative and below the selected capacity. Ranges check the
offset first, then `count <= capacity - offset`, before pointer arithmetic;
nonnegative empty ranges at capacity return zero without touching a descriptor.
Stores retain only the low eight bits. Reads retry EINTR and preserve one read's
short count/EOF. Writes complete partial results, retry EINTR and fail on zero
progress. Successful helpers preserve `rbp`, `rbx`, and `r12` through `r15`.

### Mapped Ownership And Native State

Mapped startup at ELF offset `0x600600` reserves 32 aligned stack bytes above
the existing process frame and every user frame. Preserved `r14` points to four
private u64 words: mapping base at +0, acquired flag at +8, saved exit status at
+16, and sticky failed-stderr flag at +24. These words consume no user slots.
The maximum 512-slot user frame still spans `[rbp-4096, rbp)` below that block.
`rbx` holds the shared mapping base on all successful user/helper paths; fatal
diagnostics may reuse `ebx`, so cleanup loads the base from private state.
Profile-specific fatal suffix lengths use `r10d`, preserving `r14`.

The mapping is acquired before entering the existing signal setup/main path.
Failed mmap never sets acquired, accesses the mapping or attempts munmap.
Normal main return, arithmetic/depth/range errors, stream errors, signal-setup
errors and broken stderr all reach cleanup. The requested exit status is saved
before syscalls. Cleanup clears acquired before attempting exactly one munmap;
diagnostics consuming arena bytes finish before release. Fatal signals rely on
OS reclamation and have no userspace cleanup guarantee.

Failed mmap/munmap reports a fixed, file-backed ELF diagnostic at `input:1:1`
with C0R-007, a cause/remedy, and exit 74. A failed diagnostic or error_write
marks stderr broken and still cleans up, without recursive diagnostics. Failed
munmap does not retry; its diagnostic cannot trigger another release. If stderr
was already broken, teardown failure exits 74 without attempting another write.
Located arithmetic/range failures retain 70; located stream failures retain 74.

New helpers occupy `[0x600600,0x600782)` inside the binding helper region;
resource text occupies `[0x604000,0x6040c7)` before the existing runtime data.
No interpreter, dynamic dependency, writable executable load or executable stack
is introduced. The actual mmap syscall requests protection 3 and flags 0x22.
The compiler remains one B0-compatible flat function with sixteen locals.

The test-only `c031_debugger.Guest` injects verified syscall returns and executes
real short writes while poisoning `rcx`/`r11`. Such evidence is fault injection,
not naturally occurring allocation failures or proof about native signal delivery.
The shared debugger is unchanged. Task 5 owns source-wrapper profile framing;
Task 6 owns actual component generations; Task 7 owns coherent seed promotion.

## Historical C0.30 Runtime

**Spec:** `NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md` and `NolQu-LConcept.docx`;
continuation of the measured C0.29
runtime blocker. This architectural work unit extends the existing indexed AST
pipeline, not the legacy R0 compiler or the C0.25 bounded emitter.

## Classification And Decision

Requested mode: major development. Actual class: experimental compiler feature.
Risk: high. Stages: parser, AST validation, symbol resolution, machine emission,
runtime, bootstrap pins, tests and MCP. Public contract/version impact: none.
Bootstrap impact: rebuild the two C0 components with frozen B0. ADR required: this
document. Release blocking: no public promotion until the separate release gates.

Hypothesis: the existing call/argument representation can support compiler-style
byte processing without another compiler or source expansion. A new statement
record supplies single ownership of a discarded call result. Builtins are resolved
after user functions, retaining existing legal names and executable bytes.

Alternatives: reserving builtin names breaks valid C0.29 functions; a host library
violates the canonical chain; raising all capacities now does not solve runtime
coverage and silently exceeds the existing u16 span format. Keep capacity work
separate and finish this bounded runtime foundation first.

## Global Constraints

- Keep every previously accepted C0.29 source's AST and ELF bytes unchanged.
- No host assembler, LLVM, linker or source interpreter in canonical compilation.
- Preserve source/token/node/block/function-depth bounds: 8192/512/512/64/64.
- Keep the user function ABI and left-to-right argument evaluation from FUNCTIONS.md.
- No heap allocation or opened descriptors. Runtime byte storage is one explicit
  zero-initialized 65536-byte stack arena, shared across functions, disjoint from
  their 4096-byte indexed frames. It is allocated only if an intrinsic is used.
- No pin promotion until temporary candidates pass focused tests and deterministic
  double rebuild. No commits, resets, deletion of prior work, or public version bump.
- Work in the current continuation checkout requested by the user; snapshots in
  `/tmp/nql-c030-before` preserve the actual uncommitted C0.29 sources and seeds.

## Source And AST Contract

Add `identifier(arguments?) ;?` as a statement. The root must be a call, not an
arbitrary discarded arithmetic expression. Adjacent calls and existing statements
are valid boundaries without semicolons; calls nested in arguments are expressions.
Every function still needs a final top-level return. Block and name rules are
unchanged.

NQAF/4 has the same 16-byte header/record format as /3. It is selected only when a
call statement appears. New kind 44 anchors the callee identifier, owns the
immediately preceding kind-42 call expression in `left`, has `right=0`, and links
the next physical statement through `next`. Its span equals the owned call span.
Expression topology is still contiguous postorder, with exactly one owner per
non-root record. The backend independently validates all of these conditions.
Kinds 39..43 and function envelopes have exactly the /3 contract; /1..3 reject 44.

Builtin expressions need no new record: NQAF/3 and /4 kind-42 names resolve first
against all user definitions, then against the exact builtin names below. A user
function shadows a builtin even if the call has incorrect arity: diagnose the user
arity, never silently fall back. Local variables remain a separate namespace.
Only previously unresolved names gain meaning, so old successful /3 output is
unchanged. Wrong intrinsic arity uses source-located C0B-008 before emitting ELF.

| Intrinsic | Arguments | Result |
| --- | --- | --- |
| byte_load | index | zero-extended byte |
| byte_store | index, value | 0; store low eight bits |
| input_read | offset, count | one read's byte count, 0 at EOF |
| output_write | offset, count | count after writing the entire range to fd 1 |
| error_write | offset, count | count after writing the entire range to fd 2 |

Byte indices must be in 0..65535. Ranges require 0 <= offset <= 65536 and
0 <= count <= 65536-offset. Check without signed overflow. Empty ranges, including
offset 65536, return 0 without a syscall. All violations, including constants,
are checked at runtime and report `input:line:col: error[C0R-004]` at the callee,
exit 70; no partial memory operation. This deliberate diagnostic phase differs
from B0's constant-range rejection but avoids a second constant evaluator.

Read retries EINTR but does not fill the buffer after a short read. Writes retry
EINTR and partial writes. Read failure reports C0R-005, output failure C0R-006,
both with source location and exit 74. A failed error_write or failed diagnostic
write exits 74 without recursively reporting to the broken fd. The existing
SIGPIPE-ignore installation is retained. Native helper calls do not consume the
64 user-function depth budget. Calls in unused branches are not executed.

## Execution Plan And Ledger

The master document delegates completion of missing details; the user requested
continued implementation in this checkout. Ruling: use the established B0 byte
contract plus the explicit differences above, preserve the dirty workspace and
do not create a branch or commit without authorization.

| Task | Producer / Consumer | Pre-flight finding |
| --- | --- | --- |
| 1 tests | shared AST/runtime contract for 2 and 3 | no implementation dependency for RED |
| 2 frontend | NQAF/4 kind 44 consumed by 3 | exact span and single ownership required |
| 3 backend | ELF runtime consumed by 1 and 4 | /3 intrinsic names extend resolution only |
| 4 integration | pins/gates consumed by MCP and docs | promotion waits for 1..3 verification |

- [x] Baseline: `make test` through fresh MCP `_run_result(timeout=3600)`: 1072
  PASS, 0 FAIL/SKIP, exit 0, 1338375 ms. Durable evidence:
  `/tmp/nql-c030-baseline-result.json`, `/tmp/nql-c030-baseline.log`.
  MCP unittest discovery: 33 tests, exit 0. Existing Pydantic warning retained.
- [x] Task 1: add `tests/bootstrap/test_c0_runtime_io.py`, prove failures on C0.29.
  Cover actual byte effects, range extremes, shared arena, nested argument order,
  short/EOF reads, large writes, failed descriptors, syntax/AST mutations, arity,
  exact builtin shadowing and predecessor fingerprints.
- [x] Task 2: extend `frontend.nql` with call-statement classification, boundaries,
  kind-44 ownership and version selection; reject discarded arithmetic.
- [x] Task 3: extend `backend.nql` independently: kind-44 validation, builtin name
  fallback, checked direct-code helpers, arena initialization and I/O diagnostics.
- [x] Task 4: rebuild twice through B0, compare predecessor corpus, promote pins,
  integrate bootstrap gates and fail-closed MCP fields, independent code review,
  full `make test`, MCP suite and release check. Record results in this document
  and the selected master; Full Compiler/self-hosting remain NOT_IMPLEMENTED.

### Recovery Checkpoint, 2026-09-12

Historical checkpoint, superseded by the October reverification below:

The interrupted work resumes from C0.30, not from the already completed C0.29.
RED: call-statement test failed on C0.29 with C0P-008; byte-arena expression test
failed with C0B-008. Both exited 1 as expected before implementation.
Frontend candidate built directly by B0 passes all four new frontend tests and
the two existing function syntax/long-callee tests. Eleven of twelve original
frontend tests pass before promotion; the remaining materializer test correctly
rejects the old pinned hash against the new source. It must be rerun unchanged
after joint promotion, not weakened. Backend task is in progress; seed pins and
public status have not been advanced.

## Native Runtime Layout

Only programs resolving an intrinsic get the runtime arena and helper region.
The old entry at ELF offset 176, code limit 24000 and output limit 32768 remain.
The initializer at 24576 reserves and zeroes 65536 stack bytes, retains their
base in `rbx`, then transfers to the old entry. Function frames grow below that
arena. Successful helpers preserve `rbp`, `rbx` and `r12`..`r15`; argument values
and the user's live temporaries remain in the existing indexed call frames.

| ELF offset | Role |
| --- | --- |
| 24576 | 29-byte arena initializer |
| 24608, 24640 | byte load and store |
| 24672, 24688, 24704 | input, output and error stream entrypoints |
| 24736 | common range guard and read/retry path |
| 24832, 24912 | complete-write loop and write-failure dispatch |
| 24928, 24960, 24992 | range, read and output faults |
| 25024 | diagnostic prefix writer |
| 25152, 25232, 25312 | diagnostic suffixes; last helper byte 25372 |
| 25600 | source diagnostic prefixes when the runtime is present |

Runtime-free output retains the earlier prefix base 24576. The backend's
internal intrinsic IDs 513..517 are derived only after name/arity resolution,
not trusted from serialized AST records. They are not user node IDs and do not
consume the user-function depth budget.

## Reverification, 2026-10-12

The resumed checkout already contained both completed C0.30 components and
matching promoted pins. Reverification preserves that work rather than rebuilding
C0.29 or repeating the implementation. All seven bootstrap hash checks pass.

| Component | Bytes | SHA-256 |
| --- | --- | --- |
| Frontend seed | 82711 | `8b745978c63387126ba18b6a75524551b6352b296440cadc504a4468f3ce76ad` |
| Backend seed | 165905 | `46a08a95224f7171b7fd9b948fecaf1e7b6e819c4a8b4b8471b980361d708405` |
| Frontend source | 51214 | `2cd11f6fd219bfbd84555d85998c286301b8798f7523785c385add26ed947d0a` |
| Backend source | 106949 | `56f9b2bddde5161fe6f0afb3d3b2dcb097a7ec91f44b1d6eea1f82c4e7a23782` |

The October baseline, before edits, completed `make -k test` with 1073 PASS,
0 FAIL and 0 SKIP, exit 0. Its component gates rebuild each compiler twice with
B0 and compare both bytes and pinned hashes. MCP's configured interpreter passed
33 tests; the system Python lacks `mcp` and is not the configured test environment.
Release-check had one pre-existing failure: its required-files list still named
the removed `NOLQU_MAJOR_DEVELOPMENT.md` (8 PASS, 1 FAIL).

The same stale filename broke section-backed MCP resources. New regression tests
failed before the fix, including an inline-heading false-match fixture and an
obsolete-document fallback fixture. MCP and release checks now use the revised
authority without recreating the obsolete file. A real stdio test starts MCP in
an unrelated directory, initializes the protocol, reads the current resources
and checks tool/prompt discovery. The complete MCP suite now passes 37 tests,
exit 0; release-check passes 9/9. The existing Pydantic `lifespan` warning remains.

The prior independent frontend review found no code defect, but identified a
weak test oracle: `next > current` admitted out-of-range statement links. The
test now asserts the exact physical chain, in-range children and one owner per
non-root node. All four frontend runtime tests pass; injecting the reviewer's
`next=65535` mutation now fails the oracle as intended.

The combined canonical probe passes with emitter C0.25 and frontend/backend
C0.30: `SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED`. Call-statement,
byte-memory and stream-I/O evidence is true, but Full Compiler/self-hosting
evidence remains false. This is bounded verification, not a general safety proof.

## Completion Evidence

Work unit verified on 2026-10-12, with the source and seed hashes above unchanged.

| Gate | Result |
| --- | --- |
| Original pre-C0.30 baseline (September) | 1072 PASS, 0 FAIL/SKIP, exit 0 |
| Resumed baseline before these edits | 1073 PASS, 0 FAIL/SKIP, exit 0 |
| Final `make -k test` | 1073 PASS, 0 FAIL/SKIP, exit 0 |
| Final MCP suite | 37 tests PASS, exit 0 |
| `make release-check` | 9 PASS, exit 0 |
| Frontend/runtime and backend/runtime gates | 4 + 13 runtime tests PASS, included in `make test` |
| Bootstrap artifact hashes | All seven PASS |
| Combined canonical probe | `SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED`, exit 0 |

Sorted PASS-name multisets of the resumed baseline and final suite are identical.
The runtime gate adds `c0-runtime-io` relative to the September baseline; nested
unittest cases are not counted again in the aggregate 1073 shell-gate total.
Repeatable commands are `make test`, the MCP unittest command in `tools/README.md`,
`make release-check`, and the MCP `run_c0_probe` tool. This run's full logs are
`/tmp/nql-c030-final-tests-20261012.log` and
`/tmp/nql-c030-final-mcp-20261012.log`; they supplement, not replace, checked-in tests.

An independent backend review saved its complete report before its session hit
a usage limit: `/tmp/nql-c030-backend-review-20261012.md`. The reviewed source and
seed match the table above. It found no actionable spec/correctness defect after
checking kind-44 validation, resolution precedence, native helper disassembly,
register/stack discipline, ranges and diagnostics. Additional review probes
covered 93 malformed ASTs, live-pipe short reads, six-argument builtin shadowing,
high node IDs, and injected syscall/register behavior. Those temporary probes
are supplementary review evidence, not permanent regression gates. Native x86_64
signal delivery and exhaustive malformed-input correctness are not claimed;
execution here used QEMU on aarch64.

The separate MCP reviewer did not produce a report before the usage limit.
The authority fix received local self-review, red/green regression tests and
fresh-process protocol verification; it is not described as independently reviewed.
No unreviewed compiler change was substituted for the reviewed backend.

## Historical C0.30 Capacity Boundary

The following source-size failure was resolved by the completed C0.31 capacity
milestone. It is retained as before/after evidence, not the current source limit.
C0.32 full-source generations also pass; see [CAPACITY.md](CAPACITY.md).

Feeding those complete sources to the C0.30 frontend gave exit 1 and no AST:

```text
frontend.nql (51214 bytes): input:166:8: error[C0P-002]: source exceeds 8192 bytes; split the input
backend.nql (106949 bytes): input:151:51: error[C0P-002]: source exceeds 8192 bytes; split the input
```

The backend source exceeds the 65535-byte span range as well. The next work unit
must jointly specify larger spans or bounded compilation units, token/node
capacity and arena layout. Merely increasing the 8192-byte constant is unsafe.
Do not restart runtime implementation or expand the frozen C0.25 emitter to
work around this boundary. Full Compiler and formal self-hosting remain
`NOT_IMPLEMENTED`; no public `VERSION`/`CHANNEL`, B0 or predecessor pin changed.
