"""Bake Small/Super/Propeller sprites from original assets for World 1-1."""
import argparse,json,hashlib,struct
from pathlib import Path
from PIL import Image
from inspect_assets import unpack_u8
from convert_character import Reader,model,animation
from character_texture import textures
from package_character import FRAMES,swizzle
from preview_character import render
from convert_course import fnv1a

def package(extracted,output):
    extracted=Path(extracted).resolve();output=Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:raise ValueError('Choose a new separate output folder')
    if (extracted/'sys/boot.bin').read_bytes()[:8]!=b'SMNE01\0\2':raise ValueError('Expected USA rev 2')
    raw=(extracted/'files/Object/Mario.arc').read_bytes();r=Reader(unpack_u8(raw)['g3d/model.brres'])
    models={n:model(r,p) for n,p in r.resources()['3DModels(NW4R)']}
    araw=(extracted/'files/Object/P_rcha.arc').read_bytes();ar=Reader(unpack_u8(araw)['g3d/model.brres'])
    clips={n:animation(ar,p) for n,p in ar.resources()['AnmChr(NW4R)']};tex=textures(r)
    output.mkdir(parents=True);target=output/'3ds/nsmbw-prototype/data';target.mkdir(parents=True)
    report={'source_sha256':{'Mario':hashlib.sha256(raw).hexdigest(),'P_rcha':hashlib.sha256(araw).hexdigest()},'forms':{},'native_validated':False}
    for form,bn,hn,stem in [('super','MB_model','MH_model','mario'),('small','SMB_model','SMH_model','mario-small'),('propeller','PLMB_model','PLMH_model','mario-propeller')]:
        pair={'MB_model':models[bn],'MH_model':models[hn]};atlas=Image.new('RGBA',(512,256))
        for i,(clip,frame) in enumerate(FRAMES):
            im=render(pair,clips,tex,clip,frame,128,player_form=form)
            box=im.getbbox()
            if not box or box[0]==0 or box[1]==0 or box[2]==128 or box[3]==128:raise ValueError(f'{form} {clip} {frame} exceeds cell')
            atlas.paste(im.resize((64,64),Image.Resampling.LANCZOS),((i%8)*64,(i//8)*64))
        atlas.save(output/(stem+'-atlas.png'));data=swizzle(atlas)
        header=struct.pack('<4s6I',b'NSP1',1,512,256,64,len(FRAMES),fnv1a(data));header+=struct.pack('<I',fnv1a(header))
        (target/(stem+'.nsp')).write_bytes(header);(target/(stem+'.rgba')).write_bytes(data)
        report['forms'][form]={'stem':stem,'frames':FRAMES,'texture_bytes':len(data),'texture_fnv':fnv1a(data),'body':bn,'head':hn}
        print('PACKAGED',form,flush=True)
    report['limitations']=['Baked sprites; no Wii TEV lighting or facial animation.','Single airborne pose and compressed crouch remain; propeller rotor animation is pending.','Original special-action root-scale flags and transition blending are not implemented.','No native compilation or hardware acceptance yet.']
    (output/'manifest.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('extracted',type=Path);p.add_argument('output',type=Path);a=p.parse_args();package(a.extracted,a.output)
