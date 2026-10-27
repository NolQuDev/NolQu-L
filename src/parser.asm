parser_run:
    mov     qword [tok_pos],   0
    mov     qword [ht_cnt],    0
    mov     qword [lht_cnt],   0
    mov     qword [label_ctr], 0
    mov     qword [ir_cnt],    0
    mov     qword [fn_cnt],    0
    mov     qword [mod_cnt],   0
    mov     qword [in_fn],     0
    mov     qword [blk_dep],   0
    mov     qword [decl_phase], 2
    mov     qword [lp_dep],    0
    mov     qword [for_dep],   0
    mov     qword [try_dep],   0
    mov     qword [mod_len],   0
    mov     qword [str_cnt],   0
    mov     qword [istr_total], 0
    mov     qword [istr_cur],   0
    mov     qword [its_cnt],    0
    mov     qword [its_cur],    0
    mov     qword [str_cat_cnt], 0
    mov     qword [str_cat_cur], 0
    mov     qword [file_read_total], 0
    mov     qword [file_read_cur],   0
    mov     qword [write_file_total], 0
    mov     qword [append_file_total], 0
    mov     qword [arg_str_total], 0
    mov     qword [arg_str_cur],   0
    mov     qword [str_find_total], 0
    mov     qword [str_slice_total], 0
    push    rdi
    push    rcx
    lea     rdi, [ht_key]
    xor     rax, rax
    mov     rcx, HT_SZ*3
    rep stosq
    lea     rdi, [lht_key]
    mov     rcx, HT_SZ*3
    rep stosq
    pop     rcx
    pop     rdi
.lp:
    call    tok_skip_nl
    cmp     qword [had_error], 0
    jne     .done
    call    tok_cur_type
    cmp     rax, TOK_EOF
    je      .check_unused_globals
    call    parse_stmt
    cmp     qword [had_error], 0
    jne     .done
    jmp     .lp
.check_unused_globals:
    push    r14
    push    r15
    xor     r15, r15
.ug_chk:
    cmp     r15, [ht_cnt]
    jge     .ug_done
    cmp     qword [gvar_reads+r15*8], 0
    jne     .ug_nx
    imul    rax, r15, VAR_NL
    lea     rdx, [var_store+rax]
    mov     rcx, [gvar_names_l+r15*8]
    mov     rdi, [gvar_decl_line+r15*8]
    mov     rsi, [gvar_decl_col+r15*8]
    call    emit_unused_var_err
.ug_nx:
    inc     r15
    jmp     .ug_chk
.ug_done:
    pop     r15
    pop     r14
.done:
    ret

parse_stmt:
    call    tok_cur_type
    cmp     qword [blk_dep], 0
    jne     .dispatch
    cmp     rax, TOK_VAR
    je      .chk_var_phase
    cmp     rax, TOK_INTTYPE
    jne     .chk_decl
.chk_var_phase:
    cmp     qword [decl_phase], 2
    jne     .dispatch
    mov     qword [decl_phase], 1
    jmp     .dispatch
.chk_decl:
    cmp     rax, TOK_FUNC
    je      .dispatch
    cmp     rax, TOK_MODULE
    je      .dispatch
    cmp     rax, TOK_IMPORT
    je      .dispatch
    mov     qword [decl_phase], 0
.dispatch:
    cmp     rax, TOK_VAR
    je      .v
    cmp     rax, TOK_INTTYPE
    je      .v
    cmp     rax, TOK_PRINT
    je      .p
    cmp     rax, TOK_PRINTLN
    je      .pl
    cmp     rax, TOK_IF       
    je      .i
    cmp     rax, TOK_WHILE    
    je      .w
    cmp     rax, TOK_FOR      
    je      .f
    cmp     rax, TOK_FUNC     
    je      .fn
    cmp     rax, TOK_RETURN   
    je      .r
    cmp     rax, TOK_BREAK    
    je      .b
    cmp     rax, TOK_CONTINUE 
    je      .c
    cmp     rax, TOK_TRY      
    je      .t
    cmp     rax, TOK_ERROR    
    je      .e
    cmp     rax, TOK_MODULE   
    je      .m
    cmp     rax, TOK_IMPORT   
    je      .im
    cmp     rax, TOK_IDENT
    je      .id
    cmp     rax, TOK_PUSH
    je      .push_stmt
    cmp     rax, TOK_EXIT
    je      .exit_stmt
    cmp     rax, TOK_WRITE_FILE
    je      .effect_builtin_stmt
    cmp     rax, TOK_APPEND_FILE
    je      .effect_builtin_stmt
    cmp     rax, TOK_INT
    je      .expr_stmt_start
    cmp     rax, TOK_STRING
    je      .expr_stmt_start
    cmp     rax, TOK_LPAREN
    je      .expr_stmt_start
    cmp     rax, TOK_LBRACKET
    je      .expr_stmt_start
    mov     rdx, em_bad_stmt
    mov     rcx, em_bad_stmt_l
    call    emit_error_tok
    call    tok_advance
    ret
.v:  call parse_var        
    ret
.p:  call parse_print
    ret
.pl: call parse_println
    ret
.i:  call parse_if         
    ret
.w:  call parse_while      
    ret
.f:  call parse_for        
    ret
.fn: call parse_func       
    ret
.r:  call parse_return     
    ret
.b:  call parse_break      
    ret
.c:  call parse_continue   
    ret
.t:  call parse_try        
    ret
.e:  call parse_error_stmt 
    ret
.m:  call parse_module     
    ret
.im: call parse_import
    ret
.id: call parse_ident_stmt
    ret
.push_stmt:
    call    parse_factor        ; parse push(...) as expression
    call    ty_discard          ; discard return value (new count)
    ret
.exit_stmt:
    call    parse_factor        ; parse exit(...) as expression
    call    ty_discard          ; exit does not return at runtime
    ret
.effect_builtin_stmt:
    call    parse_factor        ; parse side-effecting builtin call
    call    ty_discard          ; discard return value
    ret
.expr_stmt_start:
    call    stmt_line_has_eq
    test    rax, rax
    jz      .expr_stmt_bad
    mov     rdx, em_bad_assign_target
    mov     rcx, em_bad_assign_target_l
    call    emit_error_tok
    call    tok_advance
    ret
.expr_stmt_bad:
    mov     rdx, em_expr_stmt
    mov     rcx, em_expr_stmt_l
    call    emit_error_tok
    call    tok_advance
    ret

; ─── parse_var: var IDENT = EXPR  or  var IDENT = [...] ──────
parse_var:
    push    rbx
    push    r12
    push    r13
    call    tok_advance
    call    tok_cur_ptr
    mov     r12, rax
    call    tok_cur_len
    mov     r13, rax
    call    tok_cur_line
    mov     [decl_pending_line], rax
    call    tok_cur_col
    mov     [decl_pending_col], rax
    cmp     qword [in_fn], 1
    je      .local_scope
    ; global: check fn-name conflict
    mov     rdi, r12
    mov     rsi, r13
    call    fn_find
    cmp     rax, -1
    je      .global_var_chk
    mov     rdx, em_name_conflict
    mov     rcx, em_name_conflict_l
    call    emit_error_tok
    jmp     .done
.global_var_chk:
    ; global: check existing global variable with same name
    push    rsi
    push    rcx
    mov     rsi, r12
    mov     rcx, r13
    call    sym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    je      .after_dup_chk
    mov     rdx, em_local_dup
    mov     rcx, em_local_dup_l
    call    emit_error_tok
    jmp     .done
.local_scope:
    push    rsi
    push    rcx
    mov     rsi, r12
    mov     rcx, r13
    call    lsym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    je      .after_dup_chk
    mov     rdx, em_local_dup
    mov     rcx, em_local_dup_l
    call    emit_error_tok
    jmp     .done
.after_dup_chk:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_EQ
    jne     .err
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_LBRACKET
    je      .arr
    cmp     rax, TOK_STRTYPE
    je      .typed_arr_str
    cmp     rax, TOK_INTTYPE
    je      .typed_arr_int

    ; normal expression — set decl mode so ir_store creates new local, never touches globals
    call    parse_expr_required
    mov     rbx, r12
    mov     r12, r13
    mov     qword [var_decl_mode], 1
    call    ir_store
    mov     qword [var_decl_mode], 0
    jmp     .done

; var name = str[]  — empty typed string array
; Only intercept when next token after 'str' is '[' (not '(' which means str(n) call).
.typed_arr_str:
    mov     rdi, 1
    call    tok_peek            ; peek 1 ahead of current 'str' token
    cmp     rax, TOK_LBRACKET
    jne     .tas_expr           ; str(n) or something else — treat as expression
    call    tok_advance         ; eat 'str'
    call    tok_advance         ; eat '['
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .typed_array_rbracket_err
    call    tok_advance         ; eat ']'
.tas_done:
    mov     rdi, 0
    call    ir_arr_new
    mov     rbx, r12
    mov     r12, r13
    mov     rdi, TY_STR_ARR
    call    ty_push
    mov     qword [var_decl_mode], 1
    call    ir_store
    mov     qword [var_decl_mode], 0
    jmp     .done
.tas_expr:
    call    parse_expr_required
    mov     rbx, r12
    mov     r12, r13
    mov     qword [var_decl_mode], 1
    call    ir_store
    mov     qword [var_decl_mode], 0
    jmp     .done

; var name = int[]  — empty typed integer array
; Only intercept when next token after 'int' is '[' (not '(' which means int(s) call).
.typed_arr_int:
    mov     rdi, 1
    call    tok_peek            ; peek 1 ahead of current 'int' token
    cmp     rax, TOK_LBRACKET
    jne     .tai_expr           ; int(s) or other — treat as expression
    call    tok_advance         ; eat 'int'
    call    tok_advance         ; eat '['
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .typed_array_rbracket_err
    call    tok_advance         ; eat ']'
.tai_done:
    mov     rdi, 0
    call    ir_arr_new
    mov     rbx, r12
    mov     r12, r13
    mov     rdi, TY_ARR
    call    ty_push
    mov     qword [var_decl_mode], 1
    call    ir_store
    mov     qword [var_decl_mode], 0
    jmp     .done
.tai_expr:
    call    parse_expr_required
    mov     rbx, r12
    mov     r12, r13
    mov     qword [var_decl_mode], 1
    call    ir_store
    mov     qword [var_decl_mode], 0
    jmp     .done
.typed_array_rbracket_err:
    mov     rdx, em_expect_typed_array_rbracket
    mov     rcx, em_expect_typed_array_rbracket_l
    call    emit_error_tok
    jmp     .done

