BITS 64
ORG 0x400000

; Independent audit oracle only: nasm -f bin, never a canonical build input.

%define SYS_READ 0
%define SYS_WRITE 1
%define SYS_OPEN 2
%define SYS_CLOSE 3
%define SYS_RT_SIGACTION 13
%define SYS_EXIT 60

%define O_RDONLY 0
%define O_WRONLY_CREAT_TRUNC 577
%define MODE_755 493
%define INPUT_CAP 327680
%define OUTPUT_CAP 589824
%define STRING_CAP 2048
%define BINDING_CAP 16
%define LOCAL_STACK_BYTES 128
%define BYTE_MEMORY_CAP 65536
%define FRAME_STACK_BYTES (LOCAL_STACK_BYTES + BYTE_MEMORY_CAP)
%define BYTE_ACCESS_CAP 5376
%define BYTE_OOB_EXIT_STATUS 70
%define IO_PATCH_CAP 64
%define IO_ERROR_EXIT_STATUS 74
%define SIGPIPE 13
%define SIG_IGN 1
%define KERNEL_SIGSET_BYTES 8

%define CG_OP_ADD 1
%define CG_OP_SUB 2
%define CG_OP_MUL 3
%define CG_OP_DIV 4
%define CG_OP_EQ 5
%define CG_OP_NEQ 6
%define CG_OP_LT 7
%define CG_OP_LTE 8

section .text
image_start:
    db 0x7f, "ELF", 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0
    dw 2, 0x3e
    dd 1
    dq _start, 0x40, 0
    dd 0
    dw 0x40, 0x38, 5, 0, 0, 0
    dd 1, 4
    dq 0, 0x400000, 0x400000, header_end - image_start, header_end - image_start, 0x1000
    dd 1, 5
    dq 0x1000, 0x401000, 0x401000, 0x4000, 0x4000, 0x1000
    dd 1, 4
    dq 0x5000, 0x405000, 0x405000, 0x969, 0x969, 0x1000
    dd 1, 6
    dq 0x1000, 0x406000, 0x406000, 0, bss_end - input_buf, 0x1000
    dd 0x6474e551, 6
    dq 0, 0, 0, 0, 0, 0x10
header_end:
    times 0x1000 - ($ - image_start) db 0

_start:
    jmp near profile_args
    times 4 db 0x90
.legacy_start:

    cmp rbx, 2
    jne .not_help
    mov rdi, [r12 + 8]
    mov rsi, strict qword opt_help
    call streq
    cmp rax, 1
    jne .not_help
    mov rdi, 1
    mov rsi, strict qword msg_usage
    mov rdx, msg_usage_len
    call write_all_or_die
    xor rdi, rdi
    jmp exit

.not_help:
    cmp rbx, 3
    jne .not_lex
    mov rdi, [r12 + 8]
    mov rsi, strict qword opt_lex
    call streq
    cmp rax, 1
    jne .not_lex
    mov rdi, [r12 + 16]
    mov [current_path], rdi
    call read_input_file
    mov [input_len], rax
    xor rdi, rdi
    call lex_core
    cmp rax, 0
    jne .lex_failed
    mov rdi, 1
    call lex_core
    jmp .lex_done
.lex_failed:
    mov rax, 1
.lex_done:
    mov rdi, rax
    jmp exit

.not_lex:
    cmp rbx, 3
    jne .not_parse
    mov rdi, [r12 + 8]
    mov rsi, strict qword opt_parse
    call streq
    cmp rax, 1
    jne .not_parse
    mov rdi, [r12 + 16]
    mov [current_path], rdi
    call read_input_file
    mov [input_len], rax
    xor rdi, rdi
    call lex_core
    cmp rax, 0
    jne .parse_failed
    call parse_core
    cmp rax, 0
    jne .parse_failed
    mov rdi, 1
    mov rsi, strict qword msg_parse_ok
    mov rdx, msg_parse_ok_len
    call write_all_or_die
    xor rdi, rdi
    jmp exit
.parse_failed:
    mov rdi, 1
    jmp exit

.not_parse:
    cmp rbx, 4
    jne usage_error
    mov rdi, [r12 + 16]
    mov rsi, strict qword opt_output
    call streq
    cmp rax, 1
    jne usage_error

    mov rdi, [r12 + 8]
    mov [current_path], rdi
    call read_input_file
    mov [input_len], rax

    call try_compile_return_literal
    cmp rax, 1
    je compile_return_literal
    call try_compile_write_literal
    cmp rax, 2
    je compile_output_limit_error
    cmp rax, 1
    je compile_write_literal
    call try_compile_expression_program
    cmp rax, 4
    je compile_type_mismatch_error
    cmp rax, 5
    je compile_unknown_call_error
    cmp rax, 6
    je compile_div_overflow_error
    cmp rax, 7
    je compile_unknown_assignment_error
    cmp rax, 9
    je compile_byte_bounds_error
    cmp rax, 3
    je compile_div_zero_error
    cmp rax, 2
    je compile_output_limit_error
    cmp rax, 1
    je compile_expression_program

    xor rdi, rdi
    call lex_core
    cmp rax, 0
    jne .compile_lex_failed
    mov rdi, 2
    mov rsi, strict qword msg_unsupported
    mov rdx, msg_unsupported_len
    call write_all_or_die
.compile_lex_failed:
    mov rdi, 1
    jmp exit

compile_return_literal:
    mov r15d, edx
    mov rdi, strict qword output_buf
    mov rsi, strict qword return7_elf
    mov rdx, return7_elf_len
    call copy_bytes
    mov dword [output_buf + return_status_imm_offset], r15d
    mov rdi, [r12 + 24]
    mov rsi, strict qword output_buf
    mov rdx, return7_elf_len
    call write_output_file
    xor rdi, rdi
    jmp exit

compile_write_literal:
    jmp near profile_write_literal
    times 5 db 0x90
.legacy_entry:
    mov rsi, strict qword dynamic_write_elf
    mov rdx, dynamic_write_prefix_len
    call copy_bytes

    mov rbx, [write_literal_len]
    mov r14, dynamic_write_prefix_len
    add r14, rbx
    mov [output_buf + dynamic_write_filesz_offset], r14
    mov [output_buf + dynamic_write_memsz_offset], r14
    mov dword [output_buf + dynamic_write_message_len_imm_offset], ebx
    mov rax, [write_return_value]
    mov dword [output_buf + dynamic_write_return_imm_offset], eax

    lea rdi, [output_buf + dynamic_write_prefix_len]
    mov rsi, strict qword string_buf
    mov rdx, rbx
    call copy_bytes
    mov rdi, [r12 + 24]
    mov rsi, strict qword output_buf
    mov rdx, r14
    call write_output_file
    xor rdi, rdi
    jmp exit

compile_expression_program:
    mov rdi, [r12 + 24]
    mov rsi, strict qword output_buf
    mov rdx, [code_output_len]
    call write_output_file
    xor rdi, rdi
    jmp exit

compile_unknown_call_error:
    mov rsi, strict qword msg_codegen_unknown_call
    mov rdx, msg_codegen_unknown_call_len
    jmp compile_error

compile_type_mismatch_error:
    mov rsi, strict qword msg_codegen_type_mismatch
    mov rdx, msg_codegen_type_mismatch_len
    jmp compile_error

compile_div_zero_error:
    mov rsi, strict qword msg_codegen_div_zero
    mov rdx, msg_codegen_div_zero_len
    jmp compile_error

compile_div_overflow_error:
    mov rsi, strict qword msg_codegen_div_overflow
    mov rdx, msg_codegen_div_overflow_len
    jmp compile_error

compile_unknown_assignment_error:
    mov r14, [assignment_source_line]
    mov r15, [assignment_source_col]
    mov rdi, strict qword msg_codegen_unknown_assignment
    mov rsi, msg_codegen_unknown_assignment_len
    call print_source_error
    mov rdi, 1
    jmp exit

compile_byte_bounds_error:
    mov r14, [byte_memory_source_line]
    mov r15, [byte_memory_source_col]
    call profile_bounds_message
    times 10 db 0x90
    call print_source_error
    mov rdi, 1
    jmp exit

compile_output_limit_error:
    mov rsi, strict qword msg_codegen_output_limit
    mov rdx, msg_codegen_output_limit_len
    jmp compile_error

compile_error:
    mov rdi, 2
    call write_all_or_die
    mov rdi, 1
    jmp exit

usage_error:
    mov rdi, 2
    mov rsi, strict qword msg_usage_err
    mov rdx, msg_usage_err_len
    call write_all_or_die
    mov rdi, 1
    jmp exit

io_error:
    mov rdi, 2
    mov rsi, strict qword msg_io_error
    mov rdx, msg_io_error_len
    call write_all_or_die
    mov rdi, 1
    jmp exit

input_limit_error:
    mov rdi, 2
    mov rsi, strict qword msg_input_limit
    mov rdx, msg_input_limit_len
    call write_all_or_die
    mov rdi, 1
    jmp exit

exit:
    mov rax, SYS_EXIT
    syscall

; Match the first semantic codegen subset without relying on source-byte
; identity: fn main() { return <u32>; }. Whitespace and comments are handled
; by skip_trivia. RAX=1/RDX=value on match, RAX=0 otherwise.
try_compile_return_literal:
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, strict qword input_buf
    mov r13, strict qword input_buf
    add r13, [input_len]
    mov r14, 1
    mov r15, 1

    mov rdi, strict qword kw_fn
    mov rsi, kw_fn_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword kw_main
    mov rsi, kw_main_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword kw_return
    mov rsi, kw_return_len
    call match_word
    cmp rax, 1
    jne .no
    call parse_u32_literal
    cmp rax, 1
    jne .no
    mov rbx, rdx
    mov rdi, strict qword lit_semi
    mov rsi, 1
    call match_lit
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call skip_trivia
    cmp r12, r13
    jne .no
    mov rdx, rbx
    mov rax, 1
    jmp .done
.no:
    xor rax, rax
    xor rdx, rdx
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; Match fn main() { write(<string>); return <u32>; } and retain decoded
; bytes in string_buf for direct ELF emission.
try_compile_write_literal:
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, strict qword input_buf
    mov r13, strict qword input_buf
    add r13, [input_len]
    mov r14, 1
    mov r15, 1

    mov rdi, strict qword kw_fn
    mov rsi, kw_fn_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword kw_main
    mov rsi, kw_main_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword name_write
    mov rsi, name_write_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call parse_string_literal
    cmp rax, 2
    je .output_limit
    cmp rax, 1
    jne .no
    mov rbx, rdx
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_semi
    mov rsi, 1
    call match_lit
    mov rdi, strict qword kw_return
    mov rsi, kw_return_len
    call match_word
    cmp rax, 1
    jne .no
    call parse_u32_literal
    cmp rax, 1
    jne .no
    mov r9, rdx
    mov rdi, strict qword lit_semi
    mov rsi, 1
    call match_lit
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call skip_trivia
    cmp r12, r13
    jne .no
    mov [write_literal_len], rbx
    mov [write_return_value], r9
    mov rax, 1
    jmp .done
.output_limit:
    mov rax, 2
    jmp .done
.no:
    xor rax, rax
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; Compile a bounded semantic Core-0 subset into executable machine code:
; zero or more integer lets, simple assignment-driven while loops, bounded
; byte-memory access, then one integer return. Binary operators use the
; documented precedence and locals occupy fixed RBP slots. RAX=1 on success,
; 0 when the source is outside this subset, or a stable codegen status for a
; diagnosed failure.
try_compile_expression_program:
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, strict qword input_buf
    mov r13, strict qword input_buf
    add r13, [input_len]
    mov r14, 1
    mov r15, 1
    mov qword [binding_count], 0
    mov qword [byte_oob_patch_count], 0
    mov qword [io_read_error_patch_count], 0
    mov qword [io_write_error_patch_count], 0
    mov qword [io_error_write_patch_count], 0

    mov rdi, strict qword kw_fn
    mov rsi, kw_fn_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword kw_main
    mov rsi, kw_main_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no

    mov rdi, strict qword output_buf
    mov rsi, strict qword dynamic_code_elf
    mov rdx, dynamic_code_prefix_len
    call copy_bytes
    lea rax, [output_buf + dynamic_code_prefix_len]
    mov [code_cursor], rax
    mov rax, [code_cursor]
    mov [io_emit_cursor], rax
    mov rdi, strict qword cg_prologue
    mov rsi, cg_prologue_len
    call emit_blob
    cmp rax, 0
    jne .output_limit
    mov rax, [io_emit_cursor]
    add rax, cg_prologue_sigpipe_error_disp_offset
    mov [sigpipe_setup_error_patch], rax

.let_loop:
    mov rdi, strict qword kw_let
    mov rsi, kw_let_len
    call match_word
    cmp rax, 1
    jne .statement_loop
    call scan_identifier
    cmp rax, 1
    jne .no
    push rdx
    push rcx
    mov rdi, strict qword lit_eq
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .let_no
    call cg_parse_expr
    mov r8, rax
    mov r10, rdx
    mov r11, rcx
    pop rsi
    pop rdi
    cmp r8, 0
    jne .expression_status_r8
    push rdi
    push rsi
    call match_optional_semi
    pop rsi
    pop rdi
    mov rdx, r11
    mov rcx, r10
    call add_binding
    cmp rax, 1
    jne .no
    mov rdi, rdx
    call cg_emit_store_slot
    cmp rax, 0
    jne .output_limit
    jmp .let_loop
.let_no:
    add rsp, 16
    jmp .no

.statement_loop:
    mov rdi, strict qword kw_while
    mov rsi, kw_while_len
    call match_word
    cmp rax, 1
    je .while_stmt

