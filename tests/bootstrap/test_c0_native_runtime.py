"""Actual x86_64 guest execution; QEMU on non-x86 hosts, no host codegen."""
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from c031_debugger import Guest, MASK
from c032_support import (ROOT, candidate_binary, decode_nqaf, encode_profile_source,
                          frame, raw_body, run_native)
import test_c0_compiler_profile as profile_oracle


class NativeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage=ROOT/'bootstrap/compiler/c0/x86_64-linux'
        cls.frontend=candidate_binary('C0_FRONTEND', stage/'c0-frontend.seed')
        cls.backend=candidate_binary('C0_BACKEND', stage/'c0-backend.seed')

    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='c032-rt-')
        self.addCleanup(tmp.cleanup)
        self.directory=Path(tmp.name)
        self.sequence=0

    def program(self, source, profile=False):
        if isinstance(source,str): source=source.encode('ascii')
        parsed=run_native(self.frontend, encode_profile_source(source) if profile else source,timeout=120)
        self.assertEqual((parsed.returncode,parsed.stderr),(0,b''),source[:300])
        compiled=run_native(self.backend,parsed.stdout,timeout=120)
        self.assertEqual((compiled.returncode,compiled.stderr),(0,b''),source[:300])
        self.assertEqual(compiled.stdout[:4],b'\x7fELF')
        self.sequence+=1
        binary=self.directory/f'program-{self.sequence}'
        binary.write_bytes(compiled.stdout);binary.chmod(0o755)
        self.source,self.wire=source,parsed.stdout
        return binary

    def result(self, binary, status=0, output=b'', args=()):
        actual=run_native(binary,args=args)
        self.assertEqual((actual.returncode,actual.stdout,actual.stderr),(status,output,b''))
        return actual

    def site(self,binary,pattern):
        data=binary.read_bytes();pattern=bytes.fromhex(pattern)
        self.assertEqual(data.count(pattern),1,pattern.hex())
        return 0x400000+data.index(pattern)+len(pattern)-2

    def raw_site(self,binary):
        return self.site(binary,'4d8b4b280f05')

    def test_argv_exact_bytes_and_bounds(self):
        # Exact argument bytes, including argv0, empty, spaces and invalid UTF-8.
        body='let i=0 while i<arg_count(){let n=arg_copy(i,0,4096) output_write(0,n+1) i=i+1} return 0'
        for profile in (False,True):
            binary=self.program('fn main(){'+body+'}',profile)
            args=(b'',b'a b',b'\xff\x80\nZ',b'--literal')
            self.result(binary,output=os.fsencode(binary)+b'\0'+b'\0'.join(args)+b'\0',args=args)
            binary=self.program('fn main(){return arg_count()}',profile)
            self.result(binary,status=5,args=args)
            # An argc-only executable has no byte arena startup, nor mapped allocation.
            self.assertNotIn(bytes.fromhex('4881ec00000100'),binary.read_bytes())
            self.assertNotIn(bytes.fromhex('49c7c0ffffffff4531c90f05'),binary.read_bytes())
            for expression,code,status in [('arg_copy(0-1,0,8)',8,70),('arg_copy(arg_count(),0,8)',8,70),
                    ('arg_copy(0,0,0)',4,70),('arg_copy(0,0,0-1)',4,70),
                    ('arg_copy(0,0-1,8)',4,70),('arg_copy(0,0,1)',9,74),
                    ('arg_copy(0-1,0-1,0)',4,70)]:
                with self.subTest(expression=expression,profile=profile):
                    binary=self.program('fn main(){return '+expression+'}',profile)
                    actual=run_native(binary)
                    self.assertEqual((actual.returncode,actual.stdout),(status,b''))
                    self.assertRegex(actual.stderr,
                        (rf'^input:1:18: error\[C0R-{code:03}\]: [^\n]+; [^\n]+\n$').encode())
            cap=16777216 if profile else 65536
            binary=self.program(f'fn main(){{let n=arg_copy(1,{cap-1},1) return byte_load({cap-1})+n}}',profile)
            self.result(binary,args=(b'',))
            # Observe destination at the fatal writer before copying can publish.
            binary=self.program('fn main(){byte_store(0,77)byte_store(1,78)return arg_copy(0,0,2)}',profile)
            diagnostic=self.site(binary,'b801000000bf020000000f05')
            with Guest(binary) as guest:
                entry=0x400000+0x600840
                guest.bp(entry);at=guest.until(entry);arena=at['rbx']
                guest.bp(entry,False);guest.bp(diagnostic);guest.until(diagnostic)
                self.assertEqual(guest.read_memory(arena,2),b'MN')
                guest.bp(diagnostic,False);self.assertEqual(guest.finish()[0],74)

    def test_raw_errors_and_frame_range(self):
        for profile in (False,True):
            body=frame(1,-1,0,0,0,0,0)+'\nlet a=syscall6(999999,1)let b=syscall6(3,1) return (a==(0-38))*(b==(0-9))'
            self.result(self.program('fn main(){'+raw_body(body)+'return 0}',profile),status=1)
            cap=16777216 if profile else 65536
            for expression in (f'byte_address({cap+1},0)', 'byte_address(0-1,0)',
                               'byte_address(0,0-1)',f'byte_address({cap},1)',
                               'syscall6(39,0-1)',f'syscall6(39,{cap-47})'):
                binary=self.program('fn main(){'+raw_body('return '+expression)+'return 0}',profile)
                raw=self.raw_site(binary) if expression.startswith('syscall') else None
                with Guest(binary) as guest:
                    if raw: guest.bp(raw)
                    actual=guest.finish()
                    self.assertEqual((actual[0],actual[1]),(70,b''))
                    self.assertIn(b'[C0R-004]',actual[2])
            self.result(self.program(f'fn main(){{'+raw_body(f'return byte_address({cap},0)-byte_address(0,{cap})=={cap}')+'return 0}',profile),status=1)
            # Zero-length write to invalid fd still enters the kernel and returns EBADF.
            body=frame(0,-1,0,0,0,0,0)+'\nreturn syscall6(1,0)==(0-9)'
            binary=self.program('fn main(){'+raw_body(body)+'return 0}',profile)
            site=self.raw_site(binary)
            with Guest(binary) as guest:
                guest.bp(site);regs=guest.until(site)
                self.assertEqual((regs['rax'],regs['rdi'],regs['rdx']),(1,MASK,0))
                guest.bp(site,False);guest.bp(site+2);after=guest.until(site+2)
                self.assertEqual(after['rax'],(-9)&MASK)
                guest.bp(site+2,False);self.assertEqual(guest.finish(),(1,b'',b''))

    def test_six_register_file_mmap(self):
        expected=b'actual file mmap offset 65536\x00\xff\n'
        for profile in (False,True):
            datafile=self.directory/f'mapped-{int(profile)}.bin'
            datafile.write_bytes(b'P'*65536+expected+bytes(4096-len(expected)))
            before=datafile.read_bytes()
            path=os.fsencode(datafile)+b'\0'
            pathsource='\n'.join(f'byte_store({512+i},{b})' for i,b in enumerate(path))
            body=pathsource+'\n'+frame(0,-100,'byte_address(512,256)',2,0,0,0)+'\nlet fd=syscall6(257,0)\n'
            body+=frame(48,0,4096,3,1,'fd',65536)+'\nlet mapped=syscall6(9,48)\n'
            body+=frame(96,1,'mapped',len(expected),0,0,0)+f'\nlet n=syscall6(1,96)\n'
            body+=frame(144,'mapped',4096,0,0,0,0)+'\nlet u=syscall6(11,144)\n'
            body+=frame(192,'fd',0,0,0,0,0)+f'\nlet c=syscall6(3,192) return (n!={len(expected)})+(u!=0)+(c!=0)'
            binary=self.program('fn main(){'+raw_body(body)+'return 99}',profile)
            source,wire=self.source,self.wire
            site=self.raw_site(binary); observations=[]
            with Guest(binary,timeout=30) as guest:
                guest.bp(site)
                for number in (257,9,1,11,3):
                    pre=guest.until(site)
                    self.assertEqual(guest.read_memory(pre['rip'],2),b'\x0f\x05')
                    self.assertEqual(pre['rax'],number)
                    guest.bp(site,False);guest.bp(site+2)
                    post=guest.until(site+2)
                    observations.append(dict(number=number,pre=pre,post=post))
                    guest.bp(site+2,False);guest.bp(site)
                outcome=guest.finish()
            self.assertEqual(outcome,(0,expected,b''))
            opened,mapped,written,unmapped,closed=observations
            fd=opened['post']['rax'];address=mapped['post']['rax']
            self.assertLess(fd,1<<63);self.assertLess(address,1<<63)
            self.assertEqual(tuple(mapped['pre'][r] for r in ('rdi','rsi','rdx','r10','r8','r9')),(0,4096,3,1,fd,65536))
            self.assertEqual((written['pre']['rsi'],written['pre']['rdx'],written['post']['rax']),(address,len(expected),len(expected)))
            self.assertEqual((unmapped['pre']['rdi'],unmapped['pre']['rsi'],unmapped['post']['rax']),(address,4096,0))
            self.assertEqual((closed['pre']['rdi'],closed['post']['rax']),(fd,0))
            after=datafile.read_bytes();self.assertEqual(after,before)
            evidence=os.environ.get('C032_NATIVE_EVIDENCE_DIR')
            if evidence is not None:
                destination=Path(evidence);destination.mkdir(parents=True,exist_ok=True)
                stem=f'mmap-profile{int(profile)}'
                artifacts={'.nql':source,'.nqaf':wire,'.elf':binary.read_bytes()}
                identities={}
                for suffix,data in artifacts.items():
                    path=destination/(stem+suffix)
                    with path.open('xb') as stream:stream.write(data)
                    path.chmod(binary.stat().st_mode&0o777 if suffix=='.elf' else 0o644)
                    identities[suffix[1:]]=dict(path=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),mode=path.stat().st_mode&0o777)
                record=dict(profile=int(profile),execution='actual x86_64 Linux syscall execution via QEMU debugger',
                            synthetic_fault_injection=False,syscall_rip=site,observations=observations,
                            file_offset=65536,file_before_hex=before[65536:65536+len(expected)].hex(),
                            file_after_hex=after[65536:65536+len(expected)].hex(),expected_hex=expected.hex(),
                            file_before_sha256=hashlib.sha256(before).hexdigest(),file_after_sha256=hashlib.sha256(after).hexdigest(),
                            outcome=dict(status=outcome[0],stdout_hex=outcome[1].hex(),stderr_hex=outcome[2].hex()),artifacts=identities)
                with (destination/(stem+'.json')).open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')

    def test_callee_saved_and_alignment(self):
        # Six user arguments stay live across nested native/stream helpers.
        body=(frame(0,0,0,0,0,0,0)+'\nlet p=byte_address(0,48)let z=syscall6(39,0) '
              'let n=arg_copy(0,256,1024) input_read(0,0) output_write(0,0) '
              'return a+b+c+d+e+f+(arg_count()>0)+(n>0)+(p>0)+(z>0)')
        source='fn inner(a,b,c,d,e,f){'+raw_body(body)+'return 0}fn outer(a,b,c,d,e,f){return inner(a,b,c,d,e,f)}fn main(){return outer(1,2,3,4,5,6)}'
        for profile in (False,True):
            binary=self.program(source,profile)
            self.result(binary,status=25)
            # Inspect each new returning helper's actual entry and return address.
            for offset in (0x600820,0x600840,0x600900,0x600940):
                with self.subTest(profile=profile,helper=hex(offset)),Guest(binary) as guest:
                    entry=0x400000+offset;guest.bp(entry);before=guest.until(entry)
                    self.assertEqual(before['rsp']%16,8)
                    return_address=struct.unpack('<Q',guest.read_memory(before['rsp'],8))[0]
                    guest.bp(entry,False);guest.bp(return_address);after=guest.until(return_address)
                    self.assertEqual(after['rsp'],before['rsp']+8)
                    for name in ('rbp','rbx','r12','r13','r14','r15'):
                        self.assertEqual(after[name],before[name],name)
                    guest.bp(return_address,False);self.assertEqual(guest.finish(),(25,b'',b''))

    def test_arena_profiles_and_cleanup(self):
        # New operations participate in the existing acquired/status/cleanup ABI.
        for profile,cap in ((False,65536),(True,16777216)):
            source='fn main(){'+raw_body(f'let p=byte_address({cap},0) return p>0')+'return 0}'
            self.result(self.program(source,profile),status=1)
        for body,status,code in [('return arg_copy(0,0,1)',74,9),('return arg_copy(0-1,0,8)',70,8),
                                  (raw_body('return syscall6(39,16777200)')+'return 0',70,4),
                                  ('return arg_copy(0,16777216,1)',70,4),('return arg_count()',1,None)]:
            binary=self.program('fn main(){'+body+'}',True)
            if code is None:
                self.result(binary,status=status)
                continue
            oracle=profile_oracle.CompilerProfileTests(methodName='runTest');oracle._type_equality_funcs=self._type_equality_funcs
            sites=oracle.sites(binary)
            with Guest(binary) as guest:
                base=oracle.acquire(guest,sites)
                actual=oracle.cleanup(guest,sites,status,base=base)
                self.assertEqual((actual[0],actual[1]),(status,b''))
                self.assertIn(f'[C0R-{code:03}]'.encode(),actual[2])
            # Broken stderr must still release exactly once, then exit74.
            with Guest(binary) as guest:
                base=oracle.acquire(guest,sites)
                guest.bp(sites['diagnose']);guest.until(sites['diagnose']);guest.inject(-9)
                guest.bp(sites['diagnose'],False)
                actual=oracle.cleanup(guest,sites,74,base=base)
                self.assertEqual(actual,(74,b'',b''))

    def test_raw_io_progress(self):
        # Caller explicitly retries EINTR and advances short results. Injection
        # is synthetic, at a verified SYSCALL in actual guest machine execution.
        for profile in (False,True):
            body='byte_store(512,65)byte_store(513,66)byte_store(514,67)\n'
            body+=frame(0,1,'byte_address(512,3)',3,0,0,0)
            body+='\nlet done=0 while done<3{let n=syscall6(1,0) if n==(0-4){}else{if n<=0{return 7}done=done+n '
            body+='let p=byte_address(512+done,3-done) let i=0 while i<8{byte_store(8+i,p/1) p=p/256 i=i+1}byte_store(16,3-done)}}return 0'
            binary=self.program('fn main(){'+raw_body(body)+'return 99}',profile)
            site=self.raw_site(binary)
            with Guest(binary) as guest:
                guest.bp(site);first=guest.until(site)
                self.assertEqual((first['rax'],first['rdx']),(1,3))
                guest.inject(-4)
                again=guest.until(site)
                self.assertEqual((again['rsi'],again['rdx']),(first['rsi'],3))
                guest.short_write(1)
                remainder=guest.until(site)
                self.assertEqual((remainder['rsi'],remainder['rdx']),(first['rsi']+1,2))
                guest.bp(site,False);self.assertEqual(guest.finish(),(0,b'ABC',b''))


if __name__=='__main__':
    unittest.main()
