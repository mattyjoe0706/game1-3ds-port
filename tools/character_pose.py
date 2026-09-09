"""Rigid-bone Mario pose evaluation. Unsupported scale modes fail explicitly."""
import math

IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0]

def multiply(a,b):
    return [sum(a[row*4+k]*b[k*4+col] for k in range(3))+(a[row*4+3] if col==3 else 0)
            for row in range(3) for col in range(4)]

def point(m,p):
    return [sum(m[row*4+k]*p[k] for k in range(3))+m[row*4+3] for row in range(3)]

def srt(scale,rotation,translation):
    x,y,z=[math.radians(v) for v in rotation]
    cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    rx=[1,0,0,0,0,cx,-sx,0,0,sx,cx,0]
    ry=[cy,0,sy,0,0,1,0,0,-sy,0,cy,0]
    rz=[cz,-sz,0,0,sz,cz,0,0,0,0,1,0]
    m=multiply(multiply(rz,ry),rx)
    for row in range(3):
        for col in range(3):m[row*4+col]*=scale[col]
        m[row*4+3]=translation[row]
    return m

def pose(model,clip=None,frame=0):
    # Import late to avoid a cycle when conversion invokes validation.
    from convert_character import sample
    tracks={n['name']:n for n in clip['nodes']} if clip else {}
    matrices={0:IDENTITY};scaled=set();by_id={b['id']:b for b in model['bones']}
    for op in model['scene']['NodeTree']:
        if op['op']==6:
            dst,src=op['args'];matrices[dst]=matrices[src]
            if src in scaled:scaled.add(dst)
            continue
        bid,parent=op['args'];bone=by_id[bid]
        values=[list(bone[k]) for k in ('scale','rotation_degrees','translation')]
        node=tracks.get(bone['name'])
        if node:
            flags=node['flags']
            for g,field in enumerate(('scale','rotation','translation')):
                zero=bool(flags&(1<<1)) or (g>0 and bool(flags&(1<<2))) or bool(flags&(1<<(3 if g==0 else 5 if g==1 else 6)))
                if zero:values[g]=[1 if g==0 else 0]*3
                for axis,key in enumerate('xyz'):
                    channel=node['channels'].get(field+'_'+key)
                    if channel:values[g][axis]=sample(channel,frame)
        if parent in scaled:raise ValueError('Scaled parent needs compensation support')
        if any(abs(v-1)>1e-5 for v in values[0]):scaled.add(bone['matrix_id'])
        matrices[bone['matrix_id']]=multiply(matrices[parent],srt(*values))
    if model['scene'].get('NodeMix'):raise ValueError('Blended skinning not implemented')
    return matrices

def mesh(model,matrices,attachment=IDENTITY):
    """Yield material and textured triangle corners in posed model space."""
    for cmd in model['scene'].get('DrawOpa',[])+model['scene'].get('DrawXlu',[]):
        material,shape_id,node_id,priority=cmd['args'];shape=model['shapes'][shape_id]
        ids=shape['attribute_buffer_ids'];positions=model['position_buffers'][ids[0]]['values']
        uv=model['attribute_buffers']['uv'][ids[4]]['values']
        colors=model['attribute_buffers']['color'][ids[2]]['values']
        for draw in shape['draws']:
            palette={l['address']//12:l['index'] for l in draw['matrix_loads'] if l['command']==0x20 and l['words']==12 and l['address']%12==0}
            for tri in shape['triangles'][draw['first_triangle']:draw['first_triangle']+draw['triangle_count']]:
                corners=[]
                for index in tri:
                    v=shape['vertices'][index];mid=shape['matrix_id']
                    if mid<0:
                        if v['0']%3:raise ValueError('Unaligned position matrix index')
                        mid=palette[v['0']//3]
                    transform=multiply(attachment,matrices[mid])
                    corners.append(dict(position=point(transform,positions[v['9']]),uv=uv[v['13']],color=colors[v['11']]))
                yield material,corners
