ir_emit:
    push    rbx
    mov     rax, [ir_cnt]
    cmp     rax, IR_MAX
    jge     .overflow
    shl     rax, 5
    lea     rbx, [ir_buf+rax]
    mov     [rbx+IR_F_OP], rdi
    mov     [rbx+IR_F_A],  rsi
    mov     [rbx+IR_F_B],  rdx
    push    rax
    call    tok_cur_line
    pop     rcx
    lea     rbx, [ir_buf+rcx]
    mov     [rbx+IR_F_LN], rax
    inc     qword [ir_cnt]
.done:
    pop     rbx
    ret
.overflow:
    mov     rsi, err_irovf
    mov     rdx, err_irovf_l
    call    fatal_stderr

; ════════════════════════════════════════════════════════════
;  IR1/IR2 macros push args before overwriting rdi/rsi
; ════════════════════════════════════════════════════════════
%macro IR0 1
    mov  rdi, %1
    xor  rsi, rsi
    xor  rdx, rdx
    call ir_emit
%endmacro

%macro IR1 2
    ; %2 may be rdi — push first to survive mov rdi,%1
    push %2
    mov  rdi, %1
    pop  rsi
    xor  rdx, rdx
    call ir_emit
%endmacro

%macro IR2 3
    ; %2 may be rdi, %3 may be rsi — save both before overwriting
    push %3
    push %2
    mov  rdi, %1
    pop  rsi
    pop  rdx
    call ir_emit
%endmacro

; ── Zero-operand helpers ─────────────────────────────────────
ir_push:       IR0 IR_PUSH        
    ret
ir_pop_rbx:    IR0 IR_POP_RBX     
    ret
ir_add:        IR0 IR_ADD         
    ret
ir_sub:        IR0 IR_SUB         
    ret
ir_mul:        IR0 IR_MUL         
    ret
ir_div:        IR0 IR_DIV         
    ret
ir_mod:        IR0 IR_MOD         
    ret
ir_ret:        IR0 IR_RET         
    ret
ir_print_int:  IR0 IR_PRINT_INT   
    ret
ir_fn_end:     IR0 IR_FN_END      
    ret
ir_set_ef:     IR0 IR_SET_EF      
    ret
ir_clr_ef:     IR0 IR_CLR_EF      
    ret
ir_imul8:      IR0 IR_IMUL8       
    ret
ir_mov_rcx:    IR0 IR_MOV_RCX     
    ret
ir_mov_rbx:    IR0 IR_MOV_RBX     
    ret
ir_pop_rax:    IR0 IR_POP_RAX     
    ret
ir_inc_rax:    IR0 IR_INC_RAX     
    ret
ir_arr_ld:     IR0 IR_ARR_LD      
    ret
ir_arr_st:     IR0 IR_ARR_ST
    ret
ir_mod_end:    IR0 IR_MOD_END
    ret
ir_argc:       IR0 IR_ARGC
    ret
ir_arg:        IR0 IR_ARG
    ret
ir_arg_str:    IR0 IR_ARG_STR
    ret
ir_str_find:   IR0 IR_STR_FIND
    ret
ir_str_slice:  IR0 IR_STR_SLICE
    ret
ir_exit:       IR0 IR_EXIT
    ret
ir_lnot:       IR0 IR_LNOT
    ret
ir_arr_len:    IR0 IR_ARR_LEN
    ret
ir_abs:        IR0 IR_ABS
    ret
ir_min:        IR0 IR_FMIN
    ret
ir_max:        IR0 IR_FMAX
    ret
ir_input_int:  IR0 IR_INPUT_INT
    ret
ir_print_nl:   IR0 IR_PRINT_NL
    ret
ir_band:       IR0 IR_BAND
    ret
ir_bor:        IR0 IR_BOR
    ret
ir_bxor:       IR0 IR_BXOR
    ret
ir_bnot:       IR0 IR_BNOT
    ret
ir_shl:        IR0 IR_SHL
    ret
ir_shr:        IR0 IR_SHR
    ret
ir_print_str_var: IR0 IR_PRINT_STR_VAR
    ret
ir_str_len:    IR0 IR_STR_LEN
    ret
ir_str_eq:     IR0 IR_STR_EQ
    ret
ir_str_neq:    IR0 IR_STR_NEQ
    ret
ir_input_str:  IR0 IR_INPUT_STR
    ret
ir_str_at:     IR0 IR_STR_AT
    ret
ir_int_to_str: IR0 IR_INT_TO_STR
    ret
ir_str_to_int: IR0 IR_STR_TO_INT
    ret