.return_stmt:
    mov rdi, strict qword kw_return
    mov rsi, kw_return_len
    call match_word
    cmp rax, 1
    je .direct_return
    mov rdi, strict qword kw_if
    mov rsi, kw_if_len
    call match_word
    cmp rax, 1
    jne .identifier_stmt
    call cg_parse_expr
    cmp rax, 0
    jne .expression_status
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call cg_emit_jz_placeholder
    cmp rax, 0
    jne .output_limit
    mov [branch_patch], rdx

    mov rdi, strict qword kw_return
    mov rsi, kw_return_len
    call match_word
    cmp rax, 1
    jne .no
    call cg_parse_expr
    cmp rax, 0
    jne .expression_status
    call match_optional_semi
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword cg_exit
    mov rsi, cg_exit_len
    call emit_blob
    cmp rax, 0
    jne .output_limit

    mov rdi, strict qword kw_else
    mov rsi, kw_else_len
    call match_word
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, [branch_patch]
    mov rsi, [code_cursor]
    call patch_rel32
    cmp rax, 0
    jne .output_limit
    mov rdi, strict qword kw_return
    mov rsi, kw_return_len
    call match_word
    cmp rax, 1
    jne .no
    call cg_parse_expr
    cmp rax, 0
    jne .expression_status
    call match_optional_semi
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call skip_trivia
    cmp r12, r13
    jne .no
    mov rdi, strict qword cg_exit
    mov rsi, cg_exit_len
    call emit_blob
    cmp rax, 0
    jne .output_limit
    jmp .finalize

.while_stmt:
    mov rax, [code_cursor]
    mov [loop_start_cursor], rax
    call cg_parse_expr
    cmp rax, 0
    jne .expression_status
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call cg_emit_jz_placeholder
    cmp rax, 0
    jne .output_limit
    mov [loop_exit_patch], rdx
.while_body:
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .while_close
    call cg_parse_assignment_stmt
    cmp rax, 0
    je .while_body
    cmp rax, 8
    jne .expression_status
    call cg_parse_call_stmt
    cmp rax, 0
    je .while_body
    jmp .expression_status
.while_close:
    call cg_emit_jmp_placeholder
    cmp rax, 0
    jne .output_limit
    mov rdi, rdx
    mov rsi, [loop_start_cursor]
    call patch_rel32
    cmp rax, 0
    jne .output_limit
    mov rdi, [loop_exit_patch]
    mov rsi, [code_cursor]
    call patch_rel32
    cmp rax, 0
    jne .output_limit
    jmp .statement_loop

.identifier_stmt:
    call cg_parse_assignment_stmt
    cmp rax, 0
    je .statement_loop
    cmp rax, 8
    jne .expression_status
    call cg_parse_call_stmt
    cmp rax, 0
    je .statement_loop
    jmp .expression_status

.direct_return:
    call cg_parse_expr
    cmp rax, 0
    jne .expression_status
    call match_optional_semi
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    call skip_trivia
    cmp r12, r13
    jne .no
    mov rdi, strict qword cg_exit
    mov rsi, cg_exit_len
    call emit_blob
    cmp rax, 0
    jne .output_limit

.finalize:
    call cg_finalize_sigpipe_error_handler
    cmp rax, 0
    jne .output_limit
    call cg_finalize_byte_oob_handler
    cmp rax, 0
    jne .output_limit
    call cg_finalize_input_error_handler
    cmp rax, 0
    jne .output_limit
    call cg_finalize_output_error_handler
    cmp rax, 0
    jne .output_limit
    call cg_finalize_error_write_handler
    cmp rax, 0
    jne .output_limit
    mov rdx, [code_cursor]
    sub rdx, output_buf
    mov [code_output_len], rdx
    mov [output_buf + dynamic_code_filesz_offset], rdx
    mov [output_buf + dynamic_code_memsz_offset], rdx
    mov rax, 1
    jmp .done

.expression_status_r8:
    mov rax, r8
.expression_status:
    cmp rax, 2
    je .output_limit
    cmp rax, 3
    je .division_zero
    cmp rax, 4
    je .type_mismatch
    cmp rax, 6
    je .division_overflow
    cmp rax, 7
    je .unknown_assignment
    cmp rax, 9
    je .byte_bounds
    cmp rax, 5
    je .unknown_call
    jmp .no
.output_limit:
    mov rax, 2
    jmp .done
.division_zero:
    mov rax, 3
    jmp .done
.type_mismatch:
    mov rax, 4
    jmp .done
.division_overflow:
    mov rax, 6
    jmp .done
.unknown_assignment:
    mov rax, 7
    jmp .done
.byte_bounds:
    mov rax, 9
    jmp .done
.unknown_call:
    mov rax, 5
    jmp .done
.no:
    xor rax, rax
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; Expression parser/code generator. Success is RAX=0 with constant metadata in
; RCX/RDX. The generated value is always left in RAX at runtime.
cg_parse_expr:
    jmp cg_parse_equality

cg_parse_equality:
    push rbx
    call cg_parse_relational
    cmp rax, 0
    jne .ret
.loop:
    mov rdi, strict qword lit_eqeq
    mov rsi, 2
    call match_lit
    cmp rax, 1
    je .eq
    mov rdi, strict qword lit_neq
    mov rsi, 2
    call match_lit
    cmp rax, 1
    je .neq
    xor rax, rax
    jmp .ret
.eq:
    mov rbx, CG_OP_EQ
    jmp .rhs
.neq:
    mov rbx, CG_OP_NEQ
.rhs:
    push rdx
    push rcx
    push rbx
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .emit_failed
    call cg_parse_relational
    mov rdi, rax
    mov r10, rdx
    mov r11, rcx
    pop rbx
    pop r9
    pop r8
    mov rax, rdi
    cmp rax, 0
    jne .ret
    call cg_combine_binary
    cmp rax, 0
    jne .ret
    jmp .loop
.emit_failed:
    mov rdi, rax
    pop rbx
    pop rcx
    pop rdx
    mov rax, rdi
.ret:
    pop rbx
    ret

cg_parse_relational:
    push rbx
    call cg_parse_additive
    cmp rax, 0
    jne .ret
.loop:
    mov rdi, strict qword lit_lte
    mov rsi, 2
    call match_lit
    cmp rax, 1
    je .lte
    mov rdi, strict qword lit_lt
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .lt
    xor rax, rax
    jmp .ret
.lte:
    mov rbx, CG_OP_LTE
    jmp .rhs
.lt:
    mov rbx, CG_OP_LT
.rhs:
    push rdx
    push rcx
    push rbx
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .emit_failed
    call cg_parse_additive
    mov rdi, rax
    mov r10, rdx
    mov r11, rcx
    pop rbx
    pop r9
    pop r8
    mov rax, rdi
    cmp rax, 0
    jne .ret
    call cg_combine_binary
    cmp rax, 0
    jne .ret
    jmp .loop
.emit_failed:
    mov rdi, rax
    pop rbx
    pop rcx
    pop rdx
    mov rax, rdi
.ret:
    pop rbx
    ret

cg_parse_additive:
    push rbx
    call cg_parse_multiplicative
    cmp rax, 0
    jne .ret
.loop:
    mov rdi, strict qword lit_plus
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .add
    mov rdi, strict qword lit_minus
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .sub
    xor rax, rax
    jmp .ret
.add:
    mov rbx, CG_OP_ADD
    jmp .rhs
.sub:
    mov rbx, CG_OP_SUB
.rhs:
    push rdx
    push rcx
    push rbx
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .emit_failed
    call cg_parse_multiplicative
    mov rdi, rax
    mov r10, rdx
    mov r11, rcx
    pop rbx
    pop r9
    pop r8
    mov rax, rdi
    cmp rax, 0
    jne .ret
    call cg_combine_binary
    cmp rax, 0
    jne .ret
    jmp .loop
.emit_failed:
    mov rdi, rax
    pop rbx
    pop rcx
    pop rdx
    mov rax, rdi
.ret:
    pop rbx
    ret

cg_parse_multiplicative:
    push rbx
    call cg_parse_primary
    cmp rax, 0
    jne .ret
.loop:
    mov rdi, strict qword lit_star
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .mul
    mov rdi, strict qword lit_slash
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .div
    xor rax, rax
    jmp .ret
.mul:
    mov rbx, CG_OP_MUL
    jmp .rhs
.div:
    mov rbx, CG_OP_DIV
.rhs:
    push rdx
    push rcx
    push rbx
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .emit_failed
    call cg_parse_primary
    mov rdi, rax
    mov r10, rdx
    mov r11, rcx
    pop rbx
    pop r9
    pop r8
    mov rax, rdi
    cmp rax, 0
    jne .ret
    call cg_combine_binary
    cmp rax, 0
    jne .ret
    jmp .loop
.emit_failed:
    mov rdi, rax
    pop rbx
    pop rcx
    pop rdx
    mov rax, rdi
.ret:
    pop rbx
    ret

cg_parse_primary:
    push rbx
    call skip_trivia
    cmp r12, r13
    jae .no
    mov [primary_source_line], r14
    mov [primary_source_col], r15
    mov al, [r12]
    call is_digit_al
    cmp rax, 1
    je .integer
    cmp byte [r12], '"'
    je .string
    cmp byte [r12], '('
    je .group
    call scan_identifier
    cmp rax, 1
    jne .no
    cmp rcx, name_byte_load_len
    je .check_byte_load
    cmp rcx, name_input_read_len
    je .check_input_read
    jmp .binding
.check_byte_load:
    push rdx
    push rcx
    mov rdi, rdx
    mov rsi, strict qword name_byte_load
    mov rdx, rcx
    call memeq_raw
    cmp rax, 1
    jne .not_byte_load_call
    call skip_trivia
    cmp r12, r13
    jae .not_byte_load_call
    cmp byte [r12], '('
    jne .not_byte_load_call
    pop rcx
    pop rdx
    jmp .byte_load
.not_byte_load_call:
    pop rcx
    pop rdx
    jmp .binding
.check_input_read:
    push rdx
    push rcx
    mov rdi, rdx
    mov rsi, strict qword name_input_read
    mov rdx, rcx
    call memeq_raw
    cmp rax, 1
    jne .not_input_read_call
    call skip_trivia
    cmp r12, r13
    jae .not_input_read_call
    cmp byte [r12], '('
    jne .not_input_read_call
    pop rcx
    pop rdx
    jmp .input_read
.not_input_read_call:
    pop rcx
    pop rdx
.binding:
    mov rdi, rdx
    mov rsi, rcx
    call lookup_binding
    cmp rax, 1
    jne .no
    mov rbx, rdx
    push rcx
    push r8
    mov rdi, rbx
    call cg_emit_load_slot
    mov rbx, rax
    pop rdx
    pop rcx
    mov rax, rbx
    jmp .ret
.byte_load:
    push qword [primary_source_line]
    push qword [primary_source_col]
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .byte_load_syntax
    call cg_parse_expr
    cmp rax, 0
    jne .byte_load_status
    mov r10, rcx
    mov r11, rdx
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .byte_load_syntax
    cmp r10, 1
    jne .byte_load_emit
    call profile_cmp_r11
    times 2 db 0x90
    jae .byte_load_bounds
.byte_load_emit:
    call cg_emit_byte_guard_rax
    cmp rax, 0
    jne .byte_load_status
    mov rdi, strict qword cg_byte_load
    mov rsi, cg_byte_load_len
    call emit_blob
    cmp rax, 0
    jne .byte_load_status
    add rsp, 16
    xor rcx, rcx
    xor rdx, rdx
    xor rax, rax
    jmp .ret
.byte_load_bounds:
    pop rax
    mov [byte_memory_source_col], rax
    pop rax
    mov [byte_memory_source_line], rax
    mov rax, 9
    jmp .ret
.byte_load_syntax:
    mov rax, 1
.byte_load_status:
    add rsp, 16
    jmp .ret
.input_read:
    push qword [primary_source_line]
    push qword [primary_source_col]
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .input_read_syntax
    call cg_parse_expr
    cmp rax, 0
    jne .input_read_status
    push rcx
    push rdx
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .input_read_outer_status
    mov rdi, strict qword lit_comma
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .input_read_outer_syntax
    call cg_parse_expr
    cmp rax, 0
    jne .input_read_outer_status
    mov [io_range_count_const_flag], rcx
    mov [io_range_count_const_value], rdx
    pop rax
    mov [io_range_offset_const_value], rax
    pop rax
    mov [io_range_offset_const_flag], rax
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .input_read_syntax
    call cg_validate_io_const_range
    cmp rax, 0
    jne .input_read_bounds
    call cg_emit_byte_range_guard
    cmp rax, 0
    jne .input_read_status
    call cg_emit_input_read
    cmp rax, 0
    jne .input_read_status
    add rsp, 16
    xor rcx, rcx
    xor rdx, rdx
    xor rax, rax
    jmp .ret
.input_read_bounds:
    pop rax
    mov [byte_memory_source_col], rax
    pop rax
    mov [byte_memory_source_line], rax
    mov rax, 9
    jmp .ret
.input_read_outer_syntax:
    mov rax, 1
.input_read_outer_status:
    add rsp, 16
    jmp .input_read_status
.input_read_syntax:
    mov rax, 1
.input_read_status:
    add rsp, 16
    jmp .ret
.integer:
    call cg_parse_i64_literal
    cmp rax, 1
    jne .no
    mov rbx, rdx
    mov rdi, strict qword cg_mov_rax_imm64
    mov rsi, cg_mov_rax_imm64_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rdi, rbx
    call emit_u64
    cmp rax, 0
    jne .ret
    mov rdx, rbx
    mov rcx, 1
    xor rax, rax
    jmp .ret
.string:
    call parse_string_literal
    cmp rax, 0
    je .no
    mov rax, 4
    jmp .ret
