"""Publish one qualified Alpha snapshot; no compiler or credential configuration."""
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import posixpath
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'NolQuDev/NolQu-L'
MAX_DOWNLOAD = 64 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(root, *args):
    result = subprocess.run(list(args), cwd=root, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError('release host command failed: ' + args[0])
    return result.stdout


def release_tag(version, channel):
    if channel != 'dev' or re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)-alpha\.[1-9][0-9]*', version) is None:
        raise ValueError('publisher accepts only an Alpha version on dev')
    return 'v' + version


def validate_context(environment, tag, revision):
    if (environment.get('GITHUB_REPOSITORY') != REPOSITORY
            or re.fullmatch('[0-9a-f]{40}', revision) is None
            or environment.get('GITHUB_SHA') != revision
            or environment.get('GITHUB_REF') != 'refs/heads/release/' + tag
            or environment.get('GITHUB_EVENT_NAME') not in ('push', 'workflow_dispatch')):
        raise ValueError('release requires the exact official release branch and commit')


def qualified_run(runs, branch, revision):
    selected = [run for run in runs if run.get('head_sha') == revision
                and run.get('head_branch') == branch and run.get('event') == 'push']
    if not selected:
        raise ValueError('no exact-source qualification for ' + branch)
    latest = max(selected, key=lambda run: run['id'])
    if latest.get('status') != 'completed' or latest.get('conclusion') != 'success':
        raise ValueError('latest qualification is not successful: ' + branch)
    return latest


def validate_qualification(report, revision, gates, identities):
    actual = report.get('gates', [])
    if (report.get('passed') is not True or report.get('status') != 'PASSED'
            or report.get('canonical_inputs_unchanged') is not True
            or report.get('context', {}).get('revision') != revision
            or report.get('context', {}).get('canonical_inputs') != identities
            or [gate.get('label') for gate in actual] != list(gates)
            or any(gate.get('passed') is not True or gate.get('exit_code') != 0
                   or gate.get('invocation', {}).get('supervisor_ok') is not True
                   or gate.get('invocation', {}).get('timed_out') is not False
                   or gate.get('invocation', {}).get('cancelled') is not False for gate in actual)):
        raise ValueError('incomplete, failed or different-source qualification receipt')


def validate_draft(release, tag, revision, body):
    if (release.get('draft') is not True or release.get('prerelease') is not True
            or release.get('tag_name') != tag or release.get('target_commitish') != revision
            or release.get('body') != body):
        raise ValueError('published release or mismatched draft is immutable')


def checked_assets(assets, expected):
    checked = set()
    for asset in assets:
        name = asset.get('name')
        if (name not in expected or name in checked or asset.get('state') != 'uploaded'
                or asset.get('size') != len(expected[name])
                or asset.get('digest') != 'sha256:' + sha256(expected[name])):
            raise ValueError('existing or uploaded release asset does not match: ' + str(name))
        checked.add(name)
    return checked


def source_archive(root, revision, prefix):
    if re.fullmatch('[A-Za-z0-9._-]+', prefix) is None:
        raise ValueError('invalid archive prefix')
    policy = load('release_publication_policy', ROOT / 'tools/check_publication.py')
    payload = command(root, 'git', 'archive', '--format=tar', '--prefix=' + prefix + '/', revision)
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as stream:
        for member in stream:
            if not member.name.startswith(prefix + '/') or member.name == prefix + '/':
                if member.name.rstrip('/') == prefix:
                    continue
                raise ValueError('source archive path escape')
            relative = member.name[len(prefix) + 1:].rstrip('/')
            if policy.blocked_reason(relative):
                raise ValueError('private source archive path: ' + relative)
            if member.issym() or member.islnk():
                target = posixpath.normpath(posixpath.join(posixpath.dirname(member.name), member.linkname))
                if not target.startswith(prefix + '/'):
                    raise ValueError('source archive link escape: ' + relative)
            elif not (member.isdir() or member.isfile()):
                raise ValueError('unsupported source archive entry')
    return gzip.compress(payload, mtime=0)


