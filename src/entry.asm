rdtsc64:
    xor rax, rax
    ret

align 16
_start:
    call    kw_init
    mov     qword [build_mode], MODE_DEBUG
    mov     qword [opt_on], 0
    mov     qword [check_only], 0
    mov     qword [had_error], 0
    mov     qword [dump_tokens], 0
    mov     qword [dump_ir], 0
    mov     qword [out_fname_ptr], out_fname
    mov     qword [out_fname_len], 16    ; len("build/output.asm")
    mov     rcx, [rsp]
    cmp     rcx, 2
    jl      .bad_usage
    push    r12
    push    r13
    push    r14
    push    r15
    ; After 4 pushes: [rsp+32]=argc, argv[k]=[rsp+40+k*8]
    xor     r12, r12         ; source file ptr (0 = not found)
    mov     r13, 1           ; arg index
    xor     r14, r14         ; 1 = next arg is --emit path
    mov     r15, [rsp+32]    ; argc
.arg_lp:
    cmp     r13, r15
    jge     .args_done
    mov     rdi, [rsp+r13*8+40]
    test    r14, r14
    jnz     .store_emit
    movzx   rax, byte [rdi]
    cmp     al, '-'
    je      .is_flag
    test    r12, r12
    jnz     .bad_extra_arg_pop
    mov     r12, rdi
    jmp     .arg_next
.is_flag:
    call    parse_flag
    cmp     rax, 1
    je      .need_emit_path
    cmp     rax, 2
    je      .bad_flag_pop
    jmp     .arg_next
.need_emit_path:
    mov     r14, 1
    jmp     .arg_next
.store_emit:
    movzx   rax, byte [rdi]
    cmp     al, '-'
    je      .bad_emit_path_pop
    mov     [out_fname_ptr], rdi
    call    str_len
    mov     [out_fname_len], rax
    xor     r14, r14
.arg_next:
    inc     r13
    jmp     .arg_lp
.args_done:
    test    r14, r14
    jnz     .bad_emit_path_pop
    test    r12, r12
    jz      .bad_usage_pop
    mov     rdi, r12
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    call    rdtsc64
    mov     [ts_start], rax
    call    open_file
    cmp     rax, 0
    jl      .bad_open
    mov     rdi, rax
    call    read_file
    cmp     rax, 0
    jl      .bad_open
    call    rdtsc64
    push    rax
    call    lexer_run
    call    rdtsc64
    pop     rcx
    sub     rax, rcx
    mov     [ts_lex], rax
    cmp     qword [dump_tokens], 0
    je      .after_tok_dump
    call    dump_tokens_run
    cmp     qword [dump_ir], 0
    jne     .after_tok_dump
    jmp     .dump_done
.after_tok_dump:
    call    rdtsc64
    push    rax
    call    parser_run
    call    rdtsc64
    pop     rcx
    sub     rax, rcx
    mov     [ts_parse], rax
    cmp     qword [had_error], 0
    jne     .bad_parse
    cmp     qword [check_only], 1
    je      .check_ok
    call    rdtsc64
    push    rax
    cmp     qword [opt_on], 1
    jne     .skip_opt
    call    opt_run
.skip_opt:
    call    rdtsc64
    pop     rcx
    sub     rax, rcx
    mov     [ts_opt], rax
    cmp     qword [dump_ir], 0
    je      .after_ir_dump
    call    dump_ir_run
    jmp     .dump_done
.after_ir_dump:
    call    rdtsc64
    push    rax
    call    cg_run
    cmp     qword [str_cnt], 0
    jne     .need_str_table
    cmp     qword [istr_total], 0
    jne     .need_str_table
    cmp     qword [its_cnt], 0
    jne     .need_str_table
    cmp     qword [str_cat_cnt], 0
    jne     .need_str_table
    cmp     qword [file_read_total], 0
    jne     .need_str_table
    cmp     qword [arg_str_total], 0
    je      .skip_str_table
.need_str_table:
    call    emit_str_table
