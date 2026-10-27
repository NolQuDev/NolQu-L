; Human-readable reference for stage0.seed.
;
; This file is an audit aid, not a canonical bootstrap input. The canonical
; Stage 0 artifact is reconstructed by hex0.seed from stage0.hex.

BITS 64
ORG 0x400000

%define IMAGE_BASE          0x400000
%define MAX_INPUT           0x400000
%define INPUT_MAP_SIZE      (MAX_INPUT + 1)
%define MAX_OUTPUT          0x200000
%define MAX_LABELS          4096
%define MAX_SYMBOL_LENGTH   63
%define LABEL_RECORD_SIZE   24
%define LABEL_TABLE_SIZE    (MAX_LABELS * LABEL_RECORD_SIZE)

ehdr:
    db 0x7f, "ELF", 2, 1, 1, 0, 0
    times 7 db 0
    dw 2                         ; ET_EXEC
    dw 0x3e                      ; EM_X86_64
    dd 1                         ; EV_CURRENT
    dq _start
    dq phdrs - $$
    dq 0
    dd 0
    dw ehdr_size
    dw phdr_size
    dw 2
    dw 0
    dw 0
    dw 0
ehdr_size equ $ - ehdr

phdrs:
    dd 1                         ; PT_LOAD
    dd 5                         ; PF_R | PF_X
    dq 0
    dq IMAGE_BASE
    dq IMAGE_BASE
    dq file_end - $$
    dq file_end - $$
    dq 0x1000
phdr_size equ $ - phdrs

    dd 0x6474e551                ; PT_GNU_STACK
    dd 6                         ; PF_R | PF_W
    dq 0
    dq 0
    dq 0
    dq 0
    dq 0
    dq 16

_start:
    xor r12d, r12d               ; input mapping, zero means not allocated
    xor r14d, r14d               ; output mapping
    xor r15d, r15d               ; label-table mapping
    xor ebp, ebp                 ; label count

    cmp qword [rsp], 1
    jne .usage

    mov edi, INPUT_MAP_SIZE
    call map_rw
    test rax, rax
    js .allocation_failed
    mov r12, rax

    mov edi, MAX_OUTPUT
    call map_rw
    test rax, rax
    js .allocation_failed
    mov r14, rax

    mov edi, LABEL_TABLE_SIZE
    call map_rw
    test rax, rax
    js .allocation_failed
    mov r15, rax

    xor r13d, r13d               ; input length while reading
.read_input:
    mov edx, INPUT_MAP_SIZE
    sub rdx, r13
    xor eax, eax                 ; SYS_read
    xor edi, edi                 ; stdin
    lea rsi, [r12 + r13]
    syscall
    cmp rax, -4                  ; EINTR
    je .read_input
    test rax, rax
    js .read_failed
    jz .input_complete
    add r13, rax
    cmp r13, MAX_INPUT
    ja .input_too_large
    jmp .read_input

.input_complete:
    add r13, r12                 ; r13 is input-end from this point onward
    xor ebx, ebx                 ; pass-1 output offset
    mov r8, r12                  ; parser cursor

; Pass 1 validates syntax, records labels, and computes the final size.
.pass1_loop:
    cmp r8, r13
    jae .pass1_done
    mov r9, r8                   ; token start for diagnostics
    movzx eax, byte [r8]

    cmp al, ' '
    je .pass1_advance
    cmp al, 9
    je .pass1_advance
    cmp al, 10
    je .pass1_advance
    cmp al, 13
    je .pass1_advance
    cmp al, '#'
    je .pass1_comment
    cmp al, ':'
    je .pass1_definition
    cmp al, '@'
    je .pass1_relative
    cmp al, '&'
    je .pass1_address
    cmp al, '$'
    je .pass1_offset

    call hex_nibble
    test edx, edx
    jz .invalid_token
    lea rcx, [r8 + 1]
    cmp rcx, r13
    jae .truncated_hex
    movzx eax, byte [r8 + 1]
    call hex_nibble
    test edx, edx
    jz .invalid_token
    add r8, 2
    cmp rbx, MAX_OUTPUT
    jae .output_too_large
    inc rbx
    jmp .pass1_loop

.pass1_advance:
    inc r8
    jmp .pass1_loop

.pass1_comment:
    inc r8
.pass1_comment_loop:
    cmp r8, r13
    jae .pass1_loop
    movzx eax, byte [r8]
    inc r8
    cmp al, 10
    je .pass1_loop
    cmp al, 13
    jne .pass1_comment_loop
    jmp .pass1_loop

.pass1_definition:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    mov rdi, rax
    mov rsi, rdx
    call find_label
    test edx, edx
    jnz .duplicate_label
    cmp rbp, MAX_LABELS
    jae .too_many_labels
    mov rax, rbp
    lea rax, [rax + rax * 2]
    lea rax, [r15 + rax * 8]
    mov [rax], rdi
    mov [rax + 8], rsi
    mov [rax + 16], rbx
    inc rbp
    jmp .pass1_loop

