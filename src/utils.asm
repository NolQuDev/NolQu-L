emit_bytes:
    test    rdx, rdx
    jz      .done
    push    r8
    push    r9
    push    rdi
    push    rcx
    mov     r8, [cur_emit]
    cmp     r8, 1
    je      .fn
    cmp     r8, 2
    je      .str
    lea     r9, [out_pos]
    jmp     .copy
.fn:
    lea     r9, [fn_pos]
    jmp     .copy
.str:
    lea     r9, [str_pos]
.copy:
    mov     r8, [r9]
    mov     rax, [cur_emit]
    cmp     rax, 2
    je      .chk_str
    cmp     rax, 1
    je      .chk_fn
    mov     rax, r8
    add     rax, rdx
    cmp     rax, OUT_SIZE
    jbe     .buf_sel
    mov     rdx, em_outbuf_ovf
    mov     rcx, em_outbuf_ovf_l
    call    emit_error_emit_line
.chk_fn:
    mov     rax, r8
    add     rax, rdx
    cmp     rax, FN_SIZE
    jbe     .buf_sel
    mov     rdx, em_fnbuf_ovf
    mov     rcx, em_fnbuf_ovf_l
    call    emit_error_emit_line
.chk_str:
    mov     rax, r8
    add     rax, rdx
    cmp     rax, STR_SIZE
    jbe     .buf_sel
    mov     rdx, em_strbuf_ovf
    mov     rcx, em_strbuf_ovf_l
    call    emit_error_tok
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.buf_sel:
    mov     rax, [cur_emit]
    cmp     rax, 1
    je      .fn_buf
    cmp     rax, 2
    je      .str_buf
    lea     rdi, [out_buf + r8]
    jmp     .do
.fn_buf:
    lea     rdi, [fn_buf + r8]
    jmp     .do
.str_buf:
    lea     rdi, [str_buf + r8]
.do:
    mov     rcx, rdx
    add     r8, rdx
    rep movsb
    mov     [r9], r8
    pop     rcx
    pop     rdi
    pop     r9
    pop     r8
.done:
    ret

emit_nl:
    mov     rsi, f_nl
    mov     rdx, 1
    jmp     emit_bytes

; emit_lbl_ref: "PREFIX_N"  rdi=label_id, rsi=label_type
emit_lbl_ref:
    push    rbx
    push    r12
    mov     rbx, rdi
    mov     r12, rsi
    imul    rax, r12, 8
    mov     rsi, [lbl_tbl + rax]
    mov     rdx, 4
    call    emit_bytes
    mov     rax, rbx
    call    int_to_str
    call    emit_bytes
    pop     r12
    pop     rbx
    ret

; emit_lbl_def: "PREFIX_N:\n"  rdi=label_id, rsi=label_type
emit_lbl_def:
    call    emit_lbl_ref
    mov     rsi, f_colon_nl
    mov     rdx, f_colon_nl_l
    jmp     emit_bytes

; ────────────────────────────────────────────────────────────
;  ERROR REPORTING
; ────────────────────────────────────────────────────────────
emit_error:
    ; rdi=line, rsi=col, rdx=msg_ptr, rcx=msg_len
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx
    mov     r15, rcx
    mov     qword [had_error], 1
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, ep_prefix
    mov     rdx, ep_prefix_l
    syscall
    mov     rax, r12
    call    int_to_str
    push    rsi
    push    rdx
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    pop     rdx
    pop     rsi
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, ep_col
    mov     rdx, ep_col_l
    syscall
    mov     rax, r13
    call    int_to_str
    push    rsi
    push    rdx
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    pop     rdx
    pop     rsi
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, ep_sep
    mov     rdx, ep_sep_l
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, r14
    mov     rdx, r15
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, ep_nl
    mov     rdx, 1
    syscall
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

emit_error_tok:
    ; rdx=msg, rcx=len — reports at current token position
    push    rdx
    push    rcx
    call    tok_cur_line
    mov     rdi, rax
    call    tok_cur_col
    mov     rsi, rax
    pop     rcx
    pop     rdx
    jmp     emit_error

emit_error_emit_line:
    ; rdx=msg, rcx=len — reports at active IR source line. Does not return.
    mov     rdi, [emit_line]
    xor     rsi, rsi
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall

fatal_stderr:
    ; rsi=msg_ptr, rdx=msg_len
    mov     qword [had_error], 1
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    syscall
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall

; ────────────────────────────────────────────────────────────
;  BENCH REPORT
; ────────────────────────────────────────────────────────────
print_bench:
    push    r15
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    mov     rsi, bh_hdr
    mov     rdx, bh_hdr_l
    syscall
    mov     r15, [ts_lex]
    mov     rsi, bh_lex
    mov     rdx, bh_lex_l
    call    pbl
    mov     r15, [ts_parse]
    mov     rsi, bh_parse
    mov     rdx, bh_parse_l
    call    pbl
    mov     r15, [ts_opt]
    mov     rsi, bh_opt
    mov     rdx, bh_opt_l
    call    pbl
    mov     r15, [ts_cg]
    mov     rsi, bh_cg
    mov     rdx, bh_cg_l
    call    pbl
    mov     r15, [ts_lex]
    add     r15, [ts_parse]
    add     r15, [ts_opt]
    add     r15, [ts_cg]
    mov     rsi, bh_total
    mov     rdx, bh_total_l
    call    pbl
    pop     r15
    ret

pbl:    ; rsi=label, rdx=len, r15=cycles
    push    r15
    push    rsi
    push    rdx
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    pop     rdx
    pop     rsi
    syscall
    pop     r15
    mov     rax, r15
    call    int_to_str
    push    rsi
    push    rdx
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    pop     rdx
    pop     rsi
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    mov     rsi, bh_nl
    mov     rdx, 1
    syscall
    ret

; ────────────────────────────────────────────────────────────
;  DEBUG DUMPS
; ────────────────────────────────────────────────────────────
dbg_write:
    test    rdx, rdx
    jz      .done
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    syscall
.done:
    ret

dbg_write_num:
    call    int_to_str
    jmp     dbg_write

dbg_print_tok_name:
    cmp     rax, 79
    ja      .unknown
    mov     rsi, [tok_name_ptrs+rax*8]
    mov     rdx, [tok_name_lens+rax*8]
    test    rsi, rsi
    jz      .unknown
    jmp     dbg_write
.unknown:
    mov     rsi, dbg_unknown_tok
    mov     rdx, dbg_unknown_tok_l
    jmp     dbg_write

dbg_print_ir_name:
    cmp     rax, 75
    ja      .unknown
    mov     rsi, [ir_name_ptrs+rax*8]
    mov     rdx, [ir_name_lens+rax*8]
    test    rsi, rsi
    jz      .unknown
    jmp     dbg_write
.unknown:
    mov     rsi, dbg_unknown_ir
    mov     rdx, dbg_unknown_ir_l
    jmp     dbg_write

dbg_print_ir_extra:
    cmp     rdi, IR_CALL
    je      .name
    cmp     rdi, IR_FN_BGN
    je      .name
    cmp     rdi, IR_MOD_BGN
    je      .name
    cmp     rdi, IR_CONST
    je      .text
    cmp     rdi, IR_PRINT_STR
    je      .text
    ret
.name:
    mov     r8, rsi
    mov     r9, rdx
    mov     rsi, dbg_name_eq
    mov     rdx, dbg_name_eq_l
    call    dbg_write
    mov     rsi, r8
    mov     rdx, r9
    jmp     dbg_write
.text:
    cmp     rsi, STR_MAX
    jae     .bad_text
    mov     r8, [str_ptrs + rsi*8]
    mov     r9, [str_lens + rsi*8]
    test    r8, r8
    jz      .bad_text
    mov     rsi, dbg_text_eq
    mov     rdx, dbg_text_eq_l
    call    dbg_write
    mov     rsi, r8
    mov     rdx, r9
    jmp     dbg_write
.bad_text:
    ret

dump_tokens_run:
    push    r12
    push    r13
    push    r14
    push    r15
    mov     rsi, dbg_dump_tok_hdr
    mov     rdx, dbg_dump_tok_hdr_l
    call    dbg_write
    xor     r12, r12
.lp:
    cmp     r12, [tok_cnt]
    jge     .done
    mov     rax, r12
    call    dbg_write_num
    mov     rsi, dbg_tab
    mov     rdx, 1
    call    dbg_write
    mov     rax, [tok_type+r12*8]
    mov     r13, rax
    call    dbg_print_tok_name
    mov     rsi, dbg_tab
    mov     rdx, 1
    call    dbg_write
    mov     rax, [tok_line+r12*8]
    call    dbg_write_num
    mov     rsi, dbg_colon
    mov     rdx, 1
    call    dbg_write
    mov     rax, [tok_col+r12*8]
    call    dbg_write_num
    cmp     r13, TOK_IDENT
    je      .slice
    cmp     r13, TOK_INT
    je      .slice
    cmp     r13, TOK_STRING
    jne     .nl
.slice:
    mov     rsi, dbg_tab
    mov     rdx, 1
    call    dbg_write
    mov     rsi, [tok_ptr+r12*8]
    mov     rdx, [tok_len+r12*8]
    call    dbg_write
