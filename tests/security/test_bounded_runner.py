"""Check that the host-only assurance runner detects failures, not retries them."""
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


if __name__ == "__main__":
    unittest.main()
