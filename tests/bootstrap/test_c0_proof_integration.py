"""Bounded proof-producer controls. No compiler generation is built here."""

from contextlib import ExitStack
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

import test_c0_component_generations as generations


SELECTOR = "test_c0_never.NeverTests.test_generation_never_and_bang_contract"


class GenerationProofIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bounded-proof-")
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.pair = {name: self.work / ("B-" + name) for name in ("frontend", "backend")}
        for name, path in self.pair.items():
            path.write_bytes(("synthetic generated B " + name).encode())
        self.case = generations.GenerationCase(methodName="runTest")
        self.new_evidence("initial")
        self.runner = self.work / "oracle-boundary"
        self.runner.write_text("#!" + sys.executable + "\n" + textwrap.dedent('''
            import os, pathlib, sys
            selectors = sys.argv[sys.argv.index('-v') + 1:]
            if os.environ.get('PROOF_REQUIRE_NEVER') == '1':
                if 'test_c0_never.NeverTests.test_generation_never_and_bang_contract' not in selectors:
                    print('missing required Never selector', file=sys.stderr)
                    sys.exit(73)
            native = pathlib.Path(os.environ['C032_NATIVE_EVIDENCE_DIR'])
            native.mkdir()
            for profile in (0, 1):
                for suffix in ('json', 'nql', 'nqaf', 'elf'):
                    (native / f'mmap-profile{profile}.{suffix}').write_bytes(b'synthetic boundary artifact')
            lines = [f"{s.rsplit('.', 1)[1]} ({s}) ... ok\\n" for s in selectors]
            damage = os.environ.get('PROOF_OUTPUT_DAMAGE')
            if damage == 'summary-only': lines = []
            if damage == 'partial': lines.pop()
            if damage == 'replacement': lines[-1] = 'test_other (test_other.Other.test_other) ... ok\\n'
            if damage == 'duplicate': lines.append(lines[-1])
            sys.stderr.write(''.join(lines) + f'\\nRan {len(selectors)} tests in 1.0s\\n\\nOK\\n')
        '''))
        self.runner.chmod(0o755)

    def new_evidence(self, label):
        evidence = os.environ.get("C040_PRODUCER_EVIDENCE_DIR")
        with ExitStack() as stack:
            if evidence:
                Path(evidence).mkdir(parents=True, exist_ok=True)
                stack.enter_context(mock.patch.dict(os.environ, C031_WORK=evidence))
            self.case.evidence = generations.Evidence(self._testMethodName + "-" + label, self.pair)
        self.addCleanup(self.case.evidence.close)

    def invoke(self, *, pair=None, **environment):
        # The real subprocess boundary runs a tiny controlled program; only
        # the slow compiler/oracle subprocess is replaced, not the producer.
        with mock.patch.dict(os.environ, {"C0_FRONTEND": "A-substitute-frontend",
                                          "C0_BACKEND": "A-substitute-backend", **environment}), \
                mock.patch.object(generations.sys, "executable", str(self.runner)):
            self.case.run_generation_oracles("B", self.pair if pair is None else pair)

    def test_producer_runs_named_never_oracle_with_generated_pair(self):
        self.invoke(PROOF_REQUIRE_NEVER="1")
        receipt = self.case.evidence.receipt
        oracle = receipt["oracles"][0]
        self.assertIn(SELECTOR, oracle["selectors"])
        self.assertEqual(oracle["generation"], "B")
        for component, path in self.pair.items():
            self.assertEqual(oracle["environment"]["C0_" + component.upper()], str(path))
            self.assertEqual(oracle["components"][component], dict(path=str(path), **generations.fingerprint(path.read_bytes())))
        self.assertEqual(oracle["returncode"], 0)
        self.assertIs(receipt["component_generations_verified"], False)

    def test_producer_rejects_fakePASS_and_partial_named_results(self):
        for damage in ("summary-only", "partial", "replacement", "duplicate"):
            with self.subTest(damage=damage):
                self.new_evidence(damage)
                with self.assertRaisesRegex(AssertionError, "oracle"):
                    self.invoke(PROOF_OUTPUT_DAMAGE=damage)

    def test_producer_rejects_A_pair_under_B_generation_label(self):
        pair = {name: self.work / ("A1-" + name) for name in self.pair}
        for name, path in pair.items():
            path.write_bytes(self.pair[name].read_bytes())
        with self.assertRaisesRegex(AssertionError, "generation"):
            self.invoke(pair=pair)

    def test_producer_rejects_stale_input_identity_before_subprocess(self):
        file = self.work / "required-test.py"
        file.write_bytes(b"original\n")
        self.case.evidence.identities[str(file)] = generations.fingerprint(file.read_bytes())
        file.write_bytes(b"changed\n")
        with self.assertRaisesRegex(AssertionError, "input identity changed"):
            self.invoke()
        self.assertEqual(self.case.evidence.receipt["stages"], [])


if __name__ == "__main__":
    unittest.main()
