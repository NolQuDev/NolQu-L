#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

write_case "$TMP_DIR/nested_local.nq" <<'EOF'
func add(a, b) {
var sum = a + b
return sum
}
func wrap(x) {
var y = add(x, 3)
return add(y, 4)
}
print wrap(5)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/nested_local.nq" >/dev/null
build_generated
assert_eq "nested-local" "$(run_output "$TMP_DIR/output")" "12"

write_case "$TMP_DIR/check_ok.nq" <<'EOF'
print 99
EOF
rm -f "$ROOT_DIR/build/output.asm"
"$ROOT_DIR/nql" --check "$TMP_DIR/check_ok.nq" >/dev/null
if [[ -f "$ROOT_DIR/build/output.asm" ]]; then
    printf 'FAIL check-mode\nbuild/output.asm should not be written by --check\n' >&2
    exit 1
fi
printf 'PASS check-mode\n'

rm -f "$ROOT_DIR/build/output.asm"
: > "$TMP_DIR/empty.nq"
"$ROOT_DIR/nql" --check "$TMP_DIR/empty.nq" >/dev/null
"$ROOT_DIR/nql" "$TMP_DIR/empty.nq" >/dev/null
build_generated
assert_eq "empty-source" "$(run_output "$TMP_DIR/output")" ""

python3 - <<'PY' > "$TMP_DIR/read_large_source.nq"
for i in range(120):
    print(f"print {i}")
PY
"$ROOT_DIR/nql" "$TMP_DIR/read_large_source.nq" >/dev/null
build_generated
read_large_out="$(run_output "$TMP_DIR/output")"
if ! printf '%s\n' "$read_large_out" | grep -q '^119$'; then
    printf 'FAIL read-large-source\nmissing final line after source read\n' >&2
    exit 1
fi
printf 'PASS read-large-source\n'

write_case "$TMP_DIR/function_scope_local.nq" <<'EOF'
func scope_demo() {
if 1 == 1 {
var y = 7
}
return y
}
print scope_demo()
EOF
"$ROOT_DIR/nql" "$TMP_DIR/function_scope_local.nq" >/dev/null
build_generated
assert_eq "function-scope-local" "$(run_output "$TMP_DIR/output")" "7"

write_case "$TMP_DIR/emit_ok.nq" <<'EOF'
print 11
EOF
rm -f "$TMP_DIR/custom.asm"
emit_out="$("$ROOT_DIR/nql" --emit "$TMP_DIR/custom.asm" "$TMP_DIR/emit_ok.nq")"
if [[ ! -f "$TMP_DIR/custom.asm" ]]; then
    printf 'FAIL emit-mode\nmissing emitted file\n' >&2
    exit 1
fi
if ! printf '%s\n' "$emit_out" | grep -q "OK: $TMP_DIR/custom.asm written"; then
    printf 'FAIL emit-mode\nmissing emitted output message\n' >&2
    exit 1
fi
printf 'PASS emit-mode\n'

dump_tok_out="$("$ROOT_DIR/nql" --dump-tokens "$ROOT_DIR/examples/semantics/branching.nq")"
if ! printf '%s\n' "$dump_tok_out" | grep -q "ELSE"; then
    printf 'FAIL dump-tokens\nmissing ELSE token\n' >&2
    exit 1
fi
if ! printf '%s\n' "$dump_tok_out" | grep -q "IDENT"; then
    printf 'FAIL dump-tokens\nmissing IDENT token\n' >&2
    exit 1
fi
printf 'PASS dump-tokens\n'

dump_ir_out="$("$ROOT_DIR/nql" --dump-ir "$ROOT_DIR/examples/semantics/functions.nq" --release)"
if ! printf '%s\n' "$dump_ir_out" | grep -q "== IR =="; then
    printf 'FAIL dump-ir\nmissing IR header\n' >&2
    exit 1
fi
if ! printf '%s\n' "$dump_ir_out" | grep -q "CALL"; then
    printf 'FAIL dump-ir\nmissing CALL op\n' >&2
    exit 1
fi
printf 'PASS dump-ir\n'

rm -f "$ROOT_DIR/build/output.asm" "$ROOT_DIR/output.asm"
dump_ir_clean_out="$("$ROOT_DIR/nql" --dump-ir "$ROOT_DIR/examples/semantics/functions.nq" --release)"
if ! printf '%s\n' "$dump_ir_clean_out" | grep -q "== IR =="; then
    printf 'FAIL dump-ir-clean\nmissing IR header after clean state\n' >&2
    exit 1
fi
printf 'PASS dump-ir-clean\n'

write_case "$TMP_DIR/opt_fold_release.nq" <<'EOF'
print 8 / 2
print 9 % 4
print 2 + 3 * 4
EOF
opt_ir_out="$("$ROOT_DIR/nql" --dump-ir "$TMP_DIR/opt_fold_release.nq" --release)"
if ! printf '%s\n' "$opt_ir_out" | grep -q "CONST A=4"; then
    printf 'FAIL opt-fold-release\nmissing folded div const\n' >&2
    exit 1
fi
if ! printf '%s\n' "$opt_ir_out" | grep -q "CONST A=1"; then
    printf 'FAIL opt-fold-release\nmissing folded mod const\n' >&2
    exit 1
