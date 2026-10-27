# NolQu-L Core Compiler C0

C0 is the first Core Compiler artifact after the promoted B0 bootstrap
compiler. Its canonical source is NolQu-L Core-0 and its canonical executable
is built by B0, not by a host compiler or assembler.

The emitter described by `compiler.nq`/`c0.seed` remains C0.25. The separate
current frontend/backend source contract is experimental C0.32; see
[NATIVE_OS.md](NATIVE_OS.md). Its scoped syntax/ABI/utility tests have passed,
and actual complete-source generations pass. Final main/MCP and installed
combined-proof execution gates also pass. An earlier comparison-backend
SIGKILL remains unexplained; stable/security readiness remains PARTIAL.
Public VERSION/CHANNEL remain 1.0.2a1/dev. No full Safety, Full Compiler,
self-hosting or release readiness follows from the component designation.
The passing full main predates a four-immediate diagnostic repair. Current
post-repair MCP, generation/proof, impacted public and bounded assurance gates
pass; full main after that repair was not rerun. The
[session report](../../../docs/project/VALIDATION.md) records both
identities and the failed assurance budget calibration without erasing either.

Canonical predecessor:

```text
bootstrap/compiler/b0/x86_64-linux/b0.seed
```

Canonical source and artifact:

```text
bootstrap/compiler/c0/compiler.nq
bootstrap/compiler/c0/x86_64-linux/c0.seed
```

Completed predecessor/component milestones (historical evidence retained):

```text
C0.0 Scaffold PASS
C0.1 First Core Artifact PASS
C0.2a Bounded Lexer And Return Expressions PASS
C0.2b Multiple Statements And Local Integers PASS
C0.2c Bounded Write And Successor Emitter PASS
C0.3a Runtime Byte Memory And Input PASS
C0.3b Byte Assignment And Minimum Control Flow PASS
C0.3c Dynamic Runtime Output PASS
C0.3d Source-Consuming Successor PASS
C0.4 Bounded Textual Successor PASS
C0.5 Located Textual Return Source PASS
C0.6 Two-Digit Textual Return Source PASS
C0.7 Full Textual U8 Return Source PASS
C0.8 Function-Envelope Rebuild Probe PASS
C0.9 Bounded Statement Dispatch PASS
C0.10 Bounded Input-Read Successor PASS
C0.11 Bounded Parse-Stmts Successor PASS
C0.12 Bounded Post-Parser Store PASS
C0.13 Bounded Second Post-Parser Store PASS
C0.14 Bounded Return-Tail Split PASS
C0.15 Exact Terminating Clear Loop PASS
C0.16 Exact Return-Emitter Recognition PASS
C0.17 Canonical Parser-Emitter Recognition PASS
C0.18 Canonical Input-Emitter Recognition PASS
C0.19 Bounded Self-Image Generation PASS
C0.20 Indirect Byte Load And Source Scan PASS
C0.21 Indirect Byte Store And Source Table Copy PASS
C0.22 Bounded Source Byte Token Table PASS
C0.23 Bounded ASCII Lexical Classification PASS
C0.24 Lexical Token Coalescing PASS
C0.25 General Bounded Expression Parser PASS
C0.26 Source Frontend And Precedence AST PASS (B0-built component)
C0.27 AST Backend And Checked Scalar ELF PASS (B0-built component)
C0.28 Structured Control Flow And Lexical Scope PASS (B0-built components)
C0.29 Functions And Native Calls PASS (B0-built components; see FUNCTIONS.md for gates)
C0.30 Call Statements And Byte/Stream Runtime PASS (B0-built components; see RUNTIME_IO.md for gates)
C0.31 Compiler-Source Capacity And Component Generations PASS (experimental; see CAPACITY.md)
core-compiler PASS
```

The completed C0.31 capacity implementation is documented in
[`CAPACITY.md`](CAPACITY.md). Reviewed component pins match the complete sources;
all eight preinstallation and postinstallation commands passed without timeout or skip.
Fresh MCP capacity/profile/component-generation flags require all real gates
and complete matching receipts. Mere source presence or matching pins cannot
enable them. Full Compiler, self-hosting and Verified remain unimplemented.

The current source-frontend work is in [`frontend.nql`](frontend.nql), with its
versioned AST, grammar, memory layout and provenance defined in
[`FRONTEND.md`](FRONTEND.md), [`CONTROL_FLOW.md`](CONTROL_FLOW.md),
[`FUNCTIONS.md`](FUNCTIONS.md) and [`RUNTIME_IO.md`](RUNTIME_IO.md).
`x86_64-linux/materialize-frontend.sh`
builds `c0-frontend.seed` using B0. The compiler emitter remains the exact
C0.25 `c0.seed`; component success is not Full Compiler/self-hosting success.

[`backend.nql`](backend.nql) consumes NQAF/1..6, validates graph
ownership, function/block nesting and lexical anchors, resolves mutable i64 locals
and parameters, and
emits standalone ELF for `+ - * /`, signed comparisons and nested `if/else`
and `while`, plus forward/nested/recursive native function calls and call statements. There are up to
six parameters per function and 64 active call frames; arithmetic and depth faults
have source-located diagnostics. Its scalar
semantics, memory map and provenance are defined in [`BACKEND.md`](BACKEND.md).
`x86_64-linux/materialize-backend.sh` builds the pinned
`c0-backend.seed` directly with B0. `x86_64-linux/compile-source.sh input.nql out`
joins frontend and backend with atomic publication. It is experimental, not
the Full Compiler; public `nqlc --backend canonical` delegates to this path.
It invokes no host assembler, linker or LLVM compiler.
The checked byte/stream intrinsics use a shared 65536-byte runtime stack arena,
allocated only when an intrinsic resolves. That retains the C0.30 default path.
C0.31 also accepts NQAF/5 and the explicit mapped compiler profile.
Actual A -> B -> C component evidence and the final installation
gates are recorded in CAPACITY.md, separately from the retained C0.25 emitter.

C0.32 adds `arg_count`, checked byte-preserving `arg_copy`, unsafe
`byte_address` and raw `syscall6`, with NQAF/6 dialect5 and matching lexical
unsafe markers. The backend checks actual source containment as well as AST
ownership. `arg_count` alone needs no byte arena; the other operations retain
the selected 64 KiB default or explicit 16 MiB RW/NX arena. The actual
[native file reader](../../../examples/canonical/native_cat.nql) uses argv and
openat/read/write/close in NolQu-L source. Its [guide](../../../examples/canonical/README.md)
records literal-argument, partial-I/O, descriptor and path-capacity behavior.
This closes a native process/file-access prerequisite; it does not migrate
Python MCP/tests, shell drivers or legacy LLVM/NASM tooling away.

The older `source_token_parser.nql` is retained as the C0.25 bounded-generation
proof. Its input contract assumes the complete 49-byte tokenizer result, not
an arbitrary stream: a short read can be zero-padded by its runtime. Do not
use it as a framing validator. C0.26 instead reads original source through EOF,
checks bounds and validates the whole grammar before emitting any AST bytes.

## C0.1 Contract

C0.1 is a bounded stream compiler. It reads source bytes from fd 0, writes the
compiled artifact to fd 1, and writes diagnostics to fd 2. The accepted source
shape is:

```text
fn main() {
    return <u8>
}
```

