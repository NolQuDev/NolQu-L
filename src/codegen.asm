cg_run:
    mov     qword [out_pos],  0
    mov     qword [fn_pos],   0
    mov     qword [cur_emit], 0
    mov     qword [emit_line], 0
    mov     qword [istr_cur], 0
    mov     qword [its_cur], 0
    mov     qword [str_cat_cur], 0
    mov     qword [file_read_cur], 0
    mov     qword [arg_str_cur], 0
    xor     r12, r12
    mov     r13, [ir_cnt]
.lp:
    cmp     r12, r13
    jge     .done
    mov     rax, r12
    shl     rax, 5
    lea     rbx, [ir_buf+rax]
    mov     r14, [rbx+IR_F_OP]
    mov     rax, [rbx+IR_F_LN]
    mov     [emit_line], rax
    mov     r15, [rbx+IR_F_A]
    mov     rdi, [rbx+IR_F_B]
    cmp     r14, IR_DEAD
    je      .next
    cmp     r14, IR_NOP
    je      .next
    cmp     r14, 75
    jg      .next
    ; CALL (not JMP): handlers use ret to return here, not to cg_run's caller
    call    qword [cg_jt + r14*8]
.next:
    inc     r12
    jmp     .lp
.done:
    ret

; ── Codegen dispatch table ───────────────────────────────────
align 8
cg_jt:
    dq cg_nop        ;  0 IR_NOP
    dq cg_const      ;  1 IR_CONST
    dq cg_load_g     ;  2 IR_LOAD_G
    dq cg_store_g    ;  3 IR_STORE_G
    dq cg_load_l     ;  4 IR_LOAD_L
    dq cg_store_l    ;  5 IR_STORE_L
    dq cg_load_p     ;  6 IR_LOAD_P
    dq cg_store_p    ;  7 IR_STORE_P
    dq cg_push       ;  8 IR_PUSH
    dq cg_pop_rbx    ;  9 IR_POP_RBX
    dq cg_add        ; 10 IR_ADD
    dq cg_sub        ; 11 IR_SUB
    dq cg_mul        ; 12 IR_MUL
    dq cg_div        ; 13 IR_DIV
    dq cg_mod        ; 14 IR_MOD
    dq cg_cmp        ; 15 IR_CMP
    dq cg_jz         ; 16 IR_JZ
    dq cg_jmp        ; 17 IR_JMP
    dq cg_lbl        ; 18 IR_LBL
    dq cg_call       ; 19 IR_CALL
    dq cg_add_rsp    ; 20 IR_ADD_RSP
    dq cg_ret        ; 21 IR_RET
    dq cg_print_int  ; 22 IR_PRINT_INT
    dq cg_print_str  ; 23 IR_PRINT_STR
    dq cg_fn_bgn     ; 24 IR_FN_BGN
    dq cg_fn_end     ; 25 IR_FN_END
    dq cg_arr_new    ; 26 IR_ARR_NEW
    dq cg_arr_ld     ; 27 IR_ARR_LD
    dq cg_arr_st     ; 28 IR_ARR_ST
    dq cg_set_ef     ; 29 IR_SET_EF
    dq cg_clr_ef     ; 30 IR_CLR_EF
    dq cg_jmp_tc     ; 31 IR_JMP_TC
    dq cg_mod_bgn    ; 32 IR_MOD_BGN
    dq cg_mod_end    ; 33 IR_MOD_END
    dq cg_imul8      ; 34 IR_IMUL8
    dq cg_mov_rcx    ; 35 IR_MOV_RCX
    dq cg_pop_rax    ; 36 IR_POP_RAX
    dq cg_inc_rax    ; 37 IR_INC_RAX
    dq cg_fe_st      ; 38 IR_FE_ST
    dq cg_fe_cmp     ; 39 IR_FE_CMP
    dq cg_jge        ; 40 IR_JGE
    dq cg_mov_rbx    ; 41 IR_MOV_RBX
    dq cg_argc       ; 42 IR_ARGC
    dq cg_arg        ; 43 IR_ARG
    dq cg_lnot       ; 44 IR_LNOT
    dq cg_arr_len    ; 45 IR_ARR_LEN
    dq cg_abs        ; 46 IR_ABS
    dq cg_min        ; 47 IR_FMIN
    dq cg_max        ; 48 IR_FMAX
    dq cg_input_int  ; 49 IR_INPUT_INT
    dq cg_heap_st    ; 50 IR_STORE_HEAP
    dq cg_print_nl   ; 51 IR_PRINT_NL
    dq cg_band       ; 52 IR_BAND
    dq cg_bor        ; 53 IR_BOR
    dq cg_bxor       ; 54 IR_BXOR
    dq cg_bnot       ; 55 IR_BNOT
    dq cg_shl        ; 56 IR_SHL
    dq cg_shr          ; 57 IR_SHR
    dq cg_print_str_var ; 58 IR_PRINT_STR_VAR
    dq cg_str_len       ; 59 IR_STR_LEN
    dq cg_str_eq        ; 60 IR_STR_EQ
    dq cg_str_neq       ; 61 IR_STR_NEQ
    dq cg_input_str     ; 62 IR_INPUT_STR
    dq cg_str_at        ; 63 IR_STR_AT
    dq cg_int_to_str    ; 64 IR_INT_TO_STR
    dq cg_str_to_int    ; 65 IR_STR_TO_INT
    dq cg_str_concat    ; 66 IR_STR_CONCAT
    dq cg_arr_push      ; 67 IR_ARR_PUSH
    dq cg_arr_pop       ; 68 IR_ARR_POP
    dq cg_read_file     ; 69 IR_READ_FILE
    dq cg_write_file    ; 70 IR_WRITE_FILE
    dq cg_arg_str      ; 71 IR_ARG_STR
    dq cg_str_find      ; 72 IR_STR_FIND
    dq cg_str_slice     ; 73 IR_STR_SLICE
    dq cg_exit          ; 74 IR_EXIT
    dq cg_append_file   ; 75 IR_APPEND_FILE

