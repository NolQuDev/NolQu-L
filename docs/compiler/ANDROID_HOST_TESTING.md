# Android host smoke testing

Status: EXPERIMENTAL host tooling, targeting the existing x86_64 Linux seeds
through native Termux QEMU. This does not add an AArch64 compiler backend,
change the canonical bootstrap chain, or qualify self-hosting.

Use an ordinary native Termux session with Python and `qemu-x86_64` available.
The project and conversation migration are recorded separately in
`~/nql-native-migration-20261027/`; inspect `native-activation.json` and
`native-preflight.json` for the actual resumed context. Earlier PRoot evidence
keeps its original classification.

Prepare a new private bundle and run it into a different new directory:

```sh
python3 -B tools/nql_android_smoke.py prepare \
  --root "$PWD" --bundle "$HOME/nql-smoke-bundle-new"
python3 -B "$HOME/nql-smoke-bundle-new/android_smoke.py" run \
  --bundle "$HOME/nql-smoke-bundle-new" \
  --output "$HOME/nql-smoke-result-new" --require-native-termux
```

Both destination directories must be absent. The tool copies independent bytes,
checks the three seed pins, writes a fixed-file-set manifest last, and validates
it before launching. It does not use a compiler, assembler or linker to prepare
the bundle. Python and QEMU are host-test dependencies, outside the canonical
semantic build path. The manifest detects drift; it is not signed provenance or
a sandbox against someone who can replace trusted local files.

Native context requires Android, a Python executable resolving under the Termux
prefix, and actual `/proc/self/status` containing `TracerPid: 0`. Missing metadata
is unknown. A traced or unconfirmed process produces `BLOCKED` before guest
execution when the native requirement is set.

The finite profile runs 13 checks through 32 sequential guest invocations: B0
help/build/return; source-to-AST-to-ELF determinism and source dependence; nested
calls; binary streams; checked bounds/overflow; located syntax/semantic errors;
invalid AST; and the canonical `native_cat` argv/syscall example. Input filenames
containing shell punctuation remain literal arguments. Raw inputs, streams,
supervisor records and executable identities are retained under `calls/`.

Limits remain 15 seconds per invocation, 300 seconds across the guest runner,
8 MiB per captured stream and 3 MiB stdin. They are host test limits, not language
capacities. No RSS cap or whole-tool deadline is claimed. Adapter hashing reads
one regular descriptor in 64 KiB chunks, at most its initial size, rejects size or
timestamp drift, and compares the hash again after execution. Its file size does
not consume the guest stream limit. Large trusted adapter files still cost I/O.

`result.json` records actual host context, adapter identity, checks and limits.
Publication uses unique staging, fsync, rename and owned cleanup. An execution
or intermediate report failure produces `FAILED`, not success; persistent
storage errors can prevent terminal publication and then the command fails.
Never treat only `RUNNING`, a missing report, or exit failure as a passed gate.

The copied runner is compiled from the source bytes checked against the initial
manifest. Unchecked cached Python bytecode is not accepted as a replacement.
The runner owns and reaps its private guest descendants; it is not an OS sandbox.

Run the focused controls sequentially:

```sh
python3 -B -W error::ResourceWarning tests/bootstrap/test_run_native_evidence.py -v
python3 -B -W error::ResourceWarning tests/security/test_bounded_runner.py -v
python3 -B -W error::ResourceWarning tests/security/test_android_host.py -v
```

Evidence controls NE01–NE20 include atomic shared publication without hard links,
parallel writers, bad blobs, descriptor cleanup, cancellation and kernel path
lookup. On Android that control script reexecutes Python without only the Termux
exec shim, preserving other preload entries. It does not alter the project's
normal launch environment. The fixture checks both already-closed stdout and
host runtimes that reopen missing standard descriptors.
Guest I/O fault fixtures retain closed descriptors on Linux. On native Android
they preserve a live descriptor with the wrong access mode through QEMU startup,
so the guest still reaches the same `EBADF`, exit-code and diagnostic oracle.
They do not claim a closed standard descriptor survived Bionic startup.

The MCP supervisor prefers Python pidfd APIs or binds the runtime libc pair.
Its self-probe must pass before target launch; unavailable APIs remain a failure.
Process-boundary controls run on Android too, including timeout, cancellation,
concurrent ownership and forced missing-binding cases. This adds no permissions
or PID-only signaling fallback. Full MCP validation uses discovery across all
test modules, not only `test_nolqu_mcp.py`.

Native stdio servers explicitly inherit Termux's standard
`$PREFIX/lib/libtermux-exec.so` preload through their configured environment.
The MCP SDK's default environment omits it; unchanged `#!/usr/bin/env bash`
project commands otherwise fail before launch on Android. This is native
Termux command dispatch, outside the compiler's semantic bootstrap path.
Already-running MCP processes need restarting to use new configuration/code.

The wide-branch inspection test uses native `ndisasm` from NASM on Android.
Termux's default LLVM `objdump` lacks GNU raw-binary options, and its native
GNU binutils package supports ARM/AArch64 rather than x86. Other Linux hosts
keep the existing GNU `objdump` command. Both paths decode real instruction
boundaries and check the encoded jump bytes against the original artifact;
an `E9` byte inside an immediate must not count as a branch. Disassembly is
read incrementally through a pipe under a 60-second deadline, with owned-process
kill/wait on failure. NASM here
is a host inspection dependency, never a canonical bootstrap compiler stage.

Android controls AB01–AB12 cover independent copies, malformed/partial bundles,
pin and path failures, host classification, exact compiler behavior, unchecked
pyc rejection, rename-failure reporting, and a real adapter exceeding 8 MiB.
Focused controls complement the full main/MCP/assurance gates; they do not
replace them. See the [session report](../project/VALIDATION.md)
for actual run results and remaining blockers.
