# Legacy LLVM Bootstrap Policy

## Purpose

This document limits the role of `tools/nq_llvm_bootstrap.py`.

The parser still exists for compatibility and regression continuity. It is
outside the canonical NolQu-L bootstrap chain and must not be treated as Stage
0, a self-hosting step, or a future semantic center.

For the currently frozen supported subset, see [LLVM_BOOTSTRAP_STATUS.md](/root/Nolqu/docs/compiler/LLVM_BOOTSTRAP_STATUS.md).

## Policy

### Allowed

- bug fixes
- diagnostics improvements
- small maintenance needed to keep existing bootstrap examples working
- temporary compatibility work while the IR bridge catches up
- keeping the frozen bootstrap subset working

### Not Allowed As New Architecture

- introducing major new language semantics in the bootstrap parser first
- treating bootstrap support as proof that a feature belongs to the NolQu-L core language
- expanding the bootstrap parser faster than the real frontend and IR path
- quietly widening the bootstrap subset without updating its status document

### Canonical Direction

New canonical compiler work follows:

1. Machine-Level Foundation
2. Stage 0
3. NolQu-L Bootstrap Compiler
4. NolQu-L Core Compiler
5. Full and self-hosting `nqlc`

## Decision Rule

The bootstrap parser receives only maintenance needed for existing supported
behavior. New language features belong in the canonical compiler design and
may be mirrored in Reference Compiler R0 for compatibility.

## Release Discipline

Before treating LLVM behavior as representative of NolQu-L itself, ask:

1. does the real compiler frontend support it?
2. does the real compiler IR represent it?
3. is there bridge coverage for it?
4. is the bootstrap parser merely matching that behavior rather than inventing it?

If the answer is no, the feature should stay experimental.
