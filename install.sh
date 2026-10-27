#!/usr/bin/env bash
set -euo pipefail

PREFIX="${PREFIX:-${NQL_HOME:-/usr/local}}"
DESTDIR="${DESTDIR:-}"
BINDIR="$DESTDIR$PREFIX/bin"
LIBDIR="$DESTDIR$PREFIX/lib/nolqu"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
canonical_only=0
uninstall=0
for arg in "$@"; do
    case "$arg" in
        --canonical-only) [[ $canonical_only -eq 0 ]] || { printf 'error: duplicate --canonical-only\n' >&2; exit 1; }; canonical_only=1 ;;
        --uninstall) [[ $uninstall -eq 0 ]] || { printf 'error: duplicate --uninstall\n' >&2; exit 1; }; uninstall=1 ;;
        *) printf 'error: unknown install option: %s\n' "$arg" >&2; exit 1 ;;
    esac
done
[[ $canonical_only -eq 0 || $uninstall -eq 0 ]] || { printf 'error: --canonical-only cannot be combined with --uninstall\n' >&2; exit 1; }

if [[ $uninstall -eq 1 ]]; then
    rm -f "$BINDIR/nql" "$BINDIR/nolqul" "$BINDIR/nqlc" "$BINDIR/nolqulc"
    rm -f "$BINDIR/nq" "$BINDIR/nqc" "$BINDIR/nolqu" "$BINDIR/nolquc"
    rm -rf "$LIBDIR"
    printf "Uninstalled NolQu-L toolchain from %s\n" "$DESTDIR$PREFIX"
    exit 0
fi

if [[ $canonical_only -eq 0 && ! -x "$ROOT_DIR/build/nqlc-r0" ]]; then
    LINKER="ld"
    if command -v x86_64-linux-gnu-ld >/dev/null 2>&1; then LINKER="x86_64-linux-gnu-ld"; fi
    command -v nasm >/dev/null 2>&1 || { printf "error: assembler 'nasm' not found\n" >&2; exit 1; }
    command -v "$LINKER" >/dev/null 2>&1 || { printf "error: linker 'ld' not found. Make sure binutils is installed\n" >&2; exit 1; }
    mkdir -p "$ROOT_DIR/build"
    nasm -f elf64 "$ROOT_DIR/src/nqlc.asm" -o "$ROOT_DIR/build/nqlc-r0.o"
    "$LINKER" "$ROOT_DIR/build/nqlc-r0.o" -o "$ROOT_DIR/build/nqlc-r0"
fi

install -d "$BINDIR" "$LIBDIR/tools" "$LIBDIR/bootstrap"
rm -f "$LIBDIR/build/nolquc" "$LIBDIR/build/nolquc.o"
rm -f "$LIBDIR/src/nolquc.asm" "$LIBDIR/tools/nq_legacy.sh"
install -m 755 "$ROOT_DIR/nqlc" "$BINDIR/nqlc"
install -m 755 "$ROOT_DIR/nql" "$BINDIR/nql"
install -m 644 "$ROOT_DIR/VERSION" "$LIBDIR/VERSION"
install -m 755 "$ROOT_DIR/tools/nql_c0_driver.sh" "$LIBDIR/tools/nql_c0_driver.sh"
cp -pR -- "$ROOT_DIR/bootstrap/." "$LIBDIR/bootstrap/"
if [[ $canonical_only -eq 0 ]]; then
    install -d "$LIBDIR/build" "$LIBDIR/src"
    install -m 755 "$ROOT_DIR/build/nqlc-r0" "$LIBDIR/build/nqlc-r0"
    install -m 644 "$ROOT_DIR/src/nqlc.asm" "$LIBDIR/src/nqlc.asm"
    install -m 755 "$ROOT_DIR/tools/nql_r0_adapter.sh" "$LIBDIR/tools/nql_r0_adapter.sh"
    install -m 755 "$ROOT_DIR/tools/nq_ir_dump_parser.py" "$LIBDIR/tools/nq_ir_dump_parser.py"
    install -m 755 "$ROOT_DIR/tools/nq_ir_json_to_llvm.py" "$LIBDIR/tools/nq_ir_json_to_llvm.py"
fi
rm -f "$BINDIR/nq" "$BINDIR/nqc" "$BINDIR/nolqu" "$BINDIR/nolquc"
ln -sfn "nql" "$BINDIR/nolqul"
ln -sfn "nqlc" "$BINDIR/nolqulc"
printf "Installed nql/nolqul and nqlc/nolqulc into %s\n" "$BINDIR"
printf 'Canonical execution with terminal stdin requires Linux setsid (util-linux).\n'
