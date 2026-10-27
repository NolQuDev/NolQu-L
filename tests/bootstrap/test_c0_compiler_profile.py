"""C0 mapped runtime; canonical compilers produce every executable tested here."""

from pathlib import Path
import os
import shutil
import struct
import subprocess
import tempfile
import unittest

from standard_fd_fault import invalidate_standard_fd
from c031_debugger import Guest
from c031_support import (ROOT, candidate_binary, decode_nqaf,
                         encode_profile_source, run_native)

CAPACITY = 16777216


class CompilerProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage = ROOT / "bootstrap/compiler/c0/x86_64-linux"
        cls.frontend = candidate_binary("C0_FRONTEND", stage / "c0-frontend.seed")
        cls.backend = candidate_binary("C0_BACKEND", stage / "c0-backend.seed")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="c031-c0-profile-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.sequence = 0

    def compile_source(self, source, *, profile=True):
        if isinstance(source, str):
            source = source.encode("ascii")
        framed = encode_profile_source(source) if profile else source
        parsed = run_native(self.frontend, framed, timeout=120)
        self.assertEqual((parsed.returncode, parsed.stderr), (0, b""))
        header, _ = decode_nqaf(parsed.stdout)
        self.assertEqual((header["source"], header["runtime_profile"]),
                         (source, int(profile)))
        return run_native(self.backend, parsed.stdout, timeout=120)

    def program(self, source, *, profile=True):
        compiled = self.compile_source(source, profile=profile)
        self.assertEqual((compiled.returncode, compiled.stderr), (0, b""))
        self.assertTrue(compiled.stdout.startswith(b"\x7fELF"))
        self.sequence += 1
        binary = self.directory / f"program-{self.sequence}"
        binary.write_bytes(compiled.stdout)
        binary.chmod(0o755)
        return binary

    def test_profile_byte_above_legacy_bound(self):
        source = b"fn main(){byte_store(65536,42);return byte_load(65536)}"
        result = run_native(self.program(source))
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (42, b"", b""))
        result = run_native(self.program(source, profile=False))
        self.assertEqual((result.returncode, result.stdout), (70, b""))
        self.assertIn(b"[C0R-004]", result.stderr)

    def site(self, binary, prefix):
        image = binary.read_bytes()
        pattern = bytes.fromhex(prefix) + b"\x0f\x05"
        self.assertEqual(image.count(pattern), 1, pattern.hex())
        return 0x400000 + image.index(pattern) + len(pattern) - 2

    def sites(self, binary):
        return dict(
            mmap=self.site(binary, "49c7c0ffffffff4531c9"),
            munmap=self.site(binary, "b80b000000498b3ebe00000001"),
            exit=self.site(binary, "498b7e10b83c000000"),
            diagnose=self.site(binary, "b801000000bf02000000"),
            signal=self.site(binary, "31d241ba08000000"),
            read=self.site(binary, "31ff31c0"),
            write=self.site(binary, "4489d74989d2b801000000"),
        )

    def acquire(self, guest, sites):
        guest.bp(sites["mmap"])
        registers = guest.until(sites["mmap"])
        self.assertEqual(tuple(registers[r] for r in
                               ("rax", "rdi", "rsi", "rdx", "r10", "r8", "r9")),
                         (9, 0, CAPACITY, 3, 0x22, (1 << 64) - 1, 0))
        self.assertEqual(registers["r14"] % 16, 0)
        self.assertEqual(guest.read_memory(registers["r14"], 32), bytes(32))
        guest.bp(sites["mmap"], False)
        guest.bp(sites["mmap"] + 2)
        after = guest.until(sites["mmap"] + 2)
        self.assertLess(after["rax"], 1 << 63)
        guest.bp(sites["mmap"] + 2, False)
        # Any unexpected second allocation is an unexpected breakpoint.
        guest.bp(sites["mmap"])
        return after["rax"]

    def cleanup(self, guest, sites, status, *, acquired=True, base=None):
        guest.bp(sites["munmap"])
        if acquired:
            registers = guest.until(sites["munmap"])
            state = struct.unpack("<4Q", guest.read_memory(registers["r14"], 32))
            self.assertEqual((registers["rax"], registers["rdi"], registers["rsi"]),
                             (11, state[0], CAPACITY))
            if base is not None:
                self.assertEqual(state[0], base)
            self.assertEqual(state[1:3], (0, status))
            guest.bp(sites["munmap"], False)
            guest.bp(sites["munmap"] + 2)
            after = guest.until(sites["munmap"] + 2)
            self.assertEqual(after["rax"], 0)
            guest.bp(sites["munmap"] + 2, False)
            guest.bp(sites["munmap"])
        guest.bp(sites["exit"])
        registers = guest.until(sites["exit"])
        self.assertEqual(registers["rdi"], status)
        state = struct.unpack("<4Q", guest.read_memory(registers["r14"], 32))
        self.assertEqual(state[1:3], (0, status))
        guest.bp(sites["exit"], False)
        return guest.finish()

    def test_profile_bounds_zero_memory_and_byte_truncation(self):
        cells = ((0, 257, 1), (65535, 298, 42), (65536, 383, 127),
                 (CAPACITY - 1, 510, 254))
        initial = " ".join(f"let z{i}=byte_load({index})"
                           for i, (index, _, _) in enumerate(cells))
        stores = " ".join(f"let n{i}=byte_store({index},{value})"
                          for i, (index, value, _) in enumerate(cells))
        predicates = "*".join(f"(z{i}==0)*(n{i}==0)*(byte_load({index})=={expected})"
                              for i, (index, _, expected) in enumerate(cells))
        # All cells coexist with distinct values: aliasing cannot pass. Each
        # result is compared independently inside the guest, before exit masks.
        result = run_native(self.program(f"fn main(){{{initial} {stores} return {predicates}}}"))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, b"", b""))

        binary = self.program("fn main(){byte_store(16777215,0-1) "
                              "return byte_load(16777215)==255}")
        result = run_native(binary)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, b"", b""))
        # Negative control: execute the real load/ret, then substitute a signed
        # -1 return in registers only. The guest predicate must now fail.
        with Guest(binary) as guest:
            entry = 0x400000 + 6267456 + 24608
            guest.bp(entry)
            registers = guest.until(entry)
            successor = struct.unpack("<Q", guest.read_memory(registers["rsp"], 8))[0]
            guest.bp(entry, False)
            guest.bp(successor)
            returned = guest.until(successor)
            self.assertEqual(returned["rax"], 255)
            guest.setregs(rax=-1)
            guest.bp(successor, False)
            self.assertEqual(guest.finish(), (0, b"", b""))

    def test_shared_arena_and_nested_argument_order(self):
        source = ("fn tick(){let n=byte_load(65536)+1 byte_store(65536,n) return n} "
                  "fn mix(a,b,c){return a*100+b*10+c} "
                  "fn main(){return mix(tick(),tick(),tick())+byte_load(65536)}")
        result = run_native(self.program(source))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (126, b"", b""))

    def test_invalid_ranges_are_located_and_cleaned(self):
        calls = [f"{name}({index}{tail})"
                 for name, tail in (("byte_load", ""), ("byte_store", ",1"))
                 for index in ("16777216", "16777217", "0-1", "9223372036854775807",
                               "0-9223372036854775807-1")]
        calls += [f"{name}({args})"
                  for name in ("input_read", "output_write", "error_write")
                  for args in ("16777216,1", "16777215,2", "16777217,0", "0-1,0",
                               "0,0-1", "0,9223372036854775807",
                               "9223372036854775807,9223372036854775807")]
        for call in calls:
            with self.subTest(call=call):
                binary = self.program("fn main(){\n return " + call + "\n}")
                sites = self.sites(binary)
                with Guest(binary) as guest:
                    base = self.acquire(guest, sites)
                    result = self.cleanup(guest, sites, 70, base=base)
                self.assertEqual(result[:2], (70, b""))
                self.assertRegex(result[2], rb"^input:2:9: error\[C0R-004\]: .+; .+\n$")

    def test_empty_end_ranges_do_not_touch_descriptors(self):
        for name, descriptor in (("input_read", 0), ("output_write", 1), ("error_write", 2)):
            for offset in (0, CAPACITY):
                with self.subTest(name=name, offset=offset):
                    binary = self.program(f"fn main(){{return {name}({offset},0)}}")
                    result = run_native(binary, preexec_fn=lambda fd=descriptor: invalidate_standard_fd(fd))
                    self.assertEqual(result.returncode, 0)
                    with Guest(binary) as guest:
                        sites = self.sites(binary)
                        base = self.acquire(guest, sites)
                        guest.bp(sites["read"])
                        guest.bp(sites["write"])
                        self.assertEqual(self.cleanup(guest, sites, 0, base=base), (0, b"", b""))

    def test_full_arena_real_streams_and_return_counts(self):
        source = ("fn main(){let n=0 let got=1 while got {"
                  "got=input_read(n,16777216-n) n=n+got if n==16777216 {got=0}} "
                  "return output_write(0,n)==16777216}")
        data = bytes(range(256)) * 65536
        result = run_native(self.program(source), data, timeout=120)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, data, b""))
        binary = self.program("fn main(){let n=input_read(16777213,3) "
                              "let m=output_write(16777213,n) "
                              "let e=error_write(16777213,n) "
                              "return n+m+e+input_read(0,1)}")
        for data in (b"", b"ABC"):
            result = run_native(binary, data)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (3 * len(data), data, data))

    def test_live_pipe_read_preserves_short_count_without_eof(self):
        binary = self.program("fn main(){let n=input_read(65536,100) "
                              "output_write(65536,n) return n}")
        process = subprocess.Popen([shutil.which("qemu-x86_64"), str(binary)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        try:
            process.stdin.write(b"ABC")
            process.stdin.flush()
            # The writer stays open: a helper that fills the range would hang.
            process.wait(timeout=15)
            self.assertEqual((process.returncode, process.stdout.read(), process.stderr.read()),
                             (3, b"ABC", b""))
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    def test_stream_eintr_partial_writes_and_normal_cleanup(self):
        binary = self.program("fn main(){let n=input_read(65536,100) "
                              "let m=output_write(65536,n) return n+m+37}")
        sites = self.sites(binary)
        with Guest(binary, b"ABC") as guest:
            base = self.acquire(guest, sites)
            guest.bp(sites["read"])
            guest.until(sites["read"])
            for _ in range(2):
                guest.inject(-4)
                guest.until(sites["read"])
            guest.bp(sites["read"], False)
            guest.bp(sites["write"])
            guest.until(sites["write"])
            guest.inject(-4)
            guest.until(sites["write"])
            guest.short_write(1)
            registers = guest.until(sites["write"])
            self.assertEqual((registers["rsi"], registers["rdx"]), (base + 65537, 2))
            guest.bp(sites["write"], False)
            self.assertEqual(self.cleanup(guest, sites, 43, base=base), (43, b"ABC", b""))

    def test_stream_failures_and_zero_progress_cleanup(self):
        for name, site, code in (("input_read", "read", 5),
                                 ("output_write", "write", 6),
                                 ("error_write", "write", None)):
            for error in (-9, 0) if site == "write" else (-9,):
                with self.subTest(name=name, error=error):
                    binary = self.program(f"fn main(){{return {name}(65536,3)}}")
                    sites = self.sites(binary)
                    with Guest(binary) as guest:
                        base = self.acquire(guest, sites)
                        guest.bp(sites[site])
                        guest.until(sites[site])
                        guest.inject(error)
                        guest.bp(sites[site], False)
                        if code is None:
                            guest.bp(sites["diagnose"])
                        result = self.cleanup(guest, sites, 74, base=base)
                    self.assertEqual(result[:2], (74, b""))
                    if code is None:
                        self.assertEqual(result[2], b"")
                    else:
                        self.assertIn(f"input:1:18: error[C0R-{code:03d}]".encode(), result[2])

    def test_error_write_eintr_partial_progress_and_failure_cleanup(self):
        binary = self.program("fn main(){byte_store(65536,65) byte_store(65537,66) "
                              "byte_store(65538,67) return error_write(65536,3)}")
        sites = self.sites(binary)
        for error in (None, -9, 0):
            with self.subTest(error=error), Guest(binary) as guest:
                base = self.acquire(guest, sites)
                guest.bp(sites["write"])
                registers = guest.until(sites["write"])
                self.assertEqual(registers["rdi"], 2)
                guest.inject(-4)
                guest.until(sites["write"])
                guest.short_write(1)
                registers = guest.until(sites["write"])
                self.assertEqual((registers["rsi"], registers["rdx"]), (base + 65537, 2))
                guest.inject(-4)
                guest.until(sites["write"])
                if error is not None:
                    guest.inject(error)
                guest.bp(sites["write"], False)
                guest.bp(sites["diagnose"])
                status = 3 if error is None else 74
                self.assertEqual(self.cleanup(guest, sites, status, base=base),
                                 (status, b"", b"ABC" if error is None else b"A"))

    def test_real_closed_descriptors(self):
        for name, descriptor, code in (("input_read", 0, 5),
                                       ("output_write", 1, 6), ("error_write", 2, None)):
            with self.subTest(name=name):
                binary = self.program(f"fn main(){{return {name}(65536,1)}}")
                result = run_native(binary, preexec_fn=lambda fd=descriptor: invalidate_standard_fd(fd))
                self.assertEqual((result.returncode, result.stdout), (74, b""))
                if code is None:
                    self.assertEqual(result.stderr, b"")
                else:
                    self.assertIn(f"[C0R-{code:03d}]".encode(), result.stderr)

    def test_arithmetic_depth_and_signal_failures_cleanup(self):
        maximum = "9223372036854775807"
        minimum = "(0-9223372036854775807-1)"
        for expression in (maximum + "+1", minimum + "-1", maximum + "*2",
                           "1/0", minimum + "/(0-1)"):
            with self.subTest(expression=expression):
                binary = self.program("fn main(){byte_store(65536,42) return " + expression + "}")
                sites = self.sites(binary)
                with Guest(binary) as guest:
                    base = self.acquire(guest, sites)
                    result = self.cleanup(guest, sites, 70, base=base)
                self.assertEqual(result[:2], (70, b""))
                self.assertIn(b"[C0R-001]", result[2])
        for n, expected in ((62, 42), (63, 70)):
            binary = self.program("fn down(n){if n>0 {return down(n-1)} return byte_load(65536)} "
                                  f"fn main(){{byte_store(65536,42) return down({n})}}")
            sites = self.sites(binary)
            with Guest(binary) as guest:
                base = self.acquire(guest, sites)
                result = self.cleanup(guest, sites, expected, base=base)
            self.assertEqual(result[:2], (expected, b""))
            if n == 63:
                self.assertIn(b"[C0R-003]", result[2])
            else:
                self.assertEqual(result[2], b"")
        binary = self.program("fn main(){return byte_load(0)}")
        sites = self.sites(binary)
        with Guest(binary) as guest:
            base = self.acquire(guest, sites)
            guest.bp(sites["signal"])
            guest.until(sites["signal"])
            guest.inject(-22)
            guest.bp(sites["signal"], False)
            result = self.cleanup(guest, sites, 74, base=base)
            self.assertIn(b"[C0R-002]", result[2])

    def test_diagnostic_prefix_suffix_retry_and_broken_stderr(self):
        binary = self.program("fn main(){\n return byte_load(16777216)\n}")
        sites = self.sites(binary)
        expected = run_native(binary).stderr
        for phase in ("prefix", "suffix"):
            for error in (None, -9, 0):
                with self.subTest(phase=phase, error=error), Guest(binary) as guest:
                    base = self.acquire(guest, sites)
                    guest.bp(sites["diagnose"])
                    first = guest.until(sites["diagnose"])
                    prefix = guest.read_memory(first["rsi"], first["rdx"])
                    self.assertEqual(prefix, b"input:2:9: ")
                    if phase == "suffix":
                        guest.short_write(len(prefix))
                        guest.until(sites["diagnose"])
                    guest.inject(-4)
                    guest.until(sites["diagnose"])
                    if error is None:
                        guest.short_write(3)
                        guest.until(sites["diagnose"])
                    else:
                        guest.inject(error)
                    guest.bp(sites["diagnose"], False)
                    status = 70 if error is None else 74
                    result = self.cleanup(guest, sites, status, base=base)
                    self.assertEqual(result, (status, b"", expected if error is None else
                                              prefix if phase == "suffix" else b""))

    def test_resource_failures_and_failed_resource_diagnostics(self):
        binary = self.program("fn main(){return byte_load(65536)+42}")
        sites = self.sites(binary)
        image = binary.read_bytes()
        elf = struct.unpack_from("<16sHHIQQQIHHHHHH", image)
        segments = [struct.unpack_from("<IIQQQQQQ", image, elf[5] + i * elf[9])
                    for i in range(elf[10])]
        for fault in ("mmap", "munmap"):
            for error in (None, -9, 0):
                with self.subTest(fault=fault, error=error), Guest(binary) as guest:
                    if fault == "munmap":
                        self.acquire(guest, sites)
                    guest.bp(sites[fault])
                    guest.until(sites[fault])
                    guest.inject(-12 if fault == "mmap" else -22)
                    # Injection advances RIP. Keep both forbidden resource
                    # sites armed before even the first diagnostic is reached.
                    guest.bp(sites["mmap"])
                    guest.bp(sites["munmap"])
                    guest.bp(sites["diagnose"])
                    diagnostic = guest.until(sites["diagnose"])
                    message = guest.read_memory(diagnostic["rsi"], diagnostic["rdx"])
                    self.assertRegex(message, rb"^input:1:1: error\[C0R-007\]: .+; .+\n$")
                    self.assertIn(fault.encode(), message)
                    start, end = diagnostic["rsi"], diagnostic["rsi"] + diagnostic["rdx"]
                    self.assertGreater(end, start)
                    self.assertTrue(any(h[0] == 1 and h[2] + h[5] <= len(image)
                                        and h[3] <= start < end <= h[3] + min(h[5], h[6])
                                        for h in segments), "resource text is not in the static ELF image")
                    guest.inject(-4)
                    guest.until(sites["diagnose"])
                    if error is None:
                        guest.short_write(3)
                        guest.until(sites["diagnose"])
                    else:
                        guest.inject(error)
                    guest.bp(sites["diagnose"], False)
                    result = self.cleanup(guest, sites, 74, acquired=False)
                    self.assertEqual(result, (74, b"", message if error is None else b""))

    def test_broken_stderr_then_unmap_failure_does_not_diagnose_again(self):
        binary = self.program("fn main(){return byte_load(16777216)}")
        sites = self.sites(binary)
        with Guest(binary) as guest:
            self.acquire(guest, sites)
            guest.bp(sites["diagnose"])
            guest.until(sites["diagnose"])
            guest.inject(-9)
            guest.bp(sites["munmap"])
            guest.until(sites["munmap"])
            guest.inject(-22)
            guest.bp(sites["munmap"], False)
            self.assertEqual(self.cleanup(guest, sites, 74, acquired=False), (74, b"", b""))

    def test_large_default_source_keeps_64k(self):
        source = b"fn main(){return byte_load(65536)}".ljust(8193, b" ")
        result = run_native(self.program(source, profile=False))
        self.assertEqual((result.returncode, result.stdout), (70, b""))
        self.assertIn(b"[C0R-004]", result.stderr)

    def test_user_shadow_does_not_map_arena(self):
        for name in ("byte_load", "byte_store", "input_read", "output_write", "error_write"):
            with self.subTest(name=name):
                source = f"fn {name}(a){{return a+1}} fn main(){{return {name}(41)}}"
                binary = self.program(source)
                traced = subprocess.run([shutil.which("qemu-x86_64"), "-strace", str(binary)],
                                        capture_output=True, timeout=15, check=False)
                self.assertEqual((traced.returncode, traced.stdout), (42, b""))
                self.assertIn(b"exit(42)", traced.stderr)
                self.assertNotIn(b"mmap(", traced.stderr)
                self.assertNotIn(b"munmap(", traced.stderr)
                wrong = self.compile_source(f"fn {name}(){{return 7}} fn main(){{return {name}(0)}}")
                self.assertEqual((wrong.returncode, wrong.stdout), (1, b""))
                self.assertIn(b"[C0B-008]", wrong.stderr)
        for call in ("byte_load_extra(0)", "Byte_load(0)"):
            result = self.compile_source("fn main(){return " + call + "}")
            self.assertEqual((result.returncode, result.stdout), (1, b""))
            self.assertIn(b"[C0B-008]", result.stderr)

    def test_successful_helpers_preserve_native_abi(self):
        source = ("fn sum(a,b,c,d,e,f){return a+b+c+d+e+f} "
                  "fn main(){byte_store(65536,42) let n=input_read(65537,1) "
                  "let m=output_write(65536,1) let e=error_write(65536,1) "
                  "return sum(1,2,3,4,5,6)+byte_load(65536)+n+m+e}")
        binary = self.program(source)
        sites = self.sites(binary)
        helper_offsets = (24640, 24672, 24688, 24704, 24608)
        with Guest(binary, b"B") as guest:
            self.acquire(guest, sites)
            for offset in helper_offsets:
                entry = 0x400000 + 6267456 + offset
                guest.bp(entry)
                before = guest.until(entry)
                self.assertEqual(before["rsp"] % 16, 8)
                self.assertEqual(before["r15"], 1)
                saved = {name: before[name] for name in ("rbp", "rbx", "r14", "r15")}
                saved.update(r12=0x2233445566778899, r13=0x33445566778899aa)
                guest.setregs(r12=saved["r12"], r13=saved["r13"])
                successor = struct.unpack("<Q", guest.read_memory(before["rsp"], 8))[0]
                guest.bp(entry, False)
                guest.bp(successor)
                after = guest.until(successor)
                for register, value in saved.items():
                    self.assertEqual(after[register], value, register)
                self.assertEqual(after["rsp"], before["rsp"] + 8)
                guest.bp(successor, False)
            self.assertEqual(self.cleanup(guest, sites, 66), (66, b"*", b"*"))

    def test_maximum_native_frame_is_disjoint_from_private_state(self):
        declarations = " ".join(f"let v{i}=0" for i in range(510))
        body = " byte_store(65536,42) return byte_load(65536)}"
        binary = self.program("fn main(){" + declarations + body)
        sites = self.sites(binary)
        with Guest(binary) as guest:
            base = self.acquire(guest, sites)
            entry = 0x400000 + 6267456 + 24640
            guest.bp(entry)
            registers = guest.until(entry)
            frame_start, frame_end = registers["rbp"] - 4096, registers["rbp"]
            state_start, state_end = registers["r14"], registers["r14"] + 32
            self.assertEqual(registers["rsp"], frame_start - 8)
            self.assertLessEqual(frame_end, state_start)
            self.assertEqual(frame_end + 4096 + 16, state_start)
            self.assertLess(frame_start, frame_end)
            self.assertEqual(state_end - state_start, 32)
            # 510 permanent slots + two live arguments: slot 512 is touched.
            self.assertEqual(struct.unpack("<Q", guest.read_memory(frame_start, 8))[0], 42)
            self.assertEqual(struct.unpack("<4Q", guest.read_memory(state_start, 32)),
                             (base, 1, 0, 0))
            guest.bp(entry, False)
            self.assertEqual(self.cleanup(guest, sites, 42, base=base), (42, b"", b""))
        result = self.compile_source("fn main(){" + declarations + " let extra=0" + body)
        self.assertEqual((result.returncode, result.stdout), (1, b""))
        self.assertIn(b"[C0B-007]", result.stderr)

    def test_deterministic_static_elf_and_nonexecutable_stack(self):
        binary = self.program("fn main(){byte_store(16777215,42) return byte_load(16777215)}")
        image = binary.read_bytes()
        self.assertEqual(image, self.program(
            "fn main(){byte_store(16777215,42) return byte_load(16777215)}").read_bytes())
        header = struct.unpack_from("<16sHHIQQQIHHHHHH", image)
        self.assertEqual(header[1:4], (2, 62, 1))
        headers = [struct.unpack_from("<IIQQQQQQ", image, header[5] + i * header[9])
                   for i in range(header[10])]
        self.assertFalse(any(h[0] in (2, 3) for h in headers))
        self.assertIn((0x6474e551, 6), [(h[0], h[1]) for h in headers])
        self.assertFalse(any(h[0] == 1 and h[1] & 3 == 3 for h in headers))


if __name__ == "__main__":
    unittest.main()
