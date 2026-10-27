#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

write_case "$TMP_DIR/add.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(2, 3)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/add.nq" >/dev/null
build_generated
assert_eq "add" "$(run_output "$TMP_DIR/output")" "5"

write_case "$TMP_DIR/slash_comment.nq" <<'EOF'
// file header comment
print 1 // trailing comment
print 2
EOF
"$ROOT_DIR/nql" "$TMP_DIR/slash_comment.nq" >/dev/null
build_generated
assert_eq "slash-comment" "$(run_output "$TMP_DIR/output")" $'1\n2'

write_case "$TMP_DIR/block_comment.nq" <<'EOF'
/* file header block */
print 1
/* multi-line
   block comment */
print 2
EOF
"$ROOT_DIR/nql" "$TMP_DIR/block_comment.nq" >/dev/null
build_generated
assert_eq "block-comment" "$(run_output "$TMP_DIR/output")" $'1\n2'

write_case "$TMP_DIR/hex_literals.nq" <<'EOF'
print 0xff
print 0x10 + 5
print 0X2a
print 0x7f
EOF
"$ROOT_DIR/nql" "$TMP_DIR/hex_literals.nq" >/dev/null
build_generated
assert_eq "hex-literals" "$(run_output "$TMP_DIR/output")" $'255\n21\n42\n127'

write_case "$TMP_DIR/binary_literals.nq" <<'EOF'
print 0b101010
print 0B11111111
print 0b1000 + 0x2
print 0b01111111
EOF
"$ROOT_DIR/nql" "$TMP_DIR/binary_literals.nq" >/dev/null
build_generated
assert_eq "binary-literals" "$(run_output "$TMP_DIR/output")" $'42\n255\n10\n127'

write_case "$TMP_DIR/numeric_separators.nq" <<'EOF'
print 1_000_000
print 0xff_ff
print 0b1010_0101
print 0x7fff_ffff
EOF
"$ROOT_DIR/nql" "$TMP_DIR/numeric_separators.nq" >/dev/null
build_generated
assert_eq "numeric-separators" "$(run_output "$TMP_DIR/output")" $'1000000\n65535\n165\n2147483647'

write_case "$TMP_DIR/local.nq" <<'EOF'
func foo(a) {
var x = a + 2
return x
}
print foo(5)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/local.nq" >/dev/null
build_generated
assert_eq "local" "$(run_output "$TMP_DIR/output")" "7"

write_case "$TMP_DIR/fact.nq" <<'EOF'
func fact(n) {
if n == 0 {
return 1
}
return n * fact(n - 1)
}
print fact(5)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/fact.nq" >/dev/null
build_generated
assert_eq "fact" "$(run_output "$TMP_DIR/output")" "120"

write_case "$TMP_DIR/array.nq" <<'EOF'
var a = [1,2,3]
print a[1]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/array.nq" >/dev/null
build_generated
assert_eq "array" "$(run_output "$TMP_DIR/output")" "2"

write_case "$TMP_DIR/multi_array.nq" <<'EOF'
var a = [1,2]
var b = [7,8]
print a[1]
print b[0]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/multi_array.nq" >/dev/null
build_generated
assert_eq "multi-array" "$(run_output "$TMP_DIR/output")" $'2\n7'

write_case "$TMP_DIR/else_if.nq" <<'EOF'
func score(x) {
if x == 1 {
return 10
} else if x == 2 {
return 20
} else {
return 30
}
}
print score(2)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/else_if.nq" >/dev/null
build_generated
assert_eq "else-if" "$(run_output "$TMP_DIR/output")" "20"

write_case "$TMP_DIR/elif.nq" <<'EOF'
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
"$ROOT_DIR/nql" "$TMP_DIR/elif.nq" >/dev/null
build_generated
assert_eq "elif" "$(run_output "$TMP_DIR/output")" "20"

write_case "$TMP_DIR/logical_condition.nq" <<'EOF'
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
"$ROOT_DIR/nql" "$TMP_DIR/logical_condition.nq" >/dev/null
build_generated
assert_eq "logical-condition" "$(run_output "$TMP_DIR/output")" $'0\n1\n1'

write_case "$TMP_DIR/bool_literals.nq" <<'EOF'
print true
print false
print not true
print true + 41
EOF
"$ROOT_DIR/nql" "$TMP_DIR/bool_literals.nq" >/dev/null
build_generated
assert_eq "bool-literals" "$(run_output "$TMP_DIR/output")" $'1\n0\n0\n42'

write_case "$TMP_DIR/bitwise_ops.nq" <<'EOF'
print 0b1100 & 0b1010
print 0b1100 | 0b0011
print 0b1100 ^ 0b1010
print (0b1111 & 0b0101) + 2
EOF
"$ROOT_DIR/nql" "$TMP_DIR/bitwise_ops.nq" >/dev/null
build_generated
assert_eq "bitwise-ops" "$(run_output "$TMP_DIR/output")" $'8\n15\n6\n7'

