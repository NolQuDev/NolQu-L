"""Source/wire oracle for bottom annotations and logical bang.

These tests inspect the real frontend's NQAF bytes independently of the backend.
Accepting a /13 syntax tree proves no return, type or divergence property.
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
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = Path(os.environ.get(
    "C0_FRONTEND", ROOT / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed"))
RUNNER = [] if platform.machine() == "x86_64" else [shutil.which("qemu-x86_64") or "qemu-x86_64"]
PROFILE = b"NQSC\x01\x01" + bytes(10)
STATEMENTS = {30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 44, 45, 46}

# Frozen C039 outputs captured before implementation, including opaque bangs
# in /12 and an ordinary Never function. /4 also uses its existing frozen oracle.
OLD_BYTES = (
    (b'fn main(){return 7}', (1, 5), ('0f8f7a453e77f8cf84ae5548c6d4ef1867a26c3a68d2ed75e400bbb9e59283b9', 'e48c7dbff01d1a18a638187fb4d78455d0e8de74c8b8972fc5ac2556e1737cfc')),
    (b'fn main(){return 1!=2}', (2, 5), ('922d25c77606365bca8d109619ca64e8801ba2f0c07dd65888941ccab98cdfe2', '4c20391876f669e8f11e4578aacb019b03b7f84a350ffc76bdd7752812ab6009')),
    (b'fn f(){return 7} fn main(){return f()}', (3, 5), ('2feb2ee05356249a1074b6a74f03bfbe1d27f76e609f16c045312d9fdb6cd164', '58f3b87b6c8e9f1f6e695e5c7fac4de036085ec331efa4c124c939ec4a41e4e3')),
    (b'fn main(){let x=1 if x{x=2}else{x=3} return x}', (2, 5), ('057e4f28898915712558a637132b5b66b73f8e56d87a1154cf842ffdeb5cc376', 'f4aa86154b23022b2388cf493673d8840fa499c5d98a31deb9679048ca2ca18a')),
    (b' ' * 8200 + b'fn main(){return 7}', (5, 5), ('ff683d7277437b4a87f7a4357e0ae8738ffa5ef85bc5b04d604d7e65d55c3028', 'f0f80d8114a866deef412778febe2db4be497c109e33c4ae61fcdd4c696c3578')),
    (b'fn main(){unsafe {# safety: lexical scope\n} return 0}', (6, 6), ('df9f6fb6780e2599ae0131c71d4d7131f7ce1a53e23752f742663a26d4e210b7', '5c29d4d5964e6370628b5a58e35ad29b4289313276caa647484a99e0f763a53c')),
    (b'fn main(){return -7}', (7, 7), ('20b939c663923d4eb9ba0a61e9885017bd229e7df398dbd5fbbf2c24b4a49e1d', '343fb4dd5c96a0b289fd0e439f52b1e777482e550bf4414bd954023e55eeb2fe')),
    (b'fn main(){return ~8&15}', (8, 8), ('8788da8f2912c0b31a02c3ff28f665c9073d2b6598f63f7ecd45a78ee8d1eede', 'c823cdaea7e6b41d8922fa14db237ad2f73068ab1bf85c7d1b186e2c285870d1')),
    (b'fn main(){return not 0}', (9, 9), ('2bc0e6e35fa18d96624d0917a5028f38dbdfc566910a2aa910fdb66960eedfe5', '6d44547d95f7a49f2f1c76180195a51a97de3848ecb4c9223fe6e42fa8765867')),
    (b'fn main(){return 1<<2}', (10, 10), ('808c47574c850466810d4a42cecf106a327cf5788babd8328ad67cfe8151f8ff', 'b47f0c436268fed7e0a1a9dabbc5c3b425244d135f71d25ccd955d15a9a2471c')),
    (b'fn main(){return 7%3}', (11, 11), ('940814e4a8e9e3667b6293abf51871c79c22b181af17c94f286c2d393ff35869', 'cacfa8ffe1446ed4b496765693b9debbb0ecde408428fc98d22b5e2547f82d35')),
    (b'fn main(){let x="fn fake()->! != !!" return 0}', (12, 12), ('707d58bca0dafb08efbc3437280b6cb17fd6217fea0db87ce433652b827ad547', 'da2ebb8400af1b8250c95e384d899e8940d413635ae9e5f60c610bcc09b0a257')),
    (b'fn Never(){return 7} fn main(){return Never()}', (3, 5), ('fd11346cbd091206033c8f8f9b3335095915837d2b333957a94404d8c8aeac9c', 'd4e67b83304e9484c05482d9af1b6a379257bb47a92b6bb4d334a05641db98e2')),
    (b'fn main(){output_write(0,0) return 0}', (4, 5), ('450b9459eefb016d8a9f88afde9d071e5e9047d633d0c73d4e2096df5f2dd815', '97f3b11e5ef06017699e22732fcee32814039a606fba4d66e0d899908f3a2c84')),
)


def invoke(source, *, profile=False, timeout=45):
    payload = PROFILE + source if profile else source
    command = RUNNER + [str(FRONTEND.resolve(strict=True))]
    archive = os.environ.get("C0_NEVER_FRONTEND_EVIDENCE_DIR")
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
            (destination / "result.json").write_text(json.dumps(dict(
                command=command, timeout=timeout, timed_out=True)) + "\n")
        raise
    if destination:
        (destination / "stdout.bin").write_bytes(result.stdout)
        (destination / "stderr.bin").write_bytes(result.stderr)
        (destination / "result.json").write_text(json.dumps(dict(
            command=command, returncode=result.returncode,
            elapsed_seconds=time.monotonic() - started,
            stdin_sha256=hashlib.sha256(payload).hexdigest(),
            stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(result.stderr).hexdigest()), indent=2) + "\n")
    return result


def decode13(test, wire, source, profile):
    test.assertGreaterEqual(len(wire), 32)
    magic, version, size, flags, length, count, root, tokens, dialect, actual_profile, r16, r32 = (
        struct.unpack_from("<4sBBHIIIIBBHI", wire))
    test.assertEqual((magic, version, size, flags, dialect, actual_profile, r16, r32),
                     (b"NQAF", 13, 32, 0, 12, int(profile), 0, 0))
    test.assertEqual(length, len(source))
    test.assertEqual(wire[32:32 + length], source)
    test.assertEqual(len(wire), 32 + length + count * 32)
    test.assertTrue(0 < count <= 65536)
    test.assertTrue(0 < tokens <= 65536)
    test.assertEqual(root, count)
    records = []
    for index in range(count):
        kind, flags, reserved, offset, span, left, right, nxt, annotation, annotation_span = (
            struct.unpack_from("<BBHIIIIIII", wire, 32 + length + index * 32))
        test.assertEqual(reserved, 0)
        test.assertTrue(0 < span <= length - offset)
        test.assertTrue(0 <= left <= index and 0 <= right <= index)
        test.assertTrue(0 <= nxt <= count)
        if kind == 39:
            test.assertIn(flags, (0, 1))
        else:
            test.assertEqual(flags, 0)
        if flags:
            test.assertTrue(offset + span < annotation < length)
            test.assertTrue(3 <= annotation_span <= length - annotation)
            test.assertEqual(source[annotation:annotation + 2], b"->")
            test.assertEqual(source[annotation + annotation_span - 1:annotation + annotation_span], b"!")
        else:
            test.assertEqual((annotation, annotation_span), (0, 0))
        if kind == 54:
            test.assertIn(source[offset:offset + span], (b"!", b"not"))
            test.assertTrue(left > 0)
            test.assertEqual((right, nxt), (0, 0))
        records.append((kind, flags, offset, span, left, right, nxt, annotation, annotation_span))
    pending, seen = [root], set()
    while pending:
        node_id = pending.pop()
        test.assertTrue(1 <= node_id <= count and node_id not in seen)
        seen.add(node_id)
        pending.extend(child for child in records[node_id - 1][4:7] if child)
    test.assertEqual(len(seen), count)
    statements = [i for i, node in enumerate(records, 1) if node[0] in STATEMENTS]
    links = dict(zip(statements, statements[1:] + [0]))
    for index, node in enumerate(records, 1):
        test.assertEqual(node[6], links.get(index, 0))
    return dict(version=version, profile=actual_profile, tokens=tokens, root=root), records


class NeverFrontendTests(unittest.TestCase):
    def parse(self, source, *, profile=False):
        result = invoke(source, profile=profile)
        self.assertEqual((result.returncode, result.stderr), (0, b""), result.stderr)
        header, records = decode13(self, result.stdout, source, profile)
        return header, records, result.stdout

    def reject(self, source, *, profile=False, code=None, offset=None):
        result = invoke(source, profile=profile)
        self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
        self.assertRegex(result.stderr,
                         rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0[PS]-\d{3}\]: .+; .+\n$")
        if code is not None:
            diagnostic = code if isinstance(code, str) else f"C0P-{code:03}"
            self.assertIn(f"[{diagnostic}]".encode(), result.stderr)
        if offset is not None:
            line = source[:offset].count(b"\n") + 1
            column = offset - source.rfind(b"\n", 0, offset)
            self.assertTrue(result.stderr.startswith(f"input:{line}:{column}: ".encode()), result.stderr)

    def expression_tree(self, source, records):
        trees = {}
        binary = {15: "+", 16: "*", 17: "-", 18: "/", 20: "<", 21: "<=",
                  22: ">", 23: ">=", 24: "==", 25: "!=", 48: "&", 49: "^",
                  50: "|", 52: "and", 53: "or", 55: "<<", 56: ">>", 57: "%"}
        unary = {47: "-", 51: "~", 54: "not"}
        for index, node in enumerate(records, 1):
            kind, _, offset, span, left, right = node[:6]
            if kind in (4, 5):
                trees[index] = ("id" if kind == 4 else "int", source[offset:offset + span])
            elif kind in binary:
                trees[index] = (binary[kind], trees[left], trees[right])
            elif kind in unary:
                trees[index] = (unary[kind], trees[left])
            elif kind == 32:
                return trees[left]
        self.fail("fixture lacks its return expression")

    def test_bang_and_never_signature_wire(self):
        source = b"fn spin()->!{spin()} fn main(){return !0}"
        for profile in (False, True):
            with self.subTest(profile=profile):
                header, records, _ = self.parse(source, profile=profile)
                self.assertEqual(header["root"], 10)
                functions = [node for node in records if node[0] == 39]
                self.assertEqual(functions, [
                    (39, 1, 3, 4, 0, 0, 3, 9, 3),
                    (39, 0, 24, 4, 0, 0, 8, 0, 0)])
                self.assertEqual([node for node in records if node[0] == 54],
                                 [(54, 0, 38, 1, 6, 0, 0, 0, 0)])

    def test_prefix_precedence_and_right_associative_chains(self):
        zero, one, two, three = [("int", str(value).encode()) for value in range(4)]
        cases = [
            (b"!0", ("not", zero)),
            (b"!!2", ("not", ("not", two))),
            (b"!2==1", ("==", ("not", two), one)),
            (b"!(2==1)", ("not", ("==", two, one))),
            (b"!-~2", ("not", ("-", ("~", two)))),
            (b"-!not !0", ("-", ("not", ("not", ("not", zero))))),
            (b"!0 or 2 and 3", ("or", ("not", zero), ("and", two, three))),
            (b"1!=!2", ("!=", one, ("not", two))),
            (b"!0<<1+2", ("<<", ("not", zero), ("+", one, two))),
            (b"!0+1*2%3", ("+", ("not", zero), ("%", ("*", one, two), three))),
        ]
        for expression, expected in cases:
            for profile in (False, True):
                with self.subTest(expression=expression, profile=profile):
                    source = b"fn main(){return " + expression + b"}"
                    _, records, _ = self.parse(source, profile=profile)
                    self.assertEqual(self.expression_tree(source, records), expected)

    def test_bang_token_boundaries(self):
        source = b"fn main(){return !!0!=!1}"
        for profile in (False, True):
            _, records, _ = self.parse(source, profile=profile)
            self.assertEqual([source[n[2]:n[2] + n[3]] for n in records if n[0] == 25], [b"!="])
            self.assertEqual([n[3] for n in records if n[0] == 54], [1, 1, 1])
        for expression in (b"!", b"0!", b"0!!", b"! =0", b"!=0", b"!>0", b"!()",
                           b"f!(0)", b"0->!", b"!0 !1"):
            for profile in (False, True):
                with self.subTest(expression=expression, profile=profile):
                    self.reject(b"fn main(){return " + expression + b"}", profile=profile)

    def test_signature_legal_trivia_and_six_parameters(self):
        for trivia in (b"", b" ", b"\t", b"\n", b"\r\n", b" # ! -> fake\n", b"// ! -> fake\n"):
            annotation = b"->" + trivia + b"!"
            source = (b"fn halt(a,b,c,d,e,f)" + trivia + annotation + trivia +
                      b"{halt(a,b,c,d,e,f)} fn Never(){return 7} fn main(){halt(0,1,2,3,4,5)}")
            for profile in (False, True):
                with self.subTest(trivia=trivia, profile=profile):
                    _, records, _ = self.parse(source, profile=profile)
                    functions = [node for node in records if node[0] == 39]
                    self.assertEqual([node[1] for node in functions], [1, 0, 0])
                    self.assertEqual(functions[0][7:], (len(b"fn halt(a,b,c,d,e,f)") + len(trivia), len(annotation)))
                    self.assertEqual(sum(node[0] == 40 for node in records), 6)

    def test_bad_return_annotations(self):
        prefix = b"fn main()"
        cases = [
            (b"->{return 0}", 2), (b"-> not {return 0}", 3),
            (b"-> Never {return 0}", 3), (b"-> i64 {return 0}", 3),
            (b"- > ! {return 0}", 0), (b"! {return 0}", 0),
            (b"->!!{return 0}", 3), (b"->!={return 0}", 2),
            (b"->! ->!{return 0}", 4), (b"->!0{return 0}", 3),
            (b"->", 2), (b"->!", 3), (b"-> # ! is only comment", 22),
        ]
        for suffix, relative in cases:
            for profile in (False, True):
                with self.subTest(suffix=suffix, profile=profile):
                    source = prefix + suffix
                    offset = len(source) if suffix == b"-> # ! is only comment" else len(prefix) + relative
                    self.reject(source, profile=profile, code=16, offset=offset)

    def test_annotation_only_in_result_position_and_no_new_statements(self):
        for source in (b"fn main(x->!){return 0}", b"fn main(){let x->!=0 return x}",
                       b"fn main(){return 0->!}", b"->! fn main(){return 0}",
                       b"fn main()->!{break}", b"fn main()->!{continue}"):
            for profile in (False, True):
                with self.subTest(source=source, profile=profile):
                    self.reject(source, profile=profile)
        source = b"fn Never(){return 7} fn break(){return Never()} fn main()->!{break()}"
        for profile in (False, True):
            _, records, _ = self.parse(source, profile=profile)
            self.assertEqual([n[1] for n in records if n[0] == 39], [0, 0, 1])

    def test_comment_and_string_markers_are_opaque(self):
        for source, version in (
                (b"fn main(){# fn fake()->! !!\nreturn 0}", (1, 5)),
                (b'fn main(){let text="fn fake()->! !! !=" return 0}', (12, 12))):
            for profile in (False, True):
                result = invoke(source, profile=profile)
                self.assertEqual((result.returncode, result.stderr), (0, b""))
                self.assertEqual(result.stdout[4], version[int(profile)])
        source = (b'fn ordinary() # ->! fn fake()\n{let text="fn fake()->! { }" return !0}'
                  b' fn bottom()-> # bogus ! { -> }\n !{bottom()} fn main(){bottom()}')
        for profile in (False, True):
            _, records, _ = self.parse(source, profile=profile)
            functions = [node for node in records if node[0] == 39]
            self.assertEqual([source[n[2]:n[2] + n[3]] for n in functions], [b"ordinary", b"bottom", b"main"])
            self.assertEqual([node[1] for node in functions], [0, 1, 0])
            self.assertEqual(functions[1][7:], (source.index(b"-> # bogus"), len(b"-> # bogus ! { -> }\n !")))

    def test_frontend_defers_new_return_semantics_to_backend(self):
        # Deliberately false bottom/fallthrough contracts must reach the backend;
        # a frontend AST is syntax evidence and must not claim semantic proof.
        for source in (b"fn main()->!{}", b"fn main()->!{return 0}",
                       b"fn main(){if !0{return 1}}", b"fn main(){let x=!0}",
                       b"fn halt()->!{halt()} fn main(){halt()}",
                       b"fn main()->!{return missing}"):
            for profile in (False, True):
                with self.subTest(source=source, profile=profile):
                    self.parse(source, profile=profile)

    def test_old_return_gate_remains(self):
        for source in (b"fn main(){}", b"fn main(){while 1{}}", b"fn main(){if not 0{return 1}}",
                       b'fn main(){let text="! -> !"}'):
            for profile in (False, True):
                with self.subTest(source=source, profile=profile):
                    self.reject(source, profile=profile, code=4, offset=len(source) - 1)

    def test_new_syntax_keeps_native_permission_and_arity_checks(self):
        for source, code in (
                (b"fn main(){return !syscall6(39)}", "C0S-001"),
                (b"fn main()->!{syscall6(60,0)}", "C0S-001"),
                (b"fn main(){unsafe {return !0}}", 14),
                (b"fn halt(a,b,c,d,e,f,g)->!{} fn main(){return !0}", 12),
                (b"fn main(){return !f(0,1,2,3,4,5,6)}", 12)):
            for profile in (False, True):
                with self.subTest(source=source, profile=profile):
                    self.reject(source, profile=profile, code=code)
        source = b"fn main()->!{unsafe {# safety: exact caller-owned scope\nsyscall6(60,0)}}"
        for profile in (False, True):
            self.parse(source, profile=profile)

    def test_wide_annotation_spans_names_and_current_function_id(self):
        preceding = b" ".join(b"fn f%d(){return 0}" % number for number in range(260))
        name, trivia = b"N" * 65536, b" " * 66000
        annotation = b"->" + trivia + b"!"
        source = preceding + b" fn " + name + b"()" + annotation + b"{while 1{}} fn main(){return !0}"
        for profile in (False, True):
            _, records, _ = self.parse(source, profile=profile)
            annotated = [(index, n) for index, n in enumerate(records, 1) if n[0] == 39 and n[1]]
            self.assertEqual(len(annotated), 1)
            index, node = annotated[0]
            self.assertGreater(index, 255)
            self.assertEqual(node[3], 65536)
            self.assertEqual(node[7:], (len(preceding) + 4 + len(name) + 2, 66003))
            self.assertGreater(node[7], 65535)

    def test_source_token_and_block_bounds_in_both_profiles(self):
        source = b"fn main()->!{while 1{}}".ljust(262144, b" ")
        token_source = b"fn main(){return !!0" + b"+0" * 32763 + b"}"
        for profile in (False, True):
            self.parse(source, profile=profile)
            self.reject(source + b" ", profile=profile, code=2, offset=262144)
            header, _, _ = self.parse(token_source, profile=profile)
            self.assertEqual(header["tokens"], 65536)
            overflow = token_source[:-1] + b";}"
            self.reject(overflow, profile=profile, code=3, offset=len(overflow) - 1)
            self.parse(b"fn main()->!{" + b"while 1{" * 64 + b"}" * 65, profile=profile)
            self.reject(b"fn main()->!{" + b"while 1{" * 65 + b"}" * 66, profile=profile, code=11)

    def test_bounded_truncations_and_deterministic_mutations(self):
        source = b'fn halt()->!{halt()} fn main(){let s="!= -> !" return !!0}'
        generator = random.Random(0xB013)
        mutations = [source[:index] for index in range(len(source))]
        for _ in range(32):
            index = generator.randrange(len(source))
            mutations.append(source[:index] + bytes([generator.choice(b"!-=>(){}# \n0N\x00")]) + source[index + 1:])
        for profile in (False, True):
            for mutated in mutations:
                with self.subTest(source=mutated, profile=profile):
                    result = invoke(mutated, profile=profile, timeout=5)
                    self.assertIn(result.returncode, (0, 1), result.stderr)
                    if result.returncode:
                        self.assertEqual(result.stdout, b"")
                        self.assertRegex(result.stderr, rb"^input:\d+:\d+: error\[C0P-\d{3}\]: .+; .+\n$")
                    else:
                        self.assertEqual(result.stderr, b"")
                        decode13(self, result.stdout, mutated, profile)

    def test_frozen_source1_through12_output_byte_parity(self):
        versions = set()
        for source, expected_versions, expected_hashes in OLD_BYTES:
            for profile in (False, True):
                with self.subTest(source=source[:80], profile=profile):
                    result = invoke(source, profile=profile)
                    self.assertEqual((result.returncode, result.stderr), (0, b""), result.stderr)
                    self.assertEqual(result.stdout[4], expected_versions[int(profile)])
                    self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), expected_hashes[int(profile)])
                    versions.add(result.stdout[4])
        self.assertEqual(versions, set(range(1, 13)))


if __name__ == "__main__":
    unittest.main()
