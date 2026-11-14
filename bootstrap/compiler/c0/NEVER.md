# C0.40 Bottom Contracts And Logical Bang

Maturity: EXPERIMENTAL. This unnumbered design record is PROPOSED; it does
not imply formal RFC acceptance or a stable language promise. Qualification
requires the matched component pair, independent review and the gates below.
Public version remains 1.0.0-alpha.1, channel dev. Full Compiler, formal
full-language self-hosting, Verified nqlc and complete NolQu-L Safety remain
unimplemented.

## Design Rationale

The result contract uses a real bottom type so expression composition cannot
invent an i64 result. A function-only unchecked noreturn attribute would leave
that gap. Return-position syntax is deliberately bounded by the existing Core
type system; it does not imply general typed parameters or generic containers.
Logical bang follows NolQu-L's existing `not` operation, while `~` keeps bitwise
complement. Nullable assertions, error unions and macro/mutation spellings need
their own value, failure and effect contracts before receiving a bang role.
The defined return guard preserves machine behavior if a target violates its
contract, rather than granting an unchecked optimizer assumption.

## Source Contract

Select this experimental component pair with the existing compiler driver:

```sh
./nqlc --backend canonical program.nql -o program
```

```text
fn forever() -> ! { while 1 {} }
fn recurse() -> ! { recurse() }
fn main() { if !0 { return 7 } else { return 9 } }
```

`!expression` has exactly the logical meaning and prefix precedence of
`not expression`: i64 zero produces 1; every nonzero i64 produces 0. Prefixes
associate right. `!!x` therefore normalizes truth. `~` retains its existing
bitwise meaning. Maximal token recognition preserves the existing `!=` token.

`-> !`, after a function's parameter list, declares that an invocation cannot
return normally. The arrow is contiguous; legal whitespace and line comments
may separate the arrow, bang and body. An unannotated function retains its i64
result contract. `Never` remains a valid ordinary identifier. Parameters retain
the existing i64 syntax, with at most six arguments. General type annotations,
optional assertions, error unions, mutation suffixes and macros are outside
this extension.

A bottom type has no value, payload, default zero or conversion from an
inhabited value. It is distinct from unit/void, null and an empty byte string.
A declared-bottom body must have no normal continuation and no inhabited
return, including explicit inhabited returns in unreachable source. A return
whose operand diverges has no normal return edge. `main` may declare `-> !`;
startup then expects no return value or exit-status conversion.

The analysis recognizes nonreturning declared calls after exact global name
and arity resolution, and a loop whose condition is an exact nonzero integer
literal. Unknown conditions remain conservative. This is a bounded structural
analysis, not a general termination proof. Core still has no break/continue or
exception model. Future loop-exit syntax must revise the loop rule explicitly.
Recursive and mutually recursive declarations are checked as one compilation
unit; every body must satisfy its own result contract. The existing depth limit
may still cause a controlled fault: Never promises absence of normal return,
not unlimited execution time or a particular exit status.

## Type And Flow Rules

The internal finite type tags are i64=1, static bytes=2 and bottom=3. A bottom
expression satisfies an existing concrete context without producing or
converting bits. `let x = recurse()` retains bottom; it does not infer i64.
Assignment may diverge before supplying the binding's existing type. An
inhabited assignment to a bottom binding is rejected. Such a binding has no
generated value load/store; the unchanged fixed frame budget is still reserved.

Strict expressions evaluate children left to right, then propagate bottom.
All names, argument counts, operand types and native permission boundaries
are checked, including later or unreachable source. A bottom argument prevents
the enclosing call from executing and cannot hide a bad type in another
argument. A bottom left operand of `and`/`or` prevents both continuations.
Bottom on the right alone leaves a reachable normalized i64 short-circuit
result. The compiler must never load a missing RHS result on a diverging path.

The backend independently tracks normal continuation, inhabited return and
divergence. Sequences propagate later edges only from normal predecessors;
branches join their reachable edges; an absent else retains the false normal
edge. Unsafe blocks preserve the same type and result obligations. A producer's
annotation is not itself a proof of nonreturning behavior.

Possible expression divergence is tracked separately from its value type.
Thus an inhabited `x and recurse()` has both a normal short-circuit edge and
a recognized diverging edge. Strict parents, argument prefixes, initializers,
assignments and conditions retain that fact. The summaries conservatively
approximate recognized divergence; they do not enumerate every runtime fault
or prove the behavior of an ordinary unannotated callee.

