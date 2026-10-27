"""Actual component generations; canonical executables supply all compiler bytes."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True

from c031_debugger import Guest
from c031_support import (ROOT, assert_owned_graph, build_predecessors, candidate_binary,
                         decode_nqaf, encode_profile_source, run_native)


SOURCES = {name: ROOT / f"bootstrap/compiler/c0/{name}.nql"
           for name in ("frontend", "backend")}
STAGE = ROOT / "bootstrap/compiler/c0/x86_64-linux"
GENERATION_ORACLES = (
    "test_c0_capacity_backend.CapacityBackendTests.test_wide_header_and_graph_mutations",
    "test_c0_capacity_backend.CapacityBackendTests.test_legacy_byte_parity_and_limits",
    "test_c0_capacity_backend.CapacityBackendTests.test_high_global_ids_use_local_frames",
    "test_c0_capacity_backend.CapacityBackendTests.test_intrinsic_ids_do_not_alias_user_nodes",
    "test_c0_capacity_backend.CapacityBackendTests.test_wide_name_resolution_and_scope",
    "test_c0_capacity_backend.CapacityBackendTests.test_fragmented_stream_waits_for_eof",
    "test_c0_capacity_frontend.CapacityFrontendTests.test_frozen_predecessor_limits_and_legacy_bytes",
    "test_c0_capacity_frontend.CapacityFrontendTests.test_long_binding_and_callee_lengths",
    "test_c0_capacity_frontend.CapacityFrontendTests.test_fragmented_profile_header_keeps_source_offsets",
    "test_c0_capacity_frontend.CapacityFrontendTests.test_waits_for_eof_after_valid_prefix",
    "test_c0_backend.BackendTests.test_invalid_headers_and_framing",
    "test_c0_backend.BackendTests.test_invalid_nodes_and_graphs",
    "test_c0_backend.BackendTests.test_statement_local_postorder_is_required",
    "test_c0_runtime_io.RuntimeTests.test_stdio_and_eof",
    "test_c0_runtime_io.RuntimeTests.test_descriptor_errors",
    "test_c0_compiler_profile.CompilerProfileTests.test_live_pipe_read_preserves_short_count_without_eof",
    "test_c0_compiler_profile.CompilerProfileTests.test_real_closed_descriptors",
    "test_c0_compiler_profile.CompilerProfileTests.test_empty_end_ranges_do_not_touch_descriptors",
    'test_c0_native_frontend.NativeFrontendTests.test_unsafe_scope_and_header',
    'test_c0_native_frontend.NativeFrontendTests.test_native_transport_and_shadows',
    'test_c0_native_frontend.NativeFrontendTests.test_raw_calls_need_owning_unsafe_scope',
    'test_c0_native_frontend.NativeFrontendTests.test_nested_scope_limits',
    'test_c0_native_frontend.NativeFrontendTests.test_legacy_output_unchanged',
    'test_c0_native_frontend.NativeFrontendTests.test_frontend_errors_and_offsets',
    'test_c0_native_backend.NativeBackendTests.test_frozen_c031_baseline_is_independent',
    'test_c0_native_backend.NativeBackendTests.test_frozen_c031_byte_parity',
    'test_c0_native_backend.NativeBackendTests.test_wire_scope_ownership_mutations',
    'test_c0_native_backend.NativeBackendTests.test_legacy_versions_cannot_enable_native_ops',
    'test_c0_native_backend.NativeBackendTests.test_source_header_is_independently_validated',
    'test_c0_native_backend.NativeBackendTests.test_shadow_resolution_and_arity',
    'test_c0_native_runtime.NativeRuntimeTests.test_argv_exact_bytes_and_bounds',
    'test_c0_native_runtime.NativeRuntimeTests.test_raw_errors_and_frame_range',
    'test_c0_native_runtime.NativeRuntimeTests.test_six_register_file_mmap',
    'test_c0_native_runtime.NativeRuntimeTests.test_callee_saved_and_alignment',
    'test_c0_native_runtime.NativeRuntimeTests.test_arena_profiles_and_cleanup',
    'test_c0_native_runtime.NativeRuntimeTests.test_raw_io_progress',
    'test_c0_native_program.NativeProgramTests.test_stdin_and_literal_binary_files',
    'test_c0_native_program.NativeProgramTests.test_missing_read_and_write_errors_stop',
    'test_c0_native_program.NativeProgramTests.test_acquired_descriptor_zero_is_closed',
    'test_c0_native_program.NativeProgramTests.test_caller_retries_io_but_never_retries_close',
    'test_c0_native_program.NativeProgramTests.test_argument_copy_limit_is_explicit',
)


def fingerprint(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def first_difference(left, right):
    for offset, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return offset
    return min(len(left), len(right)) if len(left) != len(right) else None


class Evidence:
    def __init__(self, label, binaries):
        parent = os.environ.get("C031_WORK")
        self.temporary = None
        if parent:
            self.path = Path(tempfile.mkdtemp(prefix=label + "-", dir=parent))
        else:
            self.temporary = tempfile.TemporaryDirectory(prefix="c031-" + label + "-")
            self.path = Path(self.temporary.name)
        paths = [*SOURCES.values(), Path(__file__),
                 ROOT / "tests/bootstrap/c031_support.py",
                 ROOT / "tests/bootstrap/c031_debugger.py",
                 ROOT / "tests/bootstrap/c032_support.py",
                 ROOT / "examples/canonical/native_cat.nql",
                 ROOT / "tests/bootstrap/c0_native_os.sh",
                 ROOT / "tests/bootstrap/fixtures/c032/predecessor/hashes.json",
                 *ROOT.glob("tests/bootstrap/fixtures/c032/predecessor/*.nql"), *binaries.values(),
                 ROOT / "tests/bootstrap/c0_capacity.sh",
                 ROOT / "bootstrap/compiler/b0/compiler.nql0",
                 ROOT / "bootstrap/stage0/x86_64-linux/stage0.seed",
                 ROOT / "tests/bootstrap/fixtures/c031/predecessor/hashes.json",
                 *ROOT.glob("tests/bootstrap/fixtures/c031/predecessor/*.nql*"),
                 *ROOT.glob("tests/bootstrap/test_c0_*.py"),
                 *ROOT.glob("bootstrap/**/x86_64-linux/*.sha256"),
                 *ROOT.glob("bootstrap/**/x86_64-linux/*.seed")]
        self.identities = {str(path.resolve()): fingerprint(path.read_bytes())
                           for path in paths}
        self.seals = {}
        self.receipt = dict(argv=sys.argv, cwd=str(Path.cwd()),
                            identities=self.identities, stages=[], artifacts={},
                            comparisons=[], checks=[], rejections=[],
                            component_generations_verified=False)
        for name, path in {"test-source.py": Path(__file__),
                           **{name + ".nql": path for name, path in SOURCES.items()}}.items():
            (self.path / name).write_bytes(path.read_bytes())
        self.save()

    def save(self):
        (self.path / "receipt.json").write_text(
            json.dumps(self.receipt, indent=2, sort_keys=True) + "\n")

    def unchanged(self):
        for name, expected in self.identities.items():
            if fingerprint(Path(name).read_bytes()) != expected:
                raise AssertionError(f"input identity changed: {name}")

    def run(self, label, binary, data=b"", *, args=(), timeout=120):
        self.unchanged()
        self.read_artifact(binary)
        started = time.monotonic()
        result = None
        try:
            result = run_native(binary, data, args=args, timeout=timeout, cwd=ROOT)
            return result
        except subprocess.TimeoutExpired as error:
            result = error
            raise
        finally:
            if result is not None:
                self.observed(label, binary, data, result, time.monotonic() - started, timeout)
            self.unchanged()
            self.read_artifact(binary)

    def observed(self, label, binary, data, result, elapsed, timeout):
        prefix = self.path / f"{len(self.receipt['stages']):03d}-{label}"
        output, error_output = result.stdout or b"", result.stderr or b""
        for suffix, content in (("stdin", data), ("stdout", output), ("stderr", error_output)):
            Path(str(prefix) + "." + suffix).write_bytes(content)
        self.receipt["stages"].append(dict(
            label=label, command=list(result.args) if isinstance(
                result, subprocess.CompletedProcess) else list(result.cmd),
            binary=str(binary), input=fingerprint(data), stdout=fingerprint(output),
            stderr=fingerprint(error_output), returncode=getattr(result, "returncode", None),
            timed_out=isinstance(result, subprocess.TimeoutExpired),
            timeout_seconds=timeout, elapsed_seconds=elapsed, prefix=str(prefix)))
        self.save()

    def read_artifact(self, path):
        path = Path(path)
        data = path.read_bytes()
        expected = self.seals.get(path)
        if expected is not None and fingerprint(data) != expected:
            self.receipt["rejections"].append(dict(
                path=str(path), expected=expected, actual=fingerprint(data)))
            self.save()
            raise AssertionError(f"artifact identity changed: {path}")
        return data

    def close(self):
        if self.temporary is not None:
            self.temporary.cleanup()

    def artifact(self, label, data):
        path = self.path / (label + ".artifact")
        path.write_bytes(data)
        self.receipt["artifacts"][label] = dict(path=str(path), **fingerprint(data))
        self.save()
        return path

    def equal(self, label, left, right):
        difference = first_difference(left, right)
        self.receipt["comparisons"].append(dict(
            label=label, left=fingerprint(left), right=fingerprint(right),
            first_difference_offset=difference))
        self.save()
        if difference is not None:
            raise AssertionError(f"{label}: first difference at byte {difference}")

    @contextmanager
    def checked(self, label):
        check = dict(label=label, passed=False)
        self.receipt["checks"].append(check)
        try:
            yield
            check["passed"] = True
        except Exception as error:
            check["error"] = str(error)
            raise
        finally:
            self.save()


class GenerationCase(unittest.TestCase):
    def setUp(self):
        self.binaries = dict(
            b0=candidate_binary("B0_COMPILER", ROOT / "bootstrap/compiler/b0/x86_64-linux/b0.seed"),
            frontend=candidate_binary("C0_FRONTEND", STAGE / "c0-frontend.seed"),
            backend=candidate_binary("C0_BACKEND", STAGE / "c0-backend.seed"))
        self.evidence = Evidence(self._testMethodName, self.binaries)
        self.addCleanup(self.evidence.close)
        temporary = tempfile.TemporaryDirectory(prefix="work-", dir=self.evidence.path)
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.sources = {name: path.read_bytes() for name, path in SOURCES.items()}

    def compile_component(self, name, pair, label):
        return self.compile_source(self.sources[name], pair, label, profile=True)

    def parse(self, source, frontend, label, *, profile=False, version=None):
        parsed = self.evidence.run(label + "-frontend", frontend,
                                   encode_profile_source(source) if profile else source, timeout=1200)
        self.assertEqual(parsed.returncode, 0, parsed.stderr)
        self.assertEqual(parsed.stderr, b"")
        header, nodes = decode_nqaf(parsed.stdout)
        self.assertEqual(header["source"], source)
        self.assertEqual(header["runtime_profile"], int(profile))
        if version is not None:
            self.assertEqual(header["version"], version)
        elif profile:
            self.assertEqual(header["version"], 5)
        assert_owned_graph(header, nodes)
        self.evidence.artifact(label + "-nqaf", parsed.stdout)
        return parsed.stdout

    def compile_source(self, source, pair, label, *, profile=False, version=None):
        wire = self.parse(source, pair["frontend"], label, profile=profile, version=version)
        compiled = self.evidence.run(label + "-backend", pair["backend"],
                                     wire, timeout=1200)
        return self.accept_result(label, compiled)

    def accept_result(self, label, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        return self.executable(label, result.stdout)

    def run_generation_oracles(self, generation, pair):
        self.evidence.unchanged()
        identities = {name: dict(path=str(path), **fingerprint(self.evidence.read_artifact(path)))
                      for name, path in pair.items()}
        command = [sys.executable, "-B", "-W", "error::ResourceWarning", "-m", "unittest", "-v",
                   *GENERATION_ORACLES]
        started = time.monotonic()
        timed_out = False
        native_directory = self.evidence.path / (generation + "-native-machine")
        self.assertFalse(native_directory.exists())
        with tempfile.TemporaryDirectory(prefix="c031-oracle-") as directory:
            environment = {**os.environ, "PYTHONPATH": str(ROOT / "tests/bootstrap"),
                           "TMPDIR": directory, "C0_FRONTEND": str(pair["frontend"]),
                           "C0_BACKEND": str(pair["backend"]),
                           "C032_NATIVE_EVIDENCE_DIR": str(native_directory)}
            with subprocess.Popen(command, cwd=ROOT, env=environment, start_new_session=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                try:
                    output, error = process.communicate(timeout=1200)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    output, error = process.communicate()
                finally:
                    if process.poll() is None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.communicate(timeout=5)
            result = subprocess.CompletedProcess(command, process.returncode, output, error)
        self.evidence.observed(generation + "-named-oracles", sys.executable, b"", result,
                               time.monotonic() - started, 1200)
        self.evidence.receipt["stages"][-1]["timed_out"] = timed_out
        self.evidence.receipt.setdefault("oracles", []).append(dict(
            generation=generation, components=identities, selectors=list(GENERATION_ORACLES),
            environment={key: environment[key] for key in ("C0_FRONTEND", "C0_BACKEND", "PYTHONPATH", "TMPDIR", "C032_NATIVE_EVIDENCE_DIR")},
            returncode=result.returncode, timed_out=timed_out,
            child_reaped=process.poll() is not None, temporary_removed=not Path(directory).exists()))
        self.evidence.save()
        self.evidence.unchanged()
        for path in pair.values():
            self.evidence.read_artifact(path)
        self.assertFalse(timed_out, "generation oracle timed out")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(result.stdout, b"")
        self.assertRegex(result.stderr, rb"\nRan " + str(len(GENERATION_ORACLES)).encode()
                         + rb" tests in [0-9.]+s\n\nOK\n$", "missing complete, skip-free oracle result")

        # Machine artifacts are evidence from the actual named runtime tests,
        # outside their disposable program/fixture directory. Preserve canonical
        # labels as well as the original per-profile names and trace references.
        expected = {f"mmap-profile{profile}.{suffix}" for profile in (0, 1)
                    for suffix in ("json", "nql", "nqaf", "elf")}
        self.assertEqual({path.name for path in native_directory.iterdir()}, expected)
        profiles = {}
        for profile in (0, 1):
            labels = {}
            for suffix in ("json", "nql", "nqaf", "elf"):
                label = f"{generation}-native-mmap-profile{profile}-{suffix}"
                artifact = self.evidence.artifact(label, (native_directory / f"mmap-profile{profile}.{suffix}").read_bytes())
                artifact.chmod(0o755 if suffix == "elf" else 0o644)
                labels[suffix] = label
            profiles[str(profile)] = labels
        self.evidence.receipt.setdefault("machine_evidence", {})[generation] = dict(
            directory=str(native_directory), profiles=profiles)
        self.evidence.save()

    def corpus(self, generation, pair):
        from test_c0_runtime_io import PREDECESSOR_SOURCES

        scalar = [
            ("fn main(){return 7}", 7),
            ("fn main(){let long_name=1 let aa=2 long_name=long_name+aa return long_name}", 3),
            ("fn main(){return (0-9223372036854775807-1)/1}", 0),
            ("fn main(){\r\n // comment\r\n let _A42=0001; return _A42; }", 1),
        ]
        for expression, status in (("23+7+2", 32), ("23+7-2", 28), ("23+7*2", 37), ("23+7/2", 26),
                                   ("23-7+2", 18), ("23-7-2", 14), ("23-7*2", 9), ("23-7/2", 20),
                                   ("23*7+2", 163), ("23*7-2", 159), ("23*7*2", 66), ("23*7/2", 80),
                                   ("23/7+2", 5), ("23/7-2", 1), ("23/7*2", 6), ("23/7/2", 1)):
            scalar.append(("fn main(){return " + expression + "}", status))
        groups = [
            ("runtime", list(zip(PREDECESSOR_SOURCES, (7, 0, 42, 120, 8, 9, 6, 2, 3, 21))),
             "72d2daec04eac75483e3c4731719992b9a97693ee2a35209340d6c5dedd3fc4e",
             "85b4378d5ba155c5861cb90d790ce27d0a8c8f3e7727c50a95096e1b35d44365"),
            ("scalar", scalar,
             "5b8aee14a9f205e6f20ca77eafddc832cf4b3702c33285a483438a1cb73dc3b9",
             "03c8b27f782d7964e8d15bf3f353a06d038d4b71fab9c4facfb701080f0868bd"),
            ("control", [("fn main(){if 1 {return 7} else {return 9} return 0}", 7),
                         ("fn main(){let n=3 let s=0 while n {s=s+n n=n-1} return s}", 6),
                         ("fn main(){let x=1 if x {let x=x+2} return x}", 1),
                         ("fn main(){return (0-3)<(0-2)==1}", 1)],
             "a933f6eb06d0087e3d9db1d9bf67d3cb2ea6a032b835e8f13c5e45a67f817f99",
             "a29cd81af5cdb28e9d267349005d06a616cd7b1840bf8c6b7a69792a4c8eb1df"),
        ]
        case_groups = {f"{group}-{index}": group for group, sources, _, _ in groups
                       for index in range(len(sources))}
        legacy_outputs = {group: ([], []) for group, _, _, _ in groups}
        cases = [(f"{group}-{index}", source.encode("ascii"), False, status, b"", b"", None)
                 for group, sources, _, _ in groups for index, (source, status) in enumerate(sources)]
        maximum = b"9223372036854775807"
        cases += [
            ("wide-offset", b" " * 70000 + b"fn main(){return 7}", False, 7, b"", b"", None),
            ("wide-nodes", b"fn main(){let a=0 " + b"a=a+1 " * 300 + b"return a}", False, 44, b"", b"", None),
            ("streams", b"fn main(){let n=input_read(0,4) output_write(0,n) error_write(0,n) return n}", False, 4, b"ABCD", b"ABCD", None),
            ("default-bound", b"fn main(){return byte_load(65536)}", False, 70, b"", None, b"[C0R-004]"),
            ("wide-default-bound", b"fn main(){return byte_load(65536)}".ljust(8193, b" "), False, 70, b"", None, b"[C0R-004]"),
            ("profile-high", b"fn main(){byte_store(65536,42) return byte_load(65536)}", True, 42, b"", b"", None),
            ("profile-last", b"fn main(){byte_store(16777215,257) return byte_load(16777215)}", True, 1, b"", b"", None),
            ("profile-bound", b"fn main(){return byte_load(16777216)}", True, 70, b"", None, b"[C0R-004]"),
            ("profile-empty", b"fn main(){return input_read(16777216,0)+output_write(16777216,0)+error_write(16777216,0)}", True, 0, b"", b"", None),
            ("maximum", b"fn main(){return " + maximum + b"}", False, 255, b"", b"", None),
            ("maximum-digits", b"fn main(){let n=" + maximum + b" return (n/10==922337203685477580)*(n-(n/10)*10==7)}", True, 1, b"", b"", None),
            ("minimum", b"fn main(){return (0-" + maximum + b"-1)/1}", False, 0, b"", b"", None),
            ("minimum-quotient", b"fn main(){return ((0-" + maximum + b"-1)/922337203685477580)==(0-10)}", True, 1, b"", b"", None),
            ("leading-zeros", b"fn main(){return " + b"0" * 65535 + b"7}", False, 7, b"", b"", None),
            ("leading-zeros-maximum", b"fn main(){return " + b"0" * 65535 + maximum + b"}", False, 255, b"", b"", None),
            ("runtime-add-overflow", b"fn main(){return " + maximum + b"+1}", True, 70, b"", None, b"[C0R-001]"),
            ("runtime-minimum-overflow", b"fn main(){return (0-" + maximum + b"-1)-1}", True, 70, b"", None, b"[C0R-001]"),
            ("runtime-division-overflow", b"fn main(){return (0-" + maximum + b"-1)/(0-1)}", True, 70, b"", None, b"[C0R-001]"),
        ]
        for label, source, profile, status, output, error, code in cases:
            with self.subTest(generation=generation, corpus=label), self.evidence.checked(generation + "-" + label):
                group = case_groups.get(label)
                label = generation + "-" + label
                program = self.compile_source(source, pair, label, profile=profile)
                if group is not None:
                    wire = Path(self.evidence.receipt["artifacts"][label + "-nqaf"]["path"]).read_bytes()
                    legacy_outputs[group][0].append(wire)
                    legacy_outputs[group][1].append(self.evidence.read_artifact(program))
                result = self.evidence.run(label + "-execute", program, b"ABCD")
                self.assertEqual((result.returncode, result.stdout), (status, output), result.stderr)
                if code is None:
                    self.assertEqual(result.stderr, error)
                else:
                    self.assertRegex(result.stderr, rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0R-")
                    self.assertIn(code, result.stderr)

        for group, sources, ast_hash, elf_hash in groups:
            with self.subTest(generation=generation, parity=group), self.evidence.checked(generation + "-parity-" + group):
                asts, elfs = legacy_outputs[group]
                self.assertEqual((len(asts), len(elfs)), (len(sources), len(sources)))
                self.assertEqual(hashlib.sha256(b"".join(asts)).hexdigest(), ast_hash)
                self.assertEqual(hashlib.sha256(b"".join(elfs)).hexdigest(), elf_hash)

        for profile in (False, True):
            for label, digits in (("max-plus-one", b"9223372036854775808"),
                                  ("huge-invalid", b"9" * 65536),
                                  ("invalid-tail", b"9223372036854775808" + b"7" * 100)):
                with self.subTest(generation=generation, corpus=label, profile=profile), self.evidence.checked(f"{generation}-{label}-{int(profile)}"):
                    source = b"fn main(){return " + digits + b"}"
                    label = f"{generation}-{label}-{int(profile)}"
                    wire = self.parse(source, pair["frontend"], label, profile=profile)
                    result = self.evidence.run(label + "-reject", pair["backend"], wire)
                    self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
                    self.assertTrue(result.stderr.startswith(b"input:1:18: error[C0B-005]:"), result.stderr)

        for label, payload, code in (("syntax", b"fn main(){return }", b"[C0P-"),
                                     ("envelope", b"NQSC\x01", b"[C0P-013]")):
            with self.subTest(generation=generation, corpus=label), self.evidence.checked(generation + "-" + label):
                result = self.evidence.run(generation + "-" + label, pair["frontend"], payload)
                self.assertEqual((result.returncode, result.stdout), (1, b""))
                self.assertIn(code, result.stderr)

        for profile in (False, True):
            source = b"fn main(){return 7}"
            label = f"{generation}-malformed-{int(profile)}"
            wire = self.parse(source, pair["frontend"], label, profile=profile)
            reserved = bytearray(wire)
            reserved[6] = 1
            anchor = bytearray(wire)
            anchor[(32 if profile else 16) + source.index(b"7")] = ord("q")
            for name, data, code in (("truncated", wire[:-1], b"[C0B-001]"),
                                      ("trailing", wire + b"\x00", b"[C0B-001]"),
                                      ("reserved", bytes(reserved), b"[C0B-001]"),
                                      ("anchor", bytes(anchor), b"[C0B-006]")):
                with self.subTest(generation=generation, corpus=name, profile=profile), self.evidence.checked(label + "-" + name):
                    result = self.evidence.run(label + "-" + name, pair["backend"], data)
                    self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
                    self.assertIn(code, result.stderr)

    def native_corpus(self, generation, pair):
        utility = (ROOT / "examples/canonical/native_cat.nql").read_bytes()
        for profile in (False, True):
            cap = 16777216 if profile else 65536
            cases = [
                ("argc", b"fn main(){return arg_count()}", (), b"", 1, b"", None),
                ("copy-empty", f"fn main(){{let n=arg_copy(1,{cap-1},1) return n+byte_load({cap-1})}}".encode(), ("",), b"", 0, b"", None),
                ("address", f"fn main(){{let n=0 unsafe{{# safety: bounded spans owned by caller\nn=byte_address({cap},0)-byte_address(0,{cap})}} return n=={cap}}}".encode(), (), b"", 1, b"", None),
                ("enosys", b"fn main(){let n=0 unsafe{# safety: owns the complete zeroed frame\nn=syscall6(999999,0)}return n==(0-38)}", (), b"", 1, b"", None),
                ("index", b"fn main(){return arg_copy(arg_count(),0,8)}", (), b"", 70, b"", b"C0R-008"),
                ("copy-bound", b"fn main(){return arg_copy(0,0,1)}", (), b"", 74, b"", b"C0R-009"),
                ("frame-bound", f"fn main(){{unsafe{{# safety: rejected frame probe\nsyscall6(39,{cap-47})}}return 0}}".encode(), (), b"", 70, b"", b"C0R-004"),
                ("negative-span", b"fn main(){unsafe{# safety: rejected range probe\nbyte_address(0-1,0)}return 0}", (), b"", 70, b"", b"C0R-004"),
                ("cat-stdin", utility, (), b"native\x00stdin\xff\n", 0, b"native\x00stdin\xff\n", None),
            ]
            for name, source, args, payload, status, output, error in cases:
                label = f"{generation}-native-{name}-{int(profile)}"
                with self.subTest(generation=generation, native=name, profile=profile), self.evidence.checked(label):
                    program = self.compile_source(source, pair, label, profile=profile, version=6)
                    actual = self.evidence.run(label + "-execute", program, payload, args=args)
                    self.assertEqual((actual.returncode, actual.stdout), (status, output), actual.stderr)
                    if error is None:
                        self.assertEqual(actual.stderr, b"")
                    else:
                        self.assertTrue(actual.stderr.startswith(b"input:"), actual.stderr)
                        self.assertIn(b"[" + error + b"]", actual.stderr)
        for name, source, code in (
                ("permission", b"fn main(){return byte_address(0,0)}", b"C0S-001"),
                ("invariant", b"fn main(){unsafe {syscall6(39,0)}return 0}", b"C0P-014")):
            label = f"{generation}-native-{name}"
            with self.subTest(generation=generation, native=name), self.evidence.checked(label):
                actual = self.evidence.run(label, pair["frontend"], source)
                self.assertEqual((actual.returncode, actual.stdout), (1, b""))
                self.assertTrue(actual.stderr.startswith(b"input:"), actual.stderr)
                self.assertIn(b"[" + code + b"]", actual.stderr)

    def executable(self, label, data):
        self.assertGreaterEqual(len(data), 64)
        self.assertLessEqual(len(data), 8388608)
        self.assertEqual(data[:7], b"\x7fELF\x02\x01\x01")
        self.assertEqual(struct.unpack_from("<HH", data, 16), (2, 62))
        entry, headers = struct.unpack_from("<QQ", data, 24)
        stride, count = struct.unpack_from("<HH", data, 54)
        self.assertEqual(stride, 56)
        self.assertGreater(count, 0)
        self.assertLessEqual(headers + stride * count, len(data))
        executable_entry = False
        nonexecutable_stack = False
        for index in range(count):
            kind, flags, offset, address, _, files, memory, _ = struct.unpack_from(
                "<IIQQQQQQ", data, headers + stride * index)
            self.assertLessEqual(offset + files, len(data))
            self.assertLessEqual(files, memory)
            self.assertNotIn(kind, (2, 3), "dynamic linkage or interpreter")
            if kind == 1:
                self.assertNotEqual(flags & 3, 3, "writable executable load")
                executable_entry |= bool(flags & 1 and address <= entry < address + files)
            elif kind == 0x6474e551:
                nonexecutable_stack = not flags & 1
        self.assertTrue(executable_entry)
        self.assertTrue(nonexecutable_stack)
        self.evidence.artifact(label, data)
        path = self.work / label
        path.write_bytes(data)
        path.chmod(0o755)
        self.evidence.seals[path] = fingerprint(data)
        return path


class ComponentGenerationTests(GenerationCase):
    def test_actual_sources_build_and_rebuild(self):
        self.evidence.unchanged()
        predecessors = build_predecessors(self.work / "predecessors")
        for name, path in predecessors.items():
            self.evidence.artifact("predecessor-" + name, path.read_bytes())
        self.evidence.receipt["predecessor_builder"] = "c031_support.build_predecessors"
        self.evidence.save()
        self.evidence.unchanged()
        generations = {}
        for name, source in self.sources.items():
            source_path = self.work / (name + ".nql")
            source_path.write_bytes(source)
            for repeat in (1, 2):
                label = f"A{repeat}-{name}"
                output = self.work / label
                result = self.evidence.run(label, self.binaries["b0"], args=(
                    "--compiler-profile", str(source_path), "-o", str(output)), timeout=1200)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
                generations.setdefault(f"A{repeat}", {})[name] = self.executable(label, output.read_bytes())
            self.evidence.equal("A1-A2-" + name,
                                self.evidence.read_artifact(generations["A1"][name]),
                                self.evidence.read_artifact(generations["A2"][name]))
            self.evidence.equal("selected-A1-" + name, self.binaries[name].read_bytes(),
                                generations["A1"][name].read_bytes())
        for label, parent in (("B", "A1"), ("C", "B")):
            generations[label] = {}
            for name in self.sources:
                with self.subTest(generation=label, component=name):
                    generations[label][name] = self.compile_component(
                        name, generations[parent], label + "-" + name)
            if len(generations[label]) != 2:
                self.evidence.receipt["blocker"] = dict(
                    generation=label, missing_components=sorted(set(self.sources) - set(generations[label])))
                self.evidence.save()
                self.fail(f"NEEDS_CONTEXT: generation {label} incomplete; receipts: {self.evidence.path}")
        for name in self.sources:
            self.evidence.equal("B-C-" + name, self.evidence.read_artifact(generations["B"][name]),
                                self.evidence.read_artifact(generations["C"][name]))
        for generation in ("A1", "B", "C"):
            self.corpus(generation, generations[generation])
            self.native_corpus(generation, generations[generation])
        for generation in ("B", "C"):
            with self.subTest(generation=generation, corpus="named-oracles"), self.evidence.checked(generation + "-named-oracles"):
                self.run_generation_oracles(generation, generations[generation])
        if all(check["passed"] for check in self.evidence.receipt["checks"]):
            self.evidence.unchanged()
            for artifact in self.evidence.receipt["artifacts"].values():
                self.assertEqual(fingerprint(Path(artifact["path"]).read_bytes()),
                                 {key: artifact[key] for key in ("bytes", "sha256")})
            self.evidence.receipt["component_generations_verified"] = True
            self.evidence.save()


class GenerationIntegrityTests(GenerationCase):
    def test_changed_artifact_is_rejected_before_execution(self):
        program = self.compile_component("frontend", self.binaries, "control-component")
        original = program.read_bytes()
        for name, data in (("truncated", original[:-1]),
                           ("mutated", original[:-1] + bytes([original[-1] ^ 1])),
                           ("appended", original + b"\x00")):
            with self.subTest(damage=name):
                try:
                    program.write_bytes(data)
                    with self.assertRaisesRegex(AssertionError, "artifact"):
                        self.evidence.run(name, program, encode_profile_source(b"fn main(){return 7}"))
                finally:
                    program.write_bytes(original)

    def test_comparison_retains_first_differing_offset(self):
        program = self.compile_component("frontend", self.binaries, "comparison-component")
        original = program.read_bytes()
        for label, changed, offset in (
                ("truncated", original[:-1], len(original) - 1),
                ("mutated", original[:-1] + bytes([original[-1] ^ 1]), len(original) - 1),
                ("extended", original + b"\x00", len(original))):
            with self.subTest(damage=label):
                with self.assertRaises(AssertionError):
                    self.evidence.equal(label, original, changed)
                comparison = self.evidence.receipt["comparisons"][-1]
                self.assertEqual(comparison["first_difference_offset"], offset)
                self.assertNotEqual(comparison["left"], comparison["right"])

    def test_changed_input_identity_is_rejected(self):
        path = self.work / "source-snapshot.nql"
        source = self.sources["frontend"]
        path.write_bytes(source)
        self.evidence.identities[str(path)] = fingerprint(source)
        path.write_bytes(source + b"\n")
        try:
            with self.assertRaisesRegex(AssertionError, "input identity changed"):
                self.evidence.run("changed-source", self.binaries["frontend"], source)
        finally:
            path.write_bytes(source)

    def test_gate_rejects_invalid_candidate(self):
        invalid = self.work / "missing-candidate"
        command = ["bash", str(ROOT / "tests/bootstrap/c0_capacity.sh")]
        started = time.monotonic()
        result = subprocess.run(command, cwd=self.work, capture_output=True, timeout=15,
                                env={**os.environ, "ROOT_DIR": str(ROOT), "C0_FRONTEND": str(invalid)})
        self.evidence.observed("gate-invalid-candidate", "bash", b"", result,
                               time.monotonic() - started, 15)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(invalid).encode(), result.stderr)
        self.assertNotIn(b"PASS c0-capacity", result.stdout)
        self.assertNotIn(b"PASS c0-component-generations", result.stdout)

    def test_real_nonzero_producer_output_is_rejected(self):
        source = b"fn main(){return 7}"
        wire = self.parse(source, self.binaries["frontend"], "fault-input", profile=True)
        backend = self.binaries["backend"]
        control = self.evidence.run("fault-control", backend, wire)
        self.accept_result("fault-control", control)
        image = backend.read_bytes()
        for fault, prefix in (("complete", "b80b0000004c89f7be00000001"),
                              ("partial", "4885d2741fb801000000")):
            with self.subTest(output=fault):
                pattern = bytes.fromhex(prefix)
                positions = []
                position = image.find(pattern)
                while position != -1:
                    site = position + len(pattern)
                    self.assertEqual(image[site:site + 2], b"\x0f\x05")
                    positions.append(0x400000 + site)
                    position = image.find(pattern, position + 1)
                self.assertTrue(positions)
                if fault == "complete":
                    self.assertEqual(len(positions), 1)
                address = positions[0]
                started = time.monotonic()
                with Guest(backend, wire, timeout=30) as guest:
                    for site in positions:
                        guest.bp(site)
                    if fault == "partial":
                        self.assertRegex(guest.cmd("c"), r"^(?:T05|S05)")
                        registers = guest.regs()
                        address = registers["rip"]
                        self.assertIn(address, positions)
                        for site in positions:
                            if site != address:
                                guest.bp(site, False)
                        self.assertEqual((registers["rax"], registers["rdi"]), (1, 1))
                        guest.short_write(8)
                        guest.until(address)
                        guest.inject(-5)
                        guest.bp(address, False)
                    else:
                        registers = guest.until(address)
                        self.assertEqual((registers["rax"], registers["rsi"]), (11, 16777216))
                        self.assertNotEqual(registers["rdi"], 0)
                        guest.inject(-22)
                    status, output, error = guest.finish()
                    command = guest.process.args
                self.assertTrue(guest.closed)
                self.assertEqual(guest.process.poll(), status)
                self.assertFalse(guest.socket_path.exists())
                result = subprocess.CompletedProcess(command, status, output, error)
                self.evidence.observed("fault-" + fault, backend, wire, result,
                                       time.monotonic() - started, 30)
                self.evidence.receipt.setdefault("faults", []).append(dict(
                    output=fault, method="QEMU verified syscall return injection",
                    address=address, instruction="0f05", injected_result=-5 if fault == "partial" else -22,
                    child_reaped=True, socket_removed=True))
                self.evidence.save()
                self.assertEqual(status, 74, error)
                self.assertEqual(output, control.stdout if fault == "complete" else control.stdout[:8])
                self.assertIn(b"munmap" if fault == "complete" else b"output_write", error)
                with self.assertRaises(AssertionError):
                    self.accept_result("rejected-" + fault, result)
                self.assertFalse((self.work / ("rejected-" + fault)).exists())


if __name__ == "__main__":
    unittest.main()
