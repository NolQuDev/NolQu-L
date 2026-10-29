"""Check that the host-only assurance runner detects failures, not retries them."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

try:
    from bounded_runner import AssuranceFailure, BoundedRunner
except ImportError:
    AssuranceFailure = BoundedRunner = None


class BoundedRunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(BoundedRunner, "missing bounded assurance runner")
        self.tmp = tempfile.TemporaryDirectory(prefix="nql-assurance-control-")
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "run"

    def runner(self, **options):
        return BoundedRunner(self.directory, **options)

    def test_nonzero_status_and_binary_streams_are_preserved(self):
        runner = self.runner()
        result = runner.run("nonzero", [sys.executable, "-c",
                            "import sys;sys.stdout.buffer.write(b'\\x00NQL');"
                            "sys.stderr.write('cause\\n');sys.exit(7)"], b"")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (7, b"\0NQL", b"cause\n"))
        self.assertEqual(len(runner.records), 1)
        self.assertEqual(runner.records[0]["exit_code"], 7)

    def test_timeout_is_failure_and_retains_evidence(self):
        runner = self.runner(timeout=0.2)
        with self.assertRaisesRegex(AssuranceFailure, "timeout"):
            runner.run("hang", [sys.executable, "-c", "import time;time.sleep(60)"], b"")
        record = runner.records[0]
        self.assertTrue(record["timed_out"])
        with self.assertRaises(ProcessLookupError):
            os.kill(record["pid"], 0)
        self.assertTrue((self.directory / record["stdout"]["path"]).is_file())

    def test_signal_is_failure_not_ordinary_rejection(self):
        runner = self.runner()
        with self.assertRaisesRegex(AssuranceFailure, "signal"):
            runner.run("signal", [sys.executable, "-c",
                                  "import os,signal;os.kill(os.getpid(),signal.SIGTERM)"], b"")
        self.assertEqual(runner.records[0]["exit_code"], -signal.SIGTERM)

    def test_output_limit_is_failure(self):
        runner = self.runner(output_limit=4096)
        with self.assertRaisesRegex(AssuranceFailure, "output limit|signal"):
            runner.run("flood", [sys.executable, "-c",
                                 "import os;os.write(1,b'x'*8192)"], b"")
        self.assertLessEqual((self.directory / "0001.stdout").stat().st_size, 4096)

    def test_budget_and_input_limits_fail_before_execution(self):
        runner = self.runner(max_input=4)
        with self.assertRaisesRegex(AssuranceFailure, "input limit"):
            runner.run("input", [sys.executable, "-c", "raise AssertionError('executed')"], b"12345")
        self.assertEqual(runner.records, [])
        runner.deadline = 0
        with self.assertRaisesRegex(AssuranceFailure, "budget"):
            runner.run("budget", [sys.executable, "-c", "raise AssertionError('executed')"], b"")
        self.assertEqual(runner.records, [])

    def test_evidence_directory_is_never_overwritten(self):
        self.directory.mkdir()
        marker = self.directory / "previous"
        marker.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            self.runner()
        self.assertEqual(marker.read_bytes(), b"keep")

    def test_normal_leader_exit_terminates_and_reaps_descendant(self):
        runner = self.runner()
        pid_file = Path(self.tmp.name) / "descendant.pid"
        grandchild = "import os,pathlib,sys,time;os.setsid();pathlib.Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(60)"
        leader = ("import pathlib,subprocess,sys,time;"
                  "subprocess.Popen([sys.executable,'-c',sys.argv[2],sys.argv[1]]);"
                  "p=pathlib.Path(sys.argv[1]);"
                  "\nwhile not p.exists(): time.sleep(.01)\n")
        pid = None
        sibling = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            result = runner.run("descendant", [sys.executable, "-c", leader,
                                               str(pid_file), grandchild], b"")
            self.assertEqual(result.returncode, 0)
            pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            self.assertIsNone(sibling.poll(), "unrelated child was terminated or reaped")
        finally:
            sibling.terminate()
            sibling.wait()
            if pid is None and pid_file.exists():
                pid = int(pid_file.read_text())
            if pid is not None:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_exited_orphan_is_reaped_while_target_is_still_running(self):
        runner = self.runner(timeout=5)
        target = r'''
import os,pathlib,sys,time
read_end,write_end=os.pipe()
parent=os.fork()
if parent == 0:
    os.close(read_end)
    orphan=os.fork()
    if orphan == 0:
        os.write(write_end,str(os.getpid()).encode())
    os._exit(0)
os.close(write_end)
orphan=int(os.read(read_end,64))
os.close(read_end)
os.waitpid(parent,0)
path=pathlib.Path('/proc')/str(orphan)
deadline=time.monotonic()+1
while path.exists() and time.monotonic()<deadline:
    time.sleep(.01)
if path.exists():
    print(path.joinpath('stat').read_text())
    sys.exit(17)
print('orphan reaped before target exit')
'''
        result = runner.run("live-reaping", [sys.executable, "-c", target], b"")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, b"orphan reaped before target exit\n")
        self.assertGreaterEqual(runner.records[0]["control"]["reaped_descendants"], 1)

    def test_cancellation_cleans_child_and_preserves_failure_record(self):
        runner = self.runner(timeout=5)
        children = []
        original_popen = subprocess.Popen

        def launch(*args, **kwargs):
            child = original_popen(*args, **kwargs)
            children.append(child)
            return child

        def cancel(signum, frame):
            raise KeyboardInterrupt("assurance cancellation control")

        previous = signal.signal(signal.SIGALRM, cancel)
        try:
            signal.setitimer(signal.ITIMER_REAL, 0.5)
            with mock.patch("bounded_runner.subprocess.Popen", side_effect=launch):
                with self.assertRaises(KeyboardInterrupt):
                    runner.run("cancel", [sys.executable, "-c", "import time;time.sleep(60)"], b"")
            self.assertTrue(runner.records, "cancellation failure evidence was lost")
            self.assertTrue(runner.records[0]["cancelled"])
            self.assertIsNotNone(children[0].poll())
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
            for child in children:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()

    def test_partial_setup_failure_retains_summary(self):
        invalid = Path(self.tmp.name) / "invalid.json"
        invalid.write_text("{")
        evidence = Path(self.tmp.name) / "partial"
        script = (
            "import pathlib,sys,unittest;import test_native_assurance as m;"
            "m.CORPUS=pathlib.Path(sys.argv[1]);"
            "p=unittest.main(module=m,argv=['partial',"
            "'NativeBoundaryAssurance.test_seed_sources_and_deterministic_mutations'],exit=False);"
            "m.write_summary(p.result);sys.exit(not p.result.wasSuccessful())")
        env = dict(os.environ, NQL_ASSURANCE_OUTPUT=str(evidence))
        result = subprocess.run([sys.executable, "-B", "-c", script, str(invalid)],
                                cwd=Path(__file__).parent, env=env,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        import json
        summary = json.loads((evidence / "summary.json").read_text())
        self.assertFalse(summary["passed"])
        self.assertEqual((summary["errors"], summary["invocations"]), (1, 0))
        self.assertTrue((evidence / "corpus.json").is_file(), "exact failed corpus was lost")
        self.assertEqual((evidence / "corpus.json").read_bytes(), b"{")
        self.assertIn(b"ASSURANCE_EVIDENCE=", result.stderr)

    def test_signal_immediately_after_launch_defers_until_registered(self):
        runner = self.runner(timeout=5)
        children = []
        original_popen = subprocess.Popen

        def launch(*args, **kwargs):
            child = original_popen(*args, **kwargs)
            children.append(child)
            # Real signal at the acquisition gap: Popen has created a process,
            # but its caller has not received/assigned the process handle yet.
            os.kill(os.getpid(), signal.SIGINT)
            return child

        try:
            with mock.patch("bounded_runner.subprocess.Popen", side_effect=launch):
                with self.assertRaises(KeyboardInterrupt):
                    runner.run("acquisition-cancel", [sys.executable, "-c", "import time;time.sleep(60)"], b"")
            self.assertTrue(runner.records, "acquisition cancellation lost its process/evidence")
            self.assertTrue(runner.records[0]["cancelled"])
            self.assertIsNotNone(children[0].poll())
        finally:
            for child in children:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()

    def test_interrupted_supervisor_cannot_report_ordinary_status(self):
        # Synthetic control-protocol mutation, not a claimed OS race reproduction.
        fake = ("import json,pathlib,sys;pathlib.Path(sys.argv[1]).write_text("
                "json.dumps({'complete':True,'target_exit_code':int(sys.argv[2]),"
                "'interrupted':'InterruptedError'}))")
        for status in (0, 1):
            with self.subTest(status=status):
                directory = Path(self.tmp.name) / f"interrupted-{status}"
                runner = BoundedRunner(directory)
                with mock.patch("bounded_runner._SUPERVISOR", fake):
                    with self.assertRaisesRegex(AssuranceFailure, "supervisor"):
                        runner.run("interrupted-control", [str(status)], b"")

    def test_malformed_control_retains_failed_invocation(self):
        # Synthetic protocol mutations; process/file/retention behavior is real.
        # Removing controlled ingestion must lose these records and fail here.
        before = len(os.listdir("/proc/self/fd"))
        payloads = (b"{", b"", b"[]", b"null", b"false", b"7", b"\xff",
                    b'{"complete":' + b"[" * 1100 + b"0" + b"]" * 1100 + b"}")
        for index, payload in enumerate(payloads):
            with self.subTest(payload=index):
                runner = BoundedRunner(Path(self.tmp.name) / f"malformed-{index}")
                fixture = ("import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes("
                           + repr(payload) + ");sys.stdout.buffer.write(b'fixture bytes\\n')")
                failure = None
                try:
                    with mock.patch("bounded_runner._SUPERVISOR", fixture):
                        runner.run("malformed-control", ["unused"], b"input bytes")
                except Exception as error:
                    failure = error
                self.assertIsInstance(failure, AssuranceFailure)
                self.assertEqual(len(runner.records), 1)
                record = runner.records[0]
                self.assertFalse(record["supervisor_ok"])
                self.assertIn("control_error", record)
                self.assertIn("type", record["control_error"])
                self.assertEqual((runner.directory / record["input"]["path"]).read_bytes(),
                                 b"input bytes")
                self.assertEqual((runner.directory / record["stdout"]["path"]).read_bytes(),
                                 b"fixture bytes\n")
                self.assertEqual(json.loads((runner.directory / "invocations.json").read_text())
                                 ["records"], runner.records)
        self.assertEqual(len(os.listdir("/proc/self/fd")), before,
                         "control read/decode failure leaked a descriptor")

    def test_control_size_bound_preserves_exact_limit_and_rejects_overflow(self):
        # The literal 4 KiB wire budget is checked through actual file ingestion.
        control = b'{"complete":true,"target_exit_code":0,"reaped_descendants":0,"target_pid":123}'
        for size in (4096, 4097):
            with self.subTest(bytes=size):
                payload = control + b" " * (size - len(control))
                runner = BoundedRunner(Path(self.tmp.name) / f"control-size-{size}")
                fixture = ("import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes("
                           + repr(payload) + ")")
                failure = result = None
                try:
                    with mock.patch("bounded_runner._SUPERVISOR", fixture):
                        result = runner.run("control-size", ["unused"], b"")
                except Exception as error:
                    failure = error
                self.assertEqual(len(runner.records), 1)
                if size == 4096:
                    self.assertIsNone(failure)
                    self.assertEqual(result.returncode, 0)
                    self.assertTrue(runner.records[0]["supervisor_ok"])
                else:
                    self.assertIsInstance(failure, AssuranceFailure)
                    self.assertFalse(runner.records[0]["supervisor_ok"])
                    self.assertIn("type", runner.records[0]["control_error"])
                self.assertEqual((runner.directory / "0001.control.json").stat().st_size, size)

    def assert_waited_child_usage(self, record):
        self.assertIn("waited_child_usage", record["control"],
                      "final control lost the waited-child resource observation")
        usage = record["control"]["waited_child_usage"]
        self.assertIs(usage["available"], True)
        self.assertEqual(usage["source"], "getrusage(RUSAGE_CHILDREN)")
        for name in ("user_cpu_seconds", "system_cpu_seconds"):
            self.assertIs(type(usage[name]), float)
            self.assertTrue(math.isfinite(usage[name]))
            self.assertGreaterEqual(usage[name], 0)
        self.assertIs(type(usage["maxrss_kib"]), int)
        self.assertGreaterEqual(usage["maxrss_kib"], 0)
        return usage

    def test_waited_child_usage_records_resources_and_terminal_status(self):
        allocation = ("import os,signal,sys;buf=bytearray(16*1024*1024);"
                      "buf[::4096]=b'N'*len(buf[::4096]);"
                      "os.write(1,b'\\x00NQL');os.write(2,b'usage fixture\\n');")
        runner = self.runner()
        for status in (7, -signal.SIGTERM):
            with self.subTest(status=status):
                tail = "sys.exit(7)" if status == 7 else "os.kill(os.getpid(),signal.SIGTERM)"
                if status == 7:
                    result = runner.run("usage-exit", [sys.executable, "-c", allocation + tail], b"")
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (7, b"\0NQL", b"usage fixture\n"))
                else:
                    with self.assertRaisesRegex(AssuranceFailure, "signal"):
                        runner.run("usage-signal", [sys.executable, "-c", allocation + tail], b"")
                record = runner.records[-1]
                self.assertEqual(record["exit_code"], status)
                usage = self.assert_waited_child_usage(record)
                self.assertGreaterEqual(usage["maxrss_kib"], 16 * 1024)
                self.assertEqual((runner.directory / record["stdout"]["path"]).read_bytes(), b"\0NQL")
                self.assertEqual(json.loads((runner.directory / "invocations.json").read_text())
                                 ["records"], runner.records)

    def test_waited_child_usage_is_private_to_each_invocation(self):
        # A waited grandchild must count, but never a preceding invocation.
        allocation = ("buf=bytearray(48*1024*1024);"
                      "buf[::4096]=b'N'*len(buf[::4096])")
        parent = "import subprocess,sys;subprocess.run([sys.executable,'-c',sys.argv[1]],check=True)"
        runner = self.runner()
        self.assertEqual(runner.run("usage-tree", [sys.executable, "-c", parent, allocation], b"").returncode, 0)
        self.assertEqual(runner.run("usage-light", [sys.executable, "-c", "pass"], b"").returncode, 0)
        heavy, light = (self.assert_waited_child_usage(record) for record in runner.records)
        self.assertGreaterEqual(heavy["maxrss_kib"], 48 * 1024)
        self.assertLess(light["maxrss_kib"], heavy["maxrss_kib"],
                        "usage leaked from another invocation or ignored the waited grandchild")

    def test_waited_child_usage_follows_supervisor_cleanup(self):
        runner = self.runner()
        target = r'''
import os,pathlib,signal,sys,time
control=pathlib.Path(sys.argv[1])
deadline=time.monotonic()+2
while not control.exists() and time.monotonic()<deadline:
    time.sleep(.01)
if not control.exists():
    sys.exit(19)
buf=bytearray(16*1024*1024)
buf[::4096]=b'N'*len(buf[::4096])
os.kill(os.getppid(),signal.SIGTERM)
time.sleep(60)
'''
        with self.assertRaisesRegex(AssuranceFailure, "supervisor/cleanup"):
            runner.run("usage-cleanup", [sys.executable, "-c", target,
                                         str(runner.directory / "0001.control.json")], b"")
        record = runner.records[0]
        self.assertIs(record["control"]["complete"], True)
        self.assertIn("interrupted", record["control"])
        self.assertEqual(record["control"]["target_exit_code"], -signal.SIGKILL)
        self.assertGreaterEqual(self.assert_waited_child_usage(record)["maxrss_kib"], 16 * 1024)
        with self.assertRaises(ProcessLookupError):
            os.kill(record["control"]["target_pid"], 0)

    def test_unavailable_child_usage_preserves_target_result(self):
        from bounded_runner import _SUPERVISOR
        for index, error in enumerate(("OSError(5,'accounting fixture')",
                                       "AttributeError('accounting fixture')")):
            with self.subTest(error=error):
                fixture = ("import resource\ndef unavailable(*args):\n raise " + error +
                           "\nresource.getrusage=unavailable\n" + _SUPERVISOR)
                runner = BoundedRunner(Path(self.tmp.name) / f"usage-unavailable-{index}")
                with mock.patch("bounded_runner._SUPERVISOR", fixture):
                    result = runner.run("usage-unavailable", [sys.executable, "-c",
                                        "import sys;sys.stdout.buffer.write(b'\\x00NQL');sys.exit(7)"], b"")
                self.assertEqual((result.returncode, result.stdout, result.stderr), (7, b"\0NQL", b""))
                control = runner.records[0]["control"]
                self.assertIn("waited_child_usage", control)
                usage = control["waited_child_usage"]
                self.assertIs(usage["available"], False)
                self.assertEqual(usage["source"], "getrusage(RUSAGE_CHILDREN)")
                self.assertEqual(usage["error"]["type"], "OSError" if index == 0 else "AttributeError")
                self.assertEqual(usage["error"]["errno"], 5 if index == 0 else None)
                self.assertIn("accounting fixture", usage["error"]["message"])
                self.assertNotIn("maxrss_kib", usage, "unavailable usage became a zero measurement")

    def test_nonregular_control_never_blocks_or_reports_success(self):
        # An outer watchdog bounds the old FIFO read. The synthetic producer
        # exits before metadata ingestion, leaving no live target to clean up.
        probe = r'''
import json,pathlib,sys
from unittest import mock
from bounded_runner import BoundedRunner
kind=sys.argv[2]
valid='{"complete":true,"target_exit_code":0,"reaped_descendants":0,"target_pid":123}'
actions={
 'fifo':"os.mkfifo(p)",
 'directory':"p.mkdir()",
 'symlink':"q=p.with_suffix('.foreign');q.write_text("+repr(valid)+");p.symlink_to(q.name)",
 'missing':"pass",
}
fixture="import os,pathlib,sys;p=pathlib.Path(sys.argv[1]);"+actions[kind]
runner=BoundedRunner(pathlib.Path(sys.argv[1])/'calls',timeout=2,budget=4)
error=None
try:
 with mock.patch('bounded_runner._SUPERVISOR',fixture):
  runner.run('nonregular-control',['unused'],b'preserved input')
except Exception as failure:
 error=type(failure).__name__
print(json.dumps({'error':error,'records':len(runner.records),
 'manifest':(runner.directory/'invocations.json').is_file(),
 'supervisor_ok':runner.records[-1]['supervisor_ok'] if runner.records else None,
 'control_error':bool(runner.records and runner.records[-1].get('control_error')),
 'input':(runner.directory/'0001.input').read_text()}))
'''
        for kind in ("fifo", "directory", "symlink", "missing"):
            with self.subTest(kind=kind):
                try:
                    result = subprocess.run([sys.executable, "-B", "-c", probe,
                                             str(Path(self.tmp.name) / kind), kind],
                                            cwd=Path(__file__).parent, capture_output=True,
                                            timeout=5)
                except subprocess.TimeoutExpired:
                    self.fail(f"{kind}: supervisor metadata blocked beyond the host watchdog")
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report, dict(error="AssuranceFailure", records=1,
                    manifest=True, supervisor_ok=False, control_error=True,
                    input="preserved input"))


if __name__ == "__main__":
    unittest.main()
