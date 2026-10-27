%define SYS_READ   0
%define SYS_WRITE  1
%define SYS_OPEN   2
%define SYS_CLOSE  3
%define SYS_EXIT   60
%define STDOUT     1
%define STDERR     2
%define O_RDONLY   0
%define O_WRONLY   1
%define O_CREAT    64
%define O_TRUNC    512

; ─── Token types ────────────────────────────────────────────
%define TOK_VAR      1
%define TOK_PRINT    2
%define TOK_IF       3
%define TOK_IDENT    4
%define TOK_INT      5
%define TOK_EQ       6
%define TOK_PLUS     7
%define TOK_MINUS    8
%define TOK_STAR     9
%define TOK_SLASH    10
%define TOK_GT       11
%define TOK_LT       12
%define TOK_EQEQ     13
%define TOK_NEQ      14
%define TOK_GTE      15
%define TOK_LTE      16
%define TOK_LBRACE   17
%define TOK_RBRACE   18
%define TOK_NEWLINE  19
%define TOK_EOF      20
%define TOK_ELSE     21
%define TOK_WHILE    22
%define TOK_STRING   23
%define TOK_FUNC     24
%define TOK_LPAREN   25
%define TOK_RPAREN   26
%define TOK_COMMA    27
%define TOK_RETURN   28
%define TOK_BREAK    29
%define TOK_CONTINUE 30
%define TOK_AND      31
%define TOK_OR       32
%define TOK_LBRACKET 33
%define TOK_RBRACKET 34
%define TOK_FOR      35
%define TOK_IN       36
%define TOK_MODULE   37
%define TOK_IMPORT   38
%define TOK_TRY      39
%define TOK_CATCH    40
%define TOK_ERROR    41
%define TOK_DOTDOT   42
%define TOK_DOT      43
%define TOK_PERCENT  44
%define TOK_ARGC     45
%define TOK_ARG      46
%define TOK_INTTYPE  47
%define TOK_NOT       48
%define TOK_LEN       49
%define TOK_ABS       50
%define TOK_FMIN      51
%define TOK_FMAX      52
%define TOK_INPUT_INT 53
%define TOK_PRINTLN    54
%define TOK_TRUE       55
%define TOK_FALSE      56
%define TOK_PLUSEQ     57
%define TOK_MINUSEQ    58
%define TOK_STAREQ     59
%define TOK_SLASHEQ    60
%define TOK_PERCENTEQ  61
%define TOK_AMP        62
%define TOK_PIPE       63
%define TOK_CARET      64
%define TOK_TILDE      65
%define TOK_LSHIFT     66
%define TOK_RSHIFT     67
%define TOK_INPUT_STR  68
%define TOK_STRTYPE    69
%define TOK_PUSH       70
%define TOK_POP        71
%define TOK_ELIF       72
%define TOK_READ_FILE  73
%define TOK_WRITE_FILE 74
%define TOK_ARG_STR    75
%define TOK_FIND       76
%define TOK_SLICE      77
%define TOK_EXIT       78
%define TOK_APPEND_FILE 79

; ─── Compile-time types ─────────────────────────────────────
%define TY_UNK     0
%define TY_INT     1
%define TY_STR     2
%define TY_ARR     3
%define TY_STR_ARR 4

; ─── IR opcodes ─────────────────────────────────────────────
; Every IR instruction is 32 bytes:
;   +0  opcode  (8)
;   +8  A       (8)
;   +16 B       (8)
;   +24 line    (8)
%define IRS      32
%define IR_F_OP   0
%define IR_F_A    8
%define IR_F_B   16
%define IR_F_LN  24

