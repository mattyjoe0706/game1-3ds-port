"""Check this project's single-content, unencrypted CIA HOME Menu resources.

This is a packaging regression check, not a signature or device-launch verifier.
"""
import hashlib
from pathlib import Path
import struct


def verify_cia(path):
    b = Path(path).read_bytes()
    def need(condition, message):
        if not condition:
            raise ValueError(message)
    def u32(offset):
        need(offset + 4 <= len(b), 'Truncated CIA')
        return struct.unpack_from('<I', b, offset)[0]
    align = lambda n: (n + 63) & ~63
    need(len(b) >= 32, 'Truncated CIA header')
    ncch = sum(align(u32(offset)) for offset in (0, 8, 12, 16))
    content_size = struct.unpack_from('<Q', b, 24)[0]
    need(ncch + content_size <= len(b), 'Truncated CIA content')
    need(b[ncch+0x100:ncch+0x104] == b'NCCH', 'Missing NCCH header')
    need(u32(ncch+0x104)*512 == content_size, 'Expected one NCCH content')
    need(bool(b[ncch+0x18f] & 4), 'Expected unencrypted homebrew NCCH')
    exefs = ncch + u32(ncch+0x1a0)*512
    size = u32(ncch+0x1a4)*512
    need(size >= 512 and exefs+size <= ncch+content_size, 'Invalid ExeFS bounds')
    entries = {}
    for i in range(10):
        raw, offset, length = struct.unpack_from('<8sII', b, exefs+i*16)
        if not raw.strip(b'\0'):
            continue
        name = raw.rstrip(b'\0').decode('ascii')
        need(name not in entries, 'Duplicate ExeFS entry')
        need(length > 0 and 512+offset+length <= size, 'Invalid ExeFS entry bounds')
        data = b[exefs+512+offset:exefs+512+offset+length]
        expected = b[exefs+0x1e0-i*32:exefs+0x200-i*32]
        need(hashlib.sha256(data).digest() == expected, f'Invalid {name} hash')
        if name == 'banner':
            need(data[:4] == b'CBMD', 'Invalid banner header')
        if name == 'icon':
            need(data[:4] == b'SMDH', 'Invalid icon header')
        entries[name] = length
    need({'.code', 'icon', 'banner', 'logo'} <= entries.keys(),
         'Missing HOME Menu resources: code, icon, banner and logo are required by this project')
    return {'exefs_entries': entries, 'hardware_tested': False}


if __name__ == '__main__':
    import json, sys
    print(json.dumps(verify_cia(sys.argv[1]), indent=2))