fi
if ! printf '%s\n' "$opt_ir_out" | grep -q "CONST A=14"; then
    printf 'FAIL opt-fold-release\nmissing chained folded const\n' >&2
    exit 1
fi
if printf '%s\n' "$opt_ir_out" | grep -q $'\tDIV '; then
    printf 'FAIL opt-fold-release\nunexpected DIV op after folding\n' >&2
    exit 1
fi
if printf '%s\n' "$opt_ir_out" | grep -q $'\tMOD '; then
    printf 'FAIL opt-fold-release\nunexpected MOD op after folding\n' >&2
    exit 1
fi
printf 'PASS opt-fold-release\n'

write_case "$TMP_DIR/opt_cmp_release.nq" <<'EOF'
if 2 < 3 {
print 1
} else {
print 0
}
EOF
opt_cmp_ir_out="$("$ROOT_DIR/nql" --dump-ir "$TMP_DIR/opt_cmp_release.nq" --release)"
if ! printf '%s\n' "$opt_cmp_ir_out" | grep -q "CONST A=1"; then
    printf 'FAIL opt-cmp-release\nmissing folded condition const\n' >&2
    exit 1
fi
if printf '%s\n' "$opt_cmp_ir_out" | grep -q $'\tCMP '; then
    printf 'FAIL opt-cmp-release\nunexpected CMP op after folding\n' >&2
    exit 1
fi
if printf '%s\n' "$opt_cmp_ir_out" | grep -q $'\tJZ '; then
    printf 'FAIL opt-cmp-release\nunexpected JZ op after folding\n' >&2
    exit 1
fi
printf 'PASS opt-cmp-release\n'

write_case "$TMP_DIR/opt_label_prune_release.nq" <<'EOF'
if 2 < 3 {
print 1
} else {
print 0
}
EOF
opt_label_ir_out="$("$ROOT_DIR/nql" --dump-ir "$TMP_DIR/opt_label_prune_release.nq" --release)"
if printf '%s\n' "$opt_label_ir_out" | grep -q "CONST A=0"; then
    printf 'FAIL opt-label-prune-release\nunexpected dead else const after pruning\n' >&2
    exit 1
fi
print_count="$(printf '%s\n' "$opt_label_ir_out" | grep -c $'\tPRINT_INT ')"
if [[ "$print_count" != "1" ]]; then
    printf 'FAIL opt-label-prune-release\nexpected exactly one PRINT_INT, got %s\n' "$print_count" >&2
    exit 1
fi
const_count="$(printf '%s\n' "$opt_label_ir_out" | grep -c $'\tCONST ')"
if [[ "$const_count" != "1" ]]; then
    printf 'FAIL opt-label-prune-release\nexpected exactly one CONST after cleanup, got %s\n' "$const_count" >&2
    exit 1
fi
if printf '%s\n' "$opt_label_ir_out" | grep -q $'\tJMP '; then
    printf 'FAIL opt-label-prune-release\nunexpected JMP to next label after cleanup\n' >&2
    exit 1
fi
printf 'PASS opt-label-prune-release\n'

if "$ROOT_DIR/nql" run --dump-ir "$ROOT_DIR/examples/semantics/branching.nq" >/dev/null 2>"$TMP_DIR/run_dump.err"; then
    printf 'FAIL run-dump-conflict\nexpected wrapper failure\n' >&2
    exit 1
fi
if ! grep -q -- "run cannot be used with --dump-ir" "$TMP_DIR/run_dump.err"; then
    printf 'FAIL run-dump-conflict\nmissing wrapper error message\n' >&2
    exit 1
fi
printf 'PASS run-dump-conflict\n'

write_case "$TMP_DIR/no_linker_warning_on_frontend_error.nq" <<'EOF'
var a = [1]
a[0] 1
EOF
if "$ROOT_DIR/nql" "$TMP_DIR/no_linker_warning_on_frontend_error.nq" >"$TMP_DIR/no_linker_warning_on_frontend_error.err" 2>&1; then
    printf 'FAIL frontend-error-no-linker-warning\nexpected compiler failure\n' >&2
    exit 1
fi
if ! grep -q -- "expected '=' in assignment" "$TMP_DIR/no_linker_warning_on_frontend_error.err"; then
    printf 'FAIL frontend-error-no-linker-warning\nmissing frontend error message\n' >&2
    exit 1
fi
if grep -q -- "ld: warning" "$TMP_DIR/no_linker_warning_on_frontend_error.err"; then
    printf 'FAIL frontend-error-no-linker-warning\nunexpected linker warning on frontend error\n' >&2
    exit 1
fi
printf 'PASS frontend-error-no-linker-warning\n'

# Generate a recursive function that allocates 200-element arrays each call.
# 36 calls * (200+34 slots) = 8424 > 8192 → triggers "array heap overflow"
python3 - <<'PY' > "$TMP_DIR/array_heap_overflow.nq"
elems = ",".join("0" for _ in range(200))
print("func alloc_arr(n) {")
print(f"var a = [{elems}]")
print("if n > 1 {")
print("alloc_arr(n-1)")
print("}")
print("return len(a)")
print("}")
print("alloc_arr(36)")
PY
"$ROOT_DIR/nql" "$TMP_DIR/array_heap_overflow.nq" >/dev/null
build_generated
assert_runtime_fail "array-heap-overflow" "$TMP_DIR/output" "array heap overflow"

