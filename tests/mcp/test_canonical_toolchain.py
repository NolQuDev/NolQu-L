"""MCP access contracts; only the SDK cases count as compiler evidence."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MCP_SOURCE = ROOT / "tools/nolqu_mcp.py"


def load_mcp(root):
    with mock.patch.dict(os.environ, {"NOLQU_ROOT": str(root)}):
        spec = importlib.util.spec_from_file_location("canonical_mcp_" + uuid.uuid4().hex,
                                                     MCP_SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    module._git_head = lambda: None
    return module


def record(label, payload):
    receipts = os.environ.get("NQL_MCP_RECEIPTS")
    if receipts:
        directory = Path(receipts)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / (label + "-" + uuid.uuid4().hex + ".json")).write_text(
            json.dumps(payload, indent=2, default=str) + "\n")


class CanonicalForwardingTests(unittest.TestCase):
    """Record the subprocess boundary; these are not compilation proofs."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mcp-canonical-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in ("nql", "nqlc"):
            (self.root / name).write_text("unit boundary placeholder\n")
        self.source = self.root / "source with spaces.nql"
        self.source.write_text("fn main(){return 23}\n")
        self.mcp = load_mcp(self.root)
        self.commands = []
        self.status = 0
        self.publish = False
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(self.mcp, "_run_result", side_effect=self.boundary).start()

    def boundary(self, command, **options):
        self.commands.append((command, options))
        if self.publish and "-o" in command:
            output = Path(command[command.index("-o") + 1])
            if not output.is_absolute():
                output = self.root / output
            output.write_bytes(b"unit output, not ELF")
        result = self.mcp._error_result("", command=command,
                                        capability=options.get("capability", "BUILD"))
        result.update(ok=self.status == 0, exit_code=self.status,
                      artifacts=options.get("artifacts", []))
        return result

    def require_options(self, tool, *names):
        for name in names:
            self.assertIn(name, inspect.signature(getattr(self.mcp, tool)).parameters,
                          tool + " must expose optional " + name)

    def compile(self, **options):
        return self.mcp.compile_nql(self.source.name, **options)

    def test_compile_default_requests_output_without_run(self):
        result = self.compile()
        self.assertTrue(result["ok"])
        self.assertIn("-o", result["command"])
        self.assertEqual(result["command"][result["command"].index("-o") + 1],
                         str(self.root / ".nolqu-mcp/build/source with spaces"))
        self.assertNotIn("--run", result["command"])

    def test_legacy_compile_default_requests_output_and_keeps_string(self):
        result = self.mcp.compile_file(self.source.name)
        self.assertIsInstance(result, str)
        self.assertIn("-o", self.commands[-1][0])

    def test_pipeline_full_requests_output_and_keeps_string(self):
        result = self.mcp.run_pipeline_step(self.source.name, "full")
        self.assertIsInstance(result, str)
        self.assertIn("-o", self.commands[-1][0])

    def test_compile_forwards_backend_and_explicit_profile(self):
        self.require_options("compile_nql", "backend", "compiler_profile")
        result = self.compile(backend="canonical", compiler_profile=True)
        self.assertEqual(result["command"][:4],
                         [str(self.root / "nqlc"), "--backend", "canonical", "--compiler-profile"])

    def test_compile_default_selection_and_profile_are_not_forced(self):
        result = self.compile()
        self.assertNotIn("--backend", result["command"])
        self.assertNotIn("--compiler-profile", result["command"])

    def test_project_backend_forwarding_preserves_old_arguments(self):
        cases = (("nql_init", {"project_name": "app with spaces"}, ["app with spaces"]),
                 ("nql_build", {"release": True, "target": "x86_64-linux"},
                  ["--release", "--target", "x86_64-linux"]),
                 ("nql_run", {"args": "'one two' --backend literal", "release": True},
                  ["--release", "--", "one two", "--backend", "literal"]),
                 ("nql_test", {"filter": "nested case"}, ["nested case"]),
                 ("nql_check", {}, []))
        for tool, options, tail in cases:
            with self.subTest(tool=tool):
                self.require_options(tool, "backend")
                result = getattr(self.mcp, tool)(backend="canonical", **options)
                self.assertEqual(result["command"], [str(self.root / "nql"), tool[4:],
                                                     "--backend", "canonical", *tail])

    def test_omitted_project_backend_honors_manifest_and_profile_default(self):
        for tool in ("nql_init", "nql_build", "nql_run", "nql_test", "nql_check"):
            with self.subTest(tool=tool):
                result = getattr(self.mcp, tool)()
                self.assertEqual(result["command"], [str(self.root / "nql"), tool[4:]])

    def test_project_profile_is_explicit_and_can_use_manifest_backend(self):
        for tool in ("nql_build", "nql_run", "nql_test", "nql_check"):
            with self.subTest(tool=tool):
                self.require_options(tool, "compiler_profile")
                result = getattr(self.mcp, tool)(compiler_profile=True)
                self.assertEqual(result["command"],
                                 [str(self.root / "nql"), tool[4:], "--compiler-profile"])
                explicit = getattr(self.mcp, tool)(backend="canonical", compiler_profile=True)
                self.assertEqual(explicit["command"], [str(self.root / "nql"), tool[4:],
                                                       "--backend", "canonical", "--compiler-profile"])
        self.assertNotIn("compiler_profile", inspect.signature(self.mcp.nql_init).parameters)

    def test_invalid_backend_fails_before_subprocess_for_every_new_option(self):
        for tool in ("compile_nql", "nql_init", "nql_build", "nql_run", "nql_test", "nql_check"):
            for backend in ("llvm", "canonical; touch injected", "Canonical"):
                with self.subTest(tool=tool, backend=backend):
                    self.require_options(tool, "backend")
                    options = {"source_file": self.source.name} if tool == "compile_nql" else {}
                    result = getattr(self.mcp, tool)(backend=backend, **options)
                    self.assertFalse(result["ok"])
                    self.assertIn("backend", result["stderr"].lower())
                    self.assertEqual(result["artifacts"], [])
        self.assertEqual(self.commands, [])

    def test_profile_with_explicit_nasm_is_rejected_before_execution(self):
        for tool in ("compile_nql", "nql_build", "nql_run", "nql_test", "nql_check"):
            with self.subTest(tool=tool):
                self.require_options(tool, "backend", "compiler_profile")
                options = {"source_file": self.source.name} if tool == "compile_nql" else {}
                result = getattr(self.mcp, tool)(backend="nasm", compiler_profile=True, **options)
                self.assertFalse(result["ok"])
        self.assertEqual(self.commands, [])

    def test_malformed_compile_flag_quoting_is_structured(self):
        result = self.compile(flags="--target 'unterminated")
        self.assertFalse(result["ok"])
        self.assertIn("quot", result["stderr"].lower())
        self.assertEqual(self.commands, [])

    def test_legacy_malformed_quoting_keeps_string_error_schema(self):
        result = self.mcp.compile_file(self.source.name, flags="'")
        self.assertIsInstance(result, str)
        self.assertIn("quot", result.lower())
        self.assertEqual(self.commands, [])

    def test_run_malformed_argument_quoting_is_structured(self):
        result = self.mcp.nql_run(args="'")
        self.assertFalse(result["ok"])
        self.assertEqual(self.commands, [])

    def test_check_and_stdout_modes_do_not_receive_default_output(self):
        for flag in ("--check", "--emit-ir", "--dump-ir", "--dump-ast", "-M", "--emit-ccdb"):
            with self.subTest(flag=flag):
                result = self.compile(flags=flag)
                self.assertNotIn("-o", result["command"])
                self.assertEqual(result["artifacts"], [])
                self.mcp.compile_file(self.source.name, flags=flag)
                self.assertNotIn("-o", self.commands[-1][0])
        for step, flag in (("parse", "--check"), ("ir", "--emit-ir")):
            self.mcp.run_pipeline_step(self.source.name, step)
            self.assertIn(flag, self.commands[-1][0])
            self.assertNotIn("-o", self.commands[-1][0])

    def test_explicit_run_remains_explicit_without_default_output(self):
        result = self.compile(flags="--run")
        self.assertIn("--run", result["command"])
        self.assertNotIn("-o", result["command"])
        self.mcp.compile_file(self.source.name, flags="--run")
        self.assertIn("--run", self.commands[-1][0])
        self.assertNotIn("-o", self.commands[-1][0])

    def test_explicit_run_source_precedes_separator_and_preserves_literals(self):
        tail = ["one two", "@missing.rsp", "--backend", "nasm", "--compiler-profile"]
        flags = "--run -- 'one two' @missing.rsp --backend nasm --compiler-profile"
        result = self.compile(backend="canonical", flags=flags)
        self.assertEqual(result["command"], [str(self.root / "nqlc"), "--backend", "canonical",
                                             "--run", str(self.source), "--", *tail])
        self.mcp.compile_file(self.source.name, flags="--backend canonical " + flags)
        command = self.commands[-1][0]
        self.assertEqual(command[command.index("--") - 1], str(self.source))
        self.assertEqual(command[command.index("--") + 1:], tail)

    def test_default_outputs_for_reserved_names_stay_in_owned_namespace(self):
        for stem in ("nqlc", "nql", "c0-frontend.seed"):
            source = self.root / (stem + ".nql")
            source.write_text("fn main(){return 0}\n")
            expected = str(self.root / ".nolqu-mcp/build" / stem)
            calls = ((self.mcp.compile_nql, {"backend": "canonical"}),
                     (self.mcp.compile_file, {}),
                     (self.mcp.run_pipeline_step, {"step": "full"}))
            for tool, options in calls:
                with self.subTest(source=source.name, tool=tool.__name__):
                    tool(source.name, **options)
                    command = self.commands[-1][0]
                    self.assertEqual(command[command.index("-o") + 1], expected)
                    self.assertNotEqual(expected, str(self.root / stem))

    def test_default_output_rejects_source_tool_and_component_aliases(self):
        directory = self.root / ".nolqu-mcp/build"
        directory.mkdir(parents=True)
        output = directory / self.source.stem
        component = self.root / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed"
        component.parent.mkdir(parents=True)
        component.write_bytes(b"component sentinel")
        for protected in (self.source, self.root / "nqlc", self.root / "nql", component):
            with self.subTest(protected=protected):
                # Android Python omits os.link; retain a real inode-alias test.
                subprocess.run(["ln", "--", str(protected), str(output)],
                               check=True, capture_output=True, timeout=5)
                try:
                    result = self.compile()
                    self.assertFalse(result["ok"])
                    self.assertEqual(result["artifacts"], [])
                finally:
                    output.unlink()
        directory.rmdir()
        directory.symlink_to(self.root, target_is_directory=True)
        self.assertFalse(self.compile()["ok"])
        self.assertEqual(self.commands, [])

    def test_output_from_flags_is_safe_and_not_duplicated(self):
        result = self.compile(flags="-o 'out with spaces'")
        self.assertEqual(result["command"].count("-o"), 1)
        self.assertEqual(result["command"][result["command"].index("-o") + 1],
                         str(self.root / "out with spaces"))

    def test_output_flag_value_is_not_mistaken_for_run_or_check(self):
        for name in ("--run", "--check"):
            with self.subTest(name=name):
                self.publish = True
                result = self.compile(flags="-o " + name)
                self.assertEqual(result["artifacts"], [name])
                self.assertIn(str(self.root / name), result["command"])

    def test_other_option_value_named_output_flag_does_not_suppress_output(self):
        result = self.compile(flags="--target -o")
        self.assertEqual(result["command"].count("-o"), 2)

    def test_response_file_check_and_ir_keep_stdout_contract(self):
        response = self.root / "flags with spaces.rsp"
        for mode in ("--check", "--emit-ir"):
            with self.subTest(mode=mode):
                response.write_text("# one argument per line\n" + mode + "\n")
                result = self.compile(flags="@'flags with spaces.rsp'")
                self.assertNotIn("-o", result["command"])
                self.assertEqual(result["artifacts"], [])

    def test_response_file_backend_and_output_receive_the_same_validation(self):
        response = self.root / "flags.rsp"
        for flags in ("--backend\nllvm\n", "-o\n../escape\n"):
            with self.subTest(flags=flags):
                response.write_text(flags)
                result = self.compile(flags="@flags.rsp")
                self.assertFalse(result["ok"])
        self.assertEqual(self.commands, [])
        response.write_text("--backend\ncanonical\n--compiler-profile\n-o\nresponse output\n")
        self.publish = True
        result = self.compile(flags="@flags.rsp")
        self.assertTrue(result["ok"])
        self.assertEqual(result["artifacts"], ["response output"])

    def test_duplicate_or_escaping_output_is_rejected_before_execution(self):
        for options in ({"output_file": "outside", "flags": "-o other"},
                        {"flags": "-o ../escape"}, {"flags": "-o a -o b"},
                        {"output_file": "../escape"}):
            with self.subTest(options=options):
                result = self.compile(**options)
                self.assertFalse(result["ok"])
        self.assertEqual(self.commands, [])

    def test_backend_in_flags_is_validated_and_profile_not_duplicated(self):
        self.require_options("compile_nql", "backend", "compiler_profile")
        for flags in ("--backend llvm", "--backend=llvm", "--backend"):
            result = self.compile(flags=flags)
            self.assertFalse(result["ok"])
        self.assertEqual(self.commands, [])
        result = self.compile(flags="--backend=canonical --compiler-profile", compiler_profile=True)
        self.assertEqual(result["command"].count("--compiler-profile"), 1)
        denied = self.compile(backend="canonical", flags="--backend nasm")
        self.assertFalse(denied["ok"])

    def test_failed_compile_does_not_claim_preserved_output(self):
        output = self.root / "old output"
        output.write_bytes(b"old output")
        output.chmod(0o751)
        self.status = 1
        result = self.compile(output_file=output.name)
        self.assertFalse(result["ok"])
        self.assertEqual(result["artifacts"], [])
        self.assertEqual(output.read_bytes(), b"old output")
        self.assertEqual(output.stat().st_mode & 0o777, 0o751)

    def test_success_without_publication_does_not_claim_old_or_missing_file(self):
        for exists in (False, True):
            with self.subTest(exists=exists):
                if exists:
                    (self.root / "output").write_bytes(b"old")
                result = self.compile(output_file="output")
                self.assertEqual(result["artifacts"], [])

    def test_successful_publication_reports_actual_explicit_and_default_outputs(self):
        self.publish = True
        for options, artifact in (({"output_file": "explicit"}, "explicit"),
                                  ({}, ".nolqu-mcp/build/source with spaces"),
                                  ({"emit_asm": True}, ".nolqu-mcp/build/source with spaces.asm")):
            with self.subTest(options=options):
                result = self.compile(**options)
                self.assertEqual(result["artifacts"], [artifact])
                self.assertTrue((self.root / artifact).is_file())

    def test_dry_run_and_check_never_claim_existing_artifacts(self):
        (self.root / "output").write_bytes(b"old")
        for flags in ("--dry-run", "--check", "--emit-ir"):
            with self.subTest(flags=flags):
                result = self.compile(output_file="output", flags=flags)
                self.assertEqual(result["artifacts"], [])


