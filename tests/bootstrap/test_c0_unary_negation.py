"""Checked prefix minus and an independent NQAF/7 oracle; B0 builds compilers."""
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from c031_support import candidate_binary, run_native, encode_profile_source, decode_nqaf, assert_owned_graph
from test_c0_return_flow import LEGACY as LEGACY_SOURCES, LEGACY_AST_SHA256, LEGACY_ELF_SHA256

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
MIN = -(1 << 63)
MAX = (1 << 63) - 1


def negative_wire(digits=b'7', profile=0):
    """Build a complete owned unary packet without using the tested frontend."""
    source = b'fn main(){return -' + digits + b'}'
    records = [(39, 0, 3, 4, 0, 0, 4),
               (5, 0, source.index(digits, 18), len(digits), 0, 0, 0),
               (47, 0, source.index(b'-'), 1, 2, 0, 0),
               (32, 0, source.index(b'return'), 6, 3, 0, 5),
               (41, 0, len(source)-1, 1, 0, 0, 0),
               (33, 0, 0, 2, 1, 0, 0)]
    return pack_wire(source, records, profile)


def pack_wire(source, records, profile=0):
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', 7, 32, 0, len(source),
                         len(records), len(records), 9, 6, profile, 0, 0)
    return header + source + b''.join(struct.pack('<BBHIIIIIII', k, f, 0, o, n, l, r, x, 0, 0)
                                     for k, f, o, n, l, r, x in records)


class UnaryNegationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE/'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE/'c0-backend.seed')

    def ast(self, source, profile=False):
        p = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=120)
        self.assertEqual((p.returncode, p.stderr), (0, b''), source[:200])
        header, nodes = decode_nqaf(p.stdout)
        assert_owned_graph(header, nodes)
        return p.stdout, header, nodes

    def image(self, wire):
        p = run_native(self.backend, wire, timeout=120)
        self.assertEqual((p.returncode, p.stderr), (0, b''))
        self.assertEqual(p.stdout[:4], b'\x7fELF')
        return p.stdout

    def execute(self, image, payload=b''):
        with tempfile.TemporaryDirectory(prefix='c034-unary-') as directory:
            p = Path(directory)/'program';p.write_bytes(image);p.chmod(0o700)
            return run_native(p, payload, timeout=10)

    def value(self, source, expected, profile=False, payload=b'', output=b''):
        wire, _, _ = self.ast(source, profile)
        p = self.execute(self.image(wire), payload)
        self.assertEqual((p.returncode, p.stdout, p.stderr), (expected & 255, output, b''), source[:200])

    def reject_wire(self, wire, code=None):
        p = run_native(self.backend, wire, timeout=120)
        self.assertEqual((p.returncode, p.stdout), (1, b''))
        self.assertRegex(p.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$')
        if code is not None:self.assertIn(f'[C0B-{code:03}]'.encode(), p.stderr)

    def test_prefix_precedence_and_right_associativity(self):
        for profile in (False, True):
            for expression, value in ((b'-7', -7), (b'-1', -1), (b'--7', 7), (b'---7', -7),
                    (b'1--2*3', 7), (b'-2*3+10', 4), (b'-(2+3)*4', -20),
                    (b'7/-2', -3), (b'-(7/2)', -3), (b'-0', 0), (b'-2<0', 1)):
                with self.subTest(profile=profile, expression=expression):
                    source=b'fn main(){return '+expression+b'}'
                    self.value(source, value, profile)
                    _, h, nodes=self.ast(source,profile)
                    self.assertEqual((h['version'],h['dialect'],h['runtime_profile']),(7,6,int(profile)))
                    for index,node in enumerate(nodes,1):
                        if node[0]==47:self.assertEqual((h['source'][node[2]:node[2]+node[3]],node[4:]),(b'-',(index-1,0,0)))

    def test_independent_wire_and_literal_minimum(self):
        for profile in (0,1):
            for digits,value in ((b'7',-7),(str(MAX).encode(),-MAX),
                    (str(-MIN).encode(),MIN),(b'000'+str(-MIN).encode(),MIN)):
                with self.subTest(profile=profile,digits=digits):
                    p=self.execute(self.image(negative_wire(digits,profile)))
                    self.assertEqual((p.returncode,p.stdout,p.stderr),(value&255,b'',b''))

    def test_literal_bounds_and_no_extended_positive_escape(self):
        for profile in (False,True):
            for expression in (str(-MIN).encode(),str(-MIN).encode()+b'-1',
                    b'-(1+'+str(-MIN).encode()+b')',b'-9223372036854775809',
                    b'-92233720368547758080',b'-'+b'9'*100):
                with self.subTest(expression=expression,profile=profile):
                    self.reject_wire(self.ast(b'fn main(){return '+expression+b'}',profile)[0],5)
            for expression in (b'-9223372036854775808',b'-(9223372036854775808)',
                    b'-((0009223372036854775808))',b'-9223372036854775808/1'):
                self.value(b'fn main(){return '+expression+b'}',MIN,profile)

    def test_checked_runtime_overflow_and_operator_location(self):
        for profile in (False,True):
            for source in (b'fn main(){return --9223372036854775808}',
                           b'fn main(){let x=-9223372036854775808\nreturn -x}'):
                p=self.execute(self.image(self.ast(source,profile)[0]))
                self.assertEqual((p.returncode,p.stdout),(70,b''))
                line=2 if b'\n' in source else 1
                column=8 if line==2 else 18
                self.assertTrue(p.stderr.startswith(f'input:{line}:{column}: error[C0R-001]:'.encode()),p.stderr)
            self.value(b'fn main(){if 0{return --9223372036854775808}else{return 7}}',7,profile)

    def test_calls_effects_and_loop_condition_start(self):
        source=(b'fn bump(x){byte_store(0,byte_load(0)+1)return x} '
                b'fn main(){let x=3 while -x<0{x=x-1} '
                b'return -bump(-7)+byte_load(0)*10+x}')
        for profile in (False,True):self.value(source,17,profile)
        self.value(b'fn main(){let n=-input_read(32,1)output_write(32,1)return -n}',1,payload=b'Z',output=b'Z')
        self.value(b'fn f(a,b,c,d,e,f){return -a-b-c-d-e-f} fn main(){return -f(1,2,3,4,5,6)}',21)
    def test_call_arity_is_not_literal_metadata(self):
        # Literal-only proof metadata must not confuse a two-argument call's arity.
        for arity in range(7):
            names=b','.join(bytes([97+i]) for i in range(arity))
            total=b'+'.join(bytes([97+i]) for i in range(arity)) or b'7'
            arguments=b','.join(str(i+1).encode() for i in range(arity))
            program=b'fn f('+names+b'){return '+total+b'}fn main(){return -f('+arguments+b')}'
            with self.subTest(arity=arity):self.value(program,-(sum(range(1,arity+1)) if arity else 7))


    def test_unary_retains_native_unsafe_and_bounds_checks(self):
        self.value(b'fn main(){unsafe {# safety: bounded address comparison\nreturn -byte_address(0,0)<0}}',1)
        p=run_native(self.frontend,b'fn main(){return -byte_address(0,0)}')
        self.assertEqual((p.returncode,p.stdout),(1,b''));self.assertIn(b'[C0S-001]',p.stderr)
        image=self.image(self.ast(b'fn main(){return byte_load(-1)}')[0]);p=self.execute(image)
        self.assertEqual((p.returncode,p.stdout),(70,b''));self.assertIn(b'[C0R-004]',p.stderr)

    def test_malformed_prefixes_and_wire_ownership(self):
        for expression in (b'-',b'-)',b'-*7',b'-/7',b'-+7',b'7 - -',b'(-)'):
            p=run_native(self.frontend,b'fn main(){return '+expression+b'}')
            self.assertEqual((p.returncode,p.stdout),(1,b''));self.assertIn(b'[C0P-',p.stderr)
        wire=negative_wire();base=32+len(b'fn main(){return -7}')
        for offset,data in ((base+2*32+12,struct.pack('<I',0)),
                            (base+2*32+16,struct.pack('<I',2)),
                            (base+2*32+12,struct.pack('<I',3)),
                            (base+2*32+8,struct.pack('<I',2)),
                            (base+2*32+4,struct.pack('<I',0)),(4,b'\x06'),(24,b'\x05')):
            bad=bytearray(wire);bad[offset:offset+len(data)]=data
            with self.subTest(offset=offset,data=data):self.reject_wire(bad)

    def test_legacy_c033_bytes_and_bounded_prefix_chain(self):
        ast,elf=hashlib.sha256(),hashlib.sha256()
        for source in LEGACY_SOURCES:
            wire,_,_=self.ast(source);ast.update(wire);elf.update(self.image(wire))
        self.assertEqual(ast.hexdigest(),LEGACY_AST_SHA256);self.assertEqual(elf.hexdigest(),LEGACY_ELF_SHA256)
        self.value(b'fn main(){return '+b'-'*1000+b'7}',7)
        prefix=b'fn main(){return '+b'-'*32764+b'7}'
        wire,h,nodes=self.ast(prefix);self.assertEqual(h['version'],7)
        p=run_native(self.frontend,b'fn main(){return '+b'-'*65536+b'7}',timeout=120)
        self.assertEqual((p.returncode,p.stdout),(1,b''));self.assertIn(b'[C0P-003]',p.stderr)
        self.value(b'fn main(){'+b' '*70000+b'return -7}',-7)

    def test_machine_negation_and_runtime_rejection(self):
        image=self.image(self.ast(b'fn neg(x){return -x}fn main(){return neg(7)}')[0])
        # NEG rax, immediately followed by the overflow-conditional rel32 branch.
        self.assertIn(bytes.fromhex('48f7d80f80'),image)
        self.value(b'fn main(){return -(-9223372036854775807)}',MAX)

    def test_generation_unary_contract(self):
        # Named on each actual B/C pair; includes compiler-rejection and runtime oracles.
        for profile in (False,True):
            self.value(b'fn f(x){if x{return -7}else{return -(-9)}}fn main(){return -f(1)+f(0)}',16,profile)
            self.value(b'fn f(a,b){return a+b}fn main(){return -f(1,2)}',-3,profile)
            self.value(b'fn main(){return -9223372036854775808}',MIN,profile)
            self.reject_wire(self.ast(b'fn main(){return 9223372036854775808}',profile)[0],5)
            p=self.execute(self.image(self.ast(b'fn main(){return --9223372036854775808}',profile)[0]))
            self.assertEqual((p.returncode,p.stdout),(70,b''));self.assertIn(b'[C0R-001]',p.stderr)


if __name__=='__main__':unittest.main()