.arr:
    ; save r12/r13 before using r14/r15 in the count scan
    push    r12
    push    r13
    call    tok_advance         ; eat [
    ; count elements by scanning ahead
    mov     r15, [tok_pos]
    xor     r14, r14
.cnt:
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    je      .cnt_done
    cmp     rax, TOK_EOF
    je      .cnt_done
    cmp     rax, TOK_COMMA
    je      .cnt_comma
    inc     r14
.cnt_skip:
    call    tok_advance
    jmp     .cnt
.cnt_comma:
    mov     rdi, 1
    call    tok_peek
    cmp     rax, TOK_COMMA
    je      .cnt_err
    cmp     rax, TOK_RBRACKET
    je      .cnt_err
    cmp     rax, TOK_EOF
    je      .cnt_err
    cmp     rax, TOK_NEWLINE
    je      .cnt_err
    jmp     .cnt_skip
.cnt_err:
    mov     rdx, em_array_item
    mov     rcx, em_array_item_l
    call    emit_error_tok
    pop     r13
    pop     r12
    jmp     .done
.cnt_done:
    mov     [tok_pos], r15      ; restore to start of array
    cmp     r14, 8158       ; 8192 - 34 header slots
    jle     .cnt_size_ok
    mov     rdx, em_array_too_large
    mov     rcx, em_array_too_large_l
    call    emit_error_tok
    pop     r13
    pop     r12
    jmp     .done
.cnt_size_ok:
    ; emit IR_ARR_NEW(count)
    mov     rdi, r14
    call    ir_arr_new          ; rax=ptr at runtime
    ; save ptr on runtime stack, copy ptr to rbx
    call    ir_push             ; push ptr
    call    ir_mov_rbx          ; mov rbx, rax  (rbx = array base)
    ; emit each element; track whether all elements are string literals
    mov     qword [arr_is_str_arr], 1
    mov     qword [arr_elem_type], TY_UNK
    xor     r14, r14            ; element index
.elem:
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    je      .edone_adv
    cmp     rax, TOK_EOF
    je      .maybe_closed
    cmp     rax, TOK_NEWLINE
    je      .maybe_closed
    cmp     rax, TOK_COMMA
    je      .esk
    push    r14
    call    parse_expr          ; element value → rax at runtime
    ; peek type before discarding — if not TY_STR, mark as non-string array
    mov     rax, [type_stkp]
    mov     rdx, [type_stk+rax*8-8]
    cmp     rdx, TY_STR
    je      .elem_str_ok
    mov     qword [arr_is_str_arr], 0
.elem_str_ok:
    cmp     rdx, TY_UNK
    je      .elem_type_ok
    cmp     qword [arr_elem_type], TY_UNK
    je      .elem_type_set
    cmp     qword [arr_elem_type], rdx
    je      .elem_type_ok
    mov     rdx, em_array_mixed_type
    mov     rcx, em_array_mixed_type_l
    call    emit_error_tok
    jmp     .elem_type_ok
.elem_type_set:
    mov     [arr_elem_type], rdx
.elem_type_ok:
    call    ty_discard
    pop     r14
    ; IR_STORE_HEAP: A = byte offset into array
    ; codegen: "    mov [rbx+A], rax\n"
    push    r14
    imul    rax, r14, 8
    mov     rdi, rax
    mov     rsi, rdi
    mov     rdi, IR_STORE_HEAP
    xor     rdx, rdx
    call    ir_emit
    pop     r14
    inc     r14
    jmp     .elem
.maybe_closed:
    mov     rdi, -1
    call    tok_peek
    cmp     rax, TOK_RBRACKET
    je      .edone_noadv
    mov     rdx, em_parse
    mov     rcx, em_parse_l
    call    emit_error_tok
    pop     r13
    pop     r12
    jmp     .done
.esk:
    mov     rdi, 1
    call    tok_peek
    cmp     rax, TOK_COMMA
    je      .item_err
    cmp     rax, TOK_RBRACKET
    je      .item_err
    cmp     rax, TOK_EOF
    je      .item_err
    cmp     rax, TOK_NEWLINE
    je      .item_err
    call    tok_advance
    jmp     .elem
.item_err:
    mov     rdx, em_array_item
    mov     rcx, em_array_item_l
    call    emit_error_tok
    pop     r13
    pop     r12
    jmp     .done
.edone_adv:
    call    tok_advance         ; eat ]
.edone_noadv:
    ; restore ptr from runtime stack
    call    ir_pop_rax          ; pop rax  (array ptr back in rax)
    pop     r13                 ; restore name len
    pop     r12                 ; restore name ptr
    mov     rbx, r12
    mov     r12, r13
    ; If all elements were strings (and non-empty), use TY_STR_ARR so that
    ; a[i] returns TY_STR and print works correctly.
    test    r14, r14
    jz      .arr_int_type       ; empty array → TY_ARR
    cmp     qword [arr_is_str_arr], 1
    jne     .arr_int_type
    mov     rdi, TY_STR_ARR
    jmp     .arr_type_push
.arr_int_type:
    mov     rdi, TY_ARR
.arr_type_push:
    call    ty_push
    mov     qword [var_decl_mode], 1
    call    ir_store
    mov     qword [var_decl_mode], 0
    jmp     .done

.err:
    mov     rdx, em_parse
    mov     rcx, em_parse_l
    call    emit_error_tok
.done:
    pop     r13
    pop     r12
    pop     rbx
    ret

; ─── parse_ident_stmt ────────────────────────────────────────
parse_ident_stmt:
    push    r12
    push    r13
    push    r14
    push    rbx
    call    tok_cur_ptr
    mov     r12, rax
    call    tok_cur_len
    mov     r13, rax
    mov     rdi, 1
    call    tok_peek
    cmp     rax, TOK_EQ
    je      .assign
    cmp     rax, TOK_LBRACKET
    je      .arr_assign
    cmp     rax, TOK_LPAREN
    je      .call_stmt
    cmp     rax, TOK_DOT
    je      .call_stmt
    cmp     rax, TOK_PLUSEQ
    je      .compound
    cmp     rax, TOK_MINUSEQ
    je      .compound
    cmp     rax, TOK_STAREQ
    je      .compound
    cmp     rax, TOK_SLASHEQ
    je      .compound
    cmp     rax, TOK_PERCENTEQ
    je      .compound
    mov     rdx, em_ident_stmt
    mov     rcx, em_ident_stmt_l
    call    emit_error_tok
    call    tok_advance         ; consume stuck token to prevent infinite loop
    jmp     .done
.call_stmt:
    call    parse_expr
    call    ty_discard
    jmp     .done
.assign:
    call    tok_advance         ; eat ident
    call    tok_advance         ; eat =
    ; reject assignment to undeclared variable (must use 'var')
    push    rsi
    push    rcx
    mov     rsi, r12
    mov     rcx, r13
    call    var_exists
    pop     rcx
    pop     rsi
    test    rax, rax
    jnz     .assign_ok
    mov     rdx, em_undef
    mov     rcx, em_undef_l
    call    emit_error_tok
    call    parse_expr_required ; consume RHS to stay in sync
    call    ty_discard
    jmp     .done
.assign_ok:
    call    parse_expr_required
    mov     rbx, r12
    mov     r12, r13
    call    ir_store
    jmp     .done
.compound:
    ; r12=name_ptr r13=name_len — load variable, keep both types for arith check.
    mov     rbx, r12
    push    r12
    mov     r12, r13
    call    ir_load             ; old value → rax, type pushed
    pop     r12
    call    ir_push             ; push old value to runtime stack
    call    tok_advance         ; eat identifier
    call    tok_cur_type
    mov     r14, rax            ; save compound op token
    call    tok_advance         ; eat compound op
    call    parse_expr_required ; RHS → rax, type pushed
    call    ty_check_arith      ; compound assignment is integer arithmetic
    cmp     r14, TOK_PLUSEQ
    je      .ca_add
    cmp     r14, TOK_MINUSEQ
    je      .ca_sub
    cmp     r14, TOK_STAREQ
    je      .ca_mul
    cmp     r14, TOK_SLASHEQ
    je      .ca_div
    cmp     r14, TOK_PERCENTEQ
    je      .ca_mod
    jmp     .ca_store
.ca_add:
    call    ir_pop_rbx
    call    ir_add
    jmp     .ca_store
.ca_sub:
    call    ir_pop_rbx
    call    ir_sub
    jmp     .ca_store
.ca_mul:
    call    ir_pop_rbx
    call    ir_mul
    jmp     .ca_store
.ca_div:
    call    ir_div              ; div/mod pop their LHS from runtime stack internally
    jmp     .ca_store
.ca_mod:
    call    ir_mod
.ca_store:
    mov     rbx, r12
    mov     r12, r13
    call    ir_store
    jmp     .done
.arr_assign:
    ; IDENT[IDX] = VAL
    ; Load array ptr
    mov     rbx, r12
    push    r13
    mov     r12, r13
    call    ir_load
    call    ty_pop
    mov     r14, rax            ; remember array kind for RHS type validation
    cmp     r14, TY_ARR
    je      .arr_assign_base_ok
    cmp     r14, TY_STR_ARR
    je      .arr_assign_base_ok
    cmp     r14, TY_UNK
    je      .arr_assign_base_ok
    mov     rdx, em_array_store_not_arr
    mov     rcx, em_array_store_not_arr_l
    call    emit_error_tok
    mov     r14, TY_UNK         ; suppress cascaded element-type errors
.arr_assign_base_ok:
    pop     r13
    call    ir_push             ; push array ptr onto runtime stack
    call    tok_advance         ; eat IDENT
    call    tok_advance         ; eat [
    call    tok_cur_type
    cmp     rax, TOK_MINUS
    jne     .arr_assign_idx
    mov     rdx, em_neg_index
    mov     rcx, em_neg_index_l
    call    emit_error_tok
    jmp     .done
.arr_assign_idx:
    cmp     rax, TOK_RBRACKET
    je      .arr_assign_idx_err
    cmp     rax, TOK_EOF
    je      .arr_assign_idx_err
    cmp     rax, TOK_NEWLINE
    je      .arr_assign_idx_err
    call    parse_expr          ; index → rax
    call    ty_pop
    cmp     rax, TY_INT
    je      .arr_assign_idx_type_ok
    cmp     rax, TY_UNK
    je      .arr_assign_idx_type_ok
    mov     rdx, em_index_type
    mov     rcx, em_index_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
.arr_assign_idx_type_ok:
    call    ir_imul8            ; byte offset in rax
    call    ir_push             ; push byte offset onto stack (safe across RHS eval)
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    je      .arr_assign_have_rbracket
    mov     rdx, em_expect_rbracket
    mov     rcx, em_expect_rbracket_l
    call    emit_error_tok
    jmp     .done
.arr_assign_have_rbracket:
    call    tok_advance         ; eat ]
    call    tok_cur_type
    cmp     rax, TOK_EQ
    je      .arr_assign_have_eq
    mov     rdx, em_expect_eq
    mov     rcx, em_expect_eq_l
    call    emit_error_tok
    jmp     .done
.arr_assign_have_eq:
    call    tok_advance         ; eat =
    call    parse_expr_required ; value → rax
    call    ty_pop
    cmp     r14, TY_ARR
    je      .arr_assign_expect_int
    cmp     r14, TY_STR_ARR
    je      .arr_assign_expect_str
    jmp     .arr_assign_store
.arr_assign_expect_int:
    cmp     rax, TY_INT
    je      .arr_assign_store
    cmp     rax, TY_UNK
    je      .arr_assign_store
    mov     rdx, em_array_store_type
    mov     rcx, em_array_store_type_l
    call    emit_error_tok
    jmp     .arr_assign_store
.arr_assign_expect_str:
    cmp     rax, TY_STR
    je      .arr_assign_store
    cmp     rax, TY_UNK
    je      .arr_assign_store
    mov     rdx, em_array_store_type
    mov     rcx, em_array_store_type_l
    call    emit_error_tok
.arr_assign_store:
    call    ir_arr_st           ; pop rbx / mov [rbx+rcx], rax
    jmp     .done
.arr_assign_idx_err:
    mov     rdx, em_array_index
    mov     rcx, em_array_index_l
    call    emit_error_tok
.done:
    pop     rbx
    pop     r14
    pop     r13
    pop     r12
    ret

; ─── parse_print ─────────────────────────────────────────────
parse_print:
    call    tok_advance
    ; Allow `print a, b, "c"` by lowering each item to the
    ; existing print ops in source order.
.item:
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .err_item
    cmp     rax, TOK_EOF
    je      .err_item
    cmp     rax, TOK_RBRACE
    je      .err_item
    cmp     rax, TOK_COMMA
    je      .err_item
    ; Fast path for bare string literal (no + follows) → IR_PRINT_STR
    cmp     rax, TOK_STRING
    jne     .expr
    mov     rdi, 1
    call    tok_peek
    cmp     rax, TOK_PLUS
    je      .expr
    call    str_record
    mov     rdi, rax
    call    ir_print_str
    call    tok_advance
    jmp     .next
.expr:
    call    parse_expr
    call    ty_pop
    cmp     rax, TY_ARR
    je      .is_arr_type
    cmp     rax, TY_STR_ARR
    jne     .not_arr
.is_arr_type:
    mov     rdx, em_print_arr
    mov     rcx, em_print_arr_l
    call    emit_error_tok
    jmp     .do_print_int
.not_arr:
    cmp     rax, TY_STR
    jne     .do_print_int
    call    ir_print_str_var
    jmp     .next
.do_print_int:
    call    ir_print_int
    jmp     .next
.next:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .done
    call    tok_advance
    jmp     .item
.err_item:
    mov     rdx, em_print_item
    mov     rcx, em_print_item_l
    call    emit_error_tok
.done:
    ret

; ─── parse_println ───────────────────────────────────────────
; Like parse_print but appends a newline; allows empty (just newline).
parse_println:
    call    tok_advance         ; eat 'println'
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .nl_only
    cmp     rax, TOK_EOF
    je      .nl_only
    cmp     rax, TOK_RBRACE
    je      .nl_only
