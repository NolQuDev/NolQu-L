"""Independent C0.37 checked shifts: full i64 values, handwritten wire and x86.

Expected shifts use multiplication/modulo and floor division in Python. Generated
checks use ordinary if branches and compare all 64 bits, never exit-code masks
or a shift expression to decide whether an oracle assertion executes.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import tempfile
import unittest

from c031_support import (assert_owned_graph, candidate_binary, decode_nqaf,
                         encode_profile_source, run_native)
from test_c0_short_circuit import (independent_legacy_identifiers,
                                   independent_wire as logical_wire)

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
MIN, MAX = -9223372036854775808, 9223372036854775807
MODULUS, SIGN = 18446744073709551616, 9223372036854775808
FAULT_SUFFIX = b'error[C0R-010]: shift count out of range; use 0..63\n'
# Frozen from retained exact qualified C036 seeds, profile outermost. See the
# private qualification receipt for seed identities; no candidate derives wants.
LEGACY_C036 = (
    b'fn main(){return 7}',
    b'fn main(){if 1{return 7}else{return 9}return 0}',
    b'fn main(){let n=3 while n{n=n-1}return n}',
    b'fn f(a,b){return a+b}fn main(){return f(2,3)}',
    b'fn main(){byte_store(0,65)output_write(0,1)return byte_load(0)}',
    b'fn main(){unsafe {# safety: inspect the bounded owned arena only\nreturn byte_address(0,0)!=0}}',
    b'fn main(){return -9223372036854775808}',
    b'fn main(){return (~(-9223372036854775808))^3|1}',
    b'fn main(){return not 0 and 4294967296 or 0}',
    b'fn main(){return (0 and byte_load(-1))+(1 or 1/0)}',
    b'fn f(x){return not x}fn main(){return f(0) and ~0}',
    b'fn main(){'+b' '*70000+b'return not (7|2)}',
)
LEGACY_C036_AST = '35562628c64ea1144e07004f6ac0f2337d887541086196575013a9da05267bbc'
LEGACY_C036_ELF = '5ed2c4e8d29995daedd5b2bb952f1c57d23ac4d2756f5119e0cbd59e8287d42f'


def shift_value(lhs, count, operator):
    """Independent integer specification, deliberately without host shifts."""
    if not 0 <= count <= 63:
        raise ValueError('invalid signed i64 shift count')
    if operator == b'<<':
        result = ((lhs % MODULUS) * pow(2, count)) % MODULUS
        if result >= SIGN:
            result -= MODULUS
        return result
    if operator == b'>>':
        return lhs // pow(2, count)
    raise ValueError('unknown shift')


def value_cases():
    values = (MIN, MIN+1, -4294967297, -257, -3, -1, 0, 1, 3,
              255, 4294967296, MAX)
    pairs = [(a, n) for a in values for n in (0, 1, 7, 31, 32, 62, 63)]
    pairs += [(a, n) for a in (MIN+1, -3, MAX) for n in range(64)]
    rng = random.Random(0xC037)
    pairs += [(rng.randint(MIN, MAX), rng.randrange(64)) for _ in range(24)]
    return [(f'({a})'.encode()+operator+str(n).encode(), shift_value(a, n, operator))
            for a, n in pairs for operator in (b'<<', b'>>')]


def if_checks(cases):
    # A broken shift must not be able to skip the check testing that very shift.
    return b''.join(b'if ('+expr+b')!=('+str(want).encode()+b'){return '+
                    str(2+i % 200).encode()+b'}' for i, (expr, want) in enumerate(cases))


def pack_wire(source, records, profile=0, version=10, dialect=9, tokens=11):
    if version < 5:
        header = struct.pack('<4sBBHHHHH', b'NQAF', version, 16, 0, len(source),
                             len(records), len(records), tokens)
        return header+source+b''.join(struct.pack('<BBHHHHH4s', *n, bytes(4)) for n in records)
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', version, 32, 0, len(source),
                         len(records), len(records), tokens, dialect, profile, 0, 0)
    return header+source+b''.join(struct.pack('<BBHIIIIIII', k, f, 0, o, n, l, r, x, 0, 0)
                                 for k, f, o, n, l, r, x in records)


def independent_wire(operator=b'<<', profile=0, lhs=b'6', rhs=b'1'):
    """Entire graph is handwritten, including explicit NEGATE ownership for MIN."""
    source = b'fn main(){return '+lhs+operator+rhs+b'}'
    records = [(39, 0, 3, 4, 0, 0, 0)]
    def operand(text, offset):
        negative = text.startswith(b'-')
        records.append((5, 0, offset+int(negative), len(text)-int(negative), 0, 0, 0))
        if negative:
            records.append((47, 0, offset, 1, len(records), 0, 0))
        return len(records)
    left = operand(lhs, 17)
    right = operand(rhs, 19+len(lhs))
    records.append(({b'<<': 55, b'>>': 56}[operator], 0, 17+len(lhs), 2, left, right, 0))
    ret = len(records)+1
    records += [(32, 0, 10, 6, ret-1, 0, ret+1),
                (41, 0, len(source)-1, 1, 0, 0, 0), (33, 0, 0, 2, 1, 0, 0)]
    records[0] = (39, 0, 3, 4, 0, 0, ret)
    tokens = 10+int(lhs.startswith(b'-'))+int(rhs.startswith(b'-'))
    return pack_wire(source, records, profile, tokens=tokens)


def independent_unsafe_shift(profile=0, skipped=False):
    """The frontend cannot launder this unowned byte_address call in /10."""
    expression = b'0 and (1<<byte_address(0,0))' if skipped else b'1<<byte_address(0,0)'
    source = b'fn main(){return '+expression+b'}'
    call = source.index(b'byte_address')
    first, second = source.index(b'0,', call), source.index(b'0)', call)
    records = [(39, 0, 3, 4, 0, 0, 0)]
    if skipped:
        records.append((5, 0, 17, 1, 0, 0, 0))
    records.append((5, 0, source.index(b'1<<'), 1, 0, 0, 0))
    left = len(records)
    records += [(5, 0, first, 1, 0, 0, 0),
                (43, 0, source.index(b',', call), 1, 0, len(records)+1, 0)]
    arguments = len(records)
    records += [(5, 0, second, 1, 0, 0, 0),
                (43, 0, source.index(b')', call), 1, arguments, arguments+1, 0)]
    records.append((42, 0, call, 12, len(records), 0, 0))
    records.append((55, 0, source.index(b'<<'), 2, left, len(records), 0))
    if skipped:
        records.append((52, 0, source.index(b'and'), 3, 2, len(records), 0))
    ret = len(records)+1
    records += [(32, 0, 10, 6, ret-1, 0, ret+1),
                (41, 0, len(source)-1, 1, 0, 0, 0), (33, 0, 0, 2, 1, 0, 0)]
    records[0] = (39, 0, 3, 4, 0, 0, ret)
    return pack_wire(source, records, profile)


def change_node(wire, node_id, field, value):
    result = bytearray(wire)
    at = 32+struct.unpack_from('<I', wire, 8)[0]+(node_id-1)*32+field
    if field in (0, 1):
        result[at] = value
    elif field == 2:
        struct.pack_into('<H', result, at, value)
    else:
        struct.pack_into('<I', result, at, value)
    return bytes(result)


def fault_message(source, anchor, code=10):
    line = source[:anchor].count(b'\n')+1
    column = anchor-source.rfind(b'\n', 0, anchor)
    prefix = f'input:{line}:{column}: '.encode()
    if code == 10:
        return prefix+FAULT_SUFFIX
    return prefix+f'error[C0R-{code:03}]:'.encode()


def generation_source():
    # Literal wants are hand-checked. No logical AND/OR combines these assertions.
    cases = ((b'1<<63', MIN), (b'(-1)<<63', MIN), (b'(-1)<<1', -2),
             (b'9223372036854775807<<1', -2), (b'(-9223372036854775808)<<1', 0),
             (b'(-9223372036854775808)>>63', -1), (b'(-3)>>1', -2),
             (b'(-1)>>1', -1), (b'9223372036854775807>>63', 0),
             (b'4294967296>>32', 1), (b'1<<0', 1), (b'(-3)>>0', -3),
             (b'3<<2+1', 24), (b'32>>1>>2', 4), (b'1<<2<5', 1),
             (b'2&1<<1', 2), (b'0 and (1<<64)', 0), (b'1 or (1>>-1)', 1))
    return (b'fn tick(x){byte_store(0,byte_load(0)+1)return x}'
            b'fn id(x){return x}fn main(){'+if_checks(cases)+
            b'let n=8 let k=0 while tick(n)>>id(1){n=n/2 k=k+1}'
            b'if k!=3{return 30}if byte_load(0)!=4{return 31}'
            b'if (tick(3)<<tick(2))!=12{return 32}'
            b'if byte_load(0)!=6{return 33}'
            b'byte_store(1,65)let q=output_write(1,1)<<id(1)'
            b'if q!=2{return 34}return 1}')


class ShiftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE/'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE/'c0-backend.seed')

    def retain_failure(self, label, **contents):
        directory = os.environ.get('C037_FAILURE_DIR')
        if directory is None:
            return
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix=self._testMethodName+'-'+label+'-', dir=root))
        for name, data in contents.items():
            if isinstance(data, (bytes, bytearray)):
                (output/name).write_bytes(data)
            else:
                (output/name).write_text(str(data)+'\n')

    def ast(self, source, profile=False):
        p = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=120)
        if (p.returncode, p.stderr) != (0, b''):
            self.retain_failure('frontend', source=source, stdout=p.stdout, stderr=p.stderr)
        self.assertEqual((p.returncode, p.stderr), (0, b''), source[:240])
        header, nodes = decode_nqaf(p.stdout)
        assert_owned_graph(header, nodes)
        return p.stdout, header, nodes

    def image(self, wire):
        p = run_native(self.backend, wire, timeout=120)
        if (p.returncode, p.stderr) != (0, b''):
            self.retain_failure('backend', wire=wire, stdout=p.stdout, stderr=p.stderr)
        self.assertEqual((p.returncode, p.stderr), (0, b''))
        self.assertEqual(p.stdout[:4], b'\x7fELF')
        return p.stdout

    def execute(self, image, payload=b'', bad_stderr=False):
        with tempfile.TemporaryDirectory(prefix='c037-shifts-') as directory:
            path = Path(directory)/'program'
            path.write_bytes(image)
            path.chmod(0o700)
            if bad_stderr:
                # Keep fd2 occupied through Android/QEMU startup, with read-only
                # access. Guest sys_write must see EBADF on both execution modes.
                with open(os.devnull, 'rb') as inaccessible:
                    return run_native(path, payload, timeout=15, stderr=inaccessible)
            return run_native(path, payload, timeout=15)

    def value(self, source, expected=1, profile=False, payload=b'', output=b''):
        wire = self.ast(source, profile)[0]
        image = self.image(wire)
        p = self.execute(image, payload)
        if (p.returncode, p.stdout, p.stderr) != (expected % 256, output, b''):
            self.retain_failure('value', source=source, wire=wire, image=image,
                                stdout=p.stdout, stderr=p.stderr, returncode=p.returncode)
        self.assertEqual((p.returncode, p.stdout, p.stderr),
                         (expected % 256, output, b''), source[:240])

    def runtime_fault(self, source, anchor, profile=False, code=10, output=b''):
        wire = self.ast(source, profile)[0]
        image = self.image(wire)
        p = self.execute(image)
        want = fault_message(source, anchor, code)
        valid_error = p.stderr == want if code == 10 else p.stderr.startswith(want)
        if (p.returncode, p.stdout) != (70, output) or not valid_error:
            self.retain_failure('runtime', source=source, wire=wire, image=image,
                                stdout=p.stdout, stderr=p.stderr, returncode=p.returncode)
        self.assertEqual((p.returncode, p.stdout), (70, output))
        if code == 10:
            self.assertEqual(p.stderr, want)
        else:
            self.assertTrue(valid_error, (p.stderr, want))

    def reject_wire(self, wire, code=None):
        p = run_native(self.backend, wire, timeout=120)
        if (p.returncode, p.stdout) != (1, b''):
            self.retain_failure('accepted-wire', wire=wire, stdout=p.stdout, stderr=p.stderr)
        self.assertEqual((p.returncode, p.stdout), (1, b''))
        self.assertRegex(p.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$')
        if code is not None:
            self.assertIn(f'[C0B-{code:03}]'.encode(), p.stderr)

    def reject_source(self, source, profile=False, diagnostic=b'C0P-'):
        p = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=120)
        self.assertEqual((p.returncode, p.stdout), (1, b''), source[:240])
        self.assertIn(b'error['+diagnostic, p.stderr)

    def test_independent_wire_and_version(self):
        # Rejecting /10 must fail this before any frontend output is trusted.
        cases = ((b'<<', b'6', b'1', 12), (b'>>', b'6', b'1', 3),
                 (b'<<', b'1', b'63', MIN), (b'>>', b'-3', b'1', -2),
                 (b'>>', str(MIN).encode(), b'63', -1),
                 (b'<<', str(MIN).encode(), b'1', 0))
        for profile in (0, 1):
            for operator, lhs, rhs, want in cases:
                with self.subTest(profile=profile, operator=operator, lhs=lhs, rhs=rhs):
                    wire = independent_wire(operator, profile, lhs, rhs)
                    header, nodes = decode_nqaf(wire)
                    assert_owned_graph(header, nodes)
                    p = self.execute(self.image(wire))
                    self.assertEqual((p.returncode, p.stdout, p.stderr), (want % 256, b'', b''))
                    source = header['source']
                    self.assertEqual(self.ast(source, bool(profile))[0], wire)

    def test_precedence_and_associativity(self):
        cases = ((b'1+2<<3', 24), (b'1<<2+1', 8), (b'16>>1+1', 4),
                 (b'32>>1>>2', 4), (b'1<<2<<3', 32), (b'64>>2<<1', 32),
                 (b'2<<1*2', 8), (b'16/2>>1', 4), (b'-3>>1', -2),
                 (b'~0>>63', -1), (b'not 0<<3', 8), (b'1<<2<5', 1),
                 (b'1<<2==4', 1), (b'2&1<<1', 2), (b'1^1<<2', 5),
                 (b'1|1<<2', 5), (b'2<<1 and 0', 0), (b'0 or 1<<2', 1),
                 (b'(1<<2)+1', 5), (b'(-3)>>(1+0)', -2))
        for profile in (False, True):
            self.value(b'fn main(){'+if_checks(cases)+b'return 1}', profile=profile)
            _, h, nodes = self.ast(b'fn main(){return 64>>2<<1}', profile)
            self.assertEqual((h['version'], h['dialect'], h['runtime_profile']), (10, 9, int(profile)))
            operators = [(i, n) for i, n in enumerate(nodes, 1) if n[0] in (55, 56)]
            self.assertEqual([n[0] for _, n in operators], [56, 55])
            self.assertEqual(operators[1][1][4:7], (operators[0][0], operators[1][0]-1, 0))
            for _, n in operators:
                self.assertEqual((n[1], n[3], n[6]), (0, 2, 0))
                self.assertEqual(h['source'][n[2]:n[2]+2], b'<<' if n[0] == 55 else b'>>')

    def test_all_bits_against_independent_integer_oracle(self):
        # Hand-derived sentinels check the independent arithmetic model itself.
        self.assertEqual(shift_value(-3, 1, b'>>'), -2)
        self.assertEqual(shift_value(MAX, 1, b'<<'), -2)
        self.assertEqual(shift_value(1, 63, b'<<'), MIN)
        self.assertEqual(shift_value(MIN, 1, b'<<'), 0)
        cases = value_cases()
        for profile in (False, True):
            self.value(b'fn main(){'+if_checks(cases)+b'return 1}', profile=profile)

    def test_eager_left_to_right_effects_once(self):
        prefix = (b'fn mark(x,r){byte_store(16+byte_load(0),x)'
                  b'byte_store(0,byte_load(0)+1)return r}fn main(){let v=')
        cases = ((b'mark(65,3)<<mark(66,2)', 12),
                 (b'mark(65,-3)>>mark(66,1)', -2),
                 (b'mark(65,0)<<mark(66,0)', 0),
                 (b'mark(65,0)>>mark(66,63)', 0))
        for profile in (False, True):
            for expression, want in cases:
                source = (prefix+expression+b' if v!=('+str(want).encode()+b'){return 2}'
                          b'if byte_load(0)!=2{return 3}output_write(16,2)return 1}')
                self.value(source, profile=profile, output=b'AB')
            source = (b'fn mark(x,r){byte_store(0,x)output_write(0,1)return r}'
                      b'fn main(){return mark(65,0)<<mark(66,64)}')
            self.runtime_fault(source, source.index(b'<<'), profile, output=b'AB')
            self.value(b'fn main(){let n=input_read(32,1)<<1 '
                       b'if n!=2{return 2}output_write(32,1)return 1}',
                       profile=profile, payload=b'Z', output=b'Z')

    def test_loop_condition_and_nested_calls(self):
        source = (b'fn tick(x){byte_store(0,byte_load(0)+1)return x}'
                  b'fn id(x){return x}fn six(a,b,c,d,e,f){return a+b+c+d+e+f}'
                  b'fn main(){let n=8 let k=0 while tick(n)>>id(1){n=n/2 k=k+1}'
                  b'if k!=3{return 2}if byte_load(0)!=4{return 3}'
                  b'byte_store(0,0)n=1 k=0 while (tick(n)<<id(1))<9{n=n+1 k=k+1}'
                  b'if k!=4{return 4}if byte_load(0)!=5{return 5}'
                  b'if six(id(1)<<id(1),id(16)>>id(2),(-3)>>id(1),'
                  b'id(3)<<id(2),id(1)<<id(0),id(64)>>id(3))!=25{return 6}'
                  b'if ((id(4294967296)<<id(1))>>id(32))!=2{return 7}return 1}')
        for profile in (False, True):
            self.value(source, profile=profile)

    def test_invalid_counts_full_i64_and_diagnostic(self):
        invalid = (64, 65, 127, 128, 255, 256, 4294967296, 4294967297,
                   1099511627776, 4611686018427387904, MAX, -1, -64, -65,
                   -4294967296, MIN)
        for profile in (False, True):
            for operator in (b'<<', b'>>'):
                for count in invalid:
                    source = b'fn main(){return 0'+operator+str(count).encode()+b'}'
                    with self.subTest(profile=profile, operator=operator, count=count):
                        self.runtime_fault(source, source.index(operator), profile)
            for expression in (b'1<<f(4294967296)', b'1>>f(-1)', b'1<<(63+1)'):
                source = b'fn f(x){return x}fn main(){return '+expression+b'}'
                anchor = source.index(b'<<') if b'<<' in source else source.index(b'>>')
                self.runtime_fault(source, anchor, profile)

    def test_fault_order_and_unselected_paths(self):
        cases = ((b'(1/0)<<64', b'/', 1), (b'1>>(1/0)', b'/', 1),
                 (b'byte_load(-1)<<64', b'byte_load', 4),
                 (b'(1<<64)>>(1/0)', b'<<', 10),
                 (b'(1>>-1)<<(1<<64)', b'>>', 10))
        for profile in (False, True):
            for expression, token, code in cases:
                source = b'fn main(){return '+expression+b'}'
                self.runtime_fault(source, source.index(token), profile, code)
            skipped = (b'fn main(){if 0{return 1<<64}while 0{let x=1>>-1}'
                       b'let a=0 and (1<<64)let b=1 or (1>>-1)'
                       b'if a!=0{return 2}if b!=1{return 3}return 1}')
            self.value(skipped, profile=profile)
            for expression in (b'1 and (1<<64)', b'0 or (1>>-1)'):
                source = b'fn main(){return '+expression+b'}'
                token = b'<<' if b'<<' in source else b'>>'
                self.runtime_fault(source, source.index(token), profile)

    def test_static_validation_in_skipped_shifts(self):
        bad = ((b'missing<<1', 3), (b'1>>missing', 3), (b'absent(1)<<1', 8),
               (b'1<<9223372036854775808', 5), (b'9223372036854775808>>1', 5))
        for profile in (False, True):
            for expression, code in bad:
                for prefix in (b'0 and (', b'1 or ('):
                    source = b'fn main(){return '+prefix+expression+b')}'
                    with self.subTest(expression=expression, profile=profile, prefix=prefix):
                        self.reject_wire(self.ast(source, profile)[0], code)
            self.reject_wire(self.ast(b'fn f(x){return x}fn main(){return 0 and (f(1,2)<<1)}', profile)[0])
            self.reject_source(b'fn main(){return 0 and (1<<byte_address(0,0))}', profile, b'C0S-001')
            for skipped in (False, True):
                wire = independent_unsafe_shift(int(profile), skipped)
                h, n = decode_nqaf(wire)
                assert_owned_graph(h, n)
                self.reject_wire(wire, 10)
            self.value(b'fn main(){unsafe {# safety: inspect only this arena address\n'
                       b'let a=byte_address(0,0)>>0 if a==0{return 2}return 1}}', profile=profile)

    def test_minimum_literal_permission_is_negate_only(self):
        cases = ((b'(-9223372036854775808)>>0', MIN),
                 (b'(-9223372036854775808)>>63', -1), (b'1<<63', MIN),
                 (b'(-9223372036854775808)<<1', 0))
        for profile in (False, True):
            self.value(b'fn main(){'+if_checks(cases)+b'return 1}', profile=profile)
            for expression in (b'9223372036854775808<<0', b'1<<9223372036854775808',
                               b'-(9223372036854775808>>0)', b'~9223372036854775808<<0',
                               b'1<<9223372036854775809'):
                self.reject_wire(self.ast(b'fn main(){return '+expression+b'}', profile)[0], 5)
            self.reject_wire(independent_wire(b'<<', int(profile), b'9223372036854775808', b'0'), 5)
            source = b'fn main(){return --9223372036854775808<<0}'
            self.runtime_fault(source, source.index(b'--'), profile, 1)

    def test_malformed_source_and_maximal_munch(self):
        malformed = (b'<<1', b'>>1', b'1<<', b'1>>', b'1<<<2', b'1>>>2',
                     b'1<<=2', b'1>>=2', b'1 < < 2', b'1 > > 2',
                     b'1< <2', b'1> >2', b'1<\n<2', b'1>\n>2',
                     b'1<<*2', b'1>>/2', b'1<<>>2', b'1>><<2', b'1<<<<2')
        for profile in (False, True):
            for expression in malformed:
                with self.subTest(expression=expression, profile=profile):
                    self.reject_source(b'fn main(){return '+expression+b'}', profile)
            for expression, want in ((b'1<<2', 4), (b'8>>2', 2),
                                     (b'1<<-0', 1), (b'8 >> (1)', 4)):
                self.value(b'fn main(){if ('+expression+b')!='+str(want).encode()+
                           b'{return 2}return 1}', profile=profile)
            self.reject_source(b'fn main(){let a=1 a<<=2 return a}', profile)
            self.reject_source(b'fn main(){let a=1 a>>=2 return a}', profile)

    def test_malformed_wire_anchors_and_fields(self):
        for operator in (b'<<', b'>>'):
            wire = independent_wire(operator)
            h, nodes = decode_nqaf(wire)
            shift = next(i for i, n in enumerate(nodes, 1) if n[0] in (55, 56))
            changes = ((1, 1), (2, 1), (4, 0), (4, h['source_length']),
                       (4, 65536), (8, 0), (8, 1), (8, 3), (8, 4294967295),
                       (12, 0), (16, 0), (20, 1), (24, 1), (28, 1),
                       (0, 56 if operator == b'<<' else 55))
            for field, value in changes:
                with self.subTest(operator=operator, field=field, value=value):
                    self.reject_wire(change_node(wire, shift, field, value))
            for source in (b'fn main(){return 6< 1}', b'fn main(){return 6> 1}',
                           b'fn main(){return 6<>1}', b'fn main(){return 6><1}'):
                self.reject_wire(pack_wire(source, nodes), 6)
            # A wide source offset is genuine; truncating its anchor is not valid.
            pad = 70000
            shifted = [(k, f, o+pad, n, l, r, x) for k, f, o, n, l, r, x in nodes]
            wide = pack_wire(b' '*pad+h['source'], shifted)
            p = self.execute(self.image(wide))
            self.assertEqual((p.returncode, p.stdout, p.stderr),
                             (12 if operator == b'<<' else 3, b'', b''))
            self.reject_wire(change_node(wide, shift, 4, (nodes[shift-1][2]+pad) % 65536), 6)

    def test_malformed_wire_topology_and_truncation(self):
        for operator in (b'<<', b'>>'):
            wire = independent_wire(operator)
            mutations = ((12, 4), (12, 7), (12, 65536), (12, 4294967295),
                         (16, 2), (16, 4), (16, 7), (20, 2))
            for field, value in mutations:
                with self.subTest(operator=operator, field=field, value=value):
                    self.reject_wire(change_node(wire, 4, field, value), 2)
            # Still connected and uniquely owned, but RHS/LHS physical order swapped.
            swapped = change_node(change_node(wire, 4, 12, 3), 4, 16, 2)
            h, n = decode_nqaf(swapped)
            assert_owned_graph(h, n)
            self.reject_wire(swapped, 2)
            for size in (0, 4, 15, 31, 32, 33, len(wire)-33, len(wire)-1):
                self.reject_wire(wire[:size], 1)
            self.reject_wire(wire+b'\0', 1)
            for at, value in ((8, 0), (8, 262145), (12, 0), (12, 65537),
                              (16, 0), (16, 6), (20, 0), (20, 65537)):
                bad = bytearray(wire)
                struct.pack_into('<I', bad, at, value)
                self.reject_wire(bad)

    def test_version_dialect_profile_and_logical_compatibility(self):
        wire = independent_wire()
        h, n = decode_nqaf(wire)
        for operator in (b'<<', b'>>'):
            legacy_header, legacy_nodes = decode_nqaf(independent_wire(operator))
            for version in range(5, 10):
                with self.subTest(operator=operator, version=version):
                    self.reject_wire(pack_wire(legacy_header['source'], legacy_nodes,
                                               version=version,
                                               dialect=4 if version == 5 else version-1), 2)
        # Narrow scalar envelope isolates /1..4 new-kind rejection.
        scalar = [(5, 0, 17, 1, 0, 0, 0), (5, 0, 20, 1, 0, 0, 0),
                  (55, 0, 18, 2, 1, 2, 0), (33, 0, 0, 2, 3, 0, 0)]
        for version in range(1, 5):
            self.reject_wire(pack_wire(h['source'], scalar, version=version), 2)
            sar = [(*node,) for node in scalar]
            sar[2] = (56, 0, 18, 2, 1, 2, 0)
            self.reject_wire(pack_wire(h['source'].replace(b'<<', b'>>'), sar, version=version), 2)
        for at, data in ((4, b'\x0b'), (5, b'\x10'), (6, b'\x01'),
                         (24, b'\x08'), (24, b'\x0a'), (25, b'\x02'),
                         (26, b'\x01'), (28, b'\x01')):
            bad = bytearray(wire)
            bad[at:at+len(data)] = data
            self.reject_wire(bad, 1)
        for profile in (False, True):
            for old in (b'fn main(){return 7}# << >>', b'fn main(){return 1<2}',
                        b'fn main(){return 2>1}', b'fn main(){return not 0 and 1}'):
                self.assertLess(self.ast(old, profile)[1]['version'], 10)
            source = b'fn main(){return not 0 and 1<<1 or 0}'
            _, header, nodes = self.ast(source, profile)
            self.assertEqual((header['version'], header['dialect'], header['runtime_profile']), (10, 9, int(profile)))
            self.assertEqual({k for k, *_ in nodes if k >= 52}, {52, 53, 54, 55})
            self.value(source, profile=profile)
            for operator in (b'and', b'or', b'not'):
                old = bytearray(logical_wire(operator, int(profile)))
                old[4], old[24] = 10, 9
                p = self.execute(self.image(old))
                self.assertEqual((p.returncode, p.stdout, p.stderr), (0 if operator == b'not' else 1, b'', b''))
            old = bytearray(independent_legacy_identifiers(8, int(profile)))
            old[4], old[24] = 10, 9
            self.reject_wire(old)

    def test_legacy_c036_bytes(self):
        ast, elf = hashlib.sha256(), hashlib.sha256()
        versions = set()
        for profile in (False, True):
            for source in LEGACY_C036:
                wire, header, _ = self.ast(source, profile)
                self.assertLess(header['version'], 10)
                versions.add(header['version'])
                image = self.image(wire)
                self.assertNotIn(FAULT_SUFFIX, image)
                ast.update(wire)
                elf.update(image)
        self.assertEqual(versions, set(range(1, 10)))
        self.assertEqual(ast.hexdigest(), LEGACY_C036_AST)
        self.assertEqual(elf.hexdigest(), LEGACY_C036_ELF)

    def test_exact_machine_bytes_and_sensitivity(self):
        load = bytes.fromhex('488b85f8ffffff')
        rhs = bytes.fromhex('488b8df0ffffff')
        store = bytes.fromhex('488985f8ffffff')
        rhs_store = bytes.fromhex('488985f0ffffff')
        prologue = bytes.fromhex('554889e54881ec0010000041ffc7')
        following = load+bytes.fromhex('41ffcfc9c3')
        for profile in (0, 1):
            for operator, instruction, wrong, want in (
                    (b'<<', '48d3e0', '48d3f8', 12),
                    (b'>>', '48d3f8', '48d3e0', 3)):
                wire = independent_wire(operator, profile)
                image = self.image(wire)
                self.assertEqual(image, self.image(wire))
                entry = struct.unpack_from('<Q', image, 24)[0]-0x400000
                call = image.index(bytes.fromhex('4531ffe8'), entry, entry+62)+3
                main = call+5+struct.unpack_from('<i', image, call+1)[0]
                literals = (bytes.fromhex('48b8')+struct.pack('<q', 6)+store+
                            bytes.fromhex('48b8')+struct.pack('<q', 1)+rhs_store)
                prefix = b'input:1:19: '
                self.assertEqual(image.count(prefix), 1)
                location = image.index(prefix)
                located = bytes.fromhex('41b8')+struct.pack('<I', 0x400000+location)
                located += bytes.fromhex('41b9')+struct.pack('<I', len(prefix))
                before_ja = load+rhs+located+bytes.fromhex('4883f93f')
                branch = main+len(prologue)+len(literals)+len(before_ja)
                ja = bytes.fromhex('0f87')+struct.pack('<i', 6294400-(branch+6))
                shift = before_ja+ja+bytes.fromhex(instruction)+store
                self.assertEqual(len(shift), 46)
                body = prologue+literals+shift+following
                self.assertEqual(image[main:main+len(body)], body)
                self.assertEqual(image[main+len(body):main+len(body)+8], bytes(8))
                self.assertEqual(image[6294592:6294592+len(FAULT_SUFFIX)], FAULT_SUFFIX)
                self.assertEqual(self.image(self.ast(decode_nqaf(wire)[0]['source'], bool(profile))[0]), image)
                # An equal-length wrong opcode in a private image must be observable.
                changed = bytearray(image)
                at = branch+6
                changed[at:at+3] = bytes.fromhex(wrong)
                self.assertEqual(len(changed), len(image))
                result = self.execute(changed)
                actual = (result.returncode, result.stdout, result.stderr)
                expected = (3 if operator == b'<<' else 12, b'', b'')
                if actual != expected:
                    self.retain_failure('single-opcode-mutation', wire=wire, image=changed,
                                        original_image=image, stdout=result.stdout,
                                        stderr=result.stderr, returncode=result.returncode,
                                        expected=expected, operator=operator)
                self.assertEqual(actual, expected)

    def test_generation_shift_contract(self):
        # Selected by this exact name on actual B/C pairs via C0_* env paths.
        for profile in (False, True):
            self.value(generation_source(), profile=profile, output=b'A')
            for operator in (b'<<', b'>>'):
                self.image(independent_wire(operator, int(profile)))
                for count in (64, -1, 4294967296, MIN):
                    source = b'fn main(){return 1'+operator+str(count).encode()+b'}'
                    self.runtime_fault(source, source.index(operator), profile)
            self.reject_wire(independent_unsafe_shift(int(profile), True), 10)
            self.reject_wire(independent_wire(b'<<', int(profile), b'9223372036854775808', b'0'), 5)
        self.check_wrongcode_sensitivity()

    def check_wrongcode_sensitivity(self):
        for profile in (False, True):
            source = generation_source()
            wire = self.ast(source, profile)[0]
            image = self.image(wire)
            # Locate actual shift sites by the complete CMP64/JA/opcode sequence.
            marker = bytes.fromhex('4883f93f0f87')
            sites = []
            start = 0
            while True:
                at = image.find(marker, start)
                if at < 0:
                    break
                opcode = image[at+10:at+13]
                if opcode in (bytes.fromhex('48d3e0'), bytes.fromhex('48d3f8')):
                    sites.append((at, opcode))
                start = at+1
            self.assertGreater(len(sites), 10)
            for label, original, replacement, status in (
                    ('shl-to-sar', '48d3e0', '48d3f8', 2),
                    ('sar-to-shr', '48d3f8', '48d3e8', 7)):
                changed = bytearray(image)
                matches = [at for at, opcode in sites if opcode == bytes.fromhex(original)]
                self.assertTrue(matches, label)
                for at in matches:
                    changed[at+10:at+13] = bytes.fromhex(replacement)
                self.assertEqual(len(changed), len(image))
                result = self.execute(changed)
                actual = (result.returncode, result.stdout, result.stderr)
                expected = (status, b'', b'')
                if actual != expected:
                    self.retain_failure(label, source=source, wire=wire, image=changed,
                                        original_image=image, stdout=result.stdout,
                                        stderr=result.stderr, returncode=result.returncode,
                                        expected=expected)
                self.assertEqual(actual, expected, label)
            # Full-width and unsigned guards need separate negative controls:
            # low32(2**32) == 0, and signed(-1) <= 63 both falsely admit counts.
            for count, replacement, status in (
                    (4294967296, bytes.fromhex('4083f93f0f87'), 1),
                    (-1, bytes.fromhex('4883f93f0f8f'), 0)):
                source = b'fn main(){return 1<<'+str(count).encode()+b'}'
                wire = self.ast(source, profile)[0]
                original = self.image(wire)
                p = self.execute(original)
                expected_fault = (70, b'', fault_message(source, source.index(b'<<')))
                if (p.returncode, p.stdout, p.stderr) != expected_fault:
                    self.retain_failure('guard-original', source=source, wire=wire,
                                        image=original, stdout=p.stdout, stderr=p.stderr,
                                        returncode=p.returncode, expected=expected_fault)
                self.assertEqual((p.returncode, p.stdout, p.stderr), expected_fault)
                self.assertEqual(original.count(marker), 1)
                changed = original.replace(marker, replacement, 1)
                self.assertEqual(len(changed), len(original))
                p = self.execute(changed)
                actual = (p.returncode, p.stdout, p.stderr)
                expected = (status, b'', b'')
                if actual != expected:
                    self.retain_failure('guard-mutation', source=source, wire=wire,
                                        image=changed, original_image=original,
                                        stdout=p.stdout, stderr=p.stderr,
                                        returncode=p.returncode, expected=expected)
                self.assertEqual(actual, expected, count)

    def test_generation_wrongcode_sensitivity(self):
        self.check_wrongcode_sensitivity()

    def test_located_diagnostic_and_write_failure(self):
        sources = (b'fn main(){\n return 3 << 64\n}',
                   b'#'+b'x'*70000+b'\nfn main(){\nreturn -3 >> -1}',
                   b'fn main(){let n=0 while n<2{n=n+1 if n==2{return 1<<64}}return 0}')
        for profile in (False, True):
            for source in sources:
                token = b'<<' if b'<<' in source else b'>>'
                anchor = source.index(token)
                self.runtime_fault(source, anchor, profile)
                image = self.image(self.ast(source, profile)[0])
                failed_write = self.execute(image, bad_stderr=True)
                self.assertEqual((failed_write.returncode, failed_write.stdout), (74, b''))


if __name__ == '__main__':
    unittest.main()
