# NolQu-L Compiler Test Suites

This folder contains the primary test suites for the stable compiler path.

## Contents

- [smoke.sh](/root/Nolqu/tests/compiler/smoke.sh): fast checks for visible user-facing behavior
- [regression.sh](/root/Nolqu/tests/compiler/regression.sh): regressions in the main compiler workflow
- [diagnostics.sh](/root/Nolqu/tests/compiler/diagnostics.sh): parser and semantic error behavior
- [run_tests.sh](/root/Nolqu/tests/compiler/run_tests.sh): full suite entry point across compiler, LLVM, and IR layers
