"""Runtime and malformed-AST oracle; only B0 builds the tested compiler."""

import itertools
import hashlib
import fcntl
import os
from pathlib import Path
import platform
import random
import select
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest

from standard_fd_fault import invalidate_standard_fd

from c031_support import candidate_binary, encode_profile_source


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "bootstrap/compiler/c0/x86_64-linux"
FRONTEND = candidate_binary("C0_FRONTEND", STAGE / "c0-frontend.seed")
BACKEND = candidate_binary("C0_BACKEND", STAGE / "c0-backend.seed")
if (__name__ == "__main__" and len(sys.argv) > 1
        and (os.sep in sys.argv[1] or Path(sys.argv[1]).is_file())):
    BACKEND = candidate_binary("C0_BACKEND_POSITIONAL", sys.argv.pop(1))
RUNNER = ["qemu-x86_64"] if platform.machine() != "x86_64" else []
MAX = (1 << 63) - 1


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(BACKEND.is_file(), "C0 AST backend is not implemented")

    def ast(self, source):
        result = subprocess.run(RUNNER + [str(FRONTEND)],
                                input=source.encode(), capture_output=True, timeout=15)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        return result.stdout

    def compile_ast(self, data, **kwargs):
        return subprocess.run(RUNNER + [str(BACKEND)], input=data,
                              capture_output=True, timeout=15, **kwargs)

    def compile(self, source):
        result = self.compile_ast(self.ast(source))
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        return result.stdout

    def execute(self, artifact, **kwargs):
        with tempfile.TemporaryDirectory(prefix="c027-runtime-") as name:
            path = Path(name) / "program"
            path.write_bytes(artifact)
            path.chmod(0o755)
            return subprocess.run(RUNNER + [str(path)], capture_output=True, timeout=5, **kwargs)

    def value(self, source, expected):
        result = self.execute(self.compile(source))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (expected & 255, b"", b""), source)

    def reject(self, data, code=None, location=None):
        result = self.compile_ast(data)
        self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
        self.assertRegex(result.stderr, rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$")
        if code:
            self.assertIn(f"[C0B-{code:03d}]".encode(), result.stderr)
        if location:
            self.assertTrue(result.stderr.startswith(f"input:{location[0]}:{location[1]}:".encode()), result.stderr)

    def test_scalar_source_runs(self):
        self.value("fn main(){return 1+2*3}", 7)
        self.value("fn main(){let a=5; let b=3; a=a*b+2; return a-b}", 14)
        self.value("fn main(){return (0-7)/3}", -2)
        self.value(f"fn main(){{return {MAX}}}", MAX)
        self.value(f"fn main(){{return (0-{MAX}-1)/1}}", -(1 << 63))
        self.value("fn main(){return 00000000000000000000000000000000000007}", 7)

    def test_compiler_profile_is_explicitly_supported(self):
        for source, status in ((b"fn main(){return 7}", 7),
                               (b"fn main(){byte_store(65536,42);return byte_load(65536)}", 42)):
            with self.subTest(source=source):
                parsed = subprocess.run(RUNNER + [str(FRONTEND)],
                                        input=encode_profile_source(source),
                                        capture_output=True, timeout=15)
                self.assertEqual(parsed.returncode, 0, parsed.stderr[:512])
                self.assertEqual(len(parsed.stderr), 0, parsed.stderr[:512])
                compiled = self.compile_ast(parsed.stdout)
                self.assertEqual(compiled.returncode, 0, compiled.stderr[:512])
                self.assertEqual(len(compiled.stderr), 0, compiled.stderr[:512])
                self.assertEqual(compiled.stdout[:4], b"\x7fELF")
                executed = self.execute(compiled.stdout)
                self.assertEqual(executed.returncode, status, executed.stderr[:512])
                self.assertEqual(len(executed.stdout), 0, executed.stdout[:512])
                self.assertEqual(len(executed.stderr), 0, executed.stderr[:512])

    def test_operator_precedence_and_order(self):
        def calc(op, a, b):
            return {"+": lambda: a + b, "-": lambda: a - b,
                    "*": lambda: a * b,
                    "/": lambda: (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)}[op]()
        for first, second in itertools.product("+-*/", repeat=2):
            with self.subTest(first=first, second=second):
                expected = (calc(first, 23, calc(second, 7, 2)) if first in "+-" and second in "*/"
                            else calc(second, calc(first, 23, 7), 2))
                self.value(f"fn main(){{return 23{first}7{second}2}}", expected)
                self.value(f"fn main(){{return (23{first}7){second}2}}", calc(second, calc(first, 23, 7), 2))

    def test_binding_resolution_and_mutation(self):
        names = ["a", "aa", "ab", "A", "_", "main", "return_value"] + [f"value{i}" for i in range(17)]
        body = " ".join(f"let {name}={i}" for i, name in enumerate(names))
        body += " a=13 aa=aa+a value16=value16+aa"
        self.value(f"fn main(){{{body} return value16}}", 37)
        self.value("fn main(){let long_name=7 long_name=long_name*3 return long_name}", 21)
        self.value("fn main(){let x=1 let y=x x=9 return y}", 1)

    def test_semantic_errors_have_source_locations(self):
        cases = [("fn main(){return missing}", 3, (1, 18)),
                 ("fn main(){x=1 return x}", 3, (1, 11)),
                 ("fn main(){let x=x return x}", 3, (1, 17)),
                 ("fn main(){let x=1\n let x=2 return x}", 4, (2, 6)),
                 ("fn main(){return 9223372036854775808}", 5, (1, 18)),
                 ("fn main(){let a=b let b=1 return a}", 3, (1, 17))]
        for source, code, location in cases:
            with self.subTest(source=source):
                self.reject(self.ast(source), code, location)

    def test_runtime_arithmetic_is_checked(self):
        for expression in (f"{MAX}+1", f"(0-{MAX}-1)-1", f"{MAX}*2", "7/(3-3)",
                           f"(0-{MAX}-1)/(0-1)"):
            with self.subTest(expression=expression):
                result = self.execute(self.compile(f"fn main(){{\n return {expression};\n}}"))
                self.assertEqual((result.returncode, result.stdout), (70, b""))
                self.assertRegex(result.stderr, rb"^input:2:[1-9][0-9]*: error\[C0R-001\]: .+\n$")
        result = self.execute(self.compile(f"fn main(){{let unused={MAX}+1 return 0}}"))
        self.assertEqual(result.returncode, 70, "discarded initializer was not evaluated")

    def test_capacity_and_determinism(self):
        source = "fn main(){return 1" + "/1" * 252 + "}"
        self.value(source, 1)
        grouped = "fn main(){return " + "(" * 252 + "7" + ")" * 252 + "}"
        self.value(grouped, 7)
        bindings = " ".join(f"let x{i}={i}" for i in range(126))
        self.value(f"fn main(){{{bindings} return x125}}", 125)
        source = "fn main(){return 7}"
        source += " " * (8192 - len(source))
        first = self.compile(source)
        self.assertEqual(first, self.compile(source))
        self.value(source, 7)

    def test_elf_contract(self):
        binary = self.compile("fn main(){return 7}")
        self.assertEqual(binary[:7], b"\x7fELF\x02\x01\x01")
        fields = struct.unpack_from("<HHIQQQIHHHHHH", binary, 16)
        self.assertEqual(fields[:3], (2, 62, 1))
        self.assertEqual((fields[4], fields[7], fields[8], fields[9]), (64, 64, 56, 2))
        load, stack = [struct.unpack_from("<IIQQQQQQ", binary, 64 + i * 56) for i in range(2)]
        self.assertEqual(load[:3], (1, 5, 0))
        self.assertEqual(load[3], 0x400000)
        self.assertEqual(load[5:7], (len(binary), len(binary)))
        self.assertTrue(load[3] <= fields[3] < load[3] + load[5])
        self.assertEqual(stack[:2], (0x6474e551, 6))

    def test_invalid_headers_and_framing(self):
        ast = self.ast("fn main(){return 7}")
        for data in (b"", ast[:15], ast[:-1], ast + b"\0", b"\0" * 16401):
            self.reject(data, 1)
        for offset, value in ((0, 0), (4, 2), (5, 8), (6, 1), (7, 1),
                              (9, 255), (10, 0), (11, 255), (12, 0), (14, 0), (15, 255)):
            data = bytearray(ast)
            data[offset] = value
            self.reject(data, 1)

    def test_invalid_nodes_and_graphs(self):
        ast = self.ast("fn main(){let x=7 return x+2}")
        base = 16 + struct.unpack_from("<H", ast, 8)[0]
        for offset, value in ((0, 99), (1, 1), (3, 255), (4, 0), (6, 1),
                              (10, 1), (12, 1), (13, 1), (14, 1), (15, 1)):
            data = bytearray(ast)
            data[base + offset] = value
            self.reject(data, 2)
        # Let right child aliases its left child: no DAG/node sharing is allowed.
        data = bytearray(ast)
        struct.pack_into("<H", data, base + 2 * 16 + 8, 1)
        self.reject(data, 2)
        data = bytearray(ast)
        data[16 + len("fn main(){let ")] = ord("1")
        self.reject(data, 6)

    def test_statement_local_postorder_is_required(self):
        cases = [
            ("fn main(){let x=1 x=2 return x}", [1, 2, 3, 7, 4, 5, 6, 8, 9]),
            ("fn main(){let x=1 let x=2 return x}", [1, 4, 2, 3, 5, 6, 7, 8, 9]),
            ("fn main(){return (7/0)+(9/0)}", [4, 5, 6, 1, 2, 3, 7, 8, 9]),
        ]
        for source, order in cases:
            with self.subTest(source=source):
                ast = self.ast(source)
                base = 16 + struct.unpack_from("<H", ast, 8)[0]
                remap = {old: new for new, old in enumerate(order, 1)}
                data = bytearray(ast[:base])
                for old in order:
                    node = bytearray(ast[base + (old - 1) * 16:base + old * 16])
                    for field in (6, 8, 10):
                        child = struct.unpack_from("<H", node, field)[0]
                        struct.pack_into("<H", node, field, remap.get(child, 0))
                    data.extend(node)
                self.reject(data, 2)

    def test_malformed_streams_do_not_crash_or_hang(self):
        ast = self.ast("fn main(){let alpha=1+2*(3-4) alpha=(alpha+5)/2 return alpha}")
        rng = random.Random(27)
        for _ in range(100):
            data = bytearray(ast)
            for _ in range(rng.randrange(1, 4)):
                data[rng.randrange(len(data))] = rng.randrange(256)
            result = self.compile_ast(data)
            self.assertIn(result.returncode, (0, 1), result.stderr)
            if result.returncode == 1:
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"error[C0B-", result.stderr)
        for length in range(0, len(ast), 7):
            self.reject(ast[:length], 1)

    def test_io_failure(self):
        ast = self.ast("fn main(){return 7}")
        result = self.compile_ast(ast, preexec_fn=lambda: invalidate_standard_fd(1))
        self.assertEqual(result.returncode, 74)
        self.assertIn(b"output_write failed", result.stderr)
        result = self.compile_ast(b"", preexec_fn=lambda: invalidate_standard_fd(0))
        self.assertEqual(result.returncode, 74)
        artifact = self.compile("fn main(){return 1/0}")
        result = self.execute(artifact, preexec_fn=lambda: invalidate_standard_fd(2))
        self.assertEqual(result.returncode, 74)

    def test_short_reads_and_partial_write_failure(self):
        ast = self.ast("fn main(){return 7}")
        with tempfile.TemporaryFile() as output:
            with subprocess.Popen(RUNNER + [str(BACKEND)], stdin=subprocess.PIPE,
                                  stdout=output, stderr=subprocess.PIPE) as process:
                for start in range(0, len(ast), 13):
                    process.stdin.write(ast[start:start + 13])
                    process.stdin.flush()
                    time.sleep(0.005)
                process.stdin.close()
                process.stdin = None
                _, stderr = process.communicate(timeout=15)
                self.assertEqual((process.returncode, stderr), (0, b""))
                output.seek(0)
                self.assertEqual(output.read(), self.compile_ast(ast).stdout)

        read_fd, write_fd = os.pipe()
        try:
            fcntl.fcntl(write_fd, fcntl.F_SETPIPE_SZ, 4096)
            with subprocess.Popen(RUNNER + [str(BACKEND)], stdin=subprocess.PIPE,
                                  stdout=write_fd, stderr=subprocess.PIPE) as process:
                os.close(write_fd)
                write_fd = None
                process.stdin.write(ast)
                process.stdin.close()
                process.stdin = None
                ready, _, _ = select.select([read_fd], [], [], 15)
                self.assertTrue(ready, "backend produced no output before deadline")
                self.assertTrue(os.read(read_fd, 17).startswith(b"\x7fELF"))
                os.close(read_fd)
                read_fd = None
                _, stderr = process.communicate(timeout=15)
                self.assertEqual(process.returncode, 74)
                self.assertIn(b"output_write failed", stderr)
        finally:
            for fd in (read_fd, write_fd):
                if fd is not None:
                    os.close(fd)

    def test_materializer_atomicity_concurrency_and_interruption(self):
        with tempfile.TemporaryDirectory(prefix="c027-materialize-") as name:
            root = Path(name)
            stage = root / "bootstrap/compiler/c0/x86_64-linux"
            stage.mkdir(parents=True)
            b0 = root / "bootstrap/compiler/b0/x86_64-linux/b0.seed"
            b0.parent.mkdir(parents=True)
            compiler = candidate_binary("B0_COMPILER", ROOT / b0.relative_to(root))
            shutil.copy2(compiler, b0)
            for filename in ("materialize-backend.sh", "c0-backend.sha256"):
                shutil.copy2(STAGE / filename, stage / filename)
            (stage / "c0-backend.sha256").write_text(
                hashlib.sha256(BACKEND.read_bytes()).hexdigest() + "  c0-backend.seed\n")
            source = stage.parent / "backend.nql"
            shutil.copy2(STAGE.parent / "backend.nql", source)
            script, output = stage / "materialize-backend.sh", root / "backend"
            def build(target=output, **kwargs):
                return subprocess.run(["bash", str(script), str(target)],
                                      capture_output=True, timeout=30, **kwargs)
            command = ["bash", str(script), str(output)]
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as a:
                with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as b:
                    self.assertEqual(a.communicate(timeout=30)[0], b"")
                    self.assertEqual(b.communicate(timeout=30)[0], b"")
                    self.assertEqual((a.returncode, b.returncode), (0, 0))
            before = output.read_bytes()
            self.assertEqual(before, BACKEND.read_bytes())
            pin = stage / "c0-backend.sha256"
            original_pin = pin.read_bytes()
            pin.write_text("0" * 64 + "  c0-backend.seed\n")
            self.assertEqual(build().returncode, 1)
            self.assertEqual(output.read_bytes(), before)
            pin.write_bytes(original_pin)
            original_source = source.read_bytes()
            source.write_text("invalid B0 source\n")
            self.assertEqual(build().returncode, 1)
            self.assertEqual(output.read_bytes(), before)
            source.write_bytes(original_source)
            for protected in (source, pin, script, b0):
                alias = root / "alias"
                alias.symlink_to(protected)
                self.assertEqual(build(alias).returncode, 1)
                alias.unlink()

            # Fail and interrupt at publication, after compilation and hash checks.
            commands = root / "commands"
            commands.mkdir()
            mv = commands / "mv"
            mv.write_text("#!/bin/sh\nexit 73\n")
            mv.chmod(0o755)
            env = {**os.environ, "PATH": str(commands) + os.pathsep + os.environ["PATH"]}
            self.assertEqual(build(env=env).returncode, 1)
            self.assertEqual(output.read_bytes(), before)
            mv.write_text('#!/bin/sh\n: > "$C027_READY"\nexec sleep 30\n')
            ready = root / "ready"
            env["C027_READY"] = str(ready)
            process = subprocess.Popen(command, env=env, start_new_session=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 20
                while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(ready.exists(), "materializer did not reach publication")
                os.killpg(process.pid, signal.SIGTERM)
                process.communicate(timeout=10)
                self.assertEqual(process.returncode, 143)
                self.assertEqual(output.read_bytes(), before)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=10)
            self.assertEqual(list(root.glob(".c0-backend.seed.tmp.*")), [])

    def test_atomic_source_wrapper(self):
        wrapper = STAGE / "compile-source.sh"
        self.assertTrue(wrapper.is_file())
        with tempfile.TemporaryDirectory(prefix="c027-wrapper-") as name:
            root = Path(name)
            source, output = root / "input.nql", root / "output"
            temporary = root / "temporary"
            temporary.mkdir()
            env = {**os.environ, "TMPDIR": str(temporary)}
            source.write_text("fn main(){return 7}")
            def build(target=output):
                return subprocess.run(["bash", str(wrapper), str(source), str(target)],
                                      capture_output=True, timeout=15, env=env)
            result = build()
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
            before = output.read_bytes()
            self.assertEqual(before, self.compile(source.read_text()))
            source.write_text("fn main(){return missing}")
            result = build()
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"error[C0B-003]", result.stderr)
            self.assertEqual(output.read_bytes(), before)
            source.write_text("fn main(){return ;}")
            result = build()
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"error[C0P-", result.stderr)
            self.assertNotIn(b"error[C0B-", result.stderr)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(build(source).returncode, 1)
            self.assertEqual(list(root.glob(".c0-source.*")), [])
            self.assertEqual(list(temporary.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
