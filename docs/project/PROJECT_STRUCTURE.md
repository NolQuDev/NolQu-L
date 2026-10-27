# NolQu-L Project Structure

## Canonical Bootstrap

- `bootstrap/`: canonical bootstrap root and stage manifest
- `bootstrap/machine/x86_64-linux/`: machine-code trust root
- `bootstrap/stage0/x86_64-linux/`: canonical symbolic Stage 0 seed
- `tests/bootstrap/`: reproducible evidence for canonical stages
- `docs/compiler/ARCHITECTURE.md`: public architecture and implemented boundaries
- `docs/project/CHANGELOG.md`: public change summaries
- `docs/project/VALIDATION.md`: tested scope and open qualification limits

Internal design attachments, agent plans and session records stay local; see
[PUBLICATION.md](PUBLICATION.md). They are not public build inputs.

## Reference Compiler R0

- `src/`: x86_64 NASM sources for the reference compiler
- `nql`: canonical project manager/run executable
- `nolqul -> nql`: formal project-manager alias
- `nqlc`: canonical direct compiler executable
- `nolqulc -> nqlc`: formal compiler alias
- `tests/compiler/`: R0 behavior and diagnostics
- `examples/core/`, `examples/semantics/`: current language examples
- `build/`: generated R0 artifacts

## Legacy Compatibility

- `tools/`: LLVM/Python bridge and historical migration helpers
- `tests/llvm/`: frozen LLVM maintenance coverage
- `tests/ir/`: frozen IR/LLVM bridge and parity coverage
- `examples/llvm/`: historical compatibility examples

These legacy paths are visible so existing behavior remains reproducible. They
are not part of the canonical NolQu-L bootstrap chain.

## Project Support

- `docs/`: language, compiler, project, and community documentation
- `tests/meta/`: release and repository consistency checks
- `tests/shared/`: test harness utilities
- `VERSION`: release version source of truth
- `CHANNEL`: release channel source of truth
- `Makefile`: common canonical and historical-corpus workflows