Both Systems Programming and Assembly-Level Systems Programming use these
same types and compiler rules. They remain separate from Balanced, Safe and
Unsafe. Balanced is the design default. Never does not grant raw syscall or
pointer authority, establish an OS sandbox, or promise resource cleanup.

## NQAF/13 And Validation Boundary

Actual bang spelling or a bottom result annotation selects NQAF/13, dialect12,
runtime profile0/1. Header and record size stay32 bytes with u32 spans and IDs.
Source using neither retains its earlier format choice and compatibility
behavior. A stream at version13 may also contain the existing static-byte and
operator nodes. Earlier version rules remain unchanged.

| Record field | NQAF/13 rule |
| --- | --- |
| Kind54 logical NOT anchor | Exact one-byte `!` or existing three-byte `not` |
| Kind39 function flag bit0 | Declared bottom result |
| Kind39 flags other bits | Zero |
| Kind39 u32 at +24/+28, flag set | Return-annotation offset/length, from `->` through `!` |
| Kind39 u32 at +24/+28, flag clear | Zero |
| Other record flags/reserved fields | Existing rules; no new permission bits |

The backend validates complete framing, topology, ownership, source spans,
function signature order, parameter anchors, exact arrow/bang and legal trivia.
Consumed header bytes, including comments, obey the frontend's nonzero ASCII
domain and CRLF rule. Comment contents remain opaque to token recognition.
Backward trivia must stop with rejection at byte zero if no real `fn` precedes
the name; a negative cursor must never be serialized and reloaded as an index.
Quoted or commented apparent headers cannot supply a contract. Name, arity,
finite types and structured flow validate before any ELF prefix is emitted.
This is bounded correspondence validation, not general AST authentication.
Untrusted source should enter through the frontend.

For /13, the frontend parses syntax and preserves anchors; the backend owns
complete return semantics, including forward calls. A frontend-produced AST
can therefore still fail semantic validation. Old-format return checks remain
unchanged. Malformed source annotations use located C0P-016/exit1; an invalid
bottom return contract uses C0B-013/exit1. Type errors retain C0B-012/exit1.
Malformed framing/topology retains its established diagnostic family. Compile
failure produces no AST or ELF at the failing stage.

## Machine Contract And Resources

Bottom has no RAX result, return-slot store or strict-parent value operation.
Reached argument/operand effects retain their ordering, caller liveness,
alignment and depth accounting. Short-circuit joins retain a real value on
each reachable value-producing edge. Ordinary successful call code remains
unchanged on the compatibility corpus.

A17-byte guard follows each declared-bottom call and each bottom function's
physical fallthrough. At a call it replaces the ordinary7-byte result store,
giving a10-byte site delta with unchanged argument setup and native call.
If reached, it reloads the source diagnostic prefix and jumps to the defined
located C0R-011/exit70 failure. Failed diagnostic output remains74. Main's
bottom startup likewise guards a returning callee without reading its RAX.
The guard is defensive; invalid returning source bodies are still rejected.
No unchecked optimizer `unreachable` promise is introduced.

The shared bottom handler is at file0x600c00, its suffix at0x600c80 and the
main guard stub at0x600d00, within existing shared-runtime padding. Mapped-arena
paths preserve the R14 arena base and existing controlled cleanup. Prefix
logical bang uses the existing23-byte NOT emission for inhabited input;
bottom input emits only its reached child effects. Existing shared-runtime
layout also makes small /13 programs roughly6MiB, even without stream I/O.
Measured `fn main(){return !0}` emits6,309,440 bytes and recursive
`fn main()->!{main()}` emits6,309,463 bytes under profile0. Bottom's lack of
a value payload does not imply a compact executable; shared-layout compaction
is a separate unimplemented backend improvement.

These fixed shared regions are disjoint half-open file intervals. Existing
shift diagnostic storage remains intact when /13 selects both features.

| Region | File interval |
| --- | --- |
| Static byte write adapter | `[0x600b00,0x600b1a)` |
| Shift fault adapter | `[0x600b80,0x600b91)` |
| Bottom fault adapter | `[0x600c00,0x600c11)` |
| Existing shift diagnostic suffix | `[0x600c40,0x600c74)` |
| Bottom diagnostic suffix | `[0x600c80,0x600cc6)` |
| Bottom-main guard stub | `[0x600d00,0x600d11)` |

