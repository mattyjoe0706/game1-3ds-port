import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from character_pose import texture_uv

class TextureUVTests(unittest.TestCase):
    def sampler(self,scale=(1,1),rotation=0,translation=(0,0)):
        return {'srt':{'mode':0,'scale':scale,'rotation':rotation,'translation':translation}}
    def test_eye_mirror_layout(self):
        # Original half-face texture repeats mirrored over the two face halves.
        sampler=self.sampler((2,1))
        self.assertEqual(texture_uv((.25,.4),sampler),[.5,.4])
        self.assertEqual(texture_uv((.75,.4),sampler),[1.5,.4])
        for u in (.25,.75):
            mapped=texture_uv((u,.4),sampler)[0]
            self.assertEqual(1-abs(mapped%2-1),.5)
    def test_identity_and_legacy(self):
        for uv in ((0,0),(1,1),(-.1,1.2)):
            self.assertEqual(texture_uv(uv,{}),uv)
            for x,y in zip(texture_uv(uv,self.sampler()),uv):self.assertAlmostEqual(x,y)
    def test_maya_pivot_rotation_translation(self):
        self.assertAlmostEqual(texture_uv((1,1),self.sampler(rotation=90))[1],0)
        self.assertEqual(texture_uv((.5,.5),self.sampler(translation=(.25,.125))),[.25,.625])
    def test_unknown_mode_fails(self):
        sampler=self.sampler();sampler['srt']['mode']=99
        with self.assertRaises(ValueError):texture_uv((0,0),sampler)

if __name__=='__main__':unittest.main()
