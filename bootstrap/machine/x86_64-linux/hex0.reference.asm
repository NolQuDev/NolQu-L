; Human-readable reference for hex0.seed.
;
; This file is not part of the canonical bootstrap chain. It exists so the
; checked-in machine bytes can be reviewed against their intended x86_64
; Linux behavior. The canonical artifact is hex0.seed, reconstructed from
; hex0.hex and verified with hex0.sha256.

BITS 64
ORG 0x400000

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
    dq 0x400000
    dq 0x400000
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
    sub rsp, 16                  ; one-byte I/O buffer, stack stays aligned
    mov r12d, 0xff               ; 0xff means no pending high nibble
    xor r13d, r13d               ; non-zero while consuming a comment

.read_next:
    xor eax, eax                 ; SYS_read
    xor edi, edi                 ; stdin
    mov rsi, rsp
    mov edx, 1
    syscall
    cmp rax, -4                  ; EINTR
    je .read_next
    test rax, rax
    js .read_failed
    jz .end_of_input

    movzx eax, byte [rsp]
    test r13d, r13d
    jnz .in_comment

    cmp al, '#'
    je .start_comment
    cmp al, ' '
    je .read_next
    cmp al, 9                    ; horizontal tab
    je .read_next
    cmp al, 10                   ; LF
    je .read_next
    cmp al, 13                   ; CR
    je .read_next

    cmp al, '0'
    jb .invalid_hex
    cmp al, '9'
    jbe .decimal_digit
    cmp al, 'A'
    jb .invalid_hex
    cmp al, 'F'
    jbe .upper_digit
    cmp al, 'a'
    jb .invalid_hex
    cmp al, 'f'
    ja .invalid_hex
    sub al, 'a' - 10
    jmp .accept_nibble

.upper_digit:
    sub al, 'A' - 10
    jmp .accept_nibble

.decimal_digit:
    sub al, '0'

.accept_nibble:
    cmp r12b, 0xff
    jne .emit_byte
    mov r12b, al
    jmp .read_next

.emit_byte:
    shl r12b, 4
    or al, r12b
    mov byte [rsp], al
    mov r12d, 0xff

.write_byte:
    mov eax, 1                   ; SYS_write
    mov edi, 1                   ; stdout
    mov rsi, rsp
    mov edx, 1
    syscall
    cmp rax, -4                  ; EINTR
    je .write_byte
    cmp rax, 1
    jne .write_failed
    jmp .read_next

.start_comment:
    mov r13d, 1
    jmp .read_next

.in_comment:
    cmp al, 10
    je .end_comment
    cmp al, 13
    jne .read_next
.end_comment:
    xor r13d, r13d
    jmp .read_next

.end_of_input:
    cmp r12b, 0xff
    jne .odd_nibble
    xor edi, edi
    mov eax, 60                  ; SYS_exit
    syscall

.invalid_hex:
    lea rsi, [rel invalid_hex_message]
    mov edx, invalid_hex_message_len
    jmp .fail

.odd_nibble:
    lea rsi, [rel odd_nibble_message]
    mov edx, odd_nibble_message_len
    jmp .fail

.read_failed:
    lea rsi, [rel read_failed_message]
    mov edx, read_failed_message_len
    jmp .fail

.write_failed:
    lea rsi, [rel write_failed_message]
    mov edx, write_failed_message_len

.fail:
    mov edi, 2                   ; stderr
.write_message:
    mov eax, 1                   ; SYS_write
    syscall
    cmp rax, -4                  ; EINTR
    je .write_message
    test rax, rax
    jle .exit_failure
    add rsi, rax
    sub rdx, rax
    jnz .write_message

.exit_failure:
    mov edi, 1
    mov eax, 60                  ; SYS_exit
    syscall

invalid_hex_message: db "hex0: error: invalid hexadecimal byte", 10
invalid_hex_message_len equ $ - invalid_hex_message
odd_nibble_message: db "hex0: error: odd number of hexadecimal nibbles", 10
odd_nibble_message_len equ $ - odd_nibble_message
read_failed_message: db "hex0: error: cannot read standard input", 10
read_failed_message_len equ $ - read_failed_message
write_failed_message: db "hex0: error: cannot write standard output", 10
write_failed_message_len equ $ - write_failed_message

file_end:
