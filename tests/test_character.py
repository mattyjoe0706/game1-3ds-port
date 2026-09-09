from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from convert_character import Reader,track,sample,display_setup,primitives

class CharacterTests(unittest.TestCase):
    def test_triangle_topology(self):
        desc=[0]*21;desc[9]=2
        cases=[(0x90,6,[[0,1,2],[3,4,5]]),(0x80,4,[[0,1,2],[0,2,3]]),
               (0x98,5,[[0,1,2],[2,1,3],[2,3,4]]),(0xa0,5,[[0,1,2],[0,2,3],[0,3,4]])]
        for op,n,expected in cases:
            out=primitives(struct.pack('>BH',op,n)+bytes(range(n)),desc)
            self.assertEqual(out['triangles'],expected)
            self.assertEqual([v['9'] for v in out['vertices']],list(range(n)))
    def test_matrix_load_snapshot_and_wide_indices(self):
        desc=[0]*21;desc[0]=1;desc[9]=3
        draw=b'\x90\x00\x03'+b''.join(struct.pack('>BH',0,i) for i in (256,257,258))
        out=primitives(struct.pack('>BHH',0x20,7,0xb000)+draw+struct.pack('>BHH',0x20,9,0xb000)+draw,desc)
        self.assertEqual(out['vertices'][0],{'0':0,'9':256})
        self.assertEqual([d['matrix_loads'][0]['index'] for d in out['draws']],[7,9])
        self.assertEqual(out['draws'][0]['matrix_loads'][0]['words'],12)
    def test_bad_primitives(self):
        desc=[0]*21;desc[9]=2
        for data in (b'\x90\x00\x03\x01',b'\x90\x00\x04\x00\x01\x02\x03',b'\x91',b'\x20\x00'):
            with self.assertRaises(ValueError):primitives(data,desc)
        desc[10]=1
        with self.assertRaises(ValueError):primitives(b'',desc)
    def test_setup_registers_and_bounds(self):
        data=b'\0'+b''.join(struct.pack('>BBI',8,k,v) for k,v in ((0x50,0x5e1d),(0x60,3),(0x70,0)))
        desc=display_setup(data)
        self.assertEqual(desc[9],3)
        self.assertEqual(desc[13],3)
        for bad in (data[:-1],b'\x61',b'\x10\x00\x01\x10\x00\x00'):
            with self.assertRaises(ValueError):display_setup(bad)
    def test_bounds_and_names(self):
        for p,n in [(-1,4),(14,4),(0,-1)]:
            with self.assertRaises(ValueError):Reader(bytes(16)).need(p,n)
        with self.assertRaises(ValueError):Reader(b'A'*256).name(0)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):Reader(struct.pack('>f',float('nan'))).read('f',0)
    def test_dictionary_limit(self):
        b=bytearray(64);struct.pack_into('>II',b,8,24,4097)
        with self.assertRaises(ValueError):Reader(b).dic(8)
    def test_bad_brres(self):
        with self.assertRaises(ValueError):Reader(bytes(16)).resources()
    def test_compact32_signed_tangent(self):
        header=struct.pack('>HHfff',1,0,1,0.5,10)
        word=(3<<24)|(100<<12)|0xfe0
        self.assertEqual(track(Reader(header+struct.pack('>I',word)),0,1,10)['keys'],[[3,60,-1]])
    def test_compact48_fractional_time(self):
        header=struct.pack('>HHfff',1,0,1,2,-10)
        self.assertEqual(track(Reader(header+struct.pack('>hHh',48,20,-128)),0,2,10)['keys'],[[1.5,30,-0.5]])
    def test_float96(self):
        t=track(Reader(struct.pack('>HHf6f',2,0,1,0,1,0,10,9,0)),0,3,10)
        self.assertEqual([sample(t,f) for f in (0,5,10)],[1,5,9])
    def test_per_frame_encodings(self):
        for kind,raw in [(4,struct.pack('>ff3B',2,1,0,1,2)),(5,struct.pack('>ff3H',2,1,0,1,2)),(6,struct.pack('>3f',1,3,5))]:
            t=track(Reader(raw),0,kind,2)
            self.assertEqual([sample(t,f) for f in (-1,.5,10)],[1,2,5])
    def test_keyframe_order(self):
        with self.assertRaises(ValueError):track(Reader(struct.pack('>HHf6f',2,0,1,5,1,0,3,9,0)),0,3,10)
    def test_truncation_and_unknown_encoding(self):
        with self.assertRaises(ValueError):track(Reader(bytes(8)),0,7,10)
        with self.assertRaises(ValueError):track(Reader(struct.pack('>HHf',2,0,1)),0,3,10)
    def test_hermite_tangent_scaling(self):
        t=dict(type='hermite',keys=[[0,0,1],[10,10,1]])
        self.assertAlmostEqual(sample(t,2.5),2.5)
        self.assertAlmostEqual(sample(t,7.5),7.5)

if __name__=='__main__':unittest.main()
