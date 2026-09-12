"""Bounded Mario MDL0/CHR0 intermediate decoder. Not a native render package.

Format research: noclip.website src/rres/brres.ts (MIT), read 2026-09-09.
Independent implementation; original resource bytes are never bundled in source.
"""
import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import struct
from inspect_assets import unpack_u8
from character_mesh import attribute,commands,material

class Reader:
    def __init__(self,data):
        self.data=data
    def need(self,p,n):
        if p<0 or n<0 or p+n>len(self.data):raise ValueError('Resource offset/length out of bounds')
    def read(self,fmt,p):
        self.need(p,struct.calcsize('>'+fmt))
        values=struct.unpack_from('>'+fmt,self.data,p)
        if any(isinstance(v,float) and not math.isfinite(v) for v in values):raise ValueError('Nonfinite value')
        return values[0] if len(values)==1 else values
    def name(self,p):
        self.need(p,1)
        end=self.data.find(b'\0',p,min(p+256,len(self.data)))
        if end<0:raise ValueError('Unterminated resource name')
        try:return self.data[p:end].decode('ascii')
        except UnicodeDecodeError as e:raise ValueError('Non-ASCII resource name') from e
    def dic(self,p):
        if not p:return []
        size,n=self.read('II',p)
        if n>4096 or size<24+n*16:raise ValueError('Invalid resource dictionary')
        self.need(p,size)
        result=[]
        for i in range(n):
            name,offset=self.read('II',p+24+i*16+8)
            self.need(p+offset,1)
            result.append((self.name(p+name),p+offset))
        if len({n for n,_ in result})!=len(result):raise ValueError('Duplicate resource names')
        return result
    def resources(self):
        self.need(0,16)
        if self.data[:6]!=b'bres\xfe\xff' or self.read('I',8)!=len(self.data):raise ValueError('Invalid BRRES header')
        root=self.read('H',12)
        self.need(root,8)
        if self.data[root:root+4]!=b'root':raise ValueError('Missing root resource')
        return {name:self.dic(offset) for name,offset in self.dic(root+8)}
    def section(self,p,magic,version):
        self.need(p,16)
        size,v=self.read('II',p+4)
        if self.data[p:p+4]!=magic or v!=version or size<16:raise ValueError('Unsupported resource section/version')
        self.need(p,size)
        return p+size

def display_setup(data):
    """Read the bounded CP/XF setup subset used by Mario shapes."""
    r=Reader(data);p=0;cp={}
    while p<len(data):
        op=r.read('B',p);p+=1
        if op==0:continue
        if op==8:
            reg,value=r.read('BI',p);p+=5;cp[reg]=value
        elif op==0x10:
            count,address=r.read('HH',p);p+=4
            r.need(p,(count+1)*4);p+=(count+1)*4
        else:raise ValueError(f'Unsupported setup command {op:#x}')
    if not all(k in cp for k in (0x50,0x60,0x70)):raise ValueError('Missing vertex descriptors')
    if cp[0x70]&(1<<31):raise ValueError('NBT3 normals are not supported')
    lo,hi=cp[0x50],cp[0x60]
    return [(lo>>i)&1 for i in range(9)]+[(lo>>i)&3 for i in (9,11,13,15)]+[(hi>>(2*i))&3 for i in range(8)]

