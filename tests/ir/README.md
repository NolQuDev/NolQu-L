# NolQu-L IR Bridge Test Suites

This folder contains the suites for the exported-IR to LLVM path.

## Contents

- [bridge.sh](bridge.sh): end-to-end export, parse, lower, and run checks
- [diagnostics.sh](diagnostics.sh): malformed-IR and bridge failure diagnostics
- [parity.sh](parity.sh): semantic parity checks against the stable NASM backend