ASCII space, tab, LF, and CR may appear between tokens, and the semicolon after
the return value is optional. Whitespace inside `fn`, `main`, `return`, or a
decimal integer is rejected. At least one whitespace byte is required between
`fn` and `main`, and between `return` and its decimal literal, matching keyword
boundaries in Core-0. The return value must be in `0..255`. C0.1 emits a
188-byte standalone ELF64 x86_64 Linux executable with no interpreter and a
non-executable stack. The value is lowered into the executable's `mov edi,
imm32` instruction; it is not selected from a canned whole-source artifact.

Invalid source exits 1, emits no artifact bytes, and writes:

```text
input:1:1: error[C0-001]: invalid return program
```

The fallback diagnostic above is C0.1 history. Current C0 reports the first
failing token or byte with a one-based line and column and uses the broader
message `invalid C0 program`.

## C0.2a Contract

C0.2a replaces the C0.1 whitespace-compaction recognizer with a bounded,
single-pass lexer. It records token kind, u8 value, and a 16-bit source byte
offset in fixed parallel tables. Source is limited to 1,024 bytes and 128
tokens; crossing either bound fails before artifact emission.

The accepted expression grammar is:

```text
program := "fn" "main" "(" ")" "{" "return" expr ";"? "}"
expr    := term ("+" term)*
term    := u8 ("*" u8)*
u8      := decimal integer in 0..255
```

Multiplication binds tighter than addition and both operators associate left.
Every intermediate result must remain in `0..255`. Division, subtraction,
parentheses, identifiers in expressions, and local statements remain outside
C0.2a and are rejected with a source-located diagnostic. Successful programs
still lower to a standalone 188-byte ELF with the evaluated value in the exit
immediate.

## C0.2b Contract

C0.2b extends the parser without widening B0. The accepted structured subset
is:

```text
program     := "fn" "main" "(" ")" "{" let_stmt* return_stmt "}"
let_stmt    := "let" local "=" expr ";"?
return_stmt := "return" expr ";"?
expr        := term ("+" term)*
term        := factor ("*" factor)*
factor      := u8 | local
local       := one lowercase ASCII letter
```

At most eight immutable locals may be declared. A binding becomes visible
only after its initializer succeeds, so self-reference is rejected. Duplicate
bindings, unknown bindings, malformed declarations, and the ninth local fail
at the offending source location and emit no artifact bytes. The one-byte
local-name bound is an explicit bootstrap constraint: it gives direct,
collision-free lookup while C0 still has only fixed byte memory. It is not a
Full NolQu-L identifier restriction.

Local initializers and the final return expression share the checked u8
precedence evaluator. Every intermediate remains in `0..255`; successful
programs still emit the same compact standalone ELF shape with only its
semantic exit immediate changed.

## C0.2c Contract

C0.2c adds bounded string tokens and a semantic output statement:

```text
program    := "fn" "main" "(" ")" "{" (let_stmt | write_stmt)* return_stmt "}"
write_stmt := "write" "(" string ")" ";"?
```

Strings support `\n`, `\r`, `\t`, `\\`, `\"`, and `\xNN`. Multiple writes
are concatenated in source order. The decoded payload is capped at 255 bytes;
malformed escapes, unterminated strings, and payload overflow fail at the
actual source byte and emit no artifact. A program without output keeps the
188-byte C0.2b ELF shape. A program with output emits a standalone
`212 + payload_length` byte ELF whose machine code performs `write(1, ...)`
before exiting with the evaluated return value.

The original C0.2c successor proof was deliberately narrow:

```text
successor.nq --compiled by c0.seed--> c0-successor.seed
c0-successor.seed --executed--> standalone return-42 ELF
```

At C0.2c, `successor.nq` was a fixed semantic emitter rather than a
source-consuming compiler. C0.3d replaces that historical artifact with the
bounded source-consuming successor documented below. Neither proof is
self-hosting.

## C0.3a Contract

C0.3a adds the first bounded target-runtime substrate:

```text
runtime_stmt   := "input_read" "(" u8 "," u8 ")" ";"?
                | "byte_store" "(" u8 "," u8 ")" ";"?
runtime_return := "return" "byte_load" "(" u8 ")" ";"?
```

Runtime artifacts have a zero-initialized 256-byte memory region in a
dedicated RW `PT_LOAD`, separate from the RX text load. `input_read` performs
one raw read from fd 0, allows EOF, blocks `SIGPIPE`, emits
`runtime: input_read failed` through a complete-write loop to fd 2, and exits
74 on syscall failure even when the diagnostic descriptor is unavailable. Its
immediate range must satisfy `offset + count <= 256`. `byte_store` writes one
byte and the bounded `byte_load` return zero-extends one byte into the process
exit status. The stack is non-executable and no load segment is RWX.

C0.3a originally rejected static `write`, including an empty write, mixed
with runtime memory calls. C0.3d removes that temporary restriction by
lowering literal writes into the same ordered runtime operation stream.
Arithmetic around `byte_load` remains outside this bounded subset and is
rejected at its source location without partial artifact bytes.

The compiler records at most 32 runtime operations in fixed parallel tables;
the existing 128-token limit is tighter for current syntax. This remains a
bounded bootstrap subset, not a general memory model.

## C0.3b Contract

C0.3b adds mutable byte assignment and minimum control flow:

```text
dynamic_store := "byte_store" "(" u8 "," "byte_load" "(" u8 ")"
                 ("-" u8)? ")" ";"?
runtime_leaf  := "input_read" "(" u8 "," u8 ")" ";"?
               | "byte_store" "(" u8 "," u8 ")" ";"?
               | dynamic_store
while_stmt    := "while" "byte_load" "(" u8 ")" "{"
                 runtime_leaf* "}"
runtime_stmt  := runtime_leaf | while_stmt
```

A dynamic store copies one byte or subtracts an immediate with modulo-256
machine semantics. `while` compares a selected byte against zero, exits through
a patched forward `rel32`, and repeats through a real backward `rel32`. Multiple
sequential loops are valid. Nested loops are intentionally rejected at the
inner `while`; this keeps the bootstrap parser stackless and bounded. Loop
begin/end markers count toward the existing 32-operation limit.

## C0.3c Contract

C0.3c adds bounded dynamic output as a runtime leaf:

```text
runtime_leaf := "input_read" "(" u8 "," u8 ")" ";"?
              | "output_write" "(" u8 "," u8 ")" ";"?
              | "byte_store" "(" u8 "," u8 ")" ";"?
              | dynamic_store
```

`output_write(offset, count)` writes bytes from the 256-byte runtime memory
to fd 1 in operation order and is valid both at function scope and inside a
non-nested `while`. Its compile-time range must satisfy
`offset + count <= 256`. A zero count succeeds without issuing `write`.

Generated artifacts block `SIGPIPE` once before runtime output begins. Each
output operation retries short writes until the complete range has been sent.
A zero or negative syscall result, including a broken pipe, reaches one shared
handler which writes the exact diagnostic
`runtime: output_write failed\n` to fd 2 with its own complete-write loop and
exits 74. If fd 2 is also unavailable, the artifact still exits 74 without
recursion or silent success. Runtime artifacts remain standalone ELF64 with
separate RX and RW loads, no RWX segment, and a non-executable stack.

Runtime operation metadata occupies bytes 10,000 through 10,255 in C0's
bounded compiler memory: operation kind/arguments use 10,000..10,127, output
error patches use 10,128..10,191, and literal-address patches use
10,192..10,255. This is above the largest target artifact permitted by the
current 32-operation codegen bound and below scratch byte 12,000, so generated
machine code cannot overwrite metadata that later passes still consume. The
128-token lexer bound is tighter for current runtime syntax; regression gates
therefore exercise the reachable maximum of 19 operations, including an
output operation after eighteen input operations.

## C0.3d Contract

C0.3d places non-empty `write` literals in the runtime operation stream.
Literal payload bytes are appended once to the RX segment, each operation gets
a patched RIP-relative address, and literal and memory-backed output retain
source order. Empty literals are valid no-ops. Literal output uses the same
complete-write loop, shared exit-74 handler, exact diagnostic, and
`SIGPIPE` policy as `output_write`. Programs containing only static writes
retain their existing compact artifact bytes.

The C0.3d successor was the first bounded source compiler:

```text
one raw source byte (u8) -> standalone 188-byte return-u8 ELF
```

It reads at most the first byte from fd 0. EOF denotes zero and additional
bytes are outside this stage's source format and are ignored. The successor
emits a fixed 177-byte ELF prefix, constructs the source-dependent 11-byte
machine-code tail in its explicit 256-byte memory, and writes both parts in
order. Inputs `0x2a` and `0x41` are proven to produce distinct artifacts
byte-for-byte equal to direct C0 compilation of return 42 and return 65.
Failure to write either part exits 74 with the exact runtime output
diagnostic.

This machine-near bootstrap source format is retained as transition history;
C0.4 replaces it in the canonical successor. It was not textual NolQu-L, a
Full Compiler, or self-hosting.

## C0.4 Contract

C0.4 replaces the raw-byte successor input with the first exact textual
grammar:

```text
source := digit LF EOF
digit  := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

The successor emits the same 188-byte standalone return-u8 ELF as direct C0
compilation of the selected digit. Empty input, a non-digit, a missing LF, or
trailing ASCII input writes no artifact, emits exactly
`runtime: invalid source\n` to fd 2, and exits 1. A sentinel byte distinguishes
EOF after LF from ordinary trailing textual input while keeping the runtime
bounded to one three-byte read.

C0 provides this through
`byte_assert_range(offset, minimum, maximum)`. The intrinsic validates its
constant range at compile time, emits a 32-bit unsigned range check over the
256-byte runtime memory, and branches to one shared complete-write diagnostic
handler on failure. Full-width immediates preserve correct behavior for every
u8 bound, including 255. An unavailable diagnostic descriptor still exits 1.

This is the first textual successor grammar, not the final NolQu-L grammar and
not self-hosting. The next generation must expand the grammar before attempting
to consume `compiler.nq` itself.

## C0.5 Contract

C0.5 expands the successor to an exact, located textual return source:

```text
source := "return" SP digit LF EOF
digit  := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

The keyword, one ASCII space, digit, LF, and EOF sentinel are all validated
before the first artifact byte is written. Empty input, a wrong keyword,
missing spacing, a non-digit value, missing LF, or trailing input therefore
produces no partial artifact and reaches the same exact invalid-source
diagnostic and exit 1 as C0.4.

