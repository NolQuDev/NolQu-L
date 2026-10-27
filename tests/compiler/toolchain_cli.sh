#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/shared/lib.sh"

VERSION="$(<"$ROOT_DIR/VERSION")"

assert_eq "nql-version" "$("$ROOT_DIR/nql" version)" $'nql     '"$VERSION"$'\nnqlc    '"$VERSION"$' (x86_64-linux)'
assert_eq "nqlc-version" "$("$ROOT_DIR/nqlc" --version)" "nqlc $VERSION (x86_64-linux)"
[[ -f "$ROOT_DIR/nql" && ! -L "$ROOT_DIR/nql" ]] || {
    printf 'FAIL nql-canonical-binary\n' >&2
    exit 1
}
[[ -f "$ROOT_DIR/nqlc" && ! -L "$ROOT_DIR/nqlc" ]] || {
    printf 'FAIL nqlc-canonical-binary\n' >&2
    exit 1
}
[[ -L "$ROOT_DIR/nolqul" && "$(readlink "$ROOT_DIR/nolqul")" == "nql" ]] || {
    printf 'FAIL nolqul-alias\n' >&2
    exit 1
}
[[ -L "$ROOT_DIR/nolqulc" && "$(readlink "$ROOT_DIR/nolqulc")" == "nqlc" ]] || {
    printf 'FAIL nolqulc-alias\n' >&2
    exit 1
}
for removed_command in nq nqc nolqu nolquc; do
    [[ ! -e "$ROOT_DIR/$removed_command" ]] || {
        printf 'FAIL removed-command-%s\n' "$removed_command" >&2
        exit 1
    }
done
assert_eq "nolqul-version" "$("$ROOT_DIR/nolqul" version)" $'nolqul  '"$VERSION"$'\nnolqulc '"$VERSION"$' (x86_64-linux)'
assert_eq "nolqulc-version" "$("$ROOT_DIR/nolqulc" --version)" "nolqulc $VERSION (x86_64-linux)"
"$ROOT_DIR/nql" --build-compiler
[[ -x "$ROOT_DIR/build/nqlc-r0" && ! -e "$ROOT_DIR/build/nolquc" ]] || {
    printf 'FAIL canonical-r0-artifact\n' >&2
    exit 1
}
printf 'PASS canonical-cli-layout\n'

json_err="$TMP_DIR/json.err"
if "$ROOT_DIR/nqlc" --error-format=json --target arm64 "$ROOT_DIR/examples/core/hello.nq" 2>"$json_err"; then
    printf 'FAIL nqlc-json-error\nexpected failure\n' >&2
    exit 1
fi
grep -q '"level":"error"' "$json_err" || { printf 'FAIL nqlc-json-error\n' >&2; cat "$json_err" >&2; exit 1; }
grep -q '"message":"target .arm64. is not supported yet"' "$json_err" || { printf 'FAIL nqlc-json-message\n' >&2; cat "$json_err" >&2; exit 1; }
printf 'PASS nqlc-json-error\n'

flags="$TMP_DIR/flags.txt"
asm="$TMP_DIR/from-response.asm"
printf '%s\n' '-S' '-o' "$asm" > "$flags"
"$ROOT_DIR/nqlc" "@$flags" "$ROOT_DIR/examples/core/hello.nq"
[[ -s "$asm" ]] || { printf 'FAIL nqlc-response-file\n' >&2; exit 1; }
printf 'PASS nqlc-response-file\n'

if ! nasm -Werror -f elf64 "$asm" -o "$TMP_DIR/strict-assembly.o" 2>"$TMP_DIR/strict-assembly.err"; then
    printf 'FAIL nqlc-explicit-addressing\n' >&2
    cat "$TMP_DIR/strict-assembly.err" >&2
    exit 1
fi
printf 'PASS nqlc-explicit-addressing\n'

direct_bin="$TMP_DIR/direct-hello"
"$ROOT_DIR/nqlc" "$ROOT_DIR/examples/core/hello.nq" -o "$direct_bin"
assert_eq "nqlc-legacy-extension-run" "$(run_output "$direct_bin")" "42"

nolqulc_bin="$TMP_DIR/nolqulc-hello"
"$ROOT_DIR/nolqulc" "$ROOT_DIR/examples/core/hello.nq" -o "$nolqulc_bin"
assert_eq "nolqulc-direct-run" "$(run_output "$nolqulc_bin")" "42"

