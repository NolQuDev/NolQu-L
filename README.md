# NolQu-L 1.0.0-alpha.1

**NolQu-L** is the short form of **NolQu-Lang**. The **L** already means
**Language**; neither name takes an additional Language suffix.

NolQu-L is an experimental systems programming language whose canonical
bootstrap starts from auditable x86_64 machine bytes. The compiler currently
implemented in `src/*.asm` is Reference Compiler R0: it remains the tested
compatibility compiler, but it is not Stage 0 and is not evidence of
self-hosting.

The [Nine Pillars of NolQu-L](docs/language/DESIGN_PRINCIPLES.md) define the
language's principles: simplicity, readability, visible machine costs,
explicit safety and tested evolution.

The canonical direction is independent of LLVM, Python, and host-language
compilers:

```text
Machine-Level Foundation -> Stage 0 -> Bootstrap Compiler -> Core Compiler
-> Full Compiler (`nqlc`) -> Self-Hosting `nqlc` -> Verified `nqlc`
```

Version `1.0.0-alpha.1` is the current development alpha label, selected for the
NolQu-L repository on 2026-10-27. Earlier version labels remain historical;
this naming reset is not a semantic-version upgrade from those labels. Current
implemented capabilities include:

- small command-line programs
- the tested Reference Compiler R0 and its NASM output path
- the verified Machine-Level Foundation and symbolic Stage 0 seeds
- frozen LLVM/Python compatibility paths retained for regression coverage
- canonical CLI entrypoints via `./nql` and `./nqlc`

## Status

The Machine-Level Foundation, Stage 0, Bootstrap Compiler B0, and Core
Compiler emitter through C0.25 are implemented and hash-verified for x86_64 Linux.
The B0-built C0.32 frontend/backend additionally compile structured i64 programs
with lexical scopes, loops, named functions, mutable parameters and bounded
native recursion directly to ELF, with checked byte memory and Linux stream I/O.
Their installed capacity is 262144 source bytes and 65536 tokens/nodes, with
versioned NQAF/5 storage and additive NQAF/6 dialect5 for native operations.
Both complete compiler sources build through
B0 -> A -> B -> C, with byte-identical B/C component pairs. Default program
byte storage remains 65536 bytes; the explicit compiler profile maps 16 MiB RW/NX.
See [CAPACITY.md](bootstrap/compiler/c0/CAPACITY.md) for source/artifact identities,
evidence and the completed pre/postinstallation checks, and
[RUNTIME_IO.md](bootstrap/compiler/c0/RUNTIME_IO.md) for the runtime contract.
C0.32 adds lexical unsafe blocks with invariant comments, native argv copying,
checked raw arena addresses and Linux x86_64 syscalls. The actual
[native file reader](examples/canonical/README.md) handles literal filenames,
binary streams and explicit descriptor/I/O rules in NolQu-L source. Independent
backend checks bind raw-call permission to both AST ownership and source scope;
this is bounded checking, not full Safety or ownership/lifetime verification.
Scoped tests, complete-source generations and final main/MCP/probe execution
gates pass. An earlier unexplained comparison-backend SIGKILL remains OPEN;
stable/security readiness is PARTIAL. See
[NATIVE_OS.md](bootstrap/compiler/c0/NATIVE_OS.md) for the exact current boundary.
The reliability continuation closes the post-formatter full-main gap: the
unchanged baseline passed 1079 markers, then the observed host-helper revision
passed 1080, retaining every baseline label. MCP 124, fresh combined proof,
594 assurance invocations and 9 release checks pass on the new bound inputs.
The experimental [host evidence option](docs/compiler/NATIVE_TEST_EVIDENCE.md)
retains PID/input/executable/streams through temporary cleanup. See the public
[validation status](docs/project/VALIDATION.md) for current qualification limits
and the historical signal, whose cause remains OPEN. Detailed session records
remain internal.
The Full Compiler and self-hosting generations are not implemented. Reference
Compiler R0 remains the default `nasm` compatibility backend. Public `nqlc`
and `nql` also expose the experimental C0.32 subset through explicit
`--backend canonical`; this access does not promote Full Compiler, self-hosting
or Verified status. See the [canonical toolchain guide](docs/compiler/CANONICAL_TOOLCHAIN.md)
for supported syntax, project/install/MCP workflows and remaining integration gates.

