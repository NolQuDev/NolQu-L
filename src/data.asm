
msg_ok        db "OK: output.asm written", 10
msg_ok_l      equ $ - msg_ok
err_usage     db "Usage: nq <file.nq> [--check] [--emit <path>] [--release] [--bench] [--dump-tokens] [--dump-ir]", 10
err_usage_l   equ $ - err_usage
err_bad_flag  db "Error: unknown option: "
err_bad_flag_l equ $ - err_bad_flag
err_extra_arg db "Error: unexpected argument: "
err_extra_arg_l equ $ - err_extra_arg
err_emit_path db "Error: --emit requires a path", 10
err_emit_path_l equ $ - err_emit_path
err_open      db "Error: cannot open source file", 10
err_open_l    equ $ - err_open
err_noloop    db "Error: break/continue outside loop", 10
err_noloop_l  equ $ - err_noloop
err_tokovf    db "token buffer overflow"
err_tokovf_l  equ $ - err_tokovf
err_irovf     db "Error: IR buffer overflow", 10
err_irovf_l   equ $ - err_irovf
err_fnovf     db "function table overflow"
err_fnovf_l   equ $ - err_fnovf
err_modovf    db "module table overflow"
err_modovf_l  equ $ - err_modovf

ep_prefix     db "[nolqu] Error at line "
ep_prefix_l   equ $ - ep_prefix
ep_col        db ", col "
ep_col_l      equ $ - ep_col
ep_sep        db ": "
ep_sep_l      equ $ - ep_sep
ep_nl         db 10

em_undef      db "undefined variable"
em_undef_l    equ $ - em_undef
em_parse      db "parse error (unexpected token)"
em_parse_l    equ $ - em_parse
em_invalid_char db "invalid character"
em_invalid_char_l equ $ - em_invalid_char
em_expect_in  db "expected 'in' in for loop"
em_expect_in_l equ $ - em_expect_in
em_expect_dd  db "expected '..' in for loop"
em_expect_dd_l equ $ - em_expect_dd
em_expect_fn_name db "expected function name"
em_expect_fn_name_l equ $ - em_expect_fn_name
em_expect_param_name db "expected parameter name"
em_expect_param_name_l equ $ - em_expect_param_name
em_expect_mod_name db "expected module name"
em_expect_mod_name_l equ $ - em_expect_mod_name
em_mod_dup    db "duplicate module name"
em_mod_dup_l  equ $ - em_mod_dup
em_mod_undef  db "unknown module name"
em_mod_undef_l equ $ - em_mod_undef
em_expect_import_name db "expected import name"
em_expect_import_name_l equ $ - em_expect_import_name
em_expect_mod_block db "expected '{' after module name"
em_expect_mod_block_l equ $ - em_expect_mod_block
em_expect_import_end db "unexpected token after import name"
em_expect_import_end_l equ $ - em_expect_import_end
em_expect_member_name db "expected function name after '.'"
em_expect_member_name_l equ $ - em_expect_member_name
em_expect_call_lparen db "expected '(' after function name"
em_expect_call_lparen_l equ $ - em_expect_call_lparen
em_chain_unsupported db "chained call/index/member access is not supported"
em_chain_unsupported_l equ $ - em_chain_unsupported
em_expect_block db "expected '{' to start block body"
em_expect_block_l equ $ - em_expect_block
em_expect_arg_sep db "expected ',' or ')' in argument list"
em_expect_arg_sep_l equ $ - em_expect_arg_sep
em_expect_param_sep db "expected ',' or ')' in parameter list"
em_expect_param_sep_l equ $ - em_expect_param_sep
em_expect_builtin_lparen db "expected '(' after builtin name"
em_expect_builtin_lparen_l equ $ - em_expect_builtin_lparen
em_expect_builtin_rparen db "expected ')' after builtin argument list"
em_expect_builtin_rparen_l equ $ - em_expect_builtin_rparen
em_expect_rparen db "expected ')' after expression"
em_expect_rparen_l equ $ - em_expect_rparen
em_bad_stmt   db "unexpected statement"
em_bad_stmt_l equ $ - em_bad_stmt
em_print_item db "expected print item"
em_print_item_l equ $ - em_print_item
em_noloop     db "break/continue outside loop"
em_noloop_l   equ $ - em_noloop
em_need_catch db "expected 'catch' after try block"
em_need_catch_l equ $ - em_need_catch
em_error_out  db "error statement outside try"
em_error_out_l equ $ - em_error_out
em_error_str  db "error payload must be a string literal"
em_error_str_l equ $ - em_error_str
em_array_item db "expected array item"
em_array_item_l equ $ - em_array_item
em_array_too_large db "array literal exceeds fixed heap capacity"
em_array_too_large_l equ $ - em_array_too_large
em_array_mixed_type db "type error: array literal elements must have the same type"
em_array_mixed_type_l equ $ - em_array_mixed_type
em_neg_index  db "negative array index not allowed"
em_neg_index_l equ $ - em_neg_index
em_array_index db "expected array index"
em_array_index_l equ $ - em_array_index
em_expect_rbracket db "expected ']' after array index"
em_expect_rbracket_l equ $ - em_expect_rbracket
em_expect_typed_array_rbracket db "expected ']' after typed array marker"
em_expect_typed_array_rbracket_l equ $ - em_expect_typed_array_rbracket
em_expect_eq db "expected '=' in assignment"
em_expect_eq_l equ $ - em_expect_eq
em_expect_expr db "expected expression"
em_expect_expr_l equ $ - em_expect_expr
em_ident_stmt db "expected assignment or call after identifier"
em_ident_stmt_l equ $ - em_ident_stmt
em_bad_assign_target db "invalid assignment target"
em_bad_assign_target_l equ $ - em_bad_assign_target
em_expr_stmt db "only call expressions may be used as statements"
em_expr_stmt_l equ $ - em_expr_stmt
em_decl_in_fn db "declaration not allowed inside function"
em_decl_in_fn_l equ $ - em_decl_in_fn
em_decl_top db "declaration must appear at top level"
em_decl_top_l equ $ - em_decl_top
em_decl_order db "declaration must appear before executable statements"
em_decl_order_l equ $ - em_decl_order
em_fn_undef   db "undefined function"
em_fn_undef_l equ $ - em_fn_undef
em_fn_arity   db "wrong number of function arguments"
em_fn_arity_l equ $ - em_fn_arity
em_ret_out    db "return outside function"
em_ret_out_l  equ $ - em_ret_out
em_param_ovf  db "too many function parameters"
em_param_ovf_l equ $ - em_param_ovf
em_fn_dup     db "duplicate function name"
em_fn_dup_l   equ $ - em_fn_dup
em_param_dup  db "duplicate parameter name"
em_param_dup_l equ $ - em_param_dup
em_loop_ovf   db "loop nesting limit exceeded"
em_loop_ovf_l equ $ - em_loop_ovf
em_try_ovf    db "try nesting limit exceeded"
em_try_ovf_l  equ $ - em_try_ovf
em_local_dup  db "duplicate local variable"
em_local_dup_l equ $ - em_local_dup
em_name_conflict db "name conflicts with existing global"
em_name_conflict_l equ $ - em_name_conflict
em_type_arith db "type error: arithmetic on non-integer"
em_type_arith_l equ $ - em_type_arith
em_type_int_operand db "type error: integer operand required"
em_type_int_operand_l equ $ - em_type_int_operand
em_type_cmp   db "type error: comparison type mismatch"
em_type_cmp_l equ $ - em_type_cmp
em_type_assign db "type error: assignment type mismatch"
em_type_assign_l equ $ - em_type_assign
em_type_ret   db "type error: inconsistent return types"
em_type_ret_l equ $ - em_type_ret
em_type_str_concat db "type error: '+' on non-string operand"
em_type_str_concat_l equ $ - em_type_str_concat
em_str_builtin_type db "type error: str() argument must be an integer"
em_str_builtin_type_l equ $ - em_str_builtin_type
em_int_builtin_type db "type error: int() argument must be a string"
em_int_builtin_type_l equ $ - em_int_builtin_type
em_print_arr  db "type error: cannot print array"
em_print_arr_l equ $ - em_print_arr
em_print_str_expr db "type error: cannot print string expression"
em_print_str_expr_l equ $ - em_print_str_expr
em_len_type   db "type error: len() requires array or string"
em_len_type_l equ $ - em_len_type
em_read_file_type db "type error: read_file() path must be a string"
em_read_file_type_l equ $ - em_read_file_type
em_write_file_path_type db "type error: write_file() path must be a string"
em_write_file_path_type_l equ $ - em_write_file_path_type
em_write_file_data_type db "type error: write_file() data must be a string"
em_write_file_data_type_l equ $ - em_write_file_data_type
em_append_file_path_type db "type error: append_file() path must be a string"
em_append_file_path_type_l equ $ - em_append_file_path_type
em_append_file_data_type db "type error: append_file() data must be a string"
em_append_file_data_type_l equ $ - em_append_file_data_type
em_exit_type db "exit() code must be an integer"
em_exit_type_l equ $ - em_exit_type
em_arg_str_type db "type error: arg_str() index must be an integer"
em_arg_str_type_l equ $ - em_arg_str_type
em_arg_type db "type error: arg() index must be an integer"
em_arg_type_l equ $ - em_arg_type
em_find_haystack_type db "type error: find() haystack must be a string"
em_find_haystack_type_l equ $ - em_find_haystack_type
em_find_needle_type db "type error: find() needle must be a string"
em_find_needle_type_l equ $ - em_find_needle_type
em_slice_source_type db "type error: slice() source must be a string"
em_slice_source_type_l equ $ - em_slice_source_type
em_slice_start_type db "type error: slice() start must be an integer"
em_slice_start_type_l equ $ - em_slice_start_type
em_slice_end_type db "type error: slice() end must be an integer"
em_slice_end_type_l equ $ - em_slice_end_type
em_for_range_type db "type error: for range bounds must be integers"
em_for_range_type_l equ $ - em_for_range_type
em_for_each_type db "type error: for-each source must be an array"
em_for_each_type_l equ $ - em_for_each_type
em_str_ord    db "type error: strings only support == and !="
em_str_ord_l  equ $ - em_str_ord
em_cmp_arr    db "type error: cannot compare array"
em_cmp_arr_l  equ $ - em_cmp_arr
em_cmp_str    db "type error: cannot compare string expression"
em_cmp_str_l  equ $ - em_cmp_str
em_unused_pfx  db "unused variable '"
em_unused_pfx_l equ $ - em_unused_pfx
em_dead_code   db "unreachable code after return"
em_dead_code_l equ $ - em_dead_code
em_unclosed_block  db "unexpected end of file: unclosed '{'"
em_unclosed_block_l equ $ - em_unclosed_block
em_int_overflow  db "integer literal overflow (max 9223372036854775807)"
em_int_overflow_l equ $ - em_int_overflow
em_index_on_int  db "type error: cannot index an integer"
em_index_on_int_l equ $ - em_index_on_int
em_index_type db "type error: index must be an integer"
em_index_type_l equ $ - em_index_type
em_array_store_not_arr db "type error: indexed assignment requires an array"
em_array_store_not_arr_l equ $ - em_array_store_not_arr
em_array_store_type db "type error: array assignment value type does not match element type"
em_array_store_type_l equ $ - em_array_store_type
em_push_not_arr  db "type error: push() first argument must be an array"
em_push_not_arr_l equ $ - em_push_not_arr
em_push_type db "type error: push() value type does not match array element type"
em_push_type_l equ $ - em_push_type
em_pop_not_arr   db "type error: pop() argument must be an array"
em_pop_not_arr_l equ $ - em_pop_not_arr
err_strovf    db "Error: string buffer overflow", 10
err_strovf_l  equ $ - err_strovf
em_strlit_ovf db "too many string literals (max 4096)"
em_strlit_ovf_l equ $ - em_strlit_ovf
em_strbuf_ovf db "string data buffer overflow"
em_strbuf_ovf_l equ $ - em_strbuf_ovf
err_outovf    db "Error: output buffer overflow", 10
err_outovf_l  equ $ - err_outovf
em_outbuf_ovf db "output buffer overflow"
em_outbuf_ovf_l equ $ - em_outbuf_ovf
err_fnbovf    db "Error: function body buffer overflow", 10
err_fnbovf_l  equ $ - err_fnbovf
em_fnbuf_ovf db "function body buffer overflow"
em_fnbuf_ovf_l equ $ - em_fnbuf_ovf
err_htovf     db "symbol table full"
err_htovf_l   equ $ - err_htovf
err_lsymovf   db "too many local variables (max 64)"
err_lsymovf_l equ $ - err_lsymovf
err_unterm_str db "unterminated string literal"
err_unterm_str_l equ $ - err_unterm_str
err_unterm_block db "unterminated block comment"
err_unterm_block_l equ $ - err_unterm_block
err_hex_empty db "expected hex digit after 0x"
err_hex_empty_l equ $ - err_hex_empty
err_hex_digit db "invalid hex digit"
err_hex_digit_l equ $ - err_hex_digit
err_bin_empty db "expected binary digit after 0b"
err_bin_empty_l equ $ - err_bin_empty
err_bin_digit db "invalid binary digit"
err_bin_digit_l equ $ - err_bin_digit
err_num_sep db "invalid digit separator"
err_num_sep_l equ $ - err_num_sep
err_namelen   db "identifier too long"
err_namelen_l equ $ - err_namelen
err_write     db "Error: write failed", 10
err_write_l   equ $ - err_write
err_srcbig    db "Error: source file too large", 10
err_srcbig_l  equ $ - err_srcbig

