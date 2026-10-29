# NolQu-L Feature Status

## Status Levels

- `core`: part of the language surface NolQu-L wants to keep stable and simple
- `experimental`: implemented or partially implemented, but still allowed to change
- `syntax-only`: recognized syntactically, but not yet a complete language feature contract

## Current Status

The Core/Experimental lists below describe the Reference Compiler R0
compatibility language. Canonical C0 has its own bounded experimental subset;
parser recognition and concept-document targets do not imply support in both.

### Canonical C0.32 Experimental Subset

- checked signed i64, lexical bindings, comparisons, if/else and while
- named functions, positional arguments up to six, bounded native recursion
- checked byte memory, fixed stdin/stdout/stderr intrinsics, explicit arena profile
- native `arg_count` and byte-preserving `arg_copy`
- contextual lexical `unsafe` blocks with a required nonempty invariant comment
- unsafe checked `byte_address` and raw Linux x86_64 `syscall6`
- direct standalone ELF, NQAF/1..5 compatibility and additive /6 dialect5
- actual native file-reader source and verified scoped/generation execution

Current exact-source Linux qualification passes eleven gates, including the
full main suite with 1,084 PASS markers, 129 MCP methods and component-generation
checks. Earlier counts describe historical checkpoints. Separate PRoot and
Termux-runtime smoke/differential results are recorded in the
[validation status](../project/VALIDATION.md); both local callers were traced,
so they do not qualify untraced native Termux. Stable/security readiness remains
PARTIAL because the earlier comparison-backend SIGKILL is unexplained; see
[assurance](../../tests/security/README.md).
This subset provides no general types/modules/FFI/inline assembly, ownership or
lifetime checker, full Safety modes, Full Compiler or full self-hosting. Unsafe
source containment is checked independently by the backend; it is not proof of
every later kernel effect. See [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md)
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
