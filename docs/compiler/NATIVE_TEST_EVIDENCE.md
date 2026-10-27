# Native-test invocation evidence

Status: EXPERIMENTAL host-test capability. Source integration2026-10-26;
exact-input full-gate evidence is recorded in the
[reliability report](../project/VALIDATION.md).

This is host inspection/test tooling for `tests/bootstrap/c031_support.py`.
It is outside the canonical compiler pipeline. It changes no source-language,
ABI, runtime, bootstrap-stage, seed or release contract.

`run_native` keeps its ordinary `subprocess.run` path when
`NQL_NATIVE_EVIDENCE_DIR` is absent. To retain observations, create an existing
trusted directory outside disposable test trees, then opt in explicitly:

```sh
mkdir -m 700 /tmp/nql-native-observations
NQL_NATIVE_EVIDENCE_DIR=/tmp/nql-native-observations \
  python3 -B -W error::ResourceWarning tests/bootstrap/test_c0_capacity_backend.py -v
```

An empty, missing or unusable root fails with `NativeEvidenceError` before
launch; it does not silently write into the current directory. Each invocation
uses a unique private `call-*` directory and writes `begin.json`, `launched.json`
and `result.json` atomically. Every record file/blob is0600; per-call and new
blob directories are0700. The caller owns/trusts the archive root. Source,
argv and streams can contain sensitive data; archive them accordingly. The
observer does not dump environment values or add a shell invocation; caller Popen options remain unchanged.

A content-addressed `blobs/<sha256>` store retains the exact requested target
executable, QEMU adapter when selected, supplied stdin and captured byte streams.
An explicit `executable=` override is recorded separately from argv[0]; readable
regular search candidates are retained in lookup order using the actual child
cwd and environment PATH. The kernel performs symlinks-before-`..` lookup through the original logical
path. A separately live canonical filename is not required, including an
open unlinked executable selected through a passed proc FD. `lookup_path` is
the syscall-addressable request; `path` is a best-effort opened-FD link hint
(which may end in `(deleted)` or be unavailable). `cwd_lookup`, requested cwd
and best-effort observed process cwd remain separate metadata. Candidate lookup
failures (including unused PATH entries) are explicit and do not abort launch.
Blob publication/integrity failures remain fatal, distinct from path failures. PATH
prediction does not attest which bytes the kernel executed.
A blob is published only after its complete bytes are closed. Writers hold an
exclusive `flock` on the blob directory while checking for an existing blob and
renaming a new complete file; existing bytes/mode/type must agree. This works
without `os.link`, which Android Python does not provide. The lock coordinates
writers using this helper, not arbitrary same-UID modifications. Evidence descriptors are
closed before spawning, so descriptor-error tests retain their original target.
External stdin descriptors are identified without reading, seeking or replacing
them; their payload remains **UNOBSERVED**. Files merely named by argv are not
automatically read. Uncaptured streams are distinct from captured empty bytes.
Text-mode snapshots are marked `decoded-text`, encoded UTF-8 with surrogatepass,
and must not be represented as original raw output bytes.

Observation opens executable paths with NONBLOCK/CLOEXEC, checks the opened
descriptor is regular, then reads. Raw read descriptors remain owned by an
explicit try/finally through type/read errors; no fdopen ownership transfer is
needed for untrusted paths or existing blobs. A FIFO before spawn is rejected; a FIFO
replacement after exit is an explicit target_after error and changed identity.
Metadata observation cannot wait for a FIFO partner. Publication promises atomic
visibility; parent directories are not fsynced, so power-loss durability is not
claimed.

The records include lossless byte argv, requested cwd/timeout, caller identity,
child PID and observed `/proc` start ticks/parent/group/session/exe link where
available, UTC/monotonic times, returncode, signal-number interpretation,
timeout/cancellation/spawn-error classification and observer cleanup attempts.
Unavailable proc fields are explicit; short-lived children and host permissions
can limit observation. File identities are observed before/after execution;
`target_changed` flags replacements. A pre-spawn hash does **not** lock the
kernel's executable against races, prove immutable exec bytes, or identify who
sent a signal. A cleanup action records an attempt, not proof of delivery.