.group:
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    call cg_parse_expr
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .no
    xor rax, rax
    jmp .ret
.no:
    mov rax, 1
.ret:
    pop rbx
    ret

cg_parse_i64_literal:
    call skip_trivia
    cmp r12, r13
    jae .no
    xor rdx, rdx
    xor r8, r8
.loop:
    cmp r12, r13
    jae .done
    movzx ecx, byte [r12]
    cmp cl, '0'
    jb .done
    cmp cl, '9'
    ja .done
    sub ecx, '0'
    mov r9, 922337203685477580
    cmp rdx, r9
    ja .no
    jne .accumulate
    cmp ecx, 7
    ja .no
.accumulate:
    imul rdx, rdx, 10
    add rdx, rcx
    inc r12
    inc r15
    inc r8
    jmp .loop
.done:
    test r8, r8
    jz .no
    mov rax, 1
    ret
.no:
    xor rax, rax
    ret

scan_identifier:
    call skip_trivia
    cmp r12, r13
    jae .no
    mov al, [r12]
    call is_ident_start_al
    cmp rax, 1
    jne .no
    mov rdx, r12
    xor rcx, rcx
.loop:
    cmp r12, r13
    jae .yes
    mov al, [r12]
    call is_ident_part_al
    cmp rax, 1
    jne .yes
    inc r12
    inc r15
    inc rcx
    jmp .loop
.yes:
    mov rax, 1
    ret
.no:
    xor rax, rax
    ret

; Parse and lower `<existing-local> = <integer-expr>`. RAX=0 on success,
; RAX=7 for an undeclared target, and RAX=8 when an identifier was consumed
; but the statement is not an assignment. Expression/codegen statuses pass
; through unchanged.
cg_parse_assignment_stmt:
    push rbx
    call skip_trivia
    mov [assignment_source_line], r14
    mov [assignment_source_col], r15
    call scan_identifier
    cmp rax, 1
    jne .syntax
    mov [statement_name_ptr], rdx
    mov [statement_name_len], rcx
    push rdx
    push rcx
    mov rdi, strict qword lit_eq
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .not_assignment
    pop rsi
    pop rdi
    call lookup_binding
    cmp rax, 1
    jne .unknown_target
    mov rbx, rdx
    push r9
    call cg_parse_expr
    mov r10, rax
    pop r9
    cmp r10, 0
    jne .expression_status
    push r9
    call match_optional_semi
    pop r9
    mov rdi, rbx
    push r9
    call cg_emit_store_slot
    pop r9
    cmp rax, 0
    jne .done
    mov qword [binding_const_flags + r9 * 8], 0
    mov qword [binding_const_values + r9 * 8], 0
    xor rax, rax
    jmp .done
.not_assignment:
    add rsp, 16
    mov rax, 8
    jmp .done
.unknown_target:
    mov rax, 7
    jmp .done
.expression_status:
    mov rax, r10
    jmp .done
.syntax:
    mov rax, 1
.done:
    pop rbx
    ret

; Parse an intrinsic-style statement after cg_parse_assignment_stmt consumed
; its identifier. byte_store(index, value), output_write(offset, count), and
; error_write(offset, count) are semantic; all other well-formed zero-argument
; calls retain the stable unsupported-call status.
cg_parse_call_stmt:
    mov rcx, [statement_name_len]
    cmp rcx, name_byte_store_len
    je .check_byte_store
    cmp rcx, name_output_write_len
    je .check_output_write
    cmp rcx, name_error_write_len
    je .check_error_write
    jmp .unknown
.check_byte_store:
    mov rdi, [statement_name_ptr]
    mov rsi, strict qword name_byte_store
    mov rdx, rcx
    call memeq_raw
    cmp rax, 1
    je cg_parse_byte_store_stmt
    jmp .unknown
.check_output_write:
    mov rdi, [statement_name_ptr]
    mov rsi, strict qword name_output_write
    mov rdx, rcx
    call memeq_raw
    cmp rax, 1
    jne .unknown
    mov qword [io_write_fd], 1
    jmp cg_parse_output_write_stmt
.check_error_write:
    mov rdi, [statement_name_ptr]
    mov rsi, strict qword name_error_write
    mov rdx, rcx
    call memeq_raw
    cmp rax, 1
    jne .unknown
    mov qword [io_write_fd], 2
    jmp cg_parse_output_write_stmt
.unknown:
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    call match_optional_semi
    mov rax, 5
    ret
.syntax:
    mov rax, 1
    ret

cg_parse_byte_store_stmt:
    push rbx
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    call cg_parse_expr
    cmp rax, 0
    jne .done
    mov [byte_store_index_const_flag], rcx
    mov [byte_store_index_const_value], rdx
    call cg_emit_byte_guard_rax
    cmp rax, 0
    jne .done
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .done
    mov rdi, strict qword lit_comma
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    call cg_parse_expr
    cmp rax, 0
    jne .done
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    cmp qword [byte_store_index_const_flag], 1
    jne .index_valid
    mov rax, [byte_store_index_const_value]
    call profile_cmp_rax
    nop
    jae .bounds
.index_valid:
    call match_optional_semi
    mov rdi, strict qword cg_byte_store
    mov rsi, cg_byte_store_len
    call emit_blob
    cmp rax, 0
    jne .done
    xor rax, rax
    jmp .done
.bounds:
    mov rax, [assignment_source_line]
    mov [byte_memory_source_line], rax
    mov rax, [assignment_source_col]
    mov [byte_memory_source_col], rax
    mov rax, 9
    jmp .done
.syntax:
    mov rax, 1
.done:
    pop rbx
    ret

cg_parse_output_write_stmt:
    push rbx
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    call cg_parse_expr
    cmp rax, 0
    jne .done
    push rcx
    push rdx
    mov rdi, strict qword cg_push_rax
    mov rsi, cg_push_rax_len
    call emit_blob
    cmp rax, 0
    jne .outer_done
    mov rdi, strict qword lit_comma
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .outer_syntax
    call cg_parse_expr
    cmp rax, 0
    jne .outer_done
    mov [io_range_count_const_flag], rcx
    mov [io_range_count_const_value], rdx
    pop rax
    mov [io_range_offset_const_value], rax
    pop rax
    mov [io_range_offset_const_flag], rax
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .syntax
    call cg_validate_io_const_range
    cmp rax, 0
    jne .bounds
    call cg_emit_byte_range_guard
    cmp rax, 0
    jne .done
    cmp qword [io_write_fd], 2
    je .emit_error_write
    call cg_emit_output_write
    jmp .write_emitted
.emit_error_write:
    call cg_emit_error_write
.write_emitted:
    cmp rax, 0
    jne .done
    call match_optional_semi
    xor rax, rax
    jmp .done
.bounds:
    mov rax, [assignment_source_line]
    mov [byte_memory_source_line], rax
    mov rax, [assignment_source_col]
    mov [byte_memory_source_col], rax
    mov rax, 9
    jmp .done
.outer_syntax:
    add rsp, 16
    jmp .syntax
.outer_done:
    add rsp, 16
    jmp .done
.syntax:
    mov rax, 1
.done:
    pop rbx
    ret

lookup_binding:
    push rbx
    push r12
    push r13
    mov r12, rdi
    mov r13, rsi
    mov rbx, [binding_count]
.loop:
    test rbx, rbx
    jz .no
    dec rbx
    cmp [binding_name_lens + rbx * 8], r13
    jne .loop
    mov rdi, r12
    mov rsi, [binding_name_ptrs + rbx * 8]
    mov rdx, r13
    call memeq_raw
    cmp rax, 1
    jne .loop
    mov rdx, rbx
    inc rdx
    shl rdx, 3
    neg rdx
    mov rcx, [binding_const_flags + rbx * 8]
    mov r8, [binding_const_values + rbx * 8]
    mov r9, rbx
    mov rax, 1
    jmp .done
.no:
    xor rax, rax
.done:
    pop r13
    pop r12
    pop rbx
    ret

add_binding:
    push rbx
    push rdi
    push rsi
    push rdx
    push rcx
    call lookup_binding
    cmp rax, 1
    je .duplicate
    pop rcx
    pop rdx
    pop rsi
    pop rdi
    mov rbx, [binding_count]
    cmp rbx, BINDING_CAP
    jae .full
    mov [binding_name_ptrs + rbx * 8], rdi
    mov [binding_name_lens + rbx * 8], rsi
    mov [binding_const_flags + rbx * 8], rdx
    mov [binding_const_values + rbx * 8], rcx
    inc qword [binding_count]
    mov rdx, rbx
    inc rdx
    shl rdx, 3
    neg rdx
    mov rax, 1
    jmp .done
.duplicate:
    add rsp, 32
.full:
    xor rax, rax
.done:
    pop rbx
    ret

cg_emit_store_slot:
    push rdi
    mov rdi, strict qword cg_store_slot
    mov rsi, cg_store_slot_len
    call emit_blob
    pop rdi
    cmp rax, 0
    jne .ret
    call emit_u8
.ret:
    ret

cg_emit_load_slot:
    push rdi
    mov rdi, strict qword cg_load_slot
    mov rsi, cg_load_slot_len
    call emit_blob
    pop rdi
    cmp rax, 0
    jne .ret
    call emit_u8
.ret:
    ret

cg_emit_jz_placeholder:
    mov rdi, strict qword cg_branch_false
    mov rsi, cg_branch_false_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rdx, [code_cursor]
    sub rdx, 4
.ret:
    ret

cg_emit_jmp_placeholder:
    mov rdi, strict qword cg_jump
    mov rsi, cg_jump_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rdx, [code_cursor]
    sub rdx, 4
.ret:
    ret

; Validate a statically known byte-memory range. Unknown operands are deferred
; to the generated unsigned guard. Offset must name a byte; count may be zero.
cg_validate_io_const_range:
    cmp qword [io_range_offset_const_flag], 1
    jne .count_only
    mov rax, [io_range_offset_const_value]
    call profile_cmp_rax
    nop
    jae .invalid
.count_only:
    cmp qword [io_range_count_const_flag], 1
    jne .valid
    mov rax, [io_range_count_const_value]
    call profile_cmp_rax
    nop
    ja .invalid
    cmp qword [io_range_offset_const_flag], 1
    jne .valid
    mov rdx, [io_range_offset_const_value]
    add rdx, rax
    jc .invalid
    call profile_cmp_rdx
    times 2 db 0x90
    ja .invalid
.valid:
    xor rax, rax
    ret
.invalid:
    mov rax, 1
    ret

; Generated RAX is count and the generated stack top is offset. The copied
; template validates offset, count, addition overflow, and the exclusive end.
; Its four rel32 branches all join the existing byte-memory runtime handler.
cg_emit_byte_range_guard:
    mov rax, [byte_oob_patch_count]
    cmp rax, BYTE_ACCESS_CAP - 4
    ja .limit
    mov rax, [code_cursor]
    mov [range_guard_cursor], rax
    mov rdi, strict qword cg_byte_range_guard
    mov rsi, cg_byte_range_guard_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rax, [byte_oob_patch_count]
    mov rdx, [range_guard_cursor]
    add rdx, cg_byte_range_offset_disp_offset
    mov [byte_oob_patches + rax * 8], rdx
    inc rax
    mov rdx, [range_guard_cursor]
    add rdx, cg_byte_range_count_disp_offset
    mov [byte_oob_patches + rax * 8], rdx
    inc rax
    mov rdx, [range_guard_cursor]
    add rdx, cg_byte_range_overflow_disp_offset
    mov [byte_oob_patches + rax * 8], rdx
    inc rax
    mov rdx, [range_guard_cursor]
    add rdx, cg_byte_range_end_disp_offset
    mov [byte_oob_patches + rax * 8], rdx
    inc rax
    mov [byte_oob_patch_count], rax
    xor rax, rax
    ret
.limit:
    mov rax, 2
.ret:
    ret

cg_emit_input_read:
    mov rax, [io_read_error_patch_count]
    cmp rax, IO_PATCH_CAP
    jae .limit
    mov rax, [code_cursor]
    mov [io_emit_cursor], rax
    mov rdi, strict qword cg_input_read
    mov rsi, cg_input_read_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rax, [io_read_error_patch_count]
    mov rdx, [io_emit_cursor]
    add rdx, cg_input_read_error_disp_offset
    mov [io_read_error_patches + rax * 8], rdx
    inc qword [io_read_error_patch_count]
    xor rax, rax
    ret
.limit:
    mov rax, 2
.ret:
    ret

cg_emit_output_write:
    mov rax, [io_write_error_patch_count]
    cmp rax, IO_PATCH_CAP
    jae .limit
    mov rax, [code_cursor]
    mov [io_emit_cursor], rax
    mov rdi, strict qword cg_output_write
    mov rsi, cg_output_write_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rax, [io_write_error_patch_count]
    mov rdx, [io_emit_cursor]
    add rdx, cg_output_write_error_disp_offset
    mov [io_write_error_patches + rax * 8], rdx
    inc qword [io_write_error_patch_count]
    xor rax, rax
    ret
.limit:
    mov rax, 2
.ret:
    ret

cg_emit_error_write:
    mov rax, [io_error_write_patch_count]
    cmp rax, IO_PATCH_CAP
    jae .limit
    mov rax, [code_cursor]
    mov [io_emit_cursor], rax
    mov rdi, strict qword cg_error_write
    mov rsi, cg_error_write_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rax, [io_error_write_patch_count]
    mov rdx, [io_emit_cursor]
    add rdx, cg_error_write_error_disp_offset
    mov [io_error_write_patches + rax * 8], rdx
    inc qword [io_error_write_patch_count]
    xor rax, rax
    ret
.limit:
    mov rax, 2
