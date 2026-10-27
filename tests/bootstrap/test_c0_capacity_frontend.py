"""Wide frontend behavior; only canonical executables parse the source."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import platform
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import unittest

from c031_support import (assert_owned_graph, build_predecessors, candidate_binary,
                         decode_nqaf, encode_profile_source, run_native)


ROOT = Path(__file__).resolve().parents[2]
STATEMENTS = {30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 44}


class CapacityFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary(
            "C0_FRONTEND", ROOT / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed")

    def parse(self, source, *, profile=False):
        payload = encode_profile_source(source) if profile else source
        result = run_native(self.frontend, payload, timeout=120)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        header, nodes = decode_nqaf(result.stdout)
        self.assertEqual(header["source"], source)
        self.assert_graph(header, nodes)
        return header, nodes

    def assert_graph(self, header, nodes):
        assert_owned_graph(header, nodes)
        statements = [i for i, node in enumerate(nodes, 1) if node[0] in STATEMENTS]
        self.assertTrue(statements)
        expected_next = dict(zip(statements, statements[1:] + [0]))
        for node_id, node in enumerate(nodes, 1):
            self.assertLess(node[4], node_id)
            self.assertLess(node[5], node_id)
            self.assertEqual(node[6], expected_next.get(node_id, 0))
        self.assertEqual((nodes[-1][0], nodes[-1][4], nodes[-1][5:]),
                         (33, statements[0], (0, 0)))

    def reject(self, payload, *, code, source=None, offset=None):
        result = run_native(self.frontend, payload, timeout=120)
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertRegex(result.stderr, rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0P-\d{3}\]: .+; .+\n$")
        self.assertIn(f"[C0P-{code:03d}]".encode(), result.stderr)
        if offset is not None:
            line = source[:offset].count(b"\n") + 1
            column = offset - source.rfind(b"\n", 0, offset)
            self.assertTrue(result.stderr.startswith(f"input:{line}:{column}: ".encode()),
                            result.stderr)
        return result

    def test_source_crosses_legacy_limit(self):
        source = b"fn main(){return 7}".ljust(8193, b" ")
        header, nodes = self.parse(source)
        self.assertEqual((header["version"], header["source_length"],
                          header["runtime_profile"]), (5, 8193, 0))
        self.assertEqual(len(nodes), 3)

    def test_explicit_profile_forces_v5(self):
        header, nodes = self.parse(b"fn main(){return 7}", profile=True)
        self.assertEqual((header["version"], header["runtime_profile"],
                          header["dialect"]), (5, 1, 1))
        self.assertEqual(len(nodes), 3)

    def test_source_capacity_and_profile_header_exclusion(self):
        source = b"fn main(){return 7}".ljust(262144, b" ")
        for profile in (False, True):
            with self.subTest(profile=profile):
                header, _ = self.parse(source, profile=profile)
                self.assertEqual((header["source_length"], header["runtime_profile"]),
                                 (262144, int(profile)))
                overflow = source + b" "
                payload = encode_profile_source(overflow) if profile else overflow
                self.reject(payload, code=2, source=overflow, offset=262144)

    def test_exact_token_bound_and_first_excess_token(self):
        # Eight envelope/return tokens plus two tokens per added binary operation.
        source = b"fn main(){return 0" + b"+0" * 32764 + b"}"
        header, nodes = self.parse(source)
        self.assertEqual((header["version"], header["token_count"]), (5, 65536))
        self.assertEqual(len(nodes), 65531)
        overflow = source[:-1] + b";}"
        self.reject(overflow, code=3, source=overflow, offset=len(overflow) - 1)

    def test_large_operator_and_operand_stacks(self):
        cases = [
            b"fn main(){return " + b"(" * 32764 + b"0" + b")" * 32764 + b"}",
            b"fn main(){return " + b"0+(" * 16382 + b"0" + b")" * 16382 + b"}",
        ]
        for source, count in zip(cases, (3, 32767)):
            with self.subTest(nodes=count):
                header, nodes = self.parse(source)
                self.assertEqual(header["token_count"], 65536)
                self.assertEqual(len(nodes), count)

    def test_deep_call_markers_and_live_operand_bases(self):
        # Syntax only: undeclared f and runtime recursion limits belong to backend tests.
        for opening, depth, token_count, node_count in (
                (b"f(", 21842, 65534, 43689),
                (b"0+f(", 13105, 65533, 52425)):
            with self.subTest(opening=opening):
                source = b"fn main(){return " + opening * depth + b"0" + b")" * depth + b"}"
                header, nodes = self.parse(source)
                self.assertEqual((header["version"], header["dialect"],
                                  header["token_count"], len(nodes)),
                                 (5, 3, token_count, node_count))
                self.assertEqual(sum(node[0] == 42 for node in nodes), depth)
                self.assertEqual(sum(node[0] == 43 for node in nodes), depth)

    def test_high_spans_preserve_legacy_node_meaning(self):
        sources = [
            b"fn main(){let x=1 x=(x+2)*3 return x}",
            b"fn main(){let x=0 while x<2 {if x==1 {x=x+1} else {x=x+2}} return x}",
            b"fn sum(a,b,c,d,e,f){return a+b+c+d+e+f} fn main(){return sum(1,2,3,4,5,6)}",
            b"fn main(){byte_store(0,65) output_write(0,1) return byte_load(0)}",
        ]
        with tempfile.TemporaryDirectory(prefix="c031-span-parity-") as directory:
            old = build_predecessors(Path(directory))["frontend"]
            for source in sources:
                with self.subTest(source=source[:40]):
                    expected = run_native(old, source)
                    self.assertEqual((expected.returncode, expected.stderr), (0, b""))
                    legacy, narrow = decode_nqaf(expected.stdout)
                    wide, nodes = self.parse(b" " * 65536 + source)
                    self.assertEqual((wide["version"], wide["dialect"],
                                      wide["token_count"], wide["root_id"]),
                                     (5, legacy["version"], legacy["token_count"], legacy["root_id"]))
                    self.assertEqual(nodes, [(k, f, off + 65536, n, left, right, nxt)
                                             for k, f, off, n, left, right, nxt in narrow])

    def test_long_binding_and_callee_lengths(self):
        for length in (65535, 65536):
            name = b"a" * length
            sources = [
                (b"fn main(){let " + name + b"=7 return " + name + b"}", {4}),
                (b"fn " + name + b"(){return 7} fn main(){return " + name + b"()}", {39, 42}),
            ]
            for source, kinds in sources:
                with self.subTest(length=length, kinds=kinds):
                    header, nodes = self.parse(source)
                    long_nodes = [node for node in nodes if node[0] in kinds and node[3] == length]
                    self.assertEqual(len(long_nodes), 2)
                    self.assertEqual(header["version"], 5)
                    for node in long_nodes:
                        self.assertEqual(source[node[2]:node[2] + node[3]], name)

    def test_high_source_offsets_and_physical_statement_chain(self):
        prefix = b"fn main(){".ljust(65536, b" ")
        source = prefix + b"value=0 " * 300 + b"return 7+8*9}"
        header, nodes = self.parse(source)
        self.assertEqual(header["version"], 5)
        self.assertEqual(sum(node[0] == 31 for node in nodes), 300)
        for node in nodes[:-1]:
            self.assertGreaterEqual(node[2], 65536)
        for kind, lexeme in ((15, b"+"), (16, b"*")):
            node = next(node for node in nodes if node[0] == kind)
            self.assertEqual(source[node[2]:node[2] + node[3]], lexeme)

    def test_large_decimal_error_locations(self):
        sources = [b"\n" * 70000 + b"fn main(){return +}",
                   b" " * 70000 + b"fn main(){return +}"]
        for source in sources:
            for profile in (False, True):
                with self.subTest(newlines=source.count(b"\n"), profile=profile):
                    self.reject(encode_profile_source(source) if profile else source,
                                code=6, source=source, offset=source.index(b"+"))

    def test_malformed_and_truncated_envelopes(self):
        header = encode_profile_source(b"")
        for length in range(16):
            with self.subTest(prefix=length):
                result = run_native(self.frontend, header[:length])
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(b"error[C0P-", result.stderr)
                if length >= 4:
                    self.assertTrue(result.stderr.startswith(b"input:1:1: error[C0P-013]"))
        for offset, values in ((4, (0, 2, 255)), (5, (0, 2, 255)),
                               *[(i, (1,)) for i in range(6, 16)]):
            for value in values:
                with self.subTest(offset=offset, value=value):
                    payload = bytearray(header + b"fn main(){return 7}")
                    payload[offset] = value
                    result = self.reject(payload, code=13)
                    self.assertTrue(result.stderr.startswith(b"input:1:1:"))

    def test_envelope_recognized_only_once(self):
        payload = encode_profile_source(b"fn main(){return 7}")
        result = self.reject(encode_profile_source(payload), code=1,
                             source=payload, offset=4)
        self.assertNotIn(b"C0P-013", result.stderr)
        self.parse(b"# NQSC is ordinary comment text\nfn main(){return 7}", profile=True)
        self.reject(b"fn main(){return 7} let", code=10,
                    source=b"fn main(){return 7} let", offset=20)

    def streamed(self, payload, *, pause_before_eof=False, tail=b""):
        runner = [str(self.frontend)]
        if platform.machine() != "x86_64":
            qemu = shutil.which("qemu-x86_64")
            self.assertIsNotNone(qemu, "x86_64 execution unavailable")
            runner.insert(0, qemu)
        emitted, sent, release = threading.Event(), threading.Event(), threading.Event()
        with subprocess.Popen(runner, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, bufsize=0) as child:
            with ThreadPoolExecutor(max_workers=3) as pool:
                def drain(stream, mark=False):
                    chunks = []
                    while chunk := stream.read(65536):
                        chunks.append(chunk)
                        if mark:
                            emitted.set()
                    return b"".join(chunks)

                def feed():
                    try:
                        for byte in payload:
                            child.stdin.write(bytes([byte]))
                            time.sleep(0.001)
                        sent.set()
                        if pause_before_eof and not release.wait(120):
                            raise TimeoutError("test writer did not receive EOF release")
                        child.stdin.write(tail)
                    finally:
                        child.stdin.close()

                out = pool.submit(drain, child.stdout, True)
                err = pool.submit(drain, child.stderr)
                writer = pool.submit(feed)
                try:
                    if pause_before_eof:
                        self.assertTrue(sent.wait(10), "fragment writer did not finish")
                        self.assertFalse(emitted.wait(0.15), "AST emitted before EOF")
                        self.assertIsNone(child.poll(), "frontend accepted a read boundary as EOF")
                        release.set()
                    child.wait(timeout=120)
                    writer.result(timeout=5)
                    return child.returncode, out.result(timeout=5), err.result(timeout=5)
                finally:
                    release.set()
                    if child.poll() is None:
                        child.kill()
                    child.wait(timeout=5)

    def test_fragmented_profile_header_keeps_source_offsets(self):
        source = b"fn main(){\nreturn 7}\n"
        expected = run_native(self.frontend, encode_profile_source(source), timeout=120)
        self.assertEqual(expected.returncode, 0, expected.stderr)
        self.assertEqual(self.streamed(encode_profile_source(source)),
                         (0, expected.stdout, b""))
        broken = b"fn main(){\nreturn +}\n"
        code, out, err = self.streamed(encode_profile_source(broken))
        self.assertEqual((code, out), (1, b""))
        self.assertTrue(err.startswith(b"input:2:8: error[C0P-006]"), err)

    def test_waits_for_eof_after_valid_prefix(self):
        source = b"fn main(){return 7}\n"
        for profile in (False, True):
            with self.subTest(profile=profile):
                payload = encode_profile_source(source) if profile else source
                code, out, err = self.streamed(payload, pause_before_eof=True, tail=b"@")
                self.assertEqual((code, out), (1, b""))
                self.assertTrue(err.startswith(b"input:2:1: error[C0P-001]"), err)

    def test_actual_component_sources(self):
        for name in ("frontend.nql", "backend.nql"):
            with self.subTest(source=name):
                source = (ROOT / "bootstrap/compiler/c0" / name).read_bytes()
                self.assertGreater(len(source), 8192)
                header, _ = self.parse(source)
                self.assertEqual((header["version"], header["dialect"],
                                  header["runtime_profile"]), (5, 4, 0))

    def test_frozen_predecessor_limits_and_legacy_bytes(self):
        sources = [
            b"fn main(){return 7}",
            b"fn main(){let value=3 value=value+2*4 return value}",
            b"fn main(){let i=0 while i<4 {if i==2 {i=i+1} else {i=i+2}} return i}",
            b"fn add(a,b){return a+b} fn main(){return add(2,add(3,4))}",
            b"fn main(){byte_store(0,65) output_write(0,1) return byte_load(0)}",
            b"fn main(){\r\n# comment\r\nreturn 1;\r\n}\r\n",
            b"fn main(){return 0}".ljust(8192, b" "),
            b"fn main(){return 0" + b"+0" * 252 + b"}",
        ]
        with tempfile.TemporaryDirectory(prefix="c031-front-parity-") as directory:
            old = build_predecessors(Path(directory))["frontend"]
            for source in sources:
                with self.subTest(source=source[:50]):
                    expected = run_native(old, source)
                    actual = run_native(self.frontend, source, timeout=120)
                    self.assertEqual(expected.returncode, 0, expected.stderr)
                    self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                     (expected.returncode, expected.stdout, expected.stderr))
            for source, code in [(sources[0].ljust(8193, b" "), b"C0P-002"),
                                 (b"fn main(){return 0" + b"+0" * 253 + b"}", b"C0P-003")]:
                result = run_native(old, source)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(code, result.stderr)
                self.assertEqual(self.parse(source)[0]["version"], 5)


class WideWireBoundaryTests(unittest.TestCase):
    def test_frontend_storage_layout_is_bounded_and_disjoint(self):
        # Contract arithmetic only; compiler address use is checked in code review.
        regions = [
            ("source/lookahead", 0, 0x41000, 262145 + 6),
            ("tokens/sentinel", 0x50000, 0x11000C, 65537 * 12),
            ("state/scratch", 0x120000, 0x130000, 65536),
            ("nodes", 0x200000, 0x400000, 65536 * 32),
            ("operators/sentinel", 0x400000, 0x4C000C, 65537 * 12),
            ("operands/sentinel", 0x4D0000, 0x510004, 65537 * 4),
            ("calls/sentinel", 0x520000, 0x620010, 65537 * 16),
            ("blocks/sentinel", 0x630000, 0x630410, 65 * 16),
            ("header", 0x640000, 0x640020, 32),
            ("diagnostics/serialization", 0x641000, 0x651000, 65536),
            ("inactive stores", 0x7FF000, 0x7FF100, 256),
        ]
        previous_end = 0
        for name, start, end, required in regions:
            with self.subTest(region=name):
                self.assertGreaterEqual(start, previous_end)
                self.assertGreater(end, start)
                self.assertGreaterEqual(end - start, required)
                self.assertLessEqual(end, 16 * 1024 * 1024)
                previous_end = end

    def test_exact_node_storage_and_u32_ids(self):
        # Wire/storage oracle only: this deliberately is not a parser grammar fixture.
        count = 65536
        source = b"x" * 262144
        header = struct.pack("<4sBBHIIIIBBHI", b"NQAF", 5, 32, 0,
                             len(source), count, count, count, 1, 0, 0, 0)
        records = b"".join(struct.pack("<BBHIIIIIII", 33, 0, 0, 0, 1, i, 0, 0, 0, 0)
                           for i in range(count))
        wire = header + source + records
        decoded, nodes = decode_nqaf(wire)
        assert_owned_graph(decoded, nodes)
        self.assertEqual((decoded["node_count"], decoded["root_id"]), (count, count))
        self.assertEqual(len(records), 32 * 65536)
        self.assertEqual(len(wire), 2359328)
        excessive = bytearray(wire)
        struct.pack_into("<I", excessive, 12, 65537)
        with self.assertRaisesRegex(ValueError, "node count"):
            decode_nqaf(excessive)
        excessive = bytearray(wire)
        struct.pack_into("<I", excessive, 32 + len(source) + 12, 65537)
        with self.assertRaisesRegex(ValueError, "invalid ID"):
            decode_nqaf(excessive)


if __name__ == "__main__":
    unittest.main()
