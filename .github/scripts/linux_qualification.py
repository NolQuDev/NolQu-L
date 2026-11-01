"""Sequential Linux host qualification, outside the canonical compiler chain."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/security"))
from bounded_runner import BoundedRunner

PYTHON = ["python3", "-B", "-W", "error::ResourceWarning"]
GATES = [
    ("ci-controls", PYTHON + ["tests/ci/test_linux_qualification.py", "-v"]),
    ("publication-controls", PYTHON + ["tests/meta/test_publication.py", "-v"]),
    ("release-controls", PYTHON + ["tests/meta/test_alpha_release.py", "-v"]),
    ("publication", PYTHON + ["tools/check_publication.py"]),
    ("hardlinks", PYTHON + ["-m", "unittest", "-v",
        "test_canonical_toolchain.CanonicalForwardingTests.test_default_output_rejects_source_tool_and_component_aliases",
        "test_canonical_cli.CanonicalCliTests.test_repeated_hardlinks_keep_public_installation_discoverable",
        "test_canonical_cli.CanonicalCliTests.test_output_aliases_of_sources_components_and_public_tools_are_rejected",
        "test_c0_capacity_pipeline.CapacityPipelineTests.test_protected_paths_hardlinks_and_symlinks",
        "test_c0_capacity_pipeline.CapacityPipelineTests.test_destination_is_rechecked_before_publication",
        "test_materializer_outputs.MaterializerHardlinkTests.test_MO07_hardlink_aliases_are_rejected"]),
    ("main", ["make", "-j1", "test"]),
    ("mcp", PYTHON + ["-m", "unittest", "discover", "-s", "tests/mcp", "-p", "test_*.py", "-v"]),
    ("runner", PYTHON + ["tests/security/test_bounded_runner.py", "-v"]),
    ("android-controls", PYTHON + ["tests/security/test_android_host.py", "-v"]),
    ("assurance", PYTHON + ["tests/security/test_native_assurance.py", "-v"]),
    ("release", ["make", "-j1", "release-check"]),
]


def save(path, value):
    descriptor, staging = tempfile.mkstemp(prefix=".result-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, path)
    finally:
        Path(staging).unlink(missing_ok=True)


def require_linux_host(directory, *, system=None, machine=None):
    system = sys.platform if system is None else system
    machine = platform.machine() if machine is None else machine
    if system != "linux" or machine != "x86_64":
        raise RuntimeError("qualification requires Linux x86_64; native Android coverage is separate")
    required = ("bash", "make", "nasm", "ld", "objdump", "readelf", "timeout", "ln",
                "git", "python3", "qemu-x86_64", "clang", "llvm-as")
    missing = [name for name in required if shutil.which(name) is None]
    if missing:
        raise RuntimeError("missing Linux test tools: " + ", ".join(missing))
    with tempfile.TemporaryDirectory(prefix="hardlink-preflight-", dir=directory) as name:
        source, alias = Path(name) / "source", Path(name) / "alias"
        source.write_bytes(b"NolQu-L real hard-link preflight\n")
        os.link(source, alias)
        if not source.samefile(alias) or alias.stat().st_nlink != 2:
            raise RuntimeError("Linux hard-link capability was not established")
        alias.write_bytes(b"shared inode\n")
        if source.read_bytes() != b"shared inode\n":
            raise RuntimeError("hard-link mutation did not reach the shared inode")
        return {"system": system, "machine": machine, "hardlink_verified": True,
                "filesystem_device": source.stat().st_dev,
                "tools": {name: shutil.which(name) for name in required}}


def identities():
    files = [ROOT / "VERSION", ROOT / "CHANNEL", ROOT / "bootstrap/manifest.tsv",
             ROOT / "bootstrap/compiler/b0/compiler.nql0",
             ROOT / "bootstrap/compiler/c0/compiler.nq",
             ROOT / "bootstrap/compiler/c0/frontend.nql",
             ROOT / "bootstrap/compiler/c0/backend.nql"]
    files += sorted(ROOT.glob("bootstrap/**/x86_64-linux/*.seed"))
    files += sorted(ROOT.glob("bootstrap/**/x86_64-linux/*.sha256"))
    return {str(path.relative_to(ROOT)): BoundedRunner.identity(path) for path in files}


def branch_policy(branch, version):
    alpha = r"[0-9]+\.[0-9]+\.[0-9]+-alpha\.[0-9]+"
    release = r"[0-9]+\.[0-9]+\.[0-9]+(?:-rc\.[0-9]+)?"
    if branch == "Dev" and re.fullmatch(alpha, version) is None:
        raise ValueError("Dev accepts Alpha versions only")
    if branch == "Stable" and re.fullmatch(release, version) is None:
        raise ValueError("Stable accepts Release Candidate or final versions only")
    return {"branch": branch, "version": version}


def run_gates(output, gates, *, context=None, final_check=None):
    output = Path(output)
    output.mkdir(mode=0o700)
    report = {"schema": 1, "status": "RUNNING", "passed": False,
              "scope": "Linux host qualification" if context else "command-result controls",
              "context": context, "gates": []}
    save(output / "result.json", report)
    try:
        for name in ("generations", "cli", "project", "mcp", "process", "tmp"):
            (output / name).mkdir(mode=0o700)
        variables = [f"C031_WORK={output / 'generations'}",
                     f"NQL_CANONICAL_RECEIPTS={output / 'cli'}",
                     f"NQL_PROJECT_RECEIPTS={output / 'project'}",
                     f"NQL_MCP_RECEIPTS={output / 'mcp'}",
                     f"NOLQU_PROCESS_TEST_RECEIPTS={output / 'process'}",
                     f"NQL_ASSURANCE_OUTPUT={output / 'assurance'}",
                     f"TMPDIR={output / 'tmp'}",
                     "PYTHONDONTWRITEBYTECODE=1",
                     "PYTHONPATH=" + os.pathsep.join(str(ROOT / "tests" / name)
                                                    for name in ("bootstrap", "compiler", "mcp"))]
        runner = BoundedRunner(output / "calls", timeout=2700, budget=3000,
                               output_limit=32 * 1024 * 1024)
        for label, command in gates:
            result = runner.run(label, ["env", *variables, *command], b"")
            report["gates"].append({"label": label, "command": command,
                                    "exit_code": result.returncode,
                                    "passed": result.returncode == 0,
                                    "invocation": runner.records[-1]})
            save(output / "result.json", report)
            print(json.dumps({"gate": label, "exit_code": result.returncode}), flush=True)
        unchanged = True
        if final_check is not None:
            unchanged = final_check()
            report["canonical_inputs_unchanged"] = unchanged
            if not unchanged:
                report["error"] = {"type": "InputDrift",
                                   "message": "canonical inputs changed during qualification"}
        report["passed"] = (bool(report["gates"]) and unchanged and
                            all(gate["passed"] for gate in report["gates"]))
        report["status"] = "PASSED" if report["passed"] else "FAILED"
    except BaseException as error:
        report.update(status="FAILED", passed=False,
                      error={"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        save(output / "result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        parser.error("output must be a new evidence directory")
    try:
        context = require_linux_host(output.parent)
        branch = os.environ.get("GITHUB_BASE_REF") or os.environ.get("GITHUB_REF_NAME", "local")
        context["branch_policy"] = branch_policy(branch, (ROOT / "VERSION").read_text().strip())
        context.update(python=sys.version, revision=os.environ.get("GITHUB_SHA"),
                       run_id=os.environ.get("GITHUB_RUN_ID"),
                       run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT"),
                       canonical_inputs=identities())
    except Exception as error:
        output.mkdir(mode=0o700)
        save(output / "result.json", {"schema": 1, "status": "BLOCKED", "passed": False,
             "error": {"type": type(error).__name__, "message": str(error)}, "gates": []})
        print(str(error), file=sys.stderr)
        return 2
    report = run_gates(output, GATES, context=context,
                       final_check=lambda: identities() == context["canonical_inputs"])
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