.pass1_relative:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    cmp rbx, MAX_OUTPUT - 4
    ja .output_too_large
    add rbx, 4
    jmp .pass1_loop

.pass1_address:
.pass1_offset:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    cmp rbx, MAX_OUTPUT - 8
    ja .output_too_large
    add rbx, 8
    jmp .pass1_loop

.pass1_done:
    mov r10, rbx                 ; immutable final output size
    xor ebx, ebx                 ; pass-2 output offset
    mov r8, r12

; Pass 2 emits bytes and resolves all symbolic fields.
.pass2_loop:
    cmp r8, r13
    jae .pass2_done
    mov r9, r8
    movzx eax, byte [r8]

    cmp al, ' '
    je .pass2_advance
    cmp al, 9
    je .pass2_advance
    cmp al, 10
    je .pass2_advance
    cmp al, 13
    je .pass2_advance
    cmp al, '#'
    je .pass2_comment
    cmp al, ':'
    je .pass2_definition
    cmp al, '@'
    je .pass2_relative
    cmp al, '&'
    je .pass2_address
    cmp al, '$'
    je .pass2_offset

    call hex_nibble
    test edx, edx
    jz .invalid_token
    mov r11d, eax
    lea rcx, [r8 + 1]
    cmp rcx, r13
    jae .truncated_hex
    movzx eax, byte [r8 + 1]
    call hex_nibble
    test edx, edx
    jz .invalid_token
    shl r11d, 4
    or eax, r11d
    mov byte [r14 + rbx], al
    add r8, 2
    inc rbx
    jmp .pass2_loop

.pass2_advance:
    inc r8
    jmp .pass2_loop

.pass2_comment:
    inc r8
.pass2_comment_loop:
    cmp r8, r13
    jae .pass2_loop
    movzx eax, byte [r8]
    inc r8
    cmp al, 10
    je .pass2_loop
    cmp al, 13
    jne .pass2_comment_loop
    jmp .pass2_loop

.pass2_definition:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    jmp .pass2_loop

.pass2_relative:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    mov rdi, rax
    mov rsi, rdx
    call find_label
    test edx, edx
    jz .undefined_label
    mov rcx, rax
    sub rcx, rbx
    sub rcx, 4
    movsxd rax, ecx
    cmp rax, rcx
    jne .relative_overflow
    mov dword [r14 + rbx], ecx
    add rbx, 4
    jmp .pass2_loop

.pass2_address:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    mov rdi, rax
    mov rsi, rdx
    call find_label
    test edx, edx
    jz .undefined_label
    add rax, IMAGE_BASE
    mov qword [r14 + rbx], rax
    add rbx, 8
    jmp .pass2_loop

.pass2_offset:
    lea rdi, [r8 + 1]
    mov rsi, r13
    call scan_name
    test r11d, r11d
    jnz .name_error
    mov r8, rcx
    mov rdi, rax
    mov rsi, rdx
    call find_label
    test edx, edx
    jz .undefined_label
    mov qword [r14 + rbx], rax
    add rbx, 8
    jmp .pass2_loop

.pass2_done:
    cmp rbx, r10
    jne .internal_size_mismatch
    mov edi, 1                  ; stdout
    mov rsi, r14
    mov rdx, r10
    call write_all
    test eax, eax
    jnz .write_failed
    xor edi, edi
    jmp cleanup_exit

.name_error:
    cmp r11d, 2
    je .name_too_long
    mov rdi, r9
    lea rsi, [rel malformed_name_suffix]
    mov edx, malformed_name_suffix_len
    jmp fail_at

.name_too_long:
    mov rdi, r9
    lea rsi, [rel name_too_long_suffix]
    mov edx, name_too_long_suffix_len
    jmp fail_at

.invalid_token:
    mov rdi, r9
    lea rsi, [rel invalid_token_suffix]
    mov edx, invalid_token_suffix_len
    jmp fail_at

.truncated_hex:
    mov rdi, r9
    lea rsi, [rel truncated_hex_suffix]
    mov edx, truncated_hex_suffix_len
    jmp fail_at

.duplicate_label:
    mov rdi, r9
    lea rsi, [rel duplicate_label_suffix]
    mov edx, duplicate_label_suffix_len
    jmp fail_at

.undefined_label:
    mov rdi, r9
    lea rsi, [rel undefined_label_suffix]
    mov edx, undefined_label_suffix_len
    jmp fail_at

.too_many_labels:
    mov rdi, r9
    lea rsi, [rel too_many_labels_suffix]
    mov edx, too_many_labels_suffix_len
    jmp fail_at

