"""Bounded defined-program differential testing; Python is a host oracle only."""
from pathlib import Path
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from differential_oracle import (I64_MIN, I64_MAX, OPERATORS, corpus,
                                 evaluate, signature)
from bounded_runner import BoundedRunner

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/bootstrap'))
from c031_support import assert_owned_graph, decode_nqaf, encode_profile_source


class DifferentialMismatch(AssertionError):
    """A completed defined program disagrees with the independent oracle."""


class GateResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successful_test_ids = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successful_test_ids.append(test.id())


def compare(result, case):
    actual = result.returncode, result.stdout, result.stderr
    expected = case.expected_exit, case.expected_stdout, b''
    if actual != expected:
        raise DifferentialMismatch(
            f'{case.identifier}: expected exit/stdout/stderr {expected!r}, got {actual!r}')


class OracleControls(unittest.TestCase):
    def test_signed_division_and_comparisons_match_specification(self):
        for left, right, expected in ((7, 3, 2), (-7, 3, -2),
                                      (7, -3, -2), (-7, -3, 2),
                                      (I64_MIN, 1, I64_MIN)):
            with self.subTest(left=left, right=right):
                self.assertEqual(evaluate(('/', left, right), {}), expected)
        for operation, expected in (('<', 1), ('<=', 1), ('>', 0),
                                    ('>=', 0), ('==', 0), ('!=', 1)):
            self.assertEqual(evaluate((operation, -2, 1), {}), expected)
        for expression in (('+', I64_MAX, 1), ('-', I64_MIN, 1),
                           ('*', I64_MAX, 2), ('/', I64_MIN, -1)):
            with self.assertRaises(OverflowError):
                evaluate(expression, {})
        with self.assertRaises(ZeroDivisionError):
            evaluate(('/', 1, 0), {})

    def test_full_width_signature_distinguishes_high_bits_and_sign(self):
        self.assertEqual(signature(I64_MAX), b'\0' + b'\xff' * 7 + b'\x7f')
        self.assertEqual(signature(I64_MIN), b'\1' + b'\0' * 7 + b'\x80')
        self.assertEqual(signature(-257), b'\1\xff\xff' + b'\0' * 6)
        for a, b in ((0, 256), (1, 257), (-1, -257), (1, -255),
                     (I64_MAX, I64_MIN)):
            self.assertNotEqual(signature(a), signature(b))

    def test_corpus_is_reproducible_bounded_and_covers_every_operator(self):
        cases = corpus()
        self.assertEqual(cases, corpus())
        self.assertEqual(len(cases), 48)
        self.assertEqual(len({case.identifier for case in cases}), 48)
        self.assertEqual({case.model['operator'] for case in cases[:40]}, set(OPERATORS))
        for case in cases:
            self.assertLess(len(case.source), 8192)
            self.assertLessEqual(case.model['trace_bytes'], 48)
            self.assertEqual(case.expected_stdout[-case.model['trace_bytes'] - 1],
                             case.model['trace_bytes'])
            self.assertGreaterEqual(case.expected_exit, 0)
            self.assertLessEqual(case.expected_exit, 255)

    def test_edge_models_really_return_exact_i64_endpoints(self):
        cases = corpus()
        self.assertEqual(cases[40].model['results'][0], I64_MIN)
        self.assertEqual(cases[42].model['results'][0], I64_MAX)


