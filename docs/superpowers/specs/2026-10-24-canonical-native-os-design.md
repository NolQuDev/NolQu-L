# Canonical Native OS Interface

Status: controller-selected under the user's delegated substantial-development
directive; EXPERIMENTAL, not implemented by this document. The user asked to
choose a substantial feasible compiler outcome and execute it, rather than
repeat design/permission check-ins. This selection is not represented as their
approval of each API spelling. Public VERSION/CHANNEL remain 1.0.2a1/dev.

## Authority, Baseline And Objective

All four requested authorities are available. Their immutable/current readings
are snapshotted in `/tmp/nql-next-compiler-v7wdgsfr/authority/`. Both DOCX hashes
match the previously reconciled originals. v10 strengthens Assembly-Level
control and explicitly leaves concrete API/mnemonic design to implementation
evidence; unsafe boundaries remain explicit and do not disable diagnostics.
The current masters supersede historical snapshots with completed C0.31 capacity
and canonical-access evidence. None says general Safety or Full Compiler exists.

The verified isolated root is `/home/Axelly/.codex/worktrees/4878/NolquASM`,
detached at 66b92a4ce9e5491e570d292fe1b0320f04ba1907. The previous access milestone
is COMPLETE: 1078 main markers, 112 MCP methods, nine release checks, seven pins,
actual complete-source public compilation and a fresh combined C0 probe. Its
identities remain unchanged. Do not restart that completed plan or replace its
evidence. The original dirty main remains read-only. New implementation happens
in a source-identical scratch tree until candidate verification/review succeeds.

C0 currently has signed i64 functions and bounded byte memory, but only reads fd0
and writes fd1/fd2 through fixed helpers. It has no argv access or general OS
interface. Therefore an actual NolQu-L CLI cannot independently open its input
files; native toolchain/module development still needs host orchestration.

Deliver one vertical capability: source -> validated indexed AST -> explicit
unsafe permission checks -> direct x86_64 Linux syscall/argv code -> standalone
ELF -> real file-reading utility -> verified A/B/C generations. Add no Python,
LLVM, R0, assembler or linker source semantics to this path.

## Alternatives And Selection

1. Full types/modules immediately: important but modules need native file access,
   and the concept does not fix all type/conversion syntax. Host module rewriting
   would perpetuate the missing compiler boundary. Defer that broader language
   project rather than invent a resolver in Bash/Python.
2. Rewrite the full CLI/MCP immediately: argv, OS access, hashing and protocol
   primitives are missing; a wrapper around existing host code would not be a
   migration. Reject a superficial replacement.
3. Native OS capability with explicit unsafe scopes and one actual utility:
   selected. This removes a concrete compiler/toolchain prerequisite while
   retaining predecessor/bootstrap and old program contracts.

## Pre-Edit Engineering Protocol

- STAGE AFFECTED: lexer/parser, indexed AST, semantic permission validation,
  direct ELF codegen/runtime ABI, bootstrap evidence and coherent integration.
- FILES: frontend.nql/backend.nql; native-OS tests/oracles; two component seeds
  and matching pins only after review; existing wrappers/probes/docs as needed.
- BUG HYPOTHESIS: existing inability is architectural, not a missing host wrapper:
  current primitives cannot inspect argv or open an arbitrary input descriptor.
- RISK LEVEL: high, across untrusted wire validation, lexical scope and native ABI.
- PATCH STRATEGY: bounded additive constructs/intrinsics; preserve old NQAF and
  ELF bytes for old successful programs; write compiler changes in the existing
  flat B0-compatible sixteen-local language. No refactor requiring successor
  syntax to build the successor.
- ALTERNATIVES: above. The ASM skill's old token/NASM descriptions are not the
  canonical contract: current twelve-byte tokens, thirty-two-byte wide records
  and direct ELF emission are authoritative.

## Public Experimental Source Contract

The new interfaces are controller design choices, not pre-existing implemented
features. Names remain exactly `arg_count`, `arg_copy`, `byte_address`, `syscall6`.
All normal user functions resolve before intrinsics, including wrong-arity
shadows. Local variables remain a separate namespace.

| Intrinsic | NolQu-L arguments | Result / permission |
| --- | --- | --- |
| `arg_count()` | none | signed-i64 argc, including argv[0]; no byte arena needed |
| `arg_copy(index, offset, capacity)` | three i64 values | copy raw argument bytes and final NUL into the selected arena; return length excluding NUL |
| `byte_address(offset, count)` | two i64 values | checked span's native address as raw i64 bits; requires unsafe scope |
| `syscall6(number, frame_offset)` | two i64 values | one raw Linux syscall using six words in the arena; raw rax result; requires unsafe scope |

