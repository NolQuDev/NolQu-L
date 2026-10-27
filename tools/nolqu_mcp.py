from mcp.server.fastmcp import FastMCP
import hashlib
import ast
from contextlib import contextmanager
from contextvars import ContextVar
import json
import subprocess
import pathlib
import re
import shlex
import shutil
import stat
import struct
import os
import signal
import sys
import tempfile
import time
from collections import deque
from typing import Any

mcp = FastMCP("nolqu-l-compiler-tools")

# ---------------------------------------------------------------------------
# Root resolution
# ---------------------------------------------------------------------------
_env_root = os.environ.get("NOLQU_ROOT", "").strip()
ROOT: pathlib.Path = (
    pathlib.Path(_env_root).resolve()
    if _env_root
    else pathlib.Path(__file__).resolve().parents[1]
)
DEVELOPMENT_DOCUMENT = "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md"

CANONICAL_NQL = ROOT / "nql"
CANONICAL_NQLC = ROOT / "nqlc"
FORMAL_NOLQUL = ROOT / "nolqul"
FORMAL_NOLQULC = ROOT / "nolqulc"

NQL = CANONICAL_NQL
NQLC = CANONICAL_NQLC

COMPILER = NQLC

MAX_WRITE_BYTES = 50 * 1024 * 1024
MAX_READ_FILE_BYTES = 200 * 1024 * 1024
MAX_TOOL_OUTPUT_BYTES = int(os.environ.get("NOLQU_MCP_MAX_OUTPUT_BYTES", 1024 * 1024))
MAX_STDOUT_BYTES = int(os.environ.get("NOLQU_MCP_MAX_STDOUT_BYTES", 512 * 1024))
MAX_STDERR_BYTES = int(os.environ.get("NOLQU_MCP_MAX_STDERR_BYTES", 512 * 1024))
AUDIT_ENABLED = os.environ.get("NOLQU_MCP_AUDIT", "1") != "0"
AUDIT_PATH = ROOT / ".nolqu-mcp" / "audit.jsonl"

CAP_READ_ONLY = "READ_ONLY"
CAP_WRITE = "WRITE"
CAP_BUILD = "BUILD"
CAP_DESTRUCTIVE = "DESTRUCTIVE"
CAP_REMOTE = "REMOTE"
CAP_UNSAFE_SHELL = "UNSAFE_SHELL"

_LEGACY_TOOLS = {"compile_file"}
_EXPERIMENTAL_TOOLS = {
    "nql_fmt", "nql_lint", "nql_doc", "generate_ccdb",
    "build_c0_frontend", "run_c0_frontend_probe",
    "build_c0_backend", "run_c0_backend_probe",
}
_CAPABILITY_OVERRIDES = {
    "exec_shell": CAP_UNSAFE_SHELL,
    "exec_with_input": CAP_UNSAFE_SHELL,
    "write_file": CAP_WRITE,
    "patch_file": CAP_WRITE,
    "append_file": CAP_WRITE,
    "move_file": CAP_WRITE,
    "copy_file": CAP_WRITE,
    "mkdir": CAP_WRITE,
    "chmod_file": CAP_WRITE,
    "copy_dir": CAP_WRITE,
    "touch_file": CAP_WRITE,
    "symlink": CAP_WRITE,
    "backup_file": CAP_WRITE,
    "replace_lines": CAP_WRITE,
    "insert_lines": CAP_WRITE,
    "nql_init": CAP_WRITE,
    "nql_build": CAP_BUILD,
    "nql_run": CAP_BUILD,
    "nql_test": CAP_BUILD,
    "nql_check": CAP_BUILD,
    "nql_fmt": CAP_BUILD,
    "nql_lint": CAP_BUILD,
    "nql_doc": CAP_BUILD,
    "verify_migration": CAP_BUILD,
    "self_host_generation": CAP_BUILD,
    "delete_file": CAP_DESTRUCTIVE,
    "nql_clean": CAP_DESTRUCTIVE,
    "git_restore": CAP_DESTRUCTIVE,
    "git_stash": CAP_DESTRUCTIVE,
    "git_branch": CAP_DESTRUCTIVE,
    "git_tag": CAP_DESTRUCTIVE,
    "clean_rebuild": CAP_DESTRUCTIVE,
    "git_pull": CAP_REMOTE,
    "git_push": CAP_REMOTE,
}

