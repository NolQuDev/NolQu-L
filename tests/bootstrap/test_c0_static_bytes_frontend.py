"""Independent source/NQAF oracle for bounded C0.39 static byte literals.

The real frontend must keep quoted contents opaque, reject malformed literals
at the opening quote, resolve global write shadows before selecting /12, and
retain the frozen C0.38 bytes for existing source. No backend or shared NQAF
decoder supplies these expectations.
"""

import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = Path(os.environ.get(
    "C0_FRONTEND", ROOT / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed"))
RUNNER = [] if platform.machine() == "x86_64" else [shutil.which("qemu-x86_64") or "qemu-x86_64"]
PROFILE = b"NQSC\x01\x01" + bytes(10)
STATEMENTS = {30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 44, 45, 46}

# Filled from the unchanged, pinned C0.38 seed before frontend implementation.
# Each pair is the raw-source and compiler-profile transport SHA-256.
OLD_BYTES = {
    b"fn main(){return 7}": ('0f8f7a453e77f8cf84ae5548c6d4ef1867a26c3a68d2ed75e400bbb9e59283b9', 'e48c7dbff01d1a18a638187fb4d78455d0e8de74c8b8972fc5ac2556e1737cfc'),
    b"fn main(){let write=7 return write-2}": ('a407bd88a5997228fb9c715cea7772b85ea0277228e982a7e1fb94c898ed031e', 'cf4fca5edbf2604ee8c92b7a35304219387a605f5ff96405225099f6192904ee'),
    b"fn main(){let write_more=7 return write_more}": ('bb22a7c0cc1723ed2b52529374178206a9482a761a463d2b7fcde92ebd839ba1', '10b671efe560f72089f11717aca1dce31912cf0906b6210f47bfef5d423027ec'),
    b'// "write(1)" and \\xGG are comment text\nfn main(){return 0}': ('4f7d678f3b4af63139382e2ba37e14006451da0af4d0b7c6fa1e7480a7f02877', 'c95f751b39cba44b5340ea6bd7610072ae27d1e87ccf189473c6b251ae2b242a'),
    b'fn main(){# "unterminated comment literal\nreturn 0}': ('b1bae5a94327e1415fb193cb7b3e7b408584144f347260e7e33a54c105285594', 'f534405ddeb80c17bf38b32dfb90a15b77e967a87a1f5d0b6c0cd444f6c50ef7'),
    b"fn write(){return 7} fn main(){return write(1)}": ('f8b4c3e003825c4bb71dc9c5f918a63a2f73b49288b60e8fe7bfe18867a1611f', 'cdd1a58a66c3441fb31c3bb2bc37947fb24d5f3f0eaeed7d13264449d6521416'),
    b"fn main(){write(1,2) return 0} fn write(a){return a}": ('59e561ec5bc72c20d82045f3d2a4ff42f6e84346be1f2204f2f4dfdec503bba2', 'a83e888ba25729a481eb0d418710107062f193d00aa6cd35911a195a65542db5'),
    b"fn main(){let x=1 if x {x=2} else {x=3} while x<4{x=x+1} return x}": ('b86fef0f760c5c76d32b2e593ed6add3600ed8f401088667dfa6aaee47ddf909', '4b407ce89dbfaf0f69b5d92a97257aec192dec3b761ecee1c931cd315cfe55e1'),
    b"fn main(){return not 0 or 1 and 2}": ('18969380f3275bc8c5634e43c944b9ee3e0165ec9d007ac615fec810b9a60abd', '4e4549b7b2cf60ae3a24719dbafabc4fa7e0ac0c299aa945cb30f10297cd9994'),
    b"fn main(){return -7%3+~8&15^2|1<<2>>1}": ('2785630190d6553eb9cd8759ec7b55902f510138649d683fe25df55331c33379', 'af2ba54ee8c1bc01821f90d7666960af12ac6eeed1ed2fdb02634c34b9078a78'),
    b"fn main(){return f(1,g(2),3)} fn f(a,b,c){return a+b*c} fn g(x){return x}": ('28c4c74b10b0688808e80fa89acf8724cdeaa0792046b37c78a46df78f15ec3f', '8dc7c951cec197c24a7cdaee55e1e568a8bad206a32e56a03a56588ca719fe14'),
    b"fn main(){output_write(0,0) return 0}": ('450b9459eefb016d8a9f88afde9d071e5e9047d633d0c73d4e2096df5f2dd815', '97f3b11e5ef06017699e22732fcee32814039a606fba4d66e0d899908f3a2c84'),
    b"fn main(){return arg_count()}": ('4873d501426613e9e444af37d20928ba25f15867c688661c201567b24e05fb26', 'cd39e6df3224676e99301e2611d65083c7d9353dc5812747157a9632b0975195'),
    b'fn main(){unsafe {# safety: quotes " } { syscall6(0)\n} return 0}': ('f97afdc2d4878d6bf5d767299b6f52a7895f9339c10065509a83f050dd610ee6', '95f059da25df5f36063abbc3934456f91bc9ee5d16abaf2f2138289f470b9aa6'),
    b"fn main(){unsafe {# safety: caller owns effects\nsyscall6(39,0)} return 0}": ('844c9327165da5db3b1b9107f373a1b404b9f1b0a20fddfcc970dbee042d70a9', 'd0a6a18594602de5f99ef75d259b4371c8234a765c2ca29a3a7bc685d1320efd'),
    b"fn main(){let unsafe=0 if unsafe {unsafe {# safety: effects bounded\n}} return 0}": ('54d976b4d7b413423b3c2f1918fdbcd1a99b05d07e7d565e035571db9c047ba9', 'e00fdb7929db9027529d52d4c9096e9e5e430bad73ca320fed7b6440b9a98e79'),
    b"fn main(){let x=0 " + b"x=x+1 " * 180 + b"return x}": ('374a8f1a7bacc6b31210f56cd0bdba4a960f2d4617f7bfb5dd93a68f5001458d', 'db1be10720e477af030aba6079f6bbc7eb1a60fd4bcb84e8d0d2fd96a2653cfe'),
    b" " * 66000 + b"fn main(){return 0}": ('e37d43611ba86d1f3b0eb88664e61ede3ee491d0ba8c49ce06fe371242be3400', '0d344df79c6fa65ca16852e065f5cc8470bde7978a5e4c4f604f3aba82327ebb'),
}


def invoke(source, *, binary=FRONTEND, profile=False, timeout=30):
    payload = PROFILE + source if profile else source
    command = RUNNER + [str(binary.resolve(strict=True))]
    archive = os.environ.get("C039_FRONTEND_EVIDENCE_DIR")
    destination = None
    if archive:
        Path(archive).mkdir(parents=True, exist_ok=True)
        destination = Path(tempfile.mkdtemp(prefix="invoke-", dir=archive))
        (destination / "stdin.bin").write_bytes(payload)
    started = time.monotonic()
    try:
        result = subprocess.run(command, input=payload, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        if destination:
            (destination / "stdout.bin").write_bytes(error.stdout or b"")
            (destination / "stderr.bin").write_bytes(error.stderr or b"")
            (destination / "result.json").write_text(json.dumps(
                dict(command=command, timeout=timeout, timed_out=True)) + "\n")
        raise
    if destination:
        (destination / "stdout.bin").write_bytes(result.stdout)
        (destination / "stderr.bin").write_bytes(result.stderr)
        (destination / "result.json").write_text(json.dumps(dict(
            command=command, returncode=result.returncode,
            elapsed_seconds=time.monotonic() - started,
            source_sha256=hashlib.sha256(payload).hexdigest()), indent=2) + "\n")
    return result


def retain_stream_result(source, returncode, stdout, stderr):
    archive = os.environ.get("C039_FRONTEND_EVIDENCE_DIR")
    if archive:
        destination = Path(tempfile.mkdtemp(prefix="stream-", dir=archive))
        (destination / "stdin.bin").write_bytes(source)
        (destination / "stdout.bin").write_bytes(stdout)
        (destination / "stderr.bin").write_bytes(stderr)
        (destination / "result.json").write_text(json.dumps(dict(
            command=RUNNER + [str(FRONTEND)], returncode=returncode)) + "\n")


def decode_wire(test, output, source):
    """Independently validate framing, all reserved fields and unique ownership."""
    test.assertGreaterEqual(len(output), 16)
    test.assertEqual(output[:4], b"NQAF")
    version = output[4]
    if version >= 5:
        test.assertIn(version, range(5, 13))
        test.assertGreaterEqual(len(output), 32)
        magic, version, size, flags, length, count, root, tokens, dialect, profile, r16, r32 = (
            struct.unpack_from("<4sBBHIIIIBBHI", output))
        test.assertEqual((size, flags, r16, r32), (32, 0, 0, 0))
        test.assertIn(profile, (0, 1))
        test.assertIn(dialect, range(1, 5) if version == 5 else (version - 1,))
    else:
        magic, version, size, flags, length, count, root, tokens = struct.unpack_from(
            "<4sBBHHHHH", output)
        test.assertIn(version, range(1, 5))
        test.assertEqual((size, flags), (16, 0))
        dialect, profile = version, 0
    test.assertEqual(length, len(source))
    test.assertEqual(output[size:size + length], source)
    test.assertEqual(len(output), size + length + size * count)
    test.assertTrue(0 < count <= 65536)
    test.assertTrue(0 < tokens <= 65536)
    test.assertEqual(root, count)
    nodes = []
    for index in range(count):
        position = size + length + index * size
        if size == 32:
            kind, flags, reserved, offset, span, left, right, nxt, r1, r2 = (
                struct.unpack_from("<BBHIIIIIII", output, position))
            test.assertEqual((reserved, r1, r2), (0, 0, 0))
        else:
            kind, flags, offset, span, left, right, nxt, reserved = (
                struct.unpack_from("<BBHHHHH4s", output, position))
            test.assertEqual(reserved, bytes(4))
        test.assertEqual(flags, 0)
        test.assertTrue(0 < span <= length - offset)
        test.assertTrue(0 <= left <= index and 0 <= right <= index)
        test.assertTrue(0 <= nxt <= count)
        if kind == 58:
            test.assertEqual((version, left, right, nxt), (12, 0, 0, 0))
        nodes.append((kind, flags, offset, span, left, right, nxt))
    pending, seen = [root], set()
    while pending:
        node_id = pending.pop()
        test.assertTrue(1 <= node_id <= count and node_id not in seen)
        seen.add(node_id)
        pending.extend(child for child in nodes[node_id - 1][4:] if child)
    test.assertEqual(len(seen), count)
    statements = [i for i, node in enumerate(nodes, 1) if node[0] in STATEMENTS]
    links = dict(zip(statements, statements[1:] + [0]))
    for index, node in enumerate(nodes, 1):
        test.assertEqual(node[6], links.get(index, 0))
    return dict(version=version, size=size, dialect=dialect, profile=profile,
                tokens=tokens, root=root), nodes


class StaticBytesFrontendTests(unittest.TestCase):
    def parse(self, source, *, profile=False):
        result = invoke(source, profile=profile)
        self.assertEqual((result.returncode, result.stderr), (0, b""), result.stderr)
        header, nodes = decode_wire(self, result.stdout, source)
        self.assertEqual((header["version"], header["size"], header["dialect"], header["profile"]),
                         (12, 32, 11, int(profile)))
        return header, nodes, result.stdout

    def reject(self, source, *, code="C0P-015", offset=None, profile=False):
        if offset is None:
            offset = source.index(b'"')
        result = invoke(source, profile=profile)
        self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
        line = source[:offset].count(b"\n") + 1
        column = offset - source.rfind(b"\n", 0, offset)
        self.assertTrue(result.stderr.startswith(
            f"input:{line}:{column}: error[{code}]: ".encode()), result.stderr)
        self.assertRegex(result.stderr, rb": .+; .+\n$")
        return result

    def literals(self, source, nodes):
        return [source[n[2]:n[2] + n[3]] for n in nodes if n[0] == 58]

    def test_minimal_literal_is_full_span_leaf_and_v12(self):
        source = b'fn main(){let message="NQL" return 0}'
        for profile in (False, True):
            header, nodes, _ = self.parse(source, profile=profile)
            self.assertEqual((header["tokens"], header["root"]), (12, 8))
            self.assertEqual(nodes, [
                (39, 0, 3, 4, 0, 0, 4), (4, 0, 14, 7, 0, 0, 0),
                (58, 0, 22, 5, 0, 0, 0), (30, 0, 10, 3, 2, 3, 6),
                (5, 0, 35, 1, 0, 0, 0), (32, 0, 28, 6, 5, 0, 7),
                (41, 0, 36, 1, 0, 0, 0), (33, 0, 0, 2, 1, 0, 0)])

    def test_empty_printable_and_supported_escapes(self):
        literals = [b'""', b'"NQL"',
                    b'"' + bytes(c for c in range(32, 127) if c not in (34, 92)) + b'"',
                    b'" !#%&\'()*+,-./:;<=>?@[]^_`{|}~"',
                    br'"\0\n\r\t\"\\\x00\xff\xAF\xaF\xFf\x001"']
        for literal in literals:
            with self.subTest(literal=literal):
                source = b"fn main(){let x=" + literal + b" return 0}"
                for profile in (False, True):
                    _, nodes, _ = self.parse(source, profile=profile)
                    self.assertEqual(self.literals(source, nodes), [literal])

    def test_all_256_bytes_in_both_hex_cases(self):
        for code in ("02x", "02X"):
            literal = b'"' + b"".join(b"\\x" + format(value, code).encode()
                                      for value in range(256)) + b'"'
            source = b"fn main(){write(" + literal + b") return 0}"
            _, nodes, _ = self.parse(source)
            self.assertEqual(self.literals(source, nodes), [literal])
            self.assertEqual(sum(n[0] == 42 for n in nodes), 1)

    def test_invalid_raw_controls_and_nonascii_locate_opening_quote(self):
        for value in list(range(32)) + list(range(127, 256)):
            with self.subTest(value=value):
                self.reject(b'fn main(){\n let x="ok' + bytes([value]) + b'" return 0}')

    def test_invalid_escape_introducers(self):
        valid = b'0nrt"\\x'
        for value in range(256):
            if value not in valid:
                with self.subTest(value=value):
                    self.reject(b'fn main(){let x="\\' + bytes([value]) + b'" return 0}')

    def test_hex_requires_two_ascii_digits_and_terminated_quote(self):
        for tail in (br'\x', br'\x0', br'\xG0', br'\x0G', br'\x-1',
                     br'\x 1', br'\x1 ', b"\\x\xff0", b"\\x0\xff", b"\\"):
            with self.subTest(tail=tail):
                self.reject(b'fn main(){let x="' + tail + b'" return 0}')
        for source in (b'fn main(){let x="', b'fn main(){let x="text',
                       b'fn main(){let x="\\', b'fn main(){let x="\\x0'):
            self.reject(source, profile=True)

    def test_quoted_comment_brace_keyword_and_native_text_is_opaque(self):
        literal = br'"# // } { unsafe { syscall6(0) byte_address(0) fn return and or not % << \""'
        source = b"fn main(){let x=" + literal + b" return 0}"
        _, nodes, _ = self.parse(source)
        self.assertEqual(self.literals(source, nodes), [literal])
        self.assertEqual([n[0] for n in nodes], [39, 4, 58, 30, 5, 32, 41, 33])

    def test_comments_and_unsafe_header_quotes_do_not_open_literals(self):
        source = (b'// "\\xGG } unsafe\nfn main(){unsafe {# safety: " } \\xGG\n'
                  b'let x="body" } return 0} // "')
        _, nodes, _ = self.parse(source)
        self.assertEqual(self.literals(source, nodes), [b'"body"'])
        self.assertEqual(sum(n[0] == 45 for n in nodes), 1)
        begin = source.index(b"unsafe {#")
        end = source.index(b"let x")
        opener = next(n for n in nodes if n[0] == 45)
        self.assertEqual((opener[2], opener[3]), (begin, end - begin))
        self.reject(b'fn main(){unsafe {# "safety: no tag\nlet x="ok"} return 0}',
                    code="C0P-014", offset=10)

    def test_literals_do_not_grant_native_permission(self):
        source = b'fn main(){let x="unsafe {# safety: permitted }" return syscall6(39,0)}'
        self.reject(source, code="C0S-001", offset=source.index(b"syscall6"))
        source = b'fn main(){if 0 {let x="}" syscall6(39,0)} return 0}'
        self.reject(source, code="C0S-001", offset=source.index(b"syscall6"))

    def test_unshadowed_write_selects_v12_without_literal_or_arity_check(self):
        for body in (b"return write(1)", b"write(1) return 0", b"return write()",
                     b"let write=7 return write(1)",
                     b"return write(1,2)", b"return write(1,2,3,4,5,6)"):
            for profile in (False, True):
                with self.subTest(body=body, profile=profile):
                    source = b"fn main(){" + body + b"}"
                    _, nodes, _ = self.parse(source, profile=profile)
                    self.assertEqual(self.literals(source, nodes), [])
                    self.assertEqual(sum(n[0] == 42 for n in nodes), 1)

    def test_exact_global_write_shadow_in_both_orders_even_wrong_arity(self):
        for function in (b"fn write(){return 7}", b"fn write(x){return x}"):
            for main in (b"fn main(){return write(1,2)}", b"fn main(){write() return 0}"):
                for source in (function + main, main + function):
                    result = invoke(source)
                    self.assertEqual((result.returncode, result.stderr), (0, b""))
                    header, nodes = decode_wire(self, result.stdout, source)
                    self.assertIn(header["version"], (3, 4))
                    self.assertFalse(any(n[0] == 58 for n in nodes))
        source = b'fn main(){return write("x")} fn write(){return 0}'
        _, nodes, _ = self.parse(source)
        self.assertEqual(self.literals(source, nodes), [b'"x"'])
        self.parse(b"fn main(){return write(1)} fn write_more(x){return x}")

    def test_grouping_calls_operators_and_statement_boundaries(self):
        cases = (
            (b'fn main(){let x=(("a")) let y=x y="b" return 0}', [b'"a"', b'"b"']),
            (b'fn main(){write(f("a",g("b")),"c") return 0}', [b'"a"', b'"b"', b'"c"']),
            (b'fn main(){if "x" {let y="y"} else {let z="z"} return 0}', [b'"x"', b'"y"', b'"z"']),
            (b'fn main(){return -"a"%2+3*4<<1==2 and not "b" or "c"}', [b'"a"', b'"b"', b'"c"']),
            (b'fn main(){let x="a"-1 return 0}', [b'"a"']),
        )
        for source, wanted in cases:
            with self.subTest(source=source):
                _, nodes, _ = self.parse(source)
                self.assertEqual(self.literals(source, nodes), wanted)
        for source in (b'fn main(){return "a""b"}', b'fn main(){return "a"(1)}',
                       b'fn main(){write("a",) return 0}', b'fn main(){let x="a"1 return 0}'):
            result = invoke(source)
            self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)

    def test_wide_literal_span_offset_and_high_node_ids(self):
        literal = b'"' + b"a" * 66000 + b'"'
        for prefix in (b" " * 70000, b"fn main(){" + b"x=0 " * 17000):
            source = ((prefix + b"fn main(){" if prefix.startswith(b" ") else prefix)
                      + b"let message=" + literal + b" return 0}")
            header, nodes, _ = self.parse(source, profile=True)
            leaf_id, leaf = next((i, n) for i, n in enumerate(nodes, 1) if n[0] == 58)
            self.assertGreater(leaf[2], 65535)
            self.assertEqual(leaf[3], 66002)
            self.assertEqual(self.literals(source, nodes), [literal])
            if prefix.startswith(b"fn"):
                self.assertGreater(leaf_id, 50000)
                self.assertGreater(header["tokens"], 50000)

    def test_source_boundaries_and_eof_failure_publish_no_prefix(self):
        source = b'fn main(){let x="' + b"a" * (262144 - 28) + b'" return 0}'
        self.assertEqual(len(source), 262144)
        self.parse(source)
        self.reject(source + b" ", code="C0P-002", offset=262144)
        self.reject(b" " * (262144 - 1) + b'"')
        self.reject(b'fn main(){return 0}\n"unfinished')
        self.reject(b'fn main(){let x="ok" return 0}\n"bad\\q', offset=31)

    def test_literal_truncations_and_bounded_deterministic_mutations(self):
        prefix = b"fn main(){\n let x="
        literal = br'"abc\n\x00\"\\end"'
        for end in range(1, len(literal)):
            self.reject(prefix + literal[:end])
        rng = random.Random(39)
        for _ in range(60):
            tail = bytes(rng.choice(b'abc"\\x0G\n\xff') for _ in range(rng.randrange(1, 50)))
            source = prefix + b'"' + tail + b'" return 0}'
            result = invoke(source)
            self.assertIn(result.returncode, (0, 1))
            if result.returncode:
                self.assertEqual(result.stdout, b"")
                self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0P-\d{3}\]: ")
            else:
                self.assertEqual(result.stderr, b"")
                decode_wire(self, result.stdout, source)

    def test_frozen_old_source_transport_bytes(self):
        original = os.environ.get("C039_ORIGINAL_FRONTEND")
        for source, wanted in OLD_BYTES.items():
            self.assertEqual(len(wanted), 2, "missing preimplementation C0.38 oracle")
            for profile in (False, True):
                with self.subTest(source=source[:80], profile=profile):
                    result = invoke(source, profile=profile)
                    self.assertEqual((result.returncode, result.stderr), (0, b""), result.stderr)
                    self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), wanted[int(profile)])
                    if original:
                        old = invoke(source, profile=profile, binary=Path(original))
                        self.assertEqual((result.returncode, result.stdout, result.stderr),
                                         (old.returncode, old.stdout, old.stderr))

    def test_short_reads_and_waiting_for_real_eof(self):
        source = br'fn main(){let x="\x00\"\\" write(x) return 0}'
        wanted = invoke(source)
        self.assertEqual((wanted.returncode, wanted.stderr), (0, b""))
        with subprocess.Popen(RUNNER + [str(FRONTEND)], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as child:
            def feed():
                for byte in source:
                    child.stdin.write(bytes([byte]))
                    child.stdin.flush()
                    time.sleep(0.002)
                child.stdin.close()
            writer = threading.Thread(target=feed)
            writer.start()
            child.wait(timeout=15)
            writer.join(timeout=5)
            self.assertFalse(writer.is_alive())
            output, error = child.stdout.read(), child.stderr.read()
            retain_stream_result(source, child.returncode, output, error)
            self.assertEqual((child.returncode, output, error), (0, wanted.stdout, b""))
        with subprocess.Popen(RUNNER + [str(FRONTEND)], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as child:
            child.stdin.write(b'fn main(){let x="ok" return 0}\n')
            child.stdin.flush()
            time.sleep(0.05)
            self.assertIsNone(child.poll(), "accepted a read boundary as EOF")
            child.stdin.write(b'"bad\\q')
            child.stdin.close()
            child.wait(timeout=15)
            output, error = child.stdout.read(), child.stderr.read()
            retain_stream_result(b'fn main(){let x="ok" return 0}\n"bad\\q',
                                 child.returncode, output, error)
            self.assertEqual((child.returncode, output), (1, b""))
            self.assertTrue(error.startswith(b"input:2:1: error[C0P-015]: "))


if __name__ == "__main__":
    unittest.main()
