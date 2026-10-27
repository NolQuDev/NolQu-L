# C0 AST Backend

## C0.32: Independent Native Permission And ABI

The current candidate source adds NQAF/6 dialect5 while retaining /1..5.
Kind45/46 unsafe statements pass the existing graph, unique-owner, physical
chain, function, lexical-binding and combined-depth checks. Independent source
brace/header scanning binds the close to its real source brace and each raw
call to an owning unsafe source interval. An AST relink alone cannot authorize
a source-outside call. This is bounded permission correspondence, not complete
AST/source authentication or full Safety. Rejection uses new C0B-010; historical
C0B-009 remains the unsupported-profile diagnostic.

Exact global user functions resolve before all four native intrinsic names,
including wrong-arity shadows. Resolved calls lower to argv count/copy, checked
arena address or one raw six-word Linux syscall. The helper loads
rax/rdi/rsi/rdx/r10/r8/r9, returns raw rax, preserves returning callee-saved
state/alignment and does not retry or elide zero-length calls. Arg-count alone
allocates no arena. Copy/address/frame operations use the selected existing
64 KiB default or explicit 16 MiB RW/NX arena. New emitted helper/data bytes
are conditional so tested successful legacy AST/ELF bytes remain unchanged.

[NATIVE_OS.md](NATIVE_OS.md) defines the 48-byte frame, startup register roles,
actual helper offsets, diagnostics and caller responsibilities. Six runtime
and 123 backend/legacy methods passed, with independent Task2 approval and
both-profile actual mmap/register traces. Actual complete-source generations
also pass, as do final public/main/MCP/combined-proof execution gates. An
earlier frozen comparison-backend SIGKILL is unexplained; stable/security
readiness remains PARTIAL, as recorded in [NATIVE_OS.md](NATIVE_OS.md).
Full Compiler/self-hosting remain false.

## C0.31: Wide Input And Native Slots

At the completed capacity checkpoint, Task 7 labeled the source/probe contract C0.31 in metadata, without
changing reviewed compiler bytes. Backend capacity/profile/component-generation
flags require the complete fresh frontend/backend/capacity gates and validated
raw receipts. Their success remains separate from Full Compiler/self-hosting;
see [CAPACITY.md](CAPACITY.md). All final postinstallation checks passed.

The historical C0.31 seed and source implement the capacity design in
[the binding specification](CAPACITY.md).
Prevalidation, installed identities and remaining final gates are recorded in
CAPACITY.md and the C0.31 execution ledger, not implied by source presence. No Full
Compiler or self-hosting claim is made.

B0 builds `backend.nql` with explicit `--compiler-profile`. That profile gives
the compiler process a bounded 16 MiB RW/non-executable arena. It does not change
the runtime profile of a program being compiled. The explicit runtime
path consumes validated NQAF/5 or /6 profile 1 and maps 16 MiB RW/non-executable only
when an arena-using intrinsic resolves. Profile 0 retains exactly 65,536 bytes,
including wide inputs. Exact user shadows allocate no intrinsic arena. Normal
and controlled error exits attempt one release per acquired mapping, including
failed diagnostic writes; resource failures use C0R-007/74. Runtime details and
publication ordering are recorded in [RUNTIME_IO.md](RUNTIME_IO.md).

The record view selects header/record stride and integer width once. Legacy
NQAF/1..4 retain 16-byte records, u16 fields, their 8,192/512/512 source/token/node
bounds, node-ID frame slots and successful executable bytes. NQAF/5 has 32-byte
headers/records, u32 spans and IDs, at most 262,144 source bytes and 65,536
tokens/nodes. Its independent dialect byte controls grammar features; storage
version 5 is not a new grammar dialect. Both forms consume input through EOF and
reject truncation, reserved fields, unsupported profiles, trailing bytes,
invalid spans, non-postorder trees, duplicate ownership, broken physical
statement chains and invalid lexemes before producing an executable prefix.

Decimal accumulation guards both operands before eager checked arithmetic,
including inactive iterations and rejected digits. This preserves valid signed
i64 maximum literals when the backend itself is compiled by C0. Oversized
decimals retain C0B-005 and malformed literal anchors C0B-006, exit 1 without
ELF output. The flat sixteen-local source and generated runtime contracts remain
unchanged; component-generation evidence is recorded in [CAPACITY.md](CAPACITY.md).

### Candidate Storage

Addresses are offsets in the compiler process's mapped arena, not pointers in
the generated program. Intervals are half-open.