The C0 source arena is now 1,536 bytes and the token table accepts 192 tokens.
Both limits remain fixed and source-located: byte 1,537 and token 193 are
rejected without output. The canonical 1,209-byte successor exceeds the old
1,024-byte arena and exercises more than the old 128-token bound, so the
capacity bridge is proved by the real next-generation source rather than only
by a synthetic fixture. The parallel token-table layout used at this point was
later found to overlap offset-high and length-low entries above token 128.
C0.7 relocates all six 256-byte tables into one disjoint arena and adds a
high-offset regression gate; the historical capacity result remains valid,
but the old claim of guard space between every table was not correct. Its
return digit is still lowered through explicit byte memory and direct x86_64
emission; no host parser or hidden runtime was introduced.

## C0.6 Contract

C0.6 extends the located return value to exactly two decimal digits:

```text
source := "return" SP digit digit LF EOF
digit  := "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

The accepted value range is therefore `00..99`. Both digits are validated
before output. The successor converts them in explicit byte memory: one
bounded loop adds ten for each unit in the tens digit and a second bounded
loop adds one for each unit digit. Addition uses the existing modulo-256 byte
subtraction primitive (`-246` and `-255`); the validated range guarantees that
the accumulator cannot wrap. The generated immediate is therefore derived
from source bytes without adding a hidden decimal parser or host runtime.

The 1,454-byte successor fits the existing 1,536-byte source arena, but needs
more than 192 tokens. C0 now accepts 240 tokens and rejects token 241 at its
real source location. C0.7 subsequently proved that the old token-table
addresses were not fully disjoint at this bound and moved kind, value,
offset-low, offset-high, length-low, and length-high to independent 256-byte
ranges beginning at byte 16,000. The C0.6 successor intentionally fills all 32
operation records, proving the existing operation bound without increasing it.

## C0.7 Contract

C0.7 expands the successor value to the full textual u8 range:

```text
source := "return" SP decimal-u8 LF EOF
decimal-u8 := digit | digit digit | digit digit digit
```

Leading zeroes are accepted when the spelling still contains at most three
digits, so `00` and `099` denote 0 and 99. Values above 255, four digits,
missing digits or LF, malformed digits, and trailing bytes are rejected before
any artifact byte is written. Every invalid form emits exactly
`runtime: invalid source\n` to fd 2 and exits 1.

The new `byte_parse_u8(source, destination)` intrinsic makes the conversion
explicit in generated machine code. It reads at most five bytes from the
256-byte runtime memory, accepts one to three ASCII digits followed by LF and
the 255 EOF sentinel, computes the value in registers, checks `<= 255`, and
stores one byte at the destination. Its compile-time source offset must be at
most 251. All local rejection branches reach the existing shared invalid-source
handler; no host parser or runtime library is involved.

The canonical successor pre-fills sentinel positions, reads at most twelve
source bytes, validates the exact `return` prefix, invokes `byte_parse_u8`, and
emits the same 188-byte standalone ELF as direct C0 compilation. The 1,188-byte
source compiles to a 1,311-byte successor and uses 22 of 32 operation records.
Gate parity covers 0, 7, `00`, 42, `099`, 100, and 255. C0.7 also isolates all
six token tables and proves a valid token above offset 1,024 cannot corrupt an
earlier token length.

Adding the decoder grows `c0.seed` to 134,891 bytes. B0.7k therefore raises
only B0's bounded output arena to 196,608 bytes and proves both the 196,598-byte
near-limit output and rejection of the next emission step. It does not add any
B0 language semantics.

Canonical C0.7 identities:

```text
b0.seed            52,600 bytes  e665b4907c3cc177461794edf58eaea848420b29b21d257fdd13befbab908b93
c0.seed           134,891 bytes  49f57f4b15f8d23ab891ee8b3a385ce61b6c10d572a63ac8342641fe503c9f78
c0-successor.seed   1,311 bytes  3014b5f0c1efc3f311bd193a80f6b4c157cd961cf58649a9ff23f51b8297a42b
```

## C0.8 Contract

C0.8 runs the first bounded rebuild probe against the next compiler source.
The C0.7 successor failed at byte one because it expected `return` while the
compiler source begins with `fn`. The accepted successor grammar now crosses
that boundary:

```text
source := "fn" SP "main" "(" ")" "{" LF
          "return" SP decimal-u8 "}" LF EOF
```

This is the exact spelling `fn main(){\nreturn <decimal-u8>}\n`, not yet a
general whitespace-tolerant parser. The new
`byte_parse_u8_then(source, destination, terminator)` intrinsic accepts one to
three digits followed by the supplied u8 terminator, LF, and byte 255. Its
fixed 190-byte register decoder reads no more than six runtime bytes, enforces
`source <= 250`, checks the result is at most 255, and uses the existing shared
invalid-source handler. The original `byte_parse_u8` remains supported.

The canonical successor occupies 1,479 source bytes and 31 of 32 operation
records. It emits a 1,580-byte compiler artifact. Direct-C0 parity covers 0,
7, `00`, 42, `099`, 100, and 255; eighteen malformed function sources are
rejected without output.

The larger target code exposed a real arena collision: generated code crossed
the old decoded-literal scratch at byte 5,300. C0.8 moves that bounded
255-byte scratch to `18000..18254`, after the token tables ending at 17,535.
Code, operation metadata, token tables, and decoded literals are now disjoint.

The repeated self-source probe is intentionally still negative. It locks the
actual source prefix `fn main(){\nbyte_store`, proves the function envelope is
accepted, and produces the exact invalid-source diagnostic with no artifact.
The first unsupported construct is therefore `byte_store` on line two.

Canonical C0.8 identities:

```text
b0.seed             52,600 bytes  e665b4907c3cc177461794edf58eaea848420b29b21d257fdd13befbab908b93
c0.seed            156,692 bytes  d5b543b45f5ad2cc38ec3fe332e187e6e28d600954f53ca5ec09e67cba9dd537
c0-successor.seed    1,580 bytes  450fc6f26d371532a17ceb146cfba4c43bffa464db92f4788d22ebdbcd04508b
```

## C0.9 Contract

C0.9 adds `byte_parse_stmts(source, destination)`, a fixed 223-byte x86_64
dispatcher for this exact body grammar:

```text
body       := byte-store{0,3} return-statement NUL
byte-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
return-statement := "return" SP decimal-u8 "}" LF
```

Every decimal value is checked in `0..255`; the source offset is at most 183;
and a fourth store, malformed delimiter, missing newline, overflow, unknown
statement, or trailing byte reaches the shared exit-1 invalid-source handler.
The first 219 code bytes match the audited reference decoder before C0 patches
the final handler displacement.

The stores are semantically dead in this grammar because no load, output, or
other memory observer exists before the literal return. The successor emits
the same compact 188-byte return artifact for zero, one, or three stores.
Return-only outputs remain byte-identical to direct C0; dead-store programs are
locked by observable behavior and deterministic optimized output.

The successor is 1,262 source bytes, uses 24 of 32 operation records, and
emits a 1,452-byte artifact. Its repeated self-source probe now consumes all
three leading `byte_store` statements and rejects `input_read` on line five.

Canonical C0.9 identities:

```text
b0.seed             52,600 bytes  e665b4907c3cc177461794edf58eaea848420b29b21d257fdd13befbab908b93
c0.seed            183,983 bytes  ecaa8175bbbc562d223079c8368ba72a08cb71d868e0cd846ab7964004a19456
c0-successor.seed    1,452 bytes  6265d731657b436c2b90850b7c05ef93b1373c72ceeac29eb081c86061231208
```

## C0.10 Contract

C0.10 extends `byte_parse_stmts(source, destination)` with one optional exact
input operation while keeping the decoder fixed and bounded:

```text
body       := envelope? byte-store{0,3} input-read? return-statement NUL
envelope   := "fn main(){" LF
byte-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
input-read := "input_read(32,96)" LF
return-statement := "return" SP decimal-u8 "}" LF
```

The 385-byte x86_64 dispatcher accepts at most one `input_read`, after all
stores and before return. It rejects a different offset/count or numeric
spelling (including `032`/`096`), duplicate input, a store after input,
malformed delimiters, u8 overflow, and trailing
bytes through the shared invalid-source handler. Compile-time bounds require
`source <= 152` and `destination <= 253`. The result byte is stored at
`destination`, with no-input and input-present flags at the next two bytes.

The successor uses those flags to emit either the existing 188-byte return
artifact or the 377-byte `input_read(32,96)` artifact. Both outputs are
byte-identical to direct C0 output. The input artifact preserves raw-read
behavior, including the exact stderr diagnostic and exit 74 when fd 0 is
closed. The successor source is 2,449 bytes and its canonical executable is
1,802 bytes.

C0 input capacity is now 3,072 bytes. Decoded literal accounting is 16-bit
and bounded to 1,024 total bytes while retaining the 255-byte per-literal
limit. Exact and one-byte-overflow gates cover both capacities. C0.10 also
required B0.7l to raise the predecessor's byte-access patch capacity to 2,560
and output capacity to 262,144 bytes; both predecessor bounds have exact and
overflow tests and add no B0 language semantics.

The repeated self-source probe now consumes the exact envelope and
`input_read(32,96)`, then rejects `byte_parse_stmts` on line three. This is the
measured C0.11 blocker.

Canonical C0.10 identities:

```text
b0.seed             52,600 bytes  3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            201,492 bytes  7d553fb4e6896adf93b4f22ae6bf3a622c063e328d0ce779566f76e6cda79ae4
c0-successor.seed    1,802 bytes  18556ca2015f63fec1a62a1303a8bfb005ebe8e4979f99adffb607f32a411ade
```

## C0.11 Contract

C0.11 extends the fixed dispatcher only for the next construct measured by
the C0.10 rebuild probe. The accepted body grammar is now:

```text
body       := envelope? byte-store{0,3} input-read? parse-stmts? return-statement NUL
envelope   := "fn main(){" LF
byte-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
input-read := "input_read(32,96)" LF
parse-stmts := "byte_parse_stmts(32,0)" LF
return-statement := "return" SP decimal-u8 "}" LF
```

`parse-stmts` is valid only once, immediately after the exact input operation
and before return. A missing input, duplicate parser, different argument or
numeric spelling, store after input/parser, malformed delimiter, overflow, or
trailing byte reaches the shared exit-1 handler. The audited dispatcher is
499 bytes: the first 385 bytes preserve C0.10 control flow and a 114-byte tail
recognizes the single new statement. Compile-time bounds require
`source <= 129` and `destination <= 252` so all reads and four metadata bytes
remain inside byte memory.

Metadata contains the return value at `destination`, followed by no-input,
input-present, and parser-present flags. The successor uses those flags to
select exactly one frozen output path: the 188-byte return artifact, the
377-byte input artifact, or the 949-byte parse-stmts artifact. The new parser
artifact is byte-for-byte identical whether emitted directly by C0.11 or by
the successor, is deterministic, and preserves exact valid/invalid runtime
behavior.

The successor source is 3,905 bytes and its executable is 3,081 bytes. To
represent embedded executable bytes within the bounded source, C0.11 adds the
single-byte `\0` string escape while retaining `\x00`; this reduces textual
encoding without changing decoded output. Total decoded literal capacity is
now 1,536 bytes, with the existing 255-byte per-literal limit. The successor
uses 1,492 decoded literal bytes.

The measured 4,096-byte source requirement exposed an old layout collision:
source bytes above offset 3,079 overlapped compiler scratch at
`3080..3999`. C0.11 moves that scratch to `13080..13999`; source, operation
metadata, token tables, literal arena, and scratch are now disjoint. Exact
4,096/4,097 source and 1,536/1,537 literal gates lock both capacity changes.

The repeated rebuild probe now consumes the envelope, input operation, and
parse-stmts line, then rejects `byte_store(4,184)` on line four. That measured
statement is the next bounded blocker; C0.11 does not claim a general parser.

Canonical C0.11 identities:

```text
b0.seed             52,600 bytes  3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            215,029 bytes  1106d8fa33a2d0115603b0e1557b14e2b72460f3a17ab6f7c2373e37773f7666
c0-successor.seed    3,081 bytes  f957c7ca897bb26765b72061eff2d0850a36fb0fc3278899d73ed240c8cb795e
```

## C0.12 Contract

C0.12 crosses the exact line-four blocker measured by the C0.11 rebuild
probe. After a valid `input_read(32,96)` and `byte_parse_stmts(32,0)` pair,
the dispatcher accepts at most one additional bounded statement:

```text
post-parser-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
```

This is not a second store parser. The 499-byte dispatcher reuses its existing
generic `byte_store(u8,u8)` body. Parser success enters a seven-byte stub in a
previously reserved NOP island, sets the logical store count to two, and
dispatches again. A parser-present branch then reaches the existing store
body: the first post-parser store raises the count to three, while a second is
rejected by the existing bound. Store-before-parser ordering, exact parser
arguments, four-byte metadata, and every C0.11 invalid-source path remain
unchanged. No operation kind, metadata byte, dispatcher byte, or predecessor
capacity was added.

The post-parser store is unobservable in this successor subset, so the
successor omits it and emits the same 949-byte parser artifact as the no-store
form. Tests separately compile and execute the direct C0 form, then prove the
successor output is deterministic and byte-identical to its parser-only
output. A duplicate post-parser store exits 1 with no artifact.

The longest accepted post-parser store needs 20 bytes of bounded lookahead.
The compile-time source bound is therefore tightened from `source <= 129` to
`source <= 109`; `destination <= 252` remains unchanged. Exact `109/110` and
`252/253` acceptance/rejection gates prove both edges. The successor source is
3,903 bytes and its executable remains 3,081 bytes. Its embedded parser bytes
were regenerated from C0.12 rather than retaining the C0.11 payload.

The repeated self-source probe now accepts `byte_store(4,184)` on line four
and rejects the next `byte_store(5,60)` on line five. That second post-parser
store is the next measured blocker; C0.12 still does not claim a general
parser or self-hosting.

Canonical C0.12 identities:

```text
b0.seed             52,600 bytes  3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            215,029 bytes  c18e5afae0c05ed5c1476193c72fe8c02c282aa918ff892e1dcf2fb3e7a77dc9
c0-successor.seed    3,081 bytes  33cd17bfff567eacdadd8dbca9ad351c913714d78cb999bb18b4bb94ec11b405
```

## C0.13 Contract

C0.13 crosses the exact line-five blocker measured by the C0.12 rebuild
probe. After a valid `input_read(32,96)` and `byte_parse_stmts(32,0)` pair,
the unchanged grammar may now occur at most twice:

```text
post-parser-store := "byte_store(" decimal-u8 "," decimal-u8 ")" LF
```

The 499-byte dispatcher still reuses the existing generic store parser. Its
parser-success stub now initializes the logical store count to one instead of
two; the existing count check accepts the first and second post-parser stores
and rejects a third. This is a one-byte machine-code immediate change, not a
new operation kind or parser. Four-byte metadata, operation capacity, store
ordering, and predecessor capacity remain unchanged.

Both stores are unobservable in the current successor subset, so zero, one,
and two post-parser stores all emit the same 949-byte parser artifact. The
gate compiles and executes each form through direct C0 and two independent
successor builds, then proves byte-for-byte parity. A third post-parser store
exits 1, emits the exact invalid-source diagnostic, and produces no artifact.

Each worst-case store needs 20 bytes of bounded lookahead. The compile-time
source bound is therefore tightened from `source <= 109` to `source <= 89`;
`destination <= 252` remains unchanged. Exact `89/90` and `252/253` gates
prove both boundaries. The complete two-store fixture occupies the fixed
96-byte input window exactly. The successor source remains 3,903 bytes and
its executable remains 3,081 bytes; its embedded parser bytes were regenerated
from C0.13.

The repeated self-source probe now accepts `byte_store(4,184)` on line four
and `byte_store(5,60)` on line five, then rejects `byte_store(9,15)` on line
six. That third post-parser store is the next measured blocker; C0.13 still
does not claim a general parser or self-hosting.

Canonical C0.13 identities:

```text
b0.seed             52,600 bytes  3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            215,029 bytes  20539eb5da2d715df4c801b5646a5f6be49e6a6c82dce571df4a4fdb36453b52
c0-successor.seed    3,081 bytes  a2ee11260ac1411cf85030c35b109a7c61ec136561a98ae38d55ec9f5586a025
```

## C0.14 Contract

C0.14 crosses the line-six blocker without widening the parser. The four
leading stores in `successor.nq` only assembled the fixed part of the target
ELF return tail:

```text
<return-u8> 00 00 00 b8 3c 00 00 00 0f 05
```

Only the first byte varies. Both return-producing paths now emit that byte
with `output_write(0,1)` and append the remaining ten bytes as a literal
`write`. The four setup stores are removed. The parser path already emits a
complete artifact and remains unchanged.

This preserves every target artifact byte-for-byte while reducing mutable
runtime setup. The C0 compiler source and artifact are unchanged; this is a
bounded successor-source progression, not a new parser claim. The successor
source is 3,902 bytes and its canonical executable is 3,165 bytes.

The gate proves deterministic successor construction and direct-C0 parity for
return, input, and parser outputs. Its negative self-source probe still exits
1 with the exact invalid-source diagnostic and no artifact, but now reaches
`while byte_load(1)` on line four as the first unsupported construct.

Canonical C0.14 identities:

```text
b0.seed             52,600 bytes  3fd1a603c356fcd9fcad8b9c653d0b03044cfffb9c0cd8cc84751d17decd4719
c0.seed            215,029 bytes  20539eb5da2d715df4c801b5646a5f6be49e6a6c82dce571df4a4fdb36453b52
c0-successor.seed    3,165 bytes  ff37bdfef5782141a1ea37467756555086383414f2f6004d37060e93beb9c7d3
```

## C0.15 Contract

C0.15 extends the fixed dispatcher only for the complete 39-byte statement
measured by the C0.14 rebuild probe:

```text
while byte_load(1) {
byte_store(1,0)
}
```

An 80-byte matcher checks the first byte, preserves `RSI` and `RDI`, compares
the complete source sequence with `repe cmpsb`, and either advances back to
dispatch or reaches the shared invalid-source handler. The stack is balanced
on both paths. The accepted loop terminates after at most one iteration and
has no observable output in the successor subset, so successor lowering may
omit it. Other conditions, bodies, missing delimiters, and general or nested
loops remain unsupported.

The dispatcher is now 579 bytes. Its successful-return branch skips the new
tail, while its previous default branch reaches the loop matcher. The added
39-byte worst-case statement tightens the compile-time source bound from
`source <= 89` to `source <= 50`; `destination <= 252` is unchanged. Exact
`50/51` and `252/253` gates cover both edges.

The direct and successor parser artifacts are byte-identical at 1,029 bytes.
The successor source is 4,079 bytes and its executable is 3,371 bytes. Its
decoded literals require a bounded total-capacity increase from 1,536 to
2,048 bytes; the 255-byte per-literal bound and 4,096-byte source bound remain
unchanged. Exact 2,048/2,049 tests lock the literal boundary.

The C0.15 source is 136,042 bytes and therefore crosses B0.7l's old 131,072
byte input limit. B0.7m raises only predecessor `INPUT_CAP` to 196,608 bytes;
its output arena, byte-access patch table, grammar, and code generation remain
unchanged. The B0 gate accepts exactly 196,608 bytes and rejects byte 196,609.

The self-source probe now reaches `write` in the first loop body and still
exits 1 with the exact invalid-source diagnostic and no artifact. General
literal dispatch is the next measured blocker; C0.15 does not claim a general
parser or self-hosting.

Canonical C0.15 identities:

```text
b0.seed             52,600 bytes  3f54d9d1c0b9a09374444a19c15aad93700739951f65126f13024071d0004bba
c0.seed            224,279 bytes  da7f1647305da092a282937244786653aa845829db79d6b3d76dd7b4c60ae50e
c0-successor.seed    3,371 bytes  1aa777595cbeab0cb7ee7b1827f35921786f7a972ee67257bfd3c08781a97f95
```

## C0.16 Contract

C0.16 crosses the measured C0.15 `write` blocker without adding general
`write`, loop, or string grammar to the successor parser. The fixed dispatcher
recognizes the canonical successor's complete 477-byte first return-emitter
loop, covering source lines four through nine as one exact bounded construct.
The matcher refills at most 512 source bytes, compares the complete sequence
byte-for-byte, consumes it only on a full match, and reaches the shared invalid
source handler on every mismatch or read failure.

Parser metadata grows from four to five bytes. The fifth byte records that the
return-emitter construct was recognized, so the successor can select the exact
return artifact path without inferring state from partial input. The direct
parser fixture emits metadata `00 00 01 01 01` for the canonical prefix, while
an altered first ELF byte fails with status 1, exact `runtime: invalid source`
diagnostics, and no stdout bytes. The compile-time destination bound therefore
tightens from `<=252` to `<=251`; exact `251/252` gates lock the new edge.

The parser-bearing generated artifact is 1,625 bytes. It receives a private
1 KiB zero-file-size RW load at `0x402000`, while ordinary runtime artifacts
retain their 256-byte RW load at `0x401000`. Moving only parser-bearing memory
keeps the enlarged RX payload and RW mapping disjoint. All generated absolute
and RIP-relative byte-memory references follow the selected base.

Measured growth raises C0's source input bound from 4,096 to 8,192 bytes and
its total decoded-literal arena from 2,048 to 3,072 bytes; each individual
literal remains bounded to 255 bytes. Exact 8,192/8,193 and 3,072/3,073 gates
cover both limits. Successful compilation clears the source tail overlapping
sparse ELF storage before emission, so source bytes above offset 4,096 cannot
contaminate fields that must remain zero. Error paths still emit no artifact.

The resulting `compiler.nq` is 176,953 bytes and its generated artifact no
longer fits B0.7m's output and byte-access capacities. B0.7n raises only
`OUTPUT_CAP` from 262,144 to 393,216 bytes and `BYTE_ACCESS_CAP` from 2,560 to
3,072 entries. Its gates accept 393,212 output bytes and exactly 3,072 dynamic
byte accesses, then reject the next emission step and entry 3,073 without a
partial artifact. B0 grammar and code-generation semantics are unchanged.

The repeated self-source probe now consumes the entire first return-emitter
loop and stops cleanly at `while byte_load(3)` on line 10. It exits 1, emits
the exact invalid-source diagnostic, and produces no artifact. C0.16 therefore
proves one exact successor construct; it does not claim general parsing, a Full
Compiler, or self-hosting.

Canonical C0.16 identities:

```text
b0.seed             52,600 bytes  582068c5f2b32a769412727e08d7ad7ff5dd6fb57d276bb6f675a6496c380b75
c0.seed            298,359 bytes  5d7162abb44427216620b265e15429de0cf1b866b529d5ec89400d816845da77
c0-successor.seed    4,655 bytes  0be664dd95b57fce05757681cd742c6426ca0f53e9cd3fc18dd721849982280a
```

The canonical successor source is 5,088 bytes. The direct parser payload used
by the parity gate is 1,625 bytes with SHA-256
`4d8950c402b1ca51c489e56f82a82230959416c0749dcb248812f94e91e84d7b`.

## C0.17 Contract

C0.17 crosses the measured line-10 `while byte_load(3)` blocker by recognizing
the complete canonical parser-emitter loop. It keeps the proven C0.16
return-emitter matcher, then accepts the exact loop header, one or more
canonical `write("...")` lines, and the exact terminating clear tail:

```text
byte_store(3,0)
byte_store(2,0)
}
```

The matcher does not embed a recursive copy of its own artifact. It derives
the current executable's first RX `p_filesz`, decodes each source literal, and
compares every decoded byte against the running parser ELF at `0x400000`.
Canonical literals use raw printable bytes where safe plus `\0`, `\n`, `\r`,
`\t`, `\\`, `\"`, and lowercase `\xHH`; every non-final chunk decodes to
exactly 255 bytes. Missing input, malformed escapes, noncanonical spelling,
wrong chunk sizes, extra bytes, and any payload mismatch all reach the same
bounded invalid-source path.