def bundle_archive(root, prefix):
    tool = load('release_android_smoke', ROOT / 'tools/nql_android_smoke.py')
    with tempfile.TemporaryDirectory(prefix='nql-alpha-bundle-') as directory:
        bundle = Path(directory) / 'bundle'
        tool.prepare_bundle(root, bundle)
        tool.verify_bundle(bundle)
        files = {path.name: path.read_bytes() for path in bundle.iterdir()}
        files['LICENSE'] = (root / 'LICENSE').read_bytes()
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode='w', format=tarfile.USTAR_FORMAT) as stream:
        for name, data in sorted(files.items()):
            entry = tarfile.TarInfo(prefix + '/' + name)
            entry.size = len(data)
            entry.mode = 0o755 if name.endswith('.seed') else 0o644
            entry.mtime = 0
            stream.addfile(entry, io.BytesIO(data))
    return gzip.compress(payload.getvalue(), mtime=0)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


class GitHub:
    def __init__(self, token):
        if not token:
            raise ValueError('repository workflow token is missing')
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, method, route, payload=None, *, missing=False, upload=False):
        if not route.startswith('/repos/' + REPOSITORY + '/'):
            raise ValueError('unexpected repository API route')
        host = 'https://uploads.github.com' if upload else 'https://api.github.com'
        data = payload if upload else (json.dumps(payload).encode() if payload is not None else None)
        request = urllib.request.Request(host + route, method=method, data=data, headers={
            'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'NolQu-L-Alpha-Publisher',
            'Content-Type': 'application/octet-stream' if upload else 'application/json'})
        try:
            with self.opener.open(request, timeout=45) as response:
                body = response.read(MAX_DOWNLOAD + 1)
        except urllib.error.HTTPError as error:
            if missing and error.code == 404:
                error.close()
                return None
            if method == 'GET' and route.endswith('/zip') and error.code == 302:
                location = error.headers['Location']
                error.close()
                url = urllib.parse.urlsplit(location)
                if url.scheme != 'https' or not url.hostname or url.username or url.password:
                    raise ValueError('invalid artifact redirect')
                # Signed storage URL is used without the repository Authorization header.
                with urllib.request.urlopen(location, timeout=45) as response:
                    body = response.read(MAX_DOWNLOAD + 1)
            else:
                code = error.code
                error.close()
                raise RuntimeError('GitHub release request failed with HTTP ' + str(code)) from None
        if len(body) > MAX_DOWNLOAD:
            raise ValueError('release API/download size limit exceeded')
        return body if route.endswith('/zip') else json.loads(body)


def api_path(suffix):
    return '/repos/' + REPOSITORY + '/' + suffix


def heads(api, revision):
    for branch in ('Main', 'Dev'):
        ref = api.request('GET', api_path('git/ref/heads/' + branch))
        if ref['object']['type'] != 'commit' or ref['object']['sha'] != revision:
            raise ValueError('Main and Dev must both equal the release revision')


def tag_revision(api, tag):
    ref = api.request('GET', api_path('git/ref/tags/' + tag), missing=True)
    if ref is None:
        return None
    obj = ref['object']
    for _ in range(8):
        if obj['type'] == 'commit':
            return obj['sha']
        if obj['type'] != 'tag' or re.fullmatch('[0-9a-f]{40}', obj['sha']) is None:
            break
        obj = api.request('GET', api_path('git/tags/' + obj['sha']))['object']
    raise ValueError('unsupported or cyclic release tag')


