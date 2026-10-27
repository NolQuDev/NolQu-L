# Canonical Examples

These programs use the experimental C0 frontend/backend through explicit
`--backend canonical`. They target standalone Linux x86_64 ELF. Default public
compilation still selects R0/NASM; these sources are not translated to that
compatibility language. The [toolchain guide](../../docs/compiler/CANONICAL_TOOLCHAIN.md)
explains profiles, projects, installation and remaining host dependencies.

## Stream Checksum

[`checksum.nql`](checksum.nql) reads stdin in 256-byte chunks, sums bytes modulo
251 and prints a decimal result plus newline. Empty input prints `0`; `abc`
prints `43`. It uses checked byte memory and existing fixed stream operations.

```bash
./nqlc --backend canonical --check examples/canonical/checksum.nql
printf abc | ./nqlc --backend canonical --run examples/canonical/checksum.nql
```

## Native File Reader

[`native_cat.nql`](native_cat.nql) exercises C0.32 argv, checked pointer exposure,
explicit unsafe invariants and raw openat/read/write/close. Its compilation and
runtime semantics are in NolQu-L; it is not a host implementation or new command
alias. [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md) defines the exact
experimental contract and verification boundary.

From the repository root:

```bash
./nqlc --backend canonical --check examples/canonical/native_cat.nql
./nqlc --backend canonical examples/canonical/native_cat.nql -o /tmp/nql-native-cat
printf 'binary input\n' | ./nqlc --backend canonical --run examples/canonical/native_cat.nql
./nqlc --backend canonical --run examples/canonical/native_cat.nql -- -- 'input file' -
```

The last example copies the file named `input file`, then stdin. The first
`--` belongs to the public driver; the second is the utility's optional initial
delimiter. For a precompiled executable on Linux x86_64:

```bash
/tmp/nql-native-cat -- 'input file' -
```

On the aarch64 development host use `qemu-x86_64 /tmp/nql-native-cat -- 'input file' -`.
The public driver's `--run` selects the existing execution adapter itself.
Add `--compiler-profile` before the source to request the 16 MiB RW/NX arena;
the default 64 KiB arena already fits this program.

- No operands, or only the initial `--`, copies stdin.
- `-` denotes stdin; a filename literally `-` can be written `./-`.
- Only an initial `--` is consumed. A later `--` is a literal filename.
- All other operands are literal paths, including leading dashes, spaces and
  non-UTF8 bytes. The utility does no globbing, shell expansion or text decoding.
- Files are read in order, read-only. Binary bytes are preserved; the program
  stops at the first error, so earlier output may already have been written.

Arena intervals are explicit: syscall frame `[0,48)`, diagnostic bytes `[64,86)`,
NUL-terminated path `[128,4224)`, data buffer `[8192,40960)` (32768 bytes).
Argument capacity is 4096 including NUL: at most 4095 path bytes are copied.
A larger argument is the native `C0R-009` fatal error with exit 74, not a dynamic
allocation or truncated path. Negative frame values are packed as two's-complement
little-endian words by source `put_word`; this is not a new integer operator.

Source loops retry raw read/write EINTR and advance partial writes by the
returned count. Each acquired fd is closed exactly once, including fd0 if
openat returns it. A close error is reported without retry; raw syscalls do
not provide an automatic resource policy. Success returns 0. Recoverable open,
read, write or close failure returns 1 after `native_cat: I/O error` on stderr.
If writing that diagnostic fails, the existing stream runtime exits 74. Runtime
range/capacity failures retain their own diagnostics/status and rely on process
reclamation for any remaining raw resources.

Five native-program and thirty existing Guest tests passed in the retained
scoped run, including binary/literal argv, errors, actual fd0 ownership and
explicit synthetic I/O fault injection. Actual complete-source generations,
four new public methods and both installation modes also pass their scoped
checks (combined mode requires the normal legacy compiler build prerequisite).
Final main/MCP/installed combined-proof execution gates pass. An earlier
comparison-backend SIGKILL is unexplained, so stable/security readiness is
PARTIAL;
this example proves no general ownership/lifetime safety, full standard library,
Full Compiler or self-hosting.
