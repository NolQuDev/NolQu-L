# Contributing To NolQu-L

NolQu-L is still evolving, but contributions should respect the project's current
design constraints.

## Before Contributing

- read the [Nine Pillars of NolQu-L](../language/DESIGN_PRINCIPLES.md)
- read [CORE_LANGUAGE.md](../language/CORE_LANGUAGE.md)
- read [FEATURE_STATUS.md](../language/FEATURE_STATUS.md)
- read [SEMANTICS.md](../language/SEMANTICS.md)
- read [ARCHITECTURE.md](../compiler/ARCHITECTURE.md) and the relevant `bootstrap/` contract
- follow [PUBLICATION.md](../project/PUBLICATION.md) when selecting files for GitHub
- read [bootstrap/README.md](../../bootstrap/README.md)

## Contribution Priorities

- canonical Stage 0 and bootstrap work with reproducible evidence
- bug fixes in Reference Compiler R0
- regression tests
- documentation that reduces semantic ambiguity
- tooling improvements that preserve bootstrap traceability

## Avoid By Default

- silently widening the core language surface
- growing LLVM/Python compatibility paths as if they were canonical stages
- changing scope, calling convention, or argument semantics without updating
  docs and tests together
- introducing features that make the surface language more complex without a
  clear design decision

## Practical Rule

Every meaningful semantic change should normally come with:

- updated docs
- updated examples when user-visible behavior changes
- updated tests

## Contact

For coordination before larger changes:

- `nolqudev@gmail.com`
- `nolquteam@gmail.com`
- `nolqucontact@gmail.com`