.nl:
    mov     rsi, ep_nl
    mov     rdx, 1
    call    dbg_write
    inc     r12
    jmp     .lp
.done:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

dump_ir_run:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    mov     rsi, dbg_dump_ir_hdr
    mov     rdx, dbg_dump_ir_hdr_l
    call    dbg_write
    xor     r12, r12
.lp:
    cmp     r12, [ir_cnt]
    jge     .done
    imul    rbx, r12, IRS
    lea     rbx, [ir_buf+rbx]
    mov     rax, r12
    call    dbg_write_num
    mov     rsi, dbg_tab
    mov     rdx, 1
    call    dbg_write
    mov     rax, [rbx+IR_F_OP]
    call    dbg_print_ir_name
    mov     rsi, dbg_a_eq
    mov     rdx, dbg_a_eq_l
    call    dbg_write
    mov     rax, [rbx+IR_F_A]
    call    dbg_write_num
    mov     rsi, dbg_b_eq
    mov     rdx, dbg_b_eq_l
    call    dbg_write
    mov     rax, [rbx+IR_F_B]
    call    dbg_write_num
    mov     rsi, dbg_ln_eq
    mov     rdx, dbg_ln_eq_l
    call    dbg_write
    mov     rax, [rbx+IR_F_LN]
    call    dbg_write_num
    mov     rdi, [rbx+IR_F_OP]
    mov     rsi, [rbx+IR_F_A]
    mov     rdx, [rbx+IR_F_B]
    call    dbg_print_ir_extra
    mov     rsi, ep_nl
    mov     rdx, 1
    call    dbg_write
    inc     r12
    jmp     .lp
.done:
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ────────────────────────────────────────────────────────────
;  MATH / STRING UTILS
; ────────────────────────────────────────────────────────────
int_to_str:
    push    rbp
    push    rbx
    push    r12
    push    r13
    mov     r12, rax
    lea     rbx, [num_buf+30]
    mov     byte [rbx+1], 0
    test    rax, rax
    jns     .pos
    neg     rax
.pos:
    mov     r13, 10
.lp:
    xor     rdx, rdx
    div     r13
    add     dl, '0'
    mov     [rbx], dl
    dec     rbx
    test    rax, rax
    jnz     .lp
    test    r12, r12
    jns     .nn
    mov     byte [rbx], '-'
    dec     rbx
.nn:
    inc     rbx
    mov     rsi, rbx
    lea     rdx, [num_buf+31]
    sub     rdx, rsi
    pop     r13
    pop     r12
    pop     rbx
    pop     rbp
    ret

str_to_int:
    push    rbx
    xor     rax, rax
.lp:
    test    rcx, rcx
    jz      .d
    movzx   rbx, byte [rsi]
    cmp     rbx, '_'
    je      .skip
    sub     rbx, '0'
    imul    rax, rax, 10
    add     rax, rbx
.skip:
    inc     rsi
    dec     rcx
    jmp     .lp
.d: pop     rbx
    ret

str_to_hex_int:
    push    rbx
    xor     rax, rax
.lp:
    test    rcx, rcx
    jz      .done
    movzx   rbx, byte [rsi]
    cmp     rbx, '_'
    je      .skip
    cmp     rbx, '9'
    jbe     .digit
    cmp     rbx, 'F'
    jbe     .upper
    sub     rbx, 'a' - 10
    jmp     .add
.upper:
    sub     rbx, 'A' - 10
    jmp     .add
.digit:
    sub     rbx, '0'
.add:
    shl     rax, 4
    add     rax, rbx
.skip:
    inc     rsi
    dec     rcx
    jmp     .lp
.done:
    pop     rbx
    ret

str_to_bin_int:
    push    rbx
    xor     rax, rax
.lp:
    test    rcx, rcx
    jz      .done
    movzx   rbx, byte [rsi]
    cmp     rbx, '_'
    je      .skip
    sub     rbx, '0'
    shl     rax, 1
    add     rax, rbx
.skip:
    inc     rsi
    dec     rcx
    jmp     .lp
.done:
    pop     rbx
    ret

num_digit_count:
    xor     rax, rax
.lp:
    test    rcx, rcx
    jz      .done
    cmp     byte [rsi], '_'
    je      .skip
    inc     rax
.skip:
    inc     rsi
    dec     rcx
    jmp     .lp
.done:
    ret

str_len:
    push    rdi
    push    rcx
    xor     rax, rax
    mov     rcx, -1
    xor     al, al
    repne scasb
    not     rcx
    dec     rcx
    mov     rax, rcx
    pop     rcx
    pop     rdi
    ret

; ────────────────────────────────────────────────────────────
;  FNV-1a hash
