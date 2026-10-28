#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

cleanup_bridge_case() {
    local base="$1"
    rm -f \
        "$TMP_DIR/${base}.ir" \
        "$TMP_DIR/${base}.json" \
        "$TMP_DIR/${base}.ll" \
        "$TMP_DIR/${base}.err" \
        "$TMP_DIR/${base}"
}

compile_nq_ir_dump_parser() {
    local bin="$TMP_DIR/nq_ir_dump_parser_nq"
    if [[ -x "$bin" ]]; then
        return
    fi
    "$ROOT_DIR/nql" "$ROOT_DIR/tools/nq_ir_dump_parser.nq" >/dev/null
    nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_dump_parser_nq.o"
    if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
        x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_dump_parser_nq.o" -o "$bin"
    else
        ld "$TMP_DIR/nq_ir_dump_parser_nq.o" -o "$bin"
    fi
}

dump_ir_json_with_nq_parser() {
    local ir_path="$1"
    local json_path="$2"
    local expected_json="$json_path.py"
    python3 "$ROOT_DIR/tools/nq_ir_dump_parser.py" "$ir_path" "$expected_json" >/dev/null
    compile_nq_ir_dump_parser
    run_output "$TMP_DIR/nq_ir_dump_parser_nq" "$ir_path" "$json_path" >/dev/null
    if ! diff -u "$expected_json" "$json_path"; then
        printf "FAIL %s\n.nq IR dump parser output diverged\n" "$json_path" >&2
        exit 1
    fi
}

