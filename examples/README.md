# NolQu-L Examples

Examples are now grouped by purpose instead of mixing starter files,
semantics-focused programs, and LLVM experiments in one flat layout.

## Sections

- [canonical](canonical/README.md): checked C0 checksum and native argv/file reader
- [core](/root/Nolqu/examples/core): smallest starter programs
- [semantics](/root/Nolqu/examples/semantics): language behavior and semantic rules
- [llvm](/root/Nolqu/examples/llvm): frozen legacy LLVM compatibility examples

## Start Here

If you are new to NolQu-L, start with:

- [canonical guide](canonical/README.md) for explicit `--backend canonical`,
  direct ELF and the experimental native OS boundary; R0 remains the default

- [hello.nq](/root/Nolqu/examples/core/hello.nq)
- [arrays.nq](/root/Nolqu/examples/core/arrays.nq)
- [functions.nq](/root/Nolqu/examples/semantics/functions.nq)
- [branching.nq](/root/Nolqu/examples/semantics/branching.nq)

If you want LLVM-specific examples, start with:

- [llvm_basic.nq](/root/Nolqu/examples/llvm/llvm_basic.nq)
- [llvm_func.nq](/root/Nolqu/examples/llvm/llvm_func.nq)
- [llvm_fact.nq](/root/Nolqu/examples/llvm/llvm_fact.nq)
