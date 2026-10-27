# State Of Project

Current metadata (2026-10-27): `1.0.0-alpha.1`, channel `dev`, by maintainer
request for `NolQuDev/NolQu-L`. Older version strings in checkpoint evidence
below describe those historical runs; no release or bootstrap promotion occurs.

## NolQu-L Today

NolQu-L now has two deliberately separate implementation tracks:

- a canonical machine bootstrap beginning at raw x86_64 Linux ELF bytes
- Reference Compiler R0, the existing NASM implementation used for current
  programs and semantic regression coverage

LLVM and Python tooling is retained only as frozen legacy/reference tooling.

## Canonical Bootstrap Status

- Machine-Level Foundation: `PASS`
- Stage 0: `PASS`
- Bootstrap Compiler B0: `PASS`
- Core Compiler C0.25 source-driven bounded expression parser: `PASS`
- C0.31 capacity/access foundation: completed and verified within its original scope
- C0.32 source frontend (B0-built, NQAF/1..6): scoped/generation tests pass, experimental
- C0.32 AST backend (checked ELF/native argv/syscalls): scoped/generation tests pass, experimental
- C0.32 post-formatter baseline: `PASS`, 1079 markers; observed host-helper revision: `PASS`, 1080 markers, every baseline label retained
- Current C0.32 canonical/MCP/public/assurance execution: `PASS` within the
  [current reliability scope](VALIDATION.md); MCP 124, fresh proof 722/275,
  17 host evidence controls, 16 actual adapter comparisons, unchanged runner 11 baseline,
  and 594 assurance invocations; host retention is experimental
- Stable/security readiness: `PARTIAL / BELUM SIAP`; earlier comparison-backend
  SIGKILL remains `OPEN`, not explained by later passing runs
- Full canonical compiler: `NOT_IMPLEMENTED`
- Self-Hosting `nqlc`: `NOT_IMPLEMENTED`
- Verified `nqlc`: `NOT_IMPLEMENTED`

The machine seed, Stage 0, B0, and C0 artifacts are deterministic,
hash-verified, static x86_64 ELF artifacts. C0.19 proves byte-identical bounded
generations B, C, and D; C0.20 adds reusable indirect byte loading and a
terminating byte-exact source scan; C0.21 adds indirect byte storage and
byte-exact source-table copying; C0.22 composes both into a deterministic
count plus sixteen `[kind, offset, length]` byte records; C0.23 maps those
records to stable whitespace, identifier, decimal, and punctuation kinds;
C0.24 elides whitespace and coalesces contiguous identifier/integer runs while
preserving punctuation and a strict token bound; C0.25 consumes those records,
validates bounded infix expression structure with guaranteed progress, retains
source locations, and emits one flat CST root. C0.25 also raises the internal
compiler token capacity from 248 to an exact, tested 512-token bound.
These remain bounded foundation proofs and do not yet emit a replacement full
compiler from canonical compiler source.

C0.26 adds a separate `frontend.nql` component built by the existing B0. It
reads complete source streams and constructs real precedence/associativity
trees for `+ - * /`, nested groups, arbitrary-length ASCII identifiers, `let`,
assignment and a final `return` inside `fn main()`. The NQAF/1 output includes
exact source bytes and a flat 16-byte node table with lexical anchors and
statement links. Bounds are 8192 source bytes, 512 tokens and 512 nodes. This
does not change the C0.25 emitter artifact or expand its runtime intrinsics.

C0.27 connects that AST to a separate B0-built `backend.nql`: complete-stream
and graph validation, exact local resolution, signed i64 literals, mutable
bindings and runtime checked arithmetic. It emits deterministic x86_64 ELF
directly, without a host assembler/linker/LLVM, and identifies failing source
operations. The experimental source wrapper atomically publishes only after
both components succeed. At that milestone neither component could compile its
own source; C0.31's component generations below supersede that limitation.