ir_str_concat: IR0 IR_STR_CONCAT
    ret
ir_arr_pop:    IR0 IR_ARR_POP
    ret
ir_read_file:  IR0 IR_READ_FILE
    ret
ir_write_file: IR0 IR_WRITE_FILE
    ret
ir_append_file: IR0 IR_APPEND_FILE
    ret

; ── One-operand helpers (rdi=value) ──────────────────────────
ir_const:
    IR1 IR_CONST, rdi
    ret
ir_load_g:
    IR1 IR_LOAD_G, rdi
    ret
ir_store_g:
    IR1 IR_STORE_G, rdi
    ret
ir_load_l:
    IR1 IR_LOAD_L, rdi
    ret
ir_store_l:
    IR1 IR_STORE_L, rdi
    ret
ir_load_p:
    IR1 IR_LOAD_P, rdi
    ret
ir_store_p:
    IR1 IR_STORE_P, rdi
    ret
ir_print_str:
    IR1 IR_PRINT_STR, rdi
    ret
ir_arr_new:
    IR1 IR_ARR_NEW, rdi
    ret
ir_add_rsp:
    IR1 IR_ADD_RSP, rdi
    ret
ir_jmp_tc:
    IR1 IR_JMP_TC, rdi
    ret
ir_fe_st:
    IR1 IR_FE_ST, rdi
    ret
ir_fe_cmp:
    IR1 IR_FE_CMP, rdi
    ret

; ── Two-operand helpers (rdi=A, rsi=B) ───────────────────────
ir_jz:
    IR2 IR_JZ, rdi, rsi
    ret
ir_jmp:
    IR2 IR_JMP, rdi, rsi
    ret
ir_lbl:
    IR2 IR_LBL, rdi, rsi
    ret
ir_jge:
    IR2 IR_JGE, rdi, rsi
    ret
ir_call:
    IR2 IR_CALL, rdi, rsi
    ret
ir_fn_begin:
    IR2 IR_FN_BGN, rdi, rsi
    ret
ir_mod_begin:
    IR2 IR_MOD_BGN, rdi, rsi
    ret
ir_cmp:
    ; rdi=op_token, rsi=cf_label_id
    IR2 IR_CMP, rdi, rsi
    ret

; ────────────────────────────────────────────────────────────
;  COMPILE-TIME TYPE STACK  (TY_UNK=0 TY_INT=1 TY_STR=2 TY_ARR=3)
; ────────────────────────────────────────────────────────────
ty_push:
    mov     rax, [type_stkp]
    cmp     rax, 64
    jge     .ovf
    mov     [type_stk+rax*8], rdi
    inc     qword [type_stkp]
    ret
.ovf:
    mov     rsi, err_irovf
    mov     rdx, err_irovf_l
    call    fatal_stderr

ty_pop:
    mov     rax, [type_stkp]
    test    rax, rax
    jz      .empty
    dec     rax
    mov     [type_stkp], rax
    mov     rax, [type_stk+rax*8]
    ret
.empty:
    xor     rax, rax
    ret

ty_discard:
    mov     rax, [type_stkp]
    test    rax, rax
    jz      .none
    dec     qword [type_stkp]
.none:
    ret

ty_check_ret:
    ; Pop return-expr type; check/record against fn_ret_type.
    call    ty_pop             ; rax = type of return expression
    test    rax, rax
    jz      .done              ; unknown type — skip check
    mov     rcx, [fn_ret_type]
    test    rcx, rcx
    jz      .first             ; first typed return — record it
    cmp     rax, rcx
    je      .done              ; same type — OK
    push    rax
    mov     rdx, em_type_ret
    mov     rcx, em_type_ret_l
    call    emit_error_tok
    pop     rax
    ret
.first:
    mov     [fn_ret_type], rax
.done:
    ret

; emit_unused_var_err: rdi=line, rsi=col, rdx=name_ptr, rcx=name_len
emit_unused_var_err:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx
    mov     r15, rcx
    lea     rdi, [unused_msg_buf]
    mov     rbx, rdi
    lea     rsi, [em_unused_pfx]
    mov     rcx, em_unused_pfx_l
    rep movsb
    mov     rsi, r14
    mov     rcx, r15
    rep movsb
    mov     byte [rdi], 27h     ; "'"
    inc     rdi
    sub     rdi, rbx
    mov     rcx, rdi
    mov     rdx, rbx
    mov     rdi, r12
    mov     rsi, r13
    call    emit_error
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

