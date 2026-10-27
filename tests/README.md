# NolQu-L Tests

Tests are now grouped by purpose instead of staying in one flat directory.

## Sections

- [compiler](compiler): main compiler smoke, regression, and diagnostics suites
- [bootstrap](bootstrap): canonical machine-foundation and bootstrap-chain tests
- [llvm](llvm): frozen bootstrap LLVM maintenance suite
- [ir](ir): bridge, diagnostics, and parity suites for the IR-to-LLVM path
- [meta](meta): release and metadata consistency checks
- [shared](shared): shared shell helpers

Each folder now also has its own local README for quick orientation.

## Start Here

- [run_tests.sh](compiler/run_tests.sh): full suite entry point
- [run_tests.sh](bootstrap/run_tests.sh): canonical bootstrap suite
- [smoke.sh](llvm/smoke.sh): frozen LLVM bootstrap maintenance suite
- [release_check.sh](meta/release_check.sh): version/doc consistency checks

## Typical Commands

```bash
make test
make bootstrap-test
make machine-foundation
make stage0
make stage0-test
make release-check
make smoke
make llvm-smoke
```