C0.28 extends both components with signed comparisons, nested `if/else` and
`while`, lexical scopes/shadowing, and block-final returns. NQAF/2 records
explicit block delimiters; the backend checks a bounded nesting stack before
resolution and direct branch fixups. Bounds remain 8192 source bytes and 512
tokens/nodes, with at most 64 nested control bodies. The existing scalar
NQAF/1 path is retained. See `bootstrap/compiler/c0/CONTROL_FLOW.md`.

C0.29 adds named i64 functions with zero through six mutable parameters,
forward/nested/recursive calls, separate function-local scopes, and left-to-right
argument evaluation. NQAF/3 validates envelopes and argument ownership before
direct rel32 call emission. Each function reserves a 4096-byte aligned frame;
more than 64 active functions produces a source-located depth diagnostic.
NQAF/1 and NQAF/2 bytes are preserved. See `bootstrap/compiler/c0/FUNCTIONS.md`.

C0.30 adds call statements (NQAF/4) and five runtime intrinsics: `byte_load`,
`byte_store`, `input_read`, `output_write` and `error_write`. Intrinsics share a
zero-initialized 65536-byte stack arena, disjoint from function frames, and check
all indices and ranges before accessing memory. Read returns a short count or
EOF; writes complete the requested range. User functions still shadow intrinsic
names. Bounds faults exit 70 with a source location; I/O faults exit 74. No heap,
opened descriptors, libc or host linker is introduced. See
`bootstrap/compiler/c0/RUNTIME_IO.md` for the ABI, diagnostics and regression gates.

At the completed C0.31 checkpoint, source/token/node capacity rose to
262144/65536/65536, with checked u32
NQAF/5 storage, separates native frame slots from global node IDs, and carries
the compiler's 16 MiB RW/NX profile explicitly. Default programs retain 64 KiB.
Both complete current sources (63904/165737 bytes) compile through B0 -> A -> B
-> C; B/C frontend and backend pairs are individually byte-identical. Fresh
preinstallation gates pass, including 1076 main gates, 46 MCP tests, the real
215-check generation proof and preserved predecessor behavior. The reviewed
B0/frontend/backend seeds and pins are installed coherently; the exact final
postinstallation run passed the same eight commands without timeout or skip. See
[`CAPACITY.md`](../../bootstrap/compiler/c0/CAPACITY.md). This is component
generation, not Full Compiler or full self-hosting. The additive toolchain access
implementation now exposes these same components through public `nqlc`, project
`nql`, installation and MCP with explicit `--backend canonical`. The default
remains `nasm`/R0. This access work has its own final integration gates; the
historical capacity results above are not a claim that those gates have run.

## Current Native Capability — C0.32

C0.32 adds lexical `unsafe` blocks with a required nonempty invariant, native
`arg_count`/`arg_copy`, unsafe checked `byte_address` and raw `syscall6` to the
source frontend/direct-ELF backend. NQAF/6 dialect5 adds matching scope markers;
the backend independently validates both AST ownership and actual source
containment. Old successful /1..5 bytes remain covered. Checked pointer exposure
is not a syscall-specific lifetime/ownership proof or full NolQu-L Safety.

The actual [native file reader](../../examples/canonical/README.md) obtains
argv, opens literal filenames, streams binary bytes and handles interrupted/
partial read/write and single-close fd ownership in NolQu-L source. It removes
a concrete prerequisite for native tooling. It does not replace CLI/MCP/testing
or supply general types, modules, FFI or the Full Compiler.

Scoped evidence: native frontend 6 plus old 40 methods, runtime 6 plus backend/
legacy 123, native-program 5 plus old Guest 30. These groups overlap, so their
counts are not added as unique tests. Independent Task1 fix/Task2 reviews
approved their own implementation scope. The actual generation module passed
six methods in 648.759s, with 722 stages/275 checks/475 artifacts, six comparisons
and 41 named oracle methods per B/C pair. Public compilation of both complete
sources matches the new B/C bytes; four new public methods and canonical-only
relocation passed. See [CAPACITY.md](../../bootstrap/compiler/c0/CAPACITY.md)
for measured C0.32 identities and retained separate C0.31 hashes.