# ---------------------------------------------------------------------------
# Blocklist untuk exec_shell
# ---------------------------------------------------------------------------
_SHELL_BLOCKLIST = [
    "rm -rf /", "rm -rf ~", "dd if=",
    "mkfs", "fdisk", ":(){:|:&};:",
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_path(raw: str) -> pathlib.Path:
    if not raw or raw.strip() == "":
        return ROOT
    p = (ROOT / raw).resolve()
    try:
        p.relative_to(ROOT)
    except ValueError:
        raise ValueError(f"Path '{raw}' is outside the project root.")
    return p


def _truncate_output(value: str, limit: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return value, False
    if limit < 64:
        limit = 64
    head_size = (limit * 2) // 3
    tail_size = limit - head_size
    head = encoded[:head_size].decode("utf-8", errors="replace")
    tail = encoded[-tail_size:].decode("utf-8", errors="replace")
    omitted = len(encoded) - head_size - tail_size
    marker = f"\n... [truncated {omitted} bytes] ...\n"
    return head + marker + tail, True


def _git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("ascii", errors="ignore").strip() or None


def _calling_tool_name(fallback: str) -> str:
    frame = sys._getframe(2)
    while frame is not None:
        if frame.f_globals.get("__name__") == __name__:
            name = frame.f_code.co_name
            if not name.startswith("_") and name not in {"mcp_audit_log"}:
                return name
        frame = frame.f_back
    return fallback


_COMPILE_AUDIT: ContextVar[dict[str, Any] | None] = ContextVar("compile_audit", default=None)


@contextmanager
def _defer_compile_audit():
    # Each compile owns at most one pending command event, including when nested.
    state = {"event": None, "artifacts": []}
    token = _COMPILE_AUDIT.set(state)
    try:
        yield state
    finally:
        _COMPILE_AUDIT.reset(token)
        event = state["event"]
        if event is not None:
            event["artifacts"] = state["artifacts"]
            _write_audit_event(event)


def _audit_event(
    *,
    tool: str,
    capability: str,
    arguments: str,
    duration_ms: int,
    exit_code: int | None,
    ok: bool,
    changed_files: list[str] | None = None,
    artifacts: list[str] | None = None,
    git_head_before: str | None = None,
    git_head_after: str | None = None,
) -> None:
    if not AUDIT_ENABLED:
        return
    summary, _ = _truncate_output(arguments, 1024)
    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool,
        "capability": capability,
        "arguments": summary,
        "duration_ms": duration_ms,
        "exit_code": exit_code,
        "ok": ok,
        "changed_files": changed_files or [],
        "artifacts": artifacts or [],
        "git_head_before": git_head_before,
        "git_head_after": git_head_after,
    }
    deferred = _COMPILE_AUDIT.get()
    if deferred is not None and deferred["event"] is None:
        deferred["event"] = event
        return
    _write_audit_event(event)


def _write_audit_event(event: dict[str, Any]) -> None:
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
        descriptor = os.open(
            AUDIT_PATH,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        # Auditing must never hide or alter the primary tool result.
        return


def _error_result(
    message: str,
    *,
    capability: str = CAP_READ_ONLY,
    command: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "exit_code": None,
        "stdout": "",
        "stderr": message,
        "duration_ms": 0,
        "timed_out": False,
        "command": command or [],
        "capability": capability,
        "stdout_truncated": False,
        "stderr_truncated": False,
        "changed_files": [],
        "artifacts": [],
    }


def _process_supervisor_source() -> str:
    # A disposable subreaper owns this command only. Setting subreaper state in
    # the MCP server would adopt (and potentially reap) other tools' children.
    return r'''
import ctypes
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

status_fd, timeout = int(sys.argv[1]), float(sys.argv[2])
command = sys.argv[3:]
child = None
status = {}

class Interrupted(BaseException):
    pass

def interrupt(signum, frame):
    raise Interrupted()

def snapshot():
    processes = {}
    for path in pathlib.Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
            processes[int(path.parent.name)] = (int(fields[1]), fields[19])
        except (OSError, ValueError, IndexError):
            continue
    owned = {os.getpid()}
    while True:
        found = {pid for pid, (parent, _) in processes.items() if parent in owned}
        if found <= owned:
            return {pid: processes[pid][1] for pid in owned if pid != os.getpid()}
        owned.update(found)

def pidfd_functions(libc):
    if hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'):
        return os.pidfd_open, signal.pidfd_send_signal
    # Android Python can omit these bindings despite runtime libc/kernel
    # support. Use the declared libc ABI, never raw ISA syscall numbers or PIDs.
    try:
        native_open = libc.pidfd_open
        native_send = libc.pidfd_send_signal
    except AttributeError as exc:
        raise OSError('safe command cleanup requires Linux pidfds') from exc
    native_open.argtypes = (ctypes.c_int, ctypes.c_uint)
    native_open.restype = ctypes.c_int
    native_send.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint)
    native_send.restype = ctypes.c_int

    def open_handle(pid):
        descriptor = native_open(pid, 0)
        if descriptor < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return descriptor

    def send_handle(descriptor, signum):
        if native_send(descriptor, signum, None, 0) < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))

    return open_handle, send_handle

def send(pid, identity, signum):
    # pidfds bind signals to the observed process, even if a PID is recycled
    # between discovery and signaling. No process-group or process-name sweep.
    try:
        descriptor = pidfd_open(pid)
    except ProcessLookupError:
        return
    try:
        try:
            fields = pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
            if fields[19] == identity:
                pidfd_send_signal(descriptor, signum)
        except ProcessLookupError:
            pass
        except FileNotFoundError:
            pass
    finally:
        os.close(descriptor)

def cleanup():
    # Repeated discovery also catches children forked by a TERM handler and
    # orphans adopted from nested sessions. All waits are local to this worker.
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, signal.SIG_IGN)
    started = time.monotonic()
    deadline = started + 1.5
    notified = set()
    while True:
        owned = snapshot()
        force = time.monotonic() >= started + 0.2
        for pid, identity in owned.items():
            if force or (pid, identity) not in notified:
                send(pid, identity, signal.SIGKILL if force else signal.SIGTERM)
                notified.add((pid, identity))
        while True:
            try:
                pid, wait_status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                return
            if pid == 0:
                break
            if child is not None and pid == child.pid:
                child.returncode = os.waitstatus_to_exitcode(wait_status)
        if time.monotonic() >= deadline:
            raise OSError('owned process cleanup exceeded its deadline')
        time.sleep(0.01)

try:
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0):  # PR_SET_CHILD_SUBREAPER, in this worker only
        raise OSError(ctypes.get_errno(), 'cannot establish command ownership')
    pidfd_open, pidfd_send_signal = pidfd_functions(libc)
    descriptor = pidfd_open(os.getpid())
    try:
        pidfd_send_signal(descriptor, 0)
    finally:
        os.close(descriptor)
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, interrupt)
    try:
        child = subprocess.Popen(command, start_new_session=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = child.communicate(timeout=max(0, timeout))
            status['returncode'] = child.returncode
        except subprocess.TimeoutExpired as exc:
            status['timed_out'] = True
            stdout, stderr = exc.output or b'', exc.stderr or b''
    except Interrupted:
        status['interrupted'] = True
    finally:
        cleanup()
    if not status.get('interrupted'):
        if status.get('timed_out'):
            # Drain only after terminating all owned writers. A second bounded
            # communicate retains its initial partial output without doubling it.
            try:
                stdout, stderr = child.communicate(timeout=0.5)
            except subprocess.TimeoutExpired as exc:
                stdout, stderr = exc.output or b'', exc.stderr or b''
        sys.stdout.buffer.write(stdout)
        sys.stderr.buffer.write(stderr)
except OSError as exc:
    status['error'] = {'errno': exc.errno, 'detail': exc.strerror or str(exc)}
finally:
    with os.fdopen(status_fd, 'w') as stream:
        json.dump(status, stream)
'''


def _stop_process_supervisor(process: subprocess.Popen) -> None:
    process.send_signal(signal.SIGTERM)
    deadline = time.monotonic() + 2.5
    while True:
        try:
            # Cancellation must also work after a pipe read failed. The worker
            # terminates/reaps writers before forwarding captured output.
            process.wait(timeout=max(0, deadline - time.monotonic()))
            return
        except KeyboardInterrupt:
            # Finish ownership cleanup before re-raising the original exception.
            if time.monotonic() < deadline:
                continue
        except subprocess.TimeoutExpired:
            pass
        process.kill()
        process.wait(timeout=0.5)
        return


def _acquire_process_supervisor(process: subprocess.Popen, args: list[str], **options) -> None:
    import threading

    gate = threading.Lock()
    finished = threading.Event()
    cancelled = committed = False
    errors = []

    def acquire() -> None:
        nonlocal committed
        try:
            with gate:
                if cancelled:
                    return
                committed = True
            # Python SIGINT is delivered to the main thread. Keep construction
            # off that thread so cancellation cannot lose fork/exec's PID before
            # Popen records it on the already retained process object.
            subprocess.Popen.__init__(process, args, **options)
        except BaseException as exc:
            errors.append(exc)
        finally:
            finished.set()

    thread = threading.Thread(target=acquire, name='nolqu-process-acquisition')
    interruption = None
    try:
        thread.start()
        finished.wait()
    except BaseException as exc:
        interruption = exc
    finally:
        while True:
            try:
                # Close the launch gate even if Thread.start itself was
                # interrupted. A late-starting thread must not create a child.
                with gate:
                    cancelled = True
                    joining = committed
                if joining:
                    finished.wait()
                    thread.join()
                break
            except (KeyboardInterrupt, SystemExit) as exc:
                if interruption is None:
                    interruption = exc
    if interruption is not None:
        raise interruption
    if errors:
        raise errors[0]


def _run_process(
    cmd: list[str], *, cwd: pathlib.Path, timeout: float,
    env: dict[str, str] | None, stdin: bytes | None,
) -> subprocess.CompletedProcess:
    with tempfile.TemporaryFile() as status_file:
        # Register the handle before any child can exist, including when an
        # initialized Popen constructor raises instead of returning normally.
        process = subprocess.Popen.__new__(subprocess.Popen)
        try:
            _acquire_process_supervisor(
                process,
                [sys.executable, '-I', '-S', '-c', _process_supervisor_source(),
                 str(status_file.fileno()), str(timeout), *cmd],
                cwd=cwd, env=env, start_new_session=True,
                stdin=subprocess.DEVNULL if stdin is None else subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                pass_fds=(status_file.fileno(),),
            )
            stdout, stderr = process.communicate(input=stdin, timeout=max(0, timeout) + 3)
        except BaseException as original:
            try:
                if getattr(process, 'pid', None) is not None:
                    _stop_process_supervisor(process)
            except BaseException as cleanup_error:
                original.add_note(f'command cleanup failed: {cleanup_error}')
            finally:
                for name in ('stdin', 'stdout', 'stderr'):
                    stream = getattr(process, name, None)
                    if stream is not None:
                        try:
                            stream.close()
                        except OSError as close_error:
                            original.add_note(f'command pipe close failed: {close_error}')
            raise
        status_file.seek(0)
        try:
            status = json.load(status_file)
        except (ValueError, UnicodeError) as exc:
            raise OSError('command supervisor returned no valid status') from exc
        if 'error' in status:
            error = status['error']
            raise OSError(error['errno'], error['detail'])
        if status.get('timed_out'):
            raise subprocess.TimeoutExpired(cmd, timeout, output=stdout, stderr=stderr)
        if 'returncode' not in status:
            raise OSError('command supervisor was interrupted')
        return subprocess.CompletedProcess(cmd, status['returncode'], stdout, stderr)


def _run_result(
    cmd: list[str],
    timeout: float = 30,
    cwd: pathlib.Path | None = None,
    *,
    env: dict[str, str] | None = None,
    stdin: str | bytes | None = None,
    capability: str = CAP_BUILD,
    artifacts: list[str] | None = None,
    changed_files: list[str] | None = None,
) -> dict[str, Any]:
    work_dir = cwd or ROOT
    started = time.monotonic()
    tool_name = _calling_tool_name(pathlib.Path(str(cmd[0])).name if cmd else "command")
    git_head_before = _git_head()

    def audited(result: dict[str, Any]) -> dict[str, Any]:
        result["changed_files"] = changed_files or result.get("changed_files", [])
        _audit_event(
            tool=tool_name,
            capability=capability,
            arguments=shlex.join(str(item) for item in cmd),
            duration_ms=int(result.get("duration_ms", 0)),
            exit_code=result.get("exit_code"),
            ok=bool(result.get("ok")),
            changed_files=result.get("changed_files", []),
            artifacts=result.get("artifacts", []),
            git_head_before=git_head_before,
            git_head_after=_git_head(),
        )
        return result

    try:
        result = _run_process(
            cmd,
            cwd=work_dir,
            stdin=(stdin.encode("utf-8") if isinstance(stdin, str) else stdin),
            timeout=timeout,
            env=env,
        )
        stdout, stdout_truncated = _truncate_output(
            result.stdout.decode("utf-8", errors="replace"), MAX_STDOUT_BYTES
        )
        stderr, stderr_truncated = _truncate_output(
            result.stderr.decode("utf-8", errors="replace"), MAX_STDERR_BYTES
        )
        return audited({
            "ok": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": stdout.rstrip("\n"),
            "stderr": stderr.rstrip("\n"),
            "duration_ms": round((time.monotonic() - started) * 1000),
            "timed_out": False,
            "command": [str(item) for item in cmd],
            "capability": capability,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "changed_files": changed_files or [],
            "artifacts": artifacts or [],
        })
    except FileNotFoundError:
        result = _error_result(
            f"command not found: {cmd[0]}", capability=capability, command=cmd
        )
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return audited(result)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        result = _error_result(
            f"cannot execute {cmd[0]}: {detail}",
            capability=capability,
            command=cmd,
        )
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return audited(result)
    except subprocess.TimeoutExpired as exc:
        result = _error_result(
            f"timed out after {timeout}s", capability=capability, command=cmd
        )
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        result["timed_out"] = True
        result["stdout"], result["stdout_truncated"] = _truncate_output(
            (exc.output or b"").decode("utf-8", errors="replace").rstrip("\n"),
            MAX_STDOUT_BYTES,
        )
        stderr = result["stderr"]
        if exc.stderr:
            stderr += "\n" + exc.stderr.decode("utf-8", errors="replace").rstrip("\n")
        result["stderr"], result["stderr_truncated"] = _truncate_output(
            stderr, MAX_STDERR_BYTES
        )
        return audited(result)


def _format_result(result: dict[str, Any]) -> str:
    command = shlex.join(str(item) for item in result.get("command", []))
    parts = [f"$ {command}", f"exit_code: {result.get('exit_code')}"]
    if result.get("timed_out"):
        parts.append(f"timed_out: true ({result.get('duration_ms', 0)}ms)")
    if result.get("stdout"):
        parts += ["\nSTDOUT:", str(result["stdout"])]
    if result.get("stderr"):
        parts += ["\nSTDERR:", str(result["stderr"])]
    rendered, _ = _truncate_output("\n".join(parts), MAX_TOOL_OUTPUT_BYTES)
    return rendered


def _run(
    cmd: list[str],
    timeout: float = 30,
    cwd: pathlib.Path | None = None,
    *,
    env: dict[str, str] | None = None,
    stdin: str | bytes | None = None,
) -> str:
    return _format_result(
        _run_result(cmd, timeout=timeout, cwd=cwd, env=env, stdin=stdin)
    )


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(
    path: pathlib.Path,
    content: str,
    *,
    expected_sha256: str = "",
) -> int:
    started = time.monotonic()
    tool_name = _calling_tool_name("atomic_write")
    git_head_before = _git_head()
    try:
        relative_path = str(path.relative_to(ROOT))
    except ValueError:
        relative_path = str(path)
    arguments = (
        f"path={relative_path} bytes={len(content.encode('utf-8'))} "
        f"expected_sha256={'present' if expected_sha256 else 'none'}"
    )
    try:
        if expected_sha256:
            actual = _sha256(path) if path.exists() else ""
            if actual != expected_sha256.lower():
                raise RuntimeError("source changed since read")

        path.parent.mkdir(parents=True, exist_ok=True)
        previous_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
        payload = content.encode("utf-8")
        fd, temporary_name = tempfile.mkstemp(
            prefix=".nolqu-mcp-write-", dir=path.parent
        )
        temporary = pathlib.Path(temporary_name)
        try:
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, previous_mode)
                os.replace(temporary, path)
                try:
                    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                except OSError:
                    directory_fd = -1
                if directory_fd >= 0:
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
        except BaseException:
            raise
    except BaseException:
        _audit_event(
            tool=tool_name,
            capability=CAP_WRITE,
            arguments=arguments,
            duration_ms=round((time.monotonic() - started) * 1000),
            exit_code=1,
            ok=False,
            changed_files=[],
            git_head_before=git_head_before,
            git_head_after=_git_head(),
        )
        raise
    _audit_event(
        tool=tool_name,
        capability=CAP_WRITE,
        arguments=arguments,
        duration_ms=round((time.monotonic() - started) * 1000),
        exit_code=0,
        ok=True,
        changed_files=[relative_path],
        git_head_before=git_head_before,
        git_head_after=_git_head(),
    )
    return len(payload)


def _tool_capability(name: str) -> str:
    if name in _CAPABILITY_OVERRIDES:
        return _CAPABILITY_OVERRIDES[name]
    if (
        name.startswith(("build_", "run_", "compile_", "assemble_", "link_"))
        or name in {"benchmark", "memory_check", "profile_program", "strip_binary"}
    ):
        return CAP_BUILD
    if name.startswith("git_") and name not in {"git_status", "git_diff", "git_log", "git_show"}:
        return CAP_WRITE
    return CAP_READ_ONLY


def _tool_stability(name: str) -> str:
    if name in _LEGACY_TOOLS:
        return "legacy"
    if name in _EXPERIMENTAL_TOOLS:
        return "experimental"
    return "stable"


# ---------------------------------------------------------------------------
# Health & discovery
# ---------------------------------------------------------------------------

@mcp.tool()
def ping() -> str:
    """
    Health check — verify MCP server is running and project root is accessible.
    """
    version_file = ROOT / "VERSION"
    version = version_file.read_text().strip() if version_file.exists() else "(unknown)"
    compiler_ok = "yes" if NQLC.exists() else "no (run build_compiler)"
    nql_ok = "yes" if NQL.exists() else "no"
    return (
        f"MCP server running\n"
        f"  root:     {ROOT}\n"
        f"  version:  {version}\n"
        f"  nqlc:     {compiler_ok} ({NQLC.name}, canonical)\n"
        f"  nql:      {nql_ok} ({NQL.name}, canonical)"
    )

@mcp.tool()
def tool_manifest() -> list[dict[str, str]]:
    """Return the registered tool catalog with capability and stability metadata."""
    manager = getattr(mcp, "_tool_manager", None)
    registered = getattr(manager, "_tools", {}) if manager is not None else {}
    manifest: list[dict[str, str]] = []
    for name, tool in registered.items():
        description = (getattr(tool, "description", "") or "").strip()
        summary = description.splitlines()[0] if description else ""
        manifest.append({
            "name": name,
            "description": summary,
            "capability": _tool_capability(name),
            "stability": _tool_stability(name),
        })
    return manifest


@mcp.tool()
def list_tools(stability: str = "", capability: str = "") -> str:
    """
    List registered MCP tools. Optional filters accept stable/experimental/legacy
    and READ_ONLY/WRITE/BUILD/DESTRUCTIVE/REMOTE/UNSAFE_SHELL.
    """
    stability = stability.lower().strip()
    capability = capability.upper().strip()
    valid_stability = {"", "stable", "experimental", "legacy"}
    valid_capabilities = {
        "", CAP_READ_ONLY, CAP_WRITE, CAP_BUILD, CAP_DESTRUCTIVE,
        CAP_REMOTE, CAP_UNSAFE_SHELL,
    }
    if stability not in valid_stability:
        return "ERROR: stability must be stable, experimental, or legacy"
    if capability not in valid_capabilities:
        return "ERROR: capability filter is invalid"

    items = [
        item for item in tool_manifest()
        if (not stability or item["stability"] == stability)
        and (not capability or item["capability"] == capability)
    ]
    lines = ["=== NolQu-L MCP Tools ==="]
    for item in items:
        lines.append(
            f"  {item['name']:<32} "
            f"[{item['capability']}/{item['stability']}] "
            f"{item['description']}"
        )
    lines.append(f"\nTotal: {len(items)} tool(s)")
    rendered, _ = _truncate_output("\n".join(lines), MAX_TOOL_OUTPUT_BYTES)
    return rendered


@mcp.tool()
def mcp_audit_log(limit: int = 100, tool: str = "") -> dict[str, Any]:
    """Read recent local MCP audit events, optionally filtered by tool name."""
    if limit < 1 or limit > 1000:
        return {
            "ok": False,
            "error": "limit must be between 1 and 1000",
            "entries": [],
        }
    if not AUDIT_PATH.exists():
        return {
            "ok": True,
            "path": str(AUDIT_PATH.relative_to(ROOT)),
            "entries": [],
            "malformed_entries": 0,
        }

    entries: deque[dict[str, Any]] = deque(maxlen=limit)
    malformed = 0
    try:
        with AUDIT_PATH.open("r", encoding="utf-8", errors="replace") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    malformed += 1
                    continue
                if tool and event.get("tool") != tool:
                    continue
                entries.append(event)
    except OSError as exc:
        return {"ok": False, "error": str(exc), "entries": []}
    return {
        "ok": True,
        "path": str(AUDIT_PATH.relative_to(ROOT)),
        "entries": list(entries),
        "malformed_entries": malformed,
    }
# Sandbox bypass tools
# ---------------------------------------------------------------------------

@mcp.tool()
def exec_shell(
    command: str,
    timeout: int = 30,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Last-resort arbitrary shell execution. Disabled by default. It requires
    confirm=true and NOLQU_MCP_ALLOW_UNSAFE_SHELL=1. Prefer dedicated tools.

    Args:
        command: Shell command (e.g. "ls -la", "make", "cat file").
        timeout: Max seconds to wait (default 30).
        confirm: Explicit acknowledgement for this unsafe operation.
    """
    if not confirm:
        return _error_result(
            "UNSAFE_SHELL requires confirm=true",
            capability=CAP_UNSAFE_SHELL,
        )
    if os.environ.get("NOLQU_MCP_ALLOW_UNSAFE_SHELL") != "1":
        return _error_result(
            "UNSAFE_SHELL is disabled; set NOLQU_MCP_ALLOW_UNSAFE_SHELL=1",
            capability=CAP_UNSAFE_SHELL,
        )
    for blocked in _SHELL_BLOCKLIST:
        if blocked in command:
            return _error_result(
                f"command blocked by secondary guard: {blocked}",
                capability=CAP_UNSAFE_SHELL,
            )
    return _run_result(
        ["sh", "-c", command],
        timeout=timeout,
        capability=CAP_UNSAFE_SHELL,
    )


@mcp.tool()
def write_file(
    file_path: str,
    content: str,
    expected_sha256: str = "",
) -> str:
    """
    Atomically write or overwrite a file inside the project root.
    expected_sha256 rejects stale writes when the file changed after reading.

    Args:
        file_path: Path relative to project root.
        content:         Full content to write to the file.
        expected_sha256: Optional SHA-256 of the currently observed file.
    """
    content_bytes = len(content.encode("utf-8"))
    if content_bytes > MAX_WRITE_BYTES:
        return "ERROR: content terlalu besar (max 50MB)"
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    try:
        written = _atomic_write_text(
            p, content, expected_sha256=expected_sha256
        )
        return f"OK: atomically wrote {written} bytes → {p.relative_to(ROOT)}"
    except RuntimeError as e:
        return f"ERROR: {e}"
    except PermissionError:
        return f"ERROR: permission denied — '{p}'"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def patch_file(
    file_path: str,
    old_str: str,
    new_str: str,
    expected_sha256: str = "",
) -> str:
    """
    Atomically replace a unique string. expected_sha256 prevents overwriting
    concurrent changes observed after the source was read.

    Args:
        file_path: Path relative to project root.
        old_str:   Exact string to find (must appear exactly once).
        new_str:         String to replace it with.
        expected_sha256: Optional SHA-256 of the currently observed file.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"ERROR: cannot read file — {e}"
    count = content.count(old_str)
    if count == 0:
        return f"ERROR: string tidak ditemukan di '{p.relative_to(ROOT)}'"
    if count > 1:
        return f"ERROR: string ditemukan {count} kali — harus unik"
    new_content = content.replace(old_str, new_str, 1)
    try:
        _atomic_write_text(
            p, new_content, expected_sha256=expected_sha256
        )
    except RuntimeError as e:
        return f"ERROR: {e}"
    except PermissionError:
        return f"ERROR: permission denied — '{p}'"
    except OSError as e:
        return f"ERROR: cannot write file — {e}"
    return f"OK: patch applied → {p.relative_to(ROOT)}"


@mcp.tool()
def append_file(
    file_path: str,
    content: str,
    expected_sha256: str = "",
) -> str:
    """
    Append content to the end of a file. Creates file if not exists.

    Args:
        file_path: Path relative to project root.
        content:         Content to append.
        expected_sha256: Optional hash of the existing file.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    try:
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
        payload_size = len((existing + content).encode("utf-8"))
        if payload_size > MAX_WRITE_BYTES:
            return "ERROR: resulting file is too large (max 50MB)"
        _atomic_write_text(
            p, existing + content, expected_sha256=expected_sha256
        )
        return f"OK: atomically appended {len(content.encode('utf-8'))} bytes → {p.relative_to(ROOT)}"
    except RuntimeError as e:
        return f"ERROR: {e}"
    except PermissionError:
        return f"ERROR: permission denied — '{p}'"
    except OSError as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

@mcp.tool()
def get_root() -> str:
    """Return the project root path."""
    return f"ROOT: {ROOT}"


@mcp.tool()
def get_version() -> str:
    """Read and return the NolQu-L version from the VERSION file."""
    version_file = ROOT / "VERSION"
    if not version_file.exists():
        return "ERROR: file VERSION tidak ditemukan di root project"
    content = version_file.read_text(encoding="utf-8").strip()
    if not content:
        return "ERROR: file VERSION kosong"
    return f"NolQu-L version: {content}"


@mcp.tool()
def file_exists(file_path: str) -> str:
    """
    Check if a file or directory exists inside the project root.

    Args:
        file_path: Path relative to project root.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"NOT FOUND: '{file_path}'"
    kind = "directory" if p.is_dir() else "file"
    return f"EXISTS ({kind}): '{file_path}'"


@mcp.tool()
def file_info(file_path: str) -> str:
    """
    Return metadata: size, permissions, timestamps.

    Args:
        file_path: Path relative to project root.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    s = p.stat()
    perms = stat.filemode(s.st_mode)
    import datetime
    mtime = datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    kind  = "directory" if p.is_dir() else "file"
    return (
        f"=== {file_path} ===\n"
        f"type:        {kind}\n"
        f"size:        {s.st_size} bytes\n"
        f"permissions: {perms}\n"
        f"modified:    {mtime}"
    )


@mcp.tool()
def read_file(file_path: str, max_lines: int = 200, start_line: int = 1) -> str:
    """
    Read file contents with offset support. Max file size: 200MB.
    Output is still line-limited by max_lines.

    Args:
        file_path:  Path relative to project root.
        max_lines:  Maximum lines to return (default 200).
        start_line: Line to start from, 1-indexed (default 1).
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    if p.stat().st_size > MAX_READ_FILE_BYTES:
        return "ERROR: file terlalu besar (max 200MB)"
    lines = p.read_text(errors="replace").splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    end   = start + max_lines
    chunk = lines[start:end]
    body  = "\n".join(chunk)
    result = (
        f"=== {p.relative_to(ROOT)} (lines {start+1}-{min(end,total)} of {total}) ===\n"
        f"sha256: {_sha256(p)}\n{body}"
    )
    if end < total:
        result += f"\n\n... (truncated — {total - end} more lines, use start_line={end+1})"
    rendered, _ = _truncate_output(result, MAX_TOOL_OUTPUT_BYTES)
    return rendered


@mcp.tool()
def head_file(file_path: str, lines: int = 20) -> str:
    """
    Read the first N lines of a file.

    Args:
        file_path: Path relative to project root.
        lines:     Number of lines to read (default 20).
    """
    return read_file(file_path, max_lines=lines, start_line=1)


@mcp.tool()
def tail_file(file_path: str, lines: int = 20) -> str:
    """
    Read the last N lines of a file.

    Args:
        file_path: Path relative to project root.
        lines:     Number of lines to read (default 20).
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    if p.stat().st_size > MAX_READ_FILE_BYTES:
        return "ERROR: file terlalu besar (max 200MB)"
    all_lines = p.read_text(errors="replace").splitlines()
    total     = len(all_lines)
    start     = max(0, total - lines)
    body      = "\n".join(all_lines[start:])
    return f"=== {p.relative_to(ROOT)} (last {min(lines,total)} of {total} lines) ===\n{body}"


@mcp.tool()
def wc_file(file_path: str) -> str:
    """
    Count lines, words, and bytes in a file.

    Args:
        file_path: Path relative to project root.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    return _run(["wc", str(p)], timeout=10)


@mcp.tool()
def chmod_file(file_path: str, mode: str = "+x") -> str:
    """
    Change file permissions.

    Args:
        file_path: Path relative to project root.
        mode:      chmod mode (e.g. "+x", "755", "644"). Default: "+x".
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    return _run(["chmod", mode, str(p)], timeout=10)


@mcp.tool()
def delete_file(file_path: str, confirm: bool = False) -> str:
    """
    Delete a file inside the project root.
    Directories not supported — use exec_shell for that.

    Args:
        file_path: Path relative to project root.
        confirm: Must be true because deletion is destructive.
    """
    if not confirm:
        return "ERROR: DESTRUCTIVE operation requires confirm=true"
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    if p.is_dir():
        return f"ERROR: '{file_path}' adalah direktori. Gunakan exec_shell."
    try:
        p.unlink()
        return f"OK: deleted → {file_path}"
    except PermissionError:
        return f"ERROR: permission denied — '{file_path}'"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def move_file(src_path: str, dst_path: str) -> str:
    """
    Move or rename a file inside the project root.

    Args:
        src_path: Source path relative to project root.
        dst_path: Destination path relative to project root.
    """
    try:
        src = _safe_path(src_path)
        dst = _safe_path(dst_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not src.exists():
        return f"ERROR: source not found — '{src_path}'"
    if dst.exists():
        return f"ERROR: destination already exists — '{dst_path}'"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return f"OK: moved {src_path} → {dst_path}"
    except PermissionError:
        return "ERROR: permission denied"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def copy_file(src_path: str, dst_path: str) -> str:
    """
    Copy a file inside the project root.

    Args:
        src_path: Source path relative to project root.
        dst_path: Destination path relative to project root.
    """
    import shutil
    try:
        src = _safe_path(src_path)
        dst = _safe_path(dst_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not src.exists():
        return f"ERROR: source not found — '{src_path}'"
    if src.is_dir():
        return f"ERROR: '{src_path}' adalah direktori. Hanya file yang didukung."
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        return f"OK: copied {src_path} → {dst_path}"
    except PermissionError:
        return "ERROR: permission denied"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def mkdir(dir_path: str) -> str:
    """
    Create a directory (and parents) inside the project root.

    Args:
        dir_path: Directory path relative to project root.
    """
    try:
        p = _safe_path(dir_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if p.exists():
        return f"EXISTS: '{dir_path}' sudah ada"
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"OK: created → {dir_path}"
    except PermissionError:
        return f"ERROR: permission denied — '{dir_path}'"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def list_files(directory: str = "", pattern: str = "") -> str:
    """
    List files and directories inside the project root.

    Args:
        directory: Subdirectory to list (relative to project root).
        pattern:   Optional glob pattern (e.g. "*.nql", "*.asm").
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"
    if not target.exists():
        return f"ERROR: direktori tidak ditemukan — '{directory}'"
    if not target.is_dir():
        return f"ERROR: '{directory}' bukan direktori"
    try:
        entries = sorted(target.glob(pattern) if pattern else target.iterdir())
    except OSError as e:
        return f"ERROR: {e}"
    if not entries:
        suffix = f" (pattern: {pattern})" if pattern else ""
        return f"(kosong){suffix} — {directory or '.'}"
    lines = []
    for e in entries:
        rel  = e.relative_to(ROOT)
        kind = "/" if e.is_dir() else ""
        size = f"  {e.stat().st_size}B" if e.is_file() else ""
        lines.append(f"  {rel}{kind}{size}")
    label  = str(target.relative_to(ROOT)) if directory else "."
    suffix = f" (pattern: {pattern})" if pattern else ""
    return f"=== {label}{suffix} ===\n" + "\n".join(lines)


@mcp.tool()
def find_files(name_pattern: str, directory: str = "") -> str:
    """
    Find files by name pattern recursively inside the project root.

    Args:
        name_pattern: Filename pattern (e.g. "*.nql", "main.*", "VERSION").
        directory:    Subdirectory to search in (default: project root).
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"
    if not target.exists():
        return f"ERROR: direktori tidak ditemukan — '{directory}'"
    cmd = ["find", str(target), "-name", name_pattern, "-type", "f"]
    return _run(cmd, timeout=15)


@mcp.tool()
def search_files(pattern: str, directory: str = "", file_glob: str = "") -> str:
    """
    Search for a text pattern across files (like grep -rn).

    Args:
        pattern:   Text or regex to search for.
        directory: Subdirectory to search in (default: project root).
        file_glob: Limit to files matching this glob (e.g. "*.nql").
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"
    cmd = ["grep", "-rn"]
    if file_glob:
        cmd += ["--include", file_glob]
    cmd += [pattern, str(target)]
    return _run(cmd, timeout=15)


@mcp.tool()
def grep_file(pattern: str, file_path: str, context_lines: int = 0) -> str:
    """
    Search for a text pattern in a single file.

    Args:
        pattern:       Text or regex to search for.
        file_path:     Path relative to project root.
        context_lines: Lines of context before/after each match (default 0).
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    cmd = ["grep", "-n"]
    if context_lines > 0:
        cmd += [f"-C{context_lines}"]
    cmd += [pattern, str(p)]
    return _run(cmd, timeout=10)


@mcp.tool()
def diff_files(file_a: str, file_b: str) -> str:
    """
    Show unified diff between two files.

    Args:
        file_a: First file path (relative to project root).
        file_b: Second file path (relative to project root).
    """
    try:
        a = _safe_path(file_a)
        b = _safe_path(file_b)
    except ValueError as e:
        return f"ERROR: {e}"
    if not a.exists():
        return f"ERROR: file not found — '{file_a}'"
    if not b.exists():
        return f"ERROR: file not found — '{file_b}'"
    return _run(["diff", "-u", str(a), str(b)], timeout=10)


# ---------------------------------------------------------------------------
# Canonical nql project manager
# ---------------------------------------------------------------------------

def _nql_unavailable() -> dict[str, Any]:
    return _error_result(
        f"nql not found at '{CANONICAL_NQL}'",
        capability=CAP_BUILD,
    )


def _backend_options(backend: str, compiler_profile: bool = False) -> list[str]:
    if backend not in {"", "nasm", "canonical"}:
        raise ValueError("backend must be nasm or canonical")
    if not isinstance(compiler_profile, bool):
        raise ValueError("compiler_profile must be a boolean")
    if compiler_profile and backend == "nasm":
        raise ValueError("compiler_profile requires the canonical backend")
    options = ["--backend", backend] if backend else []
    if compiler_profile:
        options.append("--compiler-profile")
    return options


def _project_result(command: str, tail: list[str], backend: str,
                    compiler_profile: bool = False, *, timeout: int = 120,
                    capability: str = CAP_BUILD) -> dict[str, Any]:
    try:
        options = _backend_options(backend, compiler_profile)
    except ValueError as exc:
        return _error_result(str(exc), capability=capability)
    if not NQL.exists():
        return _nql_unavailable()
    return _run_result([str(NQL), command, *options, *tail], timeout=timeout,
                       capability=capability)


@mcp.tool()
def nql_init(project_name: str = "", backend: str = "") -> dict[str, Any]:
    """Create a project; optional backend selection is persisted, never a profile."""
    return _project_result("init", [project_name] if project_name else [], backend,
                           timeout=30, capability=CAP_WRITE)


@mcp.tool()
def nql_build(release: bool = False, target: str = "", backend: str = "",
              compiler_profile: bool = False) -> dict[str, Any]:
    """Build with nql's cache; omitted backend honors the project manifest."""
    tail = []
    if release:
        tail.append("--release")
    if target:
        tail += ["--target", target]
    return _project_result("build", tail, backend, compiler_profile)


@mcp.tool()
def nql_run(args: str = "", release: bool = False, backend: str = "",
            compiler_profile: bool = False) -> dict[str, Any]:
    """Run a project. Canonical runs recompile via nqlc --run, even after build."""
    tail = []
    if release:
        tail.append("--release")
    if args:
        try:
            tail += ["--"] + shlex.split(args)
        except ValueError as exc:
            return _error_result(f"invalid argument quoting: {exc}", capability=CAP_BUILD)
    return _project_result("run", tail, backend, compiler_profile)


@mcp.tool()
def nql_test(filter: str = "", backend: str = "",
             compiler_profile: bool = False) -> dict[str, Any]:
    """Build/run independent project tests; omitted backend honors the manifest."""
    return _project_result("test", [filter] if filter else [], backend, compiler_profile)


@mcp.tool()
def nql_check(backend: str = "", compiler_profile: bool = False) -> dict[str, Any]:
    """Check sources without publishing/running; canonical includes semantics."""
    return _project_result("check", [], backend, compiler_profile, timeout=60)


@mcp.tool()
def nql_clean(confirm: bool = False) -> dict[str, Any]:
    """Remove the nql build cache. Requires confirm=true."""
    if not confirm:
        return _error_result(
            "DESTRUCTIVE operation requires confirm=true",
            capability=CAP_DESTRUCTIVE,
        )
    if not NQL.exists():
        return _nql_unavailable()
    return _run_result(
        [str(NQL), "clean"], timeout=30, capability=CAP_DESTRUCTIVE
    )


@mcp.tool()
def nql_version() -> dict[str, Any]:
    """Show canonical nql and nqlc versions."""
    if not NQL.exists() or not NQLC.exists():
        return _error_result("nql or nqlc is unavailable", capability=CAP_READ_ONLY)
    manager = _run_result([str(NQL), "--version"], timeout=10, capability=CAP_READ_ONLY)
    compiler = _run_result([str(NQLC), "--version"], timeout=10, capability=CAP_READ_ONLY)
    return {
        "ok": manager["ok"] and compiler["ok"],
        "nql": manager,
        "nqlc": compiler,
        "canonical_manager": NQL == CANONICAL_NQL,
        "canonical_compiler": NQLC == CANONICAL_NQLC,
    }

# ---------------------------------------------------------------------------
# Build & test
# ---------------------------------------------------------------------------

@mcp.tool()
def build_compiler(target: str = "") -> str:
    """
    Build the Nolqu compiler via make.

    Args:
        target: Optional make target (e.g. "clean", "release").
    """
    cmd = ["make"] + ([target] if target else [])
    return _run(cmd, timeout=120)


@mcp.tool()
def run_tests(filter: str = "") -> str:
    """
    Run compiler tests via make test.

    Args:
        filter: Optional test-name substring filter (TEST_FILTER env var).
    """
    env = os.environ.copy()
    if filter:
        env["TEST_FILTER"] = filter
    cmd = ["make", "test"]
    return _run(cmd, timeout=900, env=env)


@mcp.tool()
def run_test_file(test_file: str) -> str:
    """
    Compile and run one canonical .nql source; legacy .nq remains accepted.

    Args:
        test_file: Path to a .nql or legacy .nq test file.
    """
    if not COMPILER.exists():
        return f"ERROR: compiler not found at '{COMPILER}'. Run build_compiler() first."
    try:
        src = _safe_path(test_file)
    except ValueError as e:
        return f"ERROR: {e}"
    if not src.exists():
        return f"ERROR: test file not found — '{test_file}'"
    out = src.with_suffix("")
    compile_result = _run([str(COMPILER), str(src), "-o", str(out)], timeout=30)
    if "exit_code: 0" not in compile_result:
        return f"Compile failed:\n{compile_result}"
    run_result = _run([str(out)], timeout=15)
    return f"=== COMPILE ===\n{compile_result}\n\n=== RUN ===\n{run_result}"


@mcp.tool()
def compare_output(program_a: str, program_b: str, args: str = "") -> str:
    """
    Run two programs with the same args and compare stdout.
    Useful to verify a .nql tool output matches a reference executable.

    Args:
        program_a: Path to first executable (relative to project root).
        program_b: Path to second executable (relative to project root).
        args:      Arguments to pass to both.
    """
    try:
        a = _safe_path(program_a)
        b = _safe_path(program_b)
    except ValueError as e:
        return f"ERROR: {e}"
    if not a.exists():
        return f"ERROR: not found — '{program_a}'"
    if not b.exists():
        return f"ERROR: not found — '{program_b}'"
    cmd_args = shlex.split(args) if args else []
    try:
        ra = subprocess.run([str(a)] + cmd_args, cwd=ROOT, text=True,
                            capture_output=True, timeout=15)
        rb = subprocess.run([str(b)] + cmd_args, cwd=ROOT, text=True,
                            capture_output=True, timeout=15)
    except subprocess.TimeoutExpired:
        return "ERROR: timed out"
    if ra.stdout == rb.stdout:
        return f"OK: output identik ({len(ra.stdout)} chars)"
    import difflib
    diff = list(difflib.unified_diff(
        ra.stdout.splitlines(keepends=True),
        rb.stdout.splitlines(keepends=True),
        fromfile=program_a, tofile=program_b,
    ))
    return f"DIFF (output berbeda):\n{''.join(diff)}"


# ---------------------------------------------------------------------------
# Compiler pipeline
# ---------------------------------------------------------------------------

def _compile_result(source_file: str, flags: str = "", output_file: str = "",
                    emit_asm: bool = False, backend: str = "",
                    compiler_profile: bool = False, *, compiler: pathlib.Path,
                    timeout: int = 60, require_extension: bool = False) -> dict[str, Any]:
    try:
        _backend_options(backend, compiler_profile)
        value_flags = {"-o", "--color", "--max-errors", "--error-format",
                       "--target", "--backend", "-j"}
        try:
            raw_tokens = shlex.split(flags)
        except ValueError as exc:
            raise ValueError(f"invalid flag quoting: {exc}") from exc
        # Match nqlc's one-argument-per-line response format before classifying
        # modes or validating paths. Hidden --check/-o/backend flags count too.
        tokens = []
        literal = False
        value_pending = False
        for token in raw_tokens:
            from_response = not literal and token.startswith("@") and len(token) > 1
            entries = (_safe_path(token[1:]).read_text(encoding="utf-8").split("\n")
                       if from_response else [token])
            for entry in entries:
                if from_response and (not entry or entry.startswith("#")):
                    continue
                if from_response and not literal and entry.startswith("@"):
                    raise ValueError("nested response files are not supported in MCP flags")
                tokens.append(entry)
                if value_pending:
                    value_pending = False
                elif entry == "--":
                    literal = True
                elif not literal and entry in value_flags:
                    value_pending = True
        src = _safe_path(source_file)
        if not src.is_file():
            raise ValueError(f"source file not found: {source_file}")
        if require_extension and src.suffix not in {".nql", ".nq"}:
            raise ValueError("source must use canonical .nql or legacy .nq extension")

        # Skip option values: an output literally named --run is not a run flag.
        modes = set()
        selected_backend = ""
        output = None
        index = 0
        separator = len(tokens)
        while index < len(tokens):
            token = tokens[index]
            if token == "--":
                separator = index
                break
            if token in value_flags:
                if index + 1 == len(tokens):
                    raise ValueError(f"flag {token} requires a value")
                value = tokens[index + 1]
                if token == "-o":
                    if output is not None or output_file:
                        raise ValueError("duplicate output selection")
                    if not value:
                        raise ValueError("output path must not be empty")
                    output = _safe_path(value)
                    tokens[index + 1] = str(output)
                elif token == "--backend":
                    if selected_backend or backend:
                        raise ValueError("duplicate backend selection")
                    _backend_options(value)
                    if not value:
                        raise ValueError("backend must be nasm or canonical")
                    selected_backend = value
                index += 2
                continue
            if token.startswith("--backend="):
                if selected_backend or backend:
                    raise ValueError("duplicate backend selection")
                selected_backend = token.partition("=")[2]
                if not selected_backend:
                    raise ValueError("backend must be nasm or canonical")
                _backend_options(selected_backend)
            modes.add(token)
            index += 1

        profile = compiler_profile or "--compiler-profile" in modes
        _backend_options(selected_backend or backend or "nasm", profile)
        options = _backend_options(backend, compiler_profile and "--compiler-profile" not in modes)
        if emit_asm:
            options.append("-S")
            modes.add("-S")
        stdout_mode = bool(modes & {"--check", "--emit-ir", "--dump-ir", "--dump-ast",
                                    "-M", "--emit-ccdb", "--help", "-h", "--version"})
        output_in_flags = output is not None
        default_output = False
        if output_file:
            output = _safe_path(output_file)
        elif output is None and not stdout_mode and "--run" not in modes:
            suffix = ".asm" if "-S" in modes else ".o" if "-c" in modes else ""
            directory = ROOT / ".nolqu-mcp" / "build"
            if directory.resolve() != directory:
                raise ValueError("default output directory must remain .nolqu-mcp/build")
            output = _safe_path(str(directory / (src.stem + suffix)))
            if output.parent != directory:
                raise ValueError("default output must remain inside .nolqu-mcp/build")
            protected = [src, compiler, NQL, NQLC, FORMAL_NOLQUL, FORMAL_NOLQULC,
                         ROOT / "install.sh", ROOT / "tools/nql_c0_driver.sh",
                         ROOT / "tools/nql_r0_adapter.sh"]
            protected.extend(path for path in (ROOT / "bootstrap").rglob("*") if path.is_file())
            if output.is_file() and any(path.is_file() and output.samefile(path) for path in protected):
                raise ValueError("default output aliases a protected source, tool or component")
            default_output = True
        if output is not None and not output_in_flags:
            options += ["-o", str(output)]
        before = output.stat() if output is not None and output.is_file() else None
    except (ValueError, OSError) as exc:
        return _error_result(str(exc), capability=CAP_BUILD)
    if not compiler.exists():
        return _error_result(f"compiler not found at '{compiler}'", capability=CAP_BUILD)
    if default_output:
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return _error_result(str(exc), capability=CAP_BUILD)
    with _defer_compile_audit() as audit:
        result = _run_result([str(compiler), *options, *tokens[:separator], str(src), *tokens[separator:]],
                             timeout=timeout, capability=CAP_BUILD)
        # The executor's result API stays untouched. Only a successful publication
        # can become an artifact; a preserved old output is not a new build.
        result["artifacts"] = []
        if result["ok"] and not stdout_mode and "--dry-run" not in modes and output is not None:
            try:
                after = output.stat() if output.is_file() else None
                if after is not None and (before is None or
                        (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) !=
                        (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)):
                    result["artifacts"] = [str(output.relative_to(ROOT))]
            except OSError:
                pass
        audit["artifacts"] = result["artifacts"]
    return result


@mcp.tool()
def compile_nql(
    source_file: str,
    flags: str = "",
    output_file: str = "",
    emit_asm: bool = False,
    backend: str = "",
    compiler_profile: bool = False,
) -> dict[str, Any]:
    """
    Compile a canonical .nql source with nqlc. A .nq source is accepted only
    as a legacy compatibility input. Ordinary compilation supplies an output
    and never implicitly runs. Explicit --run remains supported. Backend is
    nasm by default; canonical selects the experimental C0.32 subset.
    """
    return _compile_result(source_file, flags, output_file, emit_asm, backend,
                           compiler_profile, compiler=NQLC, require_extension=True)


@mcp.tool()
def compile_file(source_file: str, flags: str = "", emit_asm: bool = False) -> str:
    """
    Legacy generic MCP method: compile a .nq file using canonical nqlc.

    Args:
        source_file: Path to .nq file (relative to project root).
        flags:       Extra compiler flags (e.g. "-O1 -g").
        emit_asm:    If True, pass -S to emit assembly.
    """
    return _format_result(_compile_result(source_file, flags, emit_asm=emit_asm,
                                          compiler=COMPILER, timeout=30))


@mcp.tool()
def run_pipeline_step(source_file: str, step: str, output_file: str = "") -> str:
    """
    Run a single step of the NolQu-L compilation pipeline.

    step options:
      "parse"   -> nqlc --check (check without publication or execution)
      "ir"      -> nqlc --emit-ir
      "asm"     -> nqlc -S
      "compile" -> nqlc -c (compile, no link)
      "full"    -> nqlc with explicit output (emit executable, never run)

    Args:
        source_file: Path to canonical .nql or legacy .nq source.
        step:        Pipeline step.
        output_file: Output file path (optional).
    """
    step = step.lower().strip()
    steps = {"parse": "--check", "ir": "--emit-ir", "asm": "-S", "compile": "-c", "full": ""}
    if step not in steps:
        return f"ERROR: step tidak dikenal — '{step}'. Pilih: parse, ir, asm, compile, full"
    return _format_result(_compile_result(source_file, steps[step], output_file,
                                          compiler=COMPILER, timeout=30))


@mcp.tool()
def assemble_nasm(asm_file: str, output_file: str = "out.o", extra_flags: str = "") -> str:
    """
    Assemble a NASM file into an ELF64 object file.

    Args:
        asm_file:    Path to .asm file (relative to project root).
        output_file: Output .o file path.
        extra_flags: Additional NASM flags.
    """
    try:
        asm = _safe_path(asm_file)
        out = _safe_path(output_file)
    except ValueError as e:
        return f"ERROR: {e}"
    if not asm.exists():
        return f"ERROR: ASM file not found — '{asm_file}'"
    cmd = ["nasm", "-f", "elf64"]
    if extra_flags:
        cmd.extend(shlex.split(extra_flags))
    cmd += [str(asm), "-o", str(out)]
    return _run(cmd, timeout=30)


@mcp.tool()
def link_objects(
    object_files: list[str],
    output_file: str = "a.out",
    extra_flags: str = "",
) -> str:
    """
    Link ELF64 object files into an executable using ld. No libc.

    Args:
        object_files: List of .o paths (relative to project root).
        output_file:  Output executable path.
        extra_flags:  Extra ld flags.
    """
    try:
        objs = [_safe_path(f) for f in object_files]
        out  = _safe_path(output_file)
    except ValueError as e:
        return f"ERROR: {e}"
    missing = [str(o) for o in objs if not o.exists()]
    if missing:
        return f"ERROR: object file(s) not found — {missing}"
    cmd = ["ld", "-o", str(out)]
    if extra_flags:
        cmd.extend(shlex.split(extra_flags))
    cmd.extend(str(o) for o in objs)
    return _run(cmd, timeout=30)


@mcp.tool()
def assemble_and_link(
    asm_file: str,
    output_file: str = "a.out",
    asm_flags: str = "",
    ld_flags: str = "",
) -> str:
    """
    Assemble a NASM file then immediately link it.

    Args:
        asm_file:    Path to .asm file (relative to project root).
        output_file: Final executable path.
        asm_flags:   Extra NASM flags.
        ld_flags:    Extra ld flags.
    """
    obj_file = str(pathlib.Path(asm_file).with_suffix(".o"))
    asm_result = assemble_nasm(asm_file, obj_file, asm_flags)
    if "exit_code: 0" not in asm_result:
        return f"Assembly failed:\n{asm_result}"
    link_result = link_objects([obj_file], output_file, ld_flags)
    return f"=== ASSEMBLE ===\n{asm_result}\n\n=== LINK ===\n{link_result}"


# ---------------------------------------------------------------------------
# Run & inspect
# ---------------------------------------------------------------------------

@mcp.tool()
def run_program(program_path: str = "a.out", args: str = "") -> str:
    """
    Run a compiled executable.

    Args:
        program_path: Path to executable (relative to project root).
        args:         Command-line arguments, space-separated.
    """
    try:
        prog = _safe_path(program_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not prog.exists():
        return f"ERROR: executable not found — '{program_path}'"
    if not os.access(prog, os.X_OK):
        return f"ERROR: '{program_path}' is not executable. Run chmod_file first."
    cmd = [str(prog)] + (shlex.split(args) if args else [])
    return _run(cmd, timeout=15)


@mcp.tool()
def strace_program(program_path: str, args: str = "", syscall_filter: str = "") -> str:
    """
    Trace syscalls of a program using strace.
    Useful for debugging Nolqu programs since they use raw syscalls.

    Args:
        program_path:   Path to executable (relative to project root).
        args:           Arguments to pass to the program.
        syscall_filter: Comma-separated syscall names to trace only
                        (e.g. "read,write,open"). Traces all if empty.
    """
    try:
        prog = _safe_path(program_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not prog.exists():
        return f"ERROR: executable not found — '{program_path}'"
    cmd = ["strace"]
    if syscall_filter:
        cmd += ["-e", f"trace={syscall_filter}"]
    cmd.append(str(prog))
    if args:
        cmd.extend(shlex.split(args))
    return _run(cmd, timeout=15)


@mcp.tool()
def disassemble(binary_path: str, symbol: str = "") -> str:
    """
    Disassemble a binary or .o file using objdump (Intel syntax).

    Args:
        binary_path: Path to binary or .o (relative to project root).
        symbol:      If given, disassemble only that symbol.
    """
    try:
        p = _safe_path(binary_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{binary_path}'"
    cmd = ["objdump", "-d", "-M", "intel", "--no-show-raw-insn"]
    if symbol:
        cmd += ["--disassemble=" + symbol]
    cmd.append(str(p))
    return _run(cmd, timeout=15)


@mcp.tool()
def show_symbols(binary_path: str) -> str:
    """
    List all symbols using nm.

    Args:
        binary_path: Path relative to project root.
    """
    try:
        p = _safe_path(binary_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{binary_path}'"
    return _run(["nm", "--numeric-sort", str(p)], timeout=10)


@mcp.tool()
def readelf(binary_path: str, flags: str = "-a") -> str:
    """
    Inspect ELF headers and sections using readelf.

    Args:
        binary_path: Path to ELF binary or .o (relative to project root).
        flags:       readelf flags (default "-a"). Common: "-h", "-S", "-l".
    """
    try:
        p = _safe_path(binary_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{binary_path}'"
    cmd = ["readelf"] + shlex.split(flags) + [str(p)]
    return _run(cmd, timeout=15)


@mcp.tool()
def hexdump(file_path: str, length: int = 256) -> str:
    """
    Show hex dump of a file (first N bytes, max 4096).

    Args:
        file_path: Path relative to project root.
        length:    Number of bytes to dump (default 256, max 4096).
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    return _run(["xxd", "-l", str(min(length, 4096)), str(p)], timeout=10)


@mcp.tool()
def section_sizes(binary_path: str) -> str:
    """
    Show ELF section sizes (.text, .data, .bss, etc.) using size.

    Args:
        binary_path: Path to ELF binary or .o (relative to project root).
    """
    try:
        p = _safe_path(binary_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{binary_path}'"
    return _run(["size", str(p)], timeout=10)


@mcp.tool()
def check_stack_balance(asm_file: str) -> str:
    """
    Heuristic: scan .asm file and report push/pop imbalances per function.
    Also detects sub/add rsp patterns.

    Args:
        asm_file: Path to .asm file (relative to project root).
    """
    try:
        p = _safe_path(asm_file)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{asm_file}'"
    lines = p.read_text(errors="replace").splitlines()
    results: list[str] = []
    current_fn = "(global)"
    pushes = 0
    pops   = 0
    for raw in lines:
        line = raw.strip().lower()
        if raw.rstrip().endswith(":") and not raw.lstrip().startswith("."):
            if pushes != pops:
                results.append(
                    f"  ⚠ IMBALANCE in '{current_fn}': "
                    f"{pushes} push(es), {pops} pop(s)"
                )
            current_fn = raw.strip().rstrip(":")
            pushes = 0
            pops   = 0
        elif line.startswith("push"):
            pushes += 1
        elif line.startswith("pop"):
            pops += 1
        elif line.startswith("sub rsp") or line.startswith("sub  rsp"):
            pushes += 1
        elif line.startswith("add rsp") or line.startswith("add  rsp"):
            pops += 1
    if pushes != pops:
        results.append(
            f"  ⚠ IMBALANCE in '{current_fn}': "
            f"{pushes} push(es), {pops} pop(s)"
        )
    if not results:
        return "✓ No obvious push/pop imbalances found."
    return "Stack balance check:\n" + "\n".join(results)


@mcp.tool()
def read_ir(ir_file: str, max_lines: int = 200) -> str:
    """
    Read a NolQu-L IR dump (.nqlir; legacy .nqir is accepted).

    Args:
        ir_file:   Path to .nqlir or legacy .nqir.
        max_lines: Maximum lines to return (default 200).
    """
    return read_file(ir_file, max_lines=max_lines)


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------

@mcp.tool()
def git_status() -> str:
    """Show git status — staged, unstaged, untracked files."""
    return _run(["git", "status", "--short"], timeout=10)


@mcp.tool()
def git_diff(file_path: str = "") -> str:
    """
    Show git diff — unstaged changes.

    Args:
        file_path: Limit to this file. Shows all if empty.
    """
    cmd = ["git", "diff"]
    if file_path:
        try:
            p = _safe_path(file_path)
            cmd.append(str(p))
        except ValueError as e:
            return f"ERROR: {e}"
    return _run(cmd, timeout=10)


@mcp.tool()
def git_log(max_entries: int = 10) -> str:
    """
    Show recent git commit history.

    Args:
        max_entries: Commits to show (default 10, max 50).
    """
    return _run(
        ["git", "log", f"-{min(max_entries, 50)}", "--oneline", "--decorate"],
        timeout=10,
    )


# ---------------------------------------------------------------------------
# Git extended (prioritas sedang)
# ---------------------------------------------------------------------------

@mcp.tool()
def git_add(file_path: str = ".") -> str:
    """
    Stage file(s) for commit.

    Args:
        file_path: Path relative to project root, or "." for all changes.
    """
    if file_path == ".":
        cmd = ["git", "add", "."]
    else:
        try:
            p = _safe_path(file_path)
            cmd = ["git", "add", str(p)]
        except ValueError as e:
            return f"ERROR: {e}"
    return _run(cmd, timeout=10)


@mcp.tool()
def git_commit(message: str) -> str:
    """
    Commit staged changes with a message.

    Args:
        message: Commit message.
    """
    if not message.strip():
        return "ERROR: commit message tidak boleh kosong"
    return _run(["git", "commit", "-m", message], timeout=15)


@mcp.tool()
def git_restore(file_path: str, confirm: bool = False) -> str:
    """
    Discard unstaged changes in a file (restore to last commit).

    Args:
        file_path: Path relative to project root.
        confirm: Must be true because local changes are discarded.
    """
    if not confirm:
        return "ERROR: DESTRUCTIVE operation requires confirm=true"
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    return _run(["git", "restore", str(p)], timeout=10)


@mcp.tool()
def git_stash(
    action: str = "push",
    message: str = "",
    confirm: bool = False,
) -> str:
    """
    Stash or restore uncommitted changes.

    Args:
        action:  "push" to stash, "pop" to restore, "list" to show stashes.
        message: Optional stash message (only for push).
    """
    if action != "list" and not confirm:
        return "ERROR: DESTRUCTIVE operation requires confirm=true"
    if action == "push":
        cmd = ["git", "stash", "push"]
        if message:
            cmd += ["-m", message]
    elif action == "pop":
        cmd = ["git", "stash", "pop"]
    elif action == "list":
        cmd = ["git", "stash", "list"]
    else:
        return f"ERROR: action tidak dikenal — '{action}'. Pilih: push, pop, list"
    return _run(cmd, timeout=10)


# ---------------------------------------------------------------------------
# Directory operations (prioritas sedang)
# ---------------------------------------------------------------------------

@mcp.tool()
def tree(directory: str = "", max_depth: int = 3) -> str:
    """
    Show directory tree structure.
    Falls back to pure Python if tree binary is not installed.

    Args:
        directory: Subdirectory to show (default: project root).
        max_depth: Maximum depth (default 3, max 5).
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"
    if not target.exists():
        return f"ERROR: direktori tidak ditemukan — '{directory}'"
    max_depth = min(max_depth, 5)
    result = _run(["tree", "-L", str(max_depth), str(target)], timeout=10)
    if "command not found" in result:
        return _tree_fallback(target, max_depth)
    return result


def _tree_fallback(root: pathlib.Path, max_depth: int, _depth: int = 0, _prefix: str = "") -> str:
    """Pure Python tree fallback if tree binary is not available."""
    if _depth > max_depth:
        return ""
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda e: (e.is_file(), e.name))
    except PermissionError:
        return _prefix + "[permission denied]"
    for i, entry in enumerate(entries):
        is_last   = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(_prefix + connector + entry.name + ("/" if entry.is_dir() else ""))
        if entry.is_dir() and _depth < max_depth:
            extension = "    " if is_last else "│   "
            subtree = _tree_fallback(entry, max_depth, _depth + 1, _prefix + extension)
            if subtree:
                lines.append(subtree)
    return "\n".join(lines)


@mcp.tool()
def copy_dir(src_path: str, dst_path: str) -> str:
    """
    Copy a directory recursively inside the project root.

    Args:
        src_path: Source directory path (relative to project root).
        dst_path: Destination path (relative to project root).
    """
    import shutil
    try:
        src = _safe_path(src_path)
        dst = _safe_path(dst_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not src.exists():
        return f"ERROR: source not found — '{src_path}'"
    if not src.is_dir():
        return f"ERROR: '{src_path}' bukan direktori. Gunakan copy_file."
    if dst.exists():
        return f"ERROR: destination already exists — '{dst_path}'"
    try:
        shutil.copytree(str(src), str(dst))
        return f"OK: copied dir {src_path} -> {dst_path}"
    except PermissionError:
        return "ERROR: permission denied"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def touch_file(file_path: str) -> str:
    """
    Create an empty file or update its timestamp (like Unix touch).

    Args:
        file_path: Path relative to project root.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        existed = p.exists()
        p.touch()
        return f"OK: {'updated' if existed else 'created'} -> {file_path}"
    except PermissionError:
        return f"ERROR: permission denied — '{file_path}'"
    except OSError as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# Environment & system info (prioritas sedang)
# ---------------------------------------------------------------------------

@mcp.tool()
def env_info() -> str:
    """
    Show environment variables relevant to NolQu-L development.
    """
    keys = [
        "NOLQU_ROOT", "PATH", "TMPDIR", "HOME",
        "NOLQUC_COLOR", "NOLQUC_MAX_ERRORS",
        "NO_COLOR", "SOURCE_DATE_EPOCH", "NQ_HOME",
        "CC", "LD", "NASM",
    ]
    lines = ["=== Environment (NolQu-L relevant) ==="]
    for k in keys:
        v = os.environ.get(k, "(not set)")
        lines.append(f"  {k:<22} = {v}")
    lines.append("")
    lines.append(f"  (resolved ROOT: {ROOT})")
    return "\n".join(lines)


@mcp.tool()
def which_tool(name: str) -> str:
    """
    Check if an external tool is available in PATH.

    Args:
        name: Tool name (e.g. "nasm", "ld", "strace", "python3").
    """
    return _run(["which", name], timeout=5)


# ---------------------------------------------------------------------------
# Test & regression (prioritas sedang)
# ---------------------------------------------------------------------------

@mcp.tool()
def run_regression(suite: str = "") -> str:
    """
    Run regression tests from tests/regression.sh or via make regression.

    Args:
        suite: Optional test suite name. Runs all if empty.
    """
    regression_sh = ROOT / "tests" / "regression.sh"
    if regression_sh.exists():
        cmd = [str(regression_sh)]
        if suite:
            cmd.append(suite)
        return _run(cmd, timeout=120)
    cmd = ["make", "regression"]
    if suite:
        cmd += [f"SUITE={suite}"]
    return _run(cmd, timeout=120)


@mcp.tool()
def check_ir_valid(ir_file: str) -> str:
    """
    Basic validation of a NolQu-L IR dump (.nqlir or legacy .nqir).

    Args:
        ir_file: Path to .nqlir or legacy .nqir.
    """
    try:
        p = _safe_path(ir_file)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{ir_file}'"
    try:
        content = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"ERROR: '{ir_file}' bukan file UTF-8 yang valid"
    if not content.strip():
        return f"ERROR: '{ir_file}' kosong"
    lines  = content.splitlines()
    issues = []
    blank_streak = 0
    for i, line in enumerate(lines, 1):
        if not line.strip():
            blank_streak += 1
            if blank_streak > 3:
                issues.append(f"  line {i}: banyak baris kosong berturut-turut")
                break
        else:
            blank_streak = 0
    status  = "OK" if not issues else "WARNINGS"
    summary = "\n".join([
        f"=== {ir_file} ===",
        f"  lines:  {len(lines)}",
        f"  bytes:  {len(content.encode())}",
        f"  status: {status}",
    ])
    if issues:
        summary += "\n" + "\n".join(issues)
    return summary


# ---------------------------------------------------------------------------
# Git lanjutan (prioritas rendah)
# ---------------------------------------------------------------------------

@mcp.tool()
def git_branch(action: str = "list", name: str = "", confirm: bool = False) -> str:
    """
    Manage git branches.

    Args:
        action: "list" show all branches, "create" create new branch,
                "switch" switch to branch, "delete" delete branch.
        name:   Branch name (required for create/switch/delete).
    """
    if action == "delete" and not confirm:
        return "ERROR: DESTRUCTIVE operation requires confirm=true"
    if action == "list":
        return _run(["git", "branch", "-a"], timeout=10)
    elif action == "create":
        if not name:
            return "ERROR: name diperlukan untuk create"
        return _run(["git", "checkout", "-b", name], timeout=10)
    elif action == "switch":
        if not name:
            return "ERROR: name diperlukan untuk switch"
        return _run(["git", "checkout", name], timeout=10)
    elif action == "delete":
        if not name:
            return "ERROR: name diperlukan untuk delete"
        return _run(["git", "branch", "-d", name], timeout=10)
    else:
        return f"ERROR: action tidak dikenal — '{action}'. Pilih: list, create, switch, delete"


@mcp.tool()
def git_pull(
    remote: str = "origin",
    branch: str = "",
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Pull latest changes from remote.

    Args:
        remote: Remote name (default: origin).
        branch: Branch name (default: current branch).
        confirm: Explicit remote-operation confirmation.
    """
    if not confirm:
        return _error_result("REMOTE operation requires confirm=true", capability=CAP_REMOTE)
    if os.environ.get("NOLQU_MCP_ALLOW_REMOTE") != "1":
        return _error_result(
            "REMOTE operations are disabled; set NOLQU_MCP_ALLOW_REMOTE=1",
            capability=CAP_REMOTE,
        )
    cmd = ["git", "pull", remote]
    if branch:
        cmd.append(branch)
    return _run_result(cmd, timeout=30, capability=CAP_REMOTE)


@mcp.tool()
def git_push(
    remote: str = "origin",
    branch: str = "",
    force: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Push commits to remote.

    Args:
        remote: Remote name (default: origin).
        branch: Branch name (default: current branch).
        force:  Force-with-lease push (default: False).
        confirm: Explicit remote-operation confirmation.
    """
    if not confirm:
        return _error_result("REMOTE operation requires confirm=true", capability=CAP_REMOTE)
    if os.environ.get("NOLQU_MCP_ALLOW_REMOTE") != "1":
        return _error_result(
            "REMOTE operations are disabled; set NOLQU_MCP_ALLOW_REMOTE=1",
            capability=CAP_REMOTE,
        )
    cmd = ["git", "push", remote]
    if branch:
        cmd.append(branch)
    if force:
        cmd.append("--force-with-lease")
    return _run_result(cmd, timeout=30, capability=CAP_REMOTE)


# ---------------------------------------------------------------------------
# File utilities (prioritas rendah)
# ---------------------------------------------------------------------------

@mcp.tool()
def symlink(target: str, link_path: str) -> str:
    """
    Create a symbolic link inside the project root.
    Useful for controlled local compatibility aliases.

    Args:
        target:    Path the symlink points to (relative to project root).
        link_path: Path of the new symlink (relative to project root).
    """
    try:
        tgt  = _safe_path(target)
        link = _safe_path(link_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if link.exists() or link.is_symlink():
        return f"ERROR: '{link_path}' sudah ada"
    try:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(tgt)
        return f"OK: symlink {link_path} -> {target}"
    except PermissionError:
        return "ERROR: permission denied"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def disk_usage(directory: str = "", max_depth: int = 1) -> str:
    """
    Show disk usage of project or subdirectory.

    Args:
        directory: Subdirectory to measure (default: project root).
        max_depth: Depth for du -d flag (default 1).
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"
    if not target.exists():
        return f"ERROR: not found — '{directory}'"
    return _run(["du", "-sh", f"--max-depth={max_depth}", str(target)], timeout=15)


@mcp.tool()
def cat_files(file_paths: list[str]) -> str:
    """
    Concatenate and display multiple files in order.

    Args:
        file_paths: List of file paths (relative to project root).
    """
    parts = []
    for fp in file_paths:
        try:
            p = _safe_path(fp)
        except ValueError as e:
            parts.append(f"ERROR: {e}")
            continue
        if not p.exists():
            parts.append(f"ERROR: file not found — '{fp}'")
            continue
        if not p.is_file():
            parts.append(f"ERROR: not a file — '{fp}'")
            continue
        if p.stat().st_size > MAX_READ_FILE_BYTES:
            parts.append(f"ERROR: file too large — '{fp}'")
            continue
        content = p.read_text(errors="replace")
        parts.append(f"=== {fp} ===\n{content}")
    rendered, _ = _truncate_output("\n\n".join(parts), MAX_TOOL_OUTPUT_BYTES)
    return rendered


@mcp.tool()
def lines_of_code(directory: str = "", file_glob: str = "*.nql") -> str:
    """
    Count lines of code in source files.

    Args:
        directory: Subdirectory to count in (default: project root).
        file_glob: File pattern to count (default canonical: "*.nql").
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"
    result = _run(
        ["find", str(target), "-name", file_glob, "-type", "f",
         "-exec", "wc", "-l", "{}", "+"],
        timeout=15,
    )
    return result


# ---------------------------------------------------------------------------
# Binary tools lanjutan (prioritas rendah)
# ---------------------------------------------------------------------------

@mcp.tool()
def strip_binary(binary_path: str, output_path: str = "") -> str:
    """
    Strip debug symbols from a binary to reduce size.

    Args:
        binary_path: Path to binary (relative to project root).
        output_path: Output path (default: strip in-place).
    """
    try:
        p = _safe_path(binary_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{binary_path}'"
    cmd = ["strip"]
    if output_path:
        try:
            out = _safe_path(output_path)
            cmd += ["-o", str(out)]
        except ValueError as e:
            return f"ERROR: {e}"
    cmd.append(str(p))
    return _run(cmd, timeout=15)


@mcp.tool()
def check_undefined_symbols(binary_path: str) -> str:
    """
    List undefined symbols in a binary or object file.
    Helps catch missing symbols before linking.

    Args:
        binary_path: Path to binary or .o (relative to project root).
    """
    try:
        p = _safe_path(binary_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{binary_path}'"
    return _run(["nm", "-u", "--numeric-sort", str(p)], timeout=10)


@mcp.tool()
def memory_check(program_path: str, args: str = "") -> str:
    """
    Run a program under valgrind for memory error detection.
    Requires valgrind to be installed.

    Args:
        program_path: Path to executable (relative to project root).
        args:         Arguments to pass to the program.
    """
    try:
        prog = _safe_path(program_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not prog.exists():
        return f"ERROR: executable not found — '{program_path}'"
    cmd = [
        "valgrind",
        "--error-exitcode=1",
        "--leak-check=full",
        "--show-leak-kinds=all",
        str(prog),
    ]
    if args:
        cmd.extend(shlex.split(args))
    return _run(cmd, timeout=60)


@mcp.tool()
def profile_program(program_path: str, args: str = "") -> str:
    """
    Profile a program using perf stat (basic CPU counters).
    Requires perf to be installed.

    Args:
        program_path: Path to executable (relative to project root).
        args:         Arguments to pass to the program.
    """
    try:
        prog = _safe_path(program_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not prog.exists():
        return f"ERROR: executable not found — '{program_path}'"
    cmd = ["perf", "stat", str(prog)]
    if args:
        cmd.extend(shlex.split(args))
    return _run(cmd, timeout=60)


# ---------------------------------------------------------------------------
# Experimental nql commands
# ---------------------------------------------------------------------------

def _experimental_nql(command: str, args: list[str] | None = None) -> dict[str, Any]:
    if not NQL.exists():
        return _nql_unavailable()
    result = _run_result(
        [str(NQL), command] + (args or []),
        timeout=60,
        capability=CAP_BUILD,
    )
    result["stability"] = "experimental"
    return result


@mcp.tool()
def nql_fmt() -> dict[str, Any]:
    """Experimental: format canonical .nql project sources."""
    return _experimental_nql("fmt")


@mcp.tool()
def nql_lint() -> dict[str, Any]:
    """Experimental: lint canonical .nql project sources."""
    return _experimental_nql("lint")


@mcp.tool()
def nql_doc(output_dir: str = "docs/") -> dict[str, Any]:
    """Experimental: generate NolQu-L project documentation."""
    return _experimental_nql("doc", ["--output", output_dir])


@mcp.tool()
def generate_ccdb() -> str:
    """
    Generate compile_commands.json for LSP/IDE integration.
    Records canonical .nql files, falling back to legacy .nq sources only when
    the project has not migrated yet.

    compile_commands.json is written to the project root.
    """
    if not COMPILER.exists():
        return f"ERROR: compiler not found at '{COMPILER}'. Run build_compiler() first."
    src_dir = ROOT / "src"
    if not src_dir.exists():
        return "ERROR: direktori src/ tidak ditemukan"
    source_files = sorted(src_dir.glob("**/*.nql"))
    legacy_mode = False
    if not source_files:
        source_files = sorted(src_dir.glob("**/*.nq"))
        legacy_mode = bool(source_files)
    if not source_files:
        return "ERROR: no .nql source files found in src/"
    entries = []
    for f in source_files:
        entries.append({
            "directory": str(ROOT),
            "command":   shlex.join([str(NQLC), str(f)]),
            "file":      str(f),
        })
    out = ROOT / "compile_commands.json"
    _atomic_write_text(out, json.dumps(entries, indent=2) + "\n")
    suffix = " using legacy .nq sources" if legacy_mode else ""
    return f"OK: generated compile_commands.json ({len(entries)} entries){suffix}"


@mcp.tool()
def benchmark(test_file: str = "", iterations: int = 5) -> str:
    """
    Run a canonical .nql file multiple times and report average execution time.

    Args:
        test_file:  Path to .nql file (legacy .nq is accepted).
        iterations: Number of runs to average (default 5, max 20).
    """
    if not COMPILER.exists():
        return f"ERROR: compiler not found at '{COMPILER}'. Run build_compiler() first."

    if not test_file:
        test_file = (
            "tests/benchmark.nql"
            if (ROOT / "tests/benchmark.nql").is_file()
            else "tests/benchmark.nq"
        )

    try:
        src = _safe_path(test_file)
    except ValueError as e:
        return f"ERROR: {e}"
    if not src.exists():
        return f"ERROR: file not found — '{test_file}'"

    iterations = min(max(1, iterations), 20)

    temp_root = ROOT / ".nolqu-mcp" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="benchmark-", dir=temp_root) as temporary:
        out = pathlib.Path(temporary) / "program"
        compile_result = _run_result(
            [str(NQLC), str(src), "-o", str(out)],
            timeout=60,
            capability=CAP_BUILD,
        )
        if not compile_result["ok"]:
            return f"Compile failed:\n{_format_result(compile_result)}"

        times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            subprocess.run([str(out)], cwd=ROOT, capture_output=True, timeout=15)
            times.append(time.perf_counter() - t0)

    avg  = sum(times) / len(times)
    mn   = min(times)
    mx   = max(times)
    return "\n".join([
        f"=== benchmark: {test_file} ({iterations} runs) ===",
        f"  avg:  {avg*1000:.2f}ms",
        f"  min:  {mn*1000:.2f}ms",
        f"  max:  {mx*1000:.2f}ms",
    ])


# ---------------------------------------------------------------------------
# File ops lanjutan
# ---------------------------------------------------------------------------

@mcp.tool()
def backup_file(file_path: str) -> str:
    """
    Create a .bak backup of a file before editing.
    Safe pattern: backup_file → edit → verify → delete backup if OK.

    Args:
        file_path: Path relative to project root.
    """
    import shutil
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    bak = pathlib.Path(str(p) + ".bak")
    try:
        shutil.copy2(str(p), str(bak))
        return f"OK: backup created → {bak.relative_to(ROOT)}"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def replace_lines(
    file_path: str,
    start_line: int,
    end_line: int,
    new_content: str,
    expected_sha256: str = "",
) -> str:
    """
    Replace a range of lines in a file with new content.
    Lines are 1-indexed and inclusive.

    Args:
        file_path:   Path relative to project root.
        start_line:  First line to replace (1-indexed).
        end_line:    Last line to replace (1-indexed, inclusive).
        new_content: Replacement content (can be multiple lines).
        expected_sha256: Optional hash observed before editing.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    total = len(lines)
    if start_line < 1 or end_line < start_line or start_line > total:
        return f"ERROR: range {start_line}-{end_line} tidak valid (total: {total} baris)"
    end_line = min(end_line, total)
    replacement = new_content if new_content.endswith("\n") else new_content + "\n"
    new_lines = lines[:start_line - 1] + [replacement] + lines[end_line:]
    try:
        _atomic_write_text(
            p, "".join(new_lines), expected_sha256=expected_sha256
        )
        return f"OK: replaced lines {start_line}-{end_line} → {file_path}"
    except RuntimeError as e:
        return f"ERROR: {e}"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def insert_lines(
    file_path: str,
    after_line: int,
    content: str,
    expected_sha256: str = "",
) -> str:
    """
    Insert content after a specific line number.
    Use after_line=0 to insert at the beginning of the file.

    Args:
        file_path:  Path relative to project root.
        after_line: Insert after this line (0 = before line 1).
        content:    Content to insert.
        expected_sha256: Optional hash observed before editing.
    """
    try:
        p = _safe_path(file_path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not p.exists():
        return f"ERROR: file not found — '{file_path}'"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    total = len(lines)
    if after_line < 0 or after_line > total:
        return f"ERROR: after_line {after_line} tidak valid (total: {total} baris)"
    insert = content if content.endswith("\n") else content + "\n"
    new_lines = lines[:after_line] + [insert] + lines[after_line:]
    try:
        _atomic_write_text(
            p, "".join(new_lines), expected_sha256=expected_sha256
        )
        return f"OK: inserted after line {after_line} → {file_path}"
    except RuntimeError as e:
        return f"ERROR: {e}"
    except OSError as e:
        return f"ERROR: {e}"


@mcp.tool()
def exec_with_input(
    command: str,
    stdin_input: str,
    timeout: int = 30,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Run a shell command with stdin input provided as a string.
    Useful for piping data to a program without creating temp files.

    Args:
        command:     Shell command to run.
        stdin_input: String to pass as stdin.
        timeout:     Max seconds to wait (default 30).
        confirm:     Explicit UNSAFE_SHELL acknowledgement.
    """
    if not confirm:
        return _error_result(
            "UNSAFE_SHELL requires confirm=true", capability=CAP_UNSAFE_SHELL
        )
    if os.environ.get("NOLQU_MCP_ALLOW_UNSAFE_SHELL") != "1":
        return _error_result(
            "UNSAFE_SHELL is disabled; set NOLQU_MCP_ALLOW_UNSAFE_SHELL=1",
            capability=CAP_UNSAFE_SHELL,
        )
    for blocked in _SHELL_BLOCKLIST:
        if blocked in command:
            return _error_result(
                f"command blocked by secondary guard: {blocked}",
                capability=CAP_UNSAFE_SHELL,
            )
    return _run_result(
        ["sh", "-c", command],
        timeout=timeout,
        stdin=stdin_input,
        capability=CAP_UNSAFE_SHELL,
    )


# ---------------------------------------------------------------------------
# Project health & build
# ---------------------------------------------------------------------------

@mcp.tool()
def check_dependencies() -> str:
    """
    Verify all required build tools are installed and available in PATH.
    Checks: nasm, ld, make, git, python3, objdump, nm, readelf, xxd, size.
    """
    required = {
        "nasm":    "assembler — butuh untuk compile .asm",
        "ld":      "linker — butuh untuk link object files",
        "make":    "build tool — butuh untuk build project",
        "git":     "version control",
        "python3": "butuh untuk Python tools (sebelum self-hosting selesai)",
        "objdump": "disassembler",
        "nm":      "symbol listing",
        "readelf": "ELF inspector",
        "xxd":     "hex dump",
        "size":    "ELF section sizes",
    }
    optional = {
        "strace":   "syscall tracer",
        "valgrind": "memory checker",
        "perf":     "profiler",
        "tree":     "directory tree display",
        "llvm-as":  "LLVM assembler (untuk LLVM IR path)",
        "clang":    "LLVM compiler (untuk LLVM IR path)",
    }
    lines = ["=== Dependency Check ===\n", "Required:"]
    all_ok = True
    for tool, desc in required.items():
        result = subprocess.run(["which", tool], capture_output=True, text=True)
        ok = result.returncode == 0
        if not ok:
            all_ok = False
        status = f"✓  {result.stdout.strip()}" if ok else "✗  NOT FOUND"
        lines.append(f"  {tool:<12} {status:<30} {desc}")
    lines.append("\nOptional:")
    for tool, desc in optional.items():
        result = subprocess.run(["which", tool], capture_output=True, text=True)
        ok = result.returncode == 0
        status = f"✓  {result.stdout.strip()}" if ok else "-  not installed"
        lines.append(f"  {tool:<12} {status:<30} {desc}")
    lines.append("")
    lines.append("✓ All required dependencies found." if all_ok
                 else "✗ Some required dependencies missing — build will fail.")
    return "\n".join(lines)


@mcp.tool()
def make_targets() -> str:
    """
    List all available targets in the project Makefile.
    """
    makefile = ROOT / "Makefile"
    if not makefile.exists():
        return "ERROR: Makefile tidak ditemukan di root project"
    return _run(["make", "-qp"], timeout=10)


@mcp.tool()
def clean_rebuild(target: str = "", confirm: bool = False) -> str:
    """
    Clean build artifacts then rebuild from scratch.
    Equivalent to: make clean && make [target].

    Args:
        target: Optional make target (default: default target).
        confirm: Must be true because existing artifacts are deleted.
    """
    if not confirm:
        return "ERROR: DESTRUCTIVE operation requires confirm=true"
    clean = _run(["make", "clean"], timeout=30)
    if "exit_code: 0" not in clean:
        return f"Clean failed:\n{clean}"
    build_cmd = ["make"] + ([target] if target else [])
    build = _run(build_cmd, timeout=120)
    return f"=== CLEAN ===\n{clean}\n\n=== BUILD ===\n{build}"


@mcp.tool()
def project_status() -> dict[str, Any]:
    """Return a structured canonical NolQu-L project and bootstrap status."""
    version_file = ROOT / "VERSION"
    channel_file = ROOT / "CHANNEL"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else ""
    channel = channel_file.read_text(encoding="utf-8").strip() if channel_file.is_file() else ""

    git_head = _run_result(
        ["git", "rev-parse", "--short", "HEAD"],
        timeout=10,
        capability=CAP_READ_ONLY,
    )
    git_branch_result = _run_result(
        ["git", "branch", "--show-current"],
        timeout=10,
        capability=CAP_READ_ONLY,
    )
    git_dirty = _run_result(
        ["git", "status", "--short"],
        timeout=10,
        capability=CAP_READ_ONLY,
    )
    dirty_files = [
        line for line in git_dirty.get("stdout", "").splitlines() if line.strip()
    ]

    canonical_sources = list(ROOT.glob("**/*.nql"))
    legacy_sources = list(ROOT.glob("**/*.nq"))
    asm_sources = list((ROOT / "src").glob("**/*.asm")) if (ROOT / "src").is_dir() else []
    reference = ROOT / "build/nqlc-r0"

    return {
        "name": "NolQu-L",
        "version": version or "unknown",
        "channel": channel or "unknown",
        "architecture": "x86_64-linux",
        "git": {
            "available": git_head["ok"],
            "commit": git_head.get("stdout", ""),
            "branch": git_branch_result.get("stdout", ""),
            "dirty_files": len(dirty_files),
        },
        "toolchain": {
            "nql": {
                "path": str(NQL),
                "available": NQL.is_file(),
                "canonical": NQL == CANONICAL_NQL,
                "legacy_fallback": NQL != CANONICAL_NQL,
            },
            "nqlc": {
                "path": str(NQLC),
                "available": NQLC.is_file(),
                "canonical": NQLC == CANONICAL_NQLC,
                "legacy_fallback": NQLC != CANONICAL_NQLC,
            },
        },
        "bootstrap": canonical_bootstrap_status(),
        "reference_r0": {
            "status": "AVAILABLE" if reference.is_file() else "NOT_BUILT",
            "path": str(reference.relative_to(ROOT)),
            "canonical_stage": False,
        },
        "sources": {
            "nql": len(canonical_sources),
            "legacy_nq": len(legacy_sources),
            "reference_asm": len(asm_sources),
        },
        "tests": {
            "bootstrap_suite": (ROOT / "tests/bootstrap/run_tests.sh").is_file(),
            "reference_regression_suite": (ROOT / "tests/compiler/run_tests.sh").is_file(),
            "mcp_suite": (ROOT / "tests/mcp/test_nolqu_mcp.py").is_file(),
        },
    }
# ---------------------------------------------------------------------------
# ASM analisis
# ---------------------------------------------------------------------------

@mcp.tool()
def find_todos(directory: str = "", file_glob: str = "") -> str:
    """
    Find TODO, FIXME, HACK, XXX, and NOTE comments in source files.

    Args:
        directory: Subdirectory to search (default: project root).
        file_glob: File pattern (default: .nql, legacy .nq, and .asm).
    """
    try:
        target = _safe_path(directory) if directory else ROOT
    except ValueError as e:
        return f"ERROR: {e}"

    patterns = ["TODO", "FIXME", "HACK", "XXX", "NOTE", "BUG"]
    pattern  = "|".join(patterns)

    if file_glob:
        cmd = ["grep", "-rn", "-E", pattern, "--include", file_glob, str(target)]
    else:
        result_nql = subprocess.run(
            ["grep", "-rn", "-E", pattern, "--include", "*.nql", str(target)],
            capture_output=True, text=True
        )
        result_nq = subprocess.run(
            ["grep", "-rn", "-E", pattern, "--include", "*.nq", str(target)],
            capture_output=True, text=True
        )
        result_asm = subprocess.run(
            ["grep", "-rn", "-E", pattern, "--include", "*.asm", str(target)],
            capture_output=True, text=True
        )
        combined = (result_nql.stdout + result_nq.stdout + result_asm.stdout).strip()
        if not combined:
            return "✓ No TODO/FIXME/HACK/XXX/NOTE/BUG found."
        count = len(combined.splitlines())
        return f"Found {count} item(s):\n{combined}"

    return _run(cmd, timeout=15)


@mcp.tool()
def check_label_duplicates(asm_file: str = "") -> str:
    """
    Find duplicate labels in .asm files.
    Duplicate labels cause NASM errors and are hard to spot manually.

    Args:
        asm_file: Path to .asm file (relative to project root).
                  If empty, scans all .asm files in src/.
    """
    if asm_file:
        try:
            files = [_safe_path(asm_file)]
        except ValueError as e:
            return f"ERROR: {e}"
    else:
        files = list((ROOT / "src").glob("**/*.asm"))
        if not files:
            return "ERROR: tidak ada file .asm di src/"

    all_labels: dict[str, list[str]] = {}
    for p in files:
        if not p.exists():
            continue
        for lineno, raw in enumerate(p.read_text(errors="replace").splitlines(), 1):
            stripped = raw.strip()
            if (stripped.endswith(":")
                    and not stripped.startswith(";")
                    and not stripped.startswith(".")):
                label = stripped.rstrip(":")
                key = f"{p.relative_to(ROOT)}:{lineno}"
                all_labels.setdefault(label, []).append(key)

    dupes = {k: v for k, v in all_labels.items() if len(v) > 1}
    if not dupes:
        return f"✓ No duplicate labels found in {len(files)} file(s)."

    lines = [f"Found {len(dupes)} duplicate label(s):"]
    for label, locations in sorted(dupes.items()):
        lines.append(f"\n  '{label}' defined {len(locations)} times:")
        for loc in locations:
            lines.append(f"    {loc}")
    return "\n".join(lines)


@mcp.tool()
def asm_stats(directory: str = "src") -> str:
    """
    Show statistics for .asm source files:
    total lines, code lines, comment lines, blank lines,
    function count, and instruction breakdown.

    Args:
        directory: Subdirectory to scan (default: src/).
    """
    try:
        target = _safe_path(directory)
    except ValueError as e:
        return f"ERROR: {e}"
    if not target.exists():
        return f"ERROR: direktori tidak ditemukan — '{directory}'"

    files = list(target.glob("**/*.asm"))
    if not files:
        return f"ERROR: tidak ada file .asm di '{directory}'"

    total_lines    = 0
    code_lines     = 0
    comment_lines  = 0
    blank_lines    = 0
    functions      = 0
    instr_counts: dict[str, int] = {}

    for p in files:
        for raw in p.read_text(errors="replace").splitlines():
            total_lines += 1
            stripped = raw.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith(";"):
                comment_lines += 1
            else:
                code_lines += 1
                # count function labels
                if (stripped.endswith(":")
                        and not stripped.startswith(".")
                        and not stripped.startswith(";")):
                    functions += 1
                # count instructions (first word of code line)
                first_word = stripped.split()[0].lower().rstrip(":")
                if first_word and not first_word.endswith(":"):
                    instr_counts[first_word] = instr_counts.get(first_word, 0) + 1

    top_instrs = sorted(instr_counts.items(), key=lambda x: -x[1])[:10]

    lines = [
        f"=== ASM Stats: {directory} ({len(files)} files) ===",
        f"  total lines   : {total_lines}",
        f"  code lines    : {code_lines}",
        f"  comment lines : {comment_lines}",
        f"  blank lines   : {blank_lines}",
        f"  functions     : {functions}",
        "",
        "  Top 10 instructions:",
    ]
    for instr, count in top_instrs:
        lines.append(f"    {instr:<12} {count}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Canonical bootstrap controller
# ---------------------------------------------------------------------------

_BOOTSTRAP_ARTIFACTS: dict[str, dict[str, str]] = {
    "machine": {
        "artifact": "bootstrap/machine/x86_64-linux/hex0.seed",
        "hash": "bootstrap/machine/x86_64-linux/hex0.sha256",
        "builder": "bootstrap/machine/x86_64-linux/materialize.sh",
        "built_by": "audited machine bytes",
    },
    "stage0": {
        "artifact": "bootstrap/stage0/x86_64-linux/stage0.seed",
        "hash": "bootstrap/stage0/x86_64-linux/stage0.sha256",
        "builder": "bootstrap/stage0/x86_64-linux/materialize.sh",
        "built_by": "Machine-Level Foundation",
    },
    "b0": {
        "artifact": "bootstrap/compiler/b0/x86_64-linux/b0.seed",
        "hash": "bootstrap/compiler/b0/x86_64-linux/b0.sha256",
        "builder": "bootstrap/compiler/b0/x86_64-linux/materialize.sh",
        "built_by": "Stage 0",
    },
    "c0": {
        "artifact": "bootstrap/compiler/c0/x86_64-linux/c0.seed",
        "hash": "bootstrap/compiler/c0/x86_64-linux/c0.sha256",
        "builder": "bootstrap/compiler/c0/x86_64-linux/materialize.sh",
        "built_by": "B0",
    },
    "c0_successor": {
        "artifact": "bootstrap/compiler/c0/x86_64-linux/c0-successor.seed",
        "hash": "bootstrap/compiler/c0/x86_64-linux/c0-successor.sha256",
        "builder": "bootstrap/compiler/c0/x86_64-linux/materialize-successor.sh",
        "built_by": "C0",
    },
    "c0_frontend": {
        "artifact": "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed",
        "hash": "bootstrap/compiler/c0/x86_64-linux/c0-frontend.sha256",
        "builder": "bootstrap/compiler/c0/x86_64-linux/materialize-frontend.sh",
        "built_by": "B0",
    },
    "c0_backend": {
        "artifact": "bootstrap/compiler/c0/x86_64-linux/c0-backend.seed",
        "hash": "bootstrap/compiler/c0/x86_64-linux/c0-backend.sha256",
        "builder": "bootstrap/compiler/c0/x86_64-linux/materialize-backend.sh",
        "built_by": "B0",
    },
}


def _x86_runner(
    executable: pathlib.Path,
    *,
    machine: str = "",
) -> list[str]:
    host_machine = machine or os.uname().machine
    if host_machine in {"x86_64", "amd64"}:
        return [str(executable)]
    emulator = shutil.which("qemu-x86_64")
    if emulator:
        return [emulator, str(executable)]
    raise RuntimeError(
        f"x86_64 execution unavailable on {host_machine}; install qemu-x86_64"
    )


def _artifact_runner(executable: pathlib.Path) -> list[str]:
    """Run x86_64 ELF artifacts through qemu when the host is not x86_64."""
    header = executable.read_bytes()[:20]
    if header[:4] == b"\x7fELF" and len(header) >= 20:
        byte_order = "little" if header[5] == 1 else "big"
        machine = int.from_bytes(header[18:20], byte_order)
        if machine == 62:  # EM_X86_64
            return _x86_runner(executable)
    return [str(executable)]


def _read_expected_hash(path: pathlib.Path) -> tuple[str, str]:
    if not path.is_file():
        return "", ""
    fields = path.read_text(encoding="utf-8", errors="replace").split()
    if len(fields) < 2 or len(fields[0]) != 64:
        return "", ""
    return fields[0].lower(), fields[1]


def _bootstrap_stage_state(name: str) -> dict[str, Any]:
    definition = _BOOTSTRAP_ARTIFACTS[name]
    artifact = ROOT / definition["artifact"]
    hash_path = ROOT / definition["hash"]
    expected, expected_name = _read_expected_hash(hash_path)
    if not artifact.is_file() or not expected:
        return {
            "status": "NOT_IMPLEMENTED",
            "artifact": definition["artifact"],
            "hash_manifest": definition["hash"],
            "built_by": definition["built_by"],
        }
    actual = _sha256(artifact)
    status = "PASS" if actual == expected else "HASH_MISMATCH"
    return {
        "status": status,
        "artifact": definition["artifact"],
        "hash_manifest": definition["hash"],
        "expected_name": expected_name,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "size": artifact.stat().st_size,
        "executable": os.access(artifact, os.X_OK),
        "built_by": definition["built_by"],
    }


def _current_c0_version() -> str:
    for source_name in ("compiler.nql", "compiler.nq"):
        source = ROOT / "bootstrap/compiler/c0" / source_name
        if not source.is_file():
            continue
        with source.open("r", encoding="utf-8", errors="replace") as stream:
            first_line = stream.readline()
        match = re.match(r"\s*#\s*C0\.(\d+)\b", first_line)
        if match:
            return f"C0.{match.group(1)}"

    document = ROOT / DEVELOPMENT_DOCUMENT
    if not document.is_file():
        return "unknown"
    versions = [int(value) for value in re.findall(
        r"Core Compiler (?:emitter )?sampai subfase C0\.(\d+)",
        document.read_text(encoding="utf-8", errors="replace"),
    )]
    return f"C0.{max(versions)}" if versions else "unknown"


_C0_PROBE_HISTORY = (
    {"milestone": "C0.9", "blocker": "input_read", "line": 5},
    {"milestone": "C0.10", "blocker": "byte_parse_stmts", "line": 3},
    {"milestone": "C0.11", "blocker": "byte_store(4,184)", "line": 4},
    {"milestone": "C0.12", "blocker": "byte_store(5,60)", "line": 5},
    {"milestone": "C0.13", "blocker": "byte_store(9,15)", "line": 6},
    {"milestone": "C0.14", "blocker": "while byte_load(1)", "line": 4},
    {"milestone": "C0.15", "blocker": "write", "line": 5},
    {"milestone": "C0.16", "blocker": "while byte_load(3)", "line": 10},
    {"milestone": "C0.17", "blocker": "while byte_load(2)", "line": 23},
    {"milestone": "C0.18", "blocker": "full compiler emission", "line": None},
    {
        "milestone": "C0.19",
        "blocker": "general full compiler implementation",
        "line": None,
    },
    {
        "milestone": "C0.20",
        "blocker": "indirect byte store for source-driven token tables",
        "line": None,
    },
    {
        "milestone": "C0.21",
        "blocker": "source-driven tokenization",
        "line": None,
    },
    {
        "milestone": "C0.22",
        "blocker": "lexical token classification and coalescing",
        "line": None,
    },
    {
        "milestone": "C0.23",
        "blocker": "lexical token coalescing and whitespace elision",
        "line": None,
    },
    {
        "milestone": "C0.24",
        "blocker": "source-driven parser over coalesced tokens",
        "line": None,
    },
    {
        "milestone": "C0.25",
        "blocker": (
            "source-driven statement grammar and precedence tree construction"
        ),
        "line": None,
    },
    {
        "milestone": "C0.26",
        "blocker": "AST semantic resolution and codegen; calls and structured control flow",
        "line": None,
        "component": "B0-built source frontend; C0.25 emitter retained",
    },
    {
        "milestone": "C0.27",
        "blocker": "function calls and structured control flow; compiler-source coverage",
        "line": None,
        "component": "B0-built AST backend; C0.26 frontend and C0.25 emitter retained",
    },
    {
        "milestone": "C0.28",
        "blocker": "function calls, runtime byte/stream operations and compiler-source coverage",
        "line": None,
        "component": "B0-built structured frontend/backend; C0.25 emitter retained",
    },
    {
        "milestone": "C0.29",
        "blocker": "runtime byte/stream operations and compiler-source coverage",
        "line": None,
        "component": "B0-built function frontend/backend with native calls; C0.25 emitter retained",
    },
    {
        "milestone": "C0.30",
        "blocker": "compiler-source capacity, wider spans or bounded compilation units",
        "line": None,
        "component": "B0-built frontend/backend with call statements and checked byte/stream runtime; C0.25 emitter retained",
    },
    {
        "milestone": "C0.31",
        "blocker": "next compiler workload not measured; Full Compiler remains NOT_IMPLEMENTED",
        "line": None,
        "component": "unpromoted compiler-capacity components; fresh gates required; C0.25 emitter retained",
    },
)


def _c0_probe_expectation(version: str) -> dict[str, Any] | None:
    return next(
        (entry for entry in reversed(_C0_PROBE_HISTORY)
         if entry["milestone"] == version),
        None,
    )


@mcp.tool()
def canonical_bootstrap_status() -> dict[str, Any]:
    """Report canonical machine -> Stage 0 -> B0 -> C0 state from hashes."""
    stages = {
        name: _bootstrap_stage_state(name)
        for name in ("machine", "stage0", "b0", "c0", "c0_successor", "c0_frontend", "c0_backend")
    }
    stages["full_compiler"] = {
        "status": "NOT_IMPLEMENTED",
        "note": "Reference Compiler R0 is not a canonical bootstrap stage",
    }
    stages["self_hosting"] = {"status": "NOT_IMPLEMENTED"}
    stages["verified"] = {"status": "NOT_IMPLEMENTED"}
    return {
        "architecture": "x86_64-linux",
        "current_c0": _current_c0_version(),
        "current_frontend": (
            "C0.32" if (ROOT / "bootstrap/compiler/c0/frontend.nql").is_file()
            else "NOT_IMPLEMENTED"
        ),
        "current_backend": (
            "C0.32" if (ROOT / "bootstrap/compiler/c0/backend.nql").is_file()
            else "NOT_IMPLEMENTED"
        ),
        "stages": stages,
        "component_version_scope": "source/probe contract; hashes alone do not verify capabilities",
        "capacity_verified": False,
        "compiler_profile_verified": False,
        "component_generation_verified": False,
        "unsafe_blocks_verified": False,
        "process_arguments_verified": False,
        "syscall_abi_verified": False,
        "full_compiler_verified": False,
        "self_hosting_verified": False,
        "canonical_chain": [
            "machine", "stage0", "b0", "c0", "full_compiler",
            "self_hosting", "verified",
        ],
    }


def _build_bootstrap_stage(name: str, timeout: int) -> dict[str, Any]:
    definition = _BOOTSTRAP_ARTIFACTS[name]
    builder = ROOT / definition["builder"]
    if not builder.is_file():
        return _error_result(
            f"canonical builder is missing: {definition['builder']}",
            capability=CAP_BUILD,
        )
    result = _run_result(
        [str(builder)],
        timeout=timeout,
        capability=CAP_BUILD,
        artifacts=[definition["artifact"]],
    )
    result["stage"] = name
    result["verification"] = _bootstrap_stage_state(name)
    result["ok"] = result["ok"] and result["verification"]["status"] == "PASS"
    return result


@mcp.tool()
def build_machine_foundation() -> dict[str, Any]:
    """Reconstruct and hash-verify the canonical Machine-Level Foundation."""
    return _build_bootstrap_stage("machine", 60)


@mcp.tool()
def build_stage0() -> dict[str, Any]:
    """Build and hash-verify canonical Stage 0 with the machine seed."""
    return _build_bootstrap_stage("stage0", 120)


@mcp.tool()
def build_b0() -> dict[str, Any]:
    """Build and hash-verify canonical Bootstrap Compiler B0 with Stage 0."""
    return _build_bootstrap_stage("b0", 120)


@mcp.tool()
def build_c0() -> dict[str, Any]:
    """Build and hash-verify canonical Core Compiler C0 with B0."""
    return _build_bootstrap_stage("c0", 180)


@mcp.tool()
def verify_bootstrap_hashes() -> dict[str, Any]:
    """Verify every implemented canonical bootstrap artifact hash."""
    stages = {
        name: _bootstrap_stage_state(name)
        for name in _BOOTSTRAP_ARTIFACTS
    }
    implemented = [value for value in stages.values() if value["status"] != "NOT_IMPLEMENTED"]
    return {
        "ok": bool(implemented) and all(value["status"] == "PASS" for value in implemented),
        "stages": stages,
    }


@mcp.tool()
def bootstrap_hash(stage: str) -> dict[str, Any]:
    """Return the expected and actual SHA-256 identity for a bootstrap stage."""
    stage = stage.lower().strip()
    if stage not in _BOOTSTRAP_ARTIFACTS:
        return {"ok": False, "error": f"unknown bootstrap stage: {stage}"}
    state = _bootstrap_stage_state(stage)
    return {"ok": state["status"] == "PASS", "stage": stage, **state}


@mcp.tool()
def verify_elf_properties(artifact_path: str) -> dict[str, Any]:
    """Verify ELF64 x86_64, static linking, no interpreter, and non-exec stack."""
    try:
        artifact = _safe_path(artifact_path)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if not artifact.is_file():
        return {"ok": False, "error": f"artifact not found: {artifact_path}"}
    file_result = _run_result(["file", str(artifact)], timeout=10, capability=CAP_READ_ONLY)
    elf_result = _run_result(["readelf", "-W", "-l", str(artifact)], timeout=10, capability=CAP_READ_ONLY)
    file_text = file_result["stdout"]
    elf_text = elf_result["stdout"]
    is_elf64 = "ELF 64-bit" in file_text and "x86-64" in file_text
    no_interpreter = "INTERP" not in elf_text
    no_dynamic = "DYNAMIC" not in elf_text
    stack_lines = [line for line in elf_text.splitlines() if "GNU_STACK" in line]
    non_executable_stack = bool(stack_lines) and all("RWE" not in line for line in stack_lines)
    return {
        "ok": file_result["ok"] and elf_result["ok"] and is_elf64
        and no_interpreter and no_dynamic and non_executable_stack,
        "artifact": str(artifact.relative_to(ROOT)),
        "elf64_x86_64": is_elf64,
        "static": no_dynamic,
        "interpreter": not no_interpreter,
        "non_executable_stack": non_executable_stack,
        "sha256": _sha256(artifact),
    }


@mcp.tool()
def verify_no_host_dependency(artifact_or_stage: str) -> dict[str, Any]:
    """
    Verify that an ELF has no runtime interpreter or shared-library dependency.
    For canonical stage names, also require the committed SHA-256 identity.
    This checks runtime linkage, not semantic bootstrap provenance by itself.
    """
    requested = artifact_or_stage.strip()
    stage = requested.lower()
    if stage in _BOOTSTRAP_ARTIFACTS:
        state = _bootstrap_stage_state(stage)
        artifact = ROOT / _BOOTSTRAP_ARTIFACTS[stage]["artifact"]
        canonical_hash_verified = state["status"] == "PASS"
    else:
        try:
            artifact = _safe_path(requested)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        canonical_hash_verified = False
        state = None
    if not artifact.is_file():
        return {"ok": False, "error": f"artifact not found: {requested}"}

    elf = verify_elf_properties(str(artifact.relative_to(ROOT)))
    dynamic = _run_result(
        ["readelf", "-W", "-d", str(artifact)],
        timeout=10,
        capability=CAP_READ_ONLY,
    )
    needed_libraries: list[str] = []
    for line in dynamic.get("stdout", "").splitlines():
        if "(NEEDED)" not in line or "[" not in line or "]" not in line:
            continue
        needed_libraries.append(line.split("[", 1)[1].split("]", 1)[0])
    interpreter = bool(elf.get("interpreter"))
    runtime_independent = (
        bool(elf.get("ok"))
        and dynamic.get("ok", False)
        and not interpreter
        and not needed_libraries
    )
    hash_gate = canonical_hash_verified if state is not None else True
    return {
        "ok": runtime_independent and hash_gate,
        "artifact": str(artifact.relative_to(ROOT)),
        "stage": stage if state is not None else None,
        "scope": "ELF runtime interpreter and shared-library dependencies",
        "interpreter": interpreter,
        "needed_libraries": needed_libraries,
        "runtime_host_independent": runtime_independent,
        "canonical_hash_verified": canonical_hash_verified,
        "sha256": _sha256(artifact),
    }


@mcp.tool()
def bootstrap_artifact_info(stage: str) -> dict[str, Any]:
    """Inspect one canonical bootstrap artifact and its machine properties."""
    stage = stage.lower().strip()
    if stage not in _BOOTSTRAP_ARTIFACTS:
        return {"ok": False, "error": f"unknown bootstrap stage: {stage}"}
    state = _bootstrap_stage_state(stage)
    result: dict[str, Any] = {
        "ok": state["status"] == "PASS",
        "stage": stage,
        **state,
    }
    if state["status"] != "NOT_IMPLEMENTED":
        result["elf"] = verify_elf_properties(state["artifact"])
        result["host_dependency"] = verify_no_host_dependency(stage)
    return result


@mcp.tool()
def bootstrap_diff(stage_a: str, stage_b: str) -> dict[str, Any]:
    """Compare two canonical bootstrap artifacts byte-for-byte."""
    names = (stage_a.lower().strip(), stage_b.lower().strip())
    if any(name not in _BOOTSTRAP_ARTIFACTS for name in names):
        return {"ok": False, "error": "unknown bootstrap stage"}
    paths = [ROOT / _BOOTSTRAP_ARTIFACTS[name]["artifact"] for name in names]
    if any(not path.is_file() for path in paths):
        return {"ok": False, "error": "one or both artifacts are missing"}
    first = paths[0].read_bytes()
    second = paths[1].read_bytes()
    differing_offset = next(
        (index for index, pair in enumerate(zip(first, second)) if pair[0] != pair[1]),
        min(len(first), len(second)) if len(first) != len(second) else None,
    )
    identical = first == second
    return {
        "ok": True,
        "identical": identical,
        "stage_a": names[0],
        "stage_b": names[1],
        "size_a": len(first),
        "size_b": len(second),
        "sha256_a": hashlib.sha256(first).hexdigest(),
        "sha256_b": hashlib.sha256(second).hexdigest(),
        "first_differing_offset": differing_offset,
    }


_C031_SCOPE: ContextVar[dict[str, Any] | None] = ContextVar("c031_probe", default=None)
_C031_PROBE_SECONDS = 2400.0
_C031_TEST_SHA256 = "b946a1ffba60572117f740ef73a3f6ac92ac688ea76532f8118761788c13ad34"
_C031_GATE_SHA256 = "9e66e6942a945e9243ee6322ceafe12cae42e9440d352f4e84d0931b6e50d056"
_C031_LOADED_SHA256 = _sha256(pathlib.Path(__file__))
_C031_FLAGS = ("capacity_verified", "compiler_profile_verified", "component_generation_verified",
               "unsafe_blocks_verified", "process_arguments_verified", "syscall_abi_verified")
_C031_UNMEASURED = "next compiler workload not measured; Full Compiler remains NOT_IMPLEMENTED"


def _c031_fingerprint(path: pathlib.Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": _sha256(path)}


def _c031_inputs() -> dict[str, dict[str, Any]]:
    paths = {
        "bootstrap/manifest.tsv", "bootstrap/compiler/b0/compiler.nql0",
        "bootstrap/compiler/b0/x86_64-linux/b0.reference.asm",
        "bootstrap/compiler/c0/frontend.nql", "bootstrap/compiler/c0/backend.nql",
        "tests/bootstrap/c031_support.py", "tests/bootstrap/c031_debugger.py",
        "tests/bootstrap/c032_support.py", "examples/canonical/native_cat.nql",
        "tests/bootstrap/c0_native_os.sh", "tests/bootstrap/fixtures/c032/predecessor/hashes.json",
        "tests/bootstrap/c0_capacity.sh", "tests/bootstrap/c0_frontend.sh",
        "tests/bootstrap/c0_backend.sh", "tests/bootstrap/run_tests.sh",
        "tests/shared/lib.sh", "tests/shared/run_suite.sh", "tools/nolqu_mcp.py",
        "tests/bootstrap/fixtures/c031/predecessor/hashes.json",
    }
    for pattern in ("bootstrap/**/x86_64-linux/*.seed", "bootstrap/**/x86_64-linux/*.sha256",
                    "bootstrap/**/x86_64-linux/*.sh", "tests/bootstrap/test_c0_*.py",
                    "tests/bootstrap/fixtures/c031/predecessor/*.nql*",
                    "tests/bootstrap/fixtures/c032/predecessor/*.nql"):
        paths.update(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern))
    result = {}
    for relative in sorted(paths):
        path = ROOT / relative
        if not path.resolve(strict=True).is_relative_to(ROOT):
            raise ValueError(f"evidence input escapes root: {relative}")
        result[relative] = {**_c031_fingerprint(path), "mode": stat.S_IMODE(path.stat().st_mode)}
    for name in _BOOTSTRAP_ARTIFACTS:
        state = _bootstrap_stage_state(name)
        expected_name = pathlib.Path(state["artifact"]).name
        if state["status"] != "PASS" or not state.get("executable") or state.get("expected_name") != expected_name:
            raise ValueError(f"pinned executable is unavailable or invalid: {name}")
    if result["tools/nolqu_mcp.py"]["sha256"] != _C031_LOADED_SHA256:
        raise ValueError("loaded MCP code does not match this root; restart the server")
    if result["tests/bootstrap/test_c0_component_generations.py"]["sha256"] != _C031_TEST_SHA256:
        raise ValueError("generation test identity changed; receipt contract requires review")
    if result["tests/bootstrap/c0_capacity.sh"]["sha256"] != _C031_GATE_SHA256:
        raise ValueError("capacity gate identity changed; receipt contract requires review")
    return result


@contextmanager
def _c031_scope():
    existing = _C031_SCOPE.get()
    if existing is not None:
        yield existing
        return
    state = {"proof": None, "deadline": time.monotonic() + _C031_PROBE_SECONDS}
    token = _C031_SCOPE.set(state)
    try:
        yield state
    finally:
        _C031_SCOPE.reset(token)


def _c031_contract() -> tuple[dict[str, tuple[int, bytes]], set[str], set[str]]:
    # Reviewed legacy expectations plus additive native cases, independent of receipts.
    statuses = {
        **{f"runtime-{i}": value for i, value in enumerate((7, 0, 42, 120, 8, 9, 6, 2, 3, 21))},
        **{f"scalar-{i}": value for i, value in enumerate((7, 3, 0, 1, 32, 28, 37, 26, 18, 14,
                                                         9, 20, 163, 159, 66, 80, 5, 1, 6, 1))},
        **{f"control-{i}": value for i, value in enumerate((7, 6, 1, 1))},
        "wide-offset": 7, "wide-nodes": 44, "streams": 4, "default-bound": 70,
        "wide-default-bound": 70, "profile-high": 42, "profile-last": 1,
        "profile-bound": 70, "profile-empty": 0, "maximum": 255, "maximum-digits": 1,
        "minimum": 0, "minimum-quotient": 1, "leading-zeros": 7, "leading-zeros-maximum": 255,
        "runtime-add-overflow": 70, "runtime-minimum-overflow": 70, "runtime-division-overflow": 70,
    }
    stages: dict[str, tuple[int, bytes]] = {}
    checks: set[str] = set()
    artifacts = {f"{g}-{name}" for g in ("A1", "A2", "B", "C") for name in ("frontend", "backend")}
    artifacts.update("predecessor-" + name for name in ("b0", "frontend", "backend"))
    for name in ("frontend", "backend"):
        for g in ("A1", "A2"):
            stages[f"{g}-{name}"] = (0, b"")
        for g in ("B", "C"):
            stages[f"{g}-{name}-frontend"] = (0, b"")
            stages[f"{g}-{name}-backend"] = (0, b"")
            artifacts.add(f"{g}-{name}-nqaf")
    for g in ("A1", "B", "C"):
        for label, status in statuses.items():
            case = f"{g}-{label}"
            checks.add(case)
            stages[case + "-frontend"] = (0, b"")
            stages[case + "-backend"] = (0, b"")
            stages[case + "-execute"] = (status, b"ABCD" if label == "streams" else b"")
            artifacts.update((case, case + "-nqaf"))
        checks.update(f"{g}-parity-{group}" for group in ("runtime", "scalar", "control"))
        for profile in (0, 1):
            for kind in ("max-plus-one", "huge-invalid", "invalid-tail"):
                case = f"{g}-{kind}-{profile}"
                checks.add(case)
                stages[case + "-frontend"] = (0, b"")
                stages[case + "-reject"] = (1, b"")
                artifacts.add(case + "-nqaf")
            case = f"{g}-malformed-{profile}"
            stages[case + "-frontend"] = (0, b"")
            artifacts.add(case + "-nqaf")
            for kind in ("truncated", "trailing", "reserved", "anchor"):
                checks.add(case + "-" + kind)
                stages[case + "-" + kind] = (1, b"")
        for kind in ("syntax", "envelope"):
            checks.add(f"{g}-{kind}")
            stages[f"{g}-{kind}"] = (1, b"")
    for g in ("B", "C"):
        checks.add(g + "-named-oracles")
        stages[g + "-named-oracles"] = (0, b"")
        artifacts.update(f"{g}-native-mmap-profile{profile}-{suffix}"
                         for profile in (0, 1) for suffix in ("json", "nql", "nqaf", "elf"))
    native = {"argc": 1, "copy-empty": 0, "address": 1, "enosys": 1,
              "index": 70, "copy-bound": 74, "frame-bound": 70,
              "negative-span": 70, "cat-stdin": 0}
    for g in ("A1", "B", "C"):
        for profile in (0, 1):
            for name, status in native.items():
                case = f"{g}-native-{name}-{profile}"
                checks.add(case)
                stages[case + "-frontend"] = (0, b"")
                stages[case + "-backend"] = (0, b"")
                stages[case + "-execute"] = (status, b"native\x00stdin\xff\n" if name == "cat-stdin" else b"")
                artifacts.update((case, case + "-nqaf"))
        for name in ("permission", "invariant"):
            case = f"{g}-native-{name}"
            checks.add(case)
            stages[case] = (1, b"")
    return stages, checks, artifacts


def _c031_records(records: list[dict[str, Any]], required: set[str], key: str = "label") -> dict[str, Any]:
    result = {record[key]: record for record in records}
    if len(result) != len(records) or set(result) != required:
        raise ValueError(f"incomplete or duplicate {key} set")
    return result


def _c031_evidence_path(raw: str, directory: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(raw)
    if not path.is_absolute() or path.is_symlink() or not path.resolve(strict=True).is_relative_to(directory):
        raise ValueError(f"evidence path escapes invocation: {raw}")
    if not path.is_file():
        raise ValueError(f"missing evidence file: {raw}")
    return path


def _c031_json(path: pathlib.Path) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    with path.open(encoding="utf-8") as stream:
        result = json.load(stream, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError("receipt must be an object")
    return result


# A separate Linux subreaper owns even oracle grandchildren in new sessions.
_C031_SUPERVISOR = r'''
import ctypes, json, os, pathlib, signal, subprocess, sys, time
directory = pathlib.Path(sys.argv[1])
budget = float(sys.argv[2])
command = json.loads(sys.argv[3])
stop = False
def interrupt(signum, frame):
    global stop
    stop = True
for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(signum, interrupt)
def descendants():
    # Some Linux hosts omit task/*/children; use parent IDs from proc stat.
    parents = {}
    for path in pathlib.Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
            parents.setdefault(int(fields[1]), set()).add(int(path.parent.name))
        except (OSError, ValueError, IndexError):
            pass
    result, pending = set(), list(parents.get(os.getpid(), ()))
    while pending:
        pid = pending.pop()
        if pid not in result:
            result.add(pid)
            pending.extend(parents.get(pid, ()))
    return result
def reap():
    while True:
        try:
            if os.waitpid(-1, os.WNOHANG)[0] == 0:
                return
        except ChildProcessError:
            return
record = dict(exit_code=None, timed_out=False, cleanup_complete=False)
child = None
try:
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise OSError('cannot acquire scoped child-subreaper ownership')
    with (directory / 'stdout').open('wb') as out, (directory / 'stderr').open('wb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        deadline = time.monotonic() + budget
        while child.poll() is None and not stop and time.monotonic() < deadline:
            time.sleep(0.05)
        record['timed_out'] = child.poll() is None and not stop
        record['interrupted'] = stop
        record['leaked_descendants'] = child.poll() is not None and bool(descendants())
finally:
    # Let Python finally blocks close Guests/oracle groups before escalation.
    for sig, grace in ((signal.SIGINT, 5.0), (signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
        deadline = time.monotonic() + grace
        sent = set()
        while True:
            owned = descendants()
            if not owned:
                break
            for pid in owned - sent:
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            sent.update(owned)
            if child is not None:
                child.poll()
            if child is None or child.returncode is not None:
                reap()
            if time.monotonic() >= deadline:
                break
            time.sleep(0.05)
        if not descendants():
            break
    if child is not None:
        child.poll()
        record['exit_code'] = child.returncode
        if child.returncode is not None:
            reap()
    record['cleanup_complete'] = child is not None and child.returncode is not None and not descendants()
    (directory / 'lifecycle.json').write_text(json.dumps(record))
'''


def _c031_command(command: list[str], directory: pathlib.Path, timeout: float,
                  env: dict[str, str] | None = None) -> dict[str, Any]:
    directory.mkdir()
    started = time.monotonic()
    with (directory / "supervisor.stderr").open("wb") as diagnostic:
        with subprocess.Popen([sys.executable, "-B", "-c", _C031_SUPERVISOR,
                               str(directory), str(max(0.001, timeout)), json.dumps(command)],
                              cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=diagnostic,
                              start_new_session=True) as process:
            supervisor_timed_out = False
            try:
                process.wait(timeout=max(0.001, timeout) + 15)
            except subprocess.TimeoutExpired:
                supervisor_timed_out = True
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGTERM)
                    try:
                        process.wait(timeout=12)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
    result = _error_result("scoped gate runner did not complete", command=command, capability=CAP_BUILD)
    lifecycle = directory / "lifecycle.json"
    if lifecycle.is_file():
        result.update(_c031_json(lifecycle))
    if supervisor_timed_out:
        result.update(timed_out=True, cleanup_complete=False)
    result.update(command=command, duration_ms=round((time.monotonic() - started) * 1000))
    for name, limit in (("stdout", MAX_STDOUT_BYTES), ("stderr", MAX_STDERR_BYTES)):
        path = directory / name
        if path.is_file():
            result[name], result[name + "_truncated"] = _truncate_output(path.read_text(errors="replace"), limit)
            result[name + "_file"] = {"path": str(path), **_c031_fingerprint(path)}
    result["ok"] = (process.returncode == 0 and result["exit_code"] == 0
                    and result.get("cleanup_complete") is True
                    and not result.get("timed_out") and not result.get("interrupted")
                    and not result.get("leaked_descendants"))
    _audit_event(tool=_calling_tool_name("c031_probe"), capability=CAP_BUILD,
                 arguments=shlex.join(command), duration_ms=result["duration_ms"],
                 exit_code=result["exit_code"], ok=result["ok"], changed_files=[], artifacts=[],
                 git_head_before=None, git_head_after=None)
    return result


def _c031_native_evidence(receipt: dict[str, Any], directory: pathlib.Path) -> dict[str, Any]:
    """Consume retained native traces independently; never infer execution from a flag."""
    def require(condition, message):
        if not condition:
            raise ValueError("native machine evidence: " + message)

    machine = receipt["machine_evidence"]
    require(set(machine) == {"B", "C"}, "missing generation")
    consumed = {}
    expected = b"actual file mmap offset 65536\x00\xff\n"
    fixture_hash = hashlib.sha256(b"P" * 65536 + expected + bytes(4096 - len(expected))).hexdigest()
    registers = {"rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "r8", "r9",
                 "r10", "r11", "r12", "r13", "r14", "r15", "rip"}
    preserved = ("rbx", "rbp", "rsp", "r12", "r13", "r14", "r15")
    arguments = ("rdi", "rsi", "rdx", "r10", "r8", "r9")
    for generation in ("B", "C"):
        item = machine[generation]
        original = pathlib.Path(item["directory"])
        require(original.is_absolute() and not original.is_symlink()
                and original.resolve(strict=True).is_relative_to(directory)
                and original.name == generation + "-native-machine", "trace directory mismatch")
        require(set(item["profiles"]) == {"0", "1"}, "missing profile")
        require({path.name for path in original.iterdir()} == {
            f"mmap-profile{profile}.{suffix}" for profile in (0, 1)
            for suffix in ("json", "nql", "nqaf", "elf")}, "original artifact set mismatch")
        for profile in (0, 1):
            labels = item["profiles"][str(profile)]
            require(labels == {suffix: f"{generation}-native-mmap-profile{profile}-{suffix}"
                               for suffix in ("json", "nql", "nqaf", "elf")}, "artifact label mismatch")
            paths, data = {}, {}
            for suffix, label in labels.items():
                artifact = receipt["artifacts"][label]
                path = _c031_evidence_path(artifact["path"], directory)
                original_path = _c031_evidence_path(str(original / f"mmap-profile{profile}.{suffix}"), directory)
                mode = 0o755 if suffix == "elf" else 0o644
                identity = {key: artifact[key] for key in ("bytes", "sha256")}
                require(path.name == label + ".artifact" and 0 < identity["bytes"] <= 8388608,
                        "canonical artifact path/size mismatch")
                require(_c031_fingerprint(path) == identity == _c031_fingerprint(original_path),
                        "canonical/original artifact identity mismatch")
                require(stat.S_IMODE(path.stat().st_mode) == mode
                        == stat.S_IMODE(original_path.stat().st_mode), "artifact mode mismatch")
                paths[suffix], data[suffix] = path, path.read_bytes()
                require(data[suffix] == original_path.read_bytes(), "artifact bytes differ")
                consumed[label] = dict(path=str(path), mode=mode, **identity)
            trace = _c031_json(paths["json"])
            require(type(trace["profile"]) is int and trace["profile"] == profile
                    and trace["synthetic_fault_injection"] is False
                    and trace["execution"] == "actual x86_64 Linux syscall execution via QEMU debugger",
                    "execution/profile mismatch")
            require(set(trace["artifacts"]) == {"nql", "nqaf", "elf"}, "trace artifact set mismatch")
            for suffix, identity in trace["artifacts"].items():
                require(identity == dict(path=f"mmap-profile{profile}.{suffix}",
                    **{key: consumed[labels[suffix]][key] for key in ("bytes", "sha256", "mode")}),
                    "trace/canonical identity mismatch")
            source, wire, binary = data["nql"], data["nqaf"], data["elf"]
            require(0 < len(source) <= 262144 and len(wire) >= 32
                    and wire[:8] == b"NQAF\x06\x20\0\0"
                    and wire[24:32] == bytes((5, profile)) + bytes(6), "wire dialect/profile mismatch")
            size, nodes, root, tokens = struct.unpack_from("<IIII", wire, 8)
            require(size == len(source) and 0 < nodes <= 65536 and 1 <= root <= nodes
                    and 0 < tokens <= 65536 and len(wire) == 32 + size + 32 * nodes
                    and wire[32:32 + size] == source, "wire/source identity mismatch")
            require(len(binary) >= 64 and binary[:7] == b"\x7fELF\x02\x01\x01"
                    and struct.unpack_from("<HHI", binary, 16) == (2, 62, 1), "ELF target mismatch")
            entry, headers = struct.unpack_from("<QQ", binary, 24)
            stride, count = struct.unpack_from("<HH", binary, 54)
            require(stride == 56 and 0 < count <= 64 and 64 <= headers
                    and headers + stride * count <= len(binary), "ELF headers outside file")
            rip = trace["syscall_rip"]
            require(type(rip) is int and 0 <= rip < (1 << 64), "invalid syscall address")
            syscall_offsets, executable_entry, stack = [], False, False
            for index in range(count):
                kind, flags, offset, address, _, files, memory, _ = struct.unpack_from(
                    "<IIQQQQQQ", binary, headers + stride * index)
                require(offset + files <= len(binary) and files <= memory
                        and kind not in (2, 3), "ELF linkage/segment mismatch")
                if kind == 1:
                    require(flags & 3 != 3, "writable executable segment")
                    if flags & 1:
                        executable_entry |= address <= entry < address + files
                        if address <= rip and rip + 2 <= address + files:
                            syscall_offsets.append(offset + rip - address)
                elif kind == 0x6474e551:
                    require(not flags & 1, "executable stack")
                    stack = True
            require(executable_entry and stack and len(syscall_offsets) == 1
                    and binary[syscall_offsets[0]:syscall_offsets[0] + 2] == b"\x0f\x05",
                    "observed address is not an executable syscall")
            observations = trace["observations"]
            require(isinstance(observations, list) and len(observations) == 5, "incomplete syscall trace")
            for call, number in zip(observations, (257, 9, 1, 11, 3)):
                require(type(call["number"]) is int and call["number"] == number, "syscall sequence mismatch")
                for phase in ("pre", "post"):
                    values = call[phase]
                    require(set(values) == registers and all(type(value) is int and 0 <= value < (1 << 64)
                                                            for value in values.values()), "invalid register snapshot")
                pre, post = call["pre"], call["post"]
                require(pre["rax"] == number and pre["rip"] == rip and post["rip"] == rip + 2
                        and pre["rsp"] % 16 == 8, "instruction/stack mismatch")
                require(all(pre[name] == post[name] for name in (*preserved, *arguments)),
                        "syscall clobbered preserved registers")
                require(all(pre[name] == observations[0]["pre"][name] for name in preserved),
                        "callee/stack continuity mismatch")
            opened, mapped, written, unmapped, closed = observations
            fd, address = opened["post"]["rax"], mapped["post"]["rax"]
            arena = opened["pre"]["rbx"]
            require(0 <= fd < (1 << 63) and 0 < address < (1 << 63) and address % 4096 == 0,
                    "raw open/mmap result mismatch")
            expected_arguments = (( (1 << 64) - 100, arena + 512, 2, 0, 0, 0),
                                  (0, 4096, 3, 1, fd, 65536),
                                  (1, address, len(expected), 0, 0, 0),
                                  (address, 4096, 0, 0, 0, 0), (fd, 0, 0, 0, 0, 0))
            for index, (call, values) in enumerate(zip(observations, expected_arguments)):
                require(tuple(call["pre"][name] for name in arguments) == values
                        and call["pre"]["r11"] == arena + index * 48, "six-register frame mismatch")
            require((written["post"]["rax"], unmapped["post"]["rax"], closed["post"]["rax"])
                    == (len(expected), 0, 0), "raw write/unmap/close result mismatch")
            require(type(trace["file_offset"]) is int and trace["file_offset"] == 65536
                    and trace["file_before_hex"] == trace["file_after_hex"] == trace["expected_hex"] == expected.hex()
                    and trace["file_before_sha256"] == trace["file_after_sha256"] == fixture_hash,
                    "file effect mismatch")
            require(trace["outcome"] == dict(status=0, stdout_hex=expected.hex(), stderr_hex="")
                    and type(trace["outcome"]["status"]) is int, "execution outcome mismatch")
    return consumed


def _c031_check_retained_native(records: dict[str, Any], archive: pathlib.Path) -> None:
    expected = {f"{generation}-native-mmap-profile{profile}-{suffix}"
                for generation in ("B", "C") for profile in (0, 1)
                for suffix in ("json", "nql", "nqaf", "elf")}
    if set(records) != expected:
        raise ValueError("retained native artifact set mismatch")
    for label, record in records.items():
        path = _c031_evidence_path(record["path"], archive)
        mode = 0o755 if label.endswith("-elf") else 0o644
        if (path.name != label + ".artifact" or record["mode"] != mode
                or stat.S_IMODE(path.stat().st_mode) != mode
                or _c031_fingerprint(path) != {key: record[key] for key in ("bytes", "sha256")}):
            raise ValueError("retained native artifact identity/mode mismatch: " + label)


def _c031_archive_native(consumed: dict[str, Any], archive: pathlib.Path) -> dict[str, Any]:
    retained = {}
    for label, record in consumed.items():
        if label not in {f"{g}-native-mmap-profile{p}-{s}" for g in ("B", "C")
                         for p in (0, 1) for s in ("json", "nql", "nqaf", "elf")}:
            raise ValueError("unexpected native artifact label")
        source = pathlib.Path(record["path"])
        identity = {key: record[key] for key in ("bytes", "sha256")}
        if source.is_symlink() or _c031_fingerprint(source) != identity:
            raise ValueError("consumed native artifact changed before archival")
        destination = archive / (label + ".artifact")
        if destination.exists() or destination.is_symlink():
            raise ValueError("native archive destination already exists")
        shutil.copy2(source, destination)
        if _c031_fingerprint(source) != identity or stat.S_IMODE(source.stat().st_mode) != record["mode"]:
            raise ValueError("consumed native artifact changed during archival")
        retained[label] = {**record, "path": str(destination), "consumed_path": str(source)}
    _c031_check_retained_native(retained, archive)
    return retained


def _c031_validate(directory: pathlib.Path, before: dict[str, Any]) -> dict[str, Any]:
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    receipts = list(directory.glob("test_actual_sources_build_and_rebuild-*/receipt.json"))
    require(len(receipts) == 1, "missing or duplicate actual-source generation receipt")
    receipt_path = _c031_evidence_path(str(receipts[0]), directory)
    receipt = _c031_json(receipt_path)
    require(receipt["component_generations_verified"] is True, "incomplete component generations")
    require(receipt["rejections"] == [] and "blocker" not in receipt, "generation rejection or blocker")
    require(receipt["cwd"] == str(ROOT), "generation root mismatch")
    script = pathlib.Path(receipt["argv"][0])
    if not script.is_absolute():
        script = ROOT / script  # cwd was checked above; never use the server's cwd.
    require(receipt["argv"][1:] == ["-v"] and script.resolve() == ROOT / "tests/bootstrap/test_c0_component_generations.py",
            "generation command mismatch")
    generation_inputs = {
        "bootstrap/compiler/c0/frontend.nql", "bootstrap/compiler/c0/backend.nql",
        "tests/bootstrap/test_c0_component_generations.py", "tests/bootstrap/c031_support.py",
        "tests/bootstrap/c031_debugger.py", "tests/bootstrap/c0_capacity.sh",
        "tests/bootstrap/c032_support.py", "examples/canonical/native_cat.nql",
        "tests/bootstrap/c0_native_os.sh", "tests/bootstrap/fixtures/c032/predecessor/hashes.json",
        "bootstrap/compiler/b0/compiler.nql0", "bootstrap/stage0/x86_64-linux/stage0.seed",
        "tests/bootstrap/fixtures/c031/predecessor/hashes.json",
    }
    for pattern in ("bootstrap/**/x86_64-linux/*.seed", "bootstrap/**/x86_64-linux/*.sha256",
                    "tests/bootstrap/test_c0_*.py", "tests/bootstrap/fixtures/c031/predecessor/*.nql*",
                    "tests/bootstrap/fixtures/c032/predecessor/*.nql"):
        generation_inputs.update(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern))
    expected = {str((ROOT / name).resolve()): {key: before[name][key] for key in ("bytes", "sha256")}
                for name in generation_inputs}
    require(receipt["identities"] == expected, "generation input identity mismatch")
    require(_c031_inputs() == before, "input identity changed during probe")
    required_stages, required_checks, required_artifacts = _c031_contract()
    checks = _c031_records(receipt["checks"], required_checks)
    require(all(item["passed"] is True and "error" not in item for item in checks.values()), "failed corpus check")
    stages = _c031_records(receipt["stages"], set(required_stages))
    artifacts = receipt["artifacts"]
    require(set(artifacts) == required_artifacts, "incomplete generation artifact set")
    for label, item in artifacts.items():
        path = _c031_evidence_path(item["path"], receipt_path.parent)
        require(path.name == label + ".artifact", "artifact label/path mismatch")
        require(_c031_fingerprint(path) == {key: item[key] for key in ("bytes", "sha256")},
                f"artifact identity mismatch: {label}")
        require(0 < item["bytes"] <= 8388608, "artifact size outside contract")

    def artifact(label):
        return {key: artifacts[label][key] for key in ("bytes", "sha256")}

    for component in ("frontend", "backend"):
        pin = before[f"bootstrap/compiler/c0/x86_64-linux/c0-{component}.seed"]
        pin = {key: pin[key] for key in ("bytes", "sha256")}
        require(artifact("A1-" + component) == pin == artifact("A2-" + component), "selected A candidate differs")
    pairs = {**{f"A1-A2-{name}": (f"A1-{name}", f"A2-{name}") for name in ("frontend", "backend")},
             **{f"selected-A1-{name}": (f"A1-{name}", f"A1-{name}") for name in ("frontend", "backend")},
             **{f"B-C-{name}": (f"B-{name}", f"C-{name}") for name in ("frontend", "backend")}}
    comparisons = _c031_records(receipt["comparisons"], set(pairs))
    for label, (left, right) in pairs.items():
        item = comparisons[label]
        require(item["first_difference_offset"] is None and item["left"] == artifact(left)
                and item["right"] == artifact(right) and artifact(left) == artifact(right), "generation comparison mismatch")
        require(pathlib.Path(artifacts[left]["path"]).read_bytes() == pathlib.Path(artifacts[right]["path"]).read_bytes(),
                "generation byte inequality")
    predecessors = _c031_json(ROOT / "tests/bootstrap/fixtures/c031/predecessor/hashes.json")
    require(receipt["predecessor_builder"] == "c031_support.build_predecessors", "missing predecessor provenance")
    for component, name in (("b0", "b0.seed"), ("frontend", "c0-frontend.seed"), ("backend", "c0-backend.seed")):
        require(artifacts["predecessor-" + component]["sha256"] == predecessors["artifacts"][name],
                "predecessor identity mismatch")
    module = ast.parse((ROOT / "tests/bootstrap/test_c0_component_generations.py").read_text())
    selectors = next(ast.literal_eval(node.value) for node in module.body
                     if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "GENERATION_ORACLES" for target in node.targets))
    require(len(selectors) == 41 and len(set(selectors)) == 41, "invalid reviewed oracle set")
    oracles = _c031_records(receipt["oracles"], {"B", "C"}, "generation")
    for generation, oracle in oracles.items():
        require(oracle["selectors"] == list(selectors) and type(oracle["returncode"]) is int
                and oracle["returncode"] == 0 and oracle["timed_out"] is False
                and oracle["child_reaped"] is True and oracle["temporary_removed"] is True,
                "incomplete generation oracles")
        for component in ("frontend", "backend"):
            item = oracle["components"][component]
            require({key: item[key] for key in ("bytes", "sha256")} == artifact(generation + "-" + component),
                    "oracle component identity mismatch")
            require(oracle["environment"]["C0_" + component.upper()] == item["path"], "oracle selected component mismatch")
            require(pathlib.Path(item["path"]).name == generation + "-" + component
                    and pathlib.Path(item["path"]).resolve().is_relative_to(receipt_path.parent),
                    "oracle executable path mismatch")
        require(oracle["environment"]["PYTHONPATH"] == str(ROOT / "tests/bootstrap"), "oracle root mismatch")
        require(oracle["environment"]["C032_NATIVE_EVIDENCE_DIR"]
                == receipt["machine_evidence"][generation]["directory"], "oracle native evidence directory mismatch")

    empty = {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}
    workloads = {}
    for index, stage in enumerate(receipt["stages"]):
        label = stage["label"]
        require(stage["timed_out"] is False and type(stage["returncode"]) is int
                and stage["returncode"] == required_stages[label][0], f"stage failed: {label}")
        require(pathlib.Path(stage["prefix"]).name == f"{index:03d}-{label}", "stage stream order mismatch")
        streams = {}
        for suffix, key in (("stdin", "input"), ("stdout", "stdout"), ("stderr", "stderr")):
            path = _c031_evidence_path(stage["prefix"] + "." + suffix, receipt_path.parent)
            require(_c031_fingerprint(path) == stage[key], f"raw stage stream identity mismatch: {label}/{suffix}")
            streams[suffix] = path
        if label in {f"{g}-{name}" for g in ("A1", "A2") for name in ("frontend", "backend")}:
            require(stage["stdout"] == empty == stage["stderr"] and "--compiler-profile" in stage["command"], "invalid B0 build receipt")
            require(stage["binary"] == str(ROOT / "bootstrap/compiler/b0/x86_64-linux/b0.seed"), "B0 producer mismatch")
        elif label.endswith("-named-oracles"):
            require(stage["command"][1:] == ["-B", "-W", "error::ResourceWarning", "-m", "unittest", "-v", *selectors], "oracle command mismatch")
            require(stage["stdout"] == empty and re.search(rb"\nRan 41 tests in [0-9.]+s\n\nOK\n$", streams["stderr"].read_bytes())
                    and not re.search(rb"(?im)^SKIP\b|\bskipped=|\.\.\. skipped ", streams["stderr"].read_bytes()),
                    "incomplete or skipped oracle output")
        elif label.endswith(("-frontend", "-backend")):
            emitted = label[:-9] + "-nqaf" if label.endswith("-frontend") else label[:-8]
            require(stage["stdout"] == artifact(emitted) and stage["stderr"] == empty, "producer output/artifact mismatch")
            if label.endswith("-backend"):
                require(stage["input"] == artifact(label[:-8] + "-nqaf"), "AST producer/consumer mismatch")
        else:
            require(streams["stdout"].read_bytes() == required_stages[label][1], "corpus stdout mismatch")
            error = streams["stderr"].read_bytes()
            if label.endswith("-execute"):
                if stage["returncode"] in (70, 74):
                    code = (b"C0R-008" if "-native-index-" in label else
                            b"C0R-009" if "-native-copy-bound-" in label else
                            b"C0R-001" if "overflow" in label else b"C0R-004")
                    require(b"[" + code + b"]" in error and error.startswith(b"input:"), "runtime diagnostic mismatch")
                else:
                    require(error == (b"ABCD" if label.endswith("-streams-execute") else b""), "corpus stderr mismatch")
            else:
                code = (b"C0S-001" if label.endswith("-native-permission") else
                        b"C0P-014" if label.endswith("-native-invariant") else
                        b"C0P-013" if label.endswith("-envelope") else b"C0P-" if label.endswith("-syntax") else
                        b"C0B-005" if label.endswith("-reject") else b"C0B-006" if label.endswith("-anchor") else b"C0B-001")
                require(code in error and error.startswith(b"input:"), "negative diagnostic mismatch")
        if label.startswith(("B-frontend-", "B-backend-", "C-frontend-", "C-backend-")):
            generation, component, phase = label.split("-")
            parent = "A1" if generation == "B" else "B"
            require(pathlib.Path(stage["binary"]).name == parent + "-" + phase, "component producer generation mismatch")
            source = (ROOT / f"bootstrap/compiler/c0/{component}.nql").read_bytes()
            if phase == "frontend":
                require(streams["stdin"].read_bytes() == b"NQSC\x01\x01" + bytes(10) + source, "actual source transport mismatch")
                wire = streams["stdout"].read_bytes()
                require(wire[:8] == b"NQAF\x05\x20\0\0" and wire[24:28] == b"\x04\x01\0\0",
                        "actual-source wire format/profile mismatch")
                size = int.from_bytes(wire[8:12], "little")
                nodes = int.from_bytes(wire[12:16], "little")
                tokens = int.from_bytes(wire[20:24], "little")
                require(size == len(source) and wire[32:32 + size] == source
                        and 0 < nodes <= 65536 and 0 < tokens <= 65536
                        and len(wire) == 32 + size + 32 * nodes, "actual-source wire identity/length mismatch")
                workloads[component] = dict(source_bytes=size, tokens=tokens, nodes=nodes, wire_bytes=len(wire))
            else:
                require(stage["input"] == artifact(generation + "-" + component + "-nqaf"), "backend input wire mismatch")
    native = _c031_native_evidence(receipt, receipt_path.parent)
    require(_c031_inputs() == before, "input identity changed while consuming proof")
    return {"generation_receipt_sha256": _sha256(receipt_path),
            "checks": len(checks), "stages": len(stages), "oracles": len(oracles),
            "actual_source_workloads": workloads,
            "native_machine_artifacts": native,
            "components": {label: artifact(label) for label in sorted(artifacts)
                           if label in {f"{g}-{name}" for g in ("A1", "A2", "B", "C") for name in ("frontend", "backend")}},
            "source_identities": {name: before[f"bootstrap/compiler/c0/{name}.nql"] for name in ("frontend", "backend")}}


def _c031_proof() -> dict[str, Any]:
    with _c031_scope() as scope:
        if scope["proof"] is not None:
            proof = scope["proof"]
            try:
                if proof["ok"] and _c031_inputs() != proof["input_identities"]:
                    raise ValueError("shared proof input identity changed")
                if proof["ok"]:
                    _c031_check_retained_native(proof["native_machine_artifacts"], pathlib.Path(proof["evidence_directory"]))
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
                proof = {**proof, "ok": False, "error": str(error), "timed_out": False, "exit_code": None,
                         **dict.fromkeys(_C031_FLAGS, False)}
                scope["proof"] = proof
            return proof
        proof: dict[str, Any] = {"ok": False, "exit_code": None, "timed_out": False, "gates": [],
                                 **dict.fromkeys(_C031_FLAGS, False)}
        scope["proof"] = proof
        try:
            before = _c031_inputs()
            proof["input_identities"] = before
            parent = ROOT / ".nolqu-mcp/tmp"
            parent.mkdir(parents=True, exist_ok=True)
            environment = dict(os.environ, ROOT_DIR=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
            for variable in ("B0_COMPILER", "C0_FRONTEND", "C0_BACKEND", "C031_WORK", "TMP_DIR", "C032_NATIVE_EVIDENCE_DIR"):
                environment.pop(variable, None)
            with tempfile.TemporaryDirectory(prefix="c031-", dir=parent) as temporary:
                directory = pathlib.Path(temporary)
                generation_directory = directory / "generations"
                generation_directory.mkdir()
                environment["C031_WORK"] = str(generation_directory)
                archive = ROOT / ".nolqu-mcp/evidence" / directory.name
                archive.mkdir(parents=True)
                proof["evidence_directory"] = str(archive)
                try:
                    for name, markers in (
                        ("c0_frontend", {"PASS c0-frontend"}),
                        ("c0_backend", {"PASS c0-control-flow", "PASS c0-functions", "PASS c0-runtime-io",
                                        "PASS c0-capacity-backend", "PASS c0-native-os", "PASS c0-backend"}),
                        ("c0_capacity", {"PASS c0-capacity", "PASS c0-component-generations"}),
                    ):
                        remaining = scope["deadline"] - time.monotonic()
                        if remaining <= 0:
                            proof["timed_out"] = True
                            raise ValueError("C0.32 aggregate gate budget exhausted")
                        command_directory = directory / name
                        result = _c031_command(["bash", str(ROOT / f"tests/bootstrap/{name}.sh")],
                                               command_directory, remaining, environment)
                        proof["gates"].append(result)
                        proof.update(exit_code=result["exit_code"], timed_out=result["timed_out"])
                        for filename in ("stdout", "stderr", "lifecycle.json", "supervisor.stderr"):
                            path = command_directory / filename
                            if path.is_file():
                                shutil.copy2(path, archive / (name + "." + filename))
                        if not result["ok"]:
                            raise ValueError(f"{name} failed or did not reap its owned children")
                        output = (command_directory / "stdout").read_text().splitlines()
                        if any(output.count(marker) != 1 for marker in markers):
                            raise ValueError(f"{name} is missing required gate markers")
                        error_output = (command_directory / "stderr").read_bytes()
                        if re.search(rb"(?im)^SKIP\b|\bskipped=|\.\.\. skipped ", error_output):
                            raise ValueError(f"{name} skipped required tests")
                        if name == "c0_capacity":
                            summaries = re.findall(rb"\nRan ([0-9]+) tests? in [0-9.]+s\n\nOK\n", error_output)
                            if summaries != [b"18", b"28", b"20", b"6"]:
                                raise ValueError("capacity gate is missing complete required unittest suites")
                        if name == "c0_backend":
                            summaries = re.findall(rb"\nRan ([0-9]+) tests? in [0-9.]+s\n\nOK\n", error_output)
                            if not summaries or summaries[-1] != b"23":
                                raise ValueError("backend gate is missing complete native unittest suite")
                        if _c031_inputs() != before:
                            raise ValueError(f"input identity changed during {name}")
                    proof.update(_c031_validate(generation_directory, before))
                    proof["native_machine_artifacts"] = _c031_archive_native(proof["native_machine_artifacts"], archive)
                    if _c031_inputs() != before:
                        raise ValueError("input identity changed while archiving proof")
                    proof.update(ok=True, exit_code=0, **dict.fromkeys(_C031_FLAGS, True))
                finally:
                    for path in generation_directory.glob("test_actual_sources_build_and_rebuild-*/receipt.json"):
                        shutil.copy2(path, archive / "generation-receipt.json")
                    (archive / "probe-receipt.json").write_text(json.dumps(proof, indent=2) + "\n")
            proof["temporary_removed"] = not directory.exists()
            if not proof["temporary_removed"]:
                raise ValueError("probe temporary directory was not removed")
            (archive / "probe-receipt.json").write_text(json.dumps(proof, indent=2) + "\n")
        except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, struct.error,
                SyntaxError, StopIteration, subprocess.TimeoutExpired) as error:
            proof.update(ok=False, error=str(error), **dict.fromkeys(_C031_FLAGS, False))
            if "evidence_directory" in proof:
                try:
                    (pathlib.Path(proof["evidence_directory"]) / "probe-receipt.json").write_text(json.dumps(proof, indent=2) + "\n")
                except OSError as failure:
                    proof["evidence_error"] = str(failure)
        return proof


def _c031_component_probe(component: str) -> dict[str, Any]:
    state = _bootstrap_stage_state("c0_" + component)
    result: dict[str, Any] = {
        "ok": False, component + "_version": "C0.32", "built_by": "B0",
        "artifact": state["artifact"], "probe_status": state["status"],
        "full_compiler_verified": False, "self_hosting_verified": False,
        **dict.fromkeys(_C031_FLAGS, False), "call_statements_verified": False,
        "source_capacity": 262144, "token_capacity": 65536, "node_capacity": 65536,
        "block_depth_capacity": 64, "parameter_capacity": 6,
        "byte_memory_capacity": 65536, "compiler_profile_byte_capacity": 16777216,
    }
    if component == "frontend":
        result["format"] = "NQAF/1, NQAF/2, NQAF/3, NQAF/4, NQAF/5 and NQAF/6"
    else:
        result.update(input_format="NQAF/1, NQAF/2, NQAF/3, NQAF/4, NQAF/5 and NQAF/6",
                      output_format="ELF64 x86_64-linux", call_depth_capacity=64,
                      semantics="lexical mutable i64 locals/parameters; checked arithmetic; comparisons; structured control flow; native calls/statements; explicit bounded byte/stream profiles; contextual unsafe scopes; argv and raw six-register Linux syscalls",
                      **dict.fromkeys(("semantic_resolution_verified", "codegen_verified", "control_flow_verified",
                                      "lexical_scope_verified", "function_calls_verified", "parameter_scope_verified",
                                      "byte_memory_verified", "stream_io_verified"), False))
    if state["status"] != "PASS":
        result["error"] = "component artifact is missing or does not match its SHA-256 manifest"
        return result
    proof = _c031_proof()
    verified = proof["ok"]
    result.update(ok=verified, artifact_sha256=state["actual_sha256"], evidence=proof,
                  exit_code=proof["exit_code"], timed_out=proof["timed_out"],
                  blocker=_C031_UNMEASURED if verified else proof.get("error", "C0.32 evidence unavailable"),
                  probe_status=("SOURCE_AST_FRONTEND_VERIFIED" if component == "frontend" else "SOURCE_AST_TO_ELF_VERIFIED")
                  if verified else "TIMED_OUT" if proof["timed_out"] else "UNEXPECTED_RESULT")
    for key in tuple(result):
        if key.endswith("_verified") and key not in {"full_compiler_verified", "self_hosting_verified"}:
            result[key] = verified
    if verified and "source_identities" in proof:
        result.update(source_sha256=proof["source_identities"][component]["sha256"],
                      source_identities=proof["source_identities"], component_identities=proof["components"],
                      b0_sha256=proof["input_identities"]["bootstrap/compiler/b0/x86_64-linux/b0.seed"]["sha256"],
                      frontend_sha256=proof["components"]["A1-frontend"]["sha256"])
    result["duration_ms"] = sum(gate["duration_ms"] for gate in proof["gates"])
    return result


@mcp.tool()
def build_c0_frontend() -> dict[str, Any]:
    """Build the experimental source-to-AST C0 component using B0, not R0."""
    return _build_bootstrap_stage("c0_frontend", 60)


@mcp.tool()
def run_c0_frontend_probe() -> dict[str, Any]:
    """Verify pinned B0 rebuilds, AST shape, syntax failures and bounded I/O."""
    return _c031_component_probe("frontend")


@mcp.tool()
def build_c0_backend() -> dict[str, Any]:
    """Build the experimental NQAF-to-ELF C0 backend directly with B0."""
    return _build_bootstrap_stage("c0_backend", 60)


@mcp.tool()
def run_c0_backend_probe() -> dict[str, Any]:
    """Verify AST validation, native calls, checked byte/stream runtime and standalone ELF."""
    return _c031_component_probe("backend")


@mcp.tool()
def run_c0_probe() -> dict[str, Any]:
    """Run the measured C0 bootstrap probe and report the next proven blocker."""
    with _c031_scope() as scope:
        result = _run_c0_probe()
        components = [result[key] for key in ("frontend", "backend") if key in result]
        if scope["proof"] is not None:
            proof = _c031_proof()
            if not proof["ok"]:
                error = proof.get("error", "C0.32 evidence unavailable")
                for item in (result, *components):
                    for field in tuple(item):
                        if field.endswith(("_verified", "_complete", "_identical")) or field == "source_expectation_matches":
                            item[field] = False
                    item.update(ok=False, parse_complete=False, error=error, blocker=error,
                                probe_status="TIMED_OUT" if proof["timed_out"] else "UNEXPECTED_RESULT",
                                exit_code=proof["exit_code"], timed_out=proof["timed_out"], stderr=error)
                for item in components:
                    item["evidence"] = proof
        result.update(full_compiler_verified=False, self_hosting_verified=False)
        for field in _C031_FLAGS:
            result[field] = len(components) == 2 and all(item.get(field) is True for item in components)
        return result


def _run_c0_probe() -> dict[str, Any]:
    version = _current_c0_version()
    if version in {
        "C0.19", "C0.20", "C0.21", "C0.22", "C0.23", "C0.24", "C0.25",
    }:
        seed = ROOT / _BOOTSTRAP_ARTIFACTS["c0"]["artifact"]
        fixture = ROOT / "tests/bootstrap/fixtures/c0/successor_self_emit.nq"
        source = ROOT / "bootstrap/compiler/c0/successor.nq"
        indirect_fixture = ROOT / "tests/bootstrap/fixtures/c0/runtime_byte_load_at.nq"
        scan_fixture = ROOT / "tests/bootstrap/fixtures/c0/runtime_byte_load_at_scan.nq"
        store_fixture = ROOT / "tests/bootstrap/fixtures/c0/runtime_byte_store_at.nq"
        table_copy_fixture = (
            ROOT / "tests/bootstrap/fixtures/c0/runtime_byte_store_at_copy.nq"
        )
        source_byte_tokenizer = (
            ROOT / "bootstrap/compiler/c0/source_byte_tokenizer.nql"
        )
        source_token_parser = (
            ROOT / "bootstrap/compiler/c0/source_token_parser.nql"
        )
        required = [seed, fixture, source]
        if version in {
            "C0.20", "C0.21", "C0.22", "C0.23", "C0.24", "C0.25",
        }:
            required.extend((indirect_fixture, scan_fixture))
        if version in {"C0.21", "C0.22", "C0.23", "C0.24", "C0.25"}:
            required.extend((store_fixture, table_copy_fixture))
        if version in {"C0.22", "C0.23", "C0.24", "C0.25"}:
            required.append(source_byte_tokenizer)
        if version == "C0.25":
            required.append(source_token_parser)
        if any(not path.is_file() for path in required):
            return {
                "ok": False,
                "c0_version": version,
                "probe_status": "NOT_IMPLEMENTED",
                "error": "one or more C0 probe inputs are missing",
            }

        temp_root = ROOT / ".nolqu-mcp" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix="c0-probe-", dir=temp_root) as name:
                indirect_load_verified = False
                source_scan_verified = False
                indirect_store_verified = False
                source_table_copy_verified = False
                source_byte_tokenizer_verified = False
                source_byte_tokenizer_overflow_verified = False
                source_ascii_classification_verified = False
                source_token_coalescing_verified = False
                source_token_capacity_verified = False
                source_token_parser_verified = False
                source_token_parser_invalid_verified = False
                source_byte_tokenizer_hash = None
                source_token_parser_hash = None
                if version in {
                    "C0.20", "C0.21", "C0.22", "C0.23", "C0.24", "C0.25",
                }:
                    indirect_artifact = pathlib.Path(name) / "indirect-load.seed"
                    indirect_compile = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=indirect_fixture.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    indirect_build_ok = (
                        indirect_compile.returncode == 0
                        and indirect_compile.stderr == b""
                        and indirect_compile.stdout.startswith(b"\x7fELF")
                    )
                    if not indirect_build_ok:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "INDIRECT_LOAD_BUILD_FAILED",
                            "exit_code": indirect_compile.returncode,
                            "stdout_bytes": len(indirect_compile.stdout),
                            "stderr": indirect_compile.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }
                    indirect_artifact.write_bytes(indirect_compile.stdout)
                    indirect_artifact.chmod(0o755)
                    indirect_run = subprocess.run(
                        _x86_runner(indirect_artifact),
                        cwd=ROOT,
                        capture_output=True,
                        timeout=5,
                    )
                    indirect_load_verified = (
                        indirect_run.returncode == 90
                        and indirect_run.stdout == b""
                        and indirect_run.stderr == b""
                    )
                    if not indirect_load_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "INDIRECT_LOAD_RUNTIME_FAILED",
                            "exit_code": indirect_run.returncode,
                            "stdout_bytes": len(indirect_run.stdout),
                            "stderr": indirect_run.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                    scan_artifact = pathlib.Path(name) / "source-scan.seed"
                    scan_compile = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=scan_fixture.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    scan_build_ok = (
                        scan_compile.returncode == 0
                        and scan_compile.stderr == b""
                        and scan_compile.stdout.startswith(b"\x7fELF")
                    )
                    if not scan_build_ok:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_SCAN_BUILD_FAILED",
                            "exit_code": scan_compile.returncode,
                            "stdout_bytes": len(scan_compile.stdout),
                            "stderr": scan_compile.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }
                    scan_artifact.write_bytes(scan_compile.stdout)
                    scan_artifact.chmod(0o755)
                    scan_input = b"fn main(){\nreturn 42}\n"
                    scan_run = subprocess.run(
                        _x86_runner(scan_artifact),
                        cwd=ROOT,
                        input=scan_input,
                        capture_output=True,
                        timeout=5,
                    )
                    source_scan_verified = (
                        scan_run.returncode == 0
                        and scan_run.stdout == scan_input
                        and scan_run.stderr == b""
                    )
                    if not source_scan_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_SCAN_RUNTIME_FAILED",
                            "exit_code": scan_run.returncode,
                            "stdout_identical": scan_run.stdout == scan_input,
                            "stderr": scan_run.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                if version in {"C0.21", "C0.22", "C0.23", "C0.24", "C0.25"}:
                    store_artifact = pathlib.Path(name) / "indirect-store.seed"
                    store_compile = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=store_fixture.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    store_build_ok = (
                        store_compile.returncode == 0
                        and store_compile.stderr == b""
                        and store_compile.stdout.startswith(b"\x7fELF")
                    )
                    if not store_build_ok:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "INDIRECT_STORE_BUILD_FAILED",
                            "exit_code": store_compile.returncode,
                            "stdout_bytes": len(store_compile.stdout),
                            "stderr": store_compile.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }
                    store_artifact.write_bytes(store_compile.stdout)
                    store_artifact.chmod(0o755)
                    store_run = subprocess.run(
                        _x86_runner(store_artifact),
                        cwd=ROOT,
                        capture_output=True,
                        timeout=5,
                    )
                    indirect_store_verified = (
                        store_run.returncode == 91
                        and store_run.stdout == b""
                        and store_run.stderr == b""
                    )
                    if not indirect_store_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "INDIRECT_STORE_RUNTIME_FAILED",
                            "exit_code": store_run.returncode,
                            "stdout_bytes": len(store_run.stdout),
                            "stderr": store_run.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                    copy_artifact = pathlib.Path(name) / "source-table-copy.seed"
                    copy_compile = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=table_copy_fixture.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    copy_build_ok = (
                        copy_compile.returncode == 0
                        and copy_compile.stderr == b""
                        and copy_compile.stdout.startswith(b"\x7fELF")
                    )
                    if not copy_build_ok:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_TABLE_COPY_BUILD_FAILED",
                            "exit_code": copy_compile.returncode,
                            "stdout_bytes": len(copy_compile.stdout),
                            "stderr": copy_compile.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }
                    copy_artifact.write_bytes(copy_compile.stdout)
                    copy_artifact.chmod(0o755)
                    copy_input = b"NQL!"
                    copy_run = subprocess.run(
                        _x86_runner(copy_artifact),
                        cwd=ROOT,
                        input=copy_input,
                        capture_output=True,
                        timeout=5,
                    )
                    source_table_copy_verified = (
                        copy_run.returncode == 0
                        and copy_run.stdout == copy_input
                        and copy_run.stderr == b""
                    )
                    if not source_table_copy_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_TABLE_COPY_RUNTIME_FAILED",
                            "exit_code": copy_run.returncode,
                            "stdout_identical": copy_run.stdout == copy_input,
                            "stderr": copy_run.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                if version in {"C0.22", "C0.23", "C0.24", "C0.25"}:
                    tokenizer_artifact = (
                        pathlib.Path(name) / "source-byte-tokenizer.seed"
                    )
                    tokenizer_compile = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=source_byte_tokenizer.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    tokenizer_build_ok = (
                        tokenizer_compile.returncode == 0
                        and tokenizer_compile.stderr == b""
                        and tokenizer_compile.stdout.startswith(b"\x7fELF")
                    )
                    if not tokenizer_build_ok:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_BYTE_TOKENIZER_BUILD_FAILED",
                            "exit_code": tokenizer_compile.returncode,
                            "stdout_bytes": len(tokenizer_compile.stdout),
                            "stderr": tokenizer_compile.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }
                    tokenizer_artifact.write_bytes(tokenizer_compile.stdout)
                    tokenizer_artifact.chmod(0o755)
                    source_byte_tokenizer_hash = _sha256(tokenizer_artifact)

                    token_input = b"fn 42+\n"
                    if version in {"C0.24", "C0.25"}:
                        expected_tokens = bytes((
                            3,
                            4, 0, 2,
                            5, 3, 2,
                            15, 5, 1,
                        )) + bytes(39)
                    elif version == "C0.23":
                        token_kinds = (4, 4, 1, 5, 5, 15, 1)
                        expected_tokens = bytes((len(token_input),)) + b"".join(
                            bytes((token_kinds[offset], offset, 1))
                            for offset in range(len(token_input))
                        ) + bytes((16 - len(token_input)) * 3)
                    else:
                        token_kinds = tuple(token_input)
                        expected_tokens = bytes((len(token_input),)) + b"".join(
                            bytes((token_kinds[offset], offset, 1))
                            for offset in range(len(token_input))
                        ) + bytes((16 - len(token_input)) * 3)
                    tokenizer_run = subprocess.run(
                        _x86_runner(tokenizer_artifact),
                        cwd=ROOT,
                        input=token_input,
                        capture_output=True,
                        timeout=5,
                    )
                    source_byte_tokenizer_verified = (
                        tokenizer_run.returncode == 0
                        and tokenizer_run.stdout == expected_tokens
                        and tokenizer_run.stderr == b""
                    )
                    if not source_byte_tokenizer_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_BYTE_TOKENIZER_RUNTIME_FAILED",
                            "exit_code": tokenizer_run.returncode,
                            "stdout_identical": (
                                tokenizer_run.stdout == expected_tokens
                            ),
                            "stderr": tokenizer_run.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                    if version in {"C0.23", "C0.24", "C0.25"}:
                        classifier_invalid = subprocess.run(
                            _x86_runner(tokenizer_artifact),
                            cwd=ROOT,
                            input=b"@",
                            capture_output=True,
                            timeout=5,
                        )
                        source_ascii_classification_verified = (
                            classifier_invalid.returncode == 1
                            and classifier_invalid.stdout == b""
                            and classifier_invalid.stderr
                            == b"runtime: invalid source\n"
                        )
                        if not source_ascii_classification_verified:
                            return {
                                "ok": False,
                                "c0_version": version,
                                "probe_status": "SOURCE_ASCII_CLASSIFIER_FAILED",
                                "exit_code": classifier_invalid.returncode,
                                "stdout_bytes": len(classifier_invalid.stdout),
                                "stderr": classifier_invalid.stderr.decode(
                                    "utf-8", errors="replace"
                                ).rstrip("\n"),
                            }

                    if version in {"C0.24", "C0.25"}:
                        coalescing_expected = bytes((
                            3,
                            5, 0, 2,
                            4, 2, 1,
                            4, 4, 3,
                        )) + bytes(39)
                        coalescing_run = subprocess.run(
                            _x86_runner(tokenizer_artifact),
                            cwd=ROOT,
                            input=b"12a a12",
                            capture_output=True,
                            timeout=5,
                        )
                        source_token_coalescing_verified = (
                            coalescing_run.returncode == 0
                            and coalescing_run.stdout == coalescing_expected
                            and coalescing_run.stderr == b""
                        )
                        if not source_token_coalescing_verified:
                            return {
                                "ok": False,
                                "c0_version": version,
                                "probe_status": "SOURCE_TOKEN_COALESCING_FAILED",
                                "exit_code": coalescing_run.returncode,
                                "stdout_identical": (
                                    coalescing_run.stdout == coalescing_expected
                                ),
                                "stderr": coalescing_run.stderr.decode(
                                    "utf-8", errors="replace"
                                ).rstrip("\n"),
                            }

                    tokenizer_overflow = subprocess.run(
                        _x86_runner(tokenizer_artifact),
                        cwd=ROOT,
                        input=b"abcdefghijklmnopq",
                        capture_output=True,
                        timeout=5,
                    )
                    source_byte_tokenizer_overflow_verified = (
                        tokenizer_overflow.returncode == 1
                        and tokenizer_overflow.stdout == b""
                        and tokenizer_overflow.stderr
                        == b"runtime: invalid source\n"
                    )
                    if not source_byte_tokenizer_overflow_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_BYTE_TOKENIZER_BOUND_FAILED",
                            "exit_code": tokenizer_overflow.returncode,
                            "stdout_bytes": len(tokenizer_overflow.stdout),
                            "stderr": tokenizer_overflow.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                if version == "C0.25":
                    token_capacity_source = (
                        b"fn main(){return 0" + b"+0" * 252 + b"}\n"
                    )
                    token_capacity_compile = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=token_capacity_source,
                        capture_output=True,
                        timeout=5,
                    )
                    token_capacity_overflow = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=token_capacity_source[:-1] + b"x\n",
                        capture_output=True,
                        timeout=5,
                    )
                    source_token_capacity_verified = (
                        token_capacity_compile.returncode == 0
                        and token_capacity_compile.stderr == b""
                        and token_capacity_compile.stdout.startswith(b"\x7fELF")
                        and token_capacity_overflow.returncode == 1
                        and token_capacity_overflow.stdout == b""
                        and token_capacity_overflow.stderr
                        == b"input:1:524: error[C0-001]: invalid C0 program\n"
                    )
                    if not source_token_capacity_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_TOKEN_CAPACITY_FAILED",
                            "exact_exit_code": token_capacity_compile.returncode,
                            "exact_stdout_bytes": len(token_capacity_compile.stdout),
                            "overflow_exit_code": (
                                token_capacity_overflow.returncode
                            ),
                            "overflow_stdout_bytes": len(
                                token_capacity_overflow.stdout
                            ),
                            "overflow_stderr": (
                                token_capacity_overflow.stderr.decode(
                                    "utf-8", errors="replace"
                                ).rstrip("\n")
                            ),
                        }

                    parser_compile_a = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=source_token_parser.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    parser_compile_b = subprocess.run(
                        _x86_runner(seed),
                        cwd=ROOT,
                        input=source_token_parser.read_bytes(),
                        capture_output=True,
                        timeout=5,
                    )
                    parser_build_ok = (
                        parser_compile_a.returncode == 0
                        and parser_compile_a.stderr == b""
                        and parser_compile_a.stdout.startswith(b"\x7fELF")
                        and parser_compile_b.returncode == 0
                        and parser_compile_b.stderr == b""
                        and parser_compile_b.stdout == parser_compile_a.stdout
                    )
                    if not parser_build_ok:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_TOKEN_PARSER_BUILD_FAILED",
                            "exit_code": parser_compile_a.returncode,
                            "stdout_bytes": len(parser_compile_a.stdout),
                            "deterministic": (
                                parser_compile_b.stdout == parser_compile_a.stdout
                            ),
                            "stderr": parser_compile_a.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                    parser_artifact = pathlib.Path(name) / "source-token-parser.seed"
                    parser_artifact.write_bytes(parser_compile_a.stdout)
                    parser_artifact.chmod(0o755)
                    source_token_parser_hash = _sha256(parser_artifact)
                    expression_tokens = bytes((
                        9,
                        4, 0, 1,
                        15, 1, 1,
                        5, 2, 1,
                        16, 3, 1,
                        4, 4, 1,
                        17, 5, 1,
                        5, 6, 1,
                        18, 7, 1,
                        4, 8, 1,
                    )) + bytes(21)
                    expression_expected = (
                        expression_tokens + bytes((1, 1, 0, 9))
                    )
                    parser_run = subprocess.run(
                        _x86_runner(parser_artifact),
                        cwd=ROOT,
                        input=expression_tokens,
                        capture_output=True,
                        timeout=5,
                    )
                    source_token_parser_verified = (
                        parser_run.returncode == 0
                        and parser_run.stdout == expression_expected
                        and parser_run.stderr == b""
                    )
                    if not source_token_parser_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_TOKEN_PARSER_RUNTIME_FAILED",
                            "exit_code": parser_run.returncode,
                            "stdout_identical": (
                                parser_run.stdout == expression_expected
                            ),
                            "stderr": parser_run.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                    invalid_expression = bytes((
                        2,
                        4, 0, 1,
                        15, 1, 1,
                    )) + bytes(42)
                    parser_invalid = subprocess.run(
                        _x86_runner(parser_artifact),
                        cwd=ROOT,
                        input=invalid_expression,
                        capture_output=True,
                        timeout=5,
                    )
                    source_token_parser_invalid_verified = (
                        parser_invalid.returncode == 1
                        and parser_invalid.stdout == b""
                        and parser_invalid.stderr == b"runtime: invalid source\n"
                    )
                    if not source_token_parser_invalid_verified:
                        return {
                            "ok": False,
                            "c0_version": version,
                            "probe_status": "SOURCE_TOKEN_PARSER_REJECTION_FAILED",
                            "exit_code": parser_invalid.returncode,
                            "stdout_bytes": len(parser_invalid.stdout),
                            "stderr": parser_invalid.stderr.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\n"),
                        }

                generation_b = pathlib.Path(name) / "generation-b.seed"
                compile_result = subprocess.run(
                    _x86_runner(seed),
                    cwd=ROOT,
                    input=fixture.read_bytes(),
                    capture_output=True,
                    timeout=5,
                )
                build_ok = (
                    compile_result.returncode == 0
                    and compile_result.stderr == b""
                    and compile_result.stdout.startswith(b"\x7fELF")
                )
                if not build_ok:
                    return {
                        "ok": False,
                        "c0_version": version,
                        "probe_status": "BUILD_FAILED",
                        "exit_code": compile_result.returncode,
                        "stdout_bytes": len(compile_result.stdout),
                        "stderr": compile_result.stderr.decode(
                            "utf-8", errors="replace"
                        ).rstrip("\n"),
                    }
                generation_b.write_bytes(compile_result.stdout)
                generation_b.chmod(0o755)
                generation_b_hash = _sha256(generation_b)

                result_c = subprocess.run(
                    _x86_runner(generation_b),
                    cwd=ROOT,
                    input=source.read_bytes(),
                    capture_output=True,
                    timeout=5,
                )
                generation_c_identical = (
                    result_c.returncode == 0
                    and result_c.stderr == b""
                    and result_c.stdout == compile_result.stdout
                )
                if not generation_c_identical:
                    return {
                        "ok": False,
                        "c0_version": version,
                        "probe_status": "UNEXPECTED_RESULT",
                        "exit_code": result_c.returncode,
                        "blocker": "bounded generation B -> C parity",
                        "parse_complete": result_c.returncode == 0,
                        "generation_c_identical": False,
                        "stdout_bytes": len(result_c.stdout),
                        "stderr": result_c.stderr.decode(
                            "utf-8", errors="replace"
                        ).rstrip("\n"),
                    }

                generation_c = pathlib.Path(name) / "generation-c.seed"
                generation_c.write_bytes(result_c.stdout)
                generation_c.chmod(0o755)
                result_d = subprocess.run(
                    _x86_runner(generation_c),
                    cwd=ROOT,
                    input=source.read_bytes(),
                    capture_output=True,
                    timeout=5,
                )
                generation_d_identical = (
                    result_d.returncode == 0
                    and result_d.stderr == b""
                    and result_d.stdout == result_c.stdout
                )
                generation_c_hash = _sha256(generation_c)
        except RuntimeError as exc:
            return {
                "ok": False,
                "c0_version": version,
                "probe_status": "UNAVAILABLE",
                "error": str(exc),
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "c0_version": version,
                "probe_status": "TIMED_OUT",
                "duration_ms": round((time.monotonic() - started) * 1000),
            }

        load_verified = (
            version == "C0.19"
            or (indirect_load_verified and source_scan_verified)
        )
        store_verified = (
            version not in {"C0.21", "C0.22", "C0.23", "C0.24", "C0.25"}
            or (indirect_store_verified and source_table_copy_verified)
        )
        tokenizer_verified = (
            version not in {"C0.22", "C0.23", "C0.24", "C0.25"}
            or (
                source_byte_tokenizer_verified
                and source_byte_tokenizer_overflow_verified
                and (
                    version not in {"C0.23", "C0.24", "C0.25"}
                    or source_ascii_classification_verified
                )
                and (
                    version not in {"C0.24", "C0.25"}
                    or source_token_coalescing_verified
                )
            )
        )
        parser_verified = (
            version != "C0.25"
            or (
                source_token_capacity_verified
                and source_token_parser_verified
                and source_token_parser_invalid_verified
            )
        )
        all_verified = (
            generation_d_identical
            and load_verified
            and store_verified
            and tokenizer_verified
            and parser_verified
        )
        probe_result = {
            "ok": all_verified,
            "c0_version": version,
            "probe_status": (
                "SOURCE_EXPRESSION_PARSER_AND_BOUNDED_GENERATION_VERIFIED"
                if version == "C0.25" and all_verified
                else "SOURCE_TOKEN_COALESCING_AND_BOUNDED_GENERATION_VERIFIED"
                if version == "C0.24" and all_verified
                else "SOURCE_ASCII_CLASSIFICATION_AND_BOUNDED_GENERATION_VERIFIED"
                if version == "C0.23" and all_verified
                else "SOURCE_BYTE_TOKENS_AND_BOUNDED_GENERATION_VERIFIED"
                if version == "C0.22" and all_verified
                else "INDIRECT_STORE_AND_BOUNDED_GENERATION_VERIFIED"
                if version == "C0.21" and all_verified
                else "INDIRECT_LOAD_AND_BOUNDED_GENERATION_VERIFIED"
                if version == "C0.20" and all_verified
                else "BOUNDED_GENERATION_VERIFIED"
                if all_verified
                else "UNEXPECTED_RESULT"
            ),
            "exit_code": result_d.returncode,
            "source_line": None,
            "blocker": (
                "source-driven statement grammar and precedence tree construction"
                if version == "C0.25"
                else "source-driven parser over coalesced tokens"
                if version == "C0.24"
                else "lexical token coalescing and whitespace elision"
                if version == "C0.23"
                else "lexical token classification and coalescing"
                if version == "C0.22"
                else "source-driven tokenization"
                if version == "C0.21"
                else "indirect byte store for source-driven token tables"
                if version == "C0.20"
                else "general full compiler implementation"
            ),
            "source_excerpt": None,
            "parse_complete": True,
            "bounded_generation_verified": generation_d_identical,
            "indirect_load_verified": (
                indirect_load_verified
                if version in {
                    "C0.20", "C0.21", "C0.22", "C0.23", "C0.24", "C0.25",
                } else None
            ),
            "source_scan_verified": (
                source_scan_verified
                if version in {
                    "C0.20", "C0.21", "C0.22", "C0.23", "C0.24", "C0.25",
                } else None
            ),
            "indirect_store_verified": (
                indirect_store_verified
                if version in {"C0.21", "C0.22", "C0.23", "C0.24", "C0.25"} else None
            ),
            "source_table_copy_verified": (
                source_table_copy_verified
                if version in {"C0.21", "C0.22", "C0.23", "C0.24", "C0.25"} else None
            ),
            "source_byte_tokenizer_verified": (
                source_byte_tokenizer_verified
                if version in {"C0.22", "C0.23", "C0.24", "C0.25"} else None
            ),
            "source_byte_tokenizer_overflow_verified": (
                source_byte_tokenizer_overflow_verified
                if version in {"C0.22", "C0.23", "C0.24", "C0.25"} else None
            ),
            "source_byte_tokenizer_sha256": (
                source_byte_tokenizer_hash
                if version in {"C0.22", "C0.23", "C0.24", "C0.25"} else None
            ),
            "source_ascii_classification_verified": (
                source_ascii_classification_verified
                if version in {"C0.23", "C0.24", "C0.25"} else None
            ),
            "source_token_coalescing_verified": (
                source_token_coalescing_verified
                if version in {"C0.24", "C0.25"} else None
            ),
            "source_token_capacity": 512 if version == "C0.25" else None,
            "source_token_capacity_verified": (
                source_token_capacity_verified if version == "C0.25" else None
            ),
            "source_token_parser_verified": (
                source_token_parser_verified if version == "C0.25" else None
            ),
            "source_token_parser_invalid_verified": (
                source_token_parser_invalid_verified
                if version == "C0.25" else None
            ),
            "source_token_parser_sha256": (
                source_token_parser_hash if version == "C0.25" else None
            ),
            "generation_c_identical": generation_c_identical,
            "generation_d_identical": generation_d_identical,
            "artifact": str(seed.relative_to(ROOT)),
            "artifact_sha256": _sha256(seed),
            "generation_b_sha256": generation_b_hash,
            "generation_c_sha256": generation_c_hash,
            "generation_bytes": len(result_c.stdout),
            "stdout_bytes": len(result_d.stdout),
            "stderr": result_d.stderr.decode(
                "utf-8", errors="replace"
            ).rstrip("\n"),
            "diagnostic_identical": result_d.stderr == b"",
            "source_expectation_matches": generation_d_identical,
            "duration_ms": round((time.monotonic() - started) * 1000),
        }
        if version == "C0.25" and (ROOT / "bootstrap/compiler/c0/frontend.nql").is_file():
            frontend = run_c0_frontend_probe()
            probe_result["frontend"] = frontend
            probe_result["frontend_version"] = frontend["frontend_version"]
            probe_result["ok"] = all_verified and frontend["ok"]
            probe_result["emitter_parse_complete"] = probe_result["parse_complete"]
            probe_result["parse_complete"] = probe_result["parse_complete"] and frontend["ok"]
            if probe_result["ok"]:
                probe_result["probe_status"] = "SOURCE_AST_AND_BOUNDED_GENERATION_VERIFIED"
                probe_result["blocker"] = frontend["blocker"]
            elif not frontend["ok"]:
                probe_result["probe_status"] = frontend["probe_status"]
                probe_result["blocker"] = frontend.get("blocker", frontend.get("error"))
                probe_result["exit_code"] = frontend.get("evidence", {}).get("exit_code")
                probe_result["stderr"] = frontend.get("error", frontend.get("evidence", {}).get("stderr", ""))
            probe_result["duration_ms"] = round((time.monotonic() - started) * 1000)
        if version == "C0.25" and (ROOT / "bootstrap/compiler/c0/backend.nql").is_file():
            previous_ok = probe_result["ok"]
            backend = run_c0_backend_probe()
            probe_result["backend"] = backend
            probe_result["backend_version"] = backend["backend_version"]
            probe_result["ok"] = previous_ok and backend["ok"]
            probe_result["parse_complete"] = probe_result["parse_complete"] and backend["ok"]
            if probe_result["ok"]:
                probe_result["probe_status"] = "SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED"
                probe_result["blocker"] = backend["blocker"]
            elif previous_ok:
                probe_result["probe_status"] = backend["probe_status"]
                probe_result["blocker"] = backend.get("blocker", backend.get("error"))
                probe_result["exit_code"] = backend.get("evidence", {}).get("exit_code")
                probe_result["stderr"] = backend.get("error", backend.get("evidence", {}).get("stderr", ""))
            probe_result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return probe_result

    if version == "C0.18":
        seed = ROOT / _BOOTSTRAP_ARTIFACTS["c0"]["artifact"]
        fixture = ROOT / "tests/bootstrap/fixtures/c0/successor_parse_stmts.nq"
        source = ROOT / "bootstrap/compiler/c0/successor.nq"
        if not seed.is_file() or not fixture.is_file() or not source.is_file():
            return {
                "ok": False,
                "c0_version": version,
                "probe_status": "NOT_IMPLEMENTED",
                "error": "C0 seed, parser fixture, or successor source is missing",
            }

        temp_root = ROOT / ".nolqu-mcp" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix="c0-probe-", dir=temp_root) as name:
                parser_artifact = pathlib.Path(name) / "parser.seed"
                compile_result = subprocess.run(
                    _x86_runner(seed),
                    cwd=ROOT,
                    input=fixture.read_bytes(),
                    capture_output=True,
                    timeout=5,
                )
                if compile_result.returncode != 0 or compile_result.stderr:
                    return {
                        "ok": False,
                        "c0_version": version,
                        "probe_status": "BUILD_FAILED",
                        "exit_code": compile_result.returncode,
                        "stderr": compile_result.stderr.decode(
                            "utf-8", errors="replace"
                        ).rstrip("\n"),
                    }
                parser_artifact.write_bytes(compile_result.stdout)
                parser_artifact.chmod(0o755)
                parser_hash = _sha256(parser_artifact)
                result = subprocess.run(
                    _x86_runner(parser_artifact),
                    cwd=ROOT,
                    input=source.read_bytes(),
                    capture_output=True,
                    timeout=5,
                )
        except RuntimeError as exc:
            return {
                "ok": False,
                "c0_version": version,
                "probe_status": "UNAVAILABLE",
                "error": str(exc),
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "c0_version": version,
                "probe_status": "TIMED_OUT",
                "duration_ms": round((time.monotonic() - started) * 1000),
            }

        parsed = result.returncode == 0 and result.stdout == b"" and result.stderr == b""
        return {
            "ok": parsed,
            "c0_version": version,
            "probe_status": "PARSED" if parsed else "UNEXPECTED_RESULT",
            "exit_code": result.returncode,
            "source_line": None,
            "blocker": "full compiler emission",
            "source_excerpt": None,
            "parse_complete": parsed,
            "artifact": str(seed.relative_to(ROOT)),
            "artifact_sha256": _sha256(seed),
            "parser_artifact_sha256": parser_hash,
            "parser_artifact_bytes": len(compile_result.stdout),
            "stdout_bytes": len(result.stdout),
            "stderr": result.stderr.decode("utf-8", errors="replace").rstrip("\n"),
            "diagnostic_identical": result.stderr == b"",
            "source_expectation_matches": parsed,
            "duration_ms": round((time.monotonic() - started) * 1000),
        }

    seed = ROOT / _BOOTSTRAP_ARTIFACTS["c0_successor"]["artifact"]
    source = ROOT / "bootstrap/compiler/c0/successor.nq"
    if not seed.is_file() or not source.is_file():
        return {
            "ok": False,
            "probe_status": "NOT_IMPLEMENTED",
            "error": "C0 successor seed or source is missing",
        }
    source_bytes = source.read_bytes()
    started = time.monotonic()
    try:
        command = _x86_runner(seed)
        result = subprocess.run(
            command, cwd=ROOT, input=source_bytes,
            capture_output=True, timeout=5,
        )
    except RuntimeError as e:
        return {
            "ok": False,
            "probe_status": "UNAVAILABLE",
            "error": str(e),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "probe_status": "TIMED_OUT",
            "duration_ms": round((time.monotonic() - started) * 1000),
        }
    expectation = _c0_probe_expectation(version)
    source_lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    blocker_line = expectation["line"] if expectation else None
    blocker_source = (
        source_lines[blocker_line - 1]
        if blocker_line and blocker_line <= len(source_lines)
        else "unknown"
    )
    blocker = expectation["blocker"] if expectation else "unknown"
    source_matches = (
        expectation is not None
        and blocker_source.strip().startswith(expectation["blocker"])
    )
    diagnostic_matches = result.stderr == b"runtime: invalid source\n"
    expected_stop = (
        result.returncode == 1
        and result.stdout == b""
        and diagnostic_matches
        and source_matches
    )
    return {
        "ok": expected_stop,
        "c0_version": version,
        "probe_status": "STOPPED" if expected_stop else "UNEXPECTED_RESULT",
        "exit_code": result.returncode,
        "source_line": blocker_line,
        "blocker": blocker,
        "source_excerpt": (
            blocker_source[:77] + "..." if len(blocker_source) > 80 else blocker_source
        ),
        "artifact": str(seed.relative_to(ROOT)),
        "artifact_sha256": _sha256(seed),
        "stdout_bytes": len(result.stdout),
        "stderr": result.stderr.decode("utf-8", errors="replace").rstrip("\n"),
        "diagnostic_identical": diagnostic_matches,
        "source_expectation_matches": source_matches,
        "duration_ms": round((time.monotonic() - started) * 1000),
    }


@mcp.tool()
def current_c0_blocker() -> dict[str, Any]:
    """Return only the currently measured canonical C0 blocker."""
    probe = run_c0_probe()
    return {
        "ok": probe.get("ok", False),
        "c0_version": probe.get("c0_version", "unknown"),
        "frontend_version": probe.get("frontend_version"),
        "backend_version": probe.get("backend_version"),
        "probe_status": probe.get("probe_status", "UNKNOWN"),
        "source_line": probe.get("source_line"),
        "blocker": probe.get("blocker", probe.get("error", "unknown")),
    }


@mcp.tool()
def c0_probe_history() -> list[dict[str, Any]]:
    """Return the measured C0 blocker progression recorded by canonical gates."""
    return [dict(entry) for entry in _C0_PROBE_HISTORY]


@mcp.tool()
def build_full_compiler() -> dict[str, Any]:
    """Report canonical Full Compiler status without substituting Reference R0."""
    return {
        "ok": False,
        "status": "NOT_IMPLEMENTED",
        "error": "canonical Full NolQu-L Compiler is not implemented",
        "reference_r0": str((ROOT / "build/nqlc-r0").relative_to(ROOT)),
    }


@mcp.tool()
def self_host_generation() -> dict[str, Any]:
    """Report self-host generation status; never treats R0 as self-hosted."""
    return {
        "ok": False,
        "status": "NOT_IMPLEMENTED",
        "error": "canonical Full Compiler must exist before self-host generation",
    }


@mcp.tool()
def compare_compiler_generations(generation_b: str, generation_c: str) -> dict[str, Any]:
    """Compare two explicitly supplied compiler generations byte-for-byte."""
    try:
        first = _safe_path(generation_b)
        second = _safe_path(generation_c)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if not first.is_file() or not second.is_file():
        return {"ok": False, "error": "compiler generation artifact is missing"}
    hash_b = _sha256(first)
    hash_c = _sha256(second)
    return {
        "ok": hash_b == hash_c and first.stat().st_size == second.stat().st_size,
        "byte_identical": first.read_bytes() == second.read_bytes(),
        "generation_b_sha256": hash_b,
        "generation_c_sha256": hash_c,
        "generation_b_size": first.stat().st_size,
        "generation_c_size": second.stat().st_size,
    }


@mcp.tool()
def verify_self_hosting(
    generation_b: str = "",
    generation_c: str = "",
) -> dict[str, Any]:
    """Verify B == C only when both canonical self-host generations are supplied."""
    if not generation_b or not generation_c:
        return {
            "ok": False,
            "status": "NOT_IMPLEMENTED",
            "error": "generation B and C artifacts are required",
        }
    comparison = compare_compiler_generations(generation_b, generation_c)
    return {
        **comparison,
        "status": "VERIFIED" if comparison.get("ok") else "MISMATCH",
    }


@mcp.tool()
def mcp_self_test() -> dict[str, Any]:
    """Run isolated MCP safety, command, timeout, and cleanup checks."""
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    record("root", ROOT.is_dir() and (ROOT / "VERSION").is_file(), str(ROOT))
    try:
        _safe_path("../outside")
        escape_blocked = False
    except ValueError:
        escape_blocked = True
    record("safe_path_escape", escape_blocked)
    record("nql_detected", NQL.is_file(), str(NQL))
    record("nqlc_detected", NQLC.is_file(), str(NQLC))

    command = _run_result(
        ["sh", "-c", "printf mcp-self-test"],
        timeout=5,
        capability=CAP_READ_ONLY,
    )
    record("dedicated_command", command["ok"] and command["stdout"] == "mcp-self-test")
    timeout_result = _run_result(
        ["sh", "-c", "sleep 0.05"],
        timeout=0.001,
        capability=CAP_READ_ONLY,
    )
    record("tool_timeout", timeout_result["timed_out"])

    temp_parent = pathlib.Path(tempfile.mkdtemp(prefix=".nolqu-mcp-selftest-", dir=ROOT))
    try:
        target = temp_parent / "atomic.nql"
        _atomic_write_text(target, "ok\n")
        leaked = list(temp_parent.glob(".nolqu-mcp-write-*"))
        record("atomic_write", target.read_text(encoding="utf-8") == "ok\n")
        record("atomic_temp_cleanup", not leaked)
        audit = mcp_audit_log(limit=1)
        record("audit_log", audit.get("ok", False) and bool(audit.get("entries")))
    finally:
        import shutil
        shutil.rmtree(temp_parent, ignore_errors=True)

    return {"ok": all(item["ok"] for item in checks), "checks": checks}


# ---------------------------------------------------------------------------
# Self-hosting / migrasi
# ---------------------------------------------------------------------------

@mcp.tool()
def migration_status() -> dict[str, Any]:
    """Report canonical .nql migration state while retaining .nq aliases."""
    definitions = {
        "nql_ir_dump_parser": {
            "python": ["tools/nql_ir_dump_parser.py", "tools/nq_ir_dump_parser.py"],
            "source": [
                "tools/nql_ir_dump_parser.nql",
                "tools/nq_ir_dump_parser.nql",
                "tools/nq_ir_dump_parser.nq",
            ],
        },
        "nql_ir_json_to_llvm": {
            "python": ["tools/nql_ir_json_to_llvm.py", "tools/nq_ir_json_to_llvm.py"],
            "source": [
                "tools/nql_ir_json_to_llvm.nql",
                "tools/nq_ir_json_to_llvm.nql",
                "tools/nq_ir_json_to_llvm.nq",
            ],
        },
    }
    tools: dict[str, Any] = {}
    for name, definition in definitions.items():
        python_path, python_rel = _first_existing(definition["python"])
        source_path, source_rel = _first_existing(definition["source"])
        if source_path is None:
            status = "NOT_IMPLEMENTED"
        elif python_path is not None:
            status = "READY_FOR_VERIFICATION"
        else:
            status = "CANONICAL_ONLY"
        tools[name] = {
            "status": status,
            "python_reference": python_rel or None,
            "source": source_rel or None,
            "canonical_extension": bool(source_path and source_path.suffix == ".nql"),
            "legacy_aliases": [
                alias for alias, canonical in {
                    "nq_ir_dump_parser": "nql_ir_dump_parser",
                    "nq_ir_json_to_llvm": "nql_ir_json_to_llvm",
                }.items() if canonical == name
            ],
        }

    legacy_bootstrap = ROOT / "tools/nq_llvm_bootstrap.py"
    return {
        "ok": all(item["status"] != "NOT_IMPLEMENTED" for item in tools.values()),
        "canonical_extension": ".nql",
        "legacy_extension": ".nq",
        "compiler": "nqlc",
        "project_manager": "nql",
        "tools": tools,
        "legacy_bootstrap": {
            "path": "tools/nq_llvm_bootstrap.py",
            "status": "LEGACY_REFERENCE" if legacy_bootstrap.is_file() else "REMOVED",
        },
    }

def _first_existing(candidates: list[str]) -> tuple[pathlib.Path | None, str]:
    for candidate in candidates:
        path = ROOT / candidate
        if path.is_file():
            return path, candidate
    return None, ""


@mcp.tool()
def verify_migration(
    tool_name: str,
    test_input: str = "",
    input_file: str = "",
) -> dict[str, Any]:
    """
    Compare a Python reference and canonical .nql replacement using the same
    input/output paths. Verifies exit code, stdout, stderr, output artifact,
    and deterministic nqlc rebuild. Only canonical command-tool names are
    exposed; historical .nq sources remain readable during corpus migration.
    """
    aliases = {
        "nq_ir_dump_parser": "nql_ir_dump_parser",
        "nq_ir_json_to_llvm": "nql_ir_json_to_llvm",
    }
    canonical_name = aliases.get(tool_name, tool_name)
    tool_map = {
        "nql_ir_dump_parser": {
            "python": [
                "tools/nql_ir_dump_parser.py",
                "tools/nq_ir_dump_parser.py",
            ],
            "source": [
                "tools/nql_ir_dump_parser.nql",
                "tools/nq_ir_dump_parser.nql",
                "tools/nq_ir_dump_parser.nq",
            ],
        },
        "nql_ir_json_to_llvm": {
            "python": [
                "tools/nql_ir_json_to_llvm.py",
                "tools/nq_ir_json_to_llvm.py",
            ],
            "source": [
                "tools/nql_ir_json_to_llvm.nql",
                "tools/nq_ir_json_to_llvm.nql",
                "tools/nq_ir_json_to_llvm.nq",
            ],
        },
    }
    if canonical_name not in tool_map:
        return {
            "ok": False,
            "error": f"unknown migration tool: {tool_name}",
            "allowed": sorted(tool_map),
        }
    python_tool, python_rel = _first_existing(tool_map[canonical_name]["python"])
    nql_tool, nql_rel = _first_existing(tool_map[canonical_name]["source"])
    if python_tool is None:
        return {"ok": False, "error": "Python reference is missing"}
    if nql_tool is None:
        return {"ok": False, "error": "canonical .nql replacement is missing"}
    if not NQLC.is_file():
        return {"ok": False, "error": "nqlc is unavailable"}

    if input_file:
        try:
            supplied_input = _safe_path(input_file)
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        if not supplied_input.is_file():
            return {"ok": False, "error": f"input file not found: {input_file}"}
        input_bytes = supplied_input.read_bytes()
    elif test_input:
        input_bytes = test_input.encode("utf-8")
    else:
        input_bytes = None

    temp_root = ROOT / ".nolqu-mcp" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(
            prefix=f"{canonical_name}-", dir=temp_root
        ) as temporary_name:
            temporary = pathlib.Path(temporary_name)
            common_input = temporary / "input"
            common_output = temporary / "output"
            binary_one = temporary / "tool"

            if input_bytes is None:
                sample_source, _ = _first_existing([
                    "examples/core/hello.nql",
                    "examples/core/hello.nq",
                ])
                if sample_source is None:
                    return {"ok": False, "error": "default migration fixture is missing"}
                ir_dump = subprocess.run(
                    [str(NQLC), "--dump-ir", str(sample_source)],
                    cwd=ROOT,
                    capture_output=True,
                    timeout=60,
                )
                if ir_dump.returncode != 0:
                    return {
                        "ok": False,
                        "error": "could not generate default exported IR fixture",
                        "stderr": ir_dump.stderr.decode("utf-8", errors="replace"),
                    }
                if canonical_name == "nql_ir_dump_parser":
                    input_bytes = ir_dump.stdout
                else:
                    parser, _ = _first_existing([
                        "tools/nql_ir_dump_parser.py",
                        "tools/nq_ir_dump_parser.py",
                    ])
                    if parser is None:
                        return {"ok": False, "error": "IR dump parser reference is missing"}
                    raw_ir = temporary / "fixture.ir"
                    json_ir = temporary / "fixture.ir.json"
                    raw_ir.write_bytes(ir_dump.stdout)
                    parsed = subprocess.run(
                        ["python3", str(parser), str(raw_ir), str(json_ir)],
                        cwd=ROOT,
                        capture_output=True,
                        timeout=30,
                    )
                    if parsed.returncode != 0 or not json_ir.is_file():
                        return {
                            "ok": False,
                            "error": "could not generate default IR JSON fixture",
                            "stderr": parsed.stderr.decode("utf-8", errors="replace"),
                        }
                    input_bytes = json_ir.read_bytes()
            common_input.write_bytes(input_bytes)

            compile_one = _run_result(
                [str(NQLC), str(nql_tool), "-o", str(binary_one)],
                timeout=60,
                capability=CAP_BUILD,
            )
            artifact_one = binary_one.read_bytes() if compile_one["ok"] else b""
            if compile_one["ok"]:
                binary_one.unlink()
            compile_two = _run_result(
                [str(NQLC), str(nql_tool), "-o", str(binary_one)],
                timeout=60,
                capability=CAP_BUILD,
            )
            if not compile_one["ok"] or not compile_two["ok"]:
                return {
                    "ok": False,
                    "error": "nqlc could not compile migration source",
                    "compile_one": compile_one,
                    "compile_two": compile_two,
                }

            artifact_two = binary_one.read_bytes()
            artifact_hash_one = hashlib.sha256(artifact_one).hexdigest()
            artifact_hash_two = hashlib.sha256(artifact_two).hexdigest()
            deterministic_artifact = (
                artifact_hash_one == artifact_hash_two
                and artifact_one == artifact_two
            )
            artifact_first_difference = next(
                (
                    index
                    for index, pair in enumerate(zip(artifact_one, artifact_two))
                    if pair[0] != pair[1]
                ),
                min(len(artifact_one), len(artifact_two))
                if len(artifact_one) != len(artifact_two)
                else None,
            )

            python_run = subprocess.run(
                ["python3", str(python_tool), str(common_input), str(common_output)],
                cwd=ROOT,
                capture_output=True,
                timeout=30,
            )
            python_output = common_output.read_bytes() if common_output.is_file() else b""
            try:
                common_output.unlink()
            except FileNotFoundError:
                pass

            nql_run = subprocess.run(
                [*_artifact_runner(binary_one), str(common_input), str(common_output)],
                cwd=ROOT,
                capture_output=True,
                timeout=30,
            )
            nql_output = common_output.read_bytes() if common_output.is_file() else b""

            exit_codes_identical = python_run.returncode == nql_run.returncode
            stdout_identical = python_run.stdout == nql_run.stdout
            stderr_identical = python_run.stderr == nql_run.stderr
            output_identical = python_output == nql_output
            ok = all((
                deterministic_artifact,
                exit_codes_identical,
                stdout_identical,
                stderr_identical,
                output_identical,
            ))
            stdout_text, stdout_truncated = _truncate_output(
                nql_run.stdout.decode("utf-8", errors="replace"),
                MAX_STDOUT_BYTES,
            )
            stderr_text, stderr_truncated = _truncate_output(
                nql_run.stderr.decode("utf-8", errors="replace"),
                MAX_STDERR_BYTES,
            )
            return {
                "ok": ok,
                "tool": canonical_name,
                "requested_name": tool_name,
                "python_reference": python_rel,
                "nql_source": nql_rel,
                "legacy_source_extension": nql_tool.suffix == ".nq",
                "python_exit_code": python_run.returncode,
                "nql_exit_code": nql_run.returncode,
                "exit_codes_identical": exit_codes_identical,
                "stdout_identical": stdout_identical,
                "stderr_identical": stderr_identical,
                "output_identical": output_identical,
                "output_size": len(nql_output),
                "output_sha256": hashlib.sha256(nql_output).hexdigest(),
                "deterministic_artifact": deterministic_artifact,
                "artifact_sha256": artifact_hash_one,
                "artifact_sha256_first": artifact_hash_one,
                "artifact_sha256_second": artifact_hash_two,
                "artifact_first_differing_offset": artifact_first_difference,
                "stdout": stdout_text.rstrip("\n"),
                "stderr": stderr_text.rstrip("\n"),
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "migration verification timed out",
            "duration_ms": round((time.monotonic() - started) * 1000),
        }
# ---------------------------------------------------------------------------
# Git lanjutan
# ---------------------------------------------------------------------------

@mcp.tool()
def git_tag(
    action: str = "list",
    name: str = "",
    message: str = "",
    confirm: bool = False,
) -> str:
    """
    Manage git tags.

    Args:
        action:  "list" show all tags, "create" create annotated tag,
                 "delete" delete a tag.
        name:    Tag name (required for create/delete).
        message: Tag message (for annotated tags, used with create).
    """
    if action == "delete" and not confirm:
        return "ERROR: DESTRUCTIVE operation requires confirm=true"
    if action == "list":
        return _run(["git", "tag", "--sort=-version:refname"], timeout=10)
    elif action == "create":
        if not name:
            return "ERROR: name diperlukan untuk create"
        cmd = ["git", "tag"]
        if message:
            cmd += ["-a", name, "-m", message]
        else:
            cmd.append(name)
        return _run(cmd, timeout=10)
    elif action == "delete":
        if not name:
            return "ERROR: name diperlukan untuk delete"
        return _run(["git", "tag", "-d", name], timeout=10)
    else:
        return f"ERROR: action tidak dikenal — '{action}'. Pilih: list, create, delete"


@mcp.tool()
def git_show(ref: str = "HEAD") -> str:
    """
    Show details of a specific commit.

    Args:
        ref: Commit reference (default: HEAD). Can be hash, branch, or tag.
    """
    return _run(
        ["git", "show", "--stat", "--oneline", ref],
        timeout=10,
    )


# ---------------------------------------------------------------------------
# Canonical MCP resources and workflow prompts
# ---------------------------------------------------------------------------

def _development_section(title: str) -> str:
    document = ROOT / DEVELOPMENT_DOCUMENT
    if not document.is_file():
        return f"ERROR: {document.name} is missing"
    text = document.read_text(encoding="utf-8", errors="replace")
    heading = re.search(r"^# " + re.escape(title) + r"[ \t]*$", text, re.MULTILINE)
    if heading is None:
        return f"ERROR: section not found: {title}"
    next_heading = text.find("\n# ", heading.end())
    end = len(text) if next_heading < 0 else next_heading
    section = text[heading.start():end]
    rendered, _ = _truncate_output(section.rstrip() + "\n", MAX_TOOL_OUTPUT_BYTES)
    return rendered


@mcp.resource(
    "nolqu://architecture",
    name="NolQu-L Canonical Architecture",
    mime_type="text/markdown",
)
def architecture_resource() -> str:
    """Canonical compiler chain with no hidden host compiler stage."""
    status = canonical_bootstrap_status()
    return (
        "# NolQu-L Canonical Architecture\n\n"
        "```text\n"
        "Machine-Level Foundation\n"
        "        ↓\n"
        "Stage 0\n"
        "        ↓\n"
        "NolQu-L Bootstrap Compiler B0\n"
        "        ↓\n"
        "NolQu-L Core Compiler C0\n"
        "        ↓\n"
        "Full NolQu-L Compiler\n"
        "        ↓\n"
        "Self-Hosting nqlc\n"
        "        ↓\n"
        "Verified nqlc\n"
        "```\n\n"
        "Reference Compiler R0, LLVM, Python, NASM, and other host tools are "
        "not canonical stages.\n\n"
        f"Current structured status:\n```json\n{json.dumps(status, indent=2)}\n```\n"
    )


@mcp.resource("nolqu://nine-pillars", mime_type="text/markdown")
def nine_pillars_resource() -> str:
    """The binding Nine Pillars section from the development authority."""
    return _development_section("1. NINE PILLARS OF NOLQU-L")


@mcp.resource("nolqu://bootstrap", mime_type="text/markdown")
def bootstrap_resource() -> str:
    """Canonical bootstrap contracts and current verified stage state."""
    readme = ROOT / "bootstrap/README.md"
    content = readme.read_text(encoding="utf-8", errors="replace") if readme.is_file() else ""
    rendered, _ = _truncate_output(content, MAX_TOOL_OUTPUT_BYTES)
    return rendered


@mcp.resource("nolqu://grammar", mime_type="text/markdown")
def grammar_resource() -> str:
    """Canonical lexer and parser direction from the development authority."""
    return _development_section("7. LEXER") + "\n" + _development_section("8. PARSER")


@mcp.resource("nolqu://ir", mime_type="text/markdown")
def ir_resource() -> str:
    """Canonical NolQu IR design section."""
    return _development_section("12. NOLQU IR")


@mcp.resource("nolqu://abi", mime_type="text/markdown")
def abi_resource() -> str:
    """Canonical FFI and ABI design section."""
    return _development_section("33. FFI DAN ABI")


@mcp.resource("nolqu://diagnostics", mime_type="text/markdown")
def diagnostics_resource() -> str:
    """Canonical diagnostic-system design section."""
    return _development_section("39. DIAGNOSTIC SYSTEM")


@mcp.resource("nolqu://current-development", mime_type="text/markdown")
def current_development_resource() -> str:
    """Current C0 milestone, measured blocker, and bootstrap state."""
    metadata = canonical_bootstrap_status()
    metadata["fresh_probe_required"] = "run_c0_probe (BUILD); no compilation is performed by this resource"
    return (
        "# Current NolQu-L Development\n\n"
        f"```json\n{json.dumps(metadata, indent=2)}\n```\n\n"
        + _development_section("CURRENT ARCHITECTURE RESET")
    )


@mcp.prompt(name="develop_c0_milestone")
def develop_c0_milestone() -> str:
    """Official bounded workflow for the next measured C0 milestone."""
    return (
        "Read nolqu://current-development and run current_c0_blocker. "
        "Treat the first measured blocker as the only new semantic target. "
        "Write a failing gate, implement the smallest bounded subset, and do "
        "not alter B0 unless a measured capacity limit requires it. Do not "
        "generalize beyond evidence. Rebuild predecessor and successor twice, "
        "compare bytes, rerun the probe, run bootstrap tests, then update "
        f"{DEVELOPMENT_DOCUMENT} with only verified facts."
    )


@mcp.prompt(name="investigate_regression")
def investigate_regression() -> str:
    """Official regression investigation workflow."""
    return (
        "Stop feature work. Reproduce the failing test unchanged, identify the "
        "first bad stage and smallest causal change, add a focused regression "
        "gate, fix the root cause, then run the affected stage plus the full "
        "previously-green suite. Do not relabel a pre-existing failure as a "
        "new regression."
    )


@mcp.prompt(name="review_codegen")
def review_codegen() -> str:
    """Official machine-code review workflow."""
    return (
        "Review emitted bytes, register and stack discipline, rel32 targets, "
        "syscall ABI, RX/RW permissions, bounds, and every error edge. Verify "
        "behavior with executable gates and disassembly; do not infer machine "
        "correctness from source shape alone."
    )


@mcp.prompt(name="bootstrap_audit")
def bootstrap_audit() -> str:
    """Official canonical bootstrap audit workflow."""
    return (
        "Run canonical_bootstrap_status, verify_bootstrap_hashes, and inspect "
        "each artifact with bootstrap_artifact_info. Rebuild machine, Stage 0, "
        "B0, and C0 in order. Reject any hidden compiler, assembler, linker, "
        "Python, or LLVM dependency in the canonical chain."
    )


@mcp.prompt(name="prepare_release")
def prepare_release() -> str:
    """Official release verification workflow."""
    return (
        "Verify VERSION and CHANNEL, run MCP self-test, canonical bootstrap "
        "tests, Reference R0 regression tests, release-check, deterministic "
        "artifact hashes, and working-tree review. Report unsupported canonical "
        "stages explicitly; never promote Reference R0 to self-hosted status."
    )

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
