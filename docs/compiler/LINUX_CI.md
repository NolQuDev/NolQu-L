# Linux CI and native Termux coverage

Status: EXPERIMENTAL host qualification. Target repository: `NolQuDev/NolQu-L`.
This is not a release workflow or a new compiler stage.

Development stays in native Termux private storage. The current Android host
denies actual hard-link creation, including `ln` in a private test directory.
File copies, hashes, atomic rename and symlink controls do not establish the
same-inode protections exercised by the hard-link tests. Those required tests
remain failed/unqualified on that host; they are not removed, replaced by mocks,
or counted as passed. A Linux result is separate evidence for its recorded host.

`.github/workflows/linux-qualification.yml` uses one Ubuntu24.04 x86_64 job.
It runs on pull requests, pushes to main or ci/**, and manual dispatch. Checkout
and artifact upload are pinned to full verified commit SHAs. Contents access is
read-only, checkout does not persist credentials, and no publication/deployment
credential is supplied to tests.

The runner first verifies the actual Linux architecture, required executables,
and a real shared inode with mutation through its second name. Failure produces
a BLOCKED report and nonzero status before compiler gates. Required gates run
sequentially: CI/publication controls, tracked-publication path validation,
five existing hard-link methods, full make test,
complete MCP discovery, runner/Android controls, finite native-boundary assurance
and release metadata checks. Each command runs once. A later successful command
cannot mask an earlier failure. Missing tools and unsupported checks are not PASS.

The existing bounded runner owns child cleanup and retains exact streams,
commands, identities, status and supervisor records. Limits selected for this
workflow are45 minutes per command,50 minutes aggregate and32MiB per captured
stream, within a60-minute job. These are execution budgets, not measured compiler
performance thresholds. RSS is not capped. Job termination or service/storage
failure can still prevent final upload; absence of a complete report is not PASS.

The artifact contains result.json, calls/invocations.json and raw streams,
component-generation receipts/artifacts, named CLI/project/MCP/process receipts,
the assurance corpus/results, tool/package versions and canonical input hashes.
CI validates the canonical identities again after the gates. Artifact retention
inherits GitHub repository settings; no permanent archive or numeric project
retention policy is claimed. Download important failures into maintained evidence.

Host dependencies: Ubuntu packages Bash/coreutils, make, Python/venv, NASM,
GNU binutils, QEMU user-mode, Clang and LLVM; test packages MCP SDK1.29.0 and
PyYAML6.0.3. NASM/GNU tools inspect/test and build only Reference Compiler R0;
they are not canonical compiler stages. Python orchestrates tests and MCP.
PyYAML parses the workflow in controls (MIT license); it has no compiler runtime
role. System package versions and transitive Python dependencies are recorded
after installation but are not locked. This development job is not a fully
reproducible release builder. SBOM, signed artifacts and formal provenance are
NOT IMPLEMENTED; recorded hashes and source revision are not substitutes.

Local workflow controls (PyYAML required) run with:

```sh
python3 -B -W error::ResourceWarning tests/ci/test_linux_qualification.py -v
```

Actual qualification requires the declared Linux host:

```sh
python3 -B .github/scripts/linux_qualification.py --output /new/private/evidence
```

The output directory must not exist. Native Android rejects this Linux
qualification command explicitly; its actual smoke/control results remain in
the Android session evidence. A green workflow is not Full Compiler, self-hosting,
Verified nqlc, whole-language Safety, or stable release qualification. Historical
C032-SIGNAL-01 remains OPEN until the original unexplained signal is attributed.

Required branch/ruleset checks and independent review policy must be configured
and verified separately; this document does not claim protection is enabled.
Changing repository hosting name does not rename canonical compiler artifacts.
