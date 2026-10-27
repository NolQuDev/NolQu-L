lexer_run:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    lea     r12, [src_buf]
    mov     rax, [src_len]
    lea     r13, [src_buf+rax]
    xor     r14, r14
    mov     r15, 1
    lea     rbx, [src_buf]

lx_top:
    cmp     r14, TOK_MAX-1
    jge     lx_tok_ovf
    cmp     r12, r13
    jge     lx_eof
    movzx   rax, byte [r12]
    jmp     qword [lex_jt + rax*8]

lx_skip:
    inc     r12
    jmp     lx_top

lx_bad_char:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, em_invalid_char
    mov     rcx, em_invalid_char_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall

lx_newline:
    mov     qword [tok_type+r14*8], TOK_NEWLINE
    mov     [tok_ptr+r14*8], r12
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    mov     rax, r12
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    inc     r14
    inc     r12
    inc     r15
    mov     rbx, r12
    jmp     lx_top

lx_comment:
    inc     r12
.c: cmp     r12, r13
    jge     lx_top
    cmp     byte [r12], 10
    je      lx_top
    inc     r12
    jmp     .c

lx_string:
    inc     r12
    mov     rax, r12
    mov     rcx, r12
    sub     rcx, rbx
    mov     [tok_col+r14*8], rcx
    mov     [tok_line+r14*8], r15
.ss:
    cmp     r12, r13
    jge     .unterminated
    movzx   rcx, byte [r12]
    cmp     rcx, 0x22       ; closing "
    je      .sd
    cmp     rcx, 10         ; unescaped newline — unterminated
    je      .unterminated
    cmp     rcx, 0x5c       ; backslash: peek next byte
    jne     .ss_adv
    lea     rcx, [r12+1]
    cmp     rcx, r13
    jge     .ss_adv         ; lone \ at EOF
    movzx   rcx, byte [r12+1]
    cmp     rcx, 0x22       ; \" — skip both, don't terminate
    je      .ss_skip2
    cmp     rcx, 0x5c       ; \\ — skip both (escaped backslash)
    jne     .ss_adv
.ss_skip2:
    add     r12, 2
    jmp     .ss
.ss_adv:
    inc     r12
    jmp     .ss
.unterminated:
    mov     rdi, [tok_line+r14*8]
    mov     rsi, [tok_col+r14*8]
    dec     rsi
    mov     rdx, err_unterm_str
    mov     rcx, err_unterm_str_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.sd:
    mov     qword [tok_type+r14*8], TOK_STRING
    mov     [tok_ptr+r14*8], rax
    push    rax
    mov     rax, r12
    pop     rcx
    sub     rax, rcx
    mov     [tok_len+r14*8], rax
    inc     r14
    cmp     byte [r12], 0x22
    jne     lx_top
    inc     r12
    jmp     lx_top

lx_dot:
    inc     r12
    cmp     r12, r13
    jge     .sd
    cmp     byte [r12], '.'
    jne     .sd
    mov     qword [tok_type+r14*8], TOK_DOTDOT
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
.sd:
    mov     qword [tok_type+r14*8], TOK_DOT
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    inc     r14
    jmp     lx_top

%macro LTOK 1
    mov     rax, r12
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_type+r14*8], %1
    mov     [tok_ptr+r14*8], r12
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
%endmacro

%macro LDTOK 3
    inc     r12
    cmp     r12, r13
    jge     %%s
    cmp     byte [r12], %3
    jne     %%s
    mov     qword [tok_type+r14*8], %2
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
%%s:
    mov     qword [tok_type+r14*8], %1
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    inc     r14
    jmp     lx_top
%endmacro

lx_plus:   LDTOK TOK_PLUS,    TOK_PLUSEQ,    '='
lx_minus:  LDTOK TOK_MINUS,   TOK_MINUSEQ,   '='
lx_star:   LDTOK TOK_STAR,    TOK_STAREQ,    '='
lx_slash:
    inc     r12
    cmp     r12, r13
    jge     .single
    cmp     byte [r12], '/'
    je      .line_comment
    cmp     byte [r12], '*'
    je      .block_comment
    cmp     byte [r12], '='
    je      .assign
.single:
    mov     qword [tok_type+r14*8], TOK_SLASH
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    inc     r14
    jmp     lx_top
.assign:
    mov     qword [tok_type+r14*8], TOK_SLASHEQ
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
.line_comment:
    inc     r12
