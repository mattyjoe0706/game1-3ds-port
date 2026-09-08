"""Synthetic package checks, not native execution or signature verification."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from verify_cia import verify_cia


def fixture(missing=None):
    b = bytearray(4096)
    struct.pack_into('<I', b, 0, 64)
    struct.pack_into('<Q', b, 24, 3584)
    n = 64
    b[n+0x100:n+0x104] = b'NCCH'
    struct.pack_into('<I', b, n+0x104, 7)
    b[n+0x18f] = 4
    struct.pack_into('<II', b, n+0x1a0, 1, 6)
    e = n+512
    for i, (name, data) in enumerate([('.code', b'code'), ('icon', b'SMDH'), ('banner', b'CBMD'), ('logo', b'logo')]):
        if name == missing:
            continue
        struct.pack_into('<8sII', b, e+i*16, name.encode(), i*512, len(data))
        b[e+512+i*512:e+512+i*512+len(data)] = data
        b[e+0x1e0-i*32:e+0x200-i*32] = hashlib.sha256(data).digest()
    return b


class CiaTests(unittest.TestCase):
    def verify(self, b):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'test.cia'
            p.write_bytes(b)
            return verify_cia(p)

    def test_complete_resources(self):
        self.assertEqual(len(self.verify(fixture())['exefs_entries']), 4)

    def test_missing_home_menu_resources(self):
        for name in ('banner', 'logo', 'icon'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Missing HOME Menu'):
                self.verify(fixture(name))

    def test_corrupt_resource(self):
        b = fixture()
        b[64+512+512] ^= 1
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.verify(b)

    def test_truncated_content(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            self.verify(fixture()[:1000])
