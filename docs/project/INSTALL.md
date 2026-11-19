# NolQu-L Install

## Current Install Model

Run `./nql` and `./nqlc` in the repository, or install the tools under a
prefix. For a user-local combined installation, run this from the checkout:

```bash
PREFIX="$HOME/.local" ./install.sh
```

The installer places `nql`, `nqlc` and their long aliases in `$PREFIX/bin`.
It reuses an executable `build/nqlc-r0` when available. From a clean checkout
it builds R0 with NASM and an x86_64 ELF linker. You can also invoke the
installer by path from another directory. A relative `DESTDIR` stages the
prefix under the directory where you invoked the installer.

For a canonical-only installation, use a separate prefix:

```bash
PREFIX="$HOME/.local/nolqu-core" ./install.sh --canonical-only
"$HOME/.local/nolqu-core/bin/nqlc" --backend canonical program.nql -o program
```

This installation uses the bundled bootstrap assets. To uninstall, pass
`--uninstall` with the same `PREFIX` and, for a staged installation, `DESTDIR`.

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