.skip_str_table:
    call    rdtsc64
    pop     rcx
    sub     rax, rcx
    mov     [ts_cg], rax
    call    write_output
    cmp     rax, 0
    jl      .bad_open
    cmp     qword [build_mode], MODE_BENCH
    jne     .no_bench
    call    print_bench
.no_bench:
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    mov     rsi, msg_ok_pfx
    mov     rdx, msg_ok_pfx_l
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    mov     rsi, [out_fname_ptr]
    mov     rdx, [out_fname_len]
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDOUT
    mov     rsi, msg_ok_sfx
    mov     rdx, msg_ok_sfx_l
    syscall
    mov     rax, SYS_EXIT
    xor     rdi, rdi
    syscall
.dump_done:
    mov     rax, SYS_EXIT
    xor     rdi, rdi
    syscall
.bad_usage_pop:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
.bad_usage:
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, err_usage
    mov     rdx, err_usage_l
    syscall
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.bad_flag_pop:
    mov     r8, rdi
    call    str_len
    mov     r9, rax
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, err_bad_flag
    mov     rdx, err_bad_flag_l
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, r8
    mov     rdx, r9
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, ep_nl
    mov     rdx, 1
    syscall
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.bad_extra_arg_pop:
    mov     r8, rdi
    call    str_len
    mov     r9, rax
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, err_extra_arg
    mov     rdx, err_extra_arg_l
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, r8
    mov     rdx, r9
    syscall
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, ep_nl
    mov     rdx, 1
    syscall
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.bad_emit_path_pop:
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, err_emit_path
    mov     rdx, err_emit_path_l
    syscall
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.bad_open:
    mov     rax, SYS_WRITE
    mov     rdi, STDERR
    mov     rsi, err_open
    mov     rdx, err_open_l
    syscall
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall
.check_ok:
    mov     rax, SYS_EXIT
    xor     rdi, rdi
    syscall
.bad_parse:
    mov     rax, SYS_EXIT
    mov     rdi, 1
    syscall

parse_flag:
    push    rbx
    mov     rbx, rdi
    mov     rsi, s_release
.r:
    mov     al, [rbx]
    mov     cl, [rsi]
    cmp     al, cl
    jne     .try_bench
    test    al, al
    jz      .is_rel
    inc     rbx
    inc     rsi
    jmp     .r
.is_rel:
    mov     qword [build_mode], MODE_RELEASE
    mov     qword [opt_on], 1
    jmp     .done_0
.try_bench:
    mov     rbx, rdi
    mov     rsi, s_bench
.b:
    mov     al, [rbx]
    mov     cl, [rsi]
    cmp     al, cl
    jne     .try_dump_tok
    test    al, al
    jz      .is_bench
    inc     rbx
    inc     rsi
    jmp     .b
.is_bench:
    cmp     qword [build_mode], MODE_RELEASE
    je      .done_0
    mov     qword [build_mode], MODE_BENCH
    jmp     .done_0
.try_dump_tok:
    mov     rbx, rdi
    mov     rsi, s_dump_tok
.dt:
    mov     al, [rbx]
    mov     cl, [rsi]
    cmp     al, cl
    jne     .try_dump_ir
    test    al, al
    jz      .is_dump_tok
    inc     rbx
    inc     rsi
    jmp     .dt
.is_dump_tok:
    mov     qword [dump_tokens], 1
    jmp     .done_0
.try_dump_ir:
    mov     rbx, rdi
    mov     rsi, s_dump_ir
.di:
    mov     al, [rbx]
    mov     cl, [rsi]
    cmp     al, cl
    jne     .try_check
    test    al, al
    jz      .is_dump_ir
    inc     rbx
    inc     rsi
    jmp     .di
.is_dump_ir:
    mov     qword [dump_ir], 1
    jmp     .done_0
.try_check:
    mov     rbx, rdi
    mov     rsi, s_check
.ck:
    mov     al, [rbx]
    mov     cl, [rsi]
    cmp     al, cl
    jne     .try_emit
    test    al, al
    jz      .is_check
    inc     rbx
    inc     rsi
    jmp     .ck
.is_check:
    mov     qword [check_only], 1
    jmp     .done_0
