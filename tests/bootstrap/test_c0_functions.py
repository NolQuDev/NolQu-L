"""C0.29 source, versioned AST and native calling convention tests."""

import hashlib
import os
from pathlib import Path
import platform
import random
import struct
import subprocess
import tempfile
import unittest

from standard_fd_fault import invalidate_standard_fd

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "bootstrap/compiler/c0/x86_64-linux"
FRONTEND = Path(os.environ.get("C0_FRONTEND", STAGE / "c0-frontend.seed"))
BACKEND = Path(os.environ.get("C0_BACKEND", STAGE / "c0-backend.seed"))
RUNNER = ["qemu-x86_64"] if platform.machine() != "x86_64" else []


def run(binary, data=b"", **kwargs):
    return subprocess.run(RUNNER + [str(binary)], input=data, capture_output=True,
                          timeout=10, **kwargs)


class FunctionTests(unittest.TestCase):
    def test_control_flow_predecessor_bytes(self):
        # Captured from the pinned C0.28 components before this work unit.
        sources = ["fn main(){if 1 {return 7} else {return 9} return 0}",
                   "fn main(){let n=3 let s=0 while n {s=s+n n=n-1} return s}",
                   "fn main(){let x=1 if x {let x=x+2} return x}",
                   "fn main(){return (0-3)<(0-2)==1}"]
        self.assertEqual(hashlib.sha256(b"".join(self.ast(s) for s in sources)).hexdigest(),
                         "a933f6eb06d0087e3d9db1d9bf67d3cb2ea6a032b835e8f13c5e45a67f817f99")
        self.assertEqual(hashlib.sha256(b"".join(self.artifact(s) for s in sources)).hexdigest(),
                         "a29cd81af5cdb28e9d267349005d06a616cd7b1840bf8c6b7a69792a4c8eb1df")

    def ast(self, source):
        result = run(FRONTEND, source.encode())
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        return result.stdout

    def artifact(self, source):
        result = run(BACKEND, self.ast(source))
        self.assertEqual((result.returncode, result.stderr), (0, b""), source)
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        return result.stdout

    def execute(self, source):
        with tempfile.TemporaryDirectory(prefix="c029-runtime-") as tmp:
            binary = Path(tmp) / "program"
            binary.write_bytes(self.artifact(source))
            binary.chmod(0o755)
            return run(binary)

    def value(self, source, expected):
        result = self.execute(source)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (expected & 255, b"", b""), source)

    def test_forward_calls(self):
        self.value("fn main(){return sum(20,22)} fn sum(a,b){return a+b}", 42)
        self.value("fn answer(){return 42} fn main(){return answer()}", 42)
        self.value("fn main(){return answer()} fn answer(){return 42}", 42)
        self.value("fn f(){return 1} fn ff(){return 2} fn F(){return 3} "
                   "fn _(){return 4} fn while_count(){return 5} "
                   "fn main(){return f()+ff()*2+F()*3+_()*4+while_count()*5}", 55)

    def test_parameters_and_nested_calls(self):
        self.value("fn id(a){return a} fn add(a,b){return a+b} "
                   "fn main(){return add(id(7),add(id(8),id(9)))*2}", 48)
        self.value("fn mix(a,b,c,d,e,f){return a+2*b+3*c+4*d+5*e+6*f} "
                   "fn main(){return mix(1,2,3,4,5,6)}", 91)
        self.value("fn inc(n){n=n+1 return n} fn main(){let n=7 "
                   "let x=inc(n) return n*10+x}", 78)
        self.value("fn id(x){return x} fn main(){return "+"id("*80+"7"+")"*80+"}", 7)
        self.value("fn id(x){return x} fn sum(a,b,c,d,e,f){return a+b+c+d+e+f} "
                   "fn main(){return sum(id(1),id(2),id(3),id(4),id(5),id(6))}", 21)

    def test_long_callee_spans_and_exact_resolution(self):
        for length in (255, 256, 257):
            for arity in (0, 1, 6):
                with self.subTest(length=length, arity=arity):
                    name = "f" * length
                    params = ",".join("abcdef"[:arity])
                    args = ",".join(str(i) for i in range(1, arity + 1))
                    expr = "+".join("abcdef"[:arity]) if arity else "7"
                    source = f"fn main(){{return {name}({args})}} fn {name}({params}){{return {expr}}}"
                    ast = self.ast(source)
                    records = list(struct.iter_unpack("<BBHHHHH4s", ast[16 + len(source):]))
                    call = next(record for record in records if record[0] == 42)
                    self.assertEqual((call[2], call[3]), (source.index(name), length))
                    self.value(source, sum(range(1, arity + 1)) if arity else 7)
        # A truncated span must not resolve to a different, shorter function.
        name = "f" * 256 + "x"
        self.value(f"fn f(){{return 1}} fn {name}(){{return 42}} "
                   f"fn main(){{return {name}()}}", 42)

    def test_recursion_and_mutual_recursion(self):
        self.value("fn fact(n){if n<=1 {return 1} return n*fact(n-1)} "
                   "fn main(){return fact(5)}", 120)
        self.value("fn odd(n){if n==0 {return 0} return even(n-1)} "
                   "fn main(){return odd(9)} "
                   "fn even(n){if n==0 {return 1} return odd(n-1)}", 1)
        self.value("fn fib(n){if n<2 {return n} return fib(n-1)+fib(n-2)} "
                   "fn main(){return fib(9)}", 34)

    def test_scopes_early_return_and_loop_calls(self):
        self.value("fn f(x){if x {let x=x+3 return x} return 9} "
                   "fn main(){let i=3 let sum=0 while i {sum=sum+f(i) i=i-1} return sum}", 15)
        self.value("fn f(x){return x} fn main(){let f=5 return f+f(f)}", 10)
        self.value("fn step(x){return x-1} fn main(){let x=4 "
                   "while step(x)>0 {x=step(x)} return x}", 1)

    def test_semantic_errors(self):
        for source in ["fn other(){return 1}", "fn main(x){return x}",
                       "fn main(){return foo()}", "fn main(){return 1} fn main(){return 2}",
                       "fn main(){return missing(1)}",
                       "fn f(a){return a} fn main(){return f()}",
                       "fn f(){return 0} fn main(){return f(1)}",
                       "fn f(){return 0} fn f(){return 1} fn main(){return 0}",
                       "fn main(){return 0} fn main(){return 1}",
                       "fn f(){return 0}", "fn main(a){return a}",
                       "fn f(a,a){return a} fn main(){return 0}",
                       "fn f(a){let a=2 return a} fn main(){return 0}",
                       "fn f(){let x=2 return x} fn main(){return x}",
                       "fn f(x){return x} fn main(){if 0 {return unknown()} return 0}"]:
            with self.subTest(source=source):
                result = run(BACKEND, self.ast(source))
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0B-\d{3}\]: .+; .+\n$")

    def test_frontend_syntax_errors(self):
        for source in ["fn main(){return f(,1)}", "fn main(){return f(1,)}",
                       "fn main(){return f(1,,2)}", "fn main(){return f(1 2)}",
                       "fn main(){return f((1,2))}", "fn main(){return f(1}",
                       "fn f(a,){return a}", "fn f(,a){return a}",
                       "fn f(a b){return a}", "fn f(a,a,a,a,a,a,a){return 0}",
                       "fn main(){return f(1,2,3,4,5,6,7)}",
                       "fn main(){fn f(){return 0} return 0}",
                       "fn f(){let x=1}", "fn f(){return 1} garbage"]:
            with self.subTest(source=source):
                result = run(FRONTEND, source.encode())
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0P-\d{3}\]: .+; .+\n$")

    def test_function_diagnostic_locations(self):
        cases = [
            ("fn main(){\n return missing(1)\n}", "missing", 8),
            ("fn f(x){return x}\nfn main(){return f()}", "f()", 8),
            ("fn f(){return 1}\nfn f(){return 2}\nfn main(){return 0}", "f()", 8),
            ("fn f(a,\n a){return a}\nfn main(){return 0}", "a){", 4),
            ("fn f(x){let hidden=x return hidden}\nfn main(){return hidden}", "hidden", 3),
        ]
        for source, anchor, code in cases:
            with self.subTest(source=source):
                offset = source.rindex(anchor)
                line = source.count("\n", 0, offset) + 1
                col = offset - source.rfind("\n", 0, offset)
                result = run(BACKEND, self.ast(source))
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                prefix = f"input:{line}:{col}: error[C0B-{code:03d}]: ".encode()
                self.assertTrue(result.stderr.startswith(prefix), result.stderr)

    def test_native_elf_and_diagnostic_io_failures(self):
        source = "fn fail(){return 1/0} fn main(){return fail()}"
        artifact = self.artifact(source)
        fields = struct.unpack_from("<HHIQQQIHHHHHH", artifact, 16)
        self.assertEqual(fields[:3], (2, 62, 1))
        self.assertEqual((fields[4], fields[8], fields[9]), (64, 56, 2))
        load, stack = [struct.unpack_from("<IIQQQQQQ", artifact, 64 + i * 56)
                       for i in range(2)]
        self.assertEqual(load[:3], (1, 5, 0))
        self.assertEqual(load[5:7], (len(artifact), len(artifact)))
        self.assertEqual(stack[:2], (0x6474e551, 6))
        with tempfile.TemporaryDirectory(prefix="c029-io-") as tmp:
            binary = Path(tmp) / "program"
            binary.write_bytes(artifact)
            binary.chmod(0o755)
            result = run(binary, preexec_fn=lambda: invalidate_standard_fd(2))
            self.assertEqual((result.returncode, result.stdout), (74, b""))
            # A read-only descriptor forces EBADF without host device permissions
            # or pipe-reader lifetime races under an emulated Linux environment.
            with binary.open("rb") as readonly:
                result = subprocess.run(RUNNER + [str(binary)], stdout=subprocess.PIPE,
                                        stderr=readonly, timeout=10)
                self.assertEqual((result.returncode, result.stdout), (74, b""))

    def test_frontend_ast_contract(self):
        source = "fn main(){return sum(20,22)} fn sum(a,b){return a+b}"
        ast = self.ast(source)
        self.assertEqual(ast[4:8], b"\x03\x10\0\0")
        base = 16 + len(source)
        nodes = [struct.unpack_from("<BBHHHHH4s", ast, i)
                 for i in range(base, len(ast), 16)]
        statements = [i for i,n in enumerate(nodes, 1) if n[0] in {30,31,32,34,35,36,37,38,39,40,41}]
        self.assertEqual([nodes[i-1][0] for i in statements], [39,32,41,39,40,40,32,41])
        self.assertEqual([nodes[i-1][6] for i in statements], statements[1:]+[0])
        self.assertEqual(nodes[-1][0], 33)
        self.assertEqual(nodes[-1][4], 1)
        self.assertEqual([n[0] for n in nodes].count(42), 1)
        self.assertEqual([n[0] for n in nodes].count(43), 2)
        self.ast("fn main(){return f(g(),(2+3)*4)} fn f(a,b){return a+b} fn g(){return 1}")

    def test_depth_limit_and_budget_restoration(self):
        function = "fn down(n){if n==0 {return 7} return down(n-1)} "
        self.value(function+"fn main(){return down(62)}", 7)
        result = self.execute(function+"fn main(){return down(63)}")
        self.assertEqual(result.returncode, 70)
        self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0R-003\]")
        self.value(function+"fn main(){let i=100 let x=0 while i {x=down(3) i=i-1} return x}", 7)

    def test_faults_and_argument_evaluation_order(self):
        self.value("fn bad(){return 1/0} fn main(){if 0 {return bad()} return 9}", 9)
        source = "fn f(a,b){return a+b}\nfn main(){return f(\n1/0,\n9223372036854775807+1)}"
        result = self.execute(source)
        self.assertEqual(result.returncode, 70)
        self.assertTrue(result.stderr.startswith(b"input:3:2: error[C0R-001]"), result.stderr)

    def test_high_parameter_ids_and_caller_values(self):
        locals_ = " ".join(f"let v{i}={i}" for i in range(88))
        self.value(f"fn main(){{{locals_} return v87+f(v86,v85)}} "
                   "fn f(a,b){let c=a+b if c {let a=a+1 c=a+b} return c}", 259)
        for n in range(1, 9):
            self.value("fn square(x){return x*x} fn mix(a,b){return a*3+b} "
                       f"fn main(){{let x={n} return square(x)+mix(square(x+1),square(x+2))+x}}",
                       n*n+3*(n+1)**2+(n+2)**2+n)

    def test_backend_arity_bounds_without_frontend(self):
        def stream(arguments, parameters):
            # Each record is built independently of the frontend under test.
            source = b"fn main(){return f(1,1)} fn f(a){return 1}"
            records, statements = [], []
            def node(kind, anchor, left=0, right=0, statement=False):
                offset = source.index(anchor)
                records.append([kind, 0, offset, len(anchor), left, right, 0, b"\0"*4])
                if statement:
                    statements.append(len(records))
                return len(records)
            node(39,b"main",statement=True)
            previous = 0
            for _ in range(arguments):
                value = node(5,b"1")
                previous = node(43,b",",previous,value)
            call = node(42,b"f(",previous)
            records[call-1][3] = 1
            node(32,b"return",call,statement=True)
            node(41,b"}",statement=True)
            entry = node(39,b"f(",statement=True)
            records[entry-1][3] = 1
            for _ in range(parameters):
                node(40,b"a",statement=True)
            value = node(5,b"1")
            node(32,b"return",value,statement=True)
            node(41,b"}",statement=True)
            node(33,b"fn",statements[0])
            for current, following in zip(statements,statements[1:]):
                records[current-1][6] = following
            return (struct.pack("<4sBBHHHHH", b"NQAF",3,16,0,len(source),len(records),len(records),32)
                    +source+b"".join(struct.pack("<BBHHHHH4s", *record) for record in records))
        # One case exceeds only the call bound, the other only the parameter bound.
        for arguments,parameters in [(7,0),(0,7)]:
            result = run(BACKEND, stream(arguments,parameters))
            self.assertEqual((result.returncode,result.stdout), (1,b""))
            self.assertIn(b"[C0B-002]", result.stderr)

    def test_ast_mutations_and_determinism(self):
        source = "fn main(){return f(7)} fn f(x){if x {return x} return 0}"
        ast = self.ast(source)
        base = 16 + len(source)
        kinds = {kind: next(i for i in range(base,len(ast),16) if ast[i]==kind)
                 for kind in [39,40,41,42,43]}
        for offset,value in [(4,2), (kinds[39]+6,1), (kinds[40],5), (kinds[41],38),
                             (kinds[42]+6,255), (kinds[43]+8,0), (kinds[43]+10,1),
                             (kinds[39]+12,1)]:
            corrupted = bytearray(ast)
            corrupted[offset] = value
            result = run(BACKEND, corrupted)
            self.assertEqual((result.returncode, result.stdout), (1,b""), (offset,result.stderr))
        self.assertEqual(self.artifact(source), self.artifact(source))
        rng = random.Random(29)
        for _ in range(32):
            corrupted = bytearray(ast)
            corrupted[rng.randrange(base,len(ast))] = rng.randrange(256)
            result = run(BACKEND, corrupted)
            self.assertIn(result.returncode, (0,1))
            if result.returncode:
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"error[C0B-", result.stderr)

    def test_source_wrapper_calls_and_atomic_failure(self):
        with tempfile.TemporaryDirectory(prefix="c029-wrapper-") as tmp:
            directory = Path(tmp)
            source, output = directory / "calls.nql", directory / "program"
            temps = directory / "temps"
            temps.mkdir()
            env = dict(os.environ, TMPDIR=str(temps))
            source.write_text("fn main(){return add(20,22)} fn add(a,b){return a+b}")
            result = subprocess.run(["bash", str(STAGE / "compile-source.sh"), str(source), str(output)],
                                    capture_output=True, timeout=30, env=env)
            self.assertEqual((result.returncode,result.stdout,result.stderr), (0,b"",b""))
            self.assertEqual(run(output).returncode, 42)
            good = output.read_bytes()
            source.write_text("fn main(){return add(20)} fn add(a,b){return a+b}")
            result = subprocess.run(["bash", str(STAGE / "compile-source.sh"), str(source), str(output)],
                                    capture_output=True, timeout=30, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b"")
            self.assertIn(b"error[C0B-", result.stderr)
            self.assertEqual(output.read_bytes(), good)
            self.assertEqual(list(temps.iterdir()), [])
            self.assertEqual(sorted(p.name for p in directory.iterdir()), ["calls.nql","program","temps"])


if __name__ == "__main__":
    unittest.main()
