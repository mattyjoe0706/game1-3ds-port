"""Synthetic format cases; no original game assets required in CI."""
from pathlib import Path
import struct
import sys
import unittest
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from convert_tiles import lz11, rgb5a3, png, definition, repeated, expand, collision


class TerrainTests(unittest.TestCase):
    def test_literal_lz(self):
        self.assertEqual(lz11(b'\x11\x03\0\0\0ABC'), b'ABC')

    def test_overlapping_lz(self):
        self.assertEqual(lz11(b'\x11\x09\0\0\x40A\x70\0'), b'A'*9)

    def test_extended_lengths(self):
        for size, token in [(18,b'\0\0\0'), (274,b'\x10\0\0\0')]:
            self.assertEqual(lz11(b'\x11'+size.to_bytes(3,'little')+b'\x40A'+token),b'A'*size)

    def test_bad_lz(self):
        for data in [b'',b'\x10\x01\0\0',b'\x11\x01\0\0',
                     b'\x11\x03\0\0\x80\x20\0',
                     b'\x11\x02\0\0\x40A\x70\0']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                lz11(data)
        with self.assertRaises(ValueError):
            lz11(b'\x11\xff\xff\xff')

    def test_texture_channels_and_blocks(self):
        data = struct.pack('>16H', *([0xfc00]*16))+struct.pack('>16H',*([0x03f0]*16))
        rgba = rgb5a3(data,8,4)
        self.assertEqual(rgba[:4],bytes((255,0,0,255)))
        self.assertEqual(rgba[16:20],bytes((51,255,0,0)))
        self.assertEqual(rgba[8*3*4:8*3*4+4],bytes((255,0,0,255)))
        with self.assertRaises(ValueError):
            rgb5a3(data[:-1],8,4)

    def test_png_integrity(self):
        rgba = bytes((10,20,30,255))*8
        raw = png(4,2,rgba)
        offset = 8
        chunks = {}
        while offset < len(raw):
            size = struct.unpack_from('>I',raw,offset)[0]
            kind = raw[offset+4:offset+8]
            payload = raw[offset+8:offset+8+size]
            self.assertEqual(zlib.crc32(kind+payload),struct.unpack_from('>I',raw,offset+8+size)[0])
            chunks[kind]=payload
            offset += size+12
        self.assertEqual(zlib.decompress(chunks[b'IDAT']),b'\0'+rgba[:16]+b'\0'+rgba[16:])

    def test_object_decode(self):
        self.assertEqual(definition(bytes.fromhex('000102feff'),0),[[(0,513)]])
        for raw in [b'',b'\0',bytes.fromhex('000102ff'),b'\xfe']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                definition(raw,0)

    def test_stretch_edges(self):
        self.assertEqual(expand([[(0,1),(1,2),(0,3)]],6,2),[[1,2,2,2,2,3]]*2)
        self.assertEqual(expand([[(0,1)],[(2,2)],[(0,3)]],2,5),
                         [[1,1],[2,2],[2,2],[2,2],[3,3]])
        self.assertEqual(expand([[(0,1),(0,2)]],5,1),[[1,2,1,2,1]])

    def test_diagonal_directions(self):
        for control, expected in [(128,[[None,None,7],[None,7,None],[7,None,None]]),
                                  (129,[[7,None,None],[None,7,None],[None,None,7]]),
                                  (130,[[7,None,None],[None,7,None],[None,None,7]]),
                                  (131,[[None,None,7],[None,7,None],[7,None,None]])]:
            self.assertEqual(expand([[(control,None),(0,7)]],3,3),expected)

    def test_capacity(self):
        for w,h in [(0,1),(1025,1),(1024,512)]:
            with self.assertRaises(ValueError):
                expand([[(0,1)]],w,h)

    def test_collision_priority(self):
        self.assertEqual(collision(bytes.fromhex('0000002100000002')),'floor_slope')
        self.assertEqual(collision(bytes.fromhex('0000800100000000')),'top_only')
        self.assertEqual(collision(bytes.fromhex('0000000100000000')),'solid')
        self.assertEqual(collision(bytes(8)),'empty')


if __name__ == '__main__':
    unittest.main()
