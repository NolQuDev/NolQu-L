#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

assert_cli_fail() {
    local name="$1"
    local pattern="$2"
    shift 2
    local err_file="$TMP_DIR/${name}.err"
    if "$@" >"$err_file" 2>&1; then
        printf 'FAIL %s\nexpected CLI failure\n' "$name" >&2
        exit 1
    fi
    if ! grep -q -- "$pattern" "$err_file"; then
        printf 'FAIL %s\nmissing CLI error message\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

write_case "$TMP_DIR/cli_ok.nq" <<'EOF'
print 1
EOF
write_case "$TMP_DIR/cli_extra.nq" <<'EOF'
print 2
EOF
assert_cli_fail "cli-unknown-flag" "unknown option: --definitely-unknown" "$ROOT_DIR/nql" --definitely-unknown "$TMP_DIR/cli_ok.nq"
assert_cli_fail "cli-missing-emit-path" "--emit requires a path" "$ROOT_DIR/nql" "$TMP_DIR/cli_ok.nq" --emit
assert_cli_fail "cli-emit-path-is-option" "--emit requires a path" "$ROOT_DIR/nql" "$TMP_DIR/cli_ok.nq" --emit --release
assert_cli_fail "cli-export-ir-path-is-option" "--export-ir requires a path" "$ROOT_DIR/nql" --export-ir --release "$TMP_DIR/cli_ok.nq"
assert_cli_fail "cli-emit-subcommand-path-is-option" "emit requires a path" "$ROOT_DIR/nql" emit --release "$TMP_DIR/cli_ok.nq"
assert_cli_fail "cli-export-ir-subcommand-path-is-option" "export-ir requires a path" "$ROOT_DIR/nql" export-ir --release "$TMP_DIR/cli_ok.nq"
assert_cli_fail "cli-unknown-backend" "unknown backend: nope" "$ROOT_DIR/nql" --backend nope "$TMP_DIR/cli_ok.nq"
assert_cli_fail "cli-extra-source" "unexpected argument" "$ROOT_DIR/nql" "$TMP_DIR/cli_ok.nq" "$TMP_DIR/cli_extra.nq"
assert_cli_fail "compiler-unknown-flag" "unknown option: --definitely-unknown" qemu-x86_64 "$ROOT_DIR/build/nqlc-r0" --definitely-unknown "$TMP_DIR/cli_ok.nq"
assert_cli_fail "compiler-missing-emit-path" "--emit requires a path" qemu-x86_64 "$ROOT_DIR/build/nqlc-r0" "$TMP_DIR/cli_ok.nq" --emit
assert_cli_fail "compiler-emit-path-is-option" "--emit requires a path" qemu-x86_64 "$ROOT_DIR/build/nqlc-r0" "$TMP_DIR/cli_ok.nq" --emit --release
assert_cli_fail "compiler-extra-source" "unexpected argument" qemu-x86_64 "$ROOT_DIR/build/nqlc-r0" "$TMP_DIR/cli_ok.nq" "$TMP_DIR/cli_extra.nq"
if [[ -e /dev/full ]]; then
    assert_cli_fail "emit-write-failure" "write failed" "$ROOT_DIR/nql" --emit /dev/full "$TMP_DIR/cli_ok.nq"
fi

write_case "$TMP_DIR/invalid_char.nq" <<'EOF'
print @
EOF
assert_compile_fail "invalid-character" "$TMP_DIR/invalid_char.nq" "invalid character"

write_case "$TMP_DIR/bare_bang.nq" <<'EOF'
print !
EOF
assert_compile_fail "bare-bang" "$TMP_DIR/bare_bang.nq" "invalid character"

printf 'print \200\n' > "$TMP_DIR/non_ascii_byte.nq"
assert_compile_fail "non-ascii-byte" "$TMP_DIR/non_ascii_byte.nq" "invalid character"

printf 'print \001\n' > "$TMP_DIR/control_byte.nq"
assert_compile_fail "control-byte" "$TMP_DIR/control_byte.nq" "invalid character"

write_case "$TMP_DIR/identifier_too_long.nq" <<'EOF'
var aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = 1
EOF
assert_compile_fail "identifier-too-long" "$TMP_DIR/identifier_too_long.nq" "line 1, col 4: identifier too long"

write_case "$TMP_DIR/unterminated_block_comment.nq" <<'EOF'
print 1
/* missing end
print 2
EOF
assert_compile_fail "unterminated-block-comment" "$TMP_DIR/unterminated_block_comment.nq" "line 2, col 0: unterminated block comment"

write_case "$TMP_DIR/empty_hex_literal.nq" <<'EOF'
print 0x
EOF
assert_compile_fail "empty-hex-literal" "$TMP_DIR/empty_hex_literal.nq" "line 1, col 8: expected hex digit after 0x"

write_case "$TMP_DIR/bad_hex_literal.nq" <<'EOF'
print 0x1g
EOF
assert_compile_fail "bad-hex-literal" "$TMP_DIR/bad_hex_literal.nq" "line 1, col 9: invalid hex digit"

write_case "$TMP_DIR/hex_literal_overflow.nq" <<'EOF'
print 0x8000000000000000
EOF
assert_compile_fail "hex-literal-overflow" "$TMP_DIR/hex_literal_overflow.nq" "line 1, col 6: integer literal overflow"

write_case "$TMP_DIR/empty_binary_literal.nq" <<'EOF'
print 0b
EOF
assert_compile_fail "empty-binary-literal" "$TMP_DIR/empty_binary_literal.nq" "line 1, col 8: expected binary digit after 0b"

write_case "$TMP_DIR/bad_binary_literal.nq" <<'EOF'
print 0b102
EOF
assert_compile_fail "bad-binary-literal" "$TMP_DIR/bad_binary_literal.nq" "line 1, col 10: invalid binary digit"

write_case "$TMP_DIR/binary_literal_overflow.nq" <<'EOF'
print 0b1000000000000000000000000000000000000000000000000000000000000000
EOF
assert_compile_fail "binary-literal-overflow" "$TMP_DIR/binary_literal_overflow.nq" "line 1, col 6: integer literal overflow"

write_case "$TMP_DIR/bad_decimal_separator.nq" <<'EOF'
print 1_
EOF
assert_compile_fail "bad-decimal-separator" "$TMP_DIR/bad_decimal_separator.nq" "line 1, col 7: invalid digit separator"

write_case "$TMP_DIR/bad_hex_separator.nq" <<'EOF'
print 0x_ff
EOF
assert_compile_fail "bad-hex-separator" "$TMP_DIR/bad_hex_separator.nq" "line 1, col 8: invalid digit separator"

write_case "$TMP_DIR/bad_binary_separator.nq" <<'EOF'
print 0b10_
EOF
assert_compile_fail "bad-binary-separator" "$TMP_DIR/bad_binary_separator.nq" "line 1, col 10: invalid digit separator"

write_case "$TMP_DIR/separated_decimal_overflow.nq" <<'EOF'
print 9_999_999_999_999_999_999_9
EOF
assert_compile_fail "separated-decimal-overflow" "$TMP_DIR/separated_decimal_overflow.nq" "line 1, col 6: integer literal overflow"

python3 - "$TMP_DIR/token_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join("print 1\n" for _ in range(8200)))
PY
assert_compile_fail "token-overflow" "$TMP_DIR/token_overflow.nq" "line 5462, col 0: token buffer overflow"

python3 - "$TMP_DIR/function_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join(f"func f{i}() {{\nreturn 1\n}}\n" for i in range(520)))
PY
assert_compile_fail "function-table-overflow" "$TMP_DIR/function_table_overflow.nq" "line 1537, col 12: function table overflow"

python3 - "$TMP_DIR/local_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("func f() {\n" + "".join(f"var v{i} = {i}\n" for i in range(70)) + "return 1\n}\n")
PY
assert_compile_fail "local-table-overflow" "$TMP_DIR/local_table_overflow.nq" "line 66, col 12: too many local variables (max 64)"

python3 - "$TMP_DIR/global_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join(f"var g{i} = {i}\n" for i in range(520)))
PY
assert_compile_fail "global-table-overflow" "$TMP_DIR/global_table_overflow.nq" "line 513, col 14: symbol table full"

python3 - "$TMP_DIR/module_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join(f"module m{i} {{\n}}\n" for i in range(520)))
PY
assert_compile_fail "module-table-overflow" "$TMP_DIR/module_table_overflow.nq" "line 1025, col 12: module table overflow"

python3 - "$TMP_DIR/string_literal_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join('print "' + ("x" * 1000) + '"\n' for _ in range(300)))
PY
assert_compile_fail "string-literal-overflow" "$TMP_DIR/string_literal_overflow.nq" "string data buffer overflow"

python3 - "$TMP_DIR/output_buffer_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("var a = [" + ",".join("1" for _ in range(8000)) + "]\nprint len(a)\n")
PY
assert_compile_fail "output-buffer-overflow" "$TMP_DIR/output_buffer_overflow.nq" "line 1, col 0: output buffer overflow"

write_case "$TMP_DIR/bad_array.nq" <<'EOF'
var a = [1
EOF
assert_compile_fail "bad-array" "$TMP_DIR/bad_array.nq" ""

write_case "$TMP_DIR/undef_fn.nq" <<'EOF'
print nope(1)
EOF
assert_compile_fail "undefined-function" "$TMP_DIR/undef_fn.nq" "undefined function"

write_case "$TMP_DIR/arity.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(1)
EOF
assert_compile_fail "wrong-arity" "$TMP_DIR/arity.nq" "wrong number of function arguments"

write_case "$TMP_DIR/zero_arg_arity.nq" <<'EOF'
func one() {
return 1
}
print one(1)
EOF
assert_compile_fail "wrong-arity-zero-arg" "$TMP_DIR/zero_arg_arity.nq" "wrong number of function arguments"

write_case "$TMP_DIR/max_arg_arity.nq" <<'EOF'
func pack(a,b,c,d,e,f,g,h) {
return a
}
print pack(1,2,3,4,5,6,7)
EOF
assert_compile_fail "wrong-arity-max-arg" "$TMP_DIR/max_arg_arity.nq" "wrong number of function arguments"

write_case "$TMP_DIR/call_missing_comma.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(1 2)
EOF
assert_compile_fail "call-missing-comma" "$TMP_DIR/call_missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/call_missing_rparen.nq" <<'EOF'
func f(a) {
return a
}
print f(1
EOF
assert_compile_fail "call-missing-rparen" "$TMP_DIR/call_missing_rparen.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/call_missing_expr_eof.nq" <<'EOF'
func f(a) {
return a
}
print f(
EOF
assert_compile_fail "call-missing-expr-eof" "$TMP_DIR/call_missing_expr_eof.nq" "expected expression"

write_case "$TMP_DIR/modcall_missing_rparen.nq" <<'EOF'
module m {
func f(a) {
return a
}
}
print m.f(1
EOF
assert_compile_fail "modcall-missing-rparen" "$TMP_DIR/modcall_missing_rparen.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/call_trailing_comma.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(1, )
EOF
assert_compile_fail "call-trailing-comma" "$TMP_DIR/call_trailing_comma.nq" "expected expression"

write_case "$TMP_DIR/call-leading-comma.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(, 2)
EOF
assert_compile_fail "call-leading-comma" "$TMP_DIR/call-leading-comma.nq" "expected expression"

write_case "$TMP_DIR/modcall-missing-name.nq" <<'EOF'
print demo.(1)
EOF
assert_compile_fail "modcall-missing-name" "$TMP_DIR/modcall-missing-name.nq" "expected function name after '.'"

write_case "$TMP_DIR/modcall-bad-name.nq" <<'EOF'
print demo.1(2)
EOF
assert_compile_fail "modcall-bad-name" "$TMP_DIR/modcall-bad-name.nq" "expected function name after '.'"

write_case "$TMP_DIR/modcall-unknown-module.nq" <<'EOF'
func ping() {
return 1
}
print nope.ping()
EOF
assert_compile_fail "modcall-unknown-module" "$TMP_DIR/modcall-unknown-module.nq" "unknown module name"

write_case "$TMP_DIR/modcall-no-paren.nq" <<'EOF'
func foo() {
return 7
}
print demo.foo
EOF
assert_compile_fail "modcall-no-paren" "$TMP_DIR/modcall-no-paren.nq" "expected '(' after function name"

write_case "$TMP_DIR/index-call-chain.nq" <<'EOF'
var a = [1]
print a[0](2)
EOF
assert_compile_fail "index-call-chain" "$TMP_DIR/index-call-chain.nq" "chained call/index/member access is not supported"

write_case "$TMP_DIR/nested-index-chain.nq" <<'EOF'
var a = [1]
print a[0][0]
EOF
assert_compile_fail "nested-index-chain" "$TMP_DIR/nested-index-chain.nq" "chained call/index/member access is not supported"

write_case "$TMP_DIR/call-call-chain.nq" <<'EOF'
func one() {
return 1
}
print one()(2)
EOF
assert_compile_fail "call-call-chain" "$TMP_DIR/call-call-chain.nq" "chained call/index/member access is not supported"

write_case "$TMP_DIR/bare-ident-stmt.nq" <<'EOF'
var x = 1
x
print 7
EOF
assert_compile_fail "bare-ident-stmt" "$TMP_DIR/bare-ident-stmt.nq" "expected assignment or call after identifier"

write_case "$TMP_DIR/bad-lhs-int.nq" <<'EOF'
var x = 1
1 = x
EOF
assert_compile_fail "bad-lhs-int" "$TMP_DIR/bad-lhs-int.nq" "invalid assignment target"

write_case "$TMP_DIR/bad-lhs-paren.nq" <<'EOF'
(1 + 2) = 3
EOF
assert_compile_fail "bad-lhs-paren" "$TMP_DIR/bad-lhs-paren.nq" "invalid assignment target"

write_case "$TMP_DIR/int-expr-stmt.nq" <<'EOF'
1 + 2
print 7
EOF
assert_compile_fail "int-expr-stmt" "$TMP_DIR/int-expr-stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/string-expr-stmt.nq" <<'EOF'
"hello"
print 7
EOF
assert_compile_fail "string-expr-stmt" "$TMP_DIR/string-expr-stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/paren-expr-stmt.nq" <<'EOF'
(1 + 2)
print 7
EOF
assert_compile_fail "paren-expr-stmt" "$TMP_DIR/paren-expr-stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/array-expr-stmt.nq" <<'EOF'
[1,2,3]
print 7
EOF
assert_compile_fail "array-expr-stmt" "$TMP_DIR/array-expr-stmt.nq" "only call expressions may be used as statements"

write_case "$TMP_DIR/param_missing_comma.nq" <<'EOF'
func add(a b) {
return a + b
}
print 1
EOF
assert_compile_fail "param-missing-comma" "$TMP_DIR/param_missing_comma.nq" "expected ',' or ')' in parameter list"

write_case "$TMP_DIR/param_trailing_comma.nq" <<'EOF'
func add(a, ) {
return a
}
print 1
EOF
assert_compile_fail "param-trailing-comma" "$TMP_DIR/param_trailing_comma.nq" "expected ',' or ')' in parameter list"

write_case "$TMP_DIR/param-bad-int.nq" <<'EOF'
func add(1) {
return 1
}
print 1
EOF
assert_compile_fail "param-bad-int" "$TMP_DIR/param-bad-int.nq" "expected parameter name"

write_case "$TMP_DIR/param-bad-tail-int.nq" <<'EOF'
func add(a, 1) {
return a
}
print 1
EOF
assert_compile_fail "param-bad-tail-int" "$TMP_DIR/param-bad-tail-int.nq" "expected parameter name"

write_case "$TMP_DIR/func_missing_name.nq" <<'EOF'
func {
print 1
}
EOF
assert_compile_fail "func-missing-name" "$TMP_DIR/func_missing_name.nq" "expected function name"

write_case "$TMP_DIR/func-no-parens.nq" <<'EOF'
func add {
return 7
}
print add()
EOF
assert_compile_fail "func-no-parens" "$TMP_DIR/func-no-parens.nq" "expected '(' after function name"

write_case "$TMP_DIR/nested-func.nq" <<'EOF'
func outer() {
func inner() {
return 1
}
return inner()
}
print outer()
EOF
assert_compile_fail "nested-func" "$TMP_DIR/nested-func.nq" "declaration must appear at top level"

write_case "$TMP_DIR/module-dup-func-no-cascade.nq" <<'EOF'
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
err_file="$TMP_DIR/module-dup-func-no-cascade.err"
if "$ROOT_DIR/nql" "$TMP_DIR/module-dup-func-no-cascade.nq" >"$err_file" 2>&1; then
    printf 'FAIL %s\nexpected compiler failure\n' "module-dup-func-no-cascade" >&2
    exit 1
fi
if ! grep -q -- "duplicate function name" "$err_file"; then
    printf 'FAIL %s\nmissing duplicate function error\n' "module-dup-func-no-cascade" >&2
    exit 1
fi
if grep -q -- "return outside function" "$err_file"; then
    printf 'FAIL %s\nunexpected cascade error\n' "module-dup-func-no-cascade" >&2
    exit 1
fi
printf 'PASS %s\n' "module-dup-func-no-cascade"

write_case "$TMP_DIR/module_missing_name.nq" <<'EOF'
module
print 1
EOF
assert_compile_fail "module-missing-name" "$TMP_DIR/module_missing_name.nq" "expected module name"

write_case "$TMP_DIR/module_duplicate_name.nq" <<'EOF'
module demo {
print 1
}
module demo {
print 2
}
EOF
assert_compile_fail "module-duplicate-name" "$TMP_DIR/module_duplicate_name.nq" "duplicate module name"

write_case "$TMP_DIR/module-extra-header.nq" <<'EOF'
module demo extra
print 1
EOF
assert_compile_fail "module-extra-header" "$TMP_DIR/module-extra-header.nq" "expected '{' after module name"

write_case "$TMP_DIR/nested-module.nq" <<'EOF'
func outer() {
module demo {
print 1
}
return 2
}
print outer()
EOF
assert_compile_fail "nested-module" "$TMP_DIR/nested-module.nq" "declaration must appear at top level"

write_case "$TMP_DIR/import_missing_name.nq" <<'EOF'
import
print 1
EOF
assert_compile_fail "import-missing-name" "$TMP_DIR/import_missing_name.nq" "expected import name"

write_case "$TMP_DIR/import-extra-header.nq" <<'EOF'
import demo extra
print 1
EOF
assert_compile_fail "import-extra-header" "$TMP_DIR/import-extra-header.nq" "unexpected token after import name"

write_case "$TMP_DIR/nested-import.nq" <<'EOF'
func outer() {
import demo
return 2
}
print outer()
EOF
assert_compile_fail "nested-import" "$TMP_DIR/nested-import.nq" "declaration must appear at top level"

write_case "$TMP_DIR/import-after-stmt.nq" <<'EOF'
print 1
import demo
EOF
assert_compile_fail "import-after-stmt" "$TMP_DIR/import-after-stmt.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/import-after-var.nq" <<'EOF'
var x = 1
import demo
EOF
assert_compile_fail "import-after-var" "$TMP_DIR/import-after-var.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/module-after-stmt.nq" <<'EOF'
print 1
module demo {
print 2
}
EOF
assert_compile_fail "module-after-stmt" "$TMP_DIR/module-after-stmt.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/module-after-var.nq" <<'EOF'
var x = 1
module demo {
print 2
}
EOF
assert_compile_fail "module-after-var" "$TMP_DIR/module-after-var.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/func-after-stmt.nq" <<'EOF'
print 1
func add() {
return 2
}
EOF
assert_compile_fail "func-after-stmt" "$TMP_DIR/func-after-stmt.nq" "declaration must appear before executable statements"

write_case "$TMP_DIR/func_no_block.nq" <<'EOF'
func add(a)
print a
EOF
assert_compile_fail "func-no-block" "$TMP_DIR/func_no_block.nq" "expected '{' to start block body"

write_case "$TMP_DIR/module_no_block.nq" <<'EOF'
module demo
print 1
EOF
assert_compile_fail "module-no-block" "$TMP_DIR/module_no_block.nq" "expected '{' to start block body"

write_case "$TMP_DIR/catch_no_block.nq" <<'EOF'
try {
error "x"
} catch
print 7
EOF
assert_compile_fail "catch-no-block" "$TMP_DIR/catch_no_block.nq" "expected '{' to start block body"

write_case "$TMP_DIR/for_missing_start.nq" <<'EOF'
for i in ..3 {
print i
}
EOF
assert_compile_fail "for-missing-start" "$TMP_DIR/for_missing_start.nq" "expected expression"

write_case "$TMP_DIR/for_missing_end.nq" <<'EOF'
for i in 1.. {
print i
}
EOF
assert_compile_fail "for-missing-end" "$TMP_DIR/for_missing_end.nq" "expected expression"

write_case "$TMP_DIR/for_range_start_type.nq" <<'EOF'
for i in "abc"..3 {
print i
}
EOF
assert_compile_fail "for-range-start-type" "$TMP_DIR/for_range_start_type.nq" "type error: for range bounds must be integers"

write_case "$TMP_DIR/for_range_end_type.nq" <<'EOF'
for i in 0.."abc" {
print i
}
EOF
assert_compile_fail "for-range-end-type" "$TMP_DIR/for_range_end_type.nq" "type error: for range bounds must be integers"

write_case "$TMP_DIR/for_each_int_type.nq" <<'EOF'
for x in 7 {
print x
}
EOF
assert_compile_fail "for-each-int-type" "$TMP_DIR/for_each_int_type.nq" "type error: for-each source must be an array"

write_case "$TMP_DIR/for_each_str_type.nq" <<'EOF'
for x in "abc" {
print x
}
EOF
assert_compile_fail "for-each-str-type" "$TMP_DIR/for_each_str_type.nq" "type error: for-each source must be an array"

write_case "$TMP_DIR/if_missing_cond.nq" <<'EOF'
if {
print 1
}
EOF
assert_compile_fail "if-missing-cond" "$TMP_DIR/if_missing_cond.nq" "expected expression"

write_case "$TMP_DIR/if_and_missing_rhs.nq" <<'EOF'
if 1 == 1 and {
print 1
}
EOF
assert_compile_fail "if-and-missing-rhs" "$TMP_DIR/if_and_missing_rhs.nq" "expected expression"

write_case "$TMP_DIR/standalone_elif.nq" <<'EOF'
elif x == 1 {
print 1
}
EOF
assert_compile_fail "standalone-elif" "$TMP_DIR/standalone_elif.nq" "unexpected statement"

write_case "$TMP_DIR/while_missing_cond.nq" <<'EOF'
while {
print 1
}
EOF
assert_compile_fail "while-missing-cond" "$TMP_DIR/while_missing_cond.nq" "expected expression"

write_case "$TMP_DIR/ret_out.nq" <<'EOF'
return 1
EOF
assert_compile_fail "return-outside" "$TMP_DIR/ret_out.nq" "return outside function"

write_case "$TMP_DIR/return-missing-value.nq" <<'EOF'
func f() {
return ,
}
print f()
EOF
assert_compile_fail "return-missing-value" "$TMP_DIR/return-missing-value.nq" "expected expression"

write_case "$TMP_DIR/param_ovf.nq" <<'EOF'
func too_many(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q) {
return a
}
print 1
EOF
assert_compile_fail "param-overflow" "$TMP_DIR/param_ovf.nq" "too many function parameters"

write_case "$TMP_DIR/dup_fn.nq" <<'EOF'
func add(a, b) {
return a + b
}
func add(x, y) {
return x - y
}
print 1
EOF
assert_compile_fail "duplicate-function" "$TMP_DIR/dup_fn.nq" "duplicate function name"

write_case "$TMP_DIR/dup_param.nq" <<'EOF'
func bad(a, a) {
return a
}
print 1
EOF
assert_compile_fail "duplicate-parameter" "$TMP_DIR/dup_param.nq" "duplicate parameter name"

write_case "$TMP_DIR/dup_local.nq" <<'EOF'
func bad(a) {
var x = a
var x = a + 1
return x
}
print 1
EOF
assert_compile_fail "duplicate-local" "$TMP_DIR/dup_local.nq" "duplicate local variable"

write_case "$TMP_DIR/dup_local_nested.nq" <<'EOF'
func bad(a) {
if a == 1 {
var x = a
}
var x = a + 1
return x
}
print 1
EOF
assert_compile_fail "duplicate-local-nested" "$TMP_DIR/dup_local_nested.nq" "duplicate local variable"

: > "$TMP_DIR/loop_ovf.nq"
for _i in $(seq 1 17); do
    printf 'while 1 < 2 {\n' >> "$TMP_DIR/loop_ovf.nq"
done
printf 'print 1\n' >> "$TMP_DIR/loop_ovf.nq"
for _i in $(seq 1 17); do
    printf '}\n' >> "$TMP_DIR/loop_ovf.nq"
done
assert_compile_fail "loop-overflow" "$TMP_DIR/loop_ovf.nq" "loop nesting limit exceeded"

write_case "$TMP_DIR/global_fn_conflict.nq" <<'EOF'
var add = 1
func add(a, b) {
return a + b
}
print 1
EOF
assert_compile_fail "global-fn-conflict" "$TMP_DIR/global_fn_conflict.nq" "name conflicts with existing global"

write_case "$TMP_DIR/fn_global_conflict.nq" <<'EOF'
func add(a, b) {
return a + b
}
var add = 1
print 1
EOF
assert_compile_fail "fn-global-conflict" "$TMP_DIR/fn_global_conflict.nq" "name conflicts with existing global"

write_case "$TMP_DIR/print_empty.nq" <<'EOF'
print
EOF
assert_compile_fail "print-empty" "$TMP_DIR/print_empty.nq" "expected print item"

write_case "$TMP_DIR/print_trailing_comma.nq" <<'EOF'
print 1,
EOF
assert_compile_fail "print-trailing-comma" "$TMP_DIR/print_trailing_comma.nq" "expected print item"

write_case "$TMP_DIR/println_trailing_comma.nq" <<'EOF'
println 1,
EOF
assert_compile_fail "println-trailing-comma" "$TMP_DIR/println_trailing_comma.nq" "expected print item"

write_case "$TMP_DIR/builtin_missing_rparen.nq" <<'EOF'
var a = [1]
print len(a
EOF
assert_compile_fail "builtin-missing-rparen" "$TMP_DIR/builtin_missing_rparen.nq" "expected ')' after builtin argument list"

write_case "$TMP_DIR/builtin_missing_comma.nq" <<'EOF'
print min(1
EOF
assert_compile_fail "builtin-missing-comma" "$TMP_DIR/builtin_missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/push_missing_comma.nq" <<'EOF'
var a = [1]
push(a 2)
EOF
assert_compile_fail "push-missing-comma" "$TMP_DIR/push_missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/builtin_missing_lparen.nq" <<'EOF'
print len
EOF
assert_compile_fail "builtin-missing-lparen" "$TMP_DIR/builtin_missing_lparen.nq" "expected '(' after builtin name"

write_case "$TMP_DIR/arg_missing_lparen.nq" <<'EOF'
print arg
EOF
assert_compile_fail "arg-missing-lparen" "$TMP_DIR/arg_missing_lparen.nq" "expected '(' after builtin name"

write_case "$TMP_DIR/arg_missing_rparen.nq" <<'EOF'
print arg(1
EOF
assert_compile_fail "arg-missing-rparen" "$TMP_DIR/arg_missing_rparen.nq" "expected ')' after builtin argument list"

write_case "$TMP_DIR/arg_missing_expr.nq" <<'EOF'
print arg()
EOF
assert_compile_fail "arg-missing-expr" "$TMP_DIR/arg_missing_expr.nq" "expected expression"

write_case "$TMP_DIR/arg_type_err.nq" <<'EOF'
print arg("x")
EOF
assert_compile_fail "arg-type-err" "$TMP_DIR/arg_type_err.nq" "type error: arg() index must be an integer"

write_case "$TMP_DIR/break_outside.nq" <<'EOF'
break
print 1
EOF
assert_compile_fail "break-outside" "$TMP_DIR/break_outside.nq" "break/continue outside loop"

write_case "$TMP_DIR/continue_outside.nq" <<'EOF'
continue
print 1
EOF
assert_compile_fail "continue-outside" "$TMP_DIR/continue_outside.nq" "break/continue outside loop"

write_case "$TMP_DIR/try_no_catch.nq" <<'EOF'
try {
print 1
}
print 2
EOF
assert_compile_fail "try-no-catch" "$TMP_DIR/try_no_catch.nq" "expected 'catch' after try block"

write_case "$TMP_DIR/error_outside_try.nq" <<'EOF'
error "boom"
print 1
EOF
assert_compile_fail "error-outside-try" "$TMP_DIR/error_outside_try.nq" "error statement outside try"

write_case "$TMP_DIR/error-bad-payload.nq" <<'EOF'
try {
error 1
} catch {
print 7
}
EOF
assert_compile_fail "error-bad-payload" "$TMP_DIR/error-bad-payload.nq" "error payload must be a string literal"

write_case "$TMP_DIR/unterminated-string.nq" <<'EOF'
var s = "abc
print s
EOF
assert_compile_fail "unterminated-string" "$TMP_DIR/unterminated-string.nq" "line 1, col 8: unterminated string literal"

write_case "$TMP_DIR/catch_without_try.nq" <<'EOF'
catch {
print 1
}
EOF
assert_compile_fail "catch-without-try" "$TMP_DIR/catch_without_try.nq" "unexpected statement"

write_case "$TMP_DIR/array_trailing_comma.nq" <<'EOF'
var a = [1,]
print a[0]
EOF
assert_compile_fail "array-trailing-comma" "$TMP_DIR/array_trailing_comma.nq" "expected array item"

write_case "$TMP_DIR/array-double-comma.nq" <<'EOF'
var a = [1,,2]
print a[0]
EOF
assert_compile_fail "array-double-comma" "$TMP_DIR/array-double-comma.nq" "expected array item"

write_case "$TMP_DIR/array_mixed_int_string.nq" <<'EOF'
var a = [1,"x"]
print a[0]
EOF
assert_compile_fail "array-mixed-int-string" "$TMP_DIR/array_mixed_int_string.nq" "type error: array literal elements must have the same type"

write_case "$TMP_DIR/array_mixed_string_int.nq" <<'EOF'
var a = ["x",1]
print a[0]
EOF
assert_compile_fail "array-mixed-string-int" "$TMP_DIR/array_mixed_string_int.nq" "type error: array literal elements must have the same type"

python3 - <<'PY' > "$TMP_DIR/array-too-large.nq"
items = ",".join(str(i) for i in range(8159))
print(f"var a = [{items}]")
print("print a[0]")
PY
assert_compile_fail "array-too-large" "$TMP_DIR/array-too-large.nq" "array literal exceeds fixed heap capacity"

write_case "$TMP_DIR/negative-array-index.nq" <<'EOF'
var a = [1,2,3]
print a[-1]
EOF
assert_compile_fail "negative-array-index" "$TMP_DIR/negative-array-index.nq" "negative array index not allowed"

write_case "$TMP_DIR/var-missing-init.nq" <<'EOF'
var x =
print x
EOF
assert_compile_fail "var-missing-init" "$TMP_DIR/var-missing-init.nq" "expected expression"

write_case "$TMP_DIR/assign-missing-rhs.nq" <<'EOF'
var x = 1
x =
print x
EOF
assert_compile_fail "assign-missing-rhs" "$TMP_DIR/assign-missing-rhs.nq" "expected expression"

write_case "$TMP_DIR/compound_assign_str_rhs.nq" <<'EOF'
var x = 1
x += "a"
print x
EOF
assert_compile_fail "compound-assign-str-rhs" "$TMP_DIR/compound_assign_str_rhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/compound_assign_str_lhs.nq" <<'EOF'
var s = "a"
s += "b"
print s
EOF
assert_compile_fail "compound-assign-str-lhs" "$TMP_DIR/compound_assign_str_lhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/array-assign-missing-rhs.nq" <<'EOF'
var a = [1,2,3]
a[1] =
print a[1]
EOF
assert_compile_fail "array-assign-missing-rhs" "$TMP_DIR/array-assign-missing-rhs.nq" "expected expression"

write_case "$TMP_DIR/bitwise-str-lhs.nq" <<'EOF'
var s = "x"
print s & 1
EOF
assert_compile_fail "bitwise-str-lhs" "$TMP_DIR/bitwise-str-lhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/shift-str-rhs.nq" <<'EOF'
var s = "x"
print 1 << s
EOF
assert_compile_fail "shift-str-rhs" "$TMP_DIR/shift-str-rhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/unary-minus-str.nq" <<'EOF'
var s = "x"
print -s
EOF
assert_compile_fail "unary-minus-str" "$TMP_DIR/unary-minus-str.nq" "type error: integer operand required"

write_case "$TMP_DIR/bitwise-not-str.nq" <<'EOF'
var s = "x"
print ~s
EOF
assert_compile_fail "bitwise-not-str" "$TMP_DIR/bitwise-not-str.nq" "type error: integer operand required"

write_case "$TMP_DIR/logical-not-str.nq" <<'EOF'
var s = "x"
print not s
EOF
assert_compile_fail "logical-not-str" "$TMP_DIR/logical-not-str.nq" "type error: integer operand required"

write_case "$TMP_DIR/abs-str.nq" <<'EOF'
print abs("x")
EOF
assert_compile_fail "abs-str" "$TMP_DIR/abs-str.nq" "type error: integer operand required"

write_case "$TMP_DIR/str_builtin_string.nq" <<'EOF'
print str("x")
EOF
assert_compile_fail "str-builtin-string" "$TMP_DIR/str_builtin_string.nq" "type error: str() argument must be an integer"

write_case "$TMP_DIR/int_builtin_int.nq" <<'EOF'
print int(1)
EOF
assert_compile_fail "int-builtin-int" "$TMP_DIR/int_builtin_int.nq" "type error: int() argument must be a string"

write_case "$TMP_DIR/min-str-lhs.nq" <<'EOF'
print min("x", 1)
EOF
assert_compile_fail "min-str-lhs" "$TMP_DIR/min-str-lhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/max-str-rhs.nq" <<'EOF'
print max(1, "x")
EOF
assert_compile_fail "max-str-rhs" "$TMP_DIR/max-str-rhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/empty-array-load-index.nq" <<'EOF'
var a = [1,2,3]
print a[]
EOF
assert_compile_fail "empty-array-load-index" "$TMP_DIR/empty-array-load-index.nq" "expected array index"

write_case "$TMP_DIR/empty-array-store-index.nq" <<'EOF'
var a = [1,2,3]
a[] = 9
print a[0]
EOF
assert_compile_fail "empty-array-store-index" "$TMP_DIR/empty-array-store-index.nq" "expected array index"

write_case "$TMP_DIR/array-load-string-index.nq" <<'EOF'
var a = [1,2,3]
print a["x"]
EOF
assert_compile_fail "array-load-string-index" "$TMP_DIR/array-load-string-index.nq" "type error: index must be an integer"

write_case "$TMP_DIR/string-load-string-index.nq" <<'EOF'
var s = "abc"
print s["x"]
EOF
assert_compile_fail "string-load-string-index" "$TMP_DIR/string-load-string-index.nq" "type error: index must be an integer"

write_case "$TMP_DIR/array-store-string-index.nq" <<'EOF'
var a = [1,2,3]
a["x"] = 9
print a[0]
EOF
assert_compile_fail "array-store-string-index" "$TMP_DIR/array-store-string-index.nq" "type error: index must be an integer"

write_case "$TMP_DIR/string-index-store.nq" <<'EOF'
var s = "abc"
s[0] = 99
print s
EOF
assert_compile_fail "string-index-store" "$TMP_DIR/string-index-store.nq" "type error: indexed assignment requires an array"

write_case "$TMP_DIR/int-index-store.nq" <<'EOF'
var x = 7
x[0] = 1
print x
EOF
assert_compile_fail "int-index-store" "$TMP_DIR/int-index-store.nq" "type error: indexed assignment requires an array"

write_case "$TMP_DIR/int-array-store-string.nq" <<'EOF'
var a = [1]
a[0] = "x"
print a[0]
EOF
assert_compile_fail "int-array-store-string" "$TMP_DIR/int-array-store-string.nq" "type error: array assignment value type does not match element type"

write_case "$TMP_DIR/str-array-store-int.nq" <<'EOF'
var a = str[]
push(a, "x")
a[0] = 7
print a[0]
EOF
assert_compile_fail "str-array-store-int" "$TMP_DIR/str-array-store-int.nq" "type error: array assignment value type does not match element type"

write_case "$TMP_DIR/typed_int_array_missing_rbracket.nq" <<'EOF'
var a = int[
print 1
EOF
assert_compile_fail "typed-int-array-missing-rbracket" "$TMP_DIR/typed_int_array_missing_rbracket.nq" "expected ']' after typed array marker"

write_case "$TMP_DIR/typed_str_array_missing_rbracket.nq" <<'EOF'
var a = str[
print 1
EOF
assert_compile_fail "typed-str-array-missing-rbracket" "$TMP_DIR/typed_str_array_missing_rbracket.nq" "expected ']' after typed array marker"

write_case "$TMP_DIR/paren_missing_rparen.nq" <<'EOF'
print (1
EOF
assert_compile_fail "paren-missing-rparen" "$TMP_DIR/paren_missing_rparen.nq" "expected ')' after expression"

write_case "$TMP_DIR/array_load_missing_rbracket.nq" <<'EOF'
var a = [1]
print a[0
EOF
assert_compile_fail "array-load-missing-rbracket" "$TMP_DIR/array_load_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/string_load_missing_rbracket.nq" <<'EOF'
var s = "ab"
print s[0
EOF
assert_compile_fail "string-load-missing-rbracket" "$TMP_DIR/string_load_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/array-assign-missing-rbracket.nq" <<'EOF'
var a = [1]
a[0 1
EOF
assert_compile_fail "array-assign-missing-rbracket" "$TMP_DIR/array-assign-missing-rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/array-assign-missing-eq.nq" <<'EOF'
var a = [1]
a[0] 1
EOF
assert_compile_fail "array-assign-missing-eq" "$TMP_DIR/array-assign-missing-eq.nq" "expected '=' in assignment"
