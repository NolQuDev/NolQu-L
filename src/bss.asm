
src_buf       resb SRC_SIZE
src_len       resq 1

tok_type      resq TOK_MAX
tok_ptr       resq TOK_MAX
tok_len       resq TOK_MAX
tok_line      resq TOK_MAX
tok_col       resq TOK_MAX
tok_cnt       resq 1
tok_pos       resq 1

ir_buf        resb (IR_MAX * IRS)
ir_cnt        resq 1

out_buf       resb OUT_SIZE
out_pos       resq 1
fn_buf        resb FN_SIZE
fn_pos        resq 1
str_buf       resb STR_SIZE
str_pos       resq 1
cur_emit      resq 1
emit_line     resq 1
str_cnt       resq 1
str_ptrs      resq STR_MAX
str_lens      resq STR_MAX
istr_total    resq 1
istr_cur      resq 1
its_cnt       resq 1
its_cur       resq 1
str_cat_cnt   resq 1
str_cat_cur   resq 1
file_read_total resq 1
file_read_cur   resq 1
write_file_total resq 1
append_file_total resq 1
arg_str_total resq 1
arg_str_cur   resq 1
str_find_total resq 1
str_slice_total resq 1

label_ctr     resq 1

ht_key        resq HT_SZ
ht_klen       resq HT_SZ
ht_val        resq HT_SZ
ht_cnt        resq 1
var_store     resb (HT_SZ * VAR_NL)

lht_key       resq HT_SZ
lht_klen      resq HT_SZ
lht_val       resq HT_SZ
lht_cnt       resq 1

fn_names      resb (MAX_FN * VAR_NL)
fn_pcnt       resq MAX_FN
fn_ret_types  resq MAX_FN
fn_cnt        resq 1
mod_names     resb (MAX_FN * VAR_NL)
mod_cnt       resq 1

in_fn         resq 1
blk_dep       resq 1
decl_phase    resq 1
fn_pcur       resq 1
fn_pnames     resb (MAX_PARAMS * VAR_NL)
fn_plens      resq MAX_PARAMS
fn_param_types resq MAX_PARAMS

mod_name      resb VAR_NL
mod_len       resq 1

lp_ws_stk         resq MAX_LOOP
lp_we_stk         resq MAX_LOOP
lp_isfor      resq MAX_LOOP
lp_dep        resq 1
for_dep       resq 1

try_tc        resq MAX_TRY
try_dep       resq 1

build_mode    resq 1
opt_on        resq 1
check_only    resq 1
had_error     resq 1
dump_tokens   resq 1
dump_ir       resq 1

ts_start      resq 1
ts_lex        resq 1
ts_parse      resq 1
ts_opt        resq 1
ts_cg         resq 1

num_buf       resb 32

type_stk      resq 64
type_stkp     resq 1
gvar_types    resq (HT_SZ + 1)
lvar_types    resq LVAR_ARR_SZ

out_fname_ptr resq 1
out_fname_len resq 1

fn_ret_type   resq 1

decl_pending_line resq 1
decl_pending_col  resq 1
blk_returned      resq 1

lvar_reads     resq LVAR_ARR_SZ
lvar_decl_line resq LVAR_ARR_SZ
lvar_decl_col  resq LVAR_ARR_SZ
gvar_reads     resq (HT_SZ + 1)
gvar_decl_line resq (HT_SZ + 1)
gvar_decl_col  resq (HT_SZ + 1)
gvar_names_l   resq (HT_SZ + 1)
lvar_names     resb (LVAR_NM_ENT * VAR_NL)
lvar_names_l   resq LVAR_NM_ENT
unused_msg_buf resb 96

; Per-depth name buffer for for-each hidden variables.
; Each depth uses 6 bytes: [0..2] = __a name, [3..5] = __i name.
; Each name is 3 bytes: 0x01, type-char, for_dep byte.
; Separate slots per depth prevent hash-probe aliasing in nested loops.
fe_names_buf   resb (MAX_LOOP * 6)
arr_is_str_arr resq 1
arr_elem_type  resq 1
var_decl_mode  resq 1   ; 1 = parse_var new-local context; skip global lookup in ir_store
