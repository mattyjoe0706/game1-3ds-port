import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_items import encode
from convert_tiles import definition,expand
from convert_course import fnv1a

class ItemPackageTests(unittest.TestCase):
    def terrain(self):
        payload=struct.pack('<HHHBBBBH',560,96,49,1,0,0,1,0)
        head=struct.pack('<4s7I',b'NST1',1,1,1408,320,256,192,0)
        return head+struct.pack('<I',fnv1a(head+payload))+payload
    def test_extra_bits_preserved(self):
        data=bytes([0,49,7<<2,254,255])
        self.assertEqual(definition(data,0),[[(0,49)]])
        self.assertEqual(expand(definition(data,0,True),2,1),[[49|(7<<10)]*2])
    def test_binding_and_rejection(self):
        records=[dict(area=1,x=1056,y=480,tile=49,contents=7)]
        terrain=self.terrain();b=encode(records,[],terrain,123)
        self.assertEqual(len(b),36)
        self.assertEqual(struct.unpack_from('<II',b,12),(fnv1a(terrain),123))
        self.assertEqual(struct.unpack_from('<3HBBI',b,24),(560,96,0,2,7,0))
        self.assertEqual(struct.unpack_from('<I',b,20)[0],fnv1a(b[:20]+b[24:]))
        records[0]['contents']=3
        with self.assertRaises(ValueError):encode(records,[],terrain)
        with self.assertRaises(ValueError):encode([],[],terrain[:-1])
        bad=bytearray(terrain);bad[-1]^=1
        with self.assertRaises(ValueError):encode([],[],bad)
    def test_actor_coin_settings_not_silently_ignored(self):
        actor=dict(area=1,id=147,x=1408,y=516,layer=0,param=0)
        b=encode([],[actor],self.terrain())
        self.assertEqual(struct.unpack_from('<3HBBI',b,24),(912,132,65535,1,0,0))
        actor['param']=1
        with self.assertRaises(ValueError):encode([],[actor],self.terrain())

if __name__=='__main__':unittest.main()
