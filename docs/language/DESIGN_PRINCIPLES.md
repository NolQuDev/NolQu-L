# Nine Pillars of NolQu-L

NolQu-L aims to be an Assembly-Level Systems Programming Language: simple and
readable at the surface, transparent toward the machine, with explicit safety
boundaries and predictable costs. These nine pillars guide language design,
compiler development, tooling and compatibility decisions.

They are normative design principles, not a claim that every target capability
or Safety analysis is implemented. Check [feature status](FEATURE_STATUS.md),
the [canonical toolchain](../compiler/CANONICAL_TOOLCHAIN.md) and
[validation status](../project/VALIDATION.md) for the current implementation.

## Pillar 1 — Simplicity

Simple programs should have simple source. Avoid boilerplate, syntax and rules
that add work without adding useful control or clarity. Real problem complexity
may remain explicit; accidental complexity should be reduced.

Simplicity must preserve capability and visible machine costs. Inside the
compiler, prefer the simplest implementation that satisfies its actual contracts
and can be tested and audited.

## Pillar 2 — Readability

User-written NolQu-L code should make intent, structure and control flow easy to
follow. Names and constructs should explain their purpose; concise spelling
should not make common operations harder to understand.

Compiler internals also need readable engineering, while the language remains
designed first for the people writing programs in it.

## Pillar 3 — Close to the Machine

Allocations, release, copies, syscalls, calls, alignment, synchronization, ABI
conversions and runtime checks must have identifiable costs. Programmers should
be able to reason about where memory lives, when resources end and which
operations may be expensive.

On supported targets, explicit instruction, layout, memory and ABI control
should be auditable. This does not promise one source operation per instruction,
universal zero overhead or identical behavior across different ISAs. Capabilities
must be documented and verified for the target that implements them.

## Pillar 4 — Complex Inside, Simple Outside

The compiler may perform sophisticated analysis so users can write clear source
without carrying unnecessary implementation complexity. Internal difficulty
should not become extra syntax or an awkward public interface.

Analysis and abstractions must still expose the machine costs relevant to the
programmer's decisions.

## Pillar 5 — NolQu-L Safety

Memory and resource safety belong to the language design. They must connect to
types, semantics, ownership, moves, borrowing, lifetimes, checks, FFI, ABI,
concurrency and diagnostics as those facilities are implemented.

Balanced is the default and primary safety identity. Safe maximizes available
verification. Unsafe makes responsibility explicit where the compiler cannot
prove the required conditions; syntax, structural, type and other applicable
checks still remain. A safety comment states an invariant; it does not prove it.
These design modes must not be confused with the subset of checks available in
the current compiler.

## Pillar 6 — Clear Error Handling

Errors should identify a diagnostic code, location, cause and explanation, with
a concrete suggestion where possible. Ordinary malformed source should produce
a controlled diagnostic rather than an internal crash or an endless error loop.

Failures must propagate honestly through compiler stages and tooling. A failed
operation or partial artifact must never be reported as success.

## Pillar 7 — Test Before Merge

Every change needs validation appropriate to its impact: valid behavior,
rejection of invalid input and checks for unintended regressions. Tests,
examples and documentation should agree on the contract being verified.

An intentional breaking change accepted under Pillar 8 needs evidence for its
new behavior and migration path, as well as checks for collateral breakage.
Unintended regressions stop expansion of the affected work until resolved.

## Pillar 8 — Stability Without Blocking Evolution

Preserve working programs where practical, but backward compatibility is not
absolute. NolQu-L may replace a poor or limiting design when the improvement to
safety, simplicity, readability, performance, analysis or architecture justifies
the cost.

Before accepting a break, record the actual problem, evidence, alternatives,
expected benefit and verification method. Assess source, behavior, ABI/FFI,
tooling, libraries and bootstrap impact; define migration, tests, rollout and
rollback. Use deprecation where safe and reasonable. Explain exceptions needed
for security, ambiguity or disproportionate complexity.

Temporary compatibility paths need a purpose and an evaluation or removal
condition. Group changes at clear version or milestone boundaries and never
silently change the meaning of existing code. Historical notes that demand
absolute compatibility do not override this pillar.

## Pillar 9 — Optimize for Impact

Prioritize changes with meaningful effects on compilation, execution, memory,
binary size, generated code or architecture. Support performance claims with
relevant measurements; label unmeasured ideas as hypotheses.

Consider complexity, maintainability, portability and effects on other metrics.
Micro-optimization is optional when its benefit is unproven. An optimization
that breaks a contract must also satisfy Pillar 8.

## Applying the Pillars

Ask whether a change is simpler, readable, predictable at the machine level,
clear about safety and errors, testable, compatible where practical, and useful
for a traceable bootstrap. Preserve good decisions, repair weak ones and replace
those that obstruct the language's future with evidence and a migration plan.

- [Core language and implementation scope](CORE_LANGUAGE.md)
- [Recorded design decisions](DECISIONS.md)
- [Architecture](../compiler/ARCHITECTURE.md)
- [Current development status](../project/STATE_OF_PROJECT.md)
