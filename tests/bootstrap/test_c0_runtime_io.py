"""C0.30 call statements, checked byte arena and raw stream runtime."""

import hashlib
import os
from pathlib import Path
import platform
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "bootstrap/compiler/c0/x86_64-linux"
FRONTEND = Path(os.environ.get("C0_FRONTEND", STAGE / "c0-frontend.seed"))
BACKEND = Path(os.environ.get("C0_BACKEND", STAGE / "c0-backend.seed"))
RUNNER = ["qemu-x86_64"] if platform.machine() != "x86_64" else []
PREDECESSOR_SOURCES = [
    "fn main(){return 7}",
    "fn main(){let n=3 while n {n=n-1} return n}",
    "fn main(){return add(20,22)} fn add(a,b){return a+b}",
    "fn f(n){if n<=1{return 1} return n*f(n-1)} fn main(){return f(5)}",
    "fn main(){return byte_load(7)} fn byte_load(x){return x+1}",
    "fn byte_store(x){return x} fn main(){return byte_store(9)}",
    "fn output_write(){return 6} fn main(){return output_write()}",
    "fn input_read(x){return x} fn main(){return input_read(2)}",
    "fn error_write(x){return x} fn main(){return error_write(3)}",
    "fn f(a,b,c,d,e,f){return a+b+c+d+e+f} fn main(){return f(1,2,3,4,5,6)}",
]


def run(binary, data=b""):
    return subprocess.run(RUNNER + [str(binary)], input=data, capture_output=True,
                          timeout=10)


class FrontendRuntimeTests(unittest.TestCase):
    def test_call_statement_records(self):
        for body, count in (("f() f();", 2), ("f(f(1));", 1),
                            ("let x=f() f(x)", 1),
                            ("while 1 {f() x=2} if 0 {f()} else {f()}", 3)):
            with self.subTest(body=body):
                source = f"fn main(){{{body} return 0}}"
                result = run(FRONTEND, source.encode())
                self.assertEqual((result.returncode, result.stderr), (0, b""))
                self.assertEqual(result.stdout[4], 4)
                records = list(struct.iter_unpack("<BBHHHHH4s", result.stdout[16+len(source):]))
                statements = [(i, r) for i, r in enumerate(records) if r[0] == 44]
                self.assertEqual(len(statements), count)
                statement_ids = [i for i, r in enumerate(records, 1)
                                 if r[0] in (30, 31, 32, 34, 35, 36, 37, 38,
                                             39, 40, 41, 44)]
                for node_id, next_id in zip(statement_ids, statement_ids[1:] + [0]):
                    self.assertEqual(records[node_id-1][6], next_id)
                owners = [0] * len(records)
                for record in records:
                    for child in record[4:7]:
                        if child:
                            self.assertLessEqual(child, len(records))
                            owners[child-1] += 1
                self.assertEqual(records[-1][0], 33)
                self.assertEqual(owners, [1] * (len(records)-1) + [0])
                for i, record in statements:
                    call = records[i-1]
                    self.assertEqual((call[0], record[4], record[5]), (42, i, 0))
                    self.assertEqual(record[2:4], call[2:4])

    def test_long_call_statement_anchor(self):
        for length in (255, 256, 257):
            name = "f" * length
            source = f"fn main(){{{name}(7) return 0}}"
            result = run(FRONTEND, source.encode())
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            records = list(struct.iter_unpack("<BBHHHHH4s", result.stdout[16+len(source):]))
            statement = next(record for record in records if record[0] == 44)
            self.assertEqual(statement[2:4], (10, length))

    def test_reject_discarded_expressions_and_bad_calls(self):
        for body in ("f()+1", "1+f()", "(f())", "f(,1)", "f(1,)", "f(",
                     "f()=2", "f() f", "f() * f()"):
            result = run(FRONTEND, f"fn main(){{{body}; return 0}}".encode())
            self.assertEqual((result.returncode, result.stdout), (1, b""), body)
            self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0P-")

    def test_predecessor_ast_bytes(self):
        outputs = [run(FRONTEND, source.encode()) for source in PREDECESSOR_SOURCES]
        self.assertTrue(all(r.returncode == 0 and not r.stderr for r in outputs))
        self.assertEqual(hashlib.sha256(b"".join(r.stdout for r in outputs)).hexdigest(),
                         "72d2daec04eac75483e3c4731719992b9a97693ee2a35209340d6c5dedd3fc4e")


