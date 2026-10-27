"""Real C0 project/install integration; no bootstrap generation or host compiler."""

import hashlib
import json
import os
import platform
from pathlib import Path
import select
import shlex
import shutil
import signal
import stat
import subprocess
import tempfile
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
C0 = Path("bootstrap/compiler/c0/x86_64-linux")
HELLO = b"Hello, World!\n"
READY = ("fn main(){byte_store(0,114) byte_store(1,101) byte_store(2,97) "
         "byte_store(3,100) byte_store(4,121) byte_store(5,10) "
         "output_write(0,6) return input_read(0,1)}\n")


class CanonicalProjectTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="canonical-project-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.temps = self.work / "temporary files"
        self.temps.mkdir()
        self.tool = self.work / "tool source"
        self.tool.mkdir()
        for name in ("nql", "nqlc", "install.sh", "VERSION"):
            shutil.copy2(ROOT / name, self.tool / name)
        for name in ("bootstrap", "tools", "src"):
            shutil.copytree(ROOT / name, self.tool / name)
        (self.tool / "build").mkdir()
        if (ROOT / "build/nqlc-r0").exists():
            shutil.copy2(ROOT / "build/nqlc-r0", self.tool / "build/nqlc-r0")
        for alias, primary in (("nolqul", "nql"), ("nolqulc", "nqlc")):
            (self.tool / alias).symlink_to(primary)
        self.env = os.environ.copy()
        for name in ("NOLQU_ROOT", "NOLQUC_MAX_ERRORS", "PREFIX", "DESTDIR", "NQL_HOME"):
            self.env.pop(name, None)
        self.env.update(TMPDIR=str(self.temps), NO_COLOR="1", NOLQUC_COLOR="never")
        self.app = self.work / "app"

    def record(self, argv, cwd, result, payload=b"", **extra):
        receipts = os.environ.get("NQL_PROJECT_RECEIPTS")
        if receipts:
            path = Path(receipts) / (self._testMethodName + "-" + uuid.uuid4().hex)
            path.mkdir(parents=True)
            (path / "command.json").write_text(json.dumps({
                "argv": [str(a) for a in argv], "cwd": str(cwd),
                "returncode": result.returncode, **extra,
            }, indent=2) + "\n")
            for name, data in (("stdin", payload), ("stdout", result.stdout),
                               ("stderr", result.stderr)):
                (path / name).write_bytes(data)

    def command(self, *argv, cwd=None, env=None, payload=b""):
        cwd = cwd or self.work
        argv = [str(a) for a in argv]
        result = subprocess.run(argv, cwd=cwd, env=env or self.env, input=payload,
                                capture_output=True, timeout=60)
        self.record(argv, cwd, result, payload)
        return result

    def nql(self, *args, **kwargs):
        return self.command(self.tool / "nql", *args, **kwargs)

    def execute(self, path, **kwargs):
        runner = [] if platform.machine() == "x86_64" else ["qemu-x86_64"]
        return self.command(*runner, path, **kwargs)

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def project(self, source="fn main(){return 0}\n", backend="canonical"):
        (self.app / "src").mkdir(parents=True)
        (self.app / "tests").mkdir()
        (self.app / "src/main.nql").write_text(source)
        self.manifest(backend)
        return self.app

    def manifest(self, backend="canonical", extra=""):
        (self.app / "nql.toml").write_text(
            '[package]\nname = "app"\nversion = "0.0.0"\n\n'
            '[build]\nbackend = "' + backend + '"\n' + extra)

    @property
    def binary(self):
        return self.app / ".nql/build/app"

    def build(self, *args):
        return self.nql("build", *args, cwd=self.app)

    def assert_cached(self, result):
        self.ok(result)
        self.assertIn(b"cached", result.stderr.lower())
        self.assertNotIn(b"0ms", result.stderr)

    def assert_compiled(self, result):
        self.ok(result)
        self.assertIn(b"Compiling", result.stderr)
        self.assertNotIn(b"cached", result.stderr.lower())

    def test_init_real_canonical_lifecycle(self):
        self.ok(self.nql("init", "app", "--backend", "canonical"))
        self.assertIn('backend = "canonical"', (self.app / "nql.toml").read_text())
        self.assertTrue((self.app / "tests/smoke.nql").is_file())
        self.ok(self.nql("check", cwd=self.app))
        self.assertFalse(self.binary.exists())
        self.assert_compiled(self.build())
        self.assertEqual(self.binary.read_bytes()[:4], b"\x7fELF")
        self.assertEqual(self.ok(self.execute(self.binary)).stdout, HELLO)
        self.assert_cached(self.build())
        self.assertEqual(self.ok(self.nql("run", cwd=self.app)).stdout, HELLO)
        tested = self.ok(self.nql("test", cwd=self.app))
        self.assertIn(b"test tests/smoke.nql ... ok", tested.stderr)

    def test_native_invariant_edit_invalidates_cache(self):
        valid = "fn main(){let p=0 unsafe {# safety: owned bounded empty span\np=byte_address(0,0)}return p==0}\n"
        self.project(valid)
        self.assert_compiled(self.build())
        self.assert_cached(self.build())
        original = self.binary.read_bytes()
        mode = stat.S_IMODE(self.binary.stat().st_mode)
        (self.app / "src/main.nql").write_text(valid.replace("# safety: owned bounded empty span", "# omitted invariant"))
        rejected = self.build()
        self.assertEqual(rejected.returncode, 1, rejected.stderr)
        self.assertIn(b"[C0P-014]", rejected.stderr)
        self.assertNotIn(b"cached", rejected.stderr.lower())
        self.assertEqual((self.binary.read_bytes(), stat.S_IMODE(self.binary.stat().st_mode)), (original, mode))
        (self.app / "src/main.nql").write_text(valid)
        self.assert_cached(self.build())
        self.assertEqual(self.ok(self.execute(self.binary)).stdout, b"")

    def test_native_project_binary_files_and_profile_cache(self):
        self.project((ROOT / "examples/canonical/native_cat.nql").read_text())
        data = b"project\x00\xff\n"
        (self.app / "literal file").write_bytes(data)
        for flags in ((), ("--compiler-profile",)):
            with self.subTest(flags=flags):
                self.ok(self.nql("check", *flags, cwd=self.app))
                self.assert_compiled(self.build(*flags))
                self.assert_cached(self.build(*flags))
                result = self.nql("run", *flags, "--", "literal file", "-", cwd=self.app, payload=b"stdin\x80")
                self.assertEqual((result.returncode, result.stdout), (0, data + b"stdin\x80"), result.stderr)
        self.ok(self.nql("clean", cwd=self.app))
        self.assertFalse((self.app / ".nql").exists())
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_default_template_and_alias_stay_legacy(self):
        self.ok(self.command(self.tool / "nolqul", "init", "app"))
        self.assertIn("func main()", (self.app / "src/main.nql").read_text())
        self.assertNotIn('backend = "canonical"', (self.app / "nql.toml").read_text())
        self.assertFalse((self.app / "tests/smoke.nql").exists())
        self.ok(self.command(self.tool / "nolqul", "build", cwd=self.app))
        self.assertEqual(self.ok(self.command(self.tool / "nolqul", "run", cwd=self.app)).stdout,
                         HELLO)

    def test_manifest_selection_is_scoped_and_options_override(self):
        self.project()
        self.manifest(extra='\n[dependencies]\nbackend = "unrelated"\n')
        self.assert_compiled(self.build())
        self.manifest("nasm")
        self.assert_compiled(self.build("--backend=canonical"))
        self.assert_cached(self.build("--backend", "canonical"))
        rejected = self.build()
        self.assertNotEqual(rejected.returncode, 0)
        self.assertNotIn(b"cached", rejected.stderr.lower())
        self.assertEqual(self.binary.read_bytes()[:4], b"\x7fELF")
        (self.app / "src/main.nql").write_text('print "legacy"\n')
        self.assert_compiled(self.build())
        self.assertEqual(self.ok(self.execute(self.binary)).stdout, b"legacy\n")
        self.assert_cached(self.build())

    def test_manifest_missing_backend_retains_default(self):
        self.project('print "legacy"\n')
        (self.app / "nql.toml").write_text('[package]\nname = "app"\n[build]\n')
        self.assert_compiled(self.build())
        self.assertEqual(self.ok(self.execute(self.binary)).stdout, b"legacy\n")

    def test_invalid_duplicate_and_missing_selection_fail(self):
        self.project()
        for extra in ('backend = "canonical"\n', '[build]\nbackend = "nasm"\n'):
            with self.subTest(extra=extra):
                self.manifest(extra=extra)
                result = self.build("--backend", "canonical")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"duplicate", result.stderr.lower())
        for backend in ("unknown", "llvm", "", "canonical extra"):
            with self.subTest(backend=backend):
                self.manifest(backend)
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"backend", result.stderr)
        self.manifest()
        for args in (("--backend",), ("--backend", "bogus"),
                     ("--backend=canonical", "--backend", "canonical")):
            with self.subTest(args=args):
                self.assertNotEqual(self.build(*args).returncode, 0)
        self.assertFalse(self.binary.exists())

    def test_profile_and_backend_are_propagated_to_all_commands(self):
        self.project("fn main(){byte_store(65536,65) output_write(65536,1) return 0}\n", "nasm")
        (self.app / "tests/smoke.nql").write_text((self.app / "src/main.nql").read_text())
        for cmd in ("build", "check", "run", "test"):
            with self.subTest(command=cmd):
                result = self.nql(cmd, "--backend", "canonical", "--compiler-profile", cwd=self.app)
                self.ok(result)
                if cmd == "run":
                    self.assertEqual(result.stdout, b"A")
        self.assertNotEqual(self.build("--compiler-profile").returncode, 0)
        self.assertNotEqual(self.build("--backend", "canonical", "--release").returncode, 0)

    def test_profile_changes_cache_and_actual_elf_memory(self):
        self.project("fn main(){byte_store(65536,65) output_write(65536,1) return 0}\n")
        images = []
        for flags in ((), ("--compiler-profile",), ()):
            self.assert_compiled(self.build(*flags))
            images.append(self.binary.read_bytes())
            executed = self.execute(self.binary)
            self.assertEqual(executed.returncode, 0 if flags else 70, executed.stderr)
            self.assertEqual(executed.stdout, b"A" if flags else b"")
            self.assert_cached(self.build(*flags))
        self.assertEqual(images[0], images[2])
        self.assertNotEqual(images[0], images[1])

    def test_multisource_build_and_check_are_rejected_before_publication(self):
        self.project()
        self.ok(self.build())
        before = self.binary.read_bytes()
        (self.app / "src/second.nql").write_text("fn other(){return 0}\n")
        for cmd in ("build", "check", "run"):
            with self.subTest(command=cmd):
                result = self.nql(cmd, cwd=self.app)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"one compilation unit", result.stderr)
                self.assertEqual(self.binary.read_bytes(), before)

    def test_check_runs_semantics_and_preserves_binary_on_failure(self):
        self.project()
        self.ok(self.build())
        before = self.binary.read_bytes()
        self.binary.chmod(0o751)
        (self.app / "src/main.nql").write_text("fn main(){return missing}\n")
        for cmd in ("check", "build", "run"):
            with self.subTest(command=cmd):
                result = self.nql(cmd, cwd=self.app)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(b"C0B-003", result.stderr)
                self.assertIn(str(self.app / "src/main.nql").encode(), result.stderr)
                self.assertEqual(self.binary.read_bytes(), before)
                self.assertEqual(stat.S_IMODE(self.binary.stat().st_mode), 0o751)
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_nested_tests_and_failure_status(self):
        self.project()
        for directory in ("one", "two"):
            (self.app / "tests" / directory).mkdir()
            (self.app / "tests" / directory / "smoke.nql").write_text("fn main(){return 0}\n")
        result = self.ok(self.nql("test", cwd=self.app))
        for directory in ("one", "two"):
            self.assertIn(f"test tests/{directory}/smoke.nql ... ok".encode(), result.stderr)
        (self.app / "tests/two/smoke.nql").write_text("fn main(){return 23}\n")
        result = self.nql("test", cwd=self.app)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"1 test(s) failed", result.stderr)
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_cache_invalidates_source_manifest_and_drivers(self):
        self.project()
        self.ok(self.build())
        paths = [self.app / "src/main.nql", self.app / "nql.toml", self.tool / "nql",
                 self.tool / "nqlc", self.tool / "tools/nql_c0_driver.sh",
                 self.tool / C0 / "compile-source.sh", self.tool / "bootstrap/manifest.tsv",
                 self.tool / "bootstrap/compiler/c0/frontend.nql",
                 self.tool / "bootstrap/compiler/c0/backend.nql"]
        for path in paths:
            with self.subTest(path=path.relative_to(self.work)):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assert_compiled(self.build())
                self.assert_cached(self.build())

    def test_cache_validates_pin_seed_presence_and_component_modes(self):
        self.project()
        self.ok(self.build())
        for name in ("c0-frontend.sha256", "c0-backend.sha256"):
            pin = self.tool / C0 / name
            pin.write_bytes(pin.read_bytes() + b"\n")
            self.assert_compiled(self.build())
        paths = [self.tool / "tools/nql_c0_driver.sh", self.tool / C0 / "compile-source.sh",
                 self.tool / C0 / "c0-frontend.seed", self.tool / C0 / "c0-backend.seed",
                 self.tool / C0 / "c0-frontend.sha256", self.tool / C0 / "c0-backend.sha256"]
        for path in paths:
            with self.subTest(missing=path.name):
                moved = path.with_name(path.name + ".absent")
                path.rename(moved)
                result = self.build()
                self.assertNotEqual(result.returncode, 0, result.stderr)
                self.assertNotIn(b"cached", result.stderr.lower())
                moved.rename(path)
                self.assert_cached(self.build())
        for name in ("compile-source.sh", "c0-frontend.seed", "c0-backend.seed"):
            path = self.tool / C0 / name
            mode = path.stat().st_mode
            path.chmod(0o644)
            result = self.build()
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(b"cached", result.stderr.lower())
            path.chmod(stat.S_IMODE(mode))
            self.assert_cached(self.build())
        for name in ("c0-frontend.sha256", "c0-backend.seed"):
            path = self.tool / C0 / name
            before = path.read_bytes()
            path.write_bytes((b"0" * 64 + before[64:]) if name.endswith("sha256") else before + b"x")
            result = self.build()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"hash mismatch", result.stderr)
            path.write_bytes(before)
            self.assert_cached(self.build())

    def test_cache_validates_output_bytes_and_mode(self):
        self.project()
        self.ok(self.build())
        image = self.binary.read_bytes()
        self.binary.write_bytes(image + b"tampered")
        self.assert_compiled(self.build())
        self.assertEqual(self.binary.read_bytes(), image)
        for mode in (0o644, 0o751):
            self.binary.chmod(mode)
            self.assert_compiled(self.build())
            self.assertEqual(stat.S_IMODE(self.binary.stat().st_mode), 0o755)
        self.binary.unlink()
        self.assert_compiled(self.build())

    def test_cache_write_failure_is_advisory(self):
        self.project()
        state = self.app / ".nql"
        state.mkdir()
        (state / "cache").write_text("cannot be a directory")
        self.assert_compiled(self.build())
        self.ok(self.execute(self.binary))
        self.assert_compiled(self.build())

    def test_source_forms_preserve_status_and_streams(self):
        source = self.work / "source space.nql"
        source.write_text("fn main(){let n=input_read(0,100) output_write(0,n) error_write(0,n) return n}\n")
        payload = b"stream\x00\xff\n"
        for args in ((source, "--backend", "canonical"),
                     ("run", source, "--backend=canonical"),
                     ("--backend", "canonical", "--run", source)):
            with self.subTest(args=args):
                result = self.nql(*args, payload=payload)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (len(payload), payload, payload))
        result = self.nql("check", source, "--backend", "canonical", payload=payload)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_leading_options_project_run_check_dispatch_matrix(self):
        self.project()
        cases = (
            ("nasm", ("--backend", "canonical")),
            ("canonical", ("--backend=canonical",)),
            ("canonical", ("--compiler-profile",)),
            ("nasm", ("--compiler-profile", "--backend", "canonical")),
            ("canonical", ("-q", "--color", "never", "--target", "x86_64-linux",
                           "--compiler-profile")),
        )
        for manifest_backend, prefix in cases:
            self.manifest(manifest_backend)
            offset = 65536 if "--compiler-profile" in prefix else 0
            (self.app / "src/main.nql").write_text(
                f"fn main(){{byte_store({offset},65) output_write({offset},1) return 0}}\n")
            for cmd in ("check", "run"):
                with self.subTest(command=cmd, prefix=prefix, manifest=manifest_backend):
                    result = self.ok(self.nql(*prefix, cmd, cwd=self.app))
                    self.assertEqual(result.stdout, b"A" if cmd == "run" else b"")
        self.manifest("nasm")
        for cmd in ("check", "run"):
            with self.subTest(command=cmd, manifest="nasm", missing_backend=True):
                result = self.nql("--compiler-profile", cmd, cwd=self.app)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(b"--compiler-profile requires --backend canonical", result.stderr)
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_leading_options_source_run_check_dispatch_matrix(self):
        source = self.work / "source space.nql"
        source.write_text("fn main(){return 0}\n")
        cases = (
            (("--backend", "canonical"), ()),
            (("--compiler-profile", "--backend=canonical"), ()),
            (("--compiler-profile", "-q"), ("--backend", "canonical")),
            (("-v", "--target", "x86_64-linux", "--color", "never",
              "--backend=canonical"), ()),
            (("--backend", "canonical"), ("--compiler-profile",)),
            ((), ("--backend", "canonical")),
        )
        literal = ("--backend", "nasm", "--compiler-profile", "run", "check",
                   "tail.nql", "@missing", "", "space arg")
        for cmd in ("run", "check"):
            for prefix, suffix in cases:
                with self.subTest(command=cmd, prefix=prefix, suffix=suffix):
                    result = self.ok(self.nql(*prefix, cmd, *suffix, source,
                                              "--dry-run", "--", *literal))
                    self.assertEqual(result.stdout, b"")
                    commands = [shlex.split(line) for line in result.stderr.decode().splitlines()]
                    self.assertEqual(commands[0][0], str(self.tool / C0 / "compile-source.sh"))
                    self.assertEqual(commands[0][-2], str(source))
                    self.assertEqual("--compiler-profile" in commands[0][1:-2],
                                     "--compiler-profile" in prefix + suffix)
                    self.assertEqual(len(commands), 2 if cmd == "run" else 1)
                    if cmd == "run":
                        self.assertEqual(commands[1][-len(literal):], list(literal))
        self.assertEqual(list(self.temps.iterdir()), [])
        self.assertFalse((self.work / "source space").exists())

    def test_dispatch_option_values_are_not_commands_or_sources(self):
        source = self.work / "source space.nql"
        source.write_text("fn main(){return 0}\n")
        for output in ("run", "check", "output.nql", "--backend", "--compiler-profile"):
            with self.subTest(output=output):
                result = self.ok(self.nql("--backend", "canonical", "-o", output,
                                          "run", source, "--dry-run"))
                command = shlex.split(result.stderr.decode().splitlines()[0])
                self.assertEqual(command[-2:], [str(source), str(self.work / output)])
                self.assertNotIn("--compiler-profile", command[1:-2])
                self.assertFalse((self.work / output).exists())
        for cmd in ("run", "check"):
            with self.subTest(command=cmd, target_value="run"):
                result = self.nql("--backend", "canonical", "--target", "run",
                                  cmd, source, "--dry-run")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(b"target 'run' is not supported yet", result.stderr)
        self.assertEqual(list(self.temps.iterdir()), [])

    def test_leading_project_check_rejects_literal_tail_without_selecting_backend(self):
        self.project()
        for prefix in (("--backend", "canonical"), ("--compiler-profile",)):
            with self.subTest(prefix=prefix):
                result = self.nql(*prefix, "check", "--", "--backend", "nasm",
                                  "--compiler-profile", "run", "check", "tail.nql", cwd=self.app)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(b"nql check does not accept positional arguments", result.stderr)
                self.assertFalse(self.binary.exists())

    def test_project_run_preserves_status_and_binary_streams(self):
        self.project("fn main(){let n=input_read(0,100) output_write(0,n) error_write(0,n) return n}\n")
        payload = b"stream\x00\xff\n"
        result = self.nql("run", "-q", cwd=self.app, payload=payload)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (len(payload), payload, payload))
        self.assertEqual(list(self.temps.iterdir()), [])

    @staticmethod
    def descendants(pid):
        # Linux/proot can expose real parent relationships in stat while
        # omitting task/children. Use the same interface as the Task1 tests.
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

    def reap_child(self, child):
        if child.poll() is None:
            child.terminate()
            try:
                child.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                for pid in reversed(self.descendants(child.pid)):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                child.kill()
                child.communicate(timeout=15)
        else:
            child.communicate()

    def wait_for(self, predicate):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            result = predicate()
            if result:
                return result
            time.sleep(0.02)
        self.fail("owned real runtime did not become ready")

    def test_runtime_backend_like_arguments_after_separator_are_literal(self):
        self.project(READY)
        literal = ["--backend", "nasm", "--compiler-profile", "--dump-ir", "@missing", "", "space arg",
                   "run", "check", "tail.nql"]
        for args in (("run", "-q"), ("run", self.app / "src/main.nql", "--backend", "canonical"),
                     ("--backend", "canonical", "run", "-q"),
                     ("--compiler-profile", "run", "-q"),
                     ("--compiler-profile", "--backend", "canonical", "run", self.app / "src/main.nql")):
            with self.subTest(args=args):
                argv = [str(self.tool / "nql"), *map(str, args), "--", *literal]
                child = subprocess.Popen(argv, cwd=self.app, env=self.env, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.addCleanup(self.reap_child, child)
                try:
                    self.assertTrue(select.select([child.stdout], [], [], 15)[0])
                    ready = child.stdout.read(6)
                    if ready != b"ready\n":
                        out, err = child.communicate(timeout=15)
                        result = subprocess.CompletedProcess(argv, child.returncode, ready + out, err)
                        self.record(argv, self.app, result)
                        self.assertEqual(ready, b"ready\n", err)
                    observed = [Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")[:-1]
                                for pid in self.descendants(child.pid)]
                    self.assertTrue(any(line[-len(literal):] == [a.encode() for a in literal]
                                        for line in observed), observed)
                    out, err = child.communicate(b"x", timeout=15)
                    result = subprocess.CompletedProcess(argv, child.returncode, ready + out, err)
                    self.record(argv, self.app, result, b"x", observed_argv=[
                        [a.decode(errors="replace") for a in line] for line in observed])
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (1, b"ready\n", b""))
                finally:
                    self.reap_child(child)

    def test_signals_reap_project_run_and_test_owned_runtime(self):
        # Project test intentionally suppresses program stdout. A stderr
        # handshake proves actual C0 execution for both commands, after all
        # transient compiler children have exited and before input_read waits.
        signal_source = READY.replace("output_write(0,6)", "error_write(0,6)")
        self.project(signal_source)
        (self.app / "tests/smoke.nql").write_text(signal_source)
        for cmd in ("run", "test"):
            for sig, status in ((signal.SIGHUP, 129), (signal.SIGINT, 130), (signal.SIGTERM, 143)):
                with self.subTest(command=cmd, signal=sig):
                    argv = [str(self.tool / "nql"), cmd, "-q"]
                    child = subprocess.Popen(argv, cwd=self.app, env=self.env, stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.addCleanup(self.reap_child, child)
                    try:
                        self.assertTrue(select.select([child.stderr], [], [], 15)[0],
                                        "actual C0 runtime did not signal readiness")
                        ready = child.stderr.read(6)
                        self.assertEqual(ready, b"ready\n")
                        owned = self.descendants(child.pid)
                        self.assertEqual(len(owned), 1 if cmd == "run" else 2, owned)
                        child.send_signal(sig)
                        out, err = child.communicate(timeout=15)
                        result = subprocess.CompletedProcess(argv, child.returncode, out, ready + err)
                        self.record(argv, self.app, result, signal=int(sig), owned_pids=owned,
                                    source_text=signal_source, runtime_ready=ready.decode())
                        self.assertEqual(result.returncode, status, err)
                        self.assertEqual((out, ready + err), (b"", b"ready\n"))
                        self.assertTrue(all(not Path(f"/proc/{pid}").exists() for pid in owned), owned)
                        self.assertEqual(list(self.temps.iterdir()), [])
                    finally:
                        # A failed observer/assertion must not leave this
                        # subtest's program alive during the next subtest.
                        self.reap_child(child)

    def restricted_environment(self):
        directory = self.work / "core utilities only"
        directory.mkdir()
        for name in ("bash", "readlink", "dirname", "head", "tr", "date", "uname", "mktemp",
                     "sha256sum", "stat", "cat", "chmod", "rm", "rmdir", "mv", "mkdir",
                     "install", "cp", "ln", "find", "sort", "grep", "cut", "basename", "awk"):
            target = shutil.which(name)
            self.assertIsNotNone(target, name)
            (directory / name).symlink_to(target)
        if platform.machine() != "x86_64":
            target = shutil.which("qemu-x86_64")
            self.assertIsNotNone(target)
            (directory / "qemu-x86_64").symlink_to(target)
        for name in ("nasm", "ld", "x86_64-linux-gnu-ld", "python", "python3", "clang", "setsid"):
            self.assertIsNone(shutil.which(name, path=str(directory)), name)
        return dict(self.env, PATH=str(directory))

    def test_canonical_only_install_relocation_with_no_host_compilers(self):
        env = self.restricted_environment()
        (self.tool / "build/nqlc-r0").unlink(missing_ok=True)
        (self.tool / "src/nqlc.asm").unlink()
        dest = self.work / "staging root"
        prefix = "/opt/prefix space"
        install_env = dict(env, PREFIX=prefix, DESTDIR=str(dest))
        self.ok(self.command(self.tool / "install.sh", "--canonical-only", env=install_env))
        installed = dest / "opt/prefix space"
        relocated = self.work / "relocated toolchain"
        installed.rename(relocated)
        public = relocated / "bin"
        assets = relocated / "lib/nolqu"
        self.assertFalse((assets / "build/nqlc-r0").exists())
        for path in (self.tool / "bootstrap").rglob("*"):
            if path.is_file():
                copy = assets / path.relative_to(self.tool)
                self.assertEqual(copy.read_bytes(), path.read_bytes(), str(path))
                self.assertEqual(stat.S_IMODE(copy.stat().st_mode), stat.S_IMODE(path.stat().st_mode))
        for alias, primary in (("nolqul", "nql"), ("nolqulc", "nqlc")):
            self.assertEqual(os.readlink(public / alias), primary)
        for removed in ("nq", "nqc", "nolqu", "nolquc"):
            self.assertFalse((public / removed).exists())
        unrelated = self.work / "unrelated cwd"
        unrelated.mkdir()
        source = unrelated / "hello source.nql"
        source.write_text("fn main(){return 23}\n")
        output = unrelated / "compiled output"
        self.ok(self.command(public / "nqlc", "--backend", "canonical", source, "-o", output,
                             cwd=unrelated, env=env))
        self.assertEqual(self.execute(output, env=env).returncode, 23)
        for alias in ("nqlc", "nolqulc"):
            self.ok(self.command(public / alias, "--backend", "canonical", "--check", source,
                                 cwd=unrelated, env=env))
            self.assertEqual(self.command(public / alias, "--backend", "canonical", "--run", source,
                                          cwd=unrelated, env=env).returncode, 23)
        source.write_bytes((ROOT / "examples/canonical/native_cat.nql").read_bytes())
        data = unrelated / "native input"
        data.write_bytes(b"relocated\x00\xff\n")
        for flags in ((), ("--compiler-profile",)):
            self.ok(self.command(public / "nqlc", "--backend", "canonical", *flags,
                                 source, "-o", output, cwd=unrelated, env=env))
            runner = [] if platform.machine() == "x86_64" else ["qemu-x86_64"]
            result = self.command(*runner, output, data.name, cwd=unrelated, env=env)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, data.read_bytes(), b""))
        self.ok(self.command(public / "nolqul", "init", "fresh app", "--backend", "canonical",
                             cwd=unrelated, env=env))
        project = unrelated / "fresh app"
        for cmd in ("check", "build", "run", "test"):
            result = self.ok(self.command(public / "nql", cmd, cwd=project, env=env))
            if cmd == "run":
                self.assertEqual(result.stdout, HELLO)
        pin = assets / C0 / "c0-frontend.sha256"
        pin.write_bytes(b"0" * 64 + pin.read_bytes()[64:])
        result = self.command(public / "nql", "build", cwd=project, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"hash mismatch", result.stderr)
        self.assertNotIn(b"cached", result.stderr.lower())
        self.ok(self.command(self.tool / "install.sh", "--uninstall",
                             env=dict(env, PREFIX=str(relocated), DESTDIR="")))
        self.assertFalse(assets.exists())
        for name in ("nql", "nqlc", "nolqul", "nolqulc"):
            self.assertFalse((public / name).exists())

    def test_install_unknown_duplicate_arguments_do_not_install(self):
        prefix = self.work / "no installation"
        env = dict(self.env, PREFIX=str(prefix))
        for args in (("--unknown",), ("--canonical-only", "unexpected"),
                     ("--canonical-only", "--canonical-only"), ("--uninstall", "--unknown")):
            with self.subTest(args=args):
                result = self.command(self.tool / "install.sh", *args, env=env)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(prefix.exists())

    def test_raw_legacy_nasm_llvm_routes_and_separator_are_unchanged(self):
        adapter = self.tool / "tools/nql_r0_adapter.sh"
        adapter.write_text('#!/bin/bash\nprintf "%s\\0" "$@"\nexit 29\n')
        source = self.work / "legacy.nql"
        for args in ((source,), ("run", source), ("check", source),
                     ("--backend", "llvm", source), ("--backend", "nasm", source),
                     (source, "--", "--backend", "canonical")):
            with self.subTest(args=args):
                result = self.nql(*args)
                self.assertEqual(result.returncode, 29, result.stderr)
                self.assertEqual(result.stdout, b"".join(str(a).encode() + b"\0" for a in args))

    def test_init_source_like_project_name_is_a_project(self):
        self.ok(self.nql("--backend", "canonical", "init", "app.nql"))
        project = self.work / "app.nql"
        self.assertTrue((project / "nql.toml").is_file())
        self.ok(self.nql("check", cwd=project))

    def test_explicit_nasm_before_project_command(self):
        self.project('print "legacy"\n', "nasm")
        self.ok(self.nql("--backend", "nasm", "build", cwd=self.app))
        self.assertEqual(self.ok(self.execute(self.binary)).stdout, b"legacy\n")

    def test_install_preserves_asset_modes_with_restrictive_umask(self):
        prefix = self.work / "restrictive prefix"
        env = dict(self.restricted_environment(), PREFIX=str(prefix))
        self.ok(self.command("bash", "-c", 'umask 077; exec "$@"', "install-test",
                             self.tool / "install.sh", "--canonical-only", env=env))
        for name in ("c0-frontend.seed", "c0-backend.seed", "compile-source.sh"):
            source = self.tool / C0 / name
            installed = prefix / "lib/nolqu" / C0 / name
            self.assertEqual(stat.S_IMODE(installed.stat().st_mode),
                             stat.S_IMODE(source.stat().st_mode), name)

    def test_combined_install_supports_both_backends_and_aliases(self):
        prefix = self.work / "combined prefix"
        self.ok(self.command(self.tool / "install.sh", env=dict(self.env, PREFIX=str(prefix))))
        source = self.work / "canonical.nql"
        source.write_text("fn main(){return 23}\n")
        public = prefix / "bin"
        self.ok(self.command(public / "nolqulc", "--backend", "canonical", "--check", source))
        result = self.command(public / "nolqul", "run", source, "--backend", "canonical")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (23, b"", b""))
        relocated = self.work / "combined relocated"
        prefix.rename(relocated)
        public = relocated / "bin"
        source.write_bytes((ROOT / "examples/canonical/native_cat.nql").read_bytes())
        data = self.work / "combined input"
        data.write_bytes(b"combined\x00\xff\n")
        result = self.command(public / "nolqulc", "--backend", "canonical", "--run", source,
                              "--", data.name, "-", payload=b"stdin\x80")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, data.read_bytes() + b"stdin\x80", b""))
        self.ok(self.command(public / "nql", "init", "legacy app"))
        project = self.work / "legacy app"
        self.assertEqual(self.ok(self.command(public / "nolqul", "run", cwd=project)).stdout, HELLO)

    def test_canonical_workflow_never_invokes_forbidden_host_tools(self):
        poison = self.work / "forbidden tools"
        poison.mkdir()
        marker = self.work / "forbidden invoked"
        for name in ("nasm", "ld", "x86_64-linux-gnu-ld", "python", "python3", "clang"):
            path = poison / name
            path.write_text('#!/bin/bash\nprintf "%s\\n" "$0" >> "$FORBIDDEN_INVOKED"\nexit 99\n')
            path.chmod(0o755)
        for relative in ("tools/nql_r0_adapter.sh", "build/nqlc-r0"):
            (self.tool / relative).write_text(
                '#!/bin/bash\nprintf "%s\\n" "$0" >> "$FORBIDDEN_INVOKED"\nexit 99\n')
        env = dict(self.env, PATH=str(poison) + os.pathsep + self.env["PATH"],
                   FORBIDDEN_INVOKED=str(marker))
        self.ok(self.nql("init", "app", "--backend", "canonical", env=env))
        for cmd in ("build", "check", "run", "test"):
            result = self.ok(self.nql(cmd, cwd=self.app, env=env))
            if cmd == "run":
                self.assertEqual(result.stdout, HELLO)
        self.assertFalse(marker.exists(), marker.read_text() if marker.exists() else "")


if __name__ == "__main__":
    unittest.main()
