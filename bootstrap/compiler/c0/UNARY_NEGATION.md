# C0.34 Checked Unary Negation

This experimental component contract adds prefix `-` to canonical C0. It is
additive source functionality, with an explicit NQAF/7 compatibility boundary.
It does not change the public Alpha version, ABI, bootstrap stages or safety
modes. Full Compiler and formal self-hosting remain NOT IMPLEMENTED.

## Scoped Design Decision

Decision record: PROPOSED, unnumbered; the experimental implementation and its
qualification are tracked separately. No formally accepted RFC is claimed.
The existing indexed expression tree can represent unary negation by adding
one node kind. It does not need a new general IR or parser architecture.

A synthetic `0-x` tree would require a zero literal without a source anchor,
conflicting with the backend's literal contract and adding an unnecessary
node. Supporting negative literals alone would leave `-local`, `-call()` and
parenthesized operands unsupported. The chosen node preserves the actual
operator location, one operand and the existing postorder ownership rules.

## Grammar And i64 Semantics

```text
unary   := "-" unary | primary
primary := decimal | identifier | call | "(" expression ")"
```

Calls and primary grouping bind tighter than prefix negation; negation binds
tighter than multiplication/division. Repeated prefix minus associates right:
`--x` means `-(-x)`. Binary minus retains its existing left associativity.
Unary plus is not implemented by this contract. Existing `#` and `//` comments
and whitespace remain lexical separators.

Evaluate the operand exactly once and preserve its observable effects before
negating it. Runtime negation is checked i64 arithmetic. Negating INT64_MIN
produces the existing located `C0R-001`, exit 70; a diagnostic write failure
retains exit 74. Overflow does not wrap or become undefined behavior.

```text
fn negative(value) { return -value }
fn main() { return negative(7) }
```

The program above exits 249, the low byte of -7, according to the existing
process exit contract. Arithmetic inside the program remains signed i64.

### The Minimum Literal

The magnitude `9223372036854775808` is valid only as an integer leaf uniquely
and directly owned by a NEGATE node. Together they denote INT64_MIN, with no
observable positive out-of-range intermediate. Grouping is transparent in the
AST, so `-(9223372036854775808)` has the same meaning. Leading zeros remain
accepted. Larger magnitudes, extra digits, a bare positive magnitude, or that
magnitude inside a binary operand retain `C0B-005`, exit 1, before ELF output.

`--9223372036854775808` therefore constructs the minimum constant at the inner
minus and faults at the outer minus. `-(1+9223372036854775808)` is rejected:
the positive literal belongs to a binary node and is outside i64.

Malformed operands retain located C0P diagnostics, including `C0P-006` when
an operand is expected. The backend rejects malformed topology with C0B-002
and an invalid operator/literal anchor with C0B-006. Syntax and semantic
failures produce no partial AST/ELF. Output syscall failures still require
consumers to check the nonzero exit status.

## NQAF/7 And Independent Validation

Prefix negation selects NQAF/7, with the existing 32-byte header and record
layout, dialect 6, runtime profile 0 or 1, and zero reserved fields. Dialect 6
includes the existing function, control-flow, call, native and unsafe grammar.
Unchanged source retains its exact NQAF/1..6 representation.

| NEGATE field | Required value |
| --- | --- |
| kind | 47 |
| flags | 0 |
| anchor | the one-byte source `-` |
| left | the unique operand root, immediately preceding this node |
| right / next | 0 / 0 |

The operand subtree must be contiguous postorder and belong to the same
statement. Existing graph uniqueness, physical statement-chain, function,
lexical scope and source-span checks remain. Older wire formats cannot carry
kind 47. NQAF/7 is a superset of the existing native dialect: independently
checked unsafe source containment is still required for raw calls, including
those nested beneath negation.

The backend derives the exceptional literal permission from validated graph
ownership. It reuses only the otherwise-unused integer-node entries of the
existing per-node arity table; literal and call/parameter kinds are disjoint.
One internal tag records direct negative ownership; another records the
exceptional minimum magnitude. Neither is serialized or trusted from source.

Decimal arithmetic remains representable even in the compiler itself. Only
the final digit 8 after accumulator 922337203685477580 is exceptional; the
compiler accumulates the safe MAX value using digit 7, then writes the explicit
two's-complement minimum immediate. It never forms positive 2^63 using i64
arithmetic. All rejected/inactive operands are guarded before eager arithmetic.
The codegen exception requires both integer child kind 5 and the derived tag;
a two-argument call's arity 2 is never a literal permission.

