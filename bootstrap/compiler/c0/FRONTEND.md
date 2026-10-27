# C0 Source Frontend

The sections below record the original scalar/NQAF/1 contract. The current
candidate component contract is **C0.32**; its native additions are below.
The completed C0.31 capacity evidence remains historical and unchanged.
[RUNTIME_IO.md](RUNTIME_IO.md) retains C0.30 call statements
with single-owned call roots and NQAF/4. [FUNCTIONS.md](FUNCTIONS.md) defines named functions,
parameters, nested calls and NQAF/3. [CONTROL_FLOW.md](CONTROL_FLOW.md) defines
signed comparisons, nested if/else and while, and NQAF/2 delimiters. Scalar
sources retain byte-identical NQAF/1 output, except the explicitly newly
reserved `if`, `else`, `while` identifiers. Storage adds a 65-byte bounded block
stack at 35000 and call frames at 36000 in the legacy layout. The historical
source/token/node limits in that layout are unchanged; NQAF/5 uses the wide
layout below.
The historical grammar below describes C0.26, not the current language subset.

## C0.32: Native Calls And Lexical Unsafe Blocks

The current source adds contextual `unsafe { ... }` with a required nonempty
first-comment `# safety:` or `// safety:` invariant, lexical scope and the
existing combined depth64 limit. Existing identifiers named `unsafe` remain
valid, including operands ending if/while conditions. Functions still need a
final top-level return. There is no new lexer keyword or file-wide safety mode.

An unsafe block or resolved `arg_count`, `arg_copy`, `byte_address` or `syscall6`
selects NQAF/6, wide32/dialect5, profile0/1 with zero reserved fields. Global
user functions resolve first even on wrong arity; comments and user shadows do
not activate native semantics. Kind45 anchors the opener/header through the
byte before the first body/closing token; kind46 anchors its matching `}`.
Both have zero children/flags and ordinary statement links. Raw address/syscall
calls require the owning lexical scope, not incidental expression position.

Missing/empty invariant produces C0P-014/1; raw use outside scope produces
C0S-001/1, both with no AST. Existing bounds/checks remain. The backend repeats
permission and actual-source-containment checks independently. See
[NATIVE_OS.md](NATIVE_OS.md) for exact syntax, APIs, diagnostics and limits.
Six native frontend and forty scoped regression methods passed; the I1
condition-operand compatibility correction received independent approval.
Actual complete-source generations, public integration, full main/MCP and
installed combined-proof execution gates pass. Broader stable/security
readiness remains PARTIAL; the open signal incident and assurance limits are
recorded in [NATIVE_OS.md](NATIVE_OS.md).

## C0.31: Wide Syntax Frontend

This completed capacity foundation implements the frontend portion of the approved
[compiler-capacity design](CAPACITY.md).
It is built by the pinned B0 with `--compiler-profile`, which maps a bounded
16 MiB read/write, non-executable arena and releases it on normal and error
exits. Sources, seeds and pins were installed together after the complete
prevalidation and independent reviews. The same complete postinstallation
checks passed; see [CAPACITY.md](CAPACITY.md).

At the C0.31 checkpoint, the MCP source/probe contract was labeled C0.31
independently of the frozen compiler source comment. Its capacity/profile/component-generation
verification flags require fresh complete gate receipts and matching source,
test and artifact identities. Metadata/resource reads alone leave those flags
false. See [CAPACITY.md](CAPACITY.md) for the consumer and promotion boundaries.

The frontend accepts at most 262,144 source bytes, 65,536 tokens (excluding
EOF), and 65,536 nodes. Each bound is independent. Offsets, lengths, IDs,
operand entries and saved call links use complete unsigned 32-bit fields.
Control nesting stays at 64 and function arity at six. No grammar is added.
Each function still needs a terminal top-level `return`; the compiler sources
express their exit status as `return ok == 0`, preserving success for any
nonzero `ok` and failure for zero.