Current metadata:

- version: `1.0.0-alpha.1`
- channel: `dev`

## Requirements

Canonical seed execution:

- x86_64 Linux, or `qemu-x86_64` on another Linux architecture

Canonical seed reconstruction and verification on the development host:

- Bash
- `sha256sum`
- standard utilities used by tests: `cmp`, `grep`, `awk`, and `readelf`

Canonical public compile/check/run uses Bash and GNU coreutils with the pinned
C0 components; it needs no host assembler, linker, LLVM or Python compiler.
On ARM Linux it also uses `qemu-x86_64`. Running with terminal stdin requires
util-linux `setsid`; compile/check and piped runs do not. The optional MCP server
uses Python and its MCP SDK plus Linux procfs, subreaper and pidfd process
orchestration; Python is not a compiler stage.

Reference Compiler R0 and legacy compatibility tests additionally use:

- `nasm`
- `x86_64-linux-gnu-ld` or compatible `ld`
- `clang`
- `llvm-as`
- `qemu-x86_64` when running the NASM backend on non-`x86_64` hosts

The additional tools are not dependencies of the canonical bootstrap chain.

Verify the implemented canonical bootstrap stages:

```bash
make machine-foundation
make stage0
make stage0-test
make bootstrap-test
```

## Quick Start

Compile and run the checked byte/stream subset with the existing example:

```bash
./nqlc --backend canonical examples/canonical/checksum.nql -o /tmp/nql-checksum
printf abc | /tmp/nql-checksum       # prints 43
./nqlc --backend canonical --check examples/canonical/checksum.nql
```

The emitted ELF targets x86_64 Linux; use `qemu-x86_64 /tmp/nql-checksum` on
ARM Linux. The subset currently supports one `.nql` unit and signed i64 values,
with 262144 source bytes and 65536 tokens/nodes. Default byte storage is 64 KiB;
`--compiler-profile` explicitly selects 16 MiB. For a canonical project use
`./nql init app --backend canonical`, then `nql build/run/test/check` from the
project with `nql` on PATH. Build supplies validated caching; canonical `run`
recompiles through `nqlc --run` every time, including after a cached build.

Compile and run the new native file/stdin reader with explicit canonical mode:

```bash
./nqlc --backend canonical examples/canonical/native_cat.nql -o /tmp/nql-native-cat
printf 'input\n' | ./nqlc --backend canonical --run examples/canonical/native_cat.nql
./nqlc --backend canonical --run examples/canonical/native_cat.nql -- -- 'input file' -
```

The final example copies a literal file then stdin. The [canonical examples
guide](examples/canonical/README.md) explains both `--` boundaries, the fixed
4096-byte argument capacity including NUL, statuses and QEMU invocation. No
extra command alias is installed. Python MCP/tests, shell drivers and legacy
LLVM/NASM remain; migrating the complete toolchain to NolQu-L is unfinished.

Build or rebuild the compiler:

```bash
./nql --build-compiler
# or
make compiler
```

Compile a NolQu-L program with Reference Compiler R0:

```bash
./nql hello.nql
# or
make check EXAMPLE=examples/core/hello.nq
```

That writes `build/output.asm` with the default NASM backend.

Build the generated program:

```bash
nasm -f elf64 build/output.asm -o build/output.o
x86_64-linux-gnu-ld build/output.o -o build/output
```

Run it:

```bash
./build/output
```

On non-`x86_64` hosts:

