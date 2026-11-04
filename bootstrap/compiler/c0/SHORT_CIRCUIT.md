# C0.36 Short-Circuit Logical Expressions

Status: PROPOSED, unnumbered experimental implementation contract. Qualification
requires independent review and the exact-pair gates below; source presence is
not a passing gate or an accepted RFC. VERSION/CHANNEL remain
`1.0.0-alpha.1`/`dev`. Full Compiler, formal self-hosting and Verified nqlc remain
NOT IMPLEMENTED. Earlier [bitwise](BITWISE.md), [unary](UNARY_NEGATION.md) and
[return-flow](RETURN_FLOW.md) contracts retain their historical scope.

## Semantics And Source Compatibility

Logical operands are signed i64. Zero is false; every other 64-bit value is true.
Each logical expression returns exactly i64 0 or 1:

| Expression | Evaluation | Result |
| --- | --- | --- |
| `a and b` | Evaluate a once; evaluate b once only when a is nonzero | 1 iff both are nonzero |
| `a or b` | Evaluate a once; evaluate b once only when a is zero | 1 iff either is nonzero |
| `not a` | Evaluate a once | 1 iff a is zero |

Skipped operands execute no call, syscall, mutation, I/O or runtime fault.
Selected operands keep the existing checked arithmetic, range checks and located
runtime errors. Both operands always undergo static name, arity, literal,
structure and unsafe-boundary checks, including an operand skipped at runtime.
`0 and missing_name` and `1 or 9223372036854775808` are compile errors. Only a
uniquely owning, direct NEGATE may admit the minimum integer magnitude; logical
NOT and conditional reachability confer no literal permission.

Precedence, highest first: calls/grouping; right-associative prefix `-`, `~`,
`not`; `*`/`/`; `+`/`-`; relational; equality; bitwise `&`; bitwise `^`;
bitwise OR; `and`; `or`. All binary operators associate left. For example,
`1 or 0 and 0` is `1 or (0 and 0)`, and `not 2 == 1` is `(not 2) == 1`.
Group expressions when a different binding is intended. Unary plus, shifts and
new boolean literals are outside this work unit.

The exact words `and`, `or`, `not` become reserved in this experimental Core
source grammar. Earlier source using those words as identifiers must rename
those bindings/functions, for example to `and_value`. Keyword prefixes such as
`and_value`, `order` and `notable` remain ordinary identifiers. This is an
explicit prerelease source compatibility change; it does not change R0 or
promise a stable public contract. Existing syntax outside those exact newly
reserved names preserves its prior AST and successful ELF bytes. Historical
wire versions retain their earlier identifier rules.

R0 has a distinct condition grammar, including its leading `not` behavior.
Differential comparisons require genuinely common, fully grouped defined
semantics; mixed unparenthesized R0 conditions are not a canonical precedence
oracle. Core precedence has independent AST and runtime tests.

## NQAF/9 And Independent Validation

Actual logical syntax selects wide32 NQAF/9, dialect8, runtime profile0 or1,
with function envelopes. The 32-byte header/records, u32 little-endian spans and
IDs and zero reserved fields are unchanged. Comments and keyword prefixes do
not select the dialect. New kinds are invalid in /1..8:

| Kind | Anchor | Ownership |
| --- | --- | --- |
| 52 logical AND | Exact three-byte `and` | Contiguous left/right postorder subtrees |
| 53 logical OR | Exact two-byte `or` | Contiguous left/right postorder subtrees |
| 54 logical NOT | Exact three-byte `not` | Unique immediately preceding left root |

Flags and `next` are zero; NOT also has zero `right`. The right root immediately
precedes its binary parent, and the right subtree starts immediately after the
left root. Anchor boundaries independently reject slices of identifiers.
NEGATE47 and bitwise48..51 remain valid in /9 and in their original versions.
The /9 backend rejects logical words used as identifier anchors. It still
accepts /1..8 with their original version-specific rules.

The backend validates framing, versions, profiles, reserved fields, spans,
anchors, topology, unique ownership, physical statement order, lexical bindings,
return paths and native unsafe source containment before emitting any ELF.
Invalid source/wire retains located C0P/C0B/C0S errors and no artifact bytes.
Output syscall failure can leave a partial stream, so callers must check status.
This is bounded correspondence, not complete AST/source authentication.

## Machine Cost, Slots And Memory

The existing contiguous postorder representation is preserved. A u32 table
indexed by each logical node's unique left root associates it with its parent.
Immediately after LHS emission, before the first RHS subtree instruction:

1. Load LHS from its live frame slot and `test rax,rax`.
2. `setne al; movzx eax,al`, then store the normalized value to the parent slot.
3. `jz rel32` for AND or `jnz rel32` for OR skips the entire RHS and its join.