| Region | Purpose |
| --- | --- |
| `[0,0x241000)` | Complete maximum wire stream and overflow byte |
| `[0x241000,0x251000)` | Per-node identifier roles |
| `[0x251000,0x261000)` | Graph ownership marks |
| `[0x261000,0x2a1000)` | u32 subtree starts, then resolved binding IDs |
| `[0x2a1000,0x3a1000)` | 16-byte, kind-tagged literal/callee/function data |
| `[0x3a1000,0x3b1000)` | Per-node arity/parameter index |
| `[0x3b1000,0x3b3000)` | Bounded active bindings |
| `[0x3b3000,0x3f3000)` | u32 function-entry index |
| `[0x3f3000,0x473000)` | Per-node u32 prefix offset/length |
| `[0x473000,0x573004)` | 262,145 u32 source line starts |
| `[0x580000,0x5c0000)` | u32 expression/code offsets |
| `[0x5c0000,0x5e0000)` | u16 native frame slots |
| `[0x5e0000,0x600000)` | u16 permanent counts, indexed by function node |
| `[0x600000,0x680000)` | C0.32 eight-byte per-node native ownership/source metadata |
| `[0x680000,0x690000)` | Control stack, state and compiler diagnostics |
| `[0x690000,0x790000)` | C0.32 u32 source-brace correspondence table |
| `[0x7ff000,0x7ff100)` | Inactive stores, never semantic state |
| `[0x800000,0x1000000)` | ELF buffer, at most 8 MiB |

Optional ID zero selects read-only zero scratch `[0x7ff080,0x7ff100)` before
dereferencing. B0 evaluates arithmetic masks eagerly, so multiplying a loaded
value by zero is not a guard for the read. Inactive stores stay below 0x7ff080;
neither adjacent tables nor reserved gaps serve as accidental zero sentinels.
The native protected-page regression makes these boundaries observable.

Graph validation finishes before subtree starts become resolved binding IDs.
Kind-data bytes 0..7 hold a parsed i64 only for integer nodes. Function entries
later use bytes 0..3 for code offsets. Calls use bytes 0..3 for displacement
locations, 4..7 for callee IDs and byte 8 for the user/intrinsic tag. Those node
kinds are disjoint: no live literal is overwritten by a fixup. User node IDs
513..521 are therefore distinct from the historical and native intrinsic numbers.
Arity bytes hold prefix counts, declaration parameter counts or parameter
positions only on their corresponding node kinds. Control records are reused
between completed validation, lexical resolution and code-emission phases.

### Candidate Lifetime And Codegen Rules

A declaration index avoids scanning all records for every call; names are
matched by exact length and source bytes. Each parameter/let in a wide function
receives a permanent slot, retained after lexical scope exit. Assignment uses
the resolved binding's slot. Slots are counted before temporaries, but a let
becomes visible only after its initializer. The symbol stack enforces lexical
visibility independently of slot lifetime.

A postorder live-value stack allocates temporaries after all permanent slots.
Binary expressions and calls consume operands only after evaluation; argument
prefixes keep all preceding arguments live. Completed statements and conditions
release their temporaries. Permanent slots plus peak live temporaries must fit
512 i64 slots in the unchanged 4,096-byte frame or fail as C0B-007 before output.
Six SysV arguments, 16-byte call alignment and depth 64 including main remain
unchanged. Intrinsic helpers do not consume the user call-depth budget.

One source scan builds line starts; bounded binary searches produce full decimal
locations through line/column 262,145. Prefix spans, code locations and fixups
use u32 state. Wide program code stays below file offset `0x600000`, helpers
occupy `[0x600000,0x604000)`, and runtime diagnostic data occupies
`[0x604000,0x800000)`. Bounds precede native writes and signed rel32 patches.
Runtime arithmetic/range errors remain exit 70; descriptor/resource failures
remain exit 74, including broken stderr without recursive diagnostics.

## Historical C0.27 Scalar Contract

The sections below record the original scalar/NQAF/1 contract. At **C0.30**,
[RUNTIME_IO.md](RUNTIME_IO.md) added NQAF/4 call
statements, checked byte/stream intrinsics and their separate runtime arena.
[FUNCTIONS.md](FUNCTIONS.md) defines function-local
parameters, native calls and bounded recursion. [CONTROL_FLOW.md](CONTROL_FLOW.md)
defines structured delimiters, lexical scopes, comparisons and branch fixups.
Previously accepted NQAF/1..3 runtime bytes remain identical for the predecessor
regression corpus. Both component seeds are upgraded; B0/C0.25 are unchanged.
The historical scalar contract below does not limit the current subset.

## Decision And Plan

