"""Stage0-authored B0 compiler-profile and predecessor compatibility tests."""

from pathlib import Path
import os
import struct
import subprocess
import tempfile
import unittest

from c031_debugger import Guest
from c031_support import PREDECESSORS, ROOT, build_predecessors, candidate_binary, run_native

CAPACITY = 16777216


class B0ProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="c031-b0-profile-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.compiler = candidate_binary(
            "B0_COMPILER", ROOT / "bootstrap/compiler/b0/x86_64-linux/b0.seed")
        self.sequence = 0

    def compile_b0(self, source: bytes, *, profile: bool
                   ) -> tuple[subprocess.CompletedProcess[bytes], Path]:
        self.sequence += 1
        path = self.directory / f"source-{self.sequence}.nql"
        output = self.directory / f"program-{self.sequence}"
        path.write_bytes(source)
        args = (["--compiler-profile"] if profile else []) + [str(path), "-o", str(output)]
        return run_native(self.compiler, args=args), output

    def test_profile_byte_above_legacy_bound(self):
        source = b"fn main(){byte_store(65536,42);return byte_load(65536)}"
        result, output = self.compile_b0(source, profile=True)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertEqual(run_native(output).returncode, 42)
        self.assertNotEqual(self.compile_b0(source, profile=False)[0].returncode, 0)

    def program(self, source):
        result, binary = self.compile_b0(source, profile=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        return binary

    def test_profile_cli_positions_and_rejections(self):
        source = self.directory / "input.nql"
        source.write_bytes(b"fn main(){byte_store(65536,42);return byte_load(65536)}")
        output = self.directory / "output"
        for args in (("--compiler-profile", str(source), "-o", str(output)),
                     (str(source), "--compiler-profile", "-o", str(output)),
                     (str(source), "-o", str(output), "--compiler-profile")):
            with self.subTest(args=args):
                result = run_native(self.compiler, args=args)
                self.assertEqual((result.returncode, result.stderr), (0, b""))
                self.assertEqual(run_native(output).returncode, 42)
        for args in ((str(source), "-o", "--compiler-profile", str(output)),
                     ("--compiler-profile", str(source), "--compiler-profile", "-o", str(output)),
                     ("--compiler-profile", "--lex", str(source)),
                     ("--parse", str(source), "--compiler-profile"),
                     ("--lex", "--compiler-profile", "-o", str(output)),
                     ("--compiler-profile", "--parse", "-o", str(output)),
                     ("--compiler-profile", str(source), "--unknown", str(output))):
            with self.subTest(args=args):
                output.write_bytes(b"old-output")
                result = run_native(self.compiler, args=args)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, b"")
                self.assertEqual(output.read_bytes(), b"old-output")

    def test_profile_bounds_and_zero_initialization(self):
        for index in (0, 65535, 65536, CAPACITY - 1):
            with self.subTest(index=index):
                source = (f"fn main(){{let z=byte_load({index}) "
                          f"byte_store({index},298);return byte_load({index})+z}}")
                result = run_native(self.program(source.encode()))
                self.assertEqual((result.returncode, result.stderr), (42, b""))
        for index in ("16777216", "16777217", "0-1"):
            with self.subTest(index=index):
                for operation in (f"return byte_load({index})", f"byte_store({index},1);return 0",
                                  f"return input_read({index},0)",
                                  f"output_write({index},0);return 0"):
                    result, binary = self.compile_b0(f"fn main(){{{operation}}}".encode(), profile=True)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(b"B0-CG-008", result.stderr)
                    self.assertIn(b"16777215", result.stderr)
                    self.assertFalse(binary.exists())
        for expression in ("16777216", "0-1"):
            binary = self.program(f"fn main(){{let i=0 i={expression} return byte_load(i)}}".encode())
            result = run_native(binary)
            self.assertEqual(result.returncode, 70)
            self.assertIn(b"out of bounds", result.stderr)
        binary = self.program(b"fn main(){let n=input_read(16777215,1) "
                              b"output_write(16777215,n);return n}")
        result = run_native(binary, b"XY")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (1, b"X", b""))
        for expression in ("input_read(0,16777217)", "input_read(16777215,2)",
                           "input_read(0,0-1)"):
            result, binary = self.compile_b0(f"fn main(){{return {expression}}}".encode(), profile=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(binary.exists())

    def test_profile_option_is_not_a_lex_parse_operand(self):
        (self.directory / "--compiler-profile").write_bytes(b"fn main(){return 7}")
        output = self.directory / "output"
        for args in (("--lex", "--compiler-profile"), ("--parse", "--compiler-profile"),
                     ("--compiler-profile", "-o", str(output))):
            with self.subTest(args=args):
                result = run_native(self.compiler, args=args, cwd=self.directory)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(b"B0-IO-000", result.stderr)
                self.assertFalse(output.exists())

    def test_profile_private_state_and_b0_semantics(self):
        declarations = " ".join(f"let local{chr(97 + i)}={i}" for i in range(16))
        binary = self.program((f"fn main(){{{declarations} byte_store(16777215,42) "
                               "return localp+byte_load(16777215)}").encode())
        self.assertEqual(run_native(binary).returncode, 57)
        # B0 writes are statements and its ranges require an actual byte at offset,
        # including count zero. C0's expression returns/end-empty rule do not apply.
        for source in (b"fn main(){return output_write(0,0)}",
                       b"fn main(){return byte_store(0,7)}",
                       b"fn main(){output_write(16777216,0);return 0}"):
            self.assertEqual(self.compile_b0(source, profile=True)[0].returncode, 1)
        binary = self.program(b"fn main(){return 9223372036854775807+1}")
        self.assertEqual(run_native(binary).returncode, 0)
        binary = self.program(b"fn main(){let n=input_read(65536,3) "
                              b"output_write(65536,n);error_write(65536,n);return n}")
        result = run_native(binary, b"ABC")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (3, b"ABC", b"ABC"))

    def syscall_site(self, binary, prefix):
        data = binary.read_bytes()
        self.assertEqual(data.count(prefix), 1, prefix.hex())
        position = data.index(prefix) + len(prefix)
        self.assertEqual(data[position:position + 2], b"\x0f\x05")
        return 0x400000 + position

    def cleanup_sites(self, binary):
        return dict(
            mmap=self.syscall_site(binary, bytes.fromhex("49c7c0ffffffff4531c9")),
            munmap=self.syscall_site(binary, bytes.fromhex("b80b0000004c89f7be00000001")),
            exit=self.syscall_site(binary, bytes.fromhex("4c89c7b83c000000")),
            diagnose=self.syscall_site(binary, bytes.fromhex("4989f8bf02000000b801000000")),
            signal=self.syscall_site(binary, bytes.fromhex("4889e631d241ba08000000")),
        )

    def runtime_sites(self, binary):
        return dict(
            **self.cleanup_sites(binary),
            read=self.syscall_site(binary, bytes.fromhex("4c01f631ff31c0")),
            write=self.syscall_site(binary, bytes.fromhex("4885d2741fb801000000")),
        )

    def test_profile_stream_retry_and_cleanup(self):
        binary = self.program(b"fn main(){let n=input_read(65536,3) output_write(65536,n);return n}")
        sites = self.runtime_sites(binary)
        with Guest(binary, b"ABC") as guest:
            for name in ("mmap", "read", "write", "munmap", "exit"):
                guest.bp(sites[name])
            registers = guest.until(sites["mmap"])
            self.assertEqual(tuple(registers[r] for r in ("rax", "rdi", "rsi", "rdx", "r10")),
                             (9, 0, CAPACITY, 3, 0x22))
            guest.bp(sites["mmap"], False)
            registers = guest.until(sites["read"])
            self.assertEqual(registers["r13"], 1)
            for _ in range(2):
                guest.inject(-4)
                guest.until(sites["read"])
            guest.bp(sites["read"], False)
            guest.until(sites["write"])
            guest.inject(-4)
            guest.until(sites["write"])
            guest.short_write(1)
            registers = guest.until(sites["write"])
            self.assertEqual(registers["rdx"], 2)
            guest.bp(sites["write"], False)
            registers = guest.until(sites["munmap"])
            self.assertEqual((registers["rdi"], registers["rsi"], registers["r13"]),
                             (registers["r14"], CAPACITY, 0))
            guest.bp(sites["munmap"], False)
            guest.until(sites["exit"])
            guest.bp(sites["exit"], False)
            self.assertEqual(guest.finish(), (3, b"ABC", b""))

    def test_profile_resource_failures(self):
        binary = self.program(b"fn main(){let n=input_read(65536,3) output_write(65536,n);return n}")
        sites = self.runtime_sites(binary)
        for fault, error, message in (("mmap", -12, b"mmap"), ("munmap", -22, b"munmap"),
                                      ("read", -9, b"input_read"), ("write", -9, b"output_write")):
            with self.subTest(fault=fault), Guest(binary, b"ABC") as guest:
                guest.bp(sites[fault])
                guest.until(sites[fault])
                guest.inject(error)
                guest.bp(sites[fault], False)
                if fault in ("read", "write"):
                    guest.bp(sites["munmap"])
                    guest.until(sites["munmap"])
                    guest.bp(sites["munmap"], False)
                    guest.bp(sites["munmap"] + 2)
                    guest.until(sites["munmap"] + 2)
                    guest.bp(sites["munmap"] + 2, False)
                # Leaving munmap armed catches any second attempt or use after failed mmap.
                guest.bp(sites["munmap"])
                guest.bp(sites["exit"])
                registers = guest.until(sites["exit"])
                self.assertEqual((registers["rdi"], registers["r13"]), (74, 0))
                guest.bp(sites["exit"], False)
                status, _, stderr = guest.finish()
                self.assertEqual(status, 74)
                self.assertIn(message, stderr)

    def assert_cleanup(self, guest, sites, status, *, acquired=True):
        if acquired:
            guest.bp(sites["munmap"])
            registers = guest.until(sites["munmap"])
            self.assertEqual((registers["rdi"], registers["rsi"], registers["r13"]),
                             (registers["r14"], CAPACITY, 0))
            guest.bp(sites["munmap"], False)
            guest.bp(sites["munmap"] + 2)
            guest.until(sites["munmap"] + 2)
            guest.bp(sites["munmap"] + 2, False)
        guest.bp(sites["munmap"])
        guest.bp(sites["exit"])
        registers = guest.until(sites["exit"])
        self.assertEqual((registers["rdi"], registers["r13"]), (status, 0))
        guest.bp(sites["exit"], False)

    def test_profile_diagnostic_retry_and_broken_stderr(self):
        binary = self.program(b"fn main(){let i=0 i=16777216 return byte_load(i)}")
        sites = self.cleanup_sites(binary)
        expected = b"B0 runtime: byte-memory index out of bounds\n"
        for broken in (False, True):
            with self.subTest(broken=broken), Guest(binary) as guest:
                guest.bp(sites["diagnose"])
                guest.until(sites["diagnose"])
                guest.inject(-4)
                guest.until(sites["diagnose"])
                if broken:
                    guest.inject(-9)
                else:
                    guest.short_write(3)
                    registers = guest.until(sites["diagnose"])
                    self.assertEqual(registers["rdx"], len(expected) - 3)
                guest.bp(sites["diagnose"], False)
                self.assert_cleanup(guest, sites, 74 if broken else 70)
                self.assertEqual(guest.finish(), (74 if broken else 70, b"", b"" if broken else expected))

    def test_broken_stderr_then_unmap_failure_does_not_diagnose_again(self):
        for operation, source in (
                ("diagnostic", b"fn main(){let i=0 i=16777216 return byte_load(i)}"),
                ("error_write", b"fn main(){byte_store(65536,65) error_write(65536,1);return 9}")):
            binary = self.program(source)
            sites = self.cleanup_sites(binary)
            write = (sites["diagnose"] if operation == "diagnostic" else self.syscall_site(
                binary, bytes.fromhex("bf020000004885d2741fb801000000")))
            for error in (-9, 0):
                with self.subTest(operation=operation, error=error), Guest(binary) as guest:
                    for address in {sites["mmap"], sites["munmap"], sites["diagnose"],
                                    sites["exit"], write}:
                        guest.bp(address)
                    registers = guest.until(sites["mmap"])
                    self.assertEqual(tuple(registers[r] for r in ("rax", "rdi", "rsi", "rdx", "r10")),
                                     (9, 0, CAPACITY, 3, 0x22))
                    guest.bp(sites["mmap"], False)
                    registers = guest.until(write)
                    self.assertEqual((registers["rax"], registers["rdi"], registers["r13"]), (1, 2, 1))
                    guest.bp(sites["mmap"])
                    guest.inject(error)
                    registers = guest.until(sites["munmap"])
                    self.assertEqual((registers["rdi"], registers["rsi"], registers["r13"]),
                                     (registers["r14"], CAPACITY, 0))
                    guest.inject(-22)
                    # Leave all forbidden sites armed after both failures.
                    self.assertRegex(guest.cmd("c"), r"^[ST]05")
                    registers = guest.regs()
                    self.assertEqual(registers["rip"], sites["exit"],
                                     "broken stderr must exit without another diagnostic or mapping syscall")
                    self.assertEqual((registers["rdi"], registers["r13"]), (74, 0))
                    guest.bp(sites["exit"], False)
                    self.assertEqual(guest.finish(), (74, b"", b""))

    def test_profile_startup_and_teardown_with_broken_stderr(self):
        binary = self.program(b"fn main(){let x=42 return x}")
        sites = self.cleanup_sites(binary)
        for fault in ("signal", "mmap", "munmap"):
            for broken in (False, True):
                with self.subTest(fault=fault, broken=broken), Guest(binary) as guest:
                    guest.bp(sites[fault])
                    guest.until(sites[fault])
                    guest.inject(-22)
                    guest.bp(sites[fault], False)
                    if broken:
                        guest.bp(sites["diagnose"])
                        guest.until(sites["diagnose"])
                        guest.inject(-9)
                        guest.bp(sites["diagnose"], False)
                    if fault == "signal":
                        guest.bp(sites["mmap"])
                    self.assert_cleanup(guest, sites, 74, acquired=False)
                    status, stdout, stderr = guest.finish()
                    self.assertEqual((status, stdout), (74, b""))
                    if broken:
                        self.assertEqual(stderr, b"")
                    else:
                        self.assertIn(b"B0 runtime:", stderr)
                        self.assertIn(b"; ", stderr)

    def test_profile_error_write_retry_and_cleanup(self):
        binary = self.program(b"fn main(){byte_store(65536,65) byte_store(65537,66) "
                              b"error_write(65536,2);return 9}")
        sites = self.cleanup_sites(binary)
        write = self.syscall_site(binary, bytes.fromhex("bf020000004885d2741fb801000000"))
        for error in (None, -9, 0):
            with self.subTest(error=error), Guest(binary) as guest:
                guest.bp(write)
                guest.until(write)
                guest.inject(-4)
                guest.until(write)
                if error is None:
                    guest.short_write(1)
                    guest.until(write)
                else:
                    guest.inject(error)
                guest.bp(write, False)
                # A failure on stderr must not attempt another diagnostic.
                guest.bp(sites["diagnose"])
                self.assert_cleanup(guest, sites, 9 if error is None else 74)
                self.assertEqual(guest.finish(), (9, b"", b"AB") if error is None else (74, b"", b""))

    def test_profile_fast_literals(self):
        for source in (b"fn main(){return 23}", b"fn main(){write(\"\");return 17}",
                       b"fn main(){write(\"ABC\");return 37}"):
            binary = self.program(source)
            result = run_native(binary)
            expected = (23, b"") if b"write" not in source else ((17, b"") if b'\"\"' in source else (37, b"ABC"))
            self.assertEqual((result.returncode, result.stdout, result.stderr), (*expected, b""))
        binary = self.program(b"fn main(){write(\"ABC\");return 37}")
        sites = self.cleanup_sites(binary)
        data = binary.read_bytes()
        marker = bytes.fromhex("ba03000000bf010000004885d20f84")
        self.assertEqual(data.count(marker), 1)
        position = data.index(b"\xb8\x01\x00\x00\x00\x0f\x05", data.index(marker)) + 5
        write = 0x400000 + position
        for error in (None, -9, 0):
            with self.subTest(error=error), Guest(binary) as guest:
                guest.bp(write)
                guest.until(write)
                guest.inject(-4)
                guest.until(write)
                if error is None:
                    guest.short_write(1)
                    guest.until(write)
                else:
                    guest.inject(error)
                guest.bp(write, False)
                self.assert_cleanup(guest, sites, 37 if error is None else 74)
                status, stdout, stderr = guest.finish()
                self.assertEqual(status, 37 if error is None else 74)
                self.assertEqual(stdout, b"ABC" if error is None else b"")
                self.assertEqual(stderr, b"" if error is None else
                                 b"B0 runtime: output_write failed; check standard output\n")

    def test_profile_real_bad_fds_and_empty_ranges(self):
        binary = self.program(b"fn main(){let n=input_read(0,16777216) output_write(0,n);return n}")
        for data in (b"", b"ABC"):
            result = run_native(binary, data)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (len(data), data, b""))
        result = run_native(self.program(b"fn main(){output_write(16777215,0);return input_read(16777215,0)}"))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        for fd, source in ((0, b"fn main(){return input_read(0,1)}"),
                           (1, b"fn main(){output_write(0,1);return 0}"),
                           (2, b"fn main(){error_write(0,1);return 0}")):
            with self.subTest(fd=fd), open(os.devnull, "wb" if fd == 0 else "rb") as bad:
                result = run_native(self.program(source), **{("stdin", "stdout", "stderr")[fd]: bad})
                self.assertEqual(result.returncode, 74)

    def test_profile_compiles_actual_frozen_components(self):
        predecessor = build_predecessors(self.directory / "predecessor")
        components = {name: self.program((PREDECESSORS / f"{name}.nql").read_bytes())
                      for name in ("frontend", "backend")}
        for source in (b"fn main(){return 7}",
                       b"fn main(){let n=input_read(0,3) output_write(0,n);return n}",
                       b"fn twice(a){return a+a} fn main(){return twice(21)}",
                       b"fn main(){let n=3 while n {n=n-1} return n}", b"fn main(){return }", b"@"):
            with self.subTest(source=source):
                old = run_native(predecessor["frontend"], source)
                new = run_native(components["frontend"], source)
                self.assertEqual((new.returncode, new.stdout, new.stderr),
                                 (old.returncode, old.stdout, old.stderr))
                if old.returncode == 0:
                    old = run_native(predecessor["backend"], old.stdout)
                    new = run_native(components["backend"], new.stdout)
                    self.assertEqual((new.returncode, new.stdout, new.stderr),
                                     (old.returncode, old.stdout, old.stderr))

    def test_candidate_and_generated_elf_layout(self):
        data = self.compiler.read_bytes()
        self.assertEqual(struct.unpack_from("<Q", data, 40)[0], 0)
        self.assertEqual(struct.unpack_from("<HHH", data, 58), (0, 0, 0))
        headers = list(struct.iter_unpack("<IIQQQQQQ", data[64:64 + 5 * 56]))
        self.assertEqual([(h[0], h[1], h[2], h[3]) for h in headers],
                         [(1, 4, 0, 0x400000), (1, 5, 0x1000, 0x401000),
                          (1, 4, 0x5000, 0x405000), (1, 6, 0x1000, 0x406000),
                          (0x6474e551, 6, 0, 0)])
        self.assertEqual(len(data), 0x5969)
        binary = self.program(b"fn main(){let x=7 return x}")
        generated = binary.read_bytes()
        headers = list(struct.iter_unpack("<IIQQQQQQ", generated[64:176]))
        self.assertEqual([(h[0], h[1]) for h in headers], [(1, 5), (0x6474e551, 6)])

    def test_default_fixture_bytes_match_b07r(self):
        predecessor = build_predecessors(self.directory / "predecessor")["b0"]
        for source in sorted((ROOT / "tests/bootstrap/fixtures/b0").glob("*.nql")):
            with self.subTest(fixture=source.name):
                outputs = [self.directory / "old", self.directory / "new"]
                for output in outputs:
                    output.unlink(missing_ok=True)
                old, new = [run_native(compiler, args=(str(source), "-o", str(output)))
                            for compiler, output in zip((predecessor, self.compiler), outputs)]
                self.assertEqual((new.returncode, new.stdout, new.stderr),
                                 (old.returncode, old.stdout, old.stderr))
                self.assertEqual(outputs[0].exists(), outputs[1].exists())
                if outputs[0].exists():
                    self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
                    old, new = [run_native(output, b"B0\x00\xff\n") for output in outputs]
                    self.assertEqual((new.returncode, new.stdout, new.stderr),
                                     (old.returncode, old.stdout, old.stderr))


if __name__ == "__main__":
    unittest.main()