Parser metadata grows from five to six bytes. The sixth byte records complete
parser-emitter recognition, so the compile-time destination bound tightens
from `<=251` to `<=250`; exact `250/251` gates lock this boundary. Parser
artifacts now receive an 8 KiB zero-file-size RW load at `0x402000`. Refill is
bounded to that mapping and EOF is required before the comparison succeeds.
Ordinary runtime artifacts retain their 256-byte RW mapping.

The direct parser artifact accepts a source containing its own canonical byte
payload, while a parser-emitter metadata fixture returns the sixth flag. A
single first-byte mutation from ELF magic `0x7f` to `0x7e` exits 1, emits no
stdout, and writes exactly `runtime: invalid source` to stderr. Direct C0 and
the promoted successor emit the same 2,238-byte parser artifact.

The larger C0 source requires B0.7o, which raises `INPUT_CAP` to 262,144 bytes
and `BYTE_ACCESS_CAP` to 4,096 entries while keeping `OUTPUT_CAP` at 393,216.
The repeated self-source probe now consumes the complete parser-emitter loop
and stops at `while byte_load(2)` on line 23. That measured next construct is
not accepted by C0.17; Full Compiler and self-hosting remain unimplemented.

Canonical C0.17 identities:

```text
b0.seed             52,600 bytes  6740118e4a386e0b56b42a7dc1bdd593f4fe74cf6c04788beca91ede6bd7351f
c0.seed            367,327 bytes  e4b62412d08d6ec7681c3ccb7719d0d88d193f4d1925606acb0b60cd2bf9a3d0
c0-successor.seed    5,973 bytes  c6c2da6e699ddeb5e18eec428e89f7c16b0dcbc679ac1d269e5747ecdca67f04
```

The canonical C0.17 source is 214,941 bytes and the successor source is 6,824
bytes. The direct parser payload has SHA-256
`921daf9d67935138f6904f5f274678fd9a710775ea3dee0c53f2070a1b9eb5eb`.

## C0.18 Contract