; ── Codegen handlers ────────────────────────────────────────
; r14=opcode  r15=A(operand)  rdi=B(operand)
; rbx=ir instruction ptr
; Each handler ends with ret → returns to cg_run .next

cg_nop:
    ret

cg_const:
    ; "    mov rax, N\n"
    mov     rsi, f_mv_rax
    mov     rdx, f_mv_rax_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    jmp     emit_nl

cg_load_g:
    mov     rsi, f_vld
    mov     rdx, f_vld_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_brk_nl
    mov     rdx, f_brk_nl_l
    jmp     emit_bytes

cg_store_g:
    mov     rsi, f_vst_a
    mov     rdx, f_vst_a_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_vst_b
    mov     rdx, f_vst_b_l
    jmp     emit_bytes

cg_load_l:
    mov     rsi, f_lld
    mov     rdx, f_lld_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_brk_nl
    mov     rdx, f_brk_nl_l
    jmp     emit_bytes

cg_store_l:
    mov     rsi, f_lst_a
    mov     rdx, f_lst_a_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_lst_b
    mov     rdx, f_lst_b_l
    jmp     emit_bytes

cg_load_p:
    mov     rsi, f_pld
    mov     rdx, f_pld_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_brk_nl
    mov     rdx, f_brk_nl_l
    jmp     emit_bytes

cg_store_p:
    mov     rsi, f_pst_a
    mov     rdx, f_pst_a_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_lst_b
    mov     rdx, f_lst_b_l
    jmp     emit_bytes

cg_push:
    mov     rsi, f_push_rax
    mov     rdx, f_push_rax_l
    jmp     emit_bytes

cg_pop_rbx:
    mov     rsi, f_pop_rbx
    mov     rdx, f_pop_rbx_l
    jmp     emit_bytes

cg_mov_rbx:
    mov     rsi, f_mv_rbx_rax
    mov     rdx, f_mv_rbx_l
    jmp     emit_bytes

cg_add:
    mov     rsi, f_add_rbx
    mov     rdx, f_add_l
    jmp     emit_bytes

cg_sub:
    mov     rsi, f_sub_rbx
    mov     rdx, f_sub_l
    jmp     emit_bytes

cg_mul:
    mov     rsi, f_mul_rbx
    mov     rdx, f_mul_l
    jmp     emit_bytes

cg_div:
    mov     rsi, f_div_seq
    mov     rdx, f_div_l
    jmp     emit_bytes

cg_mod:
    mov     rsi, f_mod_seq
    mov     rdx, f_mod_l
    jmp     emit_bytes

