opt_run:
    call    opt_const_fold
    call    opt_compact
    call    opt_cmp_fold
    call    opt_compact
    call    opt_jz_const
    call    opt_compact
    call    opt_prune_labels
    call    opt_compact
    call    opt_jmp_next_label
    call    opt_compact
    call    opt_const_overwrite
    call    opt_compact
    call    opt_const_fold
    call    opt_compact
    call    opt_jz_const
    call    opt_compact
    call    opt_dce
    call    opt_compact
    call    opt_jmp_next_label
    call    opt_compact
    call    opt_prune_labels
    call    opt_compact
    ret

; ── Pass 1: Constant Folding ─────────────────────────────────
; Pattern A: CONST(a) PUSH CONST(b) POP_RBX ADD/SUB/MUL/FMIN/FMAX/BAND/BOR/BXOR → CONST(a op b)
; Pattern B: CONST(a) PUSH CONST(b) DIV/MOD/SHL/SHR                              → CONST(a op b)
; Pattern C: CONST(a) LNOT/BNOT/ABS                                               → CONST(result)
opt_const_fold:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    ; ── Pattern C: CONST + unary op (2-instruction) ─────────
    ; Handles: LNOT (x==0?1:0), BNOT (~x), ABS (|x|)
    mov     r12, [ir_cnt]
    cmp     r12, 2
    jl      .pass_ab
    sub     r12, 1
    xor     r13, r13
.scan_lnot:
    cmp     r13, r12
    jg      .pass_ab
    mov     rax, r13
    shl     rax, 5
    lea     rbx, [ir_buf+rax]
    cmp     qword [rbx+IR_F_OP], IR_CONST
    jne     .lnot_next
    mov     rax, r13
    inc     rax
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    mov     rax, [rcx+IR_F_OP]
    cmp     rax, IR_LNOT
    je      .fold_lnot
    cmp     rax, IR_BNOT
    je      .fold_bnot
    cmp     rax, IR_ABS
    je      .fold_abs
    jmp     .lnot_next
.fold_lnot:
    cmp     qword [rbx+IR_F_A], 0
    sete    al
    movzx   rax, al
    mov     [rbx+IR_F_A], rax
    jmp     .fold_unary
.fold_bnot:
    mov     rax, [rbx+IR_F_A]
    not     rax
    mov     [rbx+IR_F_A], rax
    jmp     .fold_unary
.fold_abs:
    mov     rax, [rbx+IR_F_A]
    test    rax, rax
    jns     .fold_unary
    neg     rax
    mov     [rbx+IR_F_A], rax
.fold_unary:
    mov     qword [rcx+IR_F_OP], IR_DEAD
    jmp     .scan_lnot      ; chain: new CONST may feed next unary op
.lnot_next:
    inc     r13
    jmp     .scan_lnot
    ; ── Patterns A & B: arithmetic (5-instruction) ───────────
.pass_ab:
    mov     r12, [ir_cnt]
    cmp     r12, 5
    jl      .done
    sub     r12, 4
    xor     r13, r13
.scan:
    cmp     r13, r12
    jg      .done
    mov     rax, r13
    shl     rax, 5
    lea     rbx, [ir_buf+rax]
    cmp     qword [rbx+IR_F_OP], IR_CONST
    jne     .next
    mov     rax, r13
    inc     rax
    shl     rax, 5
    lea     r14, [ir_buf+rax]
    cmp     qword [r14+IR_F_OP], IR_PUSH
    jne     .next
    mov     rax, r13
    add     rax, 2
    shl     rax, 5
    lea     r15, [ir_buf+rax]
    cmp     qword [r15+IR_F_OP], IR_CONST
    jne     .next
    mov     r9, [rbx+IR_F_A]    ; a
    mov     r10, [r15+IR_F_A]   ; b
    mov     rax, r13
    add     rax, 3
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    mov     r8, [rcx+IR_F_OP]
    cmp     r8, IR_DIV
    je      .fold_div_mod
    cmp     r8, IR_MOD
    je      .fold_div_mod
    cmp     r8, IR_SHL
    je      .fold_shl_shr
    cmp     r8, IR_SHR
    je      .fold_shl_shr
    cmp     r8, IR_POP_RBX
    jne     .next
    mov     rax, r13
    add     rax, 4
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    mov     r8, [rcx+IR_F_OP]
    cmp     qword [rcx+IR_F_OP], IR_DEAD
    je      .next
    cmp     r8, IR_ADD
    je      .fold_add
    cmp     r8, IR_SUB
    je      .fold_sub
    cmp     r8, IR_MUL
    je      .fold_mul
    cmp     r8, IR_FMIN
    je      .fold_min
    cmp     r8, IR_FMAX
    je      .fold_max
    cmp     r8, IR_BAND
    je      .fold_band
    cmp     r8, IR_BOR
    je      .fold_bor
    cmp     r8, IR_BXOR
    je      .fold_bxor
    jmp     .next