class RuntimeTests(unittest.TestCase):
    def test_predecessor_elf_bytes(self):
        self.assertEqual(hashlib.sha256(b"".join(self.artifact(s) for s in PREDECESSOR_SOURCES)).hexdigest(),
                         "85b4378d5ba155c5861cb90d790ce27d0a8c8f3e7727c50a95096e1b35d44365")

    def ast(self, source):
        result = run(FRONTEND, source.encode())
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        return result.stdout

    def artifact(self, source):
        result = run(BACKEND, self.ast(source))
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        return result.stdout

    def execute(self, source, data=b"", bad_fd=None):
        with tempfile.TemporaryDirectory(prefix="c030-runtime-") as tmp:
            binary = Path(tmp) / "program"
            binary.write_bytes(self.artifact(source))
            binary.chmod(0o755)
            if bad_fd is None:
                return run(binary, data)
            # EBADF is reproducible on proot too, unlike its emulated /dev/full.
            with open(os.devnull, "wb" if bad_fd == 0 else "rb") as wrong:
                kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE,
                          "stderr": subprocess.PIPE}
                kwargs[("stdin", "stdout", "stderr")[bad_fd]] = wrong
                return subprocess.run(RUNNER + [str(binary)], timeout=10, **kwargs)

    def value(self, source, expected=0, data=b"", stdout=b"", stderr=b""):
        result = self.execute(source, data)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (expected, stdout, stderr), source)

    def test_call_statement(self):
        self.value("fn f(){return 9} fn main(){f() f(); let n=2 "
                   "while n {f() n=n-1} if 1 {f()} else {f()} return 0}")
        self.value("fn f(x){return x} fn main(){f(f(2)); return f(7)}", 7)

    def test_byte_arena(self):
        self.value("fn main(){return byte_load(0)+byte_load(65535)}")
        self.value("fn main(){byte_store(0,321); byte_store(65535,0-1) "
                   "return (byte_load(0)==65)+(byte_load(65535)==255)}", 2)
        self.value("fn main(){let x=byte_store(19,37) return x+byte_load(19)}", 37)
        self.value("fn main(){let i=0 while i<256 {byte_store(i,i) i=i+1} "
                   "let s=0 i=0 while i<256 {s=s+(byte_load(i)==i) i=i+1} return s==256}", 1)

    def test_shared_arena_and_argument_order(self):
        self.value("fn bump(){let n=byte_load(0)+1 byte_store(0,n) return n} "
                   "fn mix(a,b,c){return a*100+b*10+c} "
                   "fn main(){return mix(bump(),bump(),bump())}", 123)
        self.value("fn bump(){let n=byte_load(0)+1 byte_store(0,n) return n} "
                   "fn main(){byte_store(bump(),bump()) return byte_load(1)*10+byte_load(0)}", 22)
        self.value("fn f(n){if n {byte_store(n,n) f(n-1)} return byte_load(n)} "
                   "fn main(){f(10) return byte_load(10)+byte_load(9)}", 19)

    def test_stdio_and_eof(self):
        self.value("fn main(){let n=input_read(0,100) let m=output_write(0,n) "
                   "return (m==n)+(input_read(0,100)==0)}", 2,
                   data=b"NolQu-L\x00\xff\n", stdout=b"NolQu-L\x00\xff\n")
        self.value("fn main(){byte_store(0,65) byte_store(1,10) "
                   "let n=error_write(0,2) return n}", 2, stderr=b"A\n")
        self.value("fn main(){let n=input_read(65534,2) output_write(65534,n) return n}",
                   2, data=b"xyz", stdout=b"xy")

    def test_full_arena_streaming_and_redirect(self):
        source = ("fn main(){let n=0 let got=1 while got {got=input_read(n,65536-n) "
                  "n=n+got if n==65536 {got=0}} return output_write(0,n)==65536}")
        data = bytes(range(256)) * 256
        self.value(source, 1, data=data, stdout=data)
        with tempfile.TemporaryDirectory(prefix="c030-redirect-") as tmp:
            binary, incoming, outgoing = (Path(tmp) / n for n in ("program", "in", "out"))
            binary.write_bytes(self.artifact("fn main(){let n=input_read(0,50) output_write(0,n) return 0}"))
            binary.chmod(0o755)
            incoming.write_bytes(b"redirected\n")
            with incoming.open("rb") as inp, outgoing.open("wb") as out:
                result = subprocess.run(RUNNER + [str(binary)], stdin=inp, stdout=out,
                                        stderr=subprocess.PIPE, timeout=10)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            self.assertEqual(outgoing.read_bytes(), incoming.read_bytes())

    def test_empty_ranges_do_not_touch_descriptors(self):
        for name, fd in (("input_read", 0), ("output_write", 1), ("error_write", 2)):
            for offset in (0, 65536):
                with self.subTest(name=name, offset=offset):
                    result = self.execute(f"fn main(){{return {name}({offset},0)}}", bad_fd=fd)
                    self.assertEqual(result.returncode, 0)

    def test_bad_ranges(self):
        calls = ["byte_load(65536)", "byte_load(0-1)", "byte_store(65536,1)",
                 "byte_store(0-1,1)", "byte_load(9223372036854775807)"]
        for name in ("input_read", "output_write", "error_write"):
            calls.extend(f"{name}({args})" for args in
                         ("65536,1", "65535,2", "0-1,0", "0,0-1", "65537,0",
                          "0,9223372036854775807", "9223372036854775807,1"))
        for call in calls:
            with self.subTest(call=call):
                result = self.execute("fn main(){\n    return " + call + "\n}")
                self.assertEqual((result.returncode, result.stdout), (70, b""))
                self.assertRegex(result.stderr, rb"^input:2:12: error\[C0R-004\]: .+; .+\n$")

    def test_descriptor_errors(self):
        for name, fd, code in (("input_read", 0, b"C0R-005"),
                               ("output_write", 1, b"C0R-006"),
                               ("error_write", 2, None)):
            with self.subTest(name=name):
                result = self.execute(f"fn main(){{return {name}(0,1)}}", bad_fd=fd)
                self.assertEqual(result.returncode, 74)
                if code:
                    self.assertIn(b"input:1:18: error[" + code + b"]:", result.stderr)
        result = self.execute("fn main(){return byte_load(65536)}", bad_fd=2)
        self.assertEqual(result.returncode, 74)

    def test_builtin_resolution_and_arity(self):
        self.value("fn byte_load(x){return x+1} fn main(){byte_load(5) return byte_load(7)}", 8)
        self.value("fn main(){let byte_load=3 return byte_load+byte_load(0)}", 3)
        calls = ["byte_load()", "byte_load(0,1)", "byte_store(0)", "byte_store(0,1,2)",
                 "input_read(0)", "output_write()", "error_write(0,1,2)",
                 "byte_load_extra(0)", "Byte_load(0)"]
        for call in calls:
            result = run(BACKEND, self.ast(f"fn main(){{return {call}}}"))
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"C0B-008", result.stderr)
        result = run(BACKEND, self.ast("fn byte_load(){return 4} fn main(){return byte_load(0)}"))
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"C0B-008", result.stderr)

    def test_statements_syntax_and_topology(self):
        source = "fn f(a){return a} fn main(){f(7) return 0}"
        ast = self.ast(source)
        self.assertEqual(ast[4], 4)
        base = 16 + len(source)
        records = list(struct.iter_unpack("<BBHHHHH4s", ast[base:]))
        statement_index = next(i for i, r in enumerate(records) if r[0] == 44)
        statement = records[statement_index]
        call = records[statement_index - 1]
        self.assertEqual((call[0], statement[4], statement[5]), (42, statement_index, 0))
        self.assertEqual(statement[2:4], call[2:4])
        mutations = [(4, b"\x03"), (base + statement_index*16 + 6, b"\x00\x00"),
                     (base + statement_index*16 + 8, b"\x01\x00"),
                     (base + statement_index*16 + 2, b"\x00\x00"),
                     (base + statement_index*16 + 4, b"\x02\x00"),
                     (base + statement_index*16 + 10, b"\x00\x00")]
        for offset, value in mutations:
            broken = bytearray(ast)
            broken[offset:offset+len(value)] = value
            result = run(BACKEND, broken)
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertRegex(result.stderr, rb"error\[C0B-00[126]\]")
        for body in ("f()+1", "1+f()", "(f())", "f(,1)", "f(1,)", "f(",
                     "f()=2", "f() f", "f() * f()"):
            result = run(FRONTEND, f"fn main(){{{body}; return 0}}".encode())
            self.assertEqual((result.returncode, result.stdout), (1, b""), body)
            self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0P-")

    def test_branching_depth_and_live_values(self):
        self.value("fn f(n){if n {return f(n-1)} byte_store(0,9) return byte_load(0)} "
                   "fn main(){return f(62)}", 9)
        self.value("fn f(a,b,c,d,e,f){byte_store(0,55) output_write(0,0) "
                   "return a+b+c+d+e+f+byte_load(0)} fn main(){return 100+f(1,2,3,4,5,6)}", 176)
        self.value("fn main(){if 0 {byte_load(65536)} else {byte_store(0,8)} "
                   "while 0 {output_write(65536,1)} return byte_load(0)}", 8)

    def test_deterministic_native_elf(self):
        source = "fn main(){byte_store(0,65) output_write(0,1) return 0}"
        artifact = self.artifact(source)
        self.assertEqual(artifact, self.artifact(source))
        header = struct.unpack_from("<16sHHIQQQIHHHHHH", artifact)
        self.assertEqual(header[1:4], (2, 62, 1))
        ph = list(struct.iter_unpack("<IIQQQQQQ", artifact[header[5]:header[5]+header[9]*header[10]]))
        self.assertFalse(any(p[0] in (2, 3) for p in ph))
        self.assertTrue(any(p[0] == 0x6474e551 and not p[1] & 1 for p in ph))
        self.assertFalse(any(p[0] == 1 and p[1] & 3 == 3 for p in ph))


if __name__ == "__main__":
    unittest.main()
