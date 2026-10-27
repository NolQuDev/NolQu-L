# C0.29 Functions Implementation Plan

> Execute test-first in the current continuation workspace. Do not revert the
> existing worktree, commit, or promote a seed before its verification gates.

**Goal:** source-driven named i64 functions, parameters and real native calls.
**Architecture:** extend the existing B0-built frontend/backend with NQAF/3.
Keep NQAF/1 and NQAF/2 scalar/control-flow streams and executable bytes unchanged.
**Tech stack:** frozen B0, flat arena state, direct x86_64 Linux ELF emission.
**Spec:** `NOLQU_MAJOR_DEVELOPMENT_UPD.md`, C0.28 successor work; this ADR records
the bounded function subset. This is experimental compiler development, not a
public release or a Full Compiler/self-hosting claim.

## Decision And Boundaries

The measured blocker is the single `fn main()` envelope and absent call syntax.
Affected stages: lexer, parser, AST validation, name resolution, codegen/runtime,
bootstrap pins and MCP probes. Risk: high (cross-stage format and stack ABI).
Extending the shared indexed passes avoids a duplicate compiler. Source expansion
or compile-time call evaluation would not implement native recursion and is rejected.

```text
program   = function+
function  = fn identifier ( parameters? ) { statement* return expression ;? }
parameters = identifier (, identifier)*
primary   = identifier | decimal | ( expression ) | identifier ( arguments? )
arguments = expression (, expression)*
```

Existing statements, precedence and lexical blocks remain unchanged. Each function
requires a final top-level return; a nested return ends that function at runtime.
Exactly one zero-parameter `main` is required, in any definition order. Forward,
nested, self-recursive and mutually recursive calls are resolved by exact name.
Function names occupy a separate namespace from local variables. Parameters are
mutable locals visible on entry; duplicate parameters and same-scope declarations
are rejected. Locals never cross function boundaries. Arguments evaluate left to
right before transferring control; there is no host evaluation.

The current ABI supports zero through six i64 parameters/arguments in
`rdi,rsi,rdx,rcx,r8,r9`, with `rax` as result. More than six is diagnosed, not
silently dropped. Calls preserve live caller values in indexed frame slots. Native
stack is 16-byte aligned at call sites; each function reserves 4096 bytes with a
saved frame pointer. At most 64 simultaneously active functions (including main)
are permitted; deeper calls fail with a source-located runtime diagnostic and
exit 70. Return restores the caller frame and the depth budget. No heap or new
file descriptors are introduced. Source/token/node/block bounds remain
8192/512/512/64. General types, varargs, function pointers, closures, external ABI,
standalone call statements, runtime byte/stream builtins and modules are outside
this work unit.

## NQAF/3 Contract

The 16-byte header/records and embedded source are unchanged. Version 3 is emitted
when multiple/non-main functions, parameters or a call appear. Existing one-main
programs without calls retain version 1/2 exactly. Reserved bytes remain zero.
Kinds 4,5,15..18,20..25,30..38 retain their field meanings. New kinds:

| Kind | Meaning | Anchor | Left | Right | Next |
| --- | --- | --- | --- | --- | --- |
| 39 | function entry | function name | 0 | 0 | next statement |
| 40 | parameter | parameter name | 0 | 0 | next statement |
| 41 | function end | closing `}` | 0 | 0 | next function entry or 0 |
| 42 | call expression | callee name | final argument record or 0 | 0 | 0 |
| 43 | argument-list prefix | comma or closing `)` | preceding argument record or 0 | argument expression | 0 |

The physical statement chain includes 39/40/41 as well as 30..32/34..38. A function
entry is followed by zero to six parameters, then its body, final return and end.
No nested functions, cross-function blocks, or statements outside functions.
The final kind-33 module root anchors the first `fn` and owns the first kind-39
statement; its right/next are zero. The penultimate record is kind 41.

Expressions and argument-list prefixes remain contiguous postorder trees with
single ownership. For kind 43, right is the preceding physical expression root;
if left is nonzero it is the preceding argument prefix and right's subtree starts
at left+1. The first prefix starts at right's subtree. Kind 42 immediately follows
its final argument prefix, or has no children for a zero-argument call. Prefix
counts are derived and independently bounded to six by both frontend and backend.
Names/arity resolve semantically, never through unchecked external addresses.

Token offsets and lengths remain u16 throughout parser scratch storage, including
call anchors longer than 255 bytes. Function and local lookup compare full names;
a long callee cannot alias a shorter prefix. Backend diagnostic C0B-008 covers
duplicate/missing functions, a missing or parameterized main, and mismatched call
arity. C0B-003/004 also apply to undeclared/duplicate function-local parameters.
Locations identify the offending name (the module root for a missing main).

Additional storage stays inside the existing zero-initialized 65536-byte arena:

| Component | Region | Purpose |
| --- | --- | --- |
| Frontend | 15017, 15020 | Low/high bytes of operator or callee token length |
| Frontend | 36000..39077 | 513 six-byte call frames indexed by operator depth |
| Backend | 20480..20991 | Per-node parameter or argument count |
| Backend | 26060..26065 | Function envelope, parameter phase and main ID |
| Backend | 21000..25095 | Consumed immediates reused for code offsets and callee IDs |

