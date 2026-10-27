# C0.28 Structured Control Flow Implementation Plan

> For agentic workers: execute task-by-task with test-driven-development and
> verification-before-completion. Continue the approved Core-0 roadmap in
> NOLQU_MAJOR_DEVELOPMENT_UPD.md; this is not public language promotion.

**Goal:** Compile nested if/else and while, block-local mutable i64 values,
comparisons and block-final returns to standalone machine code.

**Architecture:** Extend the B0-built source frontend and AST backend, leaving
Machine/Stage0/B0/C0.25 unchanged. NQAF/2 adds structured delimiters to the
indexed statement stream; expressions remain contiguous postorder trees.
The backend validates nesting, resolves lexical scopes, then fixes relative
branches. No interpreter or source evaluation occurs on the host.

**Tech Stack:** NolQu-L Core-0, x86_64 Linux syscalls, direct ELF bytes; shell
only orchestrates files/processes, Python only tests, QEMU only adapts execution.

**Spec:** NOLQU_MAJOR_DEVELOPMENT_UPD.md, Core-0 Source Contract; this ADR.

## Constraints And Decision

Requested continuation; actual class Major Development, high risk across
lexer/parser/AST/semantics/codegen. No VERSION/CHANNEL/public ABI change.
The coordinated grammar, NQAF/2 and scope/branch changes justify the major
development classification, even though both components remain experimental.
This classification is not a public major-version release.
Keep the current workspace's unrelated edits. Existing scalar sources retain
NQAF/1 output and identical runtime code. New keywords are reserved exactly;
`if`, `else`, `while` used as old local names are the explicit experimental
compatibility exception. Names such as `while_count` remain valid.

Use explicit delimited statement records instead of adding arbitrary jumps or
reordering postorder expression evaluation. They describe source block structure,
not machine addresses; only the backend owns branch layout and patching.
A recursive compiler stack or another C0.25 parser intrinsic would obscure
resource bounds and is unnecessary. Both components still build directly by B0.

Impact: HIGH frontend/AST/semantics/codegen; MEDIUM source compatibility,
bootstrap component reproducibility and docs; LOW MCP metadata. No change to
stable types/safety, public CLI, target ABI, stdlib or trusted predecessor.
Resource cost remains explicit indexed storage, not hidden dynamic allocation.

| Contract | Compatibility / migration |
| --- | --- |
| Existing scalar source | Same AST/ELF; predecessor corpus checks bytes |
| Locals named if/else/while | Now reserved; rename the experimental local |
| NQAF/1 producers | Accepted by the upgraded backend |
| NQAF/2 producers | Require C0.28 backend; old backend rejects version |
| Canonical seeds | Upgrade frontend/backend and matching SHA-256 together |
| Public nqlc / R0 / B0 / C0.25 | Unchanged; no stage/CLI promotion |

Rollback is scoped to this component pair: restore their matched source,
artifact and SHA-256 versions plus gates/MCP metadata from a retained snapshot,
then rebuild via B0 and rerun gates. Do not restore a seed independently of its
pin or silently use a NQAF/1 backend with a NQAF/2 producer. There is no automatic
rollback snapshot or release transaction manager in this repository. Never
reset the dirty workspace or unrelated user changes to roll back this work.

## Grammar And Semantics

```text
program   = "fn main()" "{" statement* "return" expr ";"? "}" EOF
block     = "{" statement* ("return" expr ";"?)? "}"
statement = ("let" identifier "=" expr | identifier "=" expr) ";"?
          | "while" expr block | "if" expr block ("else" block)?
expr      = equality
equality  = relation (("==" | "!=") relation)*
relation  = sum (("<" | "<=" | ">" | ">=") sum)*
sum       = product (("+" | "-") product)*
product   = primary (("*" | "/") primary)*
primary   = identifier | decimal | "(" expr ")"
```

All operators associate left. Comparisons are signed i64 and produce 0 or 1;
conditions use zero=false/nonzero=true. Checked arithmetic is unchanged.
Condition code runs on every while iteration, before the body. Only the chosen
if arm executes. A return exits main, including from a nested block. A return
must be the final statement of its block; main still requires its final return
(no all-path return analysis). No break/continue, else-if shorthand, standalone
blocks, unary operators, functions/calls, boolean type or short circuit added.

Every control body has lexical scope. Declarations become visible after their
initializer; inner bindings may shadow outer ones. Duplicate names in the same
scope and escaping block locals are errors, including unreachable branches.
An inner `let x=x+1` resolves its initializer against an existing outer x.
Each loop execution reinitializes its local slots. No heap or new descriptor.

## NQAF/2

The existing 16-byte header/records and source payload remain unchanged. Emit
version 2 only when a new node kind occurs; otherwise preserve version 1.
Node kinds 20..25 are `< <= > >= == !=`, with two expression children.

| Kind | Meaning | Left | Right | Anchor |
| --- | --- | --- | --- | --- |
| 34 | While guard | Condition expression | 0 | `while` |
| 35 | While end | 0 | 0 | `}` |
| 36 | If guard | Condition expression | 0 | `if` |
| 37 | Else delimiter | 0 | 0 | `else` |
| 38 | If end | 0 | 0 | `}` |

Statement next links (30..32,34..38) form one forward stream through both
arms and nested bodies. Main owns the first statement; the final top-level
return terminates the stream. An earlier return links to its block delimiter.
Delimiters must form a balanced stack: 34/35, 36/(optional 37)/38. Expression
children never cross a statement boundary. Each node has exactly one owner;
no free-standing expression, arbitrary branch, crossing block or shared node.
Backend rejects new nodes in NQAF/1 and empty version-2 extensions.

Bounds: 8192 source bytes, 512 tokens/nodes, 64 nested control bodies, 65536
compiler arena bytes, 4096 generated stack bytes, 32 KiB ELF output buffer.
Frontend block stack: 35000..35064 (sentinel plus 64 kinds).
Backend stack: 25104..25493 (65 six-byte records including sentinel), reused
for nesting validation, scope counts and codegen fixups. Literal table entries
are reused for code-start offsets only after their immediates are emitted.
Syntax/IR/name errors exit 1 without output; I/O errors 74; arithmetic faults 70.
User loops may intentionally not terminate; compilation always advances or fails.

## Execution

- [x] Add tests rejecting the old frontend: nested loops/branches, all signed
  comparisons, scope/shadowing, early return, malformed nesting, caps and AST
  corruption. Run `python3 tests/bootstrap/test_c0_control_flow.py` (red).
- [x] Extend frontend tokenization/precedence and bounded block transitions;
  run source AST tests, including byte-identical scalar comparison to C0.26.
- [x] Extend backend shape/nesting/scope validation and checked direct codegen;
  run control-flow tests and existing 12 frontend/15 backend tests (green).
- [x] Rebuild twice with B0, compare artifacts, update SHA-256 pins, integrate
  the control-flow gate into frontend/backend evidence and MCP stage metadata.
- [x] Run full baseline, MCP and release gates; review branch targets, resource
  bounds and malformed streams; record measured outcome in development docs.

Release blocked on any regression or unverified branch target. Full Compiler,
self-hosting and verified compiler generations remain NOT_IMPLEMENTED.