write_case "$TMP_DIR/array_oob_load.nq" <<'EOF'
var a = [1,2,3]
print a[3]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/array_oob_load.nq" >/dev/null
build_generated
assert_runtime_fail "array-oob-load" "$TMP_DIR/output" "array index out of bounds"

write_case "$TMP_DIR/array_oob_store.nq" <<'EOF'
var a = [1,2,3]
a[3] = 9
print a[0]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/array_oob_store.nq" >/dev/null
build_generated
assert_runtime_fail "array-oob-store" "$TMP_DIR/output" "array index out of bounds"

write_case "$TMP_DIR/global_mutate.nq" <<'EOF2'
var counter = 0
func inc() {
    counter = counter + 1
    return counter
}
print inc()
print inc()
print inc()
EOF2
"$ROOT_DIR/nql" "$TMP_DIR/global_mutate.nq" >/dev/null
build_generated
assert_eq "global-mutate" "$(run_output "$TMP_DIR/output")" "1
2
3"

write_case "$TMP_DIR/type_assign_global.nq" <<'EOF'
var x = 5
x = "hello"
print x
EOF
assert_compile_fail "type-assign-global" "$TMP_DIR/type_assign_global.nq" "type error: assignment type mismatch"

write_case "$TMP_DIR/type_assign_local.nq" <<'EOF'
func foo() {
var y = 10
y = "bad"
return y
}
print foo()
EOF
assert_compile_fail "type-assign-local" "$TMP_DIR/type_assign_local.nq" "type error: assignment type mismatch"

write_case "$TMP_DIR/type_assign_fn_global.nq" <<'EOF'
var g = 42
func bar() {
g = "wrong"
}
bar()
print g
EOF
assert_compile_fail "type-assign-fn-global" "$TMP_DIR/type_assign_fn_global.nq" "type error: assignment type mismatch"

write_case "$TMP_DIR/type_assign_ok.nq" <<'EOF'
var x = 1
x = 99
print x
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_assign_ok.nq" >/dev/null
build_generated
assert_eq "type-assign-ok" "$(run_output "$TMP_DIR/output")" "99"

write_case "$TMP_DIR/type_ret_int_str.nq" <<'EOF'
func foo(x) {
if x == 1 {
return 42
}
return "hello"
}
print foo(1)
EOF
assert_compile_fail "type-ret-int-str" "$TMP_DIR/type_ret_int_str.nq" "type error: inconsistent return types"

write_case "$TMP_DIR/type_ret_str_int.nq" <<'EOF'
func bad(x) {
if x == 0 {
return "zero"
}
return 99
}
print bad(0)
EOF
assert_compile_fail "type-ret-str-int" "$TMP_DIR/type_ret_str_int.nq" "type error: inconsistent return types"

write_case "$TMP_DIR/type_ret_consistent_ok.nq" <<'EOF'
func bar(x) {
if x == 0 {
return 0
}
return x + 1
}
print bar(5)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_ret_consistent_ok.nq" >/dev/null
build_generated
assert_eq "type-ret-consistent-ok" "$(run_output "$TMP_DIR/output")" "6"

write_case "$TMP_DIR/type_ret_propagate_assign.nq" <<'EOF'
func get_str() {
return "hello"
}
var x = get_str()
x = 99
print x
EOF
assert_compile_fail "type-ret-propagate-assign" "$TMP_DIR/type_ret_propagate_assign.nq" "type error: assignment type mismatch"

write_case "$TMP_DIR/type_ret_propagate_arith.nq" <<'EOF'
func get_str() {
return "bad"
}
print get_str() + 1
EOF
assert_compile_fail "type-ret-propagate-arith" "$TMP_DIR/type_ret_propagate_arith.nq" "type error: '+' on non-string operand"

write_case "$TMP_DIR/type_ret_propagate_ok.nq" <<'EOF'
func make_int() {
return 7
}
var y = make_int()
y = 99
print y
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_ret_propagate_ok.nq" >/dev/null
build_generated
assert_eq "type-ret-propagate-ok" "$(run_output "$TMP_DIR/output")" "99"

write_case "$TMP_DIR/type_print_arr.nq" <<'EOF'
var a = [1, 2, 3]
print a
EOF
assert_compile_fail "type-print-arr" "$TMP_DIR/type_print_arr.nq" "type error: cannot print array"

write_case "$TMP_DIR/type_print_str_expr.nq" <<'EOF'
func get_str() {
return "hello"
}
print get_str()
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_print_str_expr.nq" >/dev/null
build_generated
assert_eq "type-print-str-expr" "$(run_output "$TMP_DIR/output")" "hello"

write_case "$TMP_DIR/type_print_str_ok.nq" <<'EOF'
var s = "world"
print s
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_print_str_ok.nq" >/dev/null
build_generated
assert_eq "type-print-str-ok" "$(run_output "$TMP_DIR/output")" "world"

write_case "$TMP_DIR/type_print_int_ok.nq" <<'EOF'
var x = 42
print x
print x + 1
print 99
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_print_int_ok.nq" >/dev/null
build_generated
assert_eq "type-print-int-ok" "$(run_output "$TMP_DIR/output")" "42
43
99"

write_case "$TMP_DIR/type_cmp_arr_int.nq" <<'EOF'
var a = [1, 2, 3]
if a == 1 {
print 1
}
EOF
assert_compile_fail "type-cmp-arr-int" "$TMP_DIR/type_cmp_arr_int.nq" "type error: cannot compare array"

write_case "$TMP_DIR/type_cmp_arr_arr.nq" <<'EOF'
var a = [1, 2]
var b = [3, 4]
if a == b {
print 1
}
EOF
assert_compile_fail "type-cmp-arr-arr" "$TMP_DIR/type_cmp_arr_arr.nq" "type error: cannot compare array"

write_case "$TMP_DIR/type_cmp_str_int.nq" <<'EOF'
func get_str() {
return "hello"
}
if get_str() == 1 {
print 1
}
EOF
assert_compile_fail "type-cmp-str-int" "$TMP_DIR/type_cmp_str_int.nq" "type error: cannot compare string expression"

write_case "$TMP_DIR/type_cmp_int_ok.nq" <<'EOF'
func count() {
return 7
}
if count() == 7 {
print 1
}
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_cmp_int_ok.nq" >/dev/null
build_generated
assert_eq "type-cmp-int-ok" "$(run_output "$TMP_DIR/output")" "1"

write_case "$TMP_DIR/type_param_reassign_mismatch.nq" <<'EOF'
func foo(x) {
x = 5
x = "oops"
return x
}
print foo(1)
EOF
assert_compile_fail "type-param-reassign-mismatch" "$TMP_DIR/type_param_reassign_mismatch.nq" "type error: assignment type mismatch"

write_case "$TMP_DIR/type_param_arith_after_str.nq" <<'EOF'
func bar(x) {
x = "hello"
return x + 1
}
print bar(1)
EOF
assert_compile_fail "type-param-arith-after-str" "$TMP_DIR/type_param_arith_after_str.nq" "type error: '+' on non-string operand"

write_case "$TMP_DIR/type_param_arr_print.nq" <<'EOF'
var a = [1, 2, 3]
func show(x) {
x = a
print x
return 0
}
print show(0)
EOF
assert_compile_fail "type-param-arr-print" "$TMP_DIR/type_param_arr_print.nq" "type error: cannot print array"

write_case "$TMP_DIR/type_param_consistent_ok.nq" <<'EOF'
func calc(n) {
n = n + 1
n = n * 2
return n
}
print calc(5)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/type_param_consistent_ok.nq" >/dev/null
build_generated
assert_eq "type-param-consistent-ok" "$(run_output "$TMP_DIR/output")" "12"

# ── unused variable detection ─────────────────────────────────
write_case "$TMP_DIR/unused_global.nq" <<'EOF'
var x = 42
print 1
EOF
assert_compile_fail "unused-global" "$TMP_DIR/unused_global.nq" "unused variable 'x'"

write_case "$TMP_DIR/unused_local.nq" <<'EOF'
func f() {
var z = 10
return 0
}
print f()
EOF
assert_compile_fail "unused-local" "$TMP_DIR/unused_local.nq" "unused variable 'z'"

write_case "$TMP_DIR/unused_used_global.nq" <<'EOF'
var x = 5
print x
EOF
"$ROOT_DIR/nql" "$TMP_DIR/unused_used_global.nq" >/dev/null
build_generated
assert_eq "unused-used-global" "$(run_output "$TMP_DIR/output")" "5"

write_case "$TMP_DIR/unused_used_local.nq" <<'EOF'
func f() {
var z = 7
return z
}
print f()
EOF
"$ROOT_DIR/nql" "$TMP_DIR/unused_used_local.nq" >/dev/null
build_generated
assert_eq "unused-used-local" "$(run_output "$TMP_DIR/output")" "7"

write_case "$TMP_DIR/unused_multi_ok.nq" <<'EOF'
var a = 1
var b = 2
print a + b
EOF
"$ROOT_DIR/nql" "$TMP_DIR/unused_multi_ok.nq" >/dev/null
build_generated
assert_eq "unused-multi-ok" "$(run_output "$TMP_DIR/output")" "3"

# ── dead code detection ───────────────────────────────────────
write_case "$TMP_DIR/dead_after_return.nq" <<'EOF'
func f() {
return 1
print 99
}
print f()
EOF
assert_compile_fail "dead-after-return" "$TMP_DIR/dead_after_return.nq" "unreachable code after return"

write_case "$TMP_DIR/dead_var_after_return.nq" <<'EOF'
func f() {
return 42
var x = 1
return x
}
print f()
EOF
assert_compile_fail "dead-var-after-return" "$TMP_DIR/dead_var_after_return.nq" "unreachable code after return"

write_case "$TMP_DIR/dead_nested_ok.nq" <<'EOF'
func f(x) {
if x == 1 {
return 1
}
return 0
}
print f(1)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/dead_nested_ok.nq" >/dev/null
build_generated
assert_eq "dead-nested-ok" "$(run_output "$TMP_DIR/output")" "1"