ty_check_arith:
    ; Pop 2 types; if both known and not TY_INT → error; push TY_INT
    push    rbx
    call    ty_pop
    mov     rbx, rax
    call    ty_pop
    test    rax, rax
    jz      .ok
    test    rbx, rbx
    jz      .ok
    cmp     rax, TY_INT
    jne     .err
    cmp     rbx, TY_INT
    jne     .err
.ok:
    mov     rdi, TY_INT
    call    ty_push
    pop     rbx
    ret
.err:
    mov     rdx, em_type_arith
    mov     rcx, em_type_arith_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    pop     rbx
    ret

ty_check_int_unary:
    call    ty_pop
    test    rax, rax
    jz      .ok
    cmp     rax, TY_INT
    jne     .err
.ok:
    mov     rdi, TY_INT
    call    ty_push
    ret
.err:
    mov     rdx, em_type_int_operand
    mov     rcx, em_type_int_operand_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    ret

ty_check_str_concat:
    ; Pop 2 types; if both known and not TY_STR → error; push TY_STR
    push    rbx
    call    ty_pop
    mov     rbx, rax
    call    ty_pop
    test    rax, rax
    jz      .ok
    test    rbx, rbx
    jz      .ok
    cmp     rax, TY_STR
    jne     .err
    cmp     rbx, TY_STR
    jne     .err
.ok:
    mov     rdi, TY_STR
    call    ty_push
    pop     rbx
    ret
.err:
    mov     rdx, em_type_str_concat
    mov     rcx, em_type_str_concat_l
    call    emit_error_tok
    mov     rdi, TY_STR
    call    ty_push
    pop     rbx
    ret

ty_check_cmp:
    ; Pop 2 types; check for array, string, or mismatch → error
    push    rbx
    call    ty_pop         ; rax = RHS type
    mov     rbx, rax       ; rbx = RHS
    call    ty_pop         ; rax = LHS type
    ; Array on either side
    cmp     rax, TY_ARR
    je      .arr_err
    cmp     rax, TY_STR_ARR
    je      .arr_err
    cmp     rbx, TY_ARR
    je      .arr_err
    cmp     rbx, TY_STR_ARR
    je      .arr_err
    ; String on either side
    cmp     rax, TY_STR
    je      .str_err
    cmp     rbx, TY_STR
    je      .str_err
    ; Mismatch (both known, different)
    test    rax, rax
    jz      .ok
    test    rbx, rbx
    jz      .ok
    cmp     rax, rbx
    je      .ok
    mov     rdx, em_type_cmp
    mov     rcx, em_type_cmp_l
    call    emit_error_tok
    jmp     .ok
.arr_err:
    mov     rdx, em_cmp_arr
    mov     rcx, em_cmp_arr_l
    call    emit_error_tok
    jmp     .ok
.str_err:
    mov     rdx, em_cmp_str
    mov     rcx, em_cmp_str_l
    call    emit_error_tok
.ok:
    pop     rbx
    ret

; ────────────────────────────────────────────────────────────
;  ir_load / ir_store — resolve name → correct IR opcode
;  Input: rbx=name_ptr, r12=name_len
; ────────────────────────────────────────────────────────────
ir_load:
    push    r13
    push    r14
    push    r15
    cmp     qword [in_fn], 1
    jne     .global
    ; 1. Params
    xor     r13, r13
.pl:
    cmp     r13, [fn_pcur]
    jge     .locals
    mov     rax, r13
    imul    rax, rax, VAR_NL
    lea     r14, [fn_pnames+rax]
    mov     r15, [fn_plens+r13*8]
    cmp     r15, r12
    jne     .pnx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, rbx
    mov     rdi, r14
    mov     rcx, r12
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .pnx
    mov     rax, [fn_pcur]
    sub     rax, r13
    inc     rax
    imul    rdi, rax, 8
    call    ir_load_p
    mov     rdi, [fn_param_types+r13*8]
    call    ty_push
    jmp     .done
.pnx:
    inc     r13
    jmp     .pl
    ; 2. Locals
.locals:
    push    rsi
    push    rcx
    mov     rsi, rbx
    mov     rcx, r12
    call    lsym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    je      .global
    mov     r13, rax
    inc     qword [lvar_reads+r13*8]
    mov     rdi, rax
    call    ir_load_l
    mov     rdi, [lvar_types+r13*8]
    call    ty_push
    jmp     .done
    ; 3. Global
.global:
    push    rsi
    push    rcx
    mov     rsi, rbx
    mov     rcx, r12
    call    sym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    je      .undef
    mov     r13, rax
    inc     qword [gvar_reads+r13*8]
    imul    rdi, rax, 8
    call    ir_load_g
    mov     rdi, [gvar_types+r13*8]
    call    ty_push
    jmp     .done
