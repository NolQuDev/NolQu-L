# NolQu-L Packaging

## Current Packaging Model

NolQu-L is currently packaged as a source repository with:

- the canonical machine foundation in `bootstrap/`
- Reference Compiler R0 source in `src/`
- canonical executables `nql` and `nqlc`
- formal aliases `nolqul -> nql` and `nolqulc -> nqlc`
- a root `Makefile`
- documentation in `docs/`
- examples in `examples/`

`install.sh` and `make install` provide the existing local installation path.
A distribution-specific OS package layout is not yet defined.

## Current Entry Points

- `make machine-foundation`
- `make bootstrap-test`
- `./nql` for project-local build/run usage
- `./nqlc` for direct compilation
- `make compiler`
- `make run`
- `make check`
- `make test`

## Build Artifacts

Generated artifacts are kept under `build/`, including:

- compiler object and binary
- generated assembly
- exported IR
- derived LLVM bridge artifacts

The canonical `hex0.seed`, its byte manifest, and its hash live under
`bootstrap/machine/x86_64-linux/`; they are source-controlled trust artifacts,
not disposable `build/` output.

## Alpha release assets

An Alpha release includes a committed source archive, an optional offline host
bundle, SHA256SUMS, BUILD-METADATA.json and QUALIFICATION.json. Both archives
are generated twice and compared before publication. Tar/gzip metadata is
controlled by the packager; the source archive is made from the exact Git
revision, preserving public file modes and internal symlinks. Private paths and
links outside its root are rejected. The offline archive contains independent
regular copies of the pinned B0/frontend/backend, host supervisor/oracle and
utility source, plus its manifest and license.

These are source/bootstrap and host-testing distributions, not a new Full
Compiler or a new target backend. The offline profile remains experimental on
native Termux until actual native receipts establish that scope. Source and
archive hashes are integrity evidence; signing, formal provenance and SBOM
are NOT IMPLEMENTED. See [RELEASING.md](RELEASING.md) for the publication gate.

## Packaging Direction

Future packaging work should aim for:

- a clean install story for `nql`, `nolqul`, `nqlc`, and `nolqulc`
- reproducible build and test entry points
- explicit separation between canonical bootstrap, R0, and legacy paths
- metadata that stays aligned with `VERSION` and `CHANNEL`

## Current Recommendation

For now, treat the repository itself as the primary distribution format.

Use the Alpha source archive for a versioned public snapshot, and the optional
offline bundle for bounded host checks. No stable OS package is promised.