.item:
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .done_items
    cmp     rax, TOK_EOF
    je      .done_items
    cmp     rax, TOK_RBRACE
    je      .done_items
    cmp     rax, TOK_COMMA
    je      .err_item
    ; Fast path for bare string literal (no + follows) → IR_PRINT_STR + IR_PRINT_NL
    cmp     rax, TOK_STRING
    jne     .expr_item
    mov     rdi, 1
    call    tok_peek
    cmp     rax, TOK_PLUS
    je      .expr_item
    call    str_record
    mov     rdi, rax
    call    ir_print_str
    call    tok_advance
    jmp     .next
.expr_item:
    call    parse_expr
    call    ty_pop
    cmp     rax, TY_ARR
    je      .is_arr_type
    cmp     rax, TY_STR_ARR
    jne     .not_arr
.is_arr_type:
    mov     rdx, em_print_arr
    mov     rcx, em_print_arr_l
    call    emit_error_tok
    jmp     .do_pi
.not_arr:
    cmp     rax, TY_STR
    jne     .do_pi
    call    ir_print_str_var
    jmp     .next
.do_pi:
    call    ir_print_int
    jmp     .next
.next:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .done_items
    call    tok_advance
    jmp     .need_item
.need_item:
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .err_item
    cmp     rax, TOK_EOF
    je      .err_item
    cmp     rax, TOK_RBRACE
    je      .err_item
    cmp     rax, TOK_COMMA
    je      .err_item
    jmp     .item
.err_item:
    mov     rdx, em_print_item
    mov     rcx, em_print_item_l
    call    emit_error_tok
.done_items:
.nl_only:
    call    ir_print_nl
    ret

parse_expr_required:
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .err
    cmp     rax, TOK_EOF
    je      .err
    cmp     rax, TOK_RBRACE
    je      .err
    cmp     rax, TOK_LBRACE
    je      .err
    cmp     rax, TOK_COMMA
    je      .err
    cmp     rax, TOK_RBRACKET
    je      .err
    cmp     rax, TOK_RPAREN
    je      .err
    cmp     rax, TOK_DOTDOT
    je      .err
    call    parse_expr
    ret
.err:
    mov     rdx, em_expect_expr
    mov     rcx, em_expect_expr_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_UNK
    call    ty_push
    ret

; ─── parse_condition ─────────────────────────────────────────
parse_condition:
    push    r12
    push    r13
    push    r14
    push    r15
    xor     r15, r15             ; not_flag = 0
    call    tok_cur_type
    cmp     rax, TOK_NOT
    jne     .cpc_body
    call    tok_advance          ; eat leading 'not'
    mov     r15, 1               ; not_flag = 1
.cpc_body:
    mov     r12, [label_ctr]    ; _cf_N
    inc     qword [label_ctr]
    mov     r14, [label_ctr]    ; _cd_N
    inc     qword [label_ctr]
.next:
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .need_lhs
    cmp     rax, TOK_EOF
    je      .need_lhs
    cmp     rax, TOK_RBRACE
    je      .need_lhs
    cmp     rax, TOK_LBRACE
    je      .need_lhs
    cmp     rax, TOK_COMMA
    je      .need_lhs
    cmp     rax, TOK_RBRACKET
    je      .need_lhs
    cmp     rax, TOK_RPAREN
    je      .need_lhs
    cmp     rax, TOK_DOTDOT
    je      .need_lhs
    call    parse_expr
    call    ir_push
    call    tok_cur_type
    mov     r13, rax
    cmp     r13, TOK_EQEQ
    je      .cmp_ok
    cmp     r13, TOK_NEQ
    je      .cmp_ok
    cmp     r13, TOK_LT
    je      .cmp_ok
    cmp     r13, TOK_LTE
    je      .cmp_ok
    cmp     r13, TOK_GT
    je      .cmp_ok
    cmp     r13, TOK_GTE
    je      .cmp_ok
    mov     rdx, em_expect_expr
    mov     rcx, em_expect_expr_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .done
.need_lhs:
    mov     rdx, em_expect_expr
    mov     rcx, em_expect_expr_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .done
.cmp_ok:
    call    tok_advance
    call    parse_expr_required
    ; peek type stack: if both TY_STR → string compare path
    mov     rax, [type_stkp]
    mov     rdx, [type_stk + rax*8 - 8]
    mov     rcx, [type_stk + rax*8 - 16]
    cmp     rdx, TY_STR
    jne     .int_cmp
    cmp     rcx, TY_STR
    jne     .int_cmp
    cmp     r13, TOK_EQEQ
    je      .str_eq_cmp
    cmp     r13, TOK_NEQ
    je      .str_neq_cmp
    mov     rdx, em_str_ord
    mov     rcx, em_str_ord_l
    call    emit_error_tok
    jmp     .int_cmp
.str_eq_cmp:
    call    ty_discard
    call    ty_discard
    call    ir_str_eq
    mov     rdi, r12
    mov     rsi, LBL_CF
    call    ir_jz
    jmp     .check_and_or
.str_neq_cmp:
    call    ty_discard
    call    ty_discard
    call    ir_str_neq
    mov     rdi, r12
    mov     rsi, LBL_CF
    call    ir_jz
    jmp     .check_and_or
.int_cmp:
    call    ty_check_cmp
    call    ir_pop_rbx
    ; IR_CMP: A=op_token, B=cf_label_id
    mov     rdi, r13
    mov     rsi, r12
    call    ir_cmp
.check_and_or:
    call    tok_cur_type
    cmp     rax, TOK_AND
    je      .do_and
    cmp     rax, TOK_OR
    je      .do_or
    ; emit true/false paths
    mov     rdi, 1
    call    ir_const
    mov     rdi, r14
    mov     rsi, LBL_CD
    call    ir_jmp
    mov     rdi, r12
    mov     rsi, LBL_CF
    call    ir_lbl
    mov     rdi, 0
    call    ir_const
    mov     rdi, r14
    mov     rsi, LBL_CD
    call    ir_lbl
    jmp     .done
.do_and:
    call    tok_advance
    jmp     .next
.do_or:
    ; Patch last IR_CMP/IR_JZ's target from _cf_N to a new or_skip_N label,
    ; so a passing clause short-circuits to true rather than falling through.
    mov     rax, [ir_cnt]
    dec     rax
    shl     rax, 5
    lea     rcx, [ir_buf+rax]           ; rcx = ptr to last IR record
    mov     rax, [label_ctr]            ; rax = or_skip_N label id
    inc     qword [label_ctr]
    cmp     qword [rcx+IR_F_OP], IR_CMP
    je      .dor_cmp
    mov     [rcx+IR_F_A], rax           ; IR_JZ: patch A (jump target)
    jmp     .dor_patched
.dor_cmp:
    mov     [rcx+IR_F_B], rax           ; IR_CMP: patch B (_cf_N → or_skip_N)
.dor_patched:
    push    rax                         ; save or_skip_N across IR calls
    ; Emit: CONST(1) — result if this clause was true
    mov     rdi, 1
    call    ir_const
    ; Emit: JMP(_cd_N, LBL_CD) — short-circuit to done
    mov     rdi, r14
    mov     rsi, LBL_CD
    call    ir_jmp
    ; Emit: LBL(or_skip_N, LBL_CF) — fall-through point for failing clause
    pop     rdi                         ; restore or_skip_N
    mov     rsi, LBL_CF
    call    ir_lbl
    call    tok_advance
    jmp     .next
.done:
    test    r15, r15
    jz      .cpc_ret
    IR0     IR_LNOT
.cpc_ret:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ─── parse_body ──────────────────────────────────────────────
parse_body:
    push    rbx
    xor     rbx, rbx                    ; rbx=1 if we consumed a '{' (unclosed-block flag)
    mov     rax, [blk_returned]
    push    rax                         ; save old blk_returned
    mov     qword [blk_returned], 0
    call    tok_cur_type
    cmp     rax, TOK_LBRACE
    jne     .body
    inc     qword [blk_dep]
    mov     rbx, 1
    call    tok_advance
.body:
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_RBRACE
    je      .done
    cmp     rax, TOK_EOF
    jne     .body_stmt
    test    rbx, rbx
    jz      .done
    mov     rdx, em_unclosed_block
    mov     rcx, em_unclosed_block_l
    call    emit_error_tok
    jmp     .done
.body_stmt:
    call    parse_stmt
    cmp     qword [blk_returned], 0
    je      .body
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_RBRACE
    je      .done
    cmp     rax, TOK_EOF
    jne     .body_after_ret
    test    rbx, rbx
    jz      .done
    mov     rdx, em_unclosed_block
    mov     rcx, em_unclosed_block_l
    call    emit_error_tok
    jmp     .done
.body_after_ret:
    cmp     qword [had_error], 0
    jne     .done
    mov     rdx, em_dead_code
    mov     rcx, em_dead_code_l
    call    emit_error_tok
    jmp     .done
.done:
    call    tok_cur_type
    cmp     rax, TOK_RBRACE
    jne     .ret
    dec     qword [blk_dep]
    call    tok_advance
.ret:
    pop     rax                         ; restore old blk_returned
    mov     [blk_returned], rax
    pop     rbx
    ret

parse_block_required:
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_LBRACE
    je      .ok
    mov     rdx, em_expect_block
    mov     rcx, em_expect_block_l
    call    emit_error_tok
    ret
.ok:
    call    parse_body
    ret

; ─── parse_if ────────────────────────────────────────────────
parse_if:
    push    r12
    push    r13
    push    r14
    sub     rsp, 16
    call    tok_advance
    mov     r13, [label_ctr]
    inc     qword [label_ctr]
    mov     [rsp], r13
    call    parse_condition
    mov     rdi, [rsp]
    mov     rsi, LBL_IE
    call    ir_jz
    call    tok_skip_nl
    call    parse_body
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_ELIF
    je      .do_elif
    cmp     rax, TOK_ELSE
    je      .do_else
    mov     rdi, [rsp]
    mov     rsi, LBL_IE
    call    ir_lbl
    jmp     .done
.do_elif:
    mov     r14, [label_ctr]
    inc     qword [label_ctr]
    mov     [rsp+8], r14
    mov     rdi, [rsp+8]
    mov     rsi, LBL_ID
    call    ir_jmp
    mov     rdi, [rsp]
    mov     rsi, LBL_IE
    call    ir_lbl
    call    parse_if
    mov     rdi, [rsp+8]
    mov     rsi, LBL_ID
    call    ir_lbl
    jmp     .done
.do_else:
    mov     r14, [label_ctr]
    inc     qword [label_ctr]
    mov     [rsp+8], r14
    mov     rdi, [rsp+8]
    mov     rsi, LBL_ID
    call    ir_jmp
    mov     rdi, [rsp]
    mov     rsi, LBL_IE
    call    ir_lbl
    call    tok_advance
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_IF
    je      .do_else_if
    call    parse_body
    mov     rdi, [rsp+8]
    mov     rsi, LBL_ID
    call    ir_lbl
    jmp     .done
.do_else_if:
    call    parse_if
    mov     rdi, [rsp+8]
    mov     rsi, LBL_ID
    call    ir_lbl
.done:
    add     rsp, 16
    pop     r14
    pop     r13
    pop     r12
    ret

; ─── parse_while ─────────────────────────────────────────────
parse_while:
    push    r12
    push    r13
    call    tok_advance
    cmp     qword [lp_dep], MAX_LOOP
    jl      .depth_ok
    mov     rdx, em_loop_ovf
    mov     rcx, em_loop_ovf_l
    call    emit_error_tok
    pop     r13
    pop     r12
    ret
.depth_ok:
    mov     r13, [label_ctr]
    inc     qword [label_ctr]
    mov     rax, [lp_dep]
    mov     [lp_ws_stk+rax*8], r13
    mov     [lp_we_stk+rax*8], r13
    mov     qword [lp_isfor+rax*8], 0
    inc     qword [lp_dep]
    mov     rdi, r13
    mov     rsi, LBL_WS
    call    ir_lbl
    call    parse_condition
    mov     rdi, r13
    mov     rsi, LBL_WE
    call    ir_jz
    call    tok_skip_nl
    call    parse_body
    mov     rdi, r13
    mov     rsi, LBL_WS
    call    ir_jmp
    mov     rdi, r13
    mov     rsi, LBL_WE
    call    ir_lbl
    dec     qword [lp_dep]
    pop     r13
    pop     r12
    ret