Raw source selects runtime profile 0. At byte zero only, `NQSC`, version 1,
profile 1, zero flags and eight zero reserved bytes form a 16-byte envelope.
Those bytes are excluded from source size and diagnostic coordinates. Invalid
or truncated envelopes produce `input:1:1: error[C0P-013]`, exit 1, empty stdout.
The existing C0P-010 continues to diagnose trailing source. Prefix reads and
payload reads accumulate until EOF; a complete source prefix alone cannot
cause output while its input stream remains open.

Plain source fitting all old 8,192/512/512 bounds retains exact NQAF/1..4 bytes.
Larger valid source or an explicit profile emits NQAF/5: a 32-byte header,
unchanged source bytes, and 32-byte records. Header offsets 8/12/16/20 hold u32
source length/node count/root ID/token count; offsets 24/25 hold the independent
grammar dialect and runtime profile. Records hold kind/flags at 0/1 and u32
anchor offset/length/left/right/next at 4/8/12/16/20; all reserved fields are zero.
Node IDs remain one-based and allocation stays deterministic postorder.
Legacy serialization uses bounded scratch after validation, rather than
truncating wide state in place. No AST bytes are emitted before validation.

Candidate storage intervals are half-open offsets within the mapped arena:

| Region | Purpose |
| --- | --- |
| `[0, 0x41000)` | source, overflow byte, read lookahead |
| `[0x50000, 0x11000c)` | 65,537 twelve-byte tokens, including EOF |
| `[0x120000, 0x130000)` | transport, lexer/parser state and scratch |
| `[0x200000, 0x400000)` | 65,536 thirty-two-byte nodes |
| `[0x400000, 0x4c000c)` | 65,537 twelve-byte operator entries |
| `[0x4d0000, 0x510004)` | 65,537 four-byte operand IDs |
| `[0x520000, 0x620010)` | 65,537 sixteen-byte call markers |
| `[0x630000, 0x630410)` | 65 sixteen-byte block entries |
| `[0x640000, 0x640020)` | output header |
| `[0x641000, 0x651000)` | diagnostics and bounded serialization scratch |
| `[0x660000, 0x6a0000)` | C0.32 u32 safety-header starts |
| `[0x6a0000, 0x6b0000)` | C0.32 exact native-name classes; no trusted permission bits |
| `[0x7ff000, 0x7ff100)` | discarded inactive stores |

No descriptor is opened by the frontend. The B0 profile owns its mapping;
syntax failures exit 1, checked runtime failures exit 70, and resource/stream
failures exit 74. Output may be partial after an output syscall failure, so
consumers must inspect exit status. The storage table later in this document
is the historical C0.26 layout, not the candidate layout above.

## Decision

Requested mode: continue source-driven parser development.
Actual update class: Minor Development, medium risk.
Primary scope: lexer, parser, flat AST and canonical bootstrap evidence.
Public contract impact: none; NQAF is an experimental internal format.
Bootstrap impact: an additional C0 component is built directly by B0.
Compatibility impact: the C0.25 emitter and its generated tools are retained.
Version impact: no public VERSION or release channel change.
ADR required: this document records the component boundary and format decision.
Release blocking: new frontend gates must pass before its artifact is promoted.

The C0.25 generated language has a 256-byte runtime arena, eight constant
locals and a 40-operation limit. Extending its parser through more special
intrinsics would perpetuate the wrong abstraction. B0 already compiles Core-0
with mutable integers, arithmetic, loops, byte memory and stream I/O. Use that
existing predecessor to build a complete source-to-AST C0 component instead.
No Python, R0, LLVM or assembler participates in this build. Python is used
only by the test oracle. This is **not** C0 self-compilation or Full Compiler
promotion. AST-to-semantics/codegen remains a separate next contract.

## Grammar

```text
program    = "fn" "main" "(" ")" "{" statement* "return" expr ";"? "}" EOF
statement  = ("let" identifier "=" expr | identifier "=" expr) ";"?
expr       = sum
sum        = product (("+" | "-") product)*
product    = primary (("*" | "/") primary)*
primary    = identifier | decimal | "(" expr ")"
```

