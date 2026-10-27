"""Public source selection must exclude private development material."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/check_publication.py"


class PublicationTests(unittest.TestCase):
    def policy(self):
        spec = importlib.util.spec_from_file_location("publication_policy", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_private_material_is_rejected(self):
        policy = self.policy()
        for path in (
            "NOLQU_MAJOR_DEVELOPMENT_ASSEMBLY_LEVEL.md",
            "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md", "NolQu-LConcept.docx",
            "NolQu-L%20Concept%20-%20Refined%20v10%20Assembly-Level(1).docx",
            "docs/superpowers/plans/work.md", "docs/superpowers/specs/design.md",
            "NOLQU_MAJOR_PRIVATE.md", "subproject/.codex/config.toml",
            "subproject/.superpowers/session.json", "nested/.agents/skills/a/SKILL.md",
            "docs/project/C032_SESSION_REPORT.md", "NATIVE_HANDOFF.md",
            "Guildline/GUILDLINEFORNOLQU.md", ".agents/skills/helper/SKILL.md",
            ".codex/config.toml", ".claude/settings.json", ".cursor/rules.md",
            ".superpowers/sdd/report.json", ".venv-native/bin/python",
            ".migration-archives/state.tar.gz", ".nolqu-mcp/audit.jsonl",
            ".nql/cache.json", "tests/__pycache__/test.pyc", "../private.md",
            "/private.md", "docs/../NolQu-LConcept.docx", ".", "", "./README.md",
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(policy.blocked_reason(path))

    def test_public_contracts_and_bootstrap_evidence_are_kept(self):
        policy = self.policy()
        for path in ("VERSION", "README.md", "docs/project/CHANGELOG.md",
                     "docs/project/PUBLICATION.md", "docs/compiler/LINUX_CI.md",
                     "docs/compiler/NATIVE_TEST_EVIDENCE.md", "bootstrap/manifest.tsv",
                     "bootstrap/compiler/c0/CAPACITY.md", "bootstrap/compiler/c0/NATIVE_OS.md",
                     "bootstrap/compiler/c0/x86_64-linux/c0-backend.seed",
                     "bootstrap/compiler/c0/x86_64-linux/c0-backend.sha256",
                     "tests/meta/test_publication.py", ".github/workflows/linux-qualification.yml"):
            with self.subTest(path=path):
                self.assertIsNone(policy.blocked_reason(path))

    def test_tracked_private_file_fails_even_when_gitignored(self):
        with tempfile.TemporaryDirectory(prefix="publication-control-") as directory:
            work = Path(directory)
            subprocess.run(["git", "init", "-q", str(work)], check=True)
            (work / ".gitignore").write_text("NOLQU_MAJOR_DEVELOPMENT*.md\n")
            private = "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md"
            (work / private).write_text("private notes\n")
            subprocess.run(["git", "-C", str(work), "add", "-f", private, ".gitignore"], check=True)
            result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(work)],
                                    capture_output=True, check=False, timeout=10)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["passed"])
            self.assertEqual([item["path"] for item in report["blocked"]], [private])

    def test_selected_manifest_checks_every_entry(self):
        with tempfile.TemporaryDirectory(prefix="publication-manifest-") as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps({"files": [{"path": "README.md"},
                                                 {"path": "docs/superpowers/plans/task.md"}]}))
            result = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(path)],
                                    capture_output=True, check=False, timeout=10)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)["blocked"]), 1)


if __name__ == "__main__":
    unittest.main()