; ─── parse_for ───────────────────────────────────────────────
parse_for:
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 40         ; [rsp+0]=label_id  [rsp+8]=__a_slot  [rsp+16]=__i_slot  [rsp+24]=global_flag  [rsp+32]=elem_type
    call    tok_advance
    cmp     qword [lp_dep], MAX_LOOP
    jl      .depth_ok
    mov     rdx, em_loop_ovf
    mov     rcx, em_loop_ovf_l
    call    emit_error_tok
    jmp     .done
.depth_ok:
    call    tok_cur_ptr
    mov     r12, rax
    call    tok_cur_len
    mov     r13, rax
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_IN
    je      .ok_in
    mov     rdx, em_expect_in
    mov     rcx, em_expect_in_l
    call    emit_error_tok
    jmp     .done
.ok_in:
    call    tok_advance
    call    parse_expr_required ; start value / array expression
    ; decide: range-for (has ..) or for-each (array)
    call    tok_cur_type
    cmp     rax, TOK_DOTDOT
    jne     .foreach
    ; ── range-for ──
    call    ty_pop
    cmp     rax, TY_INT
    je      .range_start_type_ok
    test    rax, rax
    jz      .range_start_type_ok
    mov     rdx, em_for_range_type
    mov     rcx, em_for_range_type_l
    call    emit_error_tok
.range_start_type_ok:
    mov     rdi, TY_INT
    call    ty_push
    ; store start to loop var x
    mov     rbx, r12
    push    r12
    push    r13
    mov     r12, r13
    call    ir_store
    pop     r13
    pop     r12
.ok_dd:
    call    tok_advance
    call    parse_expr_required ; end value
    call    ty_pop
    cmp     rax, TY_INT
    je      .range_end_type_ok
    test    rax, rax
    jz      .range_end_type_ok
    mov     rdx, em_for_range_type
    mov     rcx, em_for_range_type_l
    call    emit_error_tok
.range_end_type_ok:
    mov     rdi, TY_INT
    call    ty_push
    ; store to _fe[for_dep]
    mov     r15, [for_dep]
    mov     rax, r15
    imul    rdi, rax, 8
    call    ir_fe_st            ; mov [_fe+depth*8], rax
    call    ty_discard
    ; claim label
    mov     r14, [label_ctr]
    inc     qword [label_ctr]
    mov     [rsp], r14
    ; push loop stack
    mov     rax, [lp_dep]
    mov     rdi, [rsp]
    mov     [lp_ws_stk+rax*8], rdi
    mov     [lp_we_stk+rax*8], rdi
    mov     qword [lp_isfor+rax*8], 1
    inc     qword [lp_dep]
    inc     qword [for_dep]
    ; _ws_N:
    mov     rdi, [rsp]
    mov     rsi, LBL_WS
    call    ir_lbl
    ; load loop var → rax
    mov     rbx, r12
    push    r12
    mov     r12, r13
    call    ir_load
    pop     r12
    call    ty_discard
    ; cmp rax, [_fe+depth*8]
    mov     rax, r15
    imul    rdi, rax, 8
    call    ir_fe_cmp
    ; jge _we_N
    mov     rdi, [rsp]
    mov     rsi, LBL_WE
    call    ir_jge
    ; body
    call    tok_skip_nl
    call    parse_body
    ; _wc_N:
    mov     rdi, [rsp]
    mov     rsi, LBL_WC
    call    ir_lbl
    ; increment loop var
    mov     rbx, r12
    push    r12
    mov     r12, r13
    call    ir_load
    call    ir_inc_rax
    call    ir_store
    pop     r12
    ; jmp _ws_N
    mov     rdi, [rsp]
    mov     rsi, LBL_WS
    call    ir_jmp
    ; _we_N:
    mov     rdi, [rsp]
    mov     rsi, LBL_WE
    call    ir_lbl
    dec     qword [lp_dep]
    dec     qword [for_dep]
    jmp     .done

; ── for-each over array: for x in <array_expr> { } ──
; At entry: array expr result in rax at runtime, type on type stack.
; r12 = loop-var name ptr, r13 = loop-var name len.
.foreach:
    ; peek element type before discarding: TY_STR_ARR → elem is TY_STR, else TY_INT
    mov     rax, [type_stkp]
    mov     qword [rsp+32], TY_INT
    cmp     qword [type_stk+rax*8-8], TY_STR_ARR
    je      .fe_str
    cmp     qword [type_stk+rax*8-8], TY_ARR
    je      .fe_not_str
    cmp     qword [type_stk+rax*8-8], TY_UNK
    je      .fe_not_str
    mov     rdx, em_for_each_type
    mov     rcx, em_for_each_type_l
    call    emit_error_tok
    jmp     .fe_not_str
.fe_str:
    mov     qword [rsp+32], TY_STR
.fe_not_str:
    call    ty_discard          ; discard array-expr type

    ; ── set global_flag: 1 = global scope, 0 = function scope ──
    xor     rax, rax
    cmp     qword [in_fn], 1
    je      .fe_scope_set
    inc     rax                 ; in_fn==0 → global scope
.fe_scope_set:
    mov     [rsp+24], rax

    ; ── build hidden names in fe_names_buf ──
    ; Each depth d uses fe_names_buf[d*6 .. d*6+5]:
    ;   [0..2] = 0x01 'a' for_dep_byte  (holds array pointer)
    ;   [3..5] = 0x01 'i' for_dep_byte  (holds integer counter)
    ; Separate slots prevent hash-probe aliasing across nested loops.
    mov     rax, [for_dep]
    mov     rcx, rax            ; rcx = for_dep byte
    imul    rax, rax, 6
    lea     rbx, [fe_names_buf]
    add     rbx, rax            ; rbx = &fe_names_buf[for_dep * 6]
    mov     byte [rbx],   0x01
    mov     byte [rbx+1], 0x61  ; 'a'
    mov     [rbx+2], cl
    mov     byte [rbx+3], 0x01
    mov     byte [rbx+4], 0x69  ; 'i'
    mov     [rbx+5], cl

    ; ── insert __a hidden var (array ptr) ──
    mov     rsi, rbx
    mov     rcx, 3
    cmp     qword [rsp+24], 0
    jne     .ins_a_g
    call    lsym_insert             ; local: rax = count*8 (pre-multiplied)
    inc     qword [lvar_reads+rax*8]
    jmp     .ins_a_done
.ins_a_g:
    call    sym_insert              ; global: rax = 0-based count
    inc     qword [gvar_reads+rax*8]
    imul    rax, rax, 8             ; pre-multiply for ir_store_g/ir_load_g
.ins_a_done:
    mov     [rsp+8], rax            ; save __a_slot
    ; store array ptr (in rax at runtime) to __a
    mov     rdi, [rsp+8]
    call    .fe_store
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard

    ; ── LOAD __a → ARR_LEN → FE_ST ──
    mov     rdi, [rsp+8]
    call    .fe_load
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard
    call    ir_arr_len          ; rax = len at runtime
    mov     r15, [for_dep]      ; r15 = depth (before increment)
    imul    rdi, r15, 8
    call    ir_fe_st            ; _fe[depth*8] = len
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard

    ; ── insert __i hidden var (counter) ──
    mov     rax, [for_dep]
    imul    rax, rax, 6
    lea     rsi, [fe_names_buf + rax + 3]
    mov     rcx, 3
    cmp     qword [rsp+24], 0
    jne     .ins_i_g
    call    lsym_insert
    inc     qword [lvar_reads+rax*8]
    jmp     .ins_i_done
.ins_i_g:
    call    sym_insert
    inc     qword [gvar_reads+rax*8]
    imul    rax, rax, 8
.ins_i_done:
    mov     [rsp+16], rax
    ; init counter = 0
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_INT
    call    ty_push
    mov     rdi, [rsp+16]
    call    .fe_store
    call    ty_discard

    ; ── claim label and push loop stack ──
    mov     r14, [label_ctr]
    inc     qword [label_ctr]
    mov     [rsp], r14
    mov     rax, [lp_dep]
    mov     rdi, r14
    mov     [lp_ws_stk+rax*8], rdi
    mov     [lp_we_stk+rax*8], rdi
    mov     qword [lp_isfor+rax*8], 1
    inc     qword [lp_dep]
    inc     qword [for_dep]

    ; ── _ws_N: ──
    mov     rdi, [rsp]
    mov     rsi, LBL_WS
    call    ir_lbl

    ; ── load __i → FE_CMP → JGE _we_N ──
    mov     rdi, [rsp+16]
    call    .fe_load
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard
    imul    rdi, r15, 8     ; r15 = depth (set before inc)
    call    ir_fe_cmp
    mov     rdi, [rsp]
    mov     rsi, LBL_WE
    call    ir_jge

    ; ── load arr[__i] → store to loop var x ──
    ; a. array ptr from __a
    mov     rdi, [rsp+8]
    call    .fe_load
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard
    call    ir_push         ; push array ptr to runtime stack
    ; b. counter from __i
    mov     rdi, [rsp+16]
    call    .fe_load
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard
    ; c. byte offset and bounds-checked load
    call    ir_imul8
    call    ir_arr_ld
    mov     rdi, [rsp+32]   ; element type: TY_STR for string arrays, TY_INT otherwise
    call    ty_push
    ; d. store element to loop var x (ir_store handles local vs global)
    mov     rbx, r12
    push    r12
    mov     r12, r13
    call    ir_store
    pop     r12

    ; ── body ──
    call    tok_skip_nl
    call    parse_body

    ; ── _wc_N: increment __i → JMP _ws_N ──
    mov     rdi, [rsp]
    mov     rsi, LBL_WC
    call    ir_lbl
    mov     rdi, [rsp+16]
    call    .fe_load
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard
    call    ir_inc_rax
    mov     rdi, [rsp+16]
    call    .fe_store
    mov     rdi, TY_INT
    call    ty_push
    call    ty_discard
    mov     rdi, [rsp]
    mov     rsi, LBL_WS
    call    ir_jmp

    ; ── _we_N: ──
    mov     rdi, [rsp]
    mov     rsi, LBL_WE
    call    ir_lbl

.done_foreach:
    dec     qword [lp_dep]
    dec     qword [for_dep]
.done:
    add     rsp, 40
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ── for-each scope helpers: dispatch store/load based on global_flag ──
; When called, return address is at [rsp], so global_flag is at [rsp+32].
.fe_store:
    cmp     qword [rsp+32], 0
    jne     .fes_g
    call    ir_store_l
    ret
.fes_g:
    call    ir_store_g
    ret
.fe_load:
    cmp     qword [rsp+32], 0
    jne     .fel_g
    call    ir_load_l
    ret
.fel_g:
    call    ir_load_g
    ret

; ─── parse_break ─────────────────────────────────────────────
parse_break:
    call    tok_advance
    cmp     qword [lp_dep], 0
    je      .nl
    mov     rax, [lp_dep]
    dec     rax
    mov     rdi, [lp_we_stk+rax*8]
    mov     rsi, LBL_WE
    call    ir_jmp
    ret
.nl:
    mov     rdx, em_noloop
    mov     rcx, em_noloop_l
    call    emit_error_tok
    ret

; ─── parse_continue ──────────────────────────────────────────
parse_continue:
    call    tok_advance
    cmp     qword [lp_dep], 0
    je      .d
    mov     rax, [lp_dep]
    dec     rax
    mov     rdi, [lp_ws_stk+rax*8]
    mov     rsi, LBL_WS
    cmp     qword [lp_isfor+rax*8], 1
    jne     .emit
    mov     rsi, LBL_WC
.emit:
    call    ir_jmp
.d:
    cmp     qword [lp_dep], 0
    jne     .ret
    mov     rdx, em_noloop
    mov     rcx, em_noloop_l
    call    emit_error_tok
.ret:
    ret

; ─── parse_func ──────────────────────────────────────────────
parse_func:
    push    r12
    push    r13
    push    rbx
    cmp     qword [blk_dep], 0
    je      .top_ok
    cmp     qword [mod_len], 0
    je      .bad_scope
    cmp     qword [blk_dep], 1
    je      .top_ok
