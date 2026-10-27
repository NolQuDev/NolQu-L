"""Source/ownership oracle for the canonical experimental native frontend.

These tests run a real C0_FRONTEND executable. Removing contextual scopes,
checking permission by expression position, ignoring forward user shadows, or
promoting mere identifier text must change observable AST/error output.
"""

from pathlib import Path
import unittest
import tempfile

from c031_support import (assert_owned_graph, candidate_binary, decode_nqaf,
                         encode_profile_source, run_native)

from c032_support import build_c031_predecessors

ROOT = Path(__file__).resolve().parents[2]
INSTALLED = ROOT / 'bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed'
STATEMENTS = {30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41, 44, 45, 46}
NATIVE_NAMES = (b'arg_count', b'arg_copy', b'byte_address', b'syscall6')


class NativeFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', INSTALLED)
        baseline = tempfile.TemporaryDirectory(prefix='c032-fe-baseline-')
        cls.addClassCleanup(baseline.cleanup)
        cls.predecessor = build_c031_predecessors(Path(baseline.name) / 'old')['frontend']

    def parse(self, source, *, profile=False, version=6):
        payload = encode_profile_source(source) if profile else source
        result = run_native(self.frontend, payload, timeout=120)
        self.assertEqual((result.returncode, result.stderr), (0, b''), source[:200])
        header, nodes = decode_nqaf(result.stdout)
        self.assertEqual(header['source'], source)
        self.assertEqual(header['version'], version)
        self.assertEqual(header['runtime_profile'], int(profile))
        if version == 6:
            self.assertEqual(header['dialect'], 5)
            self.assertEqual(result.stdout[5:8], b'\x20\0\0')
        assert_owned_graph(header, nodes)
        statements = [i for i, n in enumerate(nodes, 1) if n[0] in STATEMENTS]
        links = dict(zip(statements, statements[1:] + [0]))
        for i, node in enumerate(nodes, 1):
            self.assertLess(node[4], i)
            self.assertLess(node[5], i)
            self.assertEqual(node[6], links.get(i, 0))
            if node[0] in (45, 46):
                self.assertEqual((node[1], node[4], node[5]), (0, 0, 0))
        self.assertEqual((nodes[-1][0], nodes[-1][4], nodes[-1][5:]),
                         (33, statements[0], (0, 0)))
        return header, nodes, result.stdout

    def reject(self, source, code, offset, *, profile=False):
        payload = encode_profile_source(source) if profile else source
        result = run_native(self.frontend, payload, timeout=120)
        self.assertEqual((result.returncode, result.stdout), (1, b''), source[:200])
        line = source[:offset].count(b'\n') + 1
        column = offset - source.rfind(b'\n', 0, offset)
        self.assertTrue(result.stderr.startswith(
            f'input:{line}:{column}: error[{code}]: '.encode()), result.stderr)
        self.assertRegex(result.stderr, rb': .+; .+\n$')
        return result

    @staticmethod
    def anchor(source, node):
        return source[node[2]:node[2] + node[3]]

    def test_unsafe_scope_and_header(self):
        # Includes the unsafe-only/no-call case: /6 always uses function envelopes.
        for header in (b'# safety: caller owns these effects\n',
                       b'// safety: caller owns these effects\n',
                       b' \t\r\n\n# \tsafety:\r\n// frame and spans are valid\r\n\t',
                       b'//\tsafety: /// #\n# caller owns the descriptor\n',
                       b'# safety: braces } { are comment text\n'):
            for body in (b'', b'let x=1 ', b'syscall6(39,0) '):
                with self.subTest(header=header, body=body):
                    source = b'fn main(){unsafe {\n' + header + body + b'} return 0}'
                    _, nodes, _ = self.parse(source)
                    open_node = next(n for n in nodes if n[0] == 45)
                    close_node = next(n for n in nodes if n[0] == 46)
                    begin = source.index(b'unsafe')
                    end = begin + len(b'unsafe {\n') + len(header)
                    self.assertEqual((open_node[2], open_node[3]), (begin, end - begin))
                    self.assertEqual((close_node[2], close_node[3]),
                                     (end + len(body), 1))
                    self.assertEqual(self.anchor(source, close_node), b'}')
                    self.assertEqual([n[0] for n in nodes if n[0] in (39, 41)], [39, 41])
        # A control condition may end in the ordinary identifier unsafe; its
        # body can still contain a real unsafe-only scope with no call syntax.
        for condition in (b'if unsafe', b'if 0+unsafe',
                          b'while unsafe', b'while 0+unsafe'):
            source = (b'fn main(){let unsafe=0 ' + condition +
                      b' {unsafe {# safety: caller owns these effects\n}} return 0}')
            for profile in (False, True):
                with self.subTest(condition=condition, profile=profile):
                    _, nodes, _ = self.parse(source, profile=profile)
                    self.assertEqual(sum(n[0] == 45 for n in nodes), 1)
                    self.assertEqual(sum(n[0] == 46 for n in nodes), 1)
                    self.assertEqual([n[0] for n in nodes if n[0] in (39, 41)], [39, 41])
        # The anchor includes comments and whitespace through the first body token.
        source = (b'fn main(){unsafe /*bad*/ {# safety: owns effects\n} return 0}')
        result = run_native(self.frontend, source)
        self.assertEqual((result.returncode, result.stdout), (1, b''))

    def test_native_transport_and_shadows(self):
        cases = [(b'arg_count()', b'arg_count', 0),
                 (b'arg_copy(1,2,3)', b'arg_copy', 3),
                 (b'byte_address(0,1)', b'byte_address', 2),
                 (b'syscall6(39,0)', b'syscall6', 2)]
        for expression, name, arity in cases:
            raw = name in (b'byte_address', b'syscall6')
            source = (b'fn main(){unsafe {# safety: owns frame and spans\nlet x=' +
                      expression + b'} return 0}' if raw else
                      b'fn main(){return ' + expression + b'}')
            for profile in (False, True):
                with self.subTest(name=name, profile=profile):
                    _, nodes, wire = self.parse(source, profile=profile)
                    call = next(n for n in nodes if n[0] == 42 and self.anchor(source, n) == name)
                    prefix, actual = call[4], 0
                    while prefix:
                        self.assertEqual(nodes[prefix - 1][0], 43)
                        actual += 1
                        prefix = nodes[prefix - 1][4]
                    self.assertEqual(actual, arity)
                    # The test decoder keeps wide reserved fields/profile/dialect strict.
                    for offset, value in ((4, 7), (5, 16), (6, 1), (24, 4), (24, 6),
                                          (25, 2), (26, 1), (28, 1),
                                          (32 + len(source) + 1, 1),
                                          (32 + len(source) + 2, 1),
                                          (32 + len(source) + 24, 1),
                                          (32 + len(source) + 28, 1)):
                        mutated = bytearray(wire)
                        mutated[offset] = value
                        with self.assertRaises(ValueError):
                            decode_nqaf(mutated)
                    mutated = bytearray(wire)
                    mutated[4] = 5  # /5 must continue to reject dialect5.
                    with self.assertRaises(ValueError):
                        decode_nqaf(mutated)
        for name in NATIVE_NAMES:
            # Forward, wrong-arity definitions win globally; FE leaves arity to BE.
            source = b'fn main(){return ' + name + b'()} fn ' + name + b'(a){return a}'
            for profile in (False, True):
                with self.subTest(shadow=name, profile=profile):
                    h, _, _ = self.parse(source, profile=profile, version=5 if profile else 3)
                    self.assertEqual(h['dialect'], 3)
            source = (b'fn main(){unsafe {# safety: owns effects\n' + name +
                      b'()} return ' + name + b'()} fn ' + name + b'(a){return a}')
            self.parse(source)  # explicit scope selects /6, shadow remains permitted outside
        # Local names are a separate namespace and cannot grant raw permission.
        source = b'fn main(){let syscall6=0 return syscall6(39,0)}'
        self.reject(source, 'C0S-001', source.index(b'syscall6(39'))
        # Exact match only, including high function IDs and long prefix names.
        pad = b'x=0 ' * 300
        source = (b'fn main(){' + pad + b'return syscall6()} fn syscall6(a){return a}')
        h, nodes, _ = self.parse(source, version=5)
        self.assertEqual(h['dialect'], 3)
        self.assertGreater(next(i for i, n in enumerate(nodes, 1)
                                if n[0] == 39 and self.anchor(source, n) == b'syscall6'), 512)
        for suffix in (b'_extra', b'x', b'_' * 257):
            source = b'fn syscall6' + suffix + b'(){return 0} fn main(){return syscall6(39,0)}'
            self.reject(source, 'C0S-001', source.index(b'syscall6(39'))

    def test_raw_calls_need_owning_unsafe_scope(self):
        for expression in (b'syscall6(39,0)', b'byte_address(0,1)',
                           b'f(syscall6(39,0))', b'1+byte_address(0,1)',
                           b'f(0,syscall6(39,byte_address(0,48)))'):
            source = b'fn main(){return ' + expression + b'}'
            offset = min((source.find(name + b'(') for name in (b'syscall6', b'byte_address')
                          if name + b'(' in source))
            self.reject(source, 'C0S-001', offset)
        for source in (
                b'fn main(){unsafe {# safety: owns effects\nsyscall6(39,0)} return byte_address(0,1)}',
                b'fn main(){unsafe {# safety: owns effects\n} return syscall6(39,0)}',
                b'fn f(){unsafe {# safety: owns effects\nsyscall6(39,0)} return 0} fn main(){return syscall6(39,0)}',
                b'fn main(){if syscall6(39,0){unsafe {# safety: owns effects\n}} return 0}',
                b'fn main(){while byte_address(0,1){unsafe {# safety: owns effects\n}} return 0}'):
            with self.subTest(source=source):
                name = b'byte_address' if b'byte_address' in source else b'syscall6'
                self.reject(source, 'C0S-001', source.rindex(name + b'('))
        source = (b'fn main(){unsafe {# safety: owns effects\n'
                  b'if syscall6(39,0){while byte_address(0,1){f(syscall6(39,0))}}'
                  b'} return arg_count()}')
        self.parse(source)

    def test_nested_scope_limits(self):
        for opening, closing in ((b'unsafe {# safety: owns effects\n', b'}'),
                                 (b'if 1{unsafe {# safety: owns effects\n', b'}}'),
                                 (b'while 0{unsafe {# safety: owns effects\n', b'}}')):
            depth = 64 if closing == b'}' else 32
            source = b'fn main(){' + opening * depth + closing * depth + b'return 0}'
            _, nodes, _ = self.parse(source)
            self.assertEqual(sum(n[0] == 45 for n in nodes), depth)
            extra = b'unsafe {# safety: owns effects\n'
            source = b'fn main(){' + opening * depth + extra + b'}' + closing * depth + b'return 0}'
            self.reject(source, 'C0P-011', len(b'fn main(){') + len(opening) * depth)
        source = (b'fn f(){unsafe {# safety: owns effects\nreturn 1} return 0}'
                  b'fn main(){unsafe {# safety: owns effects\nlet x=f()} return 0}')
        self.parse(source)

    def test_legacy_output_unchanged(self):
        condition_sources = [
            b'fn main(){let unsafe=1 if unsafe {return 1} return 0}',
            b'fn main(){let unsafe=0 while unsafe {unsafe=1} return unsafe}',
            b'fn main(){let unsafe=1 if 0+unsafe {return 1} return 0}',
            b'fn main(){let unsafe=0 while 0+unsafe {unsafe=1} return unsafe}',
        ]
        sources = [b'fn main(){return 7}',
                   b'fn main(){let unsafe=1 unsafe=unsafe+1 return unsafe}',
                   b'fn unsafe(x){return x} fn main(){return unsafe(7)}',
                   b'fn main(){let arg_count=3 return arg_count}',
                   b'fn arg_count(){return 1} fn main(){return 0}',
                   b'fn main(){let i=0 while i<2{if i==1{i=i+1}else{i=i+2}} return i}',
                   b'fn main(){byte_store(0,65) output_write(0,1) return byte_load(0)}',
                   b'# unsafe { syscall6 arg_count arg_copy byte_address\nfn main(){return 0}',
                   b'fn main(){return 0}'.ljust(8193, b' ')]
        sources += condition_sources
        sources += [b'fn main(){return ' + name + b'()} fn ' + name + b'(a){return a}'
                    for name in NATIVE_NAMES]
        for source in sources:
            for profile in (False, True):
                with self.subTest(source=source[:80], profile=profile):
                    payload = encode_profile_source(source) if profile else source
                    old = run_native(self.predecessor, payload, timeout=120)
                    new = run_native(self.frontend, payload, timeout=120)
                    self.assertEqual((old.returncode, old.stderr), (0, b''))
                    if source in condition_sources:
                        # Keep this regression independent of later installed
                        # seed promotion as well as comparing complete bytes.
                        self.assertEqual((new.returncode, new.stderr), (0, b''))
                        header, nodes = decode_nqaf(new.stdout)
                        self.assertEqual((header['version'], header['dialect']),
                                         (5 if profile else 2, 2))
                        self.assertFalse(any(n[0] in (39, 40, 41, 45, 46) for n in nodes))
                    self.assertEqual((new.returncode, new.stdout, new.stderr),
                                     (old.returncode, old.stdout, old.stderr))

    def test_frontend_errors_and_offsets(self):
        for header in (b'', b'\n\n', b'# unrelated\n# safety: owns effects\n',
                       b'# Safety: owns effects\n', b'# safety\n', b'# safety : owns effects\n',
                       b'# safety:\n', b'// safety: \t\r\n// ## /// \t\n',
                       b'# safety:\t\n', b'// safety:###///\n'):
            source = b'fn main(){\nunsafe {' + header + b'} return 0}'
            for profile in (False, True):
                with self.subTest(header=header, profile=profile):
                    self.reject(source, 'C0P-014', source.index(b'unsafe'), profile=profile)
        for source in (b'fn main(){unsafe {# safety: owns effects\nreturn 0}}',
                       b'fn main(){unsafe {# safety: owns effects\n} }',
                       b'fn main(){unsafe {# safety: owns effects\nreturn 0} fn f(){return 0}',
                       b'fn main(){unsafe fn f(){return 0} return 0}',
                       b'fn main(){let x=unsafe {# safety: owns effects\n} return 0}',
                       b'fn main(){unsafe {# safety: owns effects\nreturn 0} return 0}}'):
            with self.subTest(malformed=source):
                result = run_native(self.frontend, source)
                self.assertEqual((result.returncode, result.stdout), (1, b''))
                self.assertIn(b'error[C0P-', result.stderr)
        # u32 opener and call offsets survive both source/profile transport forms.
        source = b'\n' * 70000 + b'fn main(){unsafe {# safety:\n} return 0}'
        self.reject(source, 'C0P-014', source.index(b'unsafe'), profile=True)
        source = b' ' * 70000 + b'fn main(){return syscall6(39,0)}'
        self.reject(source, 'C0S-001', source.index(b'syscall6'), profile=True)
        source = b' ' * 70000 + b'fn main(){unsafe {# safety: owns effects\nsyscall6(39,0)} return 0}'
        _, nodes, _ = self.parse(source, profile=True)
        self.assertGreater(next(n[2] for n in nodes if n[0] == 45), 65535)


if __name__ == '__main__':
    unittest.main()