write_case "$TMP_DIR/bitwise_not.nq" <<'EOF'
print ~0
print ~0b1010
print ~(0b1111 & 0b0101)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/bitwise_not.nq" >/dev/null
build_generated
assert_eq "bitwise-not" "$(run_output "$TMP_DIR/output")" $'-1\n-11\n-6'

write_case "$TMP_DIR/bitwise_shift.nq" <<'EOF'
print 1 << 3
print 16 >> 2
print 2 + (3 << 2)
print (32 >> 3) + 1
EOF
"$ROOT_DIR/nql" "$TMP_DIR/bitwise_shift.nq" >/dev/null
build_generated
assert_eq "bitwise-shift" "$(run_output "$TMP_DIR/output")" $'8\n4\n14\n5'

write_case "$TMP_DIR/bitwise_shift_mask.nq" <<'EOF'
print 1 << 64
print 8 >> 64
print 1 << -1
print -8 >> -1
EOF
"$ROOT_DIR/nql" "$TMP_DIR/bitwise_shift_mask.nq" >/dev/null
build_generated
assert_eq "bitwise-shift-mask" "$(run_output "$TMP_DIR/output")" $'1\n8\n-9223372036854775808\n-1'

write_case "$TMP_DIR/compound_assign.nq" <<'EOF'
var x = 10
x += 5
x -= 3
x *= 2
x /= 4
x %= 3
print x
EOF
"$ROOT_DIR/nql" "$TMP_DIR/compound_assign.nq" >/dev/null
build_generated
assert_eq "compound-assign" "$(run_output "$TMP_DIR/output")" "0"

write_case "$TMP_DIR/argument_patterns.nq" <<'EOF'
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
"$ROOT_DIR/nql" "$TMP_DIR/argument_patterns.nq" >/dev/null
build_generated
assert_eq "argument-patterns" "$(run_output "$TMP_DIR/output")" $'36\n20'

