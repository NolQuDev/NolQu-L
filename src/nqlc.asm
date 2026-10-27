; ═══════════════════════════════════════════════════════════════
;  NOLQU COMPILER — master build file
;  Split into modules, assembled via %include.
;
;  Modules:
;    defs.asm      — %define constants (tokens, IR opcodes, sizes)
;    data.asm      — section .data  (strings, tables, boilerplate)
;    bss.asm       — section .bss   (buffers, counters)
;    entry.asm     — _start, CLI argument parsing
;    utils.asm     — emit helpers, error reporting, debug, math
;    symtab.asm    — hash, keyword table, symbol tables, fn table
;    ir.asm        — IR emit macros/helpers, ir_load/ir_store, tok helpers
;    lexer.asm     — lexer_run, str_record
;    parser.asm    — parser_run, all parse_* functions
;    optimizer.asm — opt_run, all optimizer passes
;    codegen.asm   — cg_run, dispatch table, all cg_* handlers
;
;  Build:
;    nasm -f elf64 src/nqlc.asm -o build/nqlc-r0.o
;    x86_64-linux-gnu-ld build/nqlc-r0.o -o build/nqlc-r0
; ═══════════════════════════════════════════════════════════════

BITS 64
DEFAULT ABS

%include "src/defs.asm"

section .data
%include "src/data.asm"

section .bss
%include "src/bss.asm"

section .text
global _start
%include "src/entry.asm"
%include "src/utils.asm"
%include "src/symtab.asm"
%include "src/ir.asm"
%include "src/lexer.asm"
%include "src/parser.asm"
%include "src/optimizer.asm"
%include "src/codegen.asm"