.try_emit:
    mov     rbx, rdi
    mov     rsi, s_emit
.em:
    mov     al, [rbx]
    mov     cl, [rsi]
    cmp     al, cl
    jne     .unknown_flag
    test    al, al
    jz      .is_emit
    inc     rbx
    inc     rsi
    jmp     .em
.is_emit:
    mov     rax, 1    ; signal: next arg is --emit path
    pop     rbx
    ret
.done_0:
    xor     rax, rax
    pop     rbx
    ret
.unknown_flag:
    mov     rax, 2
    pop     rbx
    ret

; emit_str_table — appends _str_ptrs/_str_lens tables to str_buf
; Called after cg_run when str_cnt > 0
emit_str_table:
    push    r12
    push    r13
    push    r14
    push    rbx
    mov     rbx, [cur_emit]
    mov     qword [cur_emit], 2
    mov     r13, [str_cnt]
    ; Emit named BSS buffers for istr/ITS/strcat slots before _str_ptrs table
    cmp     qword [istr_total], 0
    jne     .need_dyn_bss
    cmp     qword [its_cnt], 0
    jne     .need_dyn_bss
    cmp     qword [str_cat_cnt], 0
    jne     .need_dyn_bss
    cmp     qword [file_read_total], 0
    jne     .need_dyn_bss
    cmp     qword [arg_str_total], 0
    je      .skip_dyn_bss
.need_dyn_bss:
    mov     rsi, f_its_bss_hdr      ; "section .bss\n"
    mov     rdx, f_its_bss_hdr_l
    call    emit_bytes
    cmp     qword [istr_total], 0
    je      .skip_istr_bss
    xor     r14, r14
.istr_bss_loop:
    mov     rsi, f_istr_buf_pfx     ; "_nq_istr_buf_"
    mov     rdx, f_istr_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_istr_buf_sfx     ; " resb 256\n"
    mov     rdx, f_istr_buf_sfx_l
    call    emit_bytes
    inc     r14
    cmp     r14, [istr_total]
    jl      .istr_bss_loop
.skip_istr_bss:
    cmp     qword [its_cnt], 0
    je      .skip_its_bss
    xor     r14, r14
.its_bss_loop:
    mov     rsi, f_its_buf_pfx      ; "_nq_its_buf_"
    mov     rdx, f_its_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_its_buf_sfx      ; " resb 32\n"
    mov     rdx, f_its_buf_sfx_l
    call    emit_bytes
    inc     r14
    cmp     r14, [its_cnt]
    jl      .its_bss_loop
.skip_its_bss:
    cmp     qword [str_cat_cnt], 0
    je      .skip_scat_bss
    xor     r14, r14
.scat_bss_loop:
    mov     rsi, f_scat_buf_pfx     ; "_nq_strcat_buf_"
    mov     rdx, f_scat_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_scat_buf_sfx     ; " resb 4096\n"
    mov     rdx, f_scat_buf_sfx_l
    call    emit_bytes
    inc     r14
    cmp     r14, [str_cat_cnt]
    jl      .scat_bss_loop
.skip_scat_bss:
    cmp     qword [file_read_total], 0
    je      .skip_file_bss
    xor     r14, r14
.file_bss_loop:
    mov     rsi, f_read_file_buf_pfx
    mov     rdx, f_read_file_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_read_file_buf_sfx
    mov     rdx, f_read_file_buf_sfx_l
    call    emit_bytes
    inc     r14
    cmp     r14, [file_read_total]
    jl      .file_bss_loop
.skip_file_bss:
    cmp     qword [arg_str_total], 0
    je      .skip_arg_bss
    xor     r14, r14
.arg_bss_loop:
    mov     rsi, f_arg_str_buf_pfx
    mov     rdx, f_arg_str_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    mov     rsi, f_arg_str_buf_sfx
    mov     rdx, f_arg_str_buf_sfx_l
    call    emit_bytes
    inc     r14
    cmp     r14, [arg_str_total]
    jl      .arg_bss_loop
