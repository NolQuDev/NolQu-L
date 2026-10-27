# NolQu-L Examples

Examples are now grouped by purpose instead of mixing starter files,
semantics-focused programs, and LLVM experiments in one flat layout.

## Sections

- [canonical](canonical/README.md): checked C0 checksum and native argv/file reader
- [core](core): smallest starter programs
- [semantics](semantics): language behavior and semantic rules
- [llvm](llvm): frozen legacy LLVM compatibility examples

## Start Here

If you are new to NolQu-L, start with:

- [canonical guide](canonical/README.md) for explicit `--backend canonical`,
  direct ELF and the experimental native OS boundary; R0 remains the default

- [hello.nq](core/hello.nq)
- [arrays.nq](core/arrays.nq)
- [functions.nq](semantics/functions.nq)
- [branching.nq](semantics/branching.nq)

If you want LLVM-specific examples, start with:

- [llvm_basic.nq](llvm/llvm_basic.nq)
- [llvm_func.nq](llvm/llvm_func.nq)
- [llvm_fact.nq](llvm/llvm_fact.nq)