class CanonicalCompileAuditTests(unittest.TestCase):
    """Shell fixtures exercise compile/audit bookkeeping, not the compiler."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mcp-compile-audit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.nql"
        self.source.write_text("fn main(){return 0}\n")
        self.mcp = load_mcp(self.root)
        self.mcp.AUDIT_ENABLED = True
        self.driver('printf "fixture output" > "$output"\n')

    def driver(self, body):
        path = self.root / "nqlc"
        path.write_text('#!/bin/sh\noutput=\nwhile [ "$#" -gt 0 ]; do\n'
                        '  if [ "$1" = -o ]; then output=$2; shift 2; else shift; fi\n'
                        'done\n' + body)
        path.chmod(0o755)

    def events(self):
        path = self.mcp.AUDIT_PATH
        return [json.loads(line) for line in path.read_text().splitlines()] if path.is_file() else []

    def assert_event(self, result, event, artifacts):
        self.assertEqual(result["artifacts"], artifacts)
        self.assertEqual(event["artifacts"], artifacts)
        self.assertEqual(event["artifacts"], result["artifacts"])
        self.assertEqual(event["tool"], "compile_nql")
        self.assertEqual(event["capability"], "BUILD")
        for field in ("ok", "exit_code", "duration_ms", "changed_files"):
            self.assertEqual(event[field], result[field])
        self.assertEqual(event["arguments"], shlex.join(result["command"]))
        self.assertIsNone(event["git_head_before"])
        self.assertIsNone(event["git_head_after"])
        record("shell-fixture-audit", {"result": result, "event": event,
                                      "compiler_evidence": False})

    def compile(self, artifacts, **options):
        count = len(self.events())
        result = self.mcp.compile_nql(self.source.name, **options)
        events = self.events()
        self.assertEqual(len(events), count + 1, events)
        self.assert_event(result, events[-1], artifacts)
        return result

    def test_success_audits_observed_explicit_and_default_artifacts_once(self):
        for options, artifact in (({"output_file": "explicit program"}, "explicit program"),
                                  ({}, ".nolqu-mcp/build/source"),
                                  ({"flags": "-o 'flag output'"}, "flag output")):
            with self.subTest(options=options):
                result = self.compile([artifact], **options)
                self.assertTrue(result["ok"], result)
                self.assertEqual((self.root / artifact).read_bytes(), b"fixture output")

    def test_failed_and_unexecutable_commands_audit_no_artifacts_once(self):
        output = self.root / "preserved"
        output.write_bytes(b"old output")
        output.chmod(0o751)
        self.driver('exit 7\n')
        failed = self.compile([], output_file=output.name)
        self.assertEqual(failed["exit_code"], 7)
        self.assertEqual((output.read_bytes(), output.stat().st_mode & 0o777), (b"old output", 0o751))
        self.driver('printf "failed publication" > "$output"\nexit 9\n')
        published = self.compile([], output_file="failed output")
        self.assertEqual(published["exit_code"], 9)
        self.assertTrue((self.root / "failed output").is_file())
        (self.root / "nqlc").chmod(0o644)
        blocked = self.compile([], output_file="blocked output")
        self.assertFalse(blocked["ok"])
        self.assertIsNone(blocked["exit_code"])

    def test_missing_and_unchanged_outputs_audit_no_artifacts_once(self):
        self.driver('exit 0\n')
        for exists in (False, True):
            with self.subTest(exists=exists):
                output = self.root / "output"
                if exists:
                    output.write_bytes(b"unchanged")
                result = self.compile([], output_file=output.name)
                self.assertTrue(result["ok"], result)
                if exists:
                    self.assertEqual(output.read_bytes(), b"unchanged")
                else:
                    self.assertFalse(output.exists())

    def test_check_and_dry_run_audit_no_artifacts_even_if_fixture_writes(self):
        for flag in ("--check", "--emit-ir", "--dry-run"):
            with self.subTest(flag=flag):
                result = self.compile([], output_file="output", flags=flag)
                self.assertTrue(result["ok"], result)
                self.assertEqual((self.root / "output").read_bytes(), b"fixture output")

    def test_missing_compiler_or_source_does_not_invent_command_events(self):
        missing_source = self.mcp.compile_nql("missing.nql")
        (self.root / "nqlc").unlink()
        missing_compiler = self.mcp.compile_nql(self.source.name)
        for result in (missing_source, missing_compiler):
            self.assertFalse(result["ok"])
            self.assertEqual(result["artifacts"], [])
            self.assertEqual(result["command"], [])
        self.assertEqual(self.events(), [])

    def test_audit_io_failure_preserves_primary_result_and_next_audit(self):
        audit_path = self.mcp.AUDIT_PATH
        audit_path.mkdir(parents=True)
        self.driver('printf "fixture output" > "$output"\nprintf "primary stdout\\n"\n'
                    'printf "primary stderr\\n" >&2\n')
        result = self.mcp.compile_nql(self.source.name, output_file="first")
        self.assertEqual((result["ok"], result["exit_code"], result["stdout"],
                          result["stderr"], result["artifacts"]),
                         (True, 0, "primary stdout", "primary stderr", ["first"]))
        audit_path.rmdir()
        self.compile(["second"], output_file="second")

    def test_disabled_audit_does_not_leak_into_next_enabled_compile(self):
        self.mcp.AUDIT_ENABLED = False
        result = self.mcp.compile_nql(self.source.name, output_file="unaudited")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["artifacts"], ["unaudited"])
        self.assertEqual(self.events(), [])
        self.mcp.AUDIT_ENABLED = True
        self.compile(["audited"], output_file="audited")

    def test_nested_compiles_keep_each_commands_artifacts_and_sole_event(self):
        # Timing double only: both commands still run real shell children.
        run_process = self.mcp._run_process
        nested = []

        def run(command, **options):
            result = run_process(command, **options)
            if str(self.root / "outer") in command:
                nested.append(self.mcp.compile_nql(self.source.name, output_file="inner"))
            return result

        with mock.patch.object(self.mcp, "_run_process", side_effect=run):
            outer = self.mcp.compile_nql(self.source.name, output_file="outer")
        events = self.events()
        self.assertEqual(len(events), 2, events)
        self.assertTrue(nested[0]["ok"], nested)
        self.assertTrue(outer["ok"], outer)
        self.assert_event(nested[0], events[0], ["inner"])
        self.assert_event(outer, events[1], ["outer"])

    def test_concurrent_compiles_keep_each_commands_artifacts_and_sole_event(self):
        # Synchronization double only: actual subprocess execution is retained.
        run_process = self.mcp._run_process
        barrier = threading.Barrier(2, timeout=15)

        def run(command, **options):
            result = run_process(command, **options)
            barrier.wait()
            return result

        def compile_output(name):
            return self.mcp.compile_nql(self.source.name, output_file=name)

        with mock.patch.object(self.mcp, "_run_process", side_effect=run):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(compile_output, ("first", "second")))
        events = self.events()
        self.assertEqual(len(events), 2, events)
        for result, artifact in zip(results, ("first", "second")):
            self.assertTrue(result["ok"], result)
            matches = [event for event in events if event["arguments"] == shlex.join(result["command"])]
            self.assertEqual(len(matches), 1, events)
            self.assert_event(result, matches[0], [artifact])

    def test_interrupted_compile_restores_audit_context(self):
        with mock.patch.object(self.mcp, "_run_process", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.mcp.compile_nql(self.source.name)
        self.assertEqual(self.events(), [])
        result = self.mcp._run_result(["/bin/sh", "-c", "exit 0"], capability="READ_ONLY")
        events = self.events()
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(events), 1, events)
        self.assertEqual(events[0]["capability"], "READ_ONLY")
        self.assertEqual(events[0]["artifacts"], [])


class CanonicalSdkTests(unittest.TestCase):
    """Fresh stdio sessions compile and execute actual pinned C0 output."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mcp-canonical-sdk-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.tool = self.work / "tool source"
        self.tool.mkdir()
        for name in ("nql", "nqlc", "VERSION"):
            shutil.copy2(ROOT / name, self.tool / name)
        (self.tool / "tools").mkdir()
        shutil.copy2(ROOT / "tools/nql_c0_driver.sh", self.tool / "tools/nql_c0_driver.sh")
        shutil.copytree(ROOT / "bootstrap", self.tool / "bootstrap")
        self.unrelated = self.work / "unrelated cwd"
        self.unrelated.mkdir()
        self.blocked = self.work / "forbidden tools"
        self.blocked.mkdir()
        for name in ("git", "nasm", "ld", "x86_64-linux-gnu-ld", "clang", "llvm-as",
                     "python", "python3"):
            path = self.blocked / name
            path.write_text("#!/bin/sh\nexit 127\n")
            path.chmod(0o755)
        record("sdk-inputs", {str(path.relative_to(self.tool)):
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.tool.rglob("*") if path.is_file()})

    async def session(self, root, workflow, *, audit=False):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        environment = {"NOLQU_ROOT": str(root), "NOLQU_MCP_AUDIT": "1" if audit else "0",
                       "PYTHONDONTWRITEBYTECODE": "1",
                       "PATH": str(self.blocked) + os.pathsep + os.environ["PATH"]}
        if sys.platform == "android":
            # SDK stdio's default environment omits Termux's native exec shim.
            # The unchanged Bash drivers use portable /usr/bin/env shebangs.
            shim = Path("/data/data/com.termux/files/usr/lib/libtermux-exec.so")
            self.assertTrue(shim.is_file(), "native Termux exec support is required")
            environment["LD_PRELOAD"] = str(shim)
            temporary = self.work / "server temporary"
            temporary.mkdir(mode=0o700, exist_ok=True)
            environment["TMPDIR"] = str(temporary)
        server = StdioServerParameters(command=sys.executable,
            args=["-B", "-W", "error::ResourceWarning", str(MCP_SOURCE)],
            cwd=str(self.unrelated), env=environment)
        record("sdk-server", {"command": server.command, "args": server.args,
                              "cwd": server.cwd, "env": server.env})
        async with asyncio.timeout(180):
            async with stdio_client(server) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    await workflow(client)

    async def call(self, client, name, **arguments):
        response = await client.call_tool(name, arguments)
        self.assertFalse(response.isError, response)
        result = response.structuredContent
        if result is None:
            result = json.loads(response.content[0].text)
        record(name, {"arguments": arguments, "result": result})
        return result

    def command(self, *argv, payload=b""):
        command = [str(arg) for arg in argv]
        result = subprocess.run(command, input=payload, capture_output=True,
                                cwd=self.unrelated, timeout=60)
        record("real-command", {"argv": command, "cwd": self.unrelated,
            "stdin_hex": payload.hex(), "stdout_hex": result.stdout.hex(),
            "stderr_hex": result.stderr.hex(), "exit_code": result.returncode})
        return result

    def execute(self, path, payload=b""):
        runner = [] if platform.machine() == "x86_64" else ["qemu-x86_64"]
        return self.command(*runner, path, payload=payload)

    def test_fresh_stdio_real_compilation_persists_sole_matching_audit_event(self):
        source = self.tool / "audited source.nql"
        source.write_text("fn main(){byte_store(0,65) byte_store(1,10) output_write(0,2) return 0}\n")
        output = self.tool / "audited program"
        audit_path = self.tool / ".nolqu-mcp/audit.jsonl"
        self.assertFalse(audit_path.exists())

        async def workflow(client):
            result = await self.call(client, "compile_nql", source_file=source.name,
                                     output_file=output.name, backend="canonical")
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["stdout"], "")
            self.assertEqual(result["artifacts"], ["audited program"])
            self.assertEqual(output.read_bytes()[:4], b"\x7fELF")
            events = [json.loads(line) for line in audit_path.read_text().splitlines()]
            self.assertEqual(len(events), 1, events)
            event = events[0]
            self.assertEqual(event["tool"], "compile_nql")
            self.assertEqual(event["capability"], "BUILD")
            self.assertEqual(event["artifacts"], ["audited program"])
            self.assertEqual(event["artifacts"], result["artifacts"])
            for field in ("ok", "exit_code", "duration_ms", "changed_files"):
                self.assertEqual(event[field], result[field])
            self.assertEqual(event["arguments"], shlex.join(result["command"]))
            executed = self.execute(output)
            self.assertEqual((executed.returncode, executed.stdout, executed.stderr), (0, b"A\n", b""))
            record("real-sdk-audit-proof", {"result": result, "event": event,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "artifact_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "artifact_mode": oct(output.stat().st_mode & 0o777),
                "audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
                "server_cwd": self.unrelated, "tool_root": self.tool})

        asyncio.run(self.session(self.tool, workflow, audit=True))
        self.assertEqual(len(audit_path.read_text().splitlines()), 1)
        receipts = os.environ.get("NQL_MCP_RECEIPTS")
        if receipts:
            directory = Path(receipts)
            shutil.copy2(output, directory / "audited-program.elf")
            shutil.copy2(source, directory / "audited-source.nql")
            shutil.copy2(audit_path, directory / "audit.jsonl")

    def test_fresh_stdio_real_checksum_elf_failures_and_runtime(self):
        source = self.tool / "checksum.nql"
        shutil.copy2(ROOT / "examples/canonical/checksum.nql", source)

        async def workflow(client):
            compiled = await self.call(client, "compile_nql", source_file=source.name,
                                       output_file="checksum program", backend="canonical")
            self.assertTrue(compiled["ok"], compiled)
            self.assertEqual(compiled["stdout"], "")
            self.assertEqual(compiled["artifacts"], ["checksum program"])
            output = self.tool / "checksum program"
            self.assertEqual(output.read_bytes()[:4], b"\x7fELF")
            inspected = self.command("readelf", "-h", "-l", "-d", output)
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            self.assertIn(b"ELF64", inspected.stdout)
            self.assertIn(b"Advanced Micro Devices X86-64", inspected.stdout)
            self.assertIn(b"GNU_STACK", inspected.stdout)
            self.assertNotIn(b"INTERP", inspected.stdout)
            self.assertNotIn(b"NEEDED", inspected.stdout)
            self.assertNotIn(b"RWE", inspected.stdout)
            payload = bytes(range(256)) * 3 + b"canonical\n"
            executed = self.execute(output, payload)
            self.assertEqual(executed.returncode, 0, executed.stderr)
            self.assertEqual(executed.stdout, (str(sum(payload) % 251) + "\n").encode())
            self.assertEqual(executed.stderr, b"")
            receipts = os.environ.get("NQL_MCP_RECEIPTS")
            if receipts:
                shutil.copy2(output, Path(receipts) / "checksum.elf")
                shutil.copy2(source, Path(receipts) / "checksum.nql")
            legacy = await self.call(client, "compile_file", source_file=source.name,
                                     flags="--backend canonical")
            self.assertIsInstance(legacy["result"], str)
            self.assertIn("exit_code: 0", legacy["result"])
            self.assertNotIn("STDOUT:", legacy["result"])
            self.assertEqual((self.tool / ".nolqu-mcp/build/checksum").read_bytes(), output.read_bytes())
            before = output.read_bytes(), output.stat().st_mode
            (self.tool / "bad.nql").write_text("fn main(){return unknown}\n")
            failed = await self.call(client, "compile_nql", source_file="bad.nql",
                                     output_file=output.name, backend="canonical")
            self.assertFalse(failed["ok"])
            self.assertIn("C0B-", failed["stderr"])
            self.assertEqual(failed["artifacts"], [])
            self.assertEqual((output.read_bytes(), output.stat().st_mode), before)
            unsupported = await self.call(client, "compile_nql", source_file=source.name,
                                          backend="canonical", emit_asm=True)
            self.assertFalse(unsupported["ok"])
            self.assertEqual(unsupported["artifacts"], [])
            runtime = self.tool / "runtime.nql"
            runtime.write_text("fn main(){return 9223372036854775807+1}\n")
            built = await self.call(client, "compile_nql", source_file=runtime.name,
                                    backend="canonical")
            self.assertTrue(built["ok"], built)
            trapped = self.execute(self.tool / ".nolqu-mcp/build/runtime")
            self.assertEqual(trapped.returncode, 70)
            self.assertIn(b"C0R-001", trapped.stderr)
            seed = self.tool / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed"
            seed.rename(seed.with_suffix(".missing"))
            missing = await self.call(client, "compile_nql", source_file=source.name,
                                      backend="canonical", output_file=output.name)
            self.assertFalse(missing["ok"])
            self.assertEqual(missing["artifacts"], [])
            self.assertEqual((output.read_bytes(), output.stat().st_mode), before)
            status = await self.call(client, "canonical_bootstrap_status")
            for stage in ("full_compiler", "self_hosting", "verified"):
                self.assertNotEqual(status["stages"][stage]["status"], "PASS")

        asyncio.run(self.session(self.tool, workflow))

    def test_fresh_stdio_explicit_run_preserves_literal_tail(self):
        source = self.tool / "run literal.nql"
        source.write_text("fn main(){byte_store(0,82) byte_store(1,10) output_write(0,2) return 23}\n")
        tail = ["one two", "@missing.rsp", "--backend", "nasm", "--compiler-profile"]

        async def workflow(client):
            result = await self.call(client, "compile_nql", source_file=source.name,
                backend="canonical", flags="--run -- 'one two' @missing.rsp --backend nasm --compiler-profile")
            self.assertEqual(result["exit_code"], 23, result)
            self.assertEqual(result["stdout"], "R")
            self.assertFalse(result["ok"])
            self.assertEqual(result["artifacts"], [])
            command = result["command"]
            separator = command.index("--")
            self.assertEqual(command[separator - 1], str(source))
            self.assertEqual(command[separator + 1:], tail)
            self.assertNotIn("--compiler-profile", command[:separator])

        asyncio.run(self.session(self.tool, workflow))

    def test_fresh_stdio_native_utility_reads_literal_paths_and_binary_stdin(self):
        source = self.tool / "native reader.nql"
        shutil.copy2(ROOT / "examples/canonical/native_cat.nql", source)
        literal = self.tool / "input with spaces.bin"
        payload = bytes(range(256)) + b"\x00native\xff\n"
        literal.write_bytes(payload)
        before = (literal.read_bytes(), literal.stat().st_mode)

        async def workflow(client):
            result = await self.call(client, "compile_nql", source_file=source.name,
                                     backend="canonical", output_file="native reader")
            self.assertTrue(result["ok"], result)
            binary = self.tool / "native reader"
            stdin = self.execute(binary, payload)
            self.assertEqual((stdin.returncode, stdin.stdout, stdin.stderr), (0, payload, b""))
            runner = [] if platform.machine() == "x86_64" else ["qemu-x86_64"]
            actual = self.command(*runner, binary, literal)
            self.assertEqual((actual.returncode, actual.stdout, actual.stderr), (0, payload, b""))
            self.assertEqual((literal.read_bytes(), literal.stat().st_mode), before)
            status = await self.call(client, "canonical_bootstrap_status")
            self.assertEqual((status["current_frontend"], status["current_backend"]), ("C0.32", "C0.32"))
            self.assertEqual(status["current_c0"], "C0.25")
            for flag in ("capacity_verified", "compiler_profile_verified", "component_generation_verified",
                         "unsafe_blocks_verified", "process_arguments_verified", "syscall_abi_verified"):
                self.assertIs(status[flag], False, flag)
            for stage in ("full_compiler", "self_hosting", "verified"):
                self.assertEqual(status["stages"][stage]["status"], "NOT_IMPLEMENTED")

        asyncio.run(self.session(self.tool, workflow, audit=True))

    def test_fresh_stdio_native_permission_failure_preserves_existing_output(self):
        source = self.tool / "unsafe permission.nql"
        source.write_text("fn main(){return byte_address(0,0)}\n")
        output = self.tool / "preserved output"
        output.write_bytes(b"existing executable must survive")
        output.chmod(0o751)
        before = (output.read_bytes(), output.stat().st_mode)

        async def workflow(client):
            denied = await self.call(client, "compile_nql", source_file=source.name,
                                     backend="canonical", output_file=output.name)
            self.assertFalse(denied["ok"], denied)
            self.assertEqual(denied["exit_code"], 1)
            self.assertIn("C0S-001", denied["stderr"])
            self.assertEqual(denied["artifacts"], [])
            self.assertEqual((output.read_bytes(), output.stat().st_mode), before)

        asyncio.run(self.session(self.tool, workflow, audit=True))

    def test_fresh_stdio_reserved_name_compilation_preserves_tools(self):
        source = self.tool / "nqlc.nql"
        source.write_text("fn main(){byte_store(0,82) byte_store(1,10) output_write(0,2) return 0}\n")
        tools = [self.tool / name for name in ("nqlc", "nql", "tools/nql_c0_driver.sh")]
        before = {str(path): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode)
                  for path in tools}

        async def workflow(client):
            result = await self.call(client, "compile_nql", source_file=source.name, backend="canonical")
            after = {str(path): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode)
                     for path in tools}
            self.assertEqual(after, before)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["stdout"], "")
            self.assertEqual(result["artifacts"], [".nolqu-mcp/build/nqlc"])
            output = self.tool / ".nolqu-mcp/build/nqlc"
            self.assertEqual(output.read_bytes()[:4], b"\x7fELF")
            executed = self.execute(output)
            self.assertEqual((executed.returncode, executed.stdout, executed.stderr), (0, b"R\n", b""))
            record("reserved-name-tools", {"before": before, "after": after,
                "output": output, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
            receipts = os.environ.get("NQL_MCP_RECEIPTS")
            if receipts:
                shutil.copy2(output, Path(receipts) / "reserved-name.elf")
                shutil.copy2(source, Path(receipts) / "reserved-name.nql")

        asyncio.run(self.session(self.tool, workflow))

    def test_fresh_stdio_project_manifest_and_profile_only_program(self):
        async def initialize(client):
            result = await self.call(client, "nql_init", project_name="app", backend="canonical")
            self.assertTrue(result["ok"], result)

        asyncio.run(self.session(self.tool, initialize))
        app = self.tool / "app"
        manifest = (app / "nql.toml").read_text()
        self.assertIn('backend = "canonical"', manifest)
        self.assertNotIn("profile", manifest)
        for name in ("nql", "nqlc"):
            (app / name).symlink_to(self.tool / name)
        program = ("fn main(){byte_store(65536,80) byte_store(65537,10) "
                   "output_write(65536,2) return 0}\n")
        (app / "src/main.nql").write_text(program)
        (app / "tests/smoke.nql").write_text(program)

        async def workflow(client):
            checked = await self.call(client, "nql_check", compiler_profile=True)
            self.assertTrue(checked["ok"], checked)
            built = await self.call(client, "nql_build", compiler_profile=True)
            self.assertTrue(built["ok"], built)
            self.assertNotIn("--backend", built["command"])
            image = app / ".nql/build/app"
            self.assertEqual(image.read_bytes()[:4], b"\x7fELF")
            profiled_hash = hashlib.sha256(image.read_bytes()).hexdigest()
            self.assertEqual(self.execute(image).stdout, b"P\n")
            cached = await self.call(client, "nql_build", compiler_profile=True)
            self.assertTrue(cached["ok"], cached)
            self.assertIn("cached", cached["stderr"].lower())
            # The reviewed run path recompiles via nqlc --run, even after build hits.
            before_run = image.stat()
            running = await self.call(client, "nql_run", compiler_profile=True)
            self.assertTrue(running["ok"], running)
            self.assertEqual(running["stdout"], "P")
            self.assertEqual(hashlib.sha256(image.read_bytes()).hexdigest(), profiled_hash)
            self.assertNotEqual((image.stat().st_ino, image.stat().st_mtime_ns),
                                (before_run.st_ino, before_run.st_mtime_ns))
            record("profile-runtime", {"profiled_sha256": profiled_hash,
                "cached_output_inode": before_run.st_ino, "run_output_inode": image.stat().st_ino,
                "run_republished": True})
            tested = await self.call(client, "nql_test", compiler_profile=True)
            self.assertTrue(tested["ok"], tested)
            default = await self.call(client, "nql_run")
            self.assertFalse(default["ok"])
            self.assertEqual(default["exit_code"], 70)
            self.assertIn("C0R-", default["stderr"])
            self.assertNotEqual(hashlib.sha256(image.read_bytes()).hexdigest(), profiled_hash)
            failed_tests = await self.call(client, "nql_test")
            self.assertFalse(failed_tests["ok"])
            self.assertEqual((app / "nql.toml").read_text(), manifest)

        asyncio.run(self.session(app, workflow))


if __name__ == "__main__":
    unittest.main()
