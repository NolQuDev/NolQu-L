# NolQu-L Roadmap

## Release Tracks

- `stable`: release line for versions already considered public and reliable
- `dev`: active development line for alpha, beta, and release-candidate work

## Versioning

Recommended version forms:

- stable: `1.0.0`, `1.0.1`, `1.1.0`
- alpha: `1.1.0a1`, `1.1.0a2`
- beta: `1.1.0b1`, `1.1.0b2`
- release candidate: `1.1.0rc1`

## Near-Term Goals

### 1.0.x Stable Line

- keep syntax stable
- harden parser and codegen edge cases
- improve diagnostics and examples
- preserve small-program usability
- define and protect a smaller core language surface
- keep current function-scoped local semantics stable; do not rush block-scoped locals into the `1.0.x` line

### 1.1.0 Dev Line

- richer diagnostics
- stronger debug tooling
- more complete examples and tests
- possible small language additions that do not break the `1.0.0` core
- reduce drift between "documented language" and "implemented experiments"

### 1.0.2 Dev Line

- preserve the verified x86_64 Linux Machine-Level Foundation, Stage 0 and B0
- preserve the C0.25 emitter and grow the B0-built C0.30 frontend/backend
- address measured compiler-source capacity, span width and bounded storage
- keep the NASM compiler as Reference Compiler R0 while canonical stages mature
- freeze LLVM/Python paths as compatibility and historical reference tooling
- keep experimental Core lexical scopes separate from the stable R0 scope model

C0.30 already implements structured i64 control flow, lexical scopes, named
functions, mutable parameters, bounded native recursion, call statements and
checked byte/stream I/O. See
[RUNTIME_IO.md](../../bootstrap/compiler/c0/RUNTIME_IO.md) for the bounded contract
and [State Of Project](STATE_OF_PROJECT.md) for verified stage status. This is
not a Full Compiler or self-hosting milestone, nor a stable-language promotion.

## Long-Term Direction

- grow NolQu-L through Bootstrap, Core, Full, Self-Hosting, and Verified compiler generations
- keep the canonical chain independent of LLVM, Python, and host-language compilers
- aim for small-to-medium native programs that feel practical, debuggable, and fast
- move toward capabilities associated with C/C++ toolchains where realistic:
  performance-conscious code generation
  predictable low-level behavior
  stronger backend and tooling maturity
- do this incrementally without pretending NolQu-L can instantly replace C/C++
- prefer steady compiler quality, diagnostics, and backend maturity over hype

## Process

1. Build new work on the `dev` channel.
2. Use alpha and beta versions while features are still moving.
3. Move to `rc` when the feature set is frozen.
4. Promote to `stable` only after regression tests and docs are updated.
5. Do not treat parser support alone as proof that a feature belongs to the core language.
6. Do not change the local-variable scope model casually; block scope should only land when the language is ready for a real semantic-model update.