.lc:
    cmp     r12, r13
    jge     lx_top
    cmp     byte [r12], 10
    je      lx_top
    inc     r12
    jmp     .lc
.block_comment:
    mov     r8, r15
    lea     r9, [r12-1]
    sub     r9, rbx
    inc     r12
.bc:
    cmp     r12, r13
    jge     .unterminated_block_comment
    cmp     byte [r12], 10
    je      .bc_newline
    cmp     byte [r12], '*'
    jne     .bc_advance
    lea     rax, [r12+1]
    cmp     rax, r13
    jge     .bc_advance
    cmp     byte [r12+1], '/'
    jne     .bc_advance
    add     r12, 2
    jmp     lx_top
.bc_newline:
    inc     r12
    inc     r15
    mov     rbx, r12
    jmp     .bc
.bc_advance:
    inc     r12
    jmp     .bc
.unterminated_block_comment:
    mov     rdi, r8
    mov     rsi, r9
    mov     rdx, err_unterm_block
    mov     rcx, err_unterm_block_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
lx_pct:    LDTOK TOK_PERCENT, TOK_PERCENTEQ, '='
lx_amp:    LTOK TOK_AMP
lx_pipe:   LTOK TOK_PIPE
lx_caret:  LTOK TOK_CARET
lx_tilde:  LTOK TOK_TILDE
lx_lbrace: LTOK TOK_LBRACE
lx_rbrace: LTOK TOK_RBRACE
lx_lp:     LTOK TOK_LPAREN
lx_rp:     LTOK TOK_RPAREN
lx_comma:  LTOK TOK_COMMA
lx_lbk:    LTOK TOK_LBRACKET
lx_rbk:    LTOK TOK_RBRACKET

lx_eq:  LDTOK TOK_EQ,  TOK_EQEQ, '='

lx_gt:
    inc     r12
    cmp     r12, r13
    jge     .sd_gt
    cmp     byte [r12], '='
    je      .gte
    cmp     byte [r12], '>'
    je      .rshift
.sd_gt:
    mov     qword [tok_type+r14*8], TOK_GT
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    inc     r14
    jmp     lx_top
.gte:
    mov     qword [tok_type+r14*8], TOK_GTE
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
.rshift:
    mov     qword [tok_type+r14*8], TOK_RSHIFT
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top

lx_lt:
    inc     r12
    cmp     r12, r13
    jge     .sd_lt
    cmp     byte [r12], '='
    je      .lte
    cmp     byte [r12], '<'
    je      .lshift
.sd_lt:
    mov     qword [tok_type+r14*8], TOK_LT
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 1
    mov     [tok_line+r14*8], r15
    inc     r14
    jmp     lx_top
.lte:
    mov     qword [tok_type+r14*8], TOK_LTE
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
.lshift:
    mov     qword [tok_type+r14*8], TOK_LSHIFT
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top

lx_bang:
    inc     r12
    cmp     r12, r13
    jge     .bad
    cmp     byte [r12], '='
    jne     .bad
    mov     qword [tok_type+r14*8], TOK_NEQ
    lea     rax, [r12-1]
    mov     [tok_ptr+r14*8], rax
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     qword [tok_len+r14*8], 2
    mov     [tok_line+r14*8], r15
    inc     r14
    inc     r12
    jmp     lx_top
.bad:
    dec     r12
    jmp     lx_bad_char

lx_digit:
    mov     rax, r12
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     [tok_line+r14*8], r15
    mov     rax, r12
    cmp     byte [r12], '0'
    jne     .nl
    lea     rcx, [r12+1]
    cmp     rcx, r13
    jge     .nl
    cmp     byte [r12+1], 'x'
    je      .hex_prefix
    cmp     byte [r12+1], 'X'
    je      .hex_prefix
    cmp     byte [r12+1], 'b'
    je      .bin_prefix
    cmp     byte [r12+1], 'B'
    je      .bin_prefix
.nl:
    cmp     r12, r13
    jge     .nd
    movzx   rcx, byte [r12]
    sub     rcx, '0'
    cmp     rcx, 9
    jbe     .dec_advance
    movzx   rcx, byte [r12]
    cmp     rcx, '_'
    je      .dec_sep
    jmp     .nd
.dec_advance:
    inc     r12
    jmp     .nl
