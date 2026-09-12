"""Decode original block-content bits and package opening interactions locally."""
import argparse,hashlib,json,struct
from pathlib import Path
from inspect_assets import unpack_u8
from convert_course import decode_course,fnv1a
from convert_tiles import definition,expand


def inventory(extracted):
    ext=Path(extracted)
    boot=(ext/'sys/boot.bin').read_bytes()
    if boot[:8]!=b'SMNE01\0\2':raise ValueError('Expected USA rev-2 source')
    arc=unpack_u8((ext/'files/Stage/01-01.arc').read_bytes())
    result=[];actors=[]
    for area in range(1,5):
        prefix=f'course/course{area}'
        if prefix+'.bin' not in arc:continue
        course=decode_course(arc[prefix+'.bin'],{i:arc[prefix+f'_bgdatL{i}.bin'] for i in range(3) if prefix+f'_bgdatL{i}.bin' in arc})
        tables=[]
        for name in course['tilesets']:
            if not name:tables.append([]);continue
            a=unpack_u8((ext/f'files/Stage/Texture/{name}.arc').read_bytes())
            tables.append([definition(a[f'BG_unt/{name}.bin'],off,True)
                           for off,w,h in struct.iter_unpack('>HBB',a[f'BG_unt/{name}_hd.bin'])])
        cells={}
        for obj in course['records']:
            if obj['kind']==1:actors.append(dict(area=area,**obj));continue
            if obj['kind']!=0:continue
            slot,num=obj['id']>>12,obj['id']&4095
            for dy,row in enumerate(expand(tables[slot][num],obj['w']//16,obj['h']//16)):
                for dx,t in enumerate(row):
                    if t is not None and t&1023:
                        cells[obj['layer'],obj['x']+dx*16,obj['y']+dy*16]=(t&1023,t>>10,num)
        for (layer,x,y),(tile,contents,obj) in cells.items():
            if layer==1 and (tile in (48,49,30) or 3<=tile<=13 or contents):
                result.append(dict(area=area,x=x,y=y,tile=tile,contents=contents,object=obj))
    return result,actors


def encode(records,actors,terrain,texture_hash=0):
    if len(terrain)<36 or terrain[:4]!=b'NST1' or struct.unpack_from('<I',terrain,4)[0]!=1:
        raise ValueError('Expected NST1')
    count=struct.unpack_from('<I',terrain,8)[0]
    if len(terrain)!=36+count*12 or struct.unpack_from('<4I',terrain,12)!=(1408,320,256,192):
        raise ValueError('Unexpected opening terrain')
    if fnv1a(terrain[:32]+terrain[36:])!=struct.unpack_from('<I',terrain,32)[0]:raise ValueError('Invalid terrain hash')
    tiles={}
    for i,row in enumerate(struct.iter_unpack('<HHHBBBBH',terrain[36:])):
        x,y,tile,kind,left,right,layer,reserved=row
        if layer==1:tiles[x+496,y+384]=(i,tile)
    chosen=[]
    for r in records:
        if r['area']!=1 or not (496<=r['x']<1904 and 384<=r['y']<704):continue
        if r['tile'] not in (30,48,49):
            if r['contents'] or 3<=r['tile']<=13:raise ValueError('Unimplemented content-bearing tile in opening')
            continue
        kind={30:1,49:2,48:3}[r['tile']]
        if (kind==2 and r['contents'] not in (0,7)) or (kind!=2 and r['contents']):
            raise ValueError('Unimplemented block contents')
        index,tile=tiles[r['x'],r['y']]
        if tile!=r['tile']:raise ValueError('Interaction/terrain mismatch')
        chosen.append((r['x']-496,r['y']-384,index,kind,r['contents']))
    for r in actors:
        if r['area']==1 and r['id']==147 and 496<=r['x']<1904 and 384<=r['y']<704:
            if r['param'] or r['layer']!=0:raise ValueError('Unsupported actor coin settings')
            chosen.append((r['x']-496,r['y']-384,65535,1,0))
    if len(chosen)>128:raise ValueError('Interaction capacity exceeded')
    payload=b''.join(struct.pack('<3HBBI',*row,0) for row in chosen)
    head=struct.pack('<4s4I',b'NSI1',1,len(chosen),fnv1a(terrain),texture_hash)
    return head+struct.pack('<I',fnv1a(head+payload))+payload


def package(extracted,terrain_path,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new output directory outside extraction')
    records,actors=inventory(extracted);terrain=Path(terrain_path).read_bytes()
    from item_graphics import bake
    image,texture=bake(extracted)
    data=encode(records,actors,terrain,fnv1a(texture))
    output.mkdir(parents=True);(output/'items.nsi').write_bytes(data)
    (output/'items.rgba').write_bytes(texture);image.save(output/'items-preview.png')
    report={'format':'NSI1','version':1,'count':(len(data)-24)//12,
            'terrain_sha256':hashlib.sha256(terrain).hexdigest(),
            'items_sha256':hashlib.sha256(data).hexdigest(),
            'texture_sha256':hashlib.sha256(texture).hexdigest(),
            'source_sha256':{name:hashlib.sha256((extracted/name).read_bytes()).hexdigest()
                             for name in ('files/Stage/01-01.arc','files/Object/I_kinoko.arc','files/Object/I_propeller.arc')},
            'all_area_tile_inventory':records,'all_area_actor_inventory':actors,
            'limitations':['Opening only; actor inventories are evidence, not implemented behaviors.',
                           'Original block-content bits retained. Power-up movement remains approximate.']}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return {'count':report['count'],'output':str(output)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(package(a.extracted,a.terrain,a.output),indent=2))