`arg_copy` checks destination range before pointer arithmetic; capacity must be
at least one (zero/negative capacity is C0R-004/70). Negative/out-of-range index fails C0R-008/70 at the call. It scans
within the supplied capacity, then copies only after finding the terminator;
insufficient capacity fails C0R-009/74 without partial destination publication.
Empty arguments return zero and still copy one NUL. No UTF-8 conversion,
shell splitting, environment traversal or caller-frame pointer is exposed.
Invalid destination/count uses the existing C0R-004/70 range diagnostic.

`byte_address` checks `0 <= offset <= capacity` and
`0 <= count <= capacity - offset` before address formation. A zero-length
one-past span is permitted; dereferencing it is not thereby made safe. Its
guarantee is only the checked arena span, not the later kernel operation's
memory effects. Raw pointers/FD ownership/lifetimes remain the unsafe caller's
responsibility; no borrow checker, pointer type system or full Safety is claimed.

`syscall6` reads exactly six little-endian 64-bit words at byte offsets
0,8,16,24,32,40 from a checked 48-byte arena span. Unaligned frames are supported
on this target. Number is passed in rax; words go to rdi,rsi,rdx,r10,r8,r9.
All values preserve raw bit patterns. Kernel rax is returned unchanged: there is
no libc errno conversion, automatic retry, empty-range elision, fd policy or
hidden allocation. Even a zero-length requested syscall remains an actual
syscall. Extra registers for lower-arity kernel calls are ordinary ABI inputs.
Invalid frame range fails C0R-004/70 before entering the kernel. User-function
arity remains six; this frame avoids adding stack arguments or varargs.

### Lexical Unsafe Boundary

```text
unsafe {
    # safety: the frame and its pointer spans are valid in this program's arena;
    # the selected syscall and descriptor effects are owned by this caller.
    let result = syscall6(number, frame_offset)
}
```

`unsafe` is contextual only before `{` in statement position. Existing variables
and functions named unsafe remain valid and retain their old output. Blocks
nest with the existing total control-depth bound of 64, create lexical scopes,
and do not disable graph, name, arity, arithmetic, arena or frame checks. No
runtime branch is introduced merely to enter/leave the scope. Existing final
top-level return requirements remain. `unsafe fn` and file-wide Safety modes
are outside this bounded implementation.

The introducer's first comment must be `# safety:` or `// safety:`. Whitespace
and blank lines are allowed. Nonempty explanation may follow the tag and/or in
following comment lines before the first statement. Missing/empty invariant is
C0P-014/1, no AST. It is a visible assertion of responsibility, not a proof.
New source permission analysis resolves global user shadows and checks actual
call ownership: raw intrinsic use outside unsafe is C0S-001/1, no AST. The
backend independently rejects equivalent forged AST with C0B-010/1, no ELF.

Safe functions may contain a checked unsafe implementation as in the authority's
safe-abstraction model, but this milestone proves only lexical permission and
the documented bounds/ABI, not arbitrary wrapper safety or interprocedural
preconditions. A general unsafe-function contract remains future work.

## NQAF/6 And Independent Validation

Retain every legacy NQAF/1..5 header/record meaning, reserved field requirement,
source/token/node bound and successful old output. NQAF/6 uses the current wide
32-byte header/records, u32 fields and the same 262144/65536/65536 limits.
Header version=6, size=32, dialect=5, profile in {0,1}; all existing reserved
fields remain zero. NQSC/1 profile transport is unchanged.

New statement nodes (all flags/children zero, next as ordinary statement chain):

- kind45: unsafe opener; anchor covers `unsafe`, `{`, and the validated invariant
  header through the byte before the first body/closing token.
- kind46: matching closing `}`, length1. No scope crosses a function boundary.

Both frontend and backend check matching balanced scopes, ordinary lexical
bindings, nesting limit and the source header. The backend validates untrusted
topology/ownership/source spans before dereferencing or lowering. Unsafe status
belongs to the owning statement/function traversal, never incidental expression
record position or a producer-supplied trusted flag. Cross-owner, skipped-scope,
unbalanced, reserved-byte and forged-header mutations fail before any ELF prefix.

Select /6 if an unsafe block or an actually unshadowed new intrinsic is used.
After parsing, a bounded pass identifies definitions of the four exact names,
then classifies calls; this chooses transport and permission, not codegen.
For /6 unsafe permission only, the backend additionally verifies actual source
containment: lexically scan from an opener's `{` to its matching `}` while
ignoring line comments, require the closing node to anchor that exact brace,
and require each raw call anchor to lie within the real source interval of an
owning unsafe block. AST scope membership is also required. Relinking a genuine
close node after a source-outside call cannot grant permission. This bounded
source correspondence is new for /6 unsafe permission; it does not turn legacy
NQAF into a fully authenticated parse or claim whole-AST/source equivalence.

