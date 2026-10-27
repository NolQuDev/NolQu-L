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

write_case "$TMP_DIR/ok.nq" <<'EOF'
print 1
EOF
assert_cli_fail "eh-cli-unknown-flag" "unknown option: --definitely-unknown" "$ROOT_DIR/nql" --definitely-unknown "$TMP_DIR/ok.nq"
assert_cli_fail "eh-cli-missing-emit-path" "--emit requires a path" "$ROOT_DIR/nql" "$TMP_DIR/ok.nq" --emit

write_case "$TMP_DIR/missing_rparen.nq" <<'EOF'
var a = [1]
print len(a
EOF
assert_compile_fail "eh-parser-missing-rparen" "$TMP_DIR/missing_rparen.nq" "expected ')' after builtin argument list"

write_case "$TMP_DIR/missing_comma.nq" <<'EOF'
print min(1
EOF
assert_compile_fail "eh-parser-missing-comma" "$TMP_DIR/missing_comma.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/call_missing_rparen.nq" <<'EOF'
func f(a) {
return a
}
print f(1
EOF
assert_compile_fail "eh-parser-call-missing-rparen" "$TMP_DIR/call_missing_rparen.nq" "expected ',' or ')' in argument list"

write_case "$TMP_DIR/call_missing_expr_eof.nq" <<'EOF'
func f(a) {
return a
}
print f(
EOF
assert_compile_fail "eh-parser-call-missing-expr-eof" "$TMP_DIR/call_missing_expr_eof.nq" "expected expression"

write_case "$TMP_DIR/arg_missing_lparen.nq" <<'EOF'
print arg
EOF
assert_compile_fail "eh-parser-arg-missing-lparen" "$TMP_DIR/arg_missing_lparen.nq" "expected '(' after builtin name"

write_case "$TMP_DIR/arg_missing_rparen.nq" <<'EOF'
print arg(1
EOF
assert_compile_fail "eh-parser-arg-missing-rparen" "$TMP_DIR/arg_missing_rparen.nq" "expected ')' after builtin argument list"

write_case "$TMP_DIR/arg_missing_expr.nq" <<'EOF'
print arg()
EOF
assert_compile_fail "eh-parser-arg-missing-expr" "$TMP_DIR/arg_missing_expr.nq" "expected expression"

write_case "$TMP_DIR/paren_missing_rparen.nq" <<'EOF'
print (1
EOF
assert_compile_fail "eh-parser-paren-missing-rparen" "$TMP_DIR/paren_missing_rparen.nq" "expected ')' after expression"

write_case "$TMP_DIR/standalone_elif.nq" <<'EOF'
elif x == 1 {
print 1
}
EOF
assert_compile_fail "eh-parser-standalone-elif" "$TMP_DIR/standalone_elif.nq" "unexpected statement"

write_case "$TMP_DIR/array_load_missing_rbracket.nq" <<'EOF'
var a = [1]
print a[0
EOF
assert_compile_fail "eh-parser-array-load-missing-rbracket" "$TMP_DIR/array_load_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/string_load_missing_rbracket.nq" <<'EOF'
var s = "ab"
print s[0
EOF
assert_compile_fail "eh-parser-string-load-missing-rbracket" "$TMP_DIR/string_load_missing_rbracket.nq" "expected ']' after array index"

write_case "$TMP_DIR/typed_int_array_missing_rbracket.nq" <<'EOF'
var a = int[
print 1
EOF
assert_compile_fail "eh-parser-typed-int-array-missing-rbracket" "$TMP_DIR/typed_int_array_missing_rbracket.nq" "expected ']' after typed array marker"

write_case "$TMP_DIR/typed_str_array_missing_rbracket.nq" <<'EOF'
var a = str[
print 1
EOF
assert_compile_fail "eh-parser-typed-str-array-missing-rbracket" "$TMP_DIR/typed_str_array_missing_rbracket.nq" "expected ']' after typed array marker"

write_case "$TMP_DIR/push_type.nq" <<'EOF'
var a = int[]
push(a, "x")
EOF
assert_compile_fail "eh-type-push-value" "$TMP_DIR/push_type.nq" "push() value type does not match array element type"

write_case "$TMP_DIR/compound_assign_str_rhs.nq" <<'EOF'
var x = 1
x += "a"
print x
EOF
assert_compile_fail "eh-type-compound-str-rhs" "$TMP_DIR/compound_assign_str_rhs.nq" "type error: arithmetic on non-integer"

write_case "$TMP_DIR/unterminated_string.nq" <<'EOF'
var s = "abc
print s
EOF
assert_compile_fail "eh-lexer-unterminated-string" "$TMP_DIR/unterminated_string.nq" "line 1, col 8: unterminated string literal"

write_case "$TMP_DIR/invalid_char.nq" <<'EOF'
print @
EOF
assert_compile_fail "eh-lexer-invalid-character" "$TMP_DIR/invalid_char.nq" "invalid character"

write_case "$TMP_DIR/bare_bang.nq" <<'EOF'
print !
EOF
assert_compile_fail "eh-lexer-bare-bang" "$TMP_DIR/bare_bang.nq" "invalid character"

printf 'print \200\n' > "$TMP_DIR/non_ascii_byte.nq"
assert_compile_fail "eh-lexer-non-ascii-byte" "$TMP_DIR/non_ascii_byte.nq" "invalid character"

printf 'print \001\n' > "$TMP_DIR/control_byte.nq"
assert_compile_fail "eh-lexer-control-byte" "$TMP_DIR/control_byte.nq" "invalid character"

write_case "$TMP_DIR/identifier_too_long.nq" <<'EOF'
var aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa = 1
EOF
assert_compile_fail "eh-lexer-identifier-too-long" "$TMP_DIR/identifier_too_long.nq" "line 1, col 4: identifier too long"

write_case "$TMP_DIR/unterminated_block_comment.nq" <<'EOF'
print 1
/* missing end
print 2
EOF
assert_compile_fail "eh-lexer-unterminated-block-comment" "$TMP_DIR/unterminated_block_comment.nq" "line 2, col 0: unterminated block comment"

write_case "$TMP_DIR/empty_hex_literal.nq" <<'EOF'
print 0x
EOF
assert_compile_fail "eh-lexer-empty-hex-literal" "$TMP_DIR/empty_hex_literal.nq" "line 1, col 8: expected hex digit after 0x"

write_case "$TMP_DIR/bad_hex_literal.nq" <<'EOF'
print 0x1g
EOF
assert_compile_fail "eh-lexer-bad-hex-literal" "$TMP_DIR/bad_hex_literal.nq" "line 1, col 9: invalid hex digit"

write_case "$TMP_DIR/hex_literal_overflow.nq" <<'EOF'
print 0x8000000000000000
EOF
assert_compile_fail "eh-parser-hex-literal-overflow" "$TMP_DIR/hex_literal_overflow.nq" "line 1, col 6: integer literal overflow"

write_case "$TMP_DIR/empty_binary_literal.nq" <<'EOF'
print 0b
EOF
assert_compile_fail "eh-lexer-empty-binary-literal" "$TMP_DIR/empty_binary_literal.nq" "line 1, col 8: expected binary digit after 0b"

write_case "$TMP_DIR/bad_binary_literal.nq" <<'EOF'
print 0b102
EOF
assert_compile_fail "eh-lexer-bad-binary-literal" "$TMP_DIR/bad_binary_literal.nq" "line 1, col 10: invalid binary digit"

write_case "$TMP_DIR/binary_literal_overflow.nq" <<'EOF'
print 0b1000000000000000000000000000000000000000000000000000000000000000
EOF
assert_compile_fail "eh-parser-binary-literal-overflow" "$TMP_DIR/binary_literal_overflow.nq" "line 1, col 6: integer literal overflow"

write_case "$TMP_DIR/bad_decimal_separator.nq" <<'EOF'
print 1_
EOF
assert_compile_fail "eh-lexer-bad-decimal-separator" "$TMP_DIR/bad_decimal_separator.nq" "line 1, col 7: invalid digit separator"

write_case "$TMP_DIR/bad_hex_separator.nq" <<'EOF'
print 0x_ff
EOF
assert_compile_fail "eh-lexer-bad-hex-separator" "$TMP_DIR/bad_hex_separator.nq" "line 1, col 8: invalid digit separator"

write_case "$TMP_DIR/bad_binary_separator.nq" <<'EOF'
print 0b10_
EOF
assert_compile_fail "eh-lexer-bad-binary-separator" "$TMP_DIR/bad_binary_separator.nq" "line 1, col 10: invalid digit separator"

write_case "$TMP_DIR/separated_decimal_overflow.nq" <<'EOF'
print 9_999_999_999_999_999_999_9
EOF
assert_compile_fail "eh-parser-separated-decimal-overflow" "$TMP_DIR/separated_decimal_overflow.nq" "line 1, col 6: integer literal overflow"

python3 - "$TMP_DIR/token_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join("print 1\n" for _ in range(8200)))
PY
assert_compile_fail "eh-lexer-token-overflow" "$TMP_DIR/token_overflow.nq" "line 5462, col 0: token buffer overflow"

python3 - "$TMP_DIR/function_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join(f"func f{i}() {{\nreturn 1\n}}\n" for i in range(520)))
PY
assert_compile_fail "eh-function-table-overflow" "$TMP_DIR/function_table_overflow.nq" "line 1537, col 12: function table overflow"

python3 - "$TMP_DIR/local_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("func f() {\n" + "".join(f"var v{i} = {i}\n" for i in range(70)) + "return 1\n}\n")
PY
assert_compile_fail "eh-local-table-overflow" "$TMP_DIR/local_table_overflow.nq" "line 66, col 12: too many local variables (max 64)"

python3 - "$TMP_DIR/global_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join(f"var g{i} = {i}\n" for i in range(520)))
PY
assert_compile_fail "eh-global-table-overflow" "$TMP_DIR/global_table_overflow.nq" "line 513, col 14: symbol table full"

python3 - "$TMP_DIR/module_table_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join(f"module m{i} {{\n}}\n" for i in range(520)))
PY
assert_compile_fail "eh-module-table-overflow" "$TMP_DIR/module_table_overflow.nq" "line 1025, col 12: module table overflow"

python3 - "$TMP_DIR/string_literal_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join('print "x"\n' for _ in range(4100)))
PY
assert_compile_fail "eh-string-literal-overflow" "$TMP_DIR/string_literal_overflow.nq" "line 4097, col 7: too many string literals (max 4096)"

python3 - "$TMP_DIR/string_data_buffer_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("".join('print "' + ("x" * 1000) + '"\n' for _ in range(300)))
PY
assert_compile_fail "eh-string-data-buffer-overflow" "$TMP_DIR/string_data_buffer_overflow.nq" "line 254, col 7: string data buffer overflow"

python3 - "$TMP_DIR/output_buffer_overflow.nq" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text("var a = [" + ",".join("1" for _ in range(8000)) + "]\nprint len(a)\n")
PY
assert_compile_fail "eh-output-buffer-overflow" "$TMP_DIR/output_buffer_overflow.nq" "line 1, col 0: output buffer overflow"

write_case "$TMP_DIR/runtime_pop_empty.nq" <<'EOF'
var a = int[]
print pop(a)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/runtime_pop_empty.nq" >/dev/null
build_generated
assert_runtime_fail "eh-runtime-pop-empty" "$TMP_DIR/output" "array pop: array is empty"
