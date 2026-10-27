fnv1a:
    ; rsi=ptr, rcx=len → rax=hash
    push    rbx
    push    rdx
    mov     rax, 0xcbf29ce484222325
    mov     rbx, 0x100000001b3
    test    rcx, rcx
    jz      .d
.lp:
    movzx   rdx, byte [rsi]
    xor     rax, rdx
    mul     rbx
    inc     rsi
    dec     rcx
    jnz     .lp
.d: pop     rdx
    pop     rbx
    ret

; ────────────────────────────────────────────────────────────
;  KEYWORD TABLE
; ────────────────────────────────────────────────────────────
kw_hash:
    ; rsi=ptr, rcx=len → rax=slot (0..63)
    push    rbx
    mov     rax, rcx
    imul    rax, rax, 31
    movzx   rbx, byte [rsi]
    xor     rax, rbx
    lea     rbx, [rsi+rcx-1]
    movzx   rbx, byte [rbx]
    xor     rax, rbx
    and     rax, 63
    pop     rbx
    ret

kw_init:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    lea     r12, [kw_init_data]
.lp:
    mov     r13, [r12]
    test    r13, r13
    jz      .done
    mov     r14, [r12+8]
    mov     r15, [r12+16]
    mov     rsi, r14
    mov     rcx, r15
    call    kw_hash
.probe:
    imul    rbx, rax, 24
    lea     rbx, [kw_table+rbx]
    cmp     qword [rbx], 0
    je      .store
    inc     rax
    and     rax, 63
    jmp     .probe
.store:
    mov     [rbx],    r13
    mov     [rbx+8],  r14
    mov     [rbx+16], r15
    add     r12, 24
    jmp     .lp
.done:
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

kw_check:
    ; rsi=ptr, rcx=len → rax=token_type or 0
    push    rbx
    push    r8
    push    r9
    push    r10
    mov     r8, rsi
    mov     r9, rcx
    call    kw_hash
.probe:
    imul    r10, rax, 24
    lea     r10, [kw_table+r10]
    mov     rbx, [r10]
    test    rbx, rbx
    jz      .nf
    cmp     [r10+16], r9
    jne     .nx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r8
    mov     rdi, [r10+8]
    mov     rcx, r9
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .nx
    mov     rax, rbx
    jmp     .done
.nx:
    inc     rax
    and     rax, 63
    jmp     .probe
.nf:
    xor     rax, rax
.done:
    pop     r10
    pop     r9
    pop     r8
    pop     rbx
    ret

; ────────────────────────────────────────────────────────────
;  GLOBAL SYMBOL TABLE  (FNV-1a open addressing)
; ────────────────────────────────────────────────────────────
sym_lookup:
    push    rbx
    push    r8
    push    r9
    push    r10
    mov     r8, rsi
    mov     r9, rcx
    call    fnv1a
    and     rax, HT_MASK
    mov     r10, rax
    xor     r11, r11
.probe:
    cmp     r11, HT_SZ
    jae     .nf
    mov     rbx, [ht_val+r10*8]
    test    rbx, rbx
    jz      .nf
    cmp     [ht_klen+r10*8], r9
    jne     .nx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r8
    mov     rdi, [ht_key+r10*8]
    mov     rcx, r9
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .nx
    mov     rax, rbx
    dec     rax
    jmp     .done
.nx:
    inc     r10
    and     r10, HT_MASK
    inc     r11
    jmp     .probe
.nf:
    mov     rax, -1
.done:
    pop     r10
    pop     r9
    pop     r8
    pop     rbx
    ret

sym_insert:
    push    rbx
    push    r8
    push    r9
    push    r10
    push    rdi
    mov     r8, rsi
    mov     r9, rcx
    call    sym_lookup
    cmp     rax, -1
    jne     .done
    mov     rsi, r8
    mov     rcx, r9
    call    fnv1a
    and     rax, HT_MASK
    mov     r10, rax
    cmp     qword [ht_cnt], HT_SZ
    jl      .probe
    mov     rdx, err_htovf
    mov     rcx, err_htovf_l
    call    symtab_capacity_error