assert_nq_ir_dump_parser_parity() {
    local name="$1"
    local ir_path="$2"
    local expected_json="$3"
    local got_json="$TMP_DIR/$name.nq.json"
    compile_nq_ir_dump_parser
    run_output "$TMP_DIR/nq_ir_dump_parser_nq" "$ir_path" "$got_json" >/dev/null
    if ! diff -u "$expected_json" "$got_json"; then
        printf 'FAIL %s\n.nq IR dump parser output diverged\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}


write_case "$TMP_DIR/ir_bridge_bad_header.ir" <<EOF
bad
EOF
compile_nq_ir_dump_parser
if run_output "$TMP_DIR/nq_ir_dump_parser_nq" "$TMP_DIR/ir_bridge_bad_header.ir" > "$TMP_DIR/ir_bridge_bad_header.out"; then
    printf 'FAIL %s
expected .nq IR parser failure
' "ir-bridge-nq-parser-bad-header" >&2
    exit 1
fi
assert_file_contains "ir-bridge-nq-parser-bad-header" "$TMP_DIR/ir_bridge_bad_header.out" "missing IR header"

printf '== IR ==\n0\tCONST A=0 B=0 LN=1 TEXT=a"b\\c\tz\n' > "$TMP_DIR/ir_bridge_escape_text.ir"
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_escape_text.ir" "$TMP_DIR/ir_bridge_escape_text.json"
assert_nq_ir_dump_parser_parity "ir-bridge-nq-parser-escape-text" "$TMP_DIR/ir_bridge_escape_text.ir" "$TMP_DIR/ir_bridge_escape_text.json"



write_case "$TMP_DIR/ir_bridge.nq" <<'EOF'
func add(a, b) {
return a + b
}

print add(2, 3)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge.ir" "$TMP_DIR/ir_bridge.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge.ir" "$TMP_DIR/ir_bridge.json"
assert_nq_ir_dump_parser_parity "ir-bridge-nq-parser-basic" "$TMP_DIR/ir_bridge.ir" "$TMP_DIR/ir_bridge.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge.json" "$TMP_DIR/ir_bridge.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge.ll" -o "$TMP_DIR/ir_bridge"

assert_file_contains "ir-bridge-json-op" "$TMP_DIR/ir_bridge.json" '"op": "FN_BGN"'
assert_file_contains "ir-bridge-json-name" "$TMP_DIR/ir_bridge.json" '"name": "add"'
assert_file_contains "ir-bridge-json-call" "$TMP_DIR/ir_bridge.json" '"op": "CALL"'
assert_file_contains "ir-bridge-llvm-fn" "$TMP_DIR/ir_bridge.ll" '^define i64 @add'
assert_eq "ir-bridge-run" "$("$TMP_DIR/ir_bridge")" "5"
cleanup_bridge_case "ir_bridge"

write_case "$TMP_DIR/ir_bridge_argument_patterns.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_argument_patterns.ir" "$TMP_DIR/ir_bridge_argument_patterns.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_argument_patterns.ir" "$TMP_DIR/ir_bridge_argument_patterns.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_argument_patterns.json" "$TMP_DIR/ir_bridge_argument_patterns.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_argument_patterns.ll" -o "$TMP_DIR/ir_bridge_argument_patterns"

assert_file_contains "ir-bridge-arg-pack-call" "$TMP_DIR/ir_bridge_argument_patterns.ll" 'call i64 @pack'
assert_file_contains "ir-bridge-arg-array-call" "$TMP_DIR/ir_bridge_argument_patterns.ll" 'call i64 @at'
assert_eq "ir-bridge-arg-patterns-run" "$("$TMP_DIR/ir_bridge_argument_patterns")" $'36\n20'
cleanup_bridge_case "ir_bridge_argument_patterns"

write_case "$TMP_DIR/ir_bridge_max_params.nq" <<'EOF'
func sum16(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p) {
return a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p
}

print sum16(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_max_params.ir" "$TMP_DIR/ir_bridge_max_params.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_max_params.ir" "$TMP_DIR/ir_bridge_max_params.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_max_params.json" "$TMP_DIR/ir_bridge_max_params.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_max_params.ll" -o "$TMP_DIR/ir_bridge_max_params"

assert_file_contains "ir-bridge-max-params-call" "$TMP_DIR/ir_bridge_max_params.ll" 'call i64 @sum16'
assert_eq "ir-bridge-max-params-run" "$("$TMP_DIR/ir_bridge_max_params")" "136"
cleanup_bridge_case "ir_bridge_max_params"

write_case "$TMP_DIR/ir_bridge_nested_argument_calls.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_nested_argument_calls.ir" "$TMP_DIR/ir_bridge_nested_argument_calls.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nested_argument_calls.ir" "$TMP_DIR/ir_bridge_nested_argument_calls.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nested_argument_calls.json" "$TMP_DIR/ir_bridge_nested_argument_calls.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nested_argument_calls.ll" -o "$TMP_DIR/ir_bridge_nested_argument_calls"

assert_file_contains "ir-bridge-nested-arg-add-call" "$TMP_DIR/ir_bridge_nested_argument_calls.ll" 'call i64 @add'
assert_file_contains "ir-bridge-nested-arg-inc-call" "$TMP_DIR/ir_bridge_nested_argument_calls.ll" 'call i64 @inc'
assert_file_contains "ir-bridge-nested-arg-at-call" "$TMP_DIR/ir_bridge_nested_argument_calls.ll" 'call i64 @at'
assert_eq "ir-bridge-nested-arg-run" "$("$TMP_DIR/ir_bridge_nested_argument_calls")" "45"
cleanup_bridge_case "ir_bridge_nested_argument_calls"

write_case "$TMP_DIR/ir_bridge_argument_order.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_argument_order.ir" "$TMP_DIR/ir_bridge_argument_order.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_argument_order.ir" "$TMP_DIR/ir_bridge_argument_order.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_argument_order.json" "$TMP_DIR/ir_bridge_argument_order.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_argument_order.ll" -o "$TMP_DIR/ir_bridge_argument_order"

assert_file_contains "ir-bridge-arg-order-step-call" "$TMP_DIR/ir_bridge_argument_order.ll" 'call i64 @step'
assert_file_contains "ir-bridge-arg-order-pack-call" "$TMP_DIR/ir_bridge_argument_order.ll" 'call i64 @pack'
assert_eq "ir-bridge-arg-order-run" "$("$TMP_DIR/ir_bridge_argument_order")" $'6\n123'
cleanup_bridge_case "ir_bridge_argument_order"

write_case "$TMP_DIR/ir_bridge_argument_stress.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_argument_stress.ir" "$TMP_DIR/ir_bridge_argument_stress.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_argument_stress.ir" "$TMP_DIR/ir_bridge_argument_stress.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_argument_stress.json" "$TMP_DIR/ir_bridge_argument_stress.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_argument_stress.ll" -o "$TMP_DIR/ir_bridge_argument_stress"

assert_file_contains "ir-bridge-arg-stress-touch-call" "$TMP_DIR/ir_bridge_argument_stress.ll" 'call i64 @touch'
assert_file_contains "ir-bridge-arg-stress-wrap-call" "$TMP_DIR/ir_bridge_argument_stress.ll" 'call i64 @wrap'
assert_file_contains "ir-bridge-arg-stress-pack-call" "$TMP_DIR/ir_bridge_argument_stress.ll" 'call i64 @pack'
assert_eq "ir-bridge-arg-stress-run" "$("$TMP_DIR/ir_bridge_argument_stress")" $'13\n3\n3'
cleanup_bridge_case "ir_bridge_argument_stress"

write_case "$TMP_DIR/ir_bridge_zero_arg_calls.nq" <<'EOF'
func one() {
return 1
}

func add(a, b) {
return a + b
}

print one()
print add(one(), 4)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_zero_arg_calls.ir" "$TMP_DIR/ir_bridge_zero_arg_calls.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_zero_arg_calls.ir" "$TMP_DIR/ir_bridge_zero_arg_calls.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_zero_arg_calls.json" "$TMP_DIR/ir_bridge_zero_arg_calls.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_zero_arg_calls.ll" -o "$TMP_DIR/ir_bridge_zero_arg_calls"

assert_file_contains "ir-bridge-zero-arg-one-call" "$TMP_DIR/ir_bridge_zero_arg_calls.ll" 'call i64 @one\(\)'
assert_file_contains "ir-bridge-zero-arg-add-call" "$TMP_DIR/ir_bridge_zero_arg_calls.ll" 'call i64 @add'
assert_eq "ir-bridge-zero-arg-run" "$("$TMP_DIR/ir_bridge_zero_arg_calls")" $'1\n5'
cleanup_bridge_case "ir_bridge_zero_arg_calls"

write_case "$TMP_DIR/ir_bridge_array_argument_mutation.nq" <<'EOF'
func set_mid(a, v) {
a[1] = v
return a[1]
}

var g = [1,2,3]
print set_mid(g, 9)
print g[1]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_array_argument_mutation.ir" "$TMP_DIR/ir_bridge_array_argument_mutation.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array_argument_mutation.ir" "$TMP_DIR/ir_bridge_array_argument_mutation.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array_argument_mutation.json" "$TMP_DIR/ir_bridge_array_argument_mutation.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array_argument_mutation.ll" -o "$TMP_DIR/ir_bridge_array_argument_mutation"

assert_file_contains "ir-bridge-array-arg-call" "$TMP_DIR/ir_bridge_array_argument_mutation.ll" 'call i64 @set_mid'
assert_eq "ir-bridge-array-arg-run" "$("$TMP_DIR/ir_bridge_array_argument_mutation")" $'9\n9'
cleanup_bridge_case "ir_bridge_array_argument_mutation"

write_case "$TMP_DIR/ir_bridge_multi_array.nq" <<'EOF'
var a = [1,2]
var b = [7,8]
print a[1]
print b[0]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_multi_array.ir" "$TMP_DIR/ir_bridge_multi_array.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_multi_array.ir" "$TMP_DIR/ir_bridge_multi_array.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_multi_array.json" "$TMP_DIR/ir_bridge_multi_array.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_multi_array.ll" -o "$TMP_DIR/ir_bridge_multi_array"

assert_eq "ir-bridge-multi-array-run" "$("$TMP_DIR/ir_bridge_multi_array")" $'2\n7'
cleanup_bridge_case "ir_bridge_multi_array"

write_case "$TMP_DIR/ir_bridge_array_oob_load.nq" <<'EOF'
var a = [1,2,3]
print a[3]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_array_oob_load.ir" "$TMP_DIR/ir_bridge_array_oob_load.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array_oob_load.ir" "$TMP_DIR/ir_bridge_array_oob_load.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array_oob_load.json" "$TMP_DIR/ir_bridge_array_oob_load.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array_oob_load.ll" -o "$TMP_DIR/ir_bridge_array_oob_load"
if "$TMP_DIR/ir_bridge_array_oob_load" >"$TMP_DIR/ir_bridge_array_oob_load.err" 2>&1; then
    printf 'FAIL %s\nexpected runtime failure\n' "ir-bridge-array-oob-load" >&2
    exit 1
fi
if ! grep -q -- "array index out of bounds" "$TMP_DIR/ir_bridge_array_oob_load.err"; then
    printf 'FAIL %s\nmissing runtime error message\n' "ir-bridge-array-oob-load" >&2
    exit 1
fi
printf 'PASS %s\n' "ir-bridge-array-oob-load"
cleanup_bridge_case "ir_bridge_array_oob_load"

write_case "$TMP_DIR/ir_bridge_array_oob_store.nq" <<'EOF'
var a = [1,2,3]
a[3] = 9
print a[0]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_array_oob_store.ir" "$TMP_DIR/ir_bridge_array_oob_store.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array_oob_store.ir" "$TMP_DIR/ir_bridge_array_oob_store.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array_oob_store.json" "$TMP_DIR/ir_bridge_array_oob_store.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array_oob_store.ll" -o "$TMP_DIR/ir_bridge_array_oob_store"
if "$TMP_DIR/ir_bridge_array_oob_store" >"$TMP_DIR/ir_bridge_array_oob_store.err" 2>&1; then
    printf 'FAIL %s\nexpected runtime failure\n' "ir-bridge-array-oob-store" >&2
    exit 1
fi
if ! grep -q -- "array index out of bounds" "$TMP_DIR/ir_bridge_array_oob_store.err"; then
    printf 'FAIL %s\nmissing runtime error message\n' "ir-bridge-array-oob-store" >&2
    exit 1
fi
printf 'PASS %s\n' "ir-bridge-array-oob-store"
cleanup_bridge_case "ir_bridge_array_oob_store"
write_case "$TMP_DIR/ir_bridge_div_zero.nq" <<'EOF'
print 1 / 0
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_div_zero.ir" "$TMP_DIR/ir_bridge_div_zero.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_div_zero.ir" "$TMP_DIR/ir_bridge_div_zero.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_div_zero.json" "$TMP_DIR/ir_bridge_div_zero.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_div_zero.ll" -o "$TMP_DIR/ir_bridge_div_zero"
if "$TMP_DIR/ir_bridge_div_zero" >"$TMP_DIR/ir_bridge_div_zero.err" 2>&1; then
    echo "FAIL ir-bridge-div-zero" >&2
    exit 1
fi
if ! grep -q -- "division by zero" "$TMP_DIR/ir_bridge_div_zero.err"; then
    echo "FAIL ir-bridge-div-zero" >&2
    exit 1
fi
echo "PASS ir-bridge-div-zero"
cleanup_bridge_case "ir_bridge_div_zero"

write_case "$TMP_DIR/ir_bridge_mod_zero.nq" <<'EOF'
print 1 % 0
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_mod_zero.ir" "$TMP_DIR/ir_bridge_mod_zero.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_mod_zero.ir" "$TMP_DIR/ir_bridge_mod_zero.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_mod_zero.json" "$TMP_DIR/ir_bridge_mod_zero.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_mod_zero.ll" -o "$TMP_DIR/ir_bridge_mod_zero"
if "$TMP_DIR/ir_bridge_mod_zero" >"$TMP_DIR/ir_bridge_mod_zero.err" 2>&1; then
    echo "FAIL ir-bridge-mod-zero" >&2
    exit 1
fi
if ! grep -q -- "division by zero" "$TMP_DIR/ir_bridge_mod_zero.err"; then
    echo "FAIL ir-bridge-mod-zero" >&2
    exit 1
fi
echo "PASS ir-bridge-mod-zero"
cleanup_bridge_case "ir_bridge_mod_zero"

write_case "$TMP_DIR/ir_bridge_add_overflow.nq" <<'EOF'
print 9223372036854775807 + 1
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_add_overflow.ir" "$TMP_DIR/ir_bridge_add_overflow.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_add_overflow.ir" "$TMP_DIR/ir_bridge_add_overflow.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_add_overflow.json" "$TMP_DIR/ir_bridge_add_overflow.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_add_overflow.ll" -o "$TMP_DIR/ir_bridge_add_overflow"
if "$TMP_DIR/ir_bridge_add_overflow" >"$TMP_DIR/ir_bridge_add_overflow.err" 2>&1; then
    echo "FAIL ir-bridge-add-overflow" >&2
    exit 1
fi
if ! grep -q -- "integer overflow" "$TMP_DIR/ir_bridge_add_overflow.err"; then
    echo "FAIL ir-bridge-add-overflow" >&2
    exit 1
fi
echo "PASS ir-bridge-add-overflow"
cleanup_bridge_case "ir_bridge_add_overflow"

write_case "$TMP_DIR/ir_bridge_sub_overflow.nq" <<'EOF'
print 0 - 9223372036854775807 - 2
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_sub_overflow.ir" "$TMP_DIR/ir_bridge_sub_overflow.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_sub_overflow.ir" "$TMP_DIR/ir_bridge_sub_overflow.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_sub_overflow.json" "$TMP_DIR/ir_bridge_sub_overflow.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_sub_overflow.ll" -o "$TMP_DIR/ir_bridge_sub_overflow"
if "$TMP_DIR/ir_bridge_sub_overflow" >"$TMP_DIR/ir_bridge_sub_overflow.err" 2>&1; then
    echo "FAIL ir-bridge-sub-overflow" >&2
    exit 1
fi
if ! grep -q -- "integer overflow" "$TMP_DIR/ir_bridge_sub_overflow.err"; then
    echo "FAIL ir-bridge-sub-overflow" >&2
    exit 1
fi
echo "PASS ir-bridge-sub-overflow"
cleanup_bridge_case "ir_bridge_sub_overflow"

write_case "$TMP_DIR/ir_bridge_mul_overflow.nq" <<'EOF'
print 3037000500 * 3037000500
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_mul_overflow.ir" "$TMP_DIR/ir_bridge_mul_overflow.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_mul_overflow.ir" "$TMP_DIR/ir_bridge_mul_overflow.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_mul_overflow.json" "$TMP_DIR/ir_bridge_mul_overflow.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_mul_overflow.ll" -o "$TMP_DIR/ir_bridge_mul_overflow"
if "$TMP_DIR/ir_bridge_mul_overflow" >"$TMP_DIR/ir_bridge_mul_overflow.err" 2>&1; then
    echo "FAIL ir-bridge-mul-overflow" >&2
    exit 1
fi
if ! grep -q -- "integer overflow" "$TMP_DIR/ir_bridge_mul_overflow.err"; then
    echo "FAIL ir-bridge-mul-overflow" >&2
    exit 1
fi
echo "PASS ir-bridge-mul-overflow"
cleanup_bridge_case "ir_bridge_mul_overflow"

write_case "$TMP_DIR/ir_bridge_print_multi.nq" <<'EOF'
func bump(x) {
return x + 1
}

var g = [7,8,9]
print 1, bump(2), g[1], "hello"
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_print_multi.ir" "$TMP_DIR/ir_bridge_print_multi.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_print_multi.ir" "$TMP_DIR/ir_bridge_print_multi.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_print_multi.json" "$TMP_DIR/ir_bridge_print_multi.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_print_multi.ll" -o "$TMP_DIR/ir_bridge_print_multi"

assert_file_contains "ir-bridge-print-multi-bump-call" "$TMP_DIR/ir_bridge_print_multi.ll" 'call i64 @bump'
assert_file_contains "ir-bridge-print-multi-str" "$TMP_DIR/ir_bridge_print_multi.json" '"op": "PRINT_STR"'
assert_eq "ir-bridge-print-multi-run" "$("$TMP_DIR/ir_bridge_print_multi")" $'1\n3\n8\nhello'
cleanup_bridge_case "ir_bridge_print_multi"

write_case "$TMP_DIR/ir_bridge_call_stmt.nq" <<'EOF'
func bump(x) {
print x
return x + 1
}
bump(2)
print 9
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_call_stmt.ir" "$TMP_DIR/ir_bridge_call_stmt.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_call_stmt.ir" "$TMP_DIR/ir_bridge_call_stmt.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_call_stmt.json" "$TMP_DIR/ir_bridge_call_stmt.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_call_stmt.ll" -o "$TMP_DIR/ir_bridge_call_stmt"

assert_file_contains "ir-bridge-call-stmt-call" "$TMP_DIR/ir_bridge_call_stmt.ll" 'call i64 @bump'
assert_eq "ir-bridge-call-stmt-run" "$("$TMP_DIR/ir_bridge_call_stmt")" $'2\n9'
cleanup_bridge_case "ir_bridge_call_stmt"

write_case "$TMP_DIR/ir_bridge_fact.nq" <<'EOF'
func fact(n) {
if n == 0 {
return 1
}
return n * fact(n - 1)
}

print fact(5)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_fact.ir" "$TMP_DIR/ir_bridge_fact.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_fact.ir" "$TMP_DIR/ir_bridge_fact.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_fact.json" "$TMP_DIR/ir_bridge_fact.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_fact.ll" -o "$TMP_DIR/ir_bridge_fact"

assert_file_contains "ir-bridge-fact-llvm-branch" "$TMP_DIR/ir_bridge_fact.ll" 'br i1'
assert_eq "ir-bridge-fact-run" "$("$TMP_DIR/ir_bridge_fact")" "120"
cleanup_bridge_case "ir_bridge_fact"

write_case "$TMP_DIR/ir_bridge_global.nq" <<'EOF'
var x = 1
x = x + 2
print x
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_global.ir" "$TMP_DIR/ir_bridge_global.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_global.ir" "$TMP_DIR/ir_bridge_global.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_global.json" "$TMP_DIR/ir_bridge_global.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_global.ll" -o "$TMP_DIR/ir_bridge_global"

assert_file_contains "ir-bridge-global-llvm-global" "$TMP_DIR/ir_bridge_global.ll" '^@gslot_0 = global i64 0$'
assert_eq "ir-bridge-global-run" "$("$TMP_DIR/ir_bridge_global")" "3"
cleanup_bridge_case "ir_bridge_global"

write_case "$TMP_DIR/ir_bridge_loop.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_loop.ir" "$TMP_DIR/ir_bridge_loop.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_loop.ir" "$TMP_DIR/ir_bridge_loop.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_loop.json" "$TMP_DIR/ir_bridge_loop.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_loop.ll" -o "$TMP_DIR/ir_bridge_loop"

assert_file_contains "ir-bridge-loop-alloca" "$TMP_DIR/ir_bridge_loop.ll" '%local_8 = alloca i64'
assert_file_contains "ir-bridge-loop-branch" "$TMP_DIR/ir_bridge_loop.ll" 'br i1'
assert_eq "ir-bridge-loop-run" "$("$TMP_DIR/ir_bridge_loop")" "10"
cleanup_bridge_case "ir_bridge_loop"

write_case "$TMP_DIR/ir_bridge_str.nq" <<'EOF'
print "hello"
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str.ir" "$TMP_DIR/ir_bridge_str.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str.ir" "$TMP_DIR/ir_bridge_str.json"
assert_nq_ir_dump_parser_parity "ir-bridge-nq-parser-text" "$TMP_DIR/ir_bridge_str.ir" "$TMP_DIR/ir_bridge_str.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str.json" "$TMP_DIR/ir_bridge_str.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str.ll" -o "$TMP_DIR/ir_bridge_str"

assert_file_contains "ir-bridge-str-ir-text" "$TMP_DIR/ir_bridge_str.ir" 'TEXT=hello'
assert_file_contains "ir-bridge-str-json-text" "$TMP_DIR/ir_bridge_str.json" '"text": "hello"'
assert_file_contains "ir-bridge-str-llvm-global" "$TMP_DIR/ir_bridge_str.ll" '@strlit_0 = private constant'
assert_eq "ir-bridge-str-run" "$("$TMP_DIR/ir_bridge_str")" "hello"
cleanup_bridge_case "ir_bridge_str"

write_case "$TMP_DIR/ir_bridge_str_var.nq" <<'EOF'
func label() {
return "ok"
}
var s = "hi"
print s
print label()
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_var.ir" "$TMP_DIR/ir_bridge_str_var.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_var.ir" "$TMP_DIR/ir_bridge_str_var.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_var.json" "$TMP_DIR/ir_bridge_str_var.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_var.ll" -o "$TMP_DIR/ir_bridge_str_var"

assert_file_contains "ir-bridge-str-var-ir-const-text" "$TMP_DIR/ir_bridge_str_var.ir" 'CONST A=0 B=0 LN=2 TEXT=ok'
assert_file_contains "ir-bridge-str-var-json-op" "$TMP_DIR/ir_bridge_str_var.json" '"op": "PRINT_STR_VAR"'
assert_file_contains "ir-bridge-str-var-llvm-table" "$TMP_DIR/ir_bridge_str_var.ll" '@str_ptrs = private constant'
assert_file_contains "ir-bridge-str-var-llvm-call" "$TMP_DIR/ir_bridge_str_var.ll" 'call void @__nq_print_str_id'
assert_eq "ir-bridge-str-var-run" "$("$TMP_DIR/ir_bridge_str_var")" $'hi\nok'
cleanup_bridge_case "ir_bridge_str_var"

write_case "$TMP_DIR/ir_bridge_str_len.nq" <<'EOF'
func word() {
return "ok"
}
var s = "hi"
print len(s)
print len(word())
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_len.ir" "$TMP_DIR/ir_bridge_str_len.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_len.ir" "$TMP_DIR/ir_bridge_str_len.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_len.json" "$TMP_DIR/ir_bridge_str_len.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_len.ll" -o "$TMP_DIR/ir_bridge_str_len"

assert_file_contains "ir-bridge-str-len-ir-op" "$TMP_DIR/ir_bridge_str_len.ir" 'STR_LEN'
assert_file_contains "ir-bridge-str-len-llvm-table" "$TMP_DIR/ir_bridge_str_len.ll" '@str_lens = private global'
assert_file_contains "ir-bridge-str-len-llvm-call" "$TMP_DIR/ir_bridge_str_len.ll" 'call i64 @__nq_str_len_id'
assert_eq "ir-bridge-str-len-run" "$("$TMP_DIR/ir_bridge_str_len")" $'2\n2'
cleanup_bridge_case "ir_bridge_str_len"

write_case "$TMP_DIR/ir_bridge_int_to_str.nq" <<'EOF'
var label = "n="
var n = 42
var s = str(n)
print label
print s
print len(s)
print str(-7)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_int_to_str.ir" "$TMP_DIR/ir_bridge_int_to_str.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_int_to_str.ir" "$TMP_DIR/ir_bridge_int_to_str.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_int_to_str.json" "$TMP_DIR/ir_bridge_int_to_str.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_int_to_str.ll" -o "$TMP_DIR/ir_bridge_int_to_str"

assert_file_contains "ir-bridge-int-to-str-ir-op" "$TMP_DIR/ir_bridge_int_to_str.ir" 'INT_TO_STR'
assert_file_contains "ir-bridge-int-to-str-llvm-buffer" "$TMP_DIR/ir_bridge_int_to_str.ll" '@nq_its_buf_0'
assert_file_contains "ir-bridge-int-to-str-llvm-call" "$TMP_DIR/ir_bridge_int_to_str.ll" 'call i64 @__nq_int_to_str_slot'
assert_eq "ir-bridge-int-to-str-run" "$("$TMP_DIR/ir_bridge_int_to_str")" $'n=\n42\n2\n-7'
cleanup_bridge_case "ir_bridge_int_to_str"

write_case "$TMP_DIR/ir_bridge_str_to_int.nq" <<EOF
var n = 42
var d = str(n)
print int(d)
var s = "123x"
print int(s)
print int("-7")
print int("abc")
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_to_int.ir" "$TMP_DIR/ir_bridge_str_to_int.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_to_int.ir" "$TMP_DIR/ir_bridge_str_to_int.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_to_int.json" "$TMP_DIR/ir_bridge_str_to_int.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_to_int.ll" -o "$TMP_DIR/ir_bridge_str_to_int"

assert_file_contains "ir-bridge-str-to-int-ir-op" "$TMP_DIR/ir_bridge_str_to_int.ir" "STR_TO_INT"
assert_file_contains "ir-bridge-str-to-int-llvm-call" "$TMP_DIR/ir_bridge_str_to_int.ll" "call i64 @__nq_str_to_int_id"
expected=$(printf "42\n123\n-7\n0")
assert_eq "ir-bridge-str-to-int-run" "$("$TMP_DIR/ir_bridge_str_to_int")" "$expected"
cleanup_bridge_case "ir_bridge_str_to_int"

write_case "$TMP_DIR/ir_bridge_str_concat.nq" <<EOF
var a = "ab"
var b = "cd"
print a + b
print "x=" + str(42)
print len(a + b)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_concat.ir" "$TMP_DIR/ir_bridge_str_concat.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_concat.ir" "$TMP_DIR/ir_bridge_str_concat.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_concat.json" "$TMP_DIR/ir_bridge_str_concat.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_concat.ll" -o "$TMP_DIR/ir_bridge_str_concat"

assert_file_contains "ir-bridge-str-concat-ir-op" "$TMP_DIR/ir_bridge_str_concat.ir" "STR_CONCAT"
assert_file_contains "ir-bridge-str-concat-llvm-buffer" "$TMP_DIR/ir_bridge_str_concat.ll" "@nq_strcat_buf_0"
assert_file_contains "ir-bridge-str-concat-llvm-call" "$TMP_DIR/ir_bridge_str_concat.ll" "call i64 @__nq_str_concat_slot"
assert_eq "ir-bridge-str-concat-run" "$("$TMP_DIR/ir_bridge_str_concat")" $'abcd\nx=42\n4'
cleanup_bridge_case "ir_bridge_str_concat"

write_case "$TMP_DIR/ir_bridge_str_at.nq" <<'EOF'
var s = "abc"
print s[0]
print s[2]
print len(s)
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_at.ir" "$TMP_DIR/ir_bridge_str_at.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_at.ir" "$TMP_DIR/ir_bridge_str_at.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_at.json" "$TMP_DIR/ir_bridge_str_at.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_at.ll" -o "$TMP_DIR/ir_bridge_str_at"

assert_file_contains "ir-bridge-str-at-ir-op" "$TMP_DIR/ir_bridge_str_at.ir" 'STR_AT'
assert_file_contains "ir-bridge-str-at-llvm-call" "$TMP_DIR/ir_bridge_str_at.ll" 'call i64 @__nq_str_at_id'
assert_eq "ir-bridge-str-at-run" "$("$TMP_DIR/ir_bridge_str_at")" $'97\n99\n3'
cleanup_bridge_case "ir_bridge_str_at"

write_case "$TMP_DIR/ir_bridge_str_at_oob.nq" <<'EOF'
var s = "abc"
print s[3]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_at_oob.ir" "$TMP_DIR/ir_bridge_str_at_oob.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_at_oob.ir" "$TMP_DIR/ir_bridge_str_at_oob.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_at_oob.json" "$TMP_DIR/ir_bridge_str_at_oob.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_at_oob.ll" -o "$TMP_DIR/ir_bridge_str_at_oob"
if "$TMP_DIR/ir_bridge_str_at_oob" >"$TMP_DIR/ir_bridge_str_at_oob.err" 2>&1; then
    echo "FAIL ir-bridge-str-at-oob" >&2
    exit 1
fi
if ! grep -q -- "string index out of bounds" "$TMP_DIR/ir_bridge_str_at_oob.err"; then
    echo "FAIL ir-bridge-str-at-oob" >&2
    exit 1
fi
echo "PASS ir-bridge-str-at-oob"
cleanup_bridge_case "ir_bridge_str_at_oob"

write_case "$TMP_DIR/ir_bridge_str_eq.nq" <<'EOF'
func word() {
return "hi"
}
var s = "hi"
if s == "hi" { print 1 } else { print 0 }
if s != "ok" { print 2 } else { print 9 }
if word() == s { print 3 } else { print 8 }
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_str_eq.ir" "$TMP_DIR/ir_bridge_str_eq.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_str_eq.ir" "$TMP_DIR/ir_bridge_str_eq.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_str_eq.json" "$TMP_DIR/ir_bridge_str_eq.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_str_eq.ll" -o "$TMP_DIR/ir_bridge_str_eq"

assert_file_contains "ir-bridge-str-eq-ir-op" "$TMP_DIR/ir_bridge_str_eq.ir" 'STR_EQ'
assert_file_contains "ir-bridge-str-neq-ir-op" "$TMP_DIR/ir_bridge_str_eq.ir" 'STR_NEQ'
assert_file_contains "ir-bridge-str-eq-llvm-strcmp" "$TMP_DIR/ir_bridge_str_eq.ll" 'declare i32 @strcmp'
assert_file_contains "ir-bridge-str-eq-llvm-call" "$TMP_DIR/ir_bridge_str_eq.ll" 'call i64 @__nq_str_eq_id'
assert_eq "ir-bridge-str-eq-run" "$("$TMP_DIR/ir_bridge_str_eq")" $'1\n2\n3'
cleanup_bridge_case "ir_bridge_str_eq"

write_case "$TMP_DIR/ir_bridge_array.nq" <<'EOF'
var a = [1,2,3]
print a[1]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_array.ir" "$TMP_DIR/ir_bridge_array.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array.ir" "$TMP_DIR/ir_bridge_array.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array.json" "$TMP_DIR/ir_bridge_array.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array.ll" -o "$TMP_DIR/ir_bridge_array"

assert_file_contains "ir-bridge-array-ir-op" "$TMP_DIR/ir_bridge_array.ir" 'HEAP_ST'
assert_file_contains "ir-bridge-array-json-op" "$TMP_DIR/ir_bridge_array.json" '"op": "ARR_NEW"'
assert_file_contains "ir-bridge-array-llvm-calloc" "$TMP_DIR/ir_bridge_array.ll" 'declare ptr @calloc'
assert_eq "ir-bridge-array-run" "$("$TMP_DIR/ir_bridge_array")" "2"
cleanup_bridge_case "ir_bridge_array"

write_case "$TMP_DIR/ir_bridge_array_store.nq" <<'EOF'
var a = [1,2,3]
a[1] = 9
print a[1]
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_array_store.ir" "$TMP_DIR/ir_bridge_array_store.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array_store.ir" "$TMP_DIR/ir_bridge_array_store.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array_store.json" "$TMP_DIR/ir_bridge_array_store.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array_store.ll" -o "$TMP_DIR/ir_bridge_array_store"

assert_file_contains "ir-bridge-array-store-ir-op" "$TMP_DIR/ir_bridge_array_store.ir" 'ARR_ST'
assert_file_contains "ir-bridge-array-store-llvm-op" "$TMP_DIR/ir_bridge_array_store.ll" 'store i64 9'
assert_eq "ir-bridge-array-store-run" "$("$TMP_DIR/ir_bridge_array_store")" "9"
cleanup_bridge_case "ir_bridge_array_store"

write_case "$TMP_DIR/ir_bridge_try_catch.nq" <<"EOF"
try {
error "boom"
} catch {
print 7
}
print 2
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_try_catch.ir" "$TMP_DIR/ir_bridge_try_catch.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_try_catch.ir" "$TMP_DIR/ir_bridge_try_catch.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_try_catch.json" "$TMP_DIR/ir_bridge_try_catch.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_try_catch.ll" -o "$TMP_DIR/ir_bridge_try_catch"

assert_file_contains "ir-bridge-try-json-clr" "$TMP_DIR/ir_bridge_try_catch.json" "CLR_EF"
assert_file_contains "ir-bridge-try-json-jmp-tc" "$TMP_DIR/ir_bridge_try_catch.json" "JMP_TC"
assert_file_contains "ir-bridge-try-llvm-catch-branch" "$TMP_DIR/ir_bridge_try_catch.ll" "br label %tc_0"
expected=$(printf "boom\n7\n2")
assert_eq "ir-bridge-try-catch-run" "$("$TMP_DIR/ir_bridge_try_catch")" "$expected"
cleanup_bridge_case "ir_bridge_try_catch"

write_case "$TMP_DIR/ir_bridge_module_call.nq" <<"EOF"
module demo {
func inc(x) {
return x + 1
}
}
print demo.inc(4)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_module_call.ir" "$TMP_DIR/ir_bridge_module_call.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_module_call.ir" "$TMP_DIR/ir_bridge_module_call.json"
assert_nq_ir_dump_parser_parity "ir-bridge-nq-parser-module" "$TMP_DIR/ir_bridge_module_call.ir" "$TMP_DIR/ir_bridge_module_call.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_module_call.json" "$TMP_DIR/ir_bridge_module_call.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_module_call.ll" -o "$TMP_DIR/ir_bridge_module_call"

assert_file_contains "ir-bridge-module-json-begin" "$TMP_DIR/ir_bridge_module_call.json" "MOD_BGN"
assert_file_contains "ir-bridge-module-json-end" "$TMP_DIR/ir_bridge_module_call.json" "MOD_END"
assert_file_contains "ir-bridge-module-llvm-fn" "$TMP_DIR/ir_bridge_module_call.ll" "define i64 @inc"
assert_eq "ir-bridge-module-call-run" "$("$TMP_DIR/ir_bridge_module_call")" "5"
cleanup_bridge_case "ir_bridge_module_call"

write_case "$TMP_DIR/ir_bridge_for.nq" <<'EOF'
for i in 0..3 {
print i
}
EOF

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_for.ir" "$TMP_DIR/ir_bridge_for.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_for.ir" "$TMP_DIR/ir_bridge_for.json"
assert_nq_ir_dump_parser_parity "ir-bridge-nq-parser-for" "$TMP_DIR/ir_bridge_for.ir" "$TMP_DIR/ir_bridge_for.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_for.json" "$TMP_DIR/ir_bridge_for.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_for.ll" -o "$TMP_DIR/ir_bridge_for"

assert_file_contains "ir-bridge-for-ir-op" "$TMP_DIR/ir_bridge_for.ir" 'FE_ST'
assert_file_contains "ir-bridge-for-json-op" "$TMP_DIR/ir_bridge_for.json" '"op": "FE_CMP"'
assert_file_contains "ir-bridge-for-llvm-slot" "$TMP_DIR/ir_bridge_for.ll" '%forend_0 = alloca i64'
assert_eq "ir-bridge-for-run" "$("$TMP_DIR/ir_bridge_for")" $'0\n1\n2'
cleanup_bridge_case "ir_bridge_for"

write_case "$TMP_DIR/ir_bridge_break_continue.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_break_continue.ir" "$TMP_DIR/ir_bridge_break_continue.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_break_continue.ir" "$TMP_DIR/ir_bridge_break_continue.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_break_continue.json" "$TMP_DIR/ir_bridge_break_continue.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_break_continue.ll" -o "$TMP_DIR/ir_bridge_break_continue"

assert_file_contains "ir-bridge-continue-llvm-branch" "$TMP_DIR/ir_bridge_break_continue.ll" 'br label %ws_0'
assert_file_contains "ir-bridge-break-llvm-branch" "$TMP_DIR/ir_bridge_break_continue.ll" 'br label %we_0'
assert_eq "ir-bridge-break-continue-run" "$("$TMP_DIR/ir_bridge_break_continue")" $'1\n3'
cleanup_bridge_case "ir_bridge_break_continue"

write_case "$TMP_DIR/ir_bridge_nested_break_continue.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_nested_break_continue.ir" "$TMP_DIR/ir_bridge_nested_break_continue.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nested_break_continue.ir" "$TMP_DIR/ir_bridge_nested_break_continue.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nested_break_continue.json" "$TMP_DIR/ir_bridge_nested_break_continue.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nested_break_continue.ll" -o "$TMP_DIR/ir_bridge_nested_break_continue"

assert_file_contains "ir-bridge-nested-continue-llvm-branch" "$TMP_DIR/ir_bridge_nested_break_continue.ll" 'br label %ws_[0-9][0-9]*'
assert_file_contains "ir-bridge-nested-break-llvm-branch" "$TMP_DIR/ir_bridge_nested_break_continue.ll" 'br label %we_[0-9][0-9]*'
assert_eq "ir-bridge-nested-break-continue-run" "$("$TMP_DIR/ir_bridge_nested_break_continue")" $'1\n3\n2\n4\n3\n5'
cleanup_bridge_case "ir_bridge_nested_break_continue"

write_case "$TMP_DIR/ir_bridge_nested_for_break_continue.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_nested_for_break_continue.ir" "$TMP_DIR/ir_bridge_nested_for_break_continue.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nested_for_break_continue.ir" "$TMP_DIR/ir_bridge_nested_for_break_continue.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nested_for_break_continue.json" "$TMP_DIR/ir_bridge_nested_for_break_continue.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nested_for_break_continue.ll" -o "$TMP_DIR/ir_bridge_nested_for_break_continue"

assert_file_contains "ir-bridge-nested-for-continue-llvm-branch" "$TMP_DIR/ir_bridge_nested_for_break_continue.ll" 'br label %ws_[0-9][0-9]*'
assert_file_contains "ir-bridge-nested-for-break-llvm-branch" "$TMP_DIR/ir_bridge_nested_for_break_continue.ll" 'br label %we_[0-9][0-9]*'
assert_file_contains "ir-bridge-nested-for-llvm-slot" "$TMP_DIR/ir_bridge_nested_for_break_continue.ll" '%forend_[0-9][0-9]* = alloca i64'
assert_eq "ir-bridge-nested-for-break-continue-run" "$("$TMP_DIR/ir_bridge_nested_for_break_continue")" $'0\n2\n1\n3\n2\n4'
cleanup_bridge_case "ir_bridge_nested_for_break_continue"

write_case "$TMP_DIR/ir_bridge_break_continue_helper.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_break_continue_helper.ir" "$TMP_DIR/ir_bridge_break_continue_helper.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_break_continue_helper.ir" "$TMP_DIR/ir_bridge_break_continue_helper.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_break_continue_helper.json" "$TMP_DIR/ir_bridge_break_continue_helper.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_break_continue_helper.ll" -o "$TMP_DIR/ir_bridge_break_continue_helper"

assert_file_contains "ir-bridge-helper-continue-llvm-branch" "$TMP_DIR/ir_bridge_break_continue_helper.ll" 'br label %ws_[0-9][0-9]*'
assert_file_contains "ir-bridge-helper-break-llvm-branch" "$TMP_DIR/ir_bridge_break_continue_helper.ll" 'br label %we_[0-9][0-9]*'
assert_file_contains "ir-bridge-helper-call" "$TMP_DIR/ir_bridge_break_continue_helper.ll" 'call i64 @bump'
assert_eq "ir-bridge-helper-break-continue-run" "$("$TMP_DIR/ir_bridge_break_continue_helper")" $'1\n6\n10'
cleanup_bridge_case "ir_bridge_break_continue_helper"

write_case "$TMP_DIR/ir_bridge_for_helper_break_continue.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_for_helper_break_continue.ir" "$TMP_DIR/ir_bridge_for_helper_break_continue.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_for_helper_break_continue.ir" "$TMP_DIR/ir_bridge_for_helper_break_continue.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_for_helper_break_continue.json" "$TMP_DIR/ir_bridge_for_helper_break_continue.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_for_helper_break_continue.ll" -o "$TMP_DIR/ir_bridge_for_helper_break_continue"

assert_file_contains "ir-bridge-for-helper-continue-llvm-branch" "$TMP_DIR/ir_bridge_for_helper_break_continue.ll" 'br label %wc_[0-9][0-9]*'
assert_file_contains "ir-bridge-for-helper-break-llvm-branch" "$TMP_DIR/ir_bridge_for_helper_break_continue.ll" 'br label %we_[0-9][0-9]*'
assert_file_contains "ir-bridge-for-helper-call" "$TMP_DIR/ir_bridge_for_helper_break_continue.ll" 'call i64 @bump'
assert_eq "ir-bridge-for-helper-break-continue-run" "$("$TMP_DIR/ir_bridge_for_helper_break_continue")" $'1\n3\n1\n3\n5'
cleanup_bridge_case "ir_bridge_for_helper_break_continue"

write_case "$TMP_DIR/ir_bridge_for_recursive_break_continue.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_for_recursive_break_continue.ir" "$TMP_DIR/ir_bridge_for_recursive_break_continue.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_for_recursive_break_continue.ir" "$TMP_DIR/ir_bridge_for_recursive_break_continue.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_for_recursive_break_continue.json" "$TMP_DIR/ir_bridge_for_recursive_break_continue.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_for_recursive_break_continue.ll" -o "$TMP_DIR/ir_bridge_for_recursive_break_continue"

assert_file_contains "ir-bridge-for-recursive-continue-llvm-branch" "$TMP_DIR/ir_bridge_for_recursive_break_continue.ll" 'br label %wc_[0-9][0-9]*'
assert_file_contains "ir-bridge-for-recursive-break-llvm-branch" "$TMP_DIR/ir_bridge_for_recursive_break_continue.ll" 'br label %we_[0-9][0-9]*'
assert_file_contains "ir-bridge-for-recursive-call" "$TMP_DIR/ir_bridge_for_recursive_break_continue.ll" 'call i64 @climb'
assert_eq "ir-bridge-for-recursive-break-continue-run" "$("$TMP_DIR/ir_bridge_for_recursive_break_continue")" $'2\n4\n6\n3'
cleanup_bridge_case "ir_bridge_for_recursive_break_continue"

write_case "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.nq" <<'EOF'
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

"$ROOT_DIR/nql" --export-ir "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ir" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ir" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.json" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ll" -o "$TMP_DIR/ir_bridge_for_recursive_array_break_continue"

assert_file_contains "ir-bridge-for-recursive-array-continue-llvm-branch" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ll" 'br label %wc_[0-9][0-9]*'
assert_file_contains "ir-bridge-for-recursive-array-break-llvm-branch" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ll" 'br label %we_[0-9][0-9]*'
assert_file_contains "ir-bridge-for-recursive-array-call" "$TMP_DIR/ir_bridge_for_recursive_array_break_continue.ll" 'call i64 @touch'
assert_eq "ir-bridge-for-recursive-array-break-continue-run" "$("$TMP_DIR/ir_bridge_for_recursive_array_break_continue")" $'2\n4\n6\n3'
cleanup_bridge_case "ir_bridge_for_recursive_array_break_continue"

write_case "$TMP_DIR/ir_bridge_array_push_pop.nq" <<EOF
var a = int[]
push(a, 10)
push(a, 20)
print len(a)
print a[1]
print pop(a)
print len(a)

var s = str[]
push(s, "hello")
push(s, "world")
print len(s)
print pop(s)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_array_push_pop.ir" "$TMP_DIR/ir_bridge_array_push_pop.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array_push_pop.ir" "$TMP_DIR/ir_bridge_array_push_pop.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array_push_pop.json" "$TMP_DIR/ir_bridge_array_push_pop.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array_push_pop.ll" -o "$TMP_DIR/ir_bridge_array_push_pop"

assert_file_contains "ir-bridge-array-push-json" "$TMP_DIR/ir_bridge_array_push_pop.json" "\"op\": \"ARR_PUSH\""
assert_file_contains "ir-bridge-array-pop-json" "$TMP_DIR/ir_bridge_array_push_pop.json" "\"op\": \"ARR_POP\""
assert_file_contains "ir-bridge-array-push-helper" "$TMP_DIR/ir_bridge_array_push_pop.ll" "call i64 @__nq_arr_push_i64"
assert_file_contains "ir-bridge-array-pop-helper" "$TMP_DIR/ir_bridge_array_push_pop.ll" "call i64 @__nq_arr_pop_i64"
expected=$(printf "2\n20\n20\n1\n2\nworld")
assert_eq "ir-bridge-array-push-pop-run" "$("$TMP_DIR/ir_bridge_array_push_pop")" "$expected"
cleanup_bridge_case "ir_bridge_array_push_pop"

write_case "$TMP_DIR/ir_bridge_array_pop_empty.nq" <<EOF
var a = int[]
print pop(a)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_array_pop_empty.ir" "$TMP_DIR/ir_bridge_array_pop_empty.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_array_pop_empty.ir" "$TMP_DIR/ir_bridge_array_pop_empty.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_array_pop_empty.json" "$TMP_DIR/ir_bridge_array_pop_empty.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_array_pop_empty.ll" -o "$TMP_DIR/ir_bridge_array_pop_empty"
if "$TMP_DIR/ir_bridge_array_pop_empty" >"$TMP_DIR/ir_bridge_array_pop_empty.err" 2>&1; then
    printf "FAIL %s\nexpected runtime failure\n" "ir-bridge-array-pop-empty" >&2
    exit 1
fi
if ! grep -q -- "array pop: array is empty" "$TMP_DIR/ir_bridge_array_pop_empty.err"; then
    printf "FAIL %s\nmissing runtime error message\n" "ir-bridge-array-pop-empty" >&2
    exit 1
fi
printf "PASS %s\n" "ir-bridge-array-pop-empty"
cleanup_bridge_case "ir_bridge_array_pop_empty"

write_case "$TMP_DIR/ir_bridge_argc_arg.nq" <<EOF
func first() {
return argc + arg(0)
}

print argc
print first()
print arg(1)
print arg(2)
print arg(-1)
print arg(-2)
print arg(3)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_argc_arg.ir" "$TMP_DIR/ir_bridge_argc_arg.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_argc_arg.ir" "$TMP_DIR/ir_bridge_argc_arg.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_argc_arg.json" "$TMP_DIR/ir_bridge_argc_arg.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_argc_arg.ll" -o "$TMP_DIR/ir_bridge_argc_arg"

assert_file_contains "ir-bridge-argc-json" "$TMP_DIR/ir_bridge_argc_arg.json" "\"op\": \"ARGC\""
assert_file_contains "ir-bridge-arg-json" "$TMP_DIR/ir_bridge_argc_arg.json" "\"op\": \"ARG\""
assert_file_contains "ir-bridge-argc-main-signature" "$TMP_DIR/ir_bridge_argc_arg.ll" "define i32 @main(i32 %argc32, ptr %argv)"
assert_file_contains "ir-bridge-arg-helper" "$TMP_DIR/ir_bridge_argc_arg.ll" "call i64 @__nq_arg"
expected=$(printf "3\n10\n-3\n123\n0\n0\n0")
assert_eq "ir-bridge-argc-arg-run" "$("$TMP_DIR/ir_bridge_argc_arg" 7 -3 123x)" "$expected"
expected_empty=$(printf "0\n0\n0\n0\n0\n0\n0")
assert_eq "ir-bridge-argc-arg-empty-run" "$("$TMP_DIR/ir_bridge_argc_arg")" "$expected_empty"
cleanup_bridge_case "ir_bridge_argc_arg"

write_case "$TMP_DIR/ir_bridge_input_str.nq" <<EOF
var name = input_str()
print name
print len(name)
print name[1]
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_input_str.ir" "$TMP_DIR/ir_bridge_input_str.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_input_str.ir" "$TMP_DIR/ir_bridge_input_str.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_input_str.json" "$TMP_DIR/ir_bridge_input_str.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_input_str.ll" -o "$TMP_DIR/ir_bridge_input_str"

assert_file_contains "ir-bridge-input-str-json" "$TMP_DIR/ir_bridge_input_str.json" "INPUT_STR"
assert_file_contains "ir-bridge-input-str-helper" "$TMP_DIR/ir_bridge_input_str.ll" "call i64 @__nq_input_str_slot"
expected=$(printf "Alice\n5\n108")
assert_eq "ir-bridge-input-str-run" "$(printf "Alice\n" | "$TMP_DIR/ir_bridge_input_str")" "$expected"
cleanup_bridge_case "ir_bridge_input_str"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.nq" <<EOF
print 2 + 3
print 9 * 4
print 8 - 1
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.nq" <<EOF
print 42
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.py.ll" >/dev/null
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.nq.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_hello.nq.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-hello-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-hello-parity\n'

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.json" <<EOF
[]
EOF
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.py.ll" >/dev/null
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-empty-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-empty-parity\n'
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_empty"
assert_eq "ir-bridge-nq-json-to-llvm-empty-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_empty")" ""
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_empty"

run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-linear-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-linear-parity\n'
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear"
assert_file_contains "ir-bridge-nq-json-to-llvm-header" "$TMP_DIR/ir_bridge_nq_json_to_llvm_linear.ll" "Nolqu IR to LLVM IR bridge"
expected=$(printf "5\n36\n7")
assert_eq "ir-bridge-nq-json-to-llvm-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_linear")" "$expected"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_linear"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.nq" <<EOF
var x = 10
print x
x = x + 5
print x
var y = 7
print x + y
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals"
assert_file_contains "ir-bridge-nq-json-to-llvm-global-slot" "$TMP_DIR/ir_bridge_nq_json_to_llvm_globals.ll" "@gslot_8 = global i64 0"
expected=$(printf "10\n15\n22")
assert_eq "ir-bridge-nq-json-to-llvm-globals-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_globals")" "$expected"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_globals"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.nq" <<EOF
print argc
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc"
assert_file_contains "ir-bridge-nq-json-to-llvm-argc-lower" "$TMP_DIR/ir_bridge_nq_json_to_llvm_argc.ll" "sext i32 %argc32 to i64"
assert_eq "ir-bridge-nq-json-to-llvm-argc-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_argc" a b c)" "3"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_argc"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.nq" <<EOF
print argc
print arg(0)
print arg(1)
print arg(2)
print arg(-1)
print arg(3)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg"
assert_file_contains "ir-bridge-nq-json-to-llvm-arg-helper" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arg.ll" "call i64 @__nq_arg"
expected=$(printf "3\n7\n-3\n123\n0\n0")
assert_eq "ir-bridge-nq-json-to-llvm-arg-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_arg" 7 -3 123x)" "$expected"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_arg"


