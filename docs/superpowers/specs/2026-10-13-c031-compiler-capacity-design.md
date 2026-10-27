# C0.31 Compiler-Source Capacity

Status: **COMPLETE — INSTALLED AND VERIFIED FOR THE CAPACITY MILESTONE**. Design approved on 2026-10-13;
the continuation on 2026-10-14 approved the
[implementation plan](../plans/2026-10-13-c031-compiler-capacity.md) and its
subagent-driven execution. Task 1 completed both review gates on 2026-10-16;
Task 2 completed full regression and both review gates on 2026-10-21 in the
same isolated worktree. Tasks 3, 4 and 5 completed full regression and both independent
closure reviews on 2026-10-22; Task 6 actual component generations completed
full regression and both independent closure reviews on 2026-10-23. Task 7
coherent integration has passed fresh prevalidation and independent reviews.
The repaired B0/frontend/backend set has been canonically materialized with
matching pins. All eight exact promoted-phase gates also passed without timeout
or skip; independent final whole-change closure approved the completed evidence
and documentation without actionable findings. All seven tasks are complete
within this experimental capacity contract, with no public release. This remains
the binding design; execution evidence belongs to the plan and ledger.

Authority: [revised development document](../../../NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md)
and [NolQu-L concept](../../../NolQu-LConcept.docx), supplemented on 2026-10-16 by
the [Assembly-Level contract](../../../NOLQU_MAJOR_DEVELOPMENT_ASSEMBLY_LEVEL.md)
and its v10 concept document. The new authority explicitly distinguishes design
targets from implemented capabilities and forbids changing bootstrap status by
terminology alone. Its older C0.29/C0.30 snapshot does not supersede the verified
October evidence below. C0.31's capacity, target and provenance decisions remain
unchanged; no new assembly syntax, safety mode or ISA capability is implied.
Current implemented contracts:
[frontend](../../../bootstrap/compiler/c0/FRONTEND.md),
[backend](../../../bootstrap/compiler/c0/BACKEND.md),
[functions](../../../bootstrap/compiler/c0/FUNCTIONS.md), and
[runtime](../../../bootstrap/compiler/c0/RUNTIME_IO.md).

## Intent And Classification

Make the source-driven C0 frontend/backend large enough to process and compile
their actual NolQu-L sources, while retaining simple indexed storage, explicit
resource costs, and the canonical machine bootstrap. Capacity must be a coherent
contract across input, tokens, nodes, spans, native frames, and emitted code.
Increasing only the input buffer would corrupt other bounded regions.

Requested mode: major development. Actual class: architectural, experimental
compiler-capacity change. Risk: high. Affected stages: predecessor runtime,
lexer/parser storage, AST wire format, validation, name resolution, machine
emission, source wrapper, bootstrap verification and MCP evidence. This document
records the ADR; it does not change public VERSION or CHANNEL.

Non-goals: new language syntax, modules/linker, general allocator, optimizer,
register allocator, argv API, R0/LLVM development, or declaring Full Compiler,
self-hosting, or Verified. Building these two components with C0 is evidence
about those components, not proof of all later stages.

## Measured Starting Point

The completed C0.30 artifacts and uncommitted workspace were inspected before
edits. They must not be mistaken for unfinished C0.29 work.

| Evidence | Observed result |
| --- | --- |
| `make -k test release-check` | Complete log: 1,082 PASS, 0 FAIL, 0 SKIP |
| Main-suite portion | 1,073 PASS names match the previous verified C0.30 suite exactly |
| Separate `make release-check` rerun | 9 PASS, exit 0 |
| Configured MCP unittest discovery | 37 tests PASS, exit 0 |
| Bootstrap status | All seven artifact hashes match their pins |

Logs: `/tmp/nql-c031-baseline-20261012.log` and
`/tmp/nql-c031-mcp-baseline-20261012.log`. The combined command's terminal session
was lost across interruption: its complete log is available, but its final shell
exit receipt is not. Do not report an observed exit 0 for that combined command.
Nested unittest cases are not added to the 1,073 gate count a second time.
The existing MCP Pydantic `lifespan` warning remains non-fatal.

Actual source inventory, using pinned B0's `--lex` with exit 0 and empty stderr:

| Source | Bytes | Tokens | Identifiers | Punctuation | Integers | Keywords |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `bootstrap/compiler/c0/frontend.nql` | 51,214 | 12,019 | 2,455 | 6,595 | 2,941 | 28 |
| `bootstrap/compiler/c0/backend.nql` | 106,949 | 25,014 | 5,972 | 13,390 | 5,619 | 33 |

These are lexer counts, not successful C0 parses or node-count measurements.
Both sources fail the current 8,192-byte source cap with C0P-002, exit 1 and
empty AST output. Their measured locations are 166:8 and 151:51 respectively.
The backend source alone exceeds the u16 span range.

Current coupled limits: 512 tokens/nodes; 16-byte NQAF/1..4 records; u16 spans,
counts and IDs; B0-generated 65,536-byte stack arena; 4,096-byte native function
frames indexed by global node ID; 24,000-byte code boundary; 32,768-byte ELF
buffer. Code/prefix offsets and four-digit diagnostic formatting also require
attention. Capacity alone is not proof of memory/resource safety on all inputs.

Starting identities:

| Artifact | SHA-256 |
| --- | --- |
| Frontend source | `2cd11f6fd219bfbd84555d85998c286301b8798f7523785c385add26ed947d0a` |
| Backend source | `56f9b2bddde5161fe6f0afb3d3b2dcb097a7ec91f44b1d6eea1f82c4e7a23782` |
| Frontend seed | `8b745978c63387126ba18b6a75524551b6352b296440cadc504a4468f3ce76ad` |
| Backend seed | `46a08a95224f7171b7fd9b948fecaf1e7b6e819c4a8b4b8471b980361d708405` |
| B0 seed | `7b71089df23551ea55444f132834046cc619a93cf45ad78f285d64d615ce495c` |

## Decision And Alternatives

Choose one integrated, versioned wide-capacity path. Retain the legacy AST and
ELF path for sources that still fit its contract. Runtime memory expansion is
an explicit compiler profile, never inferred from file name or source size.

Alternatives considered:

1. Input-only constant increase: rejected; u16 spans, arena overlap, frame
   addressing and code offsets remain unsafe.
2. Streaming/chunked compilation: avoids a large arena, but introduces multipass
   source storage and cross-chunk fixups before the compiler has those contracts.
3. Splitting the compiler into modules: useful later, but currently requires a
   module/link contract and does not fix large-function/global-node slot usage.

The 16 MiB compiler arena is a bounded engineering choice, not a measured memory
requirement or efficiency claim. No unbounded allocation is introduced. The
actual two compiler sources, not arbitrary primitive-count milestones, are the
acceptance workload. If implementation growth exceeds a proposed limit, record
the failing artifact and revise this contract before raising another limit.

## Proposed Limits

| Quantity | Wide-capacity contract |
| --- | ---: |
| Source bytes, excluding transport header | 262,144 |
| Tokens, excluding EOF | 65,536 |
| AST nodes | 65,536 |
| Source offsets, lengths, IDs and counts | unsigned 32-bit on wire |
| Control nesting / parameters / user call depth | unchanged: 64 / 6 / 64 |
| Per-function frame / usable i64 slots | unchanged: 4,096 bytes / 512 |
| Default program byte arena | unchanged: 65,536 bytes |
| Explicit compiler-profile byte arena | 16,777,216 bytes |
| Wide ELF buffer | 8,388,608 bytes |
| Wide code region upper boundary | file offset 6,291,456, exclusive |
| Wide helper region | `[0x600000, 0x604000)` |
| Wide runtime diagnostic data | `[0x604000, 0x800000)` |

Limits are checked independently. A source may fit the parser yet exceed native
frame or output limits; that is a located capacity error, not permission to emit
truncated code. Only used output bytes are emitted, not the whole backing arena.
Unused gaps inside the emitted ELF are deterministic zero bytes.

## Canonical Predecessor Bridge

B0's generated 64 KiB arena cannot even contain the current backend source.
An explicit predecessor bridge is therefore justified by measured input, not
by a speculative language feature.

Add `--compiler-profile` to B0's compile mode. The normal invocation, grammar,
16-local limit, runtime bounds and successful ELF bytes stay unchanged. The
option is rejected for `--lex`/`--parse`; duplicates and unknown options fail.
The option may precede or follow the input, consistent with output flag parsing.

```text
b0.seed --compiler-profile frontend.nql -o c0-frontend.candidate
```