```bash
qemu-x86_64 ./build/output
```

## CLI

`nql` is the canonical project manager/run executable and `nqlc` is the
canonical direct compiler executable. Their only command aliases are
`nolqul -> nql` and `nolqulc -> nqlc`; there is no `nq`, `nqc`, `nolqu`, or
`nolquc` command. Legacy `.nq` source remains accepted only while the source
corpus and bootstrap contracts migrate to `.nql`.

### nql

```bash
./nql init app
cd app
../nql check
../nql build
../nql run -- arg1 arg2
../nql test
../nql clean
../nql version
```

`nql init` creates `nql.toml`, `src/main.nql`, and `.nql/`. The legacy direct
R0 inspection interface is still reachable through `nql <file.nql>` and its
inspection flags while the canonical Full Compiler is being built.

### nqlc

```bash
./nqlc hello.nql                        Compile to ./hello and run
./nqlc hello.nql -o app                 Select output path
./nqlc --check hello.nql                Check without output
./nqlc -S hello.nql -o hello.asm        Emit assembly
./nqlc -c hello.nql -o hello.o          Emit object
./nqlc --dump-ast hello.nql             Inspect source structure
./nqlc --dump-ir hello.nql              Inspect R0 IR
./nqlc --run hello.nql -- arg1 arg2     Compile and run
./nqlc --version
```

`--run` / `run` compiles and runs the resulting binary; the default R0 backend
assembles/links, while canonical C0 emits ELF directly. A single source without
an output or inspection/check mode also runs implicitly. Supply `-o` to compile
without running. `--check` / `check` exits without publishing an executable;
canonical checking includes backend semantic validation.
`--dump-tokens` prints the real compiler token stream and stops before parsing/codegen.
`--dump-ir` prints the real compiler IR after parsing/optimization and stops before codegen.
`--export-ir` saves Reference Compiler R0's textual IR for inspection and
legacy compatibility tooling.
`make ir-json` and `make ir-llvm` retain the historical IR-to-LLVM bridge; they
are not canonical bootstrap steps.
`--emit` renames the generated assembly output to a chosen path.
The legacy direct `nql` R0 route retains `--backend llvm` only for its frozen
compatibility subset. Public `nqlc` and project backend selection accept `nasm`
or `canonical`.

The authoritative direction is the machine foundation and canonical Stage 0
chain under `bootstrap/`. New architecture must not grow through LLVM or
Python.

## Makefile

```bash
make machine-foundation
make stage0
make stage0-test
make bootstrap-test
make canonical-native-test
make compiler
make run EXAMPLE=examples/core/hello.nq
make check EXAMPLE=examples/semantics/functions.nq
make dump-tokens EXAMPLE=examples/semantics/branching.nq
make dump-ir EXAMPLE=examples/semantics/functions.nq MODE=--release
make export-ir EXAMPLE=examples/semantics/functions.nq MODE=--release
make ir-json EXAMPLE=examples/semantics/functions.nq MODE=--release
make ir-llvm EXAMPLE=examples/core/hello.nq MODE=--release
make smoke
make examples
make llvm-smoke
make release-check
make show-version
make show-channel
make dev
make stable
make set-dev
make set-stable
make test
make clean
```

`EXAMPLE` selects a canonical `.nql` or legacy `.nq` file for `run`, `check`, `dump-tokens`, `dump-ir`, `export-ir`, and `ir-json`.
`MODE=--release` is the usual optional flag when you want optimizer-enabled output.
`BACKEND=nasm|llvm` selects the backend for `run`, `check`, `dump-tokens`, `dump-ir`, `export-ir`, and `ir-json`.
`make release-check` verifies that version, channel, wrapper output, and key docs stay aligned.

## Example

```txt
func fact(n) {
if n == 0 {
return 1
}
return n * fact(n - 1)
}

print fact(5)
```

Expected output after compiling and running generated `output`:

