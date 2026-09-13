import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_pipe_hill import source_actor,rotate,upper_height,encode
from package_terrain import encode as terrain_encode
from convert_course import fnv1a
from package_items import encode as item_encode

class PipeHillTests(unittest.TestCase):
    def test_actual_source_settings_not_mistyped_entrance(self):
        raw=bytes.fromhex('01680770022000000e00040100000000')
        kind,x,y=struct.unpack_from('>3H',raw)
        a=dict(kind=1,id=kind,x=x,y=y,param=struct.unpack_from('>I',raw,8)[0])
        self.assertEqual((source_actor({'records':[a]})['param']>>8)&15,4)
        with self.assertRaises(ValueError):source_actor({'records':[dict(a,param=0x0e000001)]})
    def test_rotation_and_open_mouth_profile(self):
        x,y=rotate(0,400,90);self.assertAlmostEqual(x,400);self.assertAlmostEqual(y,0)
        # Raised banks separated by a lower mouth floor: never bridge the gap.
        triangles=[[(-100,300),(-20,300),(-20,0)],[(20,300),(100,300),(20,0)],
                   [(-100,200),(100,200),(0,-400)]]
        self.assertEqual(upper_height(triangles,0),200)
        self.assertEqual(upper_height(triangles,-50),300)
        with self.assertRaises(ValueError):upper_height(triangles,120)
    def test_package_binding_and_profile(self):
        terrain=terrain_encode([dict(x=496,y=608,slot=1,tile=1,layer=1,flags='0000000100000000',collision='solid',shape=0)],0,'checkpoint')[0]
        triangles=[[(-400,300),(400,300),(0,-400)]]
        b,rows=encode(terrain,b'texture',triangles)
        self.assertEqual(len(b),2592)
        self.assertEqual(struct.unpack_from('<II',b,8),(fnv1a(terrain),fnv1a(b'texture')))
        self.assertEqual(struct.unpack_from('<I',b,28)[0],fnv1a(b[:28]+b[32:]))
        self.assertEqual(rows[0],(1096,4,260,260));self.assertEqual(rows[-1][0],1732)
        with self.assertRaises(ValueError):encode(terrain,b'texture',[[(-400,900),(400,900),(0,-400)]])
    def test_no_rescue_actor_becomes_solid_coin_block(self):
        actor=dict(area=1,kind=1,id=422,x=2208,y=448,param=0,layer=0)
        terrain=terrain_encode([],0,'checkpoint',[actor])[0]
        self.assertEqual(struct.unpack('<HHHBBBBH',terrain[36:]),(1712,64,49,1,0,0,1,0))
        items=item_encode([],[actor],terrain,section='checkpoint')
        self.assertEqual(struct.unpack('<3HBBI',items[24:]),(1712,64,0,2,0,0))
        with self.assertRaises(ValueError):terrain_encode([],0,'checkpoint',[dict(actor,param=1)])

if __name__=='__main__':unittest.main()
