# NolQu-L Toolchain Commands

The canonical toolchain exposes two executables and their long-name aliases:

- `nql`: project manager and build tool, similar to Cargo
- `nolqul -> nql`: formal long-name alias
- `nqlc`: direct compiler, similar to `rustc` or `gcc`
- `nolqulc -> nqlc`: formal long-name alias

There is no `nq`, `nqc`, `nolqu`, or `nolquc` command.

All user-facing diagnostics from these wrappers go to stderr. Program output
from `nql run` and emit output from compiler flags go to stdout.

These commands currently use Reference Compiler R0. They are not Stage 0 or a
self-hosted canonical compiler.

## Canonical Bootstrap

Reconstruct the Machine-Level Foundation, build Stage 0, and run canonical
bootstrap tests:

```bash
make machine-foundation
make stage0
make stage0-test
make bootstrap-test
```

Exact canonical stage status is recorded in `bootstrap/manifest.tsv`.

## Direct Compiler

Run one file directly, like `python script.py`:

```bash
nqlc hello.nql
nolqulc hello.nql
nqlc hello.nql -- arg1 arg2
```

This writes the default output binary (`hello.nql` -> `hello`), runs it, returns
the program exit code, and removes compiler temporary files.

Compile without running by setting an explicit output path:

```bash
nqlc hello.nql -o build/hello
nqlc -o build/hello hello.nql
```

Emit assembly or object output:

```bash
nqlc -S hello.nql
nqlc -c hello.nql
```

Check syntax without producing output:

```bash
nqlc --check hello.nql
nqlc --check -j 2 a.nql b.nql
```

The explicit `--run` spelling is also accepted when you want a temporary binary
that is removed after execution:

```bash
nqlc --run hello.nql
nolqulc --run hello.nql
nqlc --run hello.nql -- arg1 arg2
```

Use a response file, one flag per line:

```bash
nqlc @flags.txt hello.nql
```

Treat a leading dash as a filename:

```bash
nqlc -- -weird.nql
```

Generate dependency or IDE metadata:

```bash
nqlc -M hello.nql
nqlc --emit-ccdb hello.nql
```

Inspect compiler-facing structure and warnings:

```bash
nqlc --dump-ast hello.nql
nqlc -Wall --check hello.nql
nqlc -Wall -Werror --check hello.nql
nqlc -Wall -Werror --max-errors=1 --check hello.nql
nqlc -Wall -Wno-trailing-whitespace --check hello.nql
nqlc --pedantic --check hello.nql
```

Warnings currently include trailing whitespace, TODO/FIXME comments, missing
final newline, and pedantic style warnings such as long lines and tab
indentation. `--dump-ast` first validates the input with the frontend and only
prints a textual source-structure dump when the source checks cleanly.

Show versions:

```bash
nqlc --version
nolqulc --version
```

Each command preserves its invocation name: `nqlc <version>` or
`nolqulc <version>` followed by `(x86_64-linux)`.

## Project Manager

Create a project:

```bash
nql init
nql init myapp
```

Build, run, test, check, and clean:

```bash
nql build
nql run
nql run -- arg1 arg2
nql test
nql check
nql clean
```

Show toolchain versions:

```bash
nql version
nql --version
```

Project builds read `nql.toml`, compile `.nql` files under `src/`, and write the
binary to `.nql/build/<package-name>`. Build cache files live under `.nql/cache/`.
The cache includes source hashes, `nql.toml`, toolchain version, target, and
release/debug mode, so switching between `nql build` and `nql build --release`
rebuilds when needed.

Test binaries are written under `.nql/tests/` using each test file's relative
path, so files such as `tests/a/basic.nql` and `tests/b/basic.nql` do not collide.

## Global `nql` Flags

```bash
nql --release build
nql build --release
nql check --release
nql test --release
nql --target x86_64-linux build
nql build --target x86_64-linux
nql -v build
nql build -v
nql check -v
nql -q build
nql build -q
nql test -q
nql --color never build
nql build --color never
```

Only `x86_64-linux` is supported today.

## Install

Install into `/usr/local`:

```bash
make install
```

Install into a custom prefix:

```bash
NQL_HOME=/opt/nolqu ./install.sh
```

Uninstall:

```bash
make uninstall
NQL_HOME=/opt/nolqu ./install.sh --uninstall
```

The install step creates:

- `bin/nql`
- `bin/nolqul -> nql`
- `bin/nqlc`
- `bin/nolqulc -> nqlc`

## Direct Pipeline Adapter

The canonical `nql` command also exposes direct compiler inspection operations:

```bash
./nql file.nql
./nql --run file.nql
./nql --dump-tokens file.nql
./nql --dump-ir file.nql
```

New project workflows should prefer `nql build` / `nql run`, and direct
single-file compiler workflows should prefer `nqlc` or `nolqulc`.