.undef:
    push    rdx
    push    rcx
    call    tok_cur_line
    mov     rdi, rax
    call    tok_cur_col
    mov     rsi, rax
    mov     rdx, em_undef
    mov     rcx, em_undef_l
    call    emit_error
    pop     rcx
    pop     rdx
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_UNK
    call    ty_push
.done:
    pop     r15
    pop     r14
    pop     r13
    ret

ir_store:
    push    r13
    push    r14
    push    r15
    cmp     qword [in_fn], 1
    jne     .locals_chk
    ; 1. Params
    xor     r13, r13
.pl:
    cmp     r13, [fn_pcur]
    jge     .locals_chk
    mov     rax, r13
    imul    rax, rax, VAR_NL
    lea     r14, [fn_pnames+rax]
    mov     r15, [fn_plens+r13*8]
    cmp     r15, r12
    jne     .pnx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, rbx
    mov     rdi, r14
    mov     rcx, r12
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .pnx
    mov     rax, [fn_pcur]
    sub     rax, r13
    inc     rax
    imul    rdi, rax, 8
    call    ir_store_p
    call    ty_pop         ; rax = new type
    push    rax
    push    r13            ; save param index
    mov     rcx, [fn_param_types+r13*8]
    test    rcx, rcx
    jz      .param_chk_done
    test    rax, rax
    jz      .param_chk_done
    cmp     rax, rcx
    je      .param_chk_done
    mov     rdx, em_type_assign
    mov     rcx, em_type_assign_l
    call    emit_error_tok
.param_chk_done:
    pop     r13
    pop     rax
    mov     [fn_param_types+r13*8], rax
    jmp     .done
.pnx:
    inc     r13
    jmp     .pl
    ; 2. Locals
.locals_chk:
    cmp     qword [in_fn], 1
    jne     .global
    push    rsi
    push    rcx
    mov     rsi, rbx
    mov     rcx, r12
    call    lsym_lookup
    cmp     rax, -1
    jne     .found_local
    ; In declaration mode (parse_var), always create new local — skip global check.
    ; In assignment mode, check global first so 'x=expr' writes to outer scope.
    cmp     qword [var_decl_mode], 1
    je      .truly_new
    push    rsi
    push    rcx
    mov     rsi, rbx
    mov     rcx, r12
    call    sym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    jne     .found_global
.truly_new:
    ; New local: insert
    mov     rsi, rbx
    mov     rcx, r12
    call    lsym_insert
    mov     r14, rax
    lea     rdi, [lvar_names+r14*8]
    mov     rsi, rbx
    mov     rcx, r12
    rep movsb
    mov     byte [rdi], 0
    mov     [lvar_names_l+r14], r12
    mov     rax, [decl_pending_line]
    mov     [lvar_decl_line+r14*8], rax
    mov     rax, [decl_pending_col]
    mov     [lvar_decl_col+r14*8], rax
    mov     rax, r14
.found_local:
    pop     rcx
    pop     rsi
    push    rax            ; save slot
    call    ty_pop         ; rax = new type
    pop     rcx            ; rcx = slot
    push    rax            ; save new type
    push    rcx            ; save slot
    mov     r13, [lvar_types+rcx*8]
    test    r13, r13
    jz      .local_chk_done
    test    rax, rax
    jz      .local_chk_done
    cmp     rax, r13
    je      .local_chk_done
    mov     rdx, em_type_assign
    mov     rcx, em_type_assign_l
    call    emit_error_tok
.local_chk_done:
    pop     rcx
    pop     rax
    mov     [lvar_types+rcx*8], rax
    mov     rdi, rcx
    call    ir_store_l
    jmp     .done
.found_global:
    pop     rcx
    pop     rsi
    push    rax            ; save slot
    call    ty_pop         ; rax = new type
    pop     rcx            ; rcx = slot
    push    rax            ; save new type
    push    rcx            ; save slot
    mov     r13, [gvar_types+rcx*8]
    test    r13, r13
    jz      .fglobal_chk_done
    test    rax, rax
    jz      .fglobal_chk_done
    cmp     rax, r13
    je      .fglobal_chk_done
    mov     rdx, em_type_assign
    mov     rcx, em_type_assign_l
    call    emit_error_tok
.fglobal_chk_done:
    pop     rcx
    pop     rax
    mov     [gvar_types+rcx*8], rax
    imul    rdi, rcx, 8
    call    ir_store_g
    jmp     .done
    ; 3. Global
