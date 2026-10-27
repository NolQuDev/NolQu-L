#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

write_case "$TMP_DIR/parity_add.nq" <<'EOF'
func add(a, b) {
return a + b
}

print add(2, 3)
EOF
assert_backend_parity "ir-parity-add" "$TMP_DIR/parity_add.nq"

write_case "$TMP_DIR/parity_argument_patterns.nq" <<'EOF'
func pack(a, b, c, d, e, f, g, h) {
return a + b + c + d + e + f + g + h
}

func at(a, i) {
return a[i]
}

print pack(1, 2, 3, 4, 5, 6, 7, 8)

var g = [10,20,30]
print at(g, 1)
EOF
assert_backend_parity "ir-parity-argument-patterns" "$TMP_DIR/parity_argument_patterns.nq"

write_case "$TMP_DIR/parity_max_params.nq" <<'EOF'
func sum16(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) {
return a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p
}

print sum16(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)
EOF
assert_backend_parity "ir-parity-max-params" "$TMP_DIR/parity_max_params.nq"

write_case "$TMP_DIR/parity_println.nq" <<'EOF'
println
println "halo"
println 1, "dua"
EOF
assert_backend_parity "ir-parity-println" "$TMP_DIR/parity_println.nq"

write_case "$TMP_DIR/parity_compound_assign.nq" <<'EOF'
var x = 10
x += 5
x -= 3
x *= 2
x /= 4
x %= 3
print x
EOF
assert_backend_parity "ir-parity-compound-assign" "$TMP_DIR/parity_compound_assign.nq"

write_case "$TMP_DIR/parity_elif.nq" <<'EOF'
func score(x) {
if x == 1 {
return 10
} elif x == 2 {
return 20
} else {
return 30
}
}

print score(2)
EOF
assert_backend_parity "ir-parity-elif" "$TMP_DIR/parity_elif.nq"

write_case "$TMP_DIR/parity_logical_condition.nq" <<'EOF'
var hits = 0
func mark(v) {
hits += v
return v
}

if mark(0) == 1 and mark(10) == 10 {
print 100
} else {
print hits
}

if mark(1) == 1 or mark(20) == 20 {
print hits
} else {
print 200
}

if not hits == 1 {
print 300
} else {
print hits
}
EOF
assert_backend_parity "ir-parity-logical-condition" "$TMP_DIR/parity_logical_condition.nq"

write_case "$TMP_DIR/parity_bool_literals.nq" <<'EOF'
print true
print false
print not true
print true + 41
EOF
assert_backend_parity "ir-parity-bool-literals" "$TMP_DIR/parity_bool_literals.nq"

write_case "$TMP_DIR/parity_bitwise_ops.nq" <<'EOF'
print 0b1100 & 0b1010
print 0b1100 | 0b0011
print 0b1100 ^ 0b1010
print (0b1111 & 0b0101) + 2
EOF
assert_backend_parity "ir-parity-bitwise-ops" "$TMP_DIR/parity_bitwise_ops.nq"

write_case "$TMP_DIR/parity_bitwise_not.nq" <<'EOF'
print ~0
print ~0b1010
print ~(0b1111 & 0b0101)
EOF
assert_backend_parity "ir-parity-bitwise-not" "$TMP_DIR/parity_bitwise_not.nq"

write_case "$TMP_DIR/parity_bitwise_shift.nq" <<'EOF'
print 1 << 3
print 16 >> 2
print 2 + (3 << 2)
print (32 >> 3) + 1
EOF
assert_backend_parity "ir-parity-bitwise-shift" "$TMP_DIR/parity_bitwise_shift.nq"

write_case "$TMP_DIR/parity_bitwise_shift_mask.nq" <<'EOF'
print 1 << 64
print 8 >> 64
print 1 << -1
print -8 >> -1
EOF
assert_backend_parity "ir-parity-bitwise-shift-mask" "$TMP_DIR/parity_bitwise_shift_mask.nq"

write_case "$TMP_DIR/parity_nested_argument_calls.nq" <<'EOF'
func add(a, b, c, d) {
return a + b + c + d
}

func inc(x) {
return x + 1
}

func at(a, i) {
return a[i]
}

var g = [10,20,30]
print add(inc(1), inc(2), at(g, 0), at(g, 2))
EOF
assert_backend_parity "ir-parity-nested-argument-calls" "$TMP_DIR/parity_nested_argument_calls.nq"