def primitives(data,descriptors):
    """Assemble triangle topology; preserve unresolved matrix loads per draw."""
    if len(descriptors)!=21 or descriptors[9] not in (2,3):raise ValueError('Indexed positions required')
    if any(t not in (0,1) for t in descriptors[:9]) or any(t not in (0,2,3) for t in descriptors[9:]):
        raise ValueError('Unsupported vertex attribute descriptor')
    r=Reader(data);p=0;vertices=[];triangles=[];draws=[];loads={}
    while p<len(data):
        op=r.read('B',p);p+=1
        if op==0:continue
        if op in (0x20,0x28,0x30,0x38):
            index,address=r.read('HH',p);p+=4
            loads[(op,address&0xfff)]=dict(command=op,index=index,address=address&0xfff,words=(address>>12)+1)
            continue
        if op not in (0x80,0x90,0x98,0xa0):raise ValueError(f'Unsupported primitive command {op:#x}')
        n=r.read('H',p);p+=2;start=len(vertices);first=len(triangles)
        if n<3 or (op==0x80 and n%4) or (op==0x90 and n%3) or start+n>100000:raise ValueError('Invalid primitive vertex count')
        for _ in range(n):
            v={}
            for attr,t in enumerate(descriptors):
                if t:
                    v[str(attr)]=r.read('H' if t==3 else 'B',p);p+=2 if t==3 else 1
            vertices.append(v)
        if op==0x90:local=[(i,i+1,i+2) for i in range(0,n,3)]
        elif op==0x80:local=[t for i in range(0,n,4) for t in ((i,i+1,i+2),(i,i+2,i+3))]
        elif op==0x98:local=[(i,i+1,i+2) if i%2==0 else (i+1,i,i+2) for i in range(n-2)]
        else:local=[(0,i,i+1) for i in range(1,n-1)]
        triangles.extend([[start+i for i in t] for t in local])
        draws.append(dict(first_triangle=first,triangle_count=len(local),matrix_loads=list(loads.values())))
    return dict(vertices=vertices,triangles=triangles,draws=draws)

def model(r,p):
    end=r.section(p,b'MDL0',11)
    def group(off):
        relative=r.read('I',p+off)
        if relative and (not p<=p+relative<end or p+relative+r.read('I',p+relative)>end):
            raise ValueError('Dictionary outside model section')
        entries=r.dic(p+relative) if relative else []
        if any(not p<=o<end for _,o in entries):raise ValueError('Model entry outside section')
        return entries
    nodes=group(0x14)
    if len(nodes)>256:raise ValueError('Skeleton capacity exceeded')
    offsets={off:i for i,(_,off) in enumerate(nodes)}
    bones=[]
    for name,off in nodes:
        if off+0xd0>end:raise ValueError('Truncated bone')
        parent=r.read('i',off+0x5c)
        if parent and off+parent not in offsets:raise ValueError('Unknown parent bone')
        bones.append(dict(name=name,id=r.read('I',off+12),matrix_id=r.read('I',off+16),
                          flags=r.read('I',off+20),parent=offsets[off+parent] if parent else -1,
                          scale=r.read('3f',off+0x20),rotation_degrees=r.read('3f',off+0x2c),
                          translation=r.read('3f',off+0x38),bind_matrix=r.read('12f',off+0x70),
                          inverse_bind_matrix=r.read('12f',off+0xa0)))
    for i in range(len(bones)):
        seen=set();current=i
        while current!=-1:
            if current in seen:raise ValueError('Cyclic skeleton')
            seen.add(current);current=bones[current]['parent']
    positions=[]
    for name,off in group(0x18):
        data=off+r.read('I',off+8)
        components,kind=r.read('II',off+0x14)
        shift,stride,count=r.read('BBH',off+0x1c)
        if components not in (0,1) or kind>4 or count>20000 or shift>31:raise ValueError('Unsupported positions')
        dims=components+2
        fmt=['B','b','H','h','f'][kind]
        length=struct.calcsize('>'+fmt)*dims
        if stride<length or data<p or data+stride*count>end:raise ValueError('Invalid position array')
        values=[]
        for i in range(count):
            v=list(r.read(fmt*dims,data+i*stride))
            if kind!=4:v=[x/(1<<shift) for x in v]
            if dims==2:v.append(0)
            values.append(v)
        positions.append(dict(name=name,values=values))
    arrays={}
    for key,offset in [('normal',0x1c),('color',0x20),('uv',0x24)]:
        arrays[key]=[dict(name=name,**attribute(r,off,end,key)) for name,off in group(offset)]
        if any(a['id']!=i for i,a in enumerate(arrays[key])):raise ValueError('Unexpected attribute buffer ID')
    shapes=[]
    for name,off in group(0x38):
        if off+0x68>end:raise ValueError('Truncated shape header')
        def dl(base):
            size,used,relative=r.read('III',off+base);start=off+base+relative
            if used>size or start<p or start+size>end:raise ValueError('Display list outside model')
            return r.data[start:start+used]
        topology=primitives(dl(0x24),display_setup(dl(0x18)))
        expected_v,expected_t=r.read('II',off+0x40)
        if len(topology['vertices'])!=expected_v or len(topology['triangles'])!=expected_t:
            raise ValueError('Shape topology count mismatch')
        ids=r.read('12h',off+0x48)
        if not 0<=ids[0]<len(positions):raise ValueError('Unknown position buffer')
        if any(v['9']>=len(positions[ids[0]]['values']) for v in topology['vertices']):raise ValueError('Position index outside buffer')
        for v in topology['vertices']:
            for attr_id,value in v.items():
                a=int(attr_id)
                if a<10:continue
                buffers=arrays['normal' if a==10 else 'color' if a<13 else 'uv']
                bid=ids[a-9]
                if not 0<=bid<len(buffers) or value>=len(buffers[bid]['values']):raise ValueError('Attribute index outside buffer')
        shapes.append(dict(name=name,matrix_id=r.read('i',off+8),attribute_buffer_ids=ids,**topology))
    scene={name:commands(r,off,end,name) for name,off in group(0x10)}
    materials=[dict(name=name,**material(r,off,end)) for name,off in group(0x30)]
    return dict(bones=bones,position_buffers=positions,attribute_buffers=arrays,materials=materials,scene=scene,
                shapes=shapes,limitation='Mesh attributes and scene commands decoded; rendering and material effects remain unimplemented.')

