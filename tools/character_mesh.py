"""Bounded MDL0 attribute and scene-command conversion helpers."""
import struct

def attribute(r,off,end,category):
    if off+32>end:raise ValueError('Truncated attribute header')
    start=off+r.read('I',off+8)
    components,kind=r.read('II',off+20)
    shift,stride,count=r.read('BBH',off+28)
    if count>20000:raise ValueError('Attribute capacity exceeded')
    if category=='color':
        if kind!=5 or components!=1:raise ValueError('Only RGBA8 character colors supported')
        stride=shift;shift=0;dims=4;fmt='B'
    else:
        if kind>4 or components not in (0,1):raise ValueError('Unsupported character attribute')
        if category=='normal' and components!=0:raise ValueError('NBT normals unsupported')
        dims=3 if category=='normal' else components+1
        fmt=['B','b','H','h','f'][kind]
    width=struct.calcsize('>'+fmt)*dims
    if stride<width or shift>31 or start<off or start+stride*count>end:raise ValueError('Invalid attribute array')
    values=[]
    for i in range(count):
        v=r.read(fmt*dims,start+stride*i)
        if dims==1:v=[v]
        if category!='color' and kind!=4:v=[x/(1<<shift) for x in v]
        values.append(list(v))
    return dict(id=r.read('I',off+16),values=values)

def commands(r,p,end,kind):
    out=[]
    allowed={'NodeTree':(2,6),'NodeMix':(3,5),'DrawOpa':(4,),'DrawXlu':(4,)}
    if kind not in allowed:raise ValueError('Unknown scene command stream')
    def take(fmt):
        nonlocal p
        size=struct.calcsize('>'+fmt)
        if p+size>end:raise ValueError('Truncated scene command')
        v=r.read(fmt,p);p+=size;return v
    for _ in range(4096):
        op=take('B')
        if op==1:return out
        if op not in allowed[kind]:raise ValueError('Unsupported scene command')
        if op in (2,5,6):out.append(dict(op=op,args=take('HH')))
        elif op==4:out.append(dict(op=op,args=take('HHHB')))
        else:
            dst,n=take('HB')
            if not 0<n<=32:raise ValueError('Invalid matrix blend count')
            pairs=[take('Hf') for _ in range(n)]
            if any(w<0 or w>1 for _,w in pairs) or abs(sum(w for _,w in pairs)-1)>0.001:
                raise ValueError('Invalid matrix blend weights')
            out.append(dict(op=op,destination=dst,weights=pairs))
    raise ValueError('Scene command capacity exceeded')

def material(r,off,end):
    if off+0x34>end:raise ValueError('Truncated material')
    n,relative=r.read('II',off+0x2c);samplers=[]
    if n>8 or off+relative+n*0x34>end:raise ValueError('Invalid sampler table')
    for i in range(n):
        p=off+relative+i*0x34;tex,palette=r.read('II',p)
        samplers.append(dict(texture=r.name(p+tex),palette=r.name(p+palette) if palette else None,
                             slot=r.read('I',p+16),wrap=r.read('II',p+24),filters=r.read('II',p+32)))
    return dict(id=r.read('I',off+12),flags=r.read('I',off+16),cull=r.read('I',off+24),samplers=samplers)