## Machine Cost And Resource Lifetime

Parsing uses the existing bounded shunting-yard stacks: prefix push and unary
reduction advance the input or reduce the operator stack. No recursive machine
stack parser, new arena, capacity increase, descriptor or runtime helper is
introduced. Unary consumes one temporary and produces one in the existing
4,096-byte frame. Its code-start metadata inherits the operand's start, so
loop back-edges reevaluate the entire operand and its effects.

Ordinary unary emission is 35 bytes: one frame-slot load, the existing error
prefix setup, `neg rax`, overflow-conditional `jo rel32` to the shared arithmetic
handler, and one result store. The validated minimum literal pair uses its
preformed immediate and a 14-byte slot copy at the parent, with no second
negation. Error-prefix data is still bounded and source-located. Callee-saved
registers, six parameters, call depth 64 and both existing byte-arena profiles
remain unchanged. This cost description is not a speed benchmark.

## Threat Model And Testable Invariants

Entry points are untrusted source and NQAF, running with ordinary compiler
process privileges. Wrong ownership or literal permissions could cause
corruption or wrong-code; nonprogressing prefix handling could cause denial of
service. Existing native source containment limits unverified kernel effects;
this feature adds no privileged operation, path or shell interface. Pinned
source/build identities and complete proof inventories address artifact drift.
No new source disclosure capability is introduced. Full NolQu-L Safety and
complete AST/source authentication are outside this subset's guarantees.

| Invariant | Permanent tests in `test_c0_unary_negation.py` |
| --- | --- |
| UN01: precedence, progress and bounded prefix parsing | `test_prefix_precedence_and_right_associativity`, `test_legacy_c033_bytes_and_bounded_prefix_chain`, `test_malformed_prefixes_and_wire_ownership` |
| UN02: independent unary ownership and anchors | `test_independent_wire_and_literal_minimum`, `test_malformed_prefixes_and_wire_ownership` |
| UN03: minimum magnitude cannot escape its typed owner | `test_literal_bounds_and_no_extended_positive_escape`, `test_call_arity_is_not_literal_metadata` |
| UN04: effects, loop starts and unsafe checks are preserved | `test_calls_effects_and_loop_condition_start`, `test_unary_retains_native_unsafe_and_bounds_checks` |
| UN05: checked instruction/fault location is correct | `test_machine_negation_and_runtime_rejection`, `test_checked_runtime_overflow_and_operator_location` |
| UN06: compatibility and actual generation correctness | `test_legacy_c033_bytes_and_bounded_prefix_chain`, `test_generation_unary_contract` |

The dedicated backend gate requires all eleven methods and the marker
`PASS c0-unary-negation`. Actual B and C pairs each run the named generation
oracle alongside all previous oracles. MCP leaves `unary_negation_verified`
false for metadata-only reads, missing markers, incomplete suites, skipped
methods, stale inputs or invalid generation receipts. Passing finite tests is
bounded evidence, not formal absence of miscompilation or vulnerabilities.

ASan/UBSan-style instrumentation for the standalone B0-generated NolQu-L
compiler is unavailable. Malformed-input, independent-wire, generated-program,
byte-identity and actual generation tests supply the available checks.
Coverage-guided fuzzing and full-language safety qualification are not claimed.

## Compatibility, Rollout And Rollback

| Axis | Status / action |
| --- | --- |
| Existing source and semantics | Compatible; legacy AST/ELF corpus parity required |
| New source | Additive prefix-minus semantics in this experimental subset |
| CLI, standard library, project format | Unchanged |
| ABI/FFI | Calling convention unchanged; no FFI feature added |
| Wire/artifact | New NQAF/7; older backends reject it; upgrade the component pair |
| Runtime | Existing checks and fault/cleanup policy retained |
| Bootstrap/trust | Same Machine -> Stage 0 -> B0 -> Core; no host compiler dependency |
| Diagnostics | Existing codes and source-location conventions retained |
| Reproducibility | Paired B0 rebuild and actual B/C equality gates required |

The private Testing candidate receives matched frontend/backend sources, seeds
and pins after targeted regression and independent review. Integration requires
complete proof and regression gates on that exact pair. Public VERSION/CHANNEL
and release tags remain unchanged. Rollback restores that pair and its matching
host proof contract from the retained baseline; newly accepted source then needs
a compatible compiler. Original failed artifacts/evidence remain retained.
Historical C032-SIGNAL-01 and Native hardlink/retention limitations remain open
as documented in the validation status; this feature does not resolve them.
