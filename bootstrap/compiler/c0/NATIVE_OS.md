# C0.32 Native OS Interface

C0.32 is the current **experimental frontend/backend contract**. It adds
lexically checked `unsafe` blocks, process arguments and a raw Linux x86_64
syscall interface to the existing direct-ELF pipeline. The monolithic
[`compiler.nq`](compiler.nq) / `c0.seed` remains C0.25. Public `VERSION=1.0.2a1`
and `CHANNEL=dev` are unchanged.

The syntax, backend and runtime have scoped passing tests and independent
Task 1/2/3/4 source review. Actual complete-source generations, public integration,
relocated installation and final main/MCP/installed combined-proof execution
gates pass. Main retains all 1078 prior PASS markers and adds `c0-native-os`
(1079 total); MCP retains all 112 methods and adds twelve (124 total). Nine
release checks and unchanged 120-tool/8-resource/5-prompt protocol schemas pass.
These counts describe separate overlapping gates, not a unique-test sum.
The reliability continuation subsequently passed a1079-marker post-formatter
baseline and1080 markers with opt-in host retention, plus fresh MCP124,
combined proof and594 assurance invocations. It adds17 host controls while
preserving every original gate and compiler artifact. See the
[reliability report](../../../docs/project/C032_RELIABILITY_REPORT.md).

One earlier full main run observed the frozen C0.30 comparison backend receiving
SIGKILL. The same input set later passed serially; cause and signal sender are
unknown. This incident remains **OPEN**, without quarantine, OOM attribution or
retry-as-fix. Stable/security readiness is **PARTIAL / BELUM SIAP**. See the
[session report](../../../docs/project/C032_SESSION_REPORT.md) and
[bounded assurance profile](../../../tests/security/README.md).
These local results do not establish Full Compiler, full-language self-hosting,
the later Verified stage or full NolQu-L Safety.

The figures above are the original C0.32 native checkpoint. A subsequent located
diagnostic audit found a duplicate separator in C0R-008/009. The source-only
repair changes four emitted immediate bytes (suffix pointer +2, length -2),
preserving selected backend size 315593. Independent review approved the fix;
B0 A1/A2 and six native runtime methods pass. The current backend pin is
`b169f9ee8890d306c080f299980c352bbabc5518052355dd0148a7878b9f51b1`.
Fresh post-repair MCP/bootstrap/public/assurance validation is recorded
separately in the session report; the original full-main run is not relabeled
as a run of this changed identity.
Post-repair MCP passes 124 methods; the fresh SDK proof verifies 722 stages,
275 checks, two 41-method B/C oracle pairs and sixteen retained native artifacts.
The current full-source backend B/C hash is
`c789a3442691dd4f51f51ecb594265ff7b106a45313b8f6e91c7ec233bd29f85`.
Five impacted public CLI/project/install methods, eleven host-runner controls,
the hardened four-method/594-invocation assurance profile and nine release
checks pass. The earlier assurance 300s budget exhaustion remains in evidence;
the unchanged-case 600s profile completes in 335.867s. No source regression,
signal-incident resolution or overall release approval is inferred from this.

## Authority And Compatibility

All four requested authorities were available and compared:
`NolQu-LConcept.docx`, the repository's encoded-name
`NolQu-L%20Concept%20-%20Refined%20v10%20Assembly-Level(1).docx`,
[`NOLQU_MAJOR_DEVELOPMENT_ASSEMBLY_LEVEL.md`](../../../NOLQU_MAJOR_DEVELOPMENT_ASSEMBLY_LEVEL.md)
and [`NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md`](../../../NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md).
The concepts supply the Nine Pillars, explicit unsafe responsibility and
Assembly-Level direction; v10's maturity boundary leaves concrete syntax/API
to implementation evidence. Current source and closed verification supersede
older in-progress checkpoints in the masters. Their historical evidence is
retained. The four API spellings below are implementation design decisions,
not a claim that a concept document already implemented them.

This bounded step supports explicit machine control, diagnostics, compatibility
and test-before-merge without claiming ownership/lifetime checking or the
concept's full safety modes. It removes an observed native argv/file-access
prerequisite for future toolchain work. It makes no performance-saving claim.