canonical_source="$TMP_DIR/hello.nql"
cp "$ROOT_DIR/examples/core/hello.nq" "$canonical_source"
nqlc_bin="$TMP_DIR/nqlc-hello"
"$ROOT_DIR/nqlc" "$canonical_source" -o "$nqlc_bin"
assert_eq "nqlc-direct-run" "$(run_output "$nqlc_bin")" "42"

repro_one="$TMP_DIR/repro-one"
repro_two="$TMP_DIR/repro-two"
SOURCE_DATE_EPOCH=0 "$ROOT_DIR/nqlc" "$canonical_source" -o "$repro_one"
SOURCE_DATE_EPOCH=0 "$ROOT_DIR/nqlc" "$canonical_source" -o "$repro_two"
cmp -s "$repro_one" "$repro_two" || {
    printf 'FAIL nqlc-reproducible-build\n' >&2
    exit 1
}
printf 'PASS nqlc-reproducible-build\n'

script_run_dir="$TMP_DIR/script-run"
mkdir -p "$script_run_dir"
(
    cd "$script_run_dir"
    assert_eq "nqlc-script-run" "$("$ROOT_DIR/nqlc" "$ROOT_DIR/examples/core/hello.nq")" "42"
    [[ -x hello ]] || { printf 'FAIL nqlc-script-default-output\n' >&2; exit 1; }
    assert_eq "nolqulc-script-run" "$("$ROOT_DIR/nolqulc" "$ROOT_DIR/examples/core/hello.nq")" "42"
    mkdir "$TMP_DIR/path-shadow"
    cat > "$TMP_DIR/path-shadow/hello" <<'SHADOW'
#!/usr/bin/env bash
printf 'wrong PATH executable\n'
exit 91
SHADOW
    chmod +x "$TMP_DIR/path-shadow/hello"
    assert_eq "nqlc-script-run-path-shadow" "$(PATH="$TMP_DIR/path-shadow:$PATH" "$ROOT_DIR/nqlc" "$ROOT_DIR/examples/core/hello.nq")" "42"
)
assert_eq "nqlc-run-direct" "$("$ROOT_DIR/nqlc" --run "$ROOT_DIR/examples/core/hello.nq")" "42"
assert_eq "nolqulc-run-direct" "$("$ROOT_DIR/nolqulc" --run "$ROOT_DIR/examples/core/hello.nq")" "42"

run_args_src="$TMP_DIR/run-args.nq"
cat > "$run_args_src" <<'NOLQU'
func main() {
    print argc
}

main()
NOLQU
run_args_dir="$TMP_DIR/run-args-dir"
mkdir -p "$run_args_dir"
(
    cd "$run_args_dir"
assert_eq "nqlc-run-args" "$("$ROOT_DIR/nqlc" "$run_args_src" -- one two three)" "3"
)

ast_out="$("$ROOT_DIR/nqlc" --dump-ast "$run_args_src")"
case "$ast_out" in
    *"File path=$run_args_src"*Function*"main"*Print*) printf 'PASS nqlc-dump-ast\n' ;;
    *) printf 'FAIL nqlc-dump-ast\n%s\n' "$ast_out" >&2; exit 1 ;;
esac
bad_ast_src="$TMP_DIR/bad-ast.nq"
printf 'print (1\n' > "$bad_ast_src"
if "$ROOT_DIR/nqlc" --dump-ast "$bad_ast_src" >"$TMP_DIR/bad-ast.out" 2>"$TMP_DIR/bad-ast.err"; then
    printf 'FAIL nqlc-dump-ast-invalid\nexpected failure\n' >&2
    exit 1
fi
[[ ! -s "$TMP_DIR/bad-ast.out" ]] || { printf 'FAIL nqlc-dump-ast-invalid-output\n' >&2; cat "$TMP_DIR/bad-ast.out" >&2; exit 1; }
printf 'PASS nqlc-dump-ast-invalid\n'