def qualification_receipts(api, revision):
    pipeline = load('release_linux_qualification', ROOT / '.github/scripts/linux_qualification.py')
    expected_gates = [name for name, _ in pipeline.GATES]
    identities = pipeline.identities()
    runs = api.request('GET', api_path('actions/workflows/linux-qualification.yml/runs?head_sha=' + revision + '&per_page=100'))['workflow_runs']
    receipts = {}
    for branch in ('Main', 'Dev'):
        run = qualified_run(runs, branch, revision)
        artifacts = api.request('GET', api_path('actions/runs/' + str(run['id']) + '/artifacts?per_page=100'))['artifacts']
        name = 'nolqu-l-linux-' + str(run['id']) + '-' + str(run['run_attempt'])
        matches = [item for item in artifacts if item['name'] == name and not item['expired']]
        if len(matches) != 1:
            raise ValueError('missing exact qualification artifact for ' + branch)
        artifact = matches[0]
        archive = api.request('GET', api_path('actions/artifacts/' + str(artifact['id']) + '/zip'))
        if artifact.get('digest') != 'sha256:' + sha256(archive):
            raise ValueError('qualification artifact digest mismatch')
        with zipfile.ZipFile(io.BytesIO(archive)) as stream:
            member = 'nolqu-l-qualification/result.json'
            if stream.namelist().count(member) != 1 or stream.getinfo(member).file_size > 2 * 1024 * 1024:
                raise ValueError('invalid qualification report framing')
            report = json.loads(stream.read(member))
        validate_qualification(report, revision, expected_gates, identities)
        context = report['context']
        if (str(context.get('run_id')) != str(run['id'])
                or str(context.get('run_attempt')) != str(run['run_attempt'])
                or context.get('branch_policy', {}).get('branch') != branch):
            raise ValueError('qualification receipt origin does not match run/attempt/branch')
        receipts[branch] = dict(run_id=run['id'], run_attempt=run['run_attempt'],
            url=run['html_url'], artifact_sha256=sha256(archive), report=report)
    return receipts, identities


