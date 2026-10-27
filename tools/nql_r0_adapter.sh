#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN="$ROOT_DIR/build/nqlc-r0"

# Pick an x86_64 linker: prefer the cross-linker on non-x86_64 hosts,
# fall back to plain ld on native x86_64.
if command -v x86_64-linux-gnu-ld &>/dev/null; then
    X86_LD="x86_64-linux-gnu-ld"
else
    X86_LD="ld"
fi

usage() {
    cat <<'USAGE'
Usage: nql <file.nql> [options]
       nql run      <file.nql>           Compile, assemble, link and execute
       nql check    <file.nql>           Compile only, do not write output
       nql emit     <path> <file.nql>    Write backend output to <path>
       nql release  <file.nql>           Enable optimizations
       nql tokens   <file.nql>           Dump tokenizer output to stdout
       nql ir       <file.nql>           Dump IR to stdout
       nql export-ir <path> <file.nql>   Write IR dump to <path>
       nql bench    <file.nql>           Print compilation timings
       nql build                        Rebuild the nqlc R0 engine

Compiler options (flag form):
  --check              Compile only, do not write output
  --emit <path>        Write backend output to <path> (default: build/output.asm)
  --backend <name>     Select backend: nasm or llvm
  --release            Enable optimizations
  --bench              Print compilation timings
  --dump-tokens        Dump tokenizer output to stdout
  --dump-ir            Dump IR to stdout
  --export-ir <path>   Write IR dump to <path>
  --build-compiler     Rebuild the nqlc R0 engine from source

General:
  --version, -v        Print version and exit
  --help,    -h        Print this help and exit
USAGE
}

args=("$@")
argc=${#args[@]}

if [[ $argc -eq 0 ]]; then
    usage >&2
    exit 1
fi
if [[ "${args[0]}" == "--help" || "${args[0]}" == "-h" ]]; then
    usage
    exit 0
fi
if [[ "${args[0]}" == "--version" || "${args[0]}" == "-v" ]]; then
    printf 'NolQu-L R0 %s\n' "$(cat "$ROOT_DIR/VERSION")"
    exit 0
fi

# Subcommand form: nql run <file>, nql check <file>, etc.
case "${args[0]}" in
    run)
        shift
        has_run=1
        args=("$@")
        argc=${#args[@]}
        ;;
    check)
        shift; exec "$0" --check "$@" ;;
    emit)
        shift
        if [[ $# -lt 1 || "$1" == --* ]]; then
            printf '%s\n' "nql: emit requires a path" >&2
            exit 1
        fi
        _emit_path="$1"; shift
        exec "$0" --emit "$_emit_path" "$@" ;;
    release)
        shift; exec "$0" --release "$@" ;;
    tokens)
        shift; exec "$0" --dump-tokens "$@" ;;
    ir)
        shift; exec "$0" --dump-ir "$@" ;;
    export-ir)
        shift
        if [[ $# -lt 1 || "$1" == --* ]]; then
            printf '%s\n' "nql: export-ir requires a path" >&2
            exit 1
        fi
        _ir_path="$1"; shift
        exec "$0" --export-ir "$_ir_path" "$@" ;;
    bench)
        shift; exec "$0" --bench "$@" ;;
    build)
        exec "$0" --build-compiler ;;
    *)
        has_run=0
        ;;
esac

# Scan argv for wrapper-level flags
has_run=${has_run:-0}
has_dump_ir=0
has_dump_tokens=0
has_emit=0
has_bench=0
has_build=0
has_release=0
emit_path=""
export_ir_path=""
backend="nasm"

for ((i=0; i<argc; i++)); do
    case "${args[$i]}" in
        --build-compiler) has_build=1 ;;
        --run)            has_run=1 ;;
        --check) ;;
        --release)         has_release=1 ;;
        --bench)          has_bench=1 ;;
        --dump-tokens)    has_dump_tokens=1 ;;
        --dump-ir)        has_dump_ir=1 ;;
        --emit)
            if ((i+1 >= argc)) || [[ "${args[$((i+1))]}" == --* ]]; then
                printf '%s\n' "nql: --emit requires a path" >&2
                exit 1
            fi
            has_emit=1
            emit_path="${args[$((i+1))]}"
            ((i+=1))
            ;;
        --export-ir)
            if ((i+1 >= argc)) || [[ "${args[$((i+1))]}" == --* ]]; then
                printf '%s\n' "nql: --export-ir requires a path" >&2
                exit 1
            fi
            export_ir_path="${args[$((i+1))]}"
            ((i+=1))
            ;;
        --backend)
            if ((i+1 >= argc)); then
                printf '%s\n' "nql: --backend requires nasm or llvm" >&2
                exit 1
            fi
            backend="${args[$((i+1))]}"
            case "$backend" in
                nasm|llvm) ;;
                *)
                    printf 'nql: unknown backend: %s\n' "$backend" >&2
                    exit 1
                    ;;
            esac
            ((i+=1))
            ;;
        --*)
            printf 'nql: unknown option: %s\n' "${args[$i]}" >&2
            exit 1
            ;;
    esac
done