.bad_scope:
    mov     rdx, em_decl_top
    mov     rcx, em_decl_top_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     rbx
    pop     r13
    pop     r12
    ret
.top_ok:
    cmp     qword [decl_phase], 1
    je      .order_ok
    cmp     qword [decl_phase], 2
    je      .order_ok
    mov     rdx, em_decl_order
    mov     rcx, em_decl_order_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     rbx
    pop     r13
    pop     r12
    ret
.order_ok:
    cmp     qword [in_fn], 1
    jne     .fn_scope_ok
    mov     rdx, em_decl_in_fn
    mov     rcx, em_decl_in_fn_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     rbx
    pop     r13
    pop     r12
    ret
.fn_scope_ok:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_IDENT
    je      .have_name
    mov     rdx, em_expect_fn_name
    mov     rcx, em_expect_fn_name_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     rbx
    pop     r13
    pop     r12
    ret
.have_name:
    call    tok_cur_ptr
    mov     r12, rax
    call    tok_cur_len
    mov     r13, rax
    push    rsi
    push    rcx
    mov     rsi, r12
    mov     rcx, r13
    call    sym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    je      .global_name_ok
    mov     rdx, em_name_conflict
    mov     rcx, em_name_conflict_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     rbx
    pop     r13
    pop     r12
    ret
.global_name_ok:
    mov     rdi, r12
    mov     rsi, r13
    call    fn_find
    cmp     rax, -1
    je      .name_ok
    mov     rdx, em_fn_dup
    mov     rcx, em_fn_dup_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     rbx
    pop     r13
    pop     r12
    ret
.name_ok:
    call    tok_advance
    ; emit IR_FN_BGN
    mov     rdi, r12
    mov     rsi, r13
    call    ir_fn_begin
    ; set function state
    mov     qword [in_fn], 1
    mov     qword [fn_pcur], 0
    mov     qword [fn_ret_type], 0
    push    rdi
    push    rcx
    lea     rdi, [lht_key]
    xor     rax, rax
    mov     rcx, HT_SZ*3
    rep stosq
    mov     qword [lht_cnt], 0
    lea     rdi, [lvar_reads]
    mov     rcx, LVAR_ARR_SZ*3
    rep stosq
    lea     rdi, [lvar_types]
    mov     rcx, LVAR_ARR_SZ
    rep stosq
    lea     rdi, [lvar_names]
    mov     rcx, LVAR_NM_ENT*9
    rep stosq
    lea     rdi, [fn_param_types]
    xor     rax, rax
    mov     rcx, MAX_PARAMS
    rep stosq
    pop     rcx
    pop     rdi
    ; parse params
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    je      .have_lparen
    mov     rdx, em_expect_call_lparen
    mov     rcx, em_expect_call_lparen_l
    call    emit_error_tok
    jmp     .abort
.have_lparen:
    call    tok_advance
    xor     rbx, rbx
.pp:
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    je      .pd
    cmp     rax, TOK_EOF
    je      .pd
    cmp     rax, TOK_IDENT
    je      .param_type_ok
    mov     rdx, em_expect_param_name
    mov     rcx, em_expect_param_name_l
    call    emit_error_tok
    jmp     .abort
.param_type_ok:
    cmp     rbx, MAX_PARAMS
    jl      .param_ok
    mov     rdx, em_param_ovf
    mov     rcx, em_param_ovf_l
    call    emit_error_tok
    jmp     .abort
.param_ok:
    call    tok_cur_ptr
    push    rax
    call    tok_cur_len
    push    rax
    mov     rdi, [rsp+8]
    mov     rsi, [rsp]
    call    fn_param_find
    cmp     rax, -1
    je      .param_store
    mov     rdx, em_param_dup
    mov     rcx, em_param_dup_l
    call    emit_error_tok
    pop     rax
    pop     rax
    jmp     .abort
.param_store:
    mov     rax, rbx
    imul    rax, rax, VAR_NL
    lea     rdi, [fn_pnames+rax]
    pop     rcx
    pop     rsi
    push    rsi
    push    rcx
    rep movsb
    mov     byte [rdi], 0
    pop     rcx
    pop     rsi
    mov     [fn_plens+rbx*8], rcx
    inc     rbx
    mov     [fn_pcur], rbx          ; keep fn_pcur live for duplicate detection
    call    tok_advance
    ; optional type annotation: 'str' or 'int' after parameter name
    call    tok_cur_type
    cmp     rax, TOK_STRTYPE
    je      .param_ann_str
    cmp     rax, TOK_INTTYPE
    je      .param_ann_int
    jmp     .param_ann_done
.param_ann_str:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_LBRACKET
    jne     .param_ann_str_scalar
    call    tok_advance         ; eat [
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .param_ann_str_scalar
    call    tok_advance         ; eat ]
    lea     rax, [rbx-1]
    mov     qword [fn_param_types+rax*8], TY_STR_ARR
    jmp     .param_ann_done
.param_ann_str_scalar:
    lea     rax, [rbx-1]
    mov     qword [fn_param_types+rax*8], TY_STR
    jmp     .param_ann_done
.param_ann_int:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_LBRACKET
    jne     .param_ann_int_scalar
    call    tok_advance         ; eat [
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .param_ann_int_scalar
    call    tok_advance         ; eat ]
    lea     rax, [rbx-1]
    mov     qword [fn_param_types+rax*8], TY_ARR
    jmp     .param_ann_done
.param_ann_int_scalar:
    lea     rax, [rbx-1]
    mov     qword [fn_param_types+rax*8], TY_INT
.param_ann_done:
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    je      .psk
    cmp     rax, TOK_RPAREN
    je      .pd
    cmp     rax, TOK_EOF
    je      .pd
    mov     rdx, em_expect_param_sep
    mov     rcx, em_expect_param_sep_l
    call    emit_error_tok
    jmp     .abort
.psk:
    call    tok_advance
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    je      .need_param
    cmp     rax, TOK_EOF
    je      .need_param
    cmp     rax, TOK_COMMA
    je      .need_param
    jmp     .pp
.need_param:
    mov     rdx, em_expect_param_sep
    mov     rcx, em_expect_param_sep_l
    call    emit_error_tok
    jmp     .abort
.pd:
    mov     [fn_pcur], rbx
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .nop
    call    tok_advance
.nop:
    mov     rdi, r12
    mov     rsi, r13
    mov     rdx, [fn_pcur]
    call    fn_register
    call    parse_block_required
    cmp     qword [had_error], 0
    jne     .skip_unused_loc
    push    r14
    push    r15
    mov     r15, 1
.ul_chk:
    cmp     r15, [lht_cnt]
    jg      .ul_done
    imul    r14, r15, 8
    cmp     qword [lvar_reads+r14*8], 0
    jne     .ul_nx
    lea     rdx, [lvar_names+r14*8]
    mov     rcx, [lvar_names_l+r14]
    mov     rdi, [lvar_decl_line+r14*8]
    mov     rsi, [lvar_decl_col+r14*8]
    call    emit_unused_var_err
.ul_nx:
    inc     r15
    jmp     .ul_chk
.ul_done:
    pop     r15
    pop     r14
.skip_unused_loc:
    call    ir_fn_end
    mov     rax, [fn_cnt]
    dec     rax
    mov     rdx, [fn_ret_type]
    mov     [fn_ret_types+rax*8], rdx
    mov     qword [in_fn], 0
    pop     rbx
    pop     r13
    pop     r12
    ret
.abort:
    mov     qword [in_fn], 0
    pop     rbx
    pop     r13
    pop     r12
    ret

; ─── parse_return ────────────────────────────────────────────
parse_return:
    cmp     qword [in_fn], 1
    je      .in_fn
    mov     rdx, em_ret_out
    mov     rcx, em_ret_out_l
    call    emit_error_tok
    call    tok_advance
    ret
.in_fn:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .nv
    cmp     rax, TOK_RBRACE
    je      .nv
    cmp     rax, TOK_EOF
    je      .nv
    cmp     rax, TOK_COMMA
    je      .badv
    cmp     rax, TOK_RPAREN
    je      .badv
    cmp     rax, TOK_LBRACE
    je      .badv
    cmp     rax, TOK_DOTDOT
    je      .badv
    call    parse_expr
    call    ty_check_ret
    jmp     .emit
.nv:
    mov     rdi, 0
    call    ir_const
    jmp     .emit
.badv:
    mov     rdx, em_expect_expr
    mov     rcx, em_expect_expr_l
    call    emit_error_tok
    call    tok_advance
    mov     rdi, 0
    call    ir_const
.emit:
    call    ir_ret
    mov     qword [blk_returned], 1
    ret

; ─── parse_try ───────────────────────────────────────────────
parse_try:
    push    r12
    push    r13
    call    tok_advance
    cmp     qword [try_dep], MAX_TRY
    jl      .depth_ok
    mov     rdx, em_try_ovf
    mov     rcx, em_try_ovf_l
    call    emit_error_tok
    pop     r13
    pop     r12
    ret
.depth_ok:
    mov     r12, [label_ctr]
    inc     qword [label_ctr]
    mov     r13, [label_ctr]
    inc     qword [label_ctr]
    mov     rax, [try_dep]
    mov     [try_tc+rax*8], r12
    inc     qword [try_dep]
    call    ir_clr_ef
    call    parse_block_required
    mov     rdi, r13
    mov     rsi, LBL_TE
    call    ir_jmp
    mov     rdi, r12
    mov     rsi, LBL_TC
    call    ir_lbl
    dec     qword [try_dep]
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_CATCH
    jne     .need_catch
    call    tok_advance
    call    parse_block_required
.nc:
    mov     rdi, r13
    mov     rsi, LBL_TE
    call    ir_lbl
    pop     r13
    pop     r12
    ret
.need_catch:
    mov     rdx, em_need_catch
    mov     rcx, em_need_catch_l
    call    emit_error_tok
    jmp     .nc

; ─── parse_error_stmt ────────────────────────────────────────
parse_error_stmt:
    cmp     qword [try_dep], 0
    jne     .in_try
    call    tok_advance
    mov     rdx, em_error_out
    mov     rcx, em_error_out_l
    call    emit_error_tok
    ret
.in_try:
    call    tok_advance
    call    ir_set_ef
    call    tok_cur_type
    cmp     rax, TOK_STRING
    je      .with_str
    cmp     rax, TOK_NEWLINE
    je      .nm
    cmp     rax, TOK_RBRACE
    je      .nm
    cmp     rax, TOK_EOF
    je      .nm
    mov     rdx, em_error_str
    mov     rcx, em_error_str_l
    call    emit_error_tok
    call    tok_advance
    jmp     .nt
.with_str:
    call    str_record
    mov     rdi, rax
    call    ir_print_str
    call    tok_advance
.nm:
    cmp     qword [try_dep], 0
    je      .nt
    mov     rax, [try_dep]
    dec     rax
    mov     rdi, [try_tc+rax*8]
    call    ir_jmp_tc
.nt:
    ret

; ─── parse_module ────────────────────────────────────────────
parse_module:
    push    r12
    push    r13
    cmp     qword [blk_dep], 0
    je      .mod_top_ok
    mov     rdx, em_decl_top
    mov     rcx, em_decl_top_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     r13
    pop     r12
    ret
.mod_top_ok:
    cmp     qword [decl_phase], 2
    je      .mod_order_ok
    mov     rdx, em_decl_order
    mov     rcx, em_decl_order_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     r13
    pop     r12
    ret
.mod_order_ok:
    cmp     qword [in_fn], 1
    jne     .mod_scope_ok
    mov     rdx, em_decl_in_fn
    mov     rcx, em_decl_in_fn_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     r13
    pop     r12
    ret
.mod_scope_ok:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_IDENT
    je      .have_name
    mov     rdx, em_expect_mod_name
    mov     rcx, em_expect_mod_name_l
    call    emit_error_tok
    pop     r13
    pop     r12
    ret
.have_name:
    call    tok_cur_ptr
    mov     r12, rax
    call    tok_cur_len
    mov     r13, rax
    mov     rdi, r12
    mov     rsi, r13
    call    mod_find
    cmp     rax, -1
    je      .mod_name_unique
    mov     rdx, em_mod_dup
    mov     rcx, em_mod_dup_l
    call    emit_error_tok
    call    skip_decl_stmt
    pop     r13
    pop     r12
    ret
