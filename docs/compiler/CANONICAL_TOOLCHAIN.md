# Canonical Toolchain Access

Current metadata (2026-10-27): `1.0.0-alpha.1`, channel `dev`, by maintainer
request for `NolQuDev/NolQu-L`. Older version strings in checkpoint evidence
below describe those historical runs; no release or bootstrap promotion occurs.

The experimental C0.32 frontend/backend can be selected through the existing
`nqlc`, `nql`, installed commands and MCP tools. Default source behavior remains
`nasm`/Reference Compiler R0. This connects implemented components to public
commands; Full Compiler, self-hosting and Verified status remain false.
The native argv/syscall extension has scoped/generation evidence and passing
final main/MCP/installed combined-proof execution gates. An earlier unexplained
comparison-backend SIGKILL remains OPEN; stable/security readiness is PARTIAL.
The completed C0.31 access checkpoint below remains historical evidence.

## Compile, Check And Run

From a checkout, using the unchanged stream example:

```bash
./nqlc --backend canonical examples/canonical/checksum.nql -o /tmp/nql-checksum
printf abc | /tmp/nql-checksum                  # 43 followed by newline
./nqlc --backend canonical --check examples/canonical/checksum.nql
printf abc | ./nqlc --backend canonical --run examples/canonical/checksum.nql
```

`examples/canonical/checksum.nql` reads stdin in 256-byte chunks, sums unsigned
bytes modulo 251, and writes a decimal checksum plus newline. It uses the bounded
runtime arena and stream intrinsics. Empty input prints `0`; input need not fit
in memory. Errors preserve native diagnostics/status; this is not a filesystem,
networking or general standard-library example.

The output is static x86_64 Linux ELF64 with syscall-only runtime and a
nonexecutable stack. On ARM Linux use `qemu-x86_64 /tmp/nql-checksum`; the public
driver selects QEMU for its own compile/run component execution. `readelf -h -l
-d /tmp/nql-checksum` inspects the actual output. No host assembler, linker,
LLVM or Python compiler supplies the canonical artifact.

Always supply `-o` for a compile-only public invocation. A single source without
output/check/inspection mode retains the public CLI's implicit compile-and-run
behavior. Explicit `--run` without `-o` uses disposable output; with `-o` it
keeps the executable. Arguments after `--` are runtime arguments. `--check`
performs frontend and backend semantic compilation to temporary output without
executing or publishing the program. Failed compilation preserves an old output
and its mode. Checked arithmetic/bounds faults exit 70; runtime I/O/resource
faults exit 74, with source-located C0 diagnostics.

## Native Arguments And Files

[`native_cat.nql`](../../examples/canonical/native_cat.nql) is a real standalone
file/stdin reader using native argv and raw openat/read/write/close:

```bash
./nqlc --backend canonical --check examples/canonical/native_cat.nql
./nqlc --backend canonical examples/canonical/native_cat.nql -o /tmp/nql-native-cat
printf 'input\n' | ./nqlc --backend canonical --run examples/canonical/native_cat.nql
./nqlc --backend canonical --run examples/canonical/native_cat.nql -- -- 'input file' -
```

The last invocation copies a literal filename then stdin. The first `--` belongs
to `nqlc`; only an initial utility operand `--` is consumed. Other paths are
literal, including leading dashes, spaces and non-UTF8 bytes; `-` denotes stdin.
The source explicitly retries read/write EINTR, advances partial writes and
closes each acquired fd once. It stops on the first error without rewriting
input files. Paths use a fixed 4096-byte copy capacity including NUL, and data
streams through a 32768-byte buffer; file length need not fit the arena.

Use `qemu-x86_64 /tmp/nql-native-cat ...` for the compiled artifact on ARM.
No new command alias or native CLI/MCP replacement is installed. The
[example guide](../../examples/canonical/README.md) records statuses and limits;
[NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md) defines the experimental
unsafe boundary, raw ABI and independent source/AST checks. An invariant
comment and checked arena pointer do not establish later kernel/lifetime safety.

## Supported Subset And Host Requirements

Canonical input is one `.nql` compilation unit targeting `x86_64-linux`.
It supports signed i64 values, checked arithmetic, comparisons, lexical bindings,
assignment, branches/loops, named functions with at most six arguments, bounded
recursion and `byte_load`, `byte_store`, `input_read`, `output_write`, `error_write`.
It also supports `arg_count()` and checked `arg_copy(index,offset,capacity)`.
`byte_address(offset,count)` and `syscall6(number,frame_offset)` require an
owning lexical `unsafe` block whose first comment carries a nonempty `safety:`
invariant. `syscall6` consumes six little-endian words from a 48-byte arena span,
loads rdi/rsi/rdx/r10/r8/r9 and returns raw rax without retry/errno conversion.
The existing R0 `func`/print/module language has broader compatibility coverage;
selecting canonical does not translate that language or fall back to R0.

Current bounds are 262144 source bytes, 65536 tokens and 65536 AST nodes, 64
nested control bodies, 64 active function frames and 4096 bytes/512 i64 slots per
frame. The ELF cap is 8388608 bytes. Default byte storage is 65536 bytes.
`--compiler-profile` explicitly selects the existing 16777216-byte RW/NX arena;
it is never inferred from source length. This mapped bound is not measured RSS.
The 80300/199908-byte current compiler sources fit the unchanged capacity;
historical 8 KiB/u16 limits no longer describe it. New native sources select
NQAF/6 dialect5; legacy sources retain /1..5, and the complete compiler sources
themselves still use /5 dialect4/profile1. See
[CAPACITY.md](../../bootstrap/compiler/c0/CAPACITY.md) for measured identities
and separate C0.31/C0.32 component-generation provenance. Arg-count alone
allocates no byte arena; copy/address/frame operations use the selected profile.

General types, modules/multiple units, a general heap allocator, FFI, inline assembly and
the full language/compiler are not implemented by this subset. Canonical mode
rejects assembly/object/IR/AST emission, debug generation, `-O1`, warning-policy
and pedantic controls, saved intermediates, non-text diagnostics, nondefault
max-error configuration and parallel compilation. `-O0`, response files, paths
with spaces, verbose/quiet/time and dry-run are supported by the public driver.
Unsupported options fail without silently selecting another backend.

Public CLI orchestration needs Bash and GNU coreutils, plus `qemu-x86_64` on
ARM Linux. Running with terminal stdin additionally needs util-linux `setsid`;
compile/check and piped execution do not. MCP additionally needs Python, the MCP
SDK, Linux procfs, subreaper support and pidfds for its reviewed process
supervisor. These host processes launch/check real compiler bytes; they do not
supply compiler semantics or self-hosting evidence.

## Projects And Cache Cost

With this checkout's directory on PATH:

```bash
nql init app --backend canonical
cd app
nql check
nql build
nql run
nql test
```

Initialization creates a C0-compatible `src/main.nql`, an independent passing
`tests/smoke.nql`, and `[build] backend = "canonical"` in `nql.toml`. Omitted
project backend honors that manifest; an absent setting defaults to `nasm`.
Explicit `--backend nasm|canonical` overrides it for one command. Profiles are
never persisted by initialization: request `--compiler-profile` separately on
each build/run/test/check that needs it. The profile is canonical-only. Checking
does not run a profile-only program, so it can pass even if that program would
exceed the default runtime arena during execution.

Build checks backend/profile, source/manifest, driver/component/pin bytes and the
cached executable's bytes/mode before accepting a cache hit. Cache writes are
advisory. Canonical `run` deliberately recompiles through `nqlc --run` on every
invocation, including after a cached build. It pays real frontend/backend
compilation and output publication cost before executing; build caching does
not make canonical run incremental. Independent test programs compile/run
separately; multiple project source units are rejected rather than concatenated.

## Installation

```bash
PREFIX=/tmp/nql-canonical ./install.sh --canonical-only
cd /tmp
/tmp/nql-canonical/bin/nql init app --backend canonical
cd app
/tmp/nql-canonical/bin/nql build
/tmp/nql-canonical/bin/nql run
```

Canonical-only installation copies the pinned bootstrap assets, private helper,
commands and metadata without building/requiring R0, NASM, a linker or Python.
Normal `./install.sh` installs the combined R0/canonical toolchain and retains
R0 build requirements. Commands still require explicit canonical selection for
direct sources; installation changes no default. `DESTDIR` staging is supported.
Both forms install only the inward aliases `nolqul -> nql` and `nolqulc -> nqlc`.
Relocated commands locate assets relative to their installed tree.

## MCP

