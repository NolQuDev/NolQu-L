"""Alpha publication controls; no network or release mutation in tests."""
import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '.github/scripts/alpha_release.py'


class AlphaReleaseTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'Alpha release publisher is not implemented')
        spec = importlib.util.spec_from_file_location('alpha_release_control', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def qualification(self):
        gates = ('main', 'mcp', 'release-controls')
        identity = {'VERSION': {'bytes': 13, 'sha256': 'a' * 64}}
        report = dict(passed=True, status='PASSED', canonical_inputs_unchanged=True,
                      context={'revision': 'b' * 40, 'canonical_inputs': identity},
                      gates=[dict(label=g, passed=True, exit_code=0,
                                  invocation=dict(supervisor_ok=True, timed_out=False,
                                                  cancelled=False)) for g in gates])
        return report, gates, identity

    def test_version_and_release_context_are_alpha_only(self):
        m = self.module()
        self.assertEqual(m.release_tag('1.0.0-alpha.1', 'dev'), 'v1.0.0-alpha.1')
        for version, channel in [('1.0.0', 'stable'), ('1.0.0-rc.1', 'dev'),
                                 ('1.0.0-alpha.1', 'stable'), ('1.0.0-alpha.0', 'dev'),
                                 ('1.0.0-alpha.1\nother', 'dev')]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                m.release_tag(version, channel)
        environment = dict(GITHUB_REPOSITORY='NolQuDev/NolQu-L', GITHUB_SHA='b' * 40,
                           GITHUB_REF='refs/heads/release/v1.0.0-alpha.1',
                           GITHUB_EVENT_NAME='push')
        m.validate_context(environment, 'v1.0.0-alpha.1', 'b' * 40)
        for key, value in [('GITHUB_REPOSITORY', 'someone/fork'),
                           ('GITHUB_SHA', 'c' * 40), ('GITHUB_REF', 'refs/heads/Main'),
                           ('GITHUB_EVENT_NAME', 'pull_request')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_context({**environment, key: value}, 'v1.0.0-alpha.1', 'b' * 40)

    def test_qualification_rejects_missing_failed_or_different_source(self):
        m = self.module()
        report, gates, identity = self.qualification()
        m.validate_qualification(report, 'b' * 40, gates, identity)
        variants = []
        for key, value in [('passed', False), ('status', 'RUNNING'),
                           ('canonical_inputs_unchanged', False)]:
            variants.append({**report, key: value})
        for field, value in [('supervisor_ok', False), ('timed_out', True), ('cancelled', True)]:
            changed = copy.deepcopy(report)
            changed['gates'][0]['invocation'][field] = value
            variants.append(changed)
        variants.append({**report, 'gates': report['gates'][:-1]})
        variants.append({**report, 'gates': report['gates'] + [report['gates'][0]]})
        changed = copy.deepcopy(report)
        changed['context']['revision'] = 'c' * 40
        variants.append(changed)
        changed = copy.deepcopy(report)
        changed['context']['canonical_inputs']['VERSION']['sha256'] = '0' * 64
        variants.append(changed)
        for changed in variants:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                m.validate_qualification(changed, 'b' * 40, gates, identity)

    def test_latest_failed_or_running_branch_run_cannot_reuse_old_success(self):
        m = self.module()
        good = dict(id=1, head_sha='b' * 40, head_branch='Main', event='push',
                    status='completed', conclusion='success')
        self.assertEqual(m.qualified_run([good], 'Main', 'b' * 40)['id'], 1)
        for state, conclusion in [('in_progress', None), ('completed', 'failure')]:
            with self.subTest(state=state), self.assertRaises(ValueError):
                m.qualified_run([good, {**good, 'id': 2, 'status': state,
                                      'conclusion': conclusion}], 'Main', 'b' * 40)
        with self.assertRaises(ValueError):
            m.qualified_run([{**good, 'head_sha': 'c' * 40}], 'Main', 'b' * 40)

    def test_receipt_from_another_workflow_run_cannot_qualify_release(self):
        m = self.module()
        pipeline = m.load('release_origin_control', ROOT / '.github/scripts/linux_qualification.py')
        archives = {}
        for number, branch in enumerate(('Main', 'Dev'), 1):
            report = dict(passed=True, status='PASSED', canonical_inputs_unchanged=True,
                context=dict(revision='b' * 40, canonical_inputs=pipeline.identities(),
                             run_id='999', run_attempt='1', branch_policy=dict(branch=branch)),
                gates=[dict(label=name, passed=True, exit_code=0,
                            invocation=dict(supervisor_ok=True, timed_out=False, cancelled=False))
                       for name, _ in pipeline.GATES])
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as stream:
                stream.writestr('nolqu-l-qualification/result.json', json.dumps(report))
            archives[number] = output.getvalue()

        class API:
            def request(self, method, route):
                if '/workflows/' in route:
                    return dict(workflow_runs=[dict(id=n, run_attempt=1, head_sha='b' * 40,
                        head_branch=branch, event='push', status='completed', conclusion='success',
                        html_url='https://example.invalid/run/' + str(n))
                        for n, branch in enumerate(('Main', 'Dev'), 1)])
                if route.endswith('/zip'):
                    return archives[int(route.split('/')[-2])]
                number = int(route.split('/runs/')[1].split('/')[0])
                return dict(artifacts=[dict(id=number, name='nolqu-l-linux-' + str(number) + '-1',
                    expired=False, digest='sha256:' + m.sha256(archives[number]))])

        with self.assertRaisesRegex(ValueError, 'origin'):
            m.qualification_receipts(API(), 'b' * 40)

    def test_published_or_mismatched_draft_and_assets_are_immutable(self):
        m = self.module()
        expected = {'source.tar.gz': b'actual source'}
        asset = dict(name='source.tar.gz', state='uploaded', size=13,
                     digest='sha256:' + m.sha256(expected['source.tar.gz']))
        self.assertEqual(m.checked_assets([asset], expected), {'source.tar.gz'})
        for change in [dict(size=0), dict(digest='sha256:' + '0' * 64),
                       dict(state='starter'), dict(name='unknown')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.checked_assets([{**asset, **change}], expected)
        with self.assertRaises(ValueError):
            m.checked_assets([asset, asset], expected)
        draft = dict(draft=True, target_commitish='b' * 40, tag_name='v1.0.0-alpha.1',
                     prerelease=True, body='reviewed notes')
        m.validate_draft(draft, 'v1.0.0-alpha.1', 'b' * 40, 'reviewed notes')
        for changed in [dict(draft=False), dict(target_commitish='c' * 40),
                        dict(body='changed notes'), dict(prerelease=False)]:
            with self.subTest(change=changed), self.assertRaises(ValueError):
                m.validate_draft({**draft, **changed}, 'v1.0.0-alpha.1', 'b' * 40, 'reviewed notes')

    def test_archive_is_deterministic_and_preserves_only_committed_bytes(self):
        m = self.module()
        with tempfile.TemporaryDirectory(prefix='nql-release-control-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'public.txt').write_bytes(b'committed bytes\n')
            subprocess.run(['git', '-C', str(root), 'add', 'public.txt'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Release Control',
                            '-c', 'user.email=release-control@example.invalid',
                            'commit', '-qm', 'fixture'], check=True)
            (root / 'public.txt').write_bytes(b'uncommitted replacement')
            (root / 'AGENTS.md').write_bytes(b'private local text')
            archive = m.source_archive(root, 'HEAD', 'nolqu-l-test')
            self.assertEqual(archive, m.source_archive(root, 'HEAD', 'nolqu-l-test'))
            with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as stream:
                self.assertEqual(stream.extractfile('nolqu-l-test/public.txt').read(), b'committed bytes\n')
                self.assertNotIn('nolqu-l-test/AGENTS.md', stream.getnames())
            subprocess.run(['git', '-C', str(root), 'add', '-f', 'AGENTS.md'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Release Control',
                            '-c', 'user.email=release-control@example.invalid',
                            'commit', '-qm', 'forbidden fixture'], check=True)
            with self.assertRaisesRegex(ValueError, 'private'):
                m.source_archive(root, 'HEAD', 'nolqu-l-test')

    def test_archive_rejects_symlink_escape(self):
        m = self.module()
        with tempfile.TemporaryDirectory(prefix='nql-release-link-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'escape').symlink_to('../../private')
            subprocess.run(['git', '-C', str(root), 'add', 'escape'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Release Control',
                            '-c', 'user.email=release-control@example.invalid',
                            'commit', '-qm', 'escape fixture'], check=True)
            with self.assertRaisesRegex(ValueError, 'escape'):
                m.source_archive(root, 'HEAD', 'nolqu-l-test')

    def test_offline_bundle_archive_has_real_pins_and_repeats_exactly(self):
        m = self.module()
        first = m.bundle_archive(ROOT, 'nolqu-l-test')
        self.assertEqual(first, m.bundle_archive(ROOT, 'nolqu-l-test'))
        with tarfile.open(fileobj=io.BytesIO(first), mode='r:gz') as stream:
            manifest = json.load(stream.extractfile('nolqu-l-test/manifest.json'))
            self.assertEqual(manifest['schema'], 'NQL-ANDROID-SMOKE/2')
            for name, identity in manifest['files'].items():
                data = stream.extractfile('nolqu-l-test/' + name).read()
                self.assertEqual(m.sha256(data), identity['sha256'])
            self.assertIn('nolqu-l-test/LICENSE', stream.getnames())

    def publication_fixture(self, directory):
        root = Path(directory) / 'source'
        root.mkdir()
        names = ['VERSION', 'CHANNEL', 'LICENSE', 'tools/nql_android_smoke.py',
                 'tools/check_publication.py', 'tests/security/bounded_runner.py',
                 'tests/security/differential_oracle.py', 'examples/canonical/native_cat.nql',
                 'docs/releases/1.0.0-alpha.1.md']
        for role in ('b0', 'c0-frontend', 'c0-backend'):
            base = 'b0' if role == 'b0' else 'c0'
            names.extend('bootstrap/compiler/' + base + '/x86_64-linux/' + role + suffix
                         for suffix in ('.seed', '.sha256'))
        for name in names:
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / name).read_bytes())
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(root), '-c', 'user.name=Release Control',
                        '-c', 'user.email=release-control@example.invalid',
                        'commit', '-qm', 'public release fixture'], check=True)
        revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD']).decode().strip()
        runner = Path(directory) / 'runner'
        runner.mkdir()
        environment = dict(GITHUB_REPOSITORY='NolQuDev/NolQu-L', GITHUB_SHA=revision,
            GITHUB_REF='refs/heads/release/v1.0.0-alpha.1', GITHUB_EVENT_NAME='push',
            GITHUB_TOKEN='explicit-test-fixture', RUNNER_TEMP=str(runner))
        return root, revision, environment

    def simulate_publication(self, directory, *, bad_asset=False, wrong_head=False):
        m = self.module()
        root, revision, environment = self.publication_fixture(directory)
        receipts = {branch: dict(run_id=index, run_attempt=1,
                     url='https://github.com/NolQuDev/NolQu-L/actions/runs/' + str(index))
                    for index, branch in enumerate(('Main', 'Dev'), 1)}

        class API:
            def __init__(self):
                self.release = None
                self.assets = []
                self.published = False
                self.mutations = []

            def request(self, method, route, payload=None, **options):
                suffix = route.split('/NolQu-L/', 1)[1]
                if method != 'GET':
                    self.mutations.append((method, suffix, payload))
                if suffix.startswith('git/ref/heads/'):
                    branch = suffix.rsplit('/', 1)[1]
                    sha = 'c' * 40 if branch == 'Stable' or wrong_head else revision
                    return dict(object=dict(type='commit', sha=sha))
                if suffix.startswith('git/ref/tags/'):
                    return dict(object=dict(type='commit', sha=revision)) if self.published else None
                if suffix.startswith('releases/tags/'):
                    return self.release
                if suffix == 'releases?per_page=100':
                    return [] if self.release is None else [self.release]
                if method == 'POST' and suffix == 'releases':
                    self.release = dict(payload, id=123, html_url='https://example.invalid/fixture-release')
                    return self.release
                if method == 'GET' and suffix.endswith('/assets?per_page=100'):
                    return self.assets
                if method == 'POST' and '/assets?name=' in suffix:
                    name = suffix.split('name=', 1)[1]
                    asset = dict(name=name, state='uploaded', size=len(payload),
                                 digest='sha256:' + ('0' * 64 if bad_asset else m.sha256(payload)))
                    self.assets.append(asset)
                    return asset
                if suffix.startswith('actions/workflows/'):
                    return dict(workflow_runs=[dict(id=index, run_attempt=1, head_sha=revision,
                        head_branch=branch, event='push', status='completed', conclusion='success')
                        for index, branch in enumerate(('Main', 'Dev'), 1)])
                if method == 'PATCH':
                    self.release.update(payload)
                    self.published = not self.release['draft']
                    return self.release
                raise AssertionError('unexpected fixture API route: ' + method + ' ' + suffix)

        api = API()
        with mock.patch.object(m, 'ROOT', root), mock.patch.object(m, 'GitHub', return_value=api), \
                mock.patch.object(m, 'qualification_receipts', return_value=(receipts, {})), \
                mock.patch.dict(m.os.environ, environment), redirect_stdout(io.StringIO()):
            try:
                result = m.main()
                error = None
            except ValueError as failure:
                result, error = None, failure
        return api, result, error, Path(environment['RUNNER_TEMP'])

    def test_publication_packages_uploads_verifies_then_exposes_prerelease(self):
        with tempfile.TemporaryDirectory(prefix='nql-release-flow-') as directory:
            api, result, error, output = self.simulate_publication(directory)
            self.assertIsNone(error)
            self.assertEqual(result, 0)
            self.assertTrue(api.published)
            self.assertTrue(api.release['prerelease'])
            self.assertEqual(api.release['make_latest'], 'false')
            receipt = json.loads((output / 'nolqu-l-alpha-assets/PUBLICATION.json').read_text())
            self.assertEqual(len(receipt['assets']), 5)
            self.assertEqual(api.mutations[0][0:2], ('POST', 'releases'))
            self.assertTrue(api.mutations[0][2]['draft'])
            self.assertEqual(api.mutations[-1][0], 'PATCH')
            self.assertFalse(api.mutations[-1][2]['draft'])

    def test_wrong_branch_head_stops_before_release_mutation(self):
        with tempfile.TemporaryDirectory(prefix='nql-release-ref-') as directory:
            api, result, error, _ = self.simulate_publication(directory, wrong_head=True)
            self.assertIsNone(result)
            self.assertIn('Main and Dev', str(error))
            self.assertFalse(api.mutations)
            self.assertFalse(api.published)

    def test_wrong_uploaded_digest_retains_draft_without_public_promotion(self):
        with tempfile.TemporaryDirectory(prefix='nql-release-digest-') as directory:
            api, result, error, output = self.simulate_publication(directory, bad_asset=True)
            self.assertIsNone(result)
            self.assertIn('asset does not match', str(error))
            self.assertFalse(api.published)
            self.assertTrue(api.release['draft'])
            self.assertFalse(any(method == 'PATCH' for method, _, _ in api.mutations))
            self.assertTrue((output / 'nolqu-l-alpha-assets/SHA256SUMS').is_file())

    def test_workflow_has_scoped_publication_permissions_and_no_pr_trigger(self):
        path = ROOT / '.github/workflows/alpha-release.yml'
        self.assertTrue(path.is_file(), 'Alpha release workflow is not implemented')
        import yaml
        workflow = yaml.safe_load(path.read_text())
        self.assertEqual(set(workflow['on']), {'push', 'workflow_dispatch'})
        self.assertEqual(workflow['on']['push']['branches'], ['release/**'])
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        job = workflow['jobs']['publish-alpha']
        self.assertEqual(job['permissions'], {'contents': 'write', 'actions': 'read'})
        checkout = next(step for step in job['steps'] if 'checkout@' in step.get('uses', ''))
        self.assertRegex(checkout['uses'], r'@[0-9a-f]{40}$')
        self.assertFalse(checkout['with']['persist-credentials'])
        token_steps = [step for step in job['steps'] if 'GITHUB_TOKEN' in step.get('env', {})]
        self.assertEqual(len(token_steps), 1)
        self.assertIn('alpha_release.py', token_steps[0]['run'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