.probe:
    cmp     qword [ht_val+r10*8], 0
    je      .empty
    inc     r10
    and     r10, HT_MASK
    jmp     .probe
.empty:
    mov     rax, [ht_cnt]
    mov     [ht_key+r10*8], r8
    mov     [ht_klen+r10*8], r9
    mov     rbx, rax
    inc     rbx
    mov     [ht_val+r10*8], rbx
    push    rcx
    push    rsi
    imul    rdi, rax, VAR_NL
    lea     rdi, [var_store+rdi]
    mov     rsi, r8
    mov     rcx, r9
    rep movsb
    mov     byte [rdi], 0
    pop     rsi
    pop     rcx
    inc     qword [ht_cnt]
.done:
    pop     rdi
    pop     r10
    pop     r9
    pop     r8
    pop     rbx
    ret

; local symbol table
lsym_lookup:
    push    rbx
    push    r8
    push    r9
    push    r10
    mov     r8, rsi
    mov     r9, rcx
    call    fnv1a
    and     rax, HT_MASK
    mov     r10, rax
.probe:
    mov     rbx, [lht_val+r10*8]
    test    rbx, rbx
    jz      .nf
    cmp     [lht_klen+r10*8], r9
    jne     .nx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r8
    mov     rdi, [lht_key+r10*8]
    mov     rcx, r9
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .nx
    mov     rax, rbx
    jmp     .done
.nx:
    inc     r10
    and     r10, HT_MASK
    jmp     .probe
.nf:
    mov     rax, -1
.done:
    pop     r10
    pop     r9
    pop     r8
    pop     rbx
    ret

lsym_insert:
    push    rbx
    push    r8
    push    r9
    push    r10
    mov     r8, rsi
    mov     r9, rcx
    call    lsym_lookup
    cmp     rax, -1
    jne     .done
    mov     rsi, r8
    mov     rcx, r9
    call    fnv1a
    and     rax, HT_MASK
    mov     r10, rax
    cmp     qword [lht_cnt], MAX_LVARS
    jl      .probe
    mov     rdx, err_lsymovf
    mov     rcx, err_lsymovf_l
    call    symtab_capacity_error
.probe:
    cmp     qword [lht_val+r10*8], 0
    je      .empty
    inc     r10
    and     r10, HT_MASK
    jmp     .probe
.empty:
    mov     rax, [lht_cnt]
    inc     rax
    imul    rbx, rax, 8
    mov     [lht_val+r10*8], rbx
    mov     [lht_key+r10*8], r8
    mov     [lht_klen+r10*8], r9
    mov     [lht_cnt], rax
    mov     rax, rbx
.done:
    pop     r10
    pop     r9
    pop     r8
    pop     rbx
    ret


; Report a user-facing symbol table capacity error at the current token.
; Input: rdx=message pointer, rcx=message length. Does not return.
symtab_capacity_error:
    push    rdx
    push    rcx
    call    tok_cur_line
    mov     rdi, rax
    call    tok_cur_col
    mov     rsi, rax
    pop     rcx
    pop     rdx
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall

; ────────────────────────────────────────────────────────────
;  FUNCTION TABLE
; ────────────────────────────────────────────────────────────
fn_register:
    push    rbx
    push    r12
    push    r13
    push    r14
    push    rdi
    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx
    mov     rax, [fn_cnt]
    cmp     rax, MAX_FN
    jl      .space_ok
    mov     rdx, err_fnovf
    mov     rcx, err_fnovf_l
    call    symtab_capacity_error
.space_ok:
    imul    rbx, rax, VAR_NL
    lea     rbx, [fn_names+rbx]
    mov     rdi, rbx
    mov     rcx, r13
    push    rsi
    mov     rsi, r12
    rep movsb
    mov     byte [rdi], 0
    pop     rsi
    mov     [fn_pcnt+rax*8], r14
    inc     rax
    mov     [fn_cnt], rax
    pop     rdi
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

fn_find:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     r12, rdi
    mov     r13, rsi
    xor     r14, r14
.s:
    cmp     r14, [fn_cnt]
    jge     .nf
    mov     rax, r14
    imul    rax, rax, VAR_NL
    lea     rbx, [fn_names+rax]
    push    rdi
    mov     rdi, rbx
    call    str_len
    pop     rdi
    cmp     rax, r13
    jne     .nx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r12
    mov     rdi, rbx
    mov     rcx, r13
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .nx
    mov     rax, r14
    jmp     .done
