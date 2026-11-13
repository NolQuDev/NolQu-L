# NolQu-L Code Generation Paths

## Canonical Core And Full Compiler Status

The implemented canonical chain is Machine-Level Foundation -> Stage 0 -> B0
-> Core Compiler. These stages are `PASS` in the
[bootstrap manifest](../../bootstrap/manifest.tsv). B0 builds both the C0.25
bounded emitter and the separate C0.39 source frontend and AST backend.

The Core frontend/backend path is:

```text
NolQu-L Core source (*.nql)
    -> C0.39 frontend
    -> versioned NQAF/1..12
    -> independently validating C0.39 backend
    -> direct ELF64 x86_64 Linux executable
```

Select it with `nqlc --backend canonical`. The backend emits machine code
directly; R0, NASM, LLVM, Python and a host linker are not semantic compiler
stages in this path. Host shell/test tools and QEMU execution on non-x86_64
hosts do not become predecessor compilers. See the
[canonical toolchain contract](CANONICAL_TOOLCHAIN.md) for supported source,
CLI options, dependencies and limits, and
[architecture](ARCHITECTURE.md) for the stage boundaries.

Full Compiler, formal self-hosting and Verified nqlc remain `NOT_IMPLEMENTED`.
The public `nqlc` driver name and successful bounded/component-generation
comparisons do not promote those stages. Qualification requirements, recorded
checkpoints and open signal-attribution/platform limits are documented in
[validation](../project/VALIDATION.md); the older C0.25 emitter and its bounded
self-image proof remain distinct from the C0.39 components.

## Programming Paths And Compiler Implementations

Systems Programming and Assembly-Level Systems Programming are complementary
paths in one language, type-system design and compiler architecture. They
describe how much explicit machine control an operation needs, rather than
which compiler implementation is selected. R0 and the developing canonical
Core pipeline are not those two programming paths.

The programming paths are also distinct from NolQu-L Safety's Balanced, Safe
and Unsafe modes. Balanced remains the design default; machine-explicit work
does not automatically make a whole program Unsafe. Full type, ownership,
Safety and target-control facilities remain subject to their implementation
maturity. See [design principles](../language/DESIGN_PRINCIPLES.md) and
[feature status](../language/FEATURE_STATUS.md).

## Reference Compiler R0 NASM Path

The Reference Compiler R0 NASM path remains the public `nqlc` default
(`--backend nasm`).

- role: compatibility implementation and semantic oracle on defined overlap
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

These helper/test paths do not imply a public LLVM backend: `nqlc --backend`
accepts only `nasm` and `canonical`; `--backend llvm` is rejected. Consult the
[legacy LLVM policy](LLVM_BOOTSTRAP_POLICY.md) for the frozen maintenance scope.

## Development Rule

New canonical compiler work belongs under `bootstrap/` and must advance the
documented predecessor-to-successor chain. Canonical behavior follows its
documented contracts and valid tests. Compare with R0 only where source and
semantics overlap; an unsupported construct or deliberate Core/R0 contract
difference is not evidence that the new compiler is wrong. Triage divergences
against the applicable contract instead of silently changing semantics to match
an oracle. New capabilities require their own tests, maturity and machine-cost
evidence before being advertised as implemented.
