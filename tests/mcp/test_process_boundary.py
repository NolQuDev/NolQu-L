"""Real subprocess regressions; a separate fixture guardian cleans even RED runs."""

import ctypes
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock


MCP_SOURCE = Path(__file__).resolve().parents[2] / "tools/nolqu_mcp.py"
PROTOCOL_INPUT = b"PRIVATE-MCP-PROTOCOL-LINE\n"
TREE_SOURCE = r'''
import json, os, pathlib, signal, sys, time
root, role, grouping, resistant = sys.argv[1:]
root = pathlib.Path(root)
def node(role):
    if role != "parent":
        if grouping == "group":
            os.setpgid(0, 0)
        elif grouping in {"session", "session-pipes"}:
            os.setsid()
        if grouping != "session-pipes":
            descriptor = os.open(os.devnull, os.O_RDWR)
            for target in (0, 1, 2):
                os.dup2(descriptor, target)
            os.close(descriptor)
    if resistant == "yes":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    record = {"pid": os.getpid(), "pgid": os.getpgrp(), "sid": os.getsid(0)}
    temporary = root / (role + ".tmp")
    temporary.write_text(json.dumps(record))
    temporary.replace(root / (role + ".json"))
    if role != "grandchild":
        if os.fork() == 0:
            node("child" if role == "parent" else "grandchild")
            os._exit(0)
        if role == "child" and resistant == "orphan":
            os._exit(0)
    if role == "parent":
        while not (root / "grandchild.json").exists():
            time.sleep(0.005)
        print("partial-out-" + "x" * 1024 + "-out-tail", flush=True)
        print("partial-err-" + "y" * 1024 + "-err-tail", file=sys.stderr, flush=True)
        if resistant == "exit-parent":
            os._exit(0)
    time.sleep(30)
node(role)
'''


def _descendants():
    """Only used by the isolated fixture guardian, never the imported MCP."""
    parents = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            parents[int(path.parent.name)] = int(fields[1])
        except (OSError, ValueError, IndexError):
            continue
    owned = {os.getpid()}
    while True:
        found = {pid for pid, parent in parents.items() if parent in owned}
        if found <= owned:
            return owned - {os.getpid()}
        owned.update(found)