The canonical compilation path remains Machine -> Stage0 -> B0 -> C0 -> ELF.
Both compiler sources remain one flat B0-compatible `main` with sixteen locals.
No Python, LLVM, R0, assembler, linker or host source rewriting supplies its
language semantics. Python tests/MCP, shell orchestration and legacy LLVM/NASM
paths still exist. Replacing the complete toolchain with NolQu-L remains work.

## Source Contract

All arguments/results are i64 values. Exact global user functions resolve
before intrinsics, including forward definitions and wrong-arity shadows.
An arity mismatch does not fall back to a builtin. Local variables occupy a
separate namespace. Merely mentioning a name in a comment or identifier does
not enable an intrinsic or allocate its runtime arena.

| Intrinsic | Meaning | Permission |
| --- | --- | --- |
| `arg_count()` | argc including argv[0] | ordinary call; no byte arena needed |
| `arg_copy(index, offset, capacity)` | copy argument bytes plus NUL into the selected arena; return length excluding NUL | ordinary call with checked destination |
| `byte_address(offset, count)` | native address of a checked arena span, as raw i64 bits | owning `unsafe` block required |
| `syscall6(number, frame_offset)` | one syscall using a checked six-word frame; return raw rax | owning `unsafe` block required |

`arg_copy` validates destination range first, then index, then scans for NUL
within the positive supplied capacity. It copies only after a terminator is
found, so a capacity failure publishes no partial destination. Empty arguments
return zero and still write one NUL. Bytes are preserved, including spaces and
non-UTF8 values; there is no shell splitting, text conversion or environment
traversal. The terminating NUL counts against capacity.

`byte_address` checks `0 <= offset <= arena_capacity` and
`0 <= count <= arena_capacity - offset` before forming a pointer. Count zero
at the one-past offset is valid, but does not authorize dereferencing that
address. The compiler checks this span only. The caller remains responsible
for subsequent kernel reads/writes, descriptor ownership, pointer lifetime,
syscall-specific structures and arguments. A later syscall can invalidate
assumptions made in an earlier invariant.

### Lexical Unsafe Blocks

```text
unsafe {
    # safety: the complete syscall frame belongs to this program;
    # any pointer and descriptor effects are valid for the selected operation.
    result = syscall6(number, frame_offset)
}
```

This is a statement fragment, not a complete program. The contextual opener
is the exact identifier `unsafe` followed by `{` at a statement boundary.
Variables and functions named `unsafe` remain legal. The first comment after
whitespace/blank lines must begin with `# safety:` or `// safety:`; horizontal
whitespace after the comment marker is allowed. `safety:` is case-sensitive.
Explanation must be nonempty on that line or following comment lines before
the first statement/closing brace. A tag alone is insufficient.

Blocks nest, create lexical binding scopes and share the existing combined
control-depth bound of 64. Entering/leaving one adds no runtime branch. Graph,
name, arity, arithmetic and memory checks still apply. Every function still
requires its final top-level `return`. There is no `unsafe fn`, file-wide mode,
general unsafe-function precondition checker or proof that an invariant is true.
An ordinary function may contain an unsafe implementation; that alone does not
prove an arbitrary safe abstraction.

## Raw Syscall ABI

`syscall6` reads exactly 48 bytes at `frame_offset`: six little-endian 64-bit
words at relative offsets 0, 8, 16, 24, 32 and 40. Unaligned frames are supported
on this target. It loads the syscall number into rax and the words into
**rdi, rsi, rdx, r10, r8, r9**, then returns the kernel's rax bits unchanged.
The fourth syscall argument uses r10. The instruction clobbers rcx/r11.
The helper preserves rbp/rbx/r12-r15 and the existing call alignment.

