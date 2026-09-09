from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_terrain import encode, gpu_atlas, morton
from convert_course import fnv1a

class TerrainPackageTests(unittest.TestCase):
    def test_header_and_bound_hash(self):
        record=dict(x=496,y=608,slot=1,tile=1,layer=1,flags='0000000100000000',collision='solid',shape=0)
        raw,omitted=encode([record],123)
        self.assertEqual(len(raw),48)
        self.assertEqual(struct.unpack('<4s8I',raw[:36]),
                         (b'NST1',1,1,1408,320,256,192,123,fnv1a(raw[:32]+raw[36:])))
        self.assertEqual(omitted,0)
        self.assertEqual(struct.unpack('<HHHBBBBH',raw[36:]),(0,224,257,1,0,0,1,0))

    def test_unsupported_shape_rejected(self):
        record=dict(x=496,y=608,slot=1,tile=1,layer=1,flags='0000004000000000',collision='ceiling_slope',shape=0)
        with self.assertRaises(ValueError):encode([record],123)

    def test_morton_addresses_unique(self):
        self.assertEqual({morton(x,y) for x in range(8) for y in range(8)},set(range(64)))

    def test_texture_sampling_orientation_and_byte_order(self):
        texture=bytearray(1024*256*4)
        for y in range(256):
            for x in range(1024):
                off=(y*1024+x)*4
                texture[off:off+4]=bytes((x%256,y,73,201))
        atlas=gpu_atlas({0:texture})
        self.assertEqual(len(atlas),1048576)
        # Independently interleave the bits for the GPU address, then undo ABGR.
        for tile,x,y in [(0,0,0),(0,15,15),(31,7,8),(255,15,15)]:
            ax=(tile%32)*16+x;ay=511-((tile//32)*16+y)
            interleave=(ax&1)|((ay&1)<<1)|((ax&2)<<1)|((ay&2)<<2)|((ax&4)<<2)|((ay&4)<<3)
            offset=((ay//8)*4096+(ax//8)*64+interleave)*4
            sx=(tile%32)*32+4+(x*24+12)//16
            sy=(tile//32)*32+4+(y*24+12)//16
            self.assertEqual(atlas[offset:offset+4][::-1],bytes((sx%256,sy,73,201)))

if __name__=='__main__':unittest.main()
