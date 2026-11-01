# C0.33 Structural Return Analysis

C0.33 extends the experimental frontend/backend pair with a bounded proof that
every normal function path returns. An exhaustive `if/else` no longer needs a
redundant outer `return`. This uses existing syntax and NQAF nodes; it adds no
type, primitive, runtime helper, optimizer pass or bootstrap stage.

```text
fn choose(value) {
    if value { return 7 } else { return 9 }
}
fn main() { return choose(1) }
```

## Decision And Semantics

Status: implemented experimental component contract. This scoped decision
extends the historical terminal-return requirements in `CONTROL_FLOW.md`,
`FUNCTIONS.md` and `NATIVE_OS.md`. It is not a new stable language promise or a
numbered, formally accepted RFC.

Each block has one summary: whether its statements guarantee a return. The
frontend computes it while parsing; the backend independently recomputes it
after validating the graph and structured statement stream.

| Construct | Return guarantee |
| --- | --- |
| `return expression` | Yes |
| `if condition { then } else { other }` | Both arms must guarantee return |
| `if condition { then }` | No new guarantee |
| `unsafe { body }` | Inherits the body's guarantee |
| `while condition { body }` | No new guarantee |
| A sequence of statements | Preserves any earlier guarantee |
| Empty block, declaration, assignment or call statement | No new guarantee |

Every function, including `main`, must have a guarantee at its closing brace.
Analysis does not evaluate constant conditions, infer termination, or treat a
call as a `noreturn` operation. Even `while 1 { return 7 }` needs a following
return. This deliberately conservative rule avoids depending on an optimizer
or a general termination proof.

A direct `return` remains the final statement of its own block. Previously
accepted statements after an exhaustive conditional retain their existing
semantic and permission checks, even when unreachable. A return in one function
or a prior sibling block cannot supply another function or block's proof.
There is no branch elimination or change to expression evaluation order.

Missing source return paths produce located `C0P-004`, exit 1 and no AST:

```text
input:1:25: error[C0P-004]: invalid syntax; expected fn name(parameters) with a return on every path
```

The example above is the diagnostic for `fn main(){if 1{return 7}}`.
Independently incomplete NQAF is rejected with located `C0B-002`, exit 1 and
no ELF prefix. Existing diagnostic codes and source coordinates are preserved;
the `C0P-004` explanation now describes the return-path requirement.

## Representation, Cost And Trust Boundary

NQAF/1..6 header/record layouts, dialect meanings, node kinds and ownership
rules are unchanged. The same existing structured delimiters express the new
accepted programs. C0.33 is the minimum backend for the newly accepted node
sequences; upgrade the experimental component pair together. An older backend
may reject a new program even though it recognizes every individual node.

The frontend uses bytes 1 and 2 of its existing sixteen-byte control records
for the block and saved then-arm summaries. The backend keeps its old direct
return syntax guard separate, and uses bytes 2 and 3 for independent summaries.
Function entry, block entry and else transitions initialize the applicable
state. Joins propagate only after validating the matching delimiter. The
backend may reuse the records only after validation has finished.

Storage remains bounded by the existing 64-block depth limit. There is no new
allocation, descriptor or generated instruction sequence. Validation performs
constant additional work per statement/delimiter. Seed/source sizes are measured
by the artifact and build gates; no capacity has been raised for this change.
Existing accepted source retains the same AST and executable bytes in the
compatibility corpus. This is byte evidence for that corpus, not a performance
benchmark or a proof for every possible source.

The security boundary is untrusted source/NQAF becoming an executable claimed
to return from every function. The backend trusts neither a producer flag nor
a frontend-supplied flow bit. This local property does not establish general
NolQu-L Safety, full AST/source authentication, or total program termination.

## Invariants And Validation

`tests/bootstrap/test_c0_return_flow.py` supplies these permanent checks:

| Invariant | Test methods |
| --- | --- |
| RF01: exhaustive branches return through native frames | `test_exhaustive_branches_and_recursive_calls`, `test_scope_joins_and_runtime_effects` |
| RF02: one arm or a loop cannot supply a false proof | `test_missing_paths_and_loops_remain_rejected`, `test_backend_rejects_incomplete_rewritten_wire_and_stale_functions` |
| RF03: state cannot leak between blocks or functions | `test_backend_rejects_incomplete_rewritten_wire_and_stale_functions`, `test_depth_wide_spans_and_both_profiles` |
| RF04: unreachable code retains semantic/unsafe checks | `test_unreachable_checks_and_legacy_bytes` |
| RF05: backend checks independently; old bytes remain deterministic | `test_backend_independently_accepts_exhaustive_wire`, `test_unreachable_checks_and_legacy_bytes` |
| RF06: source rejection explains the proof obligation | `test_missing_return_diagnostic_explains_the_proof` |

`c0_backend.sh` requires the nine-method suite and emits `PASS c0-return-flow`.
The actual B and C component pairs each run
`test_generation_return_flow_contract` as an additional named oracle, bringing
their reviewed selector set from 41 to 42. MCP binds the input identities,
requires this gate marker and the complete selector set, and leaves
`return_flow_verified` false until the full proof passes. Metadata alone is
not execution evidence.

The earlier Native frontend fixture requiring an outer return after a direct
returning unsafe body is now a positive check in both profiles. An unsafe body
with only one returning conditional arm remains a negative case. This is an
intentional acceptance extension under the contract above.

Tests include independent valid-wire rewrites, incomplete/stale-function
rejection, recursion, runtime side effects, unsafe joins, depth 64/65, wide
spans and both arena profiles. Deterministic seed builds use B0; Python and
QEMU remain host test/execution tools. Existing byte parity and failure-path
suites remain required. No NolQu-L sanitizer or exhaustive proof is claimed.

## Compatibility And Rollback

| Axis | Impact |
| --- | --- |
| Source syntax/semantics | Additive acceptance of existing structured syntax; old accepted behavior preserved |
| CLI, runtime, ABI and FFI | Unchanged |
| NQAF binary layout | Unchanged; new accepted topology requires C0.33 backend |
| Diagnostics | Same codes/locations; clearer `C0P-004` text |
| Bootstrap | Same Machine -> Stage 0 -> B0 -> Core topology; paired component pins change |
| Release version/maturity | `1.0.0-alpha.1`, `dev`; experimental; no release promotion |

Rollback restores the prior frontend/backend source, seeds, pins and matching
host proof contract as one pair. It preserves unrelated work and all failure
evidence. Full Compiler, formal self-hosting and Verified `nqlc` remain
`NOT_IMPLEMENTED`.
