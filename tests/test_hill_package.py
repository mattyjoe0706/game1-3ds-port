import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_hill import encode, opening_actor
from convert_course import fnv1a


class HillPackageTests(unittest.TestCase):
    def course(self,settings=0x01301801):
        b=bytearray(128)
        struct.pack_into('>II',b,7*8,112,16)
        struct.pack_into('>HHH2xI4x',b,112,212,1456,544,settings)
        return b

    def test_only_verified_instance(self):
        self.assertEqual(opening_actor(self.course()),(1456,544,0x01301801))
        for settings in (0x01301811,0x01301800,0x01201801):
            with self.assertRaises(ValueError):opening_actor(self.course(settings))

    def test_bound_package_and_continuous_cap(self):
        terrain=bytearray(36);terrain[:4]=b'NST1';struct.pack_into('<II',terrain,12,1408,320)
        b=encode(terrain,b'texture')
        self.assertEqual(len(b),2592)
        self.assertEqual(struct.unpack_from('<II',b,8),(fnv1a(terrain),fnv1a(b'texture')))
        self.assertEqual(struct.unpack_from('<I',b,28)[0],fnv1a(b[:28]+b[32:]))
        rows=list(struct.iter_unpack('<4f',b[32:]))
        self.assertEqual(rows[0],(648,4,320,rows[0][3]))
        self.assertEqual(rows[79][3],160)
        self.assertEqual(rows[-1][3],320)
        for a,c in zip(rows,rows[1:]):
            self.assertEqual(a[0]+a[1],c[0]);self.assertEqual(a[3],c[2])
        for x,w,left,right in rows:
            self.assertLessEqual(abs(left-right),5.4)


if __name__=='__main__':unittest.main()
