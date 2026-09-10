"""Local opening Rolling Hill conversion. Original assets stay outside Git.

Actor fields independently decoded using Reggie Next's spritedata.xml.
The opening instance has speed zero; other instances are deliberately rejected.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from convert_character import Reader, model
from character_pose import mesh, pose
from character_texture import textures
from convert_course import fnv1a
from inspect_assets import unpack_u8, course_blocks
from gpu_texture import rgba8_tiles


def opening_actor(course):
    info=course_blocks(course)[7]
    block=course[info['offset']:info['offset']+info['bytes']]
    found=[]
    for p in range(0,len(block)-15,16):
        actor,x,y=struct.unpack_from('>HHH',block,p)
        if actor==212 and 496<=x<1904:
            settings=struct.unpack_from('>I',block,p+8)[0]
            if (x,y,settings)!=(1456,544,0x01301801):
                raise ValueError('Unverified opening hill configuration')
            found.append((x,y,settings))
    if len(found)!=1:raise ValueError('Expected exactly one opening hill')
    return found[0]


def render(r,size=512):
    import numpy as np
    from PIL import Image
    m=model(r,dict(r.resources()['3DModels(NW4R)'])['circle_ground_L'])
    tex=textures(r)
    image=np.zeros((size,size,4),dtype=np.uint8)
    # The original planar model is radius 400 in XY; +Y is upward.
    for material,tri in mesh(m,pose(m)):
        sampler=next(s for s in m['materials'][material]['samplers'] if s['slot']==0)
        tw,th,rgba=tex[sampler['texture']]
        texture=np.frombuffer(rgba,dtype=np.uint8).reshape(th,tw,4)
        pts=np.array([v['position'] for v in tri])
        if np.max(np.abs(pts[:,:2]))>400.01 or np.max(np.abs(pts[:,2]))>0.01:
            raise ValueError('Unexpected circle model bounds')
        projected=np.stack(((pts[:,0]+400)*size/800,(400-pts[:,1])*size/800),axis=1)
        a,b,c=projected
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8:continue
        lo=np.maximum(np.floor(projected.min(axis=0)).astype(int),0)
        hi=np.minimum(np.ceil(projected.max(axis=0)).astype(int),size-1)
        if np.any(lo>hi):continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];x=xx+.5;y=yy+.5
        w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        weights=np.stack((w0,w1,1-w0-w1),axis=-1)
        mask=weights.min(axis=-1)>=-1e-7
        uv=weights@np.array([v['uv'] for v in tri])
        for axis,wrap in enumerate(sampler['wrap']):
            t=uv[:,:,axis]
            uv[:,:,axis]=np.clip(t,0,1) if wrap==0 else (t%1 if wrap==1 else 1-np.abs(t%2-1))
        tx=np.minimum((uv[:,:,0]*tw).astype(int),tw-1)
        ty=np.minimum((uv[:,:,1]*th).astype(int),th-1)
        image[yy[mask],xx[mask]]=texture[ty[mask],tx[mask]]
    return Image.fromarray(image)


def encode(terrain,texture):
    if len(terrain)<36 or terrain[:4]!=b'NST1' or struct.unpack_from('<II',terrain,12)!=(1408,320):
        raise ValueError('Expected the matching opening-section terrain package')
    # Editor anchor is top-centre with the standard half-tile X offset.
    # Local centre (968,560), radius 400. Only the upper cap within the crop
    # participates; the lower half must never become a platform underside.
    segments=[]
    for x in range(648,1288,4):
        heights=[560-math.sqrt(400**2-(v-968)**2) for v in (x,x+4)]
        segments.append((x,4,*heights))
    body=b''.join(struct.pack('<4f',*s) for s in segments)
    head=struct.pack('<4s6I',b'NSH1',1,fnv1a(terrain),fnv1a(texture),568,160,len(segments))
    return head+struct.pack('<I',fnv1a(head+body))+body


def package(extracted,terrain_path,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new directory separate from extraction')
    stage=unpack_u8((extracted/'files/Stage/01-01.arc').read_bytes())
    actor=opening_actor(stage['course/course1.bin'])
    raw=(extracted/'files/Object/circle_ground.arc').read_bytes()
    r=Reader(unpack_u8(raw)['g3d/circle_ground.brres'])
    im=render(r);texture=rgba8_tiles(im.tobytes(),512,512)
    data=encode(Path(terrain_path).read_bytes(),texture)
    output.mkdir(parents=True)
    im.save(output/'hill-preview.png')
    target=output/'data';target.mkdir()
    (target/'hill.nsh').write_bytes(data);(target/'hill.rgba').write_bytes(texture)
    report={'actor':212,'source_position':actor[:2],'settings':hex(actor[2]),
            'model':'circle_ground_L','radius':400,'rotation_implemented':False,
            'texture_bytes':len(texture),'source_sha256':hashlib.sha256(raw).hexdigest(),
            'limitations':['Anchor inferred from editor geometry; verify against Wii footage.',
                          'Upper circle support approximated with four-unit chords.',
                          'Speed-zero opening instance only; moving variants unsupported.',
                          'No hardware performance claim.']}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    print(json.dumps(package(a.extracted,a.terrain,a.output),indent=2))