bh_hdr        db "── nolqu bench ──────────── cycles ──", 10
bh_hdr_l      equ $ - bh_hdr
bh_lex        db "  lex      "
bh_lex_l      equ $ - bh_lex
bh_parse      db "  parse    "
bh_parse_l    equ $ - bh_parse
bh_opt        db "  optimize "
bh_opt_l      equ $ - bh_opt
bh_cg         db "  codegen  "
bh_cg_l       equ $ - bh_cg
bh_total      db "  total    "
bh_total_l    equ $ - bh_total
bh_nl         db 10

s_release     db "--release", 0
s_bench       db "--bench",   0
s_dump_tok    db "--dump-tokens", 0
s_dump_ir     db "--dump-ir", 0
s_check       db "--check", 0
s_emit        db "--emit", 0
out_fname     db "build/output.asm", 0
msg_ok_pfx    db "OK: "
msg_ok_pfx_l  equ $ - msg_ok_pfx
msg_ok_sfx    db " written", 10
msg_ok_sfx_l  equ $ - msg_ok_sfx

dbg_tab       db 9
dbg_colon     db ":"
dbg_sp        db " "
dbg_a_eq      db " A="
dbg_a_eq_l    equ $ - dbg_a_eq
dbg_b_eq      db " B="
dbg_b_eq_l    equ $ - dbg_b_eq
dbg_ln_eq     db " LN="
dbg_ln_eq_l   equ $ - dbg_ln_eq
dbg_name_eq   db " NAME="
dbg_name_eq_l equ $ - dbg_name_eq
dbg_text_eq   db " TEXT="
dbg_text_eq_l equ $ - dbg_text_eq
dbg_dump_tok_hdr db "== TOKENS ==", 10
dbg_dump_tok_hdr_l equ $ - dbg_dump_tok_hdr
dbg_dump_ir_hdr db "== IR ==", 10
dbg_dump_ir_hdr_l equ $ - dbg_dump_ir_hdr
dbg_unknown_tok db "TOK?"
dbg_unknown_tok_l equ $ - dbg_unknown_tok
dbg_unknown_ir db "IR?"
dbg_unknown_ir_l equ $ - dbg_unknown_ir

tokn_var      db "VAR"
tokn_var_l    equ $ - tokn_var
tokn_print    db "PRINT"
tokn_print_l  equ $ - tokn_print
tokn_if       db "IF"
tokn_if_l     equ $ - tokn_if
tokn_ident    db "IDENT"
tokn_ident_l  equ $ - tokn_ident
tokn_int      db "INT"
tokn_int_l    equ $ - tokn_int
tokn_eq       db "EQ"
tokn_eq_l     equ $ - tokn_eq
tokn_plus     db "PLUS"
tokn_plus_l   equ $ - tokn_plus
tokn_minus    db "MINUS"
tokn_minus_l  equ $ - tokn_minus
tokn_star     db "STAR"
tokn_star_l   equ $ - tokn_star
tokn_slash    db "SLASH"
tokn_slash_l  equ $ - tokn_slash
tokn_gt       db "GT"
tokn_gt_l     equ $ - tokn_gt
tokn_lt       db "LT"
tokn_lt_l     equ $ - tokn_lt
tokn_eqeq     db "EQEQ"
tokn_eqeq_l   equ $ - tokn_eqeq
tokn_neq      db "NEQ"
tokn_neq_l    equ $ - tokn_neq
tokn_gte      db "GTE"
tokn_gte_l    equ $ - tokn_gte
tokn_lte      db "LTE"
tokn_lte_l    equ $ - tokn_lte
tokn_lbrace   db "LBRACE"
tokn_lbrace_l equ $ - tokn_lbrace
tokn_rbrace   db "RBRACE"
tokn_rbrace_l equ $ - tokn_rbrace
tokn_nl       db "NEWLINE"
tokn_nl_l     equ $ - tokn_nl
tokn_eof      db "EOF"
tokn_eof_l    equ $ - tokn_eof
tokn_else     db "ELSE"
tokn_else_l   equ $ - tokn_else
tokn_while    db "WHILE"
tokn_while_l  equ $ - tokn_while
tokn_string   db "STRING"
tokn_string_l equ $ - tokn_string
tokn_func     db "FUNC"
tokn_func_l   equ $ - tokn_func
tokn_lp       db "LPAREN"
tokn_lp_l     equ $ - tokn_lp
tokn_rp       db "RPAREN"
tokn_rp_l     equ $ - tokn_rp
tokn_comma    db "COMMA"
tokn_comma_l  equ $ - tokn_comma
tokn_return   db "RETURN"
tokn_return_l equ $ - tokn_return
tokn_break    db "BREAK"
tokn_break_l  equ $ - tokn_break
tokn_continue db "CONTINUE"
tokn_continue_l equ $ - tokn_continue
tokn_and      db "AND"
tokn_and_l    equ $ - tokn_and
tokn_or       db "OR"
tokn_or_l     equ $ - tokn_or
tokn_lbk      db "LBRACKET"
tokn_lbk_l    equ $ - tokn_lbk
tokn_rbk      db "RBRACKET"
tokn_rbk_l    equ $ - tokn_rbk
tokn_for      db "FOR"
tokn_for_l    equ $ - tokn_for
tokn_in       db "IN"
tokn_in_l     equ $ - tokn_in
tokn_module   db "MODULE"
tokn_module_l equ $ - tokn_module
tokn_import   db "IMPORT"
tokn_import_l equ $ - tokn_import
tokn_try      db "TRY"
tokn_try_l    equ $ - tokn_try
tokn_catch    db "CATCH"
tokn_catch_l  equ $ - tokn_catch
tokn_error    db "ERROR"
tokn_error_l  equ $ - tokn_error
tokn_dd       db "DOTDOT"
tokn_dd_l     equ $ - tokn_dd
tokn_dot      db "DOT"
tokn_dot_l    equ $ - tokn_dot
tokn_pct      db "PERCENT"
tokn_pct_l    equ $ - tokn_pct
tokn_argc     db "ARGC"
tokn_argc_l   equ $ - tokn_argc
tokn_arg      db "ARG"
tokn_arg_l    equ $ - tokn_arg
tokn_inttype  db "INTTYPE"
tokn_inttype_l equ $ - tokn_inttype
tokn_not       db "NOT"
tokn_not_l     equ $ - tokn_not
tokn_len       db "LEN"
tokn_len_l     equ $ - tokn_len
tokn_abs       db "ABS"
tokn_abs_l     equ $ - tokn_abs
tokn_min       db "MIN"
tokn_min_l     equ $ - tokn_min
tokn_max       db "MAX"
tokn_max_l     equ $ - tokn_max
tokn_input_int db "INPUT_INT"
tokn_input_int_l equ $ - tokn_input_int
tokn_println   db "PRINTLN"
tokn_println_l equ $ - tokn_println
tokn_true      db "TRUE"
tokn_true_l    equ $ - tokn_true
tokn_false     db "FALSE"
tokn_false_l   equ $ - tokn_false
tokn_pluseq    db "PLUSEQ"
tokn_pluseq_l  equ $ - tokn_pluseq
tokn_minuseq   db "MINUSEQ"
tokn_minuseq_l equ $ - tokn_minuseq
tokn_stareq    db "STAREQ"
tokn_stareq_l  equ $ - tokn_stareq
tokn_slasheq   db "SLASHEQ"
tokn_slasheq_l equ $ - tokn_slasheq
tokn_percenteq db "PERCENTEQ"
tokn_percenteq_l equ $ - tokn_percenteq
tokn_amp       db "AMP"
tokn_amp_l     equ $ - tokn_amp
tokn_pipe      db "PIPE"
tokn_pipe_l    equ $ - tokn_pipe
tokn_caret     db "CARET"
tokn_caret_l   equ $ - tokn_caret
tokn_tilde     db "TILDE"
tokn_tilde_l   equ $ - tokn_tilde
tokn_lshift    db "LSHIFT"
tokn_lshift_l  equ $ - tokn_lshift
tokn_rshift    db "RSHIFT"
tokn_rshift_l  equ $ - tokn_rshift
tokn_input_str db "INPUT_STR"
tokn_input_str_l equ $ - tokn_input_str
tokn_strtype   db "STRTYPE"
tokn_strtype_l equ $ - tokn_strtype
tokn_push      db "PUSH"
tokn_push_l    equ $ - tokn_push
tokn_pop       db "POP"
tokn_pop_l     equ $ - tokn_pop
tokn_elif      db "ELIF"
tokn_elif_l    equ $ - tokn_elif
tokn_read_file db "READ_FILE"
tokn_read_file_l equ $ - tokn_read_file
tokn_slice db "SLICE"
tokn_slice_l equ $ - tokn_slice
tokn_write_file db "WRITE_FILE"
tokn_write_file_l equ $ - tokn_write_file
tokn_arg_str db "ARG_STR"
tokn_arg_str_l equ $ - tokn_arg_str
tokn_find db "FIND"
tokn_find_l equ $ - tokn_find
tokn_exit db "EXIT"
tokn_exit_l equ $ - tokn_exit
tokn_append_file db "APPEND_FILE"
tokn_append_file_l equ $ - tokn_append_file

