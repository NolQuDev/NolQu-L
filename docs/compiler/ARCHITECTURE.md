# NolQu-L Architecture

## Architectural Authority

The public implementation contracts are recorded under `bootstrap/`, with
artifact identities and stage evidence in [manifest.tsv](../../bootstrap/manifest.tsv).
Passing tests define the behavior that is actually implemented. Directory names
alone do not prove bootstrap status. The maintainer removed the earlier root
development prompts and concept attachment from the public source tree; they
are not build dependencies. This does not replace their design decisions or
promote unimplemented features. MCP resources that need the optional design
document explicitly report its absence instead of inventing replacement text.

## Canonical Bootstrap Chain

```text
Machine-Level Foundation
-> Stage 0
-> NolQu-L Bootstrap Compiler
-> NolQu-L Core Compiler
-> Full NolQu-L Compiler
-> Self-Hosting nqlc
-> Verified nqlc
```

This chain must remain independent of LLVM, Python, NASM, and host-language
compilers. Host programs may inspect or test artifacts, but they are not
canonical compiler stages.

## Current Canonical State

The x86_64 Linux Machine-Level Foundation is implemented in
`bootstrap/machine/x86_64-linux/`. Its canonical executable is the raw ELF64
machine-code artifact `hex0.seed`. `hex0.hex` is its auditable byte manifest,
and the seed can decode that manifest back into a byte-identical executable.

Stage 0 is implemented in `bootstrap/stage0/x86_64-linux/`. It is a bounded,
two-pass symbolic flat-binary emitter reconstructed by `hex0.seed`. Its tests
prove deterministic instruction emission, memory and control-flow patches,
symbol resolution, runnable ELF generation, diagnostics, and resource cleanup.

Bootstrap Compiler B0 is implemented and built by Stage 0. It builds the C0.25
bounded emitter and the separate C0.32 source frontend and AST backend. These
components compile checked i64 functions, lexical control flow, byte/stream
operations and explicitly scoped native operations directly to ELF64. NQAF/1..6 is the explicit frontend/backend
boundary; the backend validates the stream independently before code generation.
The runtime contract and gates are in
[RUNTIME_IO.md](../../bootstrap/compiler/c0/RUNTIME_IO.md),
[CAPACITY.md](../../bootstrap/compiler/c0/CAPACITY.md) and
[NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md).

Full Compiler, self-hosting and Verified nqlc remain `NOT_IMPLEMENTED`. The C0
components have bounded full-source generation comparisons; this remains a
Core component proof, with the limitations and open signal-attribution issue
recorded in `CAPACITY.md` and `NATIVE_OS.md`.

Exact statuses live in `bootstrap/manifest.tsv`.

## Reference Compiler R0

The existing `src/*.asm` implementation is Reference Compiler R0. It is kept
working as a semantic oracle and compatibility compiler while the canonical
chain is developed. It is not Stage 0 and is not self-hosted.

R0's current pipeline is:

1. `lexer_run` tokenizes source into fixed-size token buffers.
2. `parser_run` validates syntax and emits the current flat IR.
3. `opt_run` applies lightweight release-mode passes.
4. `cg_run` lowers IR into NASM source.
5. `write_output` writes assembly for the compatibility wrapper.

R0 output currently uses Linux syscalls, a stack-based function ABI, `rax`
returns, `rbp`-relative locals, and a simple generated heap region.

## Legacy Compatibility Paths

The LLVM and Python files under `tools/`, plus `tests/llvm/` and `tests/ir/`,
are frozen legacy/reference paths. They remain useful for regression history
and parity oracles, but they are outside the canonical bootstrap chain and are
not the destination of new language architecture.

## Repository Boundaries

- `bootstrap/`: canonical machine foundation, implemented stages and their contracts
- `src/`: Reference Compiler R0 sources
- `tests/bootstrap/`: canonical bootstrap evidence
- `tests/compiler/`: R0 compatibility and semantic regression evidence
- `tests/llvm/`, `tests/ir/`: frozen legacy-path maintenance evidence
- `tools/`: compatibility and inspection helpers, not bootstrap trust roots
- `build/`: generated R0 and compatibility artifacts

## Dependency Rule

Every canonical stage must document its input, output, exact predecessor,
external dependencies, deterministic verification procedure, diagnostics, and
failure exit codes. An implementation is not self-hosted merely because it is
written in assembly or in NolQu-L.
