# C0.35 Signed i64 Bitwise Operations

Status: PROPOSED, unnumbered experimental implementation contract for `&`, `^`,
`|` and prefix `~`. Qualification requires the exact-pair gates below; source
presence is not a passing gate or an accepted RFC. Public
version remains `1.0.0-alpha.1`, Dev remains Alpha, and no release is implied.
[UNARY_NEGATION.md](UNARY_NEGATION.md) and earlier component contracts retain
their historical scope. Full Compiler, formal self-hosting and Verified nqlc
remain NOT IMPLEMENTED.

## Source Semantics And Precedence

Each operation acts on all 64 two's-complement bits and returns the signed i64
interpretation. `~0` is -1; bitwise results are not normalized to booleans.
Binary operands evaluate eagerly, left to right, exactly once each; `~`
evaluates its operand once. Bitwise operations have no arithmetic overflow
fault. Checked arithmetic inside an operand retains its checks, effects and
fault order: `0 & (1/0)` still faults. An unselected control-flow arm still
does not execute.

Precedence, highest first:

| Level | Operators | Association |
| --- | --- | --- |
| Call / grouping | `f(...)`, `(expression)` | Existing primary rules |
| Prefix | `-`, `~` | Right |
| Multiplicative | `*`, `/` | Left |
| Additive | `+`, `-` | Left |
| Relational | `<`, `<=`, `>`, `>=` | Left |
| Equality | `==`, `!=` | Left |
| Bitwise AND | `&` | Left |
| Bitwise XOR | `^` | Left |
| Bitwise OR | `\|` | Left |

Thus `1|2^3&4` is `1|(2^(3&4))`, `6&3==2` is `6&(3==2)`, and `-~7`
is `-(~7)`. This deliberately experimental Core precedence differs from R0's
shared bitwise/additive level. R0 is unchanged. Unparenthesized mixed expressions
cannot establish differential equivalence; any R0 overlap comparison must
fully parenthesize the expression and stay within common defined semantics.
Canonical precedence has its own independent oracle. Shifts, short-circuit
logic and unary plus are outside this extension.

The INT64_MIN literal exception remains NEGATE-only. Magnitude
`9223372036854775808` requires a uniquely and directly owning kind47 NEGATE;
grouping remains transparent. `~(-9223372036854775808)` is valid and yields
9223372036854775807. `~9223372036854775808` and
`-(~9223372036854775808)` retain C0B-005 before ELF output: NOT cannot grant or
propagate literal permission. Negating the minimum value at runtime still
faults with located C0R-001, exit 70; diagnostic-write failure retains exit 74.

## NQAF/8 And Independent Validation

Actual bitwise syntax selects NQAF/8, wide32, dialect 7, runtime profile 0 or 1,
with function envelopes. It reuses the 32-byte header and 32-byte records,
little-endian u32 spans/IDs and zero reserved fields. Comments and unchanged
source do not activate the dialect: source without the new syntax retains
its exact previous NQAF/1..7 bytes and successful ELF bytes.

| Kind | Operation | Source anchor | Ownership |
| --- | --- | --- | --- |
| 48 AND | `&` | Exact one-byte `&` | Contiguous left/right postorder subtrees |
| 49 XOR | `^` | Exact one-byte `^` | Contiguous left/right postorder subtrees |
| 50 OR | `\|` | Exact one-byte `\|` | Contiguous left/right postorder subtrees |
| 51 NOT | `~` | Exact one-byte `~` | Unique left root immediately preceding NOT |

All four kinds have zero flags and `next`; NOT also has zero `right`. For
binary nodes, the right root immediately precedes the parent and its subtree
begins immediately after the left root. Subtrees stay uniquely owned within
their statement. Kinds48..51 are valid only in /8. NEGATE kind47 remains valid
in both /7 and /8; earlier formats cannot carry it.

The backend independently validates version/dialect/profile, reserved fields,
spans, source spelling, graph topology, ownership, physical statement chains,
bindings and return structure before ELF output. Native calls under any new
node retain independent lexical unsafe source containment and range checks.
Literal permission derives from validated integer-kind/NEGATE ownership, never
NOT or call-arity metadata. Invalid syntax/wire retains located C0P/C0B errors
and empty AST/ELF output; an output syscall failure may still leave a partial
stream, so consumers must check exit status. This is bounded source
correspondence, not complete AST/source authentication.

## Machine Cost And Bounds

| Operation | Instruction bytes | Per-node emission, excluding operands |
| --- | --- | --- |
| AND | `48 21 c8` (`and rax,rcx`) | 24 bytes |
| XOR | `48 31 c8` (`xor rax,rcx`) | 24 bytes |
| OR | `48 09 c8` (`or rax,rcx`) | 24 bytes |
| NOT | `48 f7 d0` (`not rax`) | 17 bytes |