.dec_sep:
    lea     rdx, [r12+1]
    cmp     rdx, r13
    jge     .num_sep_bad
    movzx   rcx, byte [r12+1]
    sub     rcx, '0'
    cmp     rcx, 9
    ja      .num_sep_bad
    add     r12, 2
    jmp     .nl
.hex_prefix:
    add     r12, 2
    cmp     r12, r13
    jge     .hex_empty
    mov     rdx, r12
.hex_loop:
    cmp     r12, r13
    jge     .hex_done
    movzx   rcx, byte [r12]
    cmp     rcx, '0'
    jb      .hex_maybe_end
    cmp     rcx, '9'
    jbe     .hex_advance
    cmp     rcx, 'A'
    jb      .hex_maybe_end
    cmp     rcx, 'F'
    jbe     .hex_advance
    cmp     rcx, 'a'
    jb      .hex_maybe_end
    cmp     rcx, 'f'
    jbe     .hex_advance
.hex_maybe_end:
    cmp     rcx, '_'
    je      .hex_sep
    cmp     r12, rdx
    je      .hex_empty
    cmp     rcx, 'A'
    jb      .hex_done
    cmp     rcx, 'Z'
    jbe     .hex_bad_digit
    cmp     rcx, 'a'
    jb      .hex_done
    cmp     rcx, 'z'
    jbe     .hex_bad_digit
    jmp     .hex_done
.hex_sep:
    cmp     r12, rdx
    je      .num_sep_bad
    lea     r8, [r12+1]
    cmp     r8, r13
    jge     .num_sep_bad
    movzx   r8, byte [r12+1]
    cmp     r8, '0'
    jb      .num_sep_bad
    cmp     r8, '9'
    jbe     .hex_sep_ok
    cmp     r8, 'A'
    jb      .num_sep_bad
    cmp     r8, 'F'
    jbe     .hex_sep_ok
    cmp     r8, 'a'
    jb      .num_sep_bad
    cmp     r8, 'f'
    ja      .num_sep_bad
.hex_sep_ok:
    add     r12, 2
    jmp     .hex_loop
.hex_advance:
    inc     r12
    jmp     .hex_loop
.hex_done:
    jmp     .nd
.hex_empty:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, err_hex_empty
    mov     rcx, err_hex_empty_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.hex_bad_digit:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, err_hex_digit
    mov     rcx, err_hex_digit_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.bin_prefix:
    add     r12, 2
    cmp     r12, r13
    jge     .bin_empty
    mov     rdx, r12
.bin_loop:
    cmp     r12, r13
    jge     .bin_done
    movzx   rcx, byte [r12]
    cmp     rcx, '0'
    je      .bin_advance
    cmp     rcx, '1'
    je      .bin_advance
    cmp     rcx, '_'
    je      .bin_sep
    cmp     rcx, '0'
    jb      .bin_maybe_empty
    cmp     rcx, '9'
    jbe     .bin_bad_digit
    cmp     rcx, 'A'
    jb      .bin_maybe_empty
    cmp     rcx, 'Z'
    jbe     .bin_bad_digit
    cmp     rcx, 'a'
    jb      .bin_maybe_empty
    cmp     rcx, 'z'
    jbe     .bin_bad_digit
.bin_maybe_empty:
    cmp     r12, rdx
    je      .bin_empty
    jmp     .bin_done
.bin_sep:
    cmp     r12, rdx
    je      .num_sep_bad
    lea     r8, [r12+1]
    cmp     r8, r13
    jge     .num_sep_bad
    cmp     byte [r12+1], '0'
    je      .bin_sep_ok
    cmp     byte [r12+1], '1'
    jne     .num_sep_bad
.bin_sep_ok:
    add     r12, 2
    jmp     .bin_loop
.bin_advance:
    inc     r12
    jmp     .bin_loop
.bin_done:
    jmp     .nd
.bin_empty:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, err_bin_empty
    mov     rcx, err_bin_empty_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.bin_bad_digit:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, err_bin_digit
    mov     rcx, err_bin_digit_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.num_sep_bad:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, err_num_sep
    mov     rcx, err_num_sep_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.nd:
    mov     qword [tok_type+r14*8], TOK_INT
    mov     [tok_ptr+r14*8], rax
    push    rax
    mov     rax, r12
    pop     rcx
    sub     rax, rcx
    mov     [tok_len+r14*8], rax
    inc     r14
    jmp     lx_top

