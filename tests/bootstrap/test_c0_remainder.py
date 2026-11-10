"""C0.38 checked signed remainder: independent values, wire, effects and x86.

B0 builds the compilers. Python integers supply a truncation oracle, never a
float quotient or Python's divisor-signed modulo. Guest assertions use ordinary
if statements and compare complete i64 values before returning a test status.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import resource
import signal
import struct
import tempfile
import unittest

from c031_support import (assert_owned_graph, candidate_binary, decode_nqaf,
                         encode_profile_source, run_native)

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
MIN, MAX = -9223372036854775808, 9223372036854775807
# Frozen from the unchanged qualified C037 ROOT pair before C038 source/pins.
# Profile is outermost, fixture order below is literal. Private freeze receipts
# retain both seed/input identities and each stream hash, not candidate wants.
LEGACY_C037 = (
    b'fn main(){return 7}',
    b'fn main(){if 1{return 7}else{return 9}return 0}',
    b'fn main(){let n=3 while n{n=n-1}return n}',
    b'fn f(a,b){return a+b}fn main(){return f(2,3)}',
    b'fn main(){byte_store(0,65)output_write(0,1)return byte_load(0)}',
    b'fn main(){unsafe {# safety: inspect only the owned arena\nreturn byte_address(0,0)!=0}}',
    b'fn main(){return -9223372036854775808}',
    b'fn main(){return (~(-9223372036854775808))^3|1}',
    b'fn main(){return not 0 and 4294967296 or 0}',
    b'fn main(){return (0 and byte_load(-1))+(1 or 1/0)}',
    b'fn f(x){return not x}fn main(){return f(0) and ~0}',
    b'fn main(){return (4294967296<<1)>>32}',
    b'fn main(){'+b' '*70000+b'return not (7|2)}',
    b'fn main(){return 17/5}# % %% %=\n',
    b'// % %% %=\nfn main(){return -17/-5}',
)
LEGACY_C037_HASHES = (
    ('dc886e9e9d4ff9f2400d6d199b75f38917ef519eca4c6ecc0de5191c9e850e6e',
     'd75b99e2c0d5c105026c6644c31c89e45bf107734b382e079f635021cc844b43'),
    ('b1a1513c25e1d2be34a8d6d2752a613d21deaa817d28614798e5fff62ec01892',
     'b27ac6f4acf1a57d1687f7576e55585815054bee78f05a1c80f90dfdccd4a6d6'),
)


def remainder_value(lhs, rhs):
    """Independent signed integer specification, with the checked quotient rule."""
    if rhs == 0 or (lhs == MIN and rhs == -1):
        raise ValueError('checked quotient is undefined')
    quotient = abs(lhs) // abs(rhs)
    if (lhs < 0) != (rhs < 0):
        quotient = -quotient
    return lhs - quotient * rhs


def if_checks(cases):
    # A wrong REM/logical result cannot suppress the assertion testing it.
    return b''.join(b'if ('+expression+b')!=('+str(want).encode()+
                    b'){return '+str(2+i % 200).encode()+b'}'
                    for i, (expression, want) in enumerate(cases))


def value_cases():
    values = (MIN, MIN+1, -1099511627793, -4294967297, -17, -1,
              0, 1, 17, 4294967297, 1099511627793, MAX)
    divisors = (MIN, -4294967297, -5, -1, 1, 5, 4294967297, MAX)
    pairs = [(a, b) for a in values for b in divisors if (a, b) != (MIN, -1)]
    rng = random.Random(0xC038)
    for _ in range(32):
        a, b = rng.randint(MIN, MAX), rng.randint(MIN, MAX)
        if b == 0 or (a, b) == (MIN, -1):
            b = 5
        pairs.append((a, b))
    return [(f'({a})%({b})'.encode(), remainder_value(a, b)) for a, b in pairs]


def pack_wire(source, records, profile=0, version=11, dialect=None, tokens=10):
    if version < 5:
        header = struct.pack('<4sBBHHHHH', b'NQAF', version, 16, 0, len(source),
                             len(records), len(records), tokens)
        return header+source+b''.join(struct.pack('<BBHHHHH4s', *n, bytes(4)) for n in records)
    if dialect is None:
        dialect = 4 if version == 5 else version-1
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', version, 32, 0, len(source),
                         len(records), len(records), tokens, dialect, profile, 0, 0)
    return header+source+b''.join(struct.pack('<BBHIIIIIII', k, f, 0, o, n, l, r, x, 0, 0)
                                 for k, f, o, n, l, r, x in records)


def wrap_expression(source, records, root, profile, tokens):
    """Handwritten function/statement envelope, not a frontend output adapter."""
    ret = len(records)+1
    records += [(32, 0, source.index(b'return'), 6, root, 0, ret+1),
                (41, 0, len(source)-1, 1, 0, 0, 0),
                (33, 0, source.index(b'fn'), 2, 1, 0, 0)]
    records[0] = (39, 0, source.index(b'main'), 4, 0, 0, ret)
    return pack_wire(source, records, profile, tokens=tokens)


def independent_wire(profile=0, lhs=b'17', rhs=b'5', operator=b'%'):
    source = b'fn main(){return '+lhs+operator+rhs+b'}'
    records = [(39, 0, 3, 4, 0, 0, 0)]
    def operand(text, offset):
        negative = text.startswith(b'-')
        records.append((5, 0, offset+int(negative), len(text)-int(negative), 0, 0, 0))
        if negative:
            records.append((47, 0, offset, 1, len(records), 0, 0))
        return len(records)
    left = operand(lhs, 17)
    right = operand(rhs, 17+len(lhs)+len(operator))
    records.append(({b'%': 57, b'<<': 55, b'>>': 56}[operator],
                    0, 17+len(lhs), len(operator), left, right, 0))
    return wrap_expression(source, records, len(records), profile,
                           10+int(lhs.startswith(b'-'))+int(rhs.startswith(b'-')))


def mixed_wire(profile=0):
    source = b'fn main(){return (17%5)<<1 and not 0}'
    records = [(39, 0, 3, 4, 0, 0, 0),
               (5, 0, source.index(b'17'), 2, 0, 0, 0),
               (5, 0, source.index(b'5'), 1, 0, 0, 0),
               (57, 0, source.index(b'%'), 1, 2, 3, 0),
               (5, 0, source.index(b'1 and'), 1, 0, 0, 0),
               (55, 0, source.index(b'<<'), 2, 4, 5, 0),
               (5, 0, source.index(b'0}'), 1, 0, 0, 0),
               (54, 0, source.index(b'not'), 3, 7, 0, 0),
               (52, 0, source.index(b'and'), 3, 6, 8, 0)]
    return wrap_expression(source, records, 9, profile, 17)


def unsafe_wire(profile=0, skipped=False):
    expression = b'17%byte_address(0,0)'
    if skipped:
        expression = b'0 and ('+expression+b')'
    source = b'fn main(){return '+expression+b'}'
    records = [(39, 0, 3, 4, 0, 0, 0)]
    if skipped:
        records.append((5, 0, 17, 1, 0, 0, 0))
    records.append((5, 0, source.index(b'17'), 2, 0, 0, 0))
    left = len(records)
    call = source.index(b'byte_address')
    records.append((5, 0, source.index(b'0,', call), 1, 0, 0, 0))
    records.append((43, 0, source.index(b',', call), 1, 0, len(records), 0))
    first = len(records)
    records.append((5, 0, source.index(b'0)', call), 1, 0, 0, 0))
    records.append((43, 0, source.index(b')', call), 1, first, len(records), 0))
    records.append((42, 0, call, 12, len(records), 0, 0))
    records.append((57, 0, source.index(b'%'), 1, left, len(records), 0))
    if skipped:
        records.append((52, 0, source.index(b'and'), 3, 2, len(records), 0))
    return wrap_expression(source, records, len(records), profile, 15+4*int(skipped))


def change_node(wire, node_id, field, value):
    changed = bytearray(wire)
    at = 32+struct.unpack_from('<I', wire, 8)[0]+(node_id-1)*32+field
    if field in (0, 1):
        changed[at] = value
    elif field == 2:
        struct.pack_into('<H', changed, at, value)
    else:
        struct.pack_into('<I', changed, at, value)
    return bytes(changed)


def high_wire(profile=0):
    # The wire contract bounds its declared token count; it is not full source
    # authentication. This independently supplied graph reaches root ID65536,
    # without claiming the frontend could lex that many tokens plus wrappers.
    count = 32764
    source = b' '*70000+b'fn main(){return ~('+b'0+'*count+b'17)%5}'
    first = source.index(b'0+')
    records = [(39, 0, 0, 0, 0, 0, 0)]
    left = 0
    for i in range(count+1):
        records.append((5, 0, first+2*i, 2 if i == count else 1, 0, 0, 0))
        right = len(records)
        if i:
            records.append((15, 0, first+2*i-1, 1, left, right, 0))
        left = len(records)
    records.append((51, 0, source.index(b'~'), 1, left, 0, 0))
    left = len(records)
    records.append((5, 0, len(source)-2, 1, 0, 0, 0))
    records.append((57, 0, source.index(b'%'), 1, left, len(records), 0))
    return wrap_expression(source, records, len(records), profile, 65536)


def generation_source():
    """Small literal oracle selected on actual B/C pairs; status1, stdout b'R'."""
    cases = ((b'17%5', 2), (b'-17%5', -2), (b'17%-5', 2), (b'-17%-5', -2),
             (b'(-9223372036854775808)%1', 0),
             (b'(-9223372036854775808)%(-9223372036854775808)', 0),
             (b'9223372036854775807%(-9223372036854775808)', MAX),
             (b'1099511627793%2199023255552', 1099511627793),
             (b'20%6*3', 6), (b'20/3%4', 2), (b'20%6%3', 2),
             (b'(17%5)<<1', 4), (b'0 and (1%0)', 0),
             (b'1 or ((-9223372036854775808)%-1)', 1))
    return (b'fn tick(x){byte_store(0,byte_load(0)+1)return x}'
            b'fn id(x){return x}'
            b'fn six(a,b,c,d,e,f){return a+b+c+d+e+f}'
            b'fn main(){'+if_checks(cases)+
            b'let n=5 let k=0 while tick(n)%3{n=n-1 k=k+1}'
            b'if k!=2{return 40}if byte_load(0)!=3{return 41}'
            b'if (tick(17)%tick(5))!=2{return 42}'
            b'if byte_load(0)!=5{return 43}'
            b'if six(id(17)%id(5),id(2),id(3),id(4),id(5),id(6))!=22{return 44}'
            b'if six(id(1),id(2),id(3),id(4),id(5),id(17)%id(5))!=17{return 45}'
            b'byte_store(1,82)output_write(1,1)return 1}')


class RemainderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE/'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE/'c0-backend.seed')

    def retain_failure(self, label, **contents):
        # Only failures/explicit sensitivity observations retain large images.
        # A method aborts at its first failed assertion; successful images vanish.
        parent = Path(os.environ.get('C038_FAILURE_DIR',
                                     str(Path(tempfile.gettempdir())/'nql-c038-failures')))
        parent.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix=self._testMethodName+'-'+label+'-', dir=parent))
        for name, content in contents.items():
            if isinstance(content, (bytes, bytearray)):
                (directory/name).write_bytes(content)
            else:
                (directory/name).write_text(str(content)+'\n')
        return directory

    def ast(self, source, profile=False):
        framed = encode_profile_source(source) if profile else source
        result = run_native(self.frontend, framed, timeout=120)
        if (result.returncode, result.stderr) != (0, b''):
            self.retain_failure('frontend', source=source, stdin=framed,
                                stdout=result.stdout, stderr=result.stderr, status=result.returncode)
        # Check compiler status before decoding: old-pair RED is C0P, not a
        # harness decoder exception while the parent adds /11 support.
        self.assertEqual((result.returncode, result.stderr), (0, b''), source[:240])
        header, nodes = decode_nqaf(result.stdout)
        assert_owned_graph(header, nodes)
        self.assertEqual((header['source'], header['runtime_profile']), (source, int(profile)))
        return result.stdout, header, nodes

    def image(self, wire):
        result = run_native(self.backend, wire, timeout=120)
        if (result.returncode, result.stderr, result.stdout[:4]) != (0, b'', b'\x7fELF'):
            self.retain_failure('backend', wire=wire, stdout=result.stdout,
                                stderr=result.stderr, status=result.returncode)
        self.assertEqual((result.returncode, result.stderr), (0, b''))
        self.assertEqual(result.stdout[:4], b'\x7fELF')
        return result.stdout

    def execute(self, image, payload=b'', bad_stderr=False):
        with tempfile.TemporaryDirectory(prefix='c038-remainder-') as name:
            binary = Path(name)/'program'
            binary.write_bytes(image)
            binary.chmod(0o700)
            options = dict(timeout=15, preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CORE, (0, 0)))
            if bad_stderr:
                with open(os.devnull, 'rb') as inaccessible:
                    return run_native(binary, payload, stderr=inaccessible, **options)
            return run_native(binary, payload, **options)

    def value(self, source, profile=False, *, payload=b'', output=b'', status=1):
        wire = self.ast(source, profile)[0]
        image = self.image(wire)
        result = self.execute(image, payload)
        actual, want = (result.returncode, result.stdout, result.stderr), (status, output, b'')
        if actual != want:
            self.retain_failure('runtime', source=source, wire=wire, image=image,
                                stdout=result.stdout, stderr=result.stderr, status=result.returncode, expected=want)
        self.assertEqual(actual, want, source[:240])
        return image

    def fault(self, source, anchor, profile=False, *, code=1, output=b''):
        image = self.image(self.ast(source, profile)[0])
        result = self.execute(image)
        line = source[:anchor].count(b'\n')+1
        column = anchor-source.rfind(b'\n', 0, anchor)
        prefix = f'input:{line}:{column}: error[C0R-{code:03}]:'.encode()
        if (result.returncode, result.stdout) != (70, output) or not result.stderr.startswith(prefix):
            self.retain_failure('fault', source=source, image=image, stdout=result.stdout,
                                stderr=result.stderr, status=result.returncode, expected=prefix)
        self.assertEqual((result.returncode, result.stdout), (70, output))
        self.assertTrue(result.stderr.startswith(prefix), (result.stderr, prefix))
        self.assertRegex(result.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0R-\d{3}\]: .+; .+\n$')
        return image

    def reject_wire(self, wire, code=None):
        result = run_native(self.backend, wire, timeout=120)
        good = (result.returncode, result.stdout) == (1, b'')
        if not good or (code is not None and f'[C0B-{code:03}]'.encode() not in result.stderr):
            self.retain_failure('rejected-wire', wire=wire, stdout=result.stdout,
                                stderr=result.stderr, status=result.returncode, expected=code)
        self.assertEqual((result.returncode, result.stdout), (1, b''))
        self.assertRegex(result.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$')
        if code is not None:
            self.assertIn(f'[C0B-{code:03}]'.encode(), result.stderr)

    def reject_source(self, source, profile=False, diagnostic=b'C0P-'):
        result = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=120)
        if (result.returncode, result.stdout) != (1, b'') or b'['+diagnostic not in result.stderr:
            self.retain_failure('rejected-source', source=source, stdout=result.stdout,
                                stderr=result.stderr, status=result.returncode)
        self.assertEqual((result.returncode, result.stdout), (1, b''))
        self.assertIn(b'['+diagnostic, result.stderr)

    def test_signed_full_width_values(self):
        # Returning quotient, floor-modulo, or EDX instead of RDX breaks this.
        sentinels = ((17, 5, 2), (-17, 5, -2), (17, -5, 2), (-17, -5, -2),
                     (MIN, 1, 0), (MIN, MIN, 0), (MAX, MIN, MAX), (-1, MIN, -1),
                     (1099511627793, 2199023255552, 1099511627793))
        for a, b, want in sentinels:
            self.assertEqual(remainder_value(a, b), want)
        for a, b in ((0, 0), (MIN, -1)):
            with self.assertRaises(ValueError):
                remainder_value(a, b)
        cases = value_cases()
        for profile in (False, True):
            with self.subTest(profile=profile):
                self.value(b'fn main(){'+if_checks(cases)+b'return 1}', profile)

    def test_precedence_and_left_associativity(self):
        # Equal-precedence right association and wrong prefix/shift rank differ.
        cases = ((b'20%6*3', 6), (b'20/3%4', 2), (b'20%6%3', 2),
                 (b'20%6/2', 1), (b'20*3%7', 4), (b'21/(8%3)', 10),
                 (b'-17%5', -2), (b'~-17%5', 1), (b'-~17%5', 3),
                 (b'not 0%2', 1), (b'(17%5)+3', 5), (b'1+17%5', 3),
                 (b'20%6<<1', 4), (b'32>>17%5', 8),
                 (b'17%5<3', 1), (b'17%5==2', 1), (b'17%5&3', 2),
                 (b'17%5^3', 1), (b'17%5|1', 3),
                 (b'17%5 and 0', 0), (b'0 or 17%5', 1))
        for profile in (False, True):
            self.value(b'fn main(){'+if_checks(cases)+b'return 1}', profile)
            _, header, nodes = self.ast(b'fn main(){return 20%6%3}', profile)
            self.assertEqual((header['version'], header['dialect']), (11, 10))
            rems = [(i, n) for i, n in enumerate(nodes, 1) if n[0] == 57]
            self.assertEqual(len(rems), 2)
            self.assertEqual(rems[1][1][4:7], (rems[0][0], rems[1][0]-1, 0))

    def test_eager_effects_and_fault_order(self):
        # Eliding/repeating/reordering an operand changes the separate AB trace.
        prefix = (b'fn mark(x,r){byte_store(16+byte_load(0),x)'
                  b'byte_store(0,byte_load(0)+1)return r}fn main(){let v=')
        for profile in (False, True):
            for expression, want in ((b'mark(65,17)%mark(66,5)', 2),
                                     (b'mark(65,-17)%mark(66,5)', -2),
                                     (b'mark(65,0)%mark(66,5)', 0)):
                source = (prefix+expression+b' if v!=('+str(want).encode()+b'){return 2}'
                          b'if byte_load(0)!=2{return 3}output_write(16,2)return 1}')
                self.value(source, profile, output=b'AB')
            for expression, token, code in ((b'(1/0)%(1%0)', b'/', 1),
                    (b'17%(1/0)', b'/', 1), (b'(1%0)%(1/0)', b'%', 1),
                    (b'byte_load(-1)%(1%0)', b'byte_load', 4)):
                source = b'fn main(){return '+expression+b'}'
                self.fault(source, source.index(token), profile, code=code)
            source = (b'fn emit(x,r){byte_store(0,x)output_write(0,1)return r}'
                      b'fn main(){return emit(65,17)%emit(66,0)}')
            self.fault(source, source.index(b'%'), profile, output=b'AB')
            self.value(b'fn main(){let n=input_read(32,1)%2 if n!=1{return 2}'
                       b'output_write(32,1)return 1}', profile, payload=b'Z', output=b'Z')

    def test_loop_conditions_nested_calls_and_live_arguments(self):
        # A back-edge to only the final REM loads misses tick/local reevaluation.
        source = (b'fn tick(x){byte_store(0,byte_load(0)+1)return x}'
                  b'fn zero(){return byte_load(2)}fn id(x){return x}'
                  b'fn down(n){if n==0{return 17}return down(n-1)%7}'
                  b'fn six(a,b,c,d,e,f){return a+b+c+d+e+f}'
                  b'fn main(){let n=5 let k=0 while tick(n)%3{n=n-1 k=k+1}'
                  b'if k!=2{return 2}if byte_load(0)!=3{return 3}'
                  b'byte_store(2,5)k=0 while (zero()%3)+0{'
                  b'byte_store(2,byte_load(2)-1)k=k+1}if k!=2{return 4}'
                  b'if six(id(17)%id(5),2,3,4,5,6)!=22{return 5}'
                  b'if six(1,2,3,4,5,id(17)%id(5))!=17{return 6}'
                  b'if down(3)!=3{return 7}'
                  b'if ((id(1099511627793)%id(2199023255552))%id(97))!=53{return 8}'
                  b'return 1}')
        for profile in (False, True):
            self.value(source, profile)

    def test_checked_fault_locations_and_failed_stderr(self):
        # Missing zero/MIN guards trap; lost prefix or R14 breaks located cleanup.
        cases = (b'fn main(){\nreturn 17%0\n}',
                 b'fn main(){return (-9223372036854775808)%-1}',
                 b'fn id(x){return x}fn main(){return id(17)%id(0)}',
                 b'fn id(x){return x}fn main(){return id(-9223372036854775808)%id(-1)}',
                 b'#'+b'x'*70000+b'\nfn main(){\nreturn 1 % 0}')
        for profile in (False, True):
            for source in cases:
                image = self.fault(source, source.index(b'%'), profile)
                failed = self.execute(image, bad_stderr=True)
                self.assertEqual((failed.returncode, failed.stdout), (74, b''))
        # Header profile1 alone is insufficient: resolve a real arena intrinsic.
        import test_c0_compiler_profile as profile_oracle
        from c031_debugger import Guest
        oracle = profile_oracle.CompilerProfileTests(methodName='runTest')
        for expression in (b'17%0', b'(-9223372036854775808)%-1'):
            source = b'fn main(){byte_store(65536,42)return '+expression+b'}'
            image = self.image(self.ast(source, True)[0])
            with tempfile.TemporaryDirectory(prefix='c038-mapped-') as name:
                binary = Path(name)/'program'
                binary.write_bytes(image)
                binary.chmod(0o700)
                sites = oracle.sites(binary)
                with Guest(binary) as guest:
                    base = oracle.acquire(guest, sites)
                    actual = oracle.cleanup(guest, sites, 70, base=base)
                    self.assertEqual(actual[:2], (70, b''))
                    self.assertIn(b'[C0R-001]', actual[2])
                # Synthetic failed-write injection at the real guest syscall;
                # distinct from the actual read-only fd2 checks above.
                with Guest(binary) as guest:
                    base = oracle.acquire(guest, sites)
                    guest.bp(sites['diagnose'])
                    guest.until(sites['diagnose'])
                    guest.inject(-9)
                    guest.bp(sites['diagnose'], False)
                    self.assertEqual(oracle.cleanup(guest, sites, 74, base=base), (74, b'', b''))

    def test_skipped_runtime_and_static_validation(self):
        # Runtime skip never exempts name, arity, MIN or unsafe validation.
        source = (b'fn main(){if 0{return 17%0}while 0{let x=(-9223372036854775808)%-1}'
                  b'let a=0 and (17%0)let b=1 or ((-9223372036854775808)%-1)'
                  b'if a!=0{return 2}if b!=1{return 3}'
                  b'if ((17%5)<<1 and not 0)!=1{return 4}return 1}')
        for profile in (False, True):
            self.value(source, profile)
            for expression in (b'1 and (17%0)', b'0 or ((-9223372036854775808)%-1)'):
                selected = b'fn main(){return '+expression+b'}'
                self.fault(selected, selected.index(b'%'), profile)
            for expression, code in ((b'missing%5', 3), (b'17%absent(1)', 8),
                                     (b'9223372036854775808%5', 5)):
                for prefix in (b'0 and (', b'1 or ('):
                    self.reject_wire(self.ast(b'fn main(){return '+prefix+expression+b')}', profile)[0], code)
            self.reject_wire(self.ast(b'fn f(x){return x}fn main(){return 0 and (17%f(1,2))}', profile)[0])
            self.reject_source(b'fn main(){return 0 and (17%byte_address(0,0))}', profile, b'C0S-001')
            self.reject_wire(unsafe_wire(int(profile), skipped=True), 10)

    def test_minimum_literal_ownership_and_native_ranges(self):
        # REM cannot confer NEGATE's magnitude permission or raw-call authority.
        for profile in (False, True):
            cases = ((b'(-9223372036854775808)%1', 0),
                     (b'(-9223372036854775808)%(-9223372036854775808)', 0),
                     (b'17%(-9223372036854775808)', 17))
            self.value(b'fn main(){'+if_checks(cases)+b'return 1}', profile)
            for expression in (b'9223372036854775808%1', b'1%9223372036854775808',
                               b'-(9223372036854775808%1)', b'17%9223372036854775809'):
                self.reject_wire(self.ast(b'fn main(){return '+expression+b'}', profile)[0], 5)
            self.reject_wire(independent_wire(int(profile), lhs=b'9223372036854775808', rhs=b'1'), 5)
            self.reject_wire(unsafe_wire(int(profile)), 10)
            self.value(b'fn f(a,b){return a+b}fn main(){if (-f(1,2)%2)!=-1{return 2}return 1}', profile)
            self.value(b'fn byte_address(a,b){return a+b}fn main(){if (byte_address(17,0)%5)!=2{return 2}return 1}', profile)
            self.value(b'fn main(){unsafe {# safety: compare only an owned empty arena span\n'
                       b'let p=byte_address(0,0)if (p%1)!=0{return 2}return 1}}', profile)
            source = b'fn main(){return 17%byte_load(-1)}'
            self.fault(source, source.index(b'byte_load'), profile, code=4)

    def test_percent_lexer_and_format_selection(self):
        # A comment-only percent must not select /11 or disturb old token spans.
        for profile in (False, True):
            for source in (b'fn main(){return 7}# % %% %=\n',
                           b'// % %% %=\nfn main(){return 7}'):
                self.assertLess(self.ast(source, profile)[1]['version'], 11)
            for expression in (b'%1', b'1%', b'1%%2', b'1%=2', b'1%*2', b'1%/2', b'1%+2'):
                self.reject_source(b'fn main(){return '+expression+b'}', profile)
            self.reject_source(b'fn main(){let x=17 x%=5 return x}', profile)
            for expression in (b'17%5', b'17 % (5)', b'17%# text\n5'):
                _, header, nodes = self.ast(b'fn main(){return '+expression+b'}', profile)
                self.assertEqual((header['version'], header['dialect']), (11, 10))
                for node in nodes:
                    if node[0] == 57:
                        self.assertEqual((node[1], node[3], node[6]), (0, 1, 0))
                        self.assertEqual(header['source'][node[2]:node[2]+1], b'%')

    def test_handwritten_wire_versions_profiles_and_mixed_ops(self):
        # Backend acceptance is checked BEFORE decoding: old C037 returns
        # C0B-001, not an unsupported-version exception from the test helper.
        for profile in (0, 1):
            with self.subTest(profile=profile):
                wire = independent_wire(profile)
                image = self.image(wire)
                h, nodes = decode_nqaf(wire)
                assert_owned_graph(h, nodes)
                self.assertEqual((h['version'], h['dialect'], h['runtime_profile']), (11, 10, profile))
                result = self.execute(image)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (2, b'', b''))
                self.assertEqual(self.ast(h['source'], bool(profile))[0], wire)
                for packet, want in ((mixed_wire(profile), 1),
                                     (independent_wire(profile, b'6', b'1', b'<<'), 12)):
                    result = self.execute(self.image(packet))
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (want, b'', b''))
                for version in range(5, 11):
                    self.reject_wire(pack_wire(h['source'], nodes, profile, version), 2)
                scalar = [(5, 0, 17, 2, 0, 0, 0), (5, 0, 20, 1, 0, 0, 0),
                          (57, 0, 19, 1, 1, 2, 0), (33, 0, 0, 2, 3, 0, 0)]
                for version in range(1, 5):
                    self.reject_wire(pack_wire(h['source'], scalar, version=version), 2)
                for at, value in ((4, 12), (5, 16), (6, 1), (24, 9), (24, 11),
                                  (25, 2), (26, 1), (28, 1)):
                    bad = bytearray(wire)
                    bad[at] = value
                    self.reject_wire(bad, 1)

    def test_wire_framing_anchors_fields_and_ownership(self):
        # A malformed standalone REM must not hide behind frontend validation.
        for profile in (0, 1):
            wire = independent_wire(profile)
            for field, value in ((0, 18), (1, 1), (2, 1), (4, 0), (4, 65536),
                    (4, 4294967295), (8, 0), (8, 2), (8, 4294967295),
                    (12, 0), (12, 4), (12, 7), (12, 65536),
                    (16, 0), (16, 2), (16, 4), (16, 4294967295),
                    (20, 1), (24, 1), (28, 1)):
                with self.subTest(profile=profile, field=field, value=value):
                    self.reject_wire(change_node(wire, 4, field, value))
            swapped = change_node(change_node(wire, 4, 12, 3), 4, 16, 2)
            self.reject_wire(swapped, 2)
            changed = bytearray(wire)
            changed[32+19] = ord('/')
            self.reject_wire(changed, 6)
            for size in (0, 4, 15, 31, 32, 33, len(wire)-33, len(wire)-1):
                self.reject_wire(wire[:size], 1)
            self.reject_wire(wire+b'\0', 1)
            for at, value in ((8, 0), (8, 262145), (12, 0), (12, 65537),
                              (16, 0), (16, 6), (20, 0), (20, 65537)):
                changed = bytearray(wire)
                struct.pack_into('<I', changed, at, value)
                self.reject_wire(changed, 1)
            # Share one expression between two parents in a still bounded packet.
            mixed = mixed_wire(profile)
            self.reject_wire(change_node(mixed, 9, 16, 4), 2)

    def test_high_u32_spans_and_nested_ownership(self):
        # Narrow u16 offsets/IDs or early indirect reads break these real graphs.
        for profile in (0, 1):
            wire = high_wire(profile)
            header, nodes = decode_nqaf(wire)
            assert_owned_graph(header, nodes)
            self.assertEqual((header['node_count'], header['root_id']), (65536, 65536))
            rem = next((i, n) for i, n in enumerate(nodes, 1) if n[0] == 57)
            self.assertGreater(rem[0], 32767)
            self.assertGreater(rem[1][2], 65535)
            result = self.execute(self.image(wire))
            self.assertEqual((result.returncode, result.stdout, result.stderr), (253, b'', b''))
            for field, value in ((12, 65536), (16, 65536), (16, 4294967295)):
                self.reject_wire(change_node(wire, rem[0], field, value), 2)
            self.reject_wire(change_node(wire, rem[0], 4, rem[1][2] % 65536), 6)

    def test_legacy_c037_ast_and_elf_bytes(self):
        # Wants were frozen before implementation; the candidate cannot bless itself.
        versions = set()
        for profile in (False, True):
            ah, eh = hashlib.sha256(), hashlib.sha256()
            for source in LEGACY_C037:
                wire, header, _ = self.ast(source, profile)
                versions.add(header['version'])
                self.assertLessEqual(header['version'], 10)
                ah.update(wire)
                eh.update(self.image(wire))
            self.assertEqual((ah.hexdigest(), eh.hexdigest()), LEGACY_C037_HASHES[int(profile)])
        self.assertEqual(versions, set(range(1, 11)))

    def rem_sites(self, image):
        marker = bytes.fromhex('4883f9ff750c4889c248f7da0f80')
        return [match.start()-26 for match in re.finditer(re.escape(marker), image)
                if 238 <= match.start()-26 < 0x600000
                and image[match.start()+32:match.start()+35] == bytes.fromhex('4889d0')]

    def check_sensitivity(self):
        # Equal-length wrong result instructions are detected by full-i64 ifs.
        for profile in (False, True):
            for expression, want, replacement in (
                    (b'17%5', 2, bytes.fromhex('909090')),
                    (b'1099511627793%2199023255552', 1099511627793, bytes.fromhex('89d090'))):
                source = b'fn main(){if ('+expression+b')!=('+str(want).encode()+b'){return 2}return 1}'
                image = self.value(source, profile)
                sites = self.rem_sites(image)
                self.assertEqual(len(sites), 1)
                changed = bytearray(image)
                changed[sites[0]+58:sites[0]+61] = replacement
                result = self.execute(changed)
                if (result.returncode, result.stdout, result.stderr) != (2, b'', b''):
                    self.retain_failure('undetected-result-mutation', source=source, image=changed,
                                        stdout=result.stdout, stderr=result.stderr, status=result.returncode)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (2, b'', b''))
            for expression, guard in ((b'17%0', 47), (b'(-9223372036854775808)%-1', 38)):
                source = b'fn main(){return '+expression+b'}'
                image = self.fault(source, source.index(b'%'), profile)
                sites = self.rem_sites(image)
                self.assertEqual(len(sites), 1)
                changed = bytearray(image)
                changed[sites[0]+guard:sites[0]+guard+6] = b'\x90'*6
                result = self.execute(changed)
                # Deliberately unguarded hardware fault, finitely supervised and
                # core dumps disabled. This is synthetic sensitivity, not a bug
                # attributed to a passing candidate or historical signal event.
                self.assertIn(result.returncode, (-signal.SIGFPE, 128+signal.SIGFPE))

    def test_exact_machine_bytes_and_wrongcode_sensitivity(self):
        # Wrong register width, guard destination or result slot changes behavior.
        load = bytes.fromhex('488b85f8ffffff488b8df0ffffff')
        store = bytes.fromhex('488985f8ffffff')
        prologue = bytes.fromhex('554889e54881ec0010000041ffc7')
        for profile in (0, 1):
            wire = independent_wire(profile)
            image = self.image(wire)
            prefix = b'input:1:20: '
            self.assertEqual(image.count(prefix), 1)
            location = image.index(prefix)
            sites = self.rem_sites(image)
            self.assertEqual(len(sites), 1)
            start = sites[0]
            located = bytes.fromhex('41b8')+struct.pack('<I', 0x400000+location)
            located += bytes.fromhex('41b9')+struct.pack('<I', len(prefix))
            guard = bytes.fromhex('4883f9ff750c4889c248f7da0f80')+struct.pack('<i', 0x600090-(start+44))
            guard += bytes.fromhex('4885c90f84')+struct.pack('<i', 0x600090-(start+53))
            guard += bytes.fromhex('489948f7f9')
            want = load+located+guard+bytes.fromhex('4889d0')+store
            self.assertEqual(len(want), 68)
            self.assertEqual(image[start:start+68], want)
            self.assertEqual(start+32+image[start+31], start+44)
            self.assertEqual(start+44+struct.unpack_from('<i', image, start+40)[0], 0x600090)
            self.assertEqual(start+53+struct.unpack_from('<i', image, start+49)[0], 0x600090)
            entry = struct.unpack_from('<Q', image, 24)[0]-0x400000
            call = image.index(bytes.fromhex('4531ffe8'), entry, entry+62)+3
            main = call+5+struct.unpack_from('<i', image, call+1)[0]
            literals = (bytes.fromhex('48b8')+struct.pack('<q', 17)+store+
                        bytes.fromhex('48b8')+struct.pack('<q', 5)+bytes.fromhex('488985f0ffffff'))
            following = bytes.fromhex('488b85f8ffffff41ffcfc9c3')
            self.assertEqual(image[main:main+len(prologue+literals+want+following)], prologue+literals+want+following)
            self.assertEqual(image, self.image(wire))
        self.check_sensitivity()

    def test_generation_remainder_contract(self):
        # Exact selector is run with C0_* paths bound to each actual B/C pair.
        for profile in (False, True):
            self.value(generation_source(), profile, output=b'R')
            self.image(independent_wire(int(profile)))
            self.image(mixed_wire(int(profile)))
            for expression in (b'17%0', b'(-9223372036854775808)%-1'):
                source = b'fn main(){return '+expression+b'}'
                self.fault(source, source.index(b'%'), profile)
            self.reject_wire(unsafe_wire(int(profile), skipped=True), 10)
            self.reject_wire(independent_wire(int(profile), lhs=b'9223372036854775808'), 5)
        self.check_sensitivity()


if __name__ == '__main__':
    unittest.main()
