"""AST and failure oracle only: the tested executable is built by canonical B0."""

import itertools
import hashlib
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import platform
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from standard_fd_fault import invalidate_standard_fd

from c031_support import assert_owned_graph, candidate_binary, decode_nqaf, encode_profile_source


ROOT = Path(__file__).resolve().parents[2]
BINARY = candidate_binary("C0_FRONTEND", ROOT / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed")
if (__name__ == "__main__" and len(sys.argv) > 1 and not sys.argv[1].startswith("-")
        and sys.argv[1].split(".")[0] != "FrontendTests"):
    BINARY = Path(sys.argv.pop(1)).resolve(strict=True)
RUNNER = (["qemu-x86_64"] if platform.machine() != "x86_64" else []) + [str(BINARY)]
OPS = {15: "+", 16: "*", 17: "-", 18: "/"}


class FrontendTests(unittest.TestCase):
    def run_source(self, source, **kwargs):
        return subprocess.run(RUNNER, input=source, capture_output=True, timeout=5, **kwargs)

    def decode(self, source, output, expected_version=1):
        self.assertGreaterEqual(len(output), 16)
        magic, version, size, flags, length, count, root, tokens = struct.unpack(
            "<4sBBHHHHH", output[:16]
        )
        self.assertEqual((magic, version, size, flags), (b"NQAF", expected_version, 16, 0))
        self.assertEqual(length, len(source))
        self.assertEqual(output[16:16 + length], source)
        self.assertEqual(len(output), 16 + length + 16 * count)
        self.assertTrue(0 < count <= 512)
        self.assertTrue(0 < tokens <= 512)
        self.assertEqual(root, count)
        nodes = [None] + [struct.unpack_from("<BBHHHHH4s", output, 16 + length + i * 16)
                          for i in range(count)]
        assert_owned_graph({"node_count": count, "root_id": root},
                           [node[:7] for node in nodes[1:]])
        statement_kinds = {30, 31, 32} | ({39, 41} if version == 3 else set())
        statements = [i for i in range(1, count + 1) if nodes[i][0] in statement_kinds]
        physical_next = dict(zip(statements, statements[1:] + [0]))
        trees = {}
        for index in range(1, count + 1):
            kind, flags, offset, length, left, right, nxt, reserved = nodes[index]
            self.assertEqual((flags, reserved), (0, b"\0" * 4))
            self.assertTrue(0 < length and offset + length <= len(source))
            self.assertTrue(0 <= left < index and 0 <= right < index, "non-postorder child")
            self.assertEqual(nxt, physical_next.get(index, 0), "physical statement order")
            lexeme = source[offset:offset + length].decode("ascii")
            if kind in {4, 5}:
                self.assertEqual((left, right), (0, 0))
                trees[index] = ("id" if kind == 4 else "int", lexeme)
            elif kind in OPS:
                self.assertEqual(lexeme, OPS[kind])
                trees[index] = (lexeme, trees[left], trees[right])
            elif kind in {30, 31}:
                lhs = trees[left]
                self.assertEqual(lhs[0], "id")
                self.assertEqual(lexeme, "let" if kind == 30 else lhs[1])
                trees[index] = ("let" if kind == 30 else "assign", lhs, trees[right])
            elif kind == 32:
                self.assertEqual((lexeme, right), ("return", 0))
                self.assertEqual(nxt, index + 1 if version == 3 else 0)
                trees[index] = ("return", trees[left])
            elif kind in {39, 41} and version == 3:
                self.assertEqual((left, right), (0, 0))
                if kind == 39:
                    self.assertRegex(lexeme, r"^[A-Za-z_][A-Za-z_0-9]*$")
                else:
                    self.assertEqual(lexeme, "}")
                trees[index] = ("function" if kind == 39 else "end", lexeme)
            else:
                self.assertEqual((kind, lexeme, right, index), (33, "fn", 0, root))
                self.assertTrue(statements)
                self.assertEqual(left, statements[0])
                trees[index] = [trees[statement] for statement in statements]
        tree = trees[root]
        if version == 3:
            self.assertEqual(tree[0][0], "function")
            self.assertEqual(tree[-1][0], "end")
            self.assertEqual(tree[-2][0], "return")
        else:
            self.assertEqual(tree[-1][0], "return")
        return tree, tokens

    def parse(self, source):
        if isinstance(source, str):
            source = source.encode()
        result = self.run_source(source)
        self.assertEqual((result.returncode, result.stderr), (0, b""), source[:200])
        return self.decode(source, result.stdout)[0]

    def reject(self, source, offset=None, code=None):
        result = self.run_source(source)
        self.assertEqual(result.returncode, 1, (source[:200], result.stderr))
        self.assertEqual(result.stdout, b"")
        self.assertRegex(result.stderr, rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0P-[0-9]{3}\]: .+; .+\n$")
        if offset is not None:
            line = source[:offset].count(b"\n") + 1
            col = offset - source.rfind(b"\n", 0, offset)
            self.assertTrue(result.stderr.startswith(f"input:{line}:{col}: ".encode()), result.stderr)
        if code is not None:
            self.assertIn(f"[C0P-{code:03d}]".encode(), result.stderr)

    def test_precedence_and_associativity_matrix(self):
        a, b, c = ("id", "alpha"), ("id", "beta"), ("int", "12")
        for first, second in itertools.product("+-*/", repeat=2):
            with self.subTest(first=first, second=second):
                expected = ((first, a, (second, b, c)) if first in "+-" and second in "*/"
                            else (second, (first, a, b), c))
                self.assertEqual(self.parse(f"fn main(){{return alpha{first}beta{second}12}}"),
                                 [("return", expected)])
                self.assertEqual(self.parse(f"fn main(){{return (alpha{first}beta){second}12;}}"),
                                 [("return", (second, (first, a, b), c))])
                self.assertEqual(self.parse(f"fn main(){{return alpha{first}(beta{second}12)}}"),
                                 [("return", (first, a, (second, b, c)))])

    def test_statements_names_and_keyword_boundaries(self):
        source = """// Source-driven statements
fn main() {
    let lengthy_name42 = 1 + 2 * 3
    let return_value = (lengthy_name42 - 4) / (2 + 1);
    lengthy_name42 = lengthy_name42 + return_value * 2
    return lengthy_name42 / (7 - 2) - 1;
} # EOF comment"""
        tree = self.parse(source)
        self.assertEqual([s[0] for s in tree], ["let", "let", "assign", "return"])
        self.assertEqual(tree[0], ("let", ("id", "lengthy_name42"),
                                  ("+", ("int", "1"), ("*", ("int", "2"), ("int", "3")))))
        self.assertEqual(tree[1][1], ("id", "return_value"))
        self.assertEqual(tree[2][1], ("id", "lengthy_name42"))
        self.assertEqual(tree[-1][1][0], "-")

    def test_more_than_eight_bindings(self):
        body = " ".join(f"let value{i} = {i}" for i in range(24))
        self.assertEqual(len(self.parse(f"fn main(){{{body} return value23}}")), 25)

    def test_nested_groups_and_long_expression(self):
        self.assertEqual(self.parse("fn main(){return " + "(" * 252 + "7" + ")" * 252 + "}"),
                         [("return", ("int", "7"))])
        self.parse("fn main(){return 0" + "+0" * 252 + "}")
        source = b"fn main(){return 0" + b"+0" * 253 + b"}"
        result = self.run_source(source)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        header, nodes = decode_nqaf(result.stdout)
        self.assertEqual((header["version"], header["token_count"]), (5, 514))
        assert_owned_graph(header, nodes)

    def test_source_capacity_and_short_reads(self):
        source = b"fn main(){return 7}"
        self.parse(source + b" " * (8192 - len(source)))
        larger = source.ljust(8193, b" ")
        result = self.run_source(larger)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        header, nodes = decode_nqaf(result.stdout)
        self.assertEqual((header["version"], header["source"]), (5, larger))
        assert_owned_graph(header, nodes)
        expected = self.run_source(source).stdout
        with subprocess.Popen(RUNNER, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as child:
            def feed():
                for byte in source:
                    child.stdin.write(bytes([byte]))
                    child.stdin.flush()
                    time.sleep(0.01)
                child.stdin.close()
            writer = threading.Thread(target=feed)
            writer.start()
            child.wait(timeout=5)
            writer.join(timeout=5)
            self.assertFalse(writer.is_alive())
            self.assertEqual((child.returncode, child.stdout.read(), child.stderr.read()), (0, expected, b""))

    def test_wide_nested_calls_keep_saved_anchors_and_arguments(self):
        source = (b"fn main(){" + b"x=0 " * 12000
                  + b" " * 20000 + b"f(1,g(2,h(3)),4) return 7}")
        for payload in (source, encode_profile_source(source)):
            result = self.run_source(payload)
            self.assertEqual((result.returncode, result.stderr), (0, b""))
            header, nodes = decode_nqaf(result.stdout)
            self.assertEqual(header["version"], 5)
            assert_owned_graph(header, nodes)
            calls = [node for node in nodes if node[0] == 42]
            self.assertEqual([source[n[2]:n[2] + n[3]] for n in calls], [b"h", b"g", b"f"])
            self.assertTrue(all(n[2] > 65535 and n[4] > 36000 for n in calls))
            self.assertEqual(sum(n[0] == 43 for n in nodes), 6)

    def test_complete_prefix_waits_for_eof(self):
        with subprocess.Popen(RUNNER, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as child:
            child.stdin.write(b"fn main(){return 7}\n")
            child.stdin.flush()
            time.sleep(0.1)
            self.assertIsNone(child.poll(), "accepted a read boundary as EOF")
            child.stdin.write(b"@")
            child.stdin.close()
            child.wait(timeout=5)
            self.assertEqual((child.returncode, child.stdout.read()), (1, b""))
            self.assertIn(b"input:2:1: error[C0P-001]", child.stderr.read())

    def test_deterministic_output_and_crlf(self):
        source = b"fn main() {\r\n # comment\r\n let _a42 = 0001;\r\n return _a42;\r\n}\r\n"
        self.parse(source)
        first = self.run_source(source)
        self.assertEqual(first.stdout, self.run_source(source).stdout)

    def test_terminal_return_after_conditional(self):
        source = b"fn main(){let ok=2 if ok {ok=0} else {ok=1} return ok==0}"
        result = self.run_source(source)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        header, nodes = decode_nqaf(result.stdout)
        assert_owned_graph(header, nodes)
        returns = [node for node in nodes if node[0] == 32]
        self.assertEqual(len(returns), 1)
        expression = nodes[returns[0][4] - 1]
        self.assertEqual(source[expression[2]:expression[2] + expression[3]], b"==")
        source = b"fn main(){let ok=2 if ok {return 0} else {return 1}}"
        self.reject(source, offset=len(source) - 1, code=4)

    def test_invalid_grammar_and_lexemes(self):
        # Function names, main arity and unknown callees now belong to the
        # semantic rejection suite in test_c0_functions.py, not syntax checking.
        for source in [b"", b"fn main(){}",
                       b"fn main(){let =1 return 1}", b"fn main(){x 1 return 1}",
                       b"fn main(){return }", b"fn main(){return ()}", b"fn main(){return 1+}",
                       b"fn main(){return 1 2}", b"fn main(){return 1(2)}", b"fn main(){return 1)}",
                       b"fn main(){return (1}", b"fn main(){return -1}",
                       b"fn main(){return 1;let x=2}", b"fn main(){return 1;;}",
                       b"fn main(){return 1} garbage",
                       b"fn main(){return 12abc}", b"fn main(){return 1.2}",
                       b"fn main(){return 1\0}", b"fn main(){return \xff}",
                       b"fn main(){return 1\r}"]:
            with self.subTest(source=source):
                self.reject(source)

    def test_error_location_and_no_prefix_acceptance(self):
        source = b"fn main() {\n let x = 1 + ;\n return x;\n}\n"
        self.reject(source, offset=source.index(b";"), code=6)
        source = b"fn main(){\n return 7;\n}\n@"
        self.reject(source, offset=source.index(b"@"), code=1)
        source = b"fn main(){return 7}"
        for length in range(len(source)):
            with self.subTest(length=length):
                self.reject(source[:length])

    def test_malformed_input_is_bounded(self):
        rng = random.Random(26)
        for _ in range(120):
            source = bytes(rng.choice(b"fn main(){}let=return0123+*/-;_\n\t@\0")
                           for _ in range(rng.randrange(1, 300)))
            result = self.run_source(source)
            self.assertEqual(result.returncode, 1, (source, result.stderr))
            self.assertEqual(result.stdout, b"")
            self.assertIn(b"error[C0P-", result.stderr)
        program = b"fn main(){let alpha=1+2*(3-4);alpha=(alpha+5)/2;return alpha;}"
        for length in range(len(program)):
            self.reject(program[:length])
        for _ in range(80):
            index = rng.randrange(len(program))
            source = program[:index] + bytes([rng.randrange(128)]) + program[index + 1:]
            result = self.run_source(source)
            self.assertIn(result.returncode, (0, 1), (source, result.stderr))
            if result.returncode == 0:
                self.assertEqual(result.stderr, b"")
                # A mutation may rename main into a valid function name; it
                # changes the envelope format, not the scalar expression tree.
                self.assertIn(result.stdout[4], (1, 3))
                self.decode(source, result.stdout, expected_version=result.stdout[4])
            else:
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"error[C0P-", result.stderr)

    def test_io_failure_exit_codes(self):
        source = b"fn main(){return 7}"
        result = self.run_source(source, preexec_fn=lambda: invalidate_standard_fd(1))
        self.assertEqual(result.returncode, 74)
        self.assertIn(b"output_write failed", result.stderr)
        result = self.run_source(b"", preexec_fn=lambda: invalidate_standard_fd(0))
        self.assertEqual(result.returncode, 74)
        self.assertIn(b"input_read failed", result.stderr)

    def test_materializer_atomicity_and_concurrency(self):
        with tempfile.TemporaryDirectory(prefix="c026-build-") as name:
            root = Path(name)
            for relative in ("bootstrap/compiler/b0/x86_64-linux/b0.seed",
                             "bootstrap/compiler/c0/frontend.nql",
                             "bootstrap/compiler/c0/x86_64-linux/materialize-frontend.sh",
                             "bootstrap/compiler/c0/x86_64-linux/c0-frontend.sha256"):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            builder = root / "bootstrap/compiler/c0/x86_64-linux/materialize-frontend.sh"
            compiler = candidate_binary("B0_COMPILER", ROOT / "bootstrap/compiler/b0/x86_64-linux/b0.seed")
            shutil.copy2(compiler, root / "bootstrap/compiler/b0/x86_64-linux/b0.seed")
            builder.with_name("c0-frontend.sha256").write_text(
                hashlib.sha256(BINARY.read_bytes()).hexdigest() + "  c0-frontend.seed\n")
            output = root / "frontend output"
            def build():
                return subprocess.run(["bash", str(builder), str(output)], capture_output=True, timeout=15)
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: build(), range(2)))
            for result in results:
                self.assertEqual((result.returncode, result.stdout), (0, b""), result.stderr)
            self.assertEqual(output.read_bytes(), BINARY.read_bytes())
            self.assertEqual(list(root.glob(".c0-frontend.seed.tmp.*")), [])

            old = output.read_bytes()
            manifest = builder.with_name("c0-frontend.sha256")
            manifest.write_text("0" * 64 + "  c0-frontend.seed\n")
            result = build()
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"hash mismatch", result.stderr)
            self.assertEqual(output.read_bytes(), old)
            self.assertEqual(list(root.glob(".c0-frontend.seed.tmp.*")), [])

            source = root / "bootstrap/compiler/c0/frontend.nql"
            source.write_text("fn main() { return + }\n")
            result = build()
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"B0 could not compile", result.stderr)
            self.assertEqual(output.read_bytes(), old)
            self.assertEqual(list(root.glob(".c0-frontend.seed.tmp.*")), [])

            for protected in (source, manifest, builder):
                before = protected.read_bytes()
                result = subprocess.run(["bash", str(builder), str(protected)], capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b"would replace", result.stderr)
                self.assertEqual(protected.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