cg_cmp:
    ; IR_CMP: A=op_token(r15), B=cf_label_id(rdi)
    ; Emit: "    cmp rbx, rax\n    jXX _cf_N\n"
    push    rdi                 ; save cf_label_id (B) before emit clobbers rdi
    mov     rsi, f_cmp_rbx
    mov     rdx, f_cmp_rbx_l
    call    emit_bytes
    ; pick inverted jcc string by (op_token - TOK_GT)
    mov     rax, r15
    sub     rax, TOK_GT
    cmp     rax, 0
    jl      .def
    cmp     rax, 5
    jg      .def
    jmp     qword [.jcc_tbl + rax*8]
.def:
    mov     rsi, .jne_s
    mov     rdx, .jne_l
    jmp     .emit
.jgt: mov   rsi, .jle_s
      mov   rdx, .jle_l
      jmp   .emit
.jlt: mov   rsi, .jge_s
      mov   rdx, .jge_l
      jmp   .emit
.jeq: mov   rsi, .jne_s
      mov   rdx, .jne_l
      jmp   .emit
.jne: mov   rsi, .je_s
      mov   rdx, .je_l
      jmp   .emit
.jge: mov   rsi, .jl_s
      mov   rdx, .jl_l
      jmp   .emit
.jle: mov   rsi, .jg_s
      mov   rdx, .jg_l
.emit:
    call    emit_bytes          ; "    jXX "
    pop     rdi                 ; rdi = cf_label_id
    mov     rsi, LBL_CF
    call    emit_lbl_ref        ; "_cf_N"
    jmp     emit_nl

align 8
.jcc_tbl: dq .jgt, .jlt, .jeq, .jne, .jge, .jle
.jle_s db "    jle "
.jle_l equ $ - .jle_s
.jge_s db "    jge "
.jge_l equ $ - .jge_s
.jne_s db "    jne "
.jne_l equ $ - .jne_s
.je_s  db "    je "
.je_l  equ $ - .je_s
.jl_s  db "    jl "
.jl_l  equ $ - .jl_s
.jg_s  db "    jg "
.jg_l  equ $ - .jg_s

cg_jz:
    ; IR_JZ: A=lbl_id(r15), B=lbl_type(rdi)
    push    rdi                 ; save lbl_type
    mov     rsi, f_test_rax
    mov     rdx, f_test_rax_l
    call    emit_bytes
    pop     rsi                 ; rsi = lbl_type
    mov     rdi, r15            ; rdi = lbl_id
    call    emit_lbl_ref
    jmp     emit_nl

cg_jmp:
    ; IR_JMP: A=lbl_id(r15), B=lbl_type(rdi)
    push    rdi
    mov     rsi, f_jmp_s
    mov     rdx, f_jmp_l
    call    emit_bytes
    pop     rsi
    mov     rdi, r15
    call    emit_lbl_ref
    jmp     emit_nl

cg_lbl:
    ; IR_LBL: A=lbl_id(r15), B=lbl_type(rdi)
    mov     rsi, rdi
    mov     rdi, r15
    call    emit_lbl_def
    ret

cg_call:
    ; IR_CALL: A=name_ptr(r15), B=name_len(rdi)
    push    rdi                 ; save name_len
    mov     rsi, f_call_fn
    mov     rdx, f_call_fn_l
    call    emit_bytes
    pop     rdx                 ; name_len
    mov     rsi, r15            ; name_ptr
    call    emit_bytes
    jmp     emit_nl

cg_add_rsp:
    mov     rsi, f_add_rsp
    mov     rdx, f_add_rsp_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    jmp     emit_nl

cg_ret:
    mov     rsi, f_ret_lv
    mov     rdx, f_ret_lv_l
    jmp     emit_bytes

cg_print_int:
    mov     rsi, f_print_int
    mov     rdx, f_print_int_l
    jmp     emit_bytes

cg_print_str:
    ; IR_PRINT_STR: A=str_index(r15)
    mov     rsi, f_wr_a
    mov     rdx, f_wr_a_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_wr_b
    mov     rdx, f_wr_b_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_wr_c
    mov     rdx, f_wr_c_l
    jmp     emit_bytes

