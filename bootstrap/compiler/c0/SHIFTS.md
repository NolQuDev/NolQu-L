# C0.37 Checked Signed i64 Shifts

Status: PROPOSED, unnumbered experimental implementation contract. Qualification
requires the exact-pair gates below; this is not an accepted RFC or a stable
language promise. Public version remains `1.0.0-alpha.1`, channel `dev`.
Full Compiler, formal self-hosting and Verified nqlc remain NOT IMPLEMENTED.

## Semantics And Precedence

`a << b` and `a >> b` evaluate both operands eagerly, left to right, exactly
once. The full signed i64 count must be in `0..63`. An executed invalid count
faults with `input:line:column: error[C0R-010]: shift count out of range; use 0..63`
and exit70. Failed diagnostic output retains exit74. Counts are never implicitly
masked to six bits. Constant counts have the same runtime semantics as dynamic
counts; a skipped branch or logical RHS does not execute a shift fault. Static
validation still checks all names, arities, literals and unsafe containment.

Left shift shifts all64 two's-complement bits, zero-fills low positions,
discards high bits and returns the signed i64 interpretation. It does not
perform checked multiplication: `1<<63` is INT64_MIN, `-1<<1` is -2.
Right shift is arithmetic and sign-extending: `-3>>1` is -2 and `-1>>63` is -1.
A zero count preserves the input, including its high/sign bits.
The NEGATE-only INT64_MIN literal permission remains unchanged.

Precedence, highest first: call/grouping; right-associative prefixes `- ~ not`;
`* /`; `+ -`; `<< >>`; relational; equality; `&`; `^`; `|`; `and`; `or`.
All binary operators associate left. Thus `1+2<<3+1` is `(1+2)<<(3+1)` and
`32>>1<<2` is `(32>>1)<<2`. A shift is one contiguous two-byte token;
spaced `< <`, `>>>`, `<<<`, `<<=`, `>>=` and unary plus are unsupported.
No names become newly reserved. R0 retains its own precedence and masked-count
contract; it is not an oracle for invalid Core counts or unparenthesized mixes.

## Wire Contract And Independent Validation

Actual shift syntax selects NQAF/10, wide32, dialect9, runtime profile0 or1,
with the existing32-byte header/records and u32 spans/IDs. Kinds55 SHL and56
ASR have exact two-byte source anchors, zero flags/next/reserved fields and
nonzero left/right roots. Right root immediately precedes the parent, its
subtree begins immediately after the left root, and every subtree stays uniquely
owned within its statement. /1..9 reject shift nodes. /10 retains NEGATE,
bitwise and logical kinds and the /9 exact logical keyword reservation.

The backend independently verifies framing/version/profile, spans/anchors,
postorder topology, statement/function order, name/arity resolution, literal
permission and native unsafe source containment before emitting any ELF bytes.
Malformed wire is rejected with located C0B diagnostic and no ELF output.
This is bounded source correspondence, not complete source authentication.
Output syscall failure can leave a partial stream; wrappers check status and
preserve the previous output with atomic publication.

## Machine Cost, Bounds And Alternatives

Each shift emits46 bytes excluding operand subtrees: two7-byte slot loads,
12-byte location-prefix setup, `48 83 f9 3f` (`cmp rcx,63`), `0f 87 rel32`
(unsigned JA), `48 d3 e0` (SHL) or `48 d3 f8` (SAR), then a7-byte result store.
Unsigned comparison also rejects every negative i64 count before CL masking.
The result reuses the lowest consumed temporary. Code-start inherits the
entire left subtree, so loop back-edges reevaluate both operands and effects.

Only actual validated shifts add the17-byte fatal entry at ELF offset6294400
and52-byte suffix at6294592, within existing spare output before source-prefix
text. The entry selects the suffix and reuses the complete-write diagnostic
handler. Profile1 keeps its live mapping ownership pointer intact for cleanup;
no runtime arena is acquired merely because a shift exists.

Source262144, token/node65536, compiler arena16MiB, output8MiB, frame4096/512
slots, six arguments, active calls64, combined scopes64 and runtime arenas
64KiB or explicit16MiB are unchanged. No heap, descriptor, B0 bridge, assembler,
linker or canonical dependency is added. Code size is specified; no speed
improvement is claimed. Compare compile cost on a fixed prior-source workload.

Implicit x86 count masking was rejected because it hides invalid high bits.
Arithmetic-overflow left shift was rejected because these are explicit bit
operations. Unsigned logical right shift needs a future typed/unsigned contract;
it is not silently substituted for signed i64 SAR. No optimizer is introduced.

## Threat Model And Required Invariants

Untrusted source crosses the lexer/parser; independently supplied NQAF crosses
the backend verifier. Both run with ordinary process privileges. Relevant
risks are parser nonprogress/resource exhaustion, malformed-wire corruption,
silent wrong-code, wrong signedness/truncated counts, call-register clobbers,
unsafe-call laundering and stale or incomplete qualification evidence.
No shell/path/privileged capability is introduced by these operators.

SH01: full64-bit defined values, signedness, all count bits, precedence and
exactly-once eager effects match an independent integer/stream oracle.
SH02: invalid executed counts fault at the operator; skipped paths remain
unexecuted and fault order/closed diagnostic descriptors retain their contract.
SH03: independent /10 graphs, anchors, versions, reserved fields and ownership
reject malformed input before output, including high source/node indices.
SH04: MIN ownership and unsafe/range checks cannot be bypassed by a shift node.
SH05: old source, /1..9 wire and successful ELF bytes remain identical.
SH06: deterministic B0 rebuilds, actual B/C named shift oracle, exact reviewed
suite inventories and missing/stale/truncated proof controls fail closed.

Permanent checks live in `tests/bootstrap/test_c0_shifts.py`, the component
generation suite and MCP controls. Generated assertions use independent `if`
checks rather than the shift operators being qualified. Deliberately incorrect
SHL/SAR/count-guard variants must fail the oracle. Fixed finite value/mutation
corpora and per-call timeouts provide bounded evidence. Coverage-guided fuzzing,
ASan/UBSan instrumentation of canonical NolQu-L and exhaustive correctness are
not available or claimed. Host Python/QEMU remain test/execution tooling.

## Compatibility, Qualification And Rollback

Unchanged source retains exact previous NQAF/1..9 and successful ELF bytes.
New /10 source/wire requires a matched frontend/backend upgrade; the old pair
rejects it. CLI, machine ABI, library/project formats, trust root and canonical
Machine Foundation -> Stage0 -> B0 -> Core topology remain unchanged.

Independent HIGH-risk compiler/proof review, affected suites, full Linux
qualification, fresh genuine Native component/proof execution, real named B/C
oracles, old byte parity, exact hashes/permissions and selected publication
manifest validation are required. Native receipts must show TracerPid0 at both
ends; PRoot or metadata alone cannot substitute. Missing/skipped methods,
wrong-code, nondeterminism, malformed acceptance or unresolved correctness
findings block integration. No release/tag or Stable promotion is implied.

Rollback restores both component sources/seeds/pins and matching proof contract
from retained C0.36. Preserve originals and failed evidence. Historical
C032-SIGNAL-01 remains OPEN with unknown original cause; Native full-MCP
hardlink qualification and historical retention retain their recorded limits.