warn_src="$TMP_DIR/warn.nq"
printf 'print 1  \n' > "$warn_src"
"$ROOT_DIR/nqlc" -Wall --color never --check "$warn_src" 2>"$TMP_DIR/warn.err"
grep -Fq 'warning[WTRAILING_WHITESPACE]' "$TMP_DIR/warn.err" || { printf 'FAIL nqlc-wall-warning\n' >&2; cat "$TMP_DIR/warn.err" >&2; exit 1; }
printf 'PASS nqlc-wall-warning\n'
"$ROOT_DIR/nqlc" -Wall -Wno-trailing-whitespace --check "$warn_src" 2>"$TMP_DIR/wno.err"
[[ ! -s "$TMP_DIR/wno.err" ]] || { printf 'FAIL nqlc-wno-warning\n' >&2; cat "$TMP_DIR/wno.err" >&2; exit 1; }
printf 'PASS nqlc-wno-warning\n'
if "$ROOT_DIR/nqlc" -Wall -Werror --color never --check "$warn_src" 2>"$TMP_DIR/werror.err"; then
    printf 'FAIL nqlc-werror\nexpected failure\n' >&2
    exit 1
fi
grep -q 'warnings were treated as errors' "$TMP_DIR/werror.err" || { printf 'FAIL nqlc-werror\n' >&2; cat "$TMP_DIR/werror.err" >&2; exit 1; }
printf 'PASS nqlc-werror\n'
"$ROOT_DIR/nqlc" -Wall --error-format=json --check "$warn_src" 2>"$TMP_DIR/warn-json.err"
grep -q '"level":"warning"' "$TMP_DIR/warn-json.err" || { printf 'FAIL nqlc-warning-json\n' >&2; cat "$TMP_DIR/warn-json.err" >&2; exit 1; }
printf 'PASS nqlc-warning-json\n'
warn_limit_src="$TMP_DIR/warn-limit.nq"
printf 'print 1  \n// TODO  \n' > "$warn_limit_src"
if "$ROOT_DIR/nqlc" -Wall -Werror --max-errors=1 --check "$warn_limit_src" 2>"$TMP_DIR/werror-limit.err"; then
    printf 'FAIL nqlc-werror-max-errors\nexpected failure\n' >&2
    exit 1
fi
grep -q 'fatal: too many errors (1), compilation stopped' "$TMP_DIR/werror-limit.err" || { printf 'FAIL nqlc-werror-max-errors\n' >&2; cat "$TMP_DIR/werror-limit.err" >&2; exit 1; }
printf 'PASS nqlc-werror-max-errors\n'
env -u NO_COLOR -u NOLQUC_COLOR "$ROOT_DIR/nqlc" -Wall --color always --check "$warn_src" 2>"$TMP_DIR/warn-color.err"
grep -Fq $'\033[33mwarning' "$TMP_DIR/warn-color.err" || { printf 'FAIL nqlc-warning-color\n' >&2; cat "$TMP_DIR/warn-color.err" >&2; exit 1; }
printf 'PASS nqlc-warning-color\n'

run_exit_src="$TMP_DIR/run-exit.nq"
cat > "$run_exit_src" <<'NOLQU'
exit(7)
NOLQU
run_exit_dir="$TMP_DIR/run-exit-dir"
mkdir -p "$run_exit_dir"
if (cd "$run_exit_dir" && "$ROOT_DIR/nolqulc" "$run_exit_src"); then
    printf 'FAIL nolqulc-run-exit-code\nexpected exit 7\n' >&2
    exit 1
else
    code=$?
    [[ $code -eq 7 ]] || { printf 'FAIL nolqulc-run-exit-code\nexpected 7, got %s\n' "$code" >&2; exit 1; }
fi
printf 'PASS nolqulc-run-exit-code\n'

weird="$TMP_DIR/-weird.nq"
printf 'print 7\n' > "$weird"
"$ROOT_DIR/nqlc" -S -o "$TMP_DIR/weird.asm" -- "$weird"
[[ -s "$TMP_DIR/weird.asm" ]] || { printf 'FAIL nqlc-double-dash\n' >&2; exit 1; }
printf 'PASS nqlc-double-dash\n'

if "$ROOT_DIR/nqlc" "$ROOT_DIR/examples/core/hello.nq" "$ROOT_DIR/examples/core/arrays.nq" 2>"$TMP_DIR/multi.err"; then
    printf 'FAIL nqlc-multiple-requires-output\nexpected failure\n' >&2
    exit 1
fi
grep -q -- '-o is required when compiling more than one input file' "$TMP_DIR/multi.err" || {
    printf 'FAIL nqlc-multiple-requires-output\n' >&2
    cat "$TMP_DIR/multi.err" >&2
    exit 1
}
printf 'PASS nqlc-multiple-requires-output\n'