.fold_min:
    cmp     r9, r10
    cmovg   r9, r10             ; r9 = min(r9, r10)
    jmp     .apply_long
.fold_max:
    cmp     r9, r10
    cmovl   r9, r10             ; r9 = max(r9, r10)
    jmp     .apply_long
.fold_band:
    and     r9, r10
    jmp     .apply_long
.fold_bor:
    or      r9, r10
    jmp     .apply_long
.fold_bxor:
    xor     r9, r10
    jmp     .apply_long
.fold_add:
    add     r9, r10
    jmp     .apply_long
.fold_sub:
    sub     r9, r10
    jmp     .apply_long
.fold_mul:
    imul    r9, r10
    jmp     .apply_long
.fold_shl_shr:
    mov     rax, r9
    mov     rcx, r10            ; shift amount → cl
    cmp     r8, IR_SHL
    je      .do_shl
    sar     rax, cl
    jmp     .save_shift
.do_shl:
    shl     rax, cl
.save_shift:
    mov     r9, rax
    jmp     .apply_short
.fold_div_mod:
    cmp     r10, 0
    je      .next
    mov     rax, r9
    cqo
    idiv    r10
    cmp     r8, IR_DIV
    je      .fold_div
    mov     r9, rdx
    jmp     .apply_short
.fold_div:
    mov     r9, rax
.apply_short:
    mov     qword [rbx+IR_F_OP], IR_CONST
    mov     [rbx+IR_F_A], r9
    mov     rax, r13
%rep 3
    inc     rax
    push    rax
    shl     rax, 5
    mov     qword [ir_buf+rax+IR_F_OP], IR_DEAD
    pop     rax
%endrep
    jmp     .scan
.apply_long:
    mov     qword [rbx+IR_F_OP], IR_CONST
    mov     [rbx+IR_F_A], r9
    mov     rax, r13
%rep 4
    inc     rax
    push    rax
    shl     rax, 5
    mov     qword [ir_buf+rax+IR_F_OP], IR_DEAD
    pop     rax
%endrep
    jmp     .scan   ; stay on same index — new CONST may chain
.next:
    inc     r13
    jmp     .scan
.done:
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ── Pass 2: Dead Code Elimination ────────────────────────────
opt_dce:
    push    r12
    push    r13
    push    rbx
    xor     r12, r12
    mov     r13, [ir_cnt]
    xor     rbx, rbx
.scan:
    cmp     r12, r13
    jge     .done
    mov     rax, r12
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    mov     rax, [rcx+IR_F_OP]
    test    rbx, rbx
    jz      .live
    ; in dead zone
    cmp     rax, IR_LBL
    je      .exit_dead
    cmp     rax, IR_FN_BGN
    je      .exit_dead
    cmp     rax, IR_FN_END
    je      .exit_dead
    cmp     rax, IR_MOD_BGN
    je      .exit_dead
    cmp     rax, IR_MOD_END
    je      .exit_dead
    cmp     rax, IR_DEAD
    je      .next
    mov     qword [rcx+IR_F_OP], IR_DEAD
    jmp     .next
.exit_dead:
    xor     rbx, rbx
    jmp     .next
.live:
    cmp     rax, IR_JMP
    je      .enter_dead
    cmp     rax, IR_RET
    je      .enter_dead
    cmp     rax, IR_JMP_TC
    je      .enter_dead
    jmp     .next
.enter_dead:
    mov     rbx, 1
.next:
    inc     r12
    jmp     .scan
.done:
    pop     rbx
    pop     r13
    pop     r12
    ret

; ── Pass 3: Compact Dead IR ──────────────────────────────────
opt_compact:
    push    r12
    push    r13
    push    r14
    push    r15
    xor     r12, r12            ; read index
    xor     r13, r13            ; write index
    mov     r14, [ir_cnt]
.scan:
    cmp     r12, r14
    jge     .done
    mov     rax, r12
    shl     rax, 5
    lea     r15, [ir_buf+rax]
    mov     rdx, [r15+IR_F_OP]
    cmp     rdx, IR_DEAD
    je      .next
    cmp     rdx, IR_NOP
    je      .next
    cmp     r12, r13
    je      .keep
    mov     rax, r13
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    mov     rdx, [r15+IR_F_OP]
    mov     [rcx+IR_F_OP], rdx
    mov     rdx, [r15+IR_F_A]
    mov     [rcx+IR_F_A], rdx
    mov     rdx, [r15+IR_F_B]
    mov     [rcx+IR_F_B], rdx
    mov     rdx, [r15+IR_F_LN]
    mov     [rcx+IR_F_LN], rdx