This profile generates a direct Linux anonymous private mapping, 16 MiB,
read/write and non-executable. Do not put 16 MiB on the machine stack. The
mapping base and acquired-state flag are private runtime state, disjoint from
the 16 user locals and expression stack. Every byte/range access checks the
selected bound before pointer arithmetic. Private state is not a language local.

The profile preserves B0 expression and successful intrinsic return semantics;
it does not silently adopt C0's checked-arithmetic or stream-return semantics.
Its stream helpers retry EINTR and complete partial writes, with all error exits
routed through cleanup. Default B0 templates remain unchanged.

The canonical change is authored in B0's Stage0-readable machine source, rebuilt
through Stage0, and checked against the independently maintained reference
assembly. Reference assembly is an audit/test oracle only. No host assembler,
Python code generator, semantic binary patcher, LLVM or host linker may produce
the promoted canonical artifact. B0's own source/output/patch-table capacities
remain unchanged unless a separate measured blocker requires a reviewed change.

## Profile Transport Without A New Language Feature

C0 components are stdin/stdout programs; generated B0 programs do not expose
argv. Carry the explicit compile profile in a small versioned input envelope,
not a hardcoded compiler filename or source rewriting rule.

Plain source on fd 0 still means default profile. The source wrapper gains:

```text
compile-source.sh --compiler-profile input.nql output
```

It prepends this 16-byte NQSC header, then copies the source bytes unchanged:

| Offset | Type | Value |
| --- | --- | --- |
| 0 | 4 bytes | `NQSC` |
| 4 | u8 | version 1 |
| 5 | u8 | runtime profile 1 |
| 6 | u16 | flags 0 |
| 8 | 8 bytes | reserved, all zero |

There is one envelope at most, recognized only at byte zero. Header profile 0,
unknown profiles, bad version/reserved fields and truncated envelopes are
rejected with `input:1:1: error[C0P-013]`, exit 1 and no AST. Profile 0 uses raw
source instead. A subsequent `NQSC` inside the payload is ordinary source text,
not a nested envelope. Header bytes never count toward source size or locations.

Diagnostic allocation corrected on 2026-10-16 before transport implementation:
the existing C0.30 `C0P-010` means unexpected input after a function, and
`C0P-011/012` cover block depth and arity. Preserve those identities and messages;
do not reuse them for envelope failures. `C0P-013` is the next unused code.

The wrapper only frames bytes, checks pins, and manages temporary files. It does
not tokenize, resolve names, generate code, or interpret the source. Existing
raw-source invocation stays unchanged. Short reads must not lose lookahead
bytes while distinguishing raw source from an envelope. The wrapper must check
both framing/copy and frontend statuses before invoking the backend.

## NQAF/5 Wire Contract

Little-endian, 32-byte header, exact source bytes, then exactly `node_count`
32-byte records; no trailing bytes. A maximum stream has 2,359,328 bytes.

| Header offset | Type | Meaning |
| --- | --- | --- |
| 0 | 4 bytes | `NQAF` |
| 4 | u8 | version 5 |
| 5 | u8 | record size 32 |
| 6 | u16 | flags 0 |
| 8 | u32 | source length |
| 12 | u32 | node count |
| 16 | u32 | root ID |
| 20 | u32 | token count, excluding EOF |
| 24 | u8 | dialect 1, 2, 3 or 4 |
| 25 | u8 | runtime profile 0 or 1 |
| 26 | u16 | reserved 0 |
| 28 | u32 | reserved 0 |

| Record offset | Type | Meaning |
| --- | --- | --- |
| 0 | u8 | existing node kind |
| 1 | u8 | flags 0 |
| 2 | u16 | reserved 0 |
| 4 | u32 | anchor source offset |
| 8 | u32 | anchor length |
| 12 | u32 | left child ID |
| 16 | u32 | right child ID |
| 20 | u32 | next physical statement ID |
| 24 | u32 | reserved 0 |
| 28 | u32 | reserved 0 |

IDs remain one-based; zero is absence, not an allocated record. Dialect retains
the grammar, kinds, root/function envelope and ownership rules of NQAF/1..4.
It is independent of storage width and runtime profile. No new AST kind or
language construct is introduced. Source spans still anchor lexemes, not whole
subtrees. Existing exact postorder and physical statement-chain validation stays.