"$ROOT_DIR/nqlc" --check -j 2 "$ROOT_DIR/examples/core/hello.nq" "$ROOT_DIR/examples/core/arrays.nq"
printf 'PASS nqlc-parallel-check\n'

dep_out="$("$ROOT_DIR/nqlc" -M "$ROOT_DIR/examples/core/hello.nq")"
case "$dep_out" in
    "hello: $ROOT_DIR/examples/core/hello.nq") printf 'PASS nqlc-deps\n' ;;
    *) printf 'FAIL nqlc-deps\n%s\n' "$dep_out" >&2; exit 1 ;;
esac

ccdb_dir="$TMP_DIR/ccdb"
mkdir -p "$ccdb_dir"
(
    cd "$ccdb_dir"
    "$ROOT_DIR/nqlc" --emit-ccdb "$ROOT_DIR/examples/core/hello.nq"
    [[ -s compile_commands.json ]]
    grep -q '"file": "' compile_commands.json
    grep -q 'nqlc' compile_commands.json
)
printf 'PASS nqlc-ccdb\n'
ccdb_space_dir="$TMP_DIR/ccdb space"
mkdir -p "$ccdb_space_dir"
space_src="$ccdb_space_dir/hello space.nq"
printf 'print 9\n' > "$space_src"
(
    cd "$ccdb_space_dir"
    "$ROOT_DIR/nqlc" --emit-ccdb "$space_src"
    grep -q "'$space_src'" compile_commands.json
)
printf 'PASS nqlc-ccdb-spaces\n'

timed_bin="$TMP_DIR/timed-hello"
"$ROOT_DIR/nqlc" --time -v "$ROOT_DIR/examples/core/hello.nq" -o "$timed_bin" 2>"$TMP_DIR/time.err"
grep -q '^\[1/4\] parsing' "$TMP_DIR/time.err" || { printf 'FAIL nqlc-time-parsing\n' >&2; cat "$TMP_DIR/time.err" >&2; exit 1; }
grep -q '^\[4/4\] linking' "$TMP_DIR/time.err" || { printf 'FAIL nqlc-time-linking\n' >&2; cat "$TMP_DIR/time.err" >&2; exit 1; }
grep -q '^total: [0-9][0-9]*ms$' "$TMP_DIR/time.err" || { printf 'FAIL nqlc-time-total\n' >&2; cat "$TMP_DIR/time.err" >&2; exit 1; }
printf 'PASS nqlc-time\n'

save_bin="$TMP_DIR/save-temps-hello"
"$ROOT_DIR/nqlc" --save-temps "$ROOT_DIR/examples/core/hello.nq" -o "$save_bin" 2>"$TMP_DIR/save.err"
save_dir="$(sed -n 's/^saved temporary files in //p' "$TMP_DIR/save.err")"
[[ -n "$save_dir" && -d "$save_dir" && -s "$save_dir/output.asm" ]] || {
    printf 'FAIL nqlc-save-temps\n' >&2
    cat "$TMP_DIR/save.err" >&2
    exit 1
}
rm -rf "$save_dir"
printf 'PASS nqlc-save-temps\n'

dry_bin="$TMP_DIR/dry-run-hello"
"$ROOT_DIR/nqlc" --dry-run "$ROOT_DIR/examples/core/hello.nq" -o "$dry_bin" 2>"$TMP_DIR/dry.err"
grep -q 'nql_r0_adapter.sh --emit' "$TMP_DIR/dry.err" || { printf 'FAIL nqlc-dry-run-emit\n' >&2; cat "$TMP_DIR/dry.err" >&2; exit 1; }
grep -q 'nasm -f elf64' "$TMP_DIR/dry.err" || { printf 'FAIL nqlc-dry-run-assemble\n' >&2; cat "$TMP_DIR/dry.err" >&2; exit 1; }
grep -Eq '(x86_64-linux-gnu-ld|^ld) .* -o '"$dry_bin" "$TMP_DIR/dry.err" || { printf 'FAIL nqlc-dry-run-link\n' >&2; cat "$TMP_DIR/dry.err" >&2; exit 1; }
[[ ! -e "$dry_bin" ]] || { printf 'FAIL nqlc-dry-run-output\n' >&2; exit 1; }
printf 'PASS nqlc-dry-run\n'

