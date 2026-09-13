from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_checkpoint import encode
from package_terrain import encode as terrain_encode
from convert_course import fnv1a


class CheckpointPackageTests(unittest.TestCase):
    def setUp(self):
        self.terrain=terrain_encode([dict(x=3104,y=432,slot=1,tile=1,layer=1,
            collision='solid',shape=0,flags='0000000100000000')],0,'checkpoint')[0]
        self.flag=dict(kind=1,id=188,x=3184,y=416,param=65536,layer=0)
        self.entry=dict(id=1,x=3104,y=416,type=0,flags=0,destination_file=0,destination_id=0,layer=0)

    def test_original_entrance_and_feet_alignment(self):
        raw=encode([self.flag],[self.entry],self.terrain)
        self.assertEqual(struct.unpack('<4s9I',raw),(b'NSK1',1,fnv1a(self.terrain),2688,32,2608,16,1,0,fnv1a(raw[:36])))

    def test_missing_duplicate_and_unsupported_entrances(self):
        for entries in ([],[self.entry,self.entry],[dict(self.entry,type=3)],[dict(self.entry,flags=128)],
                        [dict(self.entry,destination_file=2)],[dict(self.entry,y=384)]):
            with self.assertRaises(ValueError):encode([self.flag],entries,self.terrain)

    def test_settings_and_binding_rejected(self):
        for settings in (1,16,65537,65552,0x1000000):
            with self.assertRaises(ValueError):encode([dict(self.flag,param=settings)],[self.entry],self.terrain)
        raw=bytearray(self.terrain);raw[-1]^=1
        with self.assertRaises(ValueError):encode([self.flag],[self.entry],raw)
        with self.assertRaises(ValueError):encode([self.flag,self.flag],[self.entry],self.terrain)


if __name__=='__main__':unittest.main()