def main():
    revision = command(ROOT, 'git', 'rev-parse', 'HEAD').decode().strip()
    version, channel = [(ROOT / name).read_text().strip() for name in ('VERSION', 'CHANNEL')]
    tag = release_tag(version, channel)
    validate_context(os.environ, tag, revision)
    if command(ROOT, 'git', 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('release requires a clean source checkout')
    api = GitHub(os.environ.get('GITHUB_TOKEN'))
    heads(api, revision)
    stable = api.request('GET', api_path('git/ref/heads/Stable'))['object']['sha']
    existing_tag = tag_revision(api, tag)
    if existing_tag is not None and existing_tag != revision:
        raise ValueError('existing tag belongs to a different immutable revision')
    receipts, identities = qualification_receipts(api, revision)
    name = 'nolqu-l-' + version
    source = source_archive(ROOT, revision, name)
    bundle = bundle_archive(ROOT, name + '-termux-bundle')
    if source != source_archive(ROOT, revision, name) or bundle != bundle_archive(ROOT, name + '-termux-bundle'):
        raise ValueError('release archives did not reproduce exactly')
    assets = {name + '-source.tar.gz': source, name + '-termux-bundle.tar.gz': bundle,
              'QUALIFICATION.json': (json.dumps(receipts, sort_keys=True, indent=2) + '\n').encode()}
    metadata = dict(version=version, channel=channel, source_revision=revision,
        source_tree_state='clean committed snapshot', target='x86_64-linux',
        command='python3 -B .github/scripts/alpha_release.py',
        environment=dict(python=sys.version, platform=platform.platform(), git=command(ROOT, 'git', '--version').decode().strip()),
        builder=dict(repository=REPOSITORY, workflow='.github/workflows/alpha-release.yml',
                     run_id=os.environ.get('GITHUB_RUN_ID'), run_attempt=os.environ.get('GITHUB_RUN_ATTEMPT')),
        canonical_inputs=identities, archives={key:dict(bytes=len(value),sha256=sha256(value)) for key,value in assets.items()},
        archive_reproducibility='two same-environment builds byte-identical',
        provenance='build metadata only; formal attestation NOT IMPLEMENTED',
        signing='NOT IMPLEMENTED', sbom='NOT IMPLEMENTED', support_lifecycle='DEVELOPMENT',
        native_termux_new_profile='NOT RUN; experimental bundle, Linux controls only',
        full_compiler='NOT IMPLEMENTED', self_hosting='NOT IMPLEMENTED', verified_nqlc='NOT IMPLEMENTED')
    assets['BUILD-METADATA.json'] = (json.dumps(metadata, sort_keys=True, indent=2) + '\n').encode()
    assets['SHA256SUMS'] = ''.join(sha256(data) + '  ' + key + '\n' for key,data in sorted(assets.items())).encode()
    output = Path(os.environ['RUNNER_TEMP']) / 'nolqu-l-alpha-assets'
    output.mkdir(mode=0o700, exist_ok=False)
    for key, data in assets.items():
        (output / key).write_bytes(data)
    notes = (ROOT / 'docs/releases' / (version + '.md')).read_text()
    body = notes + '\n\nSource revision: `' + revision + '`\n\n'
    body += '\n'.join('- ' + branch + ' qualification: ' + receipt['url'] for branch,receipt in receipts.items())
    body += '\n\nArchive identity, build details and limitations are in the attached SHA256SUMS, BUILD-METADATA.json and QUALIFICATION.json.\n'
    heads(api, revision)
    release = api.request('GET', api_path('releases/tags/' + tag), missing=True)
    if release is None:
        # A draft has a private /releases/id URL; tags lookup may omit drafts.
        releases = api.request('GET', api_path('releases?per_page=100'))
        drafts = [item for item in releases if item.get('tag_name') == tag]
        if len(drafts) > 1:
            raise ValueError('duplicate release drafts')
        release = drafts[0] if drafts else None
    if release is not None:
        validate_draft(release, tag, revision, body)
    else:
        release = api.request('POST', api_path('releases'), dict(tag_name=tag,
            target_commitish=revision, name='NolQu-L ' + version, body=body,
            draft=True, prerelease=True, make_latest='false'))
    release_id = str(int(release['id']))
    uploaded = api.request('GET', api_path('releases/' + release_id + '/assets?per_page=100'))
    present = checked_assets(uploaded, assets)
    for key, data in assets.items():
        if key not in present:
            asset = api.request('POST', api_path('releases/' + release_id + '/assets?name=' + urllib.parse.quote(key, safe='')), data, upload=True)
            checked_assets([asset], {key: data})
    uploaded = api.request('GET', api_path('releases/' + release_id + '/assets?per_page=100'))
    if checked_assets(uploaded, assets) != set(assets):
        raise ValueError('release assets are incomplete')
    heads(api, revision)
    # Recheck the latest branch runs before the irreversible public promotion.
    current_runs = api.request('GET', api_path('actions/workflows/linux-qualification.yml/runs?head_sha=' + revision + '&per_page=100'))['workflow_runs']
    for branch, receipt in receipts.items():
        latest = qualified_run(current_runs, branch, revision)
        if (latest['id'], latest['run_attempt']) != (receipt['run_id'], receipt['run_attempt']):
            raise ValueError('qualification run changed before publication')
    published = api.request('PATCH', api_path('releases/' + release_id), dict(draft=False, prerelease=True, make_latest='false'))
    if published['draft'] or not published['prerelease'] or published['tag_name'] != tag or tag_revision(api, tag) != revision:
        raise ValueError('published release/tag verification failed')
    if api.request('GET', api_path('git/ref/heads/Stable'))['object']['sha'] != stable:
        raise ValueError('Stable changed during publication; investigate without rewriting release')
    receipt = dict(status='PUBLISHED', tag=tag, revision=revision, url=published['html_url'],
                   release_id=int(release_id), prerelease=True,
                   assets={key:dict(bytes=len(data),sha256=sha256(data)) for key,data in assets.items()})
    (output / 'PUBLICATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile) as error:
        print('alpha-release: ' + type(error).__name__ + ': ' + str(error), file=sys.stderr)
        raise SystemExit(1)
