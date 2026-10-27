# Bootstrap Tests

These tests verify the canonical NolQu-L bootstrap chain independently from
Reference Compiler R0 and the frozen LLVM/Python compatibility paths.

Current coverage:

- deterministic reconstruction of the x86_64 Linux `hex0.seed`
- atomic preservation of existing output on parse and hash failures
- byte-for-byte self-decoding from `hex0.hex`
- executable ELF identity and non-executable stack metadata
- lowercase, uppercase, whitespace, comments, pipe, redirect, and binary data
- explicit non-zero failures for malformed input and syscall failures
- Stage 0 reconstruction directly through `hex0.seed`
- Stage 0 self-reconstruction and optional assembly audit parity
- deterministic raw-byte, `rel32`, image-address, and file-offset emission
- generation and execution of a static ELF with control flow and memory access
- bounded Stage 0 inputs, output, symbols, syscall errors, and resource cleanup
- B0 bootstrap compiler promotion with manifest evidence
- B0 semantic lowering for non-canonical return literals and dynamic write
  strings, including a real 2,048-byte decoded-string limit
- B0 semantic machine-code lowering for bounded locals, precedence-aware
  integer expressions, comparisons, computed division-by-zero detection, and
  signed-division-overflow rejection plus deterministic true/false `if/else`
  control flow
- B0 local assignment and simple `while` lowering with a real backward
  `rel32`, zero-iteration and sequential-loop behavior, multiple mutated
  locals, constant-metadata invalidation, source-located unknown-target
  diagnostics, bounded runtime execution, and deterministic branch bytes
- B0 zero-initialized 64 KiB byte-memory with dynamic `byte_load`/`byte_store`,
  low-byte store plus zero-extended load semantics, maximum-index/local-frame
  separation, call-position intrinsic resolution, deterministic load/store
  bounds patches to one shared handler, source-located constant bounds errors,
  malformed-call diagnostics, and runtime stderr plus exit 70
- B0 bounded `input_read`/`output_write` stream I/O over fd 0/1, including
  binary byte parity, nonzero offsets, deterministic output, static/dynamic
  and negative range failures, full-region boundaries, nested-call metadata,
  multiple output patches, malformed calls, closed-fd diagnostics, and
  `SIGPIPE`-safe broken-pipe handling with exit 74
- B0 bounded `error_write` diagnostic output over fd 2, including complete
  full-range writes, constant bounds rejection, and direct exit 74 when stderr
  itself cannot be written
- B0.7g bounded 1,024-entry byte-access patch capacity required by C0.3a,
  B0.7h bounded 131,072-byte generated-output arena required by C0.3b, and
  B0.7i bounded 2,048-entry byte-access capacity required by C0.3c, including
  exact 2,048-patch execution, rejected patch 2,049, accepted 131,060-byte
  output, and rejected next-step output overflow
- B0.7j bounded 131,072-byte source arena required by C0.4, including a valid
  source above the former limit and explicit `B0-IO-003` rejection at byte
  131,073 without an output artifact
- B0.7k bounded 196,608-byte generated-output arena required by C0.7,
  including accepted 196,598-byte output and explicit rejection of the next
  18-byte emission step without a partial artifact
- B0.7l bounded 2,560-entry byte-access patch table and 262,144-byte output
  arena required by C0.10, including exact-capacity execution and one-step
  overflow rejection without a partial artifact
- B0.7m bounded 196,608-byte source arena required by C0.15, including exact
  capacity execution and explicit `B0-IO-003` rejection at byte 196,609
- B0.7n through B0.7r measured capacity bridges, ending at a 327,680-byte
  source arena, 589,824-byte output arena, and 5,376 byte-access patches. The
  output gate accepts the highest fixture-representable artifact at 589,808
  bytes and rejects the next 18-byte step; the patch gate accepts exactly
  5,376 accesses and rejects 5,377, with no B0 grammar growth
- C0.25 predecessor build, canonical hashes, deterministic materialization,
  standalone ELF metadata, real source locations, checked u8 expressions,
  bounded locals and strings, byte memory, input/output, exact nested-loop
  rejection, complete-write and `SIGPIPE` failure paths, and byte-exact
  diagnostics
- C0.25 fixed limits and layout: 9,984 source bytes, 512 tokens across six
  disjoint 512-byte tables, 4,096 decoded-literal bytes at `20000..24095`, 40
  disjoint operation records,
  seven parser metadata bytes, exact `50/51` parser-source and `249/250`
  destination gates, and a 16 KiB parser RW segment at `0x403000` proven
  disjoint from RX
