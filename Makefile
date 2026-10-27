.PHONY: canonical-native-test help show-version show-channel machine-foundation stage0 stage0-test bootstrap-test compiler run check dump-tokens dump-ir export-ir ir-json ir-llvm smoke examples llvm-smoke release-check test clean install uninstall dev stable set-dev set-stable

ROOT_DIR := $(CURDIR)
BUILD_DIR := $(ROOT_DIR)/build
NQL := $(ROOT_DIR)/nql
NQLC := $(ROOT_DIR)/nqlc
VERSION := $(shell cat $(ROOT_DIR)/VERSION)
CHANNEL := $(shell cat $(ROOT_DIR)/CHANNEL)
EXAMPLE ?= $(ROOT_DIR)/examples/core/hello.nq
MODE ?=
BACKEND ?= nasm

help:
	@printf '%s\n' \
	'Targets:' \
	'  make machine-foundation       Reconstruct and verify the machine seed' \
	'  make stage0                   Build Stage 0 with the machine seed' \
	'  make stage0-test              Test the canonical Stage 0 emitter' \
	'  make bootstrap-test           Test all implemented canonical stages' \
	'  make canonical-native-test    Test canonical unsafe/argv/syscall/native utility' \
	'  make compiler                 Build Reference Compiler R0 into build/' \
	'  make run EXAMPLE=path.nq      Compile and run a NolQu-L program with R0' \
	'  make check EXAMPLE=path.nq    Compile only to build/output.asm' \
	'  make dump-tokens EXAMPLE=...  Dump compiler tokens for a source file' \
	'  make dump-ir EXAMPLE=...      Dump compiler IR for a source file' \
	'  make export-ir EXAMPLE=...    Export compiler IR to build/output.ir' \
	'  make ir-json EXAMPLE=...      Parse exported IR into build/output.ir.json' \
	'  make ir-llvm EXAMPLE=...      Lower IR JSON into build/output.ir.ll' \
	'  make smoke                    Run the fast smoke suite' \
	'  make examples                 Run the bundled example programs' \
	'  make llvm-smoke               Run the frozen legacy LLVM smoke suite' \
	'  make release-check            Verify version/channel/docs consistency' \
	'  make show-version             Print the current NolQu-L version' \
	'  make show-channel             Print the current release channel' \
	'  make dev                      Dev workflow: build + tests on current channel' \
	'  make stable                   Stable workflow: enforce stable channel + tests' \
	'  make set-dev                  Switch the release channel to dev' \
	'  make set-stable               Switch the release channel to stable' \
	'  make test                     Run canonical and R0 regression suites' \
	'  make clean                    Remove generated build artifacts' \
	'  make install                  Install nql/nolqul and nqlc/nolqulc' \
	'  make uninstall                Remove all NolQu-L command names' \
	'' \
	'Metadata:' \
	'  version = $(VERSION)' \
	'  channel = $(CHANNEL)' \
	'' \
	'Examples:' \
	'  make compiler' \
	'  make run EXAMPLE=examples/core/hello.nq' \
	'  make dump-ir EXAMPLE=examples/semantics/functions.nq MODE=--release' \
	'  make export-ir EXAMPLE=examples/semantics/functions.nq MODE=--release' \
	'  make ir-json EXAMPLE=examples/semantics/functions.nq MODE=--release' \
	'  make ir-llvm EXAMPLE=examples/core/hello.nq MODE=--release' \
	'  make run EXAMPLE=examples/llvm/llvm_basic.nq BACKEND=llvm'

show-version:
	@printf '%s\n' "$(VERSION)"

show-channel:
	@printf '%s\n' "$(CHANNEL)"

machine-foundation:
	@$(ROOT_DIR)/bootstrap/machine/x86_64-linux/materialize.sh

stage0: machine-foundation
	@$(ROOT_DIR)/bootstrap/stage0/x86_64-linux/materialize.sh

stage0-test: stage0
	@ROOT_DIR="$(ROOT_DIR)" $(ROOT_DIR)/tests/shared/run_suite.sh "$(ROOT_DIR)/tests/bootstrap/stage0.sh"

