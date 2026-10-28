# NolQu-L Language Reference 1.0.2a1

This document describes the user-facing NolQu-L language surface as of `1.0.2a1`.

It does not treat every parser feature as equally stable. For the official status split, see [CORE_LANGUAGE.md](CORE_LANGUAGE.md) and [FEATURE_STATUS.md](FEATURE_STATUS.md).

## Status Guide

- `core`: intended to stay stable and readable
- `experimental`: implemented, but still allowed to change
- `syntax-only`: recognized by the compiler, but not yet a complete language contract

## Core Syntax

### Comments

NolQu-L supports line comments with `#` or `//`, and non-nesting block comments with `/* ... */`. Comments have no runtime cost.

```txt
// file comment
print 1 // trailing comment
# shell-style comment
/* block comment
   over multiple lines */
```

### Values

Core value kinds:

- integers, written in decimal, hexadecimal (`0x...`), or binary (`0b...`); `_` may separate digits
- strings

### Variables

Declaration:

```txt
var x = 10
var y = x + 3
```

Assignment:

```txt
x = 20
x += 1
x -= 1
```

Compound assignment operators (`+=`, `-=`, `*=`, `/=`, `%=`) are integer
arithmetic only. String concatenation stays explicit with `x = x + "text"`.

### Print

```txt
print 123
print x
print "hello"
print 1, x, "hello"
println
println "hello"
```

`print` may contain multiple comma-separated items. Each item is emitted in source order using the existing integer or string print path.
At least one print item is required.

`println` uses the same item rules as `print`, but also appends one extra newline after all items. A bare `println` prints only that newline.

### Expressions

Supported arithmetic:

- `+`
- `-`
- `*`
- `/`
- `%`

Supported integer bitwise operators:

- `&`
- `|`
- `^`
- `<<`
- `>>`
- unary `~`

Shift counts follow x86-64 integer shift behavior: only the low 6 bits of the
count are used, equivalent to `count & 63`.

Example:

```txt
var x = (2 + 3) * 4
var mask = 0xff
var flags = 0b1010_0101
```

Boolean literals are integer values, not a separate runtime type:

- `true` lowers to `1`
- `false` lowers to `0`

### Conditions

Supported comparison operators:

- `>`
- `<`
- `==`
- `!=`
- `>=`
- `<=`

Condition clauses may be combined with `and` and `or`. They short-circuit from
left to right, so skipped clauses do not run their expressions. A leading `not`
inverts the condition result.

Example:

```txt
if x == 10 {
print 1
}
```

### Blocks

Blocks use braces:

```txt
if x > 0 {
print x
}
```

### Control Flow

#### If / Else

```txt
if x == 1 {
print 7
} else if x == 2 {
print 8
} else {
print 9
}

if x == 1 {
print 7
} elif x == 2 {
print 8
}
```

#### While

```txt
var i = 0
while i < 3 {
print i
i = i + 1
}
```

### Functions

Core function support:

- positional arguments
- return values
- local variables
- recursion
- module-qualified calls still require `()` after the function name
- module-qualified calls must name a declared module

Declaration:

```txt
func add(a, b) {
return a + b
}
```

Call:

```txt
print add(2, 3)
add(2, 3)
```

Local variables:

```txt
func foo(a) {
var x = a + 2
return x
}
```

Current scope rule:
- locals are function-scoped
- blocks like `if`, `else`, `while`, and `for` do not create a new nested lexical scope yet

Recursion:

```txt
func fact(n) {
if n == 0 {
return 1
}
return n * fact(n - 1)
}
```

## Current Semantic Rules

These are the current language semantics that matter most when writing real NolQu-L programs.

### Local Scope

- local variables are function-scoped
- `if`, `else`, `while`, and `for` do not create a new lexical local scope yet
- redeclaring the same local name later in the same function is a compile error

Example:

```txt
func scope_demo() {
if 1 == 1 {
var y = 7
}
return y
}
```

### Loop Control

- `break` exits the current loop
- `continue` skips to the next loop iteration
- for `for` loops, `continue` still performs the loop increment before the next iteration starts
- `for` ranges require both a start expression and an end expression
- `if` and `while` conditions require explicit comparison expressions
- non-empty `return` statements require an explicit expression
- `error` currently accepts either no payload or a string literal payload
- `func`, `module`, and `import` declarations require explicit names
- `func`, `module`, `try`, and `catch` bodies require explicit `{ ... }` blocks
- function parameter items require identifier names
- module-qualified function calls require an identifier name after `.`
- chained call/index/member access after an expression factor is not supported yet

### Function Calls

- arguments are positional
- return values come back as normal expression values
- recursion is supported and treated as part of the core function model
- the current parameter limit is `16`
- arrays can be passed as ordinary function values
- nested function calls inside an argument list are supported
- arguments are currently evaluated from left to right
- left-to-right evaluation also applies when argument expressions recurse or mutate array/global state
- zero-argument functions and calls are supported
- array arguments currently behave as shared values: mutating the array inside a function is visible to the caller
- both call arguments and function parameter lists require explicit comma separators
- malformed argument lists with missing items or trailing commas are compile errors

Current argument-model boundaries:

- no default arguments
- no named arguments
- no variadic arguments
- wrong argument count is a compile error

## Experimental Features

These features exist in the current compiler, but should not be treated as fully frozen language surface yet.

### Arrays

Array literal:

```txt
var a = [1,2,3]
```

Array access:

```txt
print a[1]
```

Append and remove from the end of an array:

```txt
push(a, 4)
var last = pop(a)
```

Status:

- implemented
- useful
- not yet treated as the smallest protected core surface

### For

Current syntax:

```txt
for i in 0..3 {
print i
}
```

Status:

- parser/compiler support exists
- not yet promoted to core language

### Try / Catch

Current syntax:

```txt
try {
error "boom"
} catch {
print 7
}
```

Status:

- implemented in the compiler
- not yet promoted to core language
- `catch` is currently required after `try`
- `error` is only valid inside an active `try`

## Syntax-Only Or Incomplete Features

### Modules / Imports

Basic syntax exists:

```txt
module math {
func add(a, b) {
return a + b
}
}
```

Status:

- module/import syntax exists
- imports are not yet a complete stabilized module system
- duplicate module names are rejected

## Errors

Parse and undefined-variable errors are reported with line and column numbers. On parser error, the compiler exits non-zero.

Experimental backends and bridge tooling may have narrower feature support and their own diagnostics while they are still converging on the core compiler path.

## Calling Convention

The current NolQu-L ABI is intentionally simple:

- arguments are pushed on the stack by the caller
- the callee creates an `rbp` stack frame
- parameters are read from positive `rbp` offsets
- locals are stored at negative `rbp` offsets
- return value is placed in `rax`

This ABI remains intentionally minimal because that fits NolQu-L's "simple and close to the machine" philosophy.
