"""Test-only, independently frozen C0.31 baseline and native source helpers."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from c031_support import (ROOT, candidate_binary, decode_nqaf, encode_profile_source,
                         run_native)

PREDECESSORS = ROOT / 'tests/bootstrap/fixtures/c032/predecessor'
LEDGER_SHA256 = '022a3a50f6ebd9aaa693876d34a2522253c500d41b554b9b7c10c0331a9c5b54'


def build_c031_predecessors(destination):
    """Validate every input before execution; publish the complete verified pair.

    The pinned ledger binds observed C0.31 source/artifact identities and the
    unchanged B0 source/artifact, independently of promoted C0 installed seeds.
    Staging is a sibling directory so publication is a single atomic rename.
    """
    raw = (PREDECESSORS / 'hashes.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER_SHA256:
        raise ValueError('C0.31 predecessor identity ledger changed')
    ledger = json.loads(raw)
    names = ('frontend', 'backend')
    if (set(ledger) != {'sources', 'artifacts', 'b0'} or
            set(ledger['sources']) != {f'{n}.nql' for n in names} or
            set(ledger['artifacts']) != {f'c0-{n}.seed' for n in names} or
            set(ledger['b0']) != {'source_sha256', 'artifact_sha256'}):
        raise ValueError('invalid C0.31 identity ledger schema')
    for section in ledger.values():
        for value in section.values():
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('invalid C0.31 SHA-256')
    sources = {name: (PREDECESSORS / f'{name}.nql').read_bytes() for name in names}
    for name, source in sources.items():
        if hashlib.sha256(source).hexdigest() != ledger['sources'][f'{name}.nql']:
            raise ValueError(f'C0.31 source SHA-256 mismatch: {name}')
    b0 = ROOT / 'bootstrap/compiler/b0/x86_64-linux/b0.seed'
    b0_source = ROOT / 'bootstrap/compiler/b0/compiler.nql0'
    pin = b0.with_suffix('.sha256').read_text().split()
    if (hashlib.sha256(b0_source.read_bytes()).hexdigest() != ledger['b0']['source_sha256'] or
            hashlib.sha256(b0.read_bytes()).hexdigest() != ledger['b0']['artifact_sha256'] or
            pin != [ledger['b0']['artifact_sha256'], 'b0.seed'] or not os.access(b0, os.X_OK)):
        raise ValueError('frozen B0 identity mismatch')
    destination = Path(destination).absolute()
    if destination.is_symlink() or (destination.exists() and
            (not destination.is_dir() or any(destination.iterdir()))):
        raise FileExistsError('C0.31 destination must be an empty owned directory')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.c032-baseline-', dir=destination.parent) as staging:
        work = Path(staging)
        publish = work / 'verified'
        publish.mkdir()
        for name in names:
            source = work / f'{name}.nql'
            source.write_bytes(sources[name])
            artifact = publish / f'c0-{name}.seed'
            result = run_native(b0, args=('--compiler-profile', str(source), '-o', str(artifact)), timeout=120)
            if (result.returncode, result.stdout, result.stderr) != (0, b'', b''):
                raise ValueError(f'C0.31 {name} build failed: {result.returncode}: {result.stderr!r}')
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != ledger['artifacts'][artifact.name]:
                raise ValueError(f'C0.31 {name} artifact SHA-256 mismatch')
            if not os.access(artifact, os.X_OK):
                raise ValueError(f'C0.31 {name} artifact is not executable')
        # Recheck destination immediately before the only publication operation.
        if destination.is_symlink() or (destination.exists() and
                (not destination.is_dir() or any(destination.iterdir()))):
            raise FileExistsError('C0.31 destination is no longer empty')
        publish.replace(destination)
    return {name: destination / f'c0-{name}.seed' for name in names}


def frame(offset, *words):
    """Test source builder: six little-endian words, evaluated once in the guest."""
    if len(words) != 6:
        raise ValueError('syscall frames contain exactly six words')
    # NolQu expressions use checked signed arithmetic. Division/remainder by
    # powers of256 is safe for the positive addresses used by these oracles.
    lines = []
    for i, word in enumerate(words):
        if isinstance(word, int):
            for byte, value in enumerate((word & ((1 << 64)-1)).to_bytes(8, 'little')):
                lines.append(f'byte_store({offset + i*8 + byte},{value})')
            continue
        name = f'w{offset}_{i}'
        lines.append(f'let {name}={word}')
        for byte in range(8):
            lines.append(f'byte_store({offset + i*8 + byte},{name}/{256**byte})')
    return '\n'.join(lines)


def raw_body(body):
    return 'unsafe {# safety: oracle owns descriptors, frames and checked spans\n' + body + '\n}'
