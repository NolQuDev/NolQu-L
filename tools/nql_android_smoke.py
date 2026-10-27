#!/usr/bin/env python3
"""Optional offline host smoke; never a canonical compiler stage or sandbox."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import tempfile
import types

SEEDS = {
    "b0": "bootstrap/compiler/b0/x86_64-linux/b0.seed",
    "frontend": "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed",
    "backend": "bootstrap/compiler/c0/x86_64-linux/c0-backend.seed",
}
EXTRAS = {
    "bounded_runner.py": "tests/security/bounded_runner.py",
    "native_cat.nql": "examples/canonical/native_cat.nql",
    "android_smoke.py": "tools/nql_android_smoke.py",
}
FILE_SET = {role + ".seed" for role in SEEDS} | set(EXTRAS)
FILE_LIMIT = 8 * 1024 * 1024


def _read_regular(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"not a regular file: {path}")
        if info.st_size > limit:
            raise ValueError(f"file limit exceeded: {path}")
        chunks, count = [], 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
            if count > limit:
                raise ValueError(f"file limit exceeded: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _file_identity(path):
    """Hash one regular-file snapshot without reusing guest stream limits."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"not a regular adapter: {path}")
        remaining = before.st_size
        digest = hashlib.sha256()
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                raise ValueError(f"adapter changed while hashing: {path}")
            digest.update(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != \
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError(f"adapter changed while hashing: {path}")
        return {"bytes": before.st_size, "sha256": digest.hexdigest()}
    finally:
        os.close(descriptor)


def _seed_header(data):
    if len(data) < 64 or data[:7] != b"\x7fELF\x02\x01\x01" \
            or data[16:20] != b"\x02\x00\x3e\x00":
        raise ValueError("seed must be an ELF64 little-endian x86_64 executable")


def _write_new(path, data, mode=0o600):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def prepare_bundle(root, destination):
    root, destination = Path(root), Path(destination)
    payloads, pins = {}, {}
    for role, relative in SEEDS.items():
        source = root / relative
        pin = _read_regular(source.with_suffix(".sha256"), 1024).decode("ascii")
        match = re.fullmatch(r"([0-9a-f]{64})  " + re.escape(source.name) + r"\n?", pin)
        if match is None:
            raise ValueError(f"invalid seed pin: {source}")
        data = _read_regular(source, FILE_LIMIT)
        if _identity(data)["sha256"] != match[1]:
            raise ValueError(f"seed pin mismatch: {source}")
        _seed_header(data)
        pins[role] = match[1]
        payloads[role + ".seed"] = data
    for name, relative in EXTRAS.items():
        payloads[name] = _read_regular(root / relative, FILE_LIMIT)
    manifest = {"schema": "NQL-ANDROID-SMOKE/1", "pins": pins,
                "compiler_version": _read_regular(root / "VERSION", 128).decode().strip(),
                "channel": _read_regular(root / "CHANNEL", 128).decode().strip(),
                "files": {name: _identity(data) for name, data in payloads.items()},
                "scope": "trusted local smoke bundle; hashes are not signed provenance"}
    destination.mkdir(mode=0o700, exist_ok=False)
    for name, data in payloads.items():
        _write_new(destination / name, data, 0o700 if name.endswith(".seed") else 0o600)
    # The commit marker is last; a partial copy is never a prepared bundle.
    _write_new(destination / "manifest.json", _json_bytes(manifest))
    return manifest


def verify_bundle(bundle):
    bundle = Path(bundle)
    if (bundle / "manifest.json").is_symlink():
        raise ValueError("bundle manifest must be an independent regular file")
    manifest = json.loads(_read_regular(bundle / "manifest.json", 65536))
    if not isinstance(manifest, dict) or manifest.get("schema") != "NQL-ANDROID-SMOKE/1":
        raise ValueError("unsupported bundle schema")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != FILE_SET:
        raise ValueError("invalid bundle file set")
    if not isinstance(manifest.get("pins"), dict) or set(manifest["pins"]) != set(SEEDS):
        raise ValueError("invalid bundle pins")
    for name, expected in files.items():
        path = bundle / name
        if path.is_symlink():
            raise ValueError(f"bundle file must be an independent regular file: {name}")
        data = _read_regular(path, FILE_LIMIT)
        if expected != _identity(data):
            raise ValueError(f"bundle identity mismatch: {name}")
        if name.endswith(".seed"):
            _seed_header(data)
            if expected["sha256"] != manifest["pins"][name[:-5]]:
                raise ValueError(f"bundle seed pin mismatch: {name}")
    return manifest


def host_context(proc_root=Path("/proc")):
    tracer, error = None, None
    try:
        status = (Path(proc_root) / "self/status").read_text()
        match = re.search(r"^TracerPid:\s*([0-9]+)\s*$", status, re.MULTILINE)
        if match is not None:
            tracer = int(match[1])
    except OSError as exc:
        error = type(exc).__name__
    termux_python = os.path.realpath(sys.executable).startswith(
        "/data/data/com.termux/files/usr/bin/")
    android = Path("/system/bin/getprop").is_file()
    native = termux_python and android and tracer == 0
    return {"pid": os.getpid(), "python": sys.executable,
            "machine": platform.machine(), "tracer_pid": tracer,
            "proc_error": error, "termux_python": termux_python, "android": android,
            "native_termux": native,
            "context": "TERMUX_UNTRACED" if native else
            ("TRACED" if tracer else "OTHER_OR_UNKNOWN")}


def _save_report(output, report):
    data = _json_bytes(report)
    descriptor, staging = tempfile.mkstemp(prefix=".result-", suffix=".pending", dir=output)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, output / "result.json")
    finally:
        Path(staging).unlink(missing_ok=True)


