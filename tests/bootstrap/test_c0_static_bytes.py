"""C0.39: independent static-byte wire, types, payloads and native output checks.

The first test packs its own graph and is RED on C0.38. Byte wants come from
literal fixtures/range(256), never from the compiler's decoder. No host compiler
participates. The generation selector must execute on each actual B/C pair.
"""
import hashlib
import os
from pathlib import Path
import random
import struct
import tempfile
import unittest

from c031_support import candidate_binary, encode_profile_source, run_native

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'bootstrap/compiler/c0/x86_64-linux'


def pack_wire(source, records, profile=0, version=12, dialect=None, tokens=15):
    if dialect is None:
        dialect = version - 1
    header = struct.pack('<4sBBHIIIIBBHI', b'NQAF', version, 32, 0,
                         len(source), len(records), len(records), tokens,
                         dialect, profile, 0, 0)
    return header + source + b''.join(
        struct.pack('<BBHIIIIIII', k, flags, 0, off, size, left, right, nxt, 0, 0)
        for k, flags, off, size, left, right, nxt in records)


def independent_wire(profile=0, literal=b'"NQL"', padding=0):
    source = b' ' * padding + b'fn main(){let s=' + literal + b' return write(s)}'
    first = padding
    quote = source.index(literal, first + 10)
    call = source.index(b'write(s)', quote + len(literal))
    records = [
        (39, 0, first + 3, 4, 0, 0, 4),
        (4, 0, first + 14, 1, 0, 0, 0),
        (58, 0, quote, len(literal), 0, 0, 0),
        (30, 0, first + 10, 3, 2, 3, 8),
        (4, 0, call + 6, 1, 0, 0, 0),
        (43, 0, call + 7, 1, 0, 5, 0),
        (42, 0, call, 5, 6, 0, 0),
        (32, 0, source.index(b'return', quote + len(literal)), 6, 7, 0, 9),
        (41, 0, len(source) - 1, 1, 0, 0, 0),
        (33, 0, first, 2, 1, 0, 0),
    ]
    return pack_wire(source, records, profile)


def change_node(wire, node, field, value):
    changed = bytearray(wire)
    at = 32 + struct.unpack_from('<I', wire, 8)[0] + (node - 1) * 32 + field
    if field in (0, 1):
        changed[at] = value
    elif field == 2:
        struct.pack_into('<H', changed, at, value)
    else:
        struct.pack_into('<I', changed, at, value)
    return bytes(changed)


def quoted_hex(data, uppercase=False):
    digits = b'0123456789ABCDEF' if uppercase else b'0123456789abcdef'
    return b'"' + b''.join(b'\\x' + bytes([digits[b >> 4], digits[b & 15]])
                            for b in data) + b'"'


class StaticBytesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontend = candidate_binary('C0_FRONTEND', STAGE / 'c0-frontend.seed')
        cls.backend = candidate_binary('C0_BACKEND', STAGE / 'c0-backend.seed')

    def frontend_wire(self, source, profile=0):
        inp = source if profile == 0 else encode_profile_source(source)
        result = run_native(self.frontend, inp)
        self.assertEqual((result.returncode, result.stderr), (0, b''))
        self.assertTrue(result.stdout.startswith(b'NQAF'))
        return result.stdout

    def compile_wire(self, wire):
        result = run_native(self.backend, wire)
        self.assertEqual((result.returncode, result.stderr), (0, b''))
        self.assertTrue(result.stdout.startswith(b'\x7fELF'))
        return result.stdout

    def compile(self, source, profile=0):
        return self.compile_wire(self.frontend_wire(source, profile))

    def execute(self, elf, **kwargs):
        with tempfile.TemporaryDirectory(prefix='c039-guest-') as directory:
            path = Path(directory) / 'program'
            path.write_bytes(elf)
            path.chmod(0o700)
            return run_native(path, **kwargs)

    def assert_rejected(self, wire, codes=(b'C0B-001', b'C0B-002', b'C0B-006', b'C0B-011')):
        result = run_native(self.backend, wire)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b'')
        self.assertTrue(any(b'error[' + c + b']' in result.stderr for c in codes),
                        result.stderr)
        self.assertRegex(result.stderr, rb'^input:[0-9]+:[0-9]+: error\[C0B-')
        return result

    def test_independent_static_binding_and_write(self):
        # Missing /12 or a wrong literal descriptor must fail this observable case.
        for profile in (0, 1):
            with self.subTest(profile=profile):
                elf = self.compile_wire(independent_wire(profile))
                run = self.execute(elf)
                self.assertEqual((run.returncode, run.stdout, run.stderr), (3, b'NQL', b''))

    def test_all_bytes_and_both_hex_cases(self):
        want = bytes(range(256))
        for profile in (0, 1):
            for upper in (False, True):
                source = (b'fn main(){let n=write(' + quoted_hex(want, upper) +
                          b')if n!=256{return 99}return 0}')
                run = self.execute(self.compile(source, profile))
                self.assertEqual((run.returncode, run.stdout, run.stderr), (0, want, b''))

    def test_empty_large_and_escaped_literals(self):
        fixtures = [
            (b'""', b''),
            (b'"A\\0B\\n\\r\\t\\\"\\\\"', bytes([65, 0, 66, 10, 13, 9, 34, 92])),
            (b'"' + b'NQL!' * 8192 + b'"', b'NQL!' * 8192),
        ]
        for literal, want in fixtures:
            for profile in (0, 1):
                source = (b'fn main(){let s=' + literal + b'let n=write(s)if n!=' +
                          str(len(want)).encode() + b'{return 99}return 0}')
                run = self.execute(self.compile(source, profile))
                self.assertEqual((run.returncode, run.stdout, run.stderr),
                                 (0, want, b''))

    def test_inferred_alias_assignment_scope_and_loop(self):
        source = (b'fn main(){let s="A" let copy=s write(copy)'
                  b'if 1{let s="B" write(s)}s="C" let n=2 '
                  b'while n{write(s)n=n-1}return 0}')
        for profile in (0, 1):
            run = self.execute(self.compile(source, profile))
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, b'ABCC', b''))

    def test_scalar_contexts_reject_strings_even_when_skipped(self):
        expressions = [b'"s"' + op + b'1' for op in
                       (b'+', b'-', b'*', b'/', b'%', b'&', b'|', b'^', b'<<',
                        b'>>', b'<', b'<=', b'>', b'>=', b'==', b'!=')]
        expressions += [b'-"s"', b'~"s"', b'not "s"', b'0 and "s"', b'1 or "s"']
        sources = [b'fn main(){return ' + e + b'}' for e in expressions]
        sources += [
            b'fn main(){return "s"}',
            b'fn main(){if "s"{return 1}else{return 0}}',
            b'fn main(){while "s"{return 1}return 0}',
            b'fn main(){let n=1 n="s" return 0}',
            b'fn main(){let s="s" s=1 return 0}',
            b'fn f(x){return x}fn main(){return f("s")}',
            b'fn main(){if 0{let n=1 n="s"}return 0}',
            b'fn main(){unsafe {# safety: type checking remains required\nreturn "s"}}',
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assert_rejected(self.frontend_wire(source), (b'C0B-012',))

    def test_intrinsic_argument_types_and_write_shadowing(self):
        for expression in [b'write(1)', b'byte_load("x")', b'byte_store(0,"x")',
                           b'input_read("x",1)', b'output_write(0,"x")',
                           b'error_write("x",0)']:
            source = b'fn main(){return ' + expression + b'}'
            self.assert_rejected(self.frontend_wire(source), (b'C0B-012',))
        for source in [b'fn write(x){return x+1}fn main(){return write(7)}',
                       b'fn main(){return write(7)}fn write(x){return x+1}']:
            wire = self.frontend_wire(source)
            self.assertLessEqual(wire[4], 11)
            run = self.execute(self.compile_wire(wire))
            self.assertEqual((run.returncode, run.stdout, run.stderr), (8, b'', b''))
        self.assert_rejected(self.frontend_wire(
            b'fn write(){return 9}fn main(){return write("x")}'), (b'C0B-008',))
        self.assert_rejected(self.frontend_wire(
            b'fn write(x){return x}fn main(){return write("x")}'), (b'C0B-012',))

    def test_literal_contents_do_not_change_native_permission(self):
        source = (b'fn main(){write("# // unsafe { } syscall6(1,0) \\\"")'
                  b'unsafe {# safety: owned arena only\n'
                  b'let s="} { // # \\\" unsafe" write(s)'
                  b'return byte_address(0,0)!=0}}')
        want = b'# // unsafe { } syscall6(1,0) "' + b'} { // # " unsafe'
        for profile in (0, 1):
            run = self.execute(self.compile(source, profile))
            self.assertEqual((run.returncode, run.stdout, run.stderr), (1, want, b''))
        bad = b'fn main(){write("unsafe {# safety: text only }")return byte_address(0,0)}'
        front = run_native(self.frontend, bad)
        self.assertEqual((front.returncode, front.stdout), (1, b''))
        self.assertIn(b'error[C0S-001]', front.stderr)

    def test_wire_versions_and_leaf_validation(self):
        wire = independent_wire()
        for version in range(1, 12):
            changed = bytearray(wire)
            changed[4] = version
            changed[24] = 4 if version == 5 else max(1, version-1)
            self.assert_rejected(bytes(changed))
        mutations = [(1, 1), (2, 1), (4, 0xffffffff), (8, 0xffffffff),
                     (12, 2), (16, 2), (20, 2), (24, 1), (28, 1)]
        for field, value in mutations:
            with self.subTest(field=field):
                self.assert_rejected(change_node(wire, 3, field, value))
        for literal in [b'NQL', b'"unclosed', b'"bad\\q"', b'"bad\\x0"',
                        b'"bad\\xgg"', b'"raw\n"', b'"raw\x80"']:
            self.assert_rejected(independent_wire(literal=literal), (b'C0B-011', b'C0B-006'))
        for cut in [0, 1, 4, 24, 31, 32, len(wire)-1]:
            self.assert_rejected(wire[:cut])
        self.assert_rejected(wire + b'\0')

    def test_independent_type_validation_before_output(self):
        wire = independent_wire()
        # A syntactically intact i64 leaf cannot pretend to be a string handle.
        source = b'fn main(){let s=12345 return write(s)}'
        old_source_size = struct.unpack_from('<I', wire, 8)[0]
        self.assertEqual(old_source_size, len(source))
        forged = bytearray(wire)
        forged[32:32+len(source)] = source
        forged = change_node(bytes(forged), 3, 0, 5)
        self.assert_rejected(forged, (b'C0B-012',))

    def test_literal_spans_cannot_alias_or_run_backwards(self):
        # Reusing a large source span must not multiply decoder work per node.
        source = b'fn main(){write("A")return write("B")}'
        wire = self.frontend_wire(source)
        size = struct.unpack_from('<I', wire, 8)[0]
        count = struct.unpack_from('<I', wire, 12)[0]
        leaves = [n for n in range(1, count+1) if wire[32+size+(n-1)*32] == 58]
        self.assertEqual(len(leaves), 2)
        first, second = source.index(b'"A"'), source.index(b'"B"')
        alias = change_node(wire, leaves[1], 4, first)
        self.assert_rejected(alias, (b'C0B-011',))
        swapped = change_node(change_node(wire, leaves[0], 4, second), leaves[1], 4, first)
        self.assert_rejected(swapped, (b'C0B-011',))

    def test_high_spans_and_high_node_ids(self):
        for profile in (0, 1):
            run = self.execute(self.compile_wire(independent_wire(profile, padding=70000)))
            self.assertEqual((run.returncode, run.stdout, run.stderr), (3, b'NQL', b''))
        source = b'fn main(){' + b'write("")' * 300 + b'let s="high" return write(s)}'
        wire = self.frontend_wire(source)
        self.assertGreater(struct.unpack_from('<I', wire, 12)[0], 255)
        run = self.execute(self.compile_wire(wire))
        self.assertEqual((run.returncode, run.stdout, run.stderr), (4, b'high', b''))

        # User declaration522 and builtin write522 have distinct resolution tags.
        # Assert the actual wire ID so a smaller graph cannot weaken this case.
        prefix = (b'fn d0(p){return 0}' +
                  b''.join(b'fn dummy' + str(i).encode() + b'(){return 0}'
                           for i in range(129)) + b'fn target(x){return x+1}')
        for profile in (0, 1):
            for argument in (b'7', b's'):
                with self.subTest(profile=profile, collision_argument=argument):
                    source = (prefix + b'fn main(){let s="M"write(s)return target(' +
                              argument + b')}')
                    wire = self.frontend_wire(source, profile)
                    self.assertEqual(wire[4], 12)
                    size = struct.unpack_from('<I', wire, 8)[0]
                    count = struct.unpack_from('<I', wire, 12)[0]
                    targets = []
                    for index in range(count):
                        record = 32 + size + index * 32
                        if wire[record] == 39:
                            offset, length = struct.unpack_from('<II', wire, record + 4)
                            if source[offset:offset+length] == b'target':
                                targets.append(index + 1)
                    self.assertEqual(targets, [522])
                    if argument == b's':
                        self.assert_rejected(wire, (b'C0B-012',))
                    else:
                        run = self.execute(self.compile_wire(wire))
                        self.assertEqual((run.returncode, run.stdout, run.stderr),
                                         (8, b'M', b''))

    def test_maximum_source_literal_keeps_full_byte_count(self):
        prefix = b'fn main(){let n=write("'
        tail = b'{return 99}return 0}'
        count = 262000
        for _ in range(3):
            suffix = b'")if n!=' + str(count).encode() + tail
            count = 262144 - len(prefix) - len(suffix)
        suffix = b'")if n!=' + str(count).encode() + tail
        source = prefix + b'A' * count + suffix
        self.assertEqual(len(source), 262144)
        run = self.execute(self.compile(source))
        self.assertEqual((run.returncode, run.stdout, run.stderr), (0, b'A' * count, b''))

    def test_exact_machine_descriptor_and_rx_layout(self):
        elf = self.compile_wire(independent_wire())
        # The unchanged user function entry is14bytes, beginning at238.
        self.assertEqual(elf[252:254], b'\x48\xb8')
        pointer = struct.unpack_from('<Q', elf, 254)[0]
        offset = pointer - 0x400000
        self.assertEqual(elf[262:269], b'\x48\x89\x85\xf0\xff\xff\xff')
        address, length = struct.unpack_from('<QQ', elf, offset)
        self.assertEqual((address, length), (pointer + 16, 3))
        self.assertEqual(elf[address-0x400000:address-0x400000+length], b'NQL')
        self.assertEqual(offset % 8, 0)
        adapter = (b'\x48\x8b\x37\x48\x8b\x57\x08\x48\x85\xd2\x74\x0b'
                   b'\x41\xba\x01\x00\x00\x00\xe9' +
                   struct.pack('<i', 0x600340 - (0x600b00 + 23)) +
                   b'\x31\xc0\xc3')
        self.assertEqual(elf[0x600b00:0x600b00+26], adapter)
        ph = struct.unpack_from('<IIQQQQQQ', elf, 64)
        self.assertEqual(ph[0:2], (1, 5))
        self.assertLessEqual(address + length, ph[3] + ph[5])
        headers = [struct.unpack_from('<IIQQQQQQ', elf, 64+i*56)
                   for i in range(struct.unpack_from('<H', elf, 56)[0])]
        self.assertFalse(any(h[0] in (2, 3) for h in headers))
        self.assertTrue(any(h[0] == 0x6474e551 and h[1] == 6 for h in headers))
        # write-only program must not select the arena-acquiring startup.
        self.assertEqual(struct.unpack_from('<Q', elf, 24)[0], 0x400000 + 176)

    def test_output_and_diagnostic_failures(self):
        source = b'fn main(){return write("bytes")}'
        elf = self.compile(source)
        with tempfile.TemporaryDirectory(prefix='c039-fds-') as directory:
            path = Path(directory) / 'readonly'
            path.write_bytes(b'')
            with path.open('rb') as ro:
                run = self.execute(elf, stdout=ro)
            self.assertEqual(run.returncode, 74)
            self.assertRegex(run.stderr, rb'^input:1:18: error\[C0R-006\]:')
            with path.open('rb') as ro, path.open('rb') as err:
                run = self.execute(elf, stdout=ro, stderr=err)
            self.assertEqual(run.returncode, 74)
            empty = self.compile(b'fn main(){return write("")}')
            with path.open('rb') as ro:
                run = self.execute(empty, stdout=ro)
            self.assertEqual((run.returncode, run.stderr), (0, b''))

    def test_static_handle_survives_calls_and_mapped_arena_io(self):
        source = (b'fn change(v){byte_store(0,v)return 5}'
                  b'fn main(){let s="live" let n=change(65)write(s)'
                  b'output_write(0,1)if n!=5{return 99}'
                  b'if byte_load(0)!=65{return 98}return 0}')
        for profile in (0, 1):
            elf = self.compile(source, profile)
            run = self.execute(elf)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, b'liveA', b''))
            with tempfile.TemporaryDirectory(prefix='c039-mapped-error-') as directory:
                path = Path(directory) / 'readonly'
                path.write_bytes(b'')
                with path.open('rb') as ro:
                    run = self.execute(elf, stdout=ro)
                self.assertEqual(run.returncode, 74)
                self.assertIn(b'error[C0R-006]', run.stderr)

    def test_bounded_wire_mutation_is_controlled(self):
        original = independent_wire()
        rng = random.Random(0xC039)
        for _ in range(48):
            # Only reserved fields are mutated: every member must be invalid.
            field = rng.choice([1, 2, 24, 28])
            value = rng.randint(1, 255)
            self.assert_rejected(change_node(original, 3, field, value))

    def test_generation_static_bytes_contract(self):
        # Exact selector must run against each actual generated B/C pair.
        source = (b'fn main(){let s="NQL\\0\\xff" let copy=s '
                  b'if write(copy)!=5{return 99}'
                  b'copy="!" write(copy) '
                  b'if (17%5)!=2{return 98}return 0}')
        run = self.execute(self.compile(source))
        self.assertEqual((run.returncode, run.stdout, run.stderr),
                         (0, b'NQL\0\xff!', b''))
        self.assert_rejected(self.frontend_wire(
            b'fn main(){let s="x" return s+1}'), (b'C0B-012',))


if __name__ == '__main__':
    unittest.main()

