"""Bake original Mario poses to an optional NSP1 sprite package. Requires NumPy/Pillow."""
import argparse,hashlib,json,struct
from pathlib import Path
from PIL import Image
from convert_character import convert,Reader
from inspect_assets import unpack_u8
from character_texture import textures
from preview_character import render
from gpu_texture import rgba8_tiles
from convert_course import fnv1a

FRAMES=[('wait',i*40) for i in range(4)]+[('walk',i*59/8) for i in range(8)]+[('run',i*60/8) for i in range(8)]+[('jumped',5)]

def swizzle(image):
    return rgba8_tiles(image.tobytes(),*image.size)

def package(extracted,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    # convert validates source revision and rejects existing/overlapping output.
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new output separate from extraction')
    convert(extracted,output/'intermediate')
    models=json.loads((output/'intermediate/models.json').read_text());clips=json.loads((output/'intermediate/animations.json').read_text())
    raw=(extracted/'files/Object/Mario.arc').read_bytes()
    manifest=json.loads((output/'intermediate/manifest.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=manifest['source_sha256']['Mario']:raise ValueError('Mario source changed during conversion')
    tex=textures(Reader(unpack_u8(raw)['g3d/model.brres']))
    atlas=Image.new('RGBA',(512,256))
    for i,(clip,frame) in enumerate(FRAMES):
        # Supersample offline; runtime uses one small sprite draw.
        im=render(models,clips,tex,clip,frame,128)
        box=im.getbbox()
        if not box or box[0]==0 or box[1]==0 or box[2]==128 or box[3]==128:raise ValueError('Character pose exceeds sprite cell')
        im=im.resize((64,64),Image.Resampling.LANCZOS)
        atlas.paste(im,((i%8)*64,(i//8)*64))
    atlas.save(output/'mario-atlas.png');raw=swizzle(atlas)
    header=struct.pack('<4s6I',b'NSP1',1,512,256,64,len(FRAMES),fnv1a(raw))
    header+=struct.pack('<I',fnv1a(header))
    target=output/'SD-ROOT/3ds/nsmbw-prototype/data';target.mkdir(parents=True)
    (target/'mario.nsp').write_bytes(header);(target/'mario.rgba').write_bytes(raw)
    report=dict(format='NSP1',version=1,packing_revision=2,frames=FRAMES,texture_bytes=len(raw),source_sha256=manifest['source_sha256'],
                files={n:hashlib.sha256((target/n).read_bytes()).hexdigest() for n in ('mario.nsp','mario.rgba')},
                limitations=['Baked 2D poses from original model, simplified base-texture materials.',
                             'Air uses one pose; crouch scales the idle sprite. No facial animation.',
                             'Native compilation and hardware performance still require validation.'])
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('extracted',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    try:print(json.dumps(package(a.extracted,a.output),indent=2))
    except (ValueError,OSError,KeyError) as e:p.exit(1,f'Character package failed: {e}\n')