write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.nq" <<EOF
if 2 > 3 {
print 1
} else {
print 2
}
print 9
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else"
assert_file_contains "ir-bridge-nq-json-to-llvm-if-branch" "$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else.ll" "br i1"
expected=$(printf "2\n9")
assert_eq "ir-bridge-nq-json-to-llvm-if-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_if_else")" "$expected"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_if_else"


write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.nq" <<EOF
func add(a, b) {
return a + b
}
print add(2, 3)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-func-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-func-parity\n'
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_func"
assert_file_contains "ir-bridge-nq-json-to-llvm-func-define" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ll" "define i64 @add(i64 %arg0, i64 %arg1)"
assert_file_contains "ir-bridge-nq-json-to-llvm-func-call" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ll" "call i64 @add(i64 2, i64 3)"
if grep -q '^  %t1 = call i64 @add' "$TMP_DIR/ir_bridge_nq_json_to_llvm_func.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-global-temp-ids\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-global-temp-ids\n'
assert_eq "ir-bridge-nq-json-to-llvm-func-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_func")" "5"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_func"


write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.nq" <<EOF
func fact(n) {
if n == 0 {
return 1
}
return n * fact(n - 1)
}
print fact(5)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.json"
python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.py.ll" >/dev/null
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-recursive-func-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-recursive-func-parity\n'
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func"
assert_eq "ir-bridge-nq-json-to-llvm-recursive-func-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_recursive_func")" "120"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_recursive_func"


