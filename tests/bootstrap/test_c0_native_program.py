"""Actual standalone NolQu-L file utility; no host implementation of its I/O."""
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from c031_debugger import Guest, MASK
from c031_support import ROOT, candidate_binary, encode_profile_source, run_native


class NativeProgramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage = ROOT / 'bootstrap/compiler/c0/x86_64-linux'
        cls.frontend = candidate_binary('C0_FRONTEND', stage / 'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', stage / 'c0-backend.seed')
        cls.programs = tempfile.TemporaryDirectory(prefix='c032-cat-images-')
        cls.addClassCleanup(cls.programs.cleanup)
        cls.images = {}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='c032-cat-files-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def binary(self, profile):
        source_path = ROOT / 'examples/canonical/native_cat.nql'
        self.assertTrue(source_path.is_file(), 'NolQu-L native file reader is not implemented')
        source = source_path.read_bytes()
        key = (hashlib.sha256(source).hexdigest(), profile)
        if key not in self.images:
            parsed = run_native(self.frontend, encode_profile_source(source) if profile else source, timeout=120)
            self.assertEqual((parsed.returncode, parsed.stderr), (0, b''))
            result = run_native(self.backend, parsed.stdout, timeout=120)
            self.assertEqual((result.returncode, result.stderr), (0, b''))
            image = Path(self.programs.name) / f'native-cat-{int(profile)}'
            image.write_bytes(result.stdout)
            image.chmod(0o755)
            self.images[key] = image
        return self.images[key]

    def successful(self, profile, *, args=(), data=b'', expected=b''):
        result = run_native(self.binary(profile), data, args=args, cwd=self.directory)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b''))

    def raw_site(self, binary):
        data = binary.read_bytes()
        pattern = bytes.fromhex('4d8b4b280f05')
        self.assertEqual(data.count(pattern), 1)
        return 0x400000 + data.index(pattern) + len(pattern) - 2

    def step_syscall(self, guest, site):
        self.assertEqual(guest.regs()['rip'], site)
        self.assertEqual(guest.read_memory(site, 2), b'\x0f\x05')
        guest.bp(site, False)
        guest.bp(site + 2)
        after = guest.until(site + 2)
        guest.bp(site + 2, False)
        guest.bp(site)
        return after

    def test_stdin_and_literal_binary_files(self):
        data = b'\0' + bytes(range(256)) * 300
        first = self.directory / 'first file.bin'
        second = self.directory / os.fsdecode(b'\xff second.bin')
        empty = self.directory / 'empty'
        dash = self.directory / '-literal'
        delimiter = self.directory / '--'
        first.write_bytes(b'first\x00\xff\n')
        second.write_bytes(bytes(range(256)) * 140)
        empty.write_bytes(b'')
        dash.write_bytes(b'dash')
        delimiter.write_bytes(b'later delimiter is literal')
        originals = {p: p.read_bytes() for p in (first, second, empty, dash, delimiter)}
        for profile in (False, True):
            with self.subTest(profile=profile):
                self.successful(profile, data=data, expected=data)
                self.successful(profile)
                self.successful(profile, args=(os.fsencode(first), b'-', os.fsencode(second), os.fsencode(empty), b'-'),
                                data=data, expected=originals[first] + data + originals[second])
                self.successful(profile, args=(b'--', b'-literal', b'--'),
                                expected=originals[dash] + originals[delimiter])
                self.successful(profile, args=(os.fsencode(first), b'--'),
                                expected=originals[first] + originals[delimiter])
                self.successful(profile, args=(b'--',), data=data, expected=data)
        self.assertEqual({p: p.read_bytes() for p in originals}, originals)

    def test_missing_read_and_write_errors_stop(self):
        datafile = self.directory / 'owned-input'
        datafile.write_bytes(b'must stay unchanged\0\xff')
        original = datafile.read_bytes()
        for profile in (False, True):
            binary = self.binary(profile)
            for args in ((b'missing-file', os.fsencode(datafile)), (os.fsencode(self.directory),), (b'',)):
                with self.subTest(args=args, profile=profile):
                    result = run_native(binary, args=args, cwd=self.directory)
                    self.assertEqual((result.returncode, result.stdout), (1, b''))
                    self.assertIn(b'native_cat:', result.stderr)
            # A real read-only descriptor in stdout makes Linux write return EBADF.
            with open(os.devnull, 'rb') as wrong:
                result = run_native(binary, args=(os.fsencode(datafile),), stdout=wrong)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'native_cat:', result.stderr)
            self.assertEqual(datafile.read_bytes(), original)

    def test_acquired_descriptor_zero_is_closed(self):
        datafile = self.directory / 'input-for-fd-zero'
        datafile.write_bytes(b'owned descriptor zero')
        for profile in (False, True):
            binary = self.binary(profile)
            site = self.raw_site(binary)
            with Guest(binary, args=(os.fsencode(datafile), b'-'), timeout=30) as guest:
                guest.bp(site)
                opened = guest.until(site)
                self.assertEqual(opened['rax'], 257)
                # Execute a real close(0) before the original openat; then restore
                # its registers. This makes the acquired file descriptor zero.
                guest.setregs(rax=3, rdi=0)
                self.assertEqual(self.step_syscall(guest, site)['rax'], 0)
                guest.setregs(**opened)
                self.assertEqual(self.step_syscall(guest, site)['rax'], 0)
                closed = False
                for _ in range(12):
                    before = guest.until(site)
                    after = self.step_syscall(guest, site)
                    if before['rax'] == 3:
                        self.assertEqual((before['rdi'], after['rax']), (0, 0))
                        closed = True
                    if closed and before['rax'] == 0:
                        self.assertEqual((before['rdi'], after['rax']), (0, (-9) & MASK))
                        break
                else:
                    self.fail('acquired fd0 was not closed before the stdin operand')
                guest.bp(site, False)
                status, output, error = guest.finish()
                self.assertEqual((status, output), (1, datafile.read_bytes()))
                self.assertIn(b'native_cat:', error)

    def test_caller_retries_io_but_never_retries_close(self):
        payload = b'ABCDEF'
        datafile = self.directory / 'close-error-input'
        datafile.write_bytes(payload)
        for profile in (False, True):
            binary = self.binary(profile)
            site = self.raw_site(binary)
            with Guest(binary, data=payload, timeout=30) as guest:
                guest.bp(site)
                read = guest.until(site)
                self.assertEqual((read['rax'], read['rdi']), (0, 0))
                guest.inject(-4)  # Explicit synthetic EINTR before the real read.
                retry = guest.until(site)
                self.assertEqual(tuple(retry[r] for r in ('rax', 'rdi', 'rsi', 'rdx')),
                                 tuple(read[r] for r in ('rax', 'rdi', 'rsi', 'rdx')))
                self.assertEqual(self.step_syscall(guest, site)['rax'], len(payload))
                write = guest.until(site)
                self.assertEqual((write['rax'], write['rdi'], write['rdx']), (1, 1, len(payload)))
                guest.inject(-4)
                retry = guest.until(site)
                self.assertEqual((retry['rsi'], retry['rdx']), (write['rsi'], len(payload)))
                guest.short_write(2)  # The shortened write actually reaches Linux.
                remainder = guest.until(site)
                self.assertEqual((remainder['rax'], remainder['rsi'], remainder['rdx']),
                                 (1, write['rsi'] + 2, len(payload) - 2))
                self.assertEqual(self.step_syscall(guest, site)['rax'], len(payload) - 2)
                eof = guest.until(site)
                self.assertEqual(eof['rax'], 0)
                self.assertEqual(self.step_syscall(guest, site)['rax'], 0)
                guest.bp(site, False)
                self.assertEqual(guest.finish(), (0, payload, b''))
            with Guest(binary, args=(os.fsencode(datafile),), timeout=30) as guest:
                guest.bp(site)
                for _ in range(12):
                    before = guest.until(site)
                    if before['rax'] == 3:
                        # Linux releases fd even when a late close error occurs.
                        # Perform real close first, then inject only its reported
                        # result. Keeping the raw breakpoint detects any retry.
                        self.assertEqual(self.step_syscall(guest, site)['rax'], 0)
                        guest.setregs(rax=(-4) & MASK)
                        break
                    self.step_syscall(guest, site)
                else:
                    self.fail('utility never closed its acquired input')
                status, output, error = guest.finish()
                self.assertEqual((status, output), (1, payload))
                self.assertIn(b'native_cat:', error)

    def test_argument_copy_limit_is_explicit(self):
        for profile in (False, True):
            result = run_native(self.binary(profile), args=(b'x' * 4096,))
            self.assertEqual((result.returncode, result.stdout), (74, b''))
            self.assertIn(b'[C0R-009]', result.stderr)


if __name__ == '__main__':
    unittest.main()
