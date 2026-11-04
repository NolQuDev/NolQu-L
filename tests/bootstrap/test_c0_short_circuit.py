"""C0.36 semantic, independent NQAF/9 and exact x86-64 branch oracles.

The wire fixtures are handwritten graphs, never output from the tested frontend.
The finite value corpus uses Python integers only for truth, not a DSL evaluator.
"""
import hashlib
from pathlib import Path
import random
import struct
import tempfile
import unittest

from c031_support import candidate_binary, run_native, encode_profile_source, decode_nqaf, assert_owned_graph
from test_c0_return_flow import LEGACY, LEGACY_AST_SHA256, LEGACY_ELF_SHA256
from test_c0_bitwise import LEGACY_C034, LEGACY_C034_AST, LEGACY_C034_ELF

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
MIN, MAX = -(1 << 63), (1 << 63) - 1
# Frozen with absolute ROOT C0.35 seeds, before C0.36 seed promotion; profile outermost.
LEGACY_C035 = (
    b'fn main(){return 6&3}', b'fn main(){return 8^3|1}',
    b'fn main(){return ~7}',
    b'fn main(){return (~(-9223372036854775808))==9223372036854775807}',
    b'fn f(a,b){return a^b}fn main(){return f(6,3)&7}',
    b'fn main(){let n=7 while n&1{n=n-1}return ~n}',
    b'fn main(){'+b' '*70000+b'return ~(7|2)}',
)
LEGACY_C035_AST = '9d6528cfcf424c96d26011ac0073766beac8fc7547061c9f1792f19d21a8076f'
LEGACY_C035_ELF = '97d2fd44a3758ac0354a2527d0ee77a3272db080cacf8096891446d4d9fa0671'


def pack_wire(source, records, profile=0, version=9, dialect=8):
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', version, 32, 0, len(source),
                         len(records), len(records), 11, dialect, profile, 0, 0)
    return header + source + b''.join(
        struct.pack('<BBHIIIIIII', k, f, 0, o, n, l, r, x, 0, 0)
        for k, f, o, n, l, r, x in records)


def independent_wire(operator=b'and', profile=0, lhs=b'6', rhs=b'3'):
    """Complete function envelope and contiguous postorder, with literal leaves."""
    if operator == b'not':
        source = b'fn main(){return not ' + lhs + b'}'
        records = [(39, 0, 3, 4, 0, 0, 4),
                   (5, 0, 21, len(lhs), 0, 0, 0),
                   (54, 0, 17, 3, 2, 0, 0),
                   (32, 0, 10, 6, 3, 0, 5),
                   (41, 0, len(source)-1, 1, 0, 0, 0),
                   (33, 0, 0, 2, 1, 0, 0)]
    else:
        source = b'fn main(){return ' + lhs + b' ' + operator + b' ' + rhs + b'}'
        anchor = 18 + len(lhs)
        records = [(39, 0, 3, 4, 0, 0, 5),
                   (5, 0, 17, len(lhs), 0, 0, 0),
                   (5, 0, anchor+len(operator)+1, len(rhs), 0, 0, 0),
                   ({b'and': 52, b'or': 53}[operator], 0, anchor, len(operator), 2, 3, 0),
                   (32, 0, 10, 6, 4, 0, 6),
                   (41, 0, len(source)-1, 1, 0, 0, 0),
                   (33, 0, 0, 2, 1, 0, 0)]
    return pack_wire(source, records, profile)


def independent_named_wire(operator=b'and', profile=0):
    """A multi-byte name and differently sized literals exercise wire cursors."""
    name = {b'and': b'andromeda_17', b'or': b'oratorio9', b'not': b'notary_001'}[operator]
    source = b'fn main(){let '+name+b'=4294967296 return '
    start = len(source)
    if operator == b'not':
        source += b'not '+name+b'}'
        records = [(39, 0, 3, 4, 0, 0, 4), (4, 0, 14, len(name), 0, 0, 0),
                   (5, 0, 15+len(name), 10, 0, 0, 0),
                   (30, 0, 10, 3, 2, 3, 7),
                   (4, 0, start+4, len(name), 0, 0, 0),
                   (54, 0, start, 3, 5, 0, 0),
                   (32, 0, start-7, 6, 6, 0, 8),
                   (41, 0, len(source)-1, 1, 0, 0, 0),
                   (33, 0, 0, 2, 1, 0, 0)]
    else:
        source += name+b' '+operator+b' 000000003}'
        anchor = start+len(name)+1
        records = [(39, 0, 3, 4, 0, 0, 4), (4, 0, 14, len(name), 0, 0, 0),
                   (5, 0, 15+len(name), 10, 0, 0, 0),
                   (30, 0, 10, 3, 2, 3, 8),
                   (4, 0, start, len(name), 0, 0, 0),
                   (5, 0, anchor+len(operator)+1, 9, 0, 0, 0),
                   ({b'and': 52, b'or': 53}[operator], 0, anchor, len(operator), 5, 6, 0),
                   (32, 0, start-7, 6, 7, 0, 9),
                   (41, 0, len(source)-1, 1, 0, 0, 0),
                   (33, 0, 0, 2, 1, 0, 0)]
    return pack_wire(source, records, profile)


