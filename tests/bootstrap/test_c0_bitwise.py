"""Independent signed-64 value and NQAF/8 oracles for canonical bitwise operations."""
import hashlib
from pathlib import Path
import random
import struct
import tempfile
import unittest

from c031_support import candidate_binary, run_native, encode_profile_source, decode_nqaf, assert_owned_graph
from test_c0_return_flow import LEGACY, LEGACY_AST_SHA256, LEGACY_ELF_SHA256

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
MIN, MAX = -(1 << 63), (1 << 63) - 1
# Frozen from the qualified C0.34 pair, in profile/source order below.
LEGACY_C034_AST = 'cdcbabb68ca8bb955fa34505c9db3e858a20b54a3c5203382229127f46a813ea'
LEGACY_C034_ELF = '8fe96cad5cfcec9a4365e5fa95485228651a96e6204c647d8445cdb9d8f3d147'
LEGACY_C034 = (
    b'fn main(){return -7}', b'fn main(){return --7}',
    b'fn main(){return -9223372036854775808}',
    b'fn main(){return -(-9223372036854775807)}',
    b'fn f(a,b){return a+b}fn main(){return -f(1,2)}',
    b'fn main(){let x=3 while -x<0{x=x-1}return -x}',
    b'fn main(){unsafe {# safety: compare bounded address only\nreturn -byte_address(0,0)<0}}',
    b'fn main(){'+b' '*70000+b'return -(7/2)}',
)


def pack_wire(source, records, profile=0):
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', 8, 32, 0, len(source),
                         len(records), len(records), 11, 7, profile, 0, 0)
    return header + source + b''.join(struct.pack('<BBHIIIIIII', k, f, 0, o, n, l, r, x, 0, 0)
                                     for k, f, o, n, l, r, x in records)


def independent_wire(operator=b'&', profile=0):
    """Complete hand-built graph; no output from the tested frontend is used."""
    if operator == b'~':
        source = b'fn main(){return ~7}'
        records = [(39,0,3,4,0,0,4), (5,0,18,1,0,0,0),
                   (51,0,17,1,2,0,0), (32,0,10,6,3,0,5),
                   (41,0,len(source)-1,1,0,0,0), (33,0,0,2,1,0,0)]
    else:
        source = b'fn main(){return 6'+operator+b'3}'
        kind = {b'&':48, b'^':49, b'|':50}[operator]
        records = [(39,0,3,4,0,0,5), (5,0,17,1,0,0,0),
                   (5,0,19,1,0,0,0), (kind,0,18,1,2,3,0),
                   (32,0,10,6,4,0,6), (41,0,len(source)-1,1,0,0,0),
                   (33,0,0,2,1,0,0)]
    return pack_wire(source, records, profile)


def value_cases():
    """Finite defined-semantics corpus, versioned by this file and fixed seed."""
    cases = []
    values = [MIN, MIN+1, -4294967297, -256, -1, 0, 1, 255, 4294967296, MAX]
    rng = random.Random(0xC035)
    pairs = [(a, values[(i*3+1) % len(values)]) for i,a in enumerate(values)]
    pairs += [(rng.randint(MIN,MAX), rng.randint(MIN,MAX)) for _ in range(14)]
    for a,b in pairs:
        for op, result in (('&',a&b), ('^',a^b), ('|',a|b)):
            cases.append((f'({a}){op}({b})'.encode(), result))
    cases += [(f'~({a})'.encode(), ~a) for a in values]
    return cases


class BitwiseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE/'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE/'c0-backend.seed')

    def ast(self, source, profile=False):
        p = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=120)
        self.assertEqual((p.returncode,p.stderr), (0,b''), source[:200])
        h,n = decode_nqaf(p.stdout); assert_owned_graph(h,n)
        return p.stdout,h,n

    def image(self, wire):
        p = run_native(self.backend, wire, timeout=120)
        self.assertEqual((p.returncode,p.stderr), (0,b''))
        self.assertEqual(p.stdout[:4],b'\x7fELF')
        return p.stdout

    def execute(self, image, payload=b''):
        with tempfile.TemporaryDirectory(prefix='c035-bitwise-') as directory:
            path=Path(directory)/'program';path.write_bytes(image);path.chmod(0o700)
            return run_native(path,payload,timeout=10)

    def value(self, source, expected, profile=False, payload=b'', output=b''):
        p=self.execute(self.image(self.ast(source,profile)[0]),payload)
        self.assertEqual((p.returncode,p.stdout,p.stderr),(expected&255,output,b''),source[:200])

    def reject_wire(self, wire, code=None):
        p=run_native(self.backend,wire,timeout=120)
        self.assertEqual((p.returncode,p.stdout),(1,b''))
        self.assertRegex(p.stderr,rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$')
        if code is not None:self.assertIn(f'[C0B-{code:03}]'.encode(),p.stderr)

    def test_independent_wire_and_version(self):
        for profile in (0,1):
            for operator,value in ((b'&',2),(b'^',5),(b'|',7),(b'~',-8)):
                with self.subTest(operator=operator,profile=profile):
                    p=self.execute(self.image(independent_wire(operator,profile)))
                    self.assertEqual((p.returncode,p.stdout,p.stderr),(value&255,b'',b''))

    def test_precedence_and_prefix_associativity(self):
        cases=((b'1|2^3&4',3),(b'6&3==2',0),(b'2|1+1',2),
               (b'8^3&1',9),(b'8^3|1',11),(b'7&3*2',6),
               (b'~~7',7),(b'~-7',6),(b'-~7',8),(b'~(2+3)*2',-12),
               (b'1|2<3',1),(b'1^1^1',1),(b'15&7&3',3))
        for profile in (False,True):
            for expression,expected in cases:
                with self.subTest(expression=expression,profile=profile):
                    self.value(b'fn main(){return '+expression+b'}',expected,profile)
                    _,h,n=self.ast(b'fn main(){return '+expression+b'}',profile)
                    self.assertEqual((h['version'],h['dialect'],h['runtime_profile']),(8,7,int(profile)))
                    for index,node in enumerate(n,1):
                        if node[0]==51:self.assertEqual(node[4:],(index-1,0,0))

    def test_all_bits_against_independent_integer_oracle(self):
        cases=value_cases()
        # Compare all 64 bits inside the target; exit-code truncation alone is insufficient.
        body=b''.join(b'if ('+expression+b')!=('+str(expected).encode()+b'){return '+str(i+2).encode()+b'}'
                      for i,(expression,expected) in enumerate(cases))
        source=b'fn main(){'+body+b'return 1}'
        for profile in (False,True):self.value(source,1,profile)

    def test_eager_left_to_right_effects_once(self):
        prefix=(b'fn mark(x){byte_store(0,byte_load(0)*10+x)return x} '
                b'fn main(){let x=')
        for profile in (False,True):
            for op,result in ((b'&',0),(b'^',3),(b'|',3)):
                source=prefix+b'mark(1)'+op+b'mark(2) return byte_load(0)*10+x}'
                self.value(source,120+result,profile)
            self.value(prefix+b'~mark(1) return byte_load(0)*10-x}',12,profile)
            self.value(b'fn main(){let n=input_read(32,1)&255 output_write(32,n)return n}',1,profile,b'Z',b'Z')

    def test_loop_condition_and_nested_calls(self):
        source=(b'fn inc(x){return x+1}fn f(a,b,c,d,e,f){return a^b|c&d^e|f}'
                b'fn main(){let n=7 let k=0 while n&1{n=n-1 k=inc(k)} '
                b'while ~n!=(-1){n=n-1 k=k+1} return k+f(1,2,3,4,5,6)}')
        for profile in (False,True):self.value(source,14,profile)

    def test_minimum_literal_permission_is_negate_only(self):
        for profile in (False,True):
            self.value(b'fn main(){return (~(-9223372036854775808))==9223372036854775807}',1,profile)
            self.value(b'fn main(){return ((-9223372036854775808)|0)==(-9223372036854775808)}',1,profile)
            for expression in (b'~9223372036854775808',b'-(~9223372036854775808)',
                               b'1|9223372036854775808',b'~9223372036854775809'):
                self.reject_wire(self.ast(b'fn main(){return '+expression+b'}',profile)[0],5)
            p=self.execute(self.image(self.ast(b'fn main(){return -(~9223372036854775807)}',profile)[0]))
            self.assertEqual((p.returncode,p.stdout),(70,b''));self.assertIn(b'[C0R-001]',p.stderr)

    def test_fault_order_and_unselected_paths(self):
        for profile in (False,True):
            self.value(b'fn main(){if 0{return (1/0)|7}else{return ~0}}',-1,profile)
            for expression,column in ((b'(1/0)&(2/0)',20),(b'0&(1/0)',22),(b'~(1/0)',21)):
                p=self.execute(self.image(self.ast(b'fn main(){return '+expression+b'}',profile)[0]))
                self.assertEqual((p.returncode,p.stdout),(70,b''))
                self.assertTrue(p.stderr.startswith(f'input:1:{column}: error[C0R-001]:'.encode()),p.stderr)

    def test_safety_and_range_checks_remain(self):
        # The tested frontend supplies none of this complete /8 call graph.
        source=b'fn main(){return byte_address(0,0)&7}'
        first=source.index(b'0,'); second=source.index(b'0)')
        records=[(39,0,3,4,0,0,9), (5,0,first,1,0,0,0),
                 (43,0,source.index(b','),1,0,2,0), (5,0,second,1,0,0,0),
                 (43,0,source.index(b')',second),1,3,4,0),
                 (42,0,17,12,5,0,0), (5,0,source.index(b'7'),1,0,0,0),
                 (48,0,source.index(b'&'),1,6,7,0), (32,0,10,6,8,0,10),
                 (41,0,len(source)-1,1,0,0,0), (33,0,0,2,1,0,0)]
        for profile in (0,1):self.reject_wire(pack_wire(source,records,profile),10)
        self.value(b'fn main(){unsafe {# safety: inspect only the bounded arena address\nreturn (byte_address(0,0)&7)==0}}',1)
        p=run_native(self.frontend,b'fn main(){return byte_address(0,0)&7}')
        self.assertEqual((p.returncode,p.stdout),(1,b''));self.assertIn(b'[C0S-001]',p.stderr)
        p=self.execute(self.image(self.ast(b'fn main(){return byte_load(~0)}')[0]))
        self.assertEqual((p.returncode,p.stdout),(70,b''));self.assertIn(b'[C0R-004]',p.stderr)

    def test_malformed_source_and_wire(self):
        for expression in (b'~',b'&7',b'7|',b'7^^2',b'7&&2',b'7||2',b'7~2',b'~*7'):
            p=run_native(self.frontend,b'fn main(){return '+expression+b'}')
            self.assertEqual((p.returncode,p.stdout),(1,b''));self.assertIn(b'[C0P-',p.stderr)
        # C0.37 deliberately adds these former unsupported inputs. Preserve
        # their cases as real runtime assertions rather than deleting coverage.
        for expression, expected in ((b'7<<1', 14), (b'7>>1', 3)):
            result = self.execute(self.image(self.ast(b'fn main(){return '+expression+b'}')[0]))
            self.assertEqual((result.returncode, result.stdout, result.stderr), (expected, b'', b''))
        for operator in (b'&',b'^',b'|',b'~'):
            wire=independent_wire(operator);base=32+struct.unpack_from('<I',wire,8)[0]
            node=2 if operator==b'~' else 3;offset=base+node*32
            changes=[(4,b'\x07'),(24,b'\x06'),(25,b'\x02'),(26,b'\x01'),
                     (offset+1,b'\x01'),(offset+4,struct.pack('<I',0)),
                     (offset+8,struct.pack('<I',2)),(offset+12,struct.pack('<I',0)),
                     (offset+20,struct.pack('<I',1)),(offset+28,b'\x01')]
            changes += [(offset+16,struct.pack('<I',2 if operator==b'~' else 0)),
                        (offset+12,struct.pack('<I',node+1))]
            for at,data in changes:
                bad=bytearray(wire);bad[at:at+len(data)]=data
                with self.subTest(operator=operator,offset=at):self.reject_wire(bad)
            for length in (0,4,31,len(wire)-1):self.reject_wire(wire[:length])
            self.reject_wire(wire+b'\0')

    def test_legacy_bytes_and_bounded_prefix_progress(self):
        ast,elf=hashlib.sha256(),hashlib.sha256()
        for source in LEGACY:
            wire,_,_=self.ast(source);ast.update(wire);elf.update(self.image(wire))
        self.assertEqual(ast.hexdigest(),LEGACY_AST_SHA256);self.assertEqual(elf.hexdigest(),LEGACY_ELF_SHA256)
        ast,elf=hashlib.sha256(),hashlib.sha256()
        for profile in (False,True):
            for source in LEGACY_C034:
                wire,_,_=self.ast(source,profile);ast.update(wire);elf.update(self.image(wire))
        self.assertEqual(ast.hexdigest(),LEGACY_C034_AST)
        self.assertEqual(elf.hexdigest(),LEGACY_C034_ELF)
        self.value(b'fn main(){return '+b'~'*1000+b'7}',7)
        self.ast(b'fn main(){return '+b'~'*32764+b'7}')
        p=run_native(self.frontend,b'fn main(){return '+b'~'*65536+b'7}',timeout=120)
        self.assertEqual((p.returncode,p.stdout),(1,b''));self.assertIn(b'[C0P-003]',p.stderr)
        self.value(b'fn main(){'+b' '*70000+b'return ~7}',-8)

    def test_exact_machine_operations_and_determinism(self):
        for op,instruction in ((b'&','4821c8'),(b'^','4831c8'),(b'|','4809c8'),(b'~','48f7d0')):
            wire=self.ast(b'fn main(){return '+(b'~7' if op==b'~' else b'6'+op+b'3')+b'}')[0]
            first=self.image(wire);self.assertEqual(first,self.image(wire))
            load=bytes.fromhex('488b85f8ffffff')
            rhs=bytes.fromhex('488b8df0ffffff') if op!=b'~' else b''
            store=bytes.fromhex('488985f8ffffff')
            sequence=load+rhs+bytes.fromhex(instruction)+store
            self.assertEqual(len(sequence),17 if op==b'~' else 24)
            self.assertEqual(first.count(sequence),1)
            # An immediate return also detects interposed/trailing NOPs.
            following=load+bytes.fromhex('41ffcf c9 c3')
            self.assertIn(sequence+following,first)
            # Independently derive main's entry from the startup call. Check
            # its entire small fixture body, including the operator's start;
            # a leading NOP must not pass a later subsequence search.
            entry=struct.unpack_from('<Q',first,24)[0]-0x400000
            call=first.index(bytes.fromhex('4531ffe8'),entry,entry+62)+3
            main=call+5+struct.unpack_from('<i',first,call+1)[0]
            prologue=bytes.fromhex('554889e54881ec0010000041ffc7')
            literals=bytes.fromhex('48b8')+struct.pack('<q',7 if op==b'~' else 6)+store
            if op!=b'~':
                literals+=bytes.fromhex('48b8')+struct.pack('<q',3)+bytes.fromhex('488985f0ffffff')
            body=prologue+literals+sequence+following
            self.assertEqual(first[main:main+len(body)],body)

    def test_generation_bitwise_contract(self):
        # Selected by name on each actual B/C compiler pair; inspect all 64 bits.
        for profile in (False,True):
            source=(b'fn f(a,b){return (~a)&b}fn main(){let n=3 while n&1{n=n-1}'
                    b'return ((f(-9223372036854775808,9223372036854775807)^3)|2)==9223372036854775806}')
            self.value(source,1,profile)
            self.value(b'fn main(){return (~(-9223372036854775808))==9223372036854775807}',1,profile)
            self.reject_wire(self.ast(b'fn main(){return ~9223372036854775808}',profile)[0],5)
        self.reject_wire(independent_wire().replace(b'\x08\x20',b'\x07\x20',1))


if __name__=='__main__':unittest.main()