cg_fn_bgn:
    ; IR_FN_BGN: A=name_ptr(r15), B=name_len(rdi)
    push    rdi                 ; save name_len
    mov     qword [cur_emit], 1
    mov     rsi, f_fn_pfx
    mov     rdx, f_fn_pfx_l
    call    emit_bytes
    pop     rdx                 ; name_len
    mov     rsi, r15            ; name_ptr
    call    emit_bytes
    mov     rsi, f_colon_nl
    mov     rdx, f_colon_nl_l
    call    emit_bytes
    mov     rsi, f_fn_pro
    mov     rdx, f_fn_pro_l
    jmp     emit_bytes

cg_fn_end:
    ; default leave/ret (if function had no explicit return)
    mov     rsi, f_ret_lv
    mov     rdx, f_ret_lv_l
    call    emit_bytes
    mov     qword [cur_emit], 0
    ret

cg_arr_new:
    ; IR_ARR_NEW: A=count(r15)
    mov     rsi, f_mv_rdi
    mov     rdx, f_mv_rdi_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_arr_new_c
    mov     rdx, f_arr_new_l
    jmp     emit_bytes

cg_arr_ld:
    ; pop rbx / add rbx,rax / mov rax,[rbx]
    mov     rsi, f_arr_deref
    mov     rdx, f_arr_deref_l
    jmp     emit_bytes

cg_arr_st:
    ; pop rbx / mov [rbx+rcx], rax
    mov     rsi, f_arr_store
    mov     rdx, f_arr_store_l
    jmp     emit_bytes

cg_heap_st:
    ; IR_STORE_HEAP: A=byte_offset(r15)
    ; Array base ptr is on the NASM stack top (pushed by ir_push after ARR_NEW).
    ; Expression evaluation may clobber rbx, so peek from [rsp] instead.
    ; Emit: "    mov rbx, [rsp]\n    mov [rbx+A], rax\n"
    mov     rsi, .s
    mov     rdx, .s_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, .e
    mov     rdx, .e_l
    jmp     emit_bytes
.s   db "    mov rbx, [rsp]", 10, "    mov [rbx+"
.s_l equ $ - .s
.e   db "], rax", 10
.e_l equ $ - .e

cg_set_ef:
    mov     rsi, f_set_ef
    mov     rdx, f_set_ef_l
    jmp     emit_bytes

cg_clr_ef:
    mov     rsi, f_clr_ef
    mov     rdx, f_clr_ef_l
    jmp     emit_bytes

cg_jmp_tc:
    ; IR_JMP_TC: A=tc_label_id(r15)
    mov     rsi, f_jmp_s
    mov     rdx, f_jmp_l
    call    emit_bytes
    mov     rdi, r15
    mov     rsi, LBL_TC
    call    emit_lbl_ref
    jmp     emit_nl

cg_mod_bgn:
    ; IR_MOD_BGN: A=name_ptr(r15), B=name_len(rdi)
    ; cg_run sets: r15=[IR_F_A]=name_ptr, rdi=[IR_F_B]=name_len
    ; Copy name into mod_name, set mod_len
    push    rcx
    push    rsi
    push    rdi                 ; save name_len (B)
    lea     rdi, [mod_name]     ; dst
    mov     rsi, r15            ; src = name_ptr
    pop     rcx                 ; rcx = name_len
    push    rcx                 ; re-save for mod_len
    rep movsb
    mov     byte [rdi], 0
    pop     rax                 ; rax = name_len
    mov     [mod_len], rax
    pop     rsi
    pop     rcx
    ret

cg_mod_end:
    mov     qword [mod_len], 0
    ret

cg_imul8:
    mov     rsi, f_imul8
    mov     rdx, f_imul8_l
    jmp     emit_bytes

cg_mov_rcx:
    mov     rsi, f_mv_rcx_rax
    mov     rdx, f_mv_rcx_l
    jmp     emit_bytes

cg_pop_rax:
    mov     rsi, f_pop_rax_s
    mov     rdx, f_pop_rax_l
    jmp     emit_bytes

cg_inc_rax:
    mov     rsi, f_inc_rax
    mov     rdx, f_inc_rax_l
    jmp     emit_bytes

cg_fe_st:
    ; IR_FE_ST: A=depth_bytes(r15)
    mov     rsi, f_fe_st_a
    mov     rdx, f_fe_st_a_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_fe_st_b
    mov     rdx, f_fe_st_b_l
    jmp     emit_bytes

