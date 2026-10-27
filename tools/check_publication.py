"""Reject internal development files from a selected public source tree.

This checks paths, not file contents or Git history. It is not a secret scanner.
"""
import argparse
import fnmatch
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def blocked_reason(path):
    if not isinstance(path, str) or not path:
        return "invalid source path"
    relative = PurePosixPath(path)
    if not relative.parts or relative.is_absolute() or ".." in relative.parts or relative.as_posix() != path:
        return "source path must be normalized and relative"
    parts = tuple(part.lower() for part in relative.parts)
    first, name = parts[0], parts[-1]
    private = {".git", ".agents", ".codex", ".claude", ".cursor", ".superpowers",
               ".migration-archives", ".nolqu-mcp", ".nql", "guildline"}
    if any(part in private or part.startswith((".venv", ".codex-")) for part in parts):
        return "private local state or agent instructions"
    if "__pycache__" in parts or name.endswith((".pyc", ".pyo")):
        return "generated Python cache"
    if name in {"agents.md", "native_handoff.md"}:
        return "internal agent or handoff notes"
    if name.startswith("nolqu_major") or (len(parts) == 1 and name.endswith(".docx")):
        return "internal master prompt or concept attachment"
    if parts[:2] == ("docs", "superpowers"):
        return "internal agent plans and specifications"
    if parts[:2] == ("docs", "project") and fnmatch.fnmatchcase(name, "*_report.md"):
        return "internal session or execution report"
    return None


def inspect_paths(paths):
    paths = list(paths)
    blocked = [{"path": path, "reason": reason} for path in paths
               if (reason := blocked_reason(path)) is not None]
    return {"passed": bool(paths) and not blocked, "files_checked": len(paths),
            "blocked": blocked, "scope": "selected paths; not contents or history"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.manifest:
            paths = [row["path"] for row in json.loads(args.manifest.read_text())["files"]]
        else:
            result = subprocess.run(["git", "-C", str(args.root), "ls-files", "-z"],
                                    check=True, capture_output=True, timeout=30)
            paths = result.stdout.decode("utf-8").rstrip("\0").split("\0") if result.stdout else []
        report = inspect_paths(paths)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        report = {"passed": False, "error": str(error)}
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
