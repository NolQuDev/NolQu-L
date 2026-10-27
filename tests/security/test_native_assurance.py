"""Deterministic, bounded security regression; no coverage-guided fuzz claim.

Only fixed pure semantic-oracle programs are executed. Mutated source/wire is
compiled but its ELF is NEVER executed. Python and QEMU are host test tools.
Run directly; NQL_ASSURANCE_OUTPUT selects a new retained evidence directory.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import struct
import sys
import tempfile
import unittest

from bounded_runner import BoundedRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/bootstrap"))
from c031_support import assert_owned_graph, decode_nqaf, encode_profile_source

CORPUS = Path(__file__).with_name("corpus") / "native-boundary-v1.json"
MUTATION_SEED = 0x4E514C32
DIAGNOSTIC = rb"^input:[1-9][0-9]*:[1-9][0-9]*: error\[C0[PSB]-\d{3}\]: .+; .+\n$"


class NativeBoundaryAssurance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reporting defaults survive corpus/pin/platform setup failures.
        cls.runner = None
        cls.identities = {}
        cls.corpus_bytes = b""
        cls.corpus = {}
        cls.prefix = []
        cls.evidence = Path(os.environ.get("NQL_ASSURANCE_OUTPUT") or
                            (Path(tempfile.gettempdir()) / ("nql-native-assurance-" + os.urandom(8).hex())))
        cls.runner = BoundedRunner(cls.evidence, timeout=5, budget=600)
        cls.profile_counts = {"default": 0, "compiler": 0}
        cls.counts = {"seed_sources": 0, "source_mutations": 0,
                      "known_invalid_source_mutations": 0,
                      "wire_rejections": 0, "semantic_oracles": 0}
        cls.corpus_bytes = CORPUS.read_bytes()
        (cls.evidence / "corpus.json").write_bytes(cls.corpus_bytes)
        cls.corpus = json.loads(cls.corpus_bytes)
        if cls.corpus["schema"] != 1 or len(cls.corpus["seeds"]) != 12:
            raise ValueError("unexpected seed corpus schema")
        cls.frontend = ROOT / "bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed"
        cls.backend = cls.frontend.with_name("c0-backend.seed")
        cls.identities = {}
        for binary in (cls.frontend, cls.backend):
            pin_path = binary.with_suffix(".sha256")
            pin = pin_path.read_text().split()
            identity = BoundedRunner.identity(binary)
            if pin != [identity["sha256"], binary.name] or not os.access(binary, os.X_OK):
                raise ValueError(f"installed seed identity/executable mismatch: {binary.name}")
            cls.identities[str(binary.relative_to(ROOT))] = identity
            cls.identities[str(pin_path.relative_to(ROOT))] = BoundedRunner.identity(pin_path)
        for path in (ROOT / "bootstrap/compiler/c0/frontend.nql",
                     ROOT / "bootstrap/compiler/c0/backend.nql",
                     ROOT / "tests/bootstrap/c031_support.py",
                     Path(__file__), Path(__file__).with_name("bounded_runner.py"), CORPUS):
            cls.identities[str(path.relative_to(ROOT))] = BoundedRunner.identity(path)
        if platform.machine() == "x86_64":
            cls.prefix = []
        else:
            qemu = shutil.which("qemu-x86_64")
            if qemu is None:
                raise RuntimeError("x86_64 execution unavailable; no test skip")
            cls.prefix = [qemu]
            cls.identities["host_qemu"] = dict(path=qemu, **BoundedRunner.identity(qemu))

    def invoke(self, label, binary, data=b""):
        return self.runner.run(label, [*self.prefix, str(binary)], data)

    def frontend_result(self, label, source, profile):
        self.profile_counts["compiler" if profile else "default"] += 1
        result = self.invoke(label, self.frontend,
                             encode_profile_source(source) if profile else source)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        if result.returncode:
            self.assertEqual(result.stdout, b"")
            self.assertRegex(result.stderr, DIAGNOSTIC)
        else:
            self.assertEqual(result.stderr, b"")
            header, nodes = decode_nqaf(result.stdout)
            self.assertEqual(header["source"], source)
            self.assertEqual(header["runtime_profile"], int(profile))
            assert_owned_graph(header, nodes)
        return result

    def backend_result(self, label, wire, reject=False):
        result = self.invoke(label, self.backend, wire)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        if reject or result.returncode:
            self.assertEqual((result.returncode, result.stdout), (1, b""), result.stderr)
            self.assertRegex(result.stderr, DIAGNOSTIC)
            self.assertIn(b"[C0B-", result.stderr)
        else:
            self.assertEqual(result.stderr, b"")
            self.assertEqual(result.stdout[:4], b"\x7fELF")
        return result

    def test_seed_sources_and_deterministic_mutations(self):
        rng = random.Random(MUTATION_SEED)
        for seed in self.corpus["seeds"]:
            source = seed["source"].encode("utf-8")
            for profile in (False, True):
                with self.subTest(seed=seed["id"], profile=profile):
                    result = self.frontend_result(seed["id"], source, profile)
                    self.assertEqual(result.returncode, 0 if seed["accept"] else 1)
                    if "code" in seed:
                        self.assertIn(("[" + seed["code"] + "]").encode(), result.stderr)
                    if result.returncode == 0:
                        self.assertEqual(self.backend_result(seed["id"], result.stdout).returncode, 0)
                    self.counts["seed_sources"] += 1
            # Deterministic insertion, deletion and bit-flip at four seeded
            # positions per nonempty seed. No assumption every mutation is bad.
            if not source:
                continue
            positions = sorted(rng.sample(range(len(source)), min(4, len(source))))
            mutations = {}
            def add(mutant):
                mutations[mutant] = any(byte == 0 or byte >= 128 for byte in mutant)
            for position in positions:
                add(source[:position] + source[position + 1:])
                add(source[:position] + b"\xff" + source[position:])
                add(source[:position] + bytes([source[position] ^ 0x80]) + source[position + 1:])
            for number, mutant in enumerate(sorted(mutations)):
                result = self.frontend_result(f"{seed['id']}/mutation-{number}", mutant, number % 2 == 1)
                if mutations[mutant]:
                    self.assertEqual(result.returncode, 1, "forbidden source byte was accepted")
                    self.assertEqual(result.stdout, b"")
                    self.assertIn(b"[C0P-001]", result.stderr)
                    self.counts["known_invalid_source_mutations"] += 1
                if result.returncode == 0:
                    self.backend_result("accepted-source-mutation", result.stdout)
                self.counts["source_mutations"] += 1

    def test_wire_framing_reserved_fields_and_spans(self):
        source = b"fn main(){unsafe {# safety: compile only; the program owns its frame\nsyscall6(39,0)}return 0}"
        for profile in (False, True):
            parsed = self.frontend_result("wire-seed", source, profile)
            self.assertEqual(parsed.returncode, 0)
            wire = parsed.stdout
            header, nodes = decode_nqaf(wire)
            self.assertEqual(header["version"], 6)
            self.assertEqual(self.backend_result("wire-valid", wire).returncode, 0)
            record_start = 32 + len(source)
            cuts = {0, 1, 3, 4, 15, 16, 31, 32, record_start - 1,
                    record_start, len(wire) - 1}
            for index in range(len(nodes)):
                cuts.update(record_start + index * 32 + field for field in (1, 16, 31))
            mutants = {wire[:cut] for cut in cuts}
            mutants.add(wire + b"\0")
            for offset, value in ((0, 0), (4, 0), (4, 5), (4, 7), (5, 16),
                                  (6, 1), (7, 1), (24, 4), (25, 2),
                                  (26, 1), (27, 1), (28, 1), (31, 1)):
                data = bytearray(wire)
                data[offset] = value
                mutants.add(bytes(data))
            for index in range(len(nodes)):
                base = record_start + index * 32
                for field in (1, 2, 3, 24, 28):
                    data = bytearray(wire)
                    data[base + field] = 1
                    mutants.add(bytes(data))
                for field, value in ((4, len(source)), (8, 0),
                                     (12, len(nodes) + 1), (20, len(nodes) + 1)):
                    data = bytearray(wire)
                    struct.pack_into("<I", data, base + field, value)
                    mutants.add(bytes(data))
            for number, mutant in enumerate(sorted(mutants)):
                with self.subTest(profile=profile, mutation=number):
                    self.backend_result(f"wire-reject-{profile}-{number}", mutant, reject=True)
                    self.counts["wire_rejections"] += 1

    def test_safety_headers_and_scope_restoration_metamorphic(self):
        for profile in (False, True):
            for number, comment in enumerate((b"# safety: owns the frame\n",
                                              b"// safety: owns the frame\r\n",
                                              b" \t\n#\tsafety:\n// owns the frame\n",
                                              b"# safety: comment braces } { have no scope effect\n")):
                source = b"fn main(){unsafe {" + comment + b"syscall6(39,0)}return 0}"
                parsed = self.frontend_result(f"header-{number}", source, profile)
                self.assertEqual(parsed.returncode, 0)
                self.assertEqual(self.backend_result("header-valid-wire", parsed.stdout).returncode, 0)
                outside = source.replace(b"return 0}", b"return syscall6(39,0)}")
                result = self.frontend_result("scope-restored", outside, profile)
                self.assertEqual(result.returncode, 1)
                anchor = outside.rindex(b"syscall6")
                line = outside[:anchor].count(b"\n") + 1
                column = anchor - outside.rfind(b"\n", 0, anchor)
                self.assertTrue(result.stderr.startswith(
                    f"input:{line}:{column}: error[C0S-001]: ".encode()), result.stderr)

    def test_defined_pure_program_metamorphic_behavior(self):
        # Independent expected bytes/status, not candidate-vs-candidate voting.
        # Only these fixed pure programs are executed; no mutated ELF is run.
        variants = [
            b"let value=6 return value*6+6",
            b"let renamed=6 return ((renamed)*6)+6",
            b"if 0{return 99}return (6*6)+6",
            b"let value=0 while value<6{value=value+1}return value*6+6",
            b"unsafe {# safety: no raw operation or foreign pointer is used\n}return 42",
            b"return calc(6)",
        ]
        prefix = b"fn calc(value){return value*6+6}fn main(){byte_store(0,78)byte_store(1,81)byte_store(2,76)output_write(0,3)"
        for profile in (False, True):
            for number, body in enumerate(variants):
                source = prefix + body + b"}"
                parsed = self.frontend_result(f"pure-{number}", source, profile)
                self.assertEqual(parsed.returncode, 0)
                artifact = self.backend_result("pure-codegen", parsed.stdout)
                self.assertEqual(artifact.returncode, 0)
                binary = self.evidence / f"pure-{int(profile)}-{number}.elf"
                binary.write_bytes(artifact.stdout)
                binary.chmod(0o700)
                result = self.invoke("fixed-pure-runtime", binary)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (42, b"NQL", b""))
                self.counts["semantic_oracles"] += 1


def write_summary(result):
    cls = NativeBoundaryAssurance
    if getattr(cls, "runner", None) is None:
        return
    try:
        unchanged = all(BoundedRunner.identity(ROOT / name) == identity
                        for name, identity in cls.identities.items() if name != "host_qemu")
    except OSError:
        unchanged = False
    summary = dict(schema=1, scope="experimental native source/NQAF6 boundary",
                   passed=result.wasSuccessful() and unchanged,
                   tests_run=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), skipped=len(result.skipped),
                   host=platform.machine(), target="x86_64-linux",
                   execution_adapter=cls.prefix, python=sys.version,
                   corpus_sha256=hashlib.sha256(cls.corpus_bytes).hexdigest(),
                   mutation_seed=MUTATION_SEED, counts=cls.counts,
                   profiles=cls.profile_counts, inputs=cls.identities,
                   inputs_unchanged=unchanged, limits=cls.runner.limits,
                   invocations=len(cls.runner.records),
                   timeouts=sum(r["timed_out"] for r in cls.runner.records),
                   signals=sum(isinstance(r["exit_code"], int) and r["exit_code"] < 0 for r in cls.runner.records),
                   supervisor_failures=sum(r.get("supervisor_ok") is False for r in cls.runner.records),
                   coverage_guided=False, instrumentation="not available for NolQu-L",
                   limitations=["no coverage percentage", "no RSS cap", "no allocation fault injection",
                                "no optimizer comparison", "no arbitrary mutant ELF execution"])
    (cls.evidence / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"ASSURANCE_EVIDENCE={cls.evidence}", file=sys.stderr)
    if not unchanged:
        raise RuntimeError("compiler input changed during assurance run")


if __name__ == "__main__":
    program = unittest.main(exit=False)
    write_summary(program.result)
    raise SystemExit(not program.result.wasSuccessful())