.ret:
    ret

; Generated programs ignore SIGPIPE so a failed pipe write reaches the normal
; write-result branch. A setup failure has its own deterministic diagnostic.
cg_finalize_sigpipe_error_handler:
    mov rax, [code_cursor]
    mov [runtime_handler_cursor], rax
    mov rdi, strict qword cg_sigpipe_error_handler
    mov rsi, cg_sigpipe_error_handler_len
    call emit_blob
    cmp rax, 0
    jne .done
    mov rdi, [runtime_handler_cursor]
    add rdi, cg_sigpipe_error_message_disp_offset
    mov rsi, [code_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    mov rdi, strict qword cg_sigpipe_error_message
    mov rsi, cg_sigpipe_error_message_len
    call emit_blob
    cmp rax, 0
    jne .done
    mov rdi, [sigpipe_setup_error_patch]
    mov rsi, [runtime_handler_cursor]
    call patch_rel32
.done:
    ret

; Emit an unsigned bounds check for the byte index currently in generated
; RAX, then retain the rel32 field for one shared runtime diagnostic handler.
cg_emit_byte_guard_rax:
    mov rax, [byte_oob_patch_count]
    cmp rax, BYTE_ACCESS_CAP
    jae .limit
    mov rdi, strict qword cg_byte_guard_rax
    mov rsi, cg_byte_guard_rax_len
    call emit_blob
    cmp rax, 0
    jne .ret
    mov rax, [byte_oob_patch_count]
    mov rdx, [code_cursor]
    sub rdx, 4
    mov [byte_oob_patches + rax * 8], rdx
    inc qword [byte_oob_patch_count]
    xor rax, rax
    ret
.limit:
    mov rax, 2
.ret:
    ret

; Append one stderr+exit handler only when byte access exists, then resolve
; every guard to it. Normal paths already terminate before this tail.
cg_finalize_byte_oob_handler:
    push rbx
    mov rbx, [byte_oob_patch_count]
    test rbx, rbx
    jz .success
    mov rax, [code_cursor]
    mov [byte_oob_handler_cursor], rax
    mov rdi, strict qword cg_byte_oob_handler
    mov rsi, cg_byte_oob_handler_len
    call emit_blob
    cmp rax, 0
    jne .done
    mov rdi, [byte_oob_handler_cursor]
    add rdi, cg_byte_oob_message_disp_offset
    mov rsi, [code_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    mov rdi, strict qword cg_byte_oob_message
    mov rsi, cg_byte_oob_message_len
    call emit_blob
    cmp rax, 0
    jne .done
    xor rbx, rbx
.patch_loop:
    cmp rbx, [byte_oob_patch_count]
    jae .success
    mov rdi, [byte_oob_patches + rbx * 8]
    mov rsi, [byte_oob_handler_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    inc rbx
    jmp .patch_loop
.success:
    xor rax, rax
.done:
    pop rbx
    ret

cg_finalize_input_error_handler:
    push rbx
    mov rbx, [io_read_error_patch_count]
    test rbx, rbx
    jz .success
    mov rax, [code_cursor]
    mov [runtime_handler_cursor], rax
    mov rdi, strict qword cg_input_error_handler
    mov rsi, cg_input_error_handler_len
    call emit_blob
    cmp rax, 0
    jne .done
    mov rdi, [runtime_handler_cursor]
    add rdi, cg_input_error_message_disp_offset
    mov rsi, [code_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    mov rdi, strict qword cg_input_error_message
    mov rsi, cg_input_error_message_len
    call emit_blob
    cmp rax, 0
    jne .done
    xor rbx, rbx
.patch_loop:
    cmp rbx, [io_read_error_patch_count]
    jae .success
    mov rdi, [io_read_error_patches + rbx * 8]
    mov rsi, [runtime_handler_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    inc rbx
    jmp .patch_loop
.success:
    xor rax, rax
.done:
    pop rbx
    ret

cg_finalize_output_error_handler:
    push rbx
    mov rbx, [io_write_error_patch_count]
    test rbx, rbx
    jz .success
    mov rax, [code_cursor]
    mov [runtime_handler_cursor], rax
    mov rdi, strict qword cg_output_error_handler
    mov rsi, cg_output_error_handler_len
    call emit_blob
    cmp rax, 0
    jne .done
    mov rdi, [runtime_handler_cursor]
    add rdi, cg_output_error_message_disp_offset
    mov rsi, [code_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    mov rdi, strict qword cg_output_error_message
    mov rsi, cg_output_error_message_len
    call emit_blob
    cmp rax, 0
    jne .done
    xor rbx, rbx
.patch_loop:
    cmp rbx, [io_write_error_patch_count]
    jae .success
    mov rdi, [io_write_error_patches + rbx * 8]
    mov rsi, [runtime_handler_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    inc rbx
    jmp .patch_loop
.success:
    xor rax, rax
.done:
    pop rbx
    ret

; error_write already targets stderr, so a failed diagnostic write cannot
; report another diagnostic. Resolve every failure branch to a direct exit 74.
cg_finalize_error_write_handler:
    push rbx
    mov rbx, [io_error_write_patch_count]
    test rbx, rbx
    jz .success
    mov rax, [code_cursor]
    mov [runtime_handler_cursor], rax
    mov rdi, strict qword cg_error_write_error_handler
    mov rsi, cg_error_write_error_handler_len
    call emit_blob
    cmp rax, 0
    jne .done
    xor rbx, rbx
.patch_loop:
    cmp rbx, [io_error_write_patch_count]
    jae .success
    mov rdi, [io_error_write_patches + rbx * 8]
    mov rsi, [runtime_handler_cursor]
    call patch_rel32
    cmp rax, 0
    jne .done
    inc rbx
    jmp .patch_loop
.success:
    xor rax, rax
.done:
    pop rbx
    ret

patch_rel32:
    mov rax, rsi
    lea rdx, [rdi + 4]
    sub rax, rdx
    movsxd rcx, eax
    cmp rcx, rax
    jne .limit
    mov [rdi], eax
    xor rax, rax
    ret
.limit:
    mov rax, 2
    ret

; R8/R9 and R10/R11 are lhs/rhs value/constant metadata; RBX is CG_OP_*.
cg_combine_binary:
    cmp rbx, CG_OP_DIV
    jne .emit
    cmp r11, 1
    jne .emit
    test r10, r10
    jz .division_zero
    cmp r9, 1
    jne .emit
    mov rax, 0x8000000000000000
    cmp r8, rax
    jne .emit
    cmp r10, -1
    je .division_overflow
.emit:
    call cg_emit_binary
    cmp rax, 0
    jne .ret
    cmp r9, 1
    jne .not_constant
    cmp r11, 1
    jne .not_constant
    mov rcx, 1
    cmp rbx, CG_OP_ADD
    je .const_add
    cmp rbx, CG_OP_SUB
    je .const_sub
    cmp rbx, CG_OP_MUL
    je .const_mul
    cmp rbx, CG_OP_DIV
    je .const_div
    cmp rbx, CG_OP_EQ
    je .const_eq
    cmp rbx, CG_OP_NEQ
    je .const_neq
    cmp rbx, CG_OP_LT
    je .const_lt
    cmp rbx, CG_OP_LTE
    je .const_lte
    jmp .not_constant
.const_add:
    mov rdx, r8
    add rdx, r10
    jmp .success
.const_sub:
    mov rdx, r8
    sub rdx, r10
    jmp .success
.const_mul:
    mov rdx, r8
    imul rdx, r10
    jmp .success
.const_div:
    mov rax, r8
    cqo
    idiv r10
    mov rdx, rax
    jmp .success
.const_eq:
    xor rdx, rdx
    cmp r8, r10
    sete dl
    jmp .success
.const_neq:
    xor rdx, rdx
    cmp r8, r10
    setne dl
    jmp .success
.const_lt:
    xor rdx, rdx
    cmp r8, r10
    setl dl
    jmp .success
.const_lte:
    xor rdx, rdx
    cmp r8, r10
    setle dl
    jmp .success
.not_constant:
    xor rcx, rcx
    xor rdx, rdx
.success:
    xor rax, rax
.ret:
    ret
.division_zero:
    mov rax, 3
    ret
.division_overflow:
    mov rax, 6
    ret

cg_emit_binary:
    push rbx
    mov rdi, strict qword cg_binary_prepare
    mov rsi, cg_binary_prepare_len
    call emit_blob
    cmp rax, 0
    jne .done
    cmp rbx, CG_OP_ADD
    je .add
    cmp rbx, CG_OP_SUB
    je .sub
    cmp rbx, CG_OP_MUL
    je .mul
    cmp rbx, CG_OP_DIV
    je .div
    cmp rbx, CG_OP_EQ
    je .eq
    cmp rbx, CG_OP_NEQ
    je .neq
    cmp rbx, CG_OP_LT
    je .lt
    cmp rbx, CG_OP_LTE
    je .lte
    mov rax, 1
    jmp .done
.add:
    mov rdi, strict qword cg_add
    mov rsi, cg_add_len
    jmp .emit
.sub:
    mov rdi, strict qword cg_sub
    mov rsi, cg_sub_len
    jmp .emit
.mul:
    mov rdi, strict qword cg_mul
    mov rsi, cg_mul_len
    jmp .emit
.div:
    mov rdi, strict qword cg_div
    mov rsi, cg_div_len
    jmp .emit
.eq:
    mov rdi, strict qword cg_eq
    mov rsi, cg_eq_len
    jmp .emit
.neq:
    mov rdi, strict qword cg_neq
    mov rsi, cg_neq_len
    jmp .emit
.lt:
    mov rdi, strict qword cg_lt
    mov rsi, cg_lt_len
    jmp .emit
.lte:
    mov rdi, strict qword cg_lte
    mov rsi, cg_lte_len
.emit:
    call emit_blob
.done:
    pop rbx
    ret

emit_blob:
    jmp near profile_emit_blob
.legacy_saved:
    push r9
    push r10
    push r11
    mov r8, rdi
    mov rcx, rsi
    mov rdi, [code_cursor]
    mov rax, rdi
    add rax, rcx
    jc .limit
    lea r9, [output_buf + OUTPUT_CAP]
    cmp rax, r9
    ja .limit
    mov rsi, r8
    rep movsb
    mov [code_cursor], rdi
    xor rax, rax
    jmp .done
.limit:
    mov rax, 2
.done:
    pop r11
    pop r10
    pop r9
    pop r8
    pop rdx
    pop rcx
    pop rbx
    ret

emit_u64:
    push rdx
    mov rax, [code_cursor]
    lea rdx, [rax + 8]
    cmp rdx, output_buf + OUTPUT_CAP
    ja .limit
    mov [rax], rdi
    mov [code_cursor], rdx
    xor rax, rax
    pop rdx
    ret
.limit:
    mov rax, 2
    pop rdx
    ret

emit_u8:
    push rdx
    mov rax, [code_cursor]
    lea rdx, [rax + 1]
    cmp rdx, output_buf + OUTPUT_CAP
    ja .limit
    mov [rax], dil
    mov [code_cursor], rdx
    xor rax, rax
    pop rdx
    ret
.limit:
    mov rax, 2
    pop rdx
    ret

parse_string_literal:
    call skip_trivia
    cmp r12, r13
    jae .no
    cmp byte [r12], '"'
    jne .no
    inc r12
    inc r15
    xor rdx, rdx
.loop:
    cmp r12, r13
    jae .no
    mov al, [r12]
    cmp al, '"'
    je .done
    cmp al, 10
    je .no
    cmp al, 13
    je .no
    cmp al, '\'
    je .escape
.append:
    cmp rdx, STRING_CAP
    jae .too_long
    mov [string_buf + rdx], al
    inc rdx
    inc r12
    inc r15
    jmp .loop
.escape:
    inc r12
    inc r15
    cmp r12, r13
    jae .no
    mov al, [r12]
    cmp al, 'n'
    je .escape_newline
    cmp al, 'r'
    je .escape_carriage
    cmp al, 't'
    je .escape_tab
    cmp al, '\'
    je .append
    cmp al, '"'
    je .append
    jmp .no
.escape_newline:
    mov al, 10
    jmp .append
.escape_carriage:
    mov al, 13
    jmp .append
.escape_tab:
    mov al, 9
    jmp .append
.done:
    inc r12
    inc r15
    mov rax, 1
    ret
.too_long:
    mov rax, 2
    ret
.no:
    xor rax, rax
    ret

parse_u32_literal:
    call skip_trivia
    cmp r12, r13
    jae .no
    xor rdx, rdx
    xor r8, r8
.loop:
    cmp r12, r13
    jae .done
    movzx ecx, byte [r12]
    cmp cl, '0'
    jb .done
    cmp cl, '9'
    ja .done
    sub ecx, '0'
    cmp rdx, 429496729
    ja .no
    jne .accumulate
    cmp ecx, 5
    ja .no
.accumulate:
    imul rdx, rdx, 10
    add rdx, rcx
    inc r12
    inc r15
    inc r8
    jmp .loop
.done:
    test r8, r8
    jz .no
    mov rax, 1
    ret
.no:
    xor rax, rax
    ret

copy_bytes:
    test rdx, rdx
    jz .done
.loop:
    mov al, [rsi]
    mov [rdi], al
    inc rsi
    inc rdi
    dec rdx
    jnz .loop
.done:
    ret

read_input_file:
    push r12
    push r13
    mov r13, rdi
    mov rax, SYS_OPEN
    mov rdi, r13
    mov rsi, O_RDONLY
    xor rdx, rdx
    syscall
    test rax, rax
    js io_error
    mov r12, rax
    xor r13, r13
.read_loop:
    cmp r13, INPUT_CAP
    jb .read_chunk
    mov rax, SYS_READ
    mov rdi, r12
    lea rsi, [one_char]
    mov rdx, 1
    syscall
    test rax, rax
    js .read_fail
    jz .read_done
    mov rax, SYS_CLOSE
    mov rdi, r12
    syscall
    jmp input_limit_error
.read_chunk:
    mov rax, SYS_READ
    mov rdi, r12
    lea rsi, [input_buf + r13]
    mov rdx, INPUT_CAP
    sub rdx, r13
    syscall
    test rax, rax
    js .read_fail
    jz .read_done
    add r13, rax
    jmp .read_loop
.read_done:
    mov byte [input_buf + r13], 0
    mov rax, SYS_CLOSE
    mov rdi, r12
    syscall
    mov rax, r13
    pop r13
    pop r12
    ret
.read_fail:
    mov rax, SYS_CLOSE
    mov rdi, r12
    syscall
    jmp io_error

write_output_file:
    push r12
    push r13
    push r14
    mov r12, rsi
    mov r13, rdx
    mov rax, SYS_OPEN
    mov rsi, O_WRONLY_CREAT_TRUNC
    mov rdx, MODE_755
    syscall
    test rax, rax
    js io_error
    mov r14, rax
    mov rdi, r14
    mov rsi, r12
    mov rdx, r13
    call write_all_or_die
    mov rax, SYS_CLOSE
    mov rdi, r14
    syscall
    test rax, rax
    js io_error
    pop r14
    pop r13
    pop r12
    ret

write_all_or_die:
    push r12
    push r13
    push r14
    mov r12, rdi
    mov r13, rsi
    mov r14, rdx
.write_loop:
    test r14, r14
    jz .write_done
    mov rax, SYS_WRITE
    mov rdi, r12
    mov rsi, r13
    mov rdx, r14
    syscall
    test rax, rax
    jle io_error
    add r13, rax
    sub r14, rax
    jmp .write_loop
.write_done:
    pop r14
    pop r13
    pop r12
    ret

parse_core:
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, strict qword input_buf
    mov r13, strict qword input_buf
    add r13, [input_len]
    mov r14, 1
    mov r15, 1
    mov byte [seen_main], 0
    call skip_trivia
    cmp r12, r13
    jb .loop
    call parse_error
    jmp .done_ret
.loop:
    cmp r12, r13
    jae .done
    call parse_function
    cmp rax, 0
    jne .done_ret
    call skip_trivia
    jmp .loop
.done:
    cmp byte [seen_main], 1
    je .success
    call parse_error
    jmp .done_ret
.success:
    xor rax, rax
.done_ret:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

parse_function:
    mov rdi, strict qword kw_fn
    mov rsi, kw_fn_len
    call expect_word
    cmp rax, 0
    jne .ret
    call parse_identifier
    cmp rax, 0
    jne .ret
    cmp rcx, kw_main_len
    jne .not_main
    mov rdi, rdx
    mov rsi, strict qword kw_main
    mov rdx, kw_main_len
    call memeq_raw
    cmp rax, 1
    jne .not_main
    cmp byte [seen_main], 1
    je parse_error
    mov byte [seen_main], 1
.not_main:
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    call parse_block
.ret:
    ret

parse_block:
    call skip_trivia
    cmp r12, r13
    jae parse_error
    mov rdi, strict qword lit_rbrace
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .ok
    call parse_statement
    cmp rax, 0
    jne .ret
    jmp parse_block
.ok:
    xor rax, rax
.ret:
    ret

parse_statement:
    mov rdi, strict qword kw_let
    mov rsi, kw_let_len
    call match_word
    cmp rax, 1
    jne .not_let
    call parse_identifier
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_eq
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    call parse_expr
    cmp rax, 0
    jne .ret
    call match_optional_semi
    xor rax, rax
    ret
.not_let:
    mov rdi, strict qword kw_return
    mov rsi, kw_return_len
    call match_word
    cmp rax, 1
    jne .not_return
    call parse_expr
    cmp rax, 0
    jne .ret
    call match_optional_semi
    xor rax, rax
    ret
.not_return:
    mov rdi, strict qword kw_if
    mov rsi, kw_if_len
    call match_word
    cmp rax, 1
    jne .not_if
    call parse_expr
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    call parse_block
    cmp rax, 0
    jne .ret
    mov rdi, strict qword kw_else
    mov rsi, kw_else_len
    call expect_word
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    call parse_block
    ret
.not_if:
    mov rdi, strict qword kw_while
    mov rsi, kw_while_len
    call match_word
    cmp rax, 1
    jne .not_while
    call parse_expr
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_lbrace
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    call parse_block
    ret
.not_while:
    call parse_identifier
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_eq
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .assignment
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .call_done
    call parse_expr
    cmp rax, 0
    jne .ret
.call_arg_loop:
    mov rdi, strict qword lit_comma
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .call_close
    call parse_expr
    cmp rax, 0
    jne .ret
    jmp .call_arg_loop
.call_close:
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
.call_done:
    call match_optional_semi
    xor rax, rax
    jmp .ret
.assignment:
    call parse_expr
    cmp rax, 0
    jne .ret
    call match_optional_semi
    xor rax, rax
.ret:
    ret

parse_expr:
    call parse_primary
    cmp rax, 0
    jne .ret
.op_loop:
    call match_operator
    cmp rax, 1
    jne .ok
    call parse_primary
    cmp rax, 0
    jne .ret
    jmp .op_loop
.ok:
    xor rax, rax
.ret:
    ret

parse_primary:
    call skip_trivia
    cmp r12, r13
    jae parse_error
    mov al, [r12]
    call is_digit_al
    cmp rax, 1
    je .integer
    mov al, [r12]
    cmp al, '"'
    je .string
    mov al, [r12]
    cmp al, '('
    je .group
    call parse_identifier
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .ok
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .ok
    call parse_expr
    cmp rax, 0
    jne .ret
.call_arg_loop:
    mov rdi, strict qword lit_comma
    mov rsi, 1
    call match_lit
    cmp rax, 1
    jne .call_close
    call parse_expr
    cmp rax, 0
    jne .ret
    jmp .call_arg_loop
.call_close:
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call expect_lit
    ret
.integer:
    inc r12
    inc r15
.integer_loop:
    cmp r12, r13
    jae .ok
    mov al, [r12]
    call is_digit_al
    cmp rax, 1
    jne .ok
    inc r12
    inc r15
    jmp .integer_loop
.string:
    inc r12
    inc r15
.string_loop:
    cmp r12, r13
    jae parse_error
    mov al, [r12]
    cmp al, '"'
    je .string_done
    cmp al, 10
    je parse_error
    cmp al, 13
    je parse_error
    cmp al, '\'
    jne .string_next
    inc r12
    inc r15
    cmp r12, r13
    jae parse_error
.string_next:
    inc r12
    inc r15
    jmp .string_loop
.string_done:
    inc r12
    inc r15
    jmp .ok
.group:
    mov rdi, strict qword lit_lparen
    mov rsi, 1
    call expect_lit
    cmp rax, 0
    jne .ret
    call parse_expr
    cmp rax, 0
    jne .ret
    mov rdi, strict qword lit_rparen
    mov rsi, 1
    call expect_lit
    ret
.ok:
    xor rax, rax
.ret:
    ret

match_optional_semi:
    mov rdi, strict qword lit_semi
    mov rsi, 1
    call match_lit
    xor rax, rax
    ret

match_operator:
    mov rdi, strict qword lit_eqeq
    mov rsi, 2
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_neq
    mov rsi, 2
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_lte
    mov rsi, 2
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_lt
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_plus
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_minus
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_star
    mov rsi, 1
    call match_lit
    cmp rax, 1
    je .yes
    mov rdi, strict qword lit_slash
    mov rsi, 1
    call match_lit
    ret
.yes:
    mov rax, 1
    ret

parse_identifier:
    call skip_trivia
    cmp r12, r13
    jae parse_error
    mov al, [r12]
    call is_ident_start_al
    cmp rax, 1
    jne parse_error
    mov rdx, r12
    xor rcx, rcx
.loop:
    cmp r12, r13
    jae .done
    mov al, [r12]
    call is_ident_part_al
    cmp rax, 1
    jne .done
    inc r12
    inc r15
    inc rcx
    jmp .loop
.done:
    xor rax, rax
    ret

expect_word:
    call match_word
    cmp rax, 1
    jne parse_error
    xor rax, rax
    ret

match_word:
    call skip_trivia
    push rbx
    xor rbx, rbx
.cmp_loop:
    cmp rbx, rsi
    jae .boundary
    lea rax, [r12 + rbx]
    cmp rax, r13
    jae .no
    mov al, [rax]
    cmp al, [rdi + rbx]
    jne .no
    inc rbx
    jmp .cmp_loop
.boundary:
    lea rax, [r12 + rsi]
    cmp rax, r13
    jae .yes
    mov al, [rax]
    call is_ident_part_al
    cmp rax, 1
    je .no
.yes:
    add r12, rsi
    add r15, rsi
    pop rbx
    mov rax, 1
    ret
.no:
    pop rbx
    xor rax, rax
    ret

expect_lit:
    call match_lit
    cmp rax, 1
    jne parse_error
    xor rax, rax
    ret

match_lit:
    call skip_trivia
    push rbx
    xor rbx, rbx
.cmp_loop:
    cmp rbx, rsi
    jae .yes
    lea rax, [r12 + rbx]
    cmp rax, r13
    jae .no
    mov al, [r12 + rbx]
    cmp al, [rdi + rbx]
    jne .no
    inc rbx
    jmp .cmp_loop
.yes:
    add r12, rsi
    add r15, rsi
    pop rbx
    mov rax, 1
    ret
.no:
    pop rbx
    xor rax, rax
    ret

skip_trivia:
    cmp r12, r13
    jae .done
    mov al, [r12]
    cmp al, 10
    je .newline
    cmp al, 13
    je .carriage
    cmp al, ' '
    je .space
    cmp al, 9
    je .space
    cmp al, '#'
    je .hash_comment
    cmp al, '/'
    jne .done
    lea rax, [r12 + 1]
    cmp rax, r13
    jae .done
    cmp byte [r12 + 1], '/'
    jne .done
    add r12, 2
    add r15, 2
.slash_comment:
    cmp r12, r13
    jae skip_trivia
    cmp byte [r12], 10
    je skip_trivia
    inc r12
    inc r15
    jmp .slash_comment
.hash_comment:
    inc r12
    inc r15
.hash_loop:
    cmp r12, r13
    jae skip_trivia
    cmp byte [r12], 10
    je skip_trivia
    inc r12
    inc r15
    jmp .hash_loop
.newline:
    inc r12
    inc r14
    mov r15, 1
    jmp skip_trivia
.carriage:
    lea rax, [r12 + 1]
    cmp rax, r13
    jae parse_error
    cmp byte [r12 + 1], 10
    jne parse_error
    add r12, 2
    inc r14
    mov r15, 1
    jmp skip_trivia
.space:
    inc r12
    inc r15
    jmp skip_trivia
.done:
    ret

parse_error:
    mov rdi, strict qword msg_parse_error
    mov rsi, msg_parse_error_len
    call print_source_error
    mov rax, 1
    ret

memeq_raw:
    push rbx
    xor rbx, rbx
.loop:
    cmp rbx, rdx
    jae .yes
    mov al, [rdi + rbx]
    cmp al, [rsi + rbx]
    jne .no
    inc rbx
    jmp .loop
.yes:
    pop rbx
    mov rax, 1
    ret
.no:
    pop rbx
    xor rax, rax
    ret

lex_core:
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov [dump_mode], dil
    mov r12, strict qword input_buf
    mov r13, strict qword input_buf
    add r13, [input_len]
    mov r14, 1
    mov r15, 1
.loop:
    cmp r12, r13
    jae .ok
    mov al, [r12]
    cmp al, 10
    je .newline
    cmp al, 13
    je .carriage
    cmp al, ' '
    je .space
    cmp al, 9
    je .space
    cmp al, '#'
    je .hash_comment
    cmp al, '/'
    jne .not_slash
    lea rax, [r12 + 1]
    cmp rax, r13
    jae .punct
    cmp byte [r12 + 1], '/'
    jne .punct
    add r12, 2
    add r15, 2
.comment_loop:
    cmp r12, r13
    jae .loop
    cmp byte [r12], 10
    je .loop
    inc r12
    inc r15
    jmp .comment_loop
.hash_comment:
    inc r12
    inc r15
.hash_comment_loop:
    cmp r12, r13
    jae .loop
    cmp byte [r12], 10
    je .loop
    inc r12
    inc r15
    jmp .hash_comment_loop
.not_slash:
    mov al, [r12]
    call is_ident_start_al
    cmp rax, 1
    je .ident
    mov al, [r12]
    call is_digit_al
    cmp rax, 1
    je .integer
    mov al, [r12]
    cmp al, '"'
    je .string
    cmp al, '='
    je .maybe_eqeq
    cmp al, '!'
    je .maybe_neq
    cmp al, '<'
    je .maybe_lte
.punct:
    mov al, [r12]
    call is_punct_al
    cmp rax, 1
    jne .invalid
    mov rcx, 1
.emit_punct:
    mov rbx, r12
    inc r12
    inc r15
    cmp rcx, 2
    jne .emit_punct_print
    inc r12
    inc r15
.emit_punct_print:
    cmp byte [dump_mode], 0
    je .loop
    mov rdi, strict qword tok_punct
    mov rsi, tok_punct_len
    mov rdx, rbx
    call print_token
    jmp .loop
.maybe_eqeq:
    lea rax, [r12 + 1]
    cmp rax, r13
    jae .punct
    cmp byte [r12 + 1], '='
    jne .punct
    mov rcx, 2
    jmp .emit_punct
.maybe_neq:
    lea rax, [r12 + 1]
    cmp rax, r13
    jae .invalid
    cmp byte [r12 + 1], '='
    jne .invalid
    mov rcx, 2
    jmp .emit_punct
.maybe_lte:
    lea rax, [r12 + 1]
    cmp rax, r13
    jae .punct
    cmp byte [r12 + 1], '='
    jne .punct
    mov rcx, 2
    jmp .emit_punct
.newline:
    inc r12
    inc r14
    mov r15, 1
    jmp .loop
.carriage:
    lea rax, [r12 + 1]
    cmp rax, r13
    jae .bad_cr
    cmp byte [r12 + 1], 10
    jne .bad_cr
    add r12, 2
    inc r14
    mov r15, 1
    jmp .loop
.bad_cr:
    mov rdi, strict qword msg_lex_cr
    mov rsi, msg_lex_cr_len
    call print_source_error
    mov rax, 1
    jmp .done
.space:
    inc r12
    inc r15
    jmp .loop
.ident:
    mov rbx, r12
.ident_loop:
    cmp r12, r13
    jae .ident_done
    mov al, [r12]
    call is_ident_part_al
    cmp rax, 1
    jne .ident_done
    inc r12
    inc r15
    jmp .ident_loop
.ident_done:
    cmp byte [dump_mode], 0
    je .loop
    mov rdi, rbx
    mov rsi, r12
    sub rsi, rbx
    push rdi
    push rsi
    call is_keyword
    pop rcx
    pop rdx
    cmp rax, 1
    jne .ident_print
    mov rdi, strict qword tok_kw
    mov rsi, tok_kw_len
    call print_token
    jmp .loop
.ident_print:
    mov rdi, strict qword tok_ident
    mov rsi, tok_ident_len
    call print_token
    jmp .loop
.integer:
    mov rbx, r12
.integer_loop:
    cmp r12, r13
    jae .integer_done
    mov al, [r12]
    call is_digit_al
    cmp rax, 1
    jne .integer_done
    inc r12
    inc r15
    jmp .integer_loop
.integer_done:
    cmp byte [dump_mode], 0
    je .loop
    mov rdi, strict qword tok_int
    mov rsi, tok_int_len
    mov rdx, rbx
    mov rcx, r12
    sub rcx, rbx
    call print_token
    jmp .loop
.string:
    inc r12
    inc r15
    mov rbx, r12
.string_loop:
    cmp r12, r13
    jae .unterminated
    mov al, [r12]
    cmp al, '"'
    je .string_done
    cmp al, 10
    je .unterminated
    cmp al, 13
    je .unterminated
    cmp al, '\'
    jne .string_next
    inc r12
    inc r15
    cmp r12, r13
    jae .unterminated
.string_next:
    inc r12
    inc r15
    jmp .string_loop
.string_done:
    cmp byte [dump_mode], 0
    je .string_close
    mov rdi, strict qword tok_string
    mov rsi, tok_string_len
    mov rdx, rbx
    mov rcx, r12
    sub rcx, rbx
    call print_token
.string_close:
    inc r12
    inc r15
    jmp .loop
.invalid:
    mov rdi, strict qword msg_lex_invalid
    mov rsi, msg_lex_invalid_len
    call print_source_error
    mov rax, 1
    jmp .done
.unterminated:
    mov rdi, strict qword msg_lex_unterminated
    mov rsi, msg_lex_unterminated_len
    call print_source_error
    mov rax, 1
    jmp .done
.ok:
    xor rax, rax
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

print_token:
    push rdx
    push rcx
    mov rdx, rsi
    mov rsi, rdi
    mov rdi, 1
    call write_all_or_die
    pop rdx
    pop rsi
    mov rdi, 1
    call write_all_or_die
    mov rdi, 1
    mov rsi, strict qword nl
    mov rdx, 1
    call write_all_or_die
    ret

print_source_error:
    push rdi
    push rsi
    mov rdi, 2
    mov rsi, [current_path]
    call strlen
    mov rdx, rax
    call write_all_or_die
    mov rdi, 2
    mov rsi, strict qword colon
    mov rdx, 1
    call write_all_or_die
    mov rdi, r14
    call print_u64_stderr
    mov rdi, 2
    mov rsi, strict qword colon
    mov rdx, 1
    call write_all_or_die
    mov rdi, r15
    call print_u64_stderr
    mov rdi, 2
    mov rsi, strict qword err_sep
    mov rdx, err_sep_len
    call write_all_or_die
    pop rdx
    pop rsi
    mov rdi, 2
    call write_all_or_die
    ret

print_u64_stderr:
    mov rax, rdi
    lea rsi, [dec_buf + 31]
    mov byte [rsi], 0
    mov r8, 10
.digits:
    xor rdx, rdx
    div r8
    add dl, '0'
    dec rsi
    mov [rsi], dl
    test rax, rax
    jne .digits
    lea rdx, [dec_buf + 31]
    sub rdx, rsi
    mov rdi, 2
    call write_all_or_die
    ret

strlen:
    xor rax, rax
.loop:
    cmp byte [rsi + rax], 0
    je .done
    inc rax
    jmp .loop
.done:
    ret

streq:
    xor rax, rax
.loop:
    mov dl, [rdi + rax]
    cmp dl, [rsi + rax]
    jne .no
    test dl, dl
    je .yes
    inc rax
    jmp .loop
.yes:
    mov rax, 1
    ret
.no:
    xor rax, rax
    ret

is_keyword:
    cmp rsi, 2
    jne .not_two
    cmp byte [rdi], 'f'
    jne .check_if
    cmp byte [rdi + 1], 'n'
    je .yes
.check_if:
    cmp byte [rdi], 'i'
    jne .no
    cmp byte [rdi + 1], 'f'
    jne .no
    jmp .yes
.not_two:
    cmp rsi, 3
    jne .not_let
    cmp byte [rdi], 'l'
    jne .no
    cmp byte [rdi + 1], 'e'
    jne .no
    cmp byte [rdi + 2], 't'
    jne .no
    jmp .yes
.not_let:
    cmp rsi, 4
    jne .not_else
    cmp dword [rdi], 0x65736c65
    jne .no
    jmp .yes
.not_else:
    cmp rsi, 5
    jne .not_while
    cmp dword [rdi], 0x6c696877
    jne .no
    cmp byte [rdi + 4], 'e'
    jne .no
    jmp .yes
.not_while:
    cmp rsi, 6
    jne .no
    cmp dword [rdi], 0x75746572
    jne .no
    cmp word [rdi + 4], 0x6e72
    jne .no
.yes:
    mov rax, 1
    ret
.no:
    xor rax, rax
    ret

is_ident_start_al:
    cmp al, '_'
    je .yes
    cmp al, 'A'
    jb .no
    cmp al, 'Z'
    jbe .yes
    cmp al, 'a'
    jb .no
    cmp al, 'z'
    jbe .yes
.no:
    xor rax, rax
    ret
.yes:
    mov rax, 1
    ret

is_ident_part_al:
    call is_ident_start_al
    cmp rax, 1
    je .yes
    call is_digit_al
    ret
.yes:
    mov rax, 1
    ret

is_digit_al:
    cmp al, '0'
    jb .no
    cmp al, '9'
    ja .no
    mov rax, 1
    ret
.no:
    xor rax, rax
    ret

is_punct_al:
    cmp al, '('
    je .yes
    cmp al, ')'
    je .yes
    cmp al, '{'
    je .yes
    cmp al, '}'
    je .yes
    cmp al, '+'
    je .yes
    cmp al, '-'
    je .yes
    cmp al, '*'
    je .yes
    cmp al, '/'
    je .yes
    cmp al, '='
    je .yes
    cmp al, ';'
    je .yes
    cmp al, ','
    je .yes
    cmp al, '<'
    je .yes
    xor rax, rax
    ret
.yes:
    mov rax, 1
    ret

    ; All predecessor text ends at 0x4251; extension must fit before rodata.
    times 0x4251 - ($ - image_start) db 0
profile_extension:
profile_args:
    mov rbx, [rsp]
    lea r12, [rsp + 8]
    cmp rbx, 5
    jne near .legacy_args
    mov rdi, [r12 + 8]
    mov rsi, strict qword profile_option
    call streq
    cmp rax, 1
    je near .before_input
    mov rdi, [r12 + 16]
    mov rsi, strict qword profile_option
    call streq
    cmp rax, 1
    je near .after_input
    mov rdi, [r12 + 32]
    mov rsi, strict qword profile_option
    call streq
    cmp rax, 1
    jne near usage_error
    jmp near .validate
.before_input:
    mov rax, [r12 + 16]
    mov [r12 + 8], rax
.after_input:
    mov rax, [r12 + 24]
    mov [r12 + 16], rax
    mov rax, [r12 + 32]
    mov [r12 + 24], rax
.validate:
    mov rdi, [r12 + 8]
    cmp byte [rdi], '-'
    je near usage_error
    mov rdi, [r12 + 24]
    mov rsi, strict qword profile_option
    call streq
    cmp rax, 1
    je near usage_error
    mov byte [compiler_profile], 1
    mov ebx, 4
    jmp near _start.legacy_start
.legacy_args:
    cmp rbx, 2
    jb near _start.legacy_start
    mov rdi, [r12 + 8]
    mov rsi, strict qword profile_option
    call streq
    cmp rax, 1
    je near usage_error
    cmp rbx, 3
    jne near _start.legacy_start
    mov rdi, [r12 + 16]
    mov rsi, strict qword profile_option
    call streq
    cmp rax, 1
    je near usage_error
    jmp near _start.legacy_start
profile_option db "--compiler-profile", 0

; Leaf helpers preserve all registers, returning only comparison flags.
profile_cmp_rax:
    cmp byte [compiler_profile], 0
    je near .legacy
    cmp rax, 0x1000000
    ret
.legacy:
    cmp rax, BYTE_MEMORY_CAP
    ret
profile_cmp_r11:
    cmp byte [compiler_profile], 0
    je near .legacy
    cmp r11, 0x1000000
    ret
.legacy:
    cmp r11, BYTE_MEMORY_CAP
    ret
profile_cmp_rdx:
    cmp byte [compiler_profile], 0
    je near .legacy
    cmp rdx, 0x1000000
    ret
.legacy:
    cmp rdx, BYTE_MEMORY_CAP
    ret
profile_bounds_message:
    mov rdi, strict qword msg_codegen_byte_bounds
    mov esi, msg_codegen_byte_bounds_len
    cmp byte [compiler_profile], 0
    je near .done
    mov rdi, strict qword profile_bounds_text
    mov esi, profile_bounds_text_end - profile_bounds_text
.done:
    ret
profile_bounds_text db " error[B0-CG-008]: byte-memory access must stay within 0..16777215", 10
profile_bounds_text_end:

profile_emit_blob:
    push rbx
    push rcx
    push rdx
    push r8
    cmp byte [compiler_profile], 0
    je near emit_blob.legacy_saved
    lea rbx, [rel profile_templates]
    mov edx, 14
.loop:
    cmp rdi, [rbx]
    je near .found
    add rbx, 24
    dec edx
    jnz near .loop
    jmp near emit_blob.legacy_saved
.found:
    mov rdi, [rbx + 8]
    mov rsi, [rbx + 16]
    sub rsi, rdi
    jmp near emit_blob.legacy_saved
profile_templates:
    dq cg_prologue, p_prologue, p_prologue_end
    dq cg_byte_guard_rax, p_guard, p_guard_end
    dq cg_byte_load, p_load, p_load_end
    dq cg_byte_store, p_store, p_store_end
    dq cg_byte_range_guard, p_range, p_range_end
    dq cg_input_read, p_read, p_read_end
    dq cg_output_write, p_write, p_write_end
    dq cg_error_write, p_error_write, p_error_write_end
    dq cg_exit, p_exit, p_exit_end
    dq cg_byte_oob_handler, p_oob_handler, p_oob_handler_end
    dq cg_input_error_handler, p_input_handler, p_input_handler_end
    dq cg_output_error_handler, p_output_handler, p_output_handler_end
    dq cg_error_write_error_handler, p_error_handler, p_error_handler_end
    dq cg_sigpipe_error_handler, p_sigpipe_handler, p_sigpipe_handler_end

profile_write_literal:
    cmp byte [compiler_profile], 0
    je near .legacy
    mov rdi, strict qword output_buf
    mov rsi, strict qword dynamic_code_elf
    mov edx, dynamic_code_prefix_len
    call copy_bytes
    mov qword [code_cursor], output_buf + dynamic_code_prefix_len
    mov rdi, strict qword p_prologue
    mov rsi, strict qword p_prologue_end
    sub rsi, rdi
    call emit_blob
    test rax, rax
    jne near compile_output_limit_error
    mov rbx, [code_cursor]
    mov rdi, strict qword p_literal
    mov rsi, strict qword p_literal_end
    sub rsi, rdi
    call emit_blob
    test rax, rax
    jne near compile_output_limit_error
    mov rax, [write_literal_len]
    mov [rbx + 8], eax
    mov rax, [write_return_value]
    mov [rbx + 65], eax
    mov rdi, strict qword string_buf
    mov rsi, [write_literal_len]
    call emit_blob
    test rax, rax
    jne near compile_output_limit_error
    mov rdx, [code_cursor]
    sub rdx, output_buf
    mov [code_output_len], rdx
    mov [output_buf + dynamic_code_filesz_offset], rdx
    mov [output_buf + dynamic_code_memsz_offset], rdx
    jmp near compile_expression_program
.legacy:
    mov rdi, strict qword output_buf
    jmp near compile_write_literal.legacy_entry

; Generated state: 16 RBP locals; R13 owns the mapping, R14 is its base.
; R12/RBX hold continuations; R15 records broken stderr across cleanup.
; No CALL means arbitrary expression depth is safe.
p_prologue:
    push rbp
    mov rbp, rsp
    add rsp, byte -128
    xor r13d, r13d
    lea r12, [rel p_cleanup]
    lea rbx, [rel p_diagnose]
    xor r15d, r15d
    sub rsp, 32
    mov qword [rsp], SIG_IGN
    mov qword [rsp + 8], 0
    mov qword [rsp + 16], 0
    mov qword [rsp + 24], 0
    mov eax, SYS_RT_SIGACTION
    mov edi, SIGPIPE
    mov rsi, rsp
    xor edx, edx
    mov r10d, KERNEL_SIGSET_BYTES
    syscall
    add rsp, 32
    test rax, rax
    js near p_sigpipe_failure
p_prologue_signal_disp equ $ - 4
    mov eax, 9
    xor edi, edi
    mov esi, 0x1000000
    mov edx, 3
    mov r10d, 0x22
    mov r8, strict dword -1
    xor r9d, r9d
    syscall
    test rax, rax
    js near p_mmap_failure
    mov r14, rax
    inc r13d
    jmp near p_prologue_end
p_cleanup:
    mov r8, rdi
    test r13d, r13d
    jz near p_runtime_exit
    xor r13d, r13d
    mov eax, 11
    mov rdi, r14
    mov esi, 0x1000000
    syscall
    test rax, rax
    jnz near p_munmap_failure
p_runtime_exit:
    mov rdi, r8
    mov eax, SYS_EXIT
    syscall
p_diagnose:
    mov r8, rdi
    mov edi, 2
.loop:
    mov eax, SYS_WRITE
    syscall
    cmp rax, -4
    je near .loop
    test rax, rax
    jle near .failed
    add rsi, rax
    sub rdx, rax
    jnz near .loop
    mov rdi, r8
    jmp r12
.failed:
    mov r15b, 1
    mov edi, IO_ERROR_EXIT_STATUS
    jmp r12
p_mmap_failure:
    lea rsi, [rel p_mmap_text]
    mov edx, p_munmap_text - p_mmap_text
    mov edi, IO_ERROR_EXIT_STATUS
    jmp rbx
p_munmap_failure:
    test r15d, r15d
    jnz near p_runtime_exit
    lea rsi, [rel p_munmap_text]
    mov edx, p_sigpipe_text - p_munmap_text
    mov edi, IO_ERROR_EXIT_STATUS
    jmp rbx
p_sigpipe_failure:
    lea rsi, [rel p_sigpipe_text]
    mov edx, p_prologue_end - p_sigpipe_text
    mov edi, IO_ERROR_EXIT_STATUS
    jmp rbx
p_mmap_text db "B0 runtime: mmap failed; free memory and retry", 10
p_munmap_text db "B0 runtime: munmap failed; check kernel mapping support", 10
p_sigpipe_text db "B0 runtime: cannot ignore SIGPIPE; check kernel signal support", 10
p_prologue_end:

; Same sizes and fixup offsets as the default templates.
p_guard:
    cmp rax, 0x1000000
    jae near $ + 6
p_guard_end:
p_load:
    mov rcx, r14
    times 4 db 0x90
    movzx eax, byte [rcx + rax]
p_load_end:
p_store:
    pop rcx
    mov rdx, r14
    times 4 db 0x90
    mov [rdx + rcx], al
p_store_end:
p_range:
    pop rcx
    cmp rcx, 0x1000000
    jae near $ + 6
    cmp rax, 0x1000000
    ja near $ + 6
    mov rdx, rcx
    add rdx, rax
    jc near $ + 6
    cmp rdx, 0x1000000
    ja near $ + 6
    push rcx
p_range_end:
p_read:
    pop rsi
    mov rdx, rax
    add rsi, r14
    xor edi, edi
.retry:
    xor eax, eax
    syscall
    cmp rax, -4
    je short .retry
    test rax, rax
    nop
    js near $ + 6
p_read_end:

%macro PROFILE_WRITE 2
%1:
    pop rsi
    mov rdx, rax
    add rsi, r14
    mov edi, %2
    test rdx, rdx
    jz short %%done
%%retry:
    mov eax, SYS_WRITE
    syscall
    cmp rax, -4
    je short %%retry
    test rax, rax
    nop
    jle near $ + 6
    add rsi, rax
    sub rdx, rax
    jnz short %%retry
%%done:
    xor eax, eax
%1_end:
%endmacro
PROFILE_WRITE p_write, 1
PROFILE_WRITE p_error_write, 2
p_exit:
    mov rdi, rax
    jmp r12
    times 4 db 0x90
p_exit_end:

%macro PROFILE_DIAGNOSTIC 3
%1:
    mov edi, %2
    times 5 db 0x90
    lea rsi, [rel $ + 7]
    mov edx, %3
    jmp rbx
    times 12 db 0x90
%1_end:
%endmacro
PROFILE_DIAGNOSTIC p_oob_handler, BYTE_OOB_EXIT_STATUS, cg_byte_oob_message_len
PROFILE_DIAGNOSTIC p_input_handler, IO_ERROR_EXIT_STATUS, cg_input_error_message_len
PROFILE_DIAGNOSTIC p_output_handler, IO_ERROR_EXIT_STATUS, cg_output_error_message_len
p_error_handler:
    mov r15b, 1
    mov edi, IO_ERROR_EXIT_STATUS
    jmp r12
    nop
p_error_handler_end:
PROFILE_DIAGNOSTIC p_sigpipe_handler, IO_ERROR_EXIT_STATUS, cg_sigpipe_error_message_len

p_literal:
    lea rsi, [rel p_literal_end]
    mov edx, 0
    mov edi, 1
    test rdx, rdx
    jz near .return
.loop:
    mov eax, SYS_WRITE
    syscall
    cmp rax, -4
    je near .loop
    test rax, rax
    jle near .error
    add rsi, rax
    sub rdx, rax
    jnz near .loop
.return:
    mov edi, 0
    jmp r12
.error:
    mov edi, IO_ERROR_EXIT_STATUS
    times 5 db 0x90
    lea rsi, [rel .error_text]
    mov edx, p_literal_end - .error_text
    jmp rbx
.error_text db "B0 runtime: output_write failed; check standard output", 10
p_literal_end:
profile_extension_end:
    times 0x5000 - ($ - image_start) db 0
opt_help db "--help", 0
opt_lex db "--lex", 0
opt_parse db "--parse", 0
opt_output db "-o", 0
msg_usage db "usage: b0 <input.nql> -o <output>", 10
msg_usage_len equ $ - msg_usage
msg_usage_err db "b0: error[B0-IO-000]: usage: b0 <input.nql> -o <output>", 10
msg_usage_err_len equ $ - msg_usage_err
msg_io_error db "b0: error[B0-IO-001]: input/output syscall failed", 10
msg_io_error_len equ $ - msg_io_error
msg_input_limit db "b0: error[B0-IO-003]: input exceeds 327680-byte limit", 10
msg_input_limit_len equ $ - msg_input_limit
msg_unsupported db "input.nql:1:1: error[B0-CG-001]: unsupported B0.2 source", 10
msg_unsupported_len equ $ - msg_unsupported
msg_codegen_unknown_call db "input.nql:2:5: error[B0-CG-002]: unsupported call in B0.4", 10
msg_codegen_unknown_call_len equ $ - msg_codegen_unknown_call
msg_codegen_type_mismatch db "input.nql:2:12: error[B0-CG-003]: type mismatch in integer expression", 10
msg_codegen_type_mismatch_len equ $ - msg_codegen_type_mismatch
msg_codegen_div_zero db "input.nql:2:14: error[B0-CG-004]: division by zero", 10
msg_codegen_div_zero_len equ $ - msg_codegen_div_zero
msg_codegen_output_limit db "input.nql:2:5: error[B0-CG-005]: generated executable would exceed B0 output limit", 10
msg_codegen_output_limit_len equ $ - msg_codegen_output_limit
msg_codegen_div_overflow db "input.nql:4:20: error[B0-CG-006]: signed division overflow", 10
msg_codegen_div_overflow_len equ $ - msg_codegen_div_overflow
msg_codegen_unknown_assignment db " error[B0-CG-007]: assignment target is not declared; declare it with let first", 10
msg_codegen_unknown_assignment_len equ $ - msg_codegen_unknown_assignment
msg_codegen_byte_bounds db " error[B0-CG-008]: byte-memory access must stay within 0..65535", 10
msg_codegen_byte_bounds_len equ $ - msg_codegen_byte_bounds
msg_parse_ok db "PARSE OK", 10
msg_parse_ok_len equ $ - msg_parse_ok
msg_parse_error db " error[B0-PARSE-001]: invalid Core-0 syntax", 10
msg_parse_error_len equ $ - msg_parse_error
msg_lex_invalid db " error[B0-LEX-001]: invalid character", 10
msg_lex_invalid_len equ $ - msg_lex_invalid
msg_lex_unterminated db " error[B0-LEX-002]: unterminated string literal", 10
msg_lex_unterminated_len equ $ - msg_lex_unterminated
msg_lex_cr db " error[B0-LEX-003]: CR line ending without LF", 10
msg_lex_cr_len equ $ - msg_lex_cr
tok_kw db "KW "
tok_kw_len equ $ - tok_kw
tok_ident db "IDENT "
tok_ident_len equ $ - tok_ident
tok_int db "INT "
tok_int_len equ $ - tok_int
tok_string db "STRING "
tok_string_len equ $ - tok_string
tok_punct db "PUNCT "
tok_punct_len equ $ - tok_punct
nl db 10
colon db ":"
err_sep db ":"
err_sep_len equ $ - err_sep
kw_fn db "fn"
kw_fn_len equ $ - kw_fn
kw_main db "main"
kw_main_len equ $ - kw_main
kw_let db "let"
kw_let_len equ $ - kw_let
kw_return db "return"
kw_return_len equ $ - kw_return
kw_if db "if"
kw_if_len equ $ - kw_if
kw_else db "else"
kw_else_len equ $ - kw_else
kw_while db "while"
kw_while_len equ $ - kw_while
lit_lparen db "("
lit_rparen db ")"
lit_lbrace db "{"
lit_rbrace db "}"
lit_eq db "="
lit_semi db ";"
lit_comma db ","
lit_eqeq db "=="
lit_neq db "!="
lit_lte db "<="
lit_lt db "<"
lit_plus db "+"
lit_minus db "-"
lit_star db "*"
lit_slash db "/"
name_write db "write"
name_write_len equ $ - name_write
name_byte_load db "byte_load"
name_byte_load_len equ $ - name_byte_load
name_byte_store db "byte_store"
name_byte_store_len equ $ - name_byte_store
name_input_read db "input_read"
name_input_read_len equ $ - name_input_read
name_output_write db "output_write"
name_output_write_len equ $ - name_output_write
name_error_write db "error_write"
name_error_write_len equ $ - name_error_write

return7_elf:
    db 0x7f, "ELF", 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0
    dw 2
    dw 0x3e
    dd 1
    dq 0x4000b0
    dq 0x40
    dq 0
    dd 0
    dw 0x40
    dw 0x38
    dw 2
    dw 0
    dw 0
    dw 0
    dd 1
    dd 5
    dq 0
    dq 0x400000
    dq 0x400000
    dq return7_elf_len
    dq return7_elf_len
    dq 0x1000
    dd 0x6474e551
    dd 6
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0x10
    times (0xb0 - ($ - return7_elf)) db 0
    mov eax, SYS_EXIT
return7_exit_status:
    mov edi, 7
    syscall
return7_elf_len equ $ - return7_elf
return_status_imm_offset equ return7_exit_status + 1 - return7_elf

dynamic_write_elf:
    db 0x7f, "ELF", 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0
    dw 2
    dw 0x3e
    dd 1
    dq 0x4000b0
    dq 0x40
    dq 0
    dd 0
    dw 0x40
    dw 0x38
    dw 2
    dw 0
    dw 0
    dw 0
    dd 1
    dd 5
    dq 0
    dq 0x400000
    dq 0x400000
dynamic_write_filesz:
    dq dynamic_write_prefix_len
dynamic_write_memsz:
    dq dynamic_write_prefix_len
    dq 0x1000
    dd 0x6474e551
    dd 6
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0x10
    times (0xb0 - ($ - dynamic_write_elf)) db 0
    mov eax, SYS_WRITE
    mov edi, 1
    mov esi, 0x400000 + (dynamic_write_msg - dynamic_write_elf)
dynamic_write_message_len:
    mov edx, 0
    syscall
    mov eax, SYS_EXIT
dynamic_write_return_status:
    mov edi, 0
    syscall
dynamic_write_msg:
dynamic_write_prefix_len equ $ - dynamic_write_elf
dynamic_write_filesz_offset equ dynamic_write_filesz - dynamic_write_elf
dynamic_write_memsz_offset equ dynamic_write_memsz - dynamic_write_elf
dynamic_write_message_len_imm_offset equ dynamic_write_message_len + 1 - dynamic_write_elf
dynamic_write_return_imm_offset equ dynamic_write_return_status + 1 - dynamic_write_elf

dynamic_code_elf:
    db 0x7f, "ELF", 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0
    dw 2
    dw 0x3e
    dd 1
    dq 0x4000b0
    dq 0x40
    dq 0
    dd 0
    dw 0x40
    dw 0x38
    dw 2
    dw 0
    dw 0
    dw 0
    dd 1
    dd 5
    dq 0
    dq 0x400000
    dq 0x400000
dynamic_code_filesz:
    dq dynamic_code_prefix_len
dynamic_code_memsz:
    dq dynamic_code_prefix_len
    dq 0x1000
    dd 0x6474e551
    dd 6
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0x10
    times (0xb0 - ($ - dynamic_code_elf)) db 0
dynamic_code_prefix_len equ $ - dynamic_code_elf
dynamic_code_filesz_offset equ dynamic_code_filesz - dynamic_code_elf
dynamic_code_memsz_offset equ dynamic_code_memsz - dynamic_code_elf

cg_prologue db 0x55, 0x48, 0x89, 0xe5, 0x48, 0x81, 0xec
    dd FRAME_STACK_BYTES
    db 0x48, 0x8d, 0xbd
    dd -FRAME_STACK_BYTES
    db 0x31, 0xc0, 0xb9
    dd BYTE_MEMORY_CAP / 8
    db 0xf3, 0x48, 0xab
    db 0x48, 0x83, 0xec, 0x20
    db 0x48, 0xc7, 0x04, 0x24
    dd SIG_IGN
    db 0x48, 0xc7, 0x44, 0x24, 0x08
    dd 0
    db 0x48, 0xc7, 0x44, 0x24, 0x10
    dd 0
    db 0x48, 0xc7, 0x44, 0x24, 0x18
    dd 0
    db 0xb8
    dd SYS_RT_SIGACTION
    db 0xbf
    dd SIGPIPE
    db 0x48, 0x89, 0xe6, 0x31, 0xd2, 0x41, 0xba
    dd KERNEL_SIGSET_BYTES
    db 0x0f, 0x05, 0x48, 0x83, 0xc4, 0x20, 0x48, 0x85, 0xc0, 0x0f, 0x88
cg_prologue_sigpipe_error_disp:
    dd 0
cg_prologue_len equ $ - cg_prologue
cg_prologue_sigpipe_error_disp_offset equ cg_prologue_sigpipe_error_disp - cg_prologue
cg_mov_rax_imm64 db 0x48, 0xb8
cg_mov_rax_imm64_len equ $ - cg_mov_rax_imm64
cg_push_rax db 0x50
cg_push_rax_len equ $ - cg_push_rax
cg_store_slot db 0x48, 0x89, 0x45
cg_store_slot_len equ $ - cg_store_slot
cg_load_slot db 0x48, 0x8b, 0x45
cg_load_slot_len equ $ - cg_load_slot
cg_branch_false db 0x48, 0x85, 0xc0, 0x0f, 0x84, 0, 0, 0, 0
cg_branch_false_len equ $ - cg_branch_false
cg_jump db 0xe9, 0, 0, 0, 0
cg_jump_len equ $ - cg_jump
cg_byte_guard_rax db 0x48, 0x3d
    dd BYTE_MEMORY_CAP
    db 0x0f, 0x83, 0, 0, 0, 0
cg_byte_guard_rax_len equ $ - cg_byte_guard_rax
cg_byte_load db 0x48, 0x8d, 0x8d
    dd -FRAME_STACK_BYTES
    db 0x0f, 0xb6, 0x04, 0x01
cg_byte_load_len equ $ - cg_byte_load
cg_byte_store db 0x59, 0x48, 0x8d, 0x95
    dd -FRAME_STACK_BYTES
    db 0x88, 0x04, 0x0a
cg_byte_store_len equ $ - cg_byte_store
cg_byte_range_guard:
    db 0x59, 0x48, 0x81, 0xf9
    dd BYTE_MEMORY_CAP
    db 0x0f, 0x83
cg_byte_range_offset_disp:
    dd 0
    db 0x48, 0x3d
    dd BYTE_MEMORY_CAP
    db 0x0f, 0x87
cg_byte_range_count_disp:
    dd 0
    db 0x48, 0x89, 0xca, 0x48, 0x01, 0xc2, 0x0f, 0x82
cg_byte_range_overflow_disp:
    dd 0
    db 0x48, 0x81, 0xfa
    dd BYTE_MEMORY_CAP
    db 0x0f, 0x87
cg_byte_range_end_disp:
    dd 0
    db 0x51
cg_byte_range_guard_len equ $ - cg_byte_range_guard
cg_byte_range_offset_disp_offset equ cg_byte_range_offset_disp - cg_byte_range_guard
cg_byte_range_count_disp_offset equ cg_byte_range_count_disp - cg_byte_range_guard
cg_byte_range_overflow_disp_offset equ cg_byte_range_overflow_disp - cg_byte_range_guard
cg_byte_range_end_disp_offset equ cg_byte_range_end_disp - cg_byte_range_guard
cg_input_read:
    db 0x5e, 0x48, 0x89, 0xc2, 0x48, 0x8d, 0x8d
    dd -FRAME_STACK_BYTES
    db 0x48, 0x01, 0xce, 0x31, 0xff, 0x31, 0xc0, 0x0f, 0x05
    db 0x48, 0x85, 0xc0, 0x0f, 0x88
cg_input_read_error_disp:
    dd 0
cg_input_read_len equ $ - cg_input_read
cg_input_read_error_disp_offset equ cg_input_read_error_disp - cg_input_read
cg_output_write:
    db 0x5e, 0x48, 0x89, 0xc2, 0x48, 0x8d, 0x8d
    dd -FRAME_STACK_BYTES
    db 0x48, 0x01, 0xce, 0xbf
    dd 1
    db 0x48, 0x85, 0xd2, 0x74
    db cg_output_write_done - ($ + 1)
cg_output_write_loop:
    db 0xb8
    dd SYS_WRITE
    db 0x0f, 0x05, 0x48, 0x85, 0xc0, 0x0f, 0x8e
cg_output_write_error_disp:
    dd 0
    db 0x48, 0x01, 0xc6, 0x48, 0x29, 0xc2, 0x75
    db cg_output_write_loop - ($ + 1)
cg_output_write_done:
    db 0x31, 0xc0
cg_output_write_len equ $ - cg_output_write
cg_output_write_error_disp_offset equ cg_output_write_error_disp - cg_output_write
cg_error_write:
    db 0x5e, 0x48, 0x89, 0xc2, 0x48, 0x8d, 0x8d
    dd -FRAME_STACK_BYTES
    db 0x48, 0x01, 0xce, 0xbf
    dd 2
    db 0x48, 0x85, 0xd2, 0x74
    db cg_error_write_done - ($ + 1)
cg_error_write_loop:
    db 0xb8
    dd SYS_WRITE
    db 0x0f, 0x05, 0x48, 0x85, 0xc0, 0x0f, 0x8e
cg_error_write_error_disp:
    dd 0
    db 0x48, 0x01, 0xc6, 0x48, 0x29, 0xc2, 0x75
    db cg_error_write_loop - ($ + 1)
cg_error_write_done:
    db 0x31, 0xc0
cg_error_write_len equ $ - cg_error_write
cg_error_write_error_disp_offset equ cg_error_write_error_disp - cg_error_write
cg_binary_prepare db 0x48, 0x89, 0xc1, 0x58
cg_binary_prepare_len equ $ - cg_binary_prepare
cg_add db 0x48, 0x01, 0xc8
cg_add_len equ $ - cg_add
cg_sub db 0x48, 0x29, 0xc8
cg_sub_len equ $ - cg_sub
cg_mul db 0x48, 0x0f, 0xaf, 0xc1
cg_mul_len equ $ - cg_mul
cg_div db 0x48, 0x99, 0x48, 0xf7, 0xf9
cg_div_len equ $ - cg_div
cg_eq db 0x48, 0x39, 0xc8, 0x0f, 0x94, 0xc0, 0x48, 0x0f, 0xb6, 0xc0
cg_eq_len equ $ - cg_eq
cg_neq db 0x48, 0x39, 0xc8, 0x0f, 0x95, 0xc0, 0x48, 0x0f, 0xb6, 0xc0
cg_neq_len equ $ - cg_neq
cg_lt db 0x48, 0x39, 0xc8, 0x0f, 0x9c, 0xc0, 0x48, 0x0f, 0xb6, 0xc0
cg_lt_len equ $ - cg_lt
cg_lte db 0x48, 0x39, 0xc8, 0x0f, 0x9e, 0xc0, 0x48, 0x0f, 0xb6, 0xc0
cg_lte_len equ $ - cg_lte
cg_exit db 0x48, 0x89, 0xc7, 0xb8
    dd SYS_EXIT
    db 0x0f, 0x05
cg_exit_len equ $ - cg_exit
cg_byte_oob_handler:
    db 0xb8
    dd SYS_WRITE
    db 0xbf
    dd 2
    db 0x48, 0x8d, 0x35
cg_byte_oob_message_disp:
    dd 0
    db 0xba
    dd cg_byte_oob_message_len
    db 0x0f, 0x05, 0xbf
    dd BYTE_OOB_EXIT_STATUS
    db 0xb8
    dd SYS_EXIT
    db 0x0f, 0x05
cg_byte_oob_handler_len equ $ - cg_byte_oob_handler
cg_byte_oob_message_disp_offset equ cg_byte_oob_message_disp - cg_byte_oob_handler
cg_byte_oob_message db "B0 runtime: byte-memory index out of bounds", 10
cg_byte_oob_message_len equ $ - cg_byte_oob_message
cg_input_error_handler:
    db 0xb8
    dd SYS_WRITE
    db 0xbf
    dd 2
    db 0x48, 0x8d, 0x35
cg_input_error_message_disp:
    dd 0
    db 0xba
    dd cg_input_error_message_len
    db 0x0f, 0x05, 0xbf
    dd IO_ERROR_EXIT_STATUS
    db 0xb8
    dd SYS_EXIT
    db 0x0f, 0x05
cg_input_error_handler_len equ $ - cg_input_error_handler
cg_input_error_message_disp_offset equ cg_input_error_message_disp - cg_input_error_handler
cg_input_error_message db "B0 runtime: input_read failed; check standard input", 10
cg_input_error_message_len equ $ - cg_input_error_message
cg_output_error_handler:
    db 0xb8
    dd SYS_WRITE
    db 0xbf
    dd 2
    db 0x48, 0x8d, 0x35
cg_output_error_message_disp:
    dd 0
    db 0xba
    dd cg_output_error_message_len
    db 0x0f, 0x05, 0xbf
    dd IO_ERROR_EXIT_STATUS
    db 0xb8
    dd SYS_EXIT
    db 0x0f, 0x05
cg_output_error_handler_len equ $ - cg_output_error_handler
cg_output_error_message_disp_offset equ cg_output_error_message_disp - cg_output_error_handler
cg_output_error_message db "B0 runtime: output_write failed; check standard output", 10
cg_output_error_message_len equ $ - cg_output_error_message
cg_error_write_error_handler:
    db 0xbf
    dd IO_ERROR_EXIT_STATUS
    db 0xb8
    dd SYS_EXIT
    db 0x0f, 0x05
cg_error_write_error_handler_len equ $ - cg_error_write_error_handler
cg_sigpipe_error_handler:
    db 0xb8
    dd SYS_WRITE
    db 0xbf
    dd 2
    db 0x48, 0x8d, 0x35
cg_sigpipe_error_message_disp:
    dd 0
    db 0xba
    dd cg_sigpipe_error_message_len
    db 0x0f, 0x05, 0xbf
    dd IO_ERROR_EXIT_STATUS
    db 0xb8
    dd SYS_EXIT
    db 0x0f, 0x05
cg_sigpipe_error_handler_len equ $ - cg_sigpipe_error_handler
cg_sigpipe_error_message_disp_offset equ cg_sigpipe_error_message_disp - cg_sigpipe_error_handler
cg_sigpipe_error_message db "B0 runtime: cannot ignore SIGPIPE; check kernel signal support", 10
cg_sigpipe_error_message_len equ $ - cg_sigpipe_error_message

file_end:
%if p_prologue_signal_disp - p_prologue != cg_prologue_sigpipe_error_disp_offset
    %error "profile prologue changed the existing SIGPIPE fixup offset"
%endif
%if p_literal.return - p_literal + 1 != 65
    %error "profile literal return immediate moved"
%endif
absolute 0x406000
input_buf resb INPUT_CAP + 1
input_len resq 1
current_path resq 1
dump_mode resb 1
seen_main resb 1
one_char resb 1
dec_buf resb 32
output_buf resb OUTPUT_CAP
string_buf resb STRING_CAP
write_literal_len resq 1
write_return_value resq 1
code_cursor resq 1
code_output_len resq 1
branch_patch resq 1
loop_start_cursor resq 1
loop_exit_patch resq 1
assignment_source_line resq 1
assignment_source_col resq 1
primary_source_line resq 1
primary_source_col resq 1
statement_name_ptr resq 1
statement_name_len resq 1
byte_memory_source_line resq 1
byte_memory_source_col resq 1
byte_store_index_const_flag resq 1
byte_store_index_const_value resq 1
io_range_offset_const_flag resq 1
io_range_offset_const_value resq 1
io_range_count_const_flag resq 1
io_range_count_const_value resq 1
io_write_fd resq 1
range_guard_cursor resq 1
io_emit_cursor resq 1
sigpipe_setup_error_patch resq 1
byte_oob_patch_count resq 1
byte_oob_handler_cursor resq 1
byte_oob_patches resq BYTE_ACCESS_CAP
io_read_error_patch_count resq 1
io_read_error_patches resq IO_PATCH_CAP
io_write_error_patch_count resq 1
io_write_error_patches resq IO_PATCH_CAP
io_error_write_patch_count resq 1
io_error_write_patches resq IO_PATCH_CAP
runtime_handler_cursor resq 1
binding_count resq 1
binding_name_ptrs resq BINDING_CAP
binding_name_lens resq BINDING_CAP
binding_const_flags resq BINDING_CAP
binding_const_values resq BINDING_CAP
alignb 8
compiler_profile resq 1
bss_end:
