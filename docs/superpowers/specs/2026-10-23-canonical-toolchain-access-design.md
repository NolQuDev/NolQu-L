# Canonical Toolchain Access

Status: selected for implementation under the user's delegated substantial-development directive. Experimental, additive toolchain work; not a Full Compiler or release promotion.

## Authority And Baseline

All four requested authorities are available. The v10 DOCX is stored under its URL-encoded filename. Exact DOCX comparison shows that v10 adds the Assembly-Level target contract and strengthens Pillar 3; the bootstrap, safety and CLI contracts remain shared. Both complete masters were independently reconciled. Their October C0.31 installation checkpoints supersede older bounded-milestone snapshots. Concrete new type/module/ISA syntax is not specified and will not be invented by this work.

C0.31 already compiles its complete frontend/backend sources through A/B/C with B/C identity, but public `nqlc` unconditionally locates R0 and public `nql` projects generate R0 syntax. `install.sh` also requires R0/NASM and installs no canonical component tree. Thus a user cannot select the verified machine-built compiler through the normal CLI/project/install workflow. The existing structured MCP compile tool can also run a source when no output is supplied because the public CLI's implicit run mode is not suppressed.

The fresh baseline runs against the unchanged isolated worktree; implementation is staged in a source-identical scratch copy until baseline completion. The original dirty main checkout is read-only. Preserve all baseline test names/multiplicities and record actual results.

## Decision And Alternatives

Selected: explicit `--backend canonical` access through existing commands, keeping the default `nasm`/R0 behavior unchanged. Reuse the pinned `compile-source.sh` and actual C0.31 seeds. This removes the user-facing toolchain barrier without changing grammar or dropping existing programs.

Replacing the default with C0 immediately is rejected: R0's `func`/print/module language and C0's `fn`/i64/byte-stream language do not have feature parity. Adding a second public compiler command is rejected: it would multiply names instead of connecting the implemented compiler. Broad type/module/Full Compiler work remains a later independently specified compiler milestone.

Classification: substantial cross-subsystem experimental toolchain development, high integration risk. Public additions are opt-in and compatible; no public version/channel change is made in this development session.

## Public CLI Contract

- `nqlc --backend canonical input.nql -o output` compiles with actual pinned C0 frontend/backend and publishes through the unchanged canonical wrapper. `nolqulc` is the inward alias.
- `--check` performs both syntax and semantic compilation to temporary output, never runs the program and leaves no executable. This is not merely parse-only checking.
- `--run` compiles then executes, preserves stdin/stdout/stderr, exit status and arguments following `--`, and removes temporary output when no `-o` was given. Existing implicit-run behavior with a single source and no explicit output remains consistent across backends.
- `--compiler-profile` is canonical-only, explicitly selecting the existing 16 MiB RW/NX profile. Default programs retain 64 KiB. No source-size inference or default change.
- Support response files, paths with spaces, verbose/quiet/time and dry-run behavior. Dry-run invokes no compiler or runtime. Only `.nql`, one compilation unit and `x86_64-linux` are supported by this backend.
- Canonical unsupported features must fail before compilation/publication: assembly/object/IR/AST dump, debug generation, `-O1`, warning-policy/pedantic controls, `--save-temps`, non-text diagnostic format, nondefault maximum-error configuration and parallel jobs. `-O0` may identify the existing unoptimized pipeline. Do not claim unsupported switches work.
- No fallback to R0, NASM, a host linker, LLVM or Python compiler/source transformation. Valid text-mode canonical compile/check/run must work with those programs replaced by failing stubs on PATH. Bash/coreutils remain explicit orchestration dependencies; QEMU is required on non-x86_64 hosts. Canonical program execution with terminal stdin also explicitly requires Linux util-linux `setsid` to isolate the owned runtime session without transferring the caller's terminal foreground group. This host orchestration utility supplies no compiler/source semantics; compile/check and piped execution do not require it. Missing terminal-run support must fail clearly before executing the program. Terminal input, foreground preservation/restoration, driver-PID signals and terminal Ctrl-C must be tested with an actual controlling PTY.
- Native C0 diagnostics retain code/line/column and failure status, with actual source-file context supplied by the public driver. Checked runtime failures retain 70/74. No broad Safety, native-fault or leak-freedom claim.
- Trappable signals HUP/INT/TERM must terminate/reap owned children and remove owned temporary files. No unrelated process killing. Failed compilation preserves an existing output and mode; source/seed/manifest/script aliases remain protected by the existing wrapper.

## Project And Installation Contract

- `nql init app --backend canonical` creates valid C0 source, a real passing test and `[build] backend = "canonical"` in `nql.toml`. The existing default template stays R0-compatible.
- Project `build`, `run`, `test`, `check` accept explicit backend overrides and otherwise honor `[build] backend`; absent configuration retains `nasm`. `--compiler-profile` is explicit and participates in cache identity. Use the same inward aliases.
- Never concatenate multiple C0 source files or pretend modules exist. Reject unsupported multi-unit canonical projects clearly; independent test programs remain supported, including nested paths.
- Cache keys distinguish backend/profile, source/manifest and actual relevant driver/component/pin bytes. A hit also checks the built executable identity; changed or missing tools, stale pins and modified binaries cannot reuse a stale success. Cache bookkeeping is advisory: verified compilation must not be turned into failure solely because a cache cannot be written.
- `install.sh` continues to install the normal combined toolchain by default, now including canonical assets. `install.sh --canonical-only` installs a usable canonical workflow without building or requiring R0/NASM/linker/Python. Direct commands still explicitly select the canonical backend; there is no silent fallback/default rewrite. Unknown install arguments fail.
- Install into a temporary test PREFIX/DESTDIR only. Include the complete unchanged bootstrap tree needed by the canonical wrapper and its provenance, the private canonical driver helper, VERSION, both primary executables and only their two inward aliases. Uninstall removes the installed tree. Never create removed `nq/nqc/nolqu/nolquc` names.

## MCP Contract

- A bounded read-only audit of the existing `_run_result` proved two pre-existing process-boundary bugs: its timed-out parent left a live child, and a subprocess with no supplied stdin consumed a protocol fixture from the MCP stream. The probe explicitly terminated/reaped its test child. Repair these foundations before new MCP access: no-input commands receive EOF/DEVNULL; explicitly supplied stdin remains supported; timeout/interruption terminates owned processes and reaps the direct child, without killing unrelated work. Preserve result/error/audit schemas and actual status/timing semantics. No compiler semantics are supplied by this Python process supervisor.
- Preserve all existing tool names, resources/prompts, capability boundaries, default arguments and required fields. Add optional backend selection to `compile_nql`, `nql_init/build/run/test/check`; add optional compiler profile to `compile_nql` and project `nql_build/run/test/check`. Profile remains false by default and is forwarded only on an explicit true request; `nql_init` does not persist or infer it.
- Existing no-selection behavior remains R0/project-config compatible. Invalid backend values produce structured errors before subprocess creation.
- A compile tool's ordinary default/full mode must request an explicit output so compilation cannot accidentally run a program. An explicitly supplied run flag remains an explicit request. Describe parse/check behavior accurately. Artifact results identify actual successfully produced files; a failed compile must not label a preserved old file as a newly built artifact.
- Verify real canonical compile through a fresh SDK stdio client rooted at this installation from an unrelated cwd. Negative tests cover malformed source, unsupported flags, missing components and no false Full Compiler/self-hosting flags. Unit mocks are not compilation evidence.

## Acceptance And Rollback

Complete only when public compile/check/run, canonical project lifecycle, canonical-only relocated install and fresh MCP compilation all work with actual C0 output. Compare emitted ELF bytes to the existing direct wrapper, inspect ELF static/RX/RW/NX properties, and test real execution/output/status. All existing main/MCP/release tests remain green; all seven bootstrap seed/pin pairs and compiler source bytes remain unchanged. No invented performance metric or capability flag.

All changed files have a pre-edit snapshot, explicit ownership and reviewable diff. Rollback restores this additive CLI/project/install/MCP/doc set; it does not touch C0.31 source/seeds/pins. No commit, main edit, merge, push or public release is authorized by this plan. Final report distinguishes this access milestone from full language/compiler maturity.