.mod_name_unique:
    call    tok_advance
    mov     rdi, r12
    mov     rsi, r13
    push    rdi
    push    rsi
    call    mod_register
    pop     rsi
    pop     rdi
    call    ir_mod_begin
    push    rdi
    push    rcx
    lea     rdi, [mod_name]
    mov     rsi, r12
    mov     rcx, r13
    rep movsb
    mov     byte [rdi], 0
    pop     rcx
    pop     rdi
    mov     [mod_len], r13
    call    tok_cur_type
    cmp     rax, TOK_LBRACE
    je      .mod_block_ok
    cmp     rax, TOK_NEWLINE
    je      .mod_block_ok
    mov     rdx, em_expect_mod_block
    mov     rcx, em_expect_mod_block_l
    call    emit_error_tok
    mov     qword [mod_len], 0
    pop     r13
    pop     r12
    ret
.mod_block_ok:
    call    parse_block_required
    call    ir_mod_end
    mov     qword [mod_len], 0
    pop     r13
    pop     r12
    ret

; ─── parse_import ────────────────────────────────────────────
parse_import:
    cmp     qword [blk_dep], 0
    je      .import_top_ok
    mov     rdx, em_decl_top
    mov     rcx, em_decl_top_l
    call    emit_error_tok
    call    skip_decl_stmt
    ret
.import_top_ok:
    cmp     qword [decl_phase], 2
    je      .import_order_ok
    mov     rdx, em_decl_order
    mov     rcx, em_decl_order_l
    call    emit_error_tok
    call    skip_decl_stmt
    ret
.import_order_ok:
    cmp     qword [in_fn], 1
    jne     .import_scope_ok
    mov     rdx, em_decl_in_fn
    mov     rcx, em_decl_in_fn_l
    call    emit_error_tok
    call    skip_decl_stmt
    ret
.import_scope_ok:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_IDENT
    je      .ok
    mov     rdx, em_expect_import_name
    mov     rcx, em_expect_import_name_l
    call    emit_error_tok
    ret
.ok:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_NEWLINE
    je      .d
    cmp     rax, TOK_EOF
    je      .d
    cmp     rax, TOK_RBRACE
    je      .d
    mov     rdx, em_expect_import_end
    mov     rcx, em_expect_import_end_l
    call    emit_error_tok
.d: ret

; ─── parse_expr ──────────────────────────────────────────────
parse_expr:
    call    parse_term
.lp:
    call    tok_cur_type
    cmp     rax, TOK_PLUS
    je      .add
    cmp     rax, TOK_MINUS
    je      .sub
    cmp     rax, TOK_AMP
    je      .band
    cmp     rax, TOK_CARET
    je      .bxor
    cmp     rax, TOK_PIPE
    je      .bor
    ret
.add:
    ; Peek type stack top: if TY_STR → string concat, else int add
    mov     rax, [type_stkp]
    test    rax, rax
    jz      .add_int
    cmp     qword [type_stk + rax*8 - 8], TY_STR
    je      .add_str
.add_int:
    call    tok_advance
    call    ir_push
    call    parse_term
    call    ir_pop_rbx
    call    ir_add
    call    ty_check_arith
    jmp     .lp
.add_str:
    call    tok_advance
    call    ir_push
    call    parse_term
    call    ir_pop_rbx
    inc     qword [str_cat_cnt]
    call    ir_str_concat
    call    ty_check_str_concat
    jmp     .lp
.sub:
    call    tok_advance
    call    ir_push
    call    parse_term
    call    ir_pop_rbx
    call    ir_sub
    call    ty_check_arith
    jmp     .lp
.band:
    call    tok_advance
    call    ir_push
    call    parse_term
    call    ir_pop_rbx
    call    ir_band
    call    ty_check_arith
    jmp     .lp
.bxor:
    call    tok_advance
    call    ir_push
    call    parse_term
    call    ir_pop_rbx
    call    ir_bxor
    call    ty_check_arith
    jmp     .lp
.bor:
    call    tok_advance
    call    ir_push
    call    parse_term
    call    ir_pop_rbx
    call    ir_bor
    call    ty_check_arith
    jmp     .lp

; ─── parse_term ──────────────────────────────────────────────
parse_term:
    call    parse_factor
.lp:
    call    tok_cur_type
    cmp     rax, TOK_STAR
    je      .mul
    cmp     rax, TOK_SLASH
    je      .div
    cmp     rax, TOK_PERCENT
    je      .mod
    cmp     rax, TOK_LSHIFT
    je      .shl
    cmp     rax, TOK_RSHIFT
    je      .shr
    ret
.mul:
    call    tok_advance
    call    ir_push
    call    parse_factor
    call    ir_pop_rbx
    call    ir_mul
    call    ty_check_arith
    jmp     .lp
.div:
    call    tok_advance
    call    ir_push
    call    parse_factor
    call    ir_div
    call    ty_check_arith
    jmp     .lp
.mod:
    call    tok_advance
    call    ir_push
    call    parse_factor
    call    ir_mod
    call    ty_check_arith
    jmp     .lp
.shl:
    call    tok_advance
    call    ir_push
    call    parse_factor
    call    ir_shl
    call    ty_check_arith
    jmp     .lp
.shr:
    call    tok_advance
    call    ir_push
    call    parse_factor
    call    ir_shr
    call    ty_check_arith
    jmp     .lp

; ─── parse_factor ────────────────────────────────────────────
parse_factor:
    push    r12
    push    r13
    push    r14
    push    rbx
    call    tok_cur_type
    cmp     rax, TOK_INT
    je      .int
    cmp     rax, TOK_STRING
    je      .str
    cmp     rax, TOK_LPAREN
    je      .paren
    cmp     rax, TOK_IDENT
    je      .ident
    cmp     rax, TOK_ARGC
    je      .argc_builtin
    cmp     rax, TOK_ARG
    je      .arg_builtin
    cmp     rax, TOK_ARG_STR
    je      .arg_str_builtin
    cmp     rax, TOK_EXIT
    je      .exit_builtin
    cmp     rax, TOK_FIND
    je      .find_builtin
    cmp     rax, TOK_SLICE
    je      .slice_builtin
    cmp     rax, TOK_NOT
    je      .lnot
    cmp     rax, TOK_TRUE
    je      .true_lit
    cmp     rax, TOK_FALSE
    je      .false_lit
    cmp     rax, TOK_TILDE
    je      .bnot
    cmp     rax, TOK_LEN
    je      .len_builtin
    cmp     rax, TOK_ABS
    je      .abs_builtin
    cmp     rax, TOK_FMIN
    je      .min_builtin
    cmp     rax, TOK_FMAX
    je      .max_builtin
    cmp     rax, TOK_INPUT_INT
    je      .input_int_builtin
    cmp     rax, TOK_INPUT_STR
    je      .input_str_builtin
    cmp     rax, TOK_READ_FILE
    je      .read_file_builtin
    cmp     rax, TOK_WRITE_FILE
    je      .write_file_builtin
    cmp     rax, TOK_APPEND_FILE
    je      .append_file_builtin
    cmp     rax, TOK_STRTYPE
    je      .str_builtin
    cmp     rax, TOK_INTTYPE
    je      .int_builtin
    cmp     rax, TOK_PUSH
    je      .push_builtin
    cmp     rax, TOK_POP
    je      .pop_builtin
    cmp     rax, TOK_MINUS
    je      .neg
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done
.neg:
    ; unary minus: emit CONST(0) PUSH, parse inner factor, POP_RBX SUB
    ; so that -x → 0-x, and a--b correctly computes a-(-b)=a+b
    call    tok_advance         ; eat '-'
    mov     rdi, 0
    call    ir_const            ; CONST(0)
    call    ir_push             ; PUSH (save 0 for subtraction)
    call    parse_factor        ; inner factor → rax at runtime, type pushed
    call    ty_check_int_unary
    call    ir_pop_rbx          ; POP_RBX (rbx = 0)
    call    ir_sub              ; rax = 0 - rax = -rax
    jmp     .done
.int:
    call    tok_cur_ptr
    mov     rbx, rax
    call    tok_cur_len
    mov     r12, rax
    cmp     r12, 2
    jle     .int_decimal
    cmp     byte [rbx], '0'
    jne     .int_decimal
    cmp     byte [rbx+1], 'x'
    je      .int_hex
    cmp     byte [rbx+1], 'X'
    je      .int_hex
    cmp     byte [rbx+1], 'b'
    je      .int_bin
    cmp     byte [rbx+1], 'B'
    je      .int_bin
.int_decimal:
    ; check digit count, ignoring separators: > 19 digits always overflows INT64_MAX
    mov     rsi, rbx
    mov     rcx, r12
    call    num_digit_count
    cmp     rax, 19
    jg      .int_ovf
    ; parse value first (still at this token for error reporting)
    mov     rsi, rbx
    mov     rcx, r12
    call    str_to_int
    ; negative sign bit means wrap-around past INT64_MAX
    test    rax, rax
    js      .int_ovf
    jmp     .int_emit
.int_hex:
    mov     rcx, r12
    sub     rcx, 2
    lea     rsi, [rbx+2]
    call    num_digit_count
    ; 0x + more than 16 nybbles cannot fit in signed int64.
    cmp     rax, 16
    jg      .int_ovf
    mov     rcx, r12
    sub     rcx, 2
    lea     rsi, [rbx+2]
    call    str_to_hex_int
    ; Nolqu integers are signed int64, so the high bit is overflow.
    test    rax, rax
    js      .int_ovf
    jmp     .int_emit
.int_bin:
    mov     rcx, r12
    sub     rcx, 2
    lea     rsi, [rbx+2]
    call    num_digit_count
    ; 0b + more than 64 bits cannot fit in signed int64.
    cmp     rax, 64
    jg      .int_ovf
    mov     rcx, r12
    sub     rcx, 2
    lea     rsi, [rbx+2]
    call    str_to_bin_int
    ; Nolqu integers are signed int64, so the high bit is overflow.
    test    rax, rax
    js      .int_ovf
.int_emit:
    mov     r13, rax            ; save parsed value
    call    tok_advance
    mov     rdi, r13
    call    ir_const
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done
.int_ovf:
    mov     rdx, em_int_overflow
    mov     rcx, em_int_overflow_l
    call    emit_error_tok
    call    tok_advance
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done
.str:
    call    str_record
    mov     rdi, rax
    call    ir_const
    call    tok_advance
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done
.paren:
    call    tok_advance
    call    parse_expr
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .paren_missing_rparen
    call    tok_advance
    jmp     .done
.paren_missing_rparen:
    mov     rdx, em_expect_rparen
    mov     rcx, em_expect_rparen_l
    call    emit_error_tok
    jmp     .done
.ident:
    call    tok_cur_ptr
    mov     rbx, rax
    call    tok_cur_len
    mov     r12, rax
    mov     rdi, 1
    call    tok_peek
    cmp     rax, TOK_LPAREN
    je      .fn_call
    cmp     rax, TOK_DOT
    je      .mod_call
    cmp     rax, TOK_LBRACKET
    je      .arr_acc
    call    tok_advance
    call    ir_load
    jmp     .done
.fn_call:
    call    tok_advance
    mov     rdi, rbx
    mov     rsi, r12
    call    fn_find
    push    rax
    push    rbx
    push    r12
    call    parse_call_args
    mov     r14, rax
    pop     r12
    pop     rbx
    pop     r13
    cmp     qword [had_error], 0
    je      .fn_after_args
    mov     rdi, 0
    call    ir_const
    jmp     .fn_nc
.fn_after_args:
    cmp     r13, -1
    jne     .fn_chk_arity
    mov     rdx, em_fn_undef
    mov     rcx, em_fn_undef_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .fn_nc
.fn_chk_arity:
    mov     rax, [fn_pcnt+r13*8]
    cmp     rax, r14
    je      .fn_emit
    mov     rdx, em_fn_arity
    mov     rcx, em_fn_arity_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .fn_nc
.fn_emit:
    mov     rdi, rbx
    mov     rsi, r12
    call    ir_call
    mov     rax, [fn_pcnt+r13*8]
    test    rax, rax
    jz      .fn_nc
    imul    rdi, rax, 8
    call    ir_add_rsp
