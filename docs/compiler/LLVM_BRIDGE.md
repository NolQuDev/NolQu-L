# LLVM Bridge Legacy Status

## Classification

The LLVM bridge is frozen legacy compatibility/reference tooling. It is not a
NolQu-L bootstrap stage, not a self-hosting path, and not the planned canonical
backend. The canonical architecture starts at machine bytes under `bootstrap/`.

## Retained Flow

```text
Reference Compiler R0
-> exported textual IR
-> tools/nql_ir_dump_parser.nql
-> tools/nq_ir_json_to_llvm.py
-> LLVM IR
```

`tools/nq_ir_dump_parser.py` remains a parity oracle.
`tools/nql_ir_json_to_llvm.nql` remains an incomplete historical migration
artifact. `tools/nq_llvm_bootstrap.py` remains a frozen source-level translator.

## Allowed Changes

- fixes needed to preserve existing valid tests
- crash and diagnostic fixes
- explicit compatibility corrections
- documentation that clarifies legacy behavior

## Disallowed Architectural Growth

- new NolQu-L semantics implemented in LLVM first
- treating IR-to-LLVM parity as a canonical bootstrap milestone
- using Python or LLVM to construct a canonical compiler generation
- calling this path Stage 0, self-hosting, or the future NolQu-L backend

## Removal Rule

Legacy files remain until their supported compatibility commands, tests, and
documentation have been retired through an explicit migration. Their presence
does not block canonical Stage 0 work and their deletion does not prove
self-hosting.
