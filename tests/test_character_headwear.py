import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from character_pose import headwear_hidden_materials,mesh

class HeadwearTests(unittest.TestCase):
    def test_caps_and_hair_are_alternatives(self):
        m={'materials':[{'name':n} for n in ('mat_player_hat','mat_player_hair','mat_player_face')]}
        self.assertEqual(headwear_hidden_materials(m,True),{'mat_player_hair'})
        self.assertEqual(headwear_hidden_materials(m,False),{'mat_player_hat'})
        self.assertEqual(headwear_hidden_materials(m,None),set())

    def test_special_helmets_are_unchanged(self):
        for names in (('mat_player_hair',),('mat_player_hat',),('mat_player_plhead',)):
            self.assertEqual(headwear_hidden_materials({'materials':[{'name':n} for n in names]},True),set())

    def test_hidden_shapes_are_not_evaluated(self):
        m={'materials':[{'name':'mat_player_hat'},{'name':'mat_player_hair'}],
           'scene':{'DrawOpa':[{'args':[1,99,0,0]}],'DrawXlu':[{'args':[1,100,0,0]}]}}
        self.assertEqual(list(mesh(m,{},wearing_cap=True)),[])

if __name__=='__main__':unittest.main()