C0.18 crosses the measured line-23 `while byte_load(2)` blocker by recognizing
the complete canonical input-emitter loop. It retains both prior emitter
matchers, then accepts only this exact shape:

```text
while byte_load(2) {
write("<canonical input ELF bytes>")
byte_store(2,0)
output_write(0,1)
write("<constant ELF tail>")
}
```

The matcher validates every keyword, delimiter, newline, canonical literal
chunk, decoded ELF byte, clear store, output call, constant tail, and closing
brace. It is byte-exact rather than a general `while`, `write`, or output
grammar. A complete match records a seventh metadata byte; a partial match or
single altered payload byte exits 1 with `runtime: invalid source`, emits no
artifact, and never sets that flag.

The metadata layout is now:

```text
return | no-input | input | parser | return-emitter | parser-emitter | input-emitter
```

The destination bound tightens from `<=250` to `<=249`; exact `249/250` gates
lock it. Parser-bearing artifacts now receive a 16 KiB zero-file-size RW load
at `0x402000`, while ordinary runtime artifacts retain the 256-byte mapping at
`0x401000`. The source input bound is 9,984 bytes and the total decoded-literal
bound is 4,096 bytes, each with an exact one-byte overflow rejection.

The fixed parser dispatcher is 2,742 bytes. Direct C0 emits a 3,216-byte
parser artifact that accepts the complete 8,295-byte canonical successor
source twice with exit 0 and empty stdout/stderr. This proves complete parsing
of the bounded successor grammar. It does not prove self-hosting because the
parser artifact does not emit a replacement compiler.

The larger C0 source requires B0.7p, which raises `INPUT_CAP` to 327,680 bytes,
`OUTPUT_CAP` to 524,288 bytes, and `BYTE_ACCESS_CAP` to 5,120 entries without
changing B0 grammar or code-generation semantics.

Canonical C0.18 identities:

```text
b0.seed             52,600 bytes  6f8a829c1aba2159d00d0e5b2cddfe6f58cd6db83aac3587f5c79928225351d9
c0.seed            488,170 bytes  cf6f278ad1ea24c973b72717e8bba6dc5b2241e1c566a0cefb2a8b90d33ba91d
c0-successor.seed    8,113 bytes  902c2e184509abb112d5377baf957558aad04b98110864e9ba1e0bce7f7ee709
parser direct        3,216 bytes  836db9b7e711de4c33f36c8d295efe2eb7d3b945e511f0c1b74b267339804339
```

The canonical C0.18 source is 281,110 bytes. The successor source is 34 lines,
8,295 bytes, with SHA-256
`9c928c6b481e8897f2af381f5956790de123d976a12d875e7b73063a880b98e3`.
The next measured blocker is full compiler emission, not another source line.

## C0.19 Contract

C0.19 adds one bounded self-image path to the fixed `byte_parse_stmts`
dispatcher. It does not add general `write`, arbitrary loops, an ELF linker,
or the Full NolQu-L Compiler. The dedicated fixture marks a parser artifact
with `N` and `L` at byte-memory offsets 7 and 8. After the exact seven-byte
successor metadata is complete, the generated 229-byte machine routine blocks
`SIGPIPE`, reads the current RX `p_filesz` from ELF address `0x400060`, and
completely writes the current image beginning at `0x400000` to stdout. A
partial write is retried; an output failure exits 74 after the exact
`runtime: output_write failed` diagnostic. Unmarked or incomplete input keeps
the previous bounded parser behavior.

The canonical successor embeds that marked parser artifact. The direct
artifact built by C0 consumes the complete successor source and emits an
identical generation C; generation C consumes the same source and emits an
identical generation D. The three 3,459-byte images have the same SHA-256.
This is bounded self-image generation, not formal self-hosting: generation B
is compiled from a dedicated marker fixture, while the consumed successor is
an exact bounded construction source rather than the general compiler source.

Measured growth exposed two independent fixed-layout limits. The lexer token
bound is now 248 across the same six disjoint 256-byte tables. Runtime
operation records now have capacity 40 and use disjoint 40-byte kind,
argument, output-patch, and literal-patch regions at `10000..10319`. Exact
40/41 and 248/249 gates reject overflow without partial artifacts.

The 8,631-byte successor RX image also proved that the old parser BSS address
`0x402000` could shadow executable bytes once RX crossed 8 KiB. Parser-bearing
artifacts now map the same 16 KiB zero-file-size RW segment at `0x403000`;
ordinary runtime artifacts remain at `0x401000`. ELF gates calculate the RX
end and require it to be at or below the RW start.

Canonical C0.19 identities:

```text
b0.seed             52,600 bytes  6f8a829c1aba2159d00d0e5b2cddfe6f58cd6db83aac3587f5c79928225351d9
c0.seed            516,795 bytes  3b8959468cfdfb3ea7a11b498241f0d0e9b63f090d3102b48b53e8ecf9b2f0b7
c0-successor.seed    8,631 bytes  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct    3,459 bytes  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

The canonical C0.19 source is 296,992 bytes with SHA-256
`12806bae3275791a148f7c2c3da8c504bdc27eda9d3440d3b1adba31c097b5ab`.
The successor source is 35 lines and 8,919 bytes with SHA-256
`00ff07d5868c12fa0315469eed9966d6c8c835d6c54c1d56dfc0e12dde8536b2`.
The next measured blocker is general Full Compiler implementation.

## C0.20 Contract

C0.20 adds one general, bounded runtime primitive:

```text
byte_load_at(pointer_slot, destination)
```

Both operands are compile-time u8 memory offsets. At runtime the generated
program performs `memory[destination] = memory[memory[pointer_slot]]`. The
loaded pointer is itself one byte, so every effective address remains inside
the existing 256-byte runtime memory contract. Code generation is a fixed
20-byte x86_64 sequence: load the pointer byte, load through the selected
runtime BSS base, then store the result byte. No heap, host runtime, or hidden
bounds metadata is introduced.

The source-scan gate reads source bytes into memory at offset 32, advances a
pointer slot in a terminating loop, dynamically loads each byte, and writes it
back to stdout. Its output is byte-identical to the input, including the final
newline. A direct gate also proves an indirect read from offset 255, while an
out-of-range destination is rejected at its exact source location with no
artifact bytes. This is the first reusable source-traversal operation in C0;
it is not a lexer, parser, Full Compiler, or self-hosting claim.

Canonical C0.20 identities:

```text
b0.seed             52,600 bytes  6f8a829c1aba2159d00d0e5b2cddfe6f58cd6db83aac3587f5c79928225351d9
c0.seed            522,058 bytes  aa17cd154619ccf4ba8a20ef2984fa948ebca347e1bd774c45507b875c63593a
c0-successor.seed    8,631 bytes  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct    3,459 bytes  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

The canonical C0.20 source is 300,264 bytes with SHA-256
`84177febcf7e946e0b3230cdb1ae9bc2966ff59ecc6127981e626594e67838d5`.
The successor artifact remains byte-identical because its source does not use
the new primitive. C0.20 still fits B0.7p's 327,680-byte input, 524,288-byte
output, and 5,120-patch bounds, so B0 does not change. The next measured
blocker is indirect byte storage for source-driven token and patch tables.

## C0.21 Contract

C0.21 adds the matching bounded runtime mutation primitive:

```text
byte_store_at(pointer_slot, source_slot)
```

Both operands are compile-time u8 memory offsets. At runtime the generated
program performs `memory[memory[pointer_slot]] = memory[source_slot]`. The
pointer byte constrains the effective address to the existing 256-byte runtime
memory. Code generation is a fixed 20-byte x86_64 sequence: load the source
byte, load the pointer byte, then store through the selected runtime BSS base.
The sequence works with both the ordinary BSS at `0x401000` and parser BSS at
`0x403000`.

The direct gate writes through a pointer holding offset 255 and exits 91. The
source-table gate reads `NQL!` at offset 32, copies all four bytes through
runtime pointer slots into offset 160, and writes exactly `NQL!` to stdout. An
invalid source slot 256 is rejected at `input:2:22` with no artifact output.
Together with C0.20 indirect loading, C0 can now traverse and mutate bounded
source-driven tables; this is still not a lexer, Full Compiler, or self-hosting
claim.

Canonical C0.21 identities:

```text
b0.seed             52,600 bytes  4eea6da6f805d1bf07bb878bcde52e0b1d129899af25d839582d74fa4e030ad6
c0.seed            527,503 bytes  b6405b1ffd7f3581c07e831dfed54f009eaff92f18cde6a417ed1f1f19a91668
c0-successor.seed    8,631 bytes  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct    3,459 bytes  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

The canonical C0.21 source is 303,722 bytes with SHA-256
`430c44c95270801936edce7112dd180aa63373abcd818e9ff405c0b4b1b1d96c`.
Its 527,503-byte artifact exceeded B0.7p's output limit, so measured bridge
B0.7q raises only `OUTPUT_CAP` to 589,824 bytes; input and byte-access bounds
are unchanged. Sources that do not use the new primitive, including the
canonical successor, remain byte-identical. The next measured blocker is
source-driven tokenization using the now-proven indirect load/store pair.

## C0.22 Contract

C0.22 adds the canonical program `source_byte_tokenizer.nql`. It is compiled
by C0 itself and uses only the C0.21 runtime primitives; no tokenizer intrinsic
or host implementation is hidden in the compiler. The program reads at most
16 nonzero source bytes and emits a fixed 49-byte table:

```text
byte 0       token count
bytes 1..48  sixteen [kind, offset, length] records
```

This first layer deliberately defines `kind` as the original nonzero source
byte, `offset` as its zero-based source offset, and `length` as one. Unused
records are zero. It preserves whitespace and punctuation instead of claiming
identifier, number, keyword, or string recognition that is not implemented
yet.

Runtime memory is explicit and disjoint: source occupies `64..80`, scratch
slots occupy `0..5`, the count is copied to byte 127, and records occupy
`128..175`. A 17-byte read leaves the seventeenth byte at offset 80 solely as
an overflow guard. If it is nonzero, `byte_assert_range(80, 0, 0)` reaches the
shared `runtime: invalid source` path with exit 1 and no stdout. Empty, partial,
and exact 16-byte inputs terminate; no pointer can wrap before the bound.

Canonical C0.22 identities:

```text
compiler.nq              303,722 bytes  0a00c222f8d34a66f5c67994f0a13066a92898e0dd742e9d5349a3d811edf179
c0.seed                  527,503 bytes  b6405b1ffd7f3581c07e831dfed54f009eaff92f18cde6a417ed1f1f19a91668
source_byte_tokenizer.nql    688 bytes  ee19754193edf4064763eadb967cb71aa1e145ef75a9ae2018abd77305b62a4c
tokenizer artifact           900 bytes  85107865350e99c4181092960d4fb7e611f1011d4a4d66b173c678fd92ffd4ab
```

The compiler source changes only its milestone header, so B0.7q rebuilds the
same canonical `c0.seed` byte-for-byte. The tokenizer artifact is deterministic,
ELF64 x86_64, static, has no interpreter, and has a non-executable stack. The
next measured blocker is lexical token classification and coalescing while
retaining this bounded progress and record layout.

## C0.23 Contract

C0.23 adds `byte_classify_ascii(source_slot, destination)`. Both operands are
compile-time u8 memory offsets. At runtime, the primitive reads one source byte
and maps it to a stable lexical kind:

```text
1       whitespace: SP, TAB, LF, CR
4       identifier byte: A..Z, a..z, _
5       decimal digit: 0..9
10..20  ( ) { } ; + * - / = ,
```

All other ASCII bytes, DEL, and bytes `>=128` reach the shared
`runtime: invalid source` handler with exit 1. Destination memory is written
only after validation succeeds. The 170-byte x86_64 lowering consists of a
direct source load, non-ASCII guard, fixed 128-byte lookup table in RX memory,
zero-kind guard, destination store, and one patched `rel32` failure branch.

`source_byte_tokenizer.nql` now classifies each source byte before storing its
record. It preserves C0.22's 49-byte output shape and 16-byte source bound but
emits `[classified_kind, offset, 1]`. It does not yet coalesce adjacent
identifier/digit bytes or remove whitespace records.

Canonical C0.23 identities:

```text
compiler.nq              313,990 bytes  1b06384ef7a529f97d02f9f91d1792068c8596c9f88ebd5be78b4bb53a72ddd7
c0.seed                  545,270 bytes  263d818d5f6c79f6bb2eeb259e3df5e46b004077f8437041c103a1b4e7f48fd8
source_byte_tokenizer.nql    743 bytes  e8204b27f1149330cb7624e6a29532f36427e12f7171ccb2e269996b0b6b3eb8
tokenizer artifact         1,077 bytes  d658dc3cfe5eb944aa5912f528892a5b1fde271be33f8be23c8d74ca1d0833cf
c0-successor.seed           8,631 bytes  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
```

The compiler source and artifact remain below B0.7q's 327,680-byte input and
589,824-byte output bounds, so no predecessor capacity changes are required.
The next measured blocker is lexical token coalescing and whitespace elision.

## C0.24 Contract

C0.24 adds `byte_token_push(kind_slot, offset_slot, table_base)`. All operands
are compile-time u8 memory offsets. The table is one count byte followed by at
most sixteen fixed `[kind, offset, length]` records. Its 49-byte footprint
requires `table_base <= 207`.

At runtime, kind 1 whitespace is elided. Kind 4 identifier bytes coalesce with
a contiguous identifier token. Kind 5 decimal bytes coalesce with a contiguous
identifier or integer token, so `a12` is one identifier while `12a` is an
integer followed by an identifier. Punctuation kinds 10..20 remain one-byte
tokens. A seventeenth token, a wrapping length, an invalid kind, or a broken
table bound reaches the shared exact invalid-source handler before stdout is
written. The x86_64 lowering is a fixed 162 bytes.

An initial lowering used `3 * (count - 1)` as an address relative to the table
base and therefore read the count header instead of the previous record kind.
The corrected previous-kind offset is `3 * count - 2`. Regression gates cover
identifier, integer, mixed-boundary, whitespace, punctuation, exact-capacity,
and overflow behavior.

C0.24 requires 5,166 byte-access patches, above B0.7q's 5,120 limit. B0.7r
raises only that cap to 5,376, with exact and one-step-overflow gates; its
327,680-byte input and 589,824-byte output bounds remain unchanged.

Canonical C0.24 identities:

```text
compiler.nq              327,359 bytes  d464e590875adbf66ce2973106504e0c7403a0ce1806bf4b80d189129f39f00b
c0.seed                  568,889 bytes  c2b6d8138867123861eac0a34eaebfda2d44633d097f44329ac6a612edd30745
source_byte_tokenizer.nql    427 bytes  39e90287b6a592b257c977dba8413c1ac965547d41c5025b9290b92fcd0ab5f5
tokenizer artifact         1,083 bytes  132372400176567973f1f288e3ebbf8fd872abc6e65fbc08b1612c88ca03908f
c0-successor.seed           8,631 bytes  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
self-image direct           3,459 bytes  5815f13b16eb9ea824c57ad2c8df983cff03454d0a86b442b442d452b402bc53
```

The next measured blocker is a source-driven parser over these coalesced,
located tokens. Full Compiler and self-hosting claims remain unimplemented.

## C0.25 Contract

C0.25 adds `source_token_parser.nql`, a parser compiled by C0 and composed
entirely from the existing byte-memory, indirect-load, assertion, loop, and
output operations. It adds no source-visible machine primitive. The parser
consumes the fixed 49-byte coalesced-token table from C0.24 and recognizes:

```text
expression := primary (binary-operator primary)*
primary := identifier | decimal-integer
binary-operator := + | * | - | /
```

The grammar accepts one through fifteen meaningful tokens within the existing
sixteen-token lexical bound. Each iteration consumes exactly one operator and
one following primary. An even token count is rejected before subtraction can
wrap, so malformed input cannot turn into a nonterminating loop. Empty input,
leading/trailing operators, adjacent primaries/operators, unsupported
punctuation, invalid counts, and malformed consumed records all reach the
shared `runtime: invalid source` path with exit 1 and no stdout.

Successful output is 53 bytes:

```text
bytes 0..48  original [count, kind/offset/length records]
byte 49      root-node count (1)
byte 50      node kind (1 = flat infix expression)
byte 51      first token index (0)
byte 52      expression token count
```

The original records are retained byte-for-byte, so every leaf still carries
its lexical source location. This is deliberately a flat expression CST
root, not yet a precedence tree. Precedence-aware nodes, grouping, statements,
keyword resolution, and function/module grammar remain the measured next
parser work before Full Compiler emission can begin.

The parser source exposed a structural C0 limit: the old compiler stopped at
source token 249 while compiling it. C0.25 therefore widens all six internal
token tables from 256 to 512 bytes and raises the checked source-token bound
from 248 to 512. Their disjoint layout is now:

```text
kind       16000..16511
value      16512..17023
start low  17024..17535
start high 17536..18047
length low 18048..18559
length high18560..19071
```

The 4,096-byte decoded-literal arena moves from 18,000 to 20,000, remaining
disjoint through byte 24,095. The runtime operation cap remains 40 and the
9,984-byte source bound is unchanged. Exact gates accept a valid 512-token
program and reject token 513 at `input:1:524` without artifact bytes.

Canonical C0.25 identities:

```text
b0.seed                    52,600 bytes  7b71089df23551ea55444f132834046cc619a93cf45ad78f285d64d615ce495c
compiler.nq               327,359 bytes  1b75e7eb24ac27e5ff401efe5a67544b2deb7def2c4438e12f35ff28e99e813b
c0.seed                    568,889 bytes  312fc0cab67b4c366cc7f5f17546619926654bdb326afcbe7bfb1c310a70266b
source_token_parser.nql      1,356 bytes  f8f44089cc28d61847105f4cb267fcf92e23d2e430a8878137d278f8f85ffa8f
parser artifact              1,360 bytes  f03e85e4966b2439f3fbeccd22bc1b57c0dd7feaa1638bb76ce7ebc6bc4fc357
source-byte tokenizer        1,083 bytes  132372400176567973f1f288e3ebbf8fd872abc6e65fbc08b1612c88ca03908f
c0-successor.seed             8,631 bytes  477210ca214ecb05e49506124a65d9ade786ad35188eec6ea53d05377340509b
```

The predecessor, tokenizer artifact, successor, and bounded generations stay
byte-identical. Only C0's internal table layout and canonical C0 identity
change. Full Compiler, formal self-hosting, and verified `nqlc` remain
unimplemented.

## Reproducible Build

The canonical transition is:

```text
stage0.seed -> b0.seed -> c0.seed -> c0-successor.seed
```

Rebuild and verify C0 with:

```text
bootstrap/compiler/c0/x86_64-linux/materialize.sh
bootstrap/compiler/c0/x86_64-linux/materialize-successor.sh
```

The materializer invokes only canonical `b0.seed`, verifies `c0.sha256`, writes
through a temporary file, and renames only after success. On non-x86_64 test
hosts, `qemu-x86_64` is an explicit execution adapter; it is not a compiler
stage.

For a source path and atomic output path, use:

```text
bootstrap/compiler/c0/x86_64-linux/compile.sh input.nq output
```

This adapter verifies the canonical C0 hash before execution, rejects directory
targets, preserves an existing output when compilation fails, and removes its
temporary file on normal and signal exits.

## Evidence

`tests/bootstrap/core_compiler_c0.sh` and
`tests/bootstrap/c0_source_byte_tokenizer.sh` prove:

- B0 builds bytes identical to canonical `c0.seed`;
- predecessor builds and materializations are deterministic;
- the canonical hash matches;
- C0 and its output are standalone ELF64 x86_64 artifacts;
- return 7 and return 23 compile to different artifacts and execute correctly;
- addition chains and multiplication-before-addition lower deterministically;
- multiple local declarations, dependency chains, and local expressions lower
  deterministically;
- duplicate/unknown locals, malformed `let`, and the eight-local bound are
  diagnosed at the exact source location without artifact output;
- string escapes including `\0`, binary NUL output, multiple writes, exact
  static artifact hashes, the 255-byte per-literal bound, and the 4,096-byte total literal
  bound are verified byte-for-byte;
- runtime input at a nonzero memory offset, EOF, closed-fd and broken-pipe exit
  74, exact diagnostic bytes, byte store at index 255, load semantics,
  deterministic output, and range rejection are verified;
- `byte_load_at` dereferences a runtime pointer byte, reaches memory offset
  255, scans valid source in a terminating loop, preserves source bytes through
  redirected stdout, and rejects an out-of-range destination without output;
- `byte_store_at` stores through a runtime pointer byte, reaches memory offset
  255, copies a source table byte-for-byte through runtime pointers, and
  rejects an out-of-range source slot at its exact location without output;
- `source_byte_tokenizer.nql` compiles deterministically under C0, emits a
  count plus sixteen exact `[kind, offset, length]` records for empty, partial,
  and full input, elides whitespace, coalesces contiguous identifier/integer
  runs, keeps digit-after-identifier semantics and punctuation boundaries,
  rejects unmapped and non-ASCII bytes, and rejects both a seventeenth source
  byte and a seventeenth output token without output;
- `byte_assert_range` accepts and rejects u8 input deterministically, handles
  the upper bound 255 correctly, validates reversed bounds at compile time,
  emits an exact stderr diagnostic, and exits 1 even when stderr is closed;
- `byte_parse_u8` accepts every covered one/two/three-digit form, preserves
  leading-zero semantics, rejects overflow and malformed termination, checks
  its compile-time memory bound, and emits deterministic machine code;
- `byte_parse_u8_then` enforces a compile-time terminator before LF/EOF,
  accepts the same full-u8 spelling set, rejects malformed suffixes and its
  tighter source bound, and emits the audited fixed decoder deterministically;
- `byte_parse_stmts` dispatches zero to three exact dead `byte_store` lines,
  one optional exact `input_read(32,96)`, one dependent exact
  `byte_parse_stmts(32,0)`, at most two dead post-parser `byte_store` lines,
  exact terminating clear loops, the complete first return-emitter construct,
  the complete parser-emitter and input-emitter constructs, and a final
  return-u8; its seven-byte metadata, exact `50/51` source and `249/250`
  destination bounds, duplicate/order, malformed-loop, and altered-emitter
  rejection, plus the audited fixed decoder are verified deterministically;
- dynamic byte copy and modulo-256 subtraction lower to frozen deterministic
  artifacts; taken and zero-iteration loops execute correctly, while a nested
  loop fails at its exact source location without artifact bytes;
- dynamic output round-trips binary input, preserves operation order inside a
  loop, handles zero-length writes, and lowers to frozen deterministic
  artifacts with a real complete-write loop;
- closed stdout, a proven broken pipe, and unavailable diagnostic output all
  exit 74; valid failures emit the exact output diagnostic and invalid ranges
  fail at their exact source location without artifact bytes;
- long valid operation streams retain all 40 operation records, reject record
  41, and an output operation after eighteen input operations still reaches its
  patched exit-74 handler instead of corrupting metadata or hanging;
- runtime ELF output has exactly one RX load and a non-overlapping
  zero-file-size RW BSS load: 256 bytes at `0x401000` for ordinary runtime
  artifacts or 16 KiB at `0x403000` for parser-bearing artifacts; neither form
  has an RWX load and both retain a non-executable stack;
- literal writes and runtime operations execute in exact source order,
  including an empty-literal no-op, and literal write failures reach the
  shared exit-74 handler; arithmetic around dynamic byte load remains rejected
  without artifact bytes;
- C0 builds the canonical successor twice identically, and that successor
  consumes exact function-envelope return programs across 0..255,
  emits distinct deterministic standalone artifacts matching direct C0
  outputs, eliminates bounded unobservable stores, emits an input-read artifact
  byte-identical to direct C0, preserves its exit-74 closed-fd diagnostic,
  rejects the covered malformed textual forms without artifact bytes, handles
  closed stdout, emits the 3,459-byte marked parser artifact selected by C0,
  accepts two unobservable post-parser stores without changing that artifact,
  preserves return/input/parser bytes after splitting the dynamic return byte
  from the constant ELF tail, accepts the exact clear-loop and complete first
  return-emitter, parser-emitter, and input-emitter constructs without changing
  target bytes, and bounded generations B, C, and D are byte-identical on the
  canonical successor source;
- all six 512-byte token tables remain disjoint through the exact 512-token
  bound, including a valid high-offset token stream that reproduced the former
  overlap; token 513 is rejected at its source location without output;
- `source_token_parser.nql` is built deterministically by C0, accepts bounded
  identifier/integer infix chains, preserves all lexical records and locations,
  emits one flat CST root, and rejects malformed or non-progressing streams
  without partial stdout;
- malformed and out-of-range input produce no stdout artifact;
- token-internal whitespace is rejected rather than silently normalized;
- diagnostics carry the actual line and column, including three/four digit
  positions;
- the 9,984-byte source, token, literal, multiplication, and additive u8 bounds
  fail without an artifact;
- source tails above byte 4,096 are cleared before sparse ELF emission and
  cannot corrupt zero-filled target fields;
- diagnostics are byte-exact on stderr;
- failed atomic compilation preserves old output and leaves no temp file;
- materialization and path compilation reject directory targets;
- path compilation refuses a modified C0 seed before creating output;
- no host-language compiler source exists in the C0 stage.

## Historical C0.25 Next Direction

The following is the C0.25 checkpoint, not the current implementation gap.
C0.26..31 completed the parser, functions, byte/stream runtime, capacity and
component-generation work above. C0.32's current scope and remaining acceptance
are in [NATIVE_OS.md](NATIVE_OS.md); full types/modules/toolchain migration remain.

C0.25 proves the first source-driven parser over coalesced, located lexical
records while preserving C0.19's bounded generations byte-for-byte. The next
work unit must replace the flat expression root with precedence-aware nodes and
add bounded statement/function grammar with keyword resolution, strict bounds,
located failure, and guaranteed progress. Source-driven Full Compiler emission
can begin only after that parser contract is executable and independently
verified. Full NolQu-L, formal self-hosting, and verified self-hosting remain
separate unimplemented milestones.