make -s -C "$ROOT_DIR" ir-json EXAMPLE="$ROOT_DIR/examples/core/hello.nq" >/dev/null
python3 "$ROOT_DIR/tools/nq_ir_dump_parser.py" "$ROOT_DIR/build/output.ir" "$TMP_DIR/make-ir-json.expected" >/dev/null
if ! diff -u "$TMP_DIR/make-ir-json.expected" "$ROOT_DIR/build/output.ir.json"; then
    printf 'FAIL make-ir-json-nq-parser\n' >&2
    exit 1
fi
printf 'PASS make-ir-json-nq-parser\n'

init_current="$TMP_DIR/current-init"
mkdir -p "$init_current"
(
    cd "$init_current"
    "$ROOT_DIR/nolqul" init >/dev/null
    [[ -f nql.toml && -f src/main.nql && -f .gitignore ]]
    grep -q '^\.nql/$' .gitignore
    grep -q '^func main() {' src/main.nql
)
printf 'PASS nolqul-init-current-dir\n'

init_nonempty="$TMP_DIR/nonempty-init"
mkdir -p "$init_nonempty"
printf 'data\n' > "$init_nonempty/existing.txt"
if (cd "$init_nonempty" && "$ROOT_DIR/nolqul" init 2>"$TMP_DIR/init-nonempty.err"); then
    printf 'FAIL nolqul-init-nonempty\nexpected failure\n' >&2
    exit 1
fi
grep -q 'already exists and is not empty' "$TMP_DIR/init-nonempty.err" || { printf 'FAIL nolqul-init-nonempty\n' >&2; cat "$TMP_DIR/init-nonempty.err" >&2; exit 1; }
printf 'PASS nolqul-init-nonempty\n'

if "$ROOT_DIR/nolqul" build extra 2>"$TMP_DIR/nolqul-extra.err"; then
    printf 'FAIL nolqul-build-extra-arg\nexpected failure\n' >&2
    exit 1
fi
grep -q 'nolqul build does not accept positional arguments' "$TMP_DIR/nolqul-extra.err" || { printf 'FAIL nolqul-build-extra-arg\n' >&2; cat "$TMP_DIR/nolqul-extra.err" >&2; exit 1; }
printf 'PASS nolqul-build-extra-arg\n'

project="$TMP_DIR/app"
(
    cd "$TMP_DIR"
    "$ROOT_DIR/nolqul" init app >/dev/null
    cd "$project"
    "$ROOT_DIR/nolqul" check >/dev/null
    "$ROOT_DIR/nolqul" build >/dev/null
    "$ROOT_DIR/nolqul" build --release >/dev/null 2>"$TMP_DIR/nolqul-build-release.err"
    grep -q 'Compiling app v' "$TMP_DIR/nolqul-build-release.err"
    "$ROOT_DIR/nolqul" check --release -v --color never >/dev/null 2>"$TMP_DIR/nolqul-check-verbose.err"
    grep -q 'Checking app v' "$TMP_DIR/nolqul-check-verbose.err"
    "$ROOT_DIR/nolqul" check --color never >/dev/null
    [[ -x "$project/.nql/build/app" ]]
    assert_eq "nolqul-project-run-output" "$("$ROOT_DIR/nolqul" run 2>"$TMP_DIR/nolqul-run.err")" "Hello, World!"
    "$ROOT_DIR/nolqul" test 2>"$TMP_DIR/nolqul-empty-test.err"
    grep -q 'No tests found' "$TMP_DIR/nolqul-empty-test.err"
    cat > src/main.nql <<'NOLQU'
func main() {
    print argc
}

main()
NOLQU
    assert_eq "nolqul-run-args" "$("$ROOT_DIR/nolqul" run -- one two three 2>"$TMP_DIR/nolqul-run-args.err")" "3"
    mkdir -p tests/nested
    cat > tests/nested/basic.nql <<'NOLQU'
print "test ok"
NOLQU
    mkdir -p tests/other
    cat > tests/other/basic.nql <<'NOLQU'
print "other ok"
NOLQU
    "$ROOT_DIR/nolqul" test 2>"$TMP_DIR/nolqul-test.err"
    grep -q 'test tests/nested/basic.nql ... ok' "$TMP_DIR/nolqul-test.err"
    grep -q 'test tests/other/basic.nql ... ok' "$TMP_DIR/nolqul-test.err"
    [[ -x "$project/.nql/tests/tests/nested/basic" ]]
    [[ -x "$project/.nql/tests/tests/other/basic" ]]
    "$ROOT_DIR/nolqul" test --release -q 2>"$TMP_DIR/nolqul-test-quiet.err"
    [[ ! -s "$TMP_DIR/nolqul-test-quiet.err" ]]
    "$ROOT_DIR/nolqul" clean >/dev/null
    [[ ! -e "$project/.nql" ]]
)
printf 'PASS nolqul-project-lifecycle\n'

