# NolQu-L Design Decisions

This document records important current design decisions so they do not remain
implicit or drift across docs, tests, and implementations.

The normative language philosophy is the [Nine Pillars of NolQu-L](DESIGN_PRINCIPLES.md).
Implementation decisions and historical notes below do not override those pillars.

## Current Decisions

### Full Name And Short Form

`NolQu-Lang` is the full name and `NolQu-L` is the established short form.
The L already means Language; neither form receives an additional Language
suffix. `NolQu` names the broader ecosystem. Canonical commands remain `nql`
and `nqlc`, with long aliases `nolqul` and `nolqulc`. Historical artifact/path
identifiers stay intact; obsolete command names are not installed aliases.

### Bootstrap Has One Canonical Chain

The canonical chain begins with auditable machine bytes and advances through
Stage 0, Bootstrap, Core, Full, Self-Hosting, and Verified compiler stages.
LLVM, Python, NASM, and other host compilers are not hidden canonical stages.

### Existing Compiler Is Reference Compiler R0

The compiler in `src/*.asm` is maintained as the current compatibility and
semantic reference implementation. It is not Stage 0 and is not self-hosted.

### One Current Semantic Oracle

Reference Compiler R0 and its valid tests are the current behavioral oracle
until a canonical NolQu-L Core Compiler can replace it.

Implication:

- legacy LLVM paths must not become separate language authorities

### NASM Is R0's Maintained Output Path

The NASM output path remains the current usable default and parity baseline,
but it is outside the canonical bootstrap chain.

### LLVM And Python Paths Are Frozen Legacy

The source-level LLVM parser and IR-to-LLVM tools are not the long-term
direction.

Implication:

- they are frozen as maintenance and reference paths
- new semantics must not grow there first

### IR Bridge Is Compatibility Tooling

The retained legacy flow is:

`real frontend -> real IR -> export-ir -> ir-json -> ir-llvm`

Current implementation note:

- `ir-json` is handled by `tools/nq_ir_dump_parser.nq`
- `ir-llvm` still uses `tools/nq_ir_json_to_llvm.py` while
  `tools/nq_ir_json_to_llvm.nq` catches up to byte-for-byte parity

This flow is outside the canonical compiler chain and receives no new
architectural role.

### Locals Are Currently Function-Scoped

Local variables are currently function-scoped, not block-scoped.

Implication:

- duplicate local names across nested blocks in the same function are errors
- block-scoped locals are deferred rather than partially implied

### Argument Model Is Intentionally Simple

Current function arguments are:

- positional-only
- left-to-right evaluated
- not defaulted
- not named
- not variadic

### Arrays Behave As Shared Mutable Values Across Ordinary Calls

In the current model, array mutation inside a callee is visible to the caller.

### Docs, Examples, And Tests Move Together

A meaningful user-visible semantic change should normally update:

- docs
- examples when relevant
- tests

## Related Docs

- [SEMANTICS.md](SEMANTICS.md)
- [FEATURE_STATUS.md](FEATURE_STATUS.md)
- [LLVM_BOOTSTRAP_POLICY.md](../compiler/LLVM_BOOTSTRAP_POLICY.md)
- [LLVM_BRIDGE.md](../compiler/LLVM_BRIDGE.md)