```txt
120
```

## Project Files

- [Architecture](docs/compiler/ARCHITECTURE.md): implemented stages, boundaries and current limitations
- [Branch roles](docs/project/BRANCHES.md): Main integration, Dev Alpha, and empty Stable reserved for RC/final
- `bootstrap/`: canonical machine foundation and future compiler stages
- `src/`: Reference Compiler R0 sources
- `nql`: canonical project manager and run executable (`nolqul -> nql`)
- `nqlc`: canonical direct compiler executable (`nolqulc -> nqlc`)
- [LICENSE](LICENSE): current project license notice
- `.github/`: issue and pull request templates for GitHub
- [docs/README.md](docs/README.md): docs landing page
- [language docs](docs/language): language surface, semantics, and design rules
- [compiler docs](docs/compiler): architecture, backends, IR, and testing
- [project docs](docs/project): roadmap, release workflow, commands, and repo structure
- [community docs](docs/community): governance, support, contribution, and policy
- [REPO_INDEX.md](docs/project/REPO_INDEX.md): full one-page index of documentation
- `tools/`: frozen legacy backend and inspection tooling
- [tools/README.md](tools/README.md): tooling index
- `examples/core/`: minimal starter programs
- `examples/semantics/`: language and semantic behavior examples
- `examples/llvm/`: LLVM bootstrap and bridge-oriented examples
- [examples/README.md](examples/README.md): examples index
- `tests/`: grouped bootstrap, R0 compiler, legacy LLVM/IR, meta, and shared test utilities
- [tests/README.md](tests/README.md): tests index
- `build/`: compiler and generated build artifacts
- [VERSION](VERSION): current project version
- [CHANNEL](CHANNEL): current release track

## Examples

```bash
./nql --run examples/core/hello.nq
./nql --run examples/core/arrays.nq
./nql --run --backend llvm examples/llvm/llvm_basic.nq
./nql --run --backend llvm examples/llvm/llvm_fact.nq
./nql --run --backend llvm examples/llvm/llvm_fact_local.nq
./nql --run --backend llvm examples/llvm/llvm_if.nq
./nql --run --backend llvm examples/llvm/llvm_func.nq
./nql --run --backend llvm examples/llvm/llvm_func_local.nq
./nql --run --backend llvm examples/llvm/llvm_while.nq
./nql --run examples/semantics/functions.nq
./nql --run examples/semantics/argument_patterns.nq
./nql --run examples/semantics/nested_argument_calls.nq
./nql --run examples/semantics/argument_order.nq
./nql --run examples/semantics/argument_stress.nq
./nql --run examples/semantics/zero_arg_calls.nq
./nql --run examples/semantics/array_argument_mutation.nq
./nql --run examples/semantics/loop_control_helpers.nq
./nql --run examples/semantics/recursive_array_flow.nq
./nql --run examples/semantics/branching.nq
./nql --dump-tokens examples/semantics/branching.nq
./nql --dump-ir examples/semantics/functions.nq --release
./nql --export-ir build/functions.ir examples/semantics/functions.nq --release
./nqlc --run tools/nql_ir_dump_parser.nql -- build/functions.ir build/functions.ir.json
python3 tools/nq_ir_json_to_llvm.py build/functions.ir.json build/functions.ir.ll
```

## Tests

Run the canonical checks and complete Reference Compiler R0 regression suite:

```bash
make test
```

## Notes

