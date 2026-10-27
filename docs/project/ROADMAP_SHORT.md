# NolQu-L Roadmap Short

Current metadata (2026-10-27): `1.0.0-alpha.1`, channel `dev`, by maintainer
request for `NolQuDev/NolQu-L`. Older version strings in checkpoint evidence
below describe those historical runs; no release or bootstrap promotion occurs.

## Completed Foundation

- auditable x86_64 Linux machine-code trust root and deterministic reconstruction
- symbolic Stage0, hash-verified B0 and the retained C0.25 bounded emitter
- separate B0-built source frontend/direct-ELF backend with lexical scopes,
  control flow, i64 functions, parameters, recursion and checked byte/stream I/O
- C0.31 source/token/node capacity 262144/65536/65536, wide32 NQAF/5 and explicit
  16 MiB RW/NX profile with unchanged default 64 KiB arena
- actual complete-source A -> B -> C component generations and coherent C0.31
  installation, distinct from Full Compiler/full-language self-hosting
- explicit canonical public CLI/project/install/MCP access; R0/NASM stays default
- LLVM/Python legacy language tooling frozen outside canonical source semantics

Historical C0.29 8 KiB source failures and C0.30 capacity blockers were resolved
by the completed capacity milestone; do not restart that work. See
[CAPACITY.md](../../bootstrap/compiler/c0/CAPACITY.md) for preserved evidence.

## Current Substantial Milestone: Native OS Access

Experimental C0.32 implements contextual unsafe blocks with invariant comments,
native argc/argv copying, checked raw arena addresses and a 48-byte six-argument
syscall frame. Independent source/AST permission checks accompany direct ELF.
The actual native file-reader program handles binary/literal argv, stdin/files,
explicit I/O progress and descriptor ownership in NolQu-L source.

Scoped tests and actual complete-source generations pass; public full-source
builds match B/C artifacts. The reviewed coherent set is installed in the
isolated worktree; final main/MCP/release/protocol/combined-proof execution
gates pass. An earlier unexplained comparison-backend SIGKILL remains OPEN,
so stable/security readiness remains PARTIAL. Preserve all prior bounds, compatibility tests and
rollback state. [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md) defines
the capability and limits; [STATE_OF_PROJECT.md](STATE_OF_PROJECT.md) separates
measured results from open assurance limits.
The 1079 full-main checkpoint predates the diagnostic formatter repair. Current
post-repair component/proof/MCP/public/assurance evidence is recorded separately
in the [session report](VALIDATION.md); full main was not rerun.

## Following Engineering Objectives

1. Resolve the unexplained comparison-backend SIGKILL with process/resource
   attribution before stable/security promotion; preserve failed-run evidence.
   Expand the finite native assurance profile and qualify execution on actual
   target hardware before claiming broader security or target assurance.
   Then select a complete type/module/toolchain prerequisite from measured gaps.
2. Grow the canonical Full Compiler while preserving R0 compatibility or
   documenting intentional experimental-subset differences.
3. Replace shell/Python/legacy toolchain components with actual verified
   NolQu-L implementations as required language capabilities become available.
4. Build the full `nqlc` with a previous NolQu-L generation and verify repeated
   generations by byte equality or documented deterministic equivalence.

Native pointer/syscall access does not establish full Safety or wrapper
preconditions. Full Compiler, full-language self-hosting and later Verified
status remain unimplemented. Public VERSION1.0.2a1/CHANNELdev are unchanged;
experimental progress does not automatically justify a release.

## Deferred

- additional target architectures and broad FFI/inline assembly/atomics support
- deleting R0 or legacy LLVM/Python before verified replacements meet obligations
- optimizer expansion before canonical correctness and reproducibility