def _guard(case, root):
    # Adoption is confined to this disposable fixture process. The MCP runner
    # below starts with normal child ownership and must leave it unchanged.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0):
        raise OSError(ctypes.get_errno(), "fixture subreaper setup failed")
    child = subprocess.Popen(
        [sys.executable, "-B", __file__, "--case", case, str(root)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    killed, reaped = set(), set()
    try:
        try:
            stdout, stderr = child.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            child.kill()
    finally:
        deadline = time.monotonic() + 3
        remaining = set()
        while time.monotonic() < deadline:
            remaining = _descendants()
            for pid in remaining:
                try:
                    os.kill(pid, signal.SIGKILL)
                    killed.add(pid)
                except ProcessLookupError:
                    pass
            while True:
                try:
                    pid, wait_status = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    break
                if pid == 0:
                    break
                if pid == child.pid:
                    child.returncode = os.waitstatus_to_exitcode(wait_status)
                reaped.add(pid)
            if not _descendants():
                remaining = set()
                break
            time.sleep(0.01)
        (root / "fixture-cleanup.json").write_text(json.dumps({
            "killed": sorted(killed), "reaped": sorted(reaped),
            "remaining": sorted(remaining),
        }))
    stdout, stderr = child.communicate(timeout=2)
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    return child.returncode


def _load(root):
    os.environ["NOLQU_ROOT"] = str(root)
    spec = importlib.util.spec_from_file_location("process_boundary_mcp", MCP_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._git_head = lambda: None
    return module


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _ownership():
    value = ctypes.c_int()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(37, ctypes.byref(value), 0, 0, 0):
        raise OSError(ctypes.get_errno(), "fixture subreaper query failed")
    return value.value


def _case(case, root):
    mcp = _load(root)
    if case.startswith("libc-"):
        original = mcp._process_supervisor_source
        prefix = ("import os,signal\nfor owner,name in ((os,'pidfd_open'),(signal,'pidfd_send_signal')):\n"
                  " if hasattr(owner,name): delattr(owner,name)\n")
        if case == "libc-unavailable":
            prefix += '''import ctypes
real_cdll = ctypes.CDLL
class WithoutPidfds:
 def __init__(self, library): self.library = library
 def __getattr__(self, name):
  if name in ('pidfd_open','pidfd_send_signal'): raise AttributeError(name)
  return getattr(self.library, name)
ctypes.CDLL = lambda *args, **kwargs: WithoutPidfds(real_cdll(*args, **kwargs))
'''
        mcp._process_supervisor_source = lambda: prefix + original()
        case = case[5:]
    run = mcp._run_result
    python = [sys.executable, "-c"]
    before = _ownership()
    if case == "unavailable":
        marker = root / "unexpected-command"
        result = run(python + ["from pathlib import Path;Path(" + repr(str(marker)) + ").write_text('ran')"])
        return {"result": result, "command_started": marker.exists()}
    if case == "stdin":
        result = run(python + ["import sys; print(sys.stdin.buffer.read().hex())"])
        return {"result": result, "protocol_left": os.read(0, 4096).hex()}
    if case == "explicit":
        inputs = ["hello \u2603\n", b"\x00\xffbytes\n", "", b""]
        return [run(python + ["import sys; print(sys.stdin.buffer.read().hex())"], stdin=data)
                for data in inputs]
    if case == "ordinary":
        cmd = python + ["import os,sys,time; time.sleep(.05); "
                        "print(os.getcwd()); print(os.environ['BOUNDARY_VALUE']); "
                        "sys.stderr.buffer.write(b'err\\xff\\n'); sys.exit(7)"]
        failed = run(cmd, env={"BOUNDARY_VALUE": "literal value"},
                     capability=mcp.CAP_READ_ONLY, artifacts=["artifact"], changed_files=["changed"])
        passed = run(python + ["print('ok\\n')"])
        events = [json.loads(line) for line in mcp.AUDIT_PATH.read_text().splitlines()]
        return {"failed": failed, "passed": passed, "events": events, "command": cmd}
    if case == "os-errors":
        missing = run([str(root / "missing")])
        blocked = root / "blocked"
        blocked.write_text("cannot execute")
        blocked.chmod(0o644)
        denied = run([str(blocked)])
        return [missing, denied]
    if case == "late-output":
        child_code = "import sys,time; time.sleep(.3); print('late-out'); print('late-err', file=sys.stderr)"
        parent_code = ("import subprocess,sys; subprocess.Popen([sys.executable,'-c',"
                       + repr(child_code) + "],start_new_session=True); print('parent',flush=True)")
        return run(python + [parent_code], timeout=5)
    if case == "startup-deferred":
        # Interrupt Thread.start after the OS thread exists but before its
        # acquisition callback commits. Releasing it after cancellation must
        # never let a command start later.
        release, waiting = threading.Event(), threading.Event()
        original_start, original_run = threading.Thread.start, threading.Thread.run
        started_threads = []
        process = subprocess.Popen.__new__(subprocess.Popen)
        marker = root / "unexpected-command"
        handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, [])

        def deferred_run(thread):
            waiting.set()
            release.wait(timeout=5)
            original_run(thread)

        def interrupted_start(thread):
            original_start(thread)
            started_threads.append(thread)
            if not waiting.wait(timeout=2):
                raise RuntimeError("deferred acquisition thread did not start")
            os.kill(os.getpid(), signal.SIGINT)

        try:
            with mock.patch.object(threading.Thread, "run", deferred_run), mock.patch.object(
                    threading.Thread, "start", interrupted_start):
                mcp._acquire_process_supervisor(
                    process, python + ["from pathlib import Path; import sys,time; "
                                       "Path(sys.argv[1]).write_text('unexpected'); time.sleep(30)", str(marker)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
            outcome = {"raised": None}
        except BaseException as exc:
            outcome = {"raised": type(exc).__name__, "message": str(exc)}
        finally:
            release.set()
            for thread in started_threads:
                thread.join(timeout=2)
        outcome.update(pid=getattr(process, "pid", None), command_started=marker.exists(),
                       threads_alive=[thread.is_alive() for thread in started_threads],
                       ownership_before=before, ownership_after=_ownership(),
                       signal_handlers_preserved=handlers == {sig: signal.getsignal(sig) for sig in handlers},
                       signal_mask_preserved=mask == signal.pthread_sigmask(signal.SIG_BLOCK, []))
        return outcome

    fixture = root / "tree.py"
    fixture.write_text(TREE_SOURCE)
    startup = case.startswith("startup-")
    grouping = {"groups": "group", "sessions": "session", "orphan": "session",
                "pipe-timeout": "session-pipes"}.get(case, "same")
    if startup:
        grouping = "session"
    resistant = "yes" if case in {"resistant", "interrupt", "exception", "io-error", "cleanup-error", "system-exit"} else "no"
    if startup:
        resistant = "yes"
    if case == "orphan":
        resistant = "orphan"
    elif case == "pipe-timeout":
        resistant = "exit-parent"
    cmd = [sys.executable, str(fixture), str(root), "parent", grouping, resistant]
    # Both a running sibling and a waitable, exited sibling must remain owned
    # by the caller. Reaping with waitpid(-1) in the server would steal the latter.
    unrelated = subprocess.Popen(python + ["import time; time.sleep(30)"],
                                 stdin=subprocess.DEVNULL, start_new_session=True)
    waitable = subprocess.Popen(python + ["raise SystemExit(23)"], stdin=subprocess.DEVNULL)
    seen = []
    acquired = []
    popen = subprocess.Popen
    original_init = popen.__init__
    injection = {}
    handlers_before = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    mask_before = signal.pthread_sigmask(signal.SIG_BLOCK, [])

    def record_init(process, *args, **kwargs):
        original_init(process, *args, **kwargs)
        seen.append(process.pid)
        acquired.append(process)
        if case in {"startup-constructor-signal", "startup-constructor-error"}:
            ready()
            injection["boundary"] = "launched constructor before normal return"
            if case == "startup-constructor-error":
                error = KeyboardInterrupt("startup constructor interruption")
                injection["exception"] = error
                raise error
            os.kill(os.getpid(), signal.SIGINT)

    def ready():
        deadline = time.monotonic() + 5
        while not (root / "grandchild.json").is_file():
            if time.monotonic() >= deadline:
                raise RuntimeError("fixture did not become ready")
            time.sleep(0.005)

    original_communicate = subprocess.Popen.communicate
    injected = False

    def communicate(process, *args, **kwargs):
        nonlocal injected
        if injected and case == "cleanup-error":
            raise OSError(5, "fixture cleanup read failed")
        if not injected:
            injected = True
            ready()
            if case == "io-error":
                raise OSError(5, "fixture I/O failure")
            if case == "cleanup-error":
                raise KeyboardInterrupt("original fixture interruption")
            if case == "system-exit":
                raise SystemExit(19)
            raise RuntimeError("fixture communication interruption")
        return original_communicate(process, *args, **kwargs)

    interrupted = threading.Event()

    def interrupt():
        ready()
        if not interrupted.is_set():
            os.kill(os.getpid(), signal.SIGINT)

    def startup_trace(frame, event, arg):
        if frame.f_code is mcp._run_process.__code__ and event == "line" and not injection:
            process = frame.f_locals.get("process")
            if process is not None and getattr(process, "pid", None) is not None:
                ready()
                injection["boundary"] = "first caller line after launched process is visible"
                injection["line"] = frame.f_lineno
                os.kill(os.getpid(), signal.SIGINT)
        return startup_trace

    mcp.MAX_STDOUT_BYTES = 96
    mcp.MAX_STDERR_BYTES = 96
    started = time.monotonic()
    try:
        with mock.patch.object(popen, "__init__", record_init):
            if startup:
                if case == "startup-registration":
                    sys.settrace(startup_trace)
                try:
                    result = run(cmd, timeout=20)
                finally:
                    sys.settrace(None)
            elif case in {"exception", "io-error", "cleanup-error", "system-exit"}:
                with mock.patch.object(popen, "communicate", communicate):
                    result = run(cmd, timeout=6)
            elif case == "interrupt":
                thread = threading.Thread(target=interrupt, daemon=True)
                thread.start()
                try:
                    result = run(cmd, timeout=6)
                finally:
                    interrupted.set()
                    thread.join(timeout=1)
            elif case == "concurrent":
                with ThreadPoolExecutor(max_workers=1) as pool:
                    other = pool.submit(run, python + ["import time; time.sleep(2.5); print('independent')"], timeout=6)
                    result = run(cmd, timeout=1.5)
                    concurrent_result = other.result(timeout=8)
            else:
                result = run(cmd, timeout=1.5)
        outcome = {"result": result}
        if case == "concurrent":
            outcome["concurrent_result"] = concurrent_result
    except BaseException as exc:
        outcome = {"raised": type(exc).__name__, "message": str(exc)}
        if "exception" in injection:
            outcome["original_exception_preserved"] = exc is injection["exception"]
    elapsed = time.monotonic() - started
    records = [json.loads((root / (role + ".json")).read_text())
               for role in ("parent", "child", "grandchild")]
    direct_reaped = []
    for pid in seen:
        try:
            os.waitpid(pid, os.WNOHANG)
            direct_reaped.append(False)
        except ChildProcessError:
            direct_reaped.append(True)
    try:
        outcome.update(elapsed=elapsed, records=records,
                       alive=[_alive(record["pid"]) for record in records],
                       direct_reaped=direct_reaped, unrelated_alive=unrelated.poll() is None,
                       waitable_status=waitable.wait(timeout=2),
                       ownership_before=before, ownership_after=_ownership())
        if startup:
            outcome.update(
                injection={key: value for key, value in injection.items() if key != "exception"},
                supervisor_alive=[_alive(pid) for pid in seen],
                pipes_closed=all(stream is None or stream.closed for process in acquired
                                 for stream in (process.stdin, process.stdout, process.stderr)),
                signal_handlers_preserved=handlers_before == {sig: signal.getsignal(sig) for sig in handlers_before},
                signal_mask_preserved=mask_before == signal.pthread_sigmask(signal.SIG_BLOCK, []),
            )
    finally:
        unrelated.kill()
        unrelated.wait(timeout=2)
    return outcome


@unittest.skipUnless(sys.platform in ("linux", "android"), "Linux process ownership boundary")
class ProcessBoundaryTests(unittest.TestCase):
    def libc_case(self, case):
        # Python can expose pidfds on Linux even when an older libc does not.
        # Such hosts must reject the forced-libc path before target launch.
        libc = ctypes.CDLL(None, use_errno=True)
        if all(hasattr(libc, name) for name in ("pidfd_open", "pidfd_send_signal")):
            return self.isolated(case)
        self.assert_pidfds_unavailable(self.isolated("libc-unavailable"))
        return None

    def test_libc_pidfds_work_without_python_bindings(self):
        observed = self.libc_case("libc-stdin")
        if observed is None:
            return
        self.assertTrue(observed["result"]["ok"], observed)
        self.assertEqual(observed["result"]["stdout"], "")
        self.assertEqual(observed["protocol_left"], PROTOCOL_INPUT.hex())

    def test_libc_pidfds_retain_owned_timeout_cleanup(self):
        observed = self.libc_case("libc-timeout")
        if observed is None:
            return
        self.assertTrue(observed["result"]["timed_out"], observed)
        self.assertFalse(observed["result"]["ok"], observed)
        self.assert_clean(observed)

    def test_missing_pidfds_still_block_before_target_launch(self):
        self.assert_pidfds_unavailable(self.isolated("libc-unavailable"))

    def assert_pidfds_unavailable(self, observed):
        self.assertFalse(observed["result"]["ok"], observed)
        self.assertIn("pidfd", observed["result"]["stderr"])
        self.assertFalse(observed["command_started"])

    def isolated(self, case):
        with tempfile.TemporaryDirectory(prefix="nolqu-process-boundary-") as directory:
            root = Path(directory)
            completed = subprocess.run(
                [sys.executable, "-B", __file__, "--guard", case, directory],
                input=PROTOCOL_INPUT, capture_output=True, timeout=40,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            cleanup = json.loads((root / "fixture-cleanup.json").read_text())
            evidence = os.environ.get("NOLQU_PROCESS_TEST_RECEIPTS")
            if evidence:
                saved = Path(tempfile.mkdtemp(prefix=case + "-", dir=evidence))
                (saved / "stdout").write_bytes(completed.stdout)
                (saved / "stderr").write_bytes(completed.stderr)
                (saved / "fixture-cleanup.json").write_text(json.dumps(cleanup, indent=2))
            self.assertEqual(cleanup["remaining"], [], cleanup)
            self.assertEqual(completed.returncode, 0, completed.stderr.decode(errors="replace"))
            return json.loads(completed.stdout)

    def assert_clean(self, observed):
        self.assertEqual(observed["alive"], [False, False, False], observed)
        self.assertTrue(observed["direct_reaped"], observed)
        self.assertTrue(all(observed["direct_reaped"]), observed)
        self.assertTrue(observed["unrelated_alive"], observed)
        self.assertEqual(observed["waitable_status"], 23, observed)
        self.assertEqual(observed["ownership_before"], 0, observed)
        self.assertEqual(observed["ownership_after"], 0, observed)
        self.assertLess(observed["elapsed"], 6, observed)

    def test_no_input_receives_eof_and_preserves_protocol_stdin(self):
        observed = self.isolated("stdin")
        self.assertTrue(observed["result"]["ok"], observed)
        self.assertEqual(observed["result"]["stdout"], "", observed)
        self.assertEqual(observed["protocol_left"], PROTOCOL_INPUT.hex(), observed)

    def test_explicit_text_bytes_and_empty_input_are_preserved(self):
        results = self.isolated("explicit")
        for result, expected in zip(results, ["68656c6c6f20e298830a", "00ff62797465730a", "", ""]):
            with self.subTest(expected=expected):
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["stdout"], expected, result)

    def test_success_nonzero_status_environment_cwd_and_audit(self):
        observed = self.isolated("ordinary")
        failed, passed = observed["failed"], observed["passed"]
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["exit_code"], 7)
        self.assertTrue(failed["stdout"].endswith("\nliteral value"), failed)
        expected_prefix = str(Path(tempfile.gettempdir()).resolve() / "nolqu-process-boundary-")
        self.assertTrue(failed["stdout"].startswith(expected_prefix), failed)
        self.assertEqual(failed["stderr"], "err\ufffd")
        self.assertEqual(failed["command"], observed["command"])
        self.assertEqual(failed["capability"], "READ_ONLY")
        self.assertEqual(failed["artifacts"], ["artifact"])
        self.assertEqual(failed["changed_files"], ["changed"])
        self.assertGreaterEqual(failed["duration_ms"], 50)
        self.assertFalse(failed["timed_out"])
        self.assertTrue(passed["ok"])
        self.assertEqual(passed["stdout"], "ok")
        self.assertEqual(passed["exit_code"], 0)
        self.assertEqual(len(observed["events"]), 2)
        for event, result in zip(observed["events"], [failed, passed]):
            for key in ("exit_code", "ok", "capability", "duration_ms", "artifacts", "changed_files"):
                self.assertEqual(event[key], result[key])
            self.assertIsNone(event["git_head_before"])
            self.assertIsNone(event["git_head_after"])

    def test_missing_and_permission_errors_remain_structured(self):
        missing, denied = self.isolated("os-errors")
        for result in (missing, denied):
            self.assertFalse(result["ok"], result)
            self.assertIsNone(result["exit_code"])
            self.assertFalse(result["timed_out"])
            self.assertEqual(result["stdout"], "")
        self.assertIn("command not found", missing["stderr"])
        self.assertIn("permission denied", denied["stderr"].lower())

    def test_success_retains_late_output_after_direct_child_exits(self):
        result = self.isolated("late-output")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["exit_code"], 0, result)
        self.assertEqual(result["stdout"], "parent\nlate-out", result)
        self.assertEqual(result["stderr"], "late-err", result)

    def test_timeout_waits_for_descendant_pipes_after_direct_child_exits(self):
        observed = self.isolated("pipe-timeout")
        self.assertTrue(observed["result"]["timed_out"], observed)
        self.assertFalse(observed["result"]["ok"], observed)
        self.assertGreaterEqual(observed["result"]["duration_ms"], 1500, observed)
        self.assertIn("partial-out-", observed["result"]["stdout"])
        self.assert_clean(observed)

    def test_timeout_terminates_child_and_grandchild(self):
        observed = self.isolated("timeout")
        self.assertTrue(observed["result"]["timed_out"], observed)
        self.assertFalse(observed["result"]["ok"])
        self.assertIsNone(observed["result"]["exit_code"])
        self.assert_clean(observed)

    def test_timeout_terminates_nested_process_groups(self):
        observed = self.isolated("groups")
        self.assertEqual(len({item["pgid"] for item in observed["records"]}), 3)
        self.assert_clean(observed)

    def test_timeout_terminates_nested_sessions(self):
        observed = self.isolated("sessions")
        self.assertEqual(len({item["sid"] for item in observed["records"]}), 3)
        self.assert_clean(observed)

    def test_timeout_terminates_adopted_grandchild_in_another_session(self):
        observed = self.isolated("orphan")
        self.assertEqual(len({item["sid"] for item in observed["records"]}), 3)
        self.assert_clean(observed)

    def test_timeout_does_not_kill_or_reap_a_concurrent_command(self):
        observed = self.isolated("concurrent")
        self.assertTrue(observed["concurrent_result"]["ok"], observed)
        self.assertEqual(observed["concurrent_result"]["stdout"], "independent", observed)
        self.assertEqual(len(observed["direct_reaped"]), 2, observed)
        self.assert_clean(observed)

    def test_timeout_escalates_for_term_resistant_tree(self):
        self.assert_clean(self.isolated("resistant"))

    def test_timeout_retains_bounded_partial_output_and_diagnosis(self):
        observed = self.isolated("timeout")
        result = observed["result"]
        self.assertTrue(result["stdout_truncated"], result)
        self.assertTrue(result["stderr_truncated"], result)
        self.assertIn("partial-out-", result["stdout"])
        self.assertIn("-out-tail", result["stdout"])
        self.assertIn("partial-err-", result["stderr"])
        self.assertIn("-err-tail", result["stderr"])
        self.assertIn("timed out after 1.5s", result["stderr"])
        self.assert_clean(observed)

    def test_keyboard_interrupt_cleans_tree_and_propagates(self):
        observed = self.isolated("interrupt")
        self.assertEqual(observed.get("raised"), "KeyboardInterrupt", observed)
        self.assert_clean(observed)

    def test_communication_exception_cleans_tree_and_propagates(self):
        observed = self.isolated("exception")
        self.assertEqual(observed.get("raised"), "RuntimeError", observed)
        self.assertEqual(observed.get("message"), "fixture communication interruption", observed)
        self.assert_clean(observed)

    def test_communication_os_error_cleans_tree_before_structured_error(self):
        observed = self.isolated("io-error")
        self.assertIn("fixture I/O failure", observed["result"]["stderr"])
        self.assertFalse(observed["result"]["ok"])
        self.assert_clean(observed)

    def test_cleanup_io_failure_does_not_replace_keyboard_interrupt(self):
        observed = self.isolated("cleanup-error")
        self.assertEqual(observed.get("raised"), "KeyboardInterrupt", observed)
        self.assertEqual(observed.get("message"), "original fixture interruption", observed)
        self.assert_clean(observed)

    def test_system_exit_cleans_tree_and_propagates(self):
        observed = self.isolated("system-exit")
        self.assertEqual(observed.get("raised"), "SystemExit", observed)
        self.assertEqual(observed.get("message"), "19", observed)
        self.assert_clean(observed)

    def assert_startup_clean(self, case):
        observed = self.isolated(case)
        self.assertEqual(observed.get("raised"), "KeyboardInterrupt", observed)
        self.assertTrue(observed.get("injection"), observed)
        self.assert_clean(observed)
        self.assertEqual(observed["supervisor_alive"], [False], observed)
        self.assertTrue(observed["pipes_closed"], observed)
        self.assertTrue(observed["signal_handlers_preserved"], observed)
        self.assertTrue(observed["signal_mask_preserved"], observed)
        return observed

    def test_startup_interrupt_after_launch_cleans_registered_supervisor(self):
        self.assert_startup_clean("startup-registration")

    def test_startup_sigint_before_constructor_returns_cleans_owned_tree(self):
        self.assert_startup_clean("startup-constructor-signal")

    def test_startup_constructor_exception_preserves_original_and_cleans_tree(self):
        observed = self.assert_startup_clean("startup-constructor-error")
        self.assertEqual(observed["message"], "startup constructor interruption", observed)
        self.assertTrue(observed["original_exception_preserved"], observed)

    def test_startup_interrupt_closes_gate_before_deferred_acquisition(self):
        observed = self.isolated("startup-deferred")
        self.assertEqual(observed["raised"], "KeyboardInterrupt", observed)
        self.assertIsNone(observed["pid"], observed)
        self.assertFalse(observed["command_started"], observed)
        self.assertEqual(observed["threads_alive"], [False], observed)
        self.assertEqual(observed["ownership_before"], 0, observed)
        self.assertEqual(observed["ownership_after"], 0, observed)
        self.assertTrue(observed["signal_handlers_preserved"], observed)
        self.assertTrue(observed["signal_mask_preserved"], observed)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--guard":
        raise SystemExit(_guard(sys.argv[2], Path(sys.argv[3])))
    if len(sys.argv) == 4 and sys.argv[1] == "--case":
        print(json.dumps(_case(sys.argv[2], Path(sys.argv[3]))))
    else:
        unittest.main()
