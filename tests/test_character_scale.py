from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from character_pose import pose,point

def fixture(compensate=True):
    bones=[dict(id=i,matrix_id=i+1,name=str(i),flags=32 if i and compensate else 0,
                scale=[2,3,4] if i==0 else [1,1,1],
                rotation_degrees=[0,0,0] if i==0 else [0,0,90],
                translation=[0,0,0] if i==0 else [5,6,7]) for i in range(2)]
    return dict(bones=bones,scene={'NodeTree':[{'op':2,'args':[0,0]},{'op':2,'args':[1,1]}]})

class ScaleTests(unittest.TestCase):
    def test_compensation_retains_scaled_translation_and_rotation(self):
        m=pose(fixture())[2]
        for actual,expected in zip(point(m,[1,0,0]),[10,19,28]):self.assertAlmostEqual(actual,expected)

    def test_uncompensated_child_inherits_scale(self):
        m=pose(fixture(False))[2]
        for actual,expected in zip(point(m,[1,0,0]),[10,21,28]):self.assertAlmostEqual(actual,expected)

    def test_duplicate_matrix_keeps_parent_scale(self):
        m=fixture();m['scene']['NodeTree'].insert(1,{'op':6,'args':[7,1]})
        m['scene']['NodeTree'][-1]['args'][1]=7
        self.assertEqual(pose(m)[2],pose(fixture())[2])

    def test_animation_controls_compensation(self):
        clip={'nodes':[{'name':'1','flags':0,'channels':{}}]}
        self.assertEqual(pose(fixture(),clip)[2],pose(fixture(False))[2])
        clip['nodes'][0]['flags']=1<<10
        self.assertEqual(pose(fixture(False),clip)[2],pose(fixture())[2])

    def test_singular_parent_and_xsi_rejected(self):
        m=fixture();m['bones'][0]['scale'][0]=0
        with self.assertRaisesRegex(ValueError,'Singular'):pose(m)
        with self.assertRaisesRegex(ValueError,'XSI'):
            pose(fixture(),{'nodes':[{'name':'1','flags':1<<12,'channels':{}}]})

if __name__=='__main__':unittest.main()