.skip_arg_bss:
    mov     rsi, f_its_sec_dat      ; "section .data\n"
    mov     rdx, f_its_sec_dat_l
    call    emit_bytes
.skip_dyn_bss:
    ; emit "align 8\n_str_ptrs dq "
    mov     rsi, .tbl_hdr
    mov     rdx, .tbl_hdr_l
    call    emit_bytes
    ; emit each pointer entry: "_s_0, _s_1, ..." or "_s_0" for single
    xor     r12, r12
.ptrs:
    cmp     r12, r13
    je      .ptrs_done
    mov     rsi, f_str_pfx      ; "_s_"
    mov     rdx, f_str_pfx_l
    call    emit_bytes
    mov     rax, r12
    call    int_to_str
    call    emit_bytes
    lea     rax, [r12+1]
    cmp     rax, r13
    je      .ptr_last
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.ptr_last:
    inc     r12
    jmp     .ptrs
.ptrs_done:
    cmp     qword [istr_total], 0
    je      .ptrs_its_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .ptrs_istr_loop
    jmp     .ptrs_istr_name
.ptrs_istr_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.ptrs_istr_name:
    mov     rsi, f_istr_buf_pfx
    mov     rdx, f_istr_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [istr_total]
    jl      .ptrs_istr_loop
.ptrs_its_chk:
    cmp     qword [its_cnt], 0
    je      .ptrs_scat_chk
    ; First ITS entry needs comma only if prior entries exist
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .ptrs_its_loop
    cmp     qword [istr_total], 0
    jne     .ptrs_its_loop
    jmp     .ptrs_its_name
.ptrs_its_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.ptrs_its_name:
    mov     rsi, f_its_buf_pfx
    mov     rdx, f_its_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [its_cnt]
    jl      .ptrs_its_loop
.ptrs_scat_chk:
    cmp     qword [str_cat_cnt], 0
    je      .ptrs_file_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .ptrs_scat_loop
    cmp     qword [istr_total], 0
    jne     .ptrs_scat_loop
    cmp     qword [its_cnt], 0
    jne     .ptrs_scat_loop
    jmp     .ptrs_scat_name
.ptrs_scat_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.ptrs_scat_name:
    mov     rsi, f_scat_buf_pfx
    mov     rdx, f_scat_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [str_cat_cnt]
    jl      .ptrs_scat_loop
.ptrs_file_chk:
    cmp     qword [file_read_total], 0
    je      .ptrs_arg_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .ptrs_file_loop
    cmp     qword [istr_total], 0
    jne     .ptrs_file_loop
    cmp     qword [its_cnt], 0
    jne     .ptrs_file_loop
    cmp     qword [str_cat_cnt], 0
    jne     .ptrs_file_loop
    jmp     .ptrs_file_name
.ptrs_file_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.ptrs_file_name:
    mov     rsi, f_read_file_buf_pfx
    mov     rdx, f_read_file_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [file_read_total]
    jl      .ptrs_file_loop
.ptrs_arg_chk:
    cmp     qword [arg_str_total], 0
    je      .ptrs_nl
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .ptrs_arg_loop
    cmp     qword [istr_total], 0
    jne     .ptrs_arg_loop
    cmp     qword [its_cnt], 0
    jne     .ptrs_arg_loop
    cmp     qword [str_cat_cnt], 0
    jne     .ptrs_arg_loop
    cmp     qword [file_read_total], 0
    jne     .ptrs_arg_loop
    jmp     .ptrs_arg_name
.ptrs_arg_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.ptrs_arg_name:
    mov     rsi, f_arg_str_buf_pfx
    mov     rdx, f_arg_str_buf_pfx_l
    call    emit_bytes
    mov     rax, r14
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [arg_str_total]
    jl      .ptrs_arg_loop
.ptrs_nl:
    call    emit_nl
    ; emit "_str_lens dq "
    mov     rsi, .len_hdr
    mov     rdx, .len_hdr_l
    call    emit_bytes
    xor     r12, r12
