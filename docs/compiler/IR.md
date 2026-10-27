# Reference Compiler R0 IR

## Classification

The current IR belongs to Reference Compiler R0. It is a useful semantic and
diagnostic artifact, but it is not yet the canonical NolQu-L Core IR and is not
a bootstrap trust root.

## Current Pipeline Role

Within R0, the IR separates parser/semantic work from optimization and NASM
code generation. It can be inspected or exported with:

```bash
./nql --dump-ir file.nql
./nql --export-ir build/out.ir file.nql
```

The current textual fields include:

- `A` and `B`: opcode-specific numeric payloads
- `LN`: source line where available
- `NAME`: readable symbols for named instructions
- `TEXT`: exported string-literal data

## Legacy Bridge Role

The exported form is also consumed by frozen compatibility tooling:

```text
R0 exported IR -> nq_ir_dump_parser.nq -> nq_ir_json_to_llvm.py -> LLVM IR
```

The Python parser remains a byte-parity oracle and the NolQu-L LLVM translator
remains an incomplete historical migration target. None of these tools belongs
to the canonical bootstrap chain.

## Canonical IR Rule

Stage 0 should not inherit this IR automatically. A canonical Core IR may reuse
proven concepts only after its instruction set, ownership, type behavior,
control flow, machine cost, serialization, diagnostics, and bootstrap
construction are documented and tested.

## Stability

The R0 exported IR is a compatibility interface for existing tests, not a
permanently frozen public NolQu-L format. Changes require coordinated updates
to R0 tests and retained legacy consumers.
