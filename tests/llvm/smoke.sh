#!/usr/bin/env bash
set -euo pipefail

# LLVM backend wrapper and bridge maintenance suite.
# Frontend inspection flags stay frontend-owned; LLVM IR output is written via --emit.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

assert_llvm_cli_fail() {
    local name="$1"
    local pattern="$2"
    shift 2
    local err_file="$TMP_DIR/${name}.err"
    if "$@" >"$err_file" 2>&1; then
        printf 'FAIL %s\nexpected LLVM CLI failure\n' "$name" >&2
        exit 1
    fi
    if ! grep -q -- "$pattern" "$err_file"; then
        printf 'FAIL %s\nmissing LLVM CLI error message\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

write_case "$TMP_DIR/llvm_basic.nq" <<'EOF'
var x = 40
print x + 2
EOF
write_case "$TMP_DIR/llvm_extra.nq" <<'EOF'
print 7
EOF

assert_llvm_cli_fail "llvm-bench-unsupported" "LLVM backend does not support --bench" "$ROOT_DIR/nql" --backend llvm --bench "$TMP_DIR/llvm_basic.nq"
assert_llvm_cli_fail "llvm-build-conflict" "--build-compiler cannot be combined with --backend llvm" "$ROOT_DIR/nql" --backend llvm --build-compiler "$TMP_DIR/llvm_basic.nq"
assert_llvm_cli_fail "llvm-run-dump-conflict" "run cannot be used with --dump-ir" "$ROOT_DIR/nql" --backend llvm --run --dump-ir "$TMP_DIR/llvm_basic.nq"
assert_llvm_cli_fail "llvm-extra-source" "expects exactly one .nql source file" "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_basic.nq" "$TMP_DIR/llvm_extra.nq"

llvm_tokens_out="$("$ROOT_DIR/nql" --backend llvm --dump-tokens "$TMP_DIR/llvm_basic.nq")"
if ! printf "%s\n" "$llvm_tokens_out" | grep -q "IDENT"; then
    printf "FAIL llvm-dump-tokens\nmissing IDENT token\n" >&2
    exit 1
fi
printf "PASS llvm-dump-tokens\n"

llvm_ir_out="$("$ROOT_DIR/nql" --backend llvm --dump-ir "$TMP_DIR/llvm_basic.nq")"
if ! printf "%s\n" "$llvm_ir_out" | grep -q "== IR =="; then
    printf "FAIL llvm-dump-ir\nmissing IR header\n" >&2
    exit 1
fi
printf "PASS llvm-dump-ir\n"

llvm_export_path="$TMP_DIR/llvm_export.ir"
"$ROOT_DIR/nql" --backend llvm --export-ir "$llvm_export_path" "$TMP_DIR/llvm_basic.nq" >/dev/null
if [[ ! -f "$llvm_export_path" ]]; then
    printf "FAIL llvm-export-ir\nmissing exported IR file\n" >&2
    exit 1
fi
if ! grep -q "== IR ==" "$llvm_export_path"; then
    printf "FAIL llvm-export-ir\nmissing IR header\n" >&2
    exit 1
fi
printf "PASS llvm-export-ir\n"

"$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_basic.nq" >/dev/null
if [[ ! -f "$ROOT_DIR/build/output.ll" ]]; then
    printf 'FAIL llvm-check\nmissing build/output.ll\n' >&2
    exit 1
fi
printf 'PASS llvm-check\n'

llvm_emit_path="$TMP_DIR/llvm_emit.ll"
"$ROOT_DIR/nql" --backend llvm --emit "$llvm_emit_path" "$TMP_DIR/llvm_basic.nq" >/dev/null
if [[ ! -f "$llvm_emit_path" ]]; then
    printf "FAIL llvm-emit\nmissing custom LLVM IR output\n" >&2
    exit 1
fi
if ! grep -q "define i32 @main" "$llvm_emit_path"; then
    printf "FAIL llvm-emit\ncustom output does not look like LLVM IR\n" >&2
    exit 1
fi
printf "PASS llvm-emit\n"

llvm_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_basic.nq")"
if ! printf '%s\n' "$llvm_out" | grep -q '^42$'; then
    printf 'FAIL llvm-run\nexpected 42 in output\n' >&2
    exit 1
fi
printf 'PASS llvm-run\n'

write_case "$TMP_DIR/llvm_if.nq" <<'EOF'
var x = 7
x = x + 1
if x > 7 {
print x
} else {
print 0
}
EOF

llvm_if_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_if.nq")"
if ! printf '%s\n' "$llvm_if_out" | grep -q '^8$'; then
    printf 'FAIL llvm-if\nexpected 8 in output\n' >&2
    exit 1
fi
printf 'PASS llvm-if\n'

write_case "$TMP_DIR/llvm_while.nq" <<'EOF'
var x = 0
while x < 3 {
print x
x = x + 1
}
EOF

llvm_while_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_while.nq")"
if ! printf '%s\n' "$llvm_while_out" | grep -q '^0$'; then
    printf 'FAIL llvm-while\nexpected 0 1 2 output\n' >&2
    exit 1
fi
if ! printf '%s\n' "$llvm_while_out" | grep -q '^1$'; then
    printf 'FAIL llvm-while\nexpected 0 1 2 output\n' >&2
    exit 1
fi
if ! printf '%s\n' "$llvm_while_out" | grep -q '^2$'; then
    printf 'FAIL llvm-while\nexpected 0 1 2 output\n' >&2
    exit 1
fi
printf 'PASS llvm-while\n'

write_case "$TMP_DIR/llvm_func.nq" <<'EOF'
func add(a, b) {
return a + b
}

print add(20, 22)
EOF

llvm_func_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_func.nq")"
if ! printf '%s\n' "$llvm_func_out" | grep -q '^42$'; then
    printf 'FAIL llvm-func\nexpected 42 in output\n' >&2
    exit 1
fi
printf 'PASS llvm-func\n'

write_case "$TMP_DIR/llvm_func_local.nq" <<'EOF'
func add_twice(a, b) {
var sum = a + b
return sum + sum
}

print add_twice(10, 11)
EOF

llvm_func_local_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_func_local.nq")"
if ! printf '%s\n' "$llvm_func_local_out" | grep -q '^42$'; then
    printf 'FAIL llvm-func-local\nexpected 42 in output\n' >&2
    exit 1
fi
printf 'PASS llvm-func-local\n'

write_case "$TMP_DIR/llvm_fact.nq" <<'EOF'
func fact(n) {
if n == 0 {
return 1
} else {
return n * fact(n - 1)
}
}

print fact(5)
EOF

llvm_fact_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_fact.nq")"
if ! printf '%s\n' "$llvm_fact_out" | grep -q '^120$'; then
    printf 'FAIL llvm-fact\nexpected 120 in output\n' >&2
    exit 1
fi
printf 'PASS llvm-fact\n'

write_case "$TMP_DIR/llvm_fact_local.nq" <<'EOF'
func fact_local(n) {
if n == 0 {
return 1
} else {
var next = n - 1
return n * fact_local(next)
}
}

func bump(n) {
return n + 1
}

print bump(fact_local(4))
EOF

llvm_fact_local_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_fact_local.nq")"
if ! printf '%s\n' "$llvm_fact_local_out" | grep -q '^25$'; then
    printf 'FAIL llvm-fact-local\nexpected 25 in output\n' >&2
    exit 1
fi
printf 'PASS llvm-fact-local\n'

write_case "$TMP_DIR/llvm_int_builtins.nq" <<'EOF'
print abs(0 - 9)
print min(0 - 4, 2)
print max(0 - 4, 2)
EOF

llvm_int_builtins_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_int_builtins.nq")"
expected_int_builtins="$(printf "9\n-4\n2")"
if [[ "$llvm_int_builtins_out" != "$expected_int_builtins" ]]; then
    printf "FAIL llvm-int-builtins\nexpected:\n%s\ngot:\n%s\n" "$expected_int_builtins" "$llvm_int_builtins_out" >&2
    exit 1
fi
printf 'PASS llvm-int-builtins\n'

write_case "$TMP_DIR/llvm_full_frontend.nq" <<"EOF"
module math {
func inc(x) {
return x + 1
}
}
var a = [1,2,3]
print a[1]
print "ok"
try {
error "boom"
} catch {
print math.inc(6)
}
EOF

llvm_full_out="$("$ROOT_DIR/nql" --backend llvm --run "$TMP_DIR/llvm_full_frontend.nq")"
expected_full="$(printf "2\nok\nboom\n7")"
if [[ "$llvm_full_out" != "$expected_full" ]]; then
    printf "FAIL llvm-full-frontend\nexpected:\n%s\ngot:\n%s\n" "$expected_full" "$llvm_full_out" >&2
    exit 1
fi
printf "PASS llvm-full-frontend\n"

write_case "$TMP_DIR/llvm_bad.nq" <<'EOF'
print @
EOF

if "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_bad.nq" >/dev/null 2>"$TMP_DIR/llvm_bad.err"; then
    printf 'FAIL llvm-unsupported\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q "invalid character" "$TMP_DIR/llvm_bad.err"; then
    printf 'FAIL llvm-unsupported\nmissing error message\n' >&2
    exit 1
fi
printf 'PASS llvm-unsupported\n'

write_case "$TMP_DIR/llvm_line_error.nq" <<'EOF'
var x = 1
print @
EOF

if "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_line_error.nq" >/dev/null 2>"$TMP_DIR/llvm_line_error.err"; then
    printf 'FAIL llvm-line-error\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q "line 2, col" "$TMP_DIR/llvm_line_error.err"; then
    printf 'FAIL llvm-line-error\nmissing line number\n' >&2
    exit 1
fi
printf 'PASS llvm-line-error\n'

write_case "$TMP_DIR/llvm_undefined_function.nq" <<'EOF'
print nope(1)
EOF

if "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_undefined_function.nq" >/dev/null 2>"$TMP_DIR/llvm_undefined_function.err"; then
    printf 'FAIL llvm-undefined-function\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q "undefined function" "$TMP_DIR/llvm_undefined_function.err"; then
    printf 'FAIL llvm-undefined-function\nmissing error message\n' >&2
    exit 1
fi
if ! grep -q "line 1, col" "$TMP_DIR/llvm_undefined_function.err"; then
    printf 'FAIL llvm-undefined-function\nmissing line number\n' >&2
    exit 1
fi
printf 'PASS llvm-undefined-function\n'

write_case "$TMP_DIR/llvm_wrong_arity.nq" <<'EOF'
func add(a, b) {
return a + b
}

print add(1)
EOF

if "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_wrong_arity.nq" >/dev/null 2>"$TMP_DIR/llvm_wrong_arity.err"; then
    printf 'FAIL llvm-wrong-arity\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q "wrong number of function arguments" "$TMP_DIR/llvm_wrong_arity.err"; then
    printf 'FAIL llvm-wrong-arity\nmissing error message\n' >&2
    exit 1
fi
if ! grep -q "line 5, col" "$TMP_DIR/llvm_wrong_arity.err"; then
    printf 'FAIL llvm-wrong-arity\nmissing line number\n' >&2
    exit 1
fi
printf 'PASS llvm-wrong-arity\n'

write_case "$TMP_DIR/llvm_duplicate_function.nq" <<'EOF'
func add(a, b) {
return a + b
}

func add(x, y) {
return x - y
}

print add(2, 3)
EOF

if "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_duplicate_function.nq" >/dev/null 2>"$TMP_DIR/llvm_duplicate_function.err"; then
    printf 'FAIL llvm-duplicate-function\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q "duplicate function name" "$TMP_DIR/llvm_duplicate_function.err"; then
    printf 'FAIL llvm-duplicate-function\nmissing error message\n' >&2
    exit 1
fi
printf 'PASS llvm-duplicate-function\n'

write_case "$TMP_DIR/llvm_duplicate_var.nq" <<'EOF'
func bad(n) {
var x = n
var x = n + 1
return x
}

print bad(1)
EOF

if "$ROOT_DIR/nql" --backend llvm --check "$TMP_DIR/llvm_duplicate_var.nq" >/dev/null 2>"$TMP_DIR/llvm_duplicate_var.err"; then
    printf 'FAIL llvm-duplicate-var\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q "duplicate local variable" "$TMP_DIR/llvm_duplicate_var.err"; then
    printf 'FAIL llvm-duplicate-var\nmissing error message\n' >&2
    exit 1
fi
printf 'PASS llvm-duplicate-var\n'
