# NolQu-L Semantics Summary

This document summarizes the current semantic rules that matter most when writing real NolQu-L programs.

It is intentionally shorter than the full language reference in [LANGUAGE.md](LANGUAGE.md).

## Current Model

- local variables are function-scoped
- `if`, `else`, `while`, and `for` blocks do not create a new lexical local scope yet
- redeclaring the same local name later in the same function is a compile error
- function arguments are positional
- the current parameter limit is `16`
- arrays can be passed through the same call mechanism as other values
- array arguments currently behave like shared mutable values; mutating them inside a callee is visible to the caller
- `push(array, value)` appends to the same array and returns the new length
- `push` requires the pushed value to match the array element type
- `pop(array)` removes and returns the last element; popping an empty array is a runtime error
- nested calls inside argument lists are supported
- argument expressions are currently evaluated from left to right
- that left-to-right rule also applies to recursive calls and argument expressions that mutate shared state
- zero-argument calls use the same call path and are part of the active function model
- the current model has no default, named, or variadic arguments
- wrong argument count is rejected during compilation
- both call arguments and function parameters currently require explicit comma separators
- missing or trailing argument items are compile errors
- return values behave like normal expression results
- recursion is part of the active function model
- `print` accepts one or more comma-separated items
- multi-item `print` preserves left-to-right evaluation order
- each printed item still uses the normal line-oriented print behavior
- empty `print` and trailing commas in `print` are compile errors
- `println` accepts the same item list as `print`, allows an empty item list for a bare newline, and rejects trailing commas
- function and module-qualified calls can appear as standalone statements
- a bare identifier by itself is not a valid statement
- assignment targets currently must start from an identifier form, not a literal, grouped expression, or array literal
- non-call expression statements are rejected

## Loop Control

- `break` exits the current loop
- `continue` advances to the next iteration of the current loop
- in `for`, `continue` still includes the loop increment step before control returns to the loop test
- `break` and `continue` outside a loop are compile errors
- `for` ranges require both a start expression and an end expression
- `if` and `while` conditions require explicit comparison expressions
- `try` currently requires a following `catch`
- `error` is only valid inside an active `try`
- `error` currently accepts either no payload or a string literal payload
- `func`, `module`, and `import` declarations require explicit names
- function declarations currently require `()` even when they take zero parameters
- `module` currently requires its block to begin immediately after the name, except for a newline before `{`
- `import` currently accepts only a single imported name token
- `func`, `module`, and `import` declarations must appear at top level
- those declarations must also appear before executable top-level statements
- module-qualified calls are accepted, but current function resolution still uses the function name itself rather than a separate module namespace
- a module-qualified call must still name a declared module; unknown module qualifiers are rejected at compile time
- duplicate module names are rejected at compile time
- `func`, `module`, `try`, and `catch` bodies currently require explicit `{ ... }` blocks
- function parameter items currently require identifier names
- module-qualified function calls require an identifier name after `.` and `()` after the function name
- chained call/index/member access after an expression factor is currently not supported
- `catch` without a preceding `try` is rejected by the parser
- malformed array literals with missing elements are compile errors
- literal negative array indices are rejected during parsing
- array assignment currently requires an explicit `]` after the index and an explicit `=`
- variable initializers and assignment RHS values are required expressions
- non-empty `return` statements require an explicit expression
- empty array index syntax like `a[]` is rejected during parsing

## Calls And ABI

- the current ABI is intentionally simple
- arguments are passed on the stack
- the callee uses an `rbp` stack frame
- parameters are read from positive `rbp` offsets
- locals live at negative `rbp` offsets
- return values are placed in `rax`

## Current Design Boundaries

- current local-variable semantics are intentional, not accidental
- block-scoped locals are deferred for now
- `for`, arrays, and `try/catch` still exist outside the smallest protected core language surface even when parts of them are implemented

## Source Of Truth

- passing semantic tests and documented NolQu-L rules are authoritative
- Reference Compiler R0 is the current implementation oracle
- the canonical Core Compiler will become authoritative only after it reaches
  equivalent tested coverage
- legacy LLVM paths must not define separate language behavior
