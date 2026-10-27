"""Real host-process controls for optional native-test evidence; no compiler oracle."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import errno
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import c031_support as support

_CLOSED_STDOUT_TARGET = ("import errno,os\ntry: os.close(1)\nexcept OSError as error:\n"
                         " if error.errno != errno.EBADF: raise\n"
                         "try: os.write(1,b'x')\nexcept OSError: raise SystemExit(78)")


class NativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="native-evidence-control-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / "archive"
        self.archive.mkdir(mode=0o700)
        environment = patch.dict(os.environ, {"NQL_NATIVE_EVIDENCE_DIR": str(self.archive)})
        environment.start()
        self.addCleanup(environment.stop)
        # Selection only: these controls execute the real host Python, not x86 guest code.
        self.selection = patch.object(support, "platform", SimpleNamespace(machine=lambda: "x86_64"))
        self.selection.start()
        self.addCleanup(self.selection.stop)

    def run_python(self, code, data=b"", **kwargs):
        return support.run_native(Path(sys.executable), data, args=("-B", "-c", code), **kwargs)

    def records(self):
        records = [(p, json.loads(p.read_text())) for p in self.archive.glob("call-*/result.json")]
        return sorted(records, key=lambda item: item[1]["started_monotonic_ns"])

    def blob(self, description):
        data = (self.archive / description["path"]).read_bytes()
        self.assertEqual(len(data), description["bytes"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), description["sha256"])
        self.assertEqual(stat.S_IMODE((self.archive / description["path"]).stat().st_mode), 0o600)
        return data

    def test_NE01_retains_exact_bytes_after_caller_cleanup(self):
        payload = b"input\0\xff\n"
        code = "import os; data=b''\nwhile True:\n b=os.read(0,4096)\n if not b: break\n data+=b\nos.write(1,data);os.write(2,b'error\\x00\\xfe');raise SystemExit(7)"
        with tempfile.TemporaryDirectory(dir=self.root) as disposable:
            executable = Path(disposable) / "host python"
            shutil.copy2(sys.executable, executable)
            expected = executable.read_bytes()
            result = support.run_native(executable, payload, args=("-B", "-c", code))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (7, payload, b"error\0\xfe"))
        retained = self.records()
        self.assertEqual(len(retained), 1, "invocation evidence must survive caller TemporaryDirectory cleanup")
        path, record = retained[0]
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        self.assertTrue((path.parent / "begin.json").exists())
        self.assertTrue((path.parent / "launched.json").exists())
        self.assertTrue(record["complete"])
        self.assertEqual(record["outcome"], "exit")
        self.assertEqual(record["returncode"], 7)
        self.assertFalse(record["timed_out"])
        self.assertGreater(record["child"]["pid"], 0)
        self.assertIn("start_ticks", record["child"])
        self.assertEqual(self.blob(record["target_before"]["blob"]), expected)
        self.assertEqual(self.blob(record["stdin"]["blob"]), payload)
        self.assertEqual(self.blob(record["stdout"]["blob"]), payload)
        self.assertEqual(self.blob(record["stderr"]["blob"]), b"error\0\xfe")

    def test_NE02_enabled_disabled_and_check_equivalence(self):
        code = "import os,sys;d=os.read(0,4096);os.write(1,d);os.write(2,b'err');sys.exit(int(sys.argv[1]))"
        for status in (0, 1, 7):
            arguments = ("-B", "-c", code, str(status))
            with patch.dict(os.environ):
                os.environ.pop("NQL_NATIVE_EVIDENCE_DIR", None)
                plain = support.run_native(Path(sys.executable), b"\0\xff", args=arguments)
            observed = support.run_native(Path(sys.executable), b"\0\xff", args=arguments)
            self.assertEqual((plain.args, plain.returncode, plain.stdout, plain.stderr),
                             (observed.args, observed.returncode, observed.stdout, observed.stderr))
        with self.assertRaises(subprocess.CalledProcessError) as error:
            self.run_python("import os;os.write(1,b'out');os.write(2,b'err');raise SystemExit(7)", check=True)
        self.assertEqual((error.exception.returncode, error.exception.output, error.exception.stderr), (7, b"out", b"err"))
        self.assertEqual(len(self.records()), 4)
        text = self.run_python("print('hello')", data="", text=True)
        self.assertEqual((text.returncode, text.stdout, text.stderr), (0, "hello\n", ""))
        self.assertEqual(self.records()[-1][1]["stdout"]["representation"], "decoded-text")
        with self.assertRaises(ValueError):
            self.run_python("pass", capture_output=True)

    def test_NE03_signal_and_timeout_remain_distinct(self):
        killed = self.run_python("import os,signal;os.write(1,b'before');os.kill(os.getpid(),signal.SIGKILL)")
        self.assertEqual((killed.returncode, killed.stdout), (-signal.SIGKILL, b"before"))
        with self.assertRaises(subprocess.TimeoutExpired) as error:
            self.run_python("import os,time;os.write(1,b'partial\\x00\\xff');os.write(2,b'wait');time.sleep(30)", timeout=1)
        self.assertEqual((error.exception.stdout, error.exception.stderr), (b"partial\0\xff", b"wait"))
        records = [r for _, r in self.records()]
        signalled = next(r for r in records if r["outcome"] == "signal")
        timeout = next(r for r in records if r["outcome"] == "timeout")
        self.assertEqual((signalled["returncode"], signalled["signal_number"], signalled["timed_out"]), (-9, 9, False))
        self.assertEqual(signalled["cleanup_actions"], [])
        self.assertTrue(timeout["timed_out"])
        self.assertEqual(self.blob(timeout["stdout"]["blob"]), b"partial\0\xff")
        self.assertEqual(timeout["cleanup_actions"][0]["reason"], "timeout")
        for record in records:
            with self.assertRaises(ProcessLookupError):
                os.kill(record["child"]["pid"], 0)

    def test_NE04_descriptor_contracts_and_external_input(self):
        external = self.root / "external"
        external.write_bytes(b"abcdef")
        with external.open("rb") as stream:
            stream.seek(2)
            result = self.run_python("pass", stdin=stream)
            self.assertEqual(stream.tell(), 2, "observer may not consume external stdin")
        self.assertEqual((result.stdout, result.stderr), (b"", b""))
        self.assertEqual(self.records()[-1][1]["stdin"]["kind"], "external-unobserved")
        with external.open("rb") as read_only:
            result = self.run_python("import os\ntry: os.write(1,b'x')\nexcept OSError: raise SystemExit(77)", stdout=read_only)
        self.assertEqual((result.returncode, result.stdout), (77, None))
        self.assertFalse(self.records()[-1][1]["stdout"]["captured"])
        # Android's host runtime may reopen a missing standard FD at startup.
        # Close it in the target as well so EBADF remains the actual oracle.
        code = _CLOSED_STDOUT_TARGET
        for enabled in (False, True):
            with patch.dict(os.environ):
                if not enabled:
                    os.environ.pop("NQL_NATIVE_EVIDENCE_DIR", None)
                result = self.run_python(code, preexec_fn=lambda: os.close(1))
                self.assertEqual(result.returncode, 78)
        with self.assertRaises(ValueError):
            self.run_python("pass", data=b"data", stdin=subprocess.DEVNULL)
        merged = self.run_python("import os;os.write(1,b'a');os.write(2,b'b')", stderr=subprocess.STDOUT)
        self.assertEqual((merged.stdout, merged.stderr), (b"ab", None))

    def test_NE05_lossless_bytes_arguments_and_cwd(self):
        directory = self.root / "working directory"
        directory.mkdir()
        argument = b"space \xff ; $(echo untouched)"
        code = "import os,sys;os.write(1,os.fsencode(sys.argv[1]));os.write(2,os.fsencode(os.getcwd()))"
        result = support.run_native(Path(sys.executable), args=("-B", "-c", code, argument), cwd=directory)
        self.assertEqual((result.stdout, result.stderr), (argument, os.fsencode(directory)))
        record = self.records()[0][1]
        self.assertEqual(record["command"][-1], {"type": "bytes", "hex": argument.hex()})
        self.assertEqual(record["cwd"], str(directory))
        self.assertFalse((directory / "untouched").exists())

    def test_NE06_spawn_and_unavailable_proc_are_explicit(self):
        executable = self.root / "not executable"
        executable.write_bytes(b"not an executable")
        executable.chmod(0o600)
        with self.assertRaises(PermissionError):
            support.run_native(executable)
        self.assertEqual(self.records()[0][1]["outcome"], "spawn-error")
        with patch.object(support, "_native_proc_identity", return_value={"available": False, "start_ticks": None, "error": "controlled proc unavailable"}):
            result = self.run_python("pass")
        self.assertEqual(result.returncode, 0)
        record = next(r for _, r in self.records() if r["outcome"] == "exit")
        self.assertFalse(record["child"]["available"])
        self.assertIn("controlled proc unavailable", record["child"]["error"])

    def test_NE07_archive_failure_never_manufactures_guest_success(self):
        marker = self.root / "launched"
        code = "from pathlib import Path;Path(" + repr(str(marker)) + ").touch()"
        with patch.dict(os.environ, {"NQL_NATIVE_EVIDENCE_DIR": str(self.root / "missing")}):
            with self.assertRaises(support.NativeEvidenceError):
                self.run_python(code)
        self.assertFalse(marker.exists())
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(os.environ, {"NQL_NATIVE_EVIDENCE_DIR": ""}):
                with self.assertRaises(support.NativeEvidenceError):
                    self.run_python(code)
        finally:
            os.chdir(previous)
        self.assertFalse(marker.exists())
        writer = support._write_native_json
        def reject_launched(path, record):
            if path.name == "launched.json":
                raise OSError("controlled archive failure after spawn")
            return writer(path, record)
        with patch.object(support, "_write_native_json", side_effect=reject_launched):
            with self.assertRaises(support.NativeEvidenceError) as error:
                self.run_python("import time;time.sleep(30)")
        record = error.exception.record
        self.assertEqual(record["outcome"], "evidence-error")
        self.assertIsNotNone(record["returncode"])
        with self.assertRaises(ProcessLookupError):
            os.kill(record["child"]["pid"], 0)
        victim = self.root / "outside"
        victim.write_bytes(b"do not change")
        payload = b"tampered blob control"
        blob_dir = self.archive / "blobs"
        blob_dir.mkdir(exist_ok=True)
        (blob_dir / hashlib.sha256(payload).hexdigest()).symlink_to(victim)
        with self.assertRaises(support.NativeEvidenceError):
            self.run_python(code, payload)
        self.assertEqual(victim.read_bytes(), b"do not change")
        self.assertFalse(marker.exists())

    def test_NE08_cancellation_reaps_only_owned_child(self):
        helper_dir = str(Path(support.__file__).resolve().parent)
        code = "import sys;sys.path.insert(0," + repr(helper_dir) + ");import c031_support as s;from pathlib import Path;from types import SimpleNamespace;s.platform=SimpleNamespace(machine=lambda:'x86_64')\ntry: s.run_native(Path(sys.executable),args=('-B','-c','import time;time.sleep(30)'),timeout=20)\nexcept KeyboardInterrupt: raise SystemExit(42)"
        sibling = subprocess.Popen([sys.executable, "-B", "-c", "import time;time.sleep(30)"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        driver = subprocess.Popen([sys.executable, "-B", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 5
            while not list(self.archive.glob("call-*/launched.json")):
                self.assertLess(time.monotonic(), deadline, "driver did not record launched child")
                time.sleep(0.01)
            os.kill(driver.pid, signal.SIGINT)
            output, error = driver.communicate(timeout=5)
            self.assertEqual((driver.returncode, output, error), (42, b"", b""))
            record = self.records()[0][1]
            self.assertEqual(record["outcome"], "cancelled")
            self.assertEqual(record["exception"]["type"], "KeyboardInterrupt")
            with self.assertRaises(ProcessLookupError):
                os.kill(record["child"]["pid"], 0)
            self.assertIsNone(sibling.poll(), "observer must not signal unrelated sibling")
        finally:
            for process in (driver, sibling):
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)

    def test_NE09_executable_change_is_flagged_not_attested(self):
        executable = self.root / "replaceable-python"
        shutil.copy2(sys.executable, executable)
        before = executable.read_bytes()
        replacement = self.root / "replacement"
        replacement.write_bytes(b"replaced after exec")
        code = "import os;os.replace(" + repr(str(replacement)) + "," + repr(str(executable)) + ")"
        result = support.run_native(executable, args=("-B", "-c", code))
        self.assertEqual(result.returncode, 0)
        record = self.records()[0][1]
        self.assertTrue(record["target_changed"])
        self.assertEqual(self.blob(record["target_before"]["blob"]), before)
        self.assertEqual(record["target_after"]["sha256"], hashlib.sha256(executable.read_bytes()).hexdigest())

    def test_NE10_parallel_invocations_have_unique_complete_records(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda value: self.run_python("import os;os.write(1,os.read(0,4096))", bytes([value])), range(8)))
        self.assertEqual([r.stdout for r in results], [bytes([i]) for i in range(8)])
        retained = self.records()
        self.assertEqual(len(retained), 8)
        self.assertEqual(len({r["child"]["pid"] for _, r in retained}), 8)
        self.assertTrue(all(r["complete"] and r["outcome"] == "exit" for _, r in retained))
        self.assertEqual(len(list(self.archive.glob("call-*/begin.json"))), 8)


    def test_NE11_fifo_observation_cannot_outlive_watchdog(self):
        for phase in ("after", "before"):
            with self.subTest(phase=phase):
                archive = self.root / (phase + "-archive")
                archive.mkdir(mode=0o700)
                executable = self.root / (phase + "-python")
                if phase == "after":
                    shutil.copy2(sys.executable, executable)
                    code = "import os;os.unlink(" + repr(str(executable)) + ");os.mkfifo(" + repr(str(executable)) + ");os.write(1,b'done')"
                else:
                    os.mkfifo(executable)
                    code = "raise SystemExit(99)"
                script = "import sys,json;sys.path.insert(0," + repr(str(Path(support.__file__).parent)) + ");import c031_support as s;from pathlib import Path;from types import SimpleNamespace;s.platform=SimpleNamespace(machine=lambda:'x86_64')\ntry:\n r=s.run_native(Path(" + repr(str(executable)) + "),args=('-B','-c'," + repr(code) + "),timeout=0.5)\n print(json.dumps(dict(returncode=r.returncode,stdout=r.stdout.hex())))\nexcept s.NativeEvidenceError:\n print(json.dumps(dict(evidence_error=True)))"
                try:
                    result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True,
                        timeout=2, env=dict(os.environ, NQL_NATIVE_EVIDENCE_DIR=str(archive)))
                except subprocess.TimeoutExpired:
                    self.fail("nonregular file observation exceeded external watchdog")
                self.assertEqual((result.returncode, result.stderr), (0, b""))
                answer = json.loads(result.stdout)
                if phase == "before":
                    self.assertEqual(answer, {"evidence_error": True})
                    self.assertEqual(list(archive.glob("call-*/launched.json")), [])
                else:
                    self.assertEqual(answer, {"returncode": 0, "stdout": b"done".hex()})
                    record = json.loads(next(archive.glob("call-*/result.json")).read_text())
                    self.assertTrue(record["target_changed"])
                    self.assertIn("not a regular file", record["target_after"]["message"])
                    with self.assertRaises(ProcessLookupError):
                        os.kill(record["child"]["pid"], 0)

    def test_NE12_explicit_executable_bytes_survive_cleanup(self):
        for selection in ("absolute", "relative", "PATH"):
            with self.subTest(selection=selection):
                with tempfile.TemporaryDirectory(dir=self.root) as disposable:
                    work = Path(disposable)
                    requested = work / "argv zero"
                    requested.write_bytes(b"logical target is not the selected executable\n")
                    (work / "bin").mkdir()
                    selected = work / "bin/selected-python"
                    shutil.copy2(sys.executable, selected)
                    expected = selected.read_bytes()
                    chosen = str(selected) if selection == "absolute" else ("./bin/selected-python" if selection == "relative" else "selected-python")
                    result = support.run_native(requested, args=("-B", "-c", "print('OK')"),
                        executable=chosen, cwd=work, env=dict(os.environ, PATH="bin"))
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"OK\n", b""))
                self.assertFalse(selected.exists())
                record = self.records()[-1][1]
                available = record.get("executable_candidates_before", [])
                self.assertTrue(available, "known executable= selection must be retained separately from argv[0]")
                match = next((entry for entry in available if entry.get("sha256") == hashlib.sha256(expected).hexdigest()), None)
                self.assertIsNotNone(match, "selected executable bytes disappeared with disposable directory")
                self.assertEqual(self.blob(match["blob"]), expected)
                self.assertEqual(record["executable_override"], {"type": "str", "hex": os.fsencode(chosen).hex()})


    def test_NE13_symlink_parent_paths_keep_kernel_lookup_semantics(self):
        for selection in ("relative", "cwd-PATH"):
            with self.subTest(selection=selection):
                with tempfile.TemporaryDirectory(dir=self.root) as disposable:
                    parent = Path(disposable)
                    work, other = parent / "work", parent / "other"
                    work.mkdir()
                    (other / "subdir").mkdir(parents=True)
                    (work / "link").symlink_to(other / "subdir", target_is_directory=True)
                    selected = other / "selected-python"
                    shutil.copy2(sys.executable, selected)
                    expected = selected.read_bytes()
                    (work / "selected-python").write_bytes(b"not the selected executable")
                    requested = work / "argv0"
                    requested.write_bytes(b"logical target")
                    cwd = work if selection == "relative" else str(work / "link") + "/.."
                    chosen = "./link/../selected-python" if selection == "relative" else "selected-python"
                    result = support.run_native(requested, args=("-B", "-c", "import os;print(os.getcwd())"),
                        executable=chosen, cwd=cwd, env=dict(os.environ, PATH="."))
                    expected_cwd = work if selection == "relative" else other
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, os.fsencode(expected_cwd) + b"\n", b""))
                record = self.records()[-1][1]
                self.assertEqual(record["cwd"], str(expected_cwd))
                match = next((a for a in record["executable_candidates_before"] if a["sha256"] == hashlib.sha256(expected).hexdigest()), None)
                self.assertIsNotNone(match, "symlink/.. lookup archived a decoy instead of selected executable")
                self.assertEqual(self.blob(match["blob"]), expected)
                self.assertEqual(match["path"], str(selected))

    def test_NE14_nonregular_rejection_and_replacement_do_not_leak_fds(self):
        def directory_fds(target):
            result = set()
            for item in Path("/proc/self/fd").iterdir():
                try:
                    if os.readlink(item) == str(target):
                        result.add(int(item.name))
                except FileNotFoundError:
                    pass
            return result
        for phase in ("before", "after"):
            with self.subTest(phase=phase):
                target = self.root / (phase + "-directory")
                before = directory_fds(target)
                try:
                    if phase == "before":
                        target.mkdir()
                        for _ in range(3):
                            with self.assertRaises(support.NativeEvidenceError):
                                support.run_native(target)
                    else:
                        shutil.copy2(sys.executable, target)
                        code = "import os;os.unlink(" + repr(str(target)) + ");os.mkdir(" + repr(str(target)) + ");os.write(1,b'done')"
                        result = support.run_native(target, args=("-B", "-c", code))
                        self.assertEqual((result.returncode, result.stdout), (0, b"done"))
                        self.assertTrue(self.records()[-1][1]["target_changed"])
                    self.assertEqual(directory_fds(target), before, "observation leaked raw directory FDs")
                finally:
                    for descriptor in directory_fds(target) - before:
                        os.close(descriptor)

        with self.subTest(phase="blob-directory"):
            payload = b"directory at a blob filename"
            target = self.archive / "blobs" / hashlib.sha256(payload).hexdigest()
            target.parent.mkdir(exist_ok=True)
            target.mkdir()
            before = directory_fds(target)
            try:
                with self.assertRaises(support.NativeEvidenceError):
                    self.run_python("pass", payload)
                self.assertEqual(directory_fds(target), before, "invalid blob leaked its directory FD")
            finally:
                for descriptor in directory_fds(target) - before:
                    os.close(descriptor)

    def test_NE15_unused_bad_PATH_candidate_is_observation_only(self):
        good, bad = self.root / "good", self.root / "bad"
        good.mkdir()
        bad.mkdir()
        selected = good / "selected-python"
        shutil.copy2(sys.executable, selected)
        (bad / "selected-python").symlink_to("selected-python")
        requested = self.root / "argv0"
        requested.write_bytes(b"logical target")
        result = support.run_native(requested, args=("-B", "-c", "print('OK')"),
            executable="selected-python", cwd=self.root, env=dict(os.environ, PATH="good:bad"))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"OK\n", b""))
        record = self.records()[-1][1]
        self.assertEqual(self.blob(record["executable_candidates_before"][0]["blob"]), selected.read_bytes())
        self.assertTrue(any(a.get("errno") == errno.ELOOP for a in record["executable_candidates_unavailable"]))


    def test_NE16_open_unlinked_executable_retains_bytes_without_consuming_fd(self):
        with tempfile.TemporaryDirectory(dir=self.root) as disposable:
            work = Path(disposable)
            requested = work / "argv0"
            requested.write_bytes(b"logical target")
            selected = work / "selected-python"
            shutil.copy2(sys.executable, selected)
            expected = selected.read_bytes()
            with selected.open("rb") as handle:
                handle.seek(7)
                descriptor = handle.fileno()
                selected.unlink()
                choice = f"/proc/self/fd/{descriptor}"
                result = support.run_native(requested, args=("-B", "-c", "print('OK')"),
                    executable=choice, pass_fds=(descriptor,))
                self.assertEqual(handle.tell(), 7, "observation consumed the caller's passed FD")
                self.assertEqual(os.fstat(descriptor).st_size, len(expected))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"OK\n", b""))
        record = self.records()[-1][1]
        match = next((a for a in record["executable_candidates_before"] if a["sha256"] == hashlib.sha256(expected).hexdigest()), None)
        self.assertIsNotNone(match, "a usable proc FD path must be read even without a canonical pathname")
        self.assertEqual(self.blob(match["blob"]), expected)
        self.assertEqual(match["lookup_path"], choice)


    def test_NE17_deleted_parent_cwd_does_not_reject_valid_launch(self):
        child_cwd = self.root / "surviving-child-cwd"
        child_cwd.mkdir()
        actual_python = Path(sys.executable).resolve(strict=True)
        actual_shell = Path(shutil.which("sh")).resolve(strict=True)
        for phase in ("absolute", "inherited"):
            with self.subTest(phase=phase):
                saved = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
                gone = self.root / (phase + "-gone-cwd")
                gone.mkdir()
                try:
                    os.chdir(gone)
                    gone.rmdir()
                    binary = actual_python if phase == "absolute" else actual_shell
                    options = dict(args=("-B", "-c", "import os;print(os.getcwd())"), cwd=child_cwd) if phase == "absolute" else dict(args=("-c", "exit 0"))
                    with patch.dict(os.environ):
                        os.environ.pop("NQL_NATIVE_EVIDENCE_DIR", None)
                        plain = support.run_native(binary, **options)
                    observed = support.run_native(binary, **options)
                    self.assertEqual((observed.returncode, observed.stdout, observed.stderr),
                                     (plain.returncode, plain.stdout, plain.stderr))
                    self.assertEqual(observed.returncode, 0)
                finally:
                    os.fchdir(saved)
                    os.close(saved)
                record = self.records()[-1][1]
                self.assertTrue(record["complete"])
                if phase == "absolute":
                    self.assertEqual(record["cwd_lookup"], str(child_cwd))


    def test_NE19_fd_error_oracle_accepts_already_closed_stdout(self):
        for enabled in (False, True):
            with self.subTest(evidence=enabled), patch.dict(os.environ):
                if not enabled:
                    os.environ.pop("NQL_NATIVE_EVIDENCE_DIR", None)
                result = self.run_python("import os;os.close(1)\n" + _CLOSED_STDOUT_TARGET)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (78, b"", b""))

    def test_NE20_standard_fd_fault_survives_host_runtime_startup(self):
        try:
            from standard_fd_fault import invalidate_standard_fd
        except ImportError:
            self.fail("missing portable standard-descriptor fault fixture")
        for descriptor in (0, 1, 2):
            with self.subTest(descriptor=descriptor):
                operation = "os.read(0,1)" if descriptor == 0 else f"os.write({descriptor},b'x')"
                code = ("import errno,os\ntry: " + operation + "\nexcept OSError as error:\n"
                        " raise SystemExit(77 if error.errno==errno.EBADF else 88)\nraise SystemExit(66)")
                result = self.run_python(code, preexec_fn=lambda: invalidate_standard_fd(descriptor))
                self.assertEqual((result.returncode, result.stdout, result.stderr), (77, b"", b""))

    def test_NE18_publication_does_not_require_hard_links(self):
        payload = b"independent Android evidence\0\xff"
        with patch.object(support.os, "link", create=True,
                          side_effect=NotImplementedError("Android has no os.link")):
            try:
                result = self.run_python("import os;os.write(1,os.read(0,4096))", payload)
            except support.NativeEvidenceError as error:
                self.fail(f"evidence publication required unsupported hard links: {error.original_error}")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, payload, b""))
        record = self.records()[0][1]
        self.assertTrue(record["complete"])
        self.assertEqual(self.blob(record["stdin"]["blob"]), payload)
        self.assertEqual(self.blob(record["stdout"]["blob"]), payload)
        self.assertFalse(list((self.archive / "blobs").glob(".blob-*")))


if __name__ == "__main__":
    # These controls test kernel path lookup, not Termux's convenience exec
    # interceptor (which rewrites symlink/.. and deleted /proc/self/fd paths).
    # A fresh interpreter is needed: altering a child's env cannot unload a
    # library already interposing execve in the parent after fork.
    if sys.platform == "android":
        preload = os.environ.get("LD_PRELOAD", "").replace(":", " ").split()
        retained = [p for p in preload if Path(p).name not in (
            "libtermux-exec.so", "libtermux-exec-ld-preload.so")]
        if retained != preload:
            environment = dict(os.environ)
            if retained:
                environment["LD_PRELOAD"] = ":".join(retained)
            else:
                environment.pop("LD_PRELOAD", None)
            os.execve(sys.executable, [sys.executable, *sys.orig_argv[1:]], environment)
    unittest.main()
