# Legacy LLVM Bootstrap Status

## Purpose

This document freezes the supported surface of `tools/nq_llvm_bootstrap.py` as
a legacy compatibility path outside the canonical NolQu-L bootstrap.

It is not the same thing as "full NolQu-L".

## Current Bootstrap Surface

The following surface is the frozen source-level bootstrap parser surface.

Historical `nq --backend llvm` invocations belonged to the older tooling.
The current `nqlc` interface exposes `nasm` and `canonical`; it does not expose
that legacy LLVM backend selector. This document describes only the separate
retained translator in `tools/nq_llvm_bootstrap.py`.

### Supported

- integer `var` declarations
- reassignment
- integer arithmetic
- comparisons
- `print` for integers
- `if/else`
- `while`
- simple integer functions
- positional arguments
- local variables
- `return`
- nested calls
- basic recursion

### Diagnostics Covered

- line-numbered parse errors
- undefined function
- wrong function arity
- duplicate function name
- duplicate local variable
- unsupported syntax failures for features outside the bootstrap subset

## Frozen Scope

The bootstrap parser should be treated as frozen at roughly this language surface.

That means:

- maintenance is allowed
- diagnostics improvements are allowed
- compatibility adjustments are allowed when they help the IR bridge transition
- major new language features should not be added here first

## Explicitly Outside Bootstrap Scope

- arrays
- full module/import semantics
- complete `try/catch` behavior
- bridge-only IR features that already belong on the real compiler IR path

## Practical Rule

If a new feature request appears, ask:

1. is this needed to keep current bootstrap examples working?
2. is this only a maintenance or compatibility change?
3. would this be better added to the real IR bridge instead?

If the answer to 3 is yes, the feature should move to the IR bridge path.
