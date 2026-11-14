"""Bottom contracts must not create an inhabited result or bypass validation.

The minimal wire is packed independently. Its expected finite runtime result
is the existing recursion-depth diagnostic, not an infinite-loop timeout.
"""
from pathlib import Path
import random
import struct
import tempfile
import unittest

from c031_support import candidate_binary, run_native, encode_profile_source, decode_nqaf

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'


def recursive_bottom_wire(profile=0):
    source = b'fn halt()->!{halt()}fn main(){halt()}'
    main = source.index(b'main')
    second_call = source.index(b'halt()', main)
    # kind, flags, anchor, length, left, right, next, return span, return length
    rows = [
        (39, 1, 3, 4, 0, 0, 3, 9, 3),
        (42, 0, 13, 4, 0, 0, 0, 0, 0),
        (44, 0, 13, 4, 2, 0, 4, 0, 0),
        (41, 0, 19, 1, 0, 0, 5, 0, 0),
        (39, 0, main, 4, 0, 0, 7, 0, 0),
        (42, 0, second_call, 4, 0, 0, 0, 0, 0),
        (44, 0, second_call, 4, 6, 0, 8, 0, 0),
        (41, 0, len(source)-1, 1, 0, 0, 0, 0, 0),
        (33, 0, 0, 2, 1, 0, 0, 0, 0),
    ]
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', 13, 32, 0,
                         len(source), 9, 9, 23, 12, profile, 0, 0)
    return header + source + b''.join(
        struct.pack('<BBHIIIIIII', k, f, 0, off, size, l, r, n, a, z)
        for k, f, off, size, l, r, n, a, z in rows)


class NeverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = candidate_binary('C0_BACKEND', STAGE/'c0-backend.seed')
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE/'c0-frontend.seed')

    def source_wire(self, source, profile=0):
        result=run_native(self.frontend,source if profile==0 else encode_profile_source(source))
        self.assertEqual((result.returncode,result.stderr),(0,b''))
        self.assertEqual(result.stdout[:5],b'NQAF\x0d')
        return result.stdout

    def compile(self,source,profile=0):
        result=run_native(self.backend,self.source_wire(source,profile))
        self.assertEqual((result.returncode,result.stderr),(0,b''))
        self.assertTrue(result.stdout.startswith(b'\x7fELF'))
        return result.stdout

    def execute(self,binary,**kwargs):
        with tempfile.TemporaryDirectory(prefix='nb-guest-') as name:
            elf=Path(name)/'program';elf.write_bytes(binary);elf.chmod(0o700)
            return run_native(elf,**kwargs)

    def reject(self,source,code=b'C0B-013',profile=0):
        result=run_native(self.backend,self.source_wire(source,profile))
        self.assertEqual((result.returncode,result.stdout),(1,b''))
        self.assertIn(b'error['+code+b']:',result.stderr)
        self.assertRegex(result.stderr,rb'^input:[0-9]+:[0-9]+: error\[C0B-')
        return result

    def depth_fault(self,source,profile=0,stdout=b''):
        result=self.execute(self.compile(source,profile))
        self.assertEqual((result.returncode,result.stdout),(70,stdout))
        self.assertIn(b'error[C0R-003]:',result.stderr)
        return result

    def check_shift_faults_with_bang(self,profile):
        suffix=b'error[C0R-010]: shift count out of range; use 0..63\n'
        sources=[b'fn main(){return !(1<<64)}',
                 b'fn idle()->!{idle()}fn main(){return !(1>>(-1))}',
                 b'fn main(){byte_store(0,7)return !(1<<64)}']
        for source in sources:
            with self.subTest(shift_fault_source=source,profile=profile):
                image=self.compile(source,profile)
                operator=b'<<' if b'<<' in source else b'>>'
                prefix=b'input:1:'+str(source.index(operator)+1).encode()+b': '
                result=self.execute(image)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (70,b'',prefix+suffix))
                self.assertEqual(image[0x600c40:0x600c40+len(suffix)],suffix)
                with Path(__file__).open('rb') as readonly:
                    failed=self.execute(image,stderr=readonly)
                self.assertEqual((failed.returncode,failed.stdout),(74,b''))

    def test_independent_recursive_bottom_has_no_normal_result(self):
        for profile in (0, 1):
            with self.subTest(profile=profile):
                wire=recursive_bottom_wire(profile)
                decoded,nodes=decode_nqaf(wire)
                self.assertEqual((decoded['version'],decoded['runtime_profile']),(13,profile))
                self.assertEqual(decoded['return_annotations'],{1:(9,3)})
                self.assertEqual(nodes[0][1],1)
                compiled = run_native(self.backend, wire)
                self.assertEqual((compiled.returncode, compiled.stderr), (0, b''))
                self.assertTrue(compiled.stdout.startswith(b'\x7fELF'))
                with tempfile.TemporaryDirectory(prefix='nb-guest-') as name:
                    elf=Path(name)/'program';elf.write_bytes(compiled.stdout);elf.chmod(0o700)
                    outcome=run_native(elf)
                self.assertEqual((outcome.returncode,outcome.stdout),(70,b''))
                self.assertRegex(outcome.stderr,rb'^input:1:14: error\[C0R-003\]:')

    def test_logical_bang_truth_precedence_and_inequality(self):
        for expression,want in [(b'!0',1),(b'!2',0),(b'!!7',1),(b'!!0',0),
                                (b'!2==1',0),(b'!(2==1)',1),(b'!(-1)',0),
                                (b'!(-9223372036854775807-1)',0),
                                (b'!0!=0',1),(b'~!0',254)]:
            for profile in (0,1):
                with self.subTest(expression=expression,profile=profile):
                    run=self.execute(self.compile(b'fn main(){return '+expression+b'}',profile))
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(want,b'',b''))
        for profile in (0,1):self.check_shift_faults_with_bang(profile)

    def test_forward_mutual_calls_and_mixed_return_branch(self):
        for profile in (0,1):
            self.depth_fault(b'fn main(){first()}fn first()->!{second()}fn second()->!{first()}',profile)
            source=(b'fn halt()->!{halt()}fn choose(x){if x{return 7}else{halt()}}'
                    b'fn main(){return choose(1)}')
            result=self.execute(self.compile(source,profile))
            self.assertEqual((result.returncode,result.stdout,result.stderr),(7,b'',b''))

    def test_bang_not_metamorphic_defined_i64(self):
        # Independent integer wants; shifts use explicit two's-complement
        # wrapping and division truncates toward zero. No overflow/UB oracle.
        minimum,maximum=-(1<<63),(1<<63)-1
        cases=[(b'0',0),(b'1',1),(b'-1',-1),
               (str(minimum).encode(),minimum),(str(maximum).encode(),maximum),
               (b'2<<63',0),(b'(-1)>>63',-1),
               (b'7^7',0),(b'0 and 7',0),(b'0 or -1',1),
               (b'(-9223372036854775807-1)&9223372036854775807',0),
               (b'(-9223372036854775807-1)%2',0)]
        generator=random.Random(0x4e5140)
        leaves=[minimum,maximum,-257,-2,-1,0,1,2,257]
        for index in range(20):
            a,b=generator.choice(leaves),generator.choice(leaves)
            operation=index%9
            if operation==0:expression=f'({a})-({a})';value=0
            elif operation==1:expression=f'({a})==({b})';value=int(a==b)
            elif operation==2:expression=f'({a})!=({b})';value=int(a!=b)
            elif operation==3:expression=f'({a})&({b})';value=a&b
            elif operation==4:expression=f'({a})|({b})';value=a|b
            elif operation==5:expression=f'({a})^({b})';value=a^b
            elif operation in (6,7):
                count=generator.choice((0,1,31,32,63))
                if operation==6:expression=f'({a})>>{count}';value=a>>count
                else:
                    expression=f'({a})<<{count}'
                    value=((a<<count)+(1<<63))%(1<<64)-(1<<63)
            else:
                if b==0 or (a==minimum and b==-1):b=2
                expression=f'({a})/({b})'
                value=(abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)
            cases.append((expression.encode(),value))
        for expression,value in cases:
            want=int(value==0)
            for operator in (b'!',b'not '):
                source=(b'fn halt()->!{halt()}'
                        b'fn tap(v){byte_store(7,byte_load(7)+1)return v}'
                        b'fn main(){let got='+operator+b'(tap('+expression+b'))'
                        b' if got!='+str(want).encode()+b'{return 91}'
                        b' if byte_load(7)!=1{return 92}return got}')
                for profile in (0,1):
                    with self.subTest(expression=expression,operator=operator,profile=profile):
                        result=self.execute(self.compile(source,profile))
                        self.assertEqual((result.returncode,result.stdout,result.stderr),
                                         (want,b'',b''))

    def test_reject_returning_and_fallthrough_bodies(self):
        bodies=[b'',b'return 1',b'let n=1',b'while 0{}',b'while x{}',
                b'if x{halt()}',b'if x{halt()}else{return 7}',
                b'halt()return 1',b'back()',b'if x{back()}else{halt()}']
        for body in bodies:
            for profile in (0,1):
                with self.subTest(body=body,profile=profile):
                    source=(b'fn back(){return 3}fn halt()->!{halt()}'
                            b'fn wrong(x)->!{'+body+b'}fn main(){return 0}')
                    self.reject(source,profile=profile)
        self.reject(b'fn main()->!{}')

    def test_strict_bottom_composition(self):
        for expression in [b'halt()+1',b'1+halt()',b'-halt()',b'~halt()',
                           b'not halt()',b'write(halt())',b'f(1,halt())']:
            for profile in (0,1):
                self.depth_fault(b'fn halt()->!{halt()}fn f(a,b){return a+b}'
                                 b'fn main(){return '+expression+b'}',profile)

    def test_short_circuit_bottom_rhs(self):
        for expression,want in [(b'0 and halt()',0),(b'1 or halt()',1),
                                (b'1 and halt()',None),(b'0 or halt()',None)]:
            for profile in (0,1):
                source=b'fn halt()->!{halt()}fn main(){return '+expression+b'}'
                if want is None:self.depth_fault(source,profile)
                else:
                    run=self.execute(self.compile(source,profile))
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(want,b'',b''))

    def test_flow_summaries_include_conditional_divergence(self):
        # Compile the actual validation/flow prefix as a test-only observer.
        # It prints N/R/D after each function and never enters codegen. No
        # modified analyzer is installed or used as a canonical compiler stage.
        source=(ROOT/'bootstrap/compiler/c0/backend.nql').read_text()
        marker='    # /13 post-type flow:'
        end='    # Postorder live-value stack:'
        self.assertEqual(source.count(marker),1)
        self.assertEqual(source.count(end),1)
        first=source.index(marker);last=source.index(end,first)
        flow=source[first:last]
        tail='        pos = pos + 1\n    }\n\n'
        self.assertTrue(flow.endswith(tail))
        flow=flow[:-len(tail)]+('        output_write(6815744, 3 * (kind == 41))\n'+tail)
        observed_source=source[:first]+flow+'    return ok == 0\n}\n'
        b0=candidate_binary('B0_COMPILER',ROOT/'bootstrap/compiler/b0/x86_64-linux/b0.seed')
        cases=[(b'return x and halt()',1),(b'return x or halt()',1),
               (b'return 1+(x and halt())',1),(b'return f(x or halt())',1),
               (b'let v=x and halt() return 0',1),
               (b'let v=1 v=x or halt() return v',1),
               (b'if x and halt(){return 1}else{return 2}',1),
               (b'return x and 1',0),(b'return f(x)',0)]
        with tempfile.TemporaryDirectory(prefix='nb-flow-audit-') as directory:
            text=Path(directory)/'observer.nql';text.write_text(observed_source)
            observer=Path(directory)/'observer'
            built=run_native(b0,args=('--compiler-profile',str(text),'-o',str(observer)))
            self.assertEqual((built.returncode,built.stdout,built.stderr),(0,b'',b''))
            for body,diverges in cases:
                program=(b'fn halt()->!{halt()}fn f(v){return v}'
                         b'fn choose(x){'+body+b'}fn main(){return 0}')
                want=bytes([0,0,1, 0,1,0, 0,1,diverges, 0,1,0])
                for profile in (0,1):
                    with self.subTest(body=body,profile=profile):
                        result=run_native(observer,self.source_wire(program,profile))
                        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,want,b''))

    def test_argument_effect_order(self):
        source=(b'fn halt()->!{halt()}fn f(a,b,c){write("C")return 0}'
                b'fn main(){return f(write("A"),halt(),write("B"))}')
        for profile in (0,1):self.depth_fault(source,profile,stdout=b'A')

    def test_bottom_local_inference_and_assignment(self):
        bodies=[b'let n=halt()return n',b'let n=halt()let copy=n return copy',
                b'let n=1 n=halt()return n',b'let n="x" n=halt()return 0']
        for body in bodies:
            for profile in (0,1):self.depth_fault(b'fn halt()->!{halt()}fn main(){'+body+b'}',profile)
        self.reject(b'fn halt()->!{halt()}fn main(){let n=halt()n=1 return 0}',b'C0B-012')

    def test_unreachable_type_name_arity_and_permission_checks(self):
        bodies=[b'return halt()+"bad"',b'return f(halt(),"bad")',
                b'let n=1 n="bad" return halt()',b'return !"bad"']
        for body in bodies:
            for profile in (0,1):
                self.reject(b'fn halt()->!{halt()}fn f(a,b){return a+b}fn main(){'+body+b'}',b'C0B-012',profile)
        self.reject(b'fn halt()->!{halt()}fn main(){halt()return missing}',b'C0B-003')
        self.reject(b'fn halt()->!{halt()}fn f(a){return a}fn main(){return f(halt(),1)}',b'C0B-008')
        self.reject(b'fn halt()->!{halt()}fn main(){halt()return syscall0(39)}',b'C0B-008')
        # syscall6 is the implemented raw API; syscall0 is just an unknown name.
        source=b'fn halt()->!{halt()}fn main(){halt()return syscall6(39,0)}'
        result=run_native(self.frontend,source)
        self.assertEqual((result.returncode,result.stdout),(1,b''))
        self.assertIn(b'error[C0S-001]:',result.stderr)

    def test_literal_loop_proof_and_ordinary_never_identifier(self):
        # Inspect successful literal-loop compilation without running forever.
        for profile in (0,1):
            for condition in [b'1',b'256',b'9223372036854775807']:
                elf=self.compile(b'fn idle()->!{while '+condition+b'{}}fn main(){return 0}',profile)
                self.assertTrue(elf.startswith(b'\x7fELF'))
            source=b'fn Never(){return 7}fn idle()->!{while 1{}}fn main(){return Never()}'
            run=self.execute(self.compile(source,profile))
            self.assertEqual((run.returncode,run.stdout,run.stderr),(7,b'',b''))

    def test_wire_flags_spans_and_stale_versions(self):
        original=recursive_bottom_wire()
        first=32+struct.unpack_from('<I',original,8)[0]
        changes=[(first+1,1,2),(first+24,4,0),(first+28,4,0),
                 (first+24,4,0xffffffff),(first+28,4,0xffffffff),
                 (first+32+24,4,9),(first+2,1,1)]
        for offset,width,value in changes:
            wire=bytearray(original);wire[offset:offset+width]=value.to_bytes(width,'little')
            result=run_native(self.backend,wire)
            self.assertEqual((result.returncode,result.stdout),(1,b''))
            self.assertRegex(result.stderr,rb'^input:[0-9]+:[0-9]+: error\[C0B-(002|013)\]:')
        wire=bytearray(original);wire[4]=12;wire[24]=11
        result=run_native(self.backend,wire)
        self.assertEqual((result.returncode,result.stdout),(1,b''))
        self.assertIn(b'[C0B-002]',result.stderr)

    def test_comment_and_quoted_headers_cannot_supply_a_contract(self):
        # Independently supplied graph must not split the identifier fnmain
        # into a nonexistent fn keyword plus a main declaration.
        source=b'fnmain()->!{main()}'
        records=[(39,1,2,4,0,0,3,8,3),(42,0,12,4,0,0,0,0,0),
                 (44,0,12,4,2,0,4,0,0),(41,0,18,1,0,0,0,0,0),
                 (33,0,0,2,1,0,0,0,0)]
        for profile in (0,1):
            header=struct.pack('<4sBBHIIIIBBHI',b'NQAF',13,32,0,len(source),5,5,12,12,profile,0,0)
            wire=header+source+b''.join(struct.pack('<BBHIIIIIII',k,f,0,o,z,l,r,n,a,b)
                for k,f,o,z,l,r,n,a,b in records)
            rejected=run_native(self.backend,wire)
            self.assertEqual(rejected.returncode,1,rejected.stderr)
            self.assertEqual(rejected.stdout,b'')
            self.assertIn(b'error[C0B-013]:',rejected.stderr)
            # A source-owned header follows the lexer's CRLF rule too. Keep
            # offsets unchanged while replacing its valid separator with CR.
            wire=bytearray(self.source_wire(b'fn main()->!{main()}',profile))
            wire[32+2]=13
            rejected=run_native(self.backend,wire)
            self.assertEqual(rejected.returncode,1,rejected.stderr)
            self.assertEqual(rejected.stdout,b'')
            self.assertIn(b'error[C0B-013]:',rejected.stderr)
            for comment in (b'#',b'//'):
                for comment_source in (b'fn'+comment+b' bad X\nmain()->!{main()}',
                                       b'fn main()->'+comment+b' bad X\n!{main()}'):
                    # CRLF is a lexical rule even inside a consumed comment.
                    bad=comment_source.replace(b' X',b'\rX',1)
                    front=run_native(self.frontend,bad if profile==0 else encode_profile_source(bad))
                    self.assertEqual((front.returncode,front.stdout),(1,b''))
                    self.assertIn(b'error[C0P-001]:',front.stderr)
                    wire=bytearray(self.source_wire(comment_source,profile))
                    wire[32+comment_source.index(b' X')]=13
                    rejected=run_native(self.backend,wire)
                    with self.subTest(comment_source=comment_source,profile=profile):
                        self.assertEqual(rejected.returncode,1,rejected.stderr)
                        self.assertEqual(rejected.stdout,b'')
                        self.assertIn(b'error[C0B-013]:',rejected.stderr)
                    self.depth_fault(comment_source.replace(b'\n',b'\r\n'),profile)
                    for value in (0,128,255):
                        bad=comment_source.replace(b' X',bytes([value])+b'X',1)
                        front=run_native(self.frontend,bad if profile==0 else encode_profile_source(bad))
                        self.assertEqual((front.returncode,front.stdout),(1,b''))
                        self.assertIn(b'error[C0P-001]:',front.stderr)
                        wire=bytearray(self.source_wire(comment_source,profile))
                        wire[32+comment_source.index(b' X')]=value
                        rejected=run_native(self.backend,wire)
                        with self.subTest(comment_byte=value,comment_source=comment_source,profile=profile):
                            self.assertEqual(rejected.returncode,1,rejected.stderr)
                            self.assertEqual(rejected.stdout,b'')
                            self.assertRegex(rejected.stderr,rb'^input:[0-9]+:[0-9]+: error\[C0B-013\]:')
                    # Existing comment rules allow nonzero ASCII control/DEL
                    # bytes; the new check must not invent a printable-only rule.
                    for value in (1,127):
                        self.depth_fault(comment_source.replace(b' X',bytes([value])+b'X',1),profile)
            for separator in (b' ',b'\t',b'\r\n',b'# comment\n',b'// comment\n'):
                self.depth_fault(b'fn'+separator+b'main()->!{main()}',profile)
        # Missing real fn after a comment must reject before the backward
        # cursor crosses zero. Long prefixes expose split-u32 cursor wrapping.
        for comment in (b'#',b'//'):
            for padding in (0,297,1021):
                for newline in (b'\n',b'\r\n'):
                    prefix=comment+b'fn'+b' '*padding+newline
                    source=prefix+b'main()->!{main()}'
                    off=len(prefix)
                    rows=[(39,1,off,4,0,0,3,off+6,3),
                          (42,0,off+10,4,0,0,0,0,0),
                          (44,0,off+10,4,2,0,4,0,0),
                          (41,0,off+16,1,0,0,0,0,0),
                          (33,0,len(comment),2,1,0,0,0,0)]
                    for profile in (0,1):
                        header=struct.pack('<4sBBHIIIIBBHI',b'NQAF',13,32,0,len(source),5,5,12,12,profile,0,0)
                        wire=header+source+b''.join(struct.pack('<BBHIIIIIII',k,f,0,o,z,l,r,n,a,b)
                            for k,f,o,z,l,r,n,a,b in rows)
                        with self.subTest(missing_fn_prefix=len(prefix),comment=comment,newline=newline,profile=profile):
                            rejected=run_native(self.backend,wire,timeout=2)
                            self.assertEqual(rejected.returncode,1,rejected.stderr)
                            self.assertEqual(rejected.stdout,b'')
                            self.assertRegex(rejected.stderr,rb'^input:2:1: error\[C0B-013\]:')
                        if padding==1021:
                            self.depth_fault(prefix+b'fn main()->!{main()}',profile)
        original=recursive_bottom_wire();size=struct.unpack_from('<I',original,8)[0]
        src=original[32:32+size];records=original[32+size:]
        for prefix,name,annotation in [(b'#fn halt()->!{halt()}\n',4,10),
                                       (b'"fn halt()->!{halt()}"\n',4,10)]:
            self.assertEqual(prefix[name:name+4],b'halt')
            self.assertEqual(prefix[annotation:annotation+3],b'->!')
            wire=bytearray(original[:32]+prefix+src+records)
            struct.pack_into('<I',wire,8,size+len(prefix))
            base=32+size+len(prefix)
            for node in range(9):
                offset=base+node*32
                struct.pack_into('<I',wire,offset+4,struct.unpack_from('<I',wire,offset+4)[0]+len(prefix))
            struct.pack_into('<I',wire,base+4,name)
            struct.pack_into('<I',wire,base+24,annotation)
            result=run_native(self.backend,wire)
            self.assertEqual((result.returncode,result.stdout),(1,b''))
            self.assertIn(b'[C0B-013]',result.stderr)

    def test_returning_target_faults_before_reading_a_result(self):
        prologue=b'\x55\x48\x89\xe5\x48\x81\xec\x00\x10\x00\x00\x41\xff\xc7'
        for profile in (0,1):
            compiled=run_native(self.backend,recursive_bottom_wire(profile))
            self.assertEqual((compiled.returncode,compiled.stderr),(0,b''))
            mapped=self.compile(b'fn halt()->!{halt()}fn main(){byte_store(0,7)halt()}',profile)
            for image,column in [(compiled.stdout,31),(mapped,46)]:
                binary=bytearray(image);entry=binary.index(prologue)
                # Deliberate binary fault injection, outside source semantics:
                # the target restores its frame/depth then illegally returns.
                binary[entry+len(prologue):entry+len(prologue)+5]=b'\x41\xff\xcf\xc9\xc3'
                result=self.execute(binary)
                self.assertEqual((result.returncode,result.stdout),(70,b''))
                self.assertTrue(result.stderr.startswith(b'input:1:'+str(column).encode()+b': error[C0R-011]:'))
                with Path(__file__).open('rb') as readonly:
                    failed=self.execute(binary,stderr=readonly)
                self.assertEqual((failed.returncode,failed.stdout),(74,b''))

    def test_bottom_main_fallthrough_guard(self):
        prologue=b'\x55\x48\x89\xe5\x48\x81\xec\x00\x10\x00\x00\x41\xff\xc7'
        for profile in (0,1):
            for arena in (b'',b'byte_store(0,7)'):
                image=self.compile(b'fn main()->!{'+arena+b'while 1{}}',profile)
                # The mapped normal-return relocation must never overlap this
                # bottom-main jump. Check its full rel32 before running a probe.
                self.assertEqual(image[228],0xe9)
                self.assertEqual(233+struct.unpack_from('<i',image,229)[0],0x600d00)
                entry=image.index(prologue)
                for route in ('fallthrough','startup-return'):
                    binary=bytearray(image)
                    if route=='fallthrough':
                        literal=binary.index(b'\x48\xb8\x01'+b'\0'*7,entry+len(prologue))
                        binary[literal+2]=0
                    else:
                        # Controlled result-contract violation in our own test
                        # image: restore frame/depth, then exercise startup.
                        binary[entry+len(prologue):entry+len(prologue)+5]=b'\x41\xff\xcf\xc9\xc3'
                    with self.subTest(profile=profile,arena=bool(arena),route=route):
                        result=self.execute(binary)
                        self.assertEqual((result.returncode,result.stdout),(70,b''))
                        self.assertRegex(result.stderr,rb'^input:1:4: error\[C0R-011\]:')
                        with Path(__file__).open('rb') as readonly:
                            failed=self.execute(binary,stderr=readonly)
                        self.assertEqual((failed.returncode,failed.stdout),(74,b''))

    def test_high_name_and_span_callee_contracts(self):
        name=b'N'*257
        source=b' '*65540+b'fn '+name+b'()->!{'+name+b'()}fn main(){'+name+b'()}'
        for profile in (0,1):self.depth_fault(source,profile)

    def test_generation_never_and_bang_contract(self):
        for profile in (0,1):
            source=b'fn halt()->!{halt()}fn main(){if !0{return 7}else{halt()}}'
            result=self.execute(self.compile(source,profile))
            self.assertEqual((result.returncode,result.stdout,result.stderr),(7,b'',b''))
            self.reject(b'fn wrong()->!{return 7}fn main(){return 0}',profile=profile)
            self.depth_fault(b'fn halt()->!{halt()}fn main(){halt()}',profile)
            for value,want in [(b'0',11),(b'7',13),
                               (b'-9223372036854775807-1',13)]:
                source=(b'fn halt()->!{halt()}fn main(){if !('+value+
                        b'){return 11}else{return 13}}')
                result=self.execute(self.compile(source,profile))
                self.assertEqual((result.returncode,result.stdout,result.stderr),(want,b'',b''))
            for expression,want in [(b'0 and halt()',0),(b'1 or halt()',1)]:
                result=self.execute(self.compile(b'fn halt()->!{halt()}fn main(){return '+expression+b'}',profile))
                self.assertEqual((result.returncode,result.stdout,result.stderr),(want,b'',b''))
            self.depth_fault(b'fn halt()->!{halt()}fn f(a,b,c){write("C")return 0}'
                             b'fn main(){return f(write("A"),halt(),write("B"))}',profile,stdout=b'A')
            self.check_shift_faults_with_bang(profile)
        self.test_bottom_main_fallthrough_guard()
        self.test_comment_and_quoted_headers_cannot_supply_a_contract()


if __name__ == '__main__':
    unittest.main()
