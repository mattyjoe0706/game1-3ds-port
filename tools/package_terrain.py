"""Create the local NST1 opening-section package. Never publish generated assets."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from convert_tiles import convert, lz11, rgb5a3
from convert_course import fnv1a
from inspect_assets import unpack_u8

SLOPES={0:(16,0),1:(0,16),2:(16,8),3:(8,0),4:(0,8),5:(8,16),
        11:(16,12),12:(12,8),13:(8,4),14:(4,0),15:(0,4),16:(4,8),17:(8,12),18:(12,16)}

def morton(x,y):
    return sum(((x>>bit)&1)<<(2*bit) | ((y>>bit)&1)<<(2*bit+1) for bit in range(3))

def gpu_atlas(textures):
    result=bytearray(512*512*4)
    for slot,texture in textures.items():
        for tile in range(256):
            tile_id=slot*256+tile
            for y in range(16):
                for x in range(16):
                    # Nearest centre sample from the 24x24 useful tile interior.
                    sx=(tile%32)*32+4+(x*24+12)//16
                    sy=(tile//32)*32+4+(y*24+12)//16
                    src=(sy*1024+sx)*4
                    ax=(tile_id%32)*16+x
                    ay=511-((tile_id//32)*16+y)
                    dst=((ay//8)*64*64+(ax//8)*64+morton(ax&7,ay&7))*4
                    result[dst:dst+4]=texture[src:src+4][::-1] # GPU RGBA8 byte order: ABGR
    return bytes(result)

def encode(records,texture_hash):
    payload=bytearray()
    omitted=0
    for r in sorted(records,key=lambda r:-r['layer']):
        if not (496<=r['x']<1904 and 384<=r['y']<704):
            continue
        # Invisible marker tiles are inspection visuals, not terrain.
        if r['flags']=='0000000000000028':
            omitted+=1
            continue
        kind=left=right=0
        if r['layer']==1:
            tag=r['collision']
            if tag=='solid' or (tag=='floor_slope' and r['shape']==10):
                kind=1
            elif tag=='top_only':
                kind=2
            elif tag=='floor_slope' and r['shape'] in SLOPES:
                kind=2;left,right=SLOPES[r['shape']]
            elif tag not in ('empty','other'):
                raise ValueError(f'Unsupported collision in slice: {tag}/{r["shape"]}')
            elif tag=='other' and r['flags']!='0000000200000000':
                raise ValueError(f'Unknown collision flags: {r["flags"]}')
        payload.extend(struct.pack('<HHHBBBBH',r['x']-496,r['y']-384,r['slot']*256+r['tile'],
                                   kind,left,right,r['layer'],0))
    count=len(payload)//12
    if not 0<count<=2048:
        raise ValueError('Terrain capacity exceeded')
    # Original entrance X=752; spawn feet aligned to original ground Y=608.
    head=struct.pack('<4s7I',b'NST1',1,count,1408,320,256,192,texture_hash)
    return head+struct.pack('<I',fnv1a(head+payload))+payload,omitted

def package(extracted,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new output directory separate from extraction')
    # Conversion validates source header and bounded definitions before packaging.
    manifest=convert(extracted,output/'inspection')
    textures={}
    for slot,name in enumerate(manifest['tilesets']):
        if not name:continue
        raw=(extracted/f'files/Stage/Texture/{name}.arc').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=manifest['tileset_sha256'][name]:
            raise ValueError('Tileset changed during conversion')
        entries=unpack_u8(raw)
        textures[slot]=rgb5a3(lz11(entries[f'BG_tex/{name}_tex.bin.LZ']))
    atlas=gpu_atlas(textures)
    records=json.loads((output/'inspection/terrain.json').read_text())
    data,omitted=encode(records,fnv1a(atlas))
    target=output/'SD-ROOT/3ds/nsmbw-prototype/data'
    target.mkdir(parents=True)
    (target/'terrain.nst').write_bytes(data)
    (target/'terrain.rgba').write_bytes(atlas)
    report={'format':'NST1','version':1,'native_build':'TERRAIN TEST 1',
            'world_bounds':[496,384,1408,320],'tiles':(len(data)-36)//12,
            'omitted_marker_tiles':omitted,'texture_bytes':len(atlas),
            'files':{n:hashlib.sha256((target/n).read_bytes()).hexdigest() for n in ('terrain.nst','terrain.rgba')},
            'limitations':['Opening section only; approximate player physics.',
                           'Static textures; coins decorative; blocks do not release items.',
                           'No enemies, Mario graphics, background scenes or audio.',
                           'Unvalidated on hardware; does not establish 60 fps acceptance.']}
    (output/'package-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try:print(json.dumps(package(a.extracted,a.output),indent=2))
    except (ValueError,OSError,KeyError) as e:p.exit(1,f'Packaging failed: {e}\n')
