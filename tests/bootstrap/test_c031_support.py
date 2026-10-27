"""Independent framing/identity tests, not a compiler implementation."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch

import c031_support as support


def wire(version=5, profile=0):
    source = b"fn main(){return 7}"
    nodes = [(5, 0, 17, 1, 0, 0, 0), (32, 0, 10, 6, 1, 0, 0),
             (33, 0, 0, 2, 2, 0, 0)]
    if version == 5:
        header = struct.pack("<4sBBHIIIIBBHI", b"NQAF", 5, 32, 0,
                             len(source), 3, 3, 9, 1, profile, 0, 0)
        records = b"".join(struct.pack("<BBHIIIIIII", k, f, 0, o, n, l, r, nxt, 0, 0)
                           for k, f, o, n, l, r, nxt in nodes)
    else:
        header = struct.pack("<4sBBHHHHH", b"NQAF", version, 16, 0,
                             len(source), 3, 3, 9)
        records = b"".join(struct.pack("<BBHHHHH4s", *n, bytes(4)) for n in nodes)
    return header + source + records, source, nodes


class SupportTests(unittest.TestCase):
    def test_explicit_candidate_path_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with patch.dict(os.environ, {"B0_COMPILER": str(missing)}):
                with self.assertRaises(FileNotFoundError):
                    support.candidate_binary("B0_COMPILER", __file__)
            with patch.dict(os.environ, {"B0_COMPILER": ""}):
                with self.assertRaises(ValueError):
                    support.candidate_binary("B0_COMPILER", __file__)

    def test_candidate_is_executable_regular_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "binary"
            candidate.write_bytes(b"data")
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(PermissionError):
                    support.candidate_binary("B0_COMPILER", candidate)
                candidate.chmod(0o755)
                self.assertEqual(support.candidate_binary("B0_COMPILER", candidate), candidate)
                with self.assertRaises(ValueError):
                    support.candidate_binary("B0_COMPILER", tmp)

    def test_profile_envelope_preserves_bytes(self):
        for data in (b"", b"fn main(){return 0}\n", b"\0\xffNQSC\r\n"):
            self.assertEqual(support.encode_profile_source(data),
                             b"NQSC\x01\x01" + bytes(10) + data)

    def test_legacy_and_wide_headers_are_exact(self):
        for version in range(1, 6):
            for profile in ((0, 1) if version == 5 else (0,)):
                with self.subTest(version=version, profile=profile):
                    data, source, records = wire(version, profile)
                    header, nodes = support.decode_nqaf(data)
                    self.assertEqual(header, dict(version=version, source_length=len(source),
                                     node_count=3, root_id=3, token_count=9,
                                     dialect=1 if version == 5 else version,
                                     runtime_profile=profile, source=source))
                    self.assertEqual(nodes, records)

    def test_truncation_and_trailing_bytes_are_rejected(self):
        for version in (1, 5):
            data, _, _ = wire(version)
            for length in range(len(data)):
                with self.subTest(version=version, length=length):
                    with self.assertRaises(ValueError):
                        support.decode_nqaf(data[:length])
            with self.assertRaises(ValueError):
                support.decode_nqaf(data + b"\0")

    def test_invalid_header_and_reserved_bytes(self):
        for version, offsets in ((1, (0, 4, 5, 6, 7)),
                                 (5, (0, 4, 5, 6, 7, 24, 25, 26, 27, 28, 31))):
            original, source, _ = wire(version)
            for offset in offsets:
                data = bytearray(original)
                data[offset] = 255
                with self.subTest(version=version, offset=offset):
                    with self.assertRaises(ValueError):
                        support.decode_nqaf(data)
            for offset in ((1, 12, 13, 14, 15) if version == 1 else (1, 2, 3, 24, 28, 31)):
                data = bytearray(original)
                data[(16 if version == 1 else 32) + len(source) + offset] = 1
                with self.assertRaises(ValueError):
                    support.decode_nqaf(data)

    def test_spans_and_ids_are_not_truncated(self):
        data, _, _ = wire()
        for offset in (8, 12, 16, 20):
            malformed = bytearray(data)
            struct.pack_into("<I", malformed, offset, 0xffffffff)
            with self.assertRaises(ValueError):
                support.decode_nqaf(malformed)
        data = struct.pack("<4sBBHIIIIBBHI", b"NQAF", 5, 32, 0,
                           65537, 1, 1, 1, 1, 0, 0, 0) + b" " * 65536 + b"7"
        data += struct.pack("<BBHIIIIIII", 5, 0, 0, 65536, 1, 0, 0, 0, 0, 0)
        header, nodes = support.decode_nqaf(data)
        self.assertEqual(header.get("source_length"), 65537)
        self.assertEqual(nodes, [(5, 0, 65536, 1, 0, 0, 0)])
        data = bytearray(data)
        struct.pack_into("<I", data, 32 + 65537 + 8, 2)
        with self.assertRaises(ValueError):
            support.decode_nqaf(data)

    def test_graph_walk_is_iterative_and_rejects_sharing_cycles(self):
        nodes = [(5, 0, 0, 1, 0, 0, 0)]
        nodes.extend((32, 0, 0, 1, i, 0, 0) for i in range(1, 5000))
        header = dict(node_count=len(nodes), root_id=len(nodes))
        support.assert_owned_graph(header, nodes)
        for replacement in ((32, 0, 0, 1, 4999, 4999, 0),
                            (32, 0, 0, 1, 5000, 0, 0),
                            (32, 0, 0, 1, 1, 0, 0)):
            with self.assertRaises(ValueError):
                support.assert_owned_graph(header, nodes[:-1] + [replacement])

    def test_corrupt_snapshot_fails_before_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshots = Path(tmp) / "snapshots"
            shutil.copytree(support.PREDECESSORS, snapshots)
            with (snapshots / "frontend.nql").open("ab") as out:
                out.write(b"corruption")
            destination = Path(tmp) / "build"
            with patch.object(support, "PREDECESSORS", snapshots):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    support.build_predecessors(destination)
            self.assertFalse(destination.exists())

    def test_predecessors_are_reconstructed_from_verified_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = support.build_predecessors(Path(tmp) / "build")
            self.assertEqual(set(result), {"b0", "frontend", "backend"})
            hashes = json.loads((support.PREDECESSORS / "hashes.json").read_text())
            for name, filename in (("b0", "b0.seed"), ("frontend", "c0-frontend.seed"),
                                   ("backend", "c0-backend.seed")):
                self.assertEqual(hashlib.sha256(result[name].read_bytes()).hexdigest(),
                                 hashes["artifacts"][filename])
            self.assertEqual(set(p.name for p in (Path(tmp) / "build").iterdir()),
                             {"b0.seed", "c0-frontend.seed", "c0-backend.seed"})


if __name__ == "__main__":
    unittest.main()