write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.nq" <<EOF
func inc(a) {
var x = a + 1
return x
}
print inc(4)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local"
assert_file_contains "ir-bridge-nq-json-to-llvm-func-local-alloca" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.ll" "%local_8 = alloca i64"
assert_file_contains "ir-bridge-nq-json-to-llvm-func-local-load" "$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local.ll" "load i64, ptr %local_8"
assert_eq "ir-bridge-nq-json-to-llvm-func-local-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_func_local")" "5"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_func_local"


write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.nq" <<EOF
func bump(a) {
a = a + 1
return a
}
print bump(4)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p"
assert_file_contains "ir-bridge-nq-json-to-llvm-store-p-alloca" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ll" "%param_16 = alloca i64"
assert_file_contains "ir-bridge-nq-json-to-llvm-store-p-init" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ll" "store i64 %arg0, ptr %param_16"
assert_file_contains "ir-bridge-nq-json-to-llvm-store-p-load" "$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p.ll" "load i64, ptr %param_16"
store_p_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_store_p")
assert_eq "ir-bridge-nq-json-to-llvm-store-p-run" "$store_p_out" "5"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_store_p"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl.json" <<EOF
[
  {
    "index": 0,
    "op": "PRINT_NL",
    "a": 0,
    "b": 0,
    "line": 1
  }
]
EOF