lx_ident:
    mov     rax, r12
    sub     rax, rbx
    mov     [tok_col+r14*8], rax
    mov     [tok_line+r14*8], r15
    mov     rax, r12
.il:
    cmp     r12, r13
    jge     .id
    movzx   rcx, byte [r12]
    cmp     cl, '_'
    je      .ic
    cmp     cl, 'a'
    jl      .iu
    cmp     cl, 'z'
    jle     .ic
.iu:
    cmp     cl, 'A'
    jl      .id2
    cmp     cl, 'Z'
    jle     .ic
.id2:
    cmp     cl, '0'
    jl      .id
    cmp     cl, '9'
    jg      .id
.ic:
    inc     r12
    jmp     .il
.id:
    push    rax
    mov     rcx, r12
    pop     rax
    push    rax
    sub     rcx, rax
    cmp     rcx, VAR_NL
    jl      .len_ok
    mov     rdi, [tok_line+r14*8]
    mov     rsi, [tok_col+r14*8]
    mov     rdx, err_namelen
    mov     rcx, err_namelen_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.len_ok:
    push    rcx
    mov     rsi, rax
    call    kw_check
    pop     rcx
    pop     rdx
    test    rax, rax
    jnz     .kw
    mov     qword [tok_type+r14*8], TOK_IDENT
    jmp     .store
.kw:
    mov     [tok_type+r14*8], rax
.store:
    mov     [tok_ptr+r14*8], rdx
    mov     [tok_len+r14*8], rcx
    inc     r14
    jmp     lx_top

lx_eof:
    mov     qword [tok_type+r14*8], TOK_EOF
    mov     [tok_line+r14*8], r15
    inc     r14
    mov     [tok_cnt], r14
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret

lx_tok_ovf:
    mov     rdi, r15
    mov     rsi, r12
    sub     rsi, rbx
    mov     rdx, err_tokovf
    mov     rcx, err_tokovf_l
    call    emit_error
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall

; ────────────────────────────────────────────────────────────
;  STRING LITERAL RECORD → writes to str_buf, returns index
; ────────────────────────────────────────────────────────────
str_record:
    push    r12
    push    r13
    push    r14
    push    rbx
    call    tok_cur_ptr
    mov     r12, rax
    call    tok_cur_len
    mov     r13, rax
    mov     r14, [str_cnt]
    cmp     r14, STR_MAX
    jb      .cap_ok
    mov     rdx, em_strlit_ovf
    mov     rcx, em_strlit_ovf_l
    call    emit_error_tok
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.cap_ok:
    mov     rbx, [cur_emit]
    mov     [str_ptrs + r14*8], r12
    ; str_lens[r14] is set after escape processing below
    mov     qword [cur_emit], 2
    ; emit:  _s_N db <escaped-content>,10
    mov     rsi, f_str_pfx
    mov     rdx, f_str_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_str_db
    mov     rdx, f_str_db_l
    call    emit_bytes
    ; emit content with escape sequences resolved; returns processed_len in rax
    mov     rsi, r12
    mov     rdx, r13
    call    emit_str_escaped
    mov     [str_lens + r14*8], rax     ; store processed (raw) byte count
    call    emit_nl                     ; end the db line
    ; emit:  _s_N_len equ (processed_len+1)
    mov     rsi, f_str_pfx
    mov     rdx, f_str_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_len_sfx
    mov     rdx, f_len_sfx_l
    call    emit_bytes
    mov     rax, [str_lens + r14*8]
    inc     rax                         ; +1 for the display LF emitted by emit_str_escaped
    call    int_to_str
    call    emit_bytes
    call    emit_nl
    mov     [cur_emit], rbx
    inc     qword [str_cnt]
    mov     rax, r14
    pop     rbx
    pop     r14
    pop     r13
    pop     r12
    ret

; ────────────────────────────────────────────────────────────
;  emit_str_escaped  rsi=raw_ptr  rdx=raw_len  →  rax=processed_len
;
;  Emits the string content of a Nolqu string literal as NASM db
;  fragments with escape sequences expanded, then appends ",10"
;  for the display newline that print/println use.
;
;  Supported escapes:  \n→10  \t→9  \r→13  \0→0  \\→92  \"→34
;  Unrecognised escape: both bytes emitted literally.
;
;  Return: number of raw content bytes (not counting the display LF).
;
;  Register conventions across emit_bytes / int_to_str calls:
;    r12 = current source ptr   (int_to_str saves/restores r12)
;    r13 = end ptr              (int_to_str saves/restores r13)
;    r14 = in_quote flag        (neither helper touches r14)
;    r15 = processed_len        (neither helper touches r15)
; ────────────────────────────────────────────────────────────
emit_str_escaped:
    push    r12
    push    r13
    push    r14
    push    r15
    push    rbx
    mov     r12, rsi
    lea     r13, [rsi+rdx]  ; r13 = one past end
    xor     r14, r14        ; in_quote = false
    xor     r15, r15        ; processed_len = 0
