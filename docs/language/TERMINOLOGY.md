# NolQu-L Terminology

## Core Terms

### NolQu-Lang / NolQu-L

**NolQu-Lang** is the full name; **NolQu-L** is its established short form.
The L means Language, so do not append another Language word to either name.
Both forms refer to the same systems programming language and architecture.

### NolQu

The ecosystem or umbrella project. Use NolQu-Lang or NolQu-L when referring
specifically to its source specifications and compiler semantics. Historical filenames, bootstrap artifact
identifiers, hashes and evidence keep their recorded spelling.


### Machine-Level Foundation

The smallest canonical executable trust root, represented as auditable CPU
instruction bytes and an executable image.

### Stage 0

The bounded symbolic flat-binary emitter built directly by the Machine-Level
Foundation. It resolves `.nql0` symbols and produces machine bytes for the
next compiler generation. Reference Compiler R0 is not Stage 0.

### Reference Compiler R0

The existing `src/*.asm` compiler used as the current semantic and
compatibility oracle while the canonical compiler is built.

### nql / nolqul

The canonical project manager and run command. `nql` is the executable and
`nolqul` is its long-name alias. New project sources use `.nql`.

### nqlc / nolqulc

The canonical compiler entry point and its long-name alias. The default
`--backend nasm` uses Reference Compiler R0; `--backend canonical` selects the
experimental Core pipeline. Obsolete public commands `nq`, `nqc`, `nolqu` and
`nolquc` are not installed compatibility aliases. Historical source/artifact
paths that contain older names are separate from the current command interface.

## Compiler Terms

### Frontend

The real compiler path that handles source parsing and semantic work before IR
and backend lowering.

### IR

The compiler's intermediate representation used between frontend work and
backend/code-generation work.

### Exported IR

The textual IR dump produced through `--export-ir`, used as a bridge artifact
for downstream tooling.

## Backend Terms

### R0 NASM Path

The current maintained compatibility output path. It is not canonical
bootstrap infrastructure.

### LLVM Bootstrap Parser

The source-level LLVM compatibility path, frozen outside the canonical chain.

### IR-To-LLVM Bridge

A retained legacy flow built from R0 exported IR. It is not the long-term
NolQu-L direction.

## Release Terms

### stable

The public release track.

### dev

The active work track for alpha, beta, and release-candidate work.

## Design Terms

### Core Language

The smaller supported language surface NolQu-L is intentionally trying to keep
coherent and readable.

### Experimental

Features or paths that exist but should not yet be treated as fully stable
language surface.

### Syntax-Only

Surface syntax that may exist in some form without being a mature or complete
semantic feature.

## Related Docs

- [CORE_LANGUAGE.md](CORE_LANGUAGE.md)
- [FEATURE_STATUS.md](FEATURE_STATUS.md)
- [BACKENDS.md](../compiler/BACKENDS.md)
- [IR.md](../compiler/IR.md)
