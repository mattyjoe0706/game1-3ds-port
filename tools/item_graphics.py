"""Bake the original mushroom pickups; no generated assets in the repository."""
from pathlib import Path
from inspect_assets import unpack_u8
from convert_character import Reader,model
from character_texture import textures
from preview_character import render
from gpu_texture import rgba8_tiles

def bake(extracted):
    from PIL import Image
    atlas=Image.new('RGBA',(128,64))
    for index,name in enumerate(('I_kinoko','I_propeller')):
        entries=unpack_u8((Path(extracted)/f'files/Object/{name}.arc').read_bytes())
        r=Reader(entries[f'g3d/{name}.brres'])
        models={n:model(r,p) for n,p in r.resources()['3DModels(NW4R)']}
        m=next(iter(models.values()))
        names={s['texture'] for mat in m['materials'] for s in mat['samplers'] if s['slot']==0}
        im=render({'MB_model':m},{},textures(r,names),size=128,solo=True)
        bounds=im.getbbox()
        if not bounds or bounds[0]==0 or bounds[1]==0 or bounds[2]==128 or bounds[3]==128:
            raise ValueError('Item model exceeds preview bounds')
        # Fit each pickup into a padded cell; keep original aspect ratio.
        crop=im.crop(bounds);crop.thumbnail((56,56),Image.Resampling.LANCZOS)
        atlas.alpha_composite(crop,(index*64+(64-crop.width)//2,(64-crop.height)//2))
    return atlas,rgba8_tiles(atlas.tobytes(),128,64)
