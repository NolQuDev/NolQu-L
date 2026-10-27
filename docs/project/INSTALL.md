# NolQu-L Install

## Current Install Model

NolQu-L is currently used directly from the repository.

There is not yet a formal system-wide installer, package manager release, or
binary distribution process.

## Requirements

Canonical seed execution requires x86_64 Linux or `qemu-x86_64`. Reconstructing
the seed from `hex0.hex` requires Bash and `sha256sum` as explicit host tools.

Reference Compiler R0 and legacy compatibility tests additionally use:

- `nasm`
- `x86_64-linux-gnu-ld` or compatible `ld`
- `clang`
- `llvm-as`
- `qemu-x86_64` when running x86_64 binaries on non-`x86_64` hosts
- `make`
- `python3` for LLVM bridge helper tooling

Those additional tools are not canonical bootstrap dependencies.

## Basic Setup

Verify the canonical machine seed:

```bash
make machine-foundation
make bootstrap-test
```

Build Reference Compiler R0:

```bash
./nql --build-compiler
```

Or:

```bash
make compiler
```

Run a small example:

```bash
make run EXAMPLE=examples/core/hello.nq
```

Run the full suite:

```bash
make test
```

## Current Recommendation

- use repo-local `./nql` or its formal alias `./nolqul`
- use repo-local `./nqlc` or its formal alias `./nolqulc` for direct compilation
- use the root `Makefile` for common workflows
- treat R0's NASM path as the current compatibility default
- do not describe R0 as Stage 0 or self-hosted

## Future Direction

If NolQu-L later gains a formal install target, package recipe, or release
bundle, this document should be expanded to describe that process directly.
