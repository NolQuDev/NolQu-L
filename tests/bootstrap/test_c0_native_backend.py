"""Independent C0.32 wire validation and frozen C0.31 byte oracles."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch

from c031_support import (ROOT, candidate_binary, decode_nqaf, encode_profile_source,
                         run_native)


class NativeBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
        cls.frontend = candidate_binary('C0_FRONTEND', stage / 'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', stage / 'c0-backend.seed')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='c032-be-')
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)

    def wire(self, source, profile=False):
        parsed = run_native(self.frontend, encode_profile_source(source) if profile else source)
        self.assertEqual((parsed.returncode, parsed.stderr), (0, b''))
        return parsed.stdout

    def accepted(self, wire):
        result = run_native(self.backend, wire)
        self.assertEqual((result.returncode, result.stderr), (0, b''))
        self.assertEqual(result.stdout[:4], b'\x7fELF')
        return result.stdout

    def rejected(self, wire, code=None):
        result = run_native(self.backend, wire)
        self.assertEqual((result.returncode, result.stdout), (1, b''), result.stderr)
        self.assertRegex(result.stderr, rb'^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$')
        if code:
            self.assertIn(f'[C0B-{code:03}]'.encode(), result.stderr)
        return result

    def mutate(self, wire, node, field, value):
        header, _ = decode_nqaf(wire)
        data = bytearray(wire)
        at = 32 + header['source_length'] + (node - 1) * 32
        if field in (0, 1):
            data[at + field] = value
        else:
            struct.pack_into('<I', data, at + field, value)
        return bytes(data)

    def test_frozen_c031_baseline_is_independent(self):
        try:
            support = importlib.import_module('c032_support')
        except ModuleNotFoundError:
            self.fail('missing independently frozen C0.31 rebuild helper')
        old = support.build_c031_predecessors(self.directory / 'old')
        expected = {'frontend': '46aaa86e226c54d1b9429c25696699bc2d4747d84b12f79ac6b0c21971cbfa7c',
                    'backend': 'af8820eaff28b467dd148b2a48d966b775c4f170bb19fe223bc8a77c7b3559f9'}
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256(old[name].read_bytes()).hexdigest(), digest)
        with self.assertRaises(FileExistsError):
            support.build_c031_predecessors(self.directory / 'old')
        fixture = self.directory / 'fixture'
        shutil.copytree(support.PREDECESSORS, fixture)
        for name in ('frontend.nql', 'backend.nql', 'hashes.json'):
            original = (fixture / name).read_bytes()
            (fixture / name).write_bytes(original + b' ')
            with patch.object(support, 'PREDECESSORS', fixture), patch.object(
                    support, 'run_native', side_effect=AssertionError('must reject before execution')):
                with self.assertRaises(ValueError):
                    support.build_c031_predecessors(self.directory / 'bad')
            self.assertFalse((self.directory / 'bad').exists())
            (fixture / name).write_bytes(original)

    def test_frozen_c031_byte_parity(self):
        from c032_support import build_c031_predecessors
        old = build_c031_predecessors(self.directory / 'old')
        sources = [b'fn main(){return 7}',
                   b'fn main(){let x=1 while x<4{if x==2{x=x+1}else{x=x+2}}return x}',
                   b'fn f(a,b,c,d,e,f){return a+b+c+d+e+f}fn main(){return f(1,2,3,4,5,6)}',
                   b'fn main(){byte_store(0,65) output_write(0,1) return byte_load(0)}',
                   b'fn main(){let unsafe=1 if unsafe {return 7} return 0}',
                   b'fn main(){let unsafe=0 while 0+unsafe {unsafe=1} return unsafe}',
                   b'fn unsafe(a){return a}fn main(){return unsafe(7)}',
                   b'# unsafe { syscall6 arg_count arg_copy byte_address\nfn main(){return 0}',
                   b' ' * 70000 + b'fn main(){return 9}']
        for name in (b'arg_count', b'arg_copy', b'byte_address', b'syscall6'):
            sources.append(b'fn main(){return '+name+b'(7)}fn '+name+b'(a){return a}')
        for source in sources:
            for profile in (False, True):
                with self.subTest(source=source[-100:], profile=profile):
                    payload = encode_profile_source(source) if profile else source
                    before = run_native(old['frontend'], payload)
                    after = run_native(self.frontend, payload)
                    self.assertEqual((before.returncode, before.stderr), (0, b''))
                    self.assertEqual((after.returncode, after.stderr, after.stdout),
                                     (0, b'', before.stdout))
                    before_elf = run_native(old['backend'], before.stdout)
                    after_elf = run_native(self.backend, after.stdout)
                    self.assertEqual((before_elf.returncode, before_elf.stderr), (0, b''))
                    self.assertEqual((after_elf.returncode, after_elf.stderr, after_elf.stdout),
                                     (0, b'', before_elf.stdout))

    def test_wire_scope_ownership_mutations(self):
        source = (b'fn f(){return 1}fn main(){unsafe {# safety: caller owns frame\n'
                  b'let x=syscall6(39,0)} return 0}')
        wire = self.wire(source)
        self.accepted(wire)
        header, nodes = decode_nqaf(wire)
        ids = lambda kind: [i for i,n in enumerate(nodes,1) if n[0]==kind]
        op, cl, call, ret, let = ids(45)[0], ids(46)[0], ids(42)[0], ids(32)[-1], ids(30)[0]
        for node,field,value in [(op,0,46),(cl,0,45),(op,1,1),(cl,12,1),
                                 (op,20,cl),(let,20,ret),(call,12,call),
                                 (ret,12,call),(op,24,1),(cl,28,1),
                                 (cl,4,source.index(b'}'))]:
            with self.subTest(node=node,field=field,value=value):
                self.rejected(self.mutate(wire,node,field,value))
        # Expressions physically within a scope cannot be borrowed by a later
        # owning statement. Contiguous postorder AND independent ownership bind it.
        self.rejected(self.mutate(wire,ret,12,call))
        # Move genuine closing record after a raw call anchored OUTSIDE the actual
        # source brace. Keep all IDs/links/subtrees valid: source interval must deny.
        source = b'fn main(){unsafe {# safety: caller owns frame\nsyscall6(39,0)} return 0}'
        wire = self.wire(source)
        header,nodes = decode_nqaf(wire)
        close = next(n for n in nodes if n[0]==46)[2]
        call_offset = next(n for n in nodes if n[0]==42)[2]
        data=bytearray(wire)
        # Exchange one whitespace byte before the call with the genuine brace.
        # The AST topology is unchanged while the real scope ends before the call.
        data[32+call_offset-1],data[32+close]=ord('}'),ord(' ')
        self.rejected(bytes(data))
        # Genuine close record relinking after an outside call, no expression alias.
        source = b'fn main(){unsafe {# safety: owns effects\n} byte_store(0,0) return 0}'
        wire=self.wire(source)
        h,ns=decode_nqaf(wire)
        # Renaming a safe, equal-width intrinsic produces an outside raw call.
        data=bytearray(wire); where=source.index(b'byte_store'); data[32+where:32+where+10]=b'  syscall6'
        call_id=next(i for i,n in enumerate(ns,1) if n[0]==42)
        stmt_id=next(i for i,n in enumerate(ns,1) if n[0]==44)
        data=self.mutate(bytes(data),call_id,4,where+2)
        data=self.mutate(data,call_id,8,8)
        data=self.mutate(data,stmt_id,4,where+2)
        data=self.mutate(data,stmt_id,8,8)
        # Reorder close and the complete call subtree, remapping every edge.
        h,ns=decode_nqaf(data); close_id=next(i for i,n in enumerate(ns,1) if n[0]==46)
        order=list(range(1,close_id))+list(range(close_id+1,stmt_id+1))+[close_id]+list(range(stmt_id+1,len(ns)+1))
        mapping={old:new for new,old in enumerate(order,1)}
        records=[]; stmts={30,31,32,34,35,36,37,38,39,40,41,44,45,46}
        chain=[mapping[i] for i in order if ns[i-1][0] in stmts]
        links=dict(zip(chain,chain[1:]+[0]))
        for new,old in enumerate(order,1):
            n=ns[old-1]; records.append(struct.pack('<BBHIIIIIII',n[0],0,0,n[2],n[3],mapping.get(n[4],0),mapping.get(n[5],0),links.get(new,0),0,0))
        forged=bytes(data[:32+h['source_length']])+b''.join(records)
        self.rejected(forged,10)

    def test_legacy_versions_cannot_enable_native_ops(self):
        for source in (b'fn main(){return arg_count()}',
                       b'fn main(){return arg_copy(0,0,1)}',
                       b'fn main(){unsafe {# safety: owns spans\nbyte_address(0,0) syscall6(39,0)} return 0}'):
            wire=self.wire(source); self.accepted(wire)
            for version in (5,7):
                data=bytearray(wire); data[4]=version
                self.rejected(bytes(data),1)
            # /5 with a legal old dialect must never activate native names.
            data=bytearray(wire);data[4]=5;data[24]=4
            self.rejected(bytes(data))
        wire=self.wire(b'fn main(){return arg_count()}')
        for field,value in ((6,1),(25,2),(26,1),(28,1),(24,4)):
            data=bytearray(wire);data[field]=value
            self.rejected(bytes(data),1)

    def test_source_header_is_independently_validated(self):
        source=b'fn main(){unsafe {# safety: owns frame\n syscall6(39,0)} return 0}'
        wire=self.wire(source); self.accepted(wire)
        for old,new in ((b'unsafe',b'unsafE'),(b'safety:',b'safety!'),
                        (b'owns frame',b'          '),(b'# safety:',b'# nosafe:')):
            data=bytearray(wire);at=32+source.index(old);data[at:at+len(old)]=new
            self.rejected(bytes(data))
        _,nodes=decode_nqaf(wire);op=next(i for i,n in enumerate(nodes,1) if n[0]==45)
        self.rejected(self.mutate(wire,op,8,nodes[op-1][3]-1))
        for header in (b'# safety: braces } { ignored\n',b'// safety:\n# owns frame\n',
                       b' \t\n// \tsafety: frame\n'):
            self.accepted(self.wire(b'fn main(){unsafe {'+header+b'syscall6(39,0)}return 0}'))
        source=b'\n'*70000+source
        self.accepted(self.wire(source,True))

    def test_shadow_resolution_and_arity(self):
        # Forward user definitions (including node IDs > historical helper IDs)
        # shadow native names; locals are a different namespace.
        for name in (b'arg_count',b'arg_copy',b'byte_address',b'syscall6'):
            source=b'fn main(){return '+name+b'(7)}fn '+name+b'(a){return a}'
            self.accepted(self.wire(source,True))
            source=b'fn main(){unsafe {# safety: owns effects\n'+name+b'()}return 0}fn '+name+b'(a){return a}'
            self.rejected(self.wire(source),8)
        for expression in (b'arg_count(1)',b'arg_copy(0,0)',b'byte_address(0)',b'syscall6(39)'):
            self.rejected(self.wire(b'fn main(){unsafe {# safety: owns effects\n'+expression+b'}return 0}'),8)
        self.accepted(self.wire(b'fn main(){let arg_count=7 return arg_count()}'))
        self.accepted(self.wire(b'fn main(){unsafe {# safety: owns effects\nlet x=1}let x=2 return x}'))
        # Safe API implementation may own an unsafe scope, then be called safely.
        self.accepted(self.wire(b'fn raw(){unsafe {# safety: owns frame\nreturn syscall6(39,0)}return 0}fn main(){return raw()}'))


if __name__=='__main__':
    unittest.main()
