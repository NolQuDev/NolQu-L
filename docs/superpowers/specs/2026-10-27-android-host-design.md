# Android host smoke bundle

Status: EXPERIMENTAL host tooling. This is not a new compiler stage or target.

## Initial context and decision (historical)

The user selected Android development and sequential tests, delegating the host
choice. Termux Python/Bash/Make/QEMU are installed. The current process remains
traced by PRoot; invoking Termux binaries here does not remove that trace.
An existing same-UID Termux service launch returned255 with `Can't start from
invalid source: 10367`. No native task started and no permission/property changed.

Use the available PRoot host for validation and prepare an independent byte-copy
bundle for an ordinary Termux shell. Do not enable external-app execution, root,
change SELinux, start an SSH server, or replace the current workspace. Native
execution must remain NOT TESTED until a real untraced Termux process runs it.

Alternatives: retain PRoot only (usable, does not test the alternative); a new
AArch64 compiler backend (unrelated major work); automatic Android service
launch (unavailable under the observed caller boundary). The portable smoke
bundle is the smallest useful step that does not depend on changing permissions.

## Deliverable

`tools/nql_android_smoke.py prepare --root ROOT --bundle NEW_DIRECTORY` copies
the pinned B0/frontend/backend seeds, the existing bounded host runner, the
native-cat example, and this tool into a private new directory. Verify source
pins before publication. Copy bytes into independent regular files; use neither
hard links nor guest symlinks. Write the manifest last. Existing directories are
never replaced. A failed preparation may leave an incomplete new directory;
without a valid manifest it is unusable and must not be reported as prepared.

The copied tool accepts `run --bundle BUNDLE --output NEW_DIRECTORY` and optional
`--require-native-termux`. Validate the fixed manifest file set and all hashes
before importing the copied runner or launching any seed. The bundle is trusted
local code; hashes detect byte drift, not provenance or a malicious replaced
manifest. Record actual Python, adapter identity, process context and raw calls.

Native context means the running Python comes from the Termux prefix, Android
is present, and its actual proc status explicitly reports TracerPid0. Missing
status is unknown, never zero. Any traced process fails the native requirement.
The classification describes the observed process, not full platform support.

All calls are sequential, one attempt each, using the existing BoundedRunner:
15s per invocation,300s aggregate,8MiB per stream,3MiB input. No RSS cap is
claimed. Validate B0 help and compilation, frontend/backend determinism, return,
nested calls, binary byte/stream roundtrip, checked faults, located syntax and
semantic rejection, malformed AST, and the native-cat argv/syscall example.
Do not call this a full regression or a bootstrap-generation verification.

## Trust boundaries and invariants

| Boundary / plausible failure | Protection and test |
| --- | --- |
| Source seed/pin to copied executable: corruption or tampering | Exact pin and manifest hashes; AB01/AB02/AB04 |
| Guest filesystem to native filesystem: alias corruption/disclosure | Independent regular byte copies, private directories, fixed names; AB01/AB03 |
| Unknown proc status to native claim: false qualification | Explicit TracerPid and actual interpreter checks; AB06/AB07 |
| Bundle metadata to host execution: path traversal or unexpected privilege | Fixed allowlist, validate before runner import/spawn; AB04 |
| Generated program to machine: wrong code or unsafe behavior | Defined output/error oracles and existing checked bounds; AB08 |
| Guest process to host resources: hang/output exhaustion/cancellation | Existing bounded runner and its11 lifecycle tests; AB08 |
| Output path to existing evidence: accidental replacement | New private directory required; AB05 |

No network, package install or host-shell evaluation is part of bundle execution.
Residual risks: Android can still kill a process; proc visibility varies; native
Termux remains unqualified until run; finite smoke cases are not a security scan.
The historical C032-SIGNAL-01 remains OPEN. Earlier lost metadata is not recreated.

## Native continuation and review repairs — 2026-10-27

The migrated conversation now runs in native Termux with observed `TracerPid: 0`.
The migration receipt and native three-call source-to-ELF preflight are retained
in `~/nql-native-migration-20261027/`. Earlier traced results remain historical.
Full native regression is a separate gate; a host context change is not evidence
that it passed.

The runner loader compiles and executes the exact source bytes checked against
the initial verified manifest. It does not use a Python loader that can consume
unchecked `.pyc` files from the copied directory (AB10). These are trusted local
bundles, not a sandbox or signed provenance.

Report publication uses unique private staging, `fsync`, atomic replacement and
owned cleanup on failure. An intermediate rename error must not prevent a later
terminal `FAILED` report or leave a stale success claim (AB11). Storage failure
can still prevent a terminal file; a caller must treat the exception as failure.

