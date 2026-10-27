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

There is not yet a formal installer or OS package layout.

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

## Packaging Direction

Future packaging work should aim for:

- a clean install story for `nql`, `nolqul`, `nqlc`, and `nolqulc`
- reproducible build and test entry points
- explicit separation between canonical bootstrap, R0, and legacy paths
- metadata that stays aligned with `VERSION` and `CHANNEL`

## Current Recommendation

For now, treat the repository itself as the primary distribution format.

If a later release adds install targets, binary packaging, or release bundles,
this document should become the place that explains those formats.