def decode_wire(wire):
    """Independent /9 reader: an old shared /8 decoder cannot create false RED."""
    if len(wire) < 5 or wire[4] != 9:
        return decode_nqaf(wire)
    if len(wire) < 32:
        raise ValueError('truncated /9 header')
    magic, version, size, flags, length, count, root, tokens, dialect, profile, r16, r32 = \
        struct.unpack_from('<4sBBHIIIIBBHI', wire)
    if (magic, version, size, flags, dialect, r16, r32) != (b'NQAF', 9, 32, 0, 8, 0, 0) \
            or profile not in (0, 1) or not 0 < length <= 262144 \
            or not 0 < count <= 65536 or root != count or not 0 < tokens <= 65536 \
            or len(wire) != 32 + length + count*32:
        raise ValueError('invalid /9 header/extent')
    nodes = []
    for index in range(count):
        kind, node_flags, reserved, offset, span, left, right, nxt, r1, r2 = \
            struct.unpack_from('<BBHIIIIIII', wire, 32+length+index*32)
        if node_flags or reserved or r1 or r2 or offset >= length \
                or not 0 < span <= length-offset or max(left, right, nxt) > count:
            raise ValueError(f'invalid /9 node {index+1}')
        nodes.append((kind, node_flags, offset, span, left, right, nxt))
    header = dict(version=9, source_length=length, node_count=count, root_id=root,
                  token_count=tokens, dialect=8, runtime_profile=profile,
                  source=wire[32:32+length])
    return header, nodes


def change_node(wire, node_id, field, value):
    """Mutate one declared wide field; no production helper repairs the graph."""
    data = bytearray(wire)
    base = 32+struct.unpack_from('<I', wire, 8)[0]+(node_id-1)*32
    if field in (0, 1):
        data[base+field] = value
    else:
        struct.pack_into('<I', data, base+field, value)
    return bytes(data)


def keyword_neighbor(wire, before, character):
    """Keep every declared lexeme valid while making the logical anchor a suffix/prefix."""
    header, nodes = decode_wire(wire)
    operator = next(n for n in nodes if n[0] in (52, 53, 54))
    at = operator[2] if before else operator[2]+operator[3]
    source = header['source'][:at]+character+header['source'][at:]
    shifted = [(k, f, o+int(o >= at), n, l, r, x) for k, f, o, n, l, r, x in nodes]
    return pack_wire(source, shifted, header['runtime_profile'])


def independent_unsafe_rhs(operator=b'and', profile=0):
    """Unsafe intrinsic is statically invalid even though the branch skips it."""
    lhs = b'0' if operator == b'and' else b'1'
    source = b'fn main(){return '+lhs+b' '+operator+b' byte_address(0,0)}'
    call = source.index(b'byte_address')
    first, second = source.index(b'0,', call), source.index(b'0)', call)
    records = [(39, 0, 3, 4, 0, 0, 9), (5, 0, 17, 1, 0, 0, 0),
               (5, 0, first, 1, 0, 0, 0),
               (43, 0, source.index(b',', call), 1, 0, 3, 0),
               (5, 0, second, 1, 0, 0, 0),
               (43, 0, source.index(b')', call), 1, 4, 5, 0),
               (42, 0, call, 12, 6, 0, 0),
               ({b'and': 52, b'or': 53}[operator], 0, 19, len(operator), 2, 7, 0),
               (32, 0, 10, 6, 8, 0, 10),
               (41, 0, len(source)-1, 1, 0, 0, 0),
               (33, 0, 0, 2, 1, 0, 0)]
    return pack_wire(source, records, profile)


