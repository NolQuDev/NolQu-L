# NolQu-L Compiler Test Suites

This folder contains the primary test suites for the stable compiler path.

## Contents

- [smoke.sh](smoke.sh): fast checks for visible user-facing behavior
- [regression.sh](regression.sh): regressions in the main compiler workflow
- [diagnostics.sh](diagnostics.sh): parser and semantic error behavior
- [run_tests.sh](run_tests.sh): full suite entry point across compiler, LLVM, and IR layers