def _run_smoke(bundle, output, report, manifest):
    adapter = []
    if platform.machine() != "x86_64":
        qemu = shutil.which("qemu-x86_64")
        if qemu is None:
            raise RuntimeError("qemu-x86_64 is unavailable in this shell PATH")
        adapter = [str(Path(qemu).resolve())]
    report["adapter"] = {"argv_prefix": adapter, "identity":
                         _file_identity(adapter[0]) if adapter else None}
    runner_path = bundle / "bounded_runner.py"
    source = _read_regular(runner_path, FILE_LIMIT)
    if _identity(source) != manifest["files"]["bounded_runner.py"]:
        raise ValueError("bundle identity mismatch: bounded_runner.py")
    # SourceFileLoader may read unchecked cached bytecode even with Python -B.
    # Execute exactly the source bytes just checked against the verified pin.
    module = types.ModuleType("nql_android_bounded_runner")
    module.__file__ = str(runner_path)
    sys.modules[module.__name__] = module
    try:
        exec(compile(source, str(runner_path), "exec", dont_inherit=True), module.__dict__)
    finally:
        sys.modules.pop(module.__name__, None)
    runner = module.BoundedRunner(output / "calls", timeout=15.0, budget=300.0,
                                  output_limit=FILE_LIMIT, max_input=3 * 1024 * 1024)
    report["limits"] = runner.limits

    def invoke(label, program, data=b"", args=()):
        return runner.run(label, [*adapter, str(program), *map(os.fspath, args)], data)

    def expect(result, code=0, stdout=b"", diagnostic=None):
        if result.returncode != code or (stdout is not None and result.stdout != stdout):
            raise RuntimeError(f"unexpected guest result: exit={result.returncode}, "
                               f"stdout_bytes={len(result.stdout)}")
        if diagnostic is None:
            if result.stderr:
                raise RuntimeError(f"unexpected guest diagnostic: {result.stderr!r}")
        elif re.search(diagnostic, result.stderr) is None:
            raise RuntimeError(f"wrong guest diagnostic: {result.stderr!r}")

    def checked(name):
        report["checks"].append({"id": name, "passed": True})
        _save_report(output, report)

    def ast(label, source):
        parsed = invoke(label + "-frontend", bundle / "frontend.seed", source)
        expect(parsed, stdout=None)
        if not parsed.stdout.startswith(b"NQAF"):
            raise RuntimeError("frontend did not produce NQAF")
        return parsed.stdout

    def image(label, source):
        wire = ast(label, source)
        built = invoke(label + "-backend", bundle / "backend.seed", wire)
        expect(built, stdout=None)
        _seed_header(built.stdout)
        program = output / (label + ".elf")
        _write_new(program, built.stdout, 0o700)
        return program, wire, built.stdout

    help_result = invoke("b0-help", bundle / "b0.seed", args=("--help",))
    expect(help_result, stdout=None)
    if b"b0" not in help_result.stdout:
        raise RuntimeError("B0 help is empty or unexpected")
    checked("HS01-b0-help")
    source = output / "b0-return.nql"
    _write_new(source, b"fn main(){return 7}\n")
    program = output / "b0-return.elf"
    expect(invoke("b0-compile", bundle / "b0.seed", args=(source, "-o", program)))
    _seed_header(_read_regular(program, FILE_LIMIT))
    expect(invoke("b0-return", program), code=7)
    checked("HS02-b0-return")

    scalar = b"fn main(){return 6*7}\n"
    program, wire, elf = image("scalar", scalar)
    _, wire_again, elf_again = image("scalar-again", scalar)
    if wire != wire_again or elf != elf_again:
        raise RuntimeError("same-source AST/ELF is nondeterministic")
    expect(invoke("scalar-run", program), code=42)
    checked("HS03-scalar-determinism")
    program, _, _ = image("nested", b"fn add(a,b){return a+b} fn main(){return add(2,add(3,4))}")
    expect(invoke("nested-run", program), code=9)
    checked("HS04-nested-calls")
    payload = b"\x00N\xffL"
    program, _, _ = image("stream", b"fn main(){let n=input_read(4,4) output_write(4,n) return n}")
    expect(invoke("stream-run", program, payload), code=4, stdout=payload)
    checked("HS05-binary-stream")
    for label, body, diagnostic in (
            ("bounds", b"byte_load(65536)", rb"^input:1:[0-9]+: error\[C0R-004\]:"),
            ("overflow", b"9223372036854775807+1", rb"^input:1:[0-9]+: error\[C0R-001\]:")):
        program, _, _ = image(label, b"fn main(){return " + body + b"}")
        expect(invoke(label + "-run", program), code=70, diagnostic=diagnostic)
        checked("HS06-bounds" if label == "bounds" else "HS07-overflow")
    expect(invoke("syntax-invalid", bundle / "frontend.seed", b"fn main(){return @}"),
           code=1, diagnostic=rb"^input:1:[0-9]+: error\[C0P-[0-9]+\]:")
    checked("HS08-located-syntax-rejection")
    expect(invoke("semantic-invalid", bundle / "backend.seed", ast("unknown", b"fn main(){return missing}")),
           code=1, diagnostic=rb"^input:1:18: error\[C0B-003\]:")
    checked("HS09-located-semantic-rejection")
    expect(invoke("ast-invalid", bundle / "backend.seed", b"bad"),
           code=1, diagnostic=rb"error\[C0B-001\]:")
    checked("HS10-malformed-ast-rejection")

    cat, _, _ = image("native-cat", _read_regular(bundle / "native_cat.nql", FILE_LIMIT))
    expect(invoke("native-cat-stdin", cat, payload), stdout=payload)
    datafile = output / "literal file '$(nql)' .bin"
    _write_new(datafile, payload)
    expect(invoke("native-cat-file", cat, args=(datafile,)), stdout=payload)
    if _read_regular(datafile, FILE_LIMIT) != payload:
        raise RuntimeError("native-cat modified its input file")
    checked("HS11-native-cat-argv-syscall")
    expect(invoke("native-cat-missing", cat, args=(output / "absent-input",)),
           code=1, diagnostic=rb"^native_cat: I/O error\n$")
    checked("HS12-native-cat-error")
    changed, _, changed_elf = image("changed", b"fn main(){return 43}")
    if changed_elf == elf:
        raise RuntimeError("different source values produced the same executable")
    expect(invoke("changed-run", changed), code=43)
    checked("HS13-source-dependent-code")
    if adapter and _file_identity(adapter[0]) != report["adapter"]["identity"]:
        raise RuntimeError("adapter identity changed during execution")
    report["invocations"] = len(runner.records)