# LLVM backend: use the real Nolqu frontend, then lower exported IR to LLVM IR
if [[ "$backend" == "llvm" ]]; then
    if [[ $has_run -eq 1 && $has_dump_ir -eq 1 ]]; then
        printf '%s\n' "run cannot be used with --dump-ir" >&2
        exit 1
    fi
    if [[ $has_bench -eq 1 ]]; then
        printf '%s\n' "nql: LLVM backend does not support --bench" >&2
        exit 1
    fi
    if [[ $has_build -eq 1 ]]; then
        printf '%s\n' "nql: --build-compiler cannot be combined with --backend llvm" >&2
        exit 1
    fi
    src_file=""
    for arg in "${args[@]}"; do
        case "$arg" in
            --check) ;;
            --run)   ;;
            --backend|llvm|--release) ;;
            --*) ;;
            *.nql|*.nq)
                if [[ -n "$src_file" ]]; then
                    printf '%s\n' "nql: LLVM backend expects exactly one .nql source file" >&2
                    exit 1
                fi
                src_file="$arg"
                ;;
        esac
    done
    if [[ -z "$src_file" ]]; then
        printf '%s\n' "nql: LLVM backend requires a .nql source file" >&2
        exit 1
    fi
    frontend_inspect_args=("$src_file")
    if [[ $has_release -eq 1 ]]; then
        frontend_inspect_args+=("--release")
    fi
    if [[ $has_dump_tokens -eq 1 ]]; then
        qemu-x86_64 "$BIN" "$src_file" --dump-tokens
        exit $?
    fi
    if [[ $has_dump_ir -eq 1 ]]; then
        qemu-x86_64 "$BIN" "${frontend_inspect_args[@]}" --dump-ir
        exit $?
    fi
    if [[ -n "$export_ir_path" ]]; then
        mkdir -p "$(dirname "$export_ir_path")"
        qemu-x86_64 "$BIN" "${frontend_inspect_args[@]}" --dump-ir > "$export_ir_path"
        exit $?
    fi

    if [[ $has_emit -eq 1 ]]; then
        out_ll="$emit_path"
    else
        mkdir -p "$ROOT_DIR/build"
        out_ll="$ROOT_DIR/build/output.ll"
    fi
    mkdir -p "$(dirname "$out_ll")"
    tmp_dir="$(mktemp -d)"
    cleanup_llvm_tmp() {
        rm -rf "$tmp_dir"
    }
    trap cleanup_llvm_tmp EXIT
    tmp_ir="$tmp_dir/output.ir"
    tmp_json="$tmp_dir/output.json"
    tmp_parser_asm="$tmp_dir/nql_ir_dump_parser.asm"
    tmp_parser_o="$tmp_dir/nql_ir_dump_parser.o"
    tmp_parser_bin="$tmp_dir/nql_ir_dump_parser"
    frontend_args=("$src_file" "--dump-ir")
    if [[ $has_release -eq 1 ]]; then
        frontend_args+=("--release")
    fi
    qemu-x86_64 "$BIN" "${frontend_args[@]}" > "$tmp_ir"
    qemu-x86_64 "$BIN" "$ROOT_DIR/tools/nql_ir_dump_parser.nql" --emit "$tmp_parser_asm" >/dev/null
    nasm -f elf64 "$tmp_parser_asm" -o "$tmp_parser_o"
    $X86_LD "$tmp_parser_o" -o "$tmp_parser_bin"
    if [[ "$(uname -m)" == "x86_64" ]]; then
        "$tmp_parser_bin" "$tmp_ir" "$tmp_json" >/dev/null
    else
        qemu-x86_64 "$tmp_parser_bin" "$tmp_ir" "$tmp_json" >/dev/null
    fi
    python3 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$tmp_json" "$out_ll" >/dev/null
    if [[ $has_run -eq 1 ]]; then
        lli "$out_ll"
        exit $?
    fi
    exit 0
fi

# --build-compiler: rebuild the nqlc R0 engine from source
if [[ $has_build -eq 1 ]]; then
    cd "$ROOT_DIR"
    mkdir -p build
    rm -f build/nolquc build/nolquc.o
    nasm -f elf64 src/nqlc.asm -o build/nqlc-r0.o
    $X86_LD build/nqlc-r0.o -o build/nqlc-r0
    exit 0
fi

# run + --dump-ir conflict
if [[ $has_run -eq 1 && $has_dump_ir -eq 1 ]]; then
    printf '%s\n' "run cannot be used with --dump-ir" >&2
    exit 1
fi

# Build the argument list passed to the nqlc R0 engine:
# strip --build-compiler, --backend <val>, translate --export-ir <path> -> --dump-ir
compiler_args=()
skip_next=0
for ((i=0; i<argc; i++)); do
    arg="${args[$i]}"
    if [[ $skip_next -eq 1 ]]; then
        skip_next=0
        continue
    fi
    case "$arg" in
        --build-compiler) ;;
        --run) ;;
        --backend) skip_next=1 ;;
        --export-ir)
            compiler_args+=("--dump-ir")
            skip_next=1
            ;;
        *) compiler_args+=("$arg") ;;
    esac
done

# --export-ir: run the nqlc R0 engine with --dump-ir, redirect stdout to file
if [[ -n "$export_ir_path" ]]; then
    qemu-x86_64 "$BIN" "${compiler_args[@]}" > "$export_ir_path"
    exit $?
fi

# run: compile, assemble, link, execute
if [[ $has_run -eq 1 ]]; then
    mkdir -p "$ROOT_DIR/build"
    qemu-x86_64 "$BIN" "${compiler_args[@]}" --emit "$ROOT_DIR/build/output.asm" >/dev/null
    nasm -f elf64 "$ROOT_DIR/build/output.asm" -o "$ROOT_DIR/build/output.o"
    $X86_LD "$ROOT_DIR/build/output.o" -o "$ROOT_DIR/build/output"
    if [[ "$(uname -m)" == "x86_64" ]]; then
        exec "$ROOT_DIR/build/output"
    else
        exec qemu-x86_64 "$ROOT_DIR/build/output"
    fi
fi

# Default: pass through to the nqlc R0 engine
mkdir -p "$ROOT_DIR/build"
exec qemu-x86_64 "$BIN" "${compiler_args[@]}"