cg_fe_cmp:
    ; IR_FE_CMP: A=depth_bytes(r15)
    mov     rsi, f_fe_cmp_a
    mov     rdx, f_fe_cmp_a_l
    call    emit_bytes
    mov     rax, r15
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_brk_nl
    mov     rdx, f_brk_nl_l
    jmp     emit_bytes

cg_jge:
    ; IR_JGE: A=lbl_id(r15), B=lbl_type(rdi)
    push    rdi
    mov     rsi, f_jge_s
    mov     rdx, f_jge_l
    call    emit_bytes
    pop     rsi
    mov     rdi, r15
    call    emit_lbl_ref
    jmp     emit_nl

cg_argc:
    mov     rsi, f_argc
    mov     rdx, f_argc_l
    jmp     emit_bytes

cg_arg:
    mov     rsi, f_arg
    mov     rdx, f_arg_l
    jmp     emit_bytes

cg_exit:
    mov     rsi, f_exit
    mov     rdx, f_exit_l
    jmp     emit_bytes

cg_arg_str:
    ; Emit: rsi=index, rdi=dst_slot, call _nq_arg_str.
    ; N = str_cnt + istr_total + its_cnt + str_cat_cnt + file_read_total + arg_str_cur
    push    r12
    mov     rsi, f_arg_str_pre
    mov     rdx, f_arg_str_pre_l
    call    emit_bytes
    mov     rax, [str_cnt]
    add     rax, [istr_total]
    add     rax, [its_cnt]
    add     rax, [str_cat_cnt]
    add     rax, [file_read_total]
    add     rax, [arg_str_cur]
    inc     qword [arg_str_cur]
    mov     r12, rax
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_arg_str_call
    mov     rdx, f_arg_str_call_l
    call    emit_bytes
    pop     r12
    ret

cg_str_find:
    mov     rsi, f_str_find
    mov     rdx, f_str_find_l
    jmp     emit_bytes

cg_str_slice:
    ; Stack before call: [top]=start, below=source; rax=end.
    push    r12
    mov     rsi, f_slice_pre
    mov     rdx, f_slice_pre_l
    call    emit_bytes
    mov     rax, [str_cnt]
    add     rax, [istr_total]
    add     rax, [its_cnt]
    add     rax, [str_cat_cur]
    inc     qword [str_cat_cur]
    mov     r12, rax
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_slice_call
    mov     rdx, f_slice_call_l
    call    emit_bytes
    mov     rax, r12
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    pop     r12
    ret

cg_lnot:
    mov     rsi, f_lnot
    mov     rdx, f_lnot_l
    jmp     emit_bytes

cg_arr_len:
    mov     rsi, f_arr_len
    mov     rdx, f_arr_len_l
    jmp     emit_bytes

cg_abs:
    mov     rsi, f_abs
    mov     rdx, f_abs_l
    jmp     emit_bytes

cg_min:
    mov     rsi, f_min
    mov     rdx, f_min_l
    jmp     emit_bytes

cg_max:
    mov     rsi, f_max
    mov     rdx, f_max_l
    jmp     emit_bytes

cg_input_int:
    mov     rsi, f_input_int
    mov     rdx, f_input_int_l
    jmp     emit_bytes

cg_print_nl:
    mov     rsi, f_print_nl
    mov     rdx, f_print_nl_l
    jmp     emit_bytes

cg_band:
    mov     rsi, f_band
    mov     rdx, f_band_l
    jmp     emit_bytes

cg_bor:
    mov     rsi, f_bor
    mov     rdx, f_bor_l
    jmp     emit_bytes

cg_bxor:
    mov     rsi, f_bxor
    mov     rdx, f_bxor_l
    jmp     emit_bytes

cg_bnot:
    mov     rsi, f_bnot
    mov     rdx, f_bnot_l
    jmp     emit_bytes

cg_shl:
    mov     rsi, f_shl
    mov     rdx, f_shl_l
    jmp     emit_bytes

cg_shr:
    mov     rsi, f_shr
    mov     rdx, f_shr_l
    jmp     emit_bytes

cg_print_str_var:
    mov     rsi, f_pstr_var
    mov     rdx, f_pstr_var_l
    jmp     emit_bytes

