"""Controls for the maintainer-authorized, one-time branch/asset migration."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]


class MaintenanceTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('repository_maintenance', ROOT / '.github/scripts/repository_maintenance_20261101.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_only_official_testing_push_by_maintainer_is_authorized(self):
        m = self.module()
        env = dict(GITHUB_REPOSITORY='NolQuDev/NolQu-L', GITHUB_REF='refs/heads/Testing',
                   GITHUB_EVENT_NAME='push', GITHUB_ACTOR='NolQuDev', GITHUB_SHA='a' * 40)
        m.validate_context(env, 'a' * 40, m.BASE)
        for key, value in [('GITHUB_REPOSITORY', 'other/fork'), ('GITHUB_REF', 'refs/heads/Main'),
                           ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_ACTOR', 'someone'),
                           ('GITHUB_SHA', 'b' * 40)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_context({**env, key: value}, 'a' * 40, m.BASE)
        with self.assertRaises(ValueError):
            m.validate_context(env, 'a' * 40, 'b' * 40)

    def test_only_expected_ancestor_heads_can_be_removed(self):
        m = self.module()
        name, expected = next(iter(m.OLD_HEADS.items()))
        good = dict(status='ahead', behind_by=0, merge_base_commit=dict(sha=expected))
        m.validate_old_head(name, expected, good)
        for observed, compare in [('b' * 40, good), (expected, {**good, 'behind_by': 1}),
                                  (expected, {**good, 'merge_base_commit': dict(sha='c' * 40)})]:
            with self.subTest(observed=observed), self.assertRaises(ValueError):
                m.validate_old_head(name, observed, compare)
        with self.assertRaises(ValueError):
            m.validate_old_head('Main', expected, good)
        m.validate_old_head(name, None, None)  # already absent is idempotent

    def test_preflight_performs_no_mutation_when_any_ref_changed(self):
        m = self.module()
        class API:
            def request(self, method, route, *args, **kwargs):
                if method != 'GET':
                    raise AssertionError('preflight mutated repository')
                if route.endswith('/Testing'):
                    return dict(object=dict(type='commit', sha='a' * 40))
                if '/git/ref/heads/' in route:
                    return dict(object=dict(type='commit', sha='f' * 40))
                raise AssertionError(route)
        with self.assertRaises(ValueError):
            m.preflight(API(), 'a' * 40)

    def test_existing_asset_mismatch_never_overwrites_or_deletes(self):
        m = self.module()
        class API:
            def request(self, method, route, *args, **kwargs):
                if method != 'GET':
                    raise AssertionError('existing bytes overwritten')
                return [dict(name='new.zip', state='uploaded', size=1, digest='sha256:'+'0'*64)]
        with self.assertRaises(ValueError):
            m.ensure_asset(API(), 'new.zip', b'actual', 'Readable name')

    def test_frozen_release_assets_and_heads_are_specific(self):
        m = self.module()
        self.assertEqual(len(m.OLD_HEADS), 11)
        self.assertTrue(all(n.startswith(('ci/', 'release/')) for n in m.OLD_HEADS))
        self.assertEqual(m.TAG, 'v1.0.0-alpha.1')
        self.assertEqual(len(m.ORIGINAL_ASSETS), 5)
        self.assertEqual(m.RELEASE_REVISION, '26ad9b80b5a3164a20854ce3e3798642fba3f15e')

    def test_workflow_is_scoped_pinned_and_does_not_publish_a_new_version(self):
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/repository-maintenance-20261101.yml').read_text())
        self.assertEqual(set(workflow['on']), {'push'})
        self.assertEqual(workflow['on']['push']['branches'], ['Testing'])
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        job = workflow['jobs']['maintain']
        self.assertEqual(job['permissions'], {'contents': 'write', 'actions': 'read'})
        self.assertIn("github.actor == 'NolQuDev'", job['if'])
        for step in job['steps']:
            if 'uses' in step:
                self.assertRegex(step['uses'], r'@[0-9a-f]{40}$')
            if 'checkout@' in step.get('uses', ''):
                self.assertFalse(step['with']['persist-credentials'])
        self.assertEqual(sum('GITHUB_TOKEN' in s.get('env', {}) for s in job['steps']), 1)

    def run_migration(self, *, change_old_head=False):
        m = self.module()
        source = io.BytesIO()
        with tarfile.open(fileobj=source, mode='w:gz') as archive:
            item = tarfile.TarInfo('original/source.nql')
            item.size = 4
            archive.addfile(item, io.BytesIO(b'NQL!'))
        payloads = {i: (source.getvalue() if name.endswith('source.tar.gz') else b'original-' + name.encode())
                    for i, name in enumerate(m.ORIGINAL_ASSETS, 1)}
        originals = {name: dict(id=i, size=len(payloads[i]), digest='sha256:' + m.publisher.sha256(payloads[i]))
                     for i, name in enumerate(m.ORIGINAL_ASSETS, 1)}

        class API:
            def __init__(self):
                self.heads = {**m.KEEP_HEADS, **m.OLD_HEADS, 'Testing': 'a' * 40}
                self.assets = [dict(name=name, state='uploaded', **identity) for name, identity in originals.items()]
                self.release = dict(tag_name=m.TAG, draft=False, prerelease=True, body='Original notes')
                self.calls = []
                self.old_reads = {}

            def request(self, method, path, data=None, **kwargs):
                suffix = path.split('/NolQu-L/', 1)[1]
                self.calls.append((method, suffix))
                if suffix.startswith('actions/workflows/'):
                    return dict(workflow_runs=[dict(id=1, event='push', head_branch='Testing',
                        head_sha='a' * 40, status='completed', conclusion='success', html_url='qualified-fixture')])
                if suffix.startswith('git/ref/heads/'):
                    name = unquote(suffix.split('heads/', 1)[1])
                    if name not in self.heads:
                        return None
                    if name in m.OLD_HEADS:
                        self.old_reads[name] = self.old_reads.get(name, 0) + 1
                        if change_old_head and self.old_reads[name] > 1:
                            return dict(object=dict(type='commit', sha='f' * 40))
                    return dict(object=dict(type='commit', sha=self.heads[name]))
                if suffix.startswith('git/ref/tags/'):
                    return dict(object=dict(type='commit', sha=m.RELEASE_REVISION))
                if suffix.startswith('compare/'):
                    base = suffix.split('/', 1)[1].split('...')[0]
                    return dict(status='ahead', behind_by=0, merge_base_commit=dict(sha=base))
                if suffix.startswith('git/refs/heads/') and method == 'DELETE':
                    del self.heads[unquote(suffix.split('heads/', 1)[1])]
                    return None
                if suffix.startswith('releases/assets/'):
                    return payloads[int(suffix.rsplit('/', 1)[1])]
                if '/assets?' in suffix:
                    if method == 'GET':
                        return self.assets
                    query = parse_qs(urlsplit(suffix).query)
                    number = max(payloads) + 1
                    payloads[number] = data
                    asset = dict(id=number, name=query['name'][0], label=query['label'][0], state='uploaded',
                        size=len(data), digest='sha256:' + m.publisher.sha256(data), browser_download_url='https://example.invalid/asset/' + str(number))
                    self.assets.append(asset)
                    return asset
                if suffix == 'releases/' + str(m.RELEASE_ID):
                    if method == 'PATCH':
                        self.release.update(data)
                    return self.release
                raise AssertionError((method, suffix))

        api = API()
        env = dict(GITHUB_REPOSITORY='NolQuDev/NolQu-L', GITHUB_REF='refs/heads/Testing',
            GITHUB_EVENT_NAME='push', GITHUB_ACTOR='NolQuDev', GITHUB_SHA='a' * 40,
            GITHUB_TOKEN='test-fixture-only')
        with tempfile.TemporaryDirectory() as directory:
            env['RUNNER_TEMP'] = directory
            with mock.patch.dict(m.os.environ, env), mock.patch.object(m, 'ORIGINAL_ASSETS', originals), \
                    mock.patch.object(m.publisher, 'GitHub', return_value=api), \
                    mock.patch.object(m.publisher, 'command', side_effect=[b'a' * 40, m.BASE.encode()]):
                if change_old_head:
                    with self.assertRaisesRegex(ValueError, 'changed or unpreserved'):
                        m.main()
                else:
                    m.main()
            report = json.loads((Path(directory) / 'nolqu-l-maintenance/result.json').read_text())
        return m, api, report, originals

    def test_complete_migration_preserves_originals_and_all_kept_heads(self):
        m, api, report, originals = self.run_migration()
        self.assertEqual(report['status'], 'COMPLETE')
        self.assertEqual(len(report['deleted']), 11)
        self.assertEqual(api.heads, {**m.KEEP_HEADS, 'Testing': 'a' * 40})
        self.assertEqual(api.release['name'], 'NolQu-L 1.0.0 alpha.1')
        for name, original in originals.items():
            actual = next(a for a in api.assets if a['name'] == name)
            self.assertTrue(all(actual[k] == value for k, value in original.items()))
        self.assertEqual(len(api.assets), 8)

    def test_ref_changed_after_preflight_is_never_deleted(self):
        _, api, report, _ = self.run_migration(change_old_head=True)
        self.assertEqual(report['status'], 'FAILED')
        self.assertFalse(any(method == 'DELETE' for method, _ in api.calls))


if __name__ == '__main__':
    unittest.main(verbosity=2)
