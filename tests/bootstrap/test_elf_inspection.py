"""Exercise the real foundation gate with controlled host inspector streams."""
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ElfInspectionTests(unittest.TestCase):
    def gate(self, mode):
        with tempfile.TemporaryDirectory(prefix="elf-inspection-") as directory:
            commands = Path(directory)
            inspector = commands / "readelf"
            inspector.write_text(
                f"#!{sys.executable}\n"
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
                "os.write(1,payload)\n"
                "if (mode=='long-header' and header) or (mode=='interpreter' and not header):\n"
                " for _ in range(256):os.write(1,b' '+b'padding '*1024+b'\\n')\n")
            inspector.chmod(0o755)
            return subprocess.run(
                ["bash", str(ROOT / "tests/shared/run_suite.sh"),
                 str(ROOT / "tests/bootstrap/machine_foundation.sh")],
                env={**os.environ, "ROOT_DIR": str(ROOT),
                     "PATH": str(commands) + os.pathsep + os.environ["PATH"]},
                capture_output=True, timeout=30)

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
        script = (ROOT / "tests/bootstrap/core_compiler_c0.sh").read_text()
        programs = [program for program in re.findall(r"awk '([^']*GNU_STACK[^']*)'", script)
                    if "found=1;" in program]
        self.assertEqual(len(programs), 4)
        for program in programs:
            for flags, expected in (("RW", 0), ("RWE", 1), (None, 1)):
                with self.subTest(checker=program, flags=flags):
                    report = "" if flags is None else f"GNU_STACK 0 0 0 0 0 {flags} 0x10\n"
                    result = subprocess.run(["awk", program], input=report.encode(),
                                            capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
