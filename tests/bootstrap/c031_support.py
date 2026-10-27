"""Test-only invocation, predecessor reconstruction and NQAF wire oracle."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import tempfile
import stat
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
PREDECESSORS = ROOT / "tests/bootstrap/fixtures/c031/predecessor"


def candidate_binary(variable, default):
    value = os.environ.get(variable, default)
    if not value:
        raise ValueError(f"{variable}: empty candidate path")
    path = Path(value).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"{variable}: not a regular file: {path}")
    if not os.access(path, os.X_OK):
        raise PermissionError(f"{variable}: not executable: {path}")
    return path


def run_native(binary: Path, data: bytes = b"", *, args: tuple[str, ...] = (),
               timeout: float = 15.0, **kwargs) -> subprocess.CompletedProcess[bytes]:
    binary = Path(binary).resolve(strict=True)
    runner = []
    if platform.machine() != "x86_64":
        qemu = shutil.which("qemu-x86_64")
        if qemu is None:
            raise RuntimeError("x86_64 execution unavailable; install qemu-x86_64")
        runner = [qemu]
    options = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    options.update(kwargs)
    if "stdin" not in options:
        options["input"] = data
    elif data:
        raise ValueError("data and stdin cannot both supply input")
    command = runner + [str(binary), *args]
    archive = os.environ.get("NQL_NATIVE_EVIDENCE_DIR")
    if archive is not None:
        return _run_native_observed(command, binary, runner, timeout, options, archive)
    return subprocess.run(command, timeout=timeout, **options)


class NativeEvidenceError(RuntimeError):
    """An explicitly requested host observation failed; never a guest diagnostic."""

    def __init__(self, message, record, result=None, original_error=None):
        super().__init__(message)
        self.record = record
        self.result = result
        self.original_error = original_error


def _write_native_json(path, record):
    descriptor, temporary = tempfile.mkstemp(prefix=".record-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(record, output, ensure_ascii=True, sort_keys=True, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _native_blob(root, data):
    data = bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    directory = root / "blobs"
    directory.mkdir(mode=0o700, exist_ok=True)
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise ValueError("native evidence blobs must be a real directory")
    destination = directory / digest
    descriptor, temporary = tempfile.mkstemp(prefix=".blob-", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        # Android Python has no os.link. Lock the shared directory while checking
        # and publishing a closed file; cooperating writers never replace a blob.
        lock = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                descriptor = os.open(destination, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
            except FileNotFoundError:
                os.replace(temporary, destination)
            else:
                try:
                    info = os.fstat(descriptor)
                    if not stat.S_ISREG(info.st_mode) or info.st_size != len(data) \
                            or stat.S_IMODE(info.st_mode) != 0o600:
                        raise ValueError("invalid existing native evidence blob")
                    if _native_read_chunks(descriptor) != data:
                        raise ValueError("native evidence blob identity mismatch")
                finally:
                    os.close(descriptor)
        finally:
            os.close(lock)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return dict(path="blobs/" + digest, bytes=len(data), sha256=digest)


def _native_proc_identity(pid):
    result = dict(pid=pid, available=False, start_ticks=None)
    try:
        base = Path("/proc") / str(pid)
        fields = (base / "stat").read_text().rsplit(")", 1)[1].split()
        result.update(available=True, parent=int(fields[1]), group=int(fields[2]),
                      session=int(fields[3]), start_ticks=fields[19], state=fields[0])
        for name in ("exe", "cwd"):
            try:
                result[name + "_link"] = os.readlink(base / name)
            except OSError as error:
                result[name + "_error"] = dict(type=type(error).__name__, errno=error.errno)
    except (OSError, ValueError, IndexError) as error:
        result["error"] = dict(type=type(error).__name__, errno=getattr(error, "errno", None))
    return result


def _native_read_chunks(descriptor):
    chunks = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _native_read_file(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("native evidence executable is not a regular file")
        data = _native_read_chunks(descriptor)
        try:
            opened_path = os.readlink(Path("/proc/self/fd") / str(descriptor))
            path_error = None
        except OSError as error:
            opened_path = str(path)
            path_error = dict(type=type(error).__name__, errno=error.errno)
    finally:
        # Own the raw descriptor from open to close, including type/read errors.
        os.close(descriptor)
    observation = dict(path=opened_path, lookup_path=str(path), bytes=len(data),
                       sha256=hashlib.sha256(data).hexdigest(), mode=stat.S_IMODE(info.st_mode),
                       device=info.st_dev, inode=info.st_ino, mtime_ns=info.st_mtime_ns)
    if path_error is not None:
        observation["opened_path_error"] = path_error
    return observation, data


def _native_file_observation(path, root=None):
    result, data = _native_read_file(path)
    if root is not None:
        result["blob"] = _native_blob(root, data)
    return result


def _native_executable_candidates(value, cwd, environment, root):
    requested = os.fsencode(value)
    if os.path.dirname(requested):
        names = [requested]
    else:
        names = [os.path.join(os.fsencode(directory), requested)
                 for directory in os.get_exec_path(environment)]
    retained, unavailable = [], []
    for name in names:
        logical = Path(cwd) / os.fsdecode(name)
        try:
            # Let open perform kernel lookup, including symlinks followed by
            # '..' and executable magic links without a separately live name.
            observation, data = _native_read_file(logical)
        except (OSError, ValueError) as error:
            unavailable.append(dict(path=str(logical), error=type(error).__name__,
                                    errno=getattr(error, "errno", None), message=str(error)))
            continue
        # Only path lookup/read failures are observational. Archive publication
        # and integrity failures must still fail closed, including a bad blob.
        observation["blob"] = _native_blob(root, data)
        retained.append(observation)
    return retained, unavailable


def _native_fd_observation(value):
    if value in (None, subprocess.PIPE, subprocess.STDOUT, subprocess.DEVNULL):
        return dict(selection={None: "inherited", subprocess.PIPE: "PIPE",
                    subprocess.STDOUT: "STDOUT", subprocess.DEVNULL: "DEVNULL"}[value])
    try:
        descriptor = value if isinstance(value, int) else value.fileno()
        info = os.fstat(descriptor)
        return dict(selection="external-fd", descriptor=descriptor, mode=info.st_mode,
                    device=info.st_dev, inode=info.st_ino)
    except (OSError, ValueError) as error:
        return dict(selection="external-fd", error=type(error).__name__)


def _native_stream(root, value, requested):
    result = dict(captured=value is not None, capture_requested=requested)
    if value is not None:
        text = isinstance(value, str)
        result.update(representation="decoded-text" if text else "bytes",
                      blob=_native_blob(root, value.encode("utf-8", "surrogatepass") if text else value))
    return result


def _native_cwd_observation(requested):
    lookup = Path(os.fsdecode(requested)) if requested is not None else Path(".")
    result = dict(cwd_requested=None if requested is None else dict(
        type="bytes" if isinstance(requested, bytes) else "str", hex=os.fsencode(requested).hex()))
    if not lookup.is_absolute():
        try:
            lookup = Path.cwd() / lookup
        except OSError as error:
            # A process may inherit an unnamed directory; relative kernel
            # lookup still works. Metadata must not add a launch precondition.
            result["cwd_base_error"] = dict(type=type(error).__name__, errno=error.errno)
    result["cwd_lookup"] = str(lookup)
    try:
        result["cwd"] = str(lookup.resolve(strict=False))
    except (OSError, ValueError) as error:
        result.update(cwd=None, cwd_error=dict(type=type(error).__name__, errno=getattr(error, "errno", None)))
    return result


def _run_native_observed(command, binary, runner, timeout, options, archive):
    # Mirror subprocess.run's validation and cleanup, without changing sessions,
    # descriptors, resource limits, signal handlers or the requested command.
    options = dict(options)
    data = options.pop("input", None)
    check = options.pop("check", False)
    capture_output = options.pop("capture_output", False)
    if data is not None:
        if options.get("stdin") is not None:
            raise ValueError("stdin and input arguments may not both be used.")
        options["stdin"] = subprocess.PIPE
    if capture_output:
        if options.get("stdout") is not None or options.get("stderr") is not None:
            raise ValueError("stdout and stderr arguments may not be used with capture_output.")
        options.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record = dict(schema=1, complete=False, started_utc=datetime.now(timezone.utc).isoformat(),
                  started_monotonic_ns=time.monotonic_ns(), timeout_seconds=timeout,
                  command=[dict(type="bytes" if isinstance(arg, bytes) else "str",
                                hex=os.fsencode(arg).hex()) for arg in command],
                  **_native_cwd_observation(options.get("cwd")),
                  parent=_native_proc_identity(os.getpid()), child=None,
                  cleanup_actions=[], timed_out=False,
                  environment_values="UNOBSERVED", explicit_environment="env" in options,
                  stdin=dict(kind="external-unobserved", descriptor=_native_fd_observation(options.get("stdin"))),
                  descriptors={name: _native_fd_observation(options.get(name))
                               for name in ("stdout", "stderr")},
                  preexec_fn_supplied=options.get("preexec_fn") is not None)
    result = None
    original = None
    observation_error = None
    child = None
    stdout = stderr = None
    try:
        if not archive:
            raise ValueError("native evidence root must not be empty")
        root = Path(archive).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("native evidence root must be an existing directory")
        directory = Path(tempfile.mkdtemp(prefix="call-", dir=root))
        record["evidence_directory"] = str(directory)
        record["target_before"] = _native_file_observation(binary, root)
        record["adapter_before"] = _native_file_observation(Path(runner[0]).resolve(strict=True), root) if runner else None
        selected = options.get("executable")
        record["executable_override"] = None
        record["executable_candidates_before"] = []
        if selected is not None:
            record["executable_override"] = dict(type="bytes" if isinstance(selected, bytes) else "str",
                                                  hex=os.fsencode(selected).hex())
            candidates, unavailable = _native_executable_candidates(selected, record["cwd_lookup"], options.get("env"), root)
            record.update(executable_candidates_before=candidates, executable_candidates_unavailable=unavailable)
        if data is not None:
            record["stdin"] = dict(kind="supplied", **_native_stream(root, data, True))
        _write_native_json(directory / "begin.json", record)
    except Exception as error:
        raise NativeEvidenceError("cannot prepare requested native evidence before launch", record,
                                  original_error=error) from error
    try:
        with subprocess.Popen(command, **options) as process:
            child = process
            try:
                record["child"] = dict(_native_proc_identity(child.pid), pid=child.pid)
                try:
                    _write_native_json(directory / "launched.json", record)
                except Exception as error:
                    observation_error = error
                    raise
                stdout, stderr = child.communicate(data, timeout=timeout)
            except subprocess.TimeoutExpired as error:
                record["timed_out"] = True
                stdout, stderr = error.stdout, error.stderr
                record["cleanup_actions"].append(dict(pid=child.pid, signal="SIGKILL", reason="timeout"))
                child.kill()
                child.wait()
                raise
            except BaseException:
                record["cleanup_actions"].append(dict(pid=child.pid, signal="SIGKILL",
                    reason="evidence-error" if observation_error is not None else "exception"))
                child.kill()
                raise
            returncode = child.poll()
        result = subprocess.CompletedProcess(command, returncode, stdout, stderr)
        if check and returncode:
            raise subprocess.CalledProcessError(returncode, command, output=stdout, stderr=stderr)
    except BaseException as error:
        original = error
    returncode = child.returncode if child is not None else None
    if observation_error is not None:
        outcome = "evidence-error"
    elif isinstance(original, subprocess.TimeoutExpired):
        outcome = "timeout"
    elif original is not None and child is None:
        outcome = "spawn-error"
    elif original is not None and not isinstance(original, subprocess.CalledProcessError):
        outcome = "cancelled" if isinstance(original, (KeyboardInterrupt, SystemExit)) else "exception"
    else:
        outcome = "signal" if returncode < 0 else "exit"
    record.update(outcome=outcome, returncode=returncode,
                  signal_number=-returncode if returncode is not None and returncode < 0 else None,
                  exception=dict(type=type(original).__name__) if original is not None else None,
                  finished_utc=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=(time.monotonic_ns() - record["started_monotonic_ns"]) / 1e9)
    try:
        record["stdout"] = _native_stream(root, stdout, options.get("stdout") == subprocess.PIPE)
        record["stderr"] = _native_stream(root, stderr, options.get("stderr") == subprocess.PIPE)
        try:
            record["target_after"] = _native_file_observation(binary)
        except (OSError, ValueError) as error:
            record["target_after"] = dict(error=type(error).__name__, message=str(error), errno=getattr(error, "errno", None))
        record["target_changed"] = record["target_after"] != {k: v for k, v in record["target_before"].items() if k != "blob"}
        record["executable_candidates_after"] = []
        for candidate in record["executable_candidates_before"]:
            try:
                after = _native_file_observation(Path(candidate["lookup_path"]))
            except (OSError, ValueError) as error:
                after = dict(path=candidate["path"], error=type(error).__name__, message=str(error))
            record["executable_candidates_after"].append(after)
        record["executable_candidates_changed"] = record["executable_candidates_after"] != [
            {k: v for k, v in candidate.items() if k != "blob"}
            for candidate in record["executable_candidates_before"]]
        record["complete"] = observation_error is None
        _write_native_json(directory / "result.json", record)
    except Exception as error:
        observation_error = error
        record.update(complete=False, outcome="evidence-error")
    if observation_error is not None:
        raise NativeEvidenceError("requested native evidence failed after launch; owned child reaped",
                                  record, result, original) from observation_error
    if original is not None:
        raise original
    return result


def encode_profile_source(source):
    return b"NQSC\x01\x01" + bytes(10) + source


def decode_nqaf(data):
    if len(data) < 16 or data[:4] != b"NQAF":
        raise ValueError("invalid NQAF header")
    version = data[4]
    if version in (5, 6):
        if len(data) < 32:
            raise ValueError(f"truncated NQAF/{version} header")
        (_, _, size, flags, length, count, root, tokens, dialect, profile,
         reserved16, reserved32) = struct.unpack_from("<4sBBHIIIIBBHI", data)
        dialects = range(1, 5) if version == 5 else (5,)
        if size != 32 or reserved16 or reserved32 or dialect not in dialects or profile not in (0, 1):
            raise ValueError(f"invalid NQAF/{version} fields")
        source_cap, count_cap = 262144, 65536
    elif version in range(1, 5):
        _, _, size, flags, length, count, root, tokens = struct.unpack_from("<4sBBHHHHH", data)
        if size != 16:
            raise ValueError("invalid legacy record size")
        source_cap, count_cap = 8192, 512
        dialect, profile = version, 0
    else:
        raise ValueError("unsupported NQAF version")
    if flags or not 0 < length <= source_cap or not 0 < count <= count_cap:
        raise ValueError("invalid flags/source/node count")
    if root != count or not 0 < tokens <= count_cap:
        raise ValueError("invalid root/token count")
    if len(data) != size + length + count * size:
        raise ValueError("truncated or trailing NQAF data")
    nodes = []
    for index in range(count):
        position = size + length + index * size
        if version in (5, 6):
            kind, node_flags, r16, offset, span, left, right, nxt, r1, r2 = struct.unpack_from(
                "<BBHIIIIIII", data, position)
            reserved = r16 or r1 or r2
        else:
            kind, node_flags, offset, span, left, right, nxt, padding = struct.unpack_from(
                "<BBHHHHH4s", data, position)
            reserved = padding != bytes(4)
        if node_flags or reserved:
            raise ValueError(f"node {index + 1}: reserved fields")
        if offset >= length or not 0 < span <= length - offset:
            raise ValueError(f"node {index + 1}: invalid span")
        if max(left, right, nxt) > count:
            raise ValueError(f"node {index + 1}: invalid ID")
        nodes.append((kind, node_flags, offset, span, left, right, nxt))
    return dict(version=version, source_length=length, node_count=count,
                root_id=root, token_count=tokens, dialect=dialect,
                runtime_profile=profile, source=data[size:size + length]), nodes


def assert_owned_graph(header, nodes):
    """Connectivity/ownership only; grammar and physical order need separate tests."""
    count = header["node_count"]
    if len(nodes) != count:
        raise ValueError("wrong node count")
    pending, seen = [header["root_id"]], set()
    while pending:
        node_id = pending.pop()
        if not 1 <= node_id <= count or node_id in seen:
            raise ValueError("invalid, shared or cyclic node")
        seen.add(node_id)
        pending.extend(child for child in nodes[node_id - 1][4:7] if child)
    if len(seen) != count:
        raise ValueError("unreachable nodes")


def build_predecessors(destination):
    manifest = json.loads((PREDECESSORS / "hashes.json").read_text())
    source_names = {"b0.nql0", "frontend.nql", "backend.nql"}
    artifact_names = {"b0.seed", "c0-frontend.seed", "c0-backend.seed"}
    if set(manifest) != {"sources", "artifacts"} or set(manifest["sources"]) != source_names \
            or set(manifest["artifacts"]) != artifact_names:
        raise ValueError("invalid predecessor identity ledger")
    for section in manifest.values():
        for value in section.values():
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("invalid SHA-256 in predecessor ledger")
    sources = {name: (PREDECESSORS / name).read_bytes() for name in source_names}
    for name, source in sources.items():
        if hashlib.sha256(source).hexdigest() != manifest["sources"][name]:
            raise ValueError(f"predecessor SHA-256 mismatch: {name}")
    stage0 = ROOT / "bootstrap/stage0/x86_64-linux/stage0.seed"
    pin = stage0.with_suffix(".sha256").read_text().split()
    if len(pin) != 2 or pin[1] != stage0.name or hashlib.sha256(stage0.read_bytes()).hexdigest() != pin[0]:
        raise ValueError("Stage0 SHA-256 mismatch")
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("predecessor build destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    published = []
    try:
        with tempfile.TemporaryDirectory(prefix=".predecessors-", dir=destination) as tmp:
            work = Path(tmp)
            result = run_native(stage0, sources["b0.nql0"], timeout=120)
            if result.returncode or result.stderr:
                raise ValueError(f"predecessor Stage0 build failed: {result.returncode}: {result.stderr!r}")
            b0 = work / "b0.seed"
            b0.write_bytes(result.stdout)
            b0.chmod(0o755)
            if hashlib.sha256(result.stdout).hexdigest() != manifest["artifacts"][b0.name]:
                raise ValueError("predecessor B0 artifact SHA-256 mismatch")
            for name in ("frontend", "backend"):
                source = work / f"{name}.nql"
                source.write_bytes(sources[source.name])
                output = work / f"c0-{name}.seed"
                result = run_native(b0, args=(str(source), "-o", str(output)), timeout=120)
                if result.returncode or result.stdout or result.stderr:
                    raise ValueError(f"predecessor {name} build failed: {result.returncode}: {result.stderr!r}")
                if hashlib.sha256(output.read_bytes()).hexdigest() != manifest["artifacts"][output.name]:
                    raise ValueError(f"predecessor {name} artifact SHA-256 mismatch")
            for name in sorted(artifact_names):
                output = destination / name
                (work / name).rename(output)
                published.append(output)
    except BaseException:
        for output in published:
            output.unlink(missing_ok=True)
        raise
    return dict(b0=destination / "b0.seed", frontend=destination / "c0-frontend.seed",
                backend=destination / "c0-backend.seed")
