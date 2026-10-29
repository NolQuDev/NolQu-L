"""Linux host-test runner; never part of the canonical compiler pipeline.

Wall time and regular-file output are bounded. No address-space limit is
claimed: QEMU reserves a guest address space independently of physical RSS.
Each invocation is attempted once and retains its exact input and streams.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import time


# A dedicated Linux subreaper owns only this invocation, not the unittest
# process's unrelated children. All target descendants are reaped before the
# supervisor exits and captured streams are hashed. This is lifecycle control,
# not an OS sandbox. The target stays in the supervisor's disposable session.
_SUPERVISOR = r'''
import ctypes,json,os,pathlib,resource,signal,subprocess,sys
libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(36,1,0,0,0) != 0:
    raise OSError(ctypes.get_errno(), 'cannot enable child subreaper')
status_path=pathlib.Path(sys.argv[1])
target=None
record={'complete':False,'target_exit_code':None,'reaped_descendants':0}
def save():
    staging=status_path.with_suffix('.pending')
    staging.write_text(json.dumps(record))
    staging.replace(status_path)
def cancel(signum,frame):
    raise InterruptedError('supervisor cancelled')
signal.signal(signal.SIGTERM,cancel)
signal.signal(signal.SIGINT,cancel)
try:
    target=subprocess.Popen(sys.argv[2:])
    record['target_pid']=target.pid
    save()
    # Reap adopted exited children while the target is alive too. Blocking
    # only on target.wait() retains their zombies for the target's lifetime.
    while True:
        pid,status=os.waitpid(-1,0)
        if pid == target.pid:
            target.returncode=os.waitstatus_to_exitcode(status)
            record['target_exit_code']=target.returncode
            break
        record['reaped_descendants']+=1
except BaseException as exc:
    record['interrupted']=type(exc).__name__
finally:
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    signal.signal(signal.SIGINT,signal.SIG_IGN)
    if target is not None:
        if target.poll() is None:
            target.kill()
        record['target_exit_code']=target.wait()
    while True:
        try:
            pid,_=os.waitpid(-1,os.WNOHANG)
        except ChildProcessError:
            break
        if pid:
            record['reaped_descendants']+=1
            continue
        # Every PID is an unreaped direct child of this private subreaper;
        # exited descendants cannot have their PID reused before waitpid.
        # /proc/PID/task/PID/children is absent on the tested proot host.
        for path in pathlib.Path('/proc').glob('[0-9]*/stat'):
            try:
                fields=path.read_text().rsplit(')',1)[1].split()
                if int(fields[1]) == os.getpid():
                    os.kill(int(path.parent.name),signal.SIGKILL)
            except (OSError,ValueError,IndexError):
                pass
        try:
            os.waitpid(-1,0)
            record['reaped_descendants']+=1
        except ChildProcessError:
            break
    # This private supervisor owns one invocation. Account only after cleanup;
    # Linux maxrss is the largest waited child's KiB high-water mark, not a
    # simultaneous tree peak, virtual memory size or signal-cause attribution.
    usage={'available':False,'source':'getrusage(RUSAGE_CHILDREN)'}
    try:
        counters=resource.getrusage(resource.RUSAGE_CHILDREN)
        usage.update(available=True,user_cpu_seconds=counters.ru_utime,
                     system_cpu_seconds=counters.ru_stime,maxrss_kib=counters.ru_maxrss)
    except (AttributeError,OSError) as error:
        usage['error']={'type':type(error).__name__,'errno':getattr(error,'errno',None),
                        'message':str(error)}
    record['waited_child_usage']=usage
    record['complete']=True
    save()
'''


class AssuranceFailure(RuntimeError):
    pass


def _read_supervisor_control(path):
    """Read the small private protocol without blocking on special files."""
    limit = 4096
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("supervisor control must be a regular file")
        if info.st_size > limit:
            raise ValueError("supervisor control exceeds 4096 bytes")
        payload = bytearray()
        while len(payload) <= limit:
            chunk = os.read(descriptor, limit + 1 - len(payload))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) > limit:
            raise ValueError("supervisor control exceeds 4096 bytes")
    finally:
        os.close(descriptor)
    control = json.loads(payload.decode("utf-8"))
    if not isinstance(control, dict) or type(control.get("complete")) is not bool \
            or "target_exit_code" not in control \
            or type(control["target_exit_code"]) not in (int, type(None)):
        raise ValueError("invalid supervisor control object or status fields")
    return control


class _CancellationGuard:
    """Main-thread abort signals wait until the process handle is registered.

    Python signal handlers must not raise inside Popen after fork but before
    the caller receives its handle. During cleanup, further aborts are deferred
    until children are reaped and failure evidence has been persisted.
    """
    def __enter__(self):
        self.registered = False
        self.cleaning = False
        self.pending = []
        self.seen = []
        self.previous = {}
        try:
            for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
                self.previous[number] = signal.getsignal(number)
                signal.signal(number, self.handle)
        except BaseException:
            for number, handler in self.previous.items():
                signal.signal(number, handler)
            raise
        return self

    def handle(self, number, frame):
        self.seen.append(number)
        self.pending.append(number)
        if self.registered and not self.cleaning:
            self.raise_pending()

    def mark_registered(self):
        self.registered = True
        self.raise_pending()

    def defer(self):
        self.cleaning = True

    def raise_pending(self):
        if self.pending:
            number = self.pending.pop(0)
            raise KeyboardInterrupt(f"assurance cancelled by signal {number}")

    def __exit__(self, kind, value, traceback):
        for number, handler in self.previous.items():
            signal.signal(number, handler)
        if kind is None:
            self.raise_pending()


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: bytes
    stderr: bytes


class BoundedRunner:
    def __init__(self, directory, *, timeout=5.0, budget=300.0,
                 output_limit=8 * 1024 * 1024, max_input=3 * 1024 * 1024):
        if timeout <= 0 or budget <= 0 or output_limit <= 0 or max_input < 0:
            raise ValueError("invalid assurance limits")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.timeout = timeout
        self.deadline = time.monotonic() + budget
        self.output_limit = output_limit
        self.max_input = max_input
        self.records = []
        self.limits = dict(per_process_seconds=timeout, total_seconds=budget,
                           output_bytes_per_stream=output_limit,
                           input_bytes=max_input, address_space_bytes=None,
                           memory_limit_reason="QEMU virtual mapping is not physical RSS")

    @staticmethod
    def identity(path):
        data = Path(path).read_bytes()
        return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

    def run(self, label, command, data):
        with _CancellationGuard() as cancellation:
            return self._run(label, command, data, cancellation)

    def _run(self, label, command, data, cancellation):
        if len(data) > self.max_input:
            raise AssuranceFailure(f"{label}: input limit exceeded before execution")
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise AssuranceFailure(f"{label}: total time budget exhausted")
        timeout = min(self.timeout, remaining)
        ordinal = f"{len(self.records) + 1:04d}"
        paths = {name: self.directory / f"{ordinal}.{name}"
                 for name in ("input", "stdout", "stderr")}
        paths["input"].write_bytes(data)
        limit = self.output_limit

        def limits():
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
            cpu = max(1, math.ceil(timeout) + 1)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))

        record = dict(label=label, argv=[os.fspath(arg) for arg in command],
                      timeout_seconds=timeout, timed_out=False, cancelled=False)
        control_path = self.directory / f"{ordinal}.control.json"
        interruption = None
        started = time.monotonic()
        with paths["input"].open("rb") as stdin, paths["stdout"].open("xb") as stdout, \
                paths["stderr"].open("xb") as stderr:
            child = None
            try:
                child = subprocess.Popen([sys.executable, "-B", "-c", _SUPERVISOR,
                                          str(control_path), *record["argv"]],
                                         stdin=stdin, stdout=stdout, stderr=stderr,
                                         start_new_session=True, preexec_fn=limits)
                record["pid"] = child.pid
                cancellation.mark_registered()
                child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
            except BaseException as exc:
                record["cancelled"] = True
                interruption = exc
            finally:
                cancellation.defer()
                if child is not None:
                    record.setdefault("pid", child.pid)
                    if child.poll() is None:
                        child.terminate()
                        try:
                            child.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait()
                    else:
                        child.wait()
        try:
            control = _read_supervisor_control(control_path)
        except (OSError, ValueError, RecursionError) as error:
            # A protocol/read failure is not a guest result. Commit this
            # invocation and its streams before surfacing the controlled error.
            control = {}
            record["control_error"] = dict(type=type(error).__name__,
                                          errno=getattr(error, "errno", None),
                                          message=str(error))
        supervisor_ok = (child is not None and child.returncode == 0 and
                         control.get("complete") is True and
                         type(control.get("target_exit_code")) is int and
                         "interrupted" not in control and "error" not in control)
        record["cancelled"] = record["cancelled"] or bool(cancellation.pending)
        record["cancellation_signals"] = cancellation.seen
        record.update(exit_code=control.get("target_exit_code") if supervisor_ok else
                      (child.returncode if child is not None else None),
                      supervisor_exit_code=child.returncode if child is not None else None,
                      supervisor_ok=supervisor_ok, control=control,
                      elapsed_seconds=time.monotonic() - started)
        for name, path in paths.items():
            record[name] = dict(path=path.name, **self.identity(path))
        self.records.append(record)
        # Persist before raising; a detected failure must not erase its evidence.
        (self.directory / "invocations.json").write_text(
            json.dumps(dict(limits=self.limits, records=self.records), indent=2) + "\n")
        if interruption is not None:
            raise interruption
        cancellation.raise_pending()
        if record["timed_out"]:
            raise AssuranceFailure(f"{label}: timeout; evidence {self.directory}/{ordinal}")
        if not supervisor_ok:
            raise AssuranceFailure(f"{label}: supervisor/cleanup failure; evidence {self.directory}/{ordinal}")
        if record["exit_code"] < 0:
            raise AssuranceFailure(f"{label}: signal {-record['exit_code']}; evidence {self.directory}/{ordinal}")
        if any(record[name]["bytes"] >= limit for name in ("stdout", "stderr")):
            raise AssuranceFailure(f"{label}: output limit reached; evidence {self.directory}/{ordinal}")
        return Result(record["exit_code"], paths["stdout"].read_bytes(), paths["stderr"].read_bytes())
