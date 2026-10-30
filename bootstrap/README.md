# NolQu-L Bootstrap

This directory is the canonical bootstrap root for NolQu-L. It is separate
from the existing compiler in `src/`, which remains Reference Compiler R0 and
the compatibility oracle while the canonical chain is built.

## Canonical Chain

```text
Machine-Level Foundation
-> Stage 0
-> NolQu-L Bootstrap Compiler
-> NolQu-L Core Compiler
-> Full NolQu-L Compiler
-> Self-Hosting nqlc
-> Verified nqlc
```

The Machine-Level Foundation, Stage 0, B0 Bootstrap Compiler, and C0 Core
Compiler through C0.25 plus the experimental C0.32 frontend/backend are implemented. A stage
is not marked implemented
until its artifacts and reproducible tests exist. C0.20 adds indirect byte
loading for terminating, byte-exact source traversal; C0.21 adds the matching
indirect byte store and proves source-table copying through runtime pointers.
C0.22 compiles a canonical `.nql` program that turns up to 16 runtime source
bytes into bounded `[kind, offset, length]` records. C0.23 classifies every
record as whitespace, identifier, decimal digit, or stable Core-0 punctuation
and rejects unmapped/non-ASCII input atomically. C0.24 elides whitespace and
coalesces contiguous identifier/integer runs while preserving one-byte
punctuation and a strict sixteen-token bound. C0.25 adds a C0-compiled parser
that validates arbitrary bounded primary/operator chains, preserves every
located lexical record, and emits one flat CST root with guaranteed progress.
It also widens C0's internal source-token tables to an exact 512-token bound.
C0.26 adds a B0-built source frontend with real precedence trees, lexical
keyword resolution, `let`/assignment/`return` and a checked `fn main()` envelope.
Its [NQAF/1 contract](compiler/c0/FRONTEND.md) separates parsing from semantic
resolution and codegen. C0.27 adds a separate B0-built
[AST backend](compiler/c0/BACKEND.md): validated NQAF, flat mutable i64 locals,
checked runtime arithmetic and deterministic standalone ELF. The experimental
`compiler/c0/x86_64-linux/compile-source.sh` joins both components atomically.
C0.28 extends both components with [structured control flow](compiler/c0/CONTROL_FLOW.md),
signed comparisons and lexical block scopes. NQAF/2 delimiters are validated
before direct relative-branch emission. C0.25 and bounded generations remain
byte-identical; scalar NQAF/1 output is preserved for the predecessor corpus.
C0.29 adds [functions and native calls](compiler/c0/FUNCTIONS.md): NQAF/3,
zero through six mutable parameters, forward/nested/recursive calls, exact names,
and separate function-local scopes. Calls use explicit aligned stack frames with
a 64-active-function bound. Predecessor NQAF/1 and NQAF/2 output is unchanged.
C0.30 adds checked byte/stream operations and call statements. C0.31 adds the
explicit compiler profile and wide source/AST capacity needed to compile both
complete compiler components through A -> B -> C with byte-identical B/C pairs.
The C0.31 reviewed seeds were installed and passed all final postinstallation checks in
[CAPACITY.md](compiler/c0/CAPACITY.md). This is not a Full Compiler or formal
self-hosting. R0/NASM remains the public default; `--backend canonical` selects
the experimental components through existing public commands.

C0.32 adds lexical `unsafe` invariants, native argc/argv, checked arena addresses
and raw Linux x86_64 syscalls, with independently checked NQAF/6 source/AST
permission. The actual native file-reader source and complete-source A/B/C
generations pass; new B/C artifacts are byte-identical. Final main/MCP/probe
execution gates also pass. An earlier comparison-backend SIGKILL remains OPEN,
so these results do not qualify stable/security promotion.
See [NATIVE_OS.md](compiler/c0/NATIVE_OS.md). The machine/Stage0/B0 trust root,
C0.25 emitter and existing capacity bounds remain unchanged. This is not full
Safety, full-language self-hosting or completed Python/LLVM toolchain migration;
public VERSION1.0.2a1/CHANNELdev are unchanged.
The full-main1079 result predates the four-immediate diagnostic formatter fix.
Current post-fix component/proof/MCP/public/assurance results and the unrun
post-fix full main are distinguished in the
[session report](../docs/project/VALIDATION.md).

The older 49-byte token-table helper is retained only
as a bounded proof, not as an untrusted-stream framing validator.

See the [host-wrapper output contract](OUTPUTS.md) for protected inputs, exact
publication, cleanup and fail-closed ELF inspection.

## Machine-Level Foundation

`machine/x86_64-linux/hex0.seed` is an x86_64 Linux ELF64 executable encoded as
reviewable bytes in `hex0.hex`. It accepts hexadecimal text on standard input
and emits decoded bytes on standard output. It uses raw Linux syscalls and has
no libc, compiler, assembler, linker, Python, or LLVM dependency at runtime.

Files:

- `hex0.seed`: canonical machine-code trust root
- `hex0.hex`: auditable byte manifest used to reconstruct the seed
- `hex0.sha256`: expected identity of the seed
- `hex0.reference.asm`: non-canonical review aid for the machine bytes
- `materialize.sh`: host reconstruction and hash-verification helper

The shell helper is not part of the semantic compiler chain. It provides a
portable way to reconstruct the checked-in seed from text on a development
host. Once `hex0.seed` exists, later bootstrap stages consume it directly.

### Machine Contract

- target ISA: AMD64/x86_64 in 64-bit long mode
- operating interface: Linux x86_64 syscall ABI
- executable format: static ELF64 `ET_EXEC`, little-endian
- image base: `0x400000`
- entry point: `_start` at `0x4000b0`
- load policy: one read/execute `PT_LOAD`; no writable code segment
- process interpreter: none
- stack policy: inherited Linux process stack, marked read/write and
  non-executable with `PT_GNU_STACK`
- calling convention: no function calls; execution begins at the Linux process
  entry contract rather than a language runtime ABI
- memory model: one 16-byte stack reservation, no heap, no global writable
  storage, and no allocation or deallocation
- file descriptors: inherited `0`/`1`/`2`; the seed opens no descriptors

Register ownership inside the seed is explicit:

- `r12b`: pending high hexadecimal nibble (`0xff` means empty)
- `r13d`: comment-state flag
- `rsp`: one-byte read/write buffer after a 16-byte reservation
- `rax`, `rdi`, `rsi`, `rdx`: Linux syscall arguments and results
- `rcx`, `r11`: treated as syscall-clobbered

### Input And Output Contract

The seed reads hexadecimal text from stdin and writes decoded bytes to stdout.
It accepts `0-9`, `a-f`, `A-F`, spaces, tabs, LF, CRLF, and `#` comments. Empty
input succeeds with empty output.

Malformed hexadecimal input, an odd final nibble, read failure, or write
failure exits with status `1` and a specific stderr diagnostic. Successful
decoding exits `0`. Interrupted `read` and `write` syscalls are retried. Other
signals retain normal Linux process semantics.

The decoder streams complete bytes, so callers that need an all-or-nothing
file must use a temporary path and rename after success. `materialize.sh` does
exactly that and leaves an existing destination untouched on every validation
or hash failure.

### Trust And Dependencies

| Operation | Required dependency |
| --- | --- |
| Execute canonical seed | x86_64 Linux kernel |
| Execute seed on current AArch64 development host | `qemu-x86_64` test adapter |
| Reconstruct seed from checked-in text | Bash plus `sha256sum` host verifier |
| Compare reference assembly to seed | optional NASM audit only |
| Build canonical Stage 0 | `hex0.seed`; no assembler, linker, Python, LLVM, or host compiler |
| Build the Bootstrap Compiler B0 | `stage0.seed`; no assembler, linker, Python, LLVM, or host compiler |
| Build the Core Compiler C0 | `b0.seed`; no assembler, linker, Python, LLVM, or host compiler |

`hex0.reference.asm` is never an input to the canonical build. Its parity test
is an independent review aid, not the source of trust.

## Stage 0

`stage0/x86_64-linux/stage0.seed` is the canonical two-pass symbolic
flat-binary emitter. `hex0.seed` reconstructs it from `stage0.hex`, and Stage 0
can reconstruct the same manifest byte-for-byte itself.

Its documented `.nql0` format emits hexadecimal machine bytes and resolves
four symbol operations: definitions, signed `rel32`, fixed-image virtual
addresses, and file offsets. The qualification fixture uses those operations
to generate and execute a static ELF containing a forward jump and
RIP-relative memory access.

Stage 0 uses bounded `mmap` regions, raw syscalls, deterministic two-pass
resolution, input-byte diagnostics, and explicit cleanup. See
`stage0/README.md` and `tests/bootstrap/stage0.sh` for the exact contract and
evidence.

## Bootstrap Compiler B0

`compiler/b0/x86_64-linux/b0.seed` is the promoted bootstrap compiler artifact.
It is built by `stage0.seed`, checked by hash, and guarded by
`tests/bootstrap/bootstrap_compiler_b0.sh`. B0 intentionally supports only the
small Core-0 subset needed to start the next compiler generation.

B0.7m raises only its bounded source arena from 131,072 to 196,608 bytes after
the measured C0.15 source reached 136,042 bytes. B0.7n then raises only the
bounded output arena from 262,144 to 393,216 bytes and the byte-access patch
table from 2,560 to 3,072 entries after C0.16 crossed both older limits. Exact
boundary and overflow gates lock both changes. B0.7o raises the input arena to
262,144 bytes and patch table to 4,096 entries for C0.17. B0.7p raises the
input arena to 327,680 bytes, output arena to 524,288 bytes, and patch table to
5,120 entries for C0.18. C0.19 and C0.20 remain inside those predecessor
capacities. C0.21's 527,503-byte artifact then crosses only the old output
bound, so B0.7q raises `OUTPUT_CAP` to 589,824 bytes while leaving input and
byte-access capacities unchanged. Exact and one-step overflow gates cover
every bound; grammar and code-generation semantics remain unchanged.
C0.24 then requires 5,166 byte-access patches for its fixed token-push
lowering. B0.7r raises only `BYTE_ACCESS_CAP` from 5,120 to 5,376; input remains
327,680 bytes and output remains 589,824 bytes. Exact and overflow gates prove
the new patch bound without adding B0 grammar or code-generation semantics.

