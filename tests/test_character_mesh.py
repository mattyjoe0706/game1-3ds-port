import struct,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from convert_character import Reader
from character_mesh import attribute,commands
from character_pose import IDENTITY,multiply,point,srt
from character_texture import decode,rgb565

class CharacterMeshTests(unittest.TestCase):
    def test_transform_order(self):
        m=srt([1,1,1],[0,0,90],[5,2,3])
        for a,b in zip(point(m,[1,0,0]),[5,3,3]):self.assertAlmostEqual(a,b)
        self.assertEqual(multiply(IDENTITY,m),m)
    def test_normal_fixed_point(self):
        b=bytearray(38);struct.pack_into('>I',b,8,32);struct.pack_into('>II',b,20,0,3)
        struct.pack_into('>BBH3h',b,28,14,6,1,16384,0,-16384)
        self.assertEqual(attribute(Reader(b),0,len(b),'normal')['values'],[[1,0,-1]])
        with self.assertRaises(ValueError):attribute(Reader(b),0,len(b)-1,'normal')
    def test_commands(self):
        b=struct.pack('>BHHB',2,4,9,1)
        self.assertEqual(commands(Reader(b),0,len(b),'NodeTree'),[dict(op=2,args=(4,9))])
        with self.assertRaises(ValueError):commands(Reader(b[:-1]),0,len(b)-1,'NodeTree')
        b=struct.pack('>BHBHfB',3,1,1,0,0.5,1)
        with self.assertRaises(ValueError):commands(Reader(b),0,len(b),'NodeMix')
    def test_cmpr_subblocks_and_alpha(self):
        red=struct.pack('>HHI',0xf800,0,0)
        green=struct.pack('>HHI',0x7e0,0,0)
        blue=struct.pack('>HHI',0x1f,0,0)
        transparent=struct.pack('>HHI',0,0xffff,0xffffffff)
        out=decode(red+green+blue+transparent,8,8,14)
        for x,y,color in [(0,0,(255,0,0,255)),(4,0,(0,255,0,255)),(0,4,(0,0,255,255)),(4,4,(0,0,0,0))]:
            self.assertEqual(tuple(out[(y*8+x)*4:(y*8+x+1)*4]),color)
        with self.assertRaises(ValueError):decode(red,8,8,14)
    def test_i8_and_565(self):
        self.assertEqual(decode(bytes([128])*32,8,4,1),bytes([128,128,128,255])*32)
        self.assertEqual(rgb565(0xffff),(255,255,255,255))
        self.assertEqual(decode(bytes.fromhex('f800')*16,4,4,4),bytes([255,0,0,255])*16)

if __name__=='__main__':unittest.main()