The emitter is still bounded by 24000 code bytes and the existing ELF arena.
Native calls add no heap allocation or descriptor ownership. A checked runtime
fault exits 70; failure to write its diagnostic exits 74. Syntax/semantic errors
exit 1 without publishing an ELF. The source wrapper checks both pins and stages
and retains the previous output on failure.

## Implementation And Verification

- [x] Add `tests/bootstrap/test_c0_functions.py`: forward/nested/recursive calls,
  six arguments, scope/arity/duplicate errors, malformed syntax/AST, depth bound,
  runtime fault locations, wrapper atomic failure and deterministic ELF. Run a
  valid call case against C0.28 and record the expected unsupported-syntax failure.
- [x] Extend `frontend.nql`: comma token, envelope/parameter states, explicit
  call-marker stack and argument-prefix nodes. Run the syntax/AST tests and all
  predecessor frontend/control-flow cases against a temporary B0-built candidate.
- [x] Extend `backend.nql`: independent topology/arity validation, function-local
  scopes, exact callee resolution, native frames/rel32 calls, bounded recursion.
  Run runtime/error/AST mutation cases before deriving candidate hashes.
- [x] Rebuild both components twice with B0, compare bytes, update SHA-256 pins
  and materialize seeds. Add the function suite to existing bootstrap gates and
  capability fields to fresh MCP probes with fail-closed tests.
- [x] Run `make test`, MCP unittests, `make release-check`, fresh canonical probe
  and independent review. Update the selected development document with measured
  results and remaining limits, then mark this plan verified.

## Verified Artifacts

Both components were rebuilt twice with the pinned B0 on 2026-09-09, compared
byte-for-byte and promoted together through the existing materializers:

| Component | Bytes | SHA-256 |
| --- | --- | --- |
| Frontend | 81576 | `2e231661ca4da4a8a80da22cefad2b602cb09fb67d4af717bfe34262aa286875` |
| Backend | 125197 | `ac091d9fd9bc695dbbdf8c9254f05ee1e8012d383839679de241949e8281bbcf` |

Independent review caught a callee-length truncation in frontend scratch storage:
a 257-byte name could resolve to a different one-byte function. A failing test
established the wrong runtime result before the u16 fix. Regression coverage now
checks lengths 255/256/257 with zero/one/six arguments, exact-name resolution,
diagnostic locations and diagnostic-write failures. All 17 function tests pass.
Both reviewers found no remaining concrete issues after the correction; this
bounded testing is not a formal correctness or memory-safety proof.

The four-source C0.28 corpus keeps its AST and ELF bytes exactly. The Machine,
Stage 0, B0, C0.25 emitter and bounded-successor pins remain unchanged. The fresh
MCP probe reports `SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED`, with
function-call and parameter-scope gates true, while Full Compiler and self-hosting
remain false. Runtime byte/stream primitives and compiler-source capacity are
still required before these components can compile their own source.

## Final Verification

Work unit closed on 2026-09-10 against the same reviewed source and seed hashes.

| Gate | Result |
| --- | --- |
| Original `make test` baseline | 1071 PASS, 0 FAIL, 0 SKIP |
| Final complete `make test` | 1072 PASS, 0 FAIL, 0 SKIP, exit 0 |
| Function suite (included in `make test`) | 17 tests PASS |
| MCP unit suite | 33 tests PASS, exit 0 |
| `make release-check` | 9 PASS, exit 0 |
| Bootstrap hashes | All seven artifacts PASS |
| Fresh combined C0 probe | `SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED`, exit 0 |

The multiset of baseline PASS names is preserved; the additional gate is
`c0-functions`. Component unittests are not added a second time to the aggregate
PASS count. No regression remains in these suites. The interrupted run's log
also contained all 1072 PASS lines, but its process exit was no longer available;
a complete rerun stored both the log and structured exit result:
`/tmp/nql-c029-completion-test.log` and `/tmp/nql-c029-completion-result.json`.
It finished in 1242016 ms without timeout or output truncation. MCP and release
logs are `/tmp/nql-c029-completion-mcp.log` and
`/tmp/nql-c029-completion-release.log`; the combined probe result is
`/tmp/nql-c029-final-probe.json`. These temporary logs supplement the repeatable
test suites, not replace them.

## Next Measured Boundary

On 2026-09-10, feeding the complete component sources to the pinned frontend
confirmed the first self-compilation blocker without modifying any seed:

| Input | Source bytes | Result |
| --- | --- | --- |
| `frontend.nql` | 50458 | `input:167:32: error[C0P-002]: source exceeds 8192 bytes; split the input` |
| `backend.nql` | 79883 | `input:157:17: error[C0P-002]: source exceeds 8192 bytes; split the input` |

Both exit 1 with no AST output. Reproduce on x86_64 Linux with
`bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed < bootstrap/compiler/c0/frontend.nql`
and the corresponding backend source; prefix the command with `qemu-x86_64`
on the current ARM64 test host. Raising the source bound alone is insufficient:
the component sources also require runtime byte/stream operations, standalone
call statements and more tokens/nodes. These must have explicit contracts and
boundary tests before a successor can claim compiler-source coverage.
In particular, the backend source already exceeds the 65535-byte range of the
current u16 source offsets. Larger inputs require versioned wider spans or a
bounded multi-unit design, plus a new arena layout; increasing one constant
cannot safely extend the existing 65536-byte frontend state.
