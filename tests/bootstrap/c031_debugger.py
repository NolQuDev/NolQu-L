"""Bounded test-only QEMU RSP transport; never a compiler stage."""

from contextlib import ExitStack
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
import tempfile
import time

REGISTERS = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
             "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15", "rip")
MASK = (1 << 64) - 1
MAX_PACKET = 65536
_HEX = re.compile(r"[0-9a-fA-F]+")
_HEX_BYTES = re.compile(r"(?:[0-9a-fA-F]{2})*")


class ProtocolError(RuntimeError):
    pass


def _stop_signal(reply):
    if not re.fullmatch(r"[ST][0-9a-fA-F]{2}", reply[:3]):
        return None
    fields = reply[3:]
    if reply[0] == "S":
        if fields:
            return None
    elif fields:
        if not fields.endswith(";"):
            return None
        for field in fields[:-1].split(";"):
            match = re.fullmatch(r"([0-9A-Za-z_.-]+):([^:;\x00-\x20\x7f]*)", field)
            if not match:
                return None
            name, value = match.groups()
            if _HEX.fullmatch(name):
                if not value or not _HEX_BYTES.fullmatch(value):
                    return None
            elif name == "thread":
                thread = re.fullmatch(r"(?:p([0-9a-fA-F]+|-1)(?:\.([0-9a-fA-F]+|-1))?"
                                      r"|[0-9a-fA-F]+|-1)", value)
                if not thread or (thread[1] == "-1" and thread[2] not in (None, "-1")):
                    return None
            elif name in ("core", "watch", "rwatch", "awatch"):
                if not _HEX.fullmatch(value):
                    return None
            elif name in ("swbreak", "hwbreak") and value:
                return None
            # Well-formed unknown named fields are ignorable RSP extensions.
    return int(reply[1:3], 16)


class _Remote:
    def __init__(self, connection, timeout=4.0):
        self.connection = connection
        self.timeout = timeout
        self.buffer = bytearray()

    def _read(self, count, deadline):
        while len(self.buffer) < count:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("debugger response deadline exceeded")
            self.connection.settimeout(remaining)
            data = self.connection.recv(4096)
            if not data:
                raise ProtocolError("EOF in debugger response")
            self.buffer.extend(data)
        result = bytes(self.buffer[:count])
        del self.buffer[:count]
        return result

    def command(self, payload):
        raw = payload.encode("ascii")
        deadline = time.monotonic() + self.timeout
        self.connection.settimeout(self.timeout)
        self.connection.sendall(b"$" + raw + b"#" + f"{sum(raw) & 255:02x}".encode())
        for _ in range(1024):
            byte = self._read(1, deadline)
            if byte == b"$":
                break
            if byte != b"+":
                raise ProtocolError("invalid debugger acknowledgement")
        else:
            raise ProtocolError("excessive debugger acknowledgements")
        raw = bytearray()
        while True:
            byte = self._read(1, deadline)
            if byte == b"#":
                break
            raw.extend(byte)
            if len(raw) > MAX_PACKET:
                raise ProtocolError("oversized debugger packet")
        checksum = self._read(2, deadline)
        if any(byte not in b"0123456789abcdefABCDEF" for byte in checksum):
            raise ProtocolError("invalid debugger checksum")
        expected = int(checksum, 16)
        if expected != sum(raw) & 255:
            raise ProtocolError("debugger checksum mismatch")
        decoded = bytearray()
        index = 0
        while index < len(raw):
            byte = raw[index]
            index += 1
            if byte in (125, 42):
                if index == len(raw):
                    raise ProtocolError("truncated escape/repetition")
                following = raw[index]
                index += 1
                if byte == 125:
                    decoded.append(following ^ 32)
                else:
                    count = following - 29
                    if not decoded or not 3 <= count <= 97:
                        raise ProtocolError("invalid debugger repetition")
                    decoded.extend(bytes([decoded[-1]]) * count)
            else:
                decoded.append(byte)
            if len(decoded) > MAX_PACKET:
                raise ProtocolError("oversized decoded debugger packet")
        self.connection.sendall(b"+")
        try:
            return decoded.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ProtocolError("non-ASCII debugger response") from exc


