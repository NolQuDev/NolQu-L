# NolQu-L Known Limitations

## Project State

NolQu-L is still an active development project. Even with a stable `1.0.1`
baseline, the current `1.0.2a1` line is still growing and tightening parts of
the toolchain.

## Language Limitations

- Reference Compiler R0 locals are function-scoped; canonical C0 implements lexical scopes
- function arguments are currently positional-only
- there are no default arguments
- there are no named arguments
- there are no variadic arguments
- obvious malformed array literals and literal negative indices are rejected during parsing
- NASM and LLVM bridge runtimes now abort with a clear runtime error on out-of-bounds array access
- the NASM runtime now guards against exhausting the fixed array heap region and aborts with a clear runtime error instead of silently overrunning it
- a single array literal that already exceeds the fixed heap capacity is now rejected during compilation
- some language surfaces remain `experimental` or `syntax-only`

## Backend Limitations

- the canonical Machine/Stage0/B0 and C0.25 emitter are implemented; separate
  C0.32 source frontend/direct-ELF backend extend the completed C0.31 foundation
- current C0 supports one compilation unit and signed i64, not the full R0
  language, general types/modules/FFI or inline assembly
- complete compiler-source A/B/C generations pass, but Full Compiler,
  full-language Self-Hosting and the later Verified compiler remain unimplemented
- full main1079 predates the diagnostic formatter repair; current post-repair
  canonical/MCP/public/assurance gates pass, while post-repair full main was not
  rerun; the [session report](../project/C032_SESSION_REPORT.md) records the scope
- native unsafe blocks check permission/headers/source containment, not general
  ownership, lifetimes, syscall-specific kernel effects or full Safety modes
- `byte_address` exposes raw bits after checking a span; later pointer use is
  still the unsafe caller's responsibility
- raw `syscall6` performs one syscall with no automatic errno/retry/fd policy;
  the source caller owns partial I/O, interrupted-call handling and close behavior
- default arena 64 KiB and explicit 16 MiB RW/NX, source262144/tokens65536/nodes65536,
  combined control 64/call 64/arity 6 and frame 4096/512 slots remain fixed
- C0.32 scoped/generation and final main/MCP/probe execution gates pass; an
  earlier frozen comparison-backend SIGKILL remains unexplained. No retry is
  treated as a fix; stable/security readiness remains PARTIAL
- deterministic native-boundary mutation tests have finite coverage; no
  coverage-guided fuzzing, NolQu-L memory sanitizer or RSS-pressure proof is
  available in the [supplemental profile](../../tests/security/README.md)
- Reference Compiler R0 remains the default compatibility path and is not
  canonical or self-hosted
- LLVM and Python paths are frozen compatibility tooling

## Toolchain Limitations

- current workflows assume a relatively Unix-like environment
- some paths depend on external tools such as `nasm`, `ld`, `clang`, and
  `llvm-as`
- on non-`x86_64` hosts, running canonical or NASM backend output may require
  `qemu-x86_64`
- the current aarch64 development evidence executes x86_64 under QEMU; it does
  not establish hardware-native execution or another target architecture
- canonical CLI orchestration still uses shell; MCP/testing still uses Python
  and legacy LLVM/NASM tooling remains outside canonical source semantics

## Documentation Limitations

- some docs describe stable current behavior, while others describe evolving
  architecture and direction
- exported IR documentation is useful, but the IR format should not yet be
  treated as a permanently frozen public interface

## Practical Rule

Treat core language behavior and the stable NASM path as the best current
reference points. Treat experimental paths as real and useful, but not yet
final.

## Related Docs

- [FEATURE_STATUS.md](FEATURE_STATUS.md)
- [SEMANTICS.md](SEMANTICS.md)
- [BACKENDS.md](../compiler/BACKENDS.md)
- [COMPATIBILITY.md](../project/COMPATIBILITY.md)
- [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md)