%define IR_NOP        0
%define IR_CONST      1
%define IR_LOAD_G     2
%define IR_STORE_G    3
%define IR_LOAD_L     4
%define IR_STORE_L    5
%define IR_LOAD_P     6
%define IR_STORE_P    7
%define IR_PUSH       8
%define IR_POP_RBX    9
%define IR_ADD       10
%define IR_SUB       11
%define IR_MUL       12
%define IR_DIV       13
%define IR_MOD       14
%define IR_CMP       15   ; A=op_token  B=cf_label_id
%define IR_JZ        16   ; A=lbl_id    B=lbl_type
%define IR_JMP       17   ; A=lbl_id    B=lbl_type
%define IR_LBL       18   ; A=lbl_id    B=lbl_type
%define IR_CALL      19   ; A=name_ptr  B=name_len
%define IR_ADD_RSP   20   ; A=bytes
%define IR_RET       21
%define IR_PRINT_INT 22
%define IR_PRINT_STR 23   ; A=str_idx
%define IR_FN_BGN    24   ; A=name_ptr  B=name_len
%define IR_FN_END    25
%define IR_ARR_NEW   26   ; A=count
%define IR_ARR_LD    27
%define IR_ARR_ST    28
%define IR_SET_EF    29
%define IR_CLR_EF    30
%define IR_JMP_TC    31   ; A=tc_label_id
%define IR_MOD_BGN   32   ; A=name_ptr  B=name_len
%define IR_MOD_END   33
%define IR_IMUL8     34
%define IR_MOV_RCX   35
%define IR_POP_RAX   36
%define IR_INC_RAX   37
%define IR_FE_ST     38   ; A=depth_bytes
%define IR_FE_CMP    39   ; A=depth_bytes
%define IR_JGE       40   ; A=lbl_id    B=lbl_type
%define IR_MOV_RBX   41
%define IR_ARGC      42
%define IR_ARG       43
%define IR_LNOT      44
%define IR_ARR_LEN   45
%define IR_ABS       46
%define IR_FMIN      47
%define IR_FMAX      48
%define IR_INPUT_INT 49
%define IR_STORE_HEAP 50
%define IR_PRINT_NL       51
%define IR_BAND           52
%define IR_BOR            53
%define IR_BXOR           54
%define IR_BNOT           55
%define IR_SHL            56
%define IR_SHR            57
%define IR_PRINT_STR_VAR  58
%define IR_STR_LEN        59
%define IR_STR_EQ         60
%define IR_STR_NEQ        61
%define IR_INPUT_STR      62
%define IR_STR_AT         63
%define IR_INT_TO_STR     64
%define IR_STR_TO_INT     65
%define IR_STR_CONCAT     66
%define IR_ARR_PUSH       67
%define IR_ARR_POP        68
%define IR_READ_FILE      69
%define IR_WRITE_FILE     70
%define IR_ARG_STR        71
%define IR_STR_FIND       72
%define IR_STR_SLICE      73
%define IR_EXIT           74
%define IR_APPEND_FILE    75
%define IR_DEAD      127

; ─── Label types ────────────────────────────────────────────
%define LBL_IE  0
%define LBL_ID  1
%define LBL_WS  2
%define LBL_WE  3
%define LBL_CF  4
%define LBL_CD  5
%define LBL_TC  6
%define LBL_TE  7
%define LBL_WC  8

%define MODE_DEBUG   0
%define MODE_RELEASE 1
%define MODE_BENCH   2

%define SRC_SIZE    1048576
%define TOK_MAX     16384
%define IR_MAX      32768
%define OUT_SIZE    393216
%define FN_SIZE     393216
%define STR_SIZE    262144
%define STR_MAX     4096
%define HT_SZ       512
%define HT_MASK     511
%define VAR_NL      64
%define MAX_FN      512
%define MAX_PARAMS  16
%define MAX_LOOP    16
%define MAX_TRY     8
%define MAX_LVARS   64

; Derived sizes for local-variable tracking arrays.
; slot = (1-based_count * 8), accesses are [arr + slot*8] = [arr + count*64].
; Max byte offset = MAX_LVARS * 64  →  need (MAX_LVARS * 8 + 1) qwords.
%define LVAR_ARR_SZ  (MAX_LVARS * 8 + 1)
%define LVAR_NM_ENT  (MAX_LVARS + 1)
