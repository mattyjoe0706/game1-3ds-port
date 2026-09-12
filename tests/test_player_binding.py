import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from character_pose import player_animation_values

class PlayerBindingTests(unittest.TestCase):
    def bone(self,i):return dict(id=i,translation=[1,2,3],rotation_degrees=[4,5,6],scale=[1,1,1])
    def values(self):return [[2,2,2],[10,20,30],[100,200,300]]
    def test_root_and_child_positions(self):
        self.assertEqual(player_animation_values(self.bone(0),self.values(),'small'),self.values())
        v=player_animation_values(self.bone(1),self.values(),'small')
        self.assertAlmostEqual(v[2][1],109.20000076293946)
        v=player_animation_values(self.bone(16),self.values(),'small')
        self.assertEqual(v[2],[1,2,3]);self.assertEqual(v[1],[10,20,30])
    def test_penguin_wrists_and_action_override(self):
        for i in (11,14):
            v=player_animation_values(self.bone(i),self.values(),'penguin')
            self.assertEqual(v,[[1,1,1],[4,5,6],[1,2,3]])
            v=player_animation_values(self.bone(i),self.values(),'penguin',True)
            self.assertEqual(v,[[2,2,2],[10,20,30],[1,2,3]])
    def test_unknown_form_rejected(self):
        with self.assertRaises(ValueError):player_animation_values(self.bone(1),self.values(),'invented')

if __name__=='__main__':unittest.main()