irn_nop       db "NOP"
irn_nop_l     equ $ - irn_nop
irn_const     db "CONST"
irn_const_l   equ $ - irn_const
irn_load_g    db "LOAD_G"
irn_load_g_l  equ $ - irn_load_g
irn_store_g   db "STORE_G"
irn_store_g_l equ $ - irn_store_g
irn_load_l    db "LOAD_L"
irn_load_l_l  equ $ - irn_load_l
irn_store_l   db "STORE_L"
irn_store_l_l equ $ - irn_store_l
irn_load_p    db "LOAD_P"
irn_load_p_l  equ $ - irn_load_p
irn_store_p   db "STORE_P"
irn_store_p_l equ $ - irn_store_p
irn_push      db "PUSH"
irn_push_l    equ $ - irn_push
irn_pop_rbx   db "POP_RBX"
irn_pop_rbx_l equ $ - irn_pop_rbx
irn_add       db "ADD"
irn_add_l     equ $ - irn_add
irn_sub       db "SUB"
irn_sub_l     equ $ - irn_sub
irn_mul       db "MUL"
irn_mul_l     equ $ - irn_mul
irn_div       db "DIV"
irn_div_l     equ $ - irn_div
irn_mod       db "MOD"
irn_mod_l     equ $ - irn_mod
irn_cmp       db "CMP"
irn_cmp_l     equ $ - irn_cmp
irn_jz        db "JZ"
irn_jz_l      equ $ - irn_jz
irn_jmp       db "JMP"
irn_jmp_l     equ $ - irn_jmp
irn_lbl       db "LBL"
irn_lbl_l     equ $ - irn_lbl
irn_call      db "CALL"
irn_call_l    equ $ - irn_call
irn_add_rsp   db "ADD_RSP"
irn_add_rsp_l equ $ - irn_add_rsp
irn_ret       db "RET"
irn_ret_l     equ $ - irn_ret
irn_print_int db "PRINT_INT"
irn_print_int_l equ $ - irn_print_int
irn_print_str db "PRINT_STR"
irn_print_str_l equ $ - irn_print_str
irn_fn_bgn    db "FN_BGN"
irn_fn_bgn_l  equ $ - irn_fn_bgn
irn_fn_end    db "FN_END"
irn_fn_end_l  equ $ - irn_fn_end
irn_arr_new   db "ARR_NEW"
irn_arr_new_l equ $ - irn_arr_new
irn_arr_ld    db "ARR_LD"
irn_arr_ld_l  equ $ - irn_arr_ld
irn_arr_st    db "ARR_ST"
irn_arr_st_l  equ $ - irn_arr_st
irn_set_ef    db "SET_EF"
irn_set_ef_l  equ $ - irn_set_ef
irn_clr_ef    db "CLR_EF"
irn_clr_ef_l  equ $ - irn_clr_ef
irn_jmp_tc    db "JMP_TC"
irn_jmp_tc_l  equ $ - irn_jmp_tc
irn_mod_bgn   db "MOD_BGN"
irn_mod_bgn_l equ $ - irn_mod_bgn
irn_mod_end   db "MOD_END"
irn_mod_end_l equ $ - irn_mod_end
irn_imul8     db "IMUL8"
irn_imul8_l   equ $ - irn_imul8
irn_mov_rcx   db "MOV_RCX"
irn_mov_rcx_l equ $ - irn_mov_rcx
irn_pop_rax   db "POP_RAX"
irn_pop_rax_l equ $ - irn_pop_rax
irn_inc_rax   db "INC_RAX"
irn_inc_rax_l equ $ - irn_inc_rax
irn_fe_st     db "FE_ST"
irn_fe_st_l   equ $ - irn_fe_st
irn_fe_cmp    db "FE_CMP"
irn_fe_cmp_l  equ $ - irn_fe_cmp
irn_jge       db "JGE"
irn_jge_l     equ $ - irn_jge
irn_mov_rbx   db "MOV_RBX"
irn_mov_rbx_l equ $ - irn_mov_rbx
irn_heap_st   db "HEAP_ST"
irn_heap_st_l equ $ - irn_heap_st
irn_argc      db "ARGC"
irn_argc_l    equ $ - irn_argc
irn_arg       db "ARG"
irn_arg_l     equ $ - irn_arg
irn_lnot      db "LNOT"
irn_lnot_l    equ $ - irn_lnot
irn_arr_len   db "ARR_LEN"
irn_arr_len_l equ $ - irn_arr_len
irn_abs       db "ABS"
irn_abs_l     equ $ - irn_abs
irn_min       db "MIN"
irn_min_l     equ $ - irn_min
irn_max       db "MAX"
irn_max_l     equ $ - irn_max
irn_input_int db "INPUT_INT"
irn_input_int_l equ $ - irn_input_int
irn_print_nl  db "PRINT_NL"
irn_print_nl_l equ $ - irn_print_nl
irn_band      db "BAND"
irn_band_l    equ $ - irn_band
irn_bor       db "BOR"
irn_bor_l     equ $ - irn_bor
irn_bxor      db "BXOR"
irn_bxor_l    equ $ - irn_bxor
irn_bnot      db "BNOT"
irn_bnot_l    equ $ - irn_bnot
irn_shl       db "SHL"
irn_shl_l     equ $ - irn_shl
irn_shr       db "SHR"
irn_shr_l     equ $ - irn_shr
irn_pstr_var  db "PRINT_STR_VAR"
irn_pstr_var_l equ $ - irn_pstr_var
irn_str_len   db "STR_LEN"
irn_str_len_l equ $ - irn_str_len
irn_str_eq    db "STR_EQ"
irn_str_eq_l  equ $ - irn_str_eq
irn_str_neq   db "STR_NEQ"
irn_str_neq_l equ $ - irn_str_neq
irn_input_str db "INPUT_STR"
irn_input_str_l equ $ - irn_input_str
irn_str_at    db "STR_AT"
irn_str_at_l  equ $ - irn_str_at
irn_int_to_str db "INT_TO_STR"
irn_int_to_str_l equ $ - irn_int_to_str
irn_str_to_int db "STR_TO_INT"
irn_str_to_int_l equ $ - irn_str_to_int
irn_str_concat db "STR_CONCAT"
irn_str_concat_l equ $ - irn_str_concat
irn_arr_push  db "ARR_PUSH"
irn_arr_push_l equ $ - irn_arr_push
irn_arr_pop   db "ARR_POP"
irn_arr_pop_l equ $ - irn_arr_pop
irn_str_slice db "STR_SLICE"
irn_str_slice_l equ $ - irn_str_slice
irn_read_file db "READ_FILE"
irn_read_file_l equ $ - irn_read_file
irn_write_file db "WRITE_FILE"
irn_write_file_l equ $ - irn_write_file
irn_arg_str db "ARG_STR"
irn_arg_str_l equ $ - irn_arg_str
irn_str_find db "STR_FIND"
irn_str_find_l equ $ - irn_str_find
irn_exit db "EXIT"
irn_exit_l equ $ - irn_exit
irn_append_file db "APPEND_FILE"
irn_append_file_l equ $ - irn_append_file

align 8
tok_name_ptrs:
    dq 0, tokn_var, tokn_print, tokn_if, tokn_ident, tokn_int, tokn_eq, tokn_plus
    dq tokn_minus, tokn_star, tokn_slash, tokn_gt, tokn_lt, tokn_eqeq, tokn_neq, tokn_gte
    dq tokn_lte, tokn_lbrace, tokn_rbrace, tokn_nl, tokn_eof, tokn_else, tokn_while, tokn_string
    dq tokn_func, tokn_lp, tokn_rp, tokn_comma, tokn_return, tokn_break, tokn_continue, tokn_and
    dq tokn_or, tokn_lbk, tokn_rbk, tokn_for, tokn_in, tokn_module, tokn_import, tokn_try
    dq tokn_catch, tokn_error, tokn_dd, tokn_dot, tokn_pct, tokn_argc, tokn_arg, tokn_inttype
    dq tokn_not, tokn_len, tokn_abs, tokn_min, tokn_max, tokn_input_int
    dq tokn_println, tokn_true, tokn_false, tokn_pluseq, tokn_minuseq, tokn_stareq, tokn_slasheq
    dq tokn_percenteq, tokn_amp, tokn_pipe, tokn_caret, tokn_tilde, tokn_lshift, tokn_rshift
    dq tokn_input_str, tokn_strtype, tokn_push, tokn_pop, tokn_elif, tokn_read_file, tokn_write_file
    dq tokn_arg_str
    dq tokn_find
    dq tokn_slice
    dq tokn_exit
    dq tokn_append_file

tok_name_lens:
    dq 0, tokn_var_l, tokn_print_l, tokn_if_l, tokn_ident_l, tokn_int_l, tokn_eq_l, tokn_plus_l
    dq tokn_minus_l, tokn_star_l, tokn_slash_l, tokn_gt_l, tokn_lt_l, tokn_eqeq_l, tokn_neq_l, tokn_gte_l
    dq tokn_lte_l, tokn_lbrace_l, tokn_rbrace_l, tokn_nl_l, tokn_eof_l, tokn_else_l, tokn_while_l, tokn_string_l
    dq tokn_func_l, tokn_lp_l, tokn_rp_l, tokn_comma_l, tokn_return_l, tokn_break_l, tokn_continue_l, tokn_and_l
    dq tokn_or_l, tokn_lbk_l, tokn_rbk_l, tokn_for_l, tokn_in_l, tokn_module_l, tokn_import_l, tokn_try_l
    dq tokn_catch_l, tokn_error_l, tokn_dd_l, tokn_dot_l, tokn_pct_l, tokn_argc_l, tokn_arg_l, tokn_inttype_l
    dq tokn_not_l, tokn_len_l, tokn_abs_l, tokn_min_l, tokn_max_l, tokn_input_int_l
    dq tokn_println_l, tokn_true_l, tokn_false_l, tokn_pluseq_l, tokn_minuseq_l, tokn_stareq_l, tokn_slasheq_l
    dq tokn_percenteq_l, tokn_amp_l, tokn_pipe_l, tokn_caret_l, tokn_tilde_l, tokn_lshift_l, tokn_rshift_l
    dq tokn_input_str_l, tokn_strtype_l, tokn_push_l, tokn_pop_l, tokn_elif_l, tokn_read_file_l, tokn_write_file_l
    dq tokn_arg_str_l
    dq tokn_find_l
    dq tokn_slice_l
    dq tokn_exit_l
    dq tokn_append_file_l

ir_name_ptrs:
    dq irn_nop, irn_const, irn_load_g, irn_store_g, irn_load_l, irn_store_l, irn_load_p, irn_store_p
    dq irn_push, irn_pop_rbx, irn_add, irn_sub, irn_mul, irn_div, irn_mod, irn_cmp
    dq irn_jz, irn_jmp, irn_lbl, irn_call, irn_add_rsp, irn_ret, irn_print_int, irn_print_str
    dq irn_fn_bgn, irn_fn_end, irn_arr_new, irn_arr_ld, irn_arr_st, irn_set_ef, irn_clr_ef, irn_jmp_tc
    dq irn_mod_bgn, irn_mod_end, irn_imul8, irn_mov_rcx, irn_pop_rax, irn_inc_rax, irn_fe_st, irn_fe_cmp
    dq irn_jge, irn_mov_rbx, irn_argc, irn_arg, irn_lnot, irn_arr_len, irn_abs, irn_min
    dq irn_max, irn_input_int, irn_heap_st
    dq irn_print_nl, irn_band, irn_bor, irn_bxor, irn_bnot, irn_shl, irn_shr
    dq irn_pstr_var, irn_str_len
    dq irn_str_eq, irn_str_neq, irn_input_str, irn_str_at, irn_int_to_str, irn_str_to_int, irn_str_concat
    dq irn_arr_push
    dq irn_arr_pop
    dq irn_read_file
    dq irn_write_file
    dq irn_arg_str
    dq irn_str_find
    dq irn_str_slice
    dq irn_exit
    dq irn_append_file