- The wrapper keeps generated artifacts in `build/` by default.
- The docs tree is now grouped by purpose under `docs/language`, `docs/compiler`, `docs/project`, and `docs/community`.
- Core language scope is intentionally smaller than the full set of parser experiments. See [CORE_LANGUAGE.md](docs/language/CORE_LANGUAGE.md) and [FEATURE_STATUS.md](docs/language/FEATURE_STATUS.md).
- For the shortest statement of current behavior, see [SEMANTICS.md](docs/language/SEMANTICS.md).
- The project is currently released under the MIT license: see [LICENSE](LICENSE).
- Naming and branding guidance lives in [TRADEMARK.md](docs/community/TRADEMARK.md).
- Contact addresses for the project are listed in [CONTACT.md](docs/community/CONTACT.md).
- Contributor workflow guidance lives in [CONTRIBUTING.md](docs/community/CONTRIBUTING.md), with conduct expectations in [CODE_OF_CONDUCT.md](docs/community/CODE_OF_CONDUCT.md).
- Support guidance lives in [SUPPORT.md](docs/community/SUPPORT.md), and project authority is summarized in [GOVERNANCE.md](docs/community/GOVERNANCE.md).
- Quick project answers live in [FAQ.md](docs/community/FAQ.md), and contribution/documentation style guidance lives in [STYLE_GUIDE.md](docs/community/STYLE_GUIDE.md).
- Host/toolchain expectations are summarized in [COMPATIBILITY.md](docs/project/COMPATIBILITY.md), and current distribution layout is described in [PACKAGING.md](docs/project/PACKAGING.md).
- Setup notes live in [INSTALL.md](docs/project/INSTALL.md), and backend roles are summarized in [BACKENDS.md](docs/compiler/BACKENDS.md).
- Repo layout is summarized in [PROJECT_STRUCTURE.md](docs/project/PROJECT_STRUCTURE.md), and the current test model is described in [TESTING.md](docs/compiler/TESTING.md).
- Command reference lives in [COMMANDS.md](docs/project/COMMANDS.md), and the current exported IR role is summarized in [IR.md](docs/compiler/IR.md).
- Tooling roles are summarized in [tools/README.md](tools/README.md).
- GitHub ownership and triage policy are summarized in [CODEOWNERS](.github/CODEOWNERS) and [LABELS.md](docs/project/LABELS.md).
- Shared vocabulary lives in [TERMINOLOGY.md](docs/language/TERMINOLOGY.md), and current design choices are summarized in [DECISIONS.md](docs/language/DECISIONS.md).
- Current limitations are summarized in [KNOWN_LIMITATIONS.md](docs/language/KNOWN_LIMITATIONS.md), and error behavior is summarized in [ERRORS.md](docs/language/ERRORS.md).
- A short project direction summary lives in [ROADMAP_SHORT.md](docs/project/ROADMAP_SHORT.md), and a current snapshot lives in [STATE_OF_PROJECT.md](docs/project/STATE_OF_PROJECT.md).
- A one-page docs map lives in [REPO_INDEX.md](docs/project/REPO_INDEX.md), and maintainer operations are summarized in [MAINTAINER_CHECKLIST.md](docs/project/MAINTAINER_CHECKLIST.md).
- Release-note drafting lives in [RELEASE_NOTES_TEMPLATE.md](docs/project/RELEASE_NOTES_TEMPLATE.md); the normative language principles are the [Nine Pillars of NolQu-L](docs/language/DESIGN_PRINCIPLES.md).
- Function calls use a simple stack-based calling convention.
- Function arguments are currently positional-only; there are no default, named, or variadic arguments yet.
- Return values are passed in `rax`.
- Local variables use `rbp`-relative stack slots.
- R0 locals remain function-scoped; canonical C0 implements lexical block scopes.
- `break` exits the current loop and `continue` advances to the next iteration; in `for`, that still includes the loop increment step.
- Function arguments are currently evaluated from left to right.
- `stable` is intended for public releases, while `dev` is the working line for alpha, beta, and rc versions.
- The LLVM backend and Python bridge are frozen compatibility surfaces, not
  canonical NolQu-L architecture.
- Stage 0 is implemented, but no canonical NolQu-L compiler is self-hosted;
  Reference Compiler R0 must not be described as self-hosted.
- Exact bootstrap status is tracked in `bootstrap/manifest.tsv`.