$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl"
assert_file_contains "ir-bridge-nq-json-to-llvm-print-nl-global" "$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl.ll" "@.nl = private constant"
print_nl_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_print_nl")
assert_eq "ir-bridge-nq-json-to-llvm-print-nl-run" "$print_nl_out" ""
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_print_nl"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.nq" <<EOF
print 12 & 10
print 12 | 3
print 12 ^ 10
print ~0
print abs(0 - 7)
print min(3, 5)
print max(3, 5)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops"
expected_int_ops=$(printf "8\n15\n6\n-1\n7\n3\n5")
int_ops_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops")
assert_file_contains "ir-bridge-nq-json-to-llvm-int-ops-and" "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.ll" " = and i64 "
assert_file_contains "ir-bridge-nq-json-to-llvm-int-ops-select" "$TMP_DIR/ir_bridge_nq_json_to_llvm_int_ops.ll" " = select i1 "
assert_eq "ir-bridge-nq-json-to-llvm-int-ops-run" "$int_ops_out" "$expected_int_ops"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_int_ops"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "LNOT",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "PRINT_INT",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 3,
    "op": "CONST",
    "a": 1,
    "b": 0,
    "line": 2
  },
  {
    "index": 4,
    "op": "LNOT",
    "a": 0,
    "b": 0,
    "line": 2
  },
  {
    "index": 5,
    "op": "PRINT_INT",
    "a": 0,
    "b": 0,
    "line": 2
  }
]
EOF

