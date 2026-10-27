# NolQu-L Compatibility

## Canonical Target

The first canonical target is x86_64 Linux ELF64. `hex0.seed` uses raw Linux
syscalls and runs directly on x86_64 Linux or under `qemu-x86_64` on another
Linux architecture.

Reconstructing the seed from its auditable text manifest uses Bash and
`sha256sum` as explicit host verification tools. They are not compiler stages.

## Reference Compiler R0

Current source programs use Reference Compiler R0 and commonly require:

- `nasm`
- `x86_64-linux-gnu-ld` or compatible `ld`
- `qemu-x86_64` on non-x86_64 hosts

This remains the best-supported user path until the canonical compiler reaches
equivalent language coverage.

## Legacy LLVM Compatibility

Some existing commands and tests additionally require Python, Clang, and LLVM.
Those paths are frozen compatibility tooling. They are not canonical NolQu-L
dependencies and are not a portability target for future bootstrap stages.

## Compatibility Rule

Valid R0 programs and tests remain protected while canonical stages are added.
Any intentional breaking change needs an explicit migration, updated tests,
and a documented architectural reason.
