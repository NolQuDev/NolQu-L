"""Public canonical CLI integration tests using the pinned C0 components."""

import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import pty
import re
import select
import shutil
import signal
import stat
import struct
import subprocess
import tempfile
import termios
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "bootstrap/compiler/c0/x86_64-linux/compile-source.sh"
PRINT_CANONICAL = ("byte_store(0,99) byte_store(1,97) byte_store(2,110) "
                   "byte_store(3,111) byte_store(4,110) byte_store(5,105) "
                   "byte_store(6,99) byte_store(7,97) byte_store(8,108) "
                   "byte_store(9,10) output_write(0,10)")
READY_SOURCE = ("fn main(){byte_store(0,114) byte_store(1,101) byte_store(2,97) "
                "byte_store(3,100) byte_store(4,121) byte_store(5,10) "
                "output_write(0,6) return input_read(0,1)}\n")
TTY_SOURCE = ("fn main(){byte_store(0,114) byte_store(1,101) byte_store(2,97) "
              "byte_store(3,100) byte_store(4,121) byte_store(5,10) "
              "output_write(0,6) let n=input_read(100,2) "
              "output_write(100,n) return 23}\n")


class CanonicalCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="canonical-cli-")
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        self.source = self.work / "main.nql"
        self.source.write_text("fn main(){" + PRINT_CANONICAL + " return 23}\n")
        self.output = self.work / "program"
        self.temps = self.work / "temps"
        self.temps.mkdir()
        self.env = os.environ.copy()
        for name in ("NOLQU_ROOT", "NOLQUC_MAX_ERRORS"):
            self.env.pop(name, None)
        self.env.update(TMPDIR=str(self.temps), NO_COLOR="1", NOLQUC_COLOR="never")

    def command(self, *argv, input=b"", cwd=None, env=None):
        argv = [str(arg) for arg in argv]
        directory = cwd or self.work
        result = subprocess.run(argv, input=input, cwd=directory, env=env or self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=60, check=False)
        self.record(argv, directory, result, input)
        return result

    def record(self, argv, directory, result, input=b"", **extra):
        receipts = os.environ.get("NQL_CANONICAL_RECEIPTS")
        if receipts:
            receipt = Path(receipts) / (self._testMethodName + "-" + uuid.uuid4().hex)
            receipt.mkdir(parents=True)
            (receipt / "command.json").write_text(json.dumps({
                "argv": argv, "cwd": str(directory), "returncode": result.returncode,
                **extra,
            }, indent=2) + "\n")
            for name, data in (("stdin", input), ("stdout", result.stdout),
                               ("stderr", result.stderr)):
                (receipt / name).write_bytes(data)

    def preserve(self, name, path):
        receipts = os.environ.get("NQL_CANONICAL_RECEIPTS")
        if receipts:
            directory = Path(receipts) / "artifacts"
            directory.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, directory / name)

    def cli(self, *args, **kwargs):
        return self.command(ROOT / "nqlc", "--backend", "canonical", *args, **kwargs)

    def execute(self, path, **kwargs):
        runner = [] if platform.machine() == "x86_64" else ["qemu-x86_64"]
        return self.command(*runner, path, **kwargs)

    def test_real_compile_and_run(self):
        compiled = self.cli(self.source, "-o", self.output)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        self.assertEqual(compiled.stdout, b"")
        self.assertEqual(self.output.read_bytes()[:4], b"\x7fELF")
        executed = self.execute(self.output)
        self.assertEqual(executed.returncode, 23, executed.stderr)
        self.assertEqual(executed.stdout, b"canonical\n")
        self.assertEqual(executed.stderr, b"")
        self.preserve("real-program.elf", self.output)
        self.preserve("real-source.nql", self.source)
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_native_utility_check_compile_and_literal_arguments(self):
        self.source.write_bytes((ROOT / "examples/canonical/native_cat.nql").read_bytes())
        first, second = self.work / "binary input", self.work / "--backend=llvm"
        first.write_bytes(b"first\x00\xff\n")
        second.write_bytes(b"second\x80\n")
        expected = first.read_bytes() + b"stdin\x00" + second.read_bytes()
        for profile in ((), ("--compiler-profile",)):
            with self.subTest(profile=profile):
                self.assertEqual(self.cli(*profile, "--check", self.source).returncode, 0)
                compiled = self.cli(*profile, self.source, "-o", self.output)
                self.assertEqual((compiled.returncode, compiled.stdout, compiled.stderr), (0, b"", b""))
                result = self.cli(*profile, "--run", self.source, "--", "--",
                                  first.name, "-", second.name, input=b"stdin\x00")
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b""))
                runner = [] if platform.machine() == "x86_64" else ["qemu-x86_64"]
                executed = self.command(*runner, self.output, first.name)
                self.assertEqual((executed.returncode, executed.stdout, executed.stderr),
                                 (0, first.read_bytes(), b""))
                self.preserve("native-cat-profile" + str(bool(profile)) + ".elf", self.output)
                self.assertEqual(list(self.temps.iterdir()), [])

    def test_native_permission_diagnostic_preserves_output(self):
        self.source.write_text("fn main(){\nreturn byte_address(0,0)\n}\n")
        for flags in ((), ("--check",), ("--run",), ("--compiler-profile",)):
            with self.subTest(flags=flags):
                self.output.write_bytes(b"previous executable\x00")
                self.output.chmod(0o751)
                outputs = () if "--check" in flags else ("-o", self.output)
                rejected = self.cli(*flags, self.source, *outputs)
                self.assertEqual((rejected.returncode, rejected.stdout), (1, b""))
                self.assertIn(b"error[C0S-001]", rejected.stderr)
                self.assertIn(str(self.source).encode() + b":2:", rejected.stderr)
                self.assertEqual(self.output.read_bytes(), b"previous executable\x00")
                self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o751)
                self.assertEqual(list(self.temps.iterdir()), [])
                self.assertFalse(list(self.work.glob(".nqlc-canonical.*")))

    def test_matches_direct_wrapper_and_static_nx_elf(self):
        compiled = self.cli("-O0", "--no-std", self.source, "-o", self.output)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        direct = self.work / "direct"
        result = self.command(WRAPPER, self.source, direct)
        self.assertEqual(result.returncode, 0, result.stderr)
        image = self.output.read_bytes()
        self.assertEqual(image, direct.read_bytes())
        self.assertEqual(image[:7], b"\x7fELF\x02\x01\x01")
        header = struct.unpack_from("<HHIQQQIHHHHHH", image, 16)
        self.assertEqual(header[:3], (2, 62, 1))
        segments = [struct.unpack_from("<IIQQQQQQ", image, header[4] + i * header[8])
                    for i in range(header[9])]
        self.assertFalse(any(p[0] in (2, 3) for p in segments), "dynamic ELF")
        self.assertTrue(any(p[:2] == (1, 5) for p in segments), "missing RX load")
        self.assertTrue(any(p[:2] == (0x6474E551, 6) for p in segments), "executable stack")
        self.assertFalse(any(p[1] & 3 == 3 for p in segments), "RWX segment")
        self.preserve("direct-program.elf", direct)

    def test_check_compiles_semantics_without_running_or_leaving_output(self):
        checked = self.cli("--check", self.source)
        self.assertEqual((checked.returncode, checked.stdout, checked.stderr), (0, b"", b""))
        self.assertEqual(set(self.work.iterdir()), {self.source, self.temps})
        self.assertEqual(list(self.temps.iterdir()), [])
        self.source.write_text("fn main(){return missing}\n")
        rejected = self.cli("--check", self.source)
        self.assertEqual(rejected.returncode, 1, rejected.stderr)
        self.assertIn(b"[C0B-003]", rejected.stderr)
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_syntax_and_semantic_errors_keep_locations_and_prior_output(self):
        for source, code in (("fn main(){\n return (\n}\n", b"C0P-"),
                             ("fn main(){\n return missing\n}\n", b"C0B-003")):
            with self.subTest(code=code):
                self.source.write_text(source)
                self.output.write_bytes(b"previous output\x00")
                self.output.chmod(0o751)
                result = self.cli(self.source, "-o", self.output)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertIn(code, result.stderr)
                self.assertRegex(result.stderr, re.escape(str(self.source).encode()) +
                                 rb":[1-9][0-9]*:[1-9][0-9]*: error\[C0[PB]-")
                self.assertEqual(self.output.read_bytes(), b"previous output\x00")
                self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o751)
                self.assertFalse(list(self.work.glob(".c0-source.*")))
                self.assertEqual(list(self.temps.iterdir()), [])

    def test_outer_cleanup_failure_preserves_existing_output_and_mode(self):
        public, _ = self.installation(installed=True)
        self.source.write_text("fn main(){return 0}\n")
        original = b"previous executable bytes"
        self.output.write_bytes(original)
        self.output.chmod(0o751)
        stubs = self.work / "cleanup-failure"
        stubs.mkdir()
        marker = self.work / "blocked-cleanup"
        shim = stubs / "rm"
        shim.write_text('#!/bin/bash\n'
                        'if [[ "$#" == 3 && "$1" == -rf && "$2" == -- '
                        '&& "$3" == "$TMPDIR"/nqlc-canonical.* ]]; then\n'
                        '  printf "%s\\n" "$3" >> "$BLOCKED_CLEANUP"\n'
                        '  exit 19\nfi\nexec "$REAL_RM" "$@"\n')
        shim.chmod(0o755)
        env = dict(self.env, PATH=str(stubs) + os.pathsep + self.env["PATH"],
                   REAL_RM=shutil.which("rm"), BLOCKED_CLEANUP=str(marker))
        def identity():
            return {"sha256": hashlib.sha256(self.output.read_bytes()).hexdigest(),
                    "size": self.output.stat().st_size,
                    "mode": oct(stat.S_IMODE(self.output.stat().st_mode))}
        for run_flags in ((), ("--run",)):
            with self.subTest(flags=run_flags):
                self.output.write_bytes(original)
                self.output.chmod(0o751)
                marker.unlink(missing_ok=True)
                before = identity()
                argv = [str(public / "nqlc"), "--backend", "canonical", *run_flags,
                        str(self.source), "-o", str(self.output)]
                result = subprocess.run(argv, input=b"", cwd=self.work, env=env,
                                        capture_output=True, timeout=60)
                self.record(argv, self.work, result, output_before=before, output_after=identity(),
                            cleanup_injection=shim.read_text(),
                            blocked_cleanup=marker.read_text() if marker.exists() else "")
                self.assertTrue(marker.exists(), result.stderr)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(b"cannot remove temporary directory", result.stderr)
                self.assertEqual(self.output.read_bytes(), original)
                self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o751)
                self.assertFalse(list(self.work.glob(".nqlc-canonical.*")))

    def test_explicit_run_inherits_binary_streams_and_status(self):
        self.source.write_text("fn main(){let n=input_read(0,100) output_write(0,n) "
                               "error_write(0,n) return n}\n")
        payload = b"NolQu-L\x00\xff\n"
        result = self.cli("--run", self.source, input=payload)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (len(payload), payload, payload))
        self.assertEqual(set(self.work.iterdir()), {self.source, self.temps})
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_run_with_output_keeps_executable_and_alias_works(self):
        result = self.command(ROOT / "nolqulc", "--backend=canonical", "--run",
                              self.source, "-o", self.output)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (23, b"canonical\n", b""))
        self.assertTrue(os.access(self.output, os.X_OK))
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_implicit_run_matches_existing_default_output_behavior(self):
        result = self.cli(self.source)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (23, b"canonical\n", b""))
        self.assertTrue((self.work / "main").is_file())
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_runtime_fault_statuses_are_preserved(self):
        for source, status, code in (("fn main(){return 1/0}", 70, b"[C0R-001]"),
                                     ("fn main(){return input_read(0,1)}", 74, b"[C0R-005]")):
            with self.subTest(status=status):
                self.source.write_text(source)
                if status == 74:
                    # An unreadable stdin deterministically exercises the real EBADF path.
                    with open(os.devnull, "wb") as unreadable:
                        argv = [str(ROOT / "nqlc"), "--backend", "canonical", "--run", str(self.source)]
                        result = subprocess.run(argv, stdin=unreadable, capture_output=True,
                                                cwd=self.work, env=self.env, timeout=60)
                    self.record(argv, self.work, result, stdin_mode="unreadable fd")
                else:
                    result = self.cli("--run", self.source)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertIn(code, result.stderr)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(list(self.temps.iterdir()), [])

    def test_compiler_profile_is_explicit_and_default_remains_64k(self):
        # A large source must not silently opt into the 16 MiB profile.
        self.source.write_text("fn main(){byte_store(65536,42) return byte_load(65536)}" + " " * 9000)
        ordinary = self.cli("--run", self.source)
        self.assertEqual(ordinary.returncode, 70, ordinary.stderr)
        self.assertIn(b"[C0R-004]", ordinary.stderr)
        selected = self.cli("--compiler-profile", self.source, "-o", self.output)
        self.assertEqual(selected.returncode, 0, selected.stderr)
        direct = self.work / "direct-profile"
        direct_result = self.command(WRAPPER, "--compiler-profile", self.source, direct)
        self.assertEqual(direct_result.returncode, 0, direct_result.stderr)
        self.assertEqual(self.output.read_bytes(), direct.read_bytes())
        result = self.execute(self.output)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (42, b"", b""))
        self.assertEqual(self.cli("--compiler-profile", "--check", self.source).returncode, 0)

    def test_compiler_profile_is_rejected_by_default_backend(self):
        for backend in ([], ["--backend", "nasm"]):
            with self.subTest(backend=backend):
                result = self.command(ROOT / "nqlc", *backend, "--compiler-profile",
                                      self.source, "-o", self.output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"canonical", result.stderr)
                self.assertFalse(self.output.exists())

    def test_default_backend_keeps_runtime_response_file_expansion(self):
        self.source.write_text("print argc\n")
        arguments = self.work / "runtime-arguments.txt"
        arguments.write_text("one\ntwo\nthree\n")
        result = self.command(ROOT / "nqlc", "--run", self.source, "--", "@" + str(arguments))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"3\n", b""))

    def test_response_file_and_paths_with_spaces(self):
        source = self.work / "source with spaces.nql"
        self.source.rename(source)
        output = self.work / "output with spaces"
        flags = self.work / "flags with spaces.txt"
        flags.write_text(f"# flags\n--backend\ncanonical\n--run\n-o\n{output}\n{source}\n")
        result = self.command(ROOT / "nqlc", "@" + str(flags))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (23, b"canonical\n", b""))
        self.assertTrue(output.is_file())

    def test_verbose_time_quiet_and_dry_run(self):
        result = self.cli("-v", "--time", self.source, "-o", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"canonical", result.stderr)
        self.assertRegex(result.stderr, rb"total: [0-9]+ms")
        quiet = self.cli("-q", "--time", self.source, "-o", self.output)
        self.assertEqual((quiet.returncode, quiet.stdout, quiet.stderr), (0, b"", b""))
        self.output.unlink()
        dry = self.cli("--compiler-profile", "--run", "--dry-run", self.source,
                       "-o", self.output, "--", "space arg")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn(b"compile-source.sh", dry.stderr)
        self.assertIn(b"--compiler-profile", dry.stderr)
        self.assertIn(b"space", dry.stderr)
        self.assertEqual(dry.stdout, b"")
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_unsupported_options_fail_before_publication(self):
        options = [("-S",), ("-c",), ("--emit-ir",), ("--dump-ir",), ("--dump-ast",),
                   ("-g",), ("-O1",), ("-w",), ("-Werror",), ("-Wall",),
                   ("-Wno-todo",), ("--pedantic",), ("--save-temps",),
                   ("--error-format=json",), ("--max-errors=1",), ("-j", "2"),
                   ("-M",), ("--emit-ccdb",)]
        self.output.write_bytes(b"prior")
        self.output.chmod(0o750)
        for flags in options:
            with self.subTest(flags=flags):
                result = self.cli(*flags, self.source, "-o", self.output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(flags[0].split("=")[0].encode(), result.stderr)
                self.assertEqual(self.output.read_bytes(), b"prior")
                self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o750)
                self.assertEqual(list(self.temps.iterdir()), [])

    def test_dry_run_invokes_no_compiler_runtime_or_temporary_allocation(self):
        stubs = self.work / "dry-run-tools"
        stubs.mkdir()
        marker = self.work / "dry-run-called-tool"
        for name in ("sha256sum", "qemu-x86_64", "mktemp"):
            path = stubs / name
            path.write_text('#!/bin/sh\nprintf "%s\\n" "$0" >> "$DRY_RUN_CALLED"\nexit 99\n')
            path.chmod(0o755)
        env = dict(self.env, PATH=str(stubs) + os.pathsep + self.env["PATH"],
                   DRY_RUN_CALLED=str(marker))
        result = self.cli("--dry-run", "--compiler-profile", "--run", self.source, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"compile-source.sh", result.stderr)
        self.assertFalse(marker.exists(), marker.read_text() if marker.exists() else "")
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_rejects_invalid_inputs_targets_and_multiple_units(self):
        legacy = self.work / "legacy.nq"
        legacy.write_text("fn main(){return 0}\n")
        for args in ((legacy,), (self.work / "missing.nql",), ("-",),
                     (self.source, legacy), ("--target=arm64", self.source),
                     ("--check", self.source, "-o", self.output)):
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.output.exists())
                self.assertEqual(list(self.temps.iterdir()), [])

    def installation(self, *, installed=False):
        base = self.work / ("installed prefix" if installed else "repository copy")
        public = base / "bin" if installed else base
        assets = base / "lib/nolqu" if installed else base
        public.mkdir(parents=True, exist_ok=True)
        (assets / "tools").mkdir(parents=True, exist_ok=True)
        for name in ("nql", "nqlc"):
            shutil.copy2(ROOT / name, public / name)
        for name in ("VERSION", "CHANNEL"):
            shutil.copy2(ROOT / name, assets / name)
        for alias, target in (("nolqul", "nql"), ("nolqulc", "nqlc")):
            (public / alias).symlink_to(target)
        shutil.copytree(ROOT / "bootstrap", assets / "bootstrap")
        helper = ROOT / "tools/nql_c0_driver.sh"
        if helper.exists():
            shutil.copy2(helper, assets / "tools/nql_c0_driver.sh")
        return public, assets

    def test_relocated_install_uses_only_script_relative_canonical_assets(self):
        public, _ = self.installation(installed=True)
        env = dict(self.env, NOLQU_ROOT=str(ROOT))
        result = self.command(public / "nolqulc", "--backend", "canonical", self.source,
                              "-o", self.output, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        executed = self.execute(self.output)
        self.assertEqual((executed.returncode, executed.stdout), (23, b"canonical\n"))

    def test_repeated_hardlinks_keep_public_installation_discoverable(self):
        public, _ = self.installation(installed=True)
        for original, alias in ((public / "nqlc", self.work / "first-driver-link"),
                                ((public / "nolqulc").resolve(), self.work / "second-driver-link")):
            subprocess.run(["ln", "--", str(original), str(alias)],
                           check=True, capture_output=True, timeout=5)
        result = self.command(public / "nolqulc", "--backend", "canonical", self.source,
                              "-o", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        executed = self.execute(self.output)
        self.assertEqual((executed.returncode, executed.stdout), (23, b"canonical\n"))

    def test_pin_tampering_is_rejected_in_isolated_install(self):
        public, assets = self.installation(installed=True)
        stage = assets / "bootstrap/compiler/c0/x86_64-linux"
        self.output.write_bytes(b"prior")
        self.output.chmod(0o751)
        for name in ("c0-frontend.seed", "c0-backend.seed", "c0-frontend.sha256", "c0-backend.sha256"):
            with self.subTest(name=name):
                path = stage / name
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"tampered" if name.endswith("seed") else b"bad pin\n")
                    result = self.command(public / "nqlc", "--backend", "canonical",
                                          self.source, "-o", self.output)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertRegex(result.stderr, rb"hash mismatch|invalid manifest")
                    self.assertEqual(self.output.read_bytes(), b"prior")
                    self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o751)
                finally:
                    path.write_bytes(original)

    def test_output_aliases_of_sources_components_and_public_tools_are_rejected(self):
        for installed in (False, True):
            public, assets = self.installation(installed=installed)
            compiled = self.command(public / "nqlc", "--backend", "canonical",
                                    self.source, "-o", self.output)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            stage = assets / "bootstrap/compiler/c0/x86_64-linux"
            protected = [self.source, public / "nqlc", public / "nql", public / "nolqulc",
                         public / "nolqul", assets / "tools/nql_c0_driver.sh",
                         stage / "compile-source.sh", assets / "bootstrap/manifest.tsv",
                         assets / "bootstrap/compiler/c0/frontend.nql",
                         assets / "bootstrap/compiler/c0/backend.nql"]
            protected += [stage / ("c0-" + component + suffix)
                          for component in ("frontend", "backend") for suffix in (".seed", ".sha256")]
            for index, path in enumerate(protected):
                before = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
                for kind in ("direct", "symlink", "hardlink"):
                    with self.subTest(installed=installed, path=path, kind=kind):
                        alias = self.work / f"alias-{installed}-{index}-{kind}"
                        if kind == "symlink":
                            alias.symlink_to(path)
                        elif kind == "hardlink":
                            subprocess.run(["ln", "--", str(path.resolve()), str(alias)],
                                           check=True, capture_output=True, timeout=5)
                        else:
                            alias = path
                        result = self.command(public / "nqlc", "--backend", "canonical",
                                              self.source, "-o", alias)
                        self.assertNotEqual(result.returncode, 0, result.stderr)
                        self.assertIn(b"output would replace", result.stderr)
                        self.assertEqual((path.read_bytes(), stat.S_IMODE(path.stat().st_mode)), before)
                        if kind == "symlink":
                            self.assertTrue(alias.is_symlink())
                        if kind == "hardlink":
                            self.assertTrue(os.path.samefile(path, alias))

    def test_missing_canonical_components_do_not_fall_back(self):
        public, assets = self.installation(installed=True)
        for path in (assets / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed",
                     assets / "bootstrap/compiler/c0/x86_64-linux/compile-source.sh",
                     assets / "tools/nql_c0_driver.sh"):
            with self.subTest(path=path):
                hidden = path.with_name(path.name + ".hidden")
                path.rename(hidden)
                try:
                    result = self.command(public / "nqlc", "--backend", "canonical",
                                          self.source, "-o", self.output)
                    self.assertNotEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(self.output.exists())
                    self.assertNotIn(b"R0", result.stderr)
                finally:
                    hidden.rename(path)

    def test_returned_canonical_status_never_selects_r0(self):
        public, assets = self.installation(installed=True)
        # Negative dispatch test only: a broken helper must not select R0.
        (assets / "tools/nql_c0_driver.sh").write_text(
            "run_canonical_pipeline() { return 37; }\n")
        result = self.command(public / "nqlc", "--backend", "canonical",
                              self.source, "-o", self.output)
        self.assertEqual(result.returncode, 37, result.stderr)
        self.assertEqual((result.stdout, result.stderr), (b"", b""))
        self.assertFalse(self.output.exists())

    def test_compile_check_run_and_errors_with_forbidden_host_tools(self):
        stubs = self.work / "forbidden"
        stubs.mkdir()
        marker = self.work / "forbidden-called"
        for name in ("nasm", "ld", "x86_64-linux-gnu-ld", "clang", "clang++", "llc",
                     "llvm-as", "llvm-link", "gcc", "cc", "python", "python3", "nqlc-r0"):
            path = stubs / name
            path.write_text('#!/bin/sh\nprintf "%s\\n" "$0" >> "$FORBIDDEN_CALLED"\nexit 99\n')
            path.chmod(0o755)
        env = dict(self.env, PATH=str(stubs) + os.pathsep + self.env["PATH"],
                   FORBIDDEN_CALLED=str(marker))
        for flags in (("-o", self.output), ("--check",), ("--run",)):
            with self.subTest(flags=flags):
                result = self.cli(self.source, *flags, env=env)
                expected = (23, b"canonical\n", b"") if "--run" in flags else (0, b"", b"")
                self.assertEqual((result.returncode, result.stdout, result.stderr), expected)
                self.assertFalse(marker.exists(), marker.read_text() if marker.exists() else "")
        # Rejection of JSON itself must not invoke Python's generic diagnostic path.
        rejected = self.cli("--error-format=json", self.source, "-o", self.output, env=env)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(marker.exists())

    def descendants(self, pid):
        # Some Linux/proot installations expose stat but no task/children.
        # Derive the same real parent relationships without skipping checks.
        parents = {}
        for path in Path("/proc").glob("[0-9]*/stat"):
            try:
                text = path.read_text()
                fields = text[text.rfind(")") + 2:].split()
                parents.setdefault(int(fields[1]), []).append(int(path.parent.name))
            except (FileNotFoundError, ProcessLookupError):
                continue
        found = []
        pending = list(parents.get(pid, []))
        while pending:
            child = pending.pop()
            found.append(child)
            pending.extend(parents.get(child, []))
        return found

    def start_cli(self, *args, env=None):
        argv = [str(ROOT / "nqlc"), "--backend", "canonical", *map(str, args)]
        child = subprocess.Popen(argv, cwd=self.work, env=env or self.env,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        def emergency_cleanup():
            if child.poll() is None:
                child.send_signal(signal.SIGTERM)
                try:
                    child.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate(timeout=10)
            else:
                child.communicate(timeout=10)
        self.addCleanup(emergency_cleanup)
        return argv, child

    def controlling_terminal(self, action=None, *, wait_for_foreground=False, ready_path=None):
        """An outer session owner observes the real CLI's controlling PTY."""
        argv = [str(ROOT / "nqlc"), "--backend", "canonical", "--run", str(self.source)]
        bound_paths = [ROOT / "nqlc", ROOT / "tools/nql_c0_driver.sh", WRAPPER,
                       self.source, WRAPPER.parent / "c0-frontend.seed",
                       WRAPPER.parent / "c0-backend.seed"]
        session_utility = shutil.which("setsid", path=self.env["PATH"])
        if session_utility:
            bound_paths.append(Path(session_utility))
        bindings = {str(path): {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                               "size": path.stat().st_size,
                               "mode": oct(stat.S_IMODE(path.stat().st_mode))}
                    for path in bound_paths}
        source_text = self.source.read_text()
        def snapshot(pid):
            directory = Path(f"/proc/{pid}")
            text = (directory / "stat").read_text()
            fields = text[text.rfind(")") + 2:].split()
            return {"pid": pid, "state": fields[0], "parent": int(fields[1]),
                    "pgrp": int(fields[2]), "session": int(fields[3]),
                    "tty": int(fields[4]), "foreground": int(fields[5]),
                    "argv": [p.decode(errors="replace") for p in
                             (directory / "cmdline").read_bytes().split(b"\0")[:-1]],
                    "stdin": os.readlink(directory / "fd/0"),
                    "signals": [line for line in (directory / "status").read_text().splitlines()
                                if line.startswith(("SigBlk:", "SigIgn:", "SigCgt:"))]}
        master, slave = pty.openpty()
        attributes = termios.tcgetattr(slave)
        attributes[1] &= ~termios.ONLCR
        attributes[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, attributes)
        meta_r, meta_w = os.pipe()
        error_r, error_w = os.pipe()
        control_r, control_w = os.pipe()
        gate_r, gate_w = os.pipe()
        supervisor = os.fork()
        if supervisor == 0:
            driver = None
            try:
                for fd in (master, meta_r, error_r, control_w):
                    os.close(fd)
                os.setsid()
                fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
                signal.signal(signal.SIGTTOU, signal.SIG_IGN)
                owner = os.getpgrp()
                os.tcsetpgrp(slave, owner)
                def event(kind, **data):
                    os.write(meta_w, (json.dumps(dict(kind=kind, **data)) + "\n").encode())
                driver = os.fork()
                if driver == 0:
                    os.close(meta_w)
                    os.close(control_r)
                    os.close(gate_w)
                    os.setpgid(0, 0)
                    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM,
                                signal.SIGTTIN, signal.SIGTTOU, signal.SIGTSTP):
                        signal.signal(sig, signal.SIG_DFL)
                    os.dup2(slave, 0)
                    os.dup2(slave, 1)
                    os.dup2(error_w, 2)
                    if os.read(gate_r, 1) != b"g":
                        os._exit(125)
                    os.chdir(self.work)
                    os.execve(argv[0], argv, self.env)
                os.close(gate_r)
                os.setpgid(driver, driver)
                os.tcsetpgrp(slave, driver)
                event("start", supervisor=owner, driver=driver, session=os.getsid(0),
                      tty=os.ttyname(slave), stdin_isatty=os.isatty(slave),
                      foreground=os.tcgetpgrp(slave))
                os.write(gate_w, b"g")
                os.close(gate_w)
                observe_requested = False
                last_foreground = driver
                while True:
                    if select.select([control_r], [], [], 0.01)[0]:
                        if os.read(control_r, 1) == b"O":
                            observe_requested = True
                    if observe_requested and (not wait_for_foreground or os.tcgetpgrp(slave) != driver):
                        mode = termios.tcgetattr(slave)
                        event("observed", foreground=os.tcgetpgrp(slave),
                              local_flags=mode[3], intr=mode[6][termios.VINTR].hex())
                        observe_requested = False
                    foreground = os.tcgetpgrp(slave)
                    if foreground != last_foreground:
                        event("foreground", foreground=foreground)
                        last_foreground = foreground
                    done, status = os.waitpid(driver, os.WNOHANG | os.WUNTRACED)
                    if done and os.WIFSTOPPED(status):
                        event("stopped", signal=os.WSTOPSIG(status), foreground=os.tcgetpgrp(slave))
                        continue
                    if done:
                        break
                before = os.tcgetpgrp(slave)
                os.tcsetpgrp(slave, owner)
                event("finish", returncode=os.waitstatus_to_exitcode(status),
                      foreground_before_reclaim=before,
                      foreground_after_reclaim=os.tcgetpgrp(slave))
                os._exit(0)
            except BaseException as exc:
                try:
                    os.write(meta_w, (json.dumps({"kind": "error", "error": repr(exc)}) + "\n").encode())
                    if driver:
                        os.killpg(driver, signal.SIGKILL)
                        os.waitpid(driver, 0)
                finally:
                    os._exit(125)
        for fd in (slave, meta_w, error_w, control_r, gate_r, gate_w):
            os.close(fd)
        events, processes = [], []
        out, err, metadata = bytearray(), bytearray(), bytearray()
        opened = {master, meta_r, error_r}
        requested = acted = timed_out = False
        start = finish = observed = None
        payload = b"Z\n" if action is None else b"\x03" if action == "terminal-int" else b""
        deadline = time.monotonic() + 30
        try:
            while opened and time.monotonic() < deadline:
                for fd in select.select(list(opened), [], [], 0.05)[0]:
                    try:
                        data = os.read(fd, 65536)
                    except OSError as exc:
                        if exc.errno != errno.EIO:
                            raise
                        data = b""
                    if not data:
                        opened.remove(fd)
                    elif fd == master:
                        out.extend(data)
                    elif fd == error_r:
                        err.extend(data)
                    else:
                        metadata.extend(data)
                        while b"\n" in metadata:
                            line, _, rest = metadata.partition(b"\n")
                            metadata = bytearray(rest)
                            entry = json.loads(line)
                            events.append(entry)
                            if entry["kind"] == "start":
                                start = entry
                            elif entry["kind"] == "observed":
                                observed = entry
                            elif entry["kind"] == "finish":
                                finish = entry
                if (b"ready\n" in out or ready_path and ready_path.exists()) and not requested:
                    requested = True
                    try:
                        os.write(control_w, b"O")
                    except BrokenPipeError:
                        pass
                if requested and (observed or finish) and not acted:
                    acted = True
                    if start:
                        for pid in self.descendants(start["driver"]):
                            try:
                                processes.append(snapshot(pid))
                            except (ProcessLookupError, FileNotFoundError):
                                pass
                    if payload:
                        os.write(master, payload)
                    elif start:
                        try:
                            os.kill(start["driver"], action)
                        except ProcessLookupError:
                            pass
                    deadline = time.monotonic() + 8
            timed_out = bool(opened)
            if timed_out:
                state = []
                for pid in self.descendants(supervisor):
                    try:
                        state.append(snapshot(pid))
                    except (ProcessLookupError, FileNotFoundError):
                        pass
                events.append({"kind": "timeout", "processes": state})
        finally:
            # On a failing regression, terminate only this test's descendants.
            groups = set()
            for pid in self.descendants(supervisor):
                try:
                    groups.add(os.getpgid(pid))
                except ProcessLookupError:
                    pass
            if timed_out:
                groups.add(supervisor)
            for group in groups:
                if group != os.getpgrp():
                    try:
                        os.killpg(group, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            os.waitpid(supervisor, 0)
            for fd in (master, meta_r, error_r, control_w):
                os.close(fd)
        code = finish["returncode"] if finish and not timed_out else 124
        result = subprocess.CompletedProcess(argv, code, bytes(out), bytes(err))
        self.record(argv, self.work, result, input=payload, controlling_pty=True,
                    events=events, runtime_processes=processes, timed_out=timed_out,
                    executed_file_identities=bindings, source_text=source_text,
                    session_utility=session_utility,
                    remaining_owned_pids=[p["pid"] for p in processes if Path(f"/proc/{p['pid']}").exists()],
                    remaining_temporary_paths=[str(p) for p in self.temps.iterdir()],
                    driver_signal=int(action) if isinstance(action, signal.Signals) else action)
        return result, start, observed, finish, processes

    def test_controlling_terminal_input_and_foreground_restored(self):
        self.source.write_text(TTY_SOURCE)
        result, start, observed, finish, processes = self.controlling_terminal()
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (23, b"ready\nZ\n", b""))
        self.assertTrue(start["stdin_isatty"])
        self.assertEqual(observed["foreground"], start["driver"])
        self.assertEqual(len(processes), 1, processes)
        native = processes[0]
        self.assertEqual((native["parent"], native["stdin"], native["tty"]),
                         (start["driver"], start["tty"], 0))
        self.assertEqual((native["session"], native["pgrp"]), (native["pid"], native["pid"]))
        self.assertEqual(finish["foreground_before_reclaim"], start["driver"])
        self.assertEqual(finish["foreground_after_reclaim"], start["supervisor"])
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_controlling_terminal_ownership_and_cleanup_on_signals(self):
        self.source.write_text(TTY_SOURCE)
        for action, status in ((signal.SIGHUP, 129), (signal.SIGINT, 130),
                               (signal.SIGTERM, 143), ("terminal-int", 130)):
            with self.subTest(action=action):
                result, start, observed, finish, processes = self.controlling_terminal(action)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertEqual((result.stdout, result.stderr), (b"ready\n", b""))
                self.assertEqual(observed["foreground"], start["driver"])
                self.assertEqual(len(processes), 1, processes)
                self.assertEqual(processes[0]["parent"], start["driver"])
                self.assertEqual((processes[0]["session"], processes[0]["pgrp"]),
                                 (processes[0]["pid"], processes[0]["pid"]))
                self.assertEqual(finish["foreground_before_reclaim"], start["driver"])
                self.assertEqual(finish["foreground_after_reclaim"], start["supervisor"])
                self.assertTrue(all(not Path(f"/proc/{p['pid']}").exists() for p in processes))
                self.assertEqual(list(self.temps.iterdir()), [])

    def test_fast_terminal_program_keeps_status_and_foreground(self):
        self.source.write_text("fn main(){return 23}\n")
        result, start, _, finish, _ = self.controlling_terminal()
        self.assertEqual((result.returncode, result.stdout, result.stderr), (23, b"", b""))
        self.assertEqual(finish["foreground_before_reclaim"], start["driver"])
        self.assertEqual(finish["foreground_after_reclaim"], start["supervisor"])
        self.assertEqual(list(self.temps.iterdir()), [])

    def path_without_setsid(self):
        directory = self.work / "without-setsid"
        directory.mkdir()
        for name in ("bash", "readlink", "dirname", "head", "tr", "date", "uname", "mktemp",
                     "sha256sum", "cat", "chmod", "rm", "rmdir", "mv", "qemu-x86_64"):
            target = shutil.which(name)
            if target:
                (directory / name).symlink_to(target)
        self.assertIsNone(shutil.which("setsid", path=str(directory)))
        return dict(self.env, PATH=str(directory))

    def test_missing_setsid_rejects_terminal_run_without_fallback(self):
        self.env = self.path_without_setsid()
        self.source.write_text(TTY_SOURCE)
        result, start, _, finish, processes = self.controlling_terminal()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(b"setsid (util-linux) is required", result.stderr)
        self.assertNotIn(b"R0", result.stderr)
        self.assertEqual((result.stdout, processes), (b"", []))
        self.assertEqual(finish["foreground_before_reclaim"], start["driver"])
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_setsid_not_required_for_compile_check_or_piped_run(self):
        env = self.path_without_setsid()
        for flags, status, out in ((("-o", self.output), 0, b""),
                                  (("--check",), 0, b""),
                                  (("--run",), 23, b"canonical\n")):
            with self.subTest(flags=flags):
                result = self.cli(self.source, *flags, env=env)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (status, out, b""))

    def test_terminal_signal_before_setsid_establishes_its_group(self):
        self.source.write_text(TTY_SOURCE)
        directory = self.work / "delayed-setsid"
        directory.mkdir()
        marker = self.work / "setsid-started"
        gate = self.work / "setsid-gate"
        os.mkfifo(gate)
        shim = directory / "setsid"
        shim.write_text('#!/bin/bash\nprintf "%s\\n" "$BASHPID" > "$SETSID_STARTED"\n'
                        'IFS= read -r token < "$SETSID_GATE"\nexec "$REAL_SETSID" "$@"\n')
        shim.chmod(0o755)
        self.env.update(REAL_SETSID=shutil.which("setsid"), SETSID_STARTED=str(marker),
                        SETSID_GATE=str(gate),
                        PATH=str(directory) + os.pathsep + self.env["PATH"])
        for sig, status in ((signal.SIGHUP, 129), (signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(signal=sig):
                marker.unlink(missing_ok=True)
                result, start, observed, finish, processes = self.controlling_terminal(sig, ready_path=marker)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertTrue(all(not Path(f"/proc/{p['pid']}").exists() for p in processes))
                self.assertEqual(list(self.temps.iterdir()), [])
                self.assertEqual(observed["foreground"], start["driver"])
                self.assertEqual(len(processes), 1, processes)
                self.assertEqual(processes[0]["pid"], int(marker.read_text()))
                self.assertEqual(processes[0]["pgrp"], start["driver"])
                self.assertEqual(processes[0]["session"], start["session"])
                self.assertIn(str(shim), processes[0]["argv"])
                self.assertEqual(finish["foreground_before_reclaim"], start["driver"])

    def await_condition(self, predicate, message):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            value = predicate()
            if value:
                return value
            time.sleep(0.02)
        self.fail(message)

    def test_runtime_arguments_after_double_dash_are_verbatim(self):
        self.source.write_text(READY_SOURCE)
        arguments = ["space arg", "", "@literal-response", "--flag"]
        argv, child = self.start_cli("--run", self.source, "--", *arguments)
        self.assertTrue(select.select([child.stdout], [], [], 15)[0], "program did not start")
        ready = child.stdout.read(6)
        self.assertEqual(ready, b"ready\n")
        processes = [Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")[:-1]
                     for pid in self.descendants(child.pid)]
        self.assertTrue(any(cmd[-4:] == [arg.encode() for arg in arguments] for cmd in processes), processes)
        out, err = child.communicate(b"x", timeout=15)
        result = subprocess.CompletedProcess(argv, child.returncode, ready + out, err)
        self.record(argv, self.work, result, input=b"x", observed_process_arguments=[
            [part.decode(errors="replace") for part in cmd] for cmd in processes])
        self.assertEqual((child.returncode, ready + out, err), (1, b"ready\n", b""))
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_signals_reap_real_runtime_and_remove_temporary_output(self):
        self.source.write_text(READY_SOURCE)
        for sig, expected in ((signal.SIGHUP, 129), (signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(signal=sig):
                argv, child = self.start_cli("--run", self.source)
                self.assertTrue(select.select([child.stdout], [], [], 15)[0], "program did not start")
                ready = child.stdout.read(6)
                self.assertEqual(ready, b"ready\n")
                owned = self.descendants(child.pid)
                self.assertTrue(owned)
                child.send_signal(sig)
                out, err = child.communicate(timeout=15)
                result = subprocess.CompletedProcess(argv, child.returncode, ready + out, err)
                self.record(argv, self.work, result, signal=int(sig), owned_pids=owned)
                self.assertEqual(child.returncode, expected, err)
                self.assertTrue(all(not Path(f"/proc/{pid}").exists() for pid in owned), owned)
                self.assertEqual(list(self.temps.iterdir()), [])

    def test_signals_reap_compiler_wrapper_descendants_and_candidates(self):
        # Delay chmod after actual pinned compilation, so wrapper workspace,
        # candidate and an owned grandchild all exist when interrupted.
        stubs = self.work / "delay"
        stubs.mkdir()
        marker = self.work / "chmod-active"
        delay = stubs / "chmod"
        delay.write_text('#!/bin/bash\nprintf "%s\\n" "$$" > "$CHMOD_ACTIVE"\nsleep 30 &\nwait\n')
        delay.chmod(0o755)
        env = dict(self.env, PATH=str(stubs) + os.pathsep + self.env["PATH"], CHMOD_ACTIVE=str(marker))
        for sig, expected in ((signal.SIGHUP, 129), (signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(signal=sig):
                marker.unlink(missing_ok=True)
                argv, child = self.start_cli("--check", self.source, env=env)
                self.await_condition(marker.exists, "wrapper did not reach chmod")
                owned = self.descendants(child.pid)
                self.assertGreaterEqual(len(owned), 3)
                child.send_signal(sig)
                out, err = child.communicate(timeout=15)
                result = subprocess.CompletedProcess(argv, child.returncode, out, err)
                self.record(argv, self.work, result, signal=int(sig), owned_pids=owned)
                self.assertEqual(child.returncode, expected, err)
                self.await_condition(lambda: all(not Path(f"/proc/{pid}").exists() for pid in owned),
                                     f"owned descendants remain: {owned}")
                self.assertEqual(list(self.temps.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
