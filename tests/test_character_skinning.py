from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from character_pose import IDENTITY,apply_node_mix,point,srt

class SkinningTests(unittest.TestCase):
    def test_weighted_motion_and_inverse_bind(self):
        bones=[{'id':3,'inverse_bind_matrix':srt([1]*3,[0]*3,[-10,0,0])},
               {'id':7,'inverse_bind_matrix':srt([1]*3,[0]*3,[0,-20,0])}]
        matrices={2:srt([1]*3,[0]*3,[14,0,0]),8:srt([1]*3,[0]*3,[0,28,0])}
        ops=[{'op':5,'args':[2,3]},{'op':5,'args':[8,7]},
             {'op':3,'destination':9,'weights':[(2,.25),(8,.75)]}]
        apply_node_mix({'bones':bones,'scene':{'NodeMix':ops}},matrices)
        self.assertEqual(point(matrices[9],[1,2,3]),[2,8,3])
        self.assertEqual(point(matrices[2],[0,0,0]),[14,0,0])

    def test_envelope_scratch_survives_draw_overwrite(self):
        bones=[{'id':0,'inverse_bind_matrix':IDENTITY}]
        matrices={0:srt([1]*3,[0]*3,[4,0,0]),1:srt([1]*3,[0]*3,[8,0,0])}
        ops=[{'op':5,'args':[0,0]},{'op':5,'args':[1,0]},
             {'op':3,'destination':0,'weights':[(1,1)]},
             {'op':3,'destination':2,'weights':[(0,1)]}]
        apply_node_mix({'bones':bones,'scene':{'NodeMix':ops}},matrices)
        self.assertEqual(point(matrices[2],[0,0,0]),[4,0,0])

    def test_missing_reference_and_invalid_weights(self):
        cases=[{'op':5,'args':[9,0]}, {'op':5,'args':[0,9]},
               {'op':3,'destination':1,'weights':[(9,1)]},
               {'op':3,'destination':1,'weights':[(0,.5)]},
               {'op':3,'destination':1,'weights':[(0,float('nan'))]}, {'op':99}]
        for op in cases:
            with self.subTest(op=op),self.assertRaises(ValueError):
                apply_node_mix({'bones':[{'id':0,'inverse_bind_matrix':IDENTITY}], 'scene':{'NodeMix':[op]}},{0:IDENTITY})

if __name__=='__main__': unittest.main()