class Guest:
    def __init__(self, binary, data=b"", timeout=10.0, *, args=()):
        if timeout <= 0:
            raise ValueError("guest timeout must be positive")
        binary = Path(binary).resolve(strict=True)
        qemu = shutil.which("qemu-x86_64")
        if qemu is None:
            raise RuntimeError("debugger tests require qemu-x86_64")
        self.resources = ExitStack()
        self.process = None
        self.socket = None
        self.closed = False
        self.breakpoints = set()
        self.deadline = time.monotonic() + timeout
        try:
            directory = self.resources.enter_context(tempfile.TemporaryDirectory(prefix="c031-gdb-"))
            self.socket_path = Path(directory) / "gdb.sock"
            if self.socket_path.exists() or self.socket_path.is_symlink():
                raise FileExistsError("debugger socket already exists")
            # Seekable anonymous files prevent blocked pipes before/while QEMU is stopped.
            self.input = self.resources.enter_context(tempfile.TemporaryFile())
            self.output = self.resources.enter_context(tempfile.TemporaryFile())
            self.error = self.resources.enter_context(tempfile.TemporaryFile())
            self.input.write(data)
            self.input.seek(0)
            self.process = subprocess.Popen([qemu, "-g", str(self.socket_path), str(binary), *args],
                                            stdin=self.input, stdout=self.output,
                                            stderr=self.error, close_fds=True)
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            while True:
                if self.process.poll() is not None:
                    self.error.seek(0)
                    raise RuntimeError(f"QEMU debugger startup failed: {self.error.read()!r}")
                self.socket.settimeout(self._remaining())
                try:
                    self.socket.connect(str(self.socket_path))
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    time.sleep(min(0.01, self._remaining()))
            self.remote = _Remote(self.socket)
            reply = self.cmd("?")
            if _stop_signal(reply) is None:
                self._fail(f"guest did not stop at startup: {reply}")
        except BaseException:
            self.close()
            raise

    def _remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("guest debugger deadline exceeded")
        return remaining

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def cmd(self, command):
        try:
            self.remote.timeout = self._remaining()
            return self.remote.command(command)
        except BaseException:
            self.close()
            raise

    def _fail(self, message):
        self.close()
        raise ProtocolError(message)

    def _register_packet(self):
        reply = self.cmd("g")
        if not _HEX_BYTES.fullmatch(reply):
            self._fail("invalid register encoding")
        if len(reply) < len(REGISTERS) * 16:
            self._fail("truncated x86_64 register packet")
        return bytes.fromhex(reply)

    def regs(self):
        return dict(zip(REGISTERS, struct.unpack_from("<17Q", self._register_packet())))

    def setregs(self, **values):
        if set(values) - set(REGISTERS):
            raise ValueError("unknown register")
        packet = bytearray(self._register_packet())
        for name, value in values.items():
            struct.pack_into("<Q", packet, REGISTERS.index(name) * 8, value & MASK)
        if self.cmd("G" + packet.hex()) != "OK":
            self._fail("register update rejected")

    def read_memory(self, address, count):
        if not 0 <= address <= MASK or not 0 <= count <= MAX_PACKET // 2:
            raise ValueError("invalid debugger memory range")
        reply = self.cmd(f"m{address:x},{count:x}")
        if not _HEX_BYTES.fullmatch(reply):
            self._fail("invalid memory response")
        if len(reply) != count * 2:
            self._fail("wrong memory response length")
        return bytes.fromhex(reply)

    def bp(self, address, enabled=True):
        if not 0 <= address <= MASK:
            raise ValueError("invalid breakpoint address")
        if self.cmd(f'{"Z" if enabled else "z"}0,{address:x},1') != "OK":
            self._fail("breakpoint update rejected")
        if enabled:
            self.breakpoints.add(address)
        else:
            self.breakpoints.discard(address)

    def until(self, address):
        reply = self.cmd("c")
        if _stop_signal(reply) != 5:
            self._fail(f"unexpected guest stop: {reply}")
        regs = self.regs()
        if regs["rip"] != address:
            self._fail(f'expected stop at {address:x}, got {regs["rip"]:x}')
        return regs

    def _syscall(self):
        regs = self.regs()
        if self.read_memory(regs["rip"], 2) != b"\x0f\x05":
            raise ValueError("fault injection requires a verified syscall instruction")
        return regs

    def inject(self, result):
        regs = self._syscall()
        self.setregs(rax=result, rip=regs["rip"] + 2,
                     rcx=0xdeadbeefdeadbeef, r11=0xabad1deaabad1dea)

    def short_write(self, count):
        regs = self._syscall()
        if regs["rax"] != 1 or not 0 < count <= regs["rdx"]:
            raise ValueError("short_write requires write with a positive bounded count")
        address = regs["rip"]
        had_breakpoint = address in self.breakpoints
        had_after_breakpoint = address + 2 in self.breakpoints
        if had_breakpoint:
            self.bp(address, False)
        self.setregs(rdx=count)
        # QEMU may single-step past the instruction following a syscall.
        # Stop at its exact successor before it can mutate syscall registers.
        if not had_after_breakpoint:
            self.bp(address + 2)
        after = self.until(address + 2)
        if after["rax"] != count:
            self._fail("short write did not execute the requested syscall")
        if not had_after_breakpoint:
            self.bp(address + 2, False)
        self.setregs(rdx=regs["rdx"], rcx=0xdeadbeefdeadbeef, r11=0xabad1deaabad1dea)
        if had_breakpoint:
            self.bp(address)

    def finish(self):
        reply = self.cmd("c")
        if not re.fullmatch(r"[WX][0-9a-fA-F]{2}(?:;process:[0-9a-fA-F]+)?", reply):
            self._fail(f"guest did not exit: {reply}")
        self.process.wait(timeout=self._remaining())
        self.output.seek(0)
        self.error.seek(0)
        return self.process.returncode, self.output.read(), self.error.read()

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.socket is not None:
                self.socket.close()
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.kill()
                self.process.wait(timeout=5)
        finally:
            self.resources.close()
