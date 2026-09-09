"""Convert Goomba placements for the existing World 1-1 opening terrain package."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from convert_course import decode_course,fnv1a
from inspect_assets import unpack_u8

def encode(records,terrain):
    if len(terrain)<36 or terrain[:4]!=b'NST1' or struct.unpack_from('<I',terrain,4)[0]!=1:
        raise ValueError('Expected NST1 version 1')
    count=struct.unpack_from('<I',terrain,8)[0]
    if not 0<count<=2048 or len(terrain)!=36+12*count:
        raise ValueError('Invalid terrain record count/length')
    if struct.unpack_from('<I',terrain,32)[0]!=fnv1a(terrain[:32]+terrain[36:]):
        raise ValueError('Terrain checksum mismatch')
    if struct.unpack_from('<4I',terrain,12)!=(1408,320,256,192):
        raise ValueError('Expected the opening-section terrain bounds/spawn')
    payload=bytearray()
    for r in records:
        if r['kind']!=1 or r['id']!=20 or not (496<=r['x']<1904 and 384<=r['y']<704):continue
        if r['param'] or r['x']+16>1904 or r['y']+16>704:
            raise ValueError('Unsupported Goomba settings or bounds')
        payload.extend(struct.pack('<4H',r['x']-496,r['y']-384,20,0))
    n=len(payload)//8
    if n>32:raise ValueError('Enemy capacity exceeded')
    header=struct.pack('<4s4I',b'NSE1',1,n,fnv1a(terrain),0)
    return header+struct.pack('<I',fnv1a(header+payload))+payload

def package(extracted,terrain_path,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose new output outside extracted source')
    boot=(extracted/'sys/boot.bin').read_bytes()
    if boot[:8]!=b'SMNE01\0\2' or boot[24:28]!=bytes.fromhex('5d1c9ea3'):raise ValueError('Unexpected disc header')
    stage=(extracted/'files/Stage/01-01.arc').read_bytes()
    entries=unpack_u8(stage)
    decoded=decode_course(entries['course/course1.bin'],{})
    terrain=Path(terrain_path).read_bytes()
    data=encode(decoded['records'],terrain)
    output.mkdir(parents=True)
    (output/'enemies.nse').write_bytes(data)
    report={'format':'NSE1','version':1,'count':(len(data)-24)//8,'actor_id':20,
            'source_stage_sha256':hashlib.sha256(stage).hexdigest(),
            'terrain_sha256':hashlib.sha256(terrain).hexdigest(),
            'enemies_sha256':hashlib.sha256(data).hexdigest(),
            'limitations':['Goombas only; approximate walking/stomp/contact behavior.',
                           'Temporary drawn visuals; original BRRES models are not converted.']}
    (output/'enemy-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try:print(json.dumps(package(a.extracted,a.terrain,a.output),indent=2))
    except (OSError,ValueError,KeyError) as e:p.exit(1,f'Enemy conversion failed: {e}\n')