Selection is deterministic: plain sources within the old 8,192/512/512 limits
emit byte-identical /1..4 according to the existing feature tier. Sources beyond
any old capacity emit /5 with the same dialect and profile 0. Explicit compiler
profile always emits /5 with profile 1, even for a small source.

The backend accepts /1..4 with their old bounds, not relaxed forged counts.
It independently checks /5 magic, lengths, reserved bytes, dialect, profile,
counts, root, spans, node shapes, ownership and statement order before emission.
Validate `length <= source_length - offset` after checking the offset; similarly
check record bounds before multiplication/addressing. Decode into wide state
directly: never truncate to u16 and widen the truncated value afterward.

Use a versioned record view over the input buffer rather than a second complete
AST copy. Kind-specific derived callee metadata must distinguish user functions
from intrinsics; the old internal IDs 513..517 cannot alias wide user node IDs.
User-function-first lookup and wrong-arity shadowing remain unchanged.

## Bounded Storage Layout

All intervals below are half-open byte offsets within the explicitly mapped
16 MiB compiler arena. Counts include a sentinel only where stated. Node table
indexing is `(id - 1) * stride`; sentinel IDs never dereference the table.
Gaps are reserved, not automatically available to incidental scratch stores.

### Frontend

| Region | Capacity / purpose |
| --- | --- |
| `[0, 0x41000)` | source, overflow byte and read lookahead |
| `[0x50000, 0x11000c)` | 65,537 tokens including EOF; 12 bytes each |
| `[0x120000, 0x130000)` | lexer/parser/transport state and scratch |
| `[0x200000, 0x400000)` | 65,536 wide nodes |
| `[0x400000, 0x4c000c)` | 65,537 operator entries, 12 bytes each |
| `[0x4d0000, 0x510004)` | 65,537 operand IDs, 4 bytes each |
| `[0x520000, 0x620010)` | 65,537 call markers, 16 bytes each |
| `[0x630000, 0x630410)` | 65 block entries, 16 bytes each |
| `[0x640000, 0x640020)` | output header |
| `[0x641000, 0x651000)` | diagnostic formatting and bounded serialization scratch |
| `[0x7ff000, 0x7ff100)` | explicitly discarded inactive stores |

Tokens store kind/reserved, u32 offset and u32 length. Operators, operand IDs,
call markers and block links must all be wide; widening only the node record is
insufficient. The frontend holds wide nodes internally. For legacy output it
serializes validated narrow fields through scratch without altering allocation
order or source bytes. No AST is written before complete syntax validation.

### Backend

| Region | Capacity / purpose |
| --- | --- |
| `[0, 0x241000)` | maximum NQAF/5 stream plus overflow byte |
| `[0x241000, 0x251000)` | per-node identifier roles |
| `[0x251000, 0x261000)` | per-node ownership marks |
| `[0x261000, 0x2a1000)` | subtree start IDs, then resolved binding IDs; u32 |
| `[0x2a1000, 0x3a1000)` | 16-byte per-node, kind-tagged literal/callee/function data |
| `[0x3a1000, 0x3b1000)` | per-node arity metadata |
| `[0x3b1000, 0x3b3000)` | bounded active bindings/scope bookkeeping |
| `[0x3b3000, 0x3f3000)` | function-entry node ID index; u32 |
| `[0x3f3000, 0x473000)` | per-node prefix offset and length; two u32 |
| `[0x473000, 0x573004)` | source line starts; 262,145 u32 entries |
| `[0x580000, 0x5c0000)` | per-node code offsets; u32 |
| `[0x5c0000, 0x5e0000)` | per-node native frame slots; u16 |
| `[0x5e0000, 0x600000)` | per-function-node permanent slot counts; u16 |
| `[0x680000, 0x690000)` | bounded control stack, state, scratch and diagnostics |
| `[0x7ff000, 0x7ff100)` | explicitly discarded inactive stores |
| `[0x800000, 0x1000000)` | ELF output buffer |

Per-kind data reuse must be documented and happen only after the previous
phase's data is dead. In particular, graph validation must finish before subtree
starts are reused for resolved bindings. Scope bookkeeping must obey both the
64-block and 512-live-slot limits, with no unchecked spill into the function
index. A host test asserts every interval, capacity calculation and non-overlap;
the compiler itself still checks each allocation/access boundary.

## Native Frames And Structural Scaling