.lens:
    cmp     r12, r13
    je      .lens_done
    mov     rsi, f_str_pfx      ; "_s_"
    mov     rdx, f_str_pfx_l
    call    emit_bytes
    mov     rax, r12
    call    int_to_str
    call    emit_bytes
    mov     rsi, .lensfx        ; "_len"
    mov     rdx, .lensfx_l
    call    emit_bytes
    lea     rax, [r12+1]
    cmp     rax, r13
    je      .len_last
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.len_last:
    inc     r12
    jmp     .lens
.lens_done:
    cmp     qword [istr_total], 0
    je      .lens_its_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .lens_istr_loop
    jmp     .lens_istr_val
.lens_istr_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.lens_istr_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [istr_total]
    jl      .lens_istr_loop
.lens_its_chk:
    cmp     qword [its_cnt], 0
    je      .lens_scat_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .lens_its_loop
    cmp     qword [istr_total], 0
    jne     .lens_its_loop
    jmp     .lens_its_val
.lens_its_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.lens_its_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [its_cnt]
    jl      .lens_its_loop
.lens_scat_chk:
    cmp     qword [str_cat_cnt], 0
    je      .lens_file_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .lens_scat_loop
    cmp     qword [istr_total], 0
    jne     .lens_scat_loop
    cmp     qword [its_cnt], 0
    jne     .lens_scat_loop
    jmp     .lens_scat_val
.lens_scat_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.lens_scat_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [str_cat_cnt]
    jl      .lens_scat_loop
.lens_file_chk:
    cmp     qword [file_read_total], 0
    je      .lens_arg_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .lens_file_loop
    cmp     qword [istr_total], 0
    jne     .lens_file_loop
    cmp     qword [its_cnt], 0
    jne     .lens_file_loop
    cmp     qword [str_cat_cnt], 0
    jne     .lens_file_loop
    jmp     .lens_file_val
.lens_file_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.lens_file_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [file_read_total]
    jl      .lens_file_loop
.lens_arg_chk:
    cmp     qword [arg_str_total], 0
    je      .lens_nl
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .lens_arg_loop
    cmp     qword [istr_total], 0
    jne     .lens_arg_loop
    cmp     qword [its_cnt], 0
    jne     .lens_arg_loop
    cmp     qword [str_cat_cnt], 0
    jne     .lens_arg_loop
    cmp     qword [file_read_total], 0
    jne     .lens_arg_loop
    jmp     .lens_arg_val
.lens_arg_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.lens_arg_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [arg_str_total]
    jl      .lens_arg_loop
.lens_nl:
    call    emit_nl
    ; emit "_str_raw_lens dq <raw0>, <raw1>, ..."
    mov     rsi, .raw_hdr
    mov     rdx, .raw_hdr_l
    call    emit_bytes
    xor     r12, r12
.raw:
    cmp     r12, r13
    je      .raw_done
    mov     rax, [str_lens + r12*8]
    call    int_to_str
    call    emit_bytes
    lea     rax, [r12+1]
    cmp     rax, r13
    je      .raw_last
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.raw_last:
    inc     r12
    jmp     .raw
.raw_done:
    cmp     qword [istr_total], 0
    je      .raw_its_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .raw_istr_loop
    jmp     .raw_istr_val
.raw_istr_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.raw_istr_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [istr_total]
    jl      .raw_istr_loop
.raw_its_chk:
    cmp     qword [its_cnt], 0
    je      .raw_scat_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .raw_its_loop
    cmp     qword [istr_total], 0
    jne     .raw_its_loop
    jmp     .raw_its_val
.raw_its_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.raw_its_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [its_cnt]
    jl      .raw_its_loop
.raw_scat_chk:
    cmp     qword [str_cat_cnt], 0
    je      .raw_file_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .raw_scat_loop
    cmp     qword [istr_total], 0
    jne     .raw_scat_loop
    cmp     qword [its_cnt], 0
    jne     .raw_scat_loop
    jmp     .raw_scat_val
.raw_scat_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.raw_scat_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [str_cat_cnt]
    jl      .raw_scat_loop
