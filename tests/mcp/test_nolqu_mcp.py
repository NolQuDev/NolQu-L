import asyncio
import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MCP_SOURCE = REPO_ROOT / "tools" / "nolqu_mcp.py"


def load_mcp(root: pathlib.Path):
    previous_root = os.environ.get("NOLQU_ROOT")
    os.environ["NOLQU_ROOT"] = str(root)
    try:
        spec = importlib.util.spec_from_file_location(
            f"nolqu_mcp_test_{id(root)}", MCP_SOURCE
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        # Test roots have no Git provenance; keep audit fields without invoking Git.
        module._git_head = lambda: None
        return module
    finally:
        if previous_root is None:
            os.environ.pop("NOLQU_ROOT", None)
        else:
            os.environ["NOLQU_ROOT"] = previous_root


class NolQuMcpCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="nolqu-mcp-test-")
        self.root = pathlib.Path(self.temp_dir.name)
        (self.root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        for name in ("nql", "nqlc"):
            path = self.root / name
            path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            path.chmod(0o755)
        self.mcp = load_mcp(self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_canonical_tool_names_do_not_fall_back_to_removed_names(self):
        self.assertEqual(self.mcp.NQL.name, "nql")
        self.assertEqual(self.mcp.NQLC.name, "nqlc")
        self.assertFalse(hasattr(self.mcp, "NQ"))
        self.assertEqual(self.mcp.FORMAL_NOLQUL.name, "nolqul")
        self.assertEqual(self.mcp.FORMAL_NOLQULC.name, "nolqulc")
        health = self.mcp.ping()
        self.assertIn("nqlc", health)
        self.assertIn("nql", health)

    def test_structured_run_result_has_bounded_stdout(self):
        self.mcp.MAX_STDOUT_BYTES = 96
        result = self.mcp._run_result(
            ["sh", "-c", "i=0; while [ $i -lt 80 ]; do echo line-$i; i=$((i+1)); done"]
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["exit_code"], 0)
        self.assertGreaterEqual(result["duration_ms"], 0)
        self.assertTrue(result["stdout_truncated"])
        self.assertIn("line-0", result["stdout"])
        self.assertIn("line-79", result["stdout"])
        self.assertIn("[truncated", result["stdout"])
        self.assertEqual(result["changed_files"], [])
        self.assertEqual(result["artifacts"], [])

    def test_structured_run_result_converts_os_errors_to_diagnostics(self):
        blocked = self.root / "not-executable"
        blocked.write_text("data\n", encoding="utf-8")
        blocked.chmod(0o644)
        result = self.mcp._run_result([str(blocked)])
        self.assertFalse(result["ok"])
        self.assertIsNone(result["exit_code"])
        self.assertIn("permission denied", result["stderr"].lower())

    def test_atomic_write_rejects_stale_expected_hash(self):
        target = self.root / "sample.nql"
        target.write_text("old\n", encoding="utf-8")
        old_hash = hashlib.sha256(target.read_bytes()).hexdigest()

        ok = self.mcp.write_file(
            "sample.nql", "new\n", expected_sha256=old_hash
        )
        self.assertIn("OK:", ok)
        self.assertEqual(target.read_text(encoding="utf-8"), "new\n")

        stale = self.mcp.patch_file(
            "sample.nql", "new", "changed", expected_sha256=old_hash
        )
        self.assertIn("source changed since read", stale)
        self.assertEqual(target.read_text(encoding="utf-8"), "new\n")
        self.assertEqual(list(self.root.glob(".nolqu-mcp-write-*")), [])

    def test_unsafe_shell_requires_capability_and_confirmation(self):
        os.environ.pop("NOLQU_MCP_ALLOW_UNSAFE_SHELL", None)
        denied = self.mcp.exec_shell("printf ok", confirm=True)
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["capability"], "UNSAFE_SHELL")

        os.environ["NOLQU_MCP_ALLOW_UNSAFE_SHELL"] = "1"
        try:
            unconfirmed = self.mcp.exec_shell("printf ok")
            self.assertFalse(unconfirmed["ok"])
            allowed = self.mcp.exec_shell("printf ok", confirm=True)
            self.assertTrue(allowed["ok"])
            self.assertEqual(allowed["stdout"], "ok")
        finally:
            os.environ.pop("NOLQU_MCP_ALLOW_UNSAFE_SHELL", None)

    def test_tool_manifest_exposes_only_canonical_command_interfaces(self):
        manifest = {item["name"]: item for item in self.mcp.tool_manifest()}
        self.assertEqual(manifest["nql_init"]["stability"], "stable")
        self.assertEqual(manifest["nql_init"]["capability"], "WRITE")
        for removed_name in (
            "nq_init", "nq_build", "nq_run", "nq_test", "nq_check",
            "nq_clean", "nq_version", "nq_fmt", "nq_lint", "nq_doc",
        ):
            self.assertNotIn(removed_name, manifest)
        self.assertEqual(manifest["exec_shell"]["capability"], "UNSAFE_SHELL")
        self.assertEqual(manifest["nql_fmt"]["stability"], "experimental")

    def test_bootstrap_status_is_structured_and_does_not_claim_missing_stages(self):
        status = self.mcp.canonical_bootstrap_status()
        self.assertEqual(status["architecture"], "x86_64-linux")
        self.assertEqual(status["stages"]["machine"]["status"], "NOT_IMPLEMENTED")
        self.assertEqual(status["stages"]["full_compiler"]["status"], "NOT_IMPLEMENTED")
        self.assertEqual(status["stages"]["self_hosting"]["status"], "NOT_IMPLEMENTED")

    def test_c0_frontend_tools_are_experimental_build_tools(self):
        manifest = {item["name"]: item for item in self.mcp.tool_manifest()}
        for name in ("build_c0_frontend", "run_c0_frontend_probe"):
            self.assertIn(name, manifest)
            self.assertEqual(manifest[name]["capability"], "BUILD")
            self.assertEqual(manifest[name]["stability"], "experimental")

    def test_c0_backend_tools_are_experimental_build_tools(self):
        manifest = {item["name"]: item for item in self.mcp.tool_manifest()}
        for name in ("build_c0_backend", "run_c0_backend_probe"):
            self.assertIn(name, manifest)
            self.assertEqual(manifest[name]["capability"], "BUILD")
            self.assertEqual(manifest[name]["stability"], "experimental")

    def test_c0_backend_probe_rejects_missing_artifacts(self):
        self.assertTrue(hasattr(self.mcp, "run_c0_backend_probe"))
        result = self.mcp.run_c0_backend_probe()
        self.assertFalse(result["ok"])
        self.assertEqual(result["probe_status"], "NOT_IMPLEMENTED")
        self.assertFalse(result["full_compiler_verified"])
        self.assertFalse(result["self_hosting_verified"])
        self.assertFalse(result["function_calls_verified"])
        self.assertFalse(result["parameter_scope_verified"])
        self.assertFalse(result["call_statements_verified"])
        self.assertFalse(result["byte_memory_verified"])
        self.assertFalse(result["stream_io_verified"])

    def test_c0_backend_probe_requires_both_pins_and_gate(self):
        self.assertTrue(hasattr(self.mcp, "run_c0_backend_probe"))
        directory = self.root / "bootstrap/compiler/c0"
        (directory / "x86_64-linux").mkdir(parents=True)
        for name in ("frontend", "backend"):
            (directory / f"{name}.nql").write_text(f"# C0 {name}\n")
            seed = directory / "x86_64-linux" / f"c0-{name}.seed"
            seed.write_bytes(name.encode())
            seed.chmod(0o755)
            seed.with_suffix(".sha256").write_text(hashlib.sha256(seed.read_bytes()).hexdigest() + f"  c0-{name}.seed\n")
        wrapper = directory / "x86_64-linux/compile-source.sh"
        wrapper.write_text("#!/bin/sh\nexit 0\n")
        gate = self.root / "tests/bootstrap/c0_backend.sh"
        gate.parent.mkdir(parents=True)
        gate.write_text("#!/bin/sh\nexit 0\n")
        for passed in (True, False):
            with self.subTest(passed=passed), mock.patch.object(self.mcp, "_run_result", return_value={
                "ok": passed, "exit_code": 0 if passed else 1, "stdout": "", "stderr": "",
            }):
                result = self.mcp.run_c0_backend_probe()
            self.assertFalse(result["ok"])
            self.assertFalse(result["semantic_resolution_verified"])
            self.assertFalse(result["codegen_verified"])
            self.assertEqual(result["backend_version"], "C0.32")
            self.assertEqual(result["source_capacity"], 262144)
            self.assertEqual(result["token_capacity"], 65536)
            self.assertEqual(result["node_capacity"], 65536)
            self.assertIn("NQAF/5", result["input_format"])
            self.assertEqual(result["compiler_profile_byte_capacity"], 16777216)
            self.assertFalse(result["control_flow_verified"])
            self.assertFalse(result["lexical_scope_verified"])
            self.assertFalse(result["function_calls_verified"])
            self.assertFalse(result["parameter_scope_verified"])
            self.assertFalse(result["call_statements_verified"])
            self.assertFalse(result["byte_memory_verified"])
            self.assertFalse(result["stream_io_verified"])
            self.assert_c031_unverified(result)
            self.assertEqual(result["byte_memory_capacity"], 65536)
            self.assertEqual(result["call_depth_capacity"], 64)
            self.assertEqual(result["parameter_capacity"], 6)
            self.assertEqual(result["built_by"], "B0")
            self.assertFalse(result["full_compiler_verified"])
            self.assertFalse(result["self_hosting_verified"])
        (directory / "x86_64-linux/c0-frontend.seed").write_bytes(b"changed")
        with mock.patch.object(self.mcp, "_run_result") as run:
            result = self.mcp.run_c0_backend_probe()
        self.assertFalse(result["ok"])
        run.assert_not_called()

    def test_c0_frontend_probe_does_not_verify_missing_artifacts(self):
        self.assertTrue(hasattr(self.mcp, "run_c0_frontend_probe"))
        result = self.mcp.run_c0_frontend_probe()
        self.assertFalse(result["ok"])
        self.assertEqual(result["probe_status"], "NOT_IMPLEMENTED")
        self.assertFalse(result["full_compiler_verified"])

    def test_c0_frontend_probe_requires_pinned_artifact_and_successful_gate(self):
        self.assertTrue(hasattr(self.mcp, "run_c0_frontend_probe"))
        directory = self.root / "bootstrap/compiler/c0"
        (directory / "x86_64-linux").mkdir(parents=True)
        (directory / "frontend.nql").write_text("# C0.26 source-to-AST frontend\n")
        seed = directory / "x86_64-linux/c0-frontend.seed"
        seed.write_bytes(b"test-frontend-artifact")
        seed.chmod(0o755)
        (seed.with_suffix(".sha256")).write_text(hashlib.sha256(seed.read_bytes()).hexdigest() + "  c0-frontend.seed\n")
        gate = self.root / "tests/bootstrap/c0_frontend.sh"
        gate.parent.mkdir(parents=True)
        gate.write_text("#!/bin/sh\nexit 0\n")
        with mock.patch.object(self.mcp, "_run_result", return_value={
            "ok": True, "exit_code": 0, "timed_out": False, "stdout": "PASS c0-frontend\n", "stderr": "",
        }) as run:
            result = self.mcp.run_c0_frontend_probe()
        self.assertFalse(result["ok"])
        self.assertEqual(result["probe_status"], "UNEXPECTED_RESULT")
        self.assertEqual(result["frontend_version"], "C0.32")
        self.assertIn("NQAF/5", result["format"])
        self.assertEqual(result["source_capacity"], 262144)
        self.assertEqual(result["token_capacity"], 65536)
        self.assertEqual(result["node_capacity"], 65536)
        self.assertEqual(result["byte_memory_capacity"], 65536)
        self.assertEqual(result["compiler_profile_byte_capacity"], 16777216)
        self.assertFalse(result["call_statements_verified"])
        self.assertEqual(result["block_depth_capacity"], 64)
        self.assertEqual(result["parameter_capacity"], 6)
        self.assertEqual(result["built_by"], "B0")
        self.assertFalse(result["full_compiler_verified"])
        self.assert_c031_unverified(result)
        run.assert_not_called()
        with mock.patch.object(self.mcp, "_run_result", return_value={
            "ok": False, "exit_code": 1, "timed_out": False, "stdout": "", "stderr": "FAIL tree",
        }):
            self.assertFalse(self.mcp.run_c0_frontend_probe()["ok"])
        seed.write_bytes(b"changed")
        with mock.patch.object(self.mcp, "_run_result") as run:
            result = self.mcp.run_c0_frontend_probe()
        self.assertFalse(result["ok"])
        self.assertEqual(result["probe_status"], "HASH_MISMATCH")
        run.assert_not_called()

    def test_frontend_presence_is_not_full_compiler_promotion(self):
        status = self.mcp.canonical_bootstrap_status()
        self.assertIn("c0_frontend", status["stages"])
        self.assertEqual(status["stages"]["c0_frontend"]["built_by"], "B0")
        self.assertEqual(status["stages"]["full_compiler"]["status"], "NOT_IMPLEMENTED")
        self.assertEqual(status["stages"]["self_hosting"]["status"], "NOT_IMPLEMENTED")

    def c031_probe_fixture(self):
        shutil.copytree(REPO_ROOT / "bootstrap", self.root / "bootstrap")
        shutil.copytree(REPO_ROOT / "tests/bootstrap", self.root / "tests/bootstrap",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(REPO_ROOT / "tests/shared", self.root / "tests/shared")
        shutil.copytree(REPO_ROOT / "examples/canonical", self.root / "examples/canonical")
        (self.root / "tools").mkdir()
        shutil.copy2(MCP_SOURCE, self.root / "tools/nolqu_mcp.py")

    def assert_c031_unverified(self, result):
        for field in ("capacity_verified", "compiler_profile_verified",
                      "component_generation_verified", "unsafe_blocks_verified", "process_arguments_verified",
                      "syscall_abi_verified", "full_compiler_verified",
                      "self_hosting_verified"):
            self.assertIn(field, result, field)
            self.assertIs(result[field], False, field)

    def c031_gate_result(self, command, directory, timeout, env=None):
        # A command-boundary double only; it supplies no generation proof.
        markers = {
            "c0_frontend": "PASS c0-frontend\n",
            "c0_backend": ("PASS c0-control-flow\nPASS c0-functions\nPASS c0-runtime-io\n"
                           "PASS c0-capacity-backend\nPASS c0-native-os\nPASS c0-backend\n"),
            "c0_capacity": "PASS c0-capacity\nPASS c0-component-generations\n",
        }
        name = pathlib.Path(command[-1]).stem
        directory.mkdir()
        stdout = markers[name]
        stderr = ("".join(f"\nRan {count} tests in 1.0s\n\nOK\n" for count in (18, 28, 20, 6))
                  if name == "c0_capacity" else "\nRan 23 tests in 1.0s\n\nOK\n" if name == "c0_backend" else "")
        (directory / "stdout").write_text(stdout)
        (directory / "stderr").write_text(stderr)
        return dict(ok=True, exit_code=0, timed_out=False, cleanup_complete=True,
                    interrupted=False, leaked_descendants=False, command=command,
                    stdout=stdout, stderr=stderr, duration_ms=0)

    def test_c031_valid_fixture_reaches_generation_validation(self):
        self.c031_probe_fixture()
        gate = self.root / "tests/bootstrap/c0_capacity.sh"
        self.assertEqual(self.mcp._sha256(gate), self.mcp._C031_GATE_SHA256)
        self.assertTrue(self.mcp._c031_inputs())
        def unit_validate(directory, before):
            # Handmade trace bytes, not a run of the compiler/generation gates.
            work, receipt = NativeProofTests.machine_fixture(self, directory)
            return {"unit_only_validation_control": True,
                    "native_machine_artifacts": self.mcp._c031_native_evidence(receipt, work)}

        for probe in (self.mcp.run_c0_frontend_probe, self.mcp.run_c0_backend_probe):
            # Unit-only positive control of the command/validator seam, not real proof.
            with self.subTest(probe=probe.__name__), mock.patch.object(
                    self.mcp, "_c031_command", side_effect=self.c031_gate_result) as command, mock.patch.object(
                    self.mcp, "_c031_validate", side_effect=unit_validate) as validate:
                result = probe()
                self.assertEqual([pathlib.Path(call.args[0][-1]).stem for call in command.call_args_list],
                                 ["c0_frontend", "c0_backend", "c0_capacity"])
                validate.assert_called_once()
                self.assertTrue(result["ok"])
                self.assertTrue(result["evidence"]["unit_only_validation_control"])
                for field in self.mcp._C031_FLAGS:
                    self.assertIs(result[field], True)
                self.assertFalse(result["full_compiler_verified"])
                self.assertFalse(result["self_hosting_verified"])
                self.assertIsNone(self.mcp._C031_SCOPE.get())

    def test_c031_capacity_evidence_fails_closed(self):
        self.c031_probe_fixture()
        gate = self.root / "tests/bootstrap/c0_capacity.sh"
        source = self.root / "bootstrap/compiler/c0/frontend.nql"
        seed = self.root / "bootstrap/compiler/c0/x86_64-linux/c0-backend.seed"
        original = {path: path.read_bytes() for path in (gate, source, seed)}
        self.assertTrue(self.mcp._c031_inputs())
        for failure in ("missing-gate", "corrupt-seed", "changed-source",
                        "nonzero", "timeout", "markers-only"):
            for probe in (self.mcp.run_c0_frontend_probe, self.mcp.run_c0_backend_probe):
                for path, data in original.items():
                    path.write_bytes(data)
                if failure == "missing-gate":
                    gate.unlink()
                elif failure == "corrupt-seed":
                    seed.write_bytes(b"changed")

                def run(*args, **kwargs):
                    observed = self.c031_gate_result(*args, **kwargs)
                    if failure == "changed-source":
                        source.write_bytes(original[source] + b"\n")
                    elif failure == "nonzero":
                        observed.update(ok=False, exit_code=1)
                    elif failure == "timeout":
                        observed.update(ok=False, exit_code=None, timed_out=True)
                    return observed

                with self.subTest(failure=failure, probe=probe.__name__), mock.patch.object(
                        self.mcp, "_c031_command", side_effect=run) as command, mock.patch.object(
                        self.mcp, "_c031_validate", wraps=self.mcp._c031_validate) as validate, mock.patch.object(
                        self.mcp, "_run_result", side_effect=AssertionError("unused legacy command path")):
                    result = probe()
                    self.assert_c031_unverified(result)
                    reason = result.get("blocker", result.get("error", ""))
                    expected_calls = {"missing-gate": 0, "corrupt-seed": 0, "changed-source": 1,
                                      "nonzero": 1, "timeout": 1, "markers-only": 3}[failure]
                    self.assertEqual(command.call_count, expected_calls)
                    if failure == "missing-gate":
                        self.assertIn("c0_capacity.sh", reason)
                    elif failure == "corrupt-seed":
                        self.assertRegex(reason, r"pinned executable is unavailable or invalid: c0_backend|component artifact is missing or does not match")
                    elif failure == "changed-source":
                        self.assertEqual(reason, "input identity changed during c0_frontend")
                    elif failure in ("nonzero", "timeout"):
                        self.assertEqual(reason, "c0_frontend failed or did not reap its owned children")
                        self.assertEqual(result["timed_out"], failure == "timeout")
                        self.assertEqual(result["exit_code"], None if failure == "timeout" else 1)
                        self.assertEqual(result["probe_status"], "TIMED_OUT" if failure == "timeout" else "UNEXPECTED_RESULT")
                    else:
                        self.assertEqual(reason, "missing or duplicate actual-source generation receipt")
                    if failure == "markers-only":
                        validate.assert_called_once()
                    else:
                        validate.assert_not_called()
                    expected_changes = {"missing-gate": {gate}, "corrupt-seed": {seed},
                                        "changed-source": {source}}.get(failure, set())
                    self.assertEqual({path for path, data in original.items()
                                      if not path.exists() or path.read_bytes() != data}, expected_changes)
                    self.assertIsNone(self.mcp._C031_SCOPE.get())
        self.assertEqual(self.mcp._sha256(gate), self.mcp._C031_GATE_SHA256)

    def test_c031_generation_evidence_does_not_promote_full_compiler(self):
        self.c031_probe_fixture()
        before = self.mcp._c031_inputs()
        inputs = {
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
            inputs.update(str(path.relative_to(self.root)) for path in self.root.glob(pattern))
        fabricated = dict(component_generations_verified=True, identities={}, stages=[],
                          artifacts={}, comparisons=[], checks=[], rejections=[], oracles=[], cwd=str(self.root),
                          argv=[str(self.root / "tests/bootstrap/test_c0_component_generations.py"), "-v"])
        fabricated["identities"] = {str((self.root / name).resolve()): {key: before[name][key]
                                    for key in ("bytes", "sha256")} for name in inputs}

        def run(command, directory, timeout, env=None):
            observed = self.c031_gate_result(command, directory, timeout, env)
            if pathlib.Path(command[-1]).name == "c0_capacity.sh":
                receipt = pathlib.Path(env["C031_WORK"]) / "test_actual_sources_build_and_rebuild-fabricated"
                receipt.mkdir()
                (receipt / "receipt.json").write_text(json.dumps(fabricated))
            return observed

        for probe in (self.mcp.run_c0_frontend_probe, self.mcp.run_c0_backend_probe):
            with self.subTest(probe=probe.__name__), mock.patch.object(
                    self.mcp, "_c031_command", side_effect=run) as command, mock.patch.object(
                    self.mcp, "_c031_validate", wraps=self.mcp._c031_validate) as validate, mock.patch.object(
                    self.mcp, "_c031_records", wraps=self.mcp._c031_records) as records:
                result = probe()
                self.assert_c031_unverified(result)
                self.assertEqual(command.call_count, 3)
                validate.assert_called_once()
                records.assert_called_once()
                self.assertEqual(records.call_args.args[0], [])
                self.assertEqual(len(records.call_args.args[1]), 275)
                self.assertEqual(result["blocker"], "incomplete or duplicate label set")
                self.assertEqual(validate.call_args.args[1], before)
                self.assertIsNone(self.mcp._C031_SCOPE.get())
        for stage in ("full_compiler", "self_hosting", "verified"):
            self.assertEqual(self.mcp.canonical_bootstrap_status()["stages"][stage]["status"],
                             "NOT_IMPLEMENTED")

    def test_c031_scoped_runner_preserves_raw_output_before_display_truncation(self):
        self.mcp.MAX_STDOUT_BYTES = 96
        result = self.mcp._c031_command(
            [sys.executable, "-c", "print('x' * 512)"], self.root / "command", 5)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["cleanup_complete"])
        self.assertTrue(result["stdout_truncated"])
        raw = pathlib.Path(result["stdout_file"]["path"]).read_bytes()
        self.assertEqual(raw, b"x" * 512 + b"\n")
        self.assertEqual(result["stdout_file"]["sha256"], hashlib.sha256(raw).hexdigest())

    def test_c031_scoped_timeout_reaps_descendant_in_another_session(self):
        pid_file = self.root / "child.pid"
        script = ("import pathlib,subprocess,sys,time\n"
                  "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True)\n"
                  "pathlib.Path(sys.argv[1]).write_text(str(child.pid))\n"
                  "time.sleep(60)\n")
        result = self.mcp._c031_command([sys.executable, "-c", script, str(pid_file)],
                                        self.root / "timeout", 5)
        self.assertFalse(result["ok"])
        self.assertTrue(result["timed_out"])
        self.assertTrue(result["cleanup_complete"], result)
        self.assertTrue(pid_file.is_file(), result)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(pid_file.read_text()), 0)

    def test_c031_metadata_resource_does_not_execute_verification(self):
        with mock.patch.object(self.mcp.subprocess, "Popen", side_effect=AssertionError("metadata launched a compiler")):
            text = self.mcp.current_development_resource()
            metadata = self.mcp.canonical_bootstrap_status()
        self.assertIn("fresh_probe_required", text)
        self.assert_c031_unverified(metadata)

    def test_c031_b0_build_stages_do_not_consume_nqaf(self):
        # A private parser fixture, not executable generation/capability evidence.
        directory = self.root / "test_actual_sources_build_and_rebuild-parser"
        directory.mkdir()
        fingerprints = lambda data: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        inputs = {
            "bootstrap/compiler/c0/frontend.nql", "bootstrap/compiler/c0/backend.nql",
            "tests/bootstrap/test_c0_component_generations.py", "tests/bootstrap/c031_support.py",
            "tests/bootstrap/c031_debugger.py", "tests/bootstrap/c0_capacity.sh",
            "tests/bootstrap/c032_support.py", "examples/canonical/native_cat.nql",
            "tests/bootstrap/c0_native_os.sh", "tests/bootstrap/fixtures/c032/predecessor/hashes.json",
            "bootstrap/compiler/b0/compiler.nql0", "bootstrap/stage0/x86_64-linux/stage0.seed",
            "tests/bootstrap/fixtures/c031/predecessor/hashes.json",
        }
        definition = ast.parse((REPO_ROOT / "tests/bootstrap/test_c0_component_generations.py").read_text())
        selectors = next(ast.literal_eval(n.value) for n in definition.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "GENERATION_ORACLES" for t in n.targets))
        predecessors = {name: fingerprints(name.encode())["sha256"]
                        for name in ("b0.seed", "c0-frontend.seed", "c0-backend.seed")}
        for name in inputs:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")
        (self.root / "tests/bootstrap/test_c0_component_generations.py").write_text(
            "GENERATION_ORACLES = " + repr(selectors) + "\n")
        (self.root / "tests/bootstrap/fixtures/c031/predecessor/hashes.json").write_text(
            json.dumps(dict(artifacts=predecessors)))
        before = {name: self.mcp._c031_fingerprint(self.root / name) for name in inputs}
        artifacts = {}
        for generation in ("A1", "A2", "B", "C", "predecessor"):
            for component in (("b0", "frontend", "backend") if generation == "predecessor"
                              else ("frontend", "backend")):
                label = generation + "-" + component
                data = ("b0.seed" if component == "b0" else f"c0-{component}.seed").encode()
                path = directory / (label + ".artifact")
                path.write_bytes(data)
                artifacts[label] = dict(path=str(path), **fingerprints(data))
                if generation == "A1":
                    before[f"bootstrap/compiler/c0/x86_64-linux/c0-{component}.seed"] = fingerprints(data)
        identity = lambda label: {key: artifacts[label][key] for key in ("bytes", "sha256")}
        pairs = {**{f"A1-A2-{c}": (f"A1-{c}", f"A2-{c}") for c in ("frontend", "backend")},
                 **{f"selected-A1-{c}": (f"A1-{c}", f"A1-{c}") for c in ("frontend", "backend")},
                 **{f"B-C-{c}": (f"B-{c}", f"C-{c}") for c in ("frontend", "backend")}}
        stages = []
        for generation in ("A1", "A2"):
            for component in ("frontend", "backend"):
                label = generation + "-" + component
                prefix = directory / f"{len(stages):03d}-{label}"
                for suffix in ("stdin", "stdout", "stderr"):
                    pathlib.Path(str(prefix) + "." + suffix).write_bytes(b"")
                stages.append(dict(label=label, prefix=str(prefix), returncode=0, timed_out=False,
                                   binary=str(self.root / "bootstrap/compiler/b0/x86_64-linux/b0.seed"),
                                   command=["b0.seed", "--compiler-profile"],
                                   input=fingerprints(b""), stdout=fingerprints(b""), stderr=fingerprints(b"")))
        oracles = []
        for generation in ("B", "C"):
            components = {c: dict(path=str(directory / (generation + "-" + c)),
                                  **identity(generation + "-" + c)) for c in ("frontend", "backend")}
            oracles.append(dict(generation=generation, components=components, selectors=selectors,
                                returncode=0, timed_out=False, child_reaped=True, temporary_removed=True,
                                environment={"C0_FRONTEND": components["frontend"]["path"],
                                             "C0_BACKEND": components["backend"]["path"],
                                             "PYTHONPATH": str(self.root / "tests/bootstrap"),
                                             "C032_NATIVE_EVIDENCE_DIR": str(directory / (generation + "-native-machine"))}))
        receipt = dict(component_generations_verified=True, rejections=[], cwd=str(self.root),
                       argv=[str(self.root / "tests/bootstrap/test_c0_component_generations.py"), "-v"],
                       identities={str((self.root / name).resolve()): before[name] for name in inputs},
                       checks=[dict(label="parser", passed=True)], stages=stages, artifacts=artifacts,
                       comparisons=[dict(label=k, left=identity(a), right=identity(b), first_difference_offset=None)
                                    for k, (a, b) in pairs.items()], oracles=oracles,
                       predecessor_builder="c031_support.build_predecessors",
                       machine_evidence={g: dict(directory=str(directory / (g + "-native-machine"))) for g in ("B", "C")})
        (directory / "receipt.json").write_text(json.dumps(receipt))
        with mock.patch.object(self.mcp, "_c031_native_evidence", return_value={}), mock.patch.object(
                self.mcp, "_c031_inputs", return_value=before), mock.patch.object(
                self.mcp, "_c031_contract", return_value=(
                    {s["label"]: (0, b"") for s in stages}, {"parser"}, set(artifacts))):
            parsed = self.mcp._c031_validate(self.root, before)
        self.assertEqual(parsed["stages"], 4)
        self.assertNotIn("capacity_verified", parsed)

    def test_c031_combined_late_invalidation_clears_success_status(self):
        def components():
            self.mcp._C031_SCOPE.get()["proof"] = dict(
                ok=True, input_identities={}, gates=[], timed_out=False, exit_code=0)
            component = dict(ok=True, parse_complete=True, probe_status="SOURCE_AST_TO_ELF_VERIFIED",
                             exit_code=0, timed_out=False, stderr="", blocker="next workload",
                             evidence=self.mcp._C031_SCOPE.get()["proof"],
                             **dict.fromkeys(self.mcp._C031_FLAGS, True))
            return dict(ok=True, parse_complete=True, probe_status="SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED",
                        exit_code=0, timed_out=False, stderr="", blocker="next workload",
                        bounded_generation_verified=True, emitter_parse_complete=True,
                        generation_c_identical=True, generation_d_identical=True,
                        diagnostic_identical=True, source_expectation_matches=True,
                        frontend=dict(component), backend=dict(component))

        with mock.patch.object(self.mcp, "_run_c0_probe", side_effect=components), mock.patch.object(
                self.mcp, "_c031_inputs", return_value={"changed-input": {}}):
            result = self.mcp.run_c0_probe()
        self.assertFalse(result["ok"])
        self.assertEqual(result["probe_status"], "UNEXPECTED_RESULT")
        self.assertFalse(result["parse_complete"])
        self.assertIsNone(result["exit_code"])
        self.assertFalse(result["timed_out"])
        self.assertFalse(result["bounded_generation_verified"])
        for item in (result, result["frontend"], result["backend"]):
            self.assertFalse(item["ok"])
            self.assertEqual(item["probe_status"], "UNEXPECTED_RESULT")
            self.assertIn("input identity changed", item["error"])
            self.assertEqual(item["blocker"], item["error"])
            self.assertEqual(item["stderr"], item["error"])
            self.assertIsNone(item["exit_code"])
            self.assertFalse(item["parse_complete"])
            for field, value in item.items():
                if field.endswith(("_verified", "_complete", "_identical")) or field == "source_expectation_matches":
                    self.assertIs(value, False, field)
        for item in (result["frontend"], result["backend"]):
            self.assertFalse(item["evidence"]["ok"])
            self.assertEqual(item["evidence"]["error"], item["error"])
        self.assert_c031_unverified(result)
        self.assertIsNone(self.mcp._C031_SCOPE.get())

    def test_c031_scope_shares_only_within_one_invocation(self):
        marker = object()
        with self.mcp._c031_scope() as first:
            first["proof"] = marker
            with self.mcp._c031_scope() as nested:
                self.assertIs(nested, first)
                self.assertIs(nested["proof"], marker)
        self.assertIsNone(self.mcp._C031_SCOPE.get())
        with self.assertRaisesRegex(RuntimeError, "interrupted invocation"):
            with self.mcp._c031_scope() as second:
                self.assertIsNot(second, first)
                self.assertIsNone(second["proof"])
                raise RuntimeError("interrupted invocation")
        self.assertIsNone(self.mcp._C031_SCOPE.get())

    def test_x86_bootstrap_runner_uses_qemu_on_aarch64(self):
        executable = self.root / "c0.seed"
        with mock.patch.object(
            self.mcp.shutil, "which", return_value="/usr/bin/qemu-x86_64"
        ):
            command = self.mcp._x86_runner(executable, machine="aarch64")
        self.assertEqual(command, ["/usr/bin/qemu-x86_64", str(executable)])

    def test_mcp_self_test_checks_path_escape_and_temp_cleanup(self):
        result = self.mcp.mcp_self_test()
        self.assertTrue(result["ok"])
        checks = {item["name"]: item for item in result["checks"]}
        self.assertTrue(checks["root"]["ok"])
        self.assertTrue(checks["safe_path_escape"]["ok"])
        self.assertTrue(checks["atomic_temp_cleanup"]["ok"])

    def test_migration_verifier_uses_nql_source_and_cleans_unique_temp_dir(self):
        tools_dir = self.root / "tools"
        tools_dir.mkdir()
        (tools_dir / "nql_ir_dump_parser.py").write_text(
            "import pathlib, sys\n"
            "pathlib.Path(sys.argv[2]).write_bytes(pathlib.Path(sys.argv[1]).read_bytes())\n"
            "print(f'OK: {sys.argv[2]}')\n",
            encoding="utf-8",
        )
        nql_source = tools_dir / "nql_ir_dump_parser.nql"
        nql_source.write_text(
            "#!/bin/sh\ncp \"$1\" \"$2\"\nprintf 'OK: %s\\n' \"$2\"\n",
            encoding="utf-8",
        )
        nql_source.chmod(0o755)
        self.mcp.NQLC.write_text(
            "#!/bin/sh\n"
            "src=$1\n"
            "shift\n"
            "test \"$1\" = -o || exit 2\n"
            "cp \"$src\" \"$2\"\n"
            "chmod +x \"$2\"\n",
            encoding="utf-8",
        )
        self.mcp.NQLC.chmod(0o755)

        result = self.mcp.verify_migration(
            "nql_ir_dump_parser", test_input="hello\n"
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["exit_codes_identical"])
        self.assertTrue(result["stdout_identical"])
        self.assertTrue(result["stderr_identical"])
        self.assertTrue(result["deterministic_artifact"])
        self.assertEqual(
            result["artifact_sha256_first"],
            result["artifact_sha256_second"],
        )
        migration = self.mcp.migration_status()
        self.assertEqual(
            migration["tools"]["nql_ir_dump_parser"]["source"],
            "tools/nql_ir_dump_parser.nql",
        )
        temp_root = self.root / ".nolqu-mcp" / "tmp"
        self.assertEqual(list(temp_root.iterdir()) if temp_root.exists() else [], [])

    def test_destructive_and_remote_tools_require_explicit_boundaries(self):
        victim = self.root / "victim.nql"
        victim.write_text("data\n", encoding="utf-8")
        denied = self.mcp.delete_file("victim.nql")
        self.assertIn("confirm=true", denied)
        self.assertTrue(victim.exists())
        allowed = self.mcp.delete_file("victim.nql", confirm=True)
        self.assertIn("OK:", allowed)
        self.assertFalse(victim.exists())

        os.environ.pop("NOLQU_MCP_ALLOW_REMOTE", None)
        remote = self.mcp.git_push(confirm=True)
        self.assertIsInstance(remote, dict)
        self.assertFalse(remote["ok"])
        self.assertEqual(remote["capability"], "REMOTE")

    def test_resources_and_prompts_expose_canonical_architecture(self):
        architecture = self.mcp.architecture_resource()
        self.assertIn("Machine-Level Foundation", architecture)
        self.assertIn("Full NolQu-L Compiler", architecture)
        self.assertNotIn("LLVM\n        ↓", architecture)
        workflow = self.mcp.develop_c0_milestone()
        self.assertIn("first measured blocker", workflow)
        self.assertIn("Do not generalize", workflow)
        self.assertIn("NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md", workflow)
        self.assertIn("docs/project/CHANGELOG.md", workflow)
        self.assertIn("out of public pushes", workflow)

    def test_authority_resources_read_exact_headings_from_revised_document(self):
        # Original headings below are exact legacy input fixtures. Generated
        # messages use English; reading a source section preserves its bytes.
        sections = (
            ("1. NINE PILLARS OF NOLQU-L", "Revised compatibility policy."),
            ("7. LEXER", "Lexer contract."),
            ("8. PARSER", "Parser contract."),
            ("12. NOLQU IR", "IR contract."),
            ("33. FFI DAN ABI", "ABI contract."),
            ("39. DIAGNOSTIC SYSTEM", "Diagnostic contract."),
        )
        document = "See `# 1. NINE PILLARS OF NOLQU-L` below.\n"
        document += "# 1. NINE PILLARS OF NOLQU-L INDEX\nNot the policy.\n"
        rendered = []
        for title, body in sections:
            section = f"# {title}\n\n{body}\n## Details\nKeep subsections.\n"
            document += section + "\n"
            rendered.append(section)
        (self.root / "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md").write_text(
            document, encoding="utf-8"
        )
        (self.root / "NOLQU_MAJOR_DEVELOPMENT.md").write_text(
            "# 1. NINE PILLARS OF NOLQU-L\nObsolete policy.\n", encoding="utf-8"
        )
        for resource, expected in (
            (self.mcp.nine_pillars_resource, rendered[0]),
            (self.mcp.grammar_resource, rendered[1] + "\n" + rendered[2]),
            (self.mcp.ir_resource, rendered[3]),
            (self.mcp.abi_resource, rendered[4]),
            (self.mcp.diagnostics_resource, rendered[5]),
        ):
            with self.subTest(resource=resource.__name__):
                self.assertEqual(resource(), expected)

    def test_abi_resource_prefers_english_heading_and_keeps_legacy_input(self):
        authority = self.root / "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md"
        english = "# 33. FFI AND ABI\n\nEnglish ABI contract.\n"
        legacy = "# 33. FFI DAN ABI\n\nLegacy ABI contract.\n"
        authority.write_text(legacy + english, encoding="utf-8")
        self.assertEqual(self.mcp.abi_resource(), english)
        authority.write_text(legacy, encoding="utf-8")
        self.assertEqual(self.mcp.abi_resource(), legacy)

    def test_c0_version_reads_english_authority_without_overriding_source(self):
        authority = self.root / "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md"
        authority.write_text(
            "Core Compiler through subphase C0.18\n"
            "Core Compiler emitter through subphase C0.25\n", encoding="utf-8"
        )
        self.assertEqual(self.mcp._current_c0_version(), "C0.25")
        c0_dir = self.root / "bootstrap/compiler/c0"
        c0_dir.mkdir(parents=True)
        (c0_dir / "compiler.nql").write_text("# C0.19 emitter\n", encoding="utf-8")
        self.assertEqual(self.mcp._current_c0_version(), "C0.19")

    def test_authority_resources_do_not_fall_back_to_obsolete_document(self):
        (self.root / "NOLQU_MAJOR_DEVELOPMENT.md").write_text(
            "# 1. NINE PILLARS OF NOLQU-L\nObsolete policy.\n", encoding="utf-8"
        )
        self.assertEqual(
            self.mcp.nine_pillars_resource(),
            "ERROR: NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md is missing",
        )
        (self.root / "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md").write_text(
            "See `# 1. NINE PILLARS OF NOLQU-L` in the missing section.\n",
            encoding="utf-8",
        )
        self.assertEqual(
            self.mcp.nine_pillars_resource(),
            "ERROR: section not found: 1. NINE PILLARS OF NOLQU-L",
        )

    def test_c0_version_fallback_uses_revised_authority_but_source_wins(self):
        # Preserve the original wording to test historical input compatibility.
        (self.root / "NOLQU_MAJOR_DEVELOPMENT.md").write_text(
            "Core Compiler sampai subfase C0.99\n", encoding="utf-8"
        )
        self.assertEqual(self.mcp._current_c0_version(), "unknown")
        (self.root / "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md").write_text(
            "Core Compiler sampai subfase C0.18\n"
            "Core Compiler emitter sampai subfase C0.25\n",
            encoding="utf-8",
        )
        self.assertEqual(self.mcp._current_c0_version(), "C0.25")
        c0_dir = self.root / "bootstrap/compiler/c0"
        c0_dir.mkdir(parents=True)
        (c0_dir / "compiler.nql").write_text("# C0.19 emitter\n", encoding="utf-8")
        self.assertEqual(self.mcp._current_c0_version(), "C0.19")

    def test_c0_probe_reports_complete_parse_before_full_emission(self):
        (self.root / "NOLQU_MAJOR_DEVELOPMENT.md").write_text(
            "Core Compiler sampai subfase C0.18 sekarang PASS.\n",
            encoding="utf-8",
        )
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.18 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"seed")
        (c0_dir / "successor.nq").write_text("complete successor\n", encoding="utf-8")
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        (fixture / "successor_parse_stmts.nq").write_text(
            "parser fixture\n", encoding="utf-8"
        )
        parser_build = subprocess.CompletedProcess(
            args=["c0"], returncode=0, stdout=b"parser", stderr=b"",
        )
        parsed = subprocess.CompletedProcess(
            args=["parser"], returncode=0, stdout=b"", stderr=b"",
        )
        with mock.patch.object(
            self.mcp, "_x86_runner", side_effect=(["c0"], ["parser"])
        ), mock.patch.object(
            self.mcp.subprocess, "run", side_effect=(parser_build, parsed)
        ):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.18")
        self.assertEqual(result["probe_status"], "PARSED")
        self.assertIsNone(result["source_line"])
        self.assertEqual(result["blocker"], "full compiler emission")
        self.assertTrue(result["parse_complete"])
        self.assertIn(
            {"milestone": "C0.18", "blocker": "full compiler emission", "line": None},
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c019_bounded_generations(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.19 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        (fixture / "successor_self_emit.nq").write_text(
            "self emitter fixture\n", encoding="utf-8"
        )
        compiler_output = b"\x7fELFbounded-generation"
        compile_result = subprocess.CompletedProcess(
            args=["c0"], returncode=0, stdout=compiler_output, stderr=b"",
        )
        generation_c = subprocess.CompletedProcess(
            args=["generation-b"], returncode=0,
            stdout=compiler_output, stderr=b"",
        )
        generation_d = subprocess.CompletedProcess(
            args=["generation-c"], returncode=0,
            stdout=compiler_output, stderr=b"",
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(["c0"], ["generation-b"], ["generation-c"]),
        ), mock.patch.object(
            self.mcp.subprocess, "run",
            side_effect=(compile_result, generation_c, generation_d),
        ):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.19")
        self.assertEqual(result["probe_status"], "BOUNDED_GENERATION_VERIFIED")
        self.assertEqual(result["blocker"], "general full compiler implementation")
        self.assertTrue(result["parse_complete"])
        self.assertTrue(result["bounded_generation_verified"])
        self.assertTrue(result["generation_c_identical"])
        self.assertTrue(result["generation_d_identical"])
        self.assertIn(
            {
                "milestone": "C0.19",
                "blocker": "general full compiler implementation",
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c020_indirect_source_scan(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.20 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        (fixture / "runtime_byte_load_at.nq").write_text(
            "indirect load fixture\n", encoding="utf-8"
        )
        (fixture / "runtime_byte_load_at_scan.nq").write_text(
            "source scan fixture\n", encoding="utf-8"
        )
        (fixture / "successor_self_emit.nq").write_text(
            "self emitter fixture\n", encoding="utf-8"
        )

        scan_input = b"fn main(){\nreturn 42}\n"
        compiler_output = b"\x7fELFbounded-generation"
        results = (
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-load", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-load"], returncode=90,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-scan", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-scan"], returncode=0,
                stdout=scan_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-b"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-c"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(
                ["c0"], ["indirect-load"], ["c0"], ["source-scan"],
                ["c0"], ["generation-b"], ["generation-c"],
            ),
        ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.20")
        self.assertEqual(
            result["probe_status"],
            "INDIRECT_LOAD_AND_BOUNDED_GENERATION_VERIFIED",
        )
        self.assertTrue(result["indirect_load_verified"])
        self.assertTrue(result["source_scan_verified"])
        self.assertTrue(result["bounded_generation_verified"])
        self.assertEqual(
            result["blocker"],
            "indirect byte store for source-driven token tables",
        )
        self.assertIn(
            {
                "milestone": "C0.20",
                "blocker": "indirect byte store for source-driven token tables",
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c021_indirect_store(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.21 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        for name in (
            "runtime_byte_load_at.nq",
            "runtime_byte_load_at_scan.nq",
            "runtime_byte_store_at.nq",
            "runtime_byte_store_at_copy.nq",
            "successor_self_emit.nq",
        ):
            (fixture / name).write_text(f"{name}\n", encoding="utf-8")

        scan_input = b"fn main(){\nreturn 42}\n"
        copy_input = b"NQL!"
        compiler_output = b"\x7fELFbounded-generation"
        results = (
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-load", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-load"], returncode=90,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-scan", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-scan"], returncode=0,
                stdout=scan_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-store", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-store"], returncode=91,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFtable-copy", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["table-copy"], returncode=0,
                stdout=copy_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-b"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-c"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(
                ["c0"], ["indirect-load"], ["c0"], ["source-scan"],
                ["c0"], ["indirect-store"], ["c0"], ["table-copy"],
                ["c0"], ["generation-b"], ["generation-c"],
            ),
        ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.21")
        self.assertEqual(
            result["probe_status"],
            "INDIRECT_STORE_AND_BOUNDED_GENERATION_VERIFIED",
        )
        self.assertTrue(result["indirect_load_verified"])
        self.assertTrue(result["source_scan_verified"])
        self.assertTrue(result["indirect_store_verified"])
        self.assertTrue(result["source_table_copy_verified"])
        self.assertTrue(result["bounded_generation_verified"])
        self.assertEqual(result["blocker"], "source-driven tokenization")
        self.assertIn(
            {
                "milestone": "C0.21",
                "blocker": "source-driven tokenization",
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c022_source_byte_tokens(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.22 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        (c0_dir / "source_byte_tokenizer.nql").write_text(
            "fn main() { return 0 }\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        for name in (
            "runtime_byte_load_at.nq",
            "runtime_byte_load_at_scan.nq",
            "runtime_byte_store_at.nq",
            "runtime_byte_store_at_copy.nq",
            "successor_self_emit.nq",
        ):
            (fixture / name).write_text(f"{name}\n", encoding="utf-8")

        scan_input = b"fn main(){\nreturn 42}\n"
        copy_input = b"NQL!"
        token_input = b"fn 42+\n"
        token_output = bytes((len(token_input),)) + b"".join(
            bytes((value, offset, 1))
            for offset, value in enumerate(token_input)
        ) + bytes((16 - len(token_input)) * 3)
        compiler_output = b"\x7fELFbounded-generation"
        results = (
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-load", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-load"], returncode=90,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-scan", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-scan"], returncode=0,
                stdout=scan_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-store", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-store"], returncode=91,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFtable-copy", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["table-copy"], returncode=0,
                stdout=copy_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-byte-tokenizer", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=0,
                stdout=token_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-b"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-c"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(
                ["c0"], ["indirect-load"], ["c0"], ["source-scan"],
                ["c0"], ["indirect-store"], ["c0"], ["table-copy"],
                ["c0"], ["source-byte-tokenizer"],
                ["source-byte-tokenizer"], ["c0"],
                ["generation-b"], ["generation-c"],
            ),
        ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.22")
        self.assertEqual(
            result["probe_status"],
            "SOURCE_BYTE_TOKENS_AND_BOUNDED_GENERATION_VERIFIED",
        )
        self.assertTrue(result["indirect_load_verified"])
        self.assertTrue(result["source_scan_verified"])
        self.assertTrue(result["indirect_store_verified"])
        self.assertTrue(result["source_table_copy_verified"])
        self.assertTrue(result["source_byte_tokenizer_verified"])
        self.assertTrue(result["source_byte_tokenizer_overflow_verified"])
        self.assertTrue(result["bounded_generation_verified"])
        self.assertEqual(
            result["blocker"],
            "lexical token classification and coalescing",
        )
        self.assertIn(
            {
                "milestone": "C0.22",
                "blocker": "lexical token classification and coalescing",
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c023_ascii_classification(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.23 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        (c0_dir / "source_byte_tokenizer.nql").write_text(
            "fn main() { return 0 }\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        for name in (
            "runtime_byte_load_at.nq",
            "runtime_byte_load_at_scan.nq",
            "runtime_byte_store_at.nq",
            "runtime_byte_store_at_copy.nq",
            "successor_self_emit.nq",
        ):
            (fixture / name).write_text(f"{name}\n", encoding="utf-8")

        scan_input = b"fn main(){\nreturn 42}\n"
        copy_input = b"NQL!"
        token_input = b"fn 42+\n"
        token_kinds = (4, 4, 1, 5, 5, 15, 1)
        token_output = bytes((len(token_input),)) + b"".join(
            bytes((token_kinds[offset], offset, 1))
            for offset in range(len(token_input))
        ) + bytes((16 - len(token_input)) * 3)
        compiler_output = b"\x7fELFbounded-generation"
        results = (
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-load", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-load"], returncode=90,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-scan", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-scan"], returncode=0,
                stdout=scan_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-store", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-store"], returncode=91,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFtable-copy", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["table-copy"], returncode=0,
                stdout=copy_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-byte-tokenizer", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=0,
                stdout=token_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-b"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-c"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(
                ["c0"], ["indirect-load"], ["c0"], ["source-scan"],
                ["c0"], ["indirect-store"], ["c0"], ["table-copy"],
                ["c0"], ["source-byte-tokenizer"],
                ["source-byte-tokenizer"], ["source-byte-tokenizer"],
                ["c0"], ["generation-b"], ["generation-c"],
            ),
        ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.23")
        self.assertEqual(
            result["probe_status"],
            "SOURCE_ASCII_CLASSIFICATION_AND_BOUNDED_GENERATION_VERIFIED",
        )
        self.assertTrue(result["indirect_load_verified"])
        self.assertTrue(result["source_scan_verified"])
        self.assertTrue(result["indirect_store_verified"])
        self.assertTrue(result["source_table_copy_verified"])
        self.assertTrue(result["source_byte_tokenizer_verified"])
        self.assertTrue(result["source_byte_tokenizer_overflow_verified"])
        self.assertTrue(result["source_ascii_classification_verified"])
        self.assertTrue(result["bounded_generation_verified"])
        self.assertEqual(
            result["blocker"],
            "lexical token coalescing and whitespace elision",
        )
        self.assertIn(
            {
                "milestone": "C0.23",
                "blocker": "lexical token coalescing and whitespace elision",
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c024_token_coalescing(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.24 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        (c0_dir / "source_byte_tokenizer.nql").write_text(
            "fn main() { return 0 }\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        for name in (
            "runtime_byte_load_at.nq",
            "runtime_byte_load_at_scan.nq",
            "runtime_byte_store_at.nq",
            "runtime_byte_store_at_copy.nq",
            "successor_self_emit.nq",
        ):
            (fixture / name).write_text(f"{name}\n", encoding="utf-8")

        scan_input = b"fn main(){\nreturn 42}\n"
        copy_input = b"NQL!"
        token_output = bytes((
            3,
            4, 0, 2,
            5, 3, 2,
            15, 5, 1,
        )) + bytes(39)
        coalescing_output = bytes((
            3,
            5, 0, 2,
            4, 2, 1,
            4, 4, 3,
        )) + bytes(39)
        compiler_output = b"\x7fELFbounded-generation"
        results = (
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-load", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-load"], returncode=90,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-scan", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-scan"], returncode=0,
                stdout=scan_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-store", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-store"], returncode=91,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFtable-copy", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["table-copy"], returncode=0,
                stdout=copy_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-byte-tokenizer", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=0,
                stdout=token_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=0,
                stdout=coalescing_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-b"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-c"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(
                ["c0"], ["indirect-load"], ["c0"], ["source-scan"],
                ["c0"], ["indirect-store"], ["c0"], ["table-copy"],
                ["c0"], ["source-byte-tokenizer"],
                ["source-byte-tokenizer"], ["source-byte-tokenizer"],
                ["source-byte-tokenizer"], ["c0"],
                ["generation-b"], ["generation-c"],
            ),
        ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.24")
        self.assertEqual(
            result["probe_status"],
            "SOURCE_TOKEN_COALESCING_AND_BOUNDED_GENERATION_VERIFIED",
        )
        self.assertTrue(result["source_ascii_classification_verified"])
        self.assertTrue(result["source_token_coalescing_verified"])
        self.assertTrue(result["source_byte_tokenizer_overflow_verified"])
        self.assertTrue(result["bounded_generation_verified"])
        self.assertEqual(
            result["blocker"],
            "source-driven parser over coalesced tokens",
        )
        self.assertIn(
            {
                "milestone": "C0.24",
                "blocker": "source-driven parser over coalesced tokens",
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

    def test_c0_probe_verifies_c025_expression_parser(self):
        c0_dir = self.root / "bootstrap" / "compiler" / "c0"
        seed_dir = c0_dir / "x86_64-linux"
        seed_dir.mkdir(parents=True)
        (c0_dir / "compiler.nq").write_text(
            "# C0.25 stream compiler.\n", encoding="utf-8"
        )
        (seed_dir / "c0.seed").write_bytes(b"c0")
        (seed_dir / "c0-successor.seed").write_bytes(b"successor")
        (c0_dir / "successor.nq").write_text(
            "bounded successor\n", encoding="utf-8"
        )
        (c0_dir / "source_byte_tokenizer.nql").write_text(
            "fn main() { return 0 }\n", encoding="utf-8"
        )
        (c0_dir / "source_token_parser.nql").write_text(
            "fn main() { return 0 }\n", encoding="utf-8"
        )
        fixture = self.root / "tests" / "bootstrap" / "fixtures" / "c0"
        fixture.mkdir(parents=True)
        for name in (
            "runtime_byte_load_at.nq",
            "runtime_byte_load_at_scan.nq",
            "runtime_byte_store_at.nq",
            "runtime_byte_store_at_copy.nq",
            "successor_self_emit.nq",
        ):
            (fixture / name).write_text(f"{name}\n", encoding="utf-8")

        scan_input = b"fn main(){\nreturn 42}\n"
        copy_input = b"NQL!"
        token_output = bytes((
            3,
            4, 0, 2,
            5, 3, 2,
            15, 5, 1,
        )) + bytes(39)
        coalescing_output = bytes((
            3,
            5, 0, 2,
            4, 2, 1,
            4, 4, 3,
        )) + bytes(39)
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
        expression_output = expression_tokens + bytes((1, 1, 0, 9))
        invalid_expression = bytes((
            2,
            4, 0, 1,
            15, 1, 1,
        )) + bytes(42)
        compiler_output = b"\x7fELFbounded-generation"
        parser_output = b"\x7fELFsource-token-parser"
        results = (
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-load", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-load"], returncode=90,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-scan", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-scan"], returncode=0,
                stdout=scan_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFindirect-store", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["indirect-store"], returncode=91,
                stdout=b"", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFtable-copy", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["table-copy"], returncode=0,
                stdout=copy_input, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFsource-byte-tokenizer", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=0,
                stdout=token_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=0,
                stdout=coalescing_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-byte-tokenizer"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=b"\x7fELFtoken-capacity", stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=1,
                stdout=b"",
                stderr=b"input:1:524: error[C0-001]: invalid C0 program\n",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=parser_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=parser_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-token-parser"], returncode=0,
                stdout=expression_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["source-token-parser"], returncode=1,
                stdout=b"", stderr=b"runtime: invalid source\n",
            ),
            subprocess.CompletedProcess(
                args=["c0"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-b"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
            subprocess.CompletedProcess(
                args=["generation-c"], returncode=0,
                stdout=compiler_output, stderr=b"",
            ),
        )
        with mock.patch.object(
            self.mcp, "_x86_runner",
            side_effect=(
                ["c0"], ["indirect-load"], ["c0"], ["source-scan"],
                ["c0"], ["indirect-store"], ["c0"], ["table-copy"],
                ["c0"], ["source-byte-tokenizer"],
                ["source-byte-tokenizer"], ["source-byte-tokenizer"],
                ["source-byte-tokenizer"], ["c0"], ["c0"], ["c0"], ["c0"],
                ["source-token-parser"], ["source-token-parser"], ["c0"],
                ["generation-b"], ["generation-c"],
            ),
        ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results):
            result = self.mcp.run_c0_probe()

        self.assertTrue(result["ok"])
        self.assertEqual(result["c0_version"], "C0.25")
        self.assertEqual(
            result["probe_status"],
            "SOURCE_EXPRESSION_PARSER_AND_BOUNDED_GENERATION_VERIFIED",
        )
        self.assertTrue(result["source_token_parser_verified"])
        self.assertTrue(result["source_token_parser_invalid_verified"])
        self.assertTrue(result["source_token_capacity_verified"])
        self.assertEqual(
            result["blocker"],
            "source-driven statement grammar and precedence tree construction",
        )
        self.assertIn(
            {
                "milestone": "C0.25",
                "blocker": (
                    "source-driven statement grammar and precedence tree "
                    "construction"
                ),
                "line": None,
            },
            self.mcp.c0_probe_history(),
        )

        (c0_dir / "frontend.nql").write_text("# C0.26 source-to-AST frontend\n")
        for frontend_ok in (True, False):
            frontend_result = {
                "ok": frontend_ok,
                "frontend_version": "C0.26",
                "probe_status": "SOURCE_AST_FRONTEND_VERIFIED" if frontend_ok else "UNEXPECTED_RESULT",
                "blocker": "AST semantic resolution and codegen" if frontend_ok else "frontend failed",
                "evidence": {"exit_code": 0 if frontend_ok else 1, "stderr": "" if frontend_ok else "FAIL tree"},
            }
            with self.subTest(frontend_ok=frontend_ok), mock.patch.object(
                self.mcp, "_x86_runner", return_value=["seed"]
            ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results), mock.patch.object(
                self.mcp, "run_c0_frontend_probe", return_value=frontend_result
            ):
                combined = self.mcp.run_c0_probe()
            self.assertEqual(combined["ok"], frontend_ok)
            self.assertEqual(combined["parse_complete"], frontend_ok)
            self.assertEqual(combined["exit_code"], 0 if frontend_ok else 1)
            self.assertEqual(combined["blocker"], frontend_result["blocker"])
            self.assertTrue(combined["bounded_generation_verified"])
            self.assertEqual(combined["frontend_version"], "C0.26")
            if frontend_ok:
                self.assertEqual(combined["probe_status"], "SOURCE_AST_AND_BOUNDED_GENERATION_VERIFIED")

        self.assertTrue(hasattr(self.mcp, "run_c0_backend_probe"))
        (c0_dir / "backend.nql").write_text("# C0.27 AST backend\n")
        for frontend_ok, backend_ok in ((True, True), (True, False), (False, True), (False, False)):
            frontend_result = {
                "ok": frontend_ok, "frontend_version": "C0.26",
                "probe_status": "SOURCE_AST_FRONTEND_VERIFIED" if frontend_ok else "UNEXPECTED_RESULT",
                "blocker": "semantics" if frontend_ok else "frontend failed",
                "evidence": {"exit_code": 0 if frontend_ok else 1, "stderr": ""},
            }
            backend_result = {
                "ok": backend_ok, "backend_version": "C0.27",
                "probe_status": "SOURCE_AST_TO_ELF_VERIFIED" if backend_ok else "UNEXPECTED_RESULT",
                "blocker": "calls and control flow" if backend_ok else "backend failed",
                "evidence": {"exit_code": 0 if backend_ok else 1, "stderr": ""},
            }
            with self.subTest(frontend_ok=frontend_ok, backend_ok=backend_ok), mock.patch.object(
                self.mcp, "_x86_runner", return_value=["seed"]
            ), mock.patch.object(self.mcp.subprocess, "run", side_effect=results), mock.patch.object(
                self.mcp, "run_c0_frontend_probe", return_value=frontend_result
            ), mock.patch.object(self.mcp, "run_c0_backend_probe", return_value=backend_result):
                combined = self.mcp.run_c0_probe()
            self.assertEqual(combined["ok"], frontend_ok and backend_ok)
            self.assertEqual(combined["parse_complete"], frontend_ok and backend_ok)
            self.assertEqual(combined["exit_code"], 0 if frontend_ok and backend_ok else 1)
            self.assertEqual(combined["backend_version"], "C0.27")
            self.assertEqual(combined["blocker"], "frontend failed" if not frontend_ok else backend_result["blocker"])
            if frontend_ok and backend_ok:
                self.assertEqual(combined["probe_status"], "SOURCE_AST_TO_ELF_AND_BOUNDED_GENERATION_VERIFIED")

    def test_project_status_reports_canonical_and_reference_components_separately(self):
        status = self.mcp.project_status()
        self.assertEqual(status["name"], "NolQu-L")
        self.assertIn("nql", status["toolchain"])
        self.assertIn("nqlc", status["toolchain"])
        self.assertIn("reference_r0", status)
        self.assertEqual(
            status["bootstrap"]["stages"]["full_compiler"]["status"],
            "NOT_IMPLEMENTED",
        )

    def test_audit_log_records_commands_and_atomic_edits(self):
        write_result = self.mcp.write_file("audit.nql", "print 1\n")
        self.assertIn("OK:", write_result)
        command_result = self.mcp.nql_check()
        self.assertTrue(command_result["ok"])

        audit = self.mcp.mcp_audit_log(limit=20)
        self.assertTrue(audit["ok"])
        self.assertLessEqual(len(audit["entries"]), 20)
        events = {entry["tool"]: entry for entry in audit["entries"]}
        self.assertIn("write_file", events)
        self.assertIn("nql_check", events)
        self.assertEqual(events["write_file"]["changed_files"], ["audit.nql"])
        self.assertEqual(events["nql_check"]["exit_code"], 0)
        self.assertIn("duration_ms", events["nql_check"])
        self.assertIn("git_head_before", events["nql_check"])
        self.assertIn("git_head_after", events["nql_check"])


class McpProtocolTests(unittest.TestCase):
    def test_revised_resources_from_unrelated_working_directory(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from pydantic import AnyUrl

        async def inspect_server(directory, authority_root=None):
            environment = {"NOLQU_MCP_AUDIT": "0"}
            if authority_root is not None:
                environment["NOLQU_ROOT"] = str(authority_root)
            server = StdioServerParameters(
                command=sys.executable, args=[str(MCP_SOURCE)], cwd=directory,
                env=environment,
            )
            async with asyncio.timeout(60):
                async with stdio_client(server) as (read, write):
                    async with ClientSession(read, write) as session:
                        initialized = await session.initialize()
                        self.assertEqual(initialized.serverInfo.name, "nolqu-l-compiler-tools")
                        resources = await session.list_resources()
                        self.assertEqual({str(item.uri) for item in resources.resources}, {
                            "nolqu://architecture", "nolqu://nine-pillars", "nolqu://bootstrap",
                            "nolqu://grammar", "nolqu://ir", "nolqu://abi",
                            "nolqu://diagnostics", "nolqu://current-development",
                        })
                        for uri, heading in (
                            ("nine-pillars", "1. NINE PILLARS OF NOLQU-L"),
                            ("grammar", "7. LEXER"), ("ir", "12. NOLQU IR"),
                            ("abi", "33. FFI DAN ABI"), ("diagnostics", "39. DIAGNOSTIC SYSTEM"),
                        ):
                            response = await session.read_resource(AnyUrl(f"nolqu://{uri}"))
                            text = response.contents[0].text
                            # Design attachments are optional in the public tree.
                            # Missing authority must stay an explicit error; the
                            # fixture tests above exercise present/obsolete input.
                            selected_root = authority_root or REPO_ROOT
                            if not (selected_root / "NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md").is_file():
                                error = "ERROR: NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md is missing"
                                self.assertEqual(text, error + "\n" + error if uri == "grammar" else error)
                                continue
                            self.assertTrue(text.startswith(f"# {heading}\n"), text[:200])
                            self.assertNotIn("ERROR:", text)
                            if uri == "nine-pillars":
                                self.assertIn("backward compatibility bukan tujuan absolut", text)
                                self.assertNotIn("# 2. ATURAN FUNDAMENTAL", text)
                        workflow = await session.get_prompt("develop_c0_milestone")
                        self.assertIn("NOLQU_MAJOR_DEVELOPMENT_UPD_REVISED.md",
                                      workflow.messages[0].content.text)
                        tools = await session.list_tools()
                        names = {item.name for item in tools.tools}
                        self.assertEqual(len(names), len(tools.tools))
                        self.assertTrue({"nql_build", "compile_nql", "canonical_bootstrap_status",
                                         "run_c0_probe", "current_c0_blocker"} <= names)
                        self.assertFalse({"nq_build", "nqc", "nolquc"} & names)

        with tempfile.TemporaryDirectory(prefix="nolqu-mcp-cwd-") as directory:
            asyncio.run(inspect_server(directory))
            missing = pathlib.Path(directory) / "without-design"
            missing.mkdir()
            (missing / "NOLQU_MAJOR_DEVELOPMENT.md").write_text(
                "# 1. NINE PILLARS OF NOLQU-L\nObsolete policy.\n", encoding="utf-8")
            asyncio.run(inspect_server(directory, missing))


class CanonicalCliMigrationTests(unittest.TestCase):
    def run_cli(self, *args: str, cwd: pathlib.Path | None = None):
        return subprocess.run(
            [str(REPO_ROOT / args[0]), *args[1:]],
            cwd=cwd or REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )

    def test_canonical_compiler_layout_has_only_new_command_names(self):
        self.assertTrue((REPO_ROOT / "nqlc").is_file())
        self.assertFalse((REPO_ROOT / "nqlc").is_symlink())
        self.assertTrue((REPO_ROOT / "nql").is_file())
        self.assertFalse((REPO_ROOT / "nql").is_symlink())
        self.assertEqual(os.readlink(REPO_ROOT / "nolqul"), "nql")
        self.assertEqual(os.readlink(REPO_ROOT / "nolqulc"), "nqlc")
        for removed_command in ("nq", "nqc", "nolqu", "nolquc"):
            self.assertFalse((REPO_ROOT / removed_command).exists())
        self.assertTrue((REPO_ROOT / "src" / "nqlc.asm").is_file())
        self.assertFalse((REPO_ROOT / "src" / "nolquc.asm").exists())
        self.assertTrue((REPO_ROOT / "tools" / "nql_r0_adapter.sh").is_file())
        self.assertFalse((REPO_ROOT / "tools" / "nq_legacy.sh").exists())
        canonical_tools = (
            "nql_ir_dump_parser.nql",
            "nql_ir_json_to_llvm.nql",
        )
        for name in canonical_tools:
            path = REPO_ROOT / "tools" / name
            self.assertTrue(path.is_file(), name)
            self.assertFalse(path.is_symlink(), name)
        legacy_source_aliases = {
            "nq_ir_dump_parser.nq": "nql_ir_dump_parser.nql",
            "nq_ir_json_to_llvm.nq": "nql_ir_json_to_llvm.nql",
        }
        for alias, target in legacy_source_aliases.items():
            path = REPO_ROOT / "tools" / alias
            self.assertTrue(path.is_symlink(), alias)
            self.assertEqual(os.readlink(path), target)

        canonical_version = self.run_cli("nqlc", "--version")
        self.assertEqual(canonical_version.returncode, 0, canonical_version.stderr)
        self.assertTrue(canonical_version.stdout.startswith("nqlc "))

        formal_version = self.run_cli("nolqulc", "--version")
        self.assertEqual(formal_version.returncode, 0, formal_version.stderr)
        self.assertTrue(formal_version.stdout.startswith("nolqulc "))

        with tempfile.TemporaryDirectory(prefix="nolqu-naming-") as temp:
            source = pathlib.Path(temp) / "hello.nql"
            shutil.copyfile(REPO_ROOT / "examples" / "core" / "hello.nq", source)
            checked = self.run_cli("nqlc", "--check", str(source))
            self.assertEqual(checked.returncode, 0, checked.stderr)

            formal_checked = self.run_cli("nolqulc", "--check", str(source))
            self.assertEqual(formal_checked.returncode, 0, formal_checked.stderr)

    def test_canonical_project_lifecycle_uses_nql_names(self):
        with tempfile.TemporaryDirectory(prefix="nolqu-project-") as temp:
            root = pathlib.Path(temp)
            initialized = self.run_cli("nql", "init", "app", cwd=root)
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            project = root / "app"
            self.assertTrue((project / "nql.toml").is_file())
            self.assertTrue((project / "src" / "main.nql").is_file())
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                ".nql/\n",
            )

            checked = self.run_cli("nql", "check", cwd=project)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            built = self.run_cli("nql", "build", cwd=project)
            self.assertEqual(built.returncode, 0, built.stderr)
            self.assertTrue((project / ".nql" / "build" / "app").is_file())

    def test_default_migration_fixtures_match_python_oracles(self):
        mcp = load_mcp(REPO_ROOT)
        for tool_name in (
            "nql_ir_dump_parser",
            "nql_ir_json_to_llvm",
        ):
            with self.subTest(tool=tool_name):
                result = mcp.verify_migration(tool_name)
                self.assertTrue(result["ok"], result)
                self.assertTrue(result["exit_codes_identical"])
                self.assertTrue(result["stdout_identical"])
                self.assertTrue(result["stderr_identical"])
                self.assertTrue(result["output_identical"])
                self.assertTrue(result["deterministic_artifact"])

    def test_canonical_c0_has_no_dynamic_host_dependency(self):
        mcp = load_mcp(REPO_ROOT)
        result = mcp.verify_no_host_dependency("c0")
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["interpreter"])
        self.assertEqual(result["needed_libraries"], [])
        self.assertTrue(result["canonical_hash_verified"])


class NativeProofTests(unittest.TestCase):
    """Synthetic receipt mutations test the consumer, never compiler capability."""

    setUp = NolQuMcpCoreTests.setUp
    tearDown = NolQuMcpCoreTests.tearDown
    c031_probe_fixture = NolQuMcpCoreTests.c031_probe_fixture

    def test_native_metadata_is_additive_and_unverified(self):
        metadata = self.mcp.canonical_bootstrap_status()
        for field in ("unsafe_blocks_verified", "process_arguments_verified", "syscall_abi_verified"):
            self.assertIs(metadata.get(field), False, field)
        for probe in (self.mcp.run_c0_frontend_probe, self.mcp.run_c0_backend_probe):
            result = probe()
            for field in self.mcp._C031_FLAGS:
                self.assertIs(result[field], False, field)
        for stage in ("full_compiler", "self_hosting", "verified"):
            self.assertEqual(metadata["stages"][stage]["status"], "NOT_IMPLEMENTED")

    def test_native_contract_keeps_every_legacy_expectation(self):
        stages, checks, artifacts = self.mcp._c031_contract()
        legacy = {
            "stages": {k: dict(status=v[0], stdout_hex=v[1].hex()) for k, v in stages.items()
                       if "-native-" not in k},
            "checks": sorted(k for k in checks if "-native-" not in k),
            "artifacts": sorted(k for k in artifacts if "-native-" not in k),
        }
        expected = {
            "stages": (554, "6339a9a703ed859f4f7fabbc18be13b6dbc236159e91761465281c480a00093e"),
            "checks": (215, "7e62e3952b9c2487c53066f449580906d57b5d16ee2b227e7e18dcde0934d7d4"),
            "artifacts": (351, "6eab07be7f5aaae3c3919e0576057fd8f0f9e8eca80576e0badb1ac798e6e3fa"),
        }
        for name, value in legacy.items():
            self.assertEqual((len(value), hashlib.sha256(json.dumps(
                value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()), expected[name])
        for generation in ("A1", "B", "C"):
            for profile in (0, 1):
                for case, status in (("argc", 1), ("copy-empty", 0), ("address", 1),
                                     ("enosys", 1), ("index", 70), ("copy-bound", 74),
                                     ("frame-bound", 70), ("negative-span", 70), ("cat-stdin", 0)):
                    label = f"{generation}-native-{case}-{profile}"
                    self.assertIn(label, checks)
                    self.assertEqual(stages[label + "-execute"],
                                     (status, b"native\x00stdin\xff\n" if case == "cat-stdin" else b""))
                    self.assertTrue({label, label + "-nqaf"} <= artifacts)
            for case in ("permission", "invariant"):
                self.assertIn(generation + "-native-" + case, checks)
                self.assertEqual(stages[generation + "-native-" + case], (1, b""))

    def test_native_inputs_bind_support_example_and_frozen_predecessor(self):
        self.c031_probe_fixture()
        before = self.mcp._c031_inputs()
        required = {"tests/bootstrap/c032_support.py", "examples/canonical/native_cat.nql",
                    "tests/bootstrap/c0_native_os.sh",
                    "tests/bootstrap/fixtures/c032/predecessor/hashes.json",
                    "tests/bootstrap/fixtures/c032/predecessor/frontend.nql",
                    "tests/bootstrap/fixtures/c032/predecessor/backend.nql"}
        self.assertTrue(required <= set(before), required - set(before))

    def generation_fixture(self):
        # Synthetic streams exercise validation. No subprocess ran these stages.
        # The independent legacy hashes and native table above guard the builder's contract.
        import ast
        self.c031_probe_fixture()
        for component in ("frontend", "backend"):
            (self.root / f"bootstrap/compiler/c0/{component}.nql").write_bytes(b"fn main(){return 0}")
        predecessor = {"b0.seed": b"unit predecessor b0", "c0-frontend.seed": b"unit predecessor frontend",
                       "c0-backend.seed": b"unit predecessor backend"}
        fingerprint = lambda data: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        (self.root / "tests/bootstrap/fixtures/c031/predecessor/hashes.json").write_text(json.dumps(
            dict(artifacts={name: fingerprint(data)["sha256"] for name, data in predecessor.items()})))
        self.before = self.mcp._c031_inputs()
        directory = self.root / "generations/test_actual_sources_build_and_rebuild-synthetic"
        directory.mkdir(parents=True)
        _, machine = self.machine_fixture(directory)
        required, checks, names = self.mcp._c031_contract()
        self.assertEqual((len(required), len(checks), len(names)), (722, 275, 475))
        data = {label: ("synthetic:" + label).encode() for label in names}
        for generation in ("A1", "A2", "B", "C"):
            for component in ("frontend", "backend"):
                data[generation + "-" + component] = (self.root / f"bootstrap/compiler/c0/x86_64-linux/c0-{component}.seed").read_bytes()
        for component, name in (("b0", "b0.seed"), ("frontend", "c0-frontend.seed"), ("backend", "c0-backend.seed")):
            data["predecessor-" + component] = predecessor[name]
        for label, identity in machine["artifacts"].items():
            data[label] = pathlib.Path(identity["path"]).read_bytes()
        source = b"fn main(){return 0}"
        for label in names:
            if label.endswith("-nqaf") and "-native-mmap-" not in label:
                native = "-native-" in label
                profile = 1 if label.startswith(("B-frontend-", "B-backend-", "C-frontend-", "C-backend-")) else int(native and label.endswith("-1-nqaf"))
                data[label] = (struct.pack("<4sBBHIIII4BI", b"NQAF", 6 if native else 5, 32, 0,
                    len(source), 1, 1, 1, 5 if native else 4, profile, 0, 0, 0) + source + bytes(32))
        artifacts = dict(machine["artifacts"])
        for label in names - set(artifacts):
            path = directory / (label + ".artifact")
            path.write_bytes(data[label])
            artifacts[label] = dict(path=str(path), **fingerprint(data[label]))
        definition = ast.parse((REPO_ROOT / "tests/bootstrap/test_c0_component_generations.py").read_text())
        selectors = next(ast.literal_eval(n.value) for n in definition.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "GENERATION_ORACLES" for t in n.targets))
        streams = []
        work = directory / "work-synthetic"
        for label, (status, output) in required.items():
            error, payload = b"", b""
            if label in {f"{g}-{c}" for g in ("A1", "A2") for c in ("frontend", "backend")}:
                binary = self.root / "bootstrap/compiler/b0/x86_64-linux/b0.seed"
                command = [str(binary), "--compiler-profile"]
            elif label.endswith("-named-oracles"):
                binary = pathlib.Path(sys.executable)
                command = [sys.executable, "-B", "-W", "error::ResourceWarning", "-m", "unittest", "-v", *selectors]
                error = b"\nRan 41 tests in 1.0s\n\nOK\n"
            else:
                generation = label.split("-", 1)[0]
                if label.endswith("-frontend"):
                    emitted = label[:-9] + "-nqaf"
                    output = data[emitted]
                    profile = output[25]
                    payload = (b"NQSC\x01\x01" + bytes(10) if profile else b"") + source
                    parent = "A1" if generation == "B" else "B"
                    producer = parent if label in {f"{g}-{c}-frontend" for g in ("B", "C") for c in ("frontend", "backend")} else generation
                    binary = work / (producer + "-frontend")
                elif label.endswith("-backend"):
                    emitted = label[:-8]
                    output, payload = data[emitted], data[emitted + "-nqaf"]
                    parent = "A1" if generation == "B" else "B"
                    producer = parent if label in {f"{g}-{c}-backend" for g in ("B", "C") for c in ("frontend", "backend")} else generation
                    binary = work / (producer + "-backend")
                elif label.endswith("-execute"):
                    binary = work / label[:-8]
                    if "-native-cat-stdin-" in label:
                        payload = b"native\x00stdin\xff\n"
                    if status in (70, 74):
                        code = b"C0R-008" if "-native-index-" in label else b"C0R-009" if "-native-copy-bound-" in label else b"C0R-001" if "overflow" in label else b"C0R-004"
                        error = b"input:1:1: error[" + code + b"]: synthetic diagnostic\n"
                    elif label.endswith("-streams-execute"):
                        error = b"ABCD"
                else:
                    binary = work / (generation + "-frontend" if label.endswith(("-syntax", "-envelope", "-permission", "-invariant")) else generation + "-backend")
                    code = (b"C0S-001" if label.endswith("-permission") else b"C0P-014" if label.endswith("-invariant")
                            else b"C0P-013" if label.endswith("-envelope") else b"C0P-001" if label.endswith("-syntax")
                            else b"C0B-005" if label.endswith("-reject") else b"C0B-006" if label.endswith("-anchor") else b"C0B-001")
                    error = b"input:1:1: error[" + code + b"]: synthetic diagnostic\n"
                command = [str(binary)]
                if "-native-copy-empty-" in label and label.endswith("-execute"):
                    command.append("")
            prefix = directory / f"{len(streams):03d}-{label}"
            for suffix, content in (("stdin", payload), ("stdout", output), ("stderr", error)):
                pathlib.Path(str(prefix) + "." + suffix).write_bytes(content)
            streams.append(dict(label=label, prefix=str(prefix), binary=str(binary), command=command,
                returncode=status, timed_out=False, input=fingerprint(payload), stdout=fingerprint(output), stderr=fingerprint(error)))
        identity = lambda label: {key: artifacts[label][key] for key in ("bytes", "sha256")}
        pairs = {**{f"A1-A2-{c}": (f"A1-{c}", f"A2-{c}") for c in ("frontend", "backend")},
                 **{f"selected-A1-{c}": (f"A1-{c}", f"A1-{c}") for c in ("frontend", "backend")},
                 **{f"B-C-{c}": (f"B-{c}", f"C-{c}") for c in ("frontend", "backend")}}
        oracles = []
        for generation in ("B", "C"):
            components = {c: dict(path=str(work / (generation + "-" + c)), **identity(generation + "-" + c)) for c in ("frontend", "backend")}
            oracles.append(dict(generation=generation, selectors=list(selectors), components=components,
                returncode=0, timed_out=False, child_reaped=True, temporary_removed=True,
                environment=dict(C0_FRONTEND=components["frontend"]["path"], C0_BACKEND=components["backend"]["path"],
                                 PYTHONPATH=str(self.root / "tests/bootstrap"), TMPDIR="/tmp/synthetic-removed",
                                 C032_NATIVE_EVIDENCE_DIR=machine["machine_evidence"][generation]["directory"])))
        inputs = {"bootstrap/compiler/c0/frontend.nql", "bootstrap/compiler/c0/backend.nql",
                  "tests/bootstrap/test_c0_component_generations.py", "tests/bootstrap/c031_support.py", "tests/bootstrap/c031_debugger.py",
                  "tests/bootstrap/c032_support.py", "examples/canonical/native_cat.nql", "tests/bootstrap/c0_native_os.sh",
                  "tests/bootstrap/fixtures/c032/predecessor/hashes.json", "tests/bootstrap/c0_capacity.sh",
                  "bootstrap/compiler/b0/compiler.nql0", "bootstrap/stage0/x86_64-linux/stage0.seed",
                  "tests/bootstrap/fixtures/c031/predecessor/hashes.json"}
        for pattern in ("bootstrap/**/x86_64-linux/*.seed", "bootstrap/**/x86_64-linux/*.sha256", "tests/bootstrap/test_c0_*.py",
                        "tests/bootstrap/fixtures/c031/predecessor/*.nql*", "tests/bootstrap/fixtures/c032/predecessor/*.nql"):
            inputs.update(str(p.relative_to(self.root)) for p in self.root.glob(pattern))
        receipt = dict(component_generations_verified=True, rejections=[], cwd=str(self.root),
            argv=[str(self.root / "tests/bootstrap/test_c0_component_generations.py"), "-v"],
            identities={str((self.root / name).resolve()): {key: self.before[name][key] for key in ("bytes", "sha256")} for name in inputs},
            stages=streams, checks=[dict(label=label, passed=True) for label in sorted(checks)], artifacts=artifacts,
            comparisons=[dict(label=label, left=identity(a), right=identity(b), first_difference_offset=None) for label, (a, b) in pairs.items()],
            oracles=oracles, predecessor_builder="c031_support.build_predecessors", machine_evidence=machine["machine_evidence"])
        self.receipt_path = directory / "receipt.json"
        self.receipt_path.write_text(json.dumps(receipt))
        return receipt

    def validate_synthetic(self, receipt):
        self.receipt_path.write_text(json.dumps(receipt))
        return self.mcp._c031_validate(self.receipt_path.parent.parent, self.before)

    def test_native_generation_requires_every_check_artifact_selector_and_identity(self):
        import copy
        receipt = self.generation_fixture()
        accepted = self.validate_synthetic(receipt)
        self.assertEqual((accepted["stages"], accepted["checks"]), (722, 275))
        self.assertEqual(len(accepted["native_machine_artifacts"]), 16)
        for failure in ("check", "artifact", "selector", "identity", "duplicate-stage", "missing-stage", "trace", "oracle-binary"):
            with self.subTest(failure=failure):
                changed = copy.deepcopy(receipt)
                if failure == "check":
                    changed["checks"] = [x for x in changed["checks"] if x["label"] != "B-native-index-1"]
                elif failure == "artifact":
                    del changed["artifacts"]["C-native-copy-empty-0"]
                elif failure == "selector":
                    changed["oracles"][0]["selectors"][-1] = changed["oracles"][0]["selectors"][0]
                elif failure == "identity":
                    name = str((self.root / "examples/canonical/native_cat.nql").resolve())
                    changed["identities"][name]["sha256"] = "0" * 64
                elif failure == "duplicate-stage":
                    changed["stages"].append(changed["stages"][-1])
                elif failure == "missing-stage":
                    changed["stages"] = [x for x in changed["stages"] if x["label"] != "C-native-address-0-execute"]
                elif failure == "trace":
                    del changed["machine_evidence"]["B"]["profiles"]["1"]
                elif failure == "oracle-binary":
                    changed["oracles"][0]["components"]["backend"]["sha256"] = "0" * 64
                with self.assertRaises((ValueError, KeyError)):
                    self.validate_synthetic(changed)

    def test_native_generation_binds_raw_diagnostics_and_streams(self):
        receipt = self.generation_fixture()
        self.validate_synthetic(receipt)
        for label, code in (("B-native-index-0-execute", b"C0R-008"),
                            ("C-native-copy-bound-1-execute", b"C0R-009"),
                            ("A1-native-permission", b"C0S-001"), ("C-native-invariant", b"C0P-014")):
            stage = next(x for x in receipt["stages"] if x["label"] == label)
            path = pathlib.Path(stage["prefix"] + ".stderr")
            original = path.read_bytes()
            for rehash in (False, True):
                with self.subTest(label=label, rehash=rehash):
                    changed = original.replace(code, b"C0R-004")
                    path.write_bytes(changed)
                    if rehash:
                        stage["stderr"] = dict(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
                    with self.assertRaises(ValueError):
                        self.validate_synthetic(receipt)
                    path.write_bytes(original)
                    stage["stderr"] = dict(bytes=len(original), sha256=hashlib.sha256(original).hexdigest())

    def test_native_generation_relative_script_uses_recorded_root(self):
        receipt = self.generation_fixture()
        receipt["argv"][0] = "tests/bootstrap/test_c0_component_generations.py"
        self.assertEqual(self.validate_synthetic(receipt)["checks"], 275)
        receipt["argv"][0] = "../outside/test_c0_component_generations.py"
        with self.assertRaisesRegex(ValueError, "command mismatch"):
            self.validate_synthetic(receipt)

    def test_native_archive_retains_consumed_bytes_after_temporary_cleanup(self):
        temporary = self.root / "disposable"
        temporary.mkdir()
        directory, receipt = self.machine_fixture(temporary)
        self.assertTrue(hasattr(self.mcp, "_c031_archive_native"), "proof must retain machine artifacts")
        consumed = self.mcp._c031_native_evidence(receipt, directory)
        archive = self.root / "archive"
        archive.mkdir()
        retained = self.mcp._c031_archive_native(consumed, archive)
        shutil.rmtree(temporary)
        self.assertEqual(set(retained), set(consumed))
        for label, record in retained.items():
            path = pathlib.Path(record["path"])
            self.assertTrue(path.is_relative_to(archive))
            self.assertEqual(self.mcp._c031_fingerprint(path), {k: consumed[label][k] for k in ("bytes", "sha256")})
            self.assertEqual(path.stat().st_mode & 0o777, consumed[label]["mode"])
        self.mcp._c031_check_retained_native(retained, archive)
        pathlib.Path(retained["C-native-mmap-profile1-elf"]["path"]).write_bytes(b"changed after copy")
        with self.assertRaises(ValueError):
            self.mcp._c031_check_retained_native(retained, archive)

    def test_native_probe_retains_evidence_and_invalidates_changed_archive(self):
        self.c031_probe_fixture()
        gate = NolQuMcpCoreTests.c031_gate_result.__get__(self)
        def validate(directory, before):
            work, receipt = self.machine_fixture(directory)
            return {"native_machine_artifacts": self.mcp._c031_native_evidence(receipt, work)}
        with mock.patch.object(self.mcp, "_c031_command", side_effect=gate) as command, mock.patch.object(
                self.mcp, "_c031_validate", side_effect=validate), self.mcp._c031_scope():
            first = self.mcp._c031_proof()
            self.assertTrue(first["ok"], first)
            self.assertTrue(first["temporary_removed"])
            retained = first["native_machine_artifacts"]
            self.assertEqual(len(retained), 16)
            for record in retained.values():
                path = pathlib.Path(record["path"])
                self.assertTrue(path.is_file(), path)
                self.assertTrue(path.is_relative_to(pathlib.Path(first["evidence_directory"])))
            second = self.mcp._c031_proof()
            self.assertIs(second, first)
            self.assertEqual(command.call_count, 3)
            pathlib.Path(retained["B-native-mmap-profile1-json"]["path"]).write_text("{}")
            third = self.mcp._c031_proof()
            self.assertFalse(third["ok"])
            self.assertEqual(command.call_count, 3)
            for flag in ("capacity_verified", "compiler_profile_verified", "component_generation_verified",
                         "unsafe_blocks_verified", "process_arguments_verified", "syscall_abi_verified"):
                self.assertIs(third.get(flag), False, flag)

    def test_native_gate_requires_marker_and_complete_skip_free_suite(self):
        self.c031_probe_fixture()
        gate = NolQuMcpCoreTests.c031_gate_result.__get__(self)
        for failure in ("marker", "suite", "skip", "timeout", "validation"):
            def command(argv, directory, timeout, env=None):
                result = gate(argv, directory, timeout, env)
                if pathlib.Path(argv[-1]).stem == "c0_backend":
                    if failure == "marker":
                        (directory / "stdout").write_text(result["stdout"].replace("PASS c0-native-os\n", ""))
                    elif failure == "suite":
                        (directory / "stderr").write_bytes(b"\nRan 22 tests in 1.0s\n\nOK\n")
                    elif failure == "skip":
                        (directory / "stderr").write_bytes(b"\nRan 23 tests in 1.0s\n\nOK (skipped=1)\n")
                    elif failure == "timeout":
                        result.update(ok=False, timed_out=True, exit_code=None)
                return result
            with self.subTest(failure=failure), mock.patch.object(self.mcp, "_c031_command", side_effect=command), mock.patch.object(
                    self.mcp, "_c031_validate", side_effect=ValueError("synthetic invalid receipt") if failure == "validation" else lambda *a: {}):
                result = self.mcp.run_c0_backend_probe()
                self.assertFalse(result["ok"], failure)
                for flag in self.mcp._C031_FLAGS:
                    self.assertIs(result[flag], False, flag)
                self.assertFalse(result["full_compiler_verified"])
                self.assertFalse(result["self_hosting_verified"])

    def machine_fixture(self, parent=None):
        """Handmade transport/ELF/register fixture, explicitly no execution proof."""
        directory = (parent or self.root) / "machine"
        directory.mkdir()
        artifacts, machine = {}, {}
        payload = b"actual file mmap offset 65536\x00\xff\n"
        file_hash = hashlib.sha256(b"P" * 65536 + payload + bytes(4096 - len(payload))).hexdigest()
        for generation in ("B", "C"):
            original = directory / (generation + "-native-machine")
            original.mkdir()
            profiles = {}
            for profile in (0, 1):
                source = b"fn main(){unsafe{# safety: synthetic consumer fixture\nsyscall6(39,0)}return 0}"
                wire = (struct.pack("<4sBBHIIII4BI", b"NQAF", 6, 32, 0,
                                    len(source), 1, 1, 1, 5, profile, 0, 0, 0)
                        + source + bytes(32))
                binary = bytearray(1024)
                struct.pack_into("<16sHHIQQQIHHHHHH", binary, 0,
                                 b"\x7fELF\x02\x01\x01" + bytes(9), 2, 62, 1,
                                 0x400200, 64, 0, 0, 64, 56, 2, 0, 0, 0)
                struct.pack_into("<IIQQQQQQ", binary, 64, 1, 5, 0, 0x400000,
                                 0x400000, len(binary), len(binary), 4096)
                struct.pack_into("<IIQQQQQQ", binary, 120, 0x6474e551, 6, 0, 0, 0, 0, 0, 16)
                binary[512:514] = b"\x0f\x05"
                raw = {"nql": source, "nqaf": wire, "elf": bytes(binary)}
                trace = dict(profile=profile,
                    execution="actual x86_64 Linux syscall execution via QEMU debugger",
                    synthetic_fault_injection=False, syscall_rip=0x400200,
                    file_offset=65536, file_before_hex=payload.hex(), file_after_hex=payload.hex(),
                    expected_hex=payload.hex(), file_before_sha256=file_hash, file_after_sha256=file_hash,
                    outcome=dict(status=0, stdout_hex=payload.hex(), stderr_hex=""), artifacts={}, observations=[])
                registers = dict.fromkeys(("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
                                           "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15", "rip"), 0)
                registers.update(rbx=0x200000, rbp=0x300000, rsp=0x400008, r15=1)
                for index, (number, args, result) in enumerate((
                        (257, ((1 << 64) - 100, 0x200200, 2, 0, 0, 0), 5),
                        (9, (0, 4096, 3, 1, 5, 65536), 0x500000),
                        (1, (1, 0x500000, 32, 0, 0, 0), 32),
                        (11, (0x500000, 4096, 0, 0, 0, 0), 0),
                        (3, (5, 0, 0, 0, 0, 0), 0))):
                    pre = dict(registers, rax=number, rip=0x400200, r11=0x200000 + index * 48)
                    pre.update(zip(("rdi", "rsi", "rdx", "r10", "r8", "r9"), args))
                    trace["observations"].append(dict(number=number, pre=pre,
                                                        post=dict(pre, rax=result, rip=0x400202)))
                for suffix, data in raw.items():
                    name = f"mmap-profile{profile}.{suffix}"
                    trace["artifacts"][suffix] = dict(path=name, bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(), mode=0o755 if suffix == "elf" else 0o644)
                raw["json"] = json.dumps(trace).encode()
                labels = {}
                for suffix, data in raw.items():
                    name = f"mmap-profile{profile}.{suffix}"
                    (original / name).write_bytes(data)
                    (original / name).chmod(0o755 if suffix == "elf" else 0o644)
                    label = f"{generation}-native-mmap-profile{profile}-{suffix}"
                    path = directory / (label + ".artifact")
                    path.write_bytes(data)
                    path.chmod(0o755 if suffix == "elf" else 0o644)
                    artifacts[label] = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                    labels[suffix] = label
                profiles[str(profile)] = labels
            machine[generation] = dict(directory=str(original), profiles=profiles)
        return directory, dict(machine_evidence=machine, artifacts=artifacts)

    def test_native_machine_consumer_rejects_forged_registers_and_missing_trace(self):
        directory, receipt = self.machine_fixture()
        self.assertTrue(hasattr(self.mcp, "_c031_native_evidence"), "native machine proof consumer is required")
        accepted = self.mcp._c031_native_evidence(receipt, directory)
        self.assertEqual(len(accepted), 16)
        label = "B-native-mmap-profile0-json"
        path = pathlib.Path(receipt["artifacts"][label]["path"])
        original = path.read_bytes()
        for failure in ("r9", "r10", "raw-return", "callee", "instruction", "profile", "file-change",
                        "output", "synthetic", "mode", "missing-trace"):
            with self.subTest(failure=failure):
                trace = json.loads(original)
                if failure in ("r9", "r10"):
                    trace["observations"][1]["pre"][failure] = 0
                elif failure == "raw-return":
                    trace["observations"][2]["post"]["rax"] = 31
                elif failure == "callee":
                    trace["observations"][1]["post"]["rbx"] = 1
                elif failure == "instruction":
                    trace["syscall_rip"] += 8
                elif failure == "profile":
                    trace["profile"] = 1
                elif failure == "file-change":
                    trace["file_after_sha256"] = "0" * 64
                elif failure == "output":
                    trace["outcome"]["stdout_hex"] = "00"
                elif failure == "synthetic":
                    trace["synthetic_fault_injection"] = True
                elif failure == "mode":
                    path.chmod(0o755)
                if failure == "missing-trace":
                    path.unlink()
                else:
                    data = json.dumps(trace).encode()
                    path.write_bytes(data)
                    receipt["artifacts"][label].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                    (directory / "B-native-machine/mmap-profile0.json").write_bytes(data)
                with self.assertRaises((ValueError, FileNotFoundError)):
                    self.mcp._c031_native_evidence(receipt, directory)
                path.write_bytes(original)
                path.chmod(0o644)
                (directory / "B-native-machine/mmap-profile0.json").write_bytes(original)
                receipt["artifacts"][label].update(bytes=len(original), sha256=hashlib.sha256(original).hexdigest())


if __name__ == "__main__":
    unittest.main()
