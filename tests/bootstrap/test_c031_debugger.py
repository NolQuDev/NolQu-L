"""Debugger failure handling and real Stage0-generated guest execution."""

from contextlib import contextmanager
from pathlib import Path
import socket
import stat
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import c031_debugger as debugger
from c031_support import ROOT, run_native


def packet(payload):
    return b"$" + payload + b"#" + f"{sum(payload) & 255:02x}".encode()


class TransportTests(unittest.TestCase):
    def exchange(self, response):
        client, server = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        server.sendall(response)
        server.shutdown(socket.SHUT_WR)
        return debugger._Remote(client, timeout=0.1).command("?")

    def test_valid_packet(self):
        self.assertEqual(self.exchange(b"+" + packet(b"T05")), "T05")

    def test_eof_and_bad_packets_fail_without_hanging(self):
        for data in (b"", b"+", b"$T05", b"$T05#", b"$T05#zz", b"$T05#00", b"-",
                     packet(b"}"), packet(b"* "), packet(b"A*\x00")):
            with self.subTest(data=data):
                with self.assertRaises(debugger.ProtocolError):
                    self.exchange(data)

    def test_timeout_without_response(self):
        client, server = socket.socketpair()
        with client, server:
            with self.assertRaises(TimeoutError):
                debugger._Remote(client, timeout=0.05).command("?")

    def test_checksum_requires_two_hexadecimal_digits(self):
        for checksum in (b"+0", b"-0", b" 0", b"0 ", b"\t0", b"0\n"):
            for payload in (b"", b"0" * 272):
                with self.subTest(checksum=checksum, payload_length=len(payload)):
                    with self.assertRaisesRegex(debugger.ProtocolError, "checksum"):
                        self.exchange(b"$" + payload + b"#" + checksum)

    def test_fragmented_checksum_and_escaped_data(self):
        client, server = socket.socketpair()
        errors = []

        def respond():
            try:
                server.settimeout(1)
                server.recv(64)
                for byte in b"+" + packet(b"0* }\x03"):
                    server.sendall(bytes([byte]))
                server.recv(1)
            except BaseException as exc:
                errors.append(exc)
            finally:
                server.close()

        worker = threading.Thread(target=respond)
        worker.start()
        try:
            with client:
                result = debugger._Remote(client, timeout=1).command("?")
        finally:
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result, "0000#")

    def test_oversized_packets_and_repetition_are_bounded(self):
        with patch.object(debugger, "MAX_PACKET", 32):
            for response in (packet(b"x" * 33), packet(b"x*~")):
                with self.assertRaises(debugger.ProtocolError):
                    self.exchange(response)


class GuestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="c031-debugger-tests-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.binary = Path(cls.tmp.name) / "guest"
        source = ROOT / "tests/bootstrap/fixtures/c031/debugger.nql0"
        stage0 = ROOT / "bootstrap/stage0/x86_64-linux/stage0.seed"
        result = run_native(stage0, source.read_bytes())
        if result.returncode or result.stderr:
            raise AssertionError(result)
        cls.binary.write_bytes(result.stdout)
        cls.binary.chmod(0o755)
        code = result.stdout
        needle = b"\xb8\x01\0\0\0\x0f\x05"
        if code.count(needle) != 1:
            raise AssertionError("ambiguous syscall fixture")
        cls.write_site = 0x400000 + code.index(needle) + 5

    @contextmanager
    def replies(self, *payloads):
        client, server = socket.socketpair()
        with client, server:
            server.sendall(b"".join(packet(payload) for payload in payloads))
            server.shutdown(socket.SHUT_WR)
            yield debugger._Remote(client)

    def assert_closed(self, guest):
        self.assertTrue(guest.closed)
        self.assertIsNotNone(guest.process.returncode)
        self.assertEqual(guest.socket.fileno(), -1)
        self.assertTrue(guest.input.closed and guest.output.closed and guest.error.closed)
        self.assertFalse(guest.socket_path.parent.exists())

    def test_register_bodies_reject_whitespace_and_bad_hex_and_close_guest(self):
        for payload in (b"00 " * 136, b"\t" + b"0" * 272, b"0" * 272 + b"\n",
                        b"0" * 273, b"zz", b"0" * 270, b"", b"0" * 272 + b"xx"):
            with self.subTest(payload=payload), self.replies(payload) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                with self.assertRaises(debugger.ProtocolError):
                    guest.regs()
                self.assert_closed(guest)

    def test_memory_bodies_reject_whitespace_bad_hex_and_wrong_size_and_close_guest(self):
        for payload in (b"0f 05", b"\t0f05", b"0f05\n", b"0f0", b"zz", b"0f",
                        b"0f0500", b"", b"E01"):
            with self.subTest(payload=payload), self.replies(payload) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                with self.assertRaises(debugger.ProtocolError):
                    guest.read_memory(0x400000, 2)
                self.assert_closed(guest)

    def test_register_bodies_preserve_dense_hex_qemu_rle_and_extra_registers(self):
        # The three runs expand to 98 + 98 + 76 hex digits, then extra registers.
        for payload, rax in ((b"0*~0*~0*hABcd", 0),
                             (b"EfCdAb8967452301" + b"0" * 256, 0x0123456789abcdef)):
            with self.subTest(payload=payload), self.replies(payload) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                regs = guest.regs()
                self.assertEqual(regs["rax"], rax)
                self.assertEqual(list(regs.values())[1:], [0] * 16)
                self.assertFalse(guest.closed)

    def test_memory_bodies_preserve_dense_hex_qemu_rle_and_empty_reads(self):
        for payload, expected in ((b"0F05", b"\x0f\x05"), (b"0* ", b"\0\0"), (b"", b"")):
            with self.subTest(payload=payload), self.replies(payload) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                self.assertEqual(guest.read_memory(0x400000, len(expected)), expected)
                self.assertFalse(guest.closed)

    def test_until_rejects_malformed_stop_bodies_and_closes_guest(self):
        for payload in (b"S05garbage", b"S05\n", b"S5", b"Sgg", b"S04", b"T04",
                        b"T05garbage", b"T05thread:1", b"T05thread:1;;",
                        b"T05thread:1;garbage", b"T05:1;", b"T05thread:xyz;",
                        b"T05thread:;", b"T05core:gg;", b"T0510:0;", b"T0510:zz;",
                        b"T05swbreak:1;", b"T05watch:xyz;", b"T05thread:p-1.2;",
                        b"T05thread:p1a.;", b"T05thread:pzz.2;"):
            with self.subTest(payload=payload), self.replies(payload, b"0" * 272) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                with self.assertRaises(debugger.ProtocolError):
                    guest.until(0)
                self.assert_closed(guest)

    def test_until_accepts_simple_stops_and_legitimate_t_fields(self):
        for payload in (b"S05", b"T05", b"T05thread:1a;core:0;10:0000000000000000;",
                        b"T05thread:p1a.2b;swbreak:;", b"T05watch:400000;",
                        b"T05hwbreak:;vendor_hint:ready;", b"T05thread:p1a;",
                        b"T05thread:-1;", b"T05thread:p1a.-1;", b"T05thread:p-1.-1;",
                        b"T05thread:0;vendor.hint-1:ready;"):
            with self.subTest(payload=payload), self.replies(payload, b"0" * 272) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                self.assertEqual(guest.until(0)["rip"], 0)
                self.assertFalse(guest.closed)

    def test_unexpected_breakpoint_address_closes_guest(self):
        with self.replies(b"S05", b"0" * 272) as remote, debugger.Guest(self.binary) as guest:
            guest.remote = remote
            with self.assertRaisesRegex(debugger.ProtocolError, "expected stop"):
                guest.until(1)
            self.assert_closed(guest)

    def test_startup_rejects_malformed_stop_bodies_and_cleans_resources(self):
        for payload in (b"S", b"S0", b"Sgg", b"S05garbage", b"T", b"T05garbage",
                        b"T05thread:1", b"T05thread:xyz;", b"T0510:0;"):
            with self.subTest(payload=payload), self.replies(payload) as remote:
                guest = debugger.Guest.__new__(debugger.Guest)
                try:
                    # Only the connection is injected; startup still owns real QEMU/files.
                    with patch.object(debugger, "_Remote", lambda connection: remote):
                        with self.assertRaises(debugger.ProtocolError):
                            guest.__init__(self.binary)
                    self.assert_closed(guest)
                finally:
                    guest.close()

    def test_startup_accepts_valid_signal_and_t_fields(self):
        for payload in (b"S00", b"S0b", b"T05thread:1a;core:0;10:0000000000000000;"):
            with self.subTest(payload=payload), self.replies(payload) as remote:
                with patch.object(debugger, "_Remote", lambda connection: remote):
                    guest = debugger.Guest(self.binary)
                with guest:
                    guest.remote = debugger._Remote(guest.socket)
                    self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))

    def test_finish_rejects_malformed_exit_bodies_and_closes_resources(self):
        for payload in (b"W", b"W0", b"Wgg", b"W07garbage", b"W07\n", b"X",
                        b"X0bgarbage", b"W07;process:", b"X0b;process:xyz",
                        b"W07;process:1;garbage"):
            with self.subTest(payload=payload), self.replies(payload) as remote, \
                 debugger.Guest(self.binary) as guest:
                # A completed real guest exposes an accepted reply through finish's output.
                self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))
                guest.remote = remote
                with self.assertRaises(debugger.ProtocolError):
                    guest.finish()
                self.assert_closed(guest)

    def test_finish_rejects_non_exit_reply_and_reaps_live_guest(self):
        with self.replies(b"S05") as remote, debugger.Guest(self.binary) as guest:
            guest.remote = remote
            with self.assertRaises(debugger.ProtocolError):
                guest.finish()
            self.assert_closed(guest)

    def test_finish_accepts_supported_exit_shapes(self):
        for payload in (b"W07", b"W00", b"X0b", b"W07;process:1a", b"X0B;process:1a"):
            with self.subTest(payload=payload), self.replies(payload) as remote, \
                 debugger.Guest(self.binary) as guest:
                self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))
                guest.remote = remote
                self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))

    def test_rejected_register_and_breakpoint_updates_close_guest(self):
        for operation in ("setregs", "insert", "remove"):
            replies = (b"0" * 272, b"E01") if operation == "setregs" else (b"E01",)
            with self.subTest(operation=operation), self.replies(*replies) as remote, \
                 debugger.Guest(self.binary) as guest:
                guest.remote = remote
                with self.assertRaises(debugger.ProtocolError):
                    if operation == "setregs":
                        guest.setregs(rax=1)
                    else:
                        guest.bp(self.write_site, operation == "insert")
                self.assert_closed(guest)

    def test_guest_start_and_exit(self):
        with debugger.Guest(self.binary) as guest:
            self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))

    def test_registers_and_verified_syscall_injection(self):
        with debugger.Guest(self.binary) as guest:
            guest.bp(self.write_site)
            regs = guest.until(self.write_site)
            self.assertEqual((regs["rax"], regs["rdi"], regs["rdx"]), (1, 1, 6))
            self.assertEqual(guest.read_memory(regs["rsi"], 6), b"ABCDEF")
            guest.setregs(r12=0x12345678)
            self.assertEqual(guest.regs()["r12"], 0x12345678)
            guest.inject(-4)
            regs = guest.regs()
            self.assertEqual(regs["rax"], (1 << 64) - 4)
            self.assertEqual(regs["rip"], self.write_site + 2)
            self.assertEqual(regs["rcx"], 0xdeadbeefdeadbeef)
            guest.bp(self.write_site, False)
            self.assertEqual(guest.finish(), (7, b"", b""))

    def test_short_write_executes_real_syscall(self):
        with debugger.Guest(self.binary) as guest:
            guest.bp(self.write_site)
            guest.until(self.write_site)
            guest.short_write(2)
            self.assertEqual(guest.regs()["rdx"], 6)
            self.assertEqual(guest.regs()["rdi"], 1)
            self.assertEqual(guest.regs()["rip"], self.write_site + 2)
            self.assertEqual(guest.breakpoints, {self.write_site})
            guest.bp(self.write_site, False)
            self.assertEqual(guest.finish(), (7, b"AB", b""))

    def test_short_write_preserves_existing_successor_breakpoint(self):
        with debugger.Guest(self.binary) as guest:
            guest.bp(self.write_site)
            guest.bp(self.write_site + 2)
            guest.until(self.write_site)
            guest.short_write(3)
            self.assertEqual(guest.breakpoints, {self.write_site, self.write_site + 2})
            guest.bp(self.write_site, False)
            guest.bp(self.write_site + 2, False)
            self.assertEqual(guest.finish(), (7, b"ABC", b""))

    def test_non_syscall_injection_is_rejected(self):
        with debugger.Guest(self.binary) as guest:
            with self.assertRaisesRegex(ValueError, "verified syscall"):
                guest.inject(-4)
            with self.assertRaisesRegex(ValueError, "unknown register"):
                guest.setregs(unknown=1)
            self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))

    def test_large_input_and_cleanup(self):
        with debugger.Guest(self.binary, data=b"x" * (4 * 1024 * 1024)) as guest:
            self.assertTrue(stat.S_ISSOCK(guest.socket_path.stat().st_mode))
            self.assertEqual(guest.finish(), (7, b"ABCDEF", b""))
        self.assertEqual(guest.process.poll(), 7)
        self.assertTrue(guest.input.closed and guest.output.closed and guest.error.closed)
        self.assertEqual(guest.socket.fileno(), -1)
        self.assertFalse(guest.socket_path.parent.exists())
        guest.close()

    def test_timeout_reaps_child_and_removes_socket(self):
        source = Path(self.tmp.name) / "loop.nql"
        source.write_bytes(b"fn main(){let n=1 while n {n=n} return 0}")
        binary = Path(self.tmp.name) / "loop"
        result = run_native(ROOT / "bootstrap/compiler/b0/x86_64-linux/b0.seed",
                            args=(str(source), "-o", str(binary)))
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        with debugger.Guest(binary, timeout=2) as guest:
            with self.assertRaises(TimeoutError):
                guest.finish()
        self.assertIsNotNone(guest.process.poll())
        self.assertFalse(guest.socket_path.parent.exists())
        self.assertTrue(guest.output.closed)

    def test_missing_qemu_is_not_a_skip(self):
        with patch.object(debugger.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "require qemu"):
                debugger.Guest(self.binary)

    def test_malformed_transport_reaps_guest_and_closes_resources(self):
        client, server = socket.socketpair()
        with client, server, debugger.Guest(self.binary) as guest:
            server.sendall(b"$" + b"0" * 272 + b"#+0")
            server.shutdown(socket.SHUT_WR)
            guest.remote = debugger._Remote(client)
            with self.assertRaisesRegex(debugger.ProtocolError, "checksum"):
                guest.regs()
            self.assertTrue(guest.closed)
            self.assertIsNotNone(guest.process.poll())
            self.assertFalse(guest.socket_path.parent.exists())
            self.assertEqual(guest.socket.fileno(), -1)
            self.assertTrue(guest.input.closed and guest.output.closed and guest.error.closed)

    def test_socket_collision_does_not_start_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gdb.sock"
            path.write_bytes(b"existing socket path")
            with patch.object(debugger.tempfile, "TemporaryDirectory") as temporary, \
                 patch.object(debugger.subprocess, "Popen") as spawn:
                temporary.return_value.__enter__.return_value = tmp
                with self.assertRaises(FileExistsError):
                    debugger.Guest(self.binary)
                spawn.assert_not_called()
            self.assertEqual(path.read_bytes(), b"existing socket path")

    def test_startup_failure_reaps_process_and_cleans_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "not-elf"
            bad.write_bytes(b"not an executable")
            bad.chmod(0o755)
            real_temporary, real_popen = tempfile.TemporaryDirectory, subprocess.Popen
            children = []

            def spawn(*args, **kwargs):
                process = real_popen(*args, **kwargs)
                children.append(process)
                return process

            def temporary(**kwargs):
                return real_temporary(dir=tmp, **kwargs)

            with patch.object(debugger.tempfile, "TemporaryDirectory", side_effect=temporary), \
                 patch.object(debugger.subprocess, "Popen", side_effect=spawn):
                with self.assertRaisesRegex(RuntimeError, "startup failed"):
                    debugger.Guest(bad, timeout=3)
            self.assertEqual(len(children), 1)
            self.assertIsNotNone(children[0].poll())
            self.assertEqual(list(Path(tmp).iterdir()), [bad])


if __name__ == "__main__":
    unittest.main()