An unrelated declaration or user shadow must not force new semantics/image
layout. Mere identifier/comment text is not a feature. Legacy syntax without
new resolved operations remains byte-identical /1..5. The backend requires /6
for new operations; crafted /1..5 cannot activate them. Unsupported /7 fails.

## Native Runtime And Machine Evidence

Successful existing helpers preserve r12; only fatal writers reuse it as status.
For programs using argv, capture the initial kernel rsp in preserved r12 before
the existing startup path, without moving the stack. r15 remains call depth;
rbx remains arena base; mapped-profile private ownership remains in r14. New
helpers preserve rbp/rbx/r12..r15, obey 16-byte call alignment, and must survive
nested six-argument functions and existing stream helpers. Fatal paths need not
resume, but must retain profile cleanup and failed-stderr behavior.

Keep existing startup bytes when no new operation resolves. Argument count
alone does not allocate a byte arena. Copy/address/syscall-frame operations use
the existing 64 KiB default or explicit 16 MiB RW/NX profile. Do not infer a
larger allocation from source size or argv length. New helper bytes live in
unused wide helper space, documented before edits; do not overlap existing
runtime/mapped cleanup/data. Write them conditionally so old image gaps remain
identical. Preserve 4096-byte/512-slot frames and depth64. No libc/interpreter,
host assembler/linker, source rewriting, hidden child tool, or optimization.

Inspect actual ELF/disassembly and use the existing QEMU guest debugger to
observe the syscall instruction and registers. A six-argument mmap test must
map a real file at nonzero offset65536 and write its expected bytes, then unmap
and close. This detects a lost r9 or rcx/r10 confusion. Check raw ENOSYS/EBADF,
zero-length calls, invalid spans before kernel entry, short writes/EINTR under
caller control, both arena profiles and callee-save/stack behavior.

Primary references checked 2026-10-24:
[Linux syscall ABI](https://man7.org/linux/man-pages/man2/syscall.2.html),
[Linux x86 entry](https://github.com/torvalds/linux/blob/master/arch/x86/entry/entry_64.S),
[ELF initial stack](https://github.com/torvalds/linux/blob/master/fs/binfmt_elf.c),
[execve arguments](https://man7.org/linux/man-pages/man2/execve.2.html).
The libc syscall() return convention is not the raw instruction contract.

## Integrated Native Program

`examples/canonical/native_cat.nql` is actual NolQu-L source, not a host wrapper
or a newly installed public tool name. Its standalone ELF copies stdin when
no file is given, otherwise reads named files in order to stdout. It obtains
arguments natively and performs openat/read/write/close in explicit unsafe
scopes. `--` as first operand terminates option interpretation; other operands
are literal paths, no shell expansion. An argument `-` denotes stdin.
Paths with spaces/non-UTF8 bytes and binary data must survive. It handles EINTR
and partial writes explicitly, closes acquired descriptors on recoverable
failures, reports a nonzero error status, and never rewrites user input files.
Fatal memory/runtime failure still relies on process resource reclamation; no
universal descriptor/lifetime or signal leak-freedom claim is made.

## Bootstrap, Integration And Acceptance

Keep frozen Machine/Stage0/B0/monolithic-C0/successor pins unchanged. Both full
new sources must remain flat sixteen-local B0 programs and fit all current
bounds. No automatic capacity expansion is authorized by this spec.

Build each new component twice through unchanged B0 with explicit profile,
require identical A1/A2 bytes; use actual A -> B -> C and require B==C component
bytes. Run unchanged legacy goldens plus the new source/OS corpus on A and named
candidate-aware old and new oracles on B/C. Retain the exact old source/pin
ledger and receipts; a new A need not equal the old A or new B. Hashes are
computed only from observed artifacts, never filled in from expectation.

Update the two frontend/backend seeds/pins coherently in the candidate tree only
after implementation reviews and deterministic rebuild proof. Source/seed/pin/
wrapper/probe schemas form one owned promotion set. Production W is updated
only after complete candidate validation/reviews, with rollback snapshots.
Keep public tools/resources/prompts and required schemas compatible. Existing
capacity/profile/generation flags and added unsafe/argv/syscall proof flags must
fail closed until a complete fresh matching run; Full Compiler, self-hosting and
Verified remain false. Internal C0.32 names a real new experimental contract;
it does not increment public VERSION or establish a release.

Complete only when public canonical CLI compiles/checks/runs the native utility,
actual kernel effects/arguments/error statuses match, old program bytes remain,
A/B/C evidence is complete, all baseline main/MCP/release tests pass with no
skips, actual relocated installation works, current full sources compile via
the public CLI, a fresh combined probe passes, and independent whole-change
review closes. No commit/main edit/push/merge/release or evidence deletion in
this plan. Rollback restores the coherent owned set, not unrelated prior work.
