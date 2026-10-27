# NolQu-L Code Generation Paths

## Canonical Status

NolQu-L does not yet have a canonical full compiler backend. The canonical
chain currently stops at the x86_64 Linux Stage 0 symbolic emitter. The
NolQu-L Bootstrap Compiler is the next implementation milestone.

## Reference Compiler R0 NASM Path

The existing NASM path is the tested default for current programs.

- role: compatibility implementation and semantic oracle
- status: maintained
- bootstrap classification: `REFERENCE_R0_ONLY`
- canonical dependency: none; it is outside the canonical chain

This path may receive correctness, diagnostics, and compatibility fixes while
the canonical compilers are developed. It must not be relabeled as self-hosted.

## LLVM And Python Paths

All LLVM bootstrap and IR-to-LLVM paths are legacy compatibility/reference
paths.

- they are not a future NolQu-L backend requirement
- they are not stages in the bootstrap chain
- they may be maintained to keep existing tests and historical examples valid
- they should not receive new core language semantics
- their presence does not change the architecture's machine-code foundation

The legacy command-line switches remain available for backward compatibility
until a separately tested removal or deprecation decision is made.

## Development Rule

New canonical compiler work belongs under `bootstrap/` and must advance the
documented predecessor-to-successor chain. New language semantics remain
validated against Reference Compiler R0 until a canonical Core Compiler can
replace it as the semantic authority.