With observation enabled, `Popen` receives the same command and caller kwargs.
It preserves the existing input/check/capture-output validation, inherited fds,
`preexec_fn`, cwd, negative status and exception behavior. Ordinary `-9` is a
signal result when `check=False`; an actual timeout still raises
`subprocess.TimeoutExpired` with its partial output. Timeout/cancellation uses
only the owned Popen handle and its ordinary cleanup semantics. There are no
new sessions, group kills, supervisors, RLIMITs, retries or stream prefixes.
Inherited caller `preexec_fn` remains the caller's responsibility. Descendant
cleanup is not broadened beyond the original helper contract.

`result.json.complete` means the terminal observation was committed, not that
the guest or enclosing test passed. Nonzero expected diagnostics and controlled
signal tests can have complete records. Timeout partial streams are retained
when supplied by `TimeoutExpired`; arbitrary cancellation may leave streams
unobserved. Never convert `None` into a claim of observed empty bytes. A harness
SIGKILL may leave only begin/launched: missing terminal evidence stays incomplete.

If observation fails after launch, the owned child is reaped and a distinct
`NativeEvidenceError` retains `record`, any original `result`, and
`original_error` for the caller. It never fabricates guest success/diagnostics.
Disk exhaustion can prevent a terminal file; the in-memory error and already
committed records still describe the evidence failure. No storage quota, retention
period, sender attribution, OOM detector or whole-tree memory-safety claim is added.

The archive is not tamper-proof or a process sandbox: a child running with the
same UID can access its inherited environment and the selected archive. A caller
preexec function can also alter cwd/environment before exec; those effects are
not predicted from its Python object. Such observations and executable hashes
remain best effort, not an attestation or a signature.

The source/helper hash, archive selection and host toolchain must also be bound
by the enclosing gate receipt. These sidecars are separate from strict generation
stages/checks/artifacts: enabling them does not create extra compiler generations
or promote the canonical Full Compiler/self-host/Verified milestones.

## Controls and limits

The real host control suite is `test_run_native_evidence.py`, with test IDs
NE01–NE19: retention through caller cleanup; enabled/disabled and check behavior;
signal vs timeout; fd/cwd/bytes semantics; unavailable proc/spawn/archive errors;
own-child cancellation with a live unrelated sibling; file replacement and
parallel uniqueness, bounded FIFO observation, explicit executable retention, symlink/parent path
semantics, directory FD lifetime, unused bad PATH entries and an open unlinked
executable without consuming or closing its caller-owned passed FD, and a
deleted parent cwd with either valid absolute child cwd or inherited cwd.
NE18 verifies real input/output retention when hard-link publication is unavailable.
NE19 exercises the already-closed stdout case with observation enabled and disabled.
On Android the control entrypoint starts a fresh interpreter without the Termux
exec shim, retaining other preload libraries, so symlink/parent and deleted proc-FD
tests exercise kernel lookup. Changing only a child's environment cannot unload
the parent's exec interceptor. Closed-FD error tests close stdout after host
runtime startup too: Android Python may reopen a missing standard descriptor.
The inherited deleted-cwd control uses `sh -c 'exit 0'`, avoiding a resolved
Termux multicall `true` binary whose behavior depends on its invocation name.
An absolute child cwd does not require the parent cwd to have a name; relative
kernel lookup remains usable when a physical cwd hint is unavailable.
It selects only the host adapter for its Python controls;
it is not a compiler correctness oracle. Actual x86/QEMU behavior requires the
existing canonical suites with observation enabled.

The observer adds source/output copying, hashing, fsync and metadata I/O to host
tests; it changes no generated program's runtime cost. Measure archive size and
elapsed gate time, without calling instrumented timings compiler benchmarks.
Full ptrace is unsuitable for this host's tight concurrent15s materializer gate:
the traced suite failed that deadline; the unchanged exact method passed in2.152s
without ptrace. The failed experiment remains evidence, not a PASS or quarantine.
External selective tracing may help controlled reproductions, with its own
limits. Kernel/OOM telemetry is restricted on the current Android/PRoot host.

C032-SIGNAL-01 remains OPEN: the original comparison backend's PID/start/sender
were not retained. A subsequent pass or better logging cannot reconstruct them.