.output_too_large:
    mov rdi, r9
    lea rsi, [rel output_too_large_suffix]
    mov edx, output_too_large_suffix_len
    jmp fail_at

.relative_overflow:
    mov rdi, r9
    lea rsi, [rel relative_overflow_suffix]
    mov edx, relative_overflow_suffix_len
    jmp fail_at

.usage:
    mov edi, 1
    lea rsi, [rel usage_message]
    mov edx, usage_message_len
    jmp fail_plain

.allocation_failed:
    mov edi, 2
    lea rsi, [rel allocation_failed_message]
    mov edx, allocation_failed_message_len
    jmp fail_plain

.read_failed:
    mov edi, 1
    lea rsi, [rel read_failed_message]
    mov edx, read_failed_message_len
    jmp fail_plain

.input_too_large:
    mov edi, 1
    lea rsi, [rel input_too_large_message]
    mov edx, input_too_large_message_len
    jmp fail_plain

.write_failed:
    mov edi, 1
    lea rsi, [rel write_failed_message]
    mov edx, write_failed_message_len
    jmp fail_plain

.internal_size_mismatch:
    mov edi, 2
    lea rsi, [rel internal_size_message]
    mov edx, internal_size_message_len
    jmp fail_plain

; mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0)
map_rw:
    mov rsi, rdi
    xor edi, edi
    mov edx, 3
    mov r10d, 0x22
    mov r8, -1
    xor r9d, r9d
    mov eax, 9                   ; SYS_mmap
    syscall
    ret

; Convert AL to a hexadecimal nibble. EDX is one on success, zero on failure.
hex_nibble:
    movzx eax, al
    cmp al, '0'
    jb .invalid
    cmp al, '9'
    jbe .decimal
    cmp al, 'A'
    jb .invalid
    cmp al, 'F'
    jbe .upper
    cmp al, 'a'
    jb .invalid
    cmp al, 'f'
    ja .invalid
    sub eax, 'a' - 10
    mov edx, 1
    ret
.upper:
    sub eax, 'A' - 10
    mov edx, 1
    ret
.decimal:
    sub eax, '0'
    mov edx, 1
    ret
.invalid:
    xor eax, eax
    xor edx, edx
    ret

; Parse [A-Za-z_][A-Za-z0-9_]*. R11D returns 0, malformed=1, too-long=2.
scan_name:
    mov rax, rdi                 ; returned name pointer
    cmp rdi, rsi
    jae .malformed
    movzx ecx, byte [rdi]
    cmp cl, '_'
    je .first_ok
    cmp cl, 'A'
    jb .malformed
    cmp cl, 'Z'
    jbe .first_ok
    cmp cl, 'a'
    jb .malformed
    cmp cl, 'z'
    ja .malformed
.first_ok:
    inc rdi
.scan:
    mov rdx, rdi
    sub rdx, rax
    cmp rdx, MAX_SYMBOL_LENGTH
    ja .too_long
    cmp rdi, rsi
    jae .done
    movzx ecx, byte [rdi]
    cmp cl, '_'
    je .continue
    cmp cl, '0'
    jb .maybe_upper
    cmp cl, '9'
    jbe .continue
.maybe_upper:
    cmp cl, 'A'
    jb .delimiter
    cmp cl, 'Z'
    jbe .continue
    cmp cl, 'a'
    jb .delimiter
    cmp cl, 'z'
    jbe .continue
.delimiter:
    cmp cl, ' '
    je .done
    cmp cl, 9
    je .done
    cmp cl, 10
    je .done
    cmp cl, 13
    je .done
    cmp cl, '#'
    je .done
    jmp .malformed
.continue:
    inc rdi
    jmp .scan
.done:
    mov rdx, rdi
    sub rdx, rax
    mov rcx, rdi
    xor r11d, r11d
    ret
.malformed:
    mov r11d, 1
    ret
.too_long:
    mov r11d, 2
    ret

; Find a label by pointer and length. RAX is its offset; EDX is found/not-found.
find_label:
    push r8
    push r9
    push r10
    push r11
    xor r8d, r8d
.record_loop:
    cmp r8, rbp
    jae .missing
    mov r9, r8
    lea r9, [r9 + r9 * 2]
    lea r9, [r15 + r9 * 8]
    cmp qword [r9 + 8], rsi
    jne .next_record
    xor r10d, r10d
.byte_loop:
    cmp r10, rsi
    jae .found
    mov r11, [r9]
    movzx edx, byte [rdi + r10]
    cmp dl, byte [r11 + r10]
    jne .next_record
    inc r10
    jmp .byte_loop
.next_record:
    inc r8
    jmp .record_loop
.found:
    mov rax, [r9 + 16]
    mov edx, 1
    jmp .restore
.missing:
    xor eax, eax
    xor edx, edx
.restore:
    pop r11
    pop r10
    pop r9
    pop r8
    ret

