"""Offline textured Mario pose preview; requires NumPy and Pillow. No Wii TEV effects."""
import argparse,json,math
from pathlib import Path
import numpy as np
from PIL import Image
from convert_character import Reader
from inspect_assets import unpack_u8
from character_texture import textures
from character_pose import pose,mesh

def render(models,clips,tex,clip='wait',frame=0,size=256):
    body=models['MB_model'];head=models['MH_model'];matrices=pose(body,clips[clip],frame)
    attach=matrices[next(b['matrix_id'] for b in body['bones'] if b['name']=='face_1')]
    objects=[(body,mesh(body,matrices)),(head,mesh(head,pose(head),attach))]
    image=np.zeros((size,size,4),dtype=np.uint8);depth=np.full((size,size),-np.inf)
    # Three-quarter orthographic view: forward +Z projects right.
    angle=math.radians(65);ca,sa=math.cos(angle),math.sin(angle);scale=size/48
    for model,triangles in objects:
        for material,tri in triangles:
            sampler=next(s for s in model['materials'][material]['samplers'] if s['slot']==0)
            tw,th,rgba=tex[sampler['texture']];texture=np.frombuffer(rgba,dtype=np.uint8).reshape(th,tw,4)
            points=np.array([v['position'] for v in tri]);px=points[:,0]*ca+points[:,2]*sa;pz=-points[:,0]*sa+points[:,2]*ca
            projected=np.stack((size/2+px*scale,size*15/16-points[:,1]*scale),axis=1)
            a,b,c=projected;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-8:continue
            lo=np.maximum(np.floor(projected.min(axis=0)).astype(int),0);hi=np.minimum(np.ceil(projected.max(axis=0)).astype(int),size-1)
            if np.any(lo>hi):continue
            yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];x=xx+.5;y=yy+.5
            w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
            w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
            weights=np.stack((w0,w1,w2),axis=-1);z=weights@pz
            mask=(weights.min(axis=-1)>=-1e-7)&(z>depth[yy,xx])
            uv=weights@np.array([v['uv'] for v in tri])
            for axis,wrap in enumerate(sampler['wrap']):
                t=uv[:,:,axis]
                uv[:,:,axis]=np.clip(t,0,1) if wrap==0 else (t%1 if wrap==1 else 1-np.abs(t%2-1))
            tx=np.minimum((uv[:,:,0]*tw).astype(int),tw-1);ty=np.minimum((uv[:,:,1]*th).astype(int),th-1)
            color=texture[ty,tx].copy();mask&=color[:,:,3]>0
            # Simplified base texture only; GX light maps and TEV remain omitted.
            image[yy[mask],xx[mask]]=color[mask];depth[yy[mask],xx[mask]]=z[mask]
    return Image.fromarray(image)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('intermediate',type=Path);p.add_argument('extracted',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    if a.output.exists():p.error('Choose a new output file')
    models=json.loads((a.intermediate/'models.json').read_text());clips=json.loads((a.intermediate/'animations.json').read_text())
    tex=textures(Reader(unpack_u8((a.extracted/'files/Object/Mario.arc').read_bytes())['g3d/model.brres']))
    canvas=Image.new('RGBA',(1024,256),(40,48,64,255))
    for i,(clip,frame) in enumerate([('wait',0),('walk',15),('run',30),('jumped',5)]):
        im=render(models,clips,tex,clip,frame);canvas.alpha_composite(im,(i*256,0))
    a.output.parent.mkdir(parents=True,exist_ok=True);canvas.convert('RGB').save(a.output)
