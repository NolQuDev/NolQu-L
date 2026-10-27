# NolQu-L Errors

## Purpose

This document summarizes the current error and failure model across the main
compiler path and the LLVM-related bridge paths.

## Main Compiler Errors

The main compiler already rejects several classes of invalid input, including:

- malformed syntax
- wrong function arity
- undefined functions
- `return` outside a function
- duplicate function names
- duplicate parameter names
- duplicate locals within the same function scope
- namespace conflicts between globals and functions

## Current Error Philosophy

The current direction is:

- fail clearly instead of silently accepting broken input
- keep parser and semantic errors visible to the user
- keep failure behavior testable
- avoid letting unsupported experimental paths fail in opaque ways

## Bridge And LLVM Errors

The IR-to-LLVM bridge now reports structured failure context such as:

- IR index
- source line when available
- opcode context
- optional name context
- function or main context

The bridge also explicitly reports:

- malformed IR structure
- invalid stack or operand-state transitions
- missing metadata for some exported constructs
- unsupported features that are not yet lowered

## Unsupported Feature Errors

Unsupported features in bridge paths should fail as explicit unsupported
behavior, not as silent divergence.

## Practical Rule

When a new semantic or backend path is introduced, error behavior should be
considered part of the feature, not an afterthought.

## Related Docs

- [SEMANTICS.md](SEMANTICS.md)
- [TESTING.md](../compiler/TESTING.md)
- [IR.md](../compiler/IR.md)
- [LLVM_BRIDGE.md](../compiler/LLVM_BRIDGE.md)