write_case "$TMP_DIR/parity_argument_order.nq" <<'EOF'
var g = [0]

func step(x) {
g[0] = g[0] * 10 + x
return x
}

func pack(a, b, c) {
return a + b + c
}

print pack(step(1), step(2), step(3))
print g[0]
EOF
assert_backend_parity "ir-parity-argument-order" "$TMP_DIR/parity_argument_order.nq"

write_case "$TMP_DIR/parity_argument_stress.nq" <<'EOF'
var g = [1,2,3]

func touch(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
}
g[1] = g[1] + n
return touch(n - 1) + g[1]
}

func wrap(x) {
return x + 1
}

func pack(a, b, c) {
return a + b + c
}

print pack(wrap(touch(0)), wrap(touch(1)), g[1])
print g[0]
print g[1]
EOF
assert_backend_parity "ir-parity-argument-stress" "$TMP_DIR/parity_argument_stress.nq"

write_case "$TMP_DIR/parity_zero_arg_calls.nq" <<'EOF'
func one() {
return 1
}

func add(a, b) {
return a + b
}

print one()
print add(one(), 4)
EOF
assert_backend_parity "ir-parity-zero-arg-calls" "$TMP_DIR/parity_zero_arg_calls.nq"

write_case "$TMP_DIR/parity_array_argument_mutation.nq" <<'EOF'
func set_mid(a, v) {
a[1] = v
return a[1]
}

var g = [1,2,3]
print set_mid(g, 9)
print g[1]
EOF
assert_backend_parity "ir-parity-array-argument-mutation" "$TMP_DIR/parity_array_argument_mutation.nq"

write_case "$TMP_DIR/parity_multi_array.nq" <<'EOF'
var a = [1,2]
var b = [7,8]
print a[1]
print b[0]
EOF
assert_backend_parity "ir-parity-multi-array" "$TMP_DIR/parity_multi_array.nq"

write_case "$TMP_DIR/parity_print_multi.nq" <<'EOF'
func bump(x) {
return x + 1
}

var g = [7,8,9]
print 1, bump(2), g[1], "halo"
EOF
assert_backend_parity "ir-parity-print-multi" "$TMP_DIR/parity_print_multi.nq"

write_case "$TMP_DIR/parity_call_stmt.nq" <<'EOF'
func bump(x) {
print x
return x + 1
}
bump(2)
print 9
EOF
assert_backend_parity "ir-parity-call-stmt" "$TMP_DIR/parity_call_stmt.nq"

write_case "$TMP_DIR/parity_fact.nq" <<'EOF'
func fact(n) {
if n == 0 {
return 1
}
return n * fact(n - 1)
}

print fact(5)
EOF
assert_backend_parity "ir-parity-fact" "$TMP_DIR/parity_fact.nq"

write_case "$TMP_DIR/parity_loop.nq" <<'EOF'
func loop_sum(n) {
var i = 0
var acc = 0
while i < n {
acc = acc + i
i = i + 1
}
return acc
}

print loop_sum(5)
EOF
assert_backend_parity "ir-parity-loop" "$TMP_DIR/parity_loop.nq"

write_case "$TMP_DIR/parity_for.nq" <<'EOF'
for i in 0..3 {
print i
}
EOF
assert_backend_parity "ir-parity-for" "$TMP_DIR/parity_for.nq"

write_case "$TMP_DIR/parity_for_global_arr.nq" <<'EOF'
var items = [5,10,15]
for x in items {
print x
}
EOF
assert_backend_parity "ir-parity-for-global-arr" "$TMP_DIR/parity_for_global_arr.nq"

write_case "$TMP_DIR/parity_for_func_global.nq" <<'EOF'
var g = [1,2,3]

func touch(i) {
g[i] = g[i] + 1
return g[i]
}

for i in 0..3 {
print touch(i)
}

print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-for-func-global" "$TMP_DIR/parity_for_func_global.nq"

write_case "$TMP_DIR/parity_for_accumulate.nq" <<'EOF'
var g = [2,4,6]

func bump(i) {
g[i] = g[i] + i
return g[i]
}

func total() {
var acc = 0
for i in 0..3 {
acc = acc + bump(i)
}
return acc
}

print total()
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-for-accumulate" "$TMP_DIR/parity_for_accumulate.nq"

write_case "$TMP_DIR/parity_for_else_if_global.nq" <<'EOF'
var g = [1,3,5]