def track(r,p,kind,duration):
    if kind in (4,5,6):
        n=duration+1
        if kind==6:values=[r.read('f',p+4*i) for i in range(n)]
        else:
            scale,bias=r.read('2f',p)
            fmt='B' if kind==4 else 'H';stride=1 if kind==4 else 2
            values=[r.read(fmt,p+8+stride*i)*scale+bias for i in range(n)]
        return dict(type='linear',values=values)
    if kind not in (1,2,3):raise ValueError('Unsupported keyframe encoding')
    n=r.read('H',p)
    if not 0<n<=4096:raise ValueError('Invalid keyframe count')
    scale,bias=r.read('2f',p+8) if kind!=3 else (1,0)
    frames=[]
    for i in range(n):
        if kind==1:
            word=r.read('I',p+16+i*4)
            tangent=word&4095
            if tangent>=2048:tangent-=4096
            v=[word>>24,((word>>12)&4095)*scale+bias,tangent/32]
        elif kind==2:
            t,value,tangent=r.read('hHh',p+16+i*6)
            v=[t/32,value*scale+bias,tangent/256]
        else:v=list(r.read('3f',p+8+i*12))
        if v[0]<0 or v[0]>duration+1 or (frames and v[0]<=frames[-1][0]):raise ValueError('Invalid keyframe order/time')
        frames.append(v)
    return dict(type='hermite',keys=frames)

def sample(t,frame):
    if t['type']=='linear':
        v=t['values'];f=max(0,min(frame,len(v)-1));i=int(f)
        return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(f-i)
    keys=t['keys'];i=bisect.bisect_right([k[0] for k in keys],frame)
    if i==0:return keys[0][1]
    if i==len(keys):return keys[-1][1]
    a,b=keys[i-1],keys[i];length=b[0]-a[0];u=(frame-a[0])/length
    return (2*u**3-3*u*u+1)*a[1]+(u**3-2*u*u+u)*length*a[2]+(-2*u**3+3*u*u)*b[1]+(u**3-u*u)*length*b[2]