For /5, decouple AST identity from stack address. Each function parameter and
declared binding receives one permanent slot, retained for that function's
lifetime even after lexical scope ends. Initializers and name visibility retain
their current semantics; assigning a slot does not permit forward references.

Expression temporaries occupy slots after all that function's permanent slots.
Slots may be reused between completed statements/conditions. Values still
needed by a parent expression or unevaluated call must remain live. All call
arguments are evaluated left-to-right into live slots before the call; nested
callees have distinct frames. Branches may reuse consumed condition slots;
while backedges recompute the condition. Require permanent slots plus peak
statement/condition temporary slots <= 512, or emit located C0B-007 before ELF.

Slots are 1..512 with 8-byte offsets; zero means no assigned slot. Frames remain
4,096 bytes, SysV alignment and callee-saved registers are preserved, and user
call depth remains 64 including main. Runtime helpers do not consume that depth.
Legacy /1..4 retain their node-ID slot mapping and executable byte layout.

Two structural changes accompany wide input:

- Build a line-start index once, then locate source anchors by bounded search.
  Avoid rescanning the complete source prefix for every runtime diagnostic.
- Index function entries once; resolve calls against declarations rather than
  scanning every AST record for every call. No hash table or new optimizer is
  required. Keep exact-length, case-sensitive name matching and lexical scopes.

Wide code and diagnostic offsets use checked u32 state. Bounds precede every
template write and branch/call patch, including rel32 displacement validation.
Format full decimal source coordinates through the possible EOF location
262,145; do not retain the old four-digit formatter. Runtime errors continue
to name the original operation, not a generated helper location.

## Runtime Ownership And Errors

AST width does not select a larger user runtime arena. Profile 0 preserves the
64 KiB arena and its C0 byte/range contract, even for a 200 KiB program source.
Profile 1 explicitly maps 16 MiB at startup when byte/stream intrinsics are
resolved. Programs with no such intrinsic need no arena allocation.

C0's mapped arena base uses the existing preserved runtime base register;
user functions and helpers cannot overwrite it. Mapping state and successful
return status survive syscalls. Every range checks non-negativity and
`count <= capacity - offset`, allowing the existing empty range at the end.
C0 read short-count/EOF behavior, retry on EINTR, complete writes, byte-store
low-eight-bit behavior, arithmetic checking and builtin shadowing are unchanged.

On mapping failure, report the resource cause and a remedy, exit 74, and never
access the failed mapping. On normal return and every runtime error path,
attempt to unmap an acquired mapping once before exiting. Diagnostics that use
arena bytes must be written before releasing it. A diagnostic write failure
still cleans up, exits 74 and does not recursively diagnose the broken fd.
An unmap failure exits 74 with a fixed, arena-independent diagnostic; process
termination remains the final OS reclamation mechanism. Fatal signals rely on
OS mapping reclamation, not an unverified userspace cleanup guarantee.

New C0 resource diagnostic: C0R-007, `input:1:1` for startup/teardown failures,
exit 74. Existing located range/arithmetic errors remain exit 70; stream errors
remain C0R-005/006, exit 74. B0 profile resource errors identify the B0 runtime,
cause and remedy, not a fabricated source location. Compiler syntax/semantic/
capacity errors remain exit 1 with no AST/ELF before successful validation.
No file descriptor is opened by either component or generated runtime.

The source wrapper retains unique temporary storage, signal traps, output/source
alias protection, pin verification and same-directory atomic publication.
Envelope, frontend, backend and runtime cleanup must all succeed before
publication. Remove the intermediate AST/workspace before the final rename;
failure there leaves the old executable untouched and removes the candidate.
After successful rename, the new executable is committed: a later signal is
not a promise to restore the old one. Streaming stdout can be partial after a
write failure; consumers must check exit status, not merely nonempty output.

## Compatibility And Integration

Previously valid /1..4 programs keep their AST and ELF bytes. Current negative
tests at 8,193 source bytes or 513 tokens/nodes intentionally change: those
inputs may now succeed as /5. Preserve their old behavior against frozen C0.30
evidence, add the new positive expectations, and move the new capacity-negative
tests to one beyond the new bounds. Do not remove malformed legacy-IR tests or
reinterpret old-format out-of-contract streams as /5.

Targeted files for the later implementation plan:

- B0 machine source, independent reference, profile documentation, materializer
  and tests: explicit compiler-runtime bridge without changing the default path.