## Core Compiler C0

`compiler/c0/compiler.nq` is accepted semantically by B0 and compiled into the
canonical `compiler/c0/x86_64-linux/c0.seed`. C0.25 has a bounded tokenizing
lexer, real source locations, checked u8 `+`/`*` precedence lowering, multiple
immutable `let` statements, and collision-free lookup for eight bounded local
integers. Bounded `write` strings lower into standalone syscall-only output
programs. Runtime `input_read`, `output_write`, `byte_store`, `byte_load`,
mutable byte assignment, and non-nested `while` lower into a standalone
artifact with separate RX text and RW memory. Ordinary runtime artifacts keep
256 bytes at `0x401000`; parser-bearing artifacts use 16 KiB at `0x403000` so
their larger RX payload cannot overlap the writable mapping. Dynamic output
uses a complete-write loop, handles `SIGPIPE`, and exits 74 with an exact
diagnostic on failure. Literal and memory-backed output now share one ordered
operation stream. C0 also builds canonical `c0-successor.seed`, which consumes a bounded
function grammar ending in `return SP <decimal-u8> } LF EOF`, emits a matching
standalone return-u8 ELF for every value 0..255, and rejects malformed input
with no artifact bytes. Before the return, that grammar supports the exact
bounded statement forms described below. The `byte_assert_range`,
`byte_parse_u8`, `byte_parse_u8_then`, and `byte_parse_stmts` intrinsics
implement bounded
runtime validation, decimal conversion, and dispatch for at most three exact
dead `byte_store` statements, one exact `input_read(32,96)`, and one dependent
exact `byte_parse_stmts(32,0)`, followed by at most two dead post-parser
`byte_store(u8,u8)` statements, exact terminating clear loops, and the exact
complete first return-emitter, parser-emitter, and input-emitter constructs.
Seven-byte parser metadata lets the successor emit a return-only, input-read,
or marked 3,459-byte parser artifact selected by direct C0. A bounded
self-image path then writes the complete current ELF image with a retrying
syscall loop and exact exit-74 failure handling. Six independent 512-byte token
tables prevent high source offsets from corrupting earlier token lengths and
accept exactly 512 source tokens. Decoded literals occupy a separate
4,096-byte bounded arena at `20000..24095`, source input is bounded to 9,984
bytes, and compiler scratch formerly overlapping that source range now lives
at `13080..13999`. The compact successor source uses the explicit `\0` string
escape to encode machine artifacts without changing decoded bytes. Its return
and input paths emit the dynamic return byte separately from the constant
ten-byte ELF tail, eliminating four runtime setup stores without changing
target artifacts.
Its materializers verify canonical hashes and its path adapter preserves old
output on failure. See
`compiler/c0/README.md` and
`tests/bootstrap/core_compiler_c0.sh` for the exact scope and evidence.

C0.20 lowers `byte_load_at(pointer_slot, destination)` to a fixed machine
sequence that loads through the 256-byte runtime memory. C0.21 adds
`byte_store_at(pointer_slot, source_slot)` and proves a byte-exact runtime copy
from a source region into a destination table. C0.22's
`source_byte_tokenizer.nql` composes those primitives into one count byte plus
sixteen fixed `[kind, offset, length]` records, with explicit rejection of a
seventeenth nonzero source byte. C0.23 adds `byte_classify_ascii`; C0.24 adds
`byte_token_push`, which elides whitespace, coalesces identifier/integer runs,
and preserves punctuation under an independently tested sixteen-token cap.
C0.25's `source_token_parser.nql` consumes that exact table, validates bounded
infix expression structure, retains token locations, and appends one flat CST
root. Deterministic rebuild, malformed-stream, even-count underflow, and exact
output gates make this the first source-driven parser artifact in the canonical
chain.
C0.19's marked parser still consumes the complete 8,631-byte successor source and
emits its 3,459-byte current image. That image repeats the same operation and
produces byte-identical generations C and D. The proof is deliberately named
bounded generation: generation B comes from a dedicated marker fixture, not
from compiling the same general compiler source. The next work unit must add
precedence-aware nodes and bounded statement/function grammar to the C0.25
parser, then extend that foundation into Full Compiler emission without
reintroducing a host compiler into the canonical chain.

## Verification

```bash
make machine-foundation
make stage0
make stage0-test
make bootstrap-test
```

The test suite proves that reconstruction is byte-for-byte deterministic and
that the seed can decode its own byte manifest back into an identical ELF.

See `manifest.tsv` for the exact implementation status of every stage.