.fn_nc:
    cmp     r13, -1
    je      .fn_push_unk
    mov     rdi, [fn_ret_types+r13*8]
    jmp     .fn_do_push
.fn_push_unk:
    mov     rdi, TY_UNK
.fn_do_push:
    call    ty_push
    jmp     .done
.mod_call:
    push    rbx
    push    r12
    call    tok_advance         ; eat mod name
    call    tok_advance         ; eat .
    call    tok_cur_type
    cmp     rax, TOK_IDENT
    je      .mod_name_ok
    mov     rdx, em_expect_member_name
    mov     rcx, em_expect_member_name_l
    call    emit_error_tok
    pop     r12
    pop     rbx
    mov     rdi, 0
    call    ir_const
    mov     r15, -1
    jmp     .mc_nc
.mod_name_ok:
    call    tok_cur_ptr
    mov     r13, rax
    call    tok_cur_len
    mov     r14, rax
    call    tok_advance         ; eat func name
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    je      .mod_call_lparen_ok
    mov     rdx, em_expect_call_lparen
    mov     rcx, em_expect_call_lparen_l
    call    emit_error_tok
    pop     r12
    pop     rbx
    mov     rdi, 0
    call    ir_const
    mov     r15, -1
    jmp     .mc_nc
.mod_call_lparen_ok:
    mov     rdi, rbx
    mov     rsi, r12
    call    mod_find
    cmp     rax, -1
    jne     .mod_qual_ok
    mov     rdx, em_mod_undef
    mov     rcx, em_mod_undef_l
    call    emit_error_tok
    pop     r12
    pop     rbx
    mov     rdi, 0
    call    ir_const
    mov     r15, -1
    jmp     .mc_nc
.mod_qual_ok:
    mov     rdi, r13
    mov     rsi, r14
    call    fn_find
    push    rax
    call    parse_call_args
    mov     r12, rax
    pop     r15
    pop     rdx                 ; r12 = mod name len (actually pushed r12 last)
    pop     rsi                 ; rbx = mod name ptr (actually pushed rbx first)
    cmp     qword [had_error], 0
    je      .mc_after_args
    mov     rdi, 0
    call    ir_const
    jmp     .mc_nc
.mc_after_args:
    cmp     r15, -1
    jne     .mc_chk_arity
    mov     rdx, em_fn_undef
    mov     rcx, em_fn_undef_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .mc_nc
.mc_chk_arity:
    mov     rax, [fn_pcnt+r15*8]
    cmp     rax, r12
    je      .mc_emit
    mov     rdx, em_fn_arity
    mov     rcx, em_fn_arity_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .mc_nc
.mc_emit:
    ; emit call with module prefix applied
    ; module prefix is in mod_name (set by IR_MOD_BGN); use func name directly
    mov     rdi, r13
    mov     rsi, r14
    call    ir_call
    mov     rax, [fn_pcnt+r15*8]
    test    rax, rax
    jz      .mc_nc
    imul    rdi, rax, 8
    call    ir_add_rsp
.mc_nc:
    cmp     r15, -1
    je      .mc_push_unk
    mov     rdi, [fn_ret_types+r15*8]
    jmp     .mc_do_push
.mc_push_unk:
    mov     rdi, TY_UNK
.mc_do_push:
    call    ty_push
    jmp     .done
.arr_acc:
    mov     r13, [type_stkp]    ; save depth — ir_load+parse_expr types discarded via restore
    call    tok_advance
    call    ir_load
    ; dispatch: string / array indexing; reject plain int
    cmp     qword [type_stk + r13*8], TY_STR
    je      .str_idx_acc
    cmp     qword [type_stk + r13*8], TY_INT
    jne     .arr_acc_ok
    mov     rdx, em_index_on_int
    mov     rcx, em_index_on_int_l
    call    emit_error_tok
    call    tok_advance         ; consume '['
    call    parse_expr          ; consume index expression
    call    ty_discard
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .int_idx_done
    call    tok_advance         ; consume ']'