class CompilerDifferentialTests(unittest.TestCase):
    runner = None
    identities = {}
    prefix = []
    matched = {'default': 0, 'compiler': 0}
    sensitivity_rejections = []
    cases = ()
    corpus_bytes = b''

    @classmethod
    def setUpClass(cls):
        cls.prefix = []
        cls.identities = {}
        cls.matched = {'default': 0, 'compiler': 0}
        cls.sensitivity_rejections = []
        cls.evidence = Path(os.environ.get('NQL_DIFFERENTIAL_OUTPUT') or
                            (Path(tempfile.gettempdir()) / ('nql-differential-' + os.urandom(8).hex())))
        cls.evidence.mkdir(mode=0o700)
        cls.runner = BoundedRunner(cls.evidence / 'calls', timeout=5, budget=600)
        cls.cases = corpus()
        manifest = []
        for case in cls.cases:
            source = cls.evidence / (case.identifier + '.nql')
            source.write_bytes(case.source)
            manifest.append(dict(id=case.identifier, model=case.model,
                                 source_sha256=hashlib.sha256(case.source).hexdigest(),
                                 expected_exit=case.expected_exit,
                                 expected_stdout_hex=case.expected_stdout.hex()))
        cls.corpus_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
        (cls.evidence / 'corpus.json').write_bytes(cls.corpus_bytes)
        cls.frontend = ROOT / 'bootstrap/compiler/c0/x86_64-linux/c0-frontend.seed'
        cls.backend = cls.frontend.with_name('c0-backend.seed')
        paths = [Path(__file__), Path(__file__).with_name('differential_oracle.py'),
                 Path(__file__).with_name('bounded_runner.py'),
                 ROOT / 'tests/bootstrap/c031_support.py',
                 ROOT / 'bootstrap/compiler/c0/frontend.nql',
                 ROOT / 'bootstrap/compiler/c0/backend.nql']
        for binary in (cls.frontend, cls.backend):
            identity = BoundedRunner.identity(binary)
            pin = binary.with_suffix('.sha256')
            if pin.read_text().split() != [identity['sha256'], binary.name] or not os.access(binary, os.X_OK):
                raise ValueError('installed seed pin/executable mismatch: ' + binary.name)
            paths.extend((binary, pin))
        cls.identities = {str(path): BoundedRunner.identity(path) for path in paths}
        if platform.machine() != 'x86_64':
            adapter = shutil.which('qemu-x86_64')
            if adapter is None:
                raise RuntimeError('x86_64 execution adapter unavailable; no test skip')
            cls.prefix = [adapter]
            cls.identities[adapter] = BoundedRunner.identity(adapter)

    def invoke(self, label, binary, data=b''):
        return self.runner.run(label, [*self.prefix, str(binary)], data)

    def compiled_result(self, label, source, profile):
        payload = encode_profile_source(source) if profile else source
        parsed = self.invoke(label + '/frontend', self.frontend, payload)
        self.assertEqual((parsed.returncode, parsed.stderr), (0, b''), label)
        header, nodes = decode_nqaf(parsed.stdout)
        self.assertEqual((header['source'], header['runtime_profile']), (source, int(profile)))
        assert_owned_graph(header, nodes)
        emitted = self.invoke(label + '/backend', self.backend, parsed.stdout)
        self.assertEqual((emitted.returncode, emitted.stderr), (0, b''), label)
        self.assertEqual(emitted.stdout[:4], b'\x7fELF')
        binary = self.evidence / (label.replace('/', '-') + '.elf')
        binary.write_bytes(emitted.stdout)
        binary.chmod(0o700)
        return self.invoke(label + '/execute', binary)

    def test_defined_programs_against_independent_oracle(self):
        for profile in (False, True):
            name = 'compiler' if profile else 'default'
            for case in self.cases:
                with self.subTest(profile=name, case=case.identifier):
                    result = self.compiled_result(name + '/' + case.identifier, case.source, profile)
                    compare(result, case)
                    self.matched[name] += 1

    def test_real_wrong_status_and_wrong_stream_are_detected(self):
        # These are intentional sensitivity controls, not reported compiler bugs.
        # Alter only valid source; never run a mutated executable or raw syscall.
        case = self.cases[0]
        variants = {
            'wrong-exit': case.source.replace(b'return value\n', b'return value+1\n'),
            'wrong-stream': case.source.replace(b'output_write(0,byte_load(0)+1)',
                                                b'output_write(1,byte_load(0))'),
        }
        for label, source in variants.items():
            with self.subTest(control=label):
                self.assertNotEqual(source, case.source)
                result = self.compiled_result(label, source, False)
                # A compile failure, signal, timeout, supervisor failure or bad
                # stderr cannot satisfy this expected-behavior mismatch control.
                self.assertEqual(result.stderr, b'')
                self.assertIn(result.returncode, range(256))
                if label == 'wrong-exit':
                    self.assertEqual(result.stdout, case.expected_stdout)
                    self.assertNotEqual(result.returncode, case.expected_exit)
                else:
                    self.assertEqual(result.returncode, case.expected_exit)
                    self.assertEqual(len(result.stdout), len(case.expected_stdout) - 1)
                with self.assertRaises(DifferentialMismatch):
                    compare(result, case)
                self.sensitivity_rejections.append(label)