The Linux ABI is documented by [syscall(2)](https://man7.org/linux/man-pages/man2/syscall.2.html)
and [entry_64.S](https://github.com/torvalds/linux/blob/master/arch/x86/entry/entry_64.S),
checked 2026-10-24. This raw result is distinct from libc's errno conversion.
There is no automatic retry, fd policy, allocation or zero-length-call elision.
Unused arguments of a lower-arity syscall remain ordinary raw ABI inputs.
The existing six-parameter user-function limit is unchanged; no varargs or
extra stack-argument language feature is introduced.

Callers handle negative raw errno values and actual progress explicitly.
The supplied utility retries interrupted reads/writes and advances by returned
byte counts for partial writes. It closes each acquired descriptor once and
reports a close error; it does not retry close after EINTR. These Linux-specific
choices follow [read(2)](https://man7.org/linux/man-pages/man2/read.2.html),
[write(2)](https://man7.org/linux/man-pages/man2/write.2.html) and
[close(2)](https://man7.org/linux/man-pages/man2/close.2.html), checked 2026-10-24.
They are caller source behavior, not hidden `syscall6` behavior.

## Diagnostics And Publication

| Code | Condition | Exit / output |
| --- | --- | --- |
| `C0P-014` | missing/empty/invalid required safety header | 1; no AST |
| `C0S-001` | resolved raw intrinsic outside its owning unsafe source scope | 1; no AST |
| `C0B-010` | backend unsafe permission/source-containment rejection | 1; no ELF |
| `C0B-008` | existing call-resolution/arity diagnostic | 1; no ELF |
| `C0B-009` | existing unsupported-profile diagnostic, unchanged | 1; no ELF |
| `C0R-004` | invalid arena span/frame, or zero/negative copy capacity | 70; no invalid memory/kernel operation |
| `C0R-008` | negative/out-of-range argument index | 70 |
| `C0R-009` | positive copy capacity cannot include the argument's NUL | 74; destination not partially copied |

Runtime diagnostics identify the call location. Existing arithmetic, depth,
stream and mapped-resource diagnostics remain. Controlled fatal paths retain
the selected profile's cleanup and failed-stderr behavior. Fatal signals rely
on process reclamation; arbitrary raw calls have no universal cleanup guarantee.
Public compilation publishes only successful complete output and preserves an
existing destination on compiler rejection. Runtime output already written by
a failing program cannot be rolled back.

## NQAF/6 And Independent Backend Validation

A genuine unsafe block or actually resolved new intrinsic selects NQAF/6,
dialect 5. It retains wide32 storage: 32-byte header, exact source bytes and
32-byte records, u32 spans/IDs, profile 0 or 1 and zero reserved fields. NQSC/1
profile transport is unchanged. Successful legacy programs retain their
NQAF/1..5 meaning and tested byte outputs; /1..5 cannot activate the new raw
operations. A shadow alone does not force /6. Unsupported /7 is rejected.

| New kind | Anchor | Children / flags / links |
| --- | --- | --- |
| 45 | `unsafe` through the byte before the first body/closing token, including `{` and validated header | left/right/flags zero; ordinary statement `next` |
| 46 | exact matching closing `}`, length 1 | left/right/flags zero; ordinary statement `next` |

The backend independently validates graph shape, unique ownership, physical
statement chains, function/control boundaries, lexical scopes and raw-call
resolution. It also scans actual source braces while ignoring line comments,
revalidates the invariant header, binds kind46 to the real matching brace and
requires each raw call to lie inside an owning unsafe source interval. Moving
a genuine close node after a source-outside call cannot grant permission.
Both AST ownership and source containment are required. This bounded /6 check
does not authenticate all source text or establish whole-AST/source equivalence.

## Bounds And Storage

Source/token/node bounds stay 262144/65536/65536. Control and user-call depth
stay 64; user arity stays six; frames stay 4096 bytes/512 i64 slots. B0 limits
stay source327680/output589824/dynamic-byte-access5376. The wide ELF cap is 8 MiB.
Default program arena is 65536 bytes; explicit `--compiler-profile` chooses
16777216 RW/NX bytes. Neither width nor argv length increases this bound.
`arg_count` alone captures argv without allocating an arena; copy/address/frame
operations use the selected existing arena.

Compiler-private additions below are half-open **arena offsets**, not addresses
in a generated program. They fit the existing explicit 16 MiB compiler profile.

| Component | Interval | Purpose |
| --- | --- | --- |
| frontend | `[0x660000,0x6a0000)` | u32 safety-header starts |
| frontend | `[0x6a0000,0x6b0000)` | exact-name classes, not permission flags |
| backend | `[0x600000,0x680000)` | eight-byte per-node native metadata |
| backend | `[0x680000,0x690000)` | existing control/state/diagnostic region, including new scope scratch |
| backend | `[0x690000,0x790000)` | u32 source-brace correspondence table |

Frontend parsing stacks are reused only after their old values are dead.
Backend C0B-010 text uses separate offset 6825400 rather than overwriting the
existing diagnostic length table. The ELF buffer remains `[0x800000,0x1000000)`.

Generated-ELF **file offsets** are a different address space:

| File offset / interval | Purpose |
| --- | --- |
| `0x600800` | argv startup capture, before stack movement |
| `0x600820`, `0x600840` | argc and checked argument-copy helpers |
| `0x600900`, `0x600940` | address and raw syscall helpers |
| `0x600a00`, `0x600a20` | argument-index/capacity fatal entries |
| `0x604100`, `0x604180` | new runtime diagnostic suffixes |

Old wide arena/range/fatal entries remain `0x600240`, `0x6003a0`, `0x600400`.
The existing mapped helper interval `[0x600600,0x600782)` and resource text
`[0x604000,0x6040c7)` remain distinct. New bytes are emitted conditionally,
preserving legacy successful image gaps. r12 holds initial kernel rsp only
when argv is used; rbx remains arena base, r14 mapped ownership, r15 call depth.
No executable writable arena, interpreter or dynamic dependency is introduced.

## Native Utility And Evidence Boundary

[`native_cat.nql`](../../../examples/canonical/native_cat.nql) is an actual
source program producing a standalone ELF, not an installed command alias.
It reads argv, opens literal file paths, copies binary bytes/stdin and owns its
descriptors explicitly. See the [example guide](../../../examples/canonical/README.md)
for invocation, buffers, status and bounded path behavior.

Retained scoped runs passed: six native frontend plus forty frontend regression
methods; six runtime methods plus 123 backend/legacy methods; five native-program
plus thirty existing Guest methods. These groups overlap and are not summed as
unique coverage. Independent Task 1 fix, Task 2 and Task 3 reviews approved
their own scopes; the coherent source/pin/MCP/documentation set also received
independent review before isolated-worktree integration.
Actual syscall/register evidence in both profiles includes file-backed mmap at
offset 65536, binary output and unchanged input-file bytes. EINTR/short-write
injection is explicitly synthetic within real guest execution. This host runs
the x86_64 target under QEMU on aarch64; hardware-native execution is unverified.

Focused reproduction from the repository root:

```bash
make canonical-native-test
python3 -B tests/bootstrap/test_c0_component_generations.py -v
```

The second command rebuilds actual generations. The completed standalone module
passed six methods in 648.759s, with 722 stages, 275 checks, 475 artifacts, six
component comparisons and 41 named oracle methods on each B/C pair, zero skips.
The [capacity record](CAPACITY.md) binds actual new source/A/B/C hashes and the
receipt identity. Public compilation of both complete sources matches B/C.
Four new public methods and canonical-only relocation passed; combined
relocation passed its scoped rerun after the normal legacy compiler prerequisite.
The unchanged legacy fallback's foreign-cwd include limitation is recorded in
the toolchain guide. Final main/MCP/release execution gates, installed combined
proof and protocol comparison subsequently passed. The combined proof observed
722 stages/275 checks and retained sixteen native JSON/source/wire/ELF evidence
files after temporary cleanup. It binds compiler/test identities and seven
bootstrap artifact hashes. Open signal attribution and finite assurance coverage
still prevent stable/security promotion.
The intended proof fields `capacity_verified`, `compiler_profile_verified`,
`component_generation_verified`, `unsafe_blocks_verified`,
`process_arguments_verified`, `syscall_abi_verified` require a complete fresh
identity-bound run. Documentation, pins and earlier local results cannot set
them true. The actual fresh installed probe set these six bounded capability
fields true. They are not an overall security qualification or a solution to
the unexplained signal incident. Full Compiler/self-hosting/Verified remain false.
