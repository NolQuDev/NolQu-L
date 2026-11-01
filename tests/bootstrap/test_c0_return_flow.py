"""C0.33 structural return proof, independently checked source and NQAF."""
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest

from c031_support import (ROOT, assert_owned_graph, candidate_binary, decode_nqaf,
                         encode_profile_source, run_native)

STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
LEGACY = (
    b'fn main(){return 7}',
    b'fn main(){if 1{return 7}else{return 9} return 0}',
    b'fn main(){let x=2 if x {x=x+1} else {x=9} return x}',
    b'fn main(){let n=3 while n {if n==1{return 7} n=n-1} return 0}',
    b'fn f(x){if x{return 7}else{return 9} return 0} fn main(){return f(1)+f(0)}',
    b'fn main(){if 1{return 7}else{return 9} let dead=3 return dead}',
    b'fn main(){byte_store(0,65) output_write(0,1) return byte_load(0)}',
    b'fn main(){unsafe {# safety: local bounded arena\n byte_store(0,7)} return byte_load(0)}',
    b'#' + b'x' * 8200 + b'\nfn main(){if 1{return 7}else{return 9} return 0}',
)
LEGACY_AST_SHA256 = 'cd60fc7cb986c314af872c5acb095e44e80f180b99e1947057eb919311bd979e'
LEGACY_ELF_SHA256 = 'f57d6087139ab4b8d1fab5637270044dea60e6dc2b373232c6c936b4eb8fe53a'


def without_terminal_return(wire):
    """Remove the final literal `return 0` subtree, preserving valid ownership."""
    header, nodes = decode_nqaf(wire)
    anchor = header['source'].rfind(b'return 0')
    ret = next(i for i, n in enumerate(nodes, 1) if n[0] == 32 and n[2] == anchor)
    expression = nodes[ret - 1][4]
    if nodes[expression - 1][0] != 5:
        raise ValueError('fixture needs a leaf literal return')
    removed = {expression, ret}
    mapping = {old: new for new, old in enumerate((i for i in range(1, len(nodes) + 1)
                                                 if i not in removed), 1)}
    size = 32 if header['version'] >= 5 else 16
    output = bytearray(wire[:size + header['source_length']])
    if size == 16:
        struct.pack_into('<HH', output, 10, len(mapping), len(mapping))
    else:
        struct.pack_into('<II', output, 12, len(mapping), len(mapping))
    for old, record in enumerate(nodes, 1):
        if old in removed:
            continue
        kind, flags, offset, span, left, right, nxt = record
        while nxt in removed:
            nxt = nodes[nxt - 1][6]
        left, right, nxt = (mapping.get(i, 0) for i in (left, right, nxt))
        if size == 16:
            output.extend(struct.pack('<BBHHHHH4s', kind, flags, offset, span,
                                      left, right, nxt, bytes(4)))
        else:
            output.extend(struct.pack('<BBHIIIIIII', kind, flags, 0, offset, span,
                                      left, right, nxt, 0, 0))
    result = bytes(output)
    parsed, records = decode_nqaf(result)
    assert_owned_graph(parsed, records)
    return result


class ReturnFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE / 'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE / 'c0-backend.seed')

    def ast(self, source, profile=False):
        result = run_native(self.frontend, encode_profile_source(source) if profile else source)
        self.assertEqual((result.returncode, result.stderr), (0, b''), source[:200])
        header, records = decode_nqaf(result.stdout)
        assert_owned_graph(header, records)
        return result.stdout

    def artifact(self, wire):
        result = run_native(self.backend, wire)
        self.assertEqual((result.returncode, result.stderr), (0, b''))
        self.assertEqual(result.stdout[:4], b'\x7fELF')
        return result.stdout

    def value(self, source, expected, profile=False):
        image = self.artifact(self.ast(source, profile))
        with tempfile.TemporaryDirectory(prefix='c033-return-') as directory:
            program = Path(directory) / 'program'
            program.write_bytes(image)
            program.chmod(0o700)
            result = run_native(program)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (expected & 255, b'', b''))

    def reject_source(self, source, code=4):
        result = run_native(self.frontend, source)
        self.assertEqual((result.returncode, result.stdout), (1, b''), source[:200])
        self.assertRegex(result.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0P-\d{3}\]: .+; .+\n$')
        self.assertIn(f'[C0P-{code:03}]'.encode(), result.stderr)

    def reject_wire(self, wire):
        result = run_native(self.backend, wire)
        self.assertEqual((result.returncode, result.stdout), (1, b''))
        self.assertRegex(result.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-002\]: .+; .+\n$')

    def test_exhaustive_branches_and_recursive_calls(self):
        self.value(b'fn main(){if 1{return 7}else{return 9}}', 7)
        self.value(b'fn choose(x){if x{return 7}else{return 9}} '
                   b'fn main(){return choose(1)*10+choose(0)}', 79)
        self.value(b'fn f(x,y){if x{if y{return 2}else{return 3}}else{return 4}} '
                   b'fn main(){return f(1,1)*10+f(1,0)+f(0,0)}', 27)
        self.value(b'fn sum(n){if n==0{return 0}else{return n+sum(n-1)}} '
                   b'fn main(){return sum(10)}', 55)

    def test_backend_independently_accepts_exhaustive_wire(self):
        for source in (b'fn main(){if 0{return 7}else{return 9} return 0}',
                       b'fn choose(x){if x{return 7}else{return 9} return 0} '
                       b'fn main(){return choose(1)}'):
            with self.subTest(source=source):
                # The rewritten stream is valid under C0.33 without a producer flag.
                self.artifact(without_terminal_return(self.ast(source)))

    def test_missing_paths_and_loops_remain_rejected(self):
        for body in (b'', b'if 1{return 7}', b'if 1{return 7}else{}',
                     b'if 1{}else{return 7}', b'while 1{return 7}',
                     b'if 1{while 1{return 7}}else{return 9}',
                     b'if 0{}else{if 1{return 7}else{return 9}}'):
            with self.subTest(body=body):
                self.reject_source(b'fn main(){' + body + b'}')
        self.reject_source(b'fn main(){return 1 let x=2}', code=9)

    def test_backend_rejects_incomplete_rewritten_wire_and_stale_functions(self):
        for source in (
                b'fn main(){if 1{return 7} return 0}',
                b'fn main(){if 1{return 7}else{} return 0}',
                b'fn main(){if 1{}else{return 7} return 0}',
                b'fn main(){while 1{return 7} return 0}',
                b'fn f(){return 7} fn main(){if 1{return 9} return 0}',
                b'fn f(){if 1{return 7}else{return 9} return 0} '
                b'fn main(){while 1{return 3} return 0}'):
            with self.subTest(source=source):
                self.reject_wire(without_terminal_return(self.ast(source)))

    def test_unreachable_checks_and_legacy_bytes(self):
        asts = [self.ast(source) for source in LEGACY]
        images = [self.artifact(wire) for wire in asts]
        self.assertEqual(hashlib.sha256(b''.join(asts)).hexdigest(), LEGACY_AST_SHA256)
        self.assertEqual(hashlib.sha256(b''.join(images)).hexdigest(), LEGACY_ELF_SHA256)
        result = run_native(self.backend, self.ast(
            b'fn main(){if 1{return 7}else{return 9} return missing}'))
        self.assertEqual((result.returncode, result.stdout), (1, b''))
        self.assertIn(b'[C0B-003]', result.stderr)
        self.reject_source(b'fn main(){unsafe {if 1{return 7}else{return 9}}}', code=14)

    def test_missing_return_diagnostic_explains_the_proof(self):
        source = b'fn main(){if 1{return 7}}'
        result = run_native(self.frontend, source)
        self.assertEqual((result.returncode, result.stdout), (1, b''))
        self.assertEqual(result.stderr,
                         f'input:1:{len(source)}: error[C0P-004]: invalid syntax; expected fn name(parameters) with a return on every path\n'.encode())

    def test_scope_joins_and_runtime_effects(self):
        self.value(b'fn main(){unsafe {# safety: lexical return only\n'
                   b'if 1{return 7}else{return 9}}}', 7)
        self.value(b'fn f(x){if x{unsafe {# safety: lexical return only\n'
                   b'return 7}}else{return 9}} fn main(){return f(1)+f(0)}', 16)
        self.value(b'fn main(){if 1{return 7}else{return 9} while 0{return 3}}', 7)
        self.value(b'fn f(x){if x{byte_store(1,byte_load(1)+1) return 7}'
                   b'else{byte_store(1,byte_load(1)+2) return 9}} '
                   b'fn main(){let n=f(1)+f(0) return byte_load(1)*10+n}', 46)

    def test_depth_wide_spans_and_both_profiles(self):
        body = b'return 7'
        for _ in range(64):
            body = b'if 1{' + body + b'}else{return 9}'
        source = b'fn main(){' + body + b'}'
        self.value(source, 7)
        self.reject_source(b'fn main(){if 1{' + body + b'}else{return 9}}', code=11)
        source = b'#' + b'x' * 8200 + b'\nfn main(){if 0{return 7}else{return 9}}'
        for profile in (False, True):
            with self.subTest(profile=profile):
                wire = self.ast(source, profile)
                self.assertEqual(decode_nqaf(wire)[0]['version'], 5)
                self.value(source, 9, profile)

    def test_generation_return_flow_contract(self):
        # Included in both actual B/C named oracle runs: no selected-A shortcut.
        self.value(b'fn f(x){if x{return 7}else{return 9}} '
                   b'fn main(){return f(1)*10+f(0)}', 79)
        self.value(b'fn main(){unsafe {# safety: lexical return only\n'
                   b'if 0{return 7}else{return 9}}}', 9, profile=True)
        self.reject_source(b'fn main(){while 1{return 7}}')
        self.reject_wire(without_terminal_return(self.ast(
            b'fn f(){return 7} fn main(){if 1{return 9} return 0}')))


if __name__ == '__main__':
    unittest.main()