.int_idx_done:
    mov     [type_stkp], r13
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done
.arr_acc_ok:
    ; Save array element type: TY_STR_ARR → element is TY_STR; else TY_UNK
    mov     r14, [type_stk + r13*8]
    call    ir_push
    call    tok_advance         ; eat [
    call    tok_cur_type
    cmp     rax, TOK_MINUS
    jne     .arr_acc_idx
    mov     rdx, em_neg_index
    mov     rcx, em_neg_index_l
    call    emit_error_tok
    mov     [type_stkp], r13
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done
.arr_acc_idx:
    cmp     rax, TOK_RBRACKET
    je      .arr_acc_idx_err
    cmp     rax, TOK_EOF
    je      .arr_acc_idx_err
    cmp     rax, TOK_NEWLINE
    je      .arr_acc_idx_err
    call    parse_expr
    call    ty_pop
    cmp     rax, TY_INT
    je      .arr_acc_idx_type_ok
    cmp     rax, TY_UNK
    je      .arr_acc_idx_type_ok
    mov     rdx, em_index_type
    mov     rcx, em_index_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
.arr_acc_idx_type_ok:
    call    ir_imul8
    call    ir_arr_ld
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .arr_missing_rbracket
    call    tok_advance
    jmp     .arr_close
.arr_missing_rbracket:
    mov     rdx, em_expect_rbracket
    mov     rcx, em_expect_rbracket_l
    call    emit_error_tok
.arr_close:
    mov     [type_stkp], r13
    cmp     r14, TY_STR_ARR
    jne     .arr_close_unk
    mov     rdi, TY_STR
    jmp     .arr_close_push
.arr_close_unk:
    mov     rdi, TY_UNK
.arr_close_push:
    call    ty_push
    jmp     .done
.arr_acc_idx_err:
    mov     rdx, em_array_index
    mov     rcx, em_array_index_l
    call    emit_error_tok
    mov     [type_stkp], r13
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done
.str_idx_acc:
    call    ir_push
    call    tok_advance         ; eat [
    call    tok_cur_type
    cmp     rax, TOK_MINUS
    jne     .str_idx_body
    mov     rdx, em_neg_index
    mov     rcx, em_neg_index_l
    call    emit_error_tok
    mov     [type_stkp], r13
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done
.str_idx_body:
    cmp     rax, TOK_RBRACKET
    je      .arr_acc_idx_err
    cmp     rax, TOK_EOF
    je      .arr_acc_idx_err
    cmp     rax, TOK_NEWLINE
    je      .arr_acc_idx_err
    call    parse_expr
    call    ty_pop
    cmp     rax, TY_INT
    je      .str_idx_type_ok
    cmp     rax, TY_UNK
    je      .str_idx_type_ok
    mov     rdx, em_index_type
    mov     rcx, em_index_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
.str_idx_type_ok:
    call    ir_str_at
    call    tok_cur_type
    cmp     rax, TOK_RBRACKET
    jne     .str_idx_missing_rbracket
    call    tok_advance
    jmp     .str_idx_close
.str_idx_missing_rbracket:
    mov     rdx, em_expect_rbracket
    mov     rcx, em_expect_rbracket_l
    call    emit_error_tok
.str_idx_close:
    mov     [type_stkp], r13
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done
.argc_builtin:
    call    tok_advance
    call    ir_argc
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done
.arg_builtin:
    call    tok_advance         ; eat 'arg'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance         ; eat '('
    call    parse_expr_required
    call    ty_pop
    cmp     rax, TY_INT
    je      .arg_type_ok
    mov     rdx, em_arg_type
    mov     rcx, em_arg_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .arg_close
.arg_type_ok:
    call    ir_arg
.arg_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance         ; eat ')'
.arg_type_push:
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.exit_builtin:
    call    tok_advance             ; eat exit
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat (
    call    parse_expr_required     ; exit code -> rax
    call    ty_pop
    cmp     rax, TY_INT
    je      .exit_type_ok
    mov     rdx, em_exit_type
    mov     rcx, em_exit_type_l
    call    emit_error_tok
    mov     rdi, 1
    call    ir_const
.exit_type_ok:
    call    ir_exit
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat )
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.arg_str_builtin:
    call    tok_advance
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_str
    call    tok_advance
    call    parse_expr_required
    call    ty_pop
    cmp     rax, TY_INT
    je      .as_type_ok
    mov     rdx, em_arg_str_type
    mov     rcx, em_arg_str_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .as_close
.as_type_ok:
    inc     qword [arg_str_total]
    call    ir_arg_str
.as_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_str
    call    tok_advance
.as_push:
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.find_builtin:
    call    tok_advance             ; eat find
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat (
    call    parse_expr_required     ; haystack slot -> rax
    call    ir_push                 ; save haystack slot while parsing needle
    xor     r12, r12                ; nonzero means type error already emitted
    call    ty_pop
    cmp     rax, TY_STR
    je      .find_hay_type_ok
    mov     rdx, em_find_haystack_type
    mov     rcx, em_find_haystack_type_l
    call    emit_error_tok
    mov     r12, 1
.find_hay_type_ok:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .builtin_arg_sep_err_int_stack
    call    tok_advance             ; eat comma
    call    parse_expr_required     ; needle slot -> rax
    call    ty_pop
    cmp     rax, TY_STR
    je      .find_needle_type_ok
    mov     rdx, em_find_needle_type
    mov     rcx, em_find_needle_type_l
    call    emit_error_tok
    mov     r12, 1
.find_needle_type_ok:
    test    r12, r12
    jnz     .find_type_err
    inc     qword [str_find_total]
    call    ir_str_find
    jmp     .find_close
.find_type_err:
    call    ir_pop_rax              ; discard saved haystack slot on generated stack
    mov     rdi, 0
    call    ir_const
.find_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat )
.find_push:
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.slice_builtin:
    call    tok_advance             ; eat slice
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_str
    call    tok_advance             ; eat (
    call    parse_expr_required     ; source slot -> rax
    call    ir_push                 ; save source slot
    xor     r12, r12
    call    ty_pop
    cmp     rax, TY_STR
    je      .slice_source_type_ok
    mov     rdx, em_slice_source_type
    mov     rcx, em_slice_source_type_l
    call    emit_error_tok
    mov     r12, 1
.slice_source_type_ok:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .slice_comma1_err
    call    tok_advance             ; eat comma
    call    parse_expr_required     ; start -> rax
    call    ir_push                 ; save start
    call    ty_pop
    cmp     rax, TY_INT
    je      .slice_start_type_ok
    mov     rdx, em_slice_start_type
    mov     rcx, em_slice_start_type_l
    call    emit_error_tok
    mov     r12, 1
.slice_start_type_ok:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .slice_comma2_err
    call    tok_advance             ; eat comma
    call    parse_expr_required     ; end -> rax
    call    ty_pop
    cmp     rax, TY_INT
    je      .slice_end_type_ok
    mov     rdx, em_slice_end_type
    mov     rcx, em_slice_end_type_l
    call    emit_error_tok
    mov     r12, 1
.slice_end_type_ok:
    test    r12, r12
    jnz     .slice_type_err
    inc     qword [str_slice_total]
    inc     qword [str_cat_cnt]
    call    ir_str_slice
    jmp     .slice_close
.slice_type_err:
    call    ir_pop_rax              ; discard saved start
    call    ir_pop_rax              ; discard saved source
    mov     rdi, 0
    call    ir_const
.slice_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_str
    call    tok_advance             ; eat )
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done
.slice_comma1_err:
    call    ir_pop_rax              ; discard saved source
    mov     rdx, em_expect_arg_sep
    mov     rcx, em_expect_arg_sep_l
    call    emit_error_tok
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done
.slice_comma2_err:
    call    ir_pop_rax              ; discard saved start
    call    ir_pop_rax              ; discard saved source
    mov     rdx, em_expect_arg_sep
    mov     rcx, em_expect_arg_sep_l
    call    emit_error_tok
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.lnot:
    call    tok_advance
    call    parse_expr
    call    ty_check_int_unary
    IR0     IR_LNOT
    jmp     .done

.true_lit:
    call    tok_advance
    mov     rdi, 1
    call    ir_const
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.false_lit:
    call    tok_advance
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.bnot:
    call    tok_advance
    call    parse_factor
    call    ty_check_int_unary
    call    ir_bnot
    jmp     .done

.len_builtin:
    call    tok_advance             ; eat 'len'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    parse_expr_required
    call    ty_pop
    cmp     rax, TY_STR
    je      .lb_str
    cmp     rax, TY_ARR
    je      .lb_arr
    cmp     rax, TY_STR_ARR
    jne     .lb_type_err
.lb_arr:
    IR0     IR_ARR_LEN
    jmp     .lb_close
.lb_str:
    IR0     IR_STR_LEN
    jmp     .lb_close
.lb_type_err:
    mov     rdx, em_len_type
    mov     rcx, em_len_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
.lb_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
.lb_push:
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.abs_builtin:
    call    tok_advance             ; eat 'abs'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    parse_expr_required
    call    ty_check_int_unary
    IR0     IR_ABS
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
    jmp     .done

.min_builtin:
    call    tok_advance             ; eat 'min'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    parse_expr_required     ; a → rax
    call    ir_push                 ; push a
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .builtin_arg_sep_err_int_stack
    call    tok_advance             ; eat ','
    call    parse_expr_required     ; b → rax
    call    ir_pop_rbx              ; rbx = a
    IR0     IR_FMIN
    call    ty_check_arith
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
    jmp     .done

.max_builtin:
    call    tok_advance             ; eat 'max'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    parse_expr_required     ; a → rax
    call    ir_push                 ; push a
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .builtin_arg_sep_err_int_stack
    call    tok_advance             ; eat ','
    call    parse_expr_required     ; b → rax
    call    ir_pop_rbx              ; rbx = a
    IR0     IR_FMAX
    call    ty_check_arith
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
    jmp     .done

.input_int_builtin:
    call    tok_advance             ; eat 'input_int'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
.iib_push:
    IR0     IR_INPUT_INT
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.input_str_builtin:
    call    tok_advance             ; eat 'input_str'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_str
    call    tok_advance             ; eat '('
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_str
    call    tok_advance             ; eat ')'
.isb_push:
    inc     qword [istr_total]
    call    ir_input_str
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.read_file_builtin:
    call    tok_advance             ; eat "read_file"
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_str
    call    tok_advance             ; eat "("
    call    parse_expr_required
    call    ty_pop
    cmp     rax, TY_STR
    je      .rf_type_ok
    mov     rdx, em_read_file_type
    mov     rcx, em_read_file_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .rf_close
.rf_type_ok:
    inc     qword [file_read_total]
    call    ir_read_file
.rf_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_str
    call    tok_advance             ; eat ")"
.rf_push:
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.write_file_builtin:
    call    tok_advance             ; eat "write_file"
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat "("
    call    parse_expr_required     ; path slot -> rax
    call    ir_push                 ; save path slot while parsing data
    xor     r12, r12                ; nonzero means type error already emitted
    call    ty_pop
    cmp     rax, TY_STR
    je      .wf_path_type_ok
    mov     rdx, em_write_file_path_type
    mov     rcx, em_write_file_path_type_l
    call    emit_error_tok
    mov     r12, 1
.wf_path_type_ok:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .builtin_arg_sep_err_int_stack
    call    tok_advance             ; eat comma
    call    parse_expr_required     ; data slot -> rax
    call    ty_pop
    cmp     rax, TY_STR
    je      .wf_data_type_ok
    mov     rdx, em_write_file_data_type
    mov     rcx, em_write_file_data_type_l
    call    emit_error_tok
    mov     r12, 1
.wf_data_type_ok:
    test    r12, r12
    jnz     .wf_type_err
    inc     qword [write_file_total]
    call    ir_write_file
    jmp     .wf_close
.wf_type_err:
    call    ir_pop_rax              ; discard saved path slot on generated stack
    mov     rdi, 0
    call    ir_const
.wf_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ")"
.wf_push:
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.append_file_builtin:
    call    tok_advance             ; eat "append_file"
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat "("
    call    parse_expr_required     ; path slot -> rax
    call    ir_push                 ; save path slot while parsing data
    xor     r12, r12                ; nonzero means type error already emitted
    call    ty_pop
    cmp     rax, TY_STR
    je      .af_path_type_ok
    mov     rdx, em_append_file_path_type
    mov     rcx, em_append_file_path_type_l
    call    emit_error_tok
    mov     r12, 1
.af_path_type_ok:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .builtin_arg_sep_err_int_stack
    call    tok_advance             ; eat comma
    call    parse_expr_required     ; data slot -> rax
    call    ty_pop
    cmp     rax, TY_STR
    je      .af_data_type_ok
    mov     rdx, em_append_file_data_type
    mov     rcx, em_append_file_data_type_l
    call    emit_error_tok
    mov     r12, 1
.af_data_type_ok:
    test    r12, r12
    jnz     .af_type_err
    inc     qword [append_file_total]
    call    ir_append_file
    jmp     .af_close
.af_type_err:
    call    ir_pop_rax              ; discard saved path slot on generated stack
    mov     rdi, 0
    call    ir_const
.af_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ")"
.af_push:
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.str_builtin:
    call    tok_advance             ; eat 'str'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_str
    call    tok_advance             ; eat '('
    call    parse_expr_required
    call    ty_pop
    cmp     rax, TY_INT
    je      .str_type_ok
    cmp     rax, TY_UNK
    je      .str_type_ok
    mov     rdx, em_str_builtin_type
    mov     rcx, em_str_builtin_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .str_close
.str_type_ok:
    inc     qword [its_cnt]
    call    ir_int_to_str
.str_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_str
    call    tok_advance             ; eat ')'
.sb_push:
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.int_builtin:
    call    tok_advance             ; eat 'int'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    parse_expr_required
    call    ty_pop
    cmp     rax, TY_STR
    je      .int_type_ok
    cmp     rax, TY_UNK
    je      .int_type_ok
    mov     rdx, em_int_builtin_type
    mov     rcx, em_int_builtin_type_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    jmp     .int_close
.int_type_ok:
    call    ir_str_to_int
.int_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
.ib_push:
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.push_builtin:
    ; push(arr_expr, val_expr) — appends val to arr; returns new count (TY_INT)
    call    tok_advance             ; eat 'push'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_int
    call    tok_advance             ; eat '('
    call    parse_expr_required     ; arr_expr → rax = arr_ptr at runtime
    call    ir_push                 ; save arr_ptr on NASM stack
    call    ty_pop                  ; pop array type into rax
    cmp     rax, TY_ARR
    je      .pb_int_arr
    cmp     rax, TY_STR_ARR
    jne     .pb_type_err
    mov     r12, TY_STR_ARR
    jmp     .pb_arr_ok
.pb_int_arr:
    mov     r12, TY_ARR
.pb_arr_ok:
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    jne     .builtin_arg_sep_err_int_stack
    call    tok_advance             ; eat ','
    call    parse_expr_required     ; val_expr → rax = value at runtime
    call    ty_pop                  ; val type
    cmp     r12, TY_ARR
    je      .pb_expect_int
    cmp     rax, TY_STR
    jne     .pb_value_type_err
    jmp     .pb_value_ok
.pb_expect_int:
    cmp     rax, TY_INT
    jne     .pb_value_type_err
.pb_value_ok:
    IR0     IR_ARR_PUSH             ; pop rdi=arr_ptr, mov rsi=rax, call _arr_push
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_int
    call    tok_advance             ; eat ')'
.pb_no_rp:
    mov     rdi, TY_INT
    call    ty_push                 ; push returns new count
    jmp     .done
.pb_value_type_err:
    ; arr_ptr still on NASM stack from ir_push — pop it to keep stack clean
    call    ir_pop_rax
    mov     rdx, em_push_type
    mov     rcx, em_push_type_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done
.pb_type_err:
    ; arr_ptr still on NASM stack from ir_push — pop it to keep stack clean
    call    ir_pop_rax
    mov     rdx, em_push_not_arr
    mov     rcx, em_push_not_arr_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done
.pop_builtin:
    call    tok_advance             ; eat 'pop'
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .builtin_lparen_err_unknown
    call    tok_advance             ; eat '('
    call    parse_expr_required     ; arr_expr -> rax = arr_ptr at runtime
    call    ty_pop
    cmp     rax, TY_ARR
    je      .pop_int_arr
    cmp     rax, TY_STR_ARR
    je      .pop_str_arr
    mov     rdx, em_pop_not_arr
    mov     rcx, em_pop_not_arr_l
    call    emit_error_tok
    mov     rdi, 0
    call    ir_const
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .pop_close
.pop_int_arr:
    call    ir_arr_pop
    mov     rdi, TY_INT
    call    ty_push
    jmp     .pop_close
.pop_str_arr:
    call    ir_arr_pop
    mov     rdi, TY_STR
    call    ty_push
.pop_close:
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    jne     .builtin_rparen_err_done
    call    tok_advance             ; eat ')'
    jmp     .done
.pop_push_unknown:
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done

.builtin_lparen_err_int:
    mov     rdx, em_expect_builtin_lparen
    mov     rcx, em_expect_builtin_lparen_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.builtin_lparen_err_str:
    mov     rdx, em_expect_builtin_lparen
    mov     rcx, em_expect_builtin_lparen_l
    call    emit_error_tok
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.builtin_lparen_err_unknown:
    mov     rdx, em_expect_builtin_lparen
    mov     rcx, em_expect_builtin_lparen_l
    call    emit_error_tok
    mov     rdi, TY_UNK
    call    ty_push
    jmp     .done

.builtin_rparen_err_int:
    mov     rdx, em_expect_builtin_rparen
    mov     rcx, em_expect_builtin_rparen_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.builtin_rparen_err_str:
    mov     rdx, em_expect_builtin_rparen
    mov     rcx, em_expect_builtin_rparen_l
    call    emit_error_tok
    mov     rdi, TY_STR
    call    ty_push
    jmp     .done

.builtin_arg_sep_err_int_stack:
    call    ir_pop_rax             ; discard saved first argument on error path
    mov     rdx, em_expect_arg_sep
    mov     rcx, em_expect_arg_sep_l
    call    emit_error_tok
    mov     rdi, TY_INT
    call    ty_push
    jmp     .done

.builtin_rparen_err_done:
    mov     rdx, em_expect_builtin_rparen
    mov     rcx, em_expect_builtin_rparen_l
    call    emit_error_tok
    jmp     .done

.done:
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    je      .chain_err
    cmp     rax, TOK_LBRACKET
    je      .chain_err
    cmp     rax, TOK_DOT
    je      .chain_err
    jmp     .ret
.chain_err:
    mov     rdx, em_chain_unsupported
    mov     rcx, em_chain_unsupported_l
    call    emit_error_tok
.ret:
    pop     rbx
    pop     r14
    pop     r13
    pop     r12
    ret

; ─── parse_call_args ─────────────────────────────────────────
parse_call_args:
    push    r12
    push    rbx
    mov     rbx, [type_stkp]
    xor     r12, r12
    call    tok_cur_type
    cmp     rax, TOK_LPAREN
    jne     .done
    call    tok_advance
.lp:
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    je      .end
    cmp     rax, TOK_EOF
    je      .need_expr
    call    parse_expr_required
    call    ir_push
    inc     r12
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_COMMA
    je      .sk
    cmp     rax, TOK_RPAREN
    je      .end
    cmp     rax, TOK_EOF
    je      .missing_close
    mov     rdx, em_expect_arg_sep
    mov     rcx, em_expect_arg_sep_l
    call    emit_error_tok
    jmp     .end
.sk:
    call    tok_advance
    call    tok_skip_nl
    call    tok_cur_type
    cmp     rax, TOK_RPAREN
    je      .need_expr
    cmp     rax, TOK_EOF
    je      .need_expr
    cmp     rax, TOK_COMMA
    je      .need_expr
    jmp     .lp
.need_expr:
    mov     rdx, em_expect_expr
    mov     rcx, em_expect_expr_l
    call    emit_error_tok
    jmp     .end
.missing_close:
    mov     rdx, em_expect_arg_sep
    mov     rcx, em_expect_arg_sep_l
    call    emit_error_tok
    jmp     .restore
.end:
    call    tok_advance
.restore:
    mov     [type_stkp], rbx
    mov     rax, r12
.done:
    pop     rbx
    pop     r12
    ret

; ════════════════════════════════════════════════════════════
;  OPTIMIZER