The u8 per-node result/call-mode table uses existing arena
`[0x7e0000,0x7f0000)`, after the existing type table. After complete wire,
topology and type validation, a /13-only postorder pass reuses each input
record's reserved byte at+2 in compiler memory for its possible-divergence bit.
Reserved fields remain zero at the wire boundary; no modified AST is published.
This internal reuse adds neither an arena nor a transport field.
Source correspondence
reuses spare high bytes of its existing table only for non-brace bytes; actual
brace offsets retain their old representation. Compiler diagnostic constants
are initialized by a bounded seven-byte-word loop with the same message bytes
and zero gaps. This avoids a predecessor capacity change; it is not a runtime
performance claim.

Limits remain source262144, token/node65536, compiler16MiB, output8MiB,
frame4096/512slots, arity6, active-call/block depth64 and the existing runtime
arena profiles. B0, the C0.25 emitter, bounded successor and bootstrap topology
are unchanged. Python/QEMU/shell remain host test/orchestration tools.

## Threat Model And Required Evidence

Untrusted source and NQAF cross into compiler memory and executable output
with the invoking user's privileges. Risks include malformed-input exhaustion,
forged contracts, wrong-code control flow, missing-value disclosure, unchecked
native authority and false artifact/proof promotion.

| Invariant | Permanent tests |
| --- | --- |
| NB01 bounded syntax/progress and exact rejection | frontend `test_bad_return_annotations`, `test_bounded_truncations_and_deterministic_mutations` |
| NB02 bodies and source-owned contracts validate independently | `test_reject_returning_and_fallthrough_bodies`, `test_wire_flags_spans_and_stale_versions`, `test_comment_and_quoted_headers_cannot_supply_a_contract` |
| NB03 no invented value or reordered effects | `test_strict_bottom_composition`, `test_short_circuit_bottom_rhs`, `test_argument_effect_order`, `test_bottom_local_inference_and_assignment` |
| NB04 dead code retains types/names/arity/permissions | `test_unreachable_type_name_arity_and_permission_checks` |
| NB05 wide spans/IDs and capacities remain bounded | frontend `test_wide_annotation_spans_names_and_current_function_id`, `test_source_token_and_block_bounds_in_both_profiles`; backend `test_high_name_and_span_callee_contracts` |
| NB06 returning target reaches a defined guard | `test_returning_target_faults_before_reading_a_result`, `test_bottom_main_fallthrough_guard` |
| NB07 complete actual B/C evidence is required | `test_generation_never_and_bang_contract` plus producer/consumer missing-input, selector and false-success controls |

Finite recursive tests expect the actual depth fault. Literal endless loops
are inspected, not executed indefinitely and called successful after timeout.
Guard tests deliberately modify generated machine code, then require exact
fault behavior, including mapped arenas and failed stderr. Defined-semantics
bang/not comparisons and old AST/ELF byte parity supply additional oracles.

Required qualification includes deterministic B0 builds, targeted and old
subsystem suites, malformed-input/mutation bounds, whole-source component
generations with every prior named oracle plus the new one on actual B/C
pairs, MCP fail-closed controls, independent HIGH-risk review and separate
Native/Linux receipts. Native evidence requires TracerPid0 before/after.
The named Never oracle on each actual B/C pair also executes the complete
header correspondence/progress regression, including invalid raw-byte comments.
The deterministic `test_bang_not_metamorphic_defined_i64` compares32 independent
defined integer wants under both spellings/profiles and checks single operand
evaluation. Its fixed seed and finite cases supply regression evidence, not
coverage-guided fuzzing or a cross-language semantic equivalence claim.
Coverage-guided fuzzing and NolQu-L ASan/MSan/TSan instrumentation are unavailable;
finite tests do not establish exhaustive correctness or general memory safety.

## Compatibility And Rollback

Source syntax is additive, without a new reserved identifier. CLI, project
format, existing static-byte APIs and ordinary i64 ABI remain. New /13 and
bottom contracts require a matched frontend/backend upgrade. Restore the
matched C0.39 source/seed/pin/test/proof set to roll back, preserving unrelated
work, originals and failed evidence.

Completing this component milestone does not publish a release or qualify
Stable. Historical C032-SIGNAL-01 remains OPEN; full Native MCP/real-hardlink
qualification and evidence-retention limitations remain separately documented.