SETNE, MOVZX and MOV preserve TEST flags. The selected RHS path loads its root,
normalizes with TEST/SETNE/MOVZX and stores to the same parent slot. Both paths
meet after that store. Logical NOT uses TEST/SETE/MOVZX and one result store.

Expected exact per-node emission, excluding operands: binary guard 29 + join 23
=52 bytes, NOT 23 bytes. Tests derive main entry independently and compare the
whole small fixture body and branch displacement, including node boundaries.
There is no logical overflow branch, runtime helper or hidden recursive walk.

The postorder live-value stack retains LHS during RHS compilation. A logical
binary consumes two values and reuses the lowest consumed temporary slot;
its guard can safely write that slot before the RHS begins. NOT consumes and
produces one value. Subtree code-start inherits LHS (or the unary operand), so
while back-edges reevaluate all selected effects on every iteration.

The new u32 map occupies existing spare compiler arena `[0x790000,0x7d0000)`:
65,536 entries / 262,144 bytes. Pending rel32 offsets use the logical parent's
otherwise unused tagged-data entry. No compiler arena, source/token/node,
frame, call-depth, runtime arena or output bound increases. Existing limits
remain 262,144 source bytes, 65,536 tokens/nodes, 16 MiB compiler arena,
8 MiB output, 4,096-byte frames/512 slots, six parameters and 64 active calls
including main and 64 combined structured scopes. Runtime byte arenas remain
65,536 bytes/profile0 or explicit 16 MiB/profile1 when needed.

## Trust Boundaries And Qualification

Untrusted source or serialized AST crosses the compiler arena boundary and
controls the generated machine artifact. Plausible failures include invalid
indices or fixups, stale slot reads, incorrect skipped effects, hidden faults,
unsafe-call authorization bypass, denial of service and proof/artifact drift.
This work adds no filesystem, shell, privilege, external compiler, heap or
runtime dependency. B0 remains the predecessor of both Core components; Python,
QEMU and R0 are host/reference test tools.

Required invariants: SC01 normalized full-width truth and precedence; SC02
selected effects once and skipped effects absent, including loops/calls;
SC03 independent graph/version/keyword boundaries before output; SC04 static
unsafe/name/arity/MIN checks remain active on skipped paths; SC05 prior source,
wire and ELF parity; SC06 exact deterministic branches and genuine generation
proof identities. The named tests in `test_c0_short_circuit.py`, retained
bitwise/unary/native/return/capacity suites, paired B0 rebuilds and actual B/C
oracles are required evidence. Proofs fail closed on missing/skipped methods,
missing markers, stale identities, invalid streams or incomplete generations.

| Invariant | Required named tests |
| --- | --- |
| SC01 truth/precedence/progress | `test_full_i64_truth_normalization`, `test_precedence_prefixes_and_left_associativity`, `test_exact_keywords_and_identifier_boundaries`, `test_finite_malformed_input_and_prefix_chains` |
| SC02 conditional effects/faults | `test_left_to_right_selected_effects_once`, `test_skipped_streams_and_syscalls`, `test_nested_calls_preserve_pending_guards`, `test_loop_rechecks_lhs_and_selected_rhs`, `test_skipped_faults_and_selected_error_locations` |
| SC03 independent serialization/indices | `test_independent_wire_and_profiles`, `test_wire_versions_anchors_and_ownership_reject`, `test_high_u32_ids_offsets_and_guard_map` |
| SC04 static safety/semantics | `test_skipped_static_semantic_safety_and_minimum_rejection` plus retained native/arity/unary suites |
| SC05 compatibility | `test_legacy_c035_bytes_unchanged` plus retained earlier exact-byte corpus |
| SC06 exact machine/generation identity | `test_exact_machine_bytes_and_branch_destinations`, `test_generation_short_circuit_contract`, paired B0 rebuilds and fail-closed proof controls |

Run focused and subsystem tests per change; complete regression, actual B/C
component comparisons and untraced Native/Linux qualification before promotion.
Finite deterministic mutations are limited fuzzing: they do not establish
coverage-guided coverage, exhaustive correctness or absence of vulnerabilities.
Host sanitizers cannot instrument these syscall-only NolQu-L binaries; no
unsupported sanitizer or formal Safety claim is made.

Upgrade both component sources, seeds, pins and proof contract together.
Rollback restores that matching set from the retained immutable baseline.
Private raw evidence and failed attempts stay local; publish only concise
implementation contracts/notes. Historical C032-SIGNAL-01 remains OPEN and
historical retention remains PARTIAL; later passing evidence cannot close it.
Review plus required exact CI/proof gates govern Testing/Main/Dev integration.
This work unit authorizes no release/tag, public version bump or Stable
promotion.
