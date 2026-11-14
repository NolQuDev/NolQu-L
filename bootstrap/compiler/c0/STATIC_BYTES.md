# C0.39 Static Byte Values

C0.40 adds bottom to these historical finite type rules. Existing static-byte
representation and lifetime remain; [NEVER.md](NEVER.md) defines divergent
initializers/assignments and explicit nonreturning result annotations.

Maturity: EXPERIMENTAL. This unnumbered design record is PROPOSED; no formal
RFC acceptance or stable language promise is implied. Qualification requires
the matched frontend/backend pair, independent review and executed gates below.
Public version remains 1.0.0-alpha.1, channel dev. Full Compiler, formal
self-hosting, Verified nqlc and complete NolQu-L Safety remain unimplemented.

## Source And Value Model

A double-quoted literal denotes immutable bytes with program lifetime.
Printable ASCII bytes32..126 may appear directly except quote/backslash.
Supported escapes are backslash followed by0,n,r,t,doublequote,backslash,
or x and exactly two hexadecimal digits (either case). They denote NUL,
LF,CR,TAB,quote,backslash or the chosen byte. All256 byte values are expressible.
Raw controls, non-ASCII and incomplete/unknown escapes are rejected at the
opening quote with C0P-015/1 and no AST. Empty literals are valid. A byte length
includes embedded NUL and excludes any implicit terminator: none is added.

The finite Core type rules are:

| Value/context | Rule |
| --- | --- |
| Decimal, parameters, arithmetic and call results | i64 |
| Quoted literal | Static byte string |
| let name = value | Infer its exact value type after the initializer |
| Assignment | Require the existing binding's type |
| Local alias/shadow | Copy the value; retain existing lexical scope rules |
| Operators, conditions, return and ordinary call arguments | Require i64 |
| Builtin write(value) | Require one static byte string; return written length as i64 |

Both selected and unselected source paths are checked. Unsafe scopes retain
type checking. User function parameters and returns remain i64; string
parameters/returns, concatenation, equality, indexing, conversion, dynamic
allocation and general Unicode strings are not implemented by this subset.
No additional keyword is reserved. This is bounded inference for two value
classes, not the full type system or ownership checker.

An exact global function named write resolves before the builtin, including
wrong-arity shadows. Ordinary variables/prefix names and old user write
functions retain their behavior. With no such function, write(value) performs
complete fd1 output and returns the full byte count. Empty output returns0
without a syscall. EINTR and short writes retry; zero progress/failure produces
the existing located C0R-006/74 diagnostic. Failed diagnostic output remains74.

## Representation, Lifetime And Resources

A string value occupies one8-byte frame slot containing a handle to an
aligned16-byte read-only descriptor:

| Descriptor offset | Field |
| --- | --- |
| 0..7 | u64 address of immutable payload bytes |
| 8..15 | u64 byte length |

The descriptor and payload reside in the executable RX segment for its entire
lifetime. Copying a binding copies the handle. There is no string heap,
reference counter, allocation syscall, descriptor acquisition or cleanup.
No raw-address conversion is introduced. Another resolved arena intrinsic
retains its existing runtime profile and mapping ownership.

This supports readable Systems Programming and inspectable machine cost in
the same Core pipeline. The two programming paths are independent of Balanced,
Safe and Unsafe. Balanced remains the design default. Unsafe raw syscalls still
have process authority; this value class does not turn lexical checks into an
OS sandbox or establish complete NolQu-L Safety.

## NQAF/12 And Independent Validation

Actual literal syntax or a resolved unshadowed write call selects wide NQAF/12,
dialect11, runtime profile0/1. Header/record size remains32 bytes with u32
spans/IDs and zero reserved fields. Kind58 is a leaf with the full raw quoted
span; flags,left,right,next are zero. /1..11 reject kind58. A valid /12 stream
need not contain a literal. The dialect is an internal transport version,
not a second source language or programming path.

The backend independently checks framing, spans, graph/statement order,
unique ownership, exact literal syntax/escapes, names/arity and the finite
type rules before ELF publication. Invalid literals use C0B-011/1; incompatible
values use C0B-012/1. Failure emits no ELF prefix. Existing malformed-graph and
diagnostic contracts are retained.

Literal spans in physical record order must be ascending and disjoint. Reusing
or reversing a quoted source range is rejected before decoding that node. This
bounds aggregate literal decoding by the source limit, even on independently
supplied graphs; a large span cannot be replayed once per node.

