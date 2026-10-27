# NolQu-L Style Guide

## Language Style

- prefer short, direct identifiers
- keep control flow explicit
- avoid clever syntax tricks
- prefer readable small functions over dense expressions
- use examples that reflect the current supported semantic model

## Example Style

- prefer examples that are minimal but real
- avoid showing experimental features as if they were core language features
- keep examples aligned with [FEATURE_STATUS.md](/root/Nolqu/docs/language/FEATURE_STATUS.md)
- when behavior depends on semantics, prefer examples that make that behavior
  explicit

## Compiler Contribution Style

- keep passing tests and explicit semantics as the source of truth
- distinguish canonical bootstrap code, Reference Compiler R0, and legacy paths
- do not widen LLVM/Python compatibility paths with new architecture
- pair semantic changes with docs and tests
- prefer narrow, explainable changes over sprawling patches

## Documentation Style

- keep language docs honest about what is core, experimental, or incomplete
- separate syntax reference from semantic explanation when needed
- avoid promising stability where the implementation is still moving

## Release Style

- update docs when public behavior changes
- do not treat new parser support as official language design by default
- keep examples, tests, and release metadata aligned