ir_name_lens:
    dq irn_nop_l, irn_const_l, irn_load_g_l, irn_store_g_l, irn_load_l_l, irn_store_l_l, irn_load_p_l, irn_store_p_l
    dq irn_push_l, irn_pop_rbx_l, irn_add_l, irn_sub_l, irn_mul_l, irn_div_l, irn_mod_l, irn_cmp_l
    dq irn_jz_l, irn_jmp_l, irn_lbl_l, irn_call_l, irn_add_rsp_l, irn_ret_l, irn_print_int_l, irn_print_str_l
    dq irn_fn_bgn_l, irn_fn_end_l, irn_arr_new_l, irn_arr_ld_l, irn_arr_st_l, irn_set_ef_l, irn_clr_ef_l, irn_jmp_tc_l
    dq irn_mod_bgn_l, irn_mod_end_l, irn_imul8_l, irn_mov_rcx_l, irn_pop_rax_l, irn_inc_rax_l, irn_fe_st_l, irn_fe_cmp_l
    dq irn_jge_l, irn_mov_rbx_l, irn_argc_l, irn_arg_l, irn_lnot_l, irn_arr_len_l, irn_abs_l, irn_min_l
    dq irn_max_l, irn_input_int_l, irn_heap_st_l
    dq irn_print_nl_l, irn_band_l, irn_bor_l, irn_bxor_l, irn_bnot_l, irn_shl_l, irn_shr_l
    dq irn_pstr_var_l, irn_str_len_l
    dq irn_str_eq_l, irn_str_neq_l, irn_input_str_l, irn_str_at_l, irn_int_to_str_l, irn_str_to_int_l, irn_str_concat_l
    dq irn_arr_push_l
    dq irn_arr_pop_l
    dq irn_read_file_l
    dq irn_write_file_l
    dq irn_arg_str_l
    dq irn_str_find_l
    dq irn_str_slice_l
    dq irn_exit_l
    dq irn_append_file_l

kw_var        db "var"
kw_if         db "if"
kw_else       db "else"
kw_elif       db "elif"
kw_while      db "while"
kw_for        db "for"
kw_in         db "in"
kw_func       db "func"
kw_return     db "return"
kw_break      db "break"
kw_continue   db "continue"
kw_print      db "print"
kw_and        db "and"
kw_or         db "or"
kw_module     db "module"
kw_import     db "import"
kw_try        db "try"
kw_catch      db "catch"
kw_error      db "error"
kw_argc       db "argc"
kw_arg        db "arg"
kw_int        db "int"
kw_not        db "not"
kw_len        db "len"
kw_abs        db "abs"
kw_min        db "min"
kw_max        db "max"
kw_input_int  db "input_int"
kw_input_str  db "input_str"
kw_str        db "str"
kw_println    db "println"
kw_true       db "true"
kw_false      db "false"
kw_push       db "push"
kw_pop        db "pop"
kw_read_file  db "read_file"
kw_write_file db "write_file"
kw_arg_str    db "arg_str"
kw_find       db "find"
kw_slice      db "slice"
kw_exit       db "exit"
kw_append_file db "append_file"

lp_ie         db "_ie_"
lp_id         db "_id_"
lp_ws         db "_ws_"
lp_we         db "_we_"
lp_wc         db "_wc_"
lp_cf         db "_cf_"
lp_cd         db "_cd_"
lp_tc         db "_tc_"
lp_te         db "_te_"

align 8
lbl_tbl:
    dq lp_ie, lp_id, lp_ws, lp_we
    dq lp_cf, lp_cd, lp_tc, lp_te
    dq lp_wc

