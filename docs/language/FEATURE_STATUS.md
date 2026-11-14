# NolQu-L Feature Status

## Status Levels

- `core`: part of the language surface NolQu-L wants to keep stable and simple
- `experimental`: implemented or partially implemented, but still allowed to change
- `syntax-only`: recognized syntactically, but not yet a complete language feature contract

## Current Status

The Core/Experimental lists below describe the Reference Compiler R0
compatibility language. Canonical C0 has its own bounded experimental subset;
parser recognition and concept-document targets do not imply support in both.

### Canonical C0.40 Experimental Subset

- checked signed i64, lexical bindings, comparisons, if/else and while
- immutable byte literals, inferred i64/static-byte local types and complete
  write(value); exact global user shadows retain priority, user parameters/
  unannotated results stay i64. General strings/types/ownership are not implemented
- logical prefix `!` and verified `fn f() -> !` bottom contracts, preserving
  unreachable type/permission checks and defined guards for a returning target
- checked signed `%`, with dividend-signed remainder and zero/MIN%-1 faults
- eager 64-bit bitwise `&`, `^`, `|` and unary `~`
- eager `<<` and arithmetic `>>`, with full i64 counts checked in0..63
- short-circuit `and`/`or` and prefix `not`, normalized i64 0/1; new exact logical keywords are reserved
- checked prefix `-`, including the INT64_MIN literal; runtime overflow is diagnosed
- named functions, positional arguments up to six, bounded native recursion
- independent structural return proof; exhaustive if/else needs no redundant return
- checked byte memory, fixed stdin/stdout/stderr intrinsics, explicit arena profile
- native `arg_count` and byte-preserving `arg_copy`
- contextual lexical `unsafe` blocks with a required nonempty invariant comment
- unsafe checked `byte_address` and raw Linux x86_64 `syscall6`
- direct standalone ELF, NQAF/1..12 compatibility and additive /13 dialect12
- actual native file-reader source and verified scoped/generation execution

The C0.32 baseline exact-source Linux qualification of `Testing` at `75b2309f` passes eleven gates,
including the full main suite with 1,086 PASS markers, 135 MCP methods and
component-generation checks. Earlier counts describe historical checkpoints.
The same pinned finite smoke/differential profile passes in PRoot and untraced
Native Termux: 15 checks, 326 invocations and 96 oracle matches in each; their
streams and generated ELF files match. See the
[validation status](../project/VALIDATION.md). Full Native qualification remains
blocked by denied real-hardlink creation. Stable/security readiness remains
PARTIAL because the earlier comparison-backend SIGKILL is unexplained; see
[assurance](../../tests/security/README.md).
This subset provides no general types/modules/FFI/inline assembly, ownership or
lifetime checker, full Safety modes, Full Compiler or full self-hosting. Unsafe
source containment is checked independently by the backend; it is not proof of
every later kernel effect. C0.33 return-flow evidence and minimum component
compatibility are defined in [RETURN_FLOW.md](../../bootstrap/compiler/c0/RETURN_FLOW.md).
C0.40 bottom syntax/types/flow, no-payload emission and required paired
qualification are defined in [NEVER.md](../../bootstrap/compiler/c0/NEVER.md).
C0.39 byte syntax, lifetime/representation, finite type checks and matched
qualification are defined in [STATIC_BYTES.md](../../bootstrap/compiler/c0/STATIC_BYTES.md).
C0.38 remainder semantics, checked quotient faults, independent wire validation
and68-byte emission are defined in [REMAINDER.md](../../bootstrap/compiler/c0/REMAINDER.md).
C0.37 shift semantics, count diagnostics, wire validation and46-byte emission
are defined in [SHIFTS.md](../../bootstrap/compiler/c0/SHIFTS.md).
C0.36 logical semantics, exact keyword migration, independent graph validation
and conditional machine cost are defined in
[SHORT_CIRCUIT.md](../../bootstrap/compiler/c0/SHORT_CIRCUIT.md).
C0.35 bitwise semantics and the Core/R0 precedence distinction are defined in
[BITWISE.md](../../bootstrap/compiler/c0/BITWISE.md).
C0.34 unary semantics, minimum-literal ownership, machine cost and paired upgrade
are defined in [UNARY_NEGATION.md](../../bootstrap/compiler/c0/UNARY_NEGATION.md).
See [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md)
and the [toolchain guide](../compiler/CANONICAL_TOOLCHAIN.md).

### Core

- integers
- strings
- `var` declarations
- assignment
- compound assignment
- arithmetic expressions
- boolean literals: `true`, `false` as integer `1`, `0`
- bitwise integer expressions: `&`, `|`, `^`, `<<`, `>>`, unary `~`
- comparisons
- logical condition operators: `and`, `or`, `not`
- `print`
- `if`
- `else`
- `else if`
- `elif`
- `while`
- functions
- returns
- local variables
- recursion

### Experimental

- arrays
- `for`
- `try/catch`
- LLVM backend (frozen legacy compatibility path)
- IR export / JSON / LLVM bridge tooling

### Syntax-Only Or Incomplete

- modules/imports as a complete module system

## Notes

- a parser feature is not automatically a language guarantee
- a backend experiment is not automatically part of the language
- core language decisions should be conservative; tooling experiments can move faster
- R0 local-variable semantics are function-scoped; block-scoped locals remain deferred there
- canonical C0 lexical scopes are implemented independently, including unsafe blocks