The native source correspondence scan ignores quoted contents and escaped
quotes as well as line comments. Braces, comment markers, unsafe text and raw
intrinsic names inside literals do not authorize calls or alter lexical
ownership. This remains bounded source correspondence, not authentication of
every AST/source byte. Untrusted source should enter through the frontend.

## Machine Cost And Storage

Each literal emits17 bytes for movabs of the descriptor handle and its indexed
slot store, excluding surrounding expressions. The static pool adds the decoded
payload, a16-byte descriptor and0..7 alignment bytes per literal; there is no
runtime decoding or hidden NUL copy. Variable copying retains existing slot
loads/stores. The26-byte write adapter at file0x600b00 loads descriptor fields,
returns immediately on empty input or tail-jumps to the existing complete-write
entry at0x600340. Returning paths preserve callee-saved state and alignment;
syscall clobbers and fatal diagnostic/cleanup rules remain explicit.

The adapter uses the existing shared stream-runtime layout. A small write
program currently produces an executable of roughly 6 MiB; this fixed-layout
size cost remains a limitation. The26 bytes above describe the adapter's
incremental instructions, with descriptor/payload and shared-runtime storage
accounted for separately.

A u8 type table occupies spare compiler arena[0x7d0000,0x7e0000), after the
logical-parent map and before inactive scratch. Kind-tagged16-byte data entries
hold a string's descriptor address at0..7 and decoded length at8..11. Function/
call tag writes apply only to those kinds. Type inference follows name/callee
resolution; declaration type publication follows initializer validation.
Descriptors/payloads append after source-prefix data within the existing RX
buffer. Alignment, total length and every store are bounded first.

Source262144, token/node65536, compiler16MiB, output8MiB, frame4096/512slots,
arity6, combined depth64 and existing runtime arena profiles are unchanged.
No B0 bridge or canonical dependency is added. Python/QEMU/disassembly remain
host testing tools. No runtime speedup or general memory-safety proof is claimed.

## Invariants And Required Tests

SB01: quoted source and independent /12 records validate without out-of-range
reads, nonprogress or partial success. SB02: no implicit i64/byte-handle
coercion, including skipped/unsafe paths. SB03: immutable RX descriptors preserve
length, binary payload and program lifetime. SB04: string text cannot launder
native permission; exact user shadows remain authoritative. SB05: complete,
empty and failed output preserve observable bytes/counts/register/resource
contracts. SB06: old bytes, deterministic builds and actual B/C typed output
oracles fail closed when evidence is missing or stale.

Permanent tests include independent wire packing, all256 escaped bytes, both
hex cases, empty/large payloads, alias/assignment/scope/loop behavior, wrong
operand/context types, function shadows, native quote containment, truncated/
mutated fields, high spans/IDs, exact machine/data checks and I/O failures.
Expected output uses independent byte fixtures; full counts are checked in the
guest before converting return status. The named generation static-byte selector
must run against each actual B/C pair, with invalid-type rejection as well.

Finite deterministic mutation/watchdog tests are bounded host checks.
Coverage-guided fuzzing, canonical memory sanitizers, full lifetime analysis and
exhaustive correctness are not available or claimed. Actual Native evidence
must record TracerPid0 before/after; PRoot and host simulation are separate.

## Compatibility, Qualification And Rollback

Old source retains its exact /1..11 choice and successful ELF bytes, including
quotes in comments and exact user write shadows. New /12 needs a matched
component upgrade. CLI, old diagnostics, i64 calling convention, project format,
capacities and predecessor trust chain remain. B0, emitterC0.25 and bounded
successor stay unchanged.

Required gates: targeted/source/backend/security regressions, unchanged-source
byte parity, deterministic B0 rebuilds, actual full-source A/A and B/C component
comparison plus named string oracles, relevant full main/MCP/publication/release
checks, actual Native qualification and independent HIGH-risk review. Metadata
alone cannot grant verification. Passing subset generations do not establish
Full Compiler or formal full-language self-hosting.

Rollback restores the complete matched C0.38 source/seed/pin/test/proof set.
Preserve originals and failed evidence. Historical C032-SIGNAL-01 remains OPEN;
Native full-MCP/real-hardlink qualification and evidence-retention limits remain
separately documented. No release, tag, Stable or public-version promotion is
authorized by completing this milestone.