Configure `NOLQU_ROOT` to the repository/project root and start
`tools/nolqu_mcp.py` with the configured MCP interpreter. Direct compile source,
response-file and output paths are validated inside that root. For a project,
`nql`/`nqlc` must be available at the
configured root as in the repository (symlinks to installed commands also work).
The server works from an unrelated cwd.

Use existing tools with optional inputs:

```text
compile_nql(source_file="examples/canonical/checksum.nql",
            output_file="checksum", backend="canonical", compiler_profile=False)
nql_init(project_name="app", backend="canonical")
nql_build(compiler_profile=True)
nql_run(compiler_profile=True)
nql_test(compiler_profile=True)
nql_check(compiler_profile=True)
```

Project calls start at the configured root and delegate project discovery to
`nql`, which searches ancestor directories for `nql.toml`. Configure the actual
project root and use trusted project configuration; reconnect with the child
project root after initialization. Manifest-derived project outputs are not
individually validated through MCP's direct-compile path checker. These local
tools do not provide an OS filesystem/network sandbox or a compile-only grant:
BUILD also covers explicit run/test operations. Omitted backend forwards no override,
so the manifest applies. Only an explicitly true profile adds
`--compiler-profile`; `nql_init` has no profile input. Invalid backend/quoting
returns structured errors before process execution. Existing required fields,
120 tool names, eight resources and five prompts remain; only optional inputs
are added to six tools.

Ordinary `compile_nql` supplies `-o` even when `output_file` is omitted, using
`.nolqu-mcp/build/<source-stem>` under the root. This prevents implicit execution
and tool-name collisions for inputs such as `nqlc.nql`. Redirected default output
directories and source/tool/component aliases are rejected. Named outputs keep
their requested paths. Explicit `flags="--run -- 'one two' @literal"` still
requests execution, with the source before `--` and the runtime tail preserved
literally. Checking/IR retain stdout/no-publication contracts;
canonical unsupported modes still fail. Only successful observed output
publication is listed in `artifacts`; failures never claim preserved old files.
MCP flag response files use the CLI's single-level, one-argument-per-line format
and must stay inside the root; nested response references are rejected clearly.
Legacy `compile_file` and pipeline `full` also compile without implicit execution,
and keep their string return schemas. Pipeline `parse` means `--check`, not an
assertion that checking is parse-only. MCP commands get EOF by default, preserving
protocol stdin; explicit input is handled by the existing executor.

## Verification Scope

The MCP regression module includes unit forwarding/default/validation/output tests
and fresh SDK stdio tests that compile, inspect and execute actual C0 ELF from
an unrelated cwd. They exercise the unchanged checksum example, preserved old
outputs on failure, unsupported flags/missing components, runtime errors and a
program accessing byte offset 65536 that requires the explicit compiler profile.
Fresh SDK regressions also execute explicit run with literal arguments and
compile `nqlc.nql` with omitted output while preserving public tool bytes/modes.
Unit boundary doubles are not compilation evidence.

```bash
.venv-mcp/bin/python -B -m unittest discover -s tests/mcp -p test_canonical_toolchain.py -v
.venv-mcp/bin/python -B -m unittest discover -s tests/mcp -v
```

## Verified access checkpoint — 2026-10-24

This section describes the completed C0.31 access milestone and its exact old
source/artifact identities. It is not a full-suite result for changed C0.32
inputs. Current measured execution evidence and open assurance limits are below.

The complete main regression passed 1078 PASS markers: all 1076 baseline markers
remain, with one marker each for the complete 33-method CLI and 30-method project
modules. The latter includes actual canonical-only installation, physical
relocation, unrelated-cwd use and host-compiler-denial checks. The complete final
MCP suite passed 112 methods with zero skips; all 46 original methods remain.
`make release-check` passed all nine checks. Fresh stdio discovery preserves
120 tools, eight resources, five prompts and all old input/return schemas; only
the eleven documented optional backend/profile fields are added.

The main run preceded a two-file MCP artifact/audit repair. Its compiler,
CLI/project/install inputs remained identical, so independent review accepted
retaining that complete main result by dependency equivalence. It is not
represented as a post-fix rerun. The entire 112-method MCP suite, fresh protocol
comparison and release checks ran after the repair. An earlier MCP invocation
with auditing disabled failed three audit-dependent tests; the unchanged tests
passed with audit enabled, followed by the complete passing final suite. Keep
`NOLQU_MCP_AUDIT=1` when running the audit regression tests.