func branchy(i) {
if i == 0 {
g[0] = g[0] + 1
return g[0]
} else if i == 1 {
g[1] = g[1] + 2
return g[1]
} else {
g[2] = g[2] + 3
return g[2]
}
}

for i in 0..3 {
print branchy(i)
}

print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-for-else-if-global" "$TMP_DIR/parity_for_else_if_global.nq"

write_case "$TMP_DIR/parity_for_recursive_helper.nq" <<'EOF'
var g = [2,4,6]

func walk(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
}
g[1] = g[1] + n
return walk(n - 1) + g[1]
}

func drive() {
var acc = 0
for i in 0..3 {
acc = acc + walk(i)
}
return acc
}

print drive()
print g[0]
print g[1]
EOF
assert_backend_parity "ir-parity-for-recursive-helper" "$TMP_DIR/parity_for_recursive_helper.nq"

write_case "$TMP_DIR/parity_break_continue.nq" <<'EOF'
var i = 0
while i < 5 {
i = i + 1
if i == 2 {
continue
}
if i == 4 {
break
}
print i
}
EOF
assert_backend_parity "ir-parity-break-continue" "$TMP_DIR/parity_break_continue.nq"

write_case "$TMP_DIR/parity_nested_break_continue.nq" <<'EOF'
var i = 0
while i < 3 {
var j = 0
while j < 4 {
j = j + 1
if j == 2 {
continue
}
if j == 4 {
break
}
print i + j
}
i = i + 1
}
EOF
assert_backend_parity "ir-parity-nested-break-continue" "$TMP_DIR/parity_nested_break_continue.nq"

write_case "$TMP_DIR/parity_nested_for_break_continue.nq" <<'EOF'
for i in 0..3 {
for j in 0..4 {
if j == 1 {
continue
}
if j == 3 {
break
}
print i + j
}
}
EOF
assert_backend_parity "ir-parity-nested-for-break-continue" "$TMP_DIR/parity_nested_for_break_continue.nq"

write_case "$TMP_DIR/parity_break_continue_helper.nq" <<'EOF'
var g = 0

func bump(i) {
g = g + i
return g
}

var i = 0
while i < 5 {
i = i + 1
var x = bump(i)
if x == 3 {
continue
}
if x > 6 {
break
}
print x
}
print g
EOF
assert_backend_parity "ir-parity-break-continue-helper" "$TMP_DIR/parity_break_continue_helper.nq"

write_case "$TMP_DIR/parity_for_break_continue_helper.nq" <<'EOF'
var g = [1,2,3]

func bump(i) {
g[i] = g[i] + i
return g[i]
}

for i in 0..3 {
var x = bump(i)
if x == 2 {
continue
}
if x > 4 {
break
}
print x
}
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-for-break-continue-helper" "$TMP_DIR/parity_for_break_continue_helper.nq"

write_case "$TMP_DIR/parity_for_recursive_break_continue.nq" <<'EOF'
var g = [1,2,3]

func climb(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
}
g[1] = g[1] + n
return climb(n - 1) + g[1]
}

for i in 0..3 {
var x = climb(i)
if x == 6 {
continue
}
if x > 12 {
break
}
print x
}
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-for-recursive-break-continue" "$TMP_DIR/parity_for_recursive_break_continue.nq"

write_case "$TMP_DIR/parity_for_recursive_array_break_continue.nq" <<'EOF'
var g = [1,2,3]

func touch(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
}
g[1] = g[1] + n
return touch(n - 1) + g[1]
}

for i in 0..3 {
var x = touch(i)
if x == 6 {
continue
}
if x > 12 {
break
}
print x
}
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-for-recursive-array-break-continue" "$TMP_DIR/parity_for_recursive_array_break_continue.nq"

write_case "$TMP_DIR/parity_str.nq" <<'EOF'
print "halo"
EOF
assert_backend_parity "ir-parity-str" "$TMP_DIR/parity_str.nq"

write_case "$TMP_DIR/parity_str_var.nq" <<'EOF'
func label() {
return "ok"
}
var s = "hi"
print s
print label()
EOF
assert_backend_parity "ir-parity-str-var" "$TMP_DIR/parity_str_var.nq"

write_case "$TMP_DIR/parity_str_len.nq" <<'EOF'
func word() {
return "ok"
}
var s = "hi"
print len(s)
print len(word())
EOF
assert_backend_parity "ir-parity-str-len" "$TMP_DIR/parity_str_len.nq"

