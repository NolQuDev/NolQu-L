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

The broad surface below retains the R0 reference description. Canonical C0
implements a smaller experimental subset whose qualification is separate.

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

The experimental C0.37 subset adds eager `<<` and arithmetic `>>`, with full
i64 counts checked in0..63 and C0R-010 on executed invalid counts. Shifts bind
between additive and relational expressions. See
[SHIFTS.md](../../bootstrap/compiler/c0/SHIFTS.md) for NQAF/10 and qualification.

The experimental C0.36 subset adds normalized i64 short-circuit `and`/`or`
and prefix `not`, with static checking of both operands. Exact logical words
become reserved Core identifiers; prefix names retain their meaning. NQAF/9
requires a matching component pair; see
[SHORT_CIRCUIT.md](../../bootstrap/compiler/c0/SHORT_CIRCUIT.md).

The experimental C0.35 subset adds signed i64 `&`, `^`, `|` and prefix `~`,
with independent review and exact-pair qualification gates. These use
all 64 bits, eager binary evaluation left to right once per operand and
right-associative prefix `-`/`~`. Precedence, highest first, is call/grouping,
`-`/`~`, `*`/`/`, `+`/`-`, relational, equality, `&`, `^`, `|`. This deliberately
differs from R0's bitwise/additive level; mixed unparenthesized expressions
cannot establish differential equivalence. R0 is unchanged. C0.35 adds no
shifts; bitwise NOT does not extend the NEGATE-only minimum
literal exception. See the [C0.35 contract](../../bootstrap/compiler/c0/BITWISE.md).

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