.global:
    push    rsi
    push    rcx
    mov     rsi, rbx
    mov     rcx, r12
    call    sym_insert
    pop     rcx
    pop     rsi
    cmp     qword [gvar_decl_line+rax*8], 0
    jne     .gdc_skip
    mov     r14, [decl_pending_line]
    mov     r15, [decl_pending_col]
    mov     [gvar_decl_line+rax*8], r14
    mov     [gvar_decl_col+rax*8], r15
    mov     [gvar_names_l+rax*8], r12
.gdc_skip:
    push    rax            ; save slot
    call    ty_pop         ; rax = new type
    pop     rcx            ; rcx = slot
    push    rax            ; save new type
    push    rcx            ; save slot
    mov     r13, [gvar_types+rcx*8]
    test    r13, r13
    jz      .global_chk_done
    test    rax, rax
    jz      .global_chk_done
    cmp     rax, r13
    je      .global_chk_done
    mov     rdx, em_type_assign
    mov     rcx, em_type_assign_l
    call    emit_error_tok
.global_chk_done:
    pop     rcx
    pop     rax
    mov     [gvar_types+rcx*8], rax
    imul    rdi, rcx, 8
    call    ir_store_g
.done:
    pop     r15
    pop     r14
    pop     r13
    ret

; ────────────────────────────────────────────────────────────
;  TOKEN HELPERS
; ────────────────────────────────────────────────────────────
tok_cur_type:
    mov     rax, [tok_pos]
    cmp     rax, [tok_cnt]
    jb      .ok
    mov     rax, TOK_EOF
    ret
.ok:
    mov     rax, [tok_type+rax*8]
    ret
tok_cur_ptr:
    mov     rax, [tok_pos]
    cmp     rax, [tok_cnt]
    jb      .ok
    xor     rax, rax
    ret
.ok:
    mov     rax, [tok_ptr+rax*8]
    ret
tok_cur_len:
    mov     rax, [tok_pos]
    cmp     rax, [tok_cnt]
    jb      .ok
    xor     rax, rax
    ret
.ok:
    mov     rax, [tok_len+rax*8]
    ret
tok_cur_line:
    mov     rax, [tok_pos]
    cmp     rax, [tok_cnt]
    jb      .ok
    xor     rax, rax
    ret
.ok:
    mov     rax, [tok_line+rax*8]
    ret
tok_cur_col:
    mov     rax, [tok_pos]
    cmp     rax, [tok_cnt]
    jb      .ok
    xor     rax, rax
    ret
.ok:
    mov     rax, [tok_col+rax*8]
    ret
tok_advance:
    mov     rax, [tok_pos]
    cmp     rax, [tok_cnt]
    jae     .d
    inc     qword [tok_pos]
.d:
    ret
tok_skip_nl:
.l: call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    jne     .d
    call    tok_advance
    jmp     .l
.d: ret
tok_peek:
    mov     rax, [tok_pos]
    add     rax, rdi
    cmp     rax, [tok_cnt]
    jb      .ok
    mov     rax, TOK_EOF
    ret
.ok:
    mov     rax, [tok_type+rax*8]
    ret

stmt_line_has_eq:
    push    r12
    mov     r12, [tok_pos]
.lp:
    cmp     r12, [tok_cnt]
    jae     .no
    mov     rax, [tok_type+r12*8]
    cmp     rax, TOK_EQ
    je      .yes
    cmp     rax, TOK_NEWLINE
    je      .no
    cmp     rax, TOK_EOF
    je      .no
    cmp     rax, TOK_RBRACE
    je      .no
    inc     r12
    jmp     .lp
.yes:
    mov     rax, 1
    jmp     .done
.no:
    xor     rax, rax
.done:
    pop     r12
    ret

skip_decl_stmt:
    push    r12
    push    r13
    xor     r12, r12
.lp:
    call    tok_cur_type
    cmp     rax, TOK_EOF
    je      .done
    cmp     rax, TOK_NEWLINE
    je      .eat_nl
    cmp     rax, TOK_LBRACE
    jne     .chk_rbrace
    inc     r12
    call    tok_advance
    jmp     .lp
.chk_rbrace:
    cmp     rax, TOK_RBRACE
    jne     .adv
    cmp     r12, 0
    jle     .done
    dec     r12
    call    tok_advance
    cmp     r12, 0
    jne     .lp
    jmp     .done
.adv:
    call    tok_advance
    jmp     .lp
.eat_nl:
    call    tok_advance
    cmp     r12, 0
    jg      .lp
.done:
    pop     r13
    pop     r12
    ret

; ────────────────────────────────────────────────────────────
;  LEXER