.nx:
    inc     r14
    jmp     .s
.nf:
    mov     rax, -1
.done:
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

mod_register:
    push    rbx
    push    r12
    push    r13
    mov     r12, rdi
    mov     r13, rsi
    mov     rax, [mod_cnt]
    cmp     rax, MAX_FN
    jl      .space_ok
    mov     rdx, err_modovf
    mov     rcx, err_modovf_l
    call    symtab_capacity_error
.space_ok:
    imul    rbx, rax, VAR_NL
    lea     rbx, [mod_names+rbx]
    mov     rdi, rbx
    mov     rcx, r13
    push    rsi
    mov     rsi, r12
    rep movsb
    mov     byte [rdi], 0
    pop     rsi
    inc     rax
    mov     [mod_cnt], rax
    pop     r13
    pop     r12
    pop     rbx
    ret

mod_find:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     r12, rdi
    mov     r13, rsi
    xor     r14, r14
.s:
    cmp     r14, [mod_cnt]
    jge     .nf
    mov     rax, r14
    imul    rax, rax, VAR_NL
    lea     rbx, [mod_names+rax]
    push    rdi
    mov     rdi, rbx
    call    str_len
    pop     rdi
    cmp     rax, r13
    jne     .nx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r12
    mov     rdi, rbx
    mov     rcx, r13
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .nx
    mov     rax, r14
    jmp     .done
.nx:
    inc     r14
    jmp     .s
.nf:
    mov     rax, -1
.done:
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

fn_param_find:
    push    rbx
    push    r12
    push    r13
    push    r14
    mov     r12, rdi
    mov     r13, rsi
    xor     r14, r14
    mov     rbx, [fn_pcur]
.s:
    cmp     r14, rbx
    jge     .nf
    mov     rax, r14
    imul    rax, rax, VAR_NL
    lea     rax, [fn_pnames+rax]
    cmp     [fn_plens+r14*8], r13
    jne     .nx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r12
    mov     rdi, rax
    mov     rcx, r13
    repe cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jnz     .nx
    mov     rax, r14
    jmp     .done
.nx:
    inc     r14
    jmp     .s
.nf:
    mov     rax, -1
.done:
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    ret

; var_exists: rsi=ptr, rcx=len → rax=1 if variable exists, 0 if not
; Checks: params (if in_fn), locals (if in_fn), globals.
; r12=saved_ptr, r13=saved_len throughout; rsi/rcx re-loaded before each call.
var_exists:
    push    r12
    push    r13
    push    r14
    push    r15
    mov     r12, rsi            ; save ptr
    mov     r13, rcx            ; save len
    cmp     qword [in_fn], 1
    jne     .chk_global
    ; check locals
    push    rsi
    push    rcx
    call    lsym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    jne     .found
    ; check params (loop)
    xor     r14, r14
.plp:
    cmp     r14, [fn_pcur]
    jge     .chk_global
    mov     rax, r14
    imul    rax, rax, VAR_NL
    lea     r15, [fn_pnames+rax]
    mov     rax, [fn_plens+r14*8]
    cmp     rax, r13            ; compare param len vs saved len
    jne     .pnx
    push    rsi
    push    rdi
    push    rcx
    mov     rsi, r12            ; reload saved ptr
    mov     rdi, r15
    mov     rcx, r13            ; reload saved len
    repe    cmpsb
    pop     rcx
    pop     rdi
    pop     rsi
    jz      .found
.pnx:
    inc     r14
    jmp     .plp
.chk_global:
    push    rsi
    push    rcx
    mov     rsi, r12            ; reload saved ptr
    mov     rcx, r13            ; reload saved len
    call    sym_lookup
    pop     rcx
    pop     rsi
    cmp     rax, -1
    je      .not_found
.found:
    mov     rax, 1
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret
.not_found:
    xor     rax, rax
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

; ════════════════════════════════════════════════════════════
;  IR EMIT HELPERS
; ════════════════════════════════════════════════════════════