write_case "$TMP_DIR/max_params_call.nq" <<'EOF'
func sum16(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) {
return a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p
}
print sum16(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/max_params_call.nq" >/dev/null
build_generated
assert_eq "max-params-call" "$(run_output "$TMP_DIR/output")" "136"

write_case "$TMP_DIR/nested_argument_calls.nq" <<'EOF'
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
"$ROOT_DIR/nql" "$TMP_DIR/nested_argument_calls.nq" >/dev/null
build_generated
assert_eq "nested-argument-calls" "$(run_output "$TMP_DIR/output")" "45"

write_case "$TMP_DIR/argument_order.nq" <<'EOF'
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
"$ROOT_DIR/nql" "$TMP_DIR/argument_order.nq" >/dev/null
build_generated
assert_eq "argument-order" "$(run_output "$TMP_DIR/output")" $'6\n123'

write_case "$TMP_DIR/argument_stress.nq" <<'EOF'
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
"$ROOT_DIR/nql" "$TMP_DIR/argument_stress.nq" >/dev/null
build_generated
assert_eq "argument-stress" "$(run_output "$TMP_DIR/output")" $'13\n3\n3'

write_case "$TMP_DIR/zero_arg_calls.nq" <<'EOF'
func one() {
return 1
}

func add(a, b) {
return a + b
}

print one()
print add(one(), 4)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/zero_arg_calls.nq" >/dev/null
build_generated
assert_eq "zero-arg-calls" "$(run_output "$TMP_DIR/output")" $'1\n5'

write_case "$TMP_DIR/array_argument_mutation.nq" <<'EOF'
func set_mid(a, v) {
a[1] = v
return a[1]
}

var g = [1,2,3]
print set_mid(g, 9)
print g[1]
EOF
"$ROOT_DIR/nql" "$TMP_DIR/array_argument_mutation.nq" >/dev/null
build_generated
assert_eq "array-argument-mutation" "$(run_output "$TMP_DIR/output")" $'9\n9'

write_case "$TMP_DIR/print_multi.nq" <<'EOF'
func bump(x) {
return x + 1
}

var g = [7,8,9]
print 1, bump(2), g[1], "halo"
EOF
"$ROOT_DIR/nql" "$TMP_DIR/print_multi.nq" >/dev/null
build_generated
assert_eq "print-multi" "$(run_output "$TMP_DIR/output")" $'1\n3\n8\nhalo'

write_case "$TMP_DIR/println_basic.nq" <<'EOF'
println
println "halo"
println 1, "dua"
EOF
"$ROOT_DIR/nql" "$TMP_DIR/println_basic.nq" >/dev/null
build_generated
assert_eq "println-basic" "$(run_output "$TMP_DIR/output")" $'\nhalo\n\n1\ndua'

write_case "$TMP_DIR/call_stmt.nq" <<'EOF'
func bump(x) {
print x
return x + 1
}
bump(2)
print 9
EOF
"$ROOT_DIR/nql" "$TMP_DIR/call_stmt.nq" >/dev/null
build_generated
assert_eq "call-stmt" "$(run_output "$TMP_DIR/output")" $'2\n9'

write_case "$TMP_DIR/module_call_stmt.nq" <<'EOF'
module demo {
func ping() {
print 5
return 6
}
}
demo.ping()
print demo.ping()
EOF
"$ROOT_DIR/nql" "$TMP_DIR/module_call_stmt.nq" >/dev/null
build_generated
assert_eq "module-call-stmt" "$(run_output "$TMP_DIR/output")" $'5\n5\n6'

write_case "$TMP_DIR/try_ok.nq" <<'EOF'
try {
error "boom"
} catch {
print 7
}
EOF
"$ROOT_DIR/nql" "$TMP_DIR/try_ok.nq" >/dev/null
build_generated
assert_eq "try-catch" "$(run_output "$TMP_DIR/output")" "boom
7"

write_case "$TMP_DIR/nested_try_ok.nq" <<'EOF'
try {
try {
error "boom"
} catch {
print 7
}
} catch {
print 9
}
EOF
"$ROOT_DIR/nql" "$TMP_DIR/nested_try_ok.nq" >/dev/null
build_generated
assert_eq "nested-try-catch" "$(run_output "$TMP_DIR/output")" "boom
7"

write_case "$TMP_DIR/export_ir.nq" <<'EOF'
func add(a, b) {
return a + b
}
print add(2, 3)
EOF
"$ROOT_DIR/nql" --export-ir "$TMP_DIR/export.ir" "$TMP_DIR/export_ir.nq" >/dev/null
assert_file_contains "export-ir-header" "$TMP_DIR/export.ir" "^== IR ==$"
assert_file_contains "export-ir-call" "$TMP_DIR/export.ir" "CALL"
assert_file_contains "export-ir-name" "$TMP_DIR/export.ir" "NAME=add"

write_case "$TMP_DIR/print_str_var.nq" <<'EOF'
func label() {
return "ok"
}
var s = "hi"
print s
print label()
EOF
"$ROOT_DIR/nql" "$TMP_DIR/print_str_var.nq" >/dev/null
build_generated
assert_eq "print-str-var" "$(run_output "$TMP_DIR/output")" $'hi\nok'

write_case "$TMP_DIR/for_global_arr.nq" <<'EOF'
var nums = [3,1,4]
for n in nums {
print n
}
EOF
"$ROOT_DIR/nql" "$TMP_DIR/for_global_arr.nq" >/dev/null
build_generated
assert_eq "for-global-arr" "$(run_output "$TMP_DIR/output")" $'3\n1\n4'

write_case "$TMP_DIR/str_index.nq" <<'EOF'
var s = "abc"
print s[0]
print s[2]
print len(s)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_index.nq" >/dev/null
build_generated
assert_eq "str-index" "$(run_output "$TMP_DIR/output")" $'97\n99\n3'

write_case "$TMP_DIR/str_param_ann.nq" <<'EOF'
func first(s str) {
return s[0]
}
func slen(s str) {
return len(s)
}
var msg = "hi"
print first(msg)
print slen(msg)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_param_ann.nq" >/dev/null
build_generated
assert_eq "str-param-ann" "$(run_output "$TMP_DIR/output")" $'104\n2'

write_case "$TMP_DIR/str_int_conv.nq" <<'EOF'
var n = 42
var a = str(n)
var b = str(n + 1)
print a
print b
print str(n + 100)
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_int_conv.nq" >/dev/null
build_generated
assert_eq "str-int-conv" "$(run_output "$TMP_DIR/output")" $'42\n43\n142'

write_case "$TMP_DIR/int_from_str.nq" <<'EOF'
var s = "99"
var n = int(s)
print n + 1
var neg = "-7"
print int(neg) + 10
EOF
"$ROOT_DIR/nql" "$TMP_DIR/int_from_str.nq" >/dev/null
build_generated
assert_eq "int-from-str" "$(run_output "$TMP_DIR/output")" $'100\n3'

write_case "$TMP_DIR/str_concat.nq" <<'EOF'
var a = "foo"
var b = "bar"
var c = a + b
print c
var greeting = "Hello, " + "world!"
print greeting
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_concat.nq" >/dev/null
build_generated
assert_eq "str-concat" "$(run_output "$TMP_DIR/output")" $'foobar\nHello, world!'

write_case "$TMP_DIR/str_concat_chain.nq" <<'EOF'
var n = 5
var msg = "count=" + str(n)
print msg
var full = "a" + "b" + "c"
print full
EOF
"$ROOT_DIR/nql" "$TMP_DIR/str_concat_chain.nq" >/dev/null
build_generated
assert_eq "str-concat-chain" "$(run_output "$TMP_DIR/output")" $'count=5\nabc'
