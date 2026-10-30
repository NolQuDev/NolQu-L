#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
if [[ -n "${TMP_DIR:-}" ]]; then
    NQ_TMP_OWNED=0
else
    TMP_DIR="$(mktemp -d)"
    NQ_TMP_OWNED=1
fi

cleanup_tmp_dir() {
    if [[ "${NQ_TMP_OWNED:-0}" == "1" && -n "${TMP_DIR:-}" && -d "${TMP_DIR}" ]]; then
        rm -rf "${TMP_DIR}"
    fi
}

trap cleanup_tmp_dir EXIT

# Consume each inspector report before searching it. Under pipefail, grep -q
# can close a live LLVM readelf pipe early and invert positive/negative gates.
read_elf_reports() {
    elf_header="$(LC_ALL=C readelf -h "$1")" || {
        printf 'FAIL elf-header-inspection (%s)\n' "$1" >&2
        return 1
    }
    elf_program_headers="$(LC_ALL=C readelf -lW "$1")" || {
        printf 'FAIL elf-program-inspection (%s)\n' "$1" >&2
        return 1
    }
}

run_output() {
    local exe="$1"
    shift
    if [[ "$(uname -m)" == "x86_64" ]]; then
        "$exe" "$@"
    else
        qemu-x86_64 "$exe" "$@"
    fi
}