$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot"
expected_lnot=$(printf "1\n0")
lnot_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot")
assert_file_contains "ir-bridge-nq-json-to-llvm-lnot-zext" "$TMP_DIR/ir_bridge_nq_json_to_llvm_lnot.ll" " = zext i1 "
assert_eq "ir-bridge-nq-json-to-llvm-lnot-run" "$lnot_out" "$expected_lnot"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_lnot"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.nq" <<EOF
print 1 << 3
print 16 >> 2
print 1 << 70
print 64 >> 70
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift"
expected_shift=$(printf "8\n4\n64\n1")
shift_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_shift")
assert_file_contains "ir-bridge-nq-json-to-llvm-shift-mask" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ll" " = and i64 "
assert_file_contains "ir-bridge-nq-json-to-llvm-shift-shl" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ll" " = shl i64 "
assert_file_contains "ir-bridge-nq-json-to-llvm-shift-shr" "$TMP_DIR/ir_bridge_nq_json_to_llvm_shift.ll" " = ashr i64 "
assert_eq "ir-bridge-nq-json-to-llvm-shift-run" "$shift_out" "$expected_shift"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_shift"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 1,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "CONST",
    "a": 2,
    "b": 0,
    "line": 1
  },
  {
    "index": 3,
    "op": "POP_RBX",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 4,
    "op": "BOOL_CMP",
    "a": 12,
    "b": 0,
    "line": 1
  },
  {
    "index": 5,
    "op": "PRINT_INT",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 6,
    "op": "CONST",
    "a": 2,
    "b": 0,
    "line": 2
  },
  {
    "index": 7,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 2
  },
  {
    "index": 8,
    "op": "CONST",
    "a": 1,
    "b": 0,
    "line": 2
  },
  {
    "index": 9,
    "op": "POP_RBX",
    "a": 0,
    "b": 0,
    "line": 2
  },
  {
    "index": 10,
    "op": "BOOL_CMP",
    "a": 12,
    "b": 0,
    "line": 2
  },
  {
    "index": 11,
    "op": "PRINT_INT",
    "a": 0,
    "b": 0,
    "line": 2
  }
]
EOF