.raw_file_chk:
    cmp     qword [file_read_total], 0
    je      .raw_arg_chk
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .raw_file_loop
    cmp     qword [istr_total], 0
    jne     .raw_file_loop
    cmp     qword [its_cnt], 0
    jne     .raw_file_loop
    cmp     qword [str_cat_cnt], 0
    jne     .raw_file_loop
    jmp     .raw_file_val
.raw_file_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.raw_file_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [file_read_total]
    jl      .raw_file_loop
.raw_arg_chk:
    cmp     qword [arg_str_total], 0
    je      .raw_nl
    xor     r14, r14
    mov     rax, r13
    test    rax, rax
    jnz     .raw_arg_loop
    cmp     qword [istr_total], 0
    jne     .raw_arg_loop
    cmp     qword [its_cnt], 0
    jne     .raw_arg_loop
    cmp     qword [str_cat_cnt], 0
    jne     .raw_arg_loop
    cmp     qword [file_read_total], 0
    jne     .raw_arg_loop
    jmp     .raw_arg_val
.raw_arg_loop:
    mov     rsi, .comma
    mov     rdx, .comma_l
    call    emit_bytes
.raw_arg_val:
    xor     rax, rax
    call    int_to_str
    call    emit_bytes
    inc     r14
    cmp     r14, [arg_str_total]
    jl      .raw_arg_loop
.raw_nl:
    call    emit_nl
    mov     [cur_emit], rbx
    pop     rbx
    pop     r14
    pop     r13
    pop     r12
    ret
.tbl_hdr   db "align 8", 10, "_str_ptrs dq "
.tbl_hdr_l equ $ - .tbl_hdr
.len_hdr   db "_str_lens dq "
.len_hdr_l equ $ - .len_hdr
.raw_hdr   db "_str_raw_lens dq "
.raw_hdr_l equ $ - .raw_hdr
.lensfx    db "_len"
.lensfx_l  equ $ - .lensfx
.comma     db ", "
.comma_l   equ $ - .comma

open_file:
    mov     rax, SYS_OPEN
    mov     rsi, O_RDONLY
    xor     rdx, rdx
    syscall
    ret

read_file:
    push    rdi
    xor     r8, r8
.lp:
    mov     rax, SRC_SIZE-1
    sub     rax, r8
    jz      .too_big
    mov     rdx, rax
    mov     rax, SYS_READ
    mov     rdi, [rsp]
    lea     rsi, [src_buf+r8]
    syscall
    cmp     rax, 0
    jl      .fail
    je      .done
    add     r8, rax
    cmp     r8, SRC_SIZE-1
    jae     .too_big
    jmp     .lp
.done:
    mov     [src_len], r8
    lea     rcx, [src_buf+r8]
    mov     byte [rcx], 0
    pop     rdi
    push    r8
    mov     rax, SYS_CLOSE
    syscall
    pop     rax
    ret
.too_big:
    mov     rsi, err_srcbig
    mov     rdx, err_srcbig_l
    call    fatal_stderr
.fail:
    push    rax
    mov     rax, SYS_CLOSE
    mov     rdi, [rsp+8]
    syscall
    pop     rax
    pop     rdi
    ret

write_output:
    push    r15
    mov     rax, SYS_OPEN
    mov     rdi, [out_fname_ptr]
    mov     rsi, O_WRONLY|O_CREAT|O_TRUNC
    mov     rdx, 0o644
    syscall
    cmp     rax, 0
    jl      .fail
    mov     r15, rax
    mov     rsi, asm_hdr_data
    mov     rdx, asm_hdr_dl
    call    wchunk
    mov     rsi, str_buf
    mov     rdx, [str_pos]
    call    wchunk
    mov     rsi, asm_hdr_bss
    mov     rdx, asm_hdr_bl
    call    wchunk
    mov     rsi, asm_pi
    mov     rdx, asm_pi_l
    call    wchunk
    mov     rsi, asm_an
    mov     rdx, asm_an_l
    call    wchunk
    mov     rsi, asm_ao
    mov     rdx, asm_ao_l
    call    wchunk
    mov     rsi, asm_ap
    mov     rdx, asm_ap_l
    call    wchunk
    mov     rsi, asm_app
    mov     rdx, asm_app_l
    call    wchunk
    mov     rsi, asm_dz
    mov     rdx, asm_dz_l
    call    wchunk
    mov     rsi, asm_io
    mov     rdx, asm_io_l
    call    wchunk
    mov     rsi, asm_so
    mov     rdx, asm_so_l
    call    wchunk
    mov     rsi, asm_atoi
    mov     rdx, asm_atoi_l
    call    wchunk
    mov     rsi, asm_arg
    mov     rdx, asm_arg_l
    call    wchunk
    mov     rsi, asm_input_int
    mov     rdx, asm_input_int_l
    call    wchunk
    cmp     qword [str_cnt], 0
    jne     .need_str_eq
    cmp     qword [istr_total], 0
    jne     .need_str_eq
    cmp     qword [its_cnt], 0
    jne     .need_str_eq
    cmp     qword [file_read_total], 0
    jne     .need_str_eq
    cmp     qword [arg_str_total], 0
    je      .no_str_eq
