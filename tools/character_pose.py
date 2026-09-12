"""Rigid and weighted MDL0 poses. Unsupported scale modes fail explicitly."""
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

def player_animation_values(bone,values,form,penguin_hand_animation=False):
    """USA rev-2 player callback 0x800d4d80; ordinary Mario scale table
    0x802f1100 selected by 0x800caa70. Special action flags remain separate.
    """
    factors={'super':1.,'small':0.5460000038146973,'propeller':1.,'penguin':0.7200000286102295}
    if form not in factors:raise ValueError('Unsupported player binding form')
    if bone['id']==1:values[2]=[v*factors[form] for v in values[2]]
    elif bone['id']!=0:
        values[2]=list(bone['translation'])
        if form=='penguin' and bone['id'] in (11,14) and not penguin_hand_animation:
            values[0]=list(bone['scale']);values[1]=list(bone['rotation_degrees'])
    return values


def pose(model,clip=None,frame=0,*,player_form=None,penguin_hand_animation=False):
    # Import late to avoid a cycle when conversion invokes validation.
    from convert_character import sample
    tracks={n['name']:n for n in clip['nodes']} if clip else {}
    matrices={0:IDENTITY};scales={0:[1,1,1]};by_id={b['id']:b for b in model['bones']}
    for op in model['scene']['NodeTree']:
        if op['op']==6:
            dst,src=op['args'];matrices[dst]=matrices[src]
            scales[dst]=scales[src]
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
        if clip is not None and player_form is not None:
            values=player_animation_values(bone,values,player_form,penguin_hand_animation)
        compensate=bool(node['flags']&(1<<10)) if node else bool(bone.get('flags',0)&(1<<5))
        if node and node['flags']&(1<<12):raise ValueError('Unsupported XSI scaling')
        local=srt(*values)
        if compensate:
            # Maya SSC cancels the immediate parent's local scale in the
            # child's linear transform, while retaining scaled translation.
            for row,scale in enumerate(scales[parent]):
                if not math.isfinite(scale) or abs(scale)<1e-12:raise ValueError('Singular parent scale')
                for col in range(3):local[row*4+col]/=scale
        matrices[bone['matrix_id']]=multiply(matrices[parent],local)
        scales[bone['matrix_id']]=values[0]
    apply_node_mix(model,matrices)
    return matrices

def apply_node_mix(model,matrices):
    """EVPMTX builds skin matrices; NODEMIX blends them into the draw palette.

    Keep the envelope scratch palette separate from the joint/draw palette.
    Format reference: noclip.website src/rres/render.ts execNodeMixOpList.
    """
    scratch={};bones={b['id']:b for b in model['bones']}
    for op in model['scene'].get('NodeMix',[]):
        if op['op']==5:
            mid,bid=op['args']
            if mid not in matrices or bid not in bones:raise ValueError('Unknown envelope matrix or bone')
            scratch[mid]=multiply(matrices[mid],bones[bid]['inverse_bind_matrix'])
        elif op['op']==3:
            weights=op['weights']
            if not weights or any(not math.isfinite(w) or w<0 or w>1 for _,w in weights) or abs(sum(w for _,w in weights)-1)>0.001:
                raise ValueError('Invalid skin weights')
            if any(mid not in scratch for mid,_ in weights):raise ValueError('Unresolved skin matrix')
            matrices[op['destination']]=[sum(scratch[mid][i]*weight for mid,weight in weights) for i in range(12)]
        else:raise ValueError('Unsupported skinning command')

def texture_uv(uv,sampler):
    """Apply the stored Maya-mode texture transform before texture wrapping."""
    transform=sampler.get('srt')
    if transform is None:return uv  # Older intermediate files lack SRT data.
    if transform['mode']!=0:raise ValueError('Unsupported texture matrix mode')
    sx,sy=transform['scale'];tx,ty=transform['translation']
    angle=math.radians(transform['rotation']);c=math.cos(angle);s=math.sin(angle)
    u,v=uv
    return [sx*(c*(u-.5)+s*(v-.5)+.5-tx),
            sy*(-s*(u-.5)+c*(v-.5)-.5+ty)+1]

def headwear_hidden_materials(model,wearing_cap):
    """Select the cap or exposed hair; None preserves raw resource inspection."""
    names={m['name'] for m in model['materials']}
    if wearing_cap is None or not {'mat_player_hat','mat_player_hair'}<=names:return set()
    return {'mat_player_hair' if wearing_cap else 'mat_player_hat'}


def mesh(model,matrices,attachment=IDENTITY,*,wearing_cap=None):
    """Yield material and textured triangle corners in posed model space."""
    hidden=headwear_hidden_materials(model,wearing_cap)
    for cmd in model['scene'].get('DrawOpa',[])+model['scene'].get('DrawXlu',[]):
        if model['materials'][cmd['args'][0]]['name'] in hidden:continue
        material,shape_id,node_id,priority=cmd['args'];shape=model['shapes'][shape_id]
        sampler=next(s for s in model['materials'][material]['samplers'] if s['slot']==0)
        ids=shape['attribute_buffer_ids'];positions=model['position_buffers'][ids[0]]['values']
        uv=model['attribute_buffers']['uv'][ids[4]]['values']
        colors=model['attribute_buffers']['color'][ids[2]]['values'] if ids[2]>=0 else None
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
                    corners.append(dict(position=point(transform,positions[v['9']]),uv=texture_uv(uv[v['13']],sampler),
                                        color=colors[v['11']] if colors is not None else [255,255,255,255]))
                yield material,corners
