from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_enemies import encode
from package_terrain import encode as terrain_encode
from convert_course import fnv1a

def fixture():
    return terrain_encode([dict(x=496,y=608,slot=1,tile=1,layer=1,flags='0000000100000000',collision='solid',shape=0)],0)[0]

class EnemyPackageTests(unittest.TestCase):
    def test_coordinate_conversion_and_binding(self):
        terrain=fixture()
        raw=encode([dict(kind=1,id=20,x=1104,y=592,param=0)],terrain)
        self.assertEqual(struct.unpack('<4s5I',raw[:24]),(b'NSE1',1,1,fnv1a(terrain),0,fnv1a(raw[:20]+raw[24:])))
        self.assertEqual(struct.unpack('<4H',raw[24:]),(608,208,20,0))
    def test_other_actors_are_not_goombas(self):
        raw=encode([dict(kind=1,id=147,x=1104,y=592,param=0)],fixture())
        self.assertEqual(len(raw),24)
    def test_settings_and_capacity(self):
        r=dict(kind=1,id=20,x=1104,y=592,param=1)
        with self.assertRaises(ValueError):encode([r],fixture())
        r['param']=0
        with self.assertRaises(ValueError):encode([r]*33,fixture())
    def test_damaged_terrain(self):
        raw=bytearray(fixture());raw[-1]^=1
        with self.assertRaises(ValueError):encode([],raw)
        with self.assertRaises(ValueError):encode([],b'NST1')

if __name__=='__main__':unittest.main()