.loop:
    cmp     r12, r13
    jge     .end_content
    movzx   rax, byte [r12]
    cmp     al, 0x5c        ; backslash?
    jne     .plain
    ; peek next byte
    lea     rbx, [r12+1]
    cmp     rbx, r13
    jge     .plain          ; lone \ at end — emit literally
    movzx   rbx, byte [r12+1]
    cmp     bl, 'n'
    je      .esc_n
    cmp     bl, 't'
    je      .esc_t
    cmp     bl, 'r'
    je      .esc_r
    cmp     bl, '0'
    je      .esc_0
    cmp     bl, 0x22        ; \"
    je      .esc_dq
    cmp     bl, 0x5c        ; backslash escape
    je      .esc_bs
    ; unrecognised — fall through, emit \ as a plain byte
.plain:
    test    r14, r14
    jnz     .plain_in_q
    ; open a new NASM string segment; emit comma first if not the very first element
    test    r15, r15
    jz      .no_pre_comma
    mov     rsi, .es_comma
    mov     rdx, 1
    call    emit_bytes
.no_pre_comma:
    mov     rsi, f_dq
    mov     rdx, 1
    call    emit_bytes
    mov     r14, 1
.plain_in_q:
    mov     rsi, r12
    mov     rdx, 1
    call    emit_bytes
    inc     r15
    inc     r12
    jmp     .loop
.esc_n:  mov rbx, 10  ; \n
    jmp     .emit_esc_byte
.esc_t:  mov rbx, 9   ; \t
    jmp     .emit_esc_byte
.esc_r:  mov rbx, 13  ; \r
    jmp     .emit_esc_byte
.esc_0:  xor rbx, rbx ; \0
    jmp     .emit_esc_byte
.esc_dq: mov rbx, 0x22
    jmp     .emit_esc_byte
.esc_bs: mov rbx, 0x5c
.emit_esc_byte:
    ; close the open NASM string segment if any
    test    r14, r14
    jz      .esc_no_close
    mov     rsi, f_dq
    mov     rdx, 1
    call    emit_bytes
    xor     r14, r14
.esc_no_close:
    ; emit separator: "," or nothing if first byte in segment
    test    r15, r15
    jnz     .esc_comma
    ; first byte ever emitted — no leading comma needed
    jmp     .esc_emit_val
.esc_comma:
    mov     rsi, .es_comma
    mov     rdx, 1
    call    emit_bytes
.esc_emit_val:
    mov     rax, rbx
    call    int_to_str
    call    emit_bytes
    inc     r15
    add     r12, 2          ; skip \ and the escape char
    jmp     .loop
.end_content:
    ; close open quote segment, then emit display LF
    test    r14, r14
    jnz     .close_then_lf
    ; not in a quote — either empty or ended with escape bytes
    test    r15, r15
    jz      .empty_lf
    ; ended with an escape byte sequence — just append ",10"
    mov     rsi, .es_comma_lf
    mov     rdx, .es_comma_lf_l
    call    emit_bytes
    jmp     .ret
.close_then_lf:
    ; currently inside a quote — close it, then ",10"
    mov     rsi, f_dq
    mov     rdx, 1
    call    emit_bytes
    mov     rsi, .es_comma_lf
    mov     rdx, .es_comma_lf_l
    call    emit_bytes
    jmp     .ret
.empty_lf:
    ; empty string — emit "10" with no leading comma
    mov     rsi, .es_bare_lf
    mov     rdx, .es_bare_lf_l
    call    emit_bytes
.ret:
    mov     rax, r15        ; return processed_len
    pop     rbx
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    ret
.es_comma     db ","
.es_comma_lf  db ",10"
.es_comma_lf_l equ $ - .es_comma_lf
.es_bare_lf   db "10"
.es_bare_lf_l  equ $ - .es_bare_lf

; ════════════════════════════════════════════════════════════
;  PARSER  →  emits IR