- C0 frontend/backend sources: storage, /5 serialization/validation, slot mapping,
  code offsets, diagnostics, mapped-runtime emission and cleanup.
- C0 materializers/source wrapper: profile selection and atomic verified build.
- Bootstrap tests/Make gates: boundary, predecessor, component-generation and
  deterministic rebuild evidence.
- MCP/bootstrap documentation: truthful observed status, profile/format metadata
  and first actual blocker. Do not set later-stage booleans from a build alone.

Machine Foundation, Stage0 and the C0.25 bounded emitter are not feature targets.
Keep old snapshots/fixtures sufficient to run predecessor byte parity. Do not
silently replace pinned artifacts before candidate tests. The B0 bridge, C0
component pair, profile-aware materializers and manifests must advance coherently
after verification; rollback must restore that set coherently, not one seed.

## Acceptance Evidence Required

The following are requirements, **not tests already passed**:

1. Before implementation, preserve identifiable C0.30 and B0.7r sources/seeds and
   predecessor fingerprints. Reproduce RED: actual compiler sources fail C0P-002;
   /5 input and compiler-profile invocation are unsupported.
2. Verify the B0 bridge from Stage0-readable machine source. Default predecessor
   corpus output remains byte-identical. Profile probes exercise byte indices
   65,535, 65,536 and 16 MiB minus/at/above the bound, mapping failure and cleanup.
3. Test source 262,144/262,145, tokens and nodes 65,536/65,537 independently, with
   exact-bound successes and one-over failures. Exercise spans and valid node IDs
   above 65,535, EOF/short reads and both legacy/profiled transport.
4. Mutate /5 headers, flags, profiles, dialects, counts, truncation, trailing data,
   wrapping spans, root/child IDs, shared/cyclic nodes and physical statement
   links. Reject before emission, without a crash or hang. Keep all /1..4 checks.
5. Test high global node IDs across functions, exact/excess frame slots, nested
   call argument order, recursion 64/65, scopes, shadowed intrinsics, control
   nesting, large code fixups and source locations above four decimal digits.
6. Validate profile/default arena separation, arithmetic/range errors, EOF,
   partial writes, EINTR, bad descriptors, failed diagnostic writes and resource
   failure cleanup. Check native stack alignment and register preservation;
   inspect mappings/syscalls using an explicitly non-semantic test harness.
7. Rebuild each candidate component twice with the new B0 profile, compare bytes
   and actual hashes, and run the entire predecessor AST/ELF corpus against the
   candidates. Do not substitute matching exit codes for binary parity.
8. Process both actual updated compiler sources through the candidate frontend
   and backend. Execute the resulting components on the same syntax, malformed
   IR and runtime fixtures. No host semantic stage may fill a missing feature.
9. Label B0-built components A; A builds components B; B builds components C.
   Compare B/C component bytes and behavior on the common corpus. Report actual
   divergence instead of normalizing it away. This is component-generation
   evidence only; Full Compiler/self-hosting/Verified remain unpromoted.
10. Run full `make -k test`, configured MCP discovery tests, `make release-check`,
    bootstrap hash verification and the combined canonical probe. Perform separate
    spec-compliance and code-quality reviews before coherent seed promotion.

Boundary fixtures may isolate parser, validator or codegen: max-token success
does not imply max-output success. Allocation/cleanup fault injection must state
its method and limitations; a QEMU run alone is not a general leak proof. Any
new valid-input crash, old-corpus byte difference or uncontrolled failure halts
promotion until diagnosed. No performance, savings or memory-use percentages
are claimed without measurements.

## Review Handoff

Self-review on 2026-10-13 checked format/profile separation, predecessor byte
compatibility, ownership and cleanup ordering, scope and capacity arithmetic.
An executable document check found no overlap in the 11 frontend or 16 backend
regions, verified the maximum stream size and sentinel-table sizes, and resolved
all local document links. These are design checks, not generated-code tests.
Four focused MCP resource/protocol tests passed after the master-document update,
including initialization and reads from an unrelated working directory. The
source/seed hashes listed above are unchanged. No independent code review is
claimed for this documentation-only step.

The user continued after the written-spec review request on 2026-10-13. The
task-by-task implementation plan is now written and requires review and execution
selection. This remains a documentation-only step; no version, seed, branch,
commit, push or release transition has occurred.
