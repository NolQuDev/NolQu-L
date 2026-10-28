"""Controls for the optional Android host bundle; no native-host assumption."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import py_compile
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from bounded_runner import BoundedRunner

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/nql_android_smoke.py"


class AndroidHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not TOOL.is_file():
            raise AssertionError("Android host smoke tool is not implemented")
        spec = importlib.util.spec_from_file_location("nql_android_smoke_test", TOOL)
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nql-android-control-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def prepare(self):
        bundle = self.base / "bundle"
        self.tool.prepare_bundle(ROOT, bundle)
        return bundle

    def test_AB01_independent_regular_copies(self):
        bundle = self.prepare()
        manifest = self.tool.verify_bundle(bundle)
        self.assertEqual(manifest["schema"], "NQL-ANDROID-SMOKE/2")
        for name in manifest["files"]:
            self.assertTrue((bundle / name).is_file())
            self.assertFalse((bundle / name).is_symlink())
        seed = bundle / "frontend.seed"
        expected = seed.read_bytes()
        seed.write_bytes(b"copied mutation")
        self.assertEqual((ROOT / self.tool.SEEDS["frontend"]).read_bytes(), expected)

    def test_AB02_wrong_pin_prevents_preparation(self):
        original = self.tool._read_regular

        def wrong_pin(path, limit):
            if Path(path).name == "c0-frontend.sha256":
                return b"0" * 64 + b"  c0-frontend.seed\n"
            return original(path, limit)

        with patch.object(self.tool, "_read_regular", side_effect=wrong_pin):
            with self.assertRaisesRegex(ValueError, "pin"):
                self.tool.prepare_bundle(ROOT, self.base / "bundle")
        self.assertFalse((self.base / "bundle/manifest.json").exists())

    def test_AB03_fifo_and_partial_bundle_are_rejected(self):
        fifo = self.base / "fifo"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, "regular"):
            self.tool._read_regular(fifo, 1024)
        incomplete = self.base / "incomplete"
        incomplete.mkdir()
        (incomplete / "frontend.seed").write_bytes(b"partial")
        with self.assertRaises((OSError, ValueError)):
            self.tool.verify_bundle(incomplete)

    def test_AB04_modified_and_traversing_manifest_fail_closed(self):
        bundle = self.prepare()
        (bundle / "backend.seed").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "identity"):
            self.tool.verify_bundle(bundle)
        manifest_path = bundle / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"]["../outside.py"] = manifest["files"].pop("bounded_runner.py")
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "file set"):
            self.tool.verify_bundle(bundle)

    def test_AB05_existing_directories_are_preserved(self):
        bundle = self.prepare()
        before = (bundle / "manifest.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.tool.prepare_bundle(ROOT, bundle)
        self.assertEqual((bundle / "manifest.json").read_bytes(), before)
        output = self.base / "output"
        output.mkdir()
        (output / "sentinel").write_bytes(b"old evidence")
        with self.assertRaises(FileExistsError):
            self.tool.run_bundle(bundle, output)
        self.assertEqual((output / "sentinel").read_bytes(), b"old evidence")

    def test_AB06_missing_or_traced_proc_cannot_claim_native(self):
        proc = self.base / "proc"
        (proc / "self").mkdir(parents=True)
        for status in ("Name:\tpython\n", "Name:\tpython\nTracerPid:\t41\n"):
            (proc / "self/status").write_text(status)
            with patch.object(sys, "executable", "/data/data/com.termux/files/usr/bin/python3"):
                context = self.tool.host_context(proc)
            self.assertFalse(context["native_termux"])
        self.assertIsNone(self.tool.host_context(self.base / "missing")["tracer_pid"])

    def test_AB07_native_requirement_blocks_before_guest_launch(self):
        bundle = self.prepare()
        output = self.base / "output"
        with patch.object(self.tool, "host_context", return_value={
                "native_termux": False, "tracer_pid": 41, "context": "TRACED"}):
            report = self.tool.run_bundle(bundle, output, require_native_termux=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse((output / "calls").exists())
        self.assertEqual(json.loads((output / "result.json").read_text()), report)

    def test_AB08_real_sequential_compiler_smoke(self):
        bundle = self.prepare()
        output = self.base / "output"
        report = self.tool.run_bundle(bundle, output)
        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["checks"]), 13)
        calls = json.loads((output / "calls/invocations.json").read_text())
        self.assertGreater(len(calls["records"]), 25)
        self.assertTrue(all(x["supervisor_ok"] and not x["timed_out"]
                            for x in calls["records"]))
        self.assertEqual(json.loads((output / "result.json").read_text()), report)

    def test_AB09_unavailable_adapter_is_failed_with_evidence(self):
        bundle = self.prepare()
        output = self.base / "output"
        with patch.object(self.tool.platform, "machine", return_value="aarch64"), \
                patch.object(self.tool.shutil, "which", return_value=None):
            report = self.tool.run_bundle(bundle, output)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("qemu-x86_64", report["error"])
        self.assertEqual(json.loads((output / "result.json").read_text()), report)

    def test_AB10_unchecked_bytecode_cannot_replace_verified_runner(self):
        bundle = self.prepare()
        marker = self.base / "unverified-code-ran"
        poison = self.base / "poison.py"
        poison.write_text("from pathlib import Path\nPath(" + repr(str(marker)) +
                          ").write_text('unexpected cached code')\nraise RuntimeError('unchecked pyc executed')\n")
        cache = Path(importlib.util.cache_from_source(str(bundle / "bounded_runner.py")))
        cache.parent.mkdir()
        py_compile.compile(str(poison), cfile=str(cache), doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        oracle_cache = Path(importlib.util.cache_from_source(str(bundle / "differential_oracle.py")))
        py_compile.compile(str(poison), cfile=str(oracle_cache), doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        report = self.tool.run_bundle(bundle, self.base / "output", differential=True)
        self.assertFalse(marker.exists(), "hash-verified source was bypassed by unverified bytecode")
        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(len(report["checks"]), 15)

    def test_AB11_failed_publication_preserves_failed_terminal_report(self):
        bundle = self.prepare()
        output = self.base / "output"
        replace = os.replace
        publications = 0

        def fail_second_publication(source, destination):
            nonlocal publications
            if Path(destination) == output / "result.json":
                publications += 1
                if publications == 2:
                    raise OSError("controlled report rename failure")
            return replace(source, destination)

        with patch.object(self.tool.os, "replace", side_effect=fail_second_publication):
            try:
                report = self.tool.run_bundle(bundle, output)
            except OSError as error:
                self.fail(f"failed staging masked the terminal failure report: {error}")
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("controlled report rename failure", report["error"])
        self.assertEqual(json.loads((output / "result.json").read_text()), report)
        self.assertFalse(list(output.glob("*.pending")))
        self.assertFalse(list(output.glob(".*.pending")))

    def test_AB12_large_regular_adapter_is_hashed_without_stream_limit(self):
        bundle = self.prepare()
        underlying = shutil.which("qemu-x86_64") if self.tool.platform.machine() != "x86_64" else None
        if self.tool.platform.machine() != "x86_64":
            self.assertIsNotNone(underlying, "real compiler smoke needs the x86_64 adapter")
        adapter = self.base / "large-adapter"
        command = "[" + repr(underlying) + ", *sys.argv[1:]]" if underlying else "sys.argv[1:]"
        script = ("#!" + sys.executable + "\nimport os,sys\ncommand=" + command +
                  "\nos.execv(command[0],command)\n#").encode()
        payload = script + b"A" * (8388609 - len(script) - 1) + b"\n"
        adapter.write_bytes(payload)
        adapter.chmod(0o700)
        expected = {"bytes": 8388609, "sha256": hashlib.sha256(payload).hexdigest()}
        with patch.object(self.tool.platform, "machine", return_value="aarch64"), \
                patch.object(self.tool.shutil, "which", return_value=str(adapter)):
            report = self.tool.run_bundle(bundle, self.base / "output")
        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["adapter"]["identity"], expected)
        self.assertEqual(len(report["checks"]), 13)

    def test_AB13_real_offline_differential_profile(self):
        # Keep this complete external-CLI receipt in TMPDIR, which CI archives.
        # The outer supervisor also owns descendants if the CLI itself fails.
        evidence = Path(tempfile.mkdtemp(prefix="nql-android-differential-"))
        print("ANDROID_DIFFERENTIAL_EVIDENCE=" + str(evidence), file=sys.stderr)
        bundle, output = evidence / "bundle", evidence / "result"
        self.tool.prepare_bundle(ROOT, bundle)
        controller = BoundedRunner(evidence / "driver", timeout=660, budget=670)
        result = controller.run("offline-differential-cli",
            [sys.executable, "-B", "-W", "error::ResourceWarning",
             str(bundle / "android_smoke.py"), "run", "--bundle", str(bundle),
             "--output", str(output), "--differential"], b"")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        report = json.loads((output / "result.json").read_text())
        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(report["profile"], "smoke+differential")
        self.assertEqual(len(report["checks"]), 15)
        proof = report["differential"]
        self.assertTrue(proof["passed"])
        self.assertEqual(proof["defined_cases"], 48)
        self.assertEqual(proof["matched_profiles"], {"default": 48, "compiler": 48})
        self.assertEqual(proof["sensitivity_rejections"], ["wrong-exit", "wrong-stream"])
        corpus = (output / "differential/corpus.json").read_bytes()
        self.assertEqual(hashlib.sha256(corpus).hexdigest(), proof["corpus_sha256"])
        self.assertEqual(proof["corpus_sha256"],
                         "8fd66ecef1738a31044b39ed03926271a68cabfd49e9008294c81906608def9d")
        calls = json.loads((output / "calls/invocations.json").read_text())["records"]
        self.assertEqual(report["invocations"], len(calls))
        executions = [call for call in calls if call["label"].startswith("diff-")]
        self.assertEqual(len(executions), 294)
        self.assertTrue(all(call["supervisor_ok"] and not call["timed_out"]
                            and call["exit_code"] >= 0 for call in calls))
        self.assertIn("host_after", report)
        self.assertEqual(report["native_termux_verified"],
                         report["host"]["native_termux"] and report["host_after"]["native_termux"])

    def legacy_bundle(self):
        bundle = self.prepare()
        path = bundle / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["schema"] = "NQL-ANDROID-SMOKE/1"
        manifest["files"].pop("differential_oracle.py")
        (bundle / "differential_oracle.py").unlink()
        path.write_text(json.dumps(manifest))
        return bundle

    def test_AB14_old_bundle_keeps_ordinary_smoke(self):
        bundle = self.legacy_bundle()
        report = self.tool.run_bundle(bundle, self.base / "output")
        self.assertTrue(report["ok"], report.get("error"))
        self.assertEqual(len(report["checks"]), 13)
        self.assertEqual(report["profile"], "smoke")

    def test_AB15_old_bundle_cannot_claim_differential(self):
        bundle = self.legacy_bundle()
        output = self.base / "output"
        report = self.tool.run_bundle(bundle, output, differential=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("schema-2", report["error"])
        self.assertFalse((output / "calls").exists())

    def test_AB16_corrupt_oracle_is_rejected_before_execution(self):
        bundle = self.prepare()
        (bundle / "differential_oracle.py").write_text("raise RuntimeError('corrupt')\n")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.tool.run_bundle(bundle, self.base / "output", differential=True)
        self.assertFalse((self.base / "output").exists())

    def test_AB17_incomplete_check_inventory_cannot_publish_pass(self):
        bundle = self.prepare()
        output = self.base / "output"
        with patch.object(self.tool, "_run_smoke", return_value=None):
            report = self.tool.run_bundle(bundle, output)
        self.assertFalse(report["ok"], "an unexecuted smoke profile was marked PASS")
        self.assertIn("incomplete", report["error"])

    def test_AB18_repinned_manifest_change_during_run_is_rejected(self):
        bundle = self.prepare()
        original = self.tool._run_smoke

        def change_metadata(*args, **kwargs):
            original(*args, **kwargs)
            path = bundle / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["compiler_version"] = "changed during execution"
            path.write_text(json.dumps(manifest))

        with patch.object(self.tool, "_run_smoke", side_effect=change_metadata):
            report = self.tool.run_bundle(bundle, self.base / "output")
        self.assertFalse(report["ok"], "a different manifest was accepted after execution")
        self.assertIn("changed", report["error"])

    def test_AB19_native_requirement_is_rechecked_after_execution(self):
        bundle = self.prepare()
        contexts = [{"native_termux": True, "tracer_pid": 0, "context": "fixture-before"},
                    {"native_termux": False, "tracer_pid": 41, "context": "fixture-after"}]
        with patch.object(self.tool, "host_context", side_effect=contexts):
            report = self.tool.run_bundle(bundle, self.base / "output", require_native_termux=True)
        self.assertFalse(report["ok"], "native-at-start alone was marked PASS")
        self.assertEqual(report["host_after"], contexts[1])
        self.assertIn("native Termux", report["error"])
        self.assertFalse(report["native_termux_verified"])

    def test_AB20_partial_differential_counts_cannot_publish_pass(self):
        bundle = self.prepare()

        def partial_run(bundle, output, report, manifest, differential):
            report["checks"] = [{"id": name, "passed": True} for name in
                                self.tool.SMOKE_CHECKS + self.tool.DIFFERENTIAL_CHECKS]
            report["differential"] = dict(passed=True, defined_cases=48,
                matched_profiles={"default": 48, "compiler": 47},
                sensitivity_rejections=["wrong-exit", "wrong-stream"])

        with patch.object(self.tool, "_run_smoke", side_effect=partial_run):
            report = self.tool.run_bundle(bundle, self.base / "output", differential=True)
        self.assertFalse(report["ok"])
        self.assertIn("incomplete differential", report["error"])


if __name__ == "__main__":
    unittest.main()