$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp"
expected_bool_cmp=$(printf "1\n0")
bool_cmp_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp")
assert_file_contains "ir-bridge-nq-json-to-llvm-bool-cmp-zext" "$TMP_DIR/ir_bridge_nq_json_to_llvm_bool_cmp.ll" " = zext i1 "
assert_eq "ir-bridge-nq-json-to-llvm-bool-cmp-run" "$bool_cmp_out" "$expected_bool_cmp"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_bool_cmp"

python3 - "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.json" <<'PY'
import json, sys
ops = [
    ("CONST", 7, 0, 1),
    ("PUSH", 0, 0, 1),
    ("CONST", 99, 0, 1),
    ("POP_RAX", 0, 0, 1),
    ("PRINT_INT", 0, 0, 1),
    ("CONST", 4, 0, 2),
    ("MOV_RBX", 0, 0, 2),
    ("CONST", 6, 0, 2),
    ("MOV_RCX", 0, 0, 2),
    ("ADD", 0, 0, 2),
    ("PRINT_INT", 0, 0, 2),
    ("CONST", 41, 0, 3),
    ("INC_RAX", 0, 0, 3),
    ("PRINT_INT", 0, 0, 3),
]
data = []
for i, (op, av, bv, line) in enumerate(ops):
    data.append({"index": i, "op": op, "a": av, "b": bv, "line": line})
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-stack-moves-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-stack-moves-parity\n'
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves"
expected_stack_moves=$(printf "7\n10\n42")
stack_moves_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves")
assert_file_contains "ir-bridge-nq-json-to-llvm-stack-moves-add" "$TMP_DIR/ir_bridge_nq_json_to_llvm_stack_moves.ll" " = add i64 "
assert_eq "ir-bridge-nq-json-to-llvm-stack-moves-run" "$stack_moves_out" "$expected_stack_moves"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_stack_moves"

