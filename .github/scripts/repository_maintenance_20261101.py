"""One-time, maintainer-authorized consolidation; preserves tags and release bytes."""
import importlib.util
import json
import os
from pathlib import Path
import re
import time
import urllib.parse

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('maintenance_alpha', ROOT / '.github/scripts/alpha_release.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
BASE = '9495509c543dfdd81746caf5ac1314246589f36c'
RELEASE_REVISION = '26ad9b80b5a3164a20854ce3e3798642fba3f15e'
TAG = 'v1.0.0-alpha.1'
RELEASE_ID = 427654824
KEEP_HEADS = {'Main': 'c219167c324418e2cc4fd1763cec754fb33c44f1',
              'Dev': 'c219167c324418e2cc4fd1763cec754fb33c44f1',
              'Stable': '391e540a70b95daf58c582f69153dacba2c4051d'}
OLD_HEADS = {'ci/alpha1-release-20261029': 'ffe76fc0916cdcf445b38a98374aeeb0187133c5', 'ci/alpha1-release-fixed-20261029': 'd6807067e6a1d92b1dd00fd1968d746e46acd371', 'ci/alpha2-baseline-20261029': '26ad9b80b5a3164a20854ce3e3798642fba3f15e', 'ci/alpha2-control-retention-20261029': '397d18e7726b9a75712eba36e6da07c424b24dde', 'ci/bootstrap-output-guards-20261030': '9495509c543dfdd81746caf5ac1314246589f36c', 'ci/c032-differential-20261029': 'f624d89213709c777b4cb2215df07ec311174cc5', 'ci/dual-runtime-status-20261030': 'c219167c324418e2cc4fd1763cec754fb33c44f1', 'ci/nolqu-lang-naming-20261029': '26ad9b80b5a3164a20854ce3e3798642fba3f15e', 'ci/supervisor-resources-20261029': '78aa35b693e97aa4d3524d8900473eb93d2edc26', 'ci/termux-differential-20261029': '6e21758e34e327869fcfab5a9c5156616de9d31a', 'release/v1.0.0-alpha.1': '26ad9b80b5a3164a20854ce3e3798642fba3f15e'}
ORIGINAL_ASSETS = {'BUILD-METADATA.json': {'id': 687989752, 'size': 4973, 'digest': 'sha256:8dc048396e98c2518630ec06d93aab092e75a070610d28f4a7fcd4b78bac24e0'}, 'nolqu-l-1.0.0-alpha.1-source.tar.gz': {'id': 687989623, 'size': 902642, 'digest': 'sha256:35280cb5bc4a4711fed078c696cbc4cbba1e46b90af22cf5fb88a13abf694a1f'}, 'nolqu-l-1.0.0-alpha.1-termux-bundle.tar.gz': {'id': 687989666, 'size': 80238, 'digest': 'sha256:d0d7dcaf9ed608134322f6806846b0347dbb031c3db16860ccc24c6c99efd46b'}, 'QUALIFICATION.json': {'id': 687989715, 'size': 68076, 'digest': 'sha256:754ae3deae762b017f36111c87f6206d7444a9975ec8dfdc8570c8fb1a77f0d5'}, 'SHA256SUMS': {'id': 687989770, 'size': 382, 'digest': 'sha256:0b041088619a7932f548ac65779c2241ff6b822f35a8c730fa767563e55c0926'}}


def route(suffix):
    return publisher.api_path(suffix)


def validate_context(env, revision, parent):
    expected = dict(GITHUB_REPOSITORY='NolQuDev/NolQu-L', GITHUB_REF='refs/heads/Testing',
                    GITHUB_EVENT_NAME='push', GITHUB_ACTOR='NolQuDev', GITHUB_SHA=revision)
    if (parent != BASE or re.fullmatch('[0-9a-f]{40}', revision) is None
            or any(env.get(key) != value for key, value in expected.items())):
        raise ValueError('maintenance requires the explicit official Testing push and parent')


def head(api, name):
    ref = api.request('GET', route('git/ref/heads/' + urllib.parse.quote(name, safe='')), missing=True)
    if ref is None:
        return None
    if ref['object']['type'] != 'commit':
        raise ValueError('branch does not name a commit')
    return ref['object']['sha']


def validate_old_head(name, observed, comparison):
    if name not in OLD_HEADS:
        raise ValueError('unapproved deletion target')
    if observed is None:
        return
    if (observed != OLD_HEADS[name] or comparison.get('status') not in ('ahead', 'identical')
            or comparison.get('behind_by') != 0
            or comparison.get('merge_base_commit', {}).get('sha') != observed):
        raise ValueError('changed or unpreserved branch head: ' + name)


def check_kept_refs(api, revision):
    for name, expected in {**KEEP_HEADS, 'Testing': revision}.items():
        if head(api, name) != expected:
            raise ValueError('kept branch changed: ' + name)
    if publisher.tag_revision(api, TAG) != RELEASE_REVISION:
        raise ValueError('published tag changed')


def check_originals(api):
    release = api.request('GET', route('releases/' + str(RELEASE_ID)))
    if (release.get('tag_name') != TAG or release.get('draft') is not False
            or release.get('prerelease') is not True):
        raise ValueError('published Alpha identity changed')
    assets = api.request('GET', route('releases/' + str(RELEASE_ID) + '/assets?per_page=100'))
    downloaded = {}
    for name, expected in ORIGINAL_ASSETS.items():
        matches = [item for item in assets if item['name'] == name]
        if len(matches) != 1 or any(matches[0].get(k) != v for k, v in expected.items()):
            raise ValueError('published original asset changed: ' + name)
        item = matches[0]
        data = api.request('GET', route('releases/assets/' + str(item['id'])), binary=True)
        publisher.checked_assets([item], {name: data})
        downloaded[name] = data
    return release, downloaded


def preflight(api, revision):
    # Finish every read-only identity/ancestry check before the first mutation.
    check_kept_refs(api, revision)
    for name, expected in OLD_HEADS.items():
        observed = head(api, name)
        comparison = api.request('GET', route('compare/' + expected + '...' + revision)) if observed else None
        validate_old_head(name, observed, comparison)
    return check_originals(api)


def ensure_asset(api, name, data, label):
    endpoint = 'releases/' + str(RELEASE_ID) + '/assets'
    assets = api.request('GET', route(endpoint + '?per_page=100'))
    present = [item for item in assets if item['name'] == name]
    if present:
        publisher.checked_assets(present, {name: data})
        item = present[0]
    else:
        query = urllib.parse.urlencode(dict(name=name, label=label))
        item = api.request('POST', route(endpoint + '?' + query), data, upload=True)
        publisher.checked_assets([item], {name: data})
    actual = api.request('GET', route('releases/assets/' + str(item['id'])), binary=True)
    if actual != data:
        raise ValueError('uploaded asset download mismatch')
    return dict(name=name, label=label, bytes=len(data), sha256=publisher.sha256(data),
                url=item['browser_download_url'])


def wait_for_qualification(api, revision):
    deadline = time.monotonic() + 900
    while True:
        runs = api.request('GET', route('actions/workflows/linux-qualification.yml/runs?head_sha=' + revision + '&per_page=100'))['workflow_runs']
        chosen = [r for r in runs if r.get('event') == 'push' and r.get('head_branch') == 'Testing'
                  and r.get('head_sha') == revision]
        if chosen:
            latest = max(chosen, key=lambda r: r['id'])
            if latest.get('status') == 'completed':
                if latest.get('conclusion') != 'success':
                    raise ValueError('exact-source Testing qualification failed')
                return latest['html_url']
        if time.monotonic() >= deadline:
            raise ValueError('exact-source Testing qualification did not complete')
        time.sleep(10)


def main():
    revision = publisher.command(ROOT, 'git', 'rev-parse', 'HEAD').decode().strip()
    parent = publisher.command(ROOT, 'git', 'rev-parse', 'HEAD^').decode().strip()
    validate_context(os.environ, revision, parent)
    api = publisher.GitHub(os.environ.get('GITHUB_TOKEN'))
    output = Path(os.environ['RUNNER_TEMP']) / 'nolqu-l-maintenance'
    output.mkdir(exist_ok=False)
    report = dict(status='RUNNING', revision=revision, deleted=[], original_assets=ORIGINAL_ASSETS)
    def save():
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    try:
        report['qualification'] = wait_for_qualification(api, revision)
        release, downloaded = preflight(api, revision)
        display = publisher.release_name('1.0.0-alpha.1')
        portable = display.replace(' ', '.')
        source = downloaded['nolqu-l-1.0.0-alpha.1-source.tar.gz']
        zipped = publisher.source_zip(source, display)
        if zipped != publisher.source_zip(source, display):
            raise ValueError('ZIP did not reproduce')
        assets = {portable + '.zip': zipped,
                  portable + '-Termux.tar.gz': downloaded['nolqu-l-1.0.0-alpha.1-termux-bundle.tar.gz']}
        assets[portable + '.SHA256SUMS'] = publisher.checksum_bytes(assets)
        report['assets'] = []
        for name, data in assets.items():
            (output / name).write_bytes(data)
            label = name.replace(portable, display)
            report['assets'].append(ensure_asset(api, name, data, label))
            save()
        marker = '<!-- readable-downloads-20261101 -->'
        body = release['body']
        if marker not in body:
            body += '\n\n' + marker + '\nPreferred downloads (original published assets remain available):\n'
            body += '\n'.join('- [' + a['label'] + '](' + a['url'] + ')' for a in report['assets'])
            body += '\nThe ZIP repackages the original published source bytes under the readable versioned directory. The Termux copy is byte-identical to the original bundle. Tag/source revision unchanged.\n'
        api.request('PATCH', route('releases/' + str(RELEASE_ID)), dict(name=display, body=body))
        for name in OLD_HEADS:
            check_kept_refs(api, revision)
            observed = head(api, name)
            comparison = api.request('GET', route('compare/' + OLD_HEADS[name] + '...' + revision)) if observed else None
            validate_old_head(name, observed, comparison)
            if observed:
                api.request('DELETE', route('git/refs/heads/' + urllib.parse.quote(name, safe='')))
            if head(api, name) is not None:
                raise ValueError('branch deletion did not complete')
            report['deleted'].append(dict(name=name, sha=OLD_HEADS[name]))
            save()
        check_kept_refs(api, revision)
        check_originals(api)
        report['status'] = 'COMPLETE'
        save()
    except Exception:
        report['status'] = 'FAILED'
        save()
        raise
    print(json.dumps(dict(status=report['status'], deleted=len(report['deleted']), assets=report['assets'])))


if __name__ == '__main__':
    main()