write_case "$TMP_DIR/dead_if_else_ok.nq" <<'EOF'
func sign(x) {
if x == 0 {
return 0
} else {
return 1
}
}
print sign(5)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/dead_if_else_ok.nq" >/dev/null
build_generated
assert_eq "dead-if-else-ok" "$(run_output "$TMP_DIR/output")" "1"

# ── str(n) slot interaction ───────────────────────────────────
write_case "$TMP_DIR/its_with_static_str.nq" <<'EOF'
var label = "n="
var n = 7
var s = str(n)
print label
print s
EOF
"$ROOT_DIR/nql" "$TMP_DIR/its_with_static_str.nq" >/dev/null
build_generated
assert_eq "its-with-static-str" "$(run_output "$TMP_DIR/output")" $'n=\n7'

write_case "$TMP_DIR/its_len.nq" <<'EOF'
var n = 42
var s = str(n)
print len(s)
var m = -7
var t = str(m)
print len(t)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/its_len.nq" >/dev/null
build_generated
assert_eq "its-len" "$(run_output "$TMP_DIR/output")" $'2\n2'

write_case "$TMP_DIR/int_builtin_basic.nq" <<'EOF'
var s = "123"
print int(s)
print int("0") + 1
EOF
"$ROOT_DIR/nql" "$TMP_DIR/int_builtin_basic.nq" >/dev/null
build_generated
assert_eq "int-builtin-basic" "$(run_output "$TMP_DIR/output")" $'123\n1'

write_case "$TMP_DIR/int_builtin_min_max_abs.nq" <<'EOF'
print abs(0 - 7)
print min(3, 5)
print min(0 - 4, 2)
print max(3, 5)
print max(0 - 4, 2)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/int_builtin_min_max_abs.nq" >/dev/null
build_generated
assert_eq "int-builtin-min-max-abs" "$(run_output "$TMP_DIR/output")" $'7\n3\n-4\n5\n2'

write_case "$TMP_DIR/str_concat_basic.nq" <<'EOF'
var x = "ab"
var y = "cd"
print x + y
print "x=" + str(42)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_concat_basic.nq" >/dev/null
build_generated
assert_eq "str-concat-basic" "$(run_output "$TMP_DIR/output")" $'abcd\nx=42'

write_case "$TMP_DIR/str_concat_type_err.nq" <<'EOF'
var s = "hello"
print s + 5
EOF
assert_compile_fail "str-concat-type-err" "$TMP_DIR/str_concat_type_err.nq" "type error: '+' on non-string operand"

write_case "$TMP_DIR/global_redecl.nq" <<'EOF'
var x = 5
var x = 10
print x
EOF
assert_compile_fail "global-redecl" "$TMP_DIR/global_redecl.nq" "duplicate"

write_case "$TMP_DIR/undecl_assign_global.nq" <<'EOF'
x = 10
print x
EOF
assert_compile_fail "undecl-assign-global" "$TMP_DIR/undecl_assign_global.nq" "undefined variable"

write_case "$TMP_DIR/undecl_assign_local.nq" <<'EOF'
func foo() {
z = 5
print z
}
foo()
EOF
assert_compile_fail "undecl-assign-local" "$TMP_DIR/undecl_assign_local.nq" "undefined variable"

write_case "$TMP_DIR/local_shadow_global.nq" <<'EOF'
var x = 10
func foo() {
var x = 99
print x
}
foo()
print x
EOF
"$ROOT_DIR/nql" "$TMP_DIR/local_shadow_global.nq" >/dev/null
build_generated
assert_eq "local-shadow-global" "$(run_output "$TMP_DIR/output")" $'99\n10'

write_case "$TMP_DIR/var_self_ref.nq" <<'EOF'
var x = 10
func f() {
var x = x + 1
return x
}
print x
print f()
print x
EOF
"$ROOT_DIR/nql" "$TMP_DIR/var_self_ref.nq" >/dev/null
build_generated
assert_eq "var-self-ref" "$(run_output "$TMP_DIR/output")" $'10\n11\n10'

write_case "$TMP_DIR/str_arr_basic.nq" <<'EOF'
var a = ["hello", "world"]
print a[0]
print a[1]
print len(a)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_arr_basic.nq" >/dev/null
build_generated
assert_eq "str-arr-basic" "$(run_output "$TMP_DIR/output")" $'hello\nworld\n2'

write_case "$TMP_DIR/str_arr_fn.nq" <<'EOF'
func first(arr str[], n) {
return arr[0]
}
var names = ["Ana", "Budi"]
print first(names, 2)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_arr_fn.nq" >/dev/null
build_generated
assert_eq "str-arr-fn" "$(run_output "$TMP_DIR/output")" "Ana"

write_case "$TMP_DIR/str_arr_type_err.nq" <<'EOF'
var a = ["x", "y"]
print a
EOF
assert_compile_fail "str-arr-type-err" "$TMP_DIR/str_arr_type_err.nq" "cannot print array"

write_case "$TMP_DIR/str_arr_foreach.nq" <<'EOF'
var names = ["Alice", "Bob", "Carol"]
for x in names {
print x
}
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_arr_foreach.nq" >/dev/null
build_generated
assert_eq "str-arr-foreach" "$(run_output "$TMP_DIR/output")" $'Alice\nBob\nCarol'

