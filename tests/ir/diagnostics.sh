#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

write_case "$TMP_DIR/ir_diag_bad_array.nq" <<'EOF'
var a = [1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bad-array" "$TMP_DIR/ir_diag_bad_array.nq" ""

write_case "$TMP_DIR/ir_diag_invalid_char.nq" <<'EOF'
print @
EOF
assert_frontend_export_ir_fail_parity "ir-diag-invalid-character" "$TMP_DIR/ir_diag_invalid_char.nq" "invalid character"

write_case "$TMP_DIR/ir_diag_bare_bang.nq" <<'EOF'
print !
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bare-bang" "$TMP_DIR/ir_diag_bare_bang.nq" "invalid character"

printf 'print \200\n' > "$TMP_DIR/ir_diag_non_ascii_byte.nq"
assert_frontend_export_ir_fail_parity "ir-diag-non-ascii-byte" "$TMP_DIR/ir_diag_non_ascii_byte.nq" "invalid character"

printf 'print \001\n' > "$TMP_DIR/ir_diag_control_byte.nq"
assert_frontend_export_ir_fail_parity "ir-diag-control-byte" "$TMP_DIR/ir_diag_control_byte.nq" "invalid character"

write_case "$TMP_DIR/ir_diag_identifier_too_long.nq" <<'EOF'
var aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-identifier-too-long" "$TMP_DIR/ir_diag_identifier_too_long.nq" "line 1, col 4: identifier too long"

write_case "$TMP_DIR/ir_diag_undef_fn.nq" <<'EOF'
print nope(1)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-undefined-function" "$TMP_DIR/ir_diag_undef_fn.nq" "undefined function"

write_case "$TMP_DIR/ir_diag_arity.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(1)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-wrong-arity" "$TMP_DIR/ir_diag_arity.nq" "wrong number of function arguments"

write_case "$TMP_DIR/ir_diag_push_value_type.nq" <<'EOF'
var a = int[]
push(a, "x")
EOF
assert_frontend_export_ir_fail_parity "ir-diag-push-value-type" "$TMP_DIR/ir_diag_push_value_type.nq" "push() value type does not match array element type"

write_case "$TMP_DIR/ir_diag_call_missing_comma.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(1 2)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-call-missing-comma" "$TMP_DIR/ir_diag_call_missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/ir_diag_call_missing_rparen.nq" <<'EOF'
func f(a) {
return a
}
print f(1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-call-missing-rparen" "$TMP_DIR/ir_diag_call_missing_rparen.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/ir_diag_call_missing_expr_eof.nq" <<'EOF'
func f(a) {
return a
}
print f(
EOF
assert_frontend_export_ir_fail_parity "ir-diag-call-missing-expr-eof" "$TMP_DIR/ir_diag_call_missing_expr_eof.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_modcall_missing_rparen.nq" <<'EOF'
module m {
func f(a) {
return a
}
}
print m.f(1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-modcall-missing-rparen" "$TMP_DIR/ir_diag_modcall_missing_rparen.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/ir_diag_call_trailing_comma.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(1, )
EOF
assert_frontend_export_ir_fail_parity "ir-diag-call-trailing-comma" "$TMP_DIR/ir_diag_call_trailing_comma.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_call_leading_comma.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(, 2)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-call-leading-comma" "$TMP_DIR/ir_diag_call_leading_comma.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_modcall_missing_name.nq" <<'EOF'
print demo.(1)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-modcall-missing-name" "$TMP_DIR/ir_diag_modcall_missing_name.nq" "expected function name after '.'"

write_case "$TMP_DIR/ir_diag_modcall_bad_name.nq" <<'EOF'
print demo.1(2)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-modcall-bad-name" "$TMP_DIR/ir_diag_modcall_bad_name.nq" "expected function name after '.'"

write_case "$TMP_DIR/ir_diag_modcall_unknown_module.nq" <<'EOF'
func ping() {
return 1
}
print nope.ping()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-modcall-unknown-module" "$TMP_DIR/ir_diag_modcall_unknown_module.nq" "unknown module name"

write_case "$TMP_DIR/ir_diag_modcall_no_paren.nq" <<'EOF'
func foo() {
return 7
}
print demo.foo
EOF
assert_frontend_export_ir_fail_parity "ir-diag-modcall-no-paren" "$TMP_DIR/ir_diag_modcall_no_paren.nq" "expected '(' after function name"

write_case "$TMP_DIR/ir_diag_index_call_chain.nq" <<'EOF'
var a = [1]
print a[0](2)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-index-call-chain" "$TMP_DIR/ir_diag_index_call_chain.nq" "chained call/index/member access is not supported"

write_case "$TMP_DIR/ir_diag_nested_index_chain.nq" <<'EOF'
var a = [1]
print a[0][0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-nested-index-chain" "$TMP_DIR/ir_diag_nested_index_chain.nq" "chained call/index/member access is not supported"

write_case "$TMP_DIR/ir_diag_call_call_chain.nq" <<'EOF'
func one() {
return 1
}
print one()(2)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-call-call-chain" "$TMP_DIR/ir_diag_call_call_chain.nq" "chained call/index/member access is not supported"

write_case "$TMP_DIR/ir_diag_bare_ident_stmt.nq" <<'EOF'
var x = 1
x
print 7
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bare-ident-stmt" "$TMP_DIR/ir_diag_bare_ident_stmt.nq" "expected assignment or call after identifier"

write_case "$TMP_DIR/ir_diag_bad_lhs_int.nq" <<'EOF'
var x = 1
1 = x
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bad-lhs-int" "$TMP_DIR/ir_diag_bad_lhs_int.nq" "invalid assignment target"

write_case "$TMP_DIR/ir_diag_bad_lhs_paren.nq" <<'EOF'
(1 + 2) = 3
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bad-lhs-paren" "$TMP_DIR/ir_diag_bad_lhs_paren.nq" "invalid assignment target"

write_case "$TMP_DIR/ir_diag_int_expr_stmt.nq" <<'EOF'
1 + 2
print 7
EOF
assert_frontend_export_ir_fail_parity "ir-diag-int-expr-stmt" "$TMP_DIR/ir_diag_int_expr_stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/ir_diag_string_expr_stmt.nq" <<'EOF'
"hello"
print 7
EOF
assert_frontend_export_ir_fail_parity "ir-diag-string-expr-stmt" "$TMP_DIR/ir_diag_string_expr_stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/ir_diag_paren_expr_stmt.nq" <<'EOF'
(1 + 2)
print 7
EOF
assert_frontend_export_ir_fail_parity "ir-diag-paren-expr-stmt" "$TMP_DIR/ir_diag_paren_expr_stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/ir_diag_array_expr_stmt.nq" <<'EOF'
[1,2,3]
print 7
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-expr-stmt" "$TMP_DIR/ir_diag_array_expr_stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/ir_diag_param_missing_comma.nq" <<'EOF'
func add(a b) {
return a + b
}
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-param-missing-comma" "$TMP_DIR/ir_diag_param_missing_comma.nq" "expected ',' or ')' in parameter list"

write_case "$TMP_DIR/ir_diag_param_trailing_comma.nq" <<'EOF'
func add(a, ) {
return a
}
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-param-trailing-comma" "$TMP_DIR/ir_diag_param_trailing_comma.nq" "expected ',' or ')' in parameter list"

write_case "$TMP_DIR/ir_diag_param_bad_int.nq" <<'EOF'
func add(1) {
return 1
}
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-param-bad-int" "$TMP_DIR/ir_diag_param_bad_int.nq" "expected parameter name"

write_case "$TMP_DIR/ir_diag_param_bad_tail_int.nq" <<'EOF'
func add(a, 1) {
return a
}
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-param-bad-tail-int" "$TMP_DIR/ir_diag_param_bad_tail_int.nq" "expected parameter name"

write_case "$TMP_DIR/ir_diag_func_missing_name.nq" <<'EOF'
func {
print 1
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-func-missing-name" "$TMP_DIR/ir_diag_func_missing_name.nq" "expected function name"

write_case "$TMP_DIR/ir_diag_func_no_parens.nq" <<'EOF'
func add {
return 7
}
print add()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-func-no-parens" "$TMP_DIR/ir_diag_func_no_parens.nq" "expected '(' after function name"

write_case "$TMP_DIR/ir_diag_nested_func.nq" <<'EOF'
func outer() {
func inner() {
return 1
}
return inner()
}
print outer()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-nested-func" "$TMP_DIR/ir_diag_nested_func.nq" "declaration must appear at top level"

write_case "$TMP_DIR/ir_diag_module_dup_func_no_cascade.nq" <<'EOF'
func ping() {
return 1
}
module demo {
func ping() {
print 2
return 2
}
}
print demo.ping()
EOF
direct_err="$TMP_DIR/ir_diag_module_dup_func_no_cascade.direct.err"
export_err="$TMP_DIR/ir_diag_module_dup_func_no_cascade.export.err"
export_ir="$TMP_DIR/ir_diag_module_dup_func_no_cascade.ir"
if "$ROOT_DIR/nql" "$TMP_DIR/ir_diag_module_dup_func_no_cascade.nq" >"$direct_err" 2>&1; then
    printf 'FAIL %s\nexpected direct compiler failure\n' "ir-diag-module-dup-func-no-cascade" >&2
    exit 1
fi
if "$ROOT_DIR/nql" --export-ir "$export_ir" "$TMP_DIR/ir_diag_module_dup_func_no_cascade.nq" >"$export_err" 2>&1; then
    printf 'FAIL %s\nexpected export-ir compiler failure\n' "ir-diag-module-dup-func-no-cascade" >&2
    exit 1
fi
if ! grep -q -- "duplicate function name" "$direct_err"; then
    printf 'FAIL %s\nmissing direct duplicate function error\n' "ir-diag-module-dup-func-no-cascade" >&2
    exit 1
fi
if grep -q -- "return outside function" "$direct_err"; then
    printf 'FAIL %s\nunexpected direct cascade error\n' "ir-diag-module-dup-func-no-cascade" >&2
    exit 1
fi
if ! grep -q -- "duplicate function name" "$export_err"; then
    printf 'FAIL %s\nmissing export-ir duplicate function error\n' "ir-diag-module-dup-func-no-cascade" >&2
    exit 1
fi
if grep -q -- "return outside function" "$export_err"; then
    printf 'FAIL %s\nunexpected export-ir cascade error\n' "ir-diag-module-dup-func-no-cascade" >&2
    exit 1
fi
if ! cmp -s "$direct_err" "$export_err"; then
    printf 'FAIL %s\ndirect output:\n%s\nexport-ir output:\n%s\n' \
        "ir-diag-module-dup-func-no-cascade" \
        "$(cat "$direct_err")" \
        "$(cat "$export_err")" >&2
    exit 1
fi
printf 'PASS %s\n' "ir-diag-module-dup-func-no-cascade"

write_case "$TMP_DIR/ir_diag_module_missing_name.nq" <<'EOF'
module
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-module-missing-name" "$TMP_DIR/ir_diag_module_missing_name.nq" "expected module name"

write_case "$TMP_DIR/ir_diag_module_duplicate_name.nq" <<'EOF'
module demo {
print 1
}
module demo {
print 2
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-module-duplicate-name" "$TMP_DIR/ir_diag_module_duplicate_name.nq" "duplicate module name"

write_case "$TMP_DIR/ir_diag_module_extra_header.nq" <<'EOF'
module demo extra
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-module-extra-header" "$TMP_DIR/ir_diag_module_extra_header.nq" "expected '{' after module name"

write_case "$TMP_DIR/ir_diag_nested_module.nq" <<'EOF'
func outer() {
module demo {
print 1
}
return 2
}
print outer()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-nested-module" "$TMP_DIR/ir_diag_nested_module.nq" "declaration must appear at top level"

write_case "$TMP_DIR/ir_diag_import_missing_name.nq" <<'EOF'
import
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-import-missing-name" "$TMP_DIR/ir_diag_import_missing_name.nq" "expected import name"

write_case "$TMP_DIR/ir_diag_import_extra_header.nq" <<'EOF'
import demo extra
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-import-extra-header" "$TMP_DIR/ir_diag_import_extra_header.nq" "unexpected token after import name"

write_case "$TMP_DIR/ir_diag_nested_import.nq" <<'EOF'
func outer() {
import demo
return 2
}
print outer()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-nested-import" "$TMP_DIR/ir_diag_nested_import.nq" "declaration must appear at top level"

write_case "$TMP_DIR/ir_diag_import_after_stmt.nq" <<'EOF'
print 1
import demo
EOF
assert_frontend_export_ir_fail_parity "ir-diag-import-after-stmt" "$TMP_DIR/ir_diag_import_after_stmt.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/ir_diag_import_after_var.nq" <<'EOF'
var x = 1
import demo
EOF
assert_frontend_export_ir_fail_parity "ir-diag-import-after-var" "$TMP_DIR/ir_diag_import_after_var.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/ir_diag_module_after_stmt.nq" <<'EOF'
print 1
module demo {
print 2
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-module-after-stmt" "$TMP_DIR/ir_diag_module_after_stmt.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/ir_diag_module_after_var.nq" <<'EOF'
var x = 1
module demo {
print 2
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-module-after-var" "$TMP_DIR/ir_diag_module_after_var.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/ir_diag_func_after_stmt.nq" <<'EOF'
print 1
func add() {
return 2
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-func-after-stmt" "$TMP_DIR/ir_diag_func_after_stmt.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/ir_diag_func_no_block.nq" <<'EOF'
func add(a)
print a
EOF
assert_frontend_export_ir_fail_parity "ir-diag-func-no-block" "$TMP_DIR/ir_diag_func_no_block.nq" "expected '{' to start block body"

write_case "$TMP_DIR/ir_diag_module_no_block.nq" <<'EOF'
module demo
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-module-no-block" "$TMP_DIR/ir_diag_module_no_block.nq" "expected '{' to start block body"

write_case "$TMP_DIR/ir_diag_catch_no_block.nq" <<'EOF'
try {
error "x"
} catch
print 7
EOF
assert_frontend_export_ir_fail_parity "ir-diag-catch-no-block" "$TMP_DIR/ir_diag_catch_no_block.nq" "expected '{' to start block body"

write_case "$TMP_DIR/ir_diag_for_missing_start.nq" <<'EOF'
for i in ..3 {
print i
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-for-missing-start" "$TMP_DIR/ir_diag_for_missing_start.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_for_missing_end.nq" <<'EOF'
for i in 1.. {
print i
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-for-missing-end" "$TMP_DIR/ir_diag_for_missing_end.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_for_range_start_type.nq" <<'EOF'
for i in "abc"..3 {
print i
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-for-range-start-type" "$TMP_DIR/ir_diag_for_range_start_type.nq" "type error: for range bounds must be integers"

write_case "$TMP_DIR/ir_diag_for_range_end_type.nq" <<'EOF'
for i in 0.."abc" {
print i
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-for-range-end-type" "$TMP_DIR/ir_diag_for_range_end_type.nq" "type error: for range bounds must be integers"

write_case "$TMP_DIR/ir_diag_for_each_int_type.nq" <<'EOF'
for x in 7 {
print x
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-for-each-int-type" "$TMP_DIR/ir_diag_for_each_int_type.nq" "type error: for-each source must be an array"

write_case "$TMP_DIR/ir_diag_for_each_str_type.nq" <<'EOF'
for x in "abc" {
print x
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-for-each-str-type" "$TMP_DIR/ir_diag_for_each_str_type.nq" "type error: for-each source must be an array"

write_case "$TMP_DIR/ir_diag_if_missing_cond.nq" <<'EOF'
if {
print 1
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-if-missing-cond" "$TMP_DIR/ir_diag_if_missing_cond.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_if_and_missing_rhs.nq" <<'EOF'
if 1 == 1 and {
print 1
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-if-and-missing-rhs" "$TMP_DIR/ir_diag_if_and_missing_rhs.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_while_missing_cond.nq" <<'EOF'
while {
print 1
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-while-missing-cond" "$TMP_DIR/ir_diag_while_missing_cond.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_return_outside.nq" <<'EOF'
return 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-return-outside" "$TMP_DIR/ir_diag_return_outside.nq" "return outside function"

write_case "$TMP_DIR/ir_diag_return_missing_value.nq" <<'EOF'
func f() {
return ,
}
print f()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-return-missing-value" "$TMP_DIR/ir_diag_return_missing_value.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_break_outside.nq" <<'EOF'
break
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-break-outside" "$TMP_DIR/ir_diag_break_outside.nq" "break/continue outside loop"

write_case "$TMP_DIR/ir_diag_continue_outside.nq" <<'EOF'
continue
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-continue-outside" "$TMP_DIR/ir_diag_continue_outside.nq" "break/continue outside loop"

write_case "$TMP_DIR/ir_diag_try_no_catch.nq" <<'EOF'
try {
print 1
}
print 2
EOF
assert_frontend_export_ir_fail_parity "ir-diag-try-no-catch" "$TMP_DIR/ir_diag_try_no_catch.nq" "expected 'catch' after try block"

write_case "$TMP_DIR/ir_diag_error_outside_try.nq" <<'EOF'
error "boom"
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-error-outside-try" "$TMP_DIR/ir_diag_error_outside_try.nq" "error statement outside try"

write_case "$TMP_DIR/ir_diag_error_bad_payload.nq" <<'EOF'
try {
error 1
} catch {
print 7
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-error-bad-payload" "$TMP_DIR/ir_diag_error_bad_payload.nq" "error payload must be a string literal"

write_case "$TMP_DIR/ir_diag_unterminated_string.nq" <<'EOF'
var s = "abc
print s
EOF
assert_frontend_export_ir_fail_parity "ir-diag-unterminated-string" "$TMP_DIR/ir_diag_unterminated_string.nq" "line 1, col 8: unterminated string literal"

write_case "$TMP_DIR/ir_diag_catch_without_try.nq" <<'EOF'
catch {
print 1
}
EOF
assert_frontend_export_ir_fail_parity "ir-diag-catch-without-try" "$TMP_DIR/ir_diag_catch_without_try.nq" "unexpected statement"

write_case "$TMP_DIR/ir_diag_array_trailing_comma.nq" <<'EOF'
var a = [1,]
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-trailing-comma" "$TMP_DIR/ir_diag_array_trailing_comma.nq" "expected array item"

write_case "$TMP_DIR/ir_diag_array_double_comma.nq" <<'EOF'
var a = [1,,2]
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-double-comma" "$TMP_DIR/ir_diag_array_double_comma.nq" "expected array item"

write_case "$TMP_DIR/ir_diag_array_mixed_int_string.nq" <<'EOF'
var a = [1,"x"]
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-mixed-int-string" "$TMP_DIR/ir_diag_array_mixed_int_string.nq" "type error: array literal elements must have the same type"

write_case "$TMP_DIR/ir_diag_array_mixed_string_int.nq" <<'EOF'
var a = ["x",1]
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-mixed-string-int" "$TMP_DIR/ir_diag_array_mixed_string_int.nq" "type error: array literal elements must have the same type"

python3 - <<'PY' > "$TMP_DIR/ir_diag_array_too_large.nq"
items = ",".join(str(i) for i in range(8159))
print(f"var a = [{items}]")
print("print a[0]")
PY
assert_frontend_export_ir_fail_parity "ir-diag-array-too-large" "$TMP_DIR/ir_diag_array_too_large.nq" "array literal exceeds fixed heap capacity"

write_case "$TMP_DIR/ir_diag_negative_array_index.nq" <<'EOF'
var a = [1,2,3]
print a[-1]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-negative-array-index" "$TMP_DIR/ir_diag_negative_array_index.nq" "negative array index not allowed"

write_case "$TMP_DIR/ir_diag_var_missing_init.nq" <<'EOF'
var x =
print x
EOF
assert_frontend_export_ir_fail_parity "ir-diag-var-missing-init" "$TMP_DIR/ir_diag_var_missing_init.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_assign_missing_rhs.nq" <<'EOF'
var x = 1
x =
print x
EOF
assert_frontend_export_ir_fail_parity "ir-diag-assign-missing-rhs" "$TMP_DIR/ir_diag_assign_missing_rhs.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_array_assign_missing_rhs.nq" <<'EOF'
var a = [1,2,3]
a[1] =
print a[1]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-assign-missing-rhs" "$TMP_DIR/ir_diag_array_assign_missing_rhs.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_empty_array_load_index.nq" <<'EOF'
var a = [1,2,3]
print a[]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-empty-array-load-index" "$TMP_DIR/ir_diag_empty_array_load_index.nq" "expected array index"

write_case "$TMP_DIR/ir_diag_empty_array_store_index.nq" <<'EOF'
var a = [1,2,3]
a[] = 9
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-empty-array-store-index" "$TMP_DIR/ir_diag_empty_array_store_index.nq" "expected array index"

write_case "$TMP_DIR/ir_diag_array_load_string_index.nq" <<'EOF'
var a = [1,2,3]
print a["x"]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-load-string-index" "$TMP_DIR/ir_diag_array_load_string_index.nq" "type error: index must be an integer"

write_case "$TMP_DIR/ir_diag_string_load_string_index.nq" <<'EOF'
var s = "abc"
print s["x"]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-string-load-string-index" "$TMP_DIR/ir_diag_string_load_string_index.nq" "type error: index must be an integer"

write_case "$TMP_DIR/ir_diag_array_store_string_index.nq" <<'EOF'
var a = [1,2,3]
a["x"] = 9
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-store-string-index" "$TMP_DIR/ir_diag_array_store_string_index.nq" "type error: index must be an integer"

write_case "$TMP_DIR/ir_diag_string_index_store.nq" <<'EOF'
var s = "abc"
s[0] = 99
print s
EOF
assert_frontend_export_ir_fail_parity "ir-diag-string-index-store" "$TMP_DIR/ir_diag_string_index_store.nq" "type error: indexed assignment requires an array"

write_case "$TMP_DIR/ir_diag_int_index_store.nq" <<'EOF'
var x = 7
x[0] = 1
print x
EOF
assert_frontend_export_ir_fail_parity "ir-diag-int-index-store" "$TMP_DIR/ir_diag_int_index_store.nq" "type error: indexed assignment requires an array"

write_case "$TMP_DIR/ir_diag_int_array_store_string.nq" <<'EOF'
var a = [1]
a[0] = "x"
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-int-array-store-string" "$TMP_DIR/ir_diag_int_array_store_string.nq" "type error: array assignment value type does not match element type"

write_case "$TMP_DIR/ir_diag_str_array_store_int.nq" <<'EOF'
var a = str[]
push(a, "x")
a[0] = 7
print a[0]
EOF
assert_frontend_export_ir_fail_parity "ir-diag-str-array-store-int" "$TMP_DIR/ir_diag_str_array_store_int.nq" "type error: array assignment value type does not match element type"

write_case "$TMP_DIR/ir_diag_typed_int_array_missing_rbracket.nq" <<'EOF'
var a = int[
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-typed-int-array-missing-rbracket" "$TMP_DIR/ir_diag_typed_int_array_missing_rbracket.nq" "expected ']' after typed array marker"

write_case "$TMP_DIR/ir_diag_typed_str_array_missing_rbracket.nq" <<'EOF'
var a = str[
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-typed-str-array-missing-rbracket" "$TMP_DIR/ir_diag_typed_str_array_missing_rbracket.nq" "expected ']' after typed array marker"

write_case "$TMP_DIR/ir_diag_paren_missing_rparen.nq" <<'EOF'
print (1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-paren-missing-rparen" "$TMP_DIR/ir_diag_paren_missing_rparen.nq" "expected ')' after expression"

write_case "$TMP_DIR/ir_diag_array_load_missing_rbracket.nq" <<'EOF'
var a = [1]
print a[0
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-load-missing-rbracket" "$TMP_DIR/ir_diag_array_load_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/ir_diag_string_load_missing_rbracket.nq" <<'EOF'
var s = "ab"
print s[0
EOF
assert_frontend_export_ir_fail_parity "ir-diag-string-load-missing-rbracket" "$TMP_DIR/ir_diag_string_load_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/ir_diag_array_assign_missing_rbracket.nq" <<'EOF'
var a = [1]
a[0 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-assign-missing-rbracket" "$TMP_DIR/ir_diag_array_assign_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/ir_diag_array_assign_missing_eq.nq" <<'EOF'
var a = [1]
a[0] 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-array-assign-missing-eq" "$TMP_DIR/ir_diag_array_assign_missing_eq.nq" "expected '=' in assignment"

write_case "$TMP_DIR/ir_diag_bitwise_str_lhs.nq" <<'EOF'
var s = "x"
print s & 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bitwise-str-lhs" "$TMP_DIR/ir_diag_bitwise_str_lhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/ir_diag_shift_str_rhs.nq" <<'EOF'
var s = "x"
print 1 << s
EOF
assert_frontend_export_ir_fail_parity "ir-diag-shift-str-rhs" "$TMP_DIR/ir_diag_shift_str_rhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/ir_diag_unary_minus_str.nq" <<'EOF'
var s = "x"
print -s
EOF
assert_frontend_export_ir_fail_parity "ir-diag-unary-minus-str" "$TMP_DIR/ir_diag_unary_minus_str.nq" "type error: integer operand required"

write_case "$TMP_DIR/ir_diag_bitwise_not_str.nq" <<'EOF'
var s = "x"
print ~s
EOF
assert_frontend_export_ir_fail_parity "ir-diag-bitwise-not-str" "$TMP_DIR/ir_diag_bitwise_not_str.nq" "type error: integer operand required"

write_case "$TMP_DIR/ir_diag_logical_not_str.nq" <<'EOF'
var s = "x"
print not s
EOF
assert_frontend_export_ir_fail_parity "ir-diag-logical-not-str" "$TMP_DIR/ir_diag_logical_not_str.nq" "type error: integer operand required"

write_case "$TMP_DIR/ir_diag_abs_str.nq" <<'EOF'
print abs("x")
EOF
assert_frontend_export_ir_fail_parity "ir-diag-abs-str" "$TMP_DIR/ir_diag_abs_str.nq" "type error: integer operand required"

write_case "$TMP_DIR/ir_diag_str_builtin_string.nq" <<'EOF'
print str("x")
EOF
assert_frontend_export_ir_fail_parity "ir-diag-str-builtin-string" "$TMP_DIR/ir_diag_str_builtin_string.nq" "type error: str() argument must be an integer"

write_case "$TMP_DIR/ir_diag_int_builtin_int.nq" <<'EOF'
print int(1)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-int-builtin-int" "$TMP_DIR/ir_diag_int_builtin_int.nq" "type error: int() argument must be a string"

write_case "$TMP_DIR/ir_diag_min_str_lhs.nq" <<'EOF'
print min("x", 1)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-min-str-lhs" "$TMP_DIR/ir_diag_min_str_lhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/ir_diag_max_str_rhs.nq" <<'EOF'
print max(1, "x")
EOF
assert_frontend_export_ir_fail_parity "ir-diag-max-str-rhs" "$TMP_DIR/ir_diag_max_str_rhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/ir_diag_println_trailing_comma.nq" <<'EOF'
println 1,
EOF
assert_frontend_export_ir_fail_parity "ir-diag-println-trailing-comma" "$TMP_DIR/ir_diag_println_trailing_comma.nq" "expected print item"

write_case "$TMP_DIR/ir_diag_builtin_missing_rparen.nq" <<'EOF'
var a = [1]
print len(a
EOF
assert_frontend_export_ir_fail_parity "ir-diag-builtin-missing-rparen" "$TMP_DIR/ir_diag_builtin_missing_rparen.nq" "expected ')' after builtin argument list"

write_case "$TMP_DIR/ir_diag_builtin_missing_comma.nq" <<'EOF'
print min(1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-builtin-missing-comma" "$TMP_DIR/ir_diag_builtin_missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/ir_diag_push_missing_comma.nq" <<'EOF'
var a = [1]
push(a 2)
EOF
assert_frontend_export_ir_fail_parity "ir-diag-push-missing-comma" "$TMP_DIR/ir_diag_push_missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/ir_diag_builtin_missing_lparen.nq" <<'EOF'
print len
EOF
assert_frontend_export_ir_fail_parity "ir-diag-builtin-missing-lparen" "$TMP_DIR/ir_diag_builtin_missing_lparen.nq" "expected '(' after builtin name"

write_case "$TMP_DIR/ir_diag_arg_missing_lparen.nq" <<'EOF'
print arg
EOF
assert_frontend_export_ir_fail_parity "ir-diag-arg-missing-lparen" "$TMP_DIR/ir_diag_arg_missing_lparen.nq" "expected '(' after builtin name"

write_case "$TMP_DIR/ir_diag_arg_missing_rparen.nq" <<'EOF'
print arg(1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-arg-missing-rparen" "$TMP_DIR/ir_diag_arg_missing_rparen.nq" "expected ')' after builtin argument list"

write_case "$TMP_DIR/ir_diag_arg_missing_expr.nq" <<'EOF'
print arg()
EOF
assert_frontend_export_ir_fail_parity "ir-diag-arg-missing-expr" "$TMP_DIR/ir_diag_arg_missing_expr.nq" "expected expression"

write_case "$TMP_DIR/ir_diag_arg_type_err.nq" <<'EOF'
print arg("x")
EOF
assert_frontend_export_ir_fail_parity "ir-diag-arg-type-err" "$TMP_DIR/ir_diag_arg_type_err.nq" "type error: arg() index must be an integer"

write_case "$TMP_DIR/ir_diag_dup_fn.nq" <<'EOF'
func add(a, b) {
return a + b
}
func add(x, y) {
return x - y
}
print 1
EOF
assert_frontend_export_ir_fail_parity "ir-diag-duplicate-function" "$TMP_DIR/ir_diag_dup_fn.nq" "duplicate function name"


cat > "$TMP_DIR/ir_diag_call_name.json" <<'EOF'
[
  {"index": 0, "op": "FN_BGN", "a": 0, "b": 0, "line": 1, "name": "outer"},
  {"index": 1, "op": "CALL", "a": 0, "b": 0, "line": 2, "name": "foo"},
  {"index": 2, "op": "ADD_RSP", "a": 8, "b": 0, "line": 2},
  {"index": 3, "op": "RET", "a": 0, "b": 0, "line": 3},
  {"index": 4, "op": "FN_END", "a": 0, "b": 0, "line": 4}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-call-name-context" "$TMP_DIR/ir_diag_call_name.json" "source line 2, op CALL, name foo.*function 'outer'.*CALL needs 1 args but stack has 0"

cat > "$TMP_DIR/ir_diag_bad_label.json" <<'EOF'
[
  {"index": 0, "op": "LBL", "a": 1, "b": 99, "line": 1}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-bad-label-type" "$TMP_DIR/ir_diag_bad_label.json" "source line 1, op LBL.*unsupported label type 99"

cat > "$TMP_DIR/ir_diag_bad_fallthrough.json" <<'EOF'
[
  {"index": 0, "op": "FN_BGN", "a": 0, "b": 0, "line": 1, "name": "broken"},
  {"index": 1, "op": "CONST", "a": 0, "b": 0, "line": 2},
  {"index": 2, "op": "JZ", "a": 7, "b": 1, "line": 3},
  {"index": 3, "op": "FN_END", "a": 0, "b": 0, "line": 4}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-missing-fallthrough" "$TMP_DIR/ir_diag_bad_fallthrough.json" "source line 3, op JZ.*function 'broken'.*control flow requires a fallthrough block"

cat > "$TMP_DIR/ir_diag_fn_missing_name.json" <<'EOF'
[
  {"index": 0, "op": "FN_BGN", "a": 0, "b": 0, "line": 1},
  {"index": 1, "op": "FN_END", "a": 0, "b": 0, "line": 2}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-fn-missing-name" "$TMP_DIR/ir_diag_fn_missing_name.json" "source line 1, op FN_BGN.*FN_BGN missing name"

cat > "$TMP_DIR/ir_diag_missing_fn_end.json" <<'EOF'
[
  {"index": 0, "op": "FN_BGN", "a": 0, "b": 0, "line": 1, "name": "dangling"},
  {"index": 1, "op": "CONST", "a": 7, "b": 0, "line": 2}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-missing-fn-end" "$TMP_DIR/ir_diag_missing_fn_end.json" "source line 1, op FN_BGN, name dangling.*missing FN_END for dangling"

cat > "$TMP_DIR/ir_diag_print_str_missing_text.json" <<'EOF'
[
  {"index": 0, "op": "PRINT_STR", "a": 0, "b": 0, "line": 1}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-print-str-missing-text" "$TMP_DIR/ir_diag_print_str_missing_text.json" "source line 1, op PRINT_STR.*PRINT_STR is missing exported text"

cat > "$TMP_DIR/ir_diag_pop_rbx_empty.json" <<'EOF'
[
  {"index": 0, "op": "POP_RBX", "a": 0, "b": 0, "line": 1}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-pop-rbx-empty" "$TMP_DIR/ir_diag_pop_rbx_empty.json" "source line 1, op POP_RBX.*POP_RBX on empty stack"

cat > "$TMP_DIR/ir_diag_ret_without_current.json" <<'EOF'
[
  {"index": 0, "op": "FN_BGN", "a": 0, "b": 0, "line": 1, "name": "empty_ret"},
  {"index": 1, "op": "RET", "a": 0, "b": 0, "line": 2},
  {"index": 2, "op": "FN_END", "a": 0, "b": 0, "line": 3}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-ret-without-current" "$TMP_DIR/ir_diag_ret_without_current.json" "source line 2, op RET.*function 'empty_ret'.*RET without current value"

cat > "$TMP_DIR/ir_diag_arr_ld_missing_base.json" <<'EOF'
[
  {"index": 0, "op": "CONST", "a": 8, "b": 0, "line": 1},
  {"index": 1, "op": "ARR_LD", "a": 0, "b": 0, "line": 2}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-arr-ld-missing-base" "$TMP_DIR/ir_diag_arr_ld_missing_base.json" "source line 2, op ARR_LD.*\\[main\\].*ARR_LD missing base or offset"

cat > "$TMP_DIR/ir_diag_arr_st_missing_rcx.json" <<'EOF'
[
  {"index": 0, "op": "CONST", "a": 123, "b": 0, "line": 1},
  {"index": 1, "op": "PUSH", "a": 0, "b": 0, "line": 1},
  {"index": 2, "op": "CONST", "a": 456, "b": 0, "line": 2},
  {"index": 3, "op": "ARR_ST", "a": 0, "b": 0, "line": 3}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-arr-st-missing-rcx" "$TMP_DIR/ir_diag_arr_st_missing_rcx.json" "source line 3, op ARR_ST.*\\[main\\].*ARR_ST missing offset on stack"

cat > "$TMP_DIR/ir_diag_heap_st_missing_state.json" <<'EOF'
[
  {"index": 0, "op": "CONST", "a": 5, "b": 0, "line": 1},
  {"index": 1, "op": "HEAP_ST", "a": 0, "b": 0, "line": 2}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-heap-st-missing-state" "$TMP_DIR/ir_diag_heap_st_missing_state.json" "source line 2, op HEAP_ST.*\\[main\\].*HEAP_ST missing operand state"

cat > "$TMP_DIR/ir_diag_push_without_current.json" <<'EOF'
[
  {"index": 0, "op": "PUSH", "a": 0, "b": 0, "line": 1}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-push-without-current" "$TMP_DIR/ir_diag_push_without_current.json" "source line 1, op PUSH.*\\[main\\].*PUSH without current value"

cat > "$TMP_DIR/ir_diag_pop_rax_empty.json" <<'EOF'
[
  {"index": 0, "op": "POP_RAX", "a": 0, "b": 0, "line": 1}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-pop-rax-empty" "$TMP_DIR/ir_diag_pop_rax_empty.json" "source line 1, op POP_RAX.*\\[main\\].*POP_RAX on empty stack"

cat > "$TMP_DIR/ir_diag_bool_cmp_missing_operand.json" <<'EOF'
[
  {"index": 0, "op": "BOOL_CMP", "a": 13, "b": 0, "line": 1}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-bool-cmp-missing-operand" "$TMP_DIR/ir_diag_bool_cmp_missing_operand.json" "source line 1, op BOOL_CMP.*\\[main\\].*BOOL_CMP missing operand state"

cat > "$TMP_DIR/ir_diag_bad_param_offset.json" <<'EOF'
[
  {"index": 0, "op": "FN_BGN", "a": 0, "b": 0, "line": 1, "name": "bad_param"},
  {"index": 1, "op": "LOAD_P", "a": 17, "b": 0, "line": 2},
  {"index": 2, "op": "RET", "a": 0, "b": 0, "line": 3},
  {"index": 3, "op": "FN_END", "a": 0, "b": 0, "line": 4}
]
EOF
assert_ir_json_to_llvm_fail "ir-diag-bad-param-offset" "$TMP_DIR/ir_diag_bad_param_offset.json" "source line 2, op LOAD_P.*function 'bad_param'.*unsupported parameter offset 17"
