"""Wide AST validation and execution; canonical binaries do all compilation."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os
import platform
import subprocess
import struct
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from standard_fd_fault import invalidate_standard_fd

from c031_debugger import Guest, ProtocolError
from c031_support import (ROOT, assert_owned_graph, build_predecessors,
                         candidate_binary, decode_nqaf, encode_profile_source,
                         run_native)

ABI_PROBE_SOURCE = (b"fn sum(a,b,c,d,e,f){return a+b+c+d+e+f} "
                    b"fn main(){return sum(11,13,17,19,23,29)}")


def far_backward_edges(artifact, start=176, end=0x600000):
    # Disassembly is a test oracle, never a semantic bootstrap stage.
    native_android = sys.platform == "android"
    with tempfile.TemporaryDirectory(prefix="c031-disassembly-") as directory:
        binary = Path(directory) / "code"
        if native_android:
            # Termux's objdump is LLVM; native GNU binutils lacks x86 targets.
            # NASM's host-only decoder supplies real x86 instruction boundaries.
            binary.write_bytes(artifact[start:min(len(artifact), end)])
            command = ["ndisasm", "-b", "64", "-o", str(start), str(binary)]
        else:
            binary.write_bytes(artifact)
            command = ["objdump", "-D", "-b", "binary", "-m", "i386:x86-64",
                       "--insn-width=16", f"--start-address={start}",
                       f"--stop-address={min(len(artifact), end)}", str(binary)]
        def collect_edges(decoded):
            edges = []
            for raw_line in decoded:
                line = raw_line.decode("ascii")
                fields = line.split(None, 2) if native_android else line.split("\t")
                if len(fields) != 3:
                    continue
                address = fields[0].strip()
                if native_android:
                    if not all(c in "0123456789abcdefABCDEF" for c in address):
                        continue
                elif address.endswith(":"):
                    address = address[:-1]
                else:
                    continue
                instruction = bytes.fromhex(fields[1].strip())
                if len(instruction) != 5 or instruction[0] != 0xe9:
                    continue
                position = int(address, 16)
                if artifact[position:position + 5] != instruction:
                    raise AssertionError("disassembly does not match the artifact")
                displacement = struct.unpack_from("<i", artifact, position + 1)[0]
                target = position + 5 + displacement
                if displacement < -65536 and start <= target < position:
                    edges.append((position, target))
            return edges

        # Decode incrementally: text can exceed the inherited file-size limit.
        # The caller enforces the deadline while the reader drains the pipe.
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env={**os.environ, "LC_ALL": "C"}) as decoder:
            reader = None
            try:
                deadline = time.monotonic() + 60
                reader = ThreadPoolExecutor(max_workers=1)
                future = reader.submit(collect_edges, decoder.stdout)
                edges = future.result(timeout=60)
                status = decoder.wait(timeout=max(0, deadline - time.monotonic()))
                error = decoder.stderr.read()
                if status:
                    raise subprocess.CalledProcessError(status, command, stderr=error)
            finally:
                if decoder.poll() is None:
                    decoder.kill()
                decoder.wait(timeout=5)
                if reader is not None:
                    reader.shutdown(wait=True)
    return edges


class CapacityBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage = ROOT / "bootstrap/compiler/c0/x86_64-linux"
        cls.frontend = candidate_binary("C0_FRONTEND", stage / "c0-frontend.seed")
        cls.backend = candidate_binary("C0_BACKEND", stage / "c0-backend.seed")

    def ast(self, source, *, profile=False):
        if isinstance(source, str):
            source = source.encode("ascii")
        payload = encode_profile_source(source) if profile else source
        result = run_native(self.frontend, payload, timeout=120)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        header, nodes = decode_nqaf(result.stdout)
        self.assertEqual(header["source"], source)
        assert_owned_graph(header, nodes)
        return result.stdout

    def compile_ast(self, wire):
        return run_native(self.backend, wire, timeout=120)

    def compile_source(self, source):
        result = self.compile_ast(self.ast(source))
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        return result.stdout

    def execute(self, artifact, data=b"", **kwargs):
        with tempfile.TemporaryDirectory(prefix="c031-wide-runtime-") as directory:
            binary = Path(directory) / "program"
            binary.write_bytes(artifact)
            binary.chmod(0o755)
            return run_native(binary, data, timeout=120, **kwargs)

    def value(self, source, expected):
        result = self.execute(self.compile_source(source))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (expected & 255, b"", b""))

    def reject(self, wire, *, code, source=None, offset=None):
        result = self.compile_ast(wire)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(result.stdout), 0, "rejection emitted an executable prefix")
        self.assertRegex(result.stderr, rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0B-\d{3}\]: .+; .+\n$")
        self.assertIn(f"[C0B-{code:03d}]".encode(), result.stderr)
        if offset is not None:
            line = source[:offset].count(b"\n") + 1
            column = offset - source.rfind(b"\n", 0, offset)
            self.assertTrue(result.stderr.startswith(f"input:{line}:{column}: ".encode()),
                            result.stderr)
        return result

    def pack_wide(self, source, nodes, tokens, *, dialect=1, profile=0):
        header = struct.pack("<4sBBHIIIIBBHI", b"NQAF", 5, 32, 0, len(source),
                             len(nodes), len(nodes), tokens, dialect, profile, 0, 0)
        records = b"".join(struct.pack("<BBHIIIIIII", k, flags, 0, off, size,
                                       left, right, nxt, 0, 0)
                           for k, flags, off, size, left, right, nxt in nodes)
        return header + source + records

    def as_wide(self, source):
        header, nodes = decode_nqaf(self.ast(source))
        return self.pack_wide(header["source"], nodes, header["token_count"],
                              dialect=header["dialect"])

    def test_wide_source_executes(self):
        source = b"fn main(){return 7}".ljust(8193, b" ")
        wire = self.ast(source)
        self.assertEqual(decode_nqaf(wire)[0]["version"], 5)
        result = self.compile_ast(wire)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        executed = self.execute(result.stdout)
        self.assertEqual((executed.returncode, executed.stdout, executed.stderr),
                         (7, b"", b""))

    def test_absent_metadata_never_reads_before_its_table(self):
        source = (b"fn id(a){return a} fn main(){let x=1 if x {x=id(x+1)} "
                  b"return x}").ljust(8193, b" ")
        wire = self.ast(source)
        expected = self.compile_ast(wire)
        self.assertEqual((expected.returncode, expected.stderr), (0, b""))
        image = self.backend.read_bytes()
        signature = bytes.fromhex("4c01f631ff31c00f05")
        self.assertIn(signature, image)
        # The first literal read and the later dynamic read can share this tail;
        # verify the actual first-read registers at the breakpoint below.
        site = 0x400000 + image.index(signature) + len(signature) - 2
        # The small graph does not use the final pages of the preceding tables.
        # PROT_NONE makes an incidental absent-ID read observable, not just zero.
        for name, page in (("subtree", 0x260000), ("arity", 0x3a0000),
                           ("active binding", 0x3b0000), ("code offset", 0x57f000)):
            with self.subTest(table=name), Guest(self.backend, wire, timeout=30) as guest:
                guest.bp(site)
                before = guest.until(site)
                self.assertEqual((before["rax"], before["rdi"], before["rdx"]),
                                 (0, 0, 2359329))
                self.assertEqual(before["rsi"], before["r14"])
                guest.bp(site, False)
                guest.bp(site + 2)
                # Substitute one real mprotect syscall, then replay the original
                # read with all its registers restored. Compiler bytes are intact.
                guest.setregs(rax=10, rdi=before["r14"] + page, rsi=4096, rdx=0)
                after = guest.until(site + 2)
                self.assertEqual(after["rax"], 0, "guest mprotect failed")
                guest.bp(site + 2, False)
                guest.setregs(**before)
                try:
                    actual = guest.finish()
                except ProtocolError as error:
                    self.fail(f"absent-ID access crossed the {name} table boundary: {error}")
                self.assertEqual((actual[0], actual[2]), (0, b""))
                self.assertTrue(actual[1] == expected.stdout,
                                "sentinel guard changed executable bytes")

    def test_wide_header_and_graph_mutations(self):
        wire = self.as_wide(b"fn main(){let x=1 x=x+2 return x}")
        valid = self.compile_ast(wire)
        self.assertEqual((valid.returncode, valid.stderr), (0, b""))
        header, nodes = decode_nqaf(wire)
        source = header["source"]
        base = 32 + len(source)
        cases = []

        def field(label, position, size, value, code):
            altered = bytearray(wire)
            altered[position:position + size] = value.to_bytes(size, "little")
            self.assertNotEqual(altered, wire, label)
            cases.append((label, bytes(altered), code))

        for label, position, size, values in (
                ("version", 4, 1, (0, 6)), ("record size", 5, 1, (16, 31, 33)),
                ("flags", 6, 2, (1, 65535)),
                ("source length", 8, 4, (0, 262145, 0xffffffff)),
                ("node count", 12, 4, (0, 65537, 0xffffffff)),
                ("root", 16, 4, (0, len(nodes) - 1, len(nodes) + 1)),
                ("tokens", 20, 4, (0, 65537, 0xffffffff)),
                ("dialect", 24, 1, (0, 5)), ("profile", 25, 1, (2, 255)),
                ("reserved16", 26, 2, (1,)), ("reserved32", 28, 4, (1,))):
            for value in values:
                field(f"{label}={value}", position, size, value, 1)
        cases.append(("magic", b"X" + wire[1:], 1))
        for length in (0, 3, 15, 16, 31, len(wire) - 1):
            cases.append((f"truncated {length}", wire[:length], 1))
        cases.append(("trailing", wire + b"!", 1))
        for position, size in ((1, 1), (2, 2), (24, 4), (28, 4)):
            field(f"node reserved {position}", base + position, size, 1, 2)
        field("unknown kind", base, 1, 255, 2)
        field("wrapping anchor", base + 4, 4, 0xffffffff, 2)
        field("past source anchor", base + 4, 4, len(source), 2)
        field("zero anchor length", base + 8, 4, 0, 2)
        field("wrapping anchor length", base + 8, 4, 0xffffffff, 2)
        binary = next(i for i, n in enumerate(nodes) if n[0] == 15)
        field("cycle", base + binary * 32 + 12, 4, len(nodes), 2)
        field("shared child", base + binary * 32 + 16, 4, nodes[binary][4], 2)
        field("absent binary child", base + binary * 32 + 12, 4, 0, 2)
        field("out of table child", base + binary * 32 + 12, 4, 65536, 2)
        statement = next(i for i, n in enumerate(nodes) if n[0] == 30)
        field("broken physical chain", base + statement * 32 + 20, 4, 0, 2)
        field("root child", base + (len(nodes) - 1) * 32 + 12, 4, 0, 2)
        altered = bytearray(wire)
        integer = next(n for n in nodes if n[0] == 5)
        altered[32 + integer[2]] = ord("q")
        cases.append(("anchor spelling", bytes(altered), 6))
        for label, payload, code in cases:
            with self.subTest(mutation=label):
                self.reject(payload, code=code)

    def maximal_graph(self, permanent):
        # A validator/codegen fixture, not frontend output: anchors may repeat.
        # An odd binding count leaves room for a postorder binary expression
        # with exactly 65,536 total nodes, independently of lexer token limits.
        self.assertEqual(permanent % 2, 1)
        source = bytearray(b"fn main(){")
        nodes = []
        for index in range(permanent):
            name = f"x{index}".encode()
            offset = len(source)
            source.extend(b"let " + name + b"=0 ")
            left = len(nodes) + 1
            nodes.extend(((4, 0, offset + 4, len(name), 0, 0, 0),
                          (5, 0, offset + 5 + len(name), 1, 0, 0, 0),
                          (30, 0, offset, 3, left, left + 1, left + 5)))
        return_offset = len(source)
        source.extend(b"return 0+0}")
        zero = return_offset + 7
        plus = zero + 1
        expr_size = 65536 - len(nodes) - 2
        self.assertEqual(expr_size % 2, 1)
        nodes.append((5, 0, zero, 1, 0, 0, 0))
        left = len(nodes)
        for _ in range((expr_size - 1) // 2):
            nodes.append((5, 0, zero, 1, 0, 0, 0))
            right = len(nodes)
            nodes.append((15, 0, plus, 1, left, right, 0))
            left = len(nodes)
        last = 3 * permanent - 1
        nodes[last] = (*nodes[last][:6], 65535)
        nodes.append((32, 0, return_offset, 6, left, 0, 0))
        nodes.append((33, 0, 0, 2, 3, 0, 0))
        self.assertEqual(len(nodes), 65536)
        wire = self.pack_wide(bytes(source), nodes, 65536)
        header, decoded = decode_nqaf(wire)
        assert_owned_graph(header, decoded)
        return wire

    def test_independent_max_node_boundary(self):
        wire = self.maximal_graph(1)
        result = self.compile_ast(wire)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        executed = self.execute(result.stdout)
        self.assertEqual((executed.returncode, executed.stdout, executed.stderr), (0, b"", b""))
        oversized = bytearray(wire)
        struct.pack_into("<II", oversized, 12, 65537, 65537)
        oversized.extend(bytes(32))
        self.reject(bytes(oversized), code=1)
        self.reject(self.maximal_graph(511), code=7)

    def test_exact_stream_and_source_bounds(self):
        header, nodes = decode_nqaf(self.maximal_graph(1))
        source = header["source"].ljust(262144, b" ")
        wire = self.pack_wide(source, nodes, 65536)
        self.assertEqual(len(wire), 2359328)
        result = self.compile_ast(wire)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        executed = self.execute(result.stdout)
        self.assertEqual((executed.returncode, executed.stdout, executed.stderr), (0, b"", b""))
        self.reject(wire + b"!", code=1)

    def test_high_global_ids_use_local_frames(self):
        functions = []
        for index in range(24):
            body = " ".join(f"let x{i}={i}" for i in range(24))
            functions.append(f"fn f{index}(){{{body} return x23}}")
        source = " ".join(functions) + " fn main(){return f0()+f23()}"
        header, nodes = decode_nqaf(self.ast(source))
        self.assertEqual(header["version"], 5)
        self.assertGreater(max(i for i, n in enumerate(nodes, 1) if n[0] == 39), 512)
        self.value(source, 46)

    def test_frame_slots_exact_and_overflow(self):
        for declarations, code in ((511, None), (512, 7)):
            source = ("fn main(){" + " ".join(f"let x{i}={i}" for i in range(declarations))
                      + " return x510}").encode()
            with self.subTest(permanent=declarations):
                if code:
                    self.reject(self.ast(source), code=code)
                else:
                    self.value(source, 510)
        for declarations, code in ((505, None), (506, 7)):
            source = ("fn counted(a,b,c,d,e,z){"
                      + " ".join(f"let x{i}=7" for i in range(declarations))
                      + " return z} fn main(){return counted(1,2,3,4,5,6)}").encode()
            with self.subTest(parameters=6, declarations=declarations):
                if code:
                    self.reject(self.ast(source), code=code)
                else:
                    self.value(source, 6)

    def test_temporary_slots_exact_and_overflow(self):
        for depth, code in ((511, None), (512, 7)):
            source = (b"fn main(){return (" + b"1+(" * depth + b"1"
                      + b")" * depth + b")==512}")
            with self.subTest(live_values=depth + 1):
                if code:
                    self.reject(self.ast(source), code=code)
                else:
                    self.value(source, 1)

    def test_scope_exit_does_not_recycle_permanent_slots(self):
        for declarations, code in ((511, None), (512, 7)):
            source = (b"fn main(){" + b"if 1 {let x=0} " * declarations + b"return 7}")
            with self.subTest(declarations=declarations):
                if code:
                    self.reject(self.ast(source), code=code)
                else:
                    self.value(source, 7)

    def test_live_nested_call_arguments(self):
        source = (b"fn tick(){byte_store(0,byte_load(0)+1) return byte_load(0)} "
                  b"fn combine(a,b,c){return a*100+b*10+c} "
                  b"fn main(){let result=combine(tick(),combine(tick(),tick(),tick()),tick()) "
                  b"return (result==2445)*(byte_load(0)==5)}")
        self.value(source.ljust(8193, b" "), 1)

    def assert_native_abi(self, artifact):
        base = struct.unpack_from("<Q", artifact, 80)[0]
        self.assertEqual(base, 0x400000)
        prologue = bytes.fromhex("554889e54881ec0010000041ffc7")
        entries = []
        position = 175
        while (position := artifact.find(prologue, position + 1, 0x600000)) >= 0:
            entries.append(position)
        self.assertEqual(len(entries), 2)
        callee = entries[0]
        calls = []
        position = 175
        while (position := artifact.find(b"\xe8", position + 1,
                                         min(len(artifact) - 4, 0x600000))) >= 0:
            target = position + 5 + struct.unpack_from("<i", artifact, position + 1)[0]
            if target == callee:
                calls.append(position)
        self.assertEqual(len(calls), 1)
        after_call = calls[0] + 5
        self.assertEqual(artifact[after_call:after_call + 3], b"\x48\x89\x85")
        with tempfile.TemporaryDirectory(prefix="c031-abi-") as directory:
            binary = Path(directory) / "program"
            binary.write_bytes(artifact)
            binary.chmod(0o755)
            with Guest(binary) as guest:
                self.assertEqual(guest.read_memory(base + callee, len(prologue)), prologue)
                guest.bp(base + callee)
                guest.bp(base + callee + len(prologue))
                guest.bp(base + after_call)
                before = guest.until(base + callee)
                self.assertEqual(before["rsp"] % 16, 8)
                self.assertEqual(tuple(before[r] for r in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")),
                                 (11, 13, 17, 19, 23, 29))
                preserved = dict(rbx=0x1122334455667788, r12=0x2233445566778899,
                                 r13=0x33445566778899aa, r14=0x445566778899aabb)
                guest.setregs(**preserved)
                guest.bp(base + callee, False)
                inside = guest.until(base + callee + len(prologue))
                self.assertEqual(inside["rsp"] % 16, 0)
                self.assertEqual(inside["rbp"], before["rsp"] - 8)
                self.assertEqual(inside["rsp"], inside["rbp"] - 4096)
                self.assertEqual(inside["r15"], before["r15"] + 1)
                guest.bp(base + callee + len(prologue), False)
                returned = guest.until(base + after_call)
                for register, value in preserved.items():
                    self.assertEqual(returned[register], value, register)
                self.assertEqual(returned["rbp"], before["rbp"])
                self.assertEqual(returned["r15"], before["r15"])
                self.assertEqual(returned["rsp"], before["rsp"] + 8)
                self.assertEqual(returned["rax"], 112)
                guest.bp(base + after_call, False)
                self.assertEqual(guest.finish(), (112, b"", b""))

    def test_legacy_native_abi_probe_control(self):
        # The same debugger probe must work before wide codegen is available.
        self.assert_native_abi(self.compile_source(ABI_PROBE_SOURCE))

    def test_wide_native_abi_and_frame_alignment(self):
        self.assert_native_abi(self.compile_source(ABI_PROBE_SOURCE.ljust(8193, b" ")))

    def test_wide_call_depth_remains_bounded(self):
        for argument, expected in ((62, 7), (63, 70)):
            source = (b"fn down(n){if n>0 {return down(n-1)} return 7} "
                      + f"fn main(){{return down({argument})}}".encode()).ljust(8193, b" ")
            result = self.execute(self.compile_source(source))
            self.assertEqual((result.returncode, result.stdout), (expected, b""))
            if expected == 7:
                self.assertEqual(result.stderr, b"")
            else:
                self.assertIn(b"[C0R-003]", result.stderr)

    def test_intrinsic_ids_do_not_alias_user_nodes(self):
        for target in range(513, 518):
            statements = (target - 5) // 3
            if (target - 5 - 3 * statements) % 2:
                statements -= 1
            adds = (target - 5 - 3 * statements) // 2
            source = (b"fn pad(){let x=0 " + b"x=0 " * (statements - 1)
                      + b"return 0" + b"+0" * adds
                      + b"} fn ordinary(){return 7} fn main(){return ordinary()}")
            with self.subTest(entry_id=target):
                header, nodes = decode_nqaf(self.ast(source))
                self.assertEqual(header["version"], 5)
                entry = next(i for i, n in enumerate(nodes, 1) if n[0] == 39
                             and header["source"][n[2]:n[2] + n[3]] == b"ordinary")
                self.assertEqual(entry, target)
                self.value(source, 7)

    def test_runtime_location_above_four_digits(self):
        body = b"fn main(){return 7/(3-3)}"
        for prefix in (b"\n" * 14000, b" " * 70000,
                       b"\n" * (262144 - len(body)), b" " * (262144 - len(body))):
            with self.subTest(prefix=prefix[:1]):
                source = prefix + body
                executed = self.execute(self.compile_source(source))
                self.assertEqual((executed.returncode, executed.stdout), (70, b""))
                offset = source.index(b"/")
                line = source[:offset].count(b"\n") + 1
                column = offset - source.rfind(b"\n", 0, offset)
                self.assertTrue(executed.stderr.startswith(
                    f"input:{line}:{column}: error[C0R-001]: ".encode()), executed.stderr)
                missing = b"fn main(){return missing}"
                source = prefix[:262144 - len(missing)] + missing
                self.reject(self.ast(source), code=3, source=source, offset=source.index(b"missing"))

    def test_wide_code_and_rel32_bounds(self):
        # Many late anchors also exercise the required indexed line lookup.
        source = (b"\n" * 140000 + b"fn main(){let i=0 while i<2 {"
                  + b"i=i+0 " * 5000 + b"i=i+1} return i}")
        artifact = self.compile_source(source)
        result = self.execute(artifact)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (2, b"", b""))
        self.assertLessEqual(len(artifact), 8388608)
        self.assertTrue(far_backward_edges(artifact),
                        "no wide backward branch in the code region")
        source = (b"fn first(){return last()} fn pad(){let x=0 " + b"x=x+0 " * 1000
                  + b"return x} fn last(){return 7} fn main(){return first()}")
        self.value(source, 7)

    def test_wide_name_resolution_and_scope(self):
        name = b"a" * 65536
        self.value(b"fn main(){let " + name + b"=7 return " + name + b"}", 7)
        self.value(b"fn " + name + b"(){return 7} fn main(){return " + name + b"()}", 7)
        source = b"fn main(){let " + name[:-1] + b"=7 return " + name + b"}"
        self.reject(self.ast(source), code=3, source=source, offset=source.index(b"return ") + 7)
        source = b"fn " + name[:-1] + b"(){return 7} fn main(){return " + name + b"()}"
        self.reject(self.ast(source), code=8)
        self.value((b"fn main(){let x=7 let out=0 if 1 {let x=x+1 out=x} "
                    b"return out*10+x}").ljust(8193, b" "), 87)
        for body, code in ((b"let x=x return x", 3),
                           (b"let x=1 let x=2 return x", 4),
                           (b"if 1 {let x=7} return x", 3)):
            self.reject(self.ast((b"fn main(){" + body + b"}").ljust(8193, b" ")), code=code)
        source = b"fn byte_load(){return 7} fn main(){return byte_load(0)}".ljust(8193, b" ")
        self.reject(self.ast(source), code=8)

    def test_wide_literal_spans(self):
        source = b"fn main(){return " + b"0" * 65535 + b"7}"
        self.value(source, 7)
        source = b" " * 70000 + b"fn main(){return 9223372036854775808}"
        self.reject(self.ast(source), code=5, source=source,
                    offset=source.index(b"9223372036854775808"))

    def test_large_default_source_keeps_64k(self):
        source = b"fn main(){return byte_load(65536)}".ljust(8193, b" ")
        executed = self.execute(self.compile_source(source))
        self.assertEqual((executed.returncode, executed.stdout), (70, b""))
        self.assertIn(b"[C0R-004]", executed.stderr)

    def test_wide_checked_arithmetic_and_comparisons(self):
        checks = [(b"7+3", b"10"), (b"7-3", b"4"), (b"7*3", b"21"),
                  (b"(0-7)/3", b"0-2"), (b"7/(0-3)", b"0-2"),
                  (b"(0-7)/(0-3)", b"2")]
        for operator, true_rhs, false_rhs in ((b"<", b"1", b"0-2"),
                                              (b"<=", b"0-1", b"0-2"),
                                              (b">", b"0-2", b"1"),
                                              (b">=", b"0-1", b"1"),
                                              (b"==", b"0-1", b"1"),
                                              (b"!=", b"1", b"0-1")):
            checks.extend(((b"(0-1)" + operator + b"(" + true_rhs + b")", b"1"),
                           (b"(0-1)" + operator + b"(" + false_rhs + b")", b"0")))
        body = b" ".join(b"if (" + expression + b")!=(" + expected + b"){return "
                         + str(index).encode() + b"}" for index, (expression, expected)
                         in enumerate(checks, 1))
        self.value((b"fn main(){" + body + b" return 0}").ljust(8193, b" "), 0)
        maximum = b"9223372036854775807"
        minimum = b"(0-" + maximum + b"-1)"
        for expression in (maximum + b"+1", minimum + b"-1", maximum + b"*2",
                           b"7/(3-3)", minimum + b"/(0-1)"):
            with self.subTest(expression=expression):
                source = (b"fn main(){let unused=" + expression + b" return 0}").ljust(8193, b" ")
                result = self.execute(self.compile_source(source))
                self.assertEqual((result.returncode, result.stdout), (70, b""))
                self.assertIn(b"[C0R-001]", result.stderr)

    def test_wide_stream_helpers_and_failed_diagnostics(self):
        source = (b"fn main(){byte_store(65535,298) let n=input_read(0,4) "
                  b"output_write(0,n) error_write(0,n) return n+byte_load(65535)}").ljust(8193, b" ")
        artifact = self.compile_source(source)
        result = self.execute(artifact, b"ABCD")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (46, b"ABCD", b"ABCD"))
        for descriptor, code, output in ((0, 5, b""), (1, 6, b""), (2, None, b"ABCD")):
            with self.subTest(closed_fd=descriptor):
                result = self.execute(artifact, b"ABCD",
                                      preexec_fn=lambda fd=descriptor: invalidate_standard_fd(fd))
                self.assertEqual((result.returncode, result.stdout), (74, output))
                if code is None:
                    self.assertEqual(result.stderr, b"")
                else:
                    self.assertIn(f"[C0R-{code:03d}]".encode(), result.stderr)
        source = (b"fn main(){let n=input_read(65536,0) "
                  b"return n+output_write(65536,0)+error_write(65536,0)}").ljust(8193, b" ")
        self.value(source, 0)
        source = b"fn main(){return 1/0}".ljust(8193, b" ")
        result = self.execute(self.compile_source(source), preexec_fn=lambda: invalidate_standard_fd(2))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (74, b"", b""))

    def test_compiler_profile_is_explicit_and_validated(self):
        # Explicit profile 1 must execute above the legacy bound; malformed IR
        # and overflowing literals still fail before any executable is emitted.
        source = b"fn main(){byte_store(65536,42) return byte_load(65536)}"
        result = self.compile_ast(self.ast(source, profile=True))
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertTrue(result.stdout.startswith(b"\x7fELF"))
        executed = self.execute(result.stdout)
        self.assertEqual((executed.returncode, executed.stdout, executed.stderr), (42, b"", b""))
        source = b"fn main(){return 7}"
        wire = self.ast(source, profile=True)
        header, nodes = decode_nqaf(wire)
        bad_kind = bytearray(wire)
        bad_kind[32 + len(source)] = 255
        self.reject(bytes(bad_kind), code=2)
        bad_anchor = bytearray(wire)
        integer = next(n for n in nodes if n[0] == 5)
        bad_anchor[32 + integer[2]] = ord("q")
        self.reject(bytes(bad_anchor), code=6, source=source, offset=integer[2])
        source = b"fn main(){return 9223372036854775808}"
        self.reject(self.ast(source, profile=True), code=5,
                    source=source, offset=source.index(b"922"))

    def test_legacy_byte_parity_and_limits(self):
        sources = [
            b"fn main(){return 7}",
            b"fn main(){let a=5 let b=3 a=a*b+2 return a-b}",
            b"fn main(){return (0-7)/3}",
            b"fn main(){let i=0 while i<4 {if i==2 {i=i+1} else {i=i+2}} return i}",
            b"fn add(a,b){return a+b} fn main(){return add(2,add(3,4))}",
            b"fn sum(a,b,c,d,e,f){return a+b+c+d+e+f} fn main(){return sum(1,2,3,4,5,6)}",
            b"fn main(){return later()} fn later(){return 7}",
            b"fn main(){byte_store(0,65) output_write(0,1) return byte_load(0)}",
            b"fn main(){let n=input_read(0,4) output_write(0,n) error_write(0,n) return n}",
            b"fn main(){\r\n# comment\r\nreturn 1;\r\n}\r\n",
            b"fn main(){return 7}".ljust(8192, b" "),
            b"fn main(){return 0" + b"+0" * 252 + b"}",
            b"fn main(){return missing}",
            b"fn main(){let x=1 let x=2 return x}",
            b"fn main(){return 9223372036854775808}",
        ]
        with tempfile.TemporaryDirectory(prefix="c031-backend-parity-") as directory:
            old = build_predecessors(Path(directory))
            for source in sources:
                with self.subTest(source=source[:70]):
                    ast = run_native(old["frontend"], source)
                    self.assertEqual((ast.returncode, ast.stderr), (0, b""))
                    self.assertEqual(self.ast(source), ast.stdout)
                    expected = run_native(old["backend"], ast.stdout)
                    actual = self.compile_ast(ast.stdout)
                    self.assertEqual((actual.returncode, actual.stderr),
                                     (expected.returncode, expected.stderr))
                    self.assertEqual(len(actual.stdout), len(expected.stdout))
                    self.assertTrue(actual.stdout == expected.stdout, "legacy ELF bytes changed")
                    if actual.returncode == 0:
                        before = self.execute(expected.stdout, b"ABCD")
                        after = self.execute(actual.stdout, b"ABCD")
                        self.assertEqual((after.returncode, after.stdout, after.stderr),
                                         (before.returncode, before.stdout, before.stderr))
            ast = bytearray(self.ast(sources[0]))
            struct.pack_into("<H", ast, 14, 513)
            self.reject(bytes(ast), code=1)
            ast = bytearray(self.ast(sources[0]))
            struct.pack_into("<HH", ast, 10, 513, 513)
            ast.extend(bytes(16 * 510))
            self.reject(bytes(ast), code=1)
            source = sources[0].ljust(8192, b" ")
            ast = bytearray(self.ast(source))
            ast[16 + len(source):16 + len(source)] = b" "
            struct.pack_into("<H", ast, 8, 8193)
            self.reject(bytes(ast), code=1)

    def test_fragmented_stream_waits_for_eof(self):
        wire = self.ast(b"fn main(){return 7}".ljust(8193, b" "))
        expected = self.compile_ast(wire)
        self.assertEqual((expected.returncode, expected.stderr), (0, b""))
        for tail in (b"", b"!"):
            with self.subTest(trailing=tail):
                runner = ([] if platform.machine() == "x86_64" else ["qemu-x86_64"])
                release, ready, emitted = threading.Event(), threading.Event(), threading.Event()
                with subprocess.Popen(runner + [str(self.backend)], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE) as child:
                    def feed():
                        try:
                            previous = 0
                            for stop in (1, 4, 15, 16, 31, 32, len(wire)):
                                child.stdin.write(wire[previous:stop])
                                child.stdin.flush()
                                previous = stop
                                time.sleep(0.01)
                            ready.set()
                            if not release.wait(30):
                                raise TimeoutError("backend EOF probe was not released")
                            child.stdin.write(tail)
                        finally:
                            child.stdin.close()

                    def drain_output():
                        chunks = []
                        first = child.stdout.read(1)
                        if first:
                            emitted.set()
                            chunks.append(first)
                        while chunk := child.stdout.read(65536):
                            emitted.set()
                            chunks.append(chunk)
                        return b"".join(chunks)

                    with ThreadPoolExecutor(max_workers=3) as pool:
                        writer = pool.submit(feed)
                        output = pool.submit(drain_output)
                        error = pool.submit(child.stderr.read)
                        try:
                            self.assertTrue(ready.wait(30), "backend stopped reading a valid stream")
                            self.assertIsNone(child.poll(), "backend accepted a read boundary as EOF")
                            self.assertFalse(emitted.wait(0.15), "backend emitted before EOF")
                            release.set()
                            child.wait(timeout=120)
                            writer.result(timeout=5)
                            actual_output, actual_error = output.result(timeout=5), error.result(timeout=5)
                        finally:
                            release.set()
                            if child.poll() is None:
                                child.kill()
                            child.wait(timeout=5)
                    if tail:
                        self.assertEqual((child.returncode, len(actual_output)), (1, 0))
                        self.assertIn(b"[C0B-001]", actual_error)
                    else:
                        self.assertEqual((child.returncode, actual_error), (0, b""))
                        self.assertTrue(actual_output == expected.stdout)


class BackendStorageTests(unittest.TestCase):
    def test_branch_inspector_reader_startup_failure_reaps_decoder(self):
        real_popen = subprocess.Popen
        for fault in ("construction", "submit"):
            with self.subTest(fault=fault):
                children = []

                def launch(command, **options):
                    child = real_popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                       **options)
                    wait = child.wait
                    children.append((child, wait))

                    def guarded_wait(timeout=None):
                        if timeout is None and child.poll() is None:
                            raise AssertionError("unbounded decoder wait before cleanup")
                        return wait(timeout=timeout)

                    child.wait = guarded_wait
                    return child

                executor = mock.MagicMock()
                executor.__enter__.return_value = executor
                executor.submit.side_effect = RuntimeError("fixture reader startup")
                factory = mock.Mock(return_value=executor)
                if fault == "construction":
                    factory.side_effect = RuntimeError("fixture reader startup")
                try:
                    with mock.patch.object(subprocess, "Popen", side_effect=launch), \
                            mock.patch(__name__ + ".ThreadPoolExecutor", factory):
                        with self.assertRaisesRegex(RuntimeError, "fixture reader startup"):
                            far_backward_edges(b"\x90", start=0)
                    self.assertEqual(len(children), 1)
                    self.assertIsNotNone(children[0][0].returncode)
                finally:
                    for child, wait in children:
                        if child.poll() is None:
                            child.kill()
                        wait(timeout=5)
                        child.stdout.close()
                        child.stderr.close()

    def test_branch_inspector_rejects_opcode_inside_immediate(self):
        artifact = b"\x90" * 70000 + bytes.fromhex("48 b8 e9 fb ff fe ff 00 00 00 c3")
        self.assertEqual(far_backward_edges(artifact), [])

    def test_branch_inspector_accepts_real_instruction(self):
        artifact = b"\x90" * 70000 + b"\xe9" + struct.pack("<i", 176 - 70005)
        self.assertEqual(far_backward_edges(artifact), [(70000, 176)])

    def test_constructed_maximal_graph_is_owned_postorder(self):
        fixtures = CapacityBackendTests("test_independent_max_node_boundary")
        for permanent in (1, 511):
            with self.subTest(permanent=permanent):
                header, nodes = decode_nqaf(fixtures.maximal_graph(permanent))
                self.assertEqual((header["node_count"], header["root_id"]), (65536, 65536))
                self.assertEqual(sum(node[0] == 30 for node in nodes), permanent)
                statements = [i for i, n in enumerate(nodes, 1) if n[0] in (30, 32)]
                expected_next = dict(zip(statements, statements[1:] + [0]))
                anchors = {5: b"0", 15: b"+", 30: b"let", 32: b"return", 33: b"fn"}
                for node_id, node in enumerate(nodes, 1):
                    kind, flags, offset, length, left, right, nxt = node
                    self.assertEqual(flags, 0)
                    self.assertLess(left, node_id)
                    self.assertLess(right, node_id)
                    self.assertEqual(nxt, expected_next.get(node_id, 0))
                    lexeme = header["source"][offset:offset + length]
                    if kind == 4:
                        self.assertRegex(lexeme, rb"^x[0-9]+$")
                    else:
                        self.assertEqual(lexeme, anchors[kind])

    def test_backend_storage_layout_is_bounded_and_disjoint(self):
        # Contract arithmetic; actual compiler address uses need independent review.
        regions = [
            ("input", 0, 0x241000, 2359329),
            ("identifier roles", 0x241000, 0x251000, 65536),
            ("ownership", 0x251000, 0x261000, 65536),
            ("subtrees/bindings", 0x261000, 0x2A1000, 65536 * 4),
            ("kind data", 0x2A1000, 0x3A1000, 65536 * 16),
            ("arity", 0x3A1000, 0x3B1000, 65536),
            ("active scopes", 0x3B1000, 0x3B3000, 8192),
            ("function entries", 0x3B3000, 0x3F3000, 65536 * 4),
            ("prefix spans", 0x3F3000, 0x473000, 65536 * 8),
            ("line starts", 0x473000, 0x573004, 262145 * 4),
            ("code offsets", 0x580000, 0x5C0000, 65536 * 4),
            ("frame slots", 0x5C0000, 0x5E0000, 65536 * 2),
            ("permanent counts", 0x5E0000, 0x600000, 65536 * 2),
            ("state", 0x680000, 0x690000, 65536),
            ("inactive", 0x7FF000, 0x7FF100, 256),
            ("ELF", 0x800000, 0x1000000, 8388608),
        ]
        previous_end = 0
        for name, start, end, capacity in regions:
            with self.subTest(region=name):
                self.assertGreaterEqual(start, previous_end)
                self.assertGreaterEqual(end - start, capacity)
                self.assertGreater(end, start)
                self.assertLessEqual(end, 16777216)
                previous_end = end


if __name__ == "__main__":
    unittest.main()