write_case "$TMP_DIR/push_int.nq" <<'EOF'
var a = int[]
push(a, 10)
push(a, 20)
push(a, 30)
print len(a)
print a[1]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/push_int.nq" >/dev/null
build_generated
assert_eq "push-int" "$(run_output "$TMP_DIR/output")" $'3\n20'

write_case "$TMP_DIR/push_str.nq" <<'EOF'
var s = str[]
push(s, "hello")
push(s, "world")
print len(s)
print s[0]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/push_str.nq" >/dev/null
build_generated
assert_eq "push-str" "$(run_output "$TMP_DIR/output")" $'2\nhello'

write_case "$TMP_DIR/pop_int.nq" <<'EOF'
var a = int[]
push(a, 10)
push(a, 20)
print pop(a)
print len(a)
print pop(a)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/pop_int.nq" >/dev/null
build_generated
assert_eq "pop-int" "$(run_output "$TMP_DIR/output")" $'20\n1\n10'

write_case "$TMP_DIR/pop_str.nq" <<'EOF'
var s = str[]
push(s, "hello")
push(s, "world")
print pop(s)
print len(s)
print pop(s)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/pop_str.nq" >/dev/null
build_generated
assert_eq "pop-str" "$(run_output "$TMP_DIR/output")" $'world\n1\nhello'

write_case "$TMP_DIR/push_type_err.nq" <<'EOF'
var x = 42
push(x, 1)
EOF
assert_compile_fail "push-type-err" "$TMP_DIR/push_type_err.nq" "push() first argument must be an array"

write_case "$TMP_DIR/push_int_value_type_err.nq" <<'EOF'
var a = int[]
push(a, "x")
EOF
assert_compile_fail "push-int-value-type-err" "$TMP_DIR/push_int_value_type_err.nq" "push() value type does not match array element type"

write_case "$TMP_DIR/push_str_value_type_err.nq" <<'EOF'
var s = str[]
push(s, 7)
EOF
assert_compile_fail "push-str-value-type-err" "$TMP_DIR/push_str_value_type_err.nq" "push() value type does not match array element type"

write_case "$TMP_DIR/pop_type_err.nq" <<'EOF'
var x = 42
print pop(x)
EOF
assert_compile_fail "pop-type-err" "$TMP_DIR/pop_type_err.nq" "pop() argument must be an array"

write_case "$TMP_DIR/pop_empty.nq" <<'EOF'
var a = int[]
print pop(a)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/pop_empty.nq" >/dev/null
build_generated
assert_runtime_fail "pop-empty" "$TMP_DIR/output" "array pop: array is empty"



write_case "$TMP_DIR/arg_bounds.nq" <<EOF
print argc
print arg(-1)
print arg(-2)
print arg(0)
print arg(1)
print arg(2)
print arg(3)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/arg_bounds.nq" >/dev/null
build_generated
assert_eq "arg-bounds" "$(run_output "$TMP_DIR/output" 7 -3 123x)" $'3\n0\n0\n7\n-3\n123\n0'

write_case "$TMP_DIR/argc_condition.nq" <<EOF
if argc < 1 {
print 7
} else {
print 9
}
EOF
"$ROOT_DIR/nql" "$TMP_DIR/argc_condition.nq" >/dev/null
build_generated
assert_eq "argc-condition-empty" "$(run_output "$TMP_DIR/output")" "7"
assert_eq "argc-condition-one" "$(run_output "$TMP_DIR/output" x)" "9"

write_case "$TMP_DIR/arg_str_basic.nq" <<EOF
print argc
print len(arg_str(0))
print arg_str(0) + "!"
print len(arg_str(1))
print len(arg_str(9))
EOF
"$ROOT_DIR/nql" "$TMP_DIR/arg_str_basic.nq" >/dev/null
build_generated
assert_eq "arg-str-basic" "$(run_output "$TMP_DIR/output" hello -3)" $'2\n5\nhello!\n2\n0'

"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/arg_str_basic.nq" > "$TMP_DIR/arg_str_basic.ir"
assert_file_contains "arg-str-ir" "$TMP_DIR/arg_str_basic.ir" "ARG_STR"

write_case "$TMP_DIR/arg_str_type_err.nq" <<EOF
print arg_str("x")
EOF
assert_compile_fail "arg-str-type-err" "$TMP_DIR/arg_str_type_err.nq" "arg_str() index must be an integer"


write_case "$TMP_DIR/exit_basic.nq" <<EOF
print 1
exit(7)
print 2
EOF
"$ROOT_DIR/nql" "$TMP_DIR/exit_basic.nq" >/dev/null
build_generated
set +e
run_output "$TMP_DIR/output" > "$TMP_DIR/exit_basic.out"
exit_status=$?
set -e
if [[ "$exit_status" -ne 7 ]]; then
    printf 'FAIL %s
expected exit status 7, got %s
' "exit-basic-status" "$exit_status" >&2
    exit 1
fi
printf 'PASS %s
' "exit-basic-status"
printf '1
' | cmp -s - "$TMP_DIR/exit_basic.out"
printf 'PASS %s
' "exit-basic-output"
"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/exit_basic.nq" > "$TMP_DIR/exit_basic.ir"
assert_file_contains "exit-ir" "$TMP_DIR/exit_basic.ir" "EXIT"