Requested mode: continue NOLQU_MAJOR_DEVELOPMENT_UPD.md.
Actual update class: Minor Development; risk high (new machine emitter).
Stages affected: AST validation, local resolution, scalar semantics, codegen.
Public contract impact: none; this remains an experimental Core-0 component.
Bootstrap impact: B0 builds backend.nql directly, as it builds frontend.nql.
Compatibility: retain C0.25 and C0.26 source/artifacts unchanged.
Version impact: no VERSION/CHANNEL change or Full Compiler promotion.
ADR: this document defines the new component boundary and checked arithmetic.
Release blocking: runtime, malformed-IR, bootstrap/hash and existing test gates.

The missing stage is NQAF-to-executable, not another parser intrinsic.
Add a separate backend using B0's existing arithmetic, flat loops and byte I/O.
Extending the old bounded emitter or routing through R0/LLVM would not close
this architectural gap. No assembler, linker, Python or host compiler builds
either component. Python is only a test oracle; QEMU adapts x86_64 execution.

Implementation sequence:

- [x] Add failing source-to-runtime and malformed-NQAF tests.
- [x] Validate complete NQAF/1 streams, graph ownership, node shapes and spans.
- [x] Resolve local declarations/references in statement order; validate i64.
- [x] Emit deterministic x86_64 ELF, with checked arithmetic and runtime errors.
- [x] Add atomic source pipeline, pinned materializer, test gate and MCP probe.
- [x] Run regression/release gates, review, and update the development record.

## Contract

Input on fd 0 is one complete NQAF/1 stream from FRONTEND.md, through EOF.
The backend checks lengths, reserved bytes, node kinds, postorder children,
single ownership, contiguous left-to-right postorder within each statement,
reachability and anchor lexemes. Expression nodes cannot cross a statement
boundary or swap evaluation order by moving their records. It does
not authenticate that an arbitrary IR represents all text in its source
payload: compile untrusted source through the frontend, not a supplied AST.

The supported grammar is exactly C0.26's scalar fn main() grammar. One flat
scope, case-sensitive ASCII names and one expression type (signed i64).
Let introduces a mutable local only after its initializer; duplicate names,
forward references, self-initialization and undeclared assignment are errors.
There is no implicit zero initialization of language locals. Decimal literals
are 0..9223372036854775807; leading zeros are allowed. Negative values are
formed by subtraction. No strings, booleans, general type inference, calls,
control flow or modules are introduced by this backend.

Arithmetic is evaluated at runtime, not folded by the compiler. Add, subtract
and multiply check signed overflow. Division truncates toward zero and checks
zero and INT64_MIN / -1 before idiv. Failures identify the source operation,
write a diagnostic to fd 2 and exit 70. This checked policy belongs to this
experimental scalar subset, not a retroactive change to B0 or the old C0.

Success emits one ELF64 ET_EXEC for x86_64 Linux and exits 0. The executable
has a fixed entry, one RX PT_LOAD, an RW/non-executable GNU_STACK, no loader,
no dynamic libraries and no libc. Its main return follows Linux exit's low
eight bits. Values use indexed 8-byte slots in a fixed 4096-byte stack frame;
there is no heap, recursion, register allocator or optimizer.

Syntax/semantic/IR errors exit 1 with empty stdout and
input:line:col: error[C0B-NNN]: cause; hint. Compiler I/O errors use B0's status
74. An output I/O failure after emission begins may leave a partial stream;
the source wrapper publishes the executable only after both stages succeed.

## Storage

All addresses refer to the B0 runtime's zero-initialized 65536-byte arena.

| Region | Purpose |
| --- | --- |
| 0..16400 | NQAF header, 8192 source bytes, 512 nodes, overflow byte |
| 16512..17023 | Identifier roles |
| 17152..17663 | Node ownership marks |
| 18000..19023 | Subtree-start IDs during validation, then resolved local slots |
| 19456..20479 | Declared binding IDs |
| 21000..25095 | Parsed literal immediates |
| 26000..26999 | State, source location and numeric scratch |
| 27000..29047 | Per-node runtime diagnostic prefix spans |
| 29800..29927 | Inactive writes |
| 30000..62767 | ELF buffer; code below file offset 24000, data at 24576 |
| 63000..64511 | Compiler diagnostic text and numeric buffers |

No file descriptor or heap allocation is owned by the backend. Every loop
consumes an input byte, advances a node/name comparison, or terminates.
Header/node bounds are checked before derived addresses are dereferenced.

## Reproduce

```sh
bootstrap/compiler/c0/x86_64-linux/materialize-backend.sh
bootstrap/compiler/c0/x86_64-linux/compile-source.sh program.nql program
bash tests/bootstrap/c0_backend.sh
```

The wrapper is experimental and does not replace nqlc. Neither component can
yet compile its own source. Full Compiler and self-hosting remain unverified.