class GateSummaryControls(unittest.TestCase):
    def test_partial_successful_suite_cannot_publish_pass(self):
        # Exercise the real summary writer after a real selected host unittest.
        # Completed compiler counters are fixture state, not executed evidence.
        selected = unittest.TestSuite([
            OracleControls('test_signed_division_and_comparisons_match_specification')])
        result = selected.run(unittest.TestResult())
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(result.testsRun, 1)
        with tempfile.TemporaryDirectory(prefix='differential-summary-control-') as directory:
            state = dict(runner=SimpleNamespace(records=[], limits={}),
                         evidence=Path(directory), identities={}, prefix=[],
                         cases=corpus(), corpus_bytes=b'controlled fixture',
                         matched={'default': 48, 'compiler': 48},
                         sensitivity_rejections=['wrong-exit', 'wrong-stream'])
            with patch.multiple(CompilerDifferentialTests, create=True, **state):
                with self.assertRaisesRegex(RuntimeError, 'full differential suite'):
                    write_summary(result)
                summary = json.loads((Path(directory) / 'summary.json').read_text())
                self.assertFalse(summary['passed'])


def write_summary(result):
    cls = CompilerDifferentialTests
    if cls.runner is None:
        return
    try:
        unchanged = all(BoundedRunner.identity(Path(path)) == identity
                        for path, identity in cls.identities.items())
    except OSError:
        unchanged = False
    required_ids = {f'{case.__module__}.{case.__qualname__}.{name}'
                    for case in (OracleControls, CompilerDifferentialTests, GateSummaryControls)
                    for name in unittest.defaultTestLoader.getTestCaseNames(case)}
    successful_ids = getattr(result, 'successful_test_ids', [])
    suite_complete = (set(successful_ids) == required_ids
                      and len(successful_ids) == len(required_ids) == result.testsRun
                      and not result.skipped)
    complete = (suite_complete and cls.matched == {'default': 48, 'compiler': 48}
                and cls.sensitivity_rejections == ['wrong-exit', 'wrong-stream'])
    passed = result.wasSuccessful() and unchanged and complete
    summary = dict(schema=1, passed=passed, status='PASSED' if passed else 'FAILED',
                   scope='finite defined C0 scalar/call/control/byte-effect programs',
                   tests_run=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), skipped=len(result.skipped),
                   target='x86_64-linux', host=platform.machine(), python=sys.version,
                   execution_adapter=cls.prefix, identities=cls.identities,
                   inputs_unchanged=unchanged,
                   corpus_complete=complete, host_system=sys.platform,
                   required_test_ids=sorted(required_ids),
                   successful_test_ids=successful_ids, suite_complete=suite_complete,
                   corpus_sha256=hashlib.sha256(cls.corpus_bytes).hexdigest(),
                   defined_cases=len(cls.cases), matched_profiles=cls.matched,
                   sensitivity_rejections=cls.sensitivity_rejections,
                   invocations=len(cls.runner.records), limits=cls.runner.limits,
                   coverage_guided=False, rss_cap=False,
                   limitations=['finite corpus; no coverage percentage',
                                'no arbitrary source/wire/ELF mutation execution',
                                'no optimizer differential or alternate ISA',
                                'not Full Compiler or full NolQu-L Safety qualification'])
    (cls.evidence / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('DIFFERENTIAL_EVIDENCE=' + str(cls.evidence), file=sys.stderr)
    if not unchanged:
        raise RuntimeError('differential inputs changed during execution')
    if result.wasSuccessful() and not complete:
        raise RuntimeError('full differential suite or corpus was not executed')


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2, resultclass=GateResult)
    program = unittest.main(testRunner=runner, exit=False)
    write_summary(program.result)
    raise SystemExit(not program.result.wasSuccessful())