Binary cost is two seven-byte slot loads, one three-byte instruction and one
seven-byte store; NOT uses one load, instruction and store. There is no bitwise
overflow branch or runtime diagnostic prefix. Binary reduction consumes two
live values and produces one; NOT consumes and produces one. Code-start
metadata inherits the left subtree/operand start so loop back-edges reevaluate
the complete condition, including calls and effects.

The existing bounded shunting-yard stacks advance input or reduce the operator
stack; prefix chains introduce no recursive parser. Source/token/node limits
remain 262,144/65,536/65,536, with the existing 16 MiB compiler arena. Generated
programs retain the 4,096-byte frame, 512 total permanent/peak temporary i64
slots, six arguments, call depth 64 including main and combined control depth
64. Runtime arenas remain 65,536 bytes for profile0 and 16 MiB for profile1
when required. No arena, capacity increase, descriptor, heap, helper or
canonical dependency is added; B0 is unchanged. Code size is specified here;
no execution-speed improvement is claimed.

## Threat Boundaries And Testable Invariants

Untrusted source crosses lexer/parser validation; untrusted NQAF crosses an
independent backend validator before machine bytes. Both run with ordinary
process privileges. Threats include malformed-wire corruption, silent
wrong-code, parser nonprogress/resource exhaustion, unsafe-call permission
escape and artifact/proof drift. This extension adds no shell, path,
privileged operation or source-disclosure capability, and does not expand the
existing NolQu-L Safety guarantees.

The following are required checks, not a record of passing results. Method
names refer to `tests/bootstrap/test_c0_bitwise.py` unless otherwise stated.

| Invariant | Named checks |
| --- | --- |
| BW01: full-width signed results, defined precedence and bounded parsing | `test_all_bits_against_independent_integer_oracle`, `test_precedence_and_prefix_associativity`, `test_legacy_bytes_and_bounded_prefix_progress` |
| BW02: eager operand effects, fault order and full loop-condition reevaluation | `test_eager_left_to_right_effects_once`, `test_fault_order_and_unselected_paths`, `test_loop_condition_and_nested_calls` |
| BW03: independent version, graph and anchor rejection before ELF | `test_independent_wire_and_version`, `test_malformed_source_and_wire` |
| BW04: NEGATE-only minimum permission; unsafe and range checks retained | `test_minimum_literal_permission_is_negate_only`, `test_safety_and_range_checks_remain`; existing `test_call_arity_is_not_literal_metadata` in `test_c0_unary_negation.py` |
| BW05: old source/wire/ELF compatibility | `test_legacy_bytes_and_bounded_prefix_progress`; existing `test_prefix_precedence_and_right_associativity` and `test_legacy_c033_bytes_and_bounded_prefix_chain` in `test_c0_unary_negation.py`; exact prior /1..7 byte parity remains required |
| BW06: exact deterministic code and genuine generation/proof identities | `test_exact_machine_operations_and_determinism`, `test_generation_bitwise_contract`; paired B0 rebuilds, actual B/C generation and fail-closed proof inventories are also required |

The inherited legacy digest corpus predates unary negation. A separate frozen
C0.34 corpus checks eight unary/native/high-offset sources in both profiles
against the retained old pair, including exact NQAF/7 and ELF identities.

The value oracle compares all 64 bits inside generated programs; low-byte
process exits alone cannot establish i64 correctness. Fixed-seed generated
values, hand-built wire, deterministic malformed-input mutations and bounded
prefix tests supply finite evidence. ASan/UBSan instrumentation of B0-generated
NolQu-L is unavailable. Coverage-guided fuzzing, exhaustive correctness and
full Safety qualification are not claimed.

## Compatibility, Qualification And Rollback

CLI, ABI, standard library, project formats and the canonical trust chain
Machine Foundation -> Stage0 -> B0 -> Core are unchanged. R0/NASM and
LLVM/Python helpers remain reference/host tooling. /8 requires a matched
frontend/backend upgrade; an older backend rejects it, while the new pair
continues accepting /1..7. Existing unary and earlier contracts remain intact.

Independent HIGH-risk review, deterministic paired B0 rebuilds, old-byte
comparisons, complete regression gates, actual B/C generation oracles and
complete fresh MCP proof on the exact pair are required. Metadata alone,
missing/skipped methods, absent markers, stale identities or incomplete
inventories must not qualify the pair. Native Termux qualification requires
separate genuine untraced receipts with TracerPid 0 at both ends; PRoot/Linux
results cannot substitute for them. Preserve raw failures and limitations.

Promotion through reused Testing requires that review, the required proof and
selected publication-manifest validation. Wrong-code, malformed acceptance,
nondeterminism, regression or missing proof blocks promotion. This contract
authorizes no version bump, release/tag, Main push or Stable promotion.
Rollback restores both sources, seeds, pins and the matching host proof contract
together from the retained immutable baseline. New source and emitted /8 then
require a compatible pair; retain original artifacts and failed evidence.
Historical C032-SIGNAL-01 remains OPEN, and Native hardlink/retention limits
retain their recorded status. Later passing tests do not identify the original
signal cause.
