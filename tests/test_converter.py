from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from convert_course import read_layer, decode_course, encode_scene, fnv1a


def course(initial=0, entrance=0):
    blocks=[bytes(128), bytearray(20), b"", b"", b"", b"", bytearray(20), b"\xff"*4, b"", bytearray(24), b"", b"", b"", b""]
    blocks[1][16]=initial
    blocks[6][8]=entrance
    struct.pack_into(">HH",blocks[6],0,100,200)
    struct.pack_into(">4H",blocks[9],0,0,0,640,360)
    offset=112; header=bytearray()
    for block in blocks:
        header.extend(struct.pack(">II",offset,len(block))); offset+=len(block)
    return bytes(header)+b"".join(blocks)


class ConverterTests(unittest.TestCase):
    def test_endianness_tileset_and_units(self):
        r=read_layer(bytes.fromhex("1000001f0026002c0001ffff"),1)[0]
        self.assertEqual((r['id'],r['x'],r['y'],r['w'],r['h']),(0x1000,496,608,704,16))

    def test_missing_terminator(self):
        with self.assertRaises(ValueError): read_layer(bytes(10),0)

    def test_truncated_record(self):
        with self.assertRaises(ValueError): read_layer(bytes(9)+b"\xff\xff",0)

    def test_zero_sized_object(self):
        with self.assertRaises(ValueError): read_layer(bytes(10)+b"\xff\xff",0)

    def test_invalid_tileset(self):
        with self.assertRaises(ValueError): read_layer(struct.pack(">5H",0x4000,0,0,1,1)+b"\xff\xff",0)

    def test_start_entrance(self):
        decoded=decode_course(course(),{})
        self.assertEqual(decoded['view_origin']['x'],100)
        self.assertEqual(decoded['view_origin_policy'],'options_entrance')
        self.assertEqual(len(decoded['records']),2)

    def test_subarea_fallback_explicit(self):
        decoded=decode_course(course(initial=1,entrance=3),{})
        self.assertEqual(decoded['initial_entrance_id'],1)
        self.assertEqual(decoded['view_origin']['id'],3)
        self.assertEqual(decoded['view_origin_policy'],'first_entrance_for_viewer_only')

    def test_header_integrity(self):
        encoded=encode_scene(1,decode_course(course(),{}))
        self.assertEqual(encoded[:4],b'NSC1')
        self.assertEqual(len(encoded),32+2*24)
        self.assertEqual(struct.unpack_from('<I',encoded,28)[0],fnv1a(encoded[:28]+encoded[32:]))

    def test_real_course_golden(self):
        import json
        directory=Path(__file__).resolve().parents[1]/'sdmc/3ds/nsmbw-prototype/data'
        if not (directory/'manifest.json').is_file():
            self.skipTest('Local game data is intentionally absent from source-only CI')
        manifest=json.loads((directory/'manifest.json').read_text())
        self.assertEqual([a['counts'] for a in manifest['areas']],
                         [{'0':640,'1':77,'2':6,'3':1},{'0':184,'1':4,'2':4,'3':2}])
        for area in manifest['areas']:
            raw=(directory/area['file']).read_bytes()
            import hashlib
            self.assertEqual(hashlib.sha256(raw).hexdigest(),area['sha256'])
            self.assertEqual(struct.unpack_from('<I',raw,28)[0],fnv1a(raw[:28]+raw[32:]))


if __name__=='__main__': unittest.main()