Public `nqlc --backend canonical --compiler-profile` compiled both complete
current compiler sources from an unrelated cwd. The resulting frontend
(6349683 bytes, SHA-256
`e0c698ab1ad259bb0441beddfafad90e42c75c16df819e21c41c76c55fd9c2cd`)
and backend (6445930 bytes, SHA-256
`72ed5667796fde9503101201418d6b8eaa2b89b6094979915ccdc83f7b704373`)
match the actual retained C0.31 component artifacts byte for byte. Five
independent checksum cases cover empty input, text, all byte values, multiple
chunks and a NUL boundary. Target execution on this aarch64 host uses QEMU.

A fresh combined C0 MCP probe passes frontend/backend, capacity, compiler-profile
and component-generation gates with unchanged input identities and completed
owned-process/temporary cleanup. All seven bootstrap artifact hashes match
before and after. This adds no compiler semantics or bootstrap stage and does
not promote Full Compiler, self-hosting or Verified. `VERSION=1.0.2a1` and
`CHANNEL=dev` remain unchanged; passing release checks is not a public release.

LLVM remains legacy compatibility infrastructure. Python MCP/test orchestration
and shell CLI orchestration have not been migrated away. The target remains a
full NolQu-L toolchain without Python or LLVM; wrapping host implementations
would not constitute that migration. The canonical compiler already emits ELF
directly without Python/LLVM source semantics.

## C0.32 Native Checkpoint — 2026-10-25

The initial pre-formatter generation/integrity module passed six methods in 648.759s, with
722 stages, 275 checks, 475 artifacts, six comparisons and 41 named oracle methods
on each B/C pair, zero skips. Both complete sources also compile through public
`nqlc --backend canonical --compiler-profile` into the measured new B/C bytes
in [CAPACITY.md](../../bootstrap/compiler/c0/CAPACITY.md). These are actual
artifact comparisons, not a claim that A==B or the Full Compiler is self-hosted.

Four new public CLI/project methods and canonical-only physical relocation
passed their scoped tests, including literal binary argv and invalid-invariant
cache rejection. Pre-formatter execution gates passed: main 1079 PASS markers (all
1078 baseline retained), 124 MCP methods (all 112 baseline retained), nine
release checks, unchanged protocol schemas and installed combined proof with
722 stages/275 checks plus 16 retained native evidence files. Source review
approved the coherent installed set. The earlier unexplained comparison-backend
SIGKILL remains OPEN; these local passes do not qualify stable/security release. Combined R0/canonical relocation passed a scoped rerun (one method,
15.024s) after the normal `make compiler` prerequisite, without a product change.
The first isolated attempt lacked prebuilt R0; the unchanged legacy installer
fallback fails NASM include resolution from a foreign cwd in that situation.
This existing limitation is not fixed by C0.32. Canonical-only relocation passed
without host compilers. See the [session report](../project/C032_SESSION_REPORT.md)
and [supplemental assurance](../../tests/security/README.md) for exact scope and gaps.

The intended six fresh proof flags include existing capacity/profile/generation
plus unsafe blocks, process arguments and syscall ABI. They must fail closed on
missing/stale/partial proof; metadata or these docs cannot enable them. Public
VERSION1.0.2a1/CHANNELdev, default R0/NASM and the remaining shell/Python/legacy
dependencies are unchanged.

The current selected backend is `b169f9ee8890d306c080f299980c352bbabc5518052355dd0148a7878b9f51b1`,
after the four-immediate C0R-008/009 diagnostic formatter repair. Its full-source
backend B==C hash is `c789a3442691dd4f51f51ecb594265ff7b106a45313b8f6e91c7ec233bd29f85`.
The1079-marker and648.759s results above remain the original pre-formatter
checkpoint. A fresh post-formatter baseline passed1079; the host evidence revision
then passed1080 markers, retaining every baseline label. Fresh MCP124,
installed combined proof722/275 and594 bounded assurance invocations bind that
revision. The [experimental host observer](NATIVE_TEST_EVIDENCE.md) retains exact
available bytes/PID observations without changing compiler source/seed/pins.
See the [reliability report](../project/C032_RELIABILITY_REPORT.md). The original
SIGKILL cause stays OPEN and no stable/security promotion follows.
