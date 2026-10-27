# NolQu-L Tests

Tests are now grouped by purpose instead of staying in one flat directory.

## Sections

- [compiler](/root/Nolqu/tests/compiler): main compiler smoke, regression, and diagnostics suites
- [bootstrap](/root/Nolqu/tests/bootstrap): canonical machine-foundation and bootstrap-chain tests
- [llvm](/root/Nolqu/tests/llvm): frozen bootstrap LLVM maintenance suite
- [ir](/root/Nolqu/tests/ir): bridge, diagnostics, and parity suites for the IR-to-LLVM path
- [meta](/root/Nolqu/tests/meta): release and metadata consistency checks
- [shared](/root/Nolqu/tests/shared): shared shell helpers

Each folder now also has its own local README for quick orientation.

## Start Here

- [run_tests.sh](/root/Nolqu/tests/compiler/run_tests.sh): full suite entry point
- [run_tests.sh](/root/Nolqu/tests/bootstrap/run_tests.sh): canonical bootstrap suite
- [smoke.sh](/root/Nolqu/tests/llvm/smoke.sh): frozen LLVM bootstrap maintenance suite
- [release_check.sh](/root/Nolqu/tests/meta/release_check.sh): version/doc consistency checks

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