Adapter identity has a separate policy from seed/input/output capacity: stream
64KiB chunks from one regular descriptor, reading at most its initial size and
rejecting size/time metadata changes during hashing. Compare identity again at
the end. No larger arbitrary capacity constant is introduced. This bounds
memory per read and excludes growing-file loops; it does not impose an RSS or
whole-tool time limit on arbitrary trusted adapter files (AB12).

| Additional boundary | Invariant / test |
| --- | --- |
| Cached host bytecode to source pin | Execute pinned source bytes; unverified pyc marker never runs; AB10 |
| Report rename failure to terminal status | Preserve FAILED and remove only owned staging; AB11 |
| Adapter file to guest stream budget | Larger regular adapter hashes correctly; guest stream limits stay fixed; AB12 |
| Android Python to shared evidence blobs | Atomic complete publication without hard links; NE18 plus NE07/NE10/NE14 |

The evidence helper and its controls change intentionally for Android support.
Their old 61-input closure stays historical, while compiler sources, seeds,
pins, versions and bootstrap topology remain fixed. Native gate results and
remaining blockers belong in the session report; no old baseline is relabeled.

## Native qualification repairs — measured follow-up

The first native full run exposed more host assumptions. Android runtime startup
may reopen standard descriptors closed before QEMU starts. Test fixtures therefore
keep actual descriptor closure on Linux, but on native Android use a write-only
stdin or read-only stdout/stderr. The guest syscall still fails with `EBADF`;
all existing exit-code and diagnostic oracles remain fixed. Python fixtures use
`standard_fd_fault.py`; shell fixtures use `run_with_invalid_standard_fd`.
This does not claim native coverage of a descriptor remaining closed through
Bionic startup. NE20 validates all three error descriptors after host startup.

The native MCP supervisor found that Python omits pidfd bindings although the
runtime libc exposes the declared APIs. The worker now prefers the complete
Python pair, otherwise binds `pidfd_open(int, unsigned int)` and
`pidfd_send_signal(int, int, void*, unsigned int)` using ctypes. A null siginfo
and zero flags match existing calls. It probes a handle to itself and signal0
before any target can launch. Missing APIs or failed calls still fail closed.
Pidfds, observed process identity, isolated subreaper ownership, deadlines and
cleanup rules remain unchanged; no PID-only or process-group signaling fallback
is introduced. No raw ISA syscall number or permission change is needed.

Decision status: internal repair under the existing host cleanup contract,
implemented with runtime tests in progress; no public RFC/ADR acceptance claim.
Alternatives rejected: removing the pidfd requirement weakens process ownership;
raw-number syscall wrappers duplicate a runtime ABI already exposed by libc;
read-only MCP leaves the native build workflow unavailable. Libc/ctypes were
already host dependencies of this worker, outside canonical bootstrap.

The process-boundary suite now includes Android and forces absent Python
bindings to test libc success, owned-tree timeout cleanup and missing-all-APIs
rejection before target launch. Temporary-directory assertions follow the actual
host temporary root. No test is skipped merely to qualify native Termux.
Libc-success cases inspect actual symbol availability: older Linux libc without
the optional exports must still reject the forced-libc path before target launch.
Production keeps the complete Python pair as its first choice.

The native SDK fixture and copied MCP configuration explicitly pass the standard
Termux exec preload omitted by SDK environment filtering. No permissions change
or hot reload is implied. The wide-branch oracle uses existing native `ndisasm`
on Android, preserving the original GNU command on other Linux hosts, real
instruction boundaries and the positive/inside-immediate negative controls.
Output is parsed incrementally through a pipe under a 60-second deadline;
the owned decoder is killed and waited on failure. An initial temporary-file
implementation hit the inherited 32MiB file limit on real wide output; that
failed attempt is retained, and the runner limit was not increased.
The failed native GNU package experiment and its verified package hash are
retained outside the repository; no LLVM tool or linker was replaced.

## Compatibility and rollout

Keep all compiler sources, seeds, pins, public commands, ABI, VERSION1.0.2a1 and
CHANNELdev unchanged. Existing named gates and behavior oracles are retained.
The previous1080-marker full regression and combined proof remain historical;
eight host proof inputs intentionally changed during native repairs, so the old
61-input closure is not reused to prove this new code. Native tooling receives
fresh scoped gates and real smoke execution, with results in the session report.
Rollback restores only session-owned host changes from retained snapshots,
without removing evidence or altering the dirty compiler tree. No artifact
migration or release is involved. No formal RFC/ADR number is assigned.