.need_str_eq:
    mov     rsi, asm_str_eq
    mov     rdx, asm_str_eq_l
    call    wchunk
    cmp     qword [istr_total], 0
    je      .no_input_str
    mov     rsi, asm_input_str
    mov     rdx, asm_input_str_l
    call    wchunk
.no_input_str:
.no_str_eq:
    cmp     qword [str_find_total], 0
    je      .no_str_find
    mov     rsi, asm_str_find
    mov     rdx, asm_str_find_l
    call    wchunk
.no_str_find:
    cmp     qword [str_slice_total], 0
    je      .no_str_slice
    mov     rsi, asm_str_slice
    mov     rdx, asm_str_slice_l
    call    wchunk
.no_str_slice:
    cmp     qword [its_cnt], 0
    je      .no_its_str
    mov     rsi, asm_int_to_str
    mov     rdx, asm_int_to_str_l
    call    wchunk
.no_its_str:
    cmp     qword [str_cat_cnt], 0
    je      .no_str_cat
    mov     rsi, asm_str_concat
    mov     rdx, asm_str_concat_l
    call    wchunk
.no_str_cat:
    cmp     qword [file_read_total], 0
    je      .no_read_file
    mov     rsi, asm_read_file
    mov     rdx, asm_read_file_l
    call    wchunk
.no_read_file:
    cmp     qword [arg_str_total], 0
    je      .no_arg_str
    mov     rsi, asm_arg_str
    mov     rdx, asm_arg_str_l
    call    wchunk
.no_arg_str:
    cmp     qword [write_file_total], 0
    je      .no_write_file
    mov     rsi, asm_write_file
    mov     rdx, asm_write_file_l
    call    wchunk
.no_write_file:
    cmp     qword [append_file_total], 0
    je      .no_append_file
    mov     rsi, asm_append_file
    mov     rdx, asm_append_file_l
    call    wchunk
.no_append_file:
    mov     rsi, fn_buf
    mov     rdx, [fn_pos]
    call    wchunk
    mov     rsi, asm_slbl
    mov     rdx, asm_slbl_l
    call    wchunk
    mov     rsi, asm_start_save
    mov     rdx, asm_start_save_l
    call    wchunk
    mov     rsi, out_buf
    mov     rdx, [out_pos]
    call    wchunk
    mov     rsi, asm_footer
    mov     rdx, asm_footer_l
    call    wchunk
    mov     rax, SYS_CLOSE
    mov     rdi, r15
    syscall
    mov     rax, 1
    pop     r15
    ret
.fail:
    mov     rax, -1
    pop     r15
    ret

wchunk:
    test    rdx, rdx
    jz      .d
.lp:
    mov     rax, SYS_WRITE
    mov     rdi, r15
    syscall
    cmp     rax, 0
    jle     .fail
    add     rsi, rax
    sub     rdx, rax
    jnz     .lp
.d: ret
.fail:
    mov     rsi, err_write
    mov     rdx, err_write_l
    call    fatal_stderr

; ────────────────────────────────────────────────────────────
;  EMIT  (rep movsb bulk copy to output buffers)