def independent_legacy_identifiers(version, profile=0):
    """Logical words were identifiers in /1..8; no new frontend parses these packets."""
    source = b'fn main(){let and=7 let or=2 let not=3 return and+or+not}'
    tokens = 24
    if version == 1:
        nodes = [(4, 0, 14, 3, 0, 0, 0), (5, 0, 18, 1, 0, 0, 0),
                 (30, 0, 10, 3, 1, 2, 6), (4, 0, 24, 2, 0, 0, 0),
                 (5, 0, 27, 1, 0, 0, 0), (30, 0, 20, 3, 4, 5, 9),
                 (4, 0, 33, 3, 0, 0, 0), (5, 0, 37, 1, 0, 0, 0),
                 (30, 0, 29, 3, 7, 8, 15), (4, 0, 46, 3, 0, 0, 0),
                 (4, 0, 50, 2, 0, 0, 0), (15, 0, 49, 1, 10, 11, 0),
                 (4, 0, 53, 3, 0, 0, 0), (15, 0, 52, 1, 12, 13, 0),
                 (32, 0, 39, 6, 14, 0, 0), (33, 0, 0, 2, 3, 0, 0)]
    elif version == 2:
        # /2 requires an actual structured-control envelope, not just a changed version byte.
        source = b'fn main(){let and=7 let or=2 let not=3 if 0{and=0}return and+or+not}'
        tokens = 31
        nodes = [(4, 0, 14, 3, 0, 0, 0), (5, 0, 18, 1, 0, 0, 0),
                 (30, 0, 10, 3, 1, 2, 6), (4, 0, 24, 2, 0, 0, 0),
                 (5, 0, 27, 1, 0, 0, 0), (30, 0, 20, 3, 4, 5, 9),
                 (4, 0, 33, 3, 0, 0, 0), (5, 0, 37, 1, 0, 0, 0),
                 (30, 0, 29, 3, 7, 8, 11), (5, 0, 42, 1, 0, 0, 0),
                 (36, 0, 39, 2, 10, 0, 14), (4, 0, 44, 3, 0, 0, 0),
                 (5, 0, 48, 1, 0, 0, 0), (31, 0, 44, 3, 12, 13, 15),
                 (38, 0, 49, 1, 0, 0, 21), (4, 0, 57, 3, 0, 0, 0),
                 (4, 0, 61, 2, 0, 0, 0), (15, 0, 60, 1, 16, 17, 0),
                 (4, 0, 64, 3, 0, 0, 0), (15, 0, 63, 1, 18, 19, 0),
                 (32, 0, 50, 6, 20, 0, 0), (33, 0, 0, 2, 3, 0, 0)]
    elif version == 4:
        # Dialect4 requires a kind44 call statement with independently owned arguments.
        source = b'fn main(){let and=7 let or=2 let not=3 input_read(0,0) return and+or+not}'
        tokens = 30
        nodes = [(39, 0, 3, 4, 0, 0, 4), (4, 0, 14, 3, 0, 0, 0),
                 (5, 0, 18, 1, 0, 0, 0), (30, 0, 10, 3, 2, 3, 7),
                 (4, 0, 24, 2, 0, 0, 0), (5, 0, 27, 1, 0, 0, 0),
                 (30, 0, 20, 3, 5, 6, 10), (4, 0, 33, 3, 0, 0, 0),
                 (5, 0, 37, 1, 0, 0, 0), (30, 0, 29, 3, 8, 9, 16),
                 (5, 0, 50, 1, 0, 0, 0), (43, 0, 51, 1, 0, 11, 0),
                 (5, 0, 52, 1, 0, 0, 0), (43, 0, 53, 1, 12, 13, 0),
                 (42, 0, 39, 10, 14, 0, 0), (44, 0, 39, 10, 15, 0, 22),
                 (4, 0, 62, 3, 0, 0, 0), (4, 0, 66, 2, 0, 0, 0),
                 (15, 0, 65, 1, 17, 18, 0), (4, 0, 69, 3, 0, 0, 0),
                 (15, 0, 68, 1, 19, 20, 0), (32, 0, 55, 6, 21, 0, 23),
                 (41, 0, len(source)-1, 1, 0, 0, 0), (33, 0, 0, 2, 1, 0, 0)]
    else:
        nodes = [(39, 0, 3, 4, 0, 0, 4), (4, 0, 14, 3, 0, 0, 0),
                 (5, 0, 18, 1, 0, 0, 0), (30, 0, 10, 3, 2, 3, 7),
                 (4, 0, 24, 2, 0, 0, 0), (5, 0, 27, 1, 0, 0, 0),
                 (30, 0, 20, 3, 5, 6, 10), (4, 0, 33, 3, 0, 0, 0),
                 (5, 0, 37, 1, 0, 0, 0), (30, 0, 29, 3, 8, 9, 16),
                 (4, 0, 46, 3, 0, 0, 0), (4, 0, 50, 2, 0, 0, 0),
                 (15, 0, 49, 1, 11, 12, 0), (4, 0, 53, 3, 0, 0, 0),
                 (15, 0, 52, 1, 13, 14, 0), (32, 0, 39, 6, 15, 0, 17),
                 (41, 0, len(source)-1, 1, 0, 0, 0), (33, 0, 0, 2, 1, 0, 0)]
    if version < 5:
        header = struct.pack('<4sBBHHHHH', b'NQAF', version, 16, 0,
                             len(source), len(nodes), len(nodes), tokens)
        return header+source+b''.join(struct.pack('<BBHHHHH4s', *n, bytes(4)) for n in nodes)
    wire = bytearray(pack_wire(source, nodes, profile, version, 3 if version == 5 else version-1))
    struct.pack_into('<I', wire, 20, tokens)
    return bytes(wire)


class ShortCircuitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE/'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE/'c0-backend.seed')

    def ast(self, source, profile=False):
        p = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=30)
        self.assertEqual((p.returncode, p.stderr), (0, b''), source[:240])
        header, nodes = decode_wire(p.stdout)
        assert_owned_graph(header, nodes)
        return p.stdout, header, nodes

    def image(self, wire):
        p = run_native(self.backend, wire, timeout=10)
        self.assertEqual((p.returncode, p.stderr), (0, b''))
        self.assertEqual(p.stdout[:4], b'\x7fELF')
        return p.stdout

    def execute(self, image, payload=b''):
        with tempfile.TemporaryDirectory(prefix='c036-short-circuit-') as directory:
            path = Path(directory)/'program'
            path.write_bytes(image)
            path.chmod(0o700)
            return run_native(path, payload, timeout=10)

    def value(self, source, expected, profile=False, payload=b'', output=b'', error=b''):
        p = self.execute(self.image(self.ast(source, profile)[0]), payload)
        self.assertEqual((p.returncode, p.stdout, p.stderr),
                         (expected & 255, output, error), source[:240])

    def reject_wire(self, wire, code=None):
        p = run_native(self.backend, wire, timeout=10)
        self.assertEqual((p.returncode, p.stdout), (1, b''))
        self.assertRegex(p.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$')
        if code is not None:
            self.assertIn(f'[C0B-{code:03}]'.encode(), p.stderr)

    def reject_source(self, source, profile=False, diagnostic=b'C0P-'):
        p = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=10)
        self.assertEqual((p.returncode, p.stdout), (1, b''), source[:240])
        self.assertIn(b'error['+diagnostic, p.stderr)

    def test_independent_wire_and_profiles(self):
        # A backend rejecting /9 must fail here before any frontend is invoked.
        for profile in (0, 1):
            for operator, lhs, rhs, expected in (
                    (b'and', b'6', b'3', 1), (b'and', b'0', b'3', 0),
                    (b'or', b'0', b'3', 1), (b'or', b'6', b'0', 1),
                    (b'not', b'0', b'0', 1), (b'not', b'4294967296', b'0', 0)):
                with self.subTest(profile=profile, operator=operator, lhs=lhs, rhs=rhs):
                    p = self.execute(self.image(independent_wire(operator, profile, lhs, rhs)))
                    self.assertEqual((p.returncode, p.stdout, p.stderr), (expected, b'', b''))
            for operator, expected in ((b'and', 1), (b'or', 1), (b'not', 0)):
                with self.subTest(profile=profile, named_operator=operator):
                    p = self.execute(self.image(independent_named_wire(operator, profile)))
                    self.assertEqual((p.returncode, p.stdout, p.stderr), (expected, b'', b''))

    def test_full_i64_truth_normalization(self):
        values = (MIN, MIN+1, -4294967296, -256, -1, 0, 1, 2, 256, 4294967296, MAX)
        rng = random.Random(0xC036)
        pairs = [(lhs, values[(i*3+2) % len(values)]) for i, lhs in enumerate(values)]
        pairs += [(rng.randint(MIN, MAX), rng.randint(MIN, MAX)) for _ in range(16)]
        pairs += [(0, 0), (0, 4294967296), (4294967296, 0), (4294967296, 4294967296)]
        cases = []
        for lhs, rhs in pairs:
            cases += [(f'({lhs}) and ({rhs})'.encode(), int(bool(lhs) and bool(rhs))),
                      (f'({lhs}) or ({rhs})'.encode(), int(bool(lhs) or bool(rhs))),
                      (f'not ({lhs})'.encode(), int(not lhs))]
        body = b''.join(b'if ('+expr+b')!='+str(expected).encode()+b'{return '+
                        str(i+2).encode()+b'}' for i, (expr, expected) in enumerate(cases))
        # Target-side equality observes every result bit; an exit-code mask cannot pass.
        for profile in (False, True):
            self.value(b'fn main(){'+body+b'return 1}', 1, profile)

    def test_precedence_prefixes_and_left_associativity(self):
        # Literal expectations distinguish each neighboring precedence boundary.
        cases = ((b'not -7', 0), (b'-not 0', -1), (b'~not 0', -2),
                 (b'not ~0', 0), (b'not not 7', 1), (b'not 0*0', 0),
                 (b'not 0==0', 0), (b'not (0*0)', 1),
                 (b'1|2 and 0', 0), (b'2 and 0|2', 1),
                 (b'0 or 2|4', 1), (b'1 or 0 and 0', 1),
                 (b'0 and 1 or 2', 1), (b'1 or 0 or 0', 1),
                 (b'2 and 3 and 4', 1), (b'1^3&2 and 2<3', 1))
        for profile in (False, True):
            body = b''.join(b'if ('+expr+b')!=('+str(expected).encode()+b'){return '+
                            str(i+2).encode()+b'}' for i, (expr, expected) in enumerate(cases))
            self.value(b'fn main(){'+body+b'return 1}', 1, profile)
            for operator, kind in ((b'and', 52), (b'or', 53)):
                _, header, nodes = self.ast(b'fn main(){return 1 '+operator+b' 2 '+operator+b' 3}', profile)
                self.assertEqual((header['version'], header['dialect'], header['runtime_profile']),
                                 (9, 8, int(profile)))
                roots = [(i, n) for i, n in enumerate(nodes, 1) if n[0] == kind]
                self.assertEqual(len(roots), 2)
                # Associativity has identical truth/effects for a flat chain, so inspect ownership.
                self.assertEqual(roots[1][1][4:7], (roots[0][0], roots[1][0]-1, 0))
            _, _, nodes = self.ast(b'fn main(){return not -~not 0}', profile)
            prefixes = [(i, n) for i, n in enumerate(nodes, 1) if n[0] in (47, 51, 54)]
            self.assertEqual([n[0] for _, n in prefixes], [54, 51, 47, 54])
            for i, n in prefixes:
                self.assertEqual(n[4:7], (i-1, 0, 0))

    def test_exact_keywords_and_identifier_boundaries(self):
        names = (b'andrew', b'android', b'and1', b'and_', b'orphan', b'oracle',
                 b'or0', b'or_', b'notable', b'notebook', b'not0', b'not_',
                 b'_and', b'_or', b'_not', b'and'+b'x'*256, b'or'+b'x'*256, b'not'+b'x'*256)
        declarations = b''.join(b'let '+name+b'=1 ' for name in names)
        old = b'fn main(){'+declarations+b'return '+b'+'.join(names)+b'}'
        for profile in (False, True):
            self.value(old, len(names), profile)
            # Prefix names alone must not activate /9.
            self.assertLess(self.ast(old, profile)[1]['version'], 9)
            source = b'fn main(){let notable=0 return not(notable)and(2)or(0)}'
            self.value(source, 1, profile)
            _, header, nodes = self.ast(source, profile)
            self.assertEqual((header['version'], header['dialect']), (9, 8))
            anchors = {52: b'and', 53: b'or', 54: b'not'}
            logical = [n for n in nodes if n[0] in anchors]
            self.assertEqual({n[0] for n in logical}, {52, 53, 54})
            for kind, flags, offset, span, left, right, nxt in logical:
                self.assertEqual((flags, source[offset:offset+span], nxt), (0, anchors[kind], 0))
                self.assertEqual(span, len(anchors[kind]))
            for keyword in (b'and', b'or', b'not'):
                for source in (b'fn main(){let '+keyword+b'=1 return 0}',
                               b'fn '+keyword+b'(){return 0}fn main(){return 0}',
                               b'fn f('+keyword+b'){return 0}fn main(){return 0}'):
                    with self.subTest(keyword=keyword, source=source, profile=profile):
                        self.reject_source(source, profile)

    def test_left_to_right_selected_effects_once(self):
        prefix = (b'fn mark(x,r){byte_store(16+byte_load(0),x)'
                  b'byte_store(0,byte_load(0)+1)return r}fn main(){let v=')
        cases = ((b'mark(65,0) and mark(66,9)', 0, b'A'),
                 (b'mark(65,2) and mark(66,3)', 1, b'AB'),
                 (b'mark(65,2) or mark(66,0)', 1, b'A'),
                 (b'mark(65,0) or mark(66,-7)', 1, b'AB'),
                 (b'not mark(65,0)', 1, b'A'),
                 (b'(mark(65,0) or mark(66,2)) and mark(67,3)', 1, b'ABC'),
                 (b'(mark(65,0) and mark(66,2)) or mark(67,0)', 0, b'AC'),
                 (b'mark(65,1) or (mark(66,1) and mark(67,1))', 1, b'A'))
        for profile in (False, True):
            for expression, expected, output in cases:
                with self.subTest(expression=expression, profile=profile):
                    self.value(prefix+expression+b' output_write(16,byte_load(0))'
                               b'return v+10*byte_load(0)}', expected+10*len(output),
                               profile, output=output)

    def test_skipped_streams_and_syscalls(self):
        source = (b'fn main(){byte_store(0,88) '
                  b'let a=0 and input_read(32,1) let b=1 or input_read(32,1) '
                  b'let c=0 and output_write(0,1) let d=1 or error_write(0,1) '
                  b'let n=input_read(32,1) let m=input_read(33,1) '
                  b'output_write(32,2) return a+b+c+d+n+m}')
        raw = (b'fn main(){unsafe {# safety: skipped exit owns no external state\n'
               b'let a=0 and syscall6(60,0) let b=1 or syscall6(60,0) return a+b+6}}')
        for profile in (False, True):
            self.value(source, 4, profile, payload=b'ABC', output=b'AB')
            self.value(b'fn main(){byte_store(0,65) let a=1 and output_write(0,1) '
                       b'let b=0 or error_write(0,1) return a+b}', 2, profile,
                       output=b'A', error=b'A')
            self.value(raw, 7, profile)
            self.value(b'fn main(){unsafe {# safety: query this process only\n'
                       b'return 1 and syscall6(39,0)}}', 1, profile)

    def test_nested_calls_preserve_pending_guards(self):
        source = (b'fn mark(x,r){byte_store(16+byte_load(0),x)'
                  b'byte_store(0,byte_load(0)+1)return r}'
                  b'fn id(x){return x}'
                  b'fn six(a,b,c,d,e,f){return a+10*b+100*c+1000*d+10000*e+100000*f}'
                  b'fn main(){let v=six(mark(65,0) or id(mark(66,8)),'
                  b'id(mark(67,9)) and mark(68,0),not id(mark(69,0)),'
                  b'0 and six(1,2,3,4,5,1/0),1 or six(1,2,3,4,5,1/0),'
                  b'(mark(70,0) or mark(71,5)) and id(mark(72,6)))'
                  b'output_write(16,byte_load(0))return v==110101}')
        for profile in (False, True):
            self.value(source, 1, profile, output=b'ABCDEFGH')

    def test_loop_rechecks_lhs_and_selected_rhs(self):
        for profile in (False, True):
            for expression, lhs_bound, rhs_bound, bodies, lhs_count, rhs_count in (
                    (b'lhs() and rhs()', 4, 9, 3, 4, 3),
                    (b'lhs() or rhs()', 3, 5, 4, 5, 3),
                    (b'not not (lhs() and rhs())', 4, 9, 3, 4, 3)):
                source = (b'fn lhs(){let n=byte_load(0)+1 byte_store(0,n)return n<'+
                          str(lhs_bound).encode()+b'}'
                          b'fn rhs(){byte_store(1,byte_load(1)+1)return byte_load(0)<'+
                          str(rhs_bound).encode()+b'}fn main(){let n=0 while '+expression+
                          b'{n=n+1}return (n=='+str(bodies).encode()+b') and (byte_load(0)=='+
                          str(lhs_count).encode()+b') and (byte_load(1)=='+str(rhs_count).encode()+b')}')
                with self.subTest(expression=expression, profile=profile):
                    self.value(source, 1, profile)

    def test_skipped_faults_and_selected_error_locations(self):
        faults = ((b'1/0', b'/', 1), (b'9223372036854775807+1', b'+', 1),
                  (b'9223372036854775807*2', b'*', 1),
                  (b'(-9223372036854775808)/-1', b'/', 1),
                  (b'--9223372036854775808', b'-', 1),
                  (b'byte_load(-1)', b'byte_load', 4),
                  (b'input_read(-1,1)', b'input_read', 4),
                  (b'output_write(-1,1)', b'output_write', 4))
        skipped = b''.join(b'if (0 and ('+expr+b'))!=0{return 2}'
                           b'if (1 or ('+expr+b'))!=1{return 3}' for expr, _, _ in faults)
        for profile in (False, True):
            self.value(b'fn main(){'+skipped+b'return 1}', 1, profile)
            for i, (expression, token, code) in enumerate(faults):
                prefix = b'fn main(){\nreturn '+(b'1 and (' if i % 2 == 0 else b'0 or (')
                source = prefix+expression+b')}'
                p = self.execute(self.image(self.ast(source, profile)[0]))
                position = len(prefix)+expression.index(token)
                line = source[:position].count(b'\n')+1
                column = position-source.rfind(b'\n', 0, position)
                with self.subTest(expression=expression, profile=profile):
                    self.assertEqual((p.returncode, p.stdout), (70, b''))
                    self.assertTrue(p.stderr.startswith(
                        f'input:{line}:{column}: error[C0R-{code:03}]:'.encode()), p.stderr)
            for expression in (b'(1/0) and byte_load(-1)', b'(1/0) or byte_load(-1)', b'not (1/0)'):
                source = b'fn main(){return '+expression+b'}'
                p = self.execute(self.image(self.ast(source, profile)[0]))
                self.assertEqual((p.returncode, p.stdout), (70, b''))
                self.assertTrue(p.stderr.startswith(
                    f'input:1:{source.index(b"/")+1}: error[C0R-001]:'.encode()), p.stderr)

    def test_skipped_static_semantic_safety_and_minimum_rejection(self):
        for profile in (False, True):
            for operator, lhs in ((b'and', b'0'), (b'or', b'1')):
                for rhs, code in ((b'missing', 3), (b'absent(1)', 8),
                                  (b'9223372036854775808', 5),
                                  (b'not 9223372036854775808', 5),
                                  (b'-(not 9223372036854775808)', 5)):
                    source = b'fn main(){return '+lhs+b' '+operator+b' ('+rhs+b')}'
                    with self.subTest(rhs=rhs, operator=operator, profile=profile):
                        self.reject_wire(self.ast(source, profile)[0], code)
                self.reject_wire(self.ast(b'fn f(x){return x}fn main(){return '+lhs+b' '+
                                          operator+b' f(1,2)}', profile)[0])
                source = b'fn main(){return '+lhs+b' '+operator+b' byte_address(0,0)}'
                self.reject_source(source, profile, b'C0S-001')
                self.reject_wire(independent_unsafe_rhs(operator, int(profile)), 10)
                self.reject_wire(independent_wire(operator, int(profile), lhs,
                                                  b'9223372036854775808'), 5)
                wire = independent_wire(operator, int(profile), lhs, b'missing')
                self.reject_wire(change_node(wire, 3, 0, 4), 3)
            self.reject_wire(independent_wire(b'not', int(profile), b'9223372036854775808'), 5)
            self.value(b'fn main(){return (not (-9223372036854775808))==0 and '
                       b'((0 and (-9223372036854775808))==0) and '
                       b'((1 or (-9223372036854775808))==1) and '
                       b'((~(-9223372036854775808))==9223372036854775807)}', 1, profile)
            self.value(b'fn main(){unsafe {# safety: inspect only the owned arena address\n'
                       b'return 0 or (byte_address(0,0)!=0)}}', 1, profile)

    def test_wire_versions_anchors_and_ownership_reject(self):
        for operator in (b'and', b'or', b'not'):
            wire = independent_wire(operator)
            header, nodes = decode_wire(wire)
            assert_owned_graph(header, nodes)
            self.image(wire)
            logical = 3 if operator == b'not' else 4
            offset = 32+header['source_length']+(logical-1)*32
            changes = [(5, b'\x10'), (6, b'\x01'), (24, b'\x07'), (25, b'\x02'),
                       (26, b'\x01'), (28, b'\x01'), (offset+1, b'\x01'),
                       (offset+2, b'\x01'), (offset+24, b'\x01'), (offset+28, b'\x01')]
            changes += [(offset+field, struct.pack('<I', value)) for field, value in
                        ((4, 0), (8, 1), (8, len(operator)+1), (12, 0),
                         (12, logical), (12, 65536), (12, 0xffffffff), (20, 1))]
            changes += [(offset+16, struct.pack('<I', 2 if operator == b'not' else 0))]
            for at, data in changes:
                bad = bytearray(wire)
                bad[at:at+len(data)] = data
                with self.subTest(operator=operator, at=at, data=data):
                    self.reject_wire(bad)
            if operator != b'not':
                # A connected, uniquely owned tree can still violate physical postorder.
                bad = change_node(change_node(wire, logical, 12, 3), logical, 16, 2)
                h, n = decode_wire(bad)
                assert_owned_graph(h, n)
                self.reject_wire(bad, 2)
                self.reject_wire(change_node(wire, logical, 16, 2), 2)  # aliased child
            for before in (False, True):
                for character in (b'x', b'_', b'0', b'Z'):
                    with self.subTest(operator=operator, before=before, character=character):
                        self.reject_wire(keyword_neighbor(wire, before, character), 6)
            bad = bytearray(wire)
            bad[32+nodes[logical-1][2]] = ord(chr(operator[0]).upper())
            self.reject_wire(bad, 6)
            for version in range(5, 9):
                self.reject_wire(pack_wire(header['source'], nodes, version=version,
                                           dialect=4 if version == 5 else version-1), 2)
            # Valid narrow framing and scalar envelope isolate old-version kind rejection.
            scalar = []
            for k, f, o, n, l, r, x in nodes[1:-2]:
                scalar.append((k, f, o, n, l-1 if l else 0, r-1 if r else 0, 0))
            scalar.append((33, 0, 0, 2, len(scalar), 0, 0))
            for version in range(1, 5):
                old = struct.pack('<4sBBHHHHH', b'NQAF', version, 16, 0,
                                  len(header['source']), len(scalar), len(scalar), 11)
                old += header['source']+b''.join(struct.pack('<BBHHHHH4s', *n, bytes(4)) for n in scalar)
                self.reject_wire(old, 2)

    def test_high_u32_ids_offsets_and_guard_map(self):
        # Exactly 65,536 records, with a high logical LHS-map key and high source offsets.
        # As with existing maximal-wire fixtures, token_count is a bounded declaration,
        # not a claim that the backend authenticates a fresh lexical token inventory.
        count = 65529
        source = b' '*70000+b'fn main(){return '+b'~'*count+b'6 and 3}'
        literal = 70000+17+count
        records = [(39, 0, 70003, 4, 0, 0, 65534), (5, 0, literal, 1, 0, 0, 0)]
        for index in range(count):
            records.append((51, 0, literal-1-index, 1, len(records), 0, 0))
        left = len(records)
        records.append((5, 0, len(source)-2, 1, 0, 0, 0))
        records.append((52, 0, source.rindex(b'and'), 3, left, left+1, 0))
        records += [(32, 0, 70010, 6, len(records), 0, 65535),
                    (41, 0, len(source)-1, 1, 0, 0, 0), (33, 0, 70000, 2, 1, 0, 0)]
        wire = bytearray(pack_wire(source, records))
        struct.pack_into('<I', wire, 20, 65536)
        header, nodes = decode_wire(wire)
        assert_owned_graph(header, nodes)
        self.assertEqual((header['node_count'], header['root_id']), (65536, 65536))
        self.assertGreater(nodes[65532][4], 65000)
        self.assertGreater(nodes[65532][2], 65535)
        p = self.execute(self.image(wire))
        self.assertEqual((p.returncode, p.stdout, p.stderr), (1, b'', b''))
        self.reject_wire(change_node(wire, 65533, 12, 65536), 2)

    def test_legacy_c035_bytes_unchanged(self):
        corpora = ((LEGACY, (False,), LEGACY_AST_SHA256, LEGACY_ELF_SHA256),
                   (LEGACY_C034, (False, True), LEGACY_C034_AST, LEGACY_C034_ELF),
                   (LEGACY_C035, (False, True), LEGACY_C035_AST, LEGACY_C035_ELF))
        for sources, profiles, want_wire, want_elf in corpora:
            wire_hash, elf_hash = hashlib.sha256(), hashlib.sha256()
            for profile in profiles:
                for source in sources:
                    wire, header, _ = self.ast(source, profile)
                    self.assertLess(header['version'], 9)
                    wire_hash.update(wire)
                    elf_hash.update(self.image(wire))
            self.assertEqual(wire_hash.hexdigest(), want_wire)
            self.assertEqual(elf_hash.hexdigest(), want_elf)
        for version in range(1, 9):
            for profile in ((0,) if version < 5 else (0, 1)):
                with self.subTest(legacy_identifiers=True, version=version, profile=profile):
                    wire = independent_legacy_identifiers(version, profile)
                    image = self.image(wire)
                    p = self.execute(image)
                    self.assertEqual((p.returncode, p.stdout, p.stderr), (12, b'', b''))
                    if version == 1:
                        # Exact bytes frozen with the qualified ROOT C0.35 pair.
                        self.assertEqual(hashlib.sha256(wire).hexdigest(),
                                         'cbe0b6eb030dc518e69a167f55bf8241c297fbc6ded0f52fd9d28761066349d8')
                        self.assertEqual(hashlib.sha256(image).hexdigest(),
                                         '937aff5483bb2a6f2231e74432198c8b3fbfe44ffd4973be41cc71feac6097c6')

    def test_exact_machine_bytes_and_branch_destinations(self):
        load = bytes.fromhex('488b85f8ffffff')
        rhs_load = bytes.fromhex('488b85f0ffffff')
        store = bytes.fromhex('488985f8ffffff')
        rhs_store = bytes.fromhex('488985f0ffffff')
        test = bytes.fromhex('4885c0')  # Full-width TEST rax,rax, not a 32-bit truth check.
        nonzero = test+bytes.fromhex('0f95c00fb6c0')
        is_zero = test+bytes.fromhex('0f94c00fb6c0')
        prologue = bytes.fromhex('554889e54881ec0010000041ffc7')
        following = load+bytes.fromhex('41ffcfc9c3')
        for profile in (0, 1):
            for operator in (b'and', b'or', b'not'):
                wire = independent_wire(operator, profile, b'7' if operator == b'not' else b'6')
                image = self.image(wire)
                self.assertEqual(image, self.image(wire))
                # Derive main from the startup CALL rel32; a later matching substring is insufficient.
                entry = struct.unpack_from('<Q', image, 24)[0]-0x400000
                call = image.index(bytes.fromhex('4531ffe8'), entry, entry+62)+3
                main = call+5+struct.unpack_from('<i', image, call+1)[0]
                first = bytes.fromhex('48b8')+struct.pack('<q', 7 if operator == b'not' else 6)+store
                if operator == b'not':
                    logical = load+is_zero+store
                    self.assertEqual(len(logical), 23)
                    body = prologue+first+logical+following
                else:
                    right = bytes.fromhex('48b8')+struct.pack('<q', 3)+rhs_store
                    join = rhs_load+nonzero+store
                    self.assertEqual(len(join), 23)
                    # The guard skips exactly the RHS literal (17) plus the join (23).
                    guard = load+nonzero+store+bytes.fromhex('0f84' if operator == b'and' else '0f85')
                    guard += struct.pack('<i', 40)
                    self.assertEqual(len(guard), 29)
                    body = prologue+first+guard+right+join+following
                    branch = main+len(prologue)+len(first)+len(guard)-6
                    target = branch+6+struct.unpack_from('<i', image, branch+2)[0]
                    self.assertEqual(target, main+len(body)-len(following))
                    self.assertEqual(image[target:target+len(following)], following)
                self.assertEqual(image[main:main+len(body)], body)
                self.assertEqual(image[main+len(body):main+len(body)+8], bytes(8))
                # The tested frontend must select the same complete executable body.
                self.assertEqual(self.image(self.ast(decode_wire(wire)[0]['source'], bool(profile))[0]), image)

    def test_finite_malformed_input_and_prefix_chains(self):
        malformed = (b'and 7', b'or 7', b'not', b'not )', b'1 and', b'1 or',
                     b'1 not 0', b'1 and or 0', b'1 or and 0', b'not *7',
                     b'not +7', b'not (', b'(not)', b'1 && 2', b'1 || 2')
        for expression in malformed:
            with self.subTest(expression=expression):
                self.reject_source(b'fn main(){return '+expression+b'}')
        for operator in (b'and', b'or', b'not'):
            wire = independent_named_wire(operator)
            for size in (0, 4, 15, 31, 32, 33, len(wire)-33, len(wire)-1):
                with self.subTest(operator=operator, size=size):
                    self.reject_wire(wire[:size], 1)
            self.reject_wire(wire+b'\0', 1)
        self.value(b'fn main(){return '+b'not '*1000+b'7}', 1)
        self.value(b'fn main(){return '+b'not -~'*64+b'7}', 0)
        _, header, nodes = self.ast(b'fn main(){return '+b'not '*32764+b'7}')
        self.assertEqual(header['version'], 9)
        self.assertEqual(sum(n[0] == 54 for n in nodes), 32764)
        self.reject_source(b'fn main(){return not '+b'~'*65536+b'7}', diagnostic=b'C0P-003')

    def test_generation_short_circuit_contract(self):
        # This exact method is selected on each actual B/C pair; env chooses real compilers.
        # Assertions use independent branches: an always-skipped AND must not
        # skip the oracle's own checks. Full values and selected output are
        # observed separately in both runtime profiles.
        source = (b'fn tick(x){byte_store(0,byte_load(0)+1)return x}'
                  b'fn rhs(){byte_store(1,byte_load(1)+1)return 1}'
                  b'fn main(){let n=3 while tick(n) and rhs(){n=n-1}'
                  b'let a=0 and (1/0) let b=1 or byte_load(-1) '
                  b'if a!=0{return 11} if b!=1{return 12}'
                  b'if byte_load(0)!=4{return 13} if byte_load(1)!=3{return 14}'
                  b'if (4294967296 and -1)!=1{return 15}'
                  b'if (0 or -9223372036854775808)!=1{return 16}'
                  b'if (not -7)!=0{return 17} if (1 or 0 and 0)!=1{return 18}'
                  b'if (2 and 0|2)!=1{return 19} if (1 and 0)!=0{return 20}'
                  b'byte_store(2,65) let v=1 and output_write(2,1) '
                  b'if v!=1{return 21} return 1}')
        for profile in (False, True):
            with self.subTest(profile=profile):
                self.value(source, 1, profile, output=b'A')
                self.value(b'fn main(){return 1 and 0}', 0, profile)
                self.value(b'fn main(){byte_store(0,66) '
                           b'let v=1 and output_write(0,1) return v}',
                           1, profile, output=b'B')
                p = self.execute(self.image(independent_named_wire(b'and', int(profile))))
                self.assertEqual((p.returncode, p.stdout, p.stderr), (1, b'', b''))
                self.reject_wire(independent_unsafe_rhs(b'and', int(profile)), 10)
                self.reject_wire(independent_wire(b'or', int(profile), b'1', b'9223372036854775808'), 5)
        wire = bytearray(independent_wire())
        wire[4], wire[24] = 8, 7
        self.reject_wire(wire, 2)


if __name__ == '__main__':
    unittest.main()