- indirect byte loading through a runtime pointer slot, including offset 255,
  deterministic source scanning, exact redirected stdout bytes, and located
  rejection of an out-of-range destination without a partial artifact
- indirect byte storage through a runtime pointer slot, including offset 255,
  exact `NQL!` source-table copying, and located rejection of an out-of-range
  source slot without a partial artifact
- canonical `source_byte_tokenizer.nql` compilation, exact empty/partial/full
  count plus sixteen `[kind, offset, length]` records, deterministic 1,077-byte
  C0.23 artifact history followed by deterministic 1,083-byte C0.24 artifact
  identity, stable ASCII lexical classes, whitespace elision, contiguous
  identifier/integer coalescing, mixed token boundaries, punctuation, rejection
  of unmapped/non-ASCII bytes, and explicit source/token capacity rejection
- canonical `source_token_parser.nql` compilation and deterministic identity;
  byte-exact preservation of the 49-byte lexical table plus one flat CST root;
  valid primary/operator chains; and atomic rejection of empty, malformed,
  unsupported, out-of-range, or non-progressing records in complete token tables
- C0.26 `frontend.nql` built directly by B0, pinned deterministic identity,
  versioned NQAF AST decoding and reachability, all operator-pair precedence
  and associativity combinations, groups, statements, long names, 24 bindings,
  exact 8192-byte/512-token boundaries, malformed input/truncation, byte-at-a-time
  input, I/O errors, and concurrent/failed atomic materialization
- C0.27 `backend.nql` built directly by B0, deterministic pinned ELF, NQAF
  framing/shape/ownership and statement-local ordered-postorder validation,
  rejection of cross-statement hoisting and reversed subtree evaluation,
  exact local resolution and i64 bounds,
  checked runtime arithmetic and diagnostics, operator-pair runtime oracle,
  126 declarations at the token bound, truncated/mutated ASTs, short reads,
  partial-output EPIPE, closed descriptors, and atomic source compilation
- backend materializer fault injection: concurrent publication, compile/hash
  failure, protected output aliases, rename failure, SIGTERM at publication,
  unchanged previous artifact and temporary cleanup
- C0.28 structured control flow: signed comparisons and precedence, nested
  branches/loops, condition reevaluation, block scopes and shadowing, early
  returns, unselected faulting branches, delimiter corruption, independent
  backend 64/65-depth checks, wide binding IDs, deterministic runtime corpus,
  and byte-identical scalar AST/ELF predecessor outputs
- C0.29 named functions, forward/nested/recursive calls, zero through six
  mutable parameters, exact long-callee lookup, argument evaluation order,
  independent AST envelope/arity checks and the 64-frame runtime depth bound
- C0.30 call statements with exact physical links and single ownership, NQAF/4
  validation, intrinsic arity and user-function shadowing, shared 65536-byte
  byte arena, overflow-safe ranges, empty ranges without syscalls, binary streams,
  short reads and EOF, redirects, failed descriptors, source-located runtime
  diagnostics and predecessor AST/ELF byte fingerprints
- exact return-, parser-, and input-emitter recognition plus the marked
  229-byte self-image routine; generations B, C, and D are byte-identical,
  malformed input emits no artifact, closed stdout exits 74, and the evidence
  remains explicitly bounded rather than claiming Full Compiler self-hosting
- successor parity, seed hash enforcement, directory-target rejection,
  temporary cleanup, and atomic output preservation

Run with `make bootstrap-test`.

The runner also retains all earlier gates and invokes `c0_capacity.sh`. In a
coherent provisional or promoted installation this runs 18 frontend-capacity,
28 backend-capacity, 20 compiler-profile and 6 generation/integrity methods.
It emits `PASS c0-capacity` and `PASS c0-component-generations` only after the
corresponding suites complete. The first marker alone is partial proof. Do not
add these embedded unittest counts to shell PASS counts a second time; compare
the prior gate-name multiset and document the two additional markers.

MCP component probes execute fresh real gates and validate complete generation
receipts, exact required check/oracle sets, raw statuses and before/after input
and artifact hashes. Their bounded-output display is not a proof transport.
No partial receipt, version label or ok-only mock establishes capacity. The
official seed set remains unpromoted until controller verification/review and a
separate coherent-promotion authorization. See the C0 CAPACITY contract.

The isolated frontend gate is `bash tests/bootstrap/c0_frontend.sh`. Its Python
oracle only inspects ASTs and tests processes; it never builds a compiler.
The corresponding backend gate is `bash tests/bootstrap/c0_backend.sh`; its
Python oracle only checks ASTs, generated machine behavior and failure paths.
The retained C0.25 helper does not check short-input framing. Its proof scope
is deliberately narrower than the complete-source C0.26 frontend gate.