; ════════════════════════════════════════════════════════════
;  Lexer dispatch table — 256 entries, tab=skip
; ════════════════════════════════════════════════════════════
align 8
lex_jt:
    times 9  dq lx_bad_char ; 00-08
    dq       lx_skip        ; 09  TAB → skip (was wrongly lx_newline)
    dq       lx_newline     ; 0A  LF
    times 2  dq lx_bad_char ; 0B-0C
    dq       lx_skip        ; 0D  CR
    times 18 dq lx_bad_char ; 0E-1F
    dq       lx_skip        ; 20  space
    dq       lx_bang        ; 21  !
    dq       lx_string      ; 22  "
    dq       lx_comment     ; 23  #
    dq       lx_bad_char    ; 24  $
    dq       lx_pct         ; 25  %
    dq       lx_amp         ; 26  &
    dq       lx_bad_char    ; 27  '
    dq       lx_lp          ; 28  (
    dq       lx_rp          ; 29  )
    dq       lx_star        ; 2A  *
    dq       lx_plus        ; 2B  +
    dq       lx_comma       ; 2C  ,
    dq       lx_minus       ; 2D  -
    dq       lx_dot         ; 2E  .
    dq       lx_slash       ; 2F  /
    times 10 dq lx_digit   ; 30-39  0-9
    dq       lx_bad_char    ; 3A  :
    dq       lx_bad_char    ; 3B  ;
    dq       lx_lt          ; 3C  <
    dq       lx_eq          ; 3D  =
    dq       lx_gt          ; 3E  >
    dq       lx_bad_char    ; 3F  ?
    dq       lx_bad_char    ; 40  @
    times 26 dq lx_ident   ; 41-5A  A-Z
    dq       lx_lbk         ; 5B  [
    dq       lx_bad_char    ; 5C  backslash
    dq       lx_rbk         ; 5D  ]
    dq       lx_caret       ; 5E  ^
    dq       lx_ident       ; 5F  _
    dq       lx_bad_char    ; 60  `
    times 26 dq lx_ident   ; 61-7A  a-z
    dq       lx_lbrace      ; 7B  {
    dq       lx_pipe        ; 7C  |
    dq       lx_rbrace      ; 7D  }
    dq       lx_tilde       ; 7E  ~
    times 129 dq lx_bad_char ; 7F-FF

align 8
kw_table:   times (64*24) db 0

align 8
kw_init_data:
    dq TOK_VAR,      kw_var,      3
    dq TOK_IF,       kw_if,       2
    dq TOK_ELSE,     kw_else,     4
    dq TOK_ELIF,     kw_elif,     4
    dq TOK_WHILE,    kw_while,    5
    dq TOK_FOR,      kw_for,      3
    dq TOK_IN,       kw_in,       2
    dq TOK_FUNC,     kw_func,     4
    dq TOK_RETURN,   kw_return,   6
    dq TOK_BREAK,    kw_break,    5
    dq TOK_CONTINUE, kw_continue, 8
    dq TOK_PRINT,    kw_print,    5
    dq TOK_AND,      kw_and,      3
    dq TOK_OR,       kw_or,       2
    dq TOK_MODULE,   kw_module,   6
    dq TOK_IMPORT,   kw_import,   6
    dq TOK_TRY,      kw_try,      3
    dq TOK_CATCH,    kw_catch,    5
    dq TOK_ERROR,    kw_error,    5
    dq TOK_ARGC,     kw_argc,     4
    dq TOK_ARG,      kw_arg,      3
    dq TOK_INTTYPE,   kw_int,       3
    dq TOK_NOT,       kw_not,       3
    dq TOK_LEN,       kw_len,       3
    dq TOK_ABS,       kw_abs,       3
    dq TOK_FMIN,      kw_min,       3
    dq TOK_FMAX,      kw_max,       3
    dq TOK_INPUT_INT, kw_input_int, 9
    dq TOK_INPUT_STR, kw_input_str, 9
    dq TOK_STRTYPE,   kw_str,       3
    dq TOK_PRINTLN,   kw_println,   7
    dq TOK_TRUE,      kw_true,      4
    dq TOK_FALSE,     kw_false,     5
    dq TOK_PUSH,      kw_push,      4
    dq TOK_POP,       kw_pop,       3
    dq TOK_READ_FILE, kw_read_file,  9
    dq TOK_ARG_STR,  kw_arg_str,  7
    dq TOK_WRITE_FILE, kw_write_file, 10
    dq TOK_FIND,      kw_find,       4
    dq TOK_SLICE,     kw_slice,      5
    dq TOK_EXIT,      kw_exit,       4
    dq TOK_APPEND_FILE, kw_append_file, 11
    dq 0, 0, 0

; ─── Generated output.asm boilerplate ───────────────────────
asm_hdr_data  db "BITS 64", 10
              db "section .data", 10
              db "    _nl db 10", 10
              db "    _arr_oom db 'array heap overflow',10", 10
              db "    _arr_oom_len equ $-_arr_oom", 10
              db "    _arr_full db 'array capacity exceeded',10", 10
              db "    _arr_full_len equ $-_arr_full", 10
              db "    _arr_empty db 'array pop: array is empty',10", 10
              db "    _arr_empty_len equ $-_arr_empty", 10
              db "    _arr_oob db 'array index out of bounds',10", 10
              db "    _arr_oob_len equ $-_arr_oob", 10
              db "    _div_zero db 'division by zero',10", 10
              db "    _div_zero_len equ $-_div_zero", 10
              db "    _int_ovf db 'integer overflow',10", 10
              db "    _int_ovf_len equ $-_int_ovf", 10
              db "    _stk_ovf db 'stack overflow: recursion too deep',10", 10
              db "    _stk_ovf_len equ $-_stk_ovf", 10
              db "    _file_open_err db 'read_file: cannot open file',10", 10
              db "    _file_open_err_len equ $-_file_open_err", 10
              db "    _file_path_err db 'read_file: path exceeds 4095 byte limit',10", 10
              db "    _file_path_err_len equ $-_file_path_err", 10
              db "    _file_read_err db 'read_file: read failed',10", 10
              db "    _file_read_err_len equ $-_file_read_err", 10
              db "    _file_ovf_err db 'read_file: file exceeds 65535 byte limit',10", 10
              db "    _file_ovf_err_len equ $-_file_ovf_err", 10
              db "    _write_open_err db 'write_file: cannot open file',10", 10
              db "    _write_open_err_len equ $-_write_open_err", 10
              db "    _write_path_err db 'write_file: path exceeds 4095 byte limit',10", 10
              db "    _write_path_err_len equ $-_write_path_err", 10
              db "    _write_err db 'write_file: write failed',10", 10
              db "    _write_err_len equ $-_write_err", 10
              db "    _append_open_err db 'append_file: cannot open file',10", 10
              db "    _append_open_err_len equ $-_append_open_err", 10
              db "    _append_path_err db 'append_file: path exceeds 4095 byte limit',10", 10
              db "    _append_path_err_len equ $-_append_path_err", 10
              db "    _append_err db 'append_file: write failed',10", 10
              db "    _append_err_len equ $-_append_err", 10
asm_hdr_dl    equ $ - asm_hdr_data

asm_hdr_bss   db "section .bss", 10
              db "    _vars   resq 513", 10
              db "    _fe     resq 32", 10
              db "    _arr_hp resq 8192", 10
              db "    _hp_top resq 1", 10
              db "    _ef     resq 1", 10
              db "    _nq_argc resq 1", 10
              db "    _nq_argv resq 1", 10
              db "    _nq_depth resq 1", 10
              db "    _nq_in_buf resb 64", 10
              db "    _nq_path_buf resb 4096", 10
              db "section .text", 10
              db "    global _start", 10
asm_hdr_bl    equ $ - asm_hdr_bss

asm_pi        db "_print_int:", 10
              db "    push rbp", 10
              db "    mov rbp, rsp", 10
              db "    sub rsp, 32", 10
              db "    lea rsi, [rbp-2]", 10
              db "    mov byte [rbp-1], 10", 10
              db "    mov rax, rdi", 10
              db "    test rax, rax", 10
              db "    jns _pi_p", 10
              db "    neg rax", 10
              db "_pi_p:", 10
              db "    mov rcx, 10", 10
              db "_pi_l:", 10
              db "    xor rdx, rdx", 10
              db "    div rcx", 10
              db "    add dl, 48", 10
              db "    mov [rsi], dl", 10
              db "    dec rsi", 10
              db "    test rax, rax", 10
              db "    jnz _pi_l", 10
              db "    test rdi, rdi", 10
              db "    jns _pi_n", 10
              db "    mov byte [rsi], 45", 10
              db "    dec rsi", 10
              db "_pi_n:", 10
              db "    inc rsi", 10
              db "    lea rdx, [rbp-1]", 10
              db "    sub rdx, rsi", 10
              db "    inc rdx", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
              db "    leave", 10
              db "    ret", 10
asm_pi_l      equ $ - asm_pi

; _arr_new(rdi=N): allocates array with capacity=N+32, count=N
; Layout: [arr-16]=capacity  [arr-8]=count  [arr+0..]=elements
asm_an        db "_arr_new:", 10
              db "    mov rax, [_hp_top]", 10
              db "    mov rcx, rax", 10
              db "    add rcx, 34", 10   ; 2 header slots + 32 push-capacity
              db "    add rcx, rdi", 10
              db "    cmp rcx, 8192", 10
              db "    jle _an_ok", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _arr_oom", 10
              db "    mov rdx, _arr_oom_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
              db "_an_ok:", 10
              db "    mov [_hp_top], rcx", 10
              db "    lea rbx, [_arr_hp+rax*8]", 10
              db "    mov rax, rdi", 10
              db "    add rax, 32", 10  ; capacity = N + 32
              db "    mov [rbx], rax", 10    ; [arr-16] = capacity
              db "    mov [rbx+8], rdi", 10  ; [arr-8]  = count
              db "    lea rax, [rbx+16]", 10 ; arr_ptr points past both headers
              db "    ret", 10
asm_an_l      equ $ - asm_an

asm_ao        db "_arr_oob_abort:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _arr_oob", 10
              db "    mov rdx, _arr_oob_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_ao_l      equ $ - asm_ao

; _arr_push(rdi=arr_ptr, rsi=val): append val, returns new count in rax
asm_ap        db "_arr_push:", 10
              db "    mov rax, [rdi-8]", 10   ; count
              db "    cmp rax, [rdi-16]", 10  ; vs capacity
              db "    jge _ap_full", 10
              db "    mov [rdi+rax*8], rsi", 10
              db "    inc qword [rdi-8]", 10
              db "    mov rax, [rdi-8]", 10   ; return new count
              db "    ret", 10
              db "_ap_full:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _arr_full", 10
              db "    mov rdx, _arr_full_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_ap_l      equ $ - asm_ap

; _arr_pop(rdi=arr_ptr): removes and returns last element in rax
asm_app       db "_arr_pop:", 10
              db "    mov rax, [rdi-8]", 10   ; count
              db "    test rax, rax", 10
              db "    jz _app_empty", 10
              db "    dec qword [rdi-8]", 10  ; count--
              db "    mov rax, [rdi-8]", 10   ; new count (= last index)
              db "    mov rax, [rdi+rax*8]", 10 ; return arr[count]
              db "    ret", 10
              db "_app_empty:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _arr_empty", 10
              db "    mov rdx, _arr_empty_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_app_l     equ $ - asm_app

asm_dz        db "_div_zero_abort:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _div_zero", 10
              db "    mov rdx, _div_zero_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_dz_l      equ $ - asm_dz

asm_io        db "_nq_int_ovf:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _int_ovf", 10
              db "    mov rdx, _int_ovf_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_io_l      equ $ - asm_io

asm_so        db "_nq_stk_ovf:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    mov rsi, _stk_ovf", 10
              db "    mov rdx, _stk_ovf_len", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_so_l      equ $ - asm_so

asm_atoi      db "_nq_atoi:", 10
              db "    push rbp", 10
              db "    mov rbp, rsp", 10
              db "    sub rsp, 16", 10
              db "    xor rax, rax", 10
              db "    test rsi, rsi", 10
              db "    jz .atoi_done", 10
              db "    mov qword [rbp-8], 0", 10
              db "    cmp byte [rsi], 45", 10
              db "    jne .atoi_loop", 10
              db "    mov qword [rbp-8], 1", 10
              db "    inc rsi", 10
              db ".atoi_loop:", 10
              db "    movzx rcx, byte [rsi]", 10
              db "    test rcx, rcx", 10
              db "    jz .atoi_sign", 10
              db "    sub rcx, 48", 10
              db "    js .atoi_sign", 10
              db "    cmp rcx, 9", 10
              db "    jg .atoi_sign", 10
              db "    imul rax, rax, 10", 10
              db "    add rax, rcx", 10
              db "    inc rsi", 10
              db "    jmp .atoi_loop", 10
              db ".atoi_sign:", 10
              db "    cmp qword [rbp-8], 0", 10
              db "    je .atoi_done", 10
              db "    neg rax", 10
              db ".atoi_done:", 10
              db "    leave", 10
              db "    ret", 10
asm_atoi_l    equ $ - asm_atoi

asm_arg       db "_nq_arg:", 10
              db "    test rdi, rdi", 10
              db "    jl .arg_oob", 10
              db "    mov rax, [_nq_argc]", 10
              db "    cmp rdi, rax", 10
              db "    jge .arg_oob", 10
              db "    mov rsi, [_nq_argv]", 10
              db "    mov rsi, [rsi+rdi*8]", 10
              db "    call _nq_atoi", 10
              db "    ret", 10
              db ".arg_oob:", 10
              db "    xor rax, rax", 10
              db "    ret", 10

asm_arg_l     equ $ - asm_arg

asm_arg_str   db "_nq_arg_str:", 10

              db "    push rbp", 10, "    mov rbp, rsp", 10
              db "    push rbx", 10, "    push r12", 10, "    push r13", 10, "    push r14", 10
              db "    mov r12, rdi", 10, "    mov r13, rsi", 10
              db "    test r13, r13", 10, "    jl .astr_empty", 10
              db "    mov rax, [_nq_argc]", 10, "    cmp r13, rax", 10, "    jge .astr_empty", 10
              db "    mov rbx, [_nq_argv]", 10, "    mov rbx, [rbx+r13*8]", 10
              db "    mov r14, r12", 10, "    imul r14, r14, 8", 10
              db "    lea rcx, [_str_ptrs]", 10, "    mov rdi, [rcx + r14]", 10
              db "    xor rcx, rcx", 10
              db ".astr_copy:", 10
              db "    cmp rcx, 4095", 10, "    jae .astr_long", 10
              db "    mov al, [rbx + rcx]", 10, "    test al, al", 10, "    jz .astr_done", 10
              db "    mov [rdi + rcx], al", 10, "    inc rcx", 10, "    jmp .astr_copy", 10
              db ".astr_done:", 10
              db "    mov byte [rdi + rcx], 0", 10
              db "    lea rdx, [_str_raw_lens]", 10, "    mov [rdx + r14], rcx", 10
              db "    lea rdx, [_str_lens]", 10, "    mov [rdx + r14], rcx", 10
              db "    mov rax, r12", 10
              db "    pop r14", 10, "    pop r13", 10, "    pop r12", 10, "    pop rbx", 10
              db "    leave", 10, "    ret", 10
              db ".astr_empty:", 10
              db "    mov r14, r12", 10, "    imul r14, r14, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10, "    mov qword [rdx + r14], 0", 10
              db "    lea rdx, [_str_lens]", 10, "    mov qword [rdx + r14], 0", 10
              db "    lea rdx, [_str_ptrs]", 10, "    mov rdx, [rdx + r14]", 10, "    mov byte [rdx], 0", 10
              db "    mov rax, r12", 10
              db "    pop r14", 10, "    pop r13", 10, "    pop r12", 10, "    pop rbx", 10
              db "    leave", 10, "    ret", 10
              db ".astr_long:", 10
              db "    mov rax, 1", 10, "    mov rdi, 2", 10, "    mov rsi, .astr_long_msg", 10
              db "    mov rdx, .astr_long_len", 10, "    syscall", 10
              db "    mov rax, 60", 10, "    mov rdi, 1", 10, "    syscall", 10
              db ".astr_long_msg db ", 34, "arg_str: argument exceeds 4095 byte limit", 34, ",10", 10
              db ".astr_long_len equ $-.astr_long_msg", 10
asm_arg_str_l equ $ - asm_arg_str

asm_start_save db "    mov rax, [rsp]", 10
               db "    dec rax", 10
               db "    mov [_nq_argc], rax", 10
               db "    lea rax, [rsp+16]", 10
               db "    mov [_nq_argv], rax", 10
asm_start_save_l equ $ - asm_start_save

asm_slbl      db "_start:", 10
asm_slbl_l    equ $ - asm_slbl
asm_footer    db "    mov rax, 60", 10
              db "    xor rdi, rdi", 10
              db "    syscall", 10
asm_footer_l  equ $ - asm_footer

; ─── NASM code fragments ────────────────────────────────────
f_push_rax   db "    push rax", 10
f_push_rax_l equ $ - f_push_rax
f_pop_rbx    db "    pop rbx", 10
f_pop_rbx_l  equ $ - f_pop_rbx
f_pop_rax_s  db "    pop rax", 10
f_pop_rax_l  equ $ - f_pop_rax_s
f_add_rbx    db "    add rax, rbx", 10
             db "    jo _nq_int_ovf", 10
f_add_l      equ $ - f_add_rbx
f_sub_rbx    db "    sub rbx, rax", 10, "    mov rax, rbx", 10
             db "    jo _nq_int_ovf", 10
f_sub_l      equ $ - f_sub_rbx
f_mul_rbx    db "    imul rax, rbx", 10
             db "    jo _nq_int_ovf", 10
f_mul_l      equ $ - f_mul_rbx
f_div_seq    db "    mov rcx, rax", 10, "    pop rax", 10
             db "    test rcx, rcx", 10, "    jz _div_zero_abort", 10
             db "    cqo", 10, "    idiv rcx", 10
f_div_l      equ $ - f_div_seq
f_mod_seq    db "    mov rcx, rax", 10, "    pop rax", 10
             db "    test rcx, rcx", 10, "    jz _div_zero_abort", 10
             db "    cqo", 10, "    idiv rcx", 10
             db "    mov rax, rdx", 10
f_mod_l      equ $ - f_mod_seq
f_vld        db "    mov rax, [_vars+"
f_vld_l      equ $ - f_vld
f_vst_a      db "    mov [_vars+"
f_vst_a_l    equ $ - f_vst_a
f_vst_b      db "], rax", 10
f_vst_b_l    equ $ - f_vst_b
f_lld        db "    mov rax, [rbp-"
f_lld_l      equ $ - f_lld
f_lst_a      db "    mov [rbp-"
f_lst_a_l    equ $ - f_lst_a
f_lst_b      db "], rax", 10
f_lst_b_l    equ $ - f_lst_b
f_pld        db "    mov rax, [rbp+"
f_pld_l      equ $ - f_pld
f_pst_a      db "    mov [rbp+"
f_pst_a_l    equ $ - f_pst_a
f_brk_nl     db "]", 10
f_brk_nl_l   equ $ - f_brk_nl
f_mv_rax     db "    mov rax, "
f_mv_rax_l   equ $ - f_mv_rax
f_mv_rdi     db "    mov rdi, "
f_mv_rdi_l   equ $ - f_mv_rdi
f_jmp_s      db "    jmp "
f_jmp_l      equ $ - f_jmp_s
f_jge_s      db "    jge "
f_jge_l      equ $ - f_jge_s
f_colon_nl   db ":", 10
f_colon_nl_l equ $ - f_colon_nl
f_nl         db 10
f_print_int  db "    mov rdi, rax", 10, "    call _print_int", 10
f_print_int_l equ $ - f_print_int
f_arr_new_c  db "    call _arr_new", 10
f_arr_new_l  equ $ - f_arr_new_c
f_arr_push_c db "    pop rdi", 10
             db "    mov rsi, rax", 10
             db "    call _arr_push", 10
f_arr_push_l equ $ - f_arr_push_c
f_arr_pop_c  db "    mov rdi, rax", 10
             db "    call _arr_pop", 10
f_arr_pop_l  equ $ - f_arr_pop_c
f_imul8      db "    imul rax, rax, 8", 10
f_imul8_l    equ $ - f_imul8
f_mv_rbx_rax db "    mov rbx, rax", 10
f_mv_rbx_l   equ $ - f_mv_rbx_rax
f_mv_rcx_rax db "    mov rcx, rax", 10
f_mv_rcx_l   equ $ - f_mv_rcx_rax
f_arr_deref  db "    pop rbx", 10
             db "    test rax, rax", 10, "    js _arr_oob_abort", 10
             db "    mov rdx, [rbx-8]", 10, "    imul rdx, rdx, 8", 10
             db "    cmp rax, rdx", 10, "    jae _arr_oob_abort", 10
             db "    add rbx, rax", 10, "    mov rax, [rbx]", 10
f_arr_deref_l equ $ - f_arr_deref
f_arr_store  db "    pop rcx", 10, "    pop rbx", 10
             db "    test rcx, rcx", 10, "    js _arr_oob_abort", 10
             db "    mov rdx, [rbx-8]", 10, "    imul rdx, rdx, 8", 10
             db "    cmp rcx, rdx", 10, "    jae _arr_oob_abort", 10
             db "    mov [rbx+rcx], rax", 10
f_arr_store_l equ $ - f_arr_store
f_argc       db "    mov rax, [_nq_argc]", 10
f_argc_l     equ $ - f_argc
f_arg        db "    mov rdi, rax", 10, "    call _nq_arg", 10
f_arg_l      equ $ - f_arg
f_exit       db "    mov rdi, rax", 10, "    mov rax, 60", 10, "    syscall", 10
f_exit_l     equ $ - f_exit
f_arg_str_pre db "    mov rsi, rax", 10, "    mov rdi, "
f_arg_str_pre_l equ $ - f_arg_str_pre
f_arg_str_call db "    call _nq_arg_str", 10
f_arg_str_call_l equ $ - f_arg_str_call
f_arg_str_buf_pfx db "_nq_arg_buf_"
f_arg_str_buf_pfx_l equ $ - f_arg_str_buf_pfx
f_arg_str_buf_sfx db " resb 4096", 10
f_arg_str_buf_sfx_l equ $ - f_arg_str_buf_sfx
f_fn_pfx     db "_fn_"
f_fn_pfx_l   equ $ - f_fn_pfx
f_fn_pro     db "    inc qword [_nq_depth]", 10
             db "    cmp qword [_nq_depth], 500", 10
             db "    jg _nq_stk_ovf", 10
             db "    push rbp", 10, "    mov rbp, rsp", 10
             db "    sub rsp, 1024", 10
f_fn_pro_l   equ $ - f_fn_pro
f_ret_lv     db "    dec qword [_nq_depth]", 10
             db "    leave", 10, "    ret", 10
f_ret_lv_l   equ $ - f_ret_lv
f_call_fn    db "    call _fn_"
f_call_fn_l  equ $ - f_call_fn
f_add_rsp    db "    add rsp, "
f_add_rsp_l  equ $ - f_add_rsp
f_set_ef     db "    mov qword [_ef], 1", 10
f_set_ef_l   equ $ - f_set_ef
f_clr_ef     db "    mov qword [_ef], 0", 10
f_clr_ef_l   equ $ - f_clr_ef
f_test_rax   db "    test rax, rax", 10, "    jz "
f_test_rax_l equ $ - f_test_rax
f_cmp_rbx    db "    cmp rbx, rax", 10
f_cmp_rbx_l  equ $ - f_cmp_rbx
f_underscore db "_"
f_str_pfx    db "_s_"
f_str_pfx_l  equ $ - f_str_pfx
f_str_db     db " db "
f_str_db_l   equ $ - f_str_db
f_dq         db 0x22
f_str_sfx    db 0x22, ",10", 10
f_str_sfx_l  equ $ - f_str_sfx
f_len_sfx    db "_len equ "
f_len_sfx_l  equ $ - f_len_sfx
f_wr_a       db "    mov rax,1", 10, "    mov rdi,1", 10
             db "    mov rsi, _s_"
f_wr_a_l     equ $ - f_wr_a
f_wr_b       db 10, "    mov rdx, _s_"
f_wr_b_l     equ $ - f_wr_b
f_wr_c       db "_len", 10, "    syscall", 10
f_wr_c_l     equ $ - f_wr_c
f_inc_rax    db "    inc rax", 10
f_inc_rax_l  equ $ - f_inc_rax
f_fe_st_a    db "    mov [_fe+"
f_fe_st_a_l  equ $ - f_fe_st_a
f_fe_st_b    db "], rax", 10
f_fe_st_b_l  equ $ - f_fe_st_b
f_fe_cmp_a   db "    cmp rax, [_fe+"
f_fe_cmp_a_l equ $ - f_fe_cmp_a

; setcc table by (tok_op - TOK_GT), 0..5
setcc_ptrs:
    dq sg_s, sl_s, se_s, sne_s, sge_s, sle_s
setcc_lens:
    dq sg_l, sl_l, se_l, sne_l, sge_l, sle_l
sg_s   db "    setg al",  10, "    movzx rax, al", 10
sg_l   equ $ - sg_s
sl_s   db "    setl al",  10, "    movzx rax, al", 10
sl_l   equ $ - sl_s
se_s   db "    sete al",  10, "    movzx rax, al", 10
se_l   equ $ - se_s
sne_s  db "    setne al", 10, "    movzx rax, al", 10
sne_l  equ $ - sne_s
sge_s  db "    setge al", 10, "    movzx rax, al", 10
sge_l  equ $ - sge_s
sle_s  db "    setle al", 10, "    movzx rax, al", 10
sle_l  equ $ - sle_s

f_lnot        db "    test rax, rax", 10
              db "    setz al", 10
              db "    movzx rax, al", 10
f_lnot_l      equ $ - f_lnot

f_arr_len     db "    mov rax, [rax-8]", 10
f_arr_len_l   equ $ - f_arr_len

f_abs         db "    mov rbx, rax", 10
              db "    neg rbx", 10
              db "    test rax, rax", 10
              db "    cmovs rax, rbx", 10
f_abs_l       equ $ - f_abs

f_min         db "    cmp rbx, rax", 10
              db "    cmovl rax, rbx", 10
f_min_l       equ $ - f_min

f_max         db "    cmp rbx, rax", 10
              db "    cmovg rax, rbx", 10
f_max_l       equ $ - f_max

f_input_int   db "    call _nq_input_int", 10
f_input_int_l equ $ - f_input_int

f_print_nl    db "    mov rax,1", 10
              db "    mov rdi,1", 10
              db "    mov rsi,_nl", 10
              db "    mov rdx,1", 10
              db "    syscall", 10
f_print_nl_l  equ $ - f_print_nl

f_band        db "    and rax, rbx", 10
f_band_l      equ $ - f_band

f_bor         db "    or rax, rbx", 10
f_bor_l       equ $ - f_bor

f_bxor        db "    xor rax, rbx", 10
f_bxor_l      equ $ - f_bxor

f_bnot        db "    not rax", 10
f_bnot_l      equ $ - f_bnot

f_shl         db "    mov rcx, rax", 10
              db "    pop rax", 10
              db "    shl rax, cl", 10
f_shl_l       equ $ - f_shl

f_shr         db "    mov rcx, rax", 10
              db "    pop rax", 10
              db "    sar rax, cl", 10
f_shr_l       equ $ - f_shr

f_pstr_var    db "    imul rax, rax, 8", 10
              db "    lea rcx, [_str_ptrs]", 10
              db "    mov rsi, [rcx + rax]", 10
              db "    lea rcx, [_str_lens]", 10
              db "    mov rdx, [rcx + rax]", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
f_pstr_var_l  equ $ - f_pstr_var

f_str_len_a   db "    imul rax, rax, 8", 10
              db "    lea rcx, [_str_raw_lens]", 10
              db "    mov rax, [rcx + rax]", 10
f_str_len_l   equ $ - f_str_len_a

f_str_at_a    db "    pop rbx", 10
              db "    imul rbx, rbx, 8", 10
              db "    lea rcx, [_str_ptrs]", 10
              db "    mov rcx, [rcx + rbx]", 10
              db "    movzx rax, byte [rcx + rax]", 10
f_str_at_l    equ $ - f_str_at_a

f_str_eq_a    db "    pop rdi", 10
              db "    mov rsi, rax", 10
              db "    call _nq_str_eq", 10
f_str_eq_l    equ $ - f_str_eq_a

f_str_neq_a   db "    pop rdi", 10
              db "    mov rsi, rax", 10
              db "    call _nq_str_eq", 10
              db "    xor rax, 1", 10
f_str_neq_l   equ $ - f_str_neq_a

f_str_find    db "    pop rdi", 10
              db "    mov rsi, rax", 10
              db "    call _nq_str_find", 10
f_str_find_l  equ $ - f_str_find

f_slice_pre   db "    mov rcx, rax", 10, "    pop rdx", 10, "    pop rsi", 10, "    mov rdi, "
f_slice_pre_l equ $ - f_slice_pre
f_slice_call  db "    call _nq_str_slice", 10, "    mov rax, "
f_slice_call_l equ $ - f_slice_call

f_istr_call   db "    call _nq_input_str", 10
f_istr_call_l equ $ - f_istr_call

asm_input_int db "_nq_input_int:", 10
              db "    xor rax, rax", 10
              db "    xor rdi, rdi", 10
              db "    lea rsi, [_nq_in_buf]", 10
              db "    mov rdx, 63", 10
              db "    syscall", 10
              db "    test rax, rax", 10
              db "    jle _nq_iint_zero", 10
              db "    lea rsi, [_nq_in_buf]", 10
              db "    call _nq_atoi", 10
              db "    ret", 10
              db "_nq_iint_zero:", 10
              db "    xor rax, rax", 10
              db "    ret", 10
asm_input_int_l equ $ - asm_input_int

; _nq_str_eq: rdi=left_idx, rsi=right_idx → rax=1 if equal, 0 if not
; Requires _str_ptrs and _str_raw_lens to be defined.
asm_str_eq    db "_nq_str_eq:", 10
              db "    imul rdi, rdi, 8", 10
              db "    imul rsi, rsi, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10
              db "    mov rcx, [rdx + rdi]", 10
              db "    cmp rcx, [rdx + rsi]", 10
              db "    jne .nse_ne", 10
              db "    test rcx, rcx", 10
              db "    jz .nse_eq", 10
              db "    lea rdx, [_str_ptrs]", 10
              db "    mov rdi, [rdx + rdi]", 10
              db "    mov rsi, [rdx + rsi]", 10
              db ".nse_loop:", 10
              db "    dec rcx", 10
              db "    js .nse_eq", 10
              db "    movzx rax, byte [rdi + rcx]", 10
              db "    cmp al, [rsi + rcx]", 10
              db "    je .nse_loop", 10
              db ".nse_ne:", 10
              db "    xor rax, rax", 10
              db "    ret", 10
              db ".nse_eq:", 10
              db "    mov rax, 1", 10
              db "    ret", 10

asm_str_eq_l  equ $ - asm_str_eq

asm_str_find  db "_nq_str_find:", 10
              db "    push rbx", 10, "    push r12", 10, "    push r13", 10, "    push r14", 10, "    push r15", 10
              db "    imul rdi, rdi, 8", 10, "    imul rsi, rsi, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10
              db "    mov r12, [rdx + rdi]", 10, "    mov r13, [rdx + rsi]", 10
              db "    lea rdx, [_str_ptrs]", 10
              db "    mov r14, [rdx + rdi]", 10, "    mov r15, [rdx + rsi]", 10
              db "    test r13, r13", 10, "    jz .sf_zero", 10
              db "    cmp r13, r12", 10, "    ja .sf_not", 10
              db "    xor rbx, rbx", 10
              db ".sf_outer:", 10
              db "    mov rax, r12", 10, "    sub rax, r13", 10, "    cmp rbx, rax", 10, "    jg .sf_not", 10
              db "    lea r8, [r14 + rbx]", 10, "    xor rcx, rcx", 10
              db ".sf_inner:", 10
              db "    cmp rcx, r13", 10, "    je .sf_found", 10
              db "    mov al, [r8 + rcx]", 10, "    cmp al, [r15 + rcx]", 10, "    jne .sf_next", 10
              db "    inc rcx", 10, "    jmp .sf_inner", 10
              db ".sf_next:", 10, "    inc rbx", 10, "    jmp .sf_outer", 10
              db ".sf_found:", 10, "    mov rax, rbx", 10, "    jmp .sf_done", 10
              db ".sf_zero:", 10, "    xor rax, rax", 10, "    jmp .sf_done", 10
              db ".sf_not:", 10, "    mov rax, -1", 10
              db ".sf_done:", 10
              db "    pop r15", 10, "    pop r14", 10, "    pop r13", 10, "    pop r12", 10, "    pop rbx", 10, "    ret", 10
asm_str_find_l equ $ - asm_str_find

asm_str_slice db "_nq_str_slice:", 10
              db "    push rbp", 10, "    mov rbp, rsp", 10
              db "    push rbx", 10, "    push r12", 10, "    push r13", 10, "    push r14", 10, "    push r15", 10
              db "    mov r12, rdi", 10, "    mov r13, rsi", 10, "    mov r14, rdx", 10, "    mov r15, rcx", 10
              db "    test r14, r14", 10, "    js .sl_bounds", 10
              db "    test r15, r15", 10, "    js .sl_bounds", 10
              db "    cmp r15, r14", 10, "    jl .sl_bounds", 10
              db "    imul r13, r13, 8", 10
              db "    lea rbx, [_str_raw_lens]", 10, "    mov rbx, [rbx + r13]", 10
              db "    cmp r15, rbx", 10, "    jg .sl_bounds", 10
              db "    mov rbx, r15", 10, "    sub rbx, r14", 10
              db "    cmp rbx, 4095", 10, "    ja .sl_ovf", 10
              db "    mov rax, r12", 10, "    imul rax, rax, 8", 10
              db "    lea rdx, [_str_ptrs]", 10, "    mov rdi, [rdx + rax]", 10
              db "    mov rax, r13", 10, "    lea rdx, [_str_ptrs]", 10, "    mov rsi, [rdx + rax]", 10, "    add rsi, r14", 10
              db "    mov rcx, rbx", 10, "    rep movsb", 10, "    mov byte [rdi], 10", 10
              db "    mov rax, r12", 10, "    imul rax, rax, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10, "    mov [rdx + rax], rbx", 10
              db "    lea rdx, [_str_lens]", 10, "    lea rcx, [rbx + 1]", 10, "    mov [rdx + rax], rcx", 10
              db "    mov rax, r12", 10, "    jmp .sl_done", 10
              db ".sl_bounds:", 10, "    lea rsi, [rel .sl_bounds_msg]", 10, "    mov rdx, 27", 10, "    jmp .sl_abort", 10
              db ".sl_ovf:", 10, "    lea rsi, [rel .sl_ovf_msg]", 10, "    mov rdx, 38", 10
              db ".sl_abort:", 10, "    mov rax, 1", 10, "    mov rdi, 2", 10, "    syscall", 10, "    mov rax, 60", 10, "    mov rdi, 1", 10, "    syscall", 10
              db ".sl_done:", 10
              db "    pop r15", 10, "    pop r14", 10, "    pop r13", 10, "    pop r12", 10, "    pop rbx", 10, "    leave", 10, "    ret", 10
              db ".sl_bounds_msg: db ", 34, "slice: index out of bounds", 34, ",10", 10
              db ".sl_ovf_msg: db ", 34, "slice: result exceeds 4095 byte limit", 34, ",10", 10
asm_str_slice_l equ $ - asm_str_slice

; _nq_input_str: rdi=slot_idx → reads line from stdin, updates tables, rax=slot_idx
; Requires _str_raw_lens and _str_lens to be defined.
asm_input_str db "_nq_input_str:", 10
              db "    push rbp", 10
              db "    mov rbp, rsp", 10
              db "    push rdi", 10
              db "    imul rdi, rdi, 8", 10
              db "    lea rcx, [_str_ptrs]", 10
              db "    mov rsi, [rcx + rdi]", 10
              db "    xor rax, rax", 10
              db "    xor rdi, rdi", 10
              db "    mov rdx, 255", 10
              db "    syscall", 10
              db "    pop rdi", 10
              db "    test rax, rax", 10
              db "    jle .istr_zero", 10
              db "    imul rcx, rdi, 8", 10
              db "    lea rdx, [_str_ptrs]", 10
              db "    mov rcx, [rdx + rcx]", 10
              db "    mov r8, rax", 10
              db "    cmp byte [rcx + r8 - 1], 10", 10
              db "    jne .istr_no_trim", 10
              db "    dec r8", 10
              db ".istr_no_trim:", 10
              db "    imul rcx, rdi, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10
              db "    mov [rdx + rcx], r8", 10
              db "    inc r8", 10
              db "    lea rdx, [_str_lens]", 10
              db "    mov [rdx + rcx], r8", 10
              db "    mov rax, rdi", 10
              db "    pop rbp", 10
              db "    ret", 10
              db ".istr_zero:", 10
              db "    imul rcx, rdi, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10
              db "    mov qword [rdx + rcx], 0", 10
              db "    lea rdx, [_str_lens]", 10
              db "    mov qword [rdx + rcx], 0", 10
              db "    mov rax, rdi", 10
              db "    pop rbp", 10
              asm_input_str_l equ $ - asm_input_str

f_istr_buf_pfx  db "_nq_istr_buf_"
f_istr_buf_pfx_l equ $ - f_istr_buf_pfx
f_istr_buf_sfx  db " resb 256", 10
f_istr_buf_sfx_l equ $ - f_istr_buf_sfx

; ── read_file(path) ─────────────────────────────────────
f_read_file_pre db "    mov rsi, rax", 10, "    mov rdi, "
f_read_file_pre_l equ $ - f_read_file_pre
f_read_file_call db "    call _nq_read_file", 10
f_read_file_call_l equ $ - f_read_file_call
f_read_file_buf_pfx db "_nq_file_buf_"
f_read_file_buf_pfx_l equ $ - f_read_file_buf_pfx
f_read_file_buf_sfx db " resb 65536", 10
f_read_file_buf_sfx_l equ $ - f_read_file_buf_sfx

asm_read_file db "_nq_read_file:", 10
              db "    push rbp", 10
              db "    mov rbp, rsp", 10
              db "    push rbx", 10
              db "    push r12", 10
              db "    push r13", 10
              db "    mov r12, rdi", 10
              db "    mov rbx, rsi", 10
              db "    imul rbx, rbx, 8", 10
              db "    lea rcx, [_str_raw_lens]", 10
              db "    mov rcx, [rcx + rbx]", 10
              db "    cmp rcx, 4095", 10
              db "    jbe .rf_path_ok", 10
              db "    mov rsi, _file_path_err", 10
              db "    mov rdx, _file_path_err_len", 10
              db "    jmp .rf_abort", 10
              db ".rf_path_ok:", 10
              db "    lea rdx, [_str_ptrs]", 10
              db "    mov rsi, [rdx + rbx]", 10
              db "    lea rdi, [_nq_path_buf]", 10
              db "    rep movsb", 10
              db "    mov byte [rdi], 0", 10
              db "    mov rax, 2", 10
              db "    lea rdi, [_nq_path_buf]", 10
              db "    xor rsi, rsi", 10
              db "    xor rdx, rdx", 10
              db "    syscall", 10
              db "    test rax, rax", 10
              db "    js .rf_open_err", 10
              db "    mov rbx, rax", 10
              db "    mov rdi, r12", 10
              db "    imul rdi, rdi, 8", 10
              db "    lea rcx, [_str_ptrs]", 10
              db "    mov rsi, [rcx + rdi]", 10
              db "    xor rax, rax", 10
              db "    mov rdi, rbx", 10
              db "    mov rdx, 65536", 10
              db "    syscall", 10
              db "    test rax, rax", 10
              db "    js .rf_read_err", 10
              db "    cmp rax, 65536", 10
              db "    je .rf_ovf_err", 10
              db "    mov r13, rax", 10
              db "    mov rax, 3", 10
              db "    mov rdi, rbx", 10
              db "    syscall", 10
              db "    mov rdi, r12", 10
              db "    imul rdi, rdi, 8", 10
              db "    lea rdx, [_str_raw_lens]", 10
              db "    mov [rdx + rdi], r13", 10
              db "    lea rdx, [_str_lens]", 10
              db "    mov [rdx + rdi], r13", 10
              db "    lea rdx, [_str_ptrs]", 10
              db "    mov rdx, [rdx + rdi]", 10
              db "    mov byte [rdx + r13], 0", 10
              db "    mov rax, r12", 10
              db "    pop r13", 10
              db "    pop r12", 10
              db "    pop rbx", 10
              db "    leave", 10
              db "    ret", 10
              db ".rf_read_err:", 10
              db "    mov rax, 3", 10
              db "    mov rdi, rbx", 10
              db "    syscall", 10
              db "    mov rsi, _file_read_err", 10
              db "    mov rdx, _file_read_err_len", 10
              db "    jmp .rf_abort", 10
              db ".rf_ovf_err:", 10
              db "    mov rax, 3", 10
              db "    mov rdi, rbx", 10
              db "    syscall", 10
              db "    mov rsi, _file_ovf_err", 10
              db "    mov rdx, _file_ovf_err_len", 10
              db "    jmp .rf_abort", 10
              db ".rf_open_err:", 10
              db "    mov rsi, _file_open_err", 10
              db "    mov rdx, _file_open_err_len", 10
              db ".rf_abort:", 10
              db "    mov rax, 1", 10
              db "    mov rdi, 2", 10
              db "    syscall", 10
              db "    mov rax, 60", 10
              db "    mov rdi, 1", 10
              db "    syscall", 10
asm_read_file_l equ $ - asm_read_file

f_write_file_call db "    mov rsi, rax", 10
                  db "    pop rdi", 10
                  db "    call _nq_write_file", 10
f_write_file_call_l equ $ - f_write_file_call

f_append_file_call db "    mov rsi, rax", 10
                   db "    pop rdi", 10
                   db "    call _nq_append_file", 10
f_append_file_call_l equ $ - f_append_file_call

asm_write_file db "_nq_write_file:", 10
               db "    push rbp", 10
               db "    mov rbp, rsp", 10
               db "    push rbx", 10
               db "    push r12", 10
               db "    push r13", 10
               db "    push r14", 10
               db "    mov r12, rdi", 10
               db "    mov r13, rsi", 10
               db "    mov rbx, r12", 10
               db "    imul rbx, rbx, 8", 10
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov rcx, [rcx + rbx]", 10
               db "    cmp rcx, 4095", 10
               db "    jbe .wf_path_ok", 10
               db "    mov rsi, _write_path_err", 10
               db "    mov rdx, _write_path_err_len", 10
               db "    jmp .wf_abort", 10
               db ".wf_path_ok:", 10
               db "    lea rdx, [_str_ptrs]", 10
               db "    mov rsi, [rdx + rbx]", 10
               db "    lea rdi, [_nq_path_buf]", 10
               db "    rep movsb", 10
               db "    mov byte [rdi], 0", 10
               db "    mov rax, 2", 10
               db "    lea rdi, [_nq_path_buf]", 10
               db "    mov rsi, 577", 10
               db "    mov rdx, 420", 10
               db "    syscall", 10
               db "    test rax, rax", 10
               db "    js .wf_open_err", 10
               db "    mov rbx, rax", 10
               db "    mov r14, r13", 10
               db "    imul r14, r14, 8", 10
               db "    lea rcx, [_str_ptrs]", 10
               db "    mov rsi, [rcx + r14]", 10
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov rdx, [rcx + r14]", 10
               db "    xor r12, r12", 10
               db ".wf_loop:", 10
               db "    test rdx, rdx", 10
               db "    jz .wf_close_ok", 10
               db "    mov rax, 1", 10
               db "    mov rdi, rbx", 10
               db "    syscall", 10
               db "    test rax, rax", 10
               db "    jle .wf_write_err", 10
               db "    add rsi, rax", 10
               db "    sub rdx, rax", 10
               db "    add r12, rax", 10
               db "    jmp .wf_loop", 10
               db ".wf_close_ok:", 10
               db "    mov rax, 3", 10
               db "    mov rdi, rbx", 10
               db "    syscall", 10
               db "    mov rax, r12", 10
               db "    pop r14", 10
               db "    pop r13", 10
               db "    pop r12", 10
               db "    pop rbx", 10
               db "    leave", 10
               db "    ret", 10
               db ".wf_write_err:", 10
               db "    mov rax, 3", 10
               db "    mov rdi, rbx", 10
               db "    syscall", 10
               db "    mov rsi, _write_err", 10
               db "    mov rdx, _write_err_len", 10
               db "    jmp .wf_abort", 10
               db ".wf_open_err:", 10
               db "    mov rsi, _write_open_err", 10
               db "    mov rdx, _write_open_err_len", 10
               db ".wf_abort:", 10
               db "    mov rax, 1", 10
               db "    mov rdi, 2", 10
               db "    syscall", 10
               db "    mov rax, 60", 10
               db "    mov rdi, 1", 10
               db "    syscall", 10
asm_write_file_l equ $ - asm_write_file

asm_append_file db "_nq_append_file:", 10
               db "    push rbp", 10
               db "    mov rbp, rsp", 10
               db "    push rbx", 10
               db "    push r12", 10
               db "    push r13", 10
               db "    push r14", 10
               db "    mov r12, rdi", 10
               db "    mov r13, rsi", 10
               db "    mov rbx, r12", 10
               db "    imul rbx, rbx, 8", 10
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov rcx, [rcx + rbx]", 10
               db "    cmp rcx, 4095", 10
               db "    jbe .af_path_ok", 10
               db "    mov rsi, _append_path_err", 10
               db "    mov rdx, _append_path_err_len", 10
               db "    jmp .af_abort", 10
               db ".af_path_ok:", 10
               db "    lea rdx, [_str_ptrs]", 10
               db "    mov rsi, [rdx + rbx]", 10
               db "    lea rdi, [_nq_path_buf]", 10
               db "    rep movsb", 10
               db "    mov byte [rdi], 0", 10
               db "    mov rax, 2", 10
               db "    lea rdi, [_nq_path_buf]", 10
               db "    mov rsi, 1089", 10
               db "    mov rdx, 420", 10
               db "    syscall", 10
               db "    test rax, rax", 10
               db "    js .af_open_err", 10
               db "    mov rbx, rax", 10
               db "    mov r14, r13", 10
               db "    imul r14, r14, 8", 10
               db "    lea rcx, [_str_ptrs]", 10
               db "    mov rsi, [rcx + r14]", 10
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov rdx, [rcx + r14]", 10
               db "    xor r12, r12", 10
               db ".af_loop:", 10
               db "    test rdx, rdx", 10
               db "    jz .af_close_ok", 10
               db "    mov rax, 1", 10
               db "    mov rdi, rbx", 10
               db "    syscall", 10
               db "    test rax, rax", 10
               db "    jle .af_append_err", 10
               db "    add rsi, rax", 10
               db "    sub rdx, rax", 10
               db "    add r12, rax", 10
               db "    jmp .af_loop", 10
               db ".af_close_ok:", 10
               db "    mov rax, 3", 10
               db "    mov rdi, rbx", 10
               db "    syscall", 10
               db "    mov rax, r12", 10
               db "    pop r14", 10
               db "    pop r13", 10
               db "    pop r12", 10
               db "    pop rbx", 10
               db "    leave", 10
               db "    ret", 10
               db ".af_append_err:", 10
               db "    mov rax, 3", 10
               db "    mov rdi, rbx", 10
               db "    syscall", 10
               db "    mov rsi, _append_err", 10
               db "    mov rdx, _append_err_len", 10
               db "    jmp .af_abort", 10
               db ".af_open_err:", 10
               db "    mov rsi, _append_open_err", 10
               db "    mov rdx, _append_open_err_len", 10
               db ".af_abort:", 10
               db "    mov rax, 1", 10
               db "    mov rdi, 2", 10
               db "    syscall", 10
               db "    mov rax, 60", 10
               db "    mov rdi, 1", 10
               db "    syscall", 10
asm_append_file_l equ $ - asm_append_file

; ── str(n) / int-to-str ─────────────────────────────────────
; Codegen fragment: emit "    mov rdi, N\n    call _nq_int_to_str_slot\n"
; (the "mov rdi, N" part is emitted by cg_int_to_str separately)
f_its_call    db "    call _nq_int_to_str_slot", 10
f_its_call_l  equ $ - f_its_call

; Named buffer fragments for multi-slot ITS
f_its_bss_hdr  db "section .bss", 10
f_its_bss_hdr_l equ $ - f_its_bss_hdr
f_its_buf_pfx  db "_nq_its_buf_"
f_its_buf_pfx_l equ $ - f_its_buf_pfx
f_its_buf_sfx  db " resb 32", 10
f_its_buf_sfx_l equ $ - f_its_buf_sfx
f_its_sec_dat  db "section .data", 10
f_its_sec_dat_l equ $ - f_its_sec_dat

asm_int_to_str db "_nq_int_to_str_slot:", 10
               db "    push rbp", 10
               db "    mov rbp, rsp", 10
               db "    sub rsp, 48", 10
               db "    mov [rbp-8], rdi", 10
               db "    mov [rbp-16], rax", 10
               db "    lea rsi, [rbp-18]", 10
               db "    mov byte [rbp-17], 10", 10
               db "    test rax, rax", 10
               db "    jns .its_p", 10
               db "    neg rax", 10
               db ".its_p:", 10
               db "    mov rcx, 10", 10
               db ".its_l:", 10
               db "    xor rdx, rdx", 10
               db "    div rcx", 10
               db "    add dl, 48", 10
               db "    mov [rsi], dl", 10
               db "    dec rsi", 10
               db "    test rax, rax", 10
               db "    jnz .its_l", 10
               db "    mov rax, [rbp-16]", 10
               db "    test rax, rax", 10
               db "    jns .its_n", 10
               db "    mov byte [rsi], 45", 10
               db "    dec rsi", 10
               db ".its_n:", 10
               db "    inc rsi", 10
               db "    lea rdx, [rbp-17]", 10
               db "    sub rdx, rsi", 10
               db "    mov rdi, [rbp-8]", 10
               db "    imul rax, rdi, 8", 10
               db "    lea rcx, [_str_ptrs]", 10
               db "    mov rdi, [rcx + rax]", 10
               db "    mov rcx, rdx", 10
               db "    inc rcx", 10
               db "    rep movsb", 10
               db "    mov rdi, [rbp-8]", 10
               db "    imul rax, rdi, 8", 10
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov [rcx+rax], rdx", 10
               db "    inc rdx", 10
               db "    lea rcx, [_str_lens]", 10
               db "    mov [rcx+rax], rdx", 10
               db "    mov rax, rdi", 10
               db "    leave", 10
               db "    ret", 10
asm_int_to_str_l equ $ - asm_int_to_str

; ── int(s) / str-to-int ─────────────────────────────────────
; Fragment: rax=string_slot → rax=integer via _nq_atoi
; _nq_atoi(rsi=ptr): stops at null or non-digit, no len needed
f_sti_a       db "    imul rax, rax, 8", 10
              db "    lea rcx, [_str_ptrs]", 10
              db "    mov rsi, [rcx + rax]", 10
              db "    call _nq_atoi", 10
f_sti_a_l     equ $ - f_sti_a

; ── str_concat ──────────────────────────────────────────────
; Codegen fragments: emit "    mov rdx, rax\n    mov rsi, rbx\n    mov rdi, N\n"
;                   then "    call _nq_str_concat\n    mov rax, N\n"
f_scat_pre    db "    mov rdx, rax", 10, "    mov rsi, rbx", 10, "    mov rdi, "
f_scat_pre_l  equ $ - f_scat_pre
f_scat_call   db "    call _nq_str_concat", 10, "    mov rax, "
f_scat_call_l equ $ - f_scat_call

f_scat_buf_pfx  db "_nq_strcat_buf_"
f_scat_buf_pfx_l equ $ - f_scat_buf_pfx
f_scat_buf_sfx  db " resb 4096", 10
f_scat_buf_sfx_l equ $ - f_scat_buf_sfx

; _nq_str_concat: rdi=dst_slot, rsi=left_slot, rdx=right_slot
; Concatenates left+right into dst buffer; updates _str_raw_lens/_str_lens.
asm_str_concat db "_nq_str_concat:", 10
               db "    push rbp", 10
               db "    mov rbp, rsp", 10
               db "    sub rsp, 16", 10
               db "    mov [rbp-8], rdi", 10       ; save dst_slot
               db "    imul rsi, rsi, 8", 10        ; left_off = left_slot*8
               db "    imul rdx, rdx, 8", 10        ; right_off = right_slot*8
               db "    lea rcx, [_str_ptrs]", 10
               db "    mov r8, [rcx + rsi]", 10     ; r8 = left_ptr
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov r9, [rcx + rsi]", 10     ; r9 = left_len
               db "    lea rcx, [_str_ptrs]", 10
               db "    mov r10, [rcx + rdx]", 10    ; r10 = right_ptr
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov r11, [rcx + rdx]", 10    ; r11 = right_len
               db "    mov rax, r9", 10
               db "    add rax, r11", 10
               db "    cmp rax, 4095", 10
               db "    jae .scat_ovf", 10
               db "    imul rdi, rdi, 8", 10        ; dst_off = dst_slot*8
               db "    lea rcx, [_str_ptrs]", 10
               db "    mov rdi, [rcx + rdi]", 10    ; rdi = dst_ptr
               db "    mov rsi, r8", 10             ; src = left_ptr
               db "    mov rcx, r9", 10             ; count = left_len
               db "    rep movsb", 10               ; copy left into dst
               db "    mov rsi, r10", 10            ; src = right_ptr
               db "    mov rcx, r11", 10            ; count = right_len
               db "    rep movsb", 10               ; copy right into dst+left_len
               db "    mov byte [rdi], 10", 10      ; append newline for print
               db "    mov rdi, [rbp-8]", 10        ; restore dst_slot
               db "    imul rdi, rdi, 8", 10        ; dst_off
               db "    lea rcx, [_str_raw_lens]", 10
               db "    mov rax, r9", 10
               db "    add rax, r11", 10            ; total_raw = left_len+right_len
               db "    mov [rcx + rdi], rax", 10
               db "    inc rax", 10
               db "    lea rcx, [_str_lens]", 10
               db "    mov [rcx + rdi], rax", 10    ; total_lens = total_raw+1
               db "    leave", 10
               db "    ret", 10
               db ".scat_ovf:", 10
               db "    mov rax, 1", 10
               db "    mov rdi, 2", 10
               db "    lea rsi, [rel .scat_ovf_msg]", 10
               db "    mov rdx, .scat_ovf_msg_l", 10
               db "    syscall", 10
               db "    mov rax, 60", 10
               db "    mov rdi, 1", 10
               db "    syscall", 10
               db ".scat_ovf_msg: db 'error: string concat overflow (limit 4095 bytes)',10", 10
               db ".scat_ovf_msg_l equ $-.scat_ovf_msg", 10
asm_str_concat_l equ $ - asm_str_concat