bootstrap-test: stage0
	@$(ROOT_DIR)/tests/bootstrap/run_tests.sh

canonical-native-test:
	@ROOT_DIR="$(ROOT_DIR)" $(ROOT_DIR)/tests/shared/run_suite.sh "$(ROOT_DIR)/tests/bootstrap/c0_native_os.sh"

compiler:
	@mkdir -p $(BUILD_DIR)
	@$(NQL) --build-compiler

run: compiler
	@$(NQL) --backend $(BACKEND) --run $(EXAMPLE) $(MODE)

check: compiler
	@$(NQL) --backend $(BACKEND) --check $(EXAMPLE) $(MODE)

dump-tokens: compiler
	@$(NQL) --backend $(BACKEND) --dump-tokens $(EXAMPLE) $(MODE)

dump-ir: compiler
	@$(NQL) --backend $(BACKEND) --dump-ir $(EXAMPLE) $(MODE)

export-ir: compiler
	@$(NQL) --backend $(BACKEND) --export-ir $(BUILD_DIR)/output.ir $(EXAMPLE) $(MODE)

ir-json: export-ir
	@$(NQLC) --run $(ROOT_DIR)/tools/nql_ir_dump_parser.nql -- $(BUILD_DIR)/output.ir $(BUILD_DIR)/output.ir.json

ir-llvm: ir-json
	@python3 $(ROOT_DIR)/tools/nq_ir_json_to_llvm.py $(BUILD_DIR)/output.ir.json $(BUILD_DIR)/output.ir.ll

smoke: compiler
	@ROOT_DIR="$(ROOT_DIR)" $(ROOT_DIR)/tests/shared/run_suite.sh "$(ROOT_DIR)/tests/compiler/smoke.sh"

examples: compiler
	@$(NQL) --run $(ROOT_DIR)/examples/core/hello.nq >/dev/null
	@$(NQL) --run $(ROOT_DIR)/examples/core/arrays.nq >/dev/null
	@$(NQL) --run $(ROOT_DIR)/examples/semantics/functions.nq >/dev/null
	@$(NQL) --run $(ROOT_DIR)/examples/semantics/branching.nq >/dev/null
	@printf 'Examples OK\n'

llvm-smoke: compiler
	@ROOT_DIR="$(ROOT_DIR)" $(ROOT_DIR)/tests/shared/run_suite.sh "$(ROOT_DIR)/tests/llvm/smoke.sh"

release-check: compiler
	@$(ROOT_DIR)/tests/meta/release_check.sh

test: bootstrap-test compiler
	@$(ROOT_DIR)/tests/compiler/run_tests.sh

dev: compiler test release-check
	@printf 'NolQu-L %s [%s]\n' "$(VERSION)" "$(CHANNEL)"

stable:
	@if [ "$(CHANNEL)" != "stable" ]; then \
		printf 'Refusing stable workflow on channel %s\n' "$(CHANNEL)" >&2; \
		exit 1; \
	fi
	@$(MAKE) test
	@$(MAKE) release-check
	@printf 'NolQu-L %s [stable]\n' "$(VERSION)"

set-dev:
	@printf 'dev\n' > $(ROOT_DIR)/CHANNEL
	@printf 'Channel set to dev\n'

set-stable:
	@printf 'stable\n' > $(ROOT_DIR)/CHANNEL
	@printf 'Channel set to stable\n'

clean:
	@rm -f $(BUILD_DIR)/nqlc-r0 $(BUILD_DIR)/nqlc-r0.o $(BUILD_DIR)/nolquc $(BUILD_DIR)/nolquc.o $(BUILD_DIR)/output $(BUILD_DIR)/output.o $(BUILD_DIR)/output.asm $(BUILD_DIR)/output.ir $(BUILD_DIR)/output.ir.json $(BUILD_DIR)/output.ir.ll

install:
	@$(ROOT_DIR)/install.sh

uninstall:
	@$(ROOT_DIR)/install.sh --uninstall
