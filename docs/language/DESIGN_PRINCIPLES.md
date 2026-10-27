# Nine Pillars of NolQu-L

## Pillar 1 — Simplicity

NolQu-L must allow programmers to express programs as simply as possible without sacrificing functionality, control, performance, or clarity. The language must not force programmers to write syntax, boilerplate, patterns, or additional rules that provide no real benefit. Simple problems must be expressible simply. Problems that are inherently complex may require complex code, but NolQu-L must not introduce complexity that is not actually needed. Simplicity does not mean making code as short as possible; its purpose is to remove unnecessary complexity while preserving the complexity inherent in the problem being solved.

## Pillar 2 — Readability

NolQu-L code must be easy for humans to read and understand. The intent, structure, and flow of a program must be as clear as possible from its source, so readers do not need to guess hidden behavior or understand unintuitive rules just to determine what the program does. NolQu-L does not prioritize the shortest code when shortening it makes it harder to understand. Language syntax and features must encourage code that is clear, consistent, and easy to follow, both for its author and for other programmers in the future.

## Pillar 3 — Close to the Machine

NolQu-L targets assembly-level control on supported ISAs and must remain transparent about the behavior of the underlying machine. Avoid abstractions that hide real costs, such as memory allocation, syscalls, memory access, and other low-level operations.

Users must be able to understand and predict what happens at the machine level from the code they write.

## Pillar 4 — Complex Inside, Simple Outside

The internal implementation may be complex when necessary, but the interface seen by users must remain simple, consistent, and intuitive.

As far as possible, the burden of complexity must be carried by the compiler and runtime rather than the user.

## Pillar 5 — NolQu-L Safety

NolQu-L prioritizes memory safety as part of the language design through NolQu-L Safety — a safety model designed to provide memory and resource safety without sacrificing simplicity, readability, performance, or closeness to the machine.

The entire design of NolQu-L Safety must continue to follow the Nine Pillars of NolQu-L, especially Pillar 1, Pillar 3, and Pillar 4. NolQu-L Safety is NolQu-L's own safety identity — inspired by techniques proven in industry, but implemented according to NolQu-L's philosophy and needs.

### Safe by Default

NolQu-L Safety is designed around a Safe by Default philosophy, in which safety is the language's default behavior. By default, NolQu-L uses Balanced mode, which maintains core safety guarantees while balancing safety, flexibility, and performance.

The compiler performs as much analysis as possible at compile time to prevent common errors without burdening the programmer.

Compiler analysis includes:

- Out-of-bounds memory access.

- Use of uninitialized values.

- Use-after-free and double-free.

- Dangling pointers.

- Explicit checks for potentially absent values — such values must be represented by a type and cannot be ignored without deliberate handling.

- Memory leak detection where possible.

- Automatic release of memory, files, handles, and other resources where possible — deterministically, without depending on a garbage collector.

Resources are released on every path, including error paths, not only successful ones. Resources are released in the reverse order of allocation — predictably and consistently.

### Three Safety Modes

NolQu-L Safety provides three safety modes that can be selected according to need. All three modes use the same NolQu-L Safety foundation; they differ in the level of checking, flexibility, and control provided to the programmer.

#### BALANCED (default mode)

NolQu-L's default mode. It balances safety, flexibility, and performance while maintaining core safety guarantees. Suitable for general application development.

#### SAFE

Enables the maximum safety analysis within the compiler's capabilities. Used for requirements that prioritize reliability and safety over flexibility.

#### UNSAFE

Provides greater low-level control with reduced safety guarantees. Suitable for kernel and driver development, interoperability with other languages, and specialized optimizations that cannot be achieved in other modes. It approaches the control of C/C++ while remaining explicit and within the NolQu-L Safety system.

Use of this mode is written explicitly at file, module, or block level rather than hidden in build configuration.

### Unsafe Blocks

For low-level programming and certain optimization needs, NolQu-L provides unsafe blocks that give the programmer greater control.

Rules for unsafe blocks:

- Explicit use of an unsafe block indicates that responsibility for safety lies with the programmer rather than the compiler.

- The compiler still performs analysis and provides warnings where possible, even inside unsafe blocks.

- Unsafe blocks must be as small as possible and isolated, not a shortcut for avoiding safety checks.

- Every unsafe block must be accompanied by a comment explaining why the code remains safe even though the compiler cannot fully verify it (a safety invariant):

```text
unsafe {
    -- safety: pointer is valid because it is guaranteed by ...
    *ptr = 42
}
```

### Clear Errors

Every NolQu-L Safety violation must produce an error message stating:

- The NolQu-L Safety error code (NS-xxx) for documentation reference.

- The location (file, line, column).

- What was violated and why it is a problem.

- What can be done to fix it.

NolQu-L Safety violations that can be proven must not pass without an appropriate diagnostic. Behavior outside the safety guarantees must be stated explicitly and remain traceable.

### Safety and Performance Are Not Opposites

NolQu-L Safety checks are performed as early as possible, especially at compile time. Runtime checks are used only when a property cannot be proven statically and a runtime check is actually necessary. The performance cost of safety in NolQu-L must be measurable, transparent, and predictable — in accordance with Pillar 3.

### Implementation Order in the Compiler

NolQu-L Safety is implemented in stages, starting with the most fundamental:

1. Automatic resource release and use-after-free detection.

2. Checks for uninitialized values and out-of-bounds access.

3. The ownership model and move semantics.

4. Borrow checking.

5. Lifetime verification and dangling pointer checks.