Operators associate left; parentheses can nest. An omitted semicolon ends an
expression before `let`, `return`, `}`, or an identifier followed by `=`.
Other adjacent primaries are errors. Identifiers use ASCII letters/underscore
followed by letters/underscore/digits. Keywords are classified by full lexeme,
not a prefix. Decimal literals retain their original digits without evaluation.
Space, tab, LF, CRLF, `#` and `//` line comments are accepted. Bare CR, embedded
NUL, non-ASCII bytes, strings, unary operators, calls, parameters, control flow
and multiple functions are rejected in this component. Missing/extra tokens
are never accepted as a valid prefix.

This is syntax, not name resolution: duplicate declarations, undeclared names
and integer range/type checks belong to the following semantic pass.

## Storage And Progress

All storage is in B0's zero-initialized 65,536-byte runtime arena. No heap and
no file descriptors are allocated by the frontend. Input is fd 0, output fd 1,
diagnostics fd 2. Short reads are accumulated until EOF or the overflow byte.
B0 provides checked ranges, complete writes and I/O error status 74.

| Region | Purpose |
| --- | --- |
| 0..8192 | Source, at most 8192 bytes plus one overflow byte |
| 10000..13077 | 512 tokens plus EOF, six-byte records |
| 14000..14999 | Parser state and diagnostic selection |
| 15000..15127 | Per-transition scratch |
| 20000..28191 | At most 512 AST nodes, 16 bytes each |
| 30000..32051 | Operator stack, 513 four-byte entries including sentinel |
| 33000..34025 | Operand stack, 513 two-byte entries including sentinel |
| 48000..48015 | Output header |
| 50000..52407 | Diagnostic buffers |
| 65000..65015 | Discarded inactive stores |

Lexer transitions consume a byte, finish one token, or stop. Parser transitions
consume a token, pop an operator, finish a statement, finish the function, or
fail. Both stacks are bounded by the token cap; allocation is separately
checked. There is no recursive machine stack growth. No stdout bytes are
written before the entire source is validated. I/O failure after emission
begins can leave a partial stream and must be checked by the consumer.

## NQAF Version 1

Little-endian header (16 bytes), followed by the exact source bytes, then the
used node records only:

```text
0:4 magic "NQAF"   4:u8 version=1       5:u8 record_size=16
6:u16 flags=0     8:u16 source_length  10:u16 node_count
12:u16 root_id   14:u16 token_count (excluding EOF)
```

Nodes use one-based indices; zero means no node. Each 16-byte node is:

```text
0:u8 kind        1:u8 flags=0          2:u16 source_offset
4:u16 length     6:u16 left            8:u16 right
10:u16 next      12:4 reserved=0
```

Spans identify the node's anchor lexeme, not its entire subtree. All spans
refer to the included source, so names and literals need no copied strings.

| Kind | Meaning | Left | Right | Anchor |
| --- | --- | --- | --- | --- |
| 4 | Identifier | 0 | 0 | Identifier |
| 5 | Decimal | 0 | 0 | Digits |
| 15,17 | Add, subtract | LHS | RHS | Operator |
| 16,18 | Multiply, divide | LHS | RHS | Operator |
| 30 | Let | Binding identifier | Value expression | `let` |
| 31 | Assignment | Target identifier | Value expression | Target |
| 32 | Return | Value expression | 0 | `return` |
| 33 | Main function | First statement | 0 | `fn` |

Only statements have `next` links. Allocation order is deterministic postorder
for expressions; the final allocated node is the function root. Every node is
reachable exactly once through the root, child indices and statement links.

Diagnostics use one-based byte locations and `input:L:C: error[C0P-NNN]`.
Syntax/bound errors exit 1 with empty stdout; success exits 0 with empty stderr.

## Reproduce

```sh
bootstrap/compiler/c0/x86_64-linux/materialize-frontend.sh
ROOT_DIR="$PWD" bash tests/bootstrap/c0_frontend.sh
```

Run the resulting `c0-frontend.seed` with redirected source on x86_64 Linux;
on other hosts use `qemu-x86_64`. The output is NQAF, not an ELF executable.
