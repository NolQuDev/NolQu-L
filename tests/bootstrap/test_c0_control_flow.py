"""C0.28 source/AST/runtime oracle. Canonical B0 builds both components."""

import hashlib
import itertools
import os
from pathlib import Path
import platform
import random
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "bootstrap/compiler/c0/x86_64-linux"
FRONTEND = Path(os.environ.get("C0_FRONTEND", STAGE / "c0-frontend.seed"))
BACKEND = Path(os.environ.get("C0_BACKEND", STAGE / "c0-backend.seed"))
RUNNER = ["qemu-x86_64"] if platform.machine() != "x86_64" else []


def run(binary, data):
    return subprocess.run(RUNNER + [str(binary)], input=data, capture_output=True, timeout=10)


class ControlFlowTests(unittest.TestCase):
    def test_scalar_predecessor_bytes(self):
        # Captured from pinned C0.26/C0.27 before upgrading either component.
        sources = ["fn main(){return 7}",
                   "fn main(){let long_name=1 let aa=2 long_name=long_name+aa return long_name}",
                   "fn main(){return (0-9223372036854775807-1)/1}",
                   "fn main(){\r\n // comment\r\n let _A42=0001; return _A42; }",
                   *[f"fn main(){{return 23{a}7{b}2}}" for a,b in itertools.product("+-*/", repeat=2)]]
        asts = [self.ast(source) for source in sources]
        elfs = [self.artifact(source) for source in sources]
        self.assertEqual(hashlib.sha256(b"".join(asts)).hexdigest(),
                         "5b8aee14a9f205e6f20ca77eafddc832cf4b3702c33285a483438a1cb73dc3b9")
        self.assertEqual(hashlib.sha256(b"".join(elfs)).hexdigest(),
                         "03c8b27f782d7964e8d15bf3f353a06d038d4b71fab9c4facfb701080f0868bd")

    def ast(self, source):
        result = run(FRONTEND, source.encode())
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        return result.stdout

    def artifact(self, source):
        result = run(BACKEND, self.ast(source))
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        return result.stdout

    def execute(self, artifact):
        with tempfile.TemporaryDirectory(prefix="c028-runtime-") as tmp:
            binary = Path(tmp) / "program"
            binary.write_bytes(artifact)
            binary.chmod(0o755)
            return run(binary, b"")

    def value(self, source, expected):
        result = self.execute(self.artifact(source))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (expected & 255, b"", b""), source)

    def test_nested_loops_and_branches(self):
        self.value("""fn main(){
            let i=0 let sum=0
            while i<5 {
                let j=0
                while j<i {
                    if (i+j)/2*2==i+j { sum=sum+3 } else { sum=sum+1 }
                    j=j+1
                }
                i=i+1
            }
            return sum
        }""", 18)
        self.value("fn main(){let n=100 let sum=0 while n {sum=sum+n n=n-1} return sum}", 5050)
        self.value("fn main(){let x=2 while x {if x==1 {return 7} x=x-1} return 3}", 7)
        self.value("fn main(){if 0 {return 4} else {if 1 {return 9}} return 3}", 9)
        self.value("fn main(){if 1 {} if 0 {} else {} while 0 {} return 11}", 11)

    def test_signed_comparisons_and_precedence(self):
        operations = {"<": lambda a,b: a<b, "<=": lambda a,b: a<=b,
                      ">": lambda a,b: a>b, ">=": lambda a,b: a>=b,
                      "==": lambda a,b: a==b, "!=": lambda a,b: a!=b}
        def expr(value):
            return str(value) if value >= 0 else f"(0-{abs(value)})"
        for op, (a, b) in itertools.product(operations, [(0,0), (1,2), (2,1), (-3,1), (1,-3), (-3,-2)]):
            with self.subTest(op=op, a=a, b=b):
                self.value(f"fn main(){{return {expr(a)}{op}{expr(b)}}}", operations[op](a,b))
        for source, expected in [("1+2*3<8==1", 1), ("2<1<1", 1), ("0==2<1", 1),
                                 ("3>=2+2", 0), ("(0-9223372036854775807-1)<0", 1),
                                 ("9223372036854775807>(0-1)", 1)]:
            self.value(f"fn main(){{return {source}}}", expected)

    def test_lexical_scope_and_reinitialization(self):
        self.value("fn main(){let x=2 if x {let x=x+3 x=x+4} return x}", 2)
        self.value("fn main(){let x=1 if 0 {let a=8} else {let a=3 x=a} return x}", 3)
        self.value("fn main(){let n=3 let sum=0 while n {let x=1 x=x+1 sum=sum+x n=n-1} return sum}", 6)
        self.value("fn main(){let x=1 if x {let x=2 if x {let x=3} x=x+1} x=x+4 return x}", 5)
        self.value("fn main(){let if_value=2 let else_value=3 let while_count=4 return if_value+else_value+while_count}", 9)
        for source in ["fn main(){if 1 {let x=1 let x=2} return 0}",
                       "fn main(){while 0 {let x=1} return x}",
                       "fn main(){if 1 {let x=1} else {return x} return 0}",
                       "fn main(){if 0 {return missing} return 0}",
                       "fn main(){if 1 {let x=x} return 0}"]:
            with self.subTest(source=source):
                result = run(BACKEND, self.ast(source))
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0B-00[34]\]")

    def test_unselected_code_never_runs_and_faults_keep_locations(self):
        self.value("fn main(){if 0 {return 1/0} else {return 7} return 3}", 7)
        self.value("fn main(){if (0-1) {return 7} else {return 1/0} return 3}", 7)
        self.value("fn main(){while 0 {return 1/0} return 8}", 8)
        source = "fn main(){\n let n=2\n while n {n=n-1 let x=3/n}\n return 0}"
        result = self.execute(self.artifact(source))
        self.assertEqual(result.returncode, 70)
        self.assertTrue(result.stderr.startswith(b"input:3:24: error[C0R-001]"), result.stderr)

    def test_ast_delimiters_and_version(self):
        source = "fn main(){while 1 {if 0 {} else {return 7}} return 0}"
        ast = self.ast(source)
        self.assertEqual(ast[4], 2)
        base = 16 + len(source)
        nodes = [struct.unpack_from("<BBHHHHH4s", ast, i) for i in range(base, len(ast), 16)]
        statements = [i for i, n in enumerate(nodes, 1) if n[0] in {30,31,32,34,35,36,37,38}]
        self.assertEqual([nodes[i-1][0] for i in statements], [34,36,37,32,38,35,32])
        self.assertEqual([nodes[i-1][6] for i in statements], statements[1:] + [0])
        for n in nodes:
            self.assertEqual((n[1], n[7]), (0, b"\0"*4))
        self.assertEqual(self.ast("fn main(){return 7}")[4], 1)
        self.assertEqual(self.ast("fn main(){return 1<2}")[4], 2)

    def test_malformed_source_and_nesting_limit(self):
        cases = ["if {}", "while {}", "if 1", "if 1 return 2", "while 1; {}",
                 "else {}", "if 1 {} else", "if 1 {} else 1 {}", "if 1 {} else if 1 {}",
                 "if 1 {return 1 let x=2}", "if 1 {return 1;;}", "while 1 {",
                 "if 1 {} else {} else {}", "let if=1", "let else=1", "let while=1",
                 "let a=1!2", "let a=1<", "let a=1==", "if (1<2 {}"]
        for body in cases:
            with self.subTest(body=body):
                result = run(FRONTEND, f"fn main(){{{body} return 0}}".encode())
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0P-\d{3}\]: .+; .+\n$")
        self.ast("fn main(){" + "if 1 {"*64 + "}"*64 + "return 5}")
        result = run(FRONTEND, ("fn main(){" + "if 1 {"*65 + "}"*65 + "return 5}").encode())
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"[C0P-011]", result.stderr)

    def test_malformed_ast_cannot_redirect_control_flow(self):
        source = "fn main(){while 1 {if 0 {} else {return 7}} return 0}"
        ast = bytearray(self.ast(source))
        base = 16 + len(source)
        positions = {kind: next(i for i in range(base, len(ast), 16) if ast[i] == kind)
                     for kind in (34,35,36,37,38)}
        mutations = [(4,1), (positions[35],38), (positions[38],35), (positions[37],38),
                     (positions[36],34), (positions[37]+6,1), (positions[34]+6,255),
                     (positions[38]+10,1), (positions[35]+12,1)]
        for offset, value in mutations:
            with self.subTest(offset=offset, value=value):
                corrupted = ast.copy()
                corrupted[offset] = value
                result = run(BACKEND, corrupted)
                self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
        for end in (0, 15, 16, len(ast)-1):
            result = run(BACKEND, ast[:end])
            self.assertEqual((result.returncode, result.stdout), (1, b""))

    def test_backend_checks_depth_independently_of_frontend(self):
        # Encode a fully owned, ordered AST directly; do not trust parser limits.
        for depth in (64, 65):
            source = ("fn main(){" + "if 1 {"*depth + "}"*depth + "return 5}").encode()
            records = []
            statements = []
            for i in range(depth):
                records.append([5,0,13+i*6,1,0,0,0,b"\0"*4])
                records.append([36,0,10+i*6,2,len(records),0,0,b"\0"*4])
                statements.append(len(records))
            for i in range(depth):
                records.append([38,0,10+depth*6+i,1,0,0,0,b"\0"*4])
                statements.append(len(records))
            records.append([5,0,len(source)-2,1,0,0,0,b"\0"*4])
            records.append([32,0,len(source)-9,6,len(records),0,0,b"\0"*4])
            statements.append(len(records))
            for first, second in zip(statements, statements[1:]):
                records[first-1][6] = second
            records.append([33,0,0,2,statements[0],0,0,b"\0"*4])
            header = struct.pack("<4sBBHHHHH", b"NQAF",2,16,0,len(source),len(records),len(records),8+4*depth)
            ast = header + source + b"".join(struct.pack("<BBHHHHH4s", *r) for r in records)
            result = run(BACKEND, ast)
            if depth == 64:
                self.assertEqual((result.returncode, result.stderr), (0,b""))
                self.assertEqual(self.execute(result.stdout).returncode, 5)
            else:
                self.assertEqual((result.returncode, result.stdout), (1,b""))
                self.assertIn(b"[C0B-002]", result.stderr)

    def test_wide_bindings_inside_nested_scopes(self):
        prefix = " ".join(f"let value{i}={i}" for i in range(90))
        self.value("fn main(){"+prefix+" if value89 {let value89=value89+1 if value89 {value89=value89+1} value0=value89} return value0}", 91)
        self.value("fn main(){"+prefix+" while value89 {let fresh=value89 value0=value0+1 value89=value89-1} return value0}", 89)

    def test_source_wrapper_control_flow_and_atomic_failure(self):
        wrapper = STAGE / "compile-source.sh"
        with tempfile.TemporaryDirectory(prefix="c028-wrapper-") as name:
            root = Path(name)
            source = root / "source with spaces.nql"
            output = root / "program"
            scratch = root / "scratch"
            scratch.mkdir()
            env = dict(os.environ, TMPDIR=str(scratch))
            source.write_text("fn main(){let n=3 let x=1 while n {x=x*2 n=n-1} if x>7 {return x} return 0}")
            result = subprocess.run([str(wrapper), str(source), str(output)],
                                    capture_output=True, timeout=15, env=env)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0,b"",b""))
            self.assertEqual(run(output, b"").returncode, 8)
            previous = output.read_bytes()
            for text, code in [("fn main(){if 1 {return 1} else return 0}", b"C0P-"),
                               ("fn main(){if 1 {let x=1} return x}", b"C0B-003")]:
                source.write_text(text)
                result = subprocess.run([str(wrapper), str(source), str(output)],
                                        capture_output=True, timeout=15, env=env)
                self.assertEqual((result.returncode, result.stdout), (1,b""))
                self.assertIn(code, result.stderr)
                self.assertEqual(output.read_bytes(), previous)
                self.assertEqual(list(scratch.iterdir()), [])
                self.assertEqual(list(root.glob(".c0-source.*")), [])

    def test_structured_ast_mutations_terminate_without_crash(self):
        source = "fn main(){let n=2 while n {if n==1 {let x=n+1 n=x-2} else {n=n-1}} return n}"
        original = self.ast(source)
        rng = random.Random(2801)
        for _ in range(64):
            ast = bytearray(original)
            ast[rng.randrange(len(ast))] = rng.randrange(256)
            result = run(BACKEND, ast)
            self.assertIn(result.returncode, (0, 1), result.stderr)
            if result.returncode:
                self.assertEqual(result.stdout, b"")
                self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0B-\d{3}\]")
            else:
                # Source bytes are metadata; benign mutations need not fail.
                self.assertEqual(result.stderr, b"")
                self.assertTrue(result.stdout.startswith(b"\x7fELF"))

    def test_deterministic_runtime_corpus(self):
        randomizer = random.Random(28)
        for _ in range(12):
            n = randomizer.randrange(1, 10)
            threshold = randomizer.randrange(n+1)
            source = f"fn main(){{let n={n} let s=0 while n {{if n>{threshold} {{s=s+n}} else {{s=s+1}} n=n-1}} return s}}"
            expected = sum(i if i>threshold else 1 for i in range(1, n+1))
            self.value(source, expected)
        source = "fn main(){let x=3 while x {x=x-1} return x}"
        self.assertEqual(hashlib.sha256(self.artifact(source)).digest(),
                         hashlib.sha256(self.artifact(source)).digest())


if __name__ == "__main__":
    unittest.main()
