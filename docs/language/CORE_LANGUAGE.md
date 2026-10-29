# NolQu-L Core

## Purpose

This document defines the smallest stable surface that should remain simple, readable, and close to the machine even while the compiler and toolchain keep evolving.

Core NolQu-L is intentionally smaller than "everything the parser can currently understand".

## Core Principles

- simple at the source level
- readable without heavy syntax rules
- explicit control flow and data flow
- close enough to machine behavior that calling convention and runtime cost stay understandable

## Core Surface

These features are the current core language surface.

### Values

- integers
- strings

### Variables

- `var x = expr`
- `x = expr`
- local variables are currently function-scoped, not block-scoped

### Expressions

- integer arithmetic: `+`, `-`, `*`, `/`, `%`
- boolean literals: `true`, `false` as integer `1`, `0`
- bitwise integer expressions: `&`, `|`, `^`, `<<`, `>>`, unary `~`
- comparisons: `>`, `<`, `==`, `!=`, `>=`, `<=`
- logical condition operators: `and`, `or`, `not`
- function call expressions

### Control Flow

- `if`
- `else`
- `else if`
- `while`
- block syntax with `{ ... }`

### Functions

- positional arguments
- return values
- local variables
- recursion

Current local-scope rule:
- `if`, `else`, `while`, and `for` blocks do not create a new lexical local scope yet
- redeclaring the same local name later in the same function is treated as a duplicate local variable error

### Built-in Output

- `print` for integers
- `print` for strings

## Explicitly Not Core Yet

These features may exist in the compiler, parser, or experiments, but they are not part of the core language contract yet.

- `for`
- modules/imports as a complete semantic system
- arrays as a fully stabilized feature set
- `try/catch` as a finalized control-flow model
- backend-specific debug/export workflows

## Rule For Future Changes

A feature should only move into core when all of the following are true:

1. it is documented in the language reference as stable
2. it has examples
3. it has regression coverage
4. it behaves consistently on the authoritative compiler path

## Source Of Truth

Passing tests and explicit NolQu-L rules are the source of truth. Reference
Compiler R0 is the current implementation oracle until the canonical Core
Compiler reaches equivalent coverage. Legacy backend parsers are never
independent semantic authorities.