.keep:
    inc     r13
.next:
    inc     r12
    jmp     .scan
.done:
    mov     [ir_cnt], r13
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ── Pass 4: Fold Constant Compare Materialization ───────────
opt_cmp_fold:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    mov     r12, [ir_cnt]
    cmp     r12, 10
    jl      .done
    sub     r12, 9
    xor     r13, r13
.scan:
    cmp     r13, r12
    jg      .done
    mov     rax, r13
    shl     rax, 5
    lea     rbx, [ir_buf+rax]
    cmp     qword [rbx+IR_F_OP], IR_CONST
    jne     .next
    mov     rax, r13
    add     rax, 1
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_PUSH
    jne     .next
    mov     rax, r13
    add     rax, 2
    shl     rax, 5
    lea     r14, [ir_buf+rax]
    cmp     qword [r14+IR_F_OP], IR_CONST
    jne     .next
    mov     rax, r13
    add     rax, 3
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_POP_RBX
    jne     .next
    mov     rax, r13
    add     rax, 4
    shl     rax, 5
    lea     r15, [ir_buf+rax]
    cmp     qword [r15+IR_F_OP], IR_CMP
    jne     .next
    mov     rax, r13
    add     rax, 5
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_CONST
    jne     .next
    cmp     qword [ir_buf+rax+IR_F_A], 1
    jne     .next
    mov     rax, r13
    add     rax, 6
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    cmp     qword [rcx+IR_F_OP], IR_JMP
    jne     .next
    mov     r8, [r15+IR_F_B]        ; false label id
    mov     rax, r13
    add     rax, 7
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_LBL
    jne     .next
    cmp     qword [ir_buf+rax+IR_F_A], r8
    jne     .next
    cmp     qword [ir_buf+rax+IR_F_B], LBL_CF
    jne     .next
    mov     rax, r13
    add     rax, 8
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_CONST
    jne     .next
    cmp     qword [ir_buf+rax+IR_F_A], 0
    jne     .next
    mov     r9, [rcx+IR_F_A]        ; done label id
    mov     rax, r13
    add     rax, 9
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_LBL
    jne     .next
    cmp     qword [ir_buf+rax+IR_F_A], r9
    jne     .next
    cmp     qword [ir_buf+rax+IR_F_B], LBL_CD
    jne     .next
    mov     r9, [rbx+IR_F_A]
    mov     r10, [r14+IR_F_A]
    mov     r11, [r15+IR_F_A]       ; compare token
    xor     rdx, rdx
    cmp     r11, TOK_GT
    je      .gt
    cmp     r11, TOK_LT
    je      .lt
    cmp     r11, TOK_EQEQ
    je      .eq
    cmp     r11, TOK_NEQ
    je      .ne
    cmp     r11, TOK_GTE
    je      .ge
    cmp     r11, TOK_LTE
    je      .le
    jmp     .next
.gt:
    cmp     r9, r10
    setg    dl
    jmp     .apply
.lt:
    cmp     r9, r10
    setl    dl
    jmp     .apply
.eq:
    cmp     r9, r10
    sete    dl
    jmp     .apply
.ne:
    cmp     r9, r10
    setne   dl
    jmp     .apply
.ge:
    cmp     r9, r10
    setge   dl
    jmp     .apply
.le:
    cmp     r9, r10
    setle   dl
.apply:
    movzx   rdx, dl
    mov     qword [rbx+IR_F_OP], IR_CONST
    mov     [rbx+IR_F_A], rdx
    mov     rax, r13
%rep 9
    inc     rax
    push    rax
    shl     rax, 5
    mov     qword [ir_buf+rax+IR_F_OP], IR_DEAD
    pop     rax
%endrep
    jmp     .scan
.next:
    inc     r13
    jmp     .scan
.done:
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ── Pass 5: Simplify CONST + JZ ─────────────────────────────
opt_jz_const:
    push    r12
    push    r13
    push    r14
    mov     r12, [ir_cnt]
    cmp     r12, 2
    jl      .done
    dec     r12
    xor     r13, r13
.scan:
    cmp     r13, r12
    jg      .done
    mov     rax, r13
    shl     rax, 5
    lea     r14, [ir_buf+rax]
    cmp     qword [r14+IR_F_OP], IR_CONST
    jne     .next
    mov     rax, r13
    inc     rax
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    cmp     qword [rcx+IR_F_OP], IR_JZ
    jne     .next
    cmp     qword [r14+IR_F_A], 0
    je      .const_zero
    mov     qword [r14+IR_F_OP], IR_DEAD  ; CONST is dead — jump never fires
    mov     qword [rcx+IR_F_OP], IR_DEAD
    jmp     .next
.const_zero:
    mov     qword [r14+IR_F_OP], IR_DEAD  ; CONST is dead — jump always fires
    mov     qword [rcx+IR_F_OP], IR_JMP
.next:
    inc     r13
    jmp     .scan
.done:
    pop     r14
    pop     r13
    pop     r12
    ret

; ── Pass 6: Remove JMP To Immediately Following Label ───────
opt_jmp_next_label:
    push    r12
    push    r13
    push    r14
    mov     r12, [ir_cnt]
    cmp     r12, 2
    jl      .done
    dec     r12
    xor     r13, r13
.scan:
    cmp     r13, r12
    jg      .done
    mov     rax, r13
    shl     rax, 5
    lea     r14, [ir_buf+rax]
    cmp     qword [r14+IR_F_OP], IR_JMP
    jne     .next
    mov     rax, r13
    inc     rax
    shl     rax, 5
    lea     rcx, [ir_buf+rax]
    cmp     qword [rcx+IR_F_OP], IR_LBL
    jne     .next
    mov     rax, [r14+IR_F_A]
    cmp     [rcx+IR_F_A], rax
    jne     .next
    mov     rax, [r14+IR_F_B]
    cmp     [rcx+IR_F_B], rax
    jne     .next
    mov     qword [r14+IR_F_OP], IR_DEAD
.next:
    inc     r13
    jmp     .scan
.done:
    pop     r14
    pop     r13
    pop     r12
    ret

; ── Pass 7: Remove Unreferenced Labels ──────────────────────
opt_prune_labels:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    xor     r12, r12
    mov     r13, [ir_cnt]
.scan:
    cmp     r12, r13
    jge     .done
    mov     rax, r12
    shl     rax, 5
    lea     r14, [ir_buf+rax]
    cmp     qword [r14+IR_F_OP], IR_LBL
    jne     .next
    mov     rbx, [r14+IR_F_A]
    mov     r15, [r14+IR_F_B]
    xor     rcx, rcx
.find_ref:
    cmp     rcx, r13
    jge     .drop
    mov     rax, rcx
    shl     rax, 5
    lea     rdx, [ir_buf+rax]
    mov     r8, [rdx+IR_F_OP]
    cmp     r8, IR_JZ
    je      .check_ref
    cmp     r8, IR_JMP
    je      .check_ref
    cmp     r8, IR_JGE
    je      .check_ref
    ; IR_JMP_TC: A=tc_label_id, implicit type=LBL_TC (B=0 in IR record)
    cmp     r8, IR_JMP_TC
    jne     .chk_cmp
    cmp     r15, LBL_TC
    jne     .ref_next
    cmp     [rdx+IR_F_A], rbx
    je      .keep
    jmp     .ref_next
    ; IR_CMP: A=op_token (not label), B=cf_label_id → only references LBL_CF labels
.chk_cmp:
    cmp     r8, IR_CMP
    jne     .ref_next
    cmp     r15, LBL_CF
    jne     .ref_next
    cmp     [rdx+IR_F_B], rbx
    je      .keep
    jmp     .ref_next
.check_ref:
    cmp     [rdx+IR_F_A], rbx
    jne     .ref_next
    cmp     [rdx+IR_F_B], r15
    je      .keep
.ref_next:
    inc     rcx
    jmp     .find_ref
.drop:
    mov     qword [r14+IR_F_OP], IR_DEAD
.next:
    inc     r12
    jmp     .scan
.keep:
.done:
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ── Pass 8: Remove Overwritten CONST Producers ──────────────
opt_const_overwrite:
    push    r12
    push    r13
    push    r14
    mov     r12, [ir_cnt]
    cmp     r12, 2
    jl      .done
    dec     r12
    xor     r13, r13
.scan:
    cmp     r13, r12
    jg      .done
    mov     rax, r13
    shl     rax, 5
    lea     r14, [ir_buf+rax]
    cmp     qword [r14+IR_F_OP], IR_CONST
    jne     .next
    mov     rax, r13
    inc     rax
    shl     rax, 5
    cmp     qword [ir_buf+rax+IR_F_OP], IR_CONST
    jne     .next
    mov     qword [r14+IR_F_OP], IR_DEAD
.next:
    inc     r13
    jmp     .scan
.done:
    pop     r14
    pop     r13
    pop     r12
    ret

; ════════════════════════════════════════════════════════════
;  CODEGEN  (IR → NASM text)
