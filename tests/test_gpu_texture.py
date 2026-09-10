import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from gpu_texture import rgba8_tiles

class GPUTextureTests(unittest.TestCase):
    def test_known_corner_addresses(self):
        pixels=bytearray(16*16*4)
        fixtures=[(0,0,0),(1,0,1),(0,1,2),(7,7,63),(8,0,64),(0,8,128),(15,15,255)]
        for i,(x,y,index) in enumerate(fixtures):pixels[(y*16+x)*4:(y*16+x+1)*4]=bytes([i+1,22,33,255])
        packed=rgba8_tiles(pixels,16,16)
        for i,(_,_,index) in enumerate(fixtures):self.assertEqual(packed[index*4:index*4+4],bytes([255,33,22,i+1]))

    def test_all_sprite_cells_upright_and_not_blank(self):
        # Distinct top/bottom markers in all 21 occupied cells; row 3 stays blank.
        pixels=bytearray(512*256*4)
        for frame in range(21):
            for local_y,marker in ((0,10),(63,90)):
                x=(frame%8)*64;y=(frame//8)*64+local_y
                pixels[(y*512+x)*4:(y*512+x+1)*4]=bytes([frame+1,marker,77,255])
        packed=rgba8_tiles(pixels,512,256)
        # Addresses at tile corners: local (0,0)=0; local (0,7)=42.
        for frame in range(21):
            tile_x=(frame%8)*8;tile_y=(frame//8)*8
            for row,within,marker in ((tile_y,0,10),(tile_y+7,42,90)):
                address=(row*64+tile_x)*64+within
                self.assertEqual(packed[address*4:address*4+4],bytes([255,77,marker,frame+1]))
        self.assertEqual(packed[192*512*4:],bytes(64*512*4))

    def test_invalid_dimensions(self):
        for w,h,raw in ((0,8,b''),(7,8,bytes(224)),(8,8,bytes(255))):
            with self.assertRaises(ValueError):rgba8_tiles(raw,w,h)

if __name__=='__main__':unittest.main()