; Write an entire buffer. EAX is zero on success and one on failure.
write_all:
    test rdx, rdx
    jz .success
.write:
    mov eax, 1                   ; SYS_write
    syscall
    cmp rax, -4                  ; EINTR
    je .write
    test rax, rax
    jle .failure
    add rsi, rax
    sub rdx, rax
    jnz .write
.success:
    xor eax, eax
    ret
.failure:
    mov eax, 1
    ret

; RDI is a zero-based input byte offset.
write_u64_stderr:
    sub rsp, 40                  ; 32-byte digits buffer plus call alignment
    lea rsi, [rsp + 32]
    mov rax, rdi
    mov ecx, 10
.digit_loop:
    xor edx, edx
    div rcx
    dec rsi
    add dl, '0'
    mov [rsi], dl
    test rax, rax
    jnz .digit_loop
    lea rdx, [rsp + 32]
    sub rdx, rsi
    mov edi, 2
    call write_all
    add rsp, 40
    ret

; RDI points into the input mapping; RSI/RDX describe the diagnostic suffix.
fail_at:
    mov r8, rsi
    mov r9, rdx
    sub rdi, r12
    mov r10, rdi

    mov edi, 2
    lea rsi, [rel error_prefix]
    mov edx, error_prefix_len
    call write_all
    mov rdi, r10
    call write_u64_stderr
    mov edi, 2
    mov rsi, r8
    mov rdx, r9
    call write_all
    mov edi, 1
    jmp cleanup_exit

; EDI is the desired exit status; RSI/RDX describe a complete diagnostic.
fail_plain:
    mov r8d, edi
    mov edi, 2
    call write_all
    mov edi, r8d
    jmp cleanup_exit

cleanup_exit:
    mov ebx, edi
    test r15, r15
    jz .skip_labels
    mov eax, 11                  ; SYS_munmap
    mov rdi, r15
    mov esi, LABEL_TABLE_SIZE
    syscall
.skip_labels:
    test r14, r14
    jz .skip_output
    mov eax, 11
    mov rdi, r14
    mov esi, MAX_OUTPUT
    syscall
.skip_output:
    test r12, r12
    jz .skip_input
    mov eax, 11
    mov rdi, r12
    mov esi, INPUT_MAP_SIZE
    syscall
.skip_input:
    mov edi, ebx
    mov eax, 60                  ; SYS_exit
    syscall
    ud2

error_prefix: db "stage0: byte "
error_prefix_len equ $ - error_prefix
invalid_token_suffix: db ": error: invalid token; expected hexadecimal byte, :label, @label, &label, or $label", 10
invalid_token_suffix_len equ $ - invalid_token_suffix
truncated_hex_suffix: db ": error: truncated hexadecimal byte; add the second hexadecimal digit", 10
truncated_hex_suffix_len equ $ - truncated_hex_suffix
malformed_name_suffix: db ": error: malformed symbol; use [A-Za-z_][A-Za-z0-9_]*", 10
malformed_name_suffix_len equ $ - malformed_name_suffix
name_too_long_suffix: db ": error: symbol exceeds 63 bytes; shorten the symbol name", 10
name_too_long_suffix_len equ $ - name_too_long_suffix
duplicate_label_suffix: db ": error: duplicate label; define each symbol exactly once", 10
duplicate_label_suffix_len equ $ - duplicate_label_suffix
undefined_label_suffix: db ": error: undefined label; add a matching :label definition", 10
undefined_label_suffix_len equ $ - undefined_label_suffix
too_many_labels_suffix: db ": error: more than 4096 labels; split the bootstrap unit", 10
too_many_labels_suffix_len equ $ - too_many_labels_suffix
output_too_large_suffix: db ": error: output exceeds 2097152 bytes; split the bootstrap unit", 10
output_too_large_suffix_len equ $ - output_too_large_suffix
relative_overflow_suffix: db ": error: relative patch exceeds signed 32-bit range", 10
relative_overflow_suffix_len equ $ - relative_overflow_suffix

usage_message: db "stage0: error: command-line arguments are not supported; use stdin and stdout", 10
usage_message_len equ $ - usage_message
allocation_failed_message: db "stage0: internal error: cannot allocate bounded bootstrap buffers", 10
allocation_failed_message_len equ $ - allocation_failed_message
read_failed_message: db "stage0: error: cannot read standard input; check the input stream", 10
read_failed_message_len equ $ - read_failed_message
input_too_large_message: db "stage0: error: input exceeds 4194304 bytes; split the bootstrap unit", 10
input_too_large_message_len equ $ - input_too_large_message
write_failed_message: db "stage0: error: cannot write standard output; check the output stream", 10
write_failed_message_len equ $ - write_failed_message
internal_size_message: db "stage0: internal error: pass output sizes diverged", 10
internal_size_message_len equ $ - internal_size_message

file_end:
