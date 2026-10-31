"""Exercise the real foundation gate with controlled host inspector streams."""
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


class ElfInspectionTests(unittest.TestCase):
    GATE_TIMEOUT = 30

    def gate(self, mode):
        """Run a controlled inspector with owned suite files and a private process group."""
        with tempfile.TemporaryDirectory(prefix="elf-inspection-") as directory:
            commands = Path(directory)
            inspector = commands / "readelf"
            implementation = commands / "readelf.py"
            implementation.write_text(
                "import os,signal,subprocess,sys\n"
                "signal.signal(signal.SIGPIPE,signal.SIG_DFL)\n"
                f"mode={mode!r}\nreal={shutil.which('readelf')!r}\n"
                "header='-h' in sys.argv[1:]\n"
                "if mode=='tool-error' and not header:\n"
                " sys.stderr.write('controlled readelf failure\\n');sys.exit(2)\n"
                "r=subprocess.run([real,*sys.argv[1:]],capture_output=True)\n"
                "sys.stderr.buffer.write(r.stderr)\n"
                "if r.returncode:sys.exit(r.returncode)\n"
                "payload=r.stdout\n"
                "if mode=='interpreter' and not header:payload=b' INTERP \\n'+payload\n"
                "if not header and mode.startswith('stack-'):\n"
                " lines=[line for line in payload.splitlines(keepends=True) if not line.split() or line.split()[0]!=b'GNU_STACK']\n"
                " flags={'stack-executable':'R E','stack-missing':None,'stack-duplicate':'R E','stack-malformed':'RW garbage'}[mode]\n"
                " if flags is not None:lines.append((' GNU_STACK 0 0 0 0 0 '+flags+' 0x10\\n').encode())\n"
                " if mode=='stack-duplicate':lines.append(b' GNU_STACK 0 0 0 0 0 RW 0x10\\n')\n"
                " payload=b''.join(lines)\n"
                "os.write(1,payload)\n"
                "if (mode=='long-header' and header) or (mode=='interpreter' and not header):\n"
                " for _ in range(256):os.write(1,b' '+b'padding '*1024+b'\\n')\n")
            inspector.write_text("#!/bin/sh\nexec " +
                                 shlex.join([sys.executable, str(implementation)]) + ' "$@"\n')
            inspector.chmod(0o755)
            command = ["bash", str(ROOT / "tests/shared/run_suite.sh"),
                       str(ROOT / "tests/bootstrap/machine_foundation.sh")]
            with subprocess.Popen(
                command,
                env={**os.environ, "ROOT_DIR": str(ROOT), "TMP_DIR": str(commands),
                     "PATH": str(commands) + os.pathsep + os.environ["PATH"]},
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True) as process:
                try:
                    stdout, stderr = process.communicate(timeout=self.GATE_TIMEOUT)
                except BaseException:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.communicate()
                    raise
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)

    def test_EI01_complete_header_is_consumed(self):
        result = self.gate("long-header")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"PASS elf64-x86-64", result.stdout)

    def test_EI02_interpreter_cannot_hide_behind_broken_pipe(self):
        result = self.gate("interpreter")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(b"FAIL no-dynamic-interpreter", result.stderr)
        self.assertNotIn(b"PASS no-dynamic-interpreter", result.stdout)

    def test_EI03_inspector_failure_is_a_controlled_failure(self):
        result = self.gate("tool-error")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"FAIL elf-program-inspection", result.stderr)
        self.assertNotIn(b"PASS no-dynamic-interpreter", result.stdout)


    def test_EI04_core_stack_gates_reject_executable_and_missing_stack(self):
        calls = {"machine_foundation.sh": 1, "stage0.sh": 2,
                 "bootstrap_compiler_b0.sh": 1, "core_compiler_c0.sh": 4,
                 "c0_frontend.sh": 1, "c0_backend.sh": 1,
                 "c0_source_byte_tokenizer.sh": 1, "c0_source_token_parser.sh": 1}
        for name, count in calls.items():
            with self.subTest(gate=name):
                script = (ROOT / "tests/bootstrap" / name).read_text()
                self.assertEqual(script.count("elf_has_non_executable_stack"), count)
                self.assertNotIn("GNU_STACK", script, "stack rules must share the tested predicate")

    def test_EI07_all_bootstrap_gates_use_strict_stack_contract(self):
        cases = (
            ("GNU_STACK 0 0x0 0X0 0 0 RW 0x10\n", 0),
            ("GNU_STACK 0 0 0 0 0 R W 0x10\n", 0),
            ("GNU_STACK 0 0 0 0 0 0x10\n", 0),
            ("GNU_STACK 0 0xEE 0 0 0 RW 0x1E\n", 0),
            ("GNU_STACK 0 0 0 0 0 RWE 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 R E 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 RW E 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 E 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 RW garbage 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 RW\n", 1),
            ("GNU_STACK invalid 0 0 0 0 RW 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 RW bad-alignment\n", 1),
            ("GNU_STACK 0 0 0 0 0 R E 0x10\nGNU_STACK 0 0 0 0 0 RW 0x10\n", 1),
            ("GNU_STACK 0 0 0 0 0 RW 0x10\nGNU_STACK 0 0 0 0 0 RW 0x10\n", 0),
            ("filename-GNU_STACK RW\n", 1), ("", 1),
        )
        with tempfile.TemporaryDirectory(prefix="elf-stack-contract-") as directory:
            for report, expected in cases:
                with self.subTest(report=report):
                    result = subprocess.run(
                        ["bash", "-c", 'source "$1"; elf_has_non_executable_stack',
                         "stack-contract", str(ROOT / "tests/shared/lib.sh")],
                        input=report.encode(), capture_output=True, timeout=5,
                        env={**os.environ, "ROOT_DIR": str(ROOT), "TMP_DIR": directory})
                    self.assertEqual(result.returncode, expected, result.stderr)

    def test_EI08_foundation_rejects_unsafe_missing_and_malformed_stack(self):
        for mode in ("stack-executable", "stack-missing", "stack-duplicate", "stack-malformed"):
            with self.subTest(mode=mode):
                result = self.gate(mode)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(b"FAIL non-executable-stack", result.stderr)
                self.assertNotIn(b"PASS non-executable-stack", result.stdout)

    def test_EI09_load_permissions_reject_split_write_execute(self):
        with tempfile.TemporaryDirectory(prefix="elf-load-contract-") as directory:
            for flags, expected in (("RE", 0), ("R E", 0), ("RW", 0), ("R W", 0),
                                    ("E", 0), ("", 0), ("RWE", 1), ("RW E", 1),
                                    ("R W E", 1), ("R WE", 1), ("WE", 1), ("bad", 1)):
                with self.subTest(flags=flags):
                    result = subprocess.run(
                        ["bash", "-c", 'source "$1"; elf_has_no_writable_executable_load',
                         "load-contract", str(ROOT / "tests/shared/lib.sh")],
                        input=f"LOAD 0 0xEE 0 0 0 {flags} 0x1E\n".encode(),
                        capture_output=True, timeout=5,
                        env={**os.environ, "ROOT_DIR": str(ROOT), "TMP_DIR": directory})
                    self.assertEqual(result.returncode, expected, result.stderr)

    def test_EI05_interpreter_path_with_spaces_is_one_argument(self):
        with tempfile.TemporaryDirectory(prefix="elf-python-") as directory:
            interpreter = Path(directory) / "python with spaces"
            interpreter.symlink_to(sys.executable)
            with mock.patch.object(sys, "executable", str(interpreter)):
                result = self.gate("long-header")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"PASS elf64-x86-64", result.stdout)

    def test_EI06_timeout_stops_suite_descendant(self):
        with tempfile.TemporaryDirectory(prefix="elf-timeout-") as directory:
            commands = Path(directory)
            marker = commands / "descendant.pid"
            launcher = commands / "bash"
            launcher.write_text(
                f"#!{sys.executable}\n"
                "import subprocess,sys,time\n"
                "from pathlib import Path\n"
                "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],"
                "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
                f"Path({str(marker)!r}).write_text(str(child.pid))\n"
                "time.sleep(30)\n")
            launcher.chmod(0o755)

            def running(pid):
                try:
                    status = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1]
                except FileNotFoundError:
                    return False
                return status.split()[0] != "Z"

            try:
                with mock.patch.dict(os.environ, {
                        "PATH": str(commands) + os.pathsep + os.environ["PATH"]}), \
                        mock.patch.object(self, "GATE_TIMEOUT", 2):
                    with self.assertRaises(subprocess.TimeoutExpired):
                        self.gate("long-header")
                self.assertTrue(marker.exists(), "controlled suite did not spawn its child")
                pid = int(marker.read_text())
                deadline = time.monotonic() + 1
                while running(pid) and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertFalse(running(pid), "suite child survived timeout")
            finally:
                if marker.exists():
                    pid = int(marker.read_text())
                    if running(pid):
                        os.kill(pid, signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