run_with_invalid_standard_fd() {
    local number="$1"
    shift
    # Native Android startup can refill missing standard FDs. Wrong access
    # modes preserve the same guest EBADF oracle through that startup.
    if [[ "$BASH" == /data/data/com.termux/files/usr/bin/* ]]; then
        case "$number" in
            0) "$@" 0>/dev/null ;;
            1) "$@" 1</dev/null ;;
            2) "$@" 2</dev/null ;;
            *) return 64 ;;
        esac
    else
        case "$number" in
            0) "$@" 0<&- ;;
            1) "$@" 1>&- ;;
            2) "$@" 2>&- ;;
            *) return 64 ;;
        esac
    fi
}

build_generated() {
    local asm="$ROOT_DIR/build/output.asm"
    for _ in $(seq 1 20); do
        if [[ -f "$asm" ]]; then
            break
        fi
        sleep 0.05
    done
    nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$TMP_DIR/output.o"
    if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then
        x86_64-linux-gnu-ld "$TMP_DIR/output.o" -o "$TMP_DIR/output"
    else
        ld "$TMP_DIR/output.o" -o "$TMP_DIR/output"
    fi
}

compile_shared_nq_ir_dump_parser() {
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
    compile_shared_nq_ir_dump_parser
    run_output "$TMP_DIR/nq_ir_dump_parser_nq" "$ir_path" "$json_path" >/dev/null
    if ! diff -u "$expected_json" "$json_path"; then
        printf "FAIL %s\n.nq IR dump parser output diverged\n" "$json_path" >&2
        exit 1
    fi
}


build_ir_bridge_generated() {
    local src="$1"
    local ir="$TMP_DIR/bridge.ir"
    local json="$TMP_DIR/bridge.json"
    local ll="$TMP_DIR/bridge.ll"
    local bin="$TMP_DIR/bridge"

    "$ROOT_DIR/nql" --export-ir "$ir" "$src" >/dev/null
    dump_ir_json_with_nq_parser "$ir" "$json"
    python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$json" "$ll" >/dev/null
    clang -Wno-override-module "$ll" -o "$bin"
}

assert_backend_parity() {
    local name="$1"
    local src="$2"

    "$ROOT_DIR/nql" "$src" >/dev/null
    build_generated
    local nasm_out
    nasm_out="$(run_output "$TMP_DIR/output")"

    build_ir_bridge_generated "$src"
    local llvm_out
    llvm_out="$("$TMP_DIR/bridge")"

    if [[ "$nasm_out" != "$llvm_out" ]]; then
        printf 'FAIL %s\nnasm:\n%s\nllvm-bridge:\n%s\n' "$name" "$nasm_out" "$llvm_out" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_frontend_export_ir_fail_parity() {
    local name="$1"
    local src="$2"
    local pattern="$3"
    local direct_err="$TMP_DIR/${name}.direct.err"
    local export_err="$TMP_DIR/${name}.export.err"
    local export_ir="$TMP_DIR/${name}.ir"

    if "$ROOT_DIR/nql" "$src" >"$direct_err" 2>&1; then
        printf 'FAIL %s\nexpected direct compiler failure\n' "$name" >&2
        exit 1
    fi
    if "$ROOT_DIR/nql" --export-ir "$export_ir" "$src" >"$export_err" 2>&1; then
        printf 'FAIL %s\nexpected export-ir compiler failure\n' "$name" >&2
        exit 1
    fi
    if [[ -n "$pattern" ]] && ! grep -q -- "$pattern" "$direct_err"; then
        printf 'FAIL %s\nmissing direct error message\n' "$name" >&2
        exit 1
    fi
    if [[ -n "$pattern" ]] && ! grep -q -- "$pattern" "$export_err"; then
        printf 'FAIL %s\nmissing export-ir error message\n' "$name" >&2
        exit 1
    fi
    if ! cmp -s "$direct_err" "$export_err"; then
        printf 'FAIL %s\ndirect output:\n%s\nexport-ir output:\n%s\n' \
            "$name" \
            "$(cat "$direct_err")" \
            "$(cat "$export_err")" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_ir_bridge_fail() {
    local name="$1"
    local src="$2"
    local pattern="$3"
    local ir="$TMP_DIR/${name}.ir"
    local json="$TMP_DIR/${name}.json"
    local ll="$TMP_DIR/${name}.ll"
    local err="$TMP_DIR/${name}.err"

    "$ROOT_DIR/nql" --export-ir "$ir" "$src" >/dev/null
    dump_ir_json_with_nq_parser "$ir" "$json"
    if python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$json" "$ll" >/dev/null 2>"$err"; then
        printf 'FAIL %s\nexpected IR bridge failure\n' "$name" >&2
        exit 1
    fi
    if [[ -n "$pattern" ]] && ! grep -q -- "$pattern" "$err"; then
        printf 'FAIL %s\nmissing bridge error message\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_ir_json_to_llvm_fail() {
    local name="$1"
    local json_path="$2"
    local pattern="$3"
    local ll="$TMP_DIR/${name}.ll"
    local err="$TMP_DIR/${name}.err"

    if python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$json_path" "$ll" >/dev/null 2>"$err"; then
        printf 'FAIL %s\nexpected direct IR-to-LLVM failure\n' "$name" >&2
        exit 1
    fi
    if [[ -n "$pattern" ]] && ! grep -q -- "$pattern" "$err"; then
        printf 'FAIL %s\nmissing direct translator error message\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_eq() {
    local name="$1"
    local got="$2"
    local want="$3"
    if [[ "$got" != "$want" ]]; then
        printf 'FAIL %s\nexpected:\n%s\ngot:\n%s\n' "$name" "$want" "$got" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_file_contains() {
    local name="$1"
    local path="$2"
    local pattern="$3"
    if ! grep -q -- "$pattern" "$path"; then
        printf 'FAIL %s\nmissing pattern: %s\nin file: %s\n' "$name" "$pattern" "$path" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_compile_fail() {
    local name="$1"
    local file="$2"
    local pattern="$3"
    local err_file="$TMP_DIR/${name}.err"
    if "$ROOT_DIR/nql" "$file" >"$err_file" 2>&1; then
        printf 'FAIL %s\nexpected compiler failure\n' "$name" >&2
        exit 1
    fi
    if [[ -n "$pattern" ]] && ! grep -q -- "$pattern" "$err_file"; then
        printf 'FAIL %s\nmissing error message\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

assert_runtime_fail() {
    local name="$1"
    local exe="$2"
    local pattern="$3"
    local err_file="$TMP_DIR/${name}.runtime.err"
    if run_output "$exe" >"$err_file" 2>&1; then
        printf 'FAIL %s\nexpected runtime failure\n' "$name" >&2
        exit 1
    fi
    if [[ -n "$pattern" ]] && ! grep -q -- "$pattern" "$err_file"; then
        printf 'FAIL %s\nmissing runtime error message\n' "$name" >&2
        exit 1
    fi
    printf 'PASS %s\n' "$name"
}

write_case() {
    local path="$1"
    shift
    cat > "$path"
}