python3 - "$TMP_DIR/ir_bridge_nq_json_to_llvm_large.json" <<'PY'
import json, sys
data = []
for i in range(180):
    data.append({"index": len(data), "op": "CONST", "a": i, "b": 0, "line": i + 1})
    data.append({"index": len(data), "op": "PRINT_INT", "a": 0, "b": 0, "line": i + 1})
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_large.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_large.ll" >/dev/null
assert_file_contains "ir-bridge-nq-json-to-llvm-large-last" "$TMP_DIR/ir_bridge_nq_json_to_llvm_large.ll" "i64 179"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_large"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 100,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "CONST",
    "a": 55,
    "b": 0,
    "line": 1
  },
  {
    "index": 3,
    "op": "HEAP_ST",
    "a": 16,
    "b": 0,
    "line": 1
  }
]
EOF

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-heap-st-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-heap-st-parity\n'
assert_file_contains "ir-bridge-nq-json-to-llvm-heap-st-add" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.ll" " = add i64 100, 16"
assert_file_contains "ir-bridge-nq-json-to-llvm-heap-st-store" "$TMP_DIR/ir_bridge_nq_json_to_llvm_heap_st.ll" "store i64 55, ptr "
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_heap_st"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 40,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "ARR_LEN",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "PRINT_INT",
    "a": 0,
    "b": 0,
    "line": 1
  }
]
EOF

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-arr-len-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-arr-len-parity\n'
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-len-load" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_len.ll" " = load i64, ptr "
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_arr_len"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 100,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "CONST",
    "a": 2,
    "b": 0,
    "line": 1
  },
  {
    "index": 3,
    "op": "ARR_LD",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 4,
    "op": "PRINT_INT",
    "a": 0,
    "b": 0,
    "line": 1
  }
]
EOF

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-arr-ld-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-arr-ld-parity\n'
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-ld-bounds" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.ll" "call void @__nq_check_arr_bounds"
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-ld-load" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_ld.ll" " = load i64, ptr "
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_arr_ld"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 100,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "CONST",
    "a": 2,
    "b": 0,
    "line": 1
  },
  {
    "index": 3,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 4,
    "op": "CONST",
    "a": 77,
    "b": 0,
    "line": 1
  },
  {
    "index": 5,
    "op": "ARR_ST",
    "a": 0,
    "b": 0,
    "line": 1
  }
]
EOF

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-arr-st-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-arr-st-parity\n'
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-st-bounds" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.ll" "call void @__nq_check_arr_bounds"
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-st-store" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_st.ll" "store i64 77, ptr "
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_arr_st"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 100,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  },
  {
    "index": 2,
    "op": "CONST",
    "a": 77,
    "b": 0,
    "line": 1
  },
  {
    "index": 3,
    "op": "ARR_PUSH",
    "a": 0,
    "b": 0,
    "line": 1
  }
]
EOF

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-arr-push-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-arr-push-parity\n'
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-push-call" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_push.ll" "call i64 @__nq_arr_push_i64"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_arr_push"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.json" <<EOF
[
  {
    "index": 0,
    "op": "CONST",
    "a": 100,
    "b": 0,
    "line": 1
  },
  {
    "index": 1,
    "op": "ARR_POP",
    "a": 0,
    "b": 0,
    "line": 1
  }
]
EOF

python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.py.ll" >/dev/null
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.ll" >/dev/null
if ! diff -u "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.py.ll" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.ll"; then
    printf 'FAIL ir-bridge-nq-json-to-llvm-arr-pop-parity\n' >&2
    exit 1
fi
printf 'PASS ir-bridge-nq-json-to-llvm-arr-pop-parity\n'
assert_file_contains "ir-bridge-nq-json-to-llvm-arr-pop-call" "$TMP_DIR/ir_bridge_nq_json_to_llvm_arr_pop.ll" "call i64 @__nq_arr_pop_i64"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_arr_pop"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.nq" <<'EOF'
for i in 0..3 {
print i
}
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_for"
expected_for=$(printf "0\n1\n2")
for_out=$("$TMP_DIR/ir_bridge_nq_json_to_llvm_for")
assert_file_contains "ir-bridge-nq-json-to-llvm-for-slot" "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.ll" "%forend_0 = alloca i64"
assert_file_contains "ir-bridge-nq-json-to-llvm-for-cmp" "$TMP_DIR/ir_bridge_nq_json_to_llvm_for.ll" " = icmp sge i64 "
assert_eq "ir-bridge-nq-json-to-llvm-for-run" "$for_out" "$expected_for"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_for"

write_case "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.nq" <<'EOF'
module demo {
func inc(x) {
return x + 1
}
}
print demo.inc(4)
EOF

$ROOT_DIR/nql --export-ir "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.nq" >/dev/null
dump_ir_json_with_nq_parser "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.ir" "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.json"
$ROOT_DIR/nql "$ROOT_DIR/tools/nq_ir_json_to_llvm.nq" >/dev/null
nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/nq_ir_json_to_llvm_nq.o"
if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
    x86_64-linux-gnu-ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
else
    ld "$TMP_DIR/nq_ir_json_to_llvm_nq.o" -o "$TMP_DIR/nq_ir_json_to_llvm_nq"
fi
run_output "$TMP_DIR/nq_ir_json_to_llvm_nq" "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.json" "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.ll" >/dev/null
clang -Wno-override-module "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.ll" -o "$TMP_DIR/ir_bridge_nq_json_to_llvm_module"
assert_file_contains "ir-bridge-nq-json-to-llvm-module-fn" "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.ll" "define i64 @inc"
assert_file_contains "ir-bridge-nq-json-to-llvm-module-call" "$TMP_DIR/ir_bridge_nq_json_to_llvm_module.ll" "call i64 @inc"
assert_eq "ir-bridge-nq-json-to-llvm-module-run" "$("$TMP_DIR/ir_bridge_nq_json_to_llvm_module")" "5"
cleanup_bridge_case "ir_bridge_nq_json_to_llvm_module"