write_case "$TMP_DIR/parity_int_to_str.nq" <<'EOF'
var label = "n="
var n = 42
var s = str(n)
print label
print s
print len(s)
print str(-7)
EOF
assert_backend_parity "ir-parity-int-to-str" "$TMP_DIR/parity_int_to_str.nq"

write_case "$TMP_DIR/parity_str_to_int.nq" <<EOF
var n = 42
var d = str(n)
print int(d)
var s = "123x"
print int(s)
print int("-7")
print int("abc")
EOF
assert_backend_parity "ir-parity-str-to-int" "$TMP_DIR/parity_str_to_int.nq"

write_case "$TMP_DIR/parity_str_concat.nq" <<EOF
var a = "ab"
var b = "cd"
print a + b
print "x=" + str(42)
print len(a + b)
EOF
assert_backend_parity "ir-parity-str-concat" "$TMP_DIR/parity_str_concat.nq"

write_case "$TMP_DIR/parity_str_at.nq" <<'EOF'
var s = "abc"
print s[0]
print s[2]
print len(s)
EOF
assert_backend_parity "ir-parity-str-at" "$TMP_DIR/parity_str_at.nq"

write_case "$TMP_DIR/parity_str_eq.nq" <<'EOF'
func word() {
return "hi"
}
var s = "hi"
if s == "hi" { print 1 } else { print 0 }
if s != "ok" { print 2 } else { print 9 }
if word() == s { print 3 } else { print 8 }
EOF
assert_backend_parity "ir-parity-str-eq" "$TMP_DIR/parity_str_eq.nq"

write_case "$TMP_DIR/parity_array_store.nq" <<'EOF'
var a = [1,2,3]
a[1] = 9
print a[1]
EOF
assert_backend_parity "ir-parity-array-store" "$TMP_DIR/parity_array_store.nq"

write_case "$TMP_DIR/parity_global_func.nq" <<'EOF'
var base = 10

func add_base(x) {
return base + x
}

print add_base(5)
EOF
assert_backend_parity "ir-parity-global-func" "$TMP_DIR/parity_global_func.nq"

write_case "$TMP_DIR/parity_function_scope_local.nq" <<'EOF'
func scope_demo() {
if 1 == 1 {
var y = 7
}
return y
}

print scope_demo()
EOF
assert_backend_parity "ir-parity-function-scope-local" "$TMP_DIR/parity_function_scope_local.nq"

write_case "$TMP_DIR/parity_if_return.nq" <<'EOF'
func classify(x) {
if x == 0 {
return 100
} else if x == 1 {
return 200
} else {
return 300
}
}

print classify(1)
EOF
assert_backend_parity "ir-parity-if-return" "$TMP_DIR/parity_if_return.nq"

write_case "$TMP_DIR/parity_loop_array.nq" <<'EOF'
var a = [1,2,3]
var i = 0
while i < 3 {
a[i] = a[i] + 1
i = i + 1
}
print a[0]
print a[1]
print a[2]
EOF
assert_backend_parity "ir-parity-loop-array" "$TMP_DIR/parity_loop_array.nq"

write_case "$TMP_DIR/parity_global_recursion.nq" <<'EOF'
var base = 7

func climb(n) {
if n == 0 {
return base
}
return climb(n - 1) + 1
}

print climb(4)
EOF
assert_backend_parity "ir-parity-global-recursion" "$TMP_DIR/parity_global_recursion.nq"

write_case "$TMP_DIR/parity_local_array_func.nq" <<'EOF'
func tweak(i) {
var a = [4,5,6]
a[i] = a[i] + 3
return a[i]
}

print tweak(1)
EOF
assert_backend_parity "ir-parity-local-array-func" "$TMP_DIR/parity_local_array_func.nq"

write_case "$TMP_DIR/parity_branch_array_func.nq" <<'EOF'
func select_bump(i) {
var a = [10,20,30]
if i == 0 {
a[0] = a[0] + 5
} else {
a[1] = a[1] + 7
}
return a[i]
}

print select_bump(0)
print select_bump(1)
EOF
assert_backend_parity "ir-parity-branch-array-func" "$TMP_DIR/parity_branch_array_func.nq"

write_case "$TMP_DIR/parity_global_array_branch.nq" <<'EOF'
var g = [2,4,6]

func pick(i) {
if i == 2 {
return g[2]
}
return g[i]
}

