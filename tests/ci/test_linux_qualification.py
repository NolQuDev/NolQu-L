"""Linux CI contract and real command-result retention controls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/linux-qualification.yml"
SCRIPT = ROOT / ".github/scripts/linux_qualification.py"


class LinuxCiTests(unittest.TestCase):
    def workflow(self):
        self.assertTrue(WORKFLOW.is_file(), "Linux qualification workflow is absent")
        return yaml.safe_load(WORKFLOW.read_text())

    def module(self):
        self.assertTrue(SCRIPT.is_file(), "Linux qualification runner is absent")
        spec = importlib.util.spec_from_file_location("linux_ci_control", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_workflow_is_read_only_pinned_and_retains_failure_evidence(self):
        workflow = self.workflow()
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertEqual(set(workflow["on"]), {"push", "pull_request", "workflow_dispatch"})
        self.assertEqual(len(workflow["jobs"]), 1)
        job = next(iter(workflow["jobs"].values()))
        self.assertEqual(job["runs-on"], "ubuntu-24.04")
        self.assertLessEqual(job["timeout-minutes"], 60)
        steps = job["steps"]
        uses = [step for step in steps if "uses" in step]
        self.assertEqual(len(uses), 2)
        for step in uses:
            self.assertRegex(step["uses"], r"^actions/[a-z-]+@[0-9a-f]{40}$")
        self.assertFalse(uses[0]["with"]["persist-credentials"])
        self.assertEqual(uses[1]["if"], "always()")
        self.assertEqual(uses[1]["with"]["if-no-files-found"], "error")
        for step in steps:
            self.assertNotIn("continue-on-error", step)
        self.assertTrue(any("linux_qualification.py" in step.get("run", "") for step in steps))

    def test_required_gate_commands_include_real_alias_and_regression_tests(self):
        module = self.module()
        gates = dict(module.GATES)
        self.assertEqual(gates["main"], ["make", "-j1", "test"])
        self.assertIn("discover", gates["mcp"])
        self.assertIn("tests/mcp", gates["mcp"])
        selectors = " ".join(gates["hardlinks"])
        for name in ("test_default_output_rejects_source_tool_and_component_aliases",
                     "test_repeated_hardlinks_keep_public_installation_discoverable",
                     "test_output_aliases_of_sources_components_and_public_tools_are_rejected",
                     "test_protected_paths_hardlinks_and_symlinks",
                     "test_destination_is_rechecked_before_publication"):
            self.assertIn(name, selectors)
        self.assertIn("assurance", gates)
        self.assertIn("release", gates)
        self.assertEqual(gates["publication"], [*module.PYTHON, "tools/check_publication.py"])

    def test_runner_paths_are_defined_in_step_context(self):
        workflow = self.workflow()
        job = next(iter(workflow["jobs"].values()))
        for environment in (workflow.get("env", {}), job.get("env", {})):
            self.assertNotRegex(json.dumps(environment), r"\brunner\s*\.",
                                "runner context is unavailable in workflow/job env")
        gate_step = next(step for step in job["steps"]
                         if "linux_qualification.py" in step.get("run", ""))
        self.assertEqual(gate_step["env"]["NQL_CI_OUTPUT"],
                         "${{ runner.temp }}/nolqu-l-qualification")

    def test_failed_gate_is_retained_and_later_gate_cannot_mask_it(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix="linux-ci-control-") as directory:
            output = Path(directory) / "evidence"
            result = module.run_gates(output, [
                ("bad", [sys.executable, "-c", "import sys;print('before');sys.stderr.write('failed\\n');sys.exit(7)"]),
                ("later", [sys.executable, "-c", "print('after')"]),
            ])
            self.assertFalse(result["passed"])
            self.assertEqual([r["exit_code"] for r in result["gates"]], [7, 0])
            self.assertEqual((output / "calls/0001.stdout").read_bytes(), b"before\n")
            self.assertEqual((output / "calls/0001.stderr").read_bytes(), b"failed\n")
            self.assertEqual((output / "calls/0002.stdout").read_bytes(), b"after\n")
            self.assertEqual(json.loads((output / "result.json").read_text())["status"], "FAILED")

    def test_successful_gates_record_actual_status_and_streams(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix="linux-ci-control-") as directory:
            output = Path(directory) / "evidence"
            result = module.run_gates(output, [("ok", [sys.executable, "-c", "print('ok')"])])
            self.assertTrue(result["passed"])
            self.assertEqual(result["gates"][0]["exit_code"], 0)
            self.assertEqual(result["gates"][0]["invocation"]["control"]["complete"], True)

    def test_existing_evidence_is_not_replaced(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix="linux-ci-control-") as directory:
            output = Path(directory) / "evidence"
            output.mkdir()
            sentinel = output / "result.json"
            sentinel.write_bytes(b"previous evidence")
            marker = Path(directory) / "unexpected"
            with self.assertRaises(FileExistsError):
                module.run_gates(output, [("no", [sys.executable, "-c",
                    f"from pathlib import Path;Path({str(marker)!r}).write_text('ran')"])])
            self.assertFalse(marker.exists())
            self.assertEqual(sentinel.read_bytes(), b"previous evidence")

    def test_final_identity_check_error_cannot_leave_a_passed_report(self):
        module = self.module()
        for failure in (OSError("final read failed"), KeyboardInterrupt("final check interrupted")):
            with self.subTest(error=type(failure).__name__), \
                    tempfile.TemporaryDirectory(prefix="linux-ci-control-") as directory:
                output = Path(directory) / "evidence"
                with mock.patch.object(module, "require_linux_host", return_value={"fixture": True}), \
                        mock.patch.object(module, "identities", side_effect=[{"pin": "before"}, failure]), \
                        mock.patch.object(module, "GATES", [("ok", [sys.executable, "-c", "pass"])]), \
                        mock.patch.object(sys, "argv", [str(SCRIPT), "--output", str(output)]):
                    with self.assertRaises(type(failure)):
                        module.main()
                report = json.loads((output / "result.json").read_text())
                self.assertEqual(report["status"], "FAILED")
                self.assertFalse(report["passed"])
                self.assertEqual(report["error"]["type"], type(failure).__name__)

    def test_android_host_cannot_be_reported_as_linux_qualification(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix="linux-ci-control-") as directory:
            with self.assertRaisesRegex(RuntimeError, "Linux x86_64"):
                module.require_linux_host(Path(directory), system="android", machine="aarch64")


if __name__ == "__main__":
    unittest.main()
