"""Source transport/publication tests using real canonical compiler components."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

from standard_fd_fault import invalidate_standard_fd

from c031_support import candidate_binary, run_native


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "bootstrap/compiler/c0/x86_64-linux"
FRONTEND = candidate_binary("C0_FRONTEND", STAGE / "c0-frontend.seed")
BACKEND = candidate_binary("C0_BACKEND", STAGE / "c0-backend.seed")
B0 = candidate_binary("B0_COMPILER", ROOT / "bootstrap/compiler/b0/x86_64-linux/b0.seed")


class CapacityPipelineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="c031-pipeline-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.install = self.root / "candidate installation"
        self.stage = self.install / STAGE.relative_to(ROOT)
        self.stage.mkdir(parents=True)
        self.script = self.stage / "compile-source.sh"
        shutil.copy2(STAGE / self.script.name, self.script)
        for name, binary in (("frontend", FRONTEND), ("backend", BACKEND)):
            seed = self.stage / f"c0-{name}.seed"
            shutil.copy2(binary, seed)
            seed.with_suffix(".sha256").write_text(
                hashlib.sha256(seed.read_bytes()).hexdigest() + f"  {seed.name}\n")
            shutil.copy2(STAGE.parent / f"{name}.nql", self.stage.parent)
        shutil.copy2(ROOT / "bootstrap/manifest.tsv", self.install / "bootstrap")
        self.cwd = self.root / "unrelated directory"
        self.cwd.mkdir()
        self.work = self.root / "temporary workspace"
        self.work.mkdir()
        self.source = self.root / "input source.nql"
        self.output = self.root / "output program"
        self.source.write_bytes(b"fn main(){return 7}")
        self.output.write_bytes(b"old executable\x00with retained bytes\n")
        self.output.chmod(0o641)
        self.old = self.snapshot(self.output)
        self.commands = self.root / "commands"
        self.commands.mkdir()
        self.env = {**os.environ, "TMPDIR": str(self.work)}
        self.children = []
        self.owned_pids = set()
        self.addCleanup(self.reap)

    def build(self, *args, script=None, **kwargs):
        return subprocess.run(["bash", str(script or self.script), *map(str, args)],
                              cwd=self.cwd, env=self.env, capture_output=True,
                              timeout=20, **kwargs)

    def snapshot(self, path):
        return path.read_bytes(), path.stat().st_mode & 0o7777

    def assert_clean(self):
        self.assertEqual(list(self.work.iterdir()), [])
        self.assertEqual(list(self.root.glob(".c0-source.*")), [])
        self.assertEqual(list(self.root.glob(".c0-*.seed.tmp.*")), [])

    def assert_failed(self, result, status=None):
        if status is None:
            self.assertNotEqual(result.returncode, 0, result.stderr)
        else:
            self.assertEqual(result.returncode, status, result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(self.snapshot(self.output), self.old)
        self.assert_clean()

    def shim(self, name, body):
        real = shutil.which(name)
        self.assertIsNotNone(real, name)
        path = self.commands / name
        path.write_text(f"#!{sys.executable}\n"
                        "import json, os, pathlib, signal, socket, struct, subprocess, sys, time\n"
                        f"REAL = {real!r}\n" + textwrap.dedent(body))
        path.chmod(0o755)
        self.env["PATH"] = str(self.commands) + os.pathsep + os.environ["PATH"]
        return path

    def runner_shim(self, body):
        self.shim("uname", "print('aarch64')\n")
        return self.shim("qemu-x86_64", body)

    def wait_for(self, predicate, process=None):
        deadline = time.monotonic() + 10
        while not predicate():
            if time.monotonic() >= deadline or (process is not None and process.poll() is not None):
                self.fail("owned command did not reach its synchronized marker")
            time.sleep(0.01)

    def alive(self, pid):
        try:
            state = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[0]
        except FileNotFoundError:
            return False
        return state != "Z"

    def start(self, *args, script=None):
        process = subprocess.Popen(["bash", str(script or self.script), *map(str, args)],
                                   cwd=self.cwd, env=self.env, start_new_session=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.children.append(process)
        return process

    def reap(self):
        for marker in self.root.glob("*.pid"):
            for value in marker.read_text().split():
                self.owned_pids.add(int(value))
        for pid in self.owned_pids:
            if self.alive(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        self.owned_pids.clear()
        for process in self.children:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=10)

    def expected(self, source=None, profile=False):
        from c031_support import encode_profile_source
        source = self.source.read_bytes() if source is None else source
        parsed = run_native(FRONTEND, encode_profile_source(source) if profile else source)
        self.assertEqual((parsed.returncode, parsed.stderr), (0, b""))
        compiled = run_native(BACKEND, parsed.stdout)
        self.assertEqual((compiled.returncode, compiled.stderr), (0, b""))
        return parsed.stdout, compiled.stdout

    def test_profile_wrapper_from_unrelated_cwd(self):
        self.source.write_bytes(
            b"fn main(){byte_store(65536,42);return byte_load(65536)}")
        result = self.build("--compiler-profile", self.source, self.output)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        executed = run_native(self.output)
        self.assertEqual((executed.returncode, executed.stdout, executed.stderr),
                         (42, b"", b""))
        self.assert_clean()

    def test_raw_bytes_and_production_environment_isolation(self):
        expected = self.expected()[1]
        self.env.update(B0_COMPILER="/missing/b0", C0_FRONTEND="/missing/front",
                        C0_BACKEND="/missing/back")
        result = self.build(self.source, self.output)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        self.assertEqual(self.snapshot(self.output), (expected, 0o755))
        self.assert_clean()

    def test_argument_rejections(self):
        cases = [(), (self.source,), ("--unknown", self.source, self.output),
                 ("--compiler-profile", "--compiler-profile", self.source, self.output),
                 (self.source, self.output, "--compiler-profile"),
                 ("--compiler-profile", self.source),
                 ("--compiler-profile", self.source, self.output, "extra")]
        for args in cases:
            with self.subTest(args=args):
                self.assert_failed(self.build(*args), 1)

    def test_invalid_sources_and_output_parents(self):
        wrong = self.root / "wrong.nq"
        wrong.write_bytes(self.source.read_bytes())
        parent = self.root / "not a directory"
        parent.write_bytes(b"file")
        for source, output in ((self.root / "missing.nql", self.output),
                               (wrong, self.output), (self.work, self.output),
                               (self.source, parent / "output"),
                               (self.source, self.root / "absent" / "output"),
                               (self.source, self.cwd)):
            with self.subTest(source=source, output=output):
                self.assert_failed(self.build(source, output), 1)

    def test_unreadable_source(self):
        self.source.chmod(0)
        if os.access(self.source, os.R_OK):
            # This proot host may still permit reads; inject EACCES at byte copy.
            self.shim("cat", "sys.stderr.write('test copy: Permission denied (EACCES)\\n')\nsys.exit(1)\n")
        self.assert_failed(self.build("--compiler-profile", self.source, self.output), 1)

    def test_protected_paths_hardlinks_and_symlinks(self):
        protected = [self.source, self.script, self.install / "bootstrap/manifest.tsv"]
        protected += list(self.stage.glob("*.seed")) + list(self.stage.glob("*.sha256"))
        protected += list(self.stage.parent.glob("*.nql"))
        alias = self.root / "protected alias"
        for path in protected:
            for kind in ("direct", "hardlink", "symlink"):
                with self.subTest(path=path.name, kind=kind):
                    before = self.snapshot(path)
                    target = path
                    try:
                        if kind == "hardlink":
                            subprocess.run(["ln", "--", str(path), str(alias)],
                                           check=True, capture_output=True, timeout=5)
                            target = alias
                        elif kind == "symlink":
                            alias.symlink_to(path)
                            target = alias
                        result = self.build(self.source, target)
                        self.assert_failed(result, 1)
                        self.assertEqual(self.snapshot(path), before)
                    finally:
                        alias.unlink(missing_ok=True)
                        path.write_bytes(before[0])
                        path.chmod(before[1])

    def test_missing_malformed_and_stale_pins(self):
        for component in ("frontend", "backend"):
            pin = self.stage / f"c0-{component}.sha256"
            original = pin.read_bytes()
            for data in (None, b"malformed\n", b"0" * 64 + b"  wrong.seed\n",
                         b"0" * 64 + f"  c0-{component}.seed\n".encode()):
                with self.subTest(component=component, data=data):
                    try:
                        if data is None:
                            pin.unlink()
                        else:
                            pin.write_bytes(data)
                        self.assert_failed(self.build(self.source, self.output), 1)
                    finally:
                        pin.write_bytes(original)
            seed = pin.with_suffix(".seed")
            seed.rename(seed.with_suffix(".missing"))
            try:
                self.assert_failed(self.build(self.source, self.output), 1)
            finally:
                seed.with_suffix(".missing").rename(seed)

    def test_frontend_and_backend_semantic_failures(self):
        for source, code in ((b"fn main(){return ;}", b"C0P-"),
                             (b"fn main(){return missing}", b"C0B-003")):
            with self.subTest(code=code):
                self.source.write_bytes(source)
                result = self.build("--compiler-profile", self.source, self.output)
                self.assert_failed(result, 1)
                self.assertIn(code, result.stderr)
                if code == b"C0P-":
                    self.assertNotIn(b"C0B-", result.stderr)

    def test_copy_failure_after_all_bytes_does_not_run_frontend(self):
        marker = self.root / "frontend invoked"
        self.runner_shim(f"pathlib.Path({str(marker)!r}).touch()\nos.execv(REAL, [REAL, *sys.argv[1:]])\n")
        self.shim("cat", "result = subprocess.run([REAL, *sys.argv[1:]])\nsys.exit(73 if result.returncode == 0 else result.returncode)\n")
        self.assert_failed(self.build("--compiler-profile", self.source, self.output), 73)
        self.assertFalse(marker.exists())

    def test_protected_path_resolution_failure_fails_closed(self):
        self.shim("readlink", """
            if sys.argv[-1].endswith('/bootstrap/manifest.tsv'):
                sys.exit(73)
            os.execv(REAL, [REAL, *sys.argv[1:]])
        """)
        self.assert_failed(self.build(self.source, self.output), 1)

    def test_failed_producer_reaps_descendants_before_cleanup(self):
        marker = self.root / "descendant.pid"
        ready = self.root / "descendant ready"
        descendant = ("import pathlib,time; pathlib.Path(" + repr(str(ready))
                      + ").touch(); time.sleep(60)")
        self.shim("cat", f"""
            result = subprocess.run([REAL, *sys.argv[1:]])
            assert result.returncode == 0
            child = subprocess.Popen([sys.executable, '-c', {descendant!r}],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
            pathlib.Path({str(marker)!r}).write_text(str(child.pid))
            deadline = time.monotonic() + 5
            while not pathlib.Path({str(ready)!r}).exists():
                assert time.monotonic() < deadline
                time.sleep(0.01)
            sys.exit(73)
        """)
        self.assert_failed(self.build("--compiler-profile", self.source, self.output), 73)
        self.wait_for(lambda: not self.alive(int(marker.read_text())))

    def test_header_and_compiler_output_open_failures(self):
        try:
            descriptor = os.open("/dev/full", os.O_WRONLY)
        except OSError:
            compiler_status = 1
        else:
            os.close(descriptor)
            compiler_status = 74
        for filename, profile, status in (("source.nqsc", True, 1),
                                          ("module.nqaf", False, compiler_status),
                                          (None, False, compiler_status)):
            with self.subTest(filename=filename):
                self.shim("mktemp", f"""
                    result = subprocess.run([REAL, *sys.argv[1:]], capture_output=True)
                    sys.stderr.buffer.write(result.stderr)
                    if result.returncode:
                        sys.exit(result.returncode)
                    path = pathlib.Path(os.fsdecode(result.stdout.rstrip(b'\\n')))
                    filename = {filename!r}
                    if '-d' in sys.argv and filename:
                        (path / filename).symlink_to('/dev/full')
                    elif '-d' not in sys.argv and filename is None:
                        path.unlink()
                        path.symlink_to('/dev/full')
                    sys.stdout.buffer.write(result.stdout)
                """)
                args = ("--compiler-profile", self.source, self.output) if profile else (self.source, self.output)
                self.assert_failed(self.build(*args), status)

    def test_real_compiler_stdout_write_failures(self):
        for component in ("frontend", "backend"):
            with self.subTest(component=component):
                self.runner_shim(f"""
                    sys.path.insert(0, {str(ROOT / 'tests/bootstrap')!r})
                    from standard_fd_fault import invalidate_standard_fd
                    if pathlib.Path(sys.argv[1]).name == {'c0-' + component + '.seed'!r}:
                        invalidate_standard_fd(1)
                    os.execv(REAL, [REAL, *sys.argv[1:]])
                """)
                result = self.build(self.source, self.output)
                self.assert_failed(result, 74)
                self.assertIn(b"output_write failed", result.stderr)

    def test_real_copy_and_compiler_readonly_stdout_write_failures(self):
        readonly_output = f"""
            descriptor = os.open({str(self.source)!r}, os.O_RDONLY)
            os.dup2(descriptor, 1)
            os.close(descriptor)
        """
        for component in ("copy", "frontend", "backend"):
            with self.subTest(component=component):
                for shim in self.commands.iterdir():
                    shim.unlink()
                if component == "copy":
                    self.shim("cat", textwrap.dedent(readonly_output) +
                              "os.execv(REAL, [REAL, *sys.argv[1:]])\n")
                else:
                    self.runner_shim(
                        f"if pathlib.Path(sys.argv[1]).name == {'c0-' + component + '.seed'!r}:\n"
                        + textwrap.indent(textwrap.dedent(readonly_output), "    ")
                        + "os.execv(REAL, [REAL, *sys.argv[1:]])\n")
                result = self.build("--compiler-profile", self.source, self.output)
                self.assert_failed(result, 1 if component == "copy" else 74)
                if component == "copy":
                    self.assertIn(b"Bad file descriptor", result.stderr)
                else:
                    self.assertIn(b"output_write failed", result.stderr)

    def test_exact_profile_transport(self):
        from c031_support import encode_profile_source
        self.source.write_bytes(b"\n \tfn main() { return 23 }\r\n\t ")
        observed = self.root / "observed transport"
        self.runner_shim(f"""
            if pathlib.Path(sys.argv[1]).name == 'c0-frontend.seed':
                pathlib.Path({str(observed)!r}).write_bytes(pathlib.Path('/proc/self/fd/0').read_bytes())
            os.execv(REAL, [REAL, *sys.argv[1:]])
        """)
        result = self.build("--compiler-profile", self.source, self.output)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        self.assertEqual(observed.read_bytes(), encode_profile_source(self.source.read_bytes()))
        self.assertEqual(self.output.read_bytes(), self.expected(profile=True)[1])
        self.assert_clean()

    def test_broken_stderr_and_absent_destination_failure(self):
        self.source.write_bytes(b"fn main(){return ;}")
        result = self.build(self.source, self.output, preexec_fn=lambda: invalidate_standard_fd(2))
        self.assert_failed(result, 74)
        self.output.unlink()
        result = self.build(self.source, self.output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(self.output.exists())
        self.assert_clean()

    def test_allocation_failures_preserve_output(self):
        for directory in (True, False):
            with self.subTest(directory=directory):
                self.shim("mktemp", f"""
                    if ('-d' in sys.argv) == {directory!r}:
                        sys.exit(73)
                    os.execv(REAL, [REAL, *sys.argv[1:]])
                """)
                self.assert_failed(self.build(self.source, self.output), 1)

    def test_chmod_and_rename_failures(self):
        for utility in ("chmod", "mv"):
            with self.subTest(utility=utility):
                shim = self.shim(utility, "sys.exit(73)\n")
                try:
                    self.assert_failed(self.build(self.source, self.output), 1)
                finally:
                    shim.unlink()

    def test_intermediate_cleanup_failure_prevents_publication(self):
        for utility in ("rm", "rmdir"):
            with self.subTest(utility=utility):
                marker = self.root / f"{utility} failed once"
                shim = self.shim(utility, f"""
                    marker = pathlib.Path({str(marker)!r})
                    selected = {utility == 'rmdir'!r} or any(arg.endswith('/module.nqaf') for arg in sys.argv[1:])
                    if selected and not marker.exists():
                        marker.touch()
                        sys.exit(73)
                    os.execv(REAL, [REAL, *sys.argv[1:]])
                """)
                try:
                    self.assert_failed(self.build(self.source, self.output), 1)
                    self.assertTrue(marker.exists())
                finally:
                    shim.unlink()

    def test_permanent_cleanup_refusal_reports_residue(self):
        self.shim("rm", """
            if any(arg.endswith('/module.nqaf') for arg in sys.argv[1:]):
                sys.exit(73)
            os.execv(REAL, [REAL, *sys.argv[1:]])
        """)
        result = self.build(self.source, self.output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.snapshot(self.output), self.old)
        self.assertEqual(list(self.root.glob(".c0-source.*")), [])
        remaining = list(self.work.glob("c0-source.*/module.nqaf"))
        self.assertEqual(len(remaining), 1)
        self.assertIn(os.fsencode(remaining[0]), result.stderr)

    def test_destination_is_rechecked_before_publication(self):
        protected = self.install / "bootstrap/manifest.tsv"
        before = self.snapshot(protected)
        self.shim("chmod", f"""
            result = subprocess.run([REAL, *sys.argv[1:]])
            output = pathlib.Path({str(self.output)!r})
            output.unlink()
            subprocess.run(['ln', '--', {str(protected)!r}, str(output)],
                           check=True, capture_output=True, timeout=5)
            sys.exit(result.returncode)
        """)
        result = self.build(self.source, self.output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.snapshot(protected), before)
        self.assertTrue(self.output.samefile(protected))
        self.assert_clean()

    def test_concurrent_builds_use_disjoint_private_files(self):
        gate = self.root / "release builds"
        self.shim("chmod", f"""
            pathlib.Path({str(self.root)!r}, 'candidate-' + str(os.getpid())).write_text(sys.argv[-1])
            deadline = time.monotonic() + 15
            while not pathlib.Path({str(gate)!r}).exists():
                if time.monotonic() >= deadline:
                    sys.exit(72)
                time.sleep(0.01)
            os.execv(REAL, [REAL, *sys.argv[1:]])
        """)
        other = self.root / "other source.nql"
        other.write_bytes(b"fn main(){return 23}")
        expected = {self.expected()[1], self.expected(other.read_bytes())[1]}
        a = self.start(self.source, self.output)
        b = self.start(other, self.output)
        self.wait_for(lambda: len(list(self.root.glob("candidate-*"))) == 2)
        candidates = [Path(p.read_text()) for p in self.root.glob("candidate-*")]
        self.assertEqual(len(set(candidates)), 2)
        self.assertTrue(all(p.parent == self.output.parent for p in candidates))
        workspaces = list(self.work.iterdir())
        self.assertEqual(len(workspaces), 2)
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o700 for p in workspaces))
        self.assertEqual(self.snapshot(self.output), self.old)
        gate.touch()
        for process in (a, b):
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual((process.returncode, stdout, stderr), (0, b"", b""))
        self.assertIn(self.output.read_bytes(), expected)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o755)
        self.assert_clean()

    def test_wrapper_pid_signals_reap_owned_commands(self):
        for stage in ("copy", "frontend", "backend", "rm", "rmdir", "rename", "after-rename"):
            for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
                with self.subTest(stage=stage, signal=sig):
                    for shim in self.commands.iterdir():
                        shim.unlink()
                    self.output.write_bytes(self.old[0])
                    self.output.chmod(self.old[1])
                    marker = self.root / "owned.pid"
                    marker.unlink(missing_ok=True)
                    ready = self.root / "owned ready"
                    ready.unlink(missing_ok=True)
                    sock = self.root / "compiler.sock"
                    sock.unlink(missing_ok=True)
                    block = f"""
                        child = subprocess.Popen(['sleep', '60'], stdin=subprocess.DEVNULL)
                        pathlib.Path({str(marker)!r}).write_text(str(os.getpid()) + ' ' + str(child.pid))
                        pathlib.Path({str(ready)!r}).touch()
                        os.execvp('sleep', ['sleep', '60'])
                    """
                    if stage == "copy":
                        self.shim("cat", textwrap.dedent(block))
                    elif stage in ("frontend", "backend"):
                        self.runner_shim(f"""
                            if pathlib.Path(sys.argv[1]).name == {'c0-' + stage + '.seed'!r}:
                                pathlib.Path({str(marker)!r}).write_text(str(os.getpid()))
                                os.execv(REAL, [REAL, '-g', {str(sock)!r}, *sys.argv[1:]])
                            os.execv(REAL, [REAL, *sys.argv[1:]])
                        """)
                    elif stage in ("rm", "rmdir"):
                        self.shim(stage, f"if not pathlib.Path({str(ready)!r}).exists():\n"
                                  + textwrap.indent(textwrap.dedent(block), "    ")
                                  + "os.execv(REAL, [REAL, *sys.argv[1:]])\n")
                    else:
                        before = "subprocess.run([REAL, *sys.argv[1:]], check=True)\n" if stage == "after-rename" else ""
                        self.shim("mv", before + textwrap.dedent(block))
                    process = self.start("--compiler-profile", self.source, self.output)
                    self.wait_for(lambda: sock.exists() if stage in ("frontend", "backend") else ready.exists(), process)
                    pids = [int(value) for value in marker.read_text().split()]
                    self.owned_pids.update(pids)
                    self.assertTrue(all(self.alive(pid) for pid in pids))
                    if stage in ("rename", "after-rename"):
                        self.assertEqual(list(self.work.iterdir()), [], "workspace must be gone before rename")
                    os.kill(process.pid, sig)
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.fail("wrapper-only signal did not terminate/reap its owned command")
                    self.assertEqual((process.returncode, stdout), (128 + sig, b""), stderr)
                    self.wait_for(lambda: all(not self.alive(pid) for pid in pids))
                    self.assertFalse(Path(f"/proc/{pids[0]}").exists(), "direct child must be reaped")
                    if stage == "after-rename":
                        self.assertEqual(self.snapshot(self.output), (self.expected(profile=True)[1], 0o755))
                    else:
                        self.assertEqual(self.snapshot(self.output), self.old)
                    self.assert_clean()
                    self.reap()

    def test_launch_allocation_and_completed_rename_signal_windows(self):
        # DEBUG is test-only synchronization before the next shell instruction.
        for window in ("launch", "allocated", "renamed"):
            with self.subTest(window=window):
                self.output.write_bytes(self.old[0])
                self.output.chmod(self.old[1])
                marker = self.root / "window reached"
                marker.unlink(missing_ok=True)
                bash_env = self.root / "synchronize bash"
                conditions = {
                    "launch": "[[ $BASH_COMMAND == 'active=$!' ]]",
                    "allocated": "[[ $BASH_COMMAND == 'registering=0' && -n ${work:-} && -n ${temp:-} ]]",
                    "renamed": "[[ $BASH_COMMAND == 'active=\"\"' && -z ${work:-} && -n ${temp:-} ]]",
                }
                bash_env.write_text(
                    "set -o functrace\nwindow_signal() {\n"
                    f"  if {conditions[window]} && [[ ! -e '{marker}' ]]; then\n"
                    f"    builtin printf reached > '{marker}'\n"
                    "    kill -TERM $$\n  fi\n}\ntrap window_signal DEBUG\n")
                self.env["BASH_ENV"] = str(bash_env)
                result = self.build("--compiler-profile", self.source, self.output)
                self.assertTrue(marker.exists(), window)
                self.assertEqual(result.returncode, 143, result.stderr)
                if window == "renamed":
                    self.assertEqual(self.snapshot(self.output), (self.expected(profile=True)[1], 0o755))
                else:
                    self.assertEqual(self.snapshot(self.output), self.old)
                self.assert_clean()
        self.env.pop("BASH_ENV")

    def materializer(self, component):
        compiler = self.install / "bootstrap/compiler/b0/x86_64-linux/b0.seed"
        compiler.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(B0, compiler)
        script = self.stage / f"materialize-{component}.sh"
        shutil.copy2(STAGE / script.name, script)
        return script

    def materializer_lifetime(self, phases):
        for component in ("frontend", "backend"):
            script = self.materializer(component)
            expected = (FRONTEND if component == "frontend" else BACKEND).read_bytes()
            for phase in phases:
                for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
                    with self.subTest(component=component, phase=phase, signal=sig):
                        for shim in self.commands.iterdir():
                            shim.unlink()
                        self.output.write_bytes(self.old[0])
                        self.output.chmod(self.old[1])
                        marker = self.root / "materializer.pid"
                        marker.unlink(missing_ok=True)
                        ready = self.root / "materializer ready"
                        ready.unlink(missing_ok=True)
                        sock = self.root / "materializer.sock"
                        sock.unlink(missing_ok=True)
                        if phase == "compiler":
                            self.runner_shim(f"""
                                pathlib.Path({str(marker)!r}).write_text(str(os.getpid()))
                                os.execv(REAL, [REAL, '-g', {str(sock)!r}, *sys.argv[1:]])
                            """)
                        else:
                            before = "subprocess.run([REAL, *sys.argv[1:]], check=True)\n" if phase == "after-rename" else ""
                            self.shim("mv", before + textwrap.dedent(f"""
                                child = subprocess.Popen(['sleep', '60'], stdin=subprocess.DEVNULL)
                                pathlib.Path({str(marker)!r}).write_text(str(os.getpid()) + ' ' + str(child.pid))
                                pathlib.Path({str(ready)!r}).touch()
                                os.execvp('sleep', ['sleep', '60'])
                            """))
                        process = self.start(self.output, script=script)
                        try:
                            self.wait_for(lambda: sock.exists() if phase == "compiler" else ready.exists(), process)
                            pids = [int(value) for value in marker.read_text().split()]
                            self.owned_pids.update(pids)
                            self.assertTrue(all(self.alive(pid) for pid in pids))
                            if phase == "compiler":
                                cmdline = Path(f"/proc/{pids[0]}/cmdline").read_bytes()
                                self.assertIn(b"b0.seed", cmdline)
                                self.assertIn(b"--compiler-profile", cmdline)
                            os.kill(process.pid, sig)
                            try:
                                stdout, stderr = process.communicate(timeout=3)
                            except subprocess.TimeoutExpired:
                                self.fail("materializer-only signal left an owned command alive")
                            self.assertEqual((process.returncode, stdout), (128 + sig, b""), stderr)
                            self.wait_for(lambda: all(not self.alive(pid) for pid in pids))
                            self.assertFalse(Path(f"/proc/{pids[0]}").exists())
                            self.assertEqual(self.snapshot(self.output),
                                             (expected, 0o755) if phase == "after-rename" else self.old)
                            self.assert_clean()
                        finally:
                            self.reap()

    def test_materializer_signals_while_native_b0_runs(self):
        self.materializer_lifetime(("compiler",))

    def test_materializer_signals_before_and_after_rename(self):
        self.materializer_lifetime(("rename", "after-rename"))

    def test_real_compiler_teardown_failure_after_complete_output(self):
        for component in ("frontend", "backend"):
            with self.subTest(component=component):
                ast, elf = self.expected(profile=True)
                expected = self.root / "expected complete output"
                expected.write_bytes(ast if component == "frontend" else elf)
                receipt = self.root / "resource observation.json"
                self.runner_shim(f"""
                    if pathlib.Path(sys.argv[1]).name != {'c0-' + component + '.seed'!r}:
                        os.execv(REAL, [REAL, *sys.argv[1:]])
                    sys.path.insert(0, {str(ROOT / 'tests/bootstrap')!r})
                    from c031_debugger import _Remote
                    data = pathlib.Path(sys.argv[1]).read_bytes()
                    prefix = bytes.fromhex('b80b0000004c89f7be00000001')
                    assert data.count(prefix) == 1
                    position = data.index(prefix) + len(prefix)
                    assert data[position:position+2] == b'\\x0f\\x05'
                    address = 0x400000 + position
                    sock = {str(self.root / 'fault.sock')!r}
                    child = subprocess.Popen([REAL, '-g', sock, *sys.argv[1:]])
                    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    try:
                        deadline = time.monotonic() + 10
                        while True:
                            try:
                                connection.connect(sock)
                                break
                            except (FileNotFoundError, ConnectionRefusedError):
                                assert child.poll() is None and time.monotonic() < deadline
                                time.sleep(0.01)
                        remote = _Remote(connection)
                        assert remote.command('?').startswith(('T', 'S'))
                        assert remote.command('Z0,' + format(address, 'x') + ',1') == 'OK'
                        assert remote.command('c').startswith('T05')
                        registers = bytearray.fromhex(remote.command('g'))
                        values = struct.unpack_from('<17Q', registers)
                        assert values[0] == 11 and values[16] == address
                        assert values[4] == 16777216 and values[5] != 0
                        output = pathlib.Path(os.readlink('/proc/self/fd/1')).read_bytes()
                        assert output == pathlib.Path({str(expected)!r}).read_bytes()
                        struct.pack_into('<Q', registers, 0, (1 << 64) - 22)
                        struct.pack_into('<Q', registers, 16 * 8, address + 2)
                        assert remote.command('G' + registers.hex()) == 'OK'
                        # Keep munmap armed: a second attempt must stop, not exit.
                        reply = remote.command('c')
                        assert reply.startswith('W4a'), reply
                        status = child.wait(timeout=5)
                        assert status == 74
                        pathlib.Path({str(receipt)!r}).write_text(json.dumps(dict(
                            component={component!r}, syscall_address=address,
                            syscall_bytes=data[position:position+2].hex(),
                            base=values[5], capacity=values[4], injected_result=-22,
                            complete_bytes=len(output), returncode=status, child_reaped=True)))
                        sys.exit(status)
                    finally:
                        connection.close()
                        if child.poll() is None:
                            child.kill()
                        child.wait(timeout=5)
                        pathlib.Path(sock).unlink(missing_ok=True)
                """)
                result = self.build("--compiler-profile", self.source, self.output)
                self.assert_failed(result, 74)
                self.assertIn(b"munmap", result.stderr)
                observed = json.loads(receipt.read_text())
                self.assertEqual(observed["returncode"], 74)
                self.assertTrue(observed["child_reaped"])
                events = os.environ.get("C031_PIPELINE_EVENTS")
                if events:
                    with open(events, "a") as log:
                        log.write(json.dumps(observed) + "\n")


if __name__ == "__main__":
    unittest.main()