print pick(0)
print pick(2)
EOF
assert_backend_parity "ir-parity-global-array-branch" "$TMP_DIR/parity_global_array_branch.nq"

write_case "$TMP_DIR/parity_global_array_update_func.nq" <<'EOF'
var g = [3,6,9]

func bump_at(i) {
if i == 0 {
g[0] = g[0] + 2
} else {
g[i] = g[i] + 4
}
return g[i]
}

print bump_at(0)
print bump_at(2)
EOF
assert_backend_parity "ir-parity-global-array-update-func" "$TMP_DIR/parity_global_array_update_func.nq"

write_case "$TMP_DIR/parity_mixed_call_flow.nq" <<'EOF'
var g = [5,10,15]

func read_or_bump(i) {
if i == 1 {
g[1] = g[1] + 3
return g[1]
}
return g[i]
}

func combine(a, b) {
return read_or_bump(a) + read_or_bump(b)
}

print combine(0, 1)
print g[1]
EOF
assert_backend_parity "ir-parity-mixed-call-flow" "$TMP_DIR/parity_mixed_call_flow.nq"

write_case "$TMP_DIR/parity_loop_global_array_func.nq" <<'EOF'
var g = [1,2,3]

func bump(i) {
g[i] = g[i] + i
return g[i]
}

func drive(n) {
var i = 0
while i < n {
print bump(i)
i = i + 1
}
return g[0] + g[1] + g[2]
}

print drive(3)
EOF
assert_backend_parity "ir-parity-loop-global-array-func" "$TMP_DIR/parity_loop_global_array_func.nq"

write_case "$TMP_DIR/parity_loop_call_accumulate.nq" <<'EOF'
var g = [2,4,6]

func touch(i) {
if i == 0 {
g[0] = g[0] + 1
} else {
g[i] = g[i] + 2
}
return g[i]
}

func total(n) {
var i = 0
var acc = 0
while i < n {
acc = acc + touch(i)
i = i + 1
}
return acc
}

print total(3)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-loop-call-accumulate" "$TMP_DIR/parity_loop_call_accumulate.nq"

write_case "$TMP_DIR/parity_nested_helper_chain.nq" <<'EOF'
var g = [3,5,7]

func adjust(i) {
if i == 0 {
g[0] = g[0] + 1
} else {
g[i] = g[i] + 2
}
return g[i]
}

func step(i) {
return adjust(i) + 1
}

func run(n) {
var i = 0
var acc = 0
while i < n {
acc = acc + step(i)
i = i + 1
}
return acc
}

print run(3)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-nested-helper-chain" "$TMP_DIR/parity_nested_helper_chain.nq"

write_case "$TMP_DIR/parity_nested_branch_loop_chain.nq" <<'EOF'
var g = [4,8,12]

func mutate(i) {
if i == 1 {
g[1] = g[1] + 5
} else {
g[i] = g[i] + 1
}
return g[i]
}

func choose(i) {
if i == 2 {
return mutate(2)
}
return mutate(i)
}

func drive(n) {
var i = 0
var acc = 0
while i < n {
acc = acc + choose(i)
i = i + 1
}
return acc
}

print drive(3)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-nested-branch-loop-chain" "$TMP_DIR/parity_nested_branch_loop_chain.nq"

write_case "$TMP_DIR/parity_recursive_global_state.nq" <<'EOF'
var g = [1,2,3]

func walk(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
}
g[1] = g[1] + n
return walk(n - 1) + g[1]
}

print walk(2)
print g[0]
print g[1]
EOF
assert_backend_parity "ir-parity-recursive-global-state" "$TMP_DIR/parity_recursive_global_state.nq"

write_case "$TMP_DIR/parity_recursive_array_branch.nq" <<'EOF'
var g = [2,4,6]

func descend(n) {
if n == 0 {
g[2] = g[2] + 1
return g[2]
} else {
if n == 1 {
g[1] = g[1] + 2
return descend(0) + g[1]
} else {
g[0] = g[0] + 3
return descend(n - 1) + g[0]
}
}
}

print descend(2)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-recursive-array-branch" "$TMP_DIR/parity_recursive_array_branch.nq"

write_case "$TMP_DIR/parity_else_if_side_effects.nq" <<'EOF'
var g = [1,3,5,7]