write_case "$TMP_DIR/exit_type_err.nq" <<EOF
exit("x")
EOF
assert_compile_fail "exit-type-err" "$TMP_DIR/exit_type_err.nq" "exit() code must be an integer"

write_case "$TMP_DIR/find_basic.nq" <<EOF
print find("alpha beta", "alpha")
print find("alpha beta", "beta")
print find("alpha beta", "z")
print find("alpha beta", "")
print find(arg_str(0), "lo")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/find_basic.nq" >/dev/null
build_generated
assert_eq "find-basic" "$(run_output "$TMP_DIR/output" hello)" "0
6
-1
0
3"

"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/find_basic.nq" > "$TMP_DIR/find_basic.ir"
assert_file_contains "find-ir" "$TMP_DIR/find_basic.ir" "STR_FIND"

write_case "$TMP_DIR/find_haystack_type_err.nq" <<EOF
print find(123, "x")
EOF
assert_compile_fail "find-haystack-type-err" "$TMP_DIR/find_haystack_type_err.nq" "find() haystack must be a string"

write_case "$TMP_DIR/find_needle_type_err.nq" <<EOF
print find("abc", 1)
EOF
assert_compile_fail "find-needle-type-err" "$TMP_DIR/find_needle_type_err.nq" "find() needle must be a string"

write_case "$TMP_DIR/slice_basic.nq" <<EOF
print slice("abcdef", 0, 3)
print slice("abcdef", 2, 6)
print len(slice("abcdef", 2, 2))
print find(slice(arg_str(0), 1, 4), "bc")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/slice_basic.nq" >/dev/null
build_generated
assert_eq "slice-basic" "$(run_output "$TMP_DIR/output" xabcd)" "abc
cdef
0
1"

"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/slice_basic.nq" > "$TMP_DIR/slice_basic.ir"
assert_file_contains "slice-ir" "$TMP_DIR/slice_basic.ir" "STR_SLICE"

write_case "$TMP_DIR/slice_source_type_err.nq" <<EOF
print slice(123, 0, 1)
EOF
assert_compile_fail "slice-source-type-err" "$TMP_DIR/slice_source_type_err.nq" "slice() source must be a string"

write_case "$TMP_DIR/slice_start_type_err.nq" <<EOF
print slice("abc", "0", 1)
EOF
assert_compile_fail "slice-start-type-err" "$TMP_DIR/slice_start_type_err.nq" "slice() start must be an integer"

write_case "$TMP_DIR/slice_end_type_err.nq" <<EOF
print slice("abc", 0, "1")
EOF
assert_compile_fail "slice-end-type-err" "$TMP_DIR/slice_end_type_err.nq" "slice() end must be an integer"

write_case "$TMP_DIR/slice_oob.nq" <<EOF
print slice("abc", 0, 4)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/slice_oob.nq" >/dev/null
build_generated
assert_runtime_fail "slice-oob" "$TMP_DIR/output" "slice: index out of bounds"

write_case "$TMP_DIR/input_str_line.nq" <<EOF
var name = input_str()
print name
print len(name)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/input_str_line.nq" >/dev/null
build_generated
expected=$(printf "Alice\n5")
assert_eq "input-str-line" "$(printf "Alice\n" | run_output "$TMP_DIR/output")" "$expected"


printf "alpha\nbeta\n" > "$TMP_DIR/read_file_input.txt"
write_case "$TMP_DIR/read_file_basic.nq" <<EOF
var p = "$TMP_DIR/read_file_input.txt"
var data = read_file(p)
print len(data)
print data[0]
print data[6]
print data
EOF
"$ROOT_DIR/nql" "$TMP_DIR/read_file_basic.nq" >/dev/null
build_generated
expected=$(printf "11\n97\n98\nalpha\nbeta")
assert_eq "read-file-basic" "$(run_output "$TMP_DIR/output")" "$expected"

printf "" > "$TMP_DIR/read_file_empty.txt"
write_case "$TMP_DIR/read_file_empty.nq" <<EOF
var data = read_file("$TMP_DIR/read_file_empty.txt")
print len(data)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/read_file_empty.nq" >/dev/null
build_generated
assert_eq "read-file-empty" "$(run_output "$TMP_DIR/output")" "0"

"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/read_file_basic.nq" > "$TMP_DIR/read_file_basic.ir"
assert_file_contains "read-file-ir" "$TMP_DIR/read_file_basic.ir" "READ_FILE"

write_case "$TMP_DIR/read_file_type_err.nq" <<EOF
print read_file(123)
EOF
assert_compile_fail "read-file-type-err" "$TMP_DIR/read_file_type_err.nq" "read_file() path must be a string"

write_case "$TMP_DIR/read_file_missing.nq" <<EOF
print read_file("$TMP_DIR/no_such_file.nq")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/read_file_missing.nq" >/dev/null
build_generated
assert_runtime_fail "read-file-open-err" "$TMP_DIR/output" "read_file: cannot open file"