def animation(r,p):
    end=r.section(p,b'CHR0',5)
    duration,count=r.read('HH',p+0x20)
    if duration>4096:raise ValueError('Animation too long')
    entries=r.dic(p+r.read('I',p+16))
    if len(entries)!=count or count>256:raise ValueError('Animation node count mismatch')
    result=[]
    for name,off in entries:
        if not p<=off<end:raise ValueError('Animation node outside section')
        flags=r.read('I',off+4);cursor=off+8;channels={}
        def next_track(kind,constant):
            nonlocal cursor
            if cursor+4>end:raise ValueError('Animation channel outside section')
            if constant or kind==0:t=dict(type='linear',values=[r.read('f',cursor)])
            else:
                tp=off+r.read('I',cursor)
                if not p<=tp<end:raise ValueError('Animation track outside section')
                # Track reads must stay within the CHR0 section, even when strings live outside it.
                t=track(Reader(r.data[:end]),tp,kind,duration)
            cursor+=4
            return t
        masks=[(1<<1)|(1<<3)|(1<<7),(1<<1)|(1<<2)|(1<<5)|(1<<8),(1<<1)|(1<<2)|(1<<6)|(1<<9)]
        for group,field,fmt,const_base in [(0,'scale',(flags>>25)&3,13),(1,'rotation',(flags>>27)&7,16),(2,'translation',(flags>>30)&3,19)]:
            if flags&masks[group]:continue
            uniform=group==0 and bool(flags&(1<<4))
            vals=[next_track(fmt,bool(flags&(1<<(const_base+i)))) for i in range(1 if uniform else 3)]
            if uniform:vals*=3
            for axis,t in zip('xyz',vals):channels[field+'_'+axis]=t
        result.append(dict(name=name,flags=flags,channels=channels))
    return dict(duration=duration,loop=r.read('I',p+0x24),scaling_rule=r.read('I',p+0x28),nodes=result)

def convert(extracted,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new output separate from extracted source')
    boot=(extracted/'sys/boot.bin').read_bytes()
    if boot[:8]!=b'SMNE01\0\2' or boot[24:28]!=bytes.fromhex('5d1c9ea3'):raise ValueError('Unexpected source disc header')
    readers={};hashes={}
    for name in ('Mario','P_rcha'):
        raw=(extracted/f'files/Object/{name}.arc').read_bytes();hashes[name]=hashlib.sha256(raw).hexdigest()
        readers[name]=Reader(unpack_u8(raw)['g3d/model.brres'])
    models={name:model(readers['Mario'],off) for name,off in readers['Mario'].resources()['3DModels(NW4R)']}
    clips={name:animation(readers['P_rcha'],off) for name,off in readers['P_rcha'].resources()['AnmChr(NW4R)']}
    summaries=[]
    for name,clip in clips.items():
        values=[sample(t,f) for n in clip['nodes'] for t in n['channels'].values() for f in (0,clip['duration']/2,clip['duration'])]
        if not all(math.isfinite(v) for v in values):raise ValueError('Invalid sampled animation')
        summaries.append(dict(name=name,duration=clip['duration'],nodes=len(clip['nodes'])))
    report=dict(format='character-intermediate',version=3,native_ready=False,source_sha256=hashes,
                models={n:dict(bones=len(m['bones']),positions=sum(len(b['values']) for b in m['position_buffers']),shapes=len(m['shapes']),triangles=sum(len(s['triangles']) for s in m['shapes'])) for n,m in models.items()},
                animations=summaries,limitations=['Triangle topology and skin weights decoded; character_pose.py evaluates rigid and weighted matrices.',
                'Base material samplers and attribute arrays decoded; full Wii material effects are not reproduced.',
                'General parent scale compensation remains unsupported; rigid and weighted poses use character_pose.py.',
                'This intermediate format is not loaded on 3DS; package_character.py produces an optional baked sprite atlas.'])
    output.mkdir(parents=True)
    (output/'models.json').write_text(json.dumps(models,separators=(',',':'))+'\n')
    (output/'animations.json').write_text(json.dumps(clips,separators=(',',':'))+'\n')
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('extracted',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        report=convert(a.extracted,a.output)
        print(json.dumps({'models':report['models'],'animation_clips':len(report['animations']),'native_ready':False},indent=2))
    except (ValueError,OSError,KeyError) as e:p.exit(1,f'Character conversion failed: {e}\n')