Combined relocated installation also passed its scoped rerun after the normal
legacy compiler build prerequisite; its precondition failure remains recorded
in the toolchain guide. The original native checkpoint passed 1079 main markers;
all 1078 earlier labels remained. The reliability continuation now passes 1080
markers, retaining all 1079 baseline labels; MCP 124, fresh installed combined proof,
594 assurance invocations and nine release checks pass on the host-helper revision.
Exact public protocol schemas are unchanged. An earlier comparison-backend
SIGKILL is unresolved; no stable/security promotion is justified by the later
pass. See the [session report](VALIDATION.md) and
[assurance profile](../../tests/security/README.md). Target execution uses QEMU
on this aarch64 host. This is an experimental engineering checkpoint, not a new release or
claim of hardware-native/full-language verification. VERSION1.0.2a1/CHANNELdev
are unchanged. [NATIVE_OS.md](../../bootstrap/compiler/c0/NATIVE_OS.md) defines
the exact current contract and its safety/verification limits.

## What Is Strong Now

- Reference Compiler R0 has broad regression coverage
- the canonical trust root is small and auditable
- bootstrap status is explicit and machine-verifiable
- C0 can consume source, mutate source-driven tables, emit bounded byte-token
  records, and parse a bounded expression stream through explicit runtime
  memory
- the old compiler remains usable while the new chain is built

## Main Architectural Debt

- The active AST backend has one scalar type and one compilation unit. Modules
  and the Full Compiler remain missing; public CLI/project/MCP access to the
  experimental C0.32 subset is implemented, with capacity and explicit byte/stream/native
  profiles bounded as above
- C0.25's older 49-byte token-table helper assumes complete tokenizer output;
  it does not validate short input framing and is not the new source frontend
- C0 does not yet emit a Full Compiler from canonical compiler source
- bounded self-image generations are not formal `nqlc` self-hosting

## Current Direction

Use the tested [canonical toolchain access](../compiler/CANONICAL_TOOLCHAIN.md)
as the foundation for full NolQu-L toolchain migration. The coherent C0.32
source/seed/pin/proof set is already installed in the isolated worktree. Preserve
that set while resolving the unexplained comparison-backend SIGKILL and the
remaining stable/security qualification gaps. The former 8192-byte/u16 blocker
was resolved by C0.31; current frontend/backend sources measure80300/199908 bytes
and17900/47114 tokens,
producing 15739/40939 nodes through u32 NQAF/5. Both fit the unchanged
262144-byte, 65536-token/node bounds and have byte-identical B/C component
generations. Default programs keep
64 KiB byte storage; the explicit compiler profile maps 16 MiB RW/NX. These
component facts do not establish a general-purpose type/module system or Full
Compiler. Preserve the B0-built boundary and existing C0.25 emitter gates. R0
remains the compatibility oracle; LLVM parity growth is no longer a project
objective. Full Compiler, self-hosting and Verified status remain false.

## Completed C0.31 Access Checkpoint — 2026-10-24

This is retained verification of the preceding source/pin set, not a complete
regression result for changed C0.32 inputs.

The access implementation kept the C0.31 subset experimental and opt-in.
Project build supplies a validated cache; canonical run recompiles via
`nqlc --run` even after a cache hit. Completed technical verification covers all 1076 original main markers plus
both new suite markers (1078 total), 33 CLI and 30 project methods including
relocated installation, 112 current MCP methods, nine release checks and seven
bootstrap hashes. A fresh combined C0 probe passes capacity/profile/component
generation and cleanup checks. Public CLI builds of both complete compiler
sources match the retained C0.31 artifacts byte for byte; the stream example
passes independent binary-input oracles. The guide records the exact scope of
main evidence retained across the isolated MCP audit repair.

LLVM remains legacy compatibility infrastructure. Python MCP/testing and shell
orchestration are explicit remaining dependencies, not a completed migration.
The long-term target remains a full NolQu-L toolchain without Python or LLVM;
replace those components with real verified NolQu-L implementations as compiler
capabilities permit. The canonical compiler already emits ELF directly without
host compiler/source-transformation semantics.
