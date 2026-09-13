import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from character_texture import decode

class RGB5A3Tests(unittest.TestCase):
    def test_opaque_and_translucent_branches(self):
        words=[0xfc00,0x83e0,0x801f,0xffff,0x0f00,0x70f0,0x300f,0x7fff]+[0]*8
        data=struct.pack('>16H',*words)
        rgba=decode(data,4,4,5)
        expected=[(255,0,0,255),(0,255,0,255),(0,0,255,255),(255,255,255,255),
                  (255,0,0,0),(0,255,0,255),(0,0,255,109),(255,255,255,255)]
        self.assertEqual([tuple(rgba[i:i+4]) for i in range(0,32,4)],expected)
        self.assertEqual(decode(struct.pack('>H',0xc210)*16,1,1,5),bytes((132,132,132,255)))
        self.assertEqual(decode(struct.pack('>H',0x2fff)*16,1,1,5),bytes((255,255,255,73)))
    def test_tile_order_and_partial_edge(self):
        red=struct.pack('>H',0xfc00)*16;blue=struct.pack('>H',0x801f)*16
        rgba=decode(red+blue,5,3,5)
        self.assertEqual(len(rgba),60)
        for row in range(3):
            self.assertEqual(rgba[row*20:row*20+16],bytes((255,0,0,255))*4)
            self.assertEqual(rgba[row*20+16:row*20+20],bytes((0,0,255,255)))
        with self.assertRaises(ValueError):decode(red,5,3,5)

if __name__=='__main__':unittest.main()
