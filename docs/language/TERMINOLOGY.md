# NolQu-L Terminology

## Core Terms

### NolQu-L

The formal language, project, and architecture name. `Nolqu` remains only in
older compatibility names where changing it would break users.

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

### nq

The main repo-local CLI wrapper used to build, run, check, and inspect NolQu-L
programs.

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

- [CORE_LANGUAGE.md](/root/Nolqu/docs/language/CORE_LANGUAGE.md)
- [FEATURE_STATUS.md](/root/Nolqu/docs/language/FEATURE_STATUS.md)
- [BACKENDS.md](/root/Nolqu/docs/compiler/BACKENDS.md)
- [IR.md](/root/Nolqu/docs/compiler/IR.md)
