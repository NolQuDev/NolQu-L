# NolQu-L IR Bridge Test Suites

This folder contains the suites for the exported-IR to LLVM path.

## Contents

- [bridge.sh](/root/Nolqu/tests/ir/bridge.sh): end-to-end export, parse, lower, and run checks
- [diagnostics.sh](/root/Nolqu/tests/ir/diagnostics.sh): malformed-IR and bridge failure diagnostics
- [parity.sh](/root/Nolqu/tests/ir/parity.sh): semantic parity checks against the stable NASM backend