write_case "$TMP_DIR/write_file_basic.nq" <<EOF
var n = write_file("$TMP_DIR/write_file_out.txt", "hello file")
print n
EOF
"$ROOT_DIR/nql" "$TMP_DIR/write_file_basic.nq" >/dev/null
build_generated
assert_eq "write-file-basic" "$(run_output "$TMP_DIR/output")" "10"
assert_eq "write-file-content" "$(cat "$TMP_DIR/write_file_out.txt")" "hello file"

write_case "$TMP_DIR/write_file_empty.nq" <<EOF
print write_file("$TMP_DIR/write_file_empty.txt", "")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/write_file_empty.nq" >/dev/null
build_generated
assert_eq "write-file-empty" "$(run_output "$TMP_DIR/output")" "0"
assert_eq "write-file-empty-content" "$(wc -c < "$TMP_DIR/write_file_empty.txt")" "0"

"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/write_file_basic.nq" > "$TMP_DIR/write_file_basic.ir"
assert_file_contains "write-file-ir" "$TMP_DIR/write_file_basic.ir" "WRITE_FILE"

write_case "$TMP_DIR/write_file_path_type_err.nq" <<EOF
print write_file(123, "x")
EOF
assert_compile_fail "write-file-path-type-err" "$TMP_DIR/write_file_path_type_err.nq" "write_file() path must be a string"

write_case "$TMP_DIR/write_file_data_type_err.nq" <<EOF
print write_file("$TMP_DIR/out.txt", 123)
EOF
assert_compile_fail "write-file-data-type-err" "$TMP_DIR/write_file_data_type_err.nq" "write_file() data must be a string"

write_case "$TMP_DIR/write_file_open_err.nq" <<EOF
print write_file("$TMP_DIR/no_such_dir/out.txt", "x")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/write_file_open_err.nq" >/dev/null
build_generated
assert_runtime_fail "write-file-open-err" "$TMP_DIR/output" "write_file: cannot open file"

write_case "$TMP_DIR/append_file_basic.nq" <<EOF
print append_file("$TMP_DIR/append_file_out.txt", "ab")
print append_file("$TMP_DIR/append_file_out.txt", "cd")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/append_file_basic.nq" >/dev/null
build_generated
assert_eq "append-file-basic" "$(run_output "$TMP_DIR/output" | grep -c 2)" "2"
assert_eq "append-file-content" "$(cat "$TMP_DIR/append_file_out.txt")" "abcd"

"$ROOT_DIR/nql" --dump-ir "$TMP_DIR/append_file_basic.nq" > "$TMP_DIR/append_file_basic.ir"
assert_file_contains "append-file-ir" "$TMP_DIR/append_file_basic.ir" "APPEND_FILE"

write_case "$TMP_DIR/append_file_empty.nq" <<EOF
print append_file("$TMP_DIR/append_file_out.txt", "")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/append_file_empty.nq" >/dev/null
build_generated
assert_eq "append-file-empty" "$(run_output "$TMP_DIR/output")" "0"
assert_eq "append-file-empty-content" "$(cat "$TMP_DIR/append_file_out.txt")" "abcd"

write_case "$TMP_DIR/file_builtin_statement.nq" <<EOF
write_file("$TMP_DIR/file_builtin_statement.txt", "A")
append_file("$TMP_DIR/file_builtin_statement.txt", "B")
var data = read_file("$TMP_DIR/file_builtin_statement.txt")
print data
EOF
"$ROOT_DIR/nql" "$TMP_DIR/file_builtin_statement.nq" >/dev/null
build_generated
assert_eq "file-builtin-statement" "$(run_output "$TMP_DIR/output")" "AB"
assert_eq "file-builtin-statement-content" "$(cat "$TMP_DIR/file_builtin_statement.txt")" "AB"

write_case "$TMP_DIR/append_file_path_type_err.nq" <<EOF
print append_file(123, "x")
EOF
assert_compile_fail "append-file-path-type-err" "$TMP_DIR/append_file_path_type_err.nq" "type error: append_file() path must be a string"

write_case "$TMP_DIR/append_file_data_type_err.nq" <<EOF
print append_file("$TMP_DIR/out.txt", 123)
EOF
assert_compile_fail "append-file-data-type-err" "$TMP_DIR/append_file_data_type_err.nq" "type error: append_file() data must be a string"

write_case "$TMP_DIR/append_file_open_err.nq" <<EOF
print append_file("$TMP_DIR/no_such_dir/out.txt", "x")
EOF
"$ROOT_DIR/nql" "$TMP_DIR/append_file_open_err.nq" >/dev/null
build_generated
assert_runtime_fail "append-file-open-err" "$TMP_DIR/output" "append_file: cannot open file"

printf "x" > "$TMP_DIR/fd_stress_input.txt"
write_case "$TMP_DIR/file_fd_cleanup.nq" <<EOF
var i = 0
var data = ""
var n = 0
while i < 80 {
data = read_file("$TMP_DIR/fd_stress_input.txt")
n = write_file("$TMP_DIR/fd_stress_output.txt", data)
n = append_file("$TMP_DIR/fd_stress_output.txt", "")
i = i + 1
}
print i
print n
EOF
"$ROOT_DIR/nql" "$TMP_DIR/file_fd_cleanup.nq" >/dev/null
build_generated
assert_eq "file-fd-cleanup" "$(
    ulimit -n 64
    run_output "$TMP_DIR/output"
)" $'80\n0'