cg_str_len:
    mov     rsi, f_str_len_a
    mov     rdx, f_str_len_l
    jmp     emit_bytes

cg_str_eq:
    mov     rsi, f_str_eq_a
    mov     rdx, f_str_eq_l
    jmp     emit_bytes

cg_str_neq:
    mov     rsi, f_str_neq_a
    mov     rdx, f_str_neq_l
    jmp     emit_bytes

cg_str_at:
    mov     rsi, f_str_at_a
    mov     rdx, f_str_at_l
    jmp     emit_bytes

cg_int_to_str:
    ; Emit: "    mov rdi, N\n    call _nq_int_to_str_slot\n"
    ; N = str_cnt + istr_total + its_cur  (unique slot per call site)
    mov     rsi, f_mv_rdi
    mov     rdx, f_mv_rdi_l
    call    emit_bytes
    mov     rax, [str_cnt]
    add     rax, [istr_total]
    add     rax, [its_cur]
    inc     qword [its_cur]
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_its_call
    mov     rdx, f_its_call_l
    jmp     emit_bytes

cg_input_str:
    ; Emit: "    mov rdi, N\n    call _nq_input_str\n"
    ; N = str_cnt + istr_cur  (unique slot per call site)
    mov     rsi, f_mv_rdi
    mov     rdx, f_mv_rdi_l
    call    emit_bytes
    mov     rax, [str_cnt]
    add     rax, [istr_cur]
    inc     qword [istr_cur]
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_istr_call
    mov     rdx, f_istr_call_l
    jmp     emit_bytes

cg_str_to_int:
    ; Emit: rax=string_slot fragment → _nq_atoi → rax=integer
    mov     rsi, f_sti_a
    mov     rdx, f_sti_a_l
    jmp     emit_bytes

cg_read_file:
    ; Emit: rsi=path_slot, rdi=dst_slot, call _nq_read_file.
    ; N = str_cnt + istr_total + its_cnt + str_cat_cnt + file_read_cur
    push    r12
    mov     rsi, f_read_file_pre
    mov     rdx, f_read_file_pre_l
    call    emit_bytes
    mov     rax, [str_cnt]
    add     rax, [istr_total]
    add     rax, [its_cnt]
    add     rax, [str_cat_cnt]
    add     rax, [file_read_cur]
    inc     qword [file_read_cur]
    mov     r12, rax
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_read_file_call
    mov     rdx, f_read_file_call_l
    call    emit_bytes
    pop     r12
    ret

cg_write_file:
    ; Emit: rsi=data_slot, rdi=path_slot, call _nq_write_file.
    mov     rsi, f_write_file_call
    mov     rdx, f_write_file_call_l
    jmp     emit_bytes

cg_append_file:
    ; Emit: rsi=data_slot, rdi=path_slot, call _nq_append_file.
    mov     rsi, f_append_file_call
    mov     rdx, f_append_file_call_l
    jmp     emit_bytes

cg_str_concat:
    ; Emit: "    mov rdx, rax\n    mov rsi, rbx\n    mov rdi, N\n
    ;        call _nq_str_concat\n    mov rax, N\n"
    ; N = str_cnt + istr_total + its_cnt + str_cat_cur  (unique slot)
    push    r12
    mov     rsi, f_scat_pre
    mov     rdx, f_scat_pre_l
    call    emit_bytes
    mov     rax, [str_cnt]
    add     rax, [istr_total]
    add     rax, [its_cnt]
    add     rax, [str_cat_cur]
    inc     qword [str_cat_cur]
    mov     r12, rax
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     rsi, f_scat_call
    mov     rdx, f_scat_call_l
    call    emit_bytes
    mov     rax, r12
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    pop     r12
    ret

cg_arr_push:
    ; rax = val (from parse_expr), stack top = arr_ptr (from ir_push)
    ; Emit: pop rdi; mov rsi, rax; call _arr_push
    mov     rsi, f_arr_push_c
    mov     rdx, f_arr_push_l
    jmp     emit_bytes

cg_arr_pop:
    ; rdi = arr_ptr (already in rdi from prior LOAD), returns last element in rax
    ; Emit: call _arr_pop
    mov     rsi, f_arr_pop_c
    mov     rdx, f_arr_pop_l
    jmp     emit_bytes