func route(i) {
if i == 0 {
g[0] = g[0] + 10
return g[0]
} else if i == 1 {
g[1] = g[1] + 20
return g[1]
} else if i == 2 {
g[2] = g[2] + 30
return g[2]
} else {
g[3] = g[3] + 40
return g[3]
}
}

print route(0)
print route(1)
print route(2)
print route(3)
print g[0]
print g[1]
print g[2]
print g[3]
EOF
assert_backend_parity "ir-parity-else-if-side-effects" "$TMP_DIR/parity_else_if_side_effects.nq"

write_case "$TMP_DIR/parity_else_if_loop_chain.nq" <<'EOF'
var g = [2,4,6]

func classify(i) {
if i == 0 {
g[0] = g[0] + 1
return g[0]
} else if i == 1 {
g[1] = g[1] + 2
return g[1]
} else {
g[2] = g[2] + 3
return g[2]
}
}

func drive(n) {
var i = 0
var acc = 0
while i < n {
acc = acc + classify(i)
i = i + 1
}
return acc
}

print drive(3)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-else-if-loop-chain" "$TMP_DIR/parity_else_if_loop_chain.nq"

write_case "$TMP_DIR/parity_else_if_recursive_state.nq" <<'EOF'
var g = [1,2,3]

func cascade(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
} else if n == 1 {
g[1] = g[1] + 2
return cascade(0) + g[1]
} else {
g[2] = g[2] + 3
return cascade(n - 1) + g[2]
}
}

print cascade(2)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-else-if-recursive-state" "$TMP_DIR/parity_else_if_recursive_state.nq"

write_case "$TMP_DIR/parity_else_if_recursive_loop.nq" <<'EOF'
var g = [2,3,4]

func branchy(n) {
if n == 0 {
g[0] = g[0] + 1
return g[0]
} else if n == 1 {
g[1] = g[1] + 2
return g[1]
} else {
g[2] = g[2] + 3
return branchy(n - 2) + g[2]
}
}

func drive(n) {
var i = 0
var acc = 0
while i < n {
acc = acc + branchy(i)
i = i + 1
}
return acc
}

print drive(3)
print g[0]
print g[1]
print g[2]
EOF
assert_backend_parity "ir-parity-else-if-recursive-loop" "$TMP_DIR/parity_else_if_recursive_loop.nq"

write_case "$TMP_DIR/parity_param_reassign.nq" <<'NQEOF'
func clamp(x, lo, hi) {
if x < lo {
x = lo
}
if x > hi {
x = hi
}
return x
}

print clamp(5, 1, 10)
print clamp(-3, 0, 7)
print clamp(99, 0, 7)
NQEOF
assert_backend_parity "ir-parity-param-reassign" "$TMP_DIR/parity_param_reassign.nq"

write_case "$TMP_DIR/parity_param_mutate_loop.nq" <<'NQEOF'
func countdown(n) {
var acc = 0
while n > 0 {
acc = acc + n
n = n - 1
}
return acc
}

print countdown(5)
print countdown(0)
NQEOF
assert_backend_parity "ir-parity-param-mutate-loop" "$TMP_DIR/parity_param_mutate_loop.nq"

write_case "$TMP_DIR/parity_array_push_pop.nq" <<EOF
var a = int[]
push(a, 10)
push(a, 20)
push(a, 30)
print len(a)
print a[1]
print pop(a)
print len(a)

var s = str[]
push(s, "hello")
push(s, "world")
print len(s)
print s[0]
print pop(s)
print len(s)
EOF
assert_backend_parity "ir-parity-array-push-pop" "$TMP_DIR/parity_array_push_pop.nq"

write_case "$TMP_DIR/parity_try_catch.nq" <<"NQEOF"
try {
error "boom"
} catch {
print 7
}
print 2
NQEOF
assert_backend_parity "ir-parity-try-catch" "$TMP_DIR/parity_try_catch.nq"

write_case "$TMP_DIR/parity_nested_try_catch.nq" <<"NQEOF"
try {
try {
error "boom"
} catch {
print 7
}
} catch {
print 9
}
NQEOF
assert_backend_parity "ir-parity-nested-try-catch" "$TMP_DIR/parity_nested_try_catch.nq"

write_case "$TMP_DIR/parity_module_call.nq" <<"NQEOF"
module demo {
func inc(x) {
return x + 1
}
}
print demo.inc(4)
NQEOF
assert_backend_parity "ir-parity-module-call" "$TMP_DIR/parity_module_call.nq"