canonical_project="$TMP_DIR/nql-app"
(
    cd "$TMP_DIR"
    "$ROOT_DIR/nql" init nql-app >/dev/null
    cd "$canonical_project"
    [[ -f nql.toml && -f src/main.nql ]]
    grep -q '^\.nql/$' .gitignore
    "$ROOT_DIR/nql" check >/dev/null
    "$ROOT_DIR/nql" build >/dev/null
    [[ -x "$canonical_project/.nql/build/nql-app" ]]
    assert_eq "nql-project-run-output" "$("$ROOT_DIR/nql" run 2>"$TMP_DIR/nql-run.err")" "Hello, World!"
    "$ROOT_DIR/nql" clean >/dev/null
    [[ ! -e "$canonical_project/.nql" ]]
)
printf 'PASS nql-project-lifecycle\n'

install_root="$TMP_DIR/install-root"
mkdir -p "$install_root/opt/nolqu-test/bin"
for removed_command in nq nqc nolqu nolquc; do
    touch "$install_root/opt/nolqu-test/bin/$removed_command"
done
env -u PREFIX NQL_HOME="/opt/nolqu-test" DESTDIR="$install_root" "$ROOT_DIR/install.sh" >/dev/null
[[ -f "$install_root/opt/nolqu-test/bin/nql" && ! -L "$install_root/opt/nolqu-test/bin/nql" ]]
[[ -f "$install_root/opt/nolqu-test/bin/nqlc" && ! -L "$install_root/opt/nolqu-test/bin/nqlc" ]]
[[ -L "$install_root/opt/nolqu-test/bin/nolqul" && "$(readlink "$install_root/opt/nolqu-test/bin/nolqul")" == "nql" ]]
[[ -L "$install_root/opt/nolqu-test/bin/nolqulc" && "$(readlink "$install_root/opt/nolqu-test/bin/nolqulc")" == "nqlc" ]]
[[ -x "$install_root/opt/nolqu-test/lib/nolqu/build/nqlc-r0" ]]
[[ -f "$install_root/opt/nolqu-test/lib/nolqu/src/nqlc.asm" ]]
[[ -x "$install_root/opt/nolqu-test/lib/nolqu/tools/nql_r0_adapter.sh" ]]
[[ ! -e "$install_root/opt/nolqu-test/lib/nolqu/build/nolquc" ]]
for removed_command in nq nqc nolqu nolquc; do
    [[ ! -e "$install_root/opt/nolqu-test/bin/$removed_command" ]]
done
installed_run_dir="$TMP_DIR/installed-run"
mkdir -p "$installed_run_dir"
(
    cd "$installed_run_dir"
    assert_eq "installed-nqlc-script-run" "$("$install_root/opt/nolqu-test/bin/nqlc" "$ROOT_DIR/examples/core/hello.nq")" "42"
    assert_eq "installed-nolqulc-script-run" "$("$install_root/opt/nolqu-test/bin/nolqulc" "$ROOT_DIR/examples/core/hello.nq")" "42"
)
for removed_command in nq nqc nolqu nolquc; do
    touch "$install_root/opt/nolqu-test/bin/$removed_command"
done
env -u PREFIX NQL_HOME="/opt/nolqu-test" DESTDIR="$install_root" "$ROOT_DIR/install.sh" --uninstall >/dev/null
[[ ! -e "$install_root/opt/nolqu-test/bin/nql" ]]
[[ ! -e "$install_root/opt/nolqu-test/bin/nqlc" ]]
[[ ! -e "$install_root/opt/nolqu-test/bin/nolqul" ]]
[[ ! -e "$install_root/opt/nolqu-test/bin/nolqulc" ]]
for removed_command in nq nqc nolqu nolquc; do
    [[ ! -e "$install_root/opt/nolqu-test/bin/$removed_command" ]]
done
printf 'PASS toolchain-install-nql-home\n'