def run_bundle(bundle, output, require_native_termux=False):
    bundle, output = Path(bundle).resolve(), Path(output)
    manifest = verify_bundle(bundle)
    output.mkdir(mode=0o700, exist_ok=False)
    report = {"schema": "NQL-ANDROID-HOST-RESULT/1", "ok": False,
              "status": "BLOCKED", "host": host_context(), "checks": [],
              "bundle_manifest": _identity(_read_regular(bundle / "manifest.json", 65536)),
              "scope": "finite host smoke, not full regression or self-host verification"}
    if require_native_termux and not report["host"]["native_termux"]:
        report["error"] = "native Termux required; current context is traced or unconfirmed"
        _save_report(output, report)
        return report
    report["status"] = "RUNNING"
    _save_report(output, report)
    try:
        _run_smoke(bundle, output, report, manifest)
        verify_bundle(bundle)
        report.update(ok=True, status="PASS")
    except BaseException as exc:
        report.update(ok=False, status="FAILED", error=f"{type(exc).__name__}: {exc}")
        if not isinstance(exc, Exception):
            _save_report(output, report)
            raise
    _save_report(output, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="copy pinned inputs to a new private directory")
    prepare.add_argument("--root", required=True, type=Path)
    prepare.add_argument("--bundle", required=True, type=Path)
    run = commands.add_parser("run", help="run finite smoke cases sequentially")
    run.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--require-native-termux", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            manifest = prepare_bundle(args.root, args.bundle)
            print(json.dumps({"status": "PREPARED", "bundle": str(args.bundle),
                              "files": len(manifest["files"])}))
            return 0
        report = run_bundle(args.bundle, args.output, args.require_native_termux)
        print(json.dumps({"status": report["status"], "host": report["host"],
                          "result": str(args.output / "result.json")}))
        return 0 if report["ok"] else 2
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"android-host: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