6. The three safety modes (Balanced, Safe, Unsafe).

Each stage must be stable before the next stage begins.

## Pillar 6 — Clear Error Handling

Every error must provide:

- The location of the error (file, line, column).

- The cause of the error.

- Where possible, concrete suggestions for fixing it.

There must be no silent failures or crashes without clear context. Errors are part of the language interface, not merely an additional feature.

This applies to every layer: lexer, parser, NolQu-L Safety, linker, and runtime. No layer may produce messages that users cannot understand.

## Pillar 7 — Test Before Merge

No change may be merged without tests proving that it works correctly and does not cause unintended regressions elsewhere.

Every change must have testing appropriate to its impact, including when it intentionally changes previous behavior.

If an unintended regression is found during implementation, stop — fix it before continuing.

A breaking change planned and approved under Pillar 8 is not considered a regression, but it still requires tests proving that:

- The new behavior works as designed.

- Other parts are not unintentionally broken.

- The change delivers the benefits that justify the breaking change.

- The migration path works when one is provided.

Tests are not only a means of preserving old behavior. They also provide evidence that the language's evolution is controlled.

## Pillar 8 — Stability Without Blocking Evolution

Changes must preserve compatibility and avoid breaking working code as far as possible. However, backward compatibility is not an absolute goal.

Stability is the default, not a boundary that prevents the language from evolving.

Changes that break compatibility are permitted when they deliver meaningful improvements to:

- Safety.

- Simplicity.

- Readability.

- Performance.

- Language consistency.

- The compiler's ability to perform analysis.

- Maintainability.

- Long-term architectural quality.

NolQu-L must not retain poor design decisions solely for compatibility.

### Breaking Changes Must Have a Reason

Breaking changes must not be made merely because a new design looks more attractive or more modern.

Every breaking change must have a clear technical reason and benefits large enough to justify its migration costs.

Before a breaking change is accepted, at least the following must be known:

- The problem with the old design or behavior.

- Why the problem needs to be fixed.

- The benefits of the new design.

- The parts of the language or ecosystem affected.

- The risks introduced.

- The alternatives considered.

The wider the impact of a change, the stronger the justification required.

### Compatibility Has Several Forms

Compatibility is not only about whether old source code can still be compiled. Changes can affect:

- Source compatibility.

- Behavior compatibility.

- Binary or ABI compatibility.

- Library compatibility.

- Tooling compatibility.

- Interoperability with other systems.

The impact on each area must be considered in the context of the change. NolQu-L does not promise that every form of compatibility must always be preserved, but the compiler and ecosystem must not break them without a known reason.

### Migration Path

Where possible, a breaking change must provide a reasonable migration path.

A migration path may include:

- Compiler diagnostics explaining the change.

- Suggested replacements for old syntax or APIs.

- Automatic fixes or migration tooling.

- Temporary compatibility layers.

- Migration documentation.

- A deprecation period before a feature is removed.

However, a migration path is not an absolute obligation if retaining the old mechanism would instead:

- Create security risks.

- Make implementation much more complex.

- Cause ambiguous behavior.

- Obstruct the new architecture.

- Conflict with the Nine Pillars of NolQu-L.

In these circumstances, direct changes are still permitted provided their reasons are clearly documented.

### Deprecation Before Removal

Features that remain safe and can be retained at a reasonable cost should go through deprecation before removal.

The compiler may issue warnings explaining:

- That the feature is deprecated.

- The reason for deprecation.

- The recommended alternatives.

- The version in which removal is planned, if already known.

Deprecation must not become a permanent home for an old design. If a feature has a better replacement and there is no longer a sufficiently strong reason for its existence, it may eventually be removed.

### Avoid Compatibility Debt

Compatibility has a cost. Compatibility shims, legacy behavior, special parsers for old syntax, and additional compiler paths can increase implementation and maintenance complexity.

NolQu-L must not keep adding compatibility layers until the compiler becomes harder to understand, test, optimize, or develop.

If the cost of maintaining compatibility begins to outweigh its benefits, the design must be reevaluated. Removing compatibility debt is permitted when it delivers a real architectural improvement and follows the breaking-change rules in this pillar.

### Breaking Changes Must Be Controlled

Breaking changes must be explicit and planned. Where possible, major changes should be grouped at clear version boundaries rather than appearing randomly across many small updates.

Users must be able to tell that a version brings changes requiring migration.

The compiler must not silently change the meaning of old code when doing so could produce different behavior without adequate diagnostics.

### Evolution Without Unjustified Rewrites

The freedom to make breaking changes is not a license to keep redesigning the language. Parts that already work well do not need to change merely for cosmetic consistency, personal preference, or trends in other programming languages.

Changes must solve real problems or provide sufficiently meaningful improvements.

> Preserve what is good.\
> Fix what is bad.\
> Replace what holds back the future.

Stability must protect users from unnecessary changes. Evolution must protect the language from old decisions that are no longer worth retaining.

## Pillar 9 — Optimization Based on Impact

Structural optimization is encouraged where there is a real opportunity to make a significant difference to performance, memory use, binary size, compilation time, or architectural quality.

There is no need to force micro-optimizations whose impact has not yet been measured or remains unproven.

Optimizations that increase implementation complexity must have benefits commensurate with the maintenance costs they introduce.

If an optimization requires a breaking change, it must also satisfy Pillar 8. Thus, "faster" alone does not automatically justify breaking compatibility.

The greater the cost of a change to users, the greater the improvement that must be demonstrable. Optimization must be based on real impact, not merely theoretical possibilities.
