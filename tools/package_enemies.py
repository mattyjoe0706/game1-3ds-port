"""Convert verified Goomba/Koopa placements, bound to a World 1-1 section."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from convert_course import decode_course,fnv1a
from inspect_assets import unpack_u8
from route_section import SECTIONS, section_named

def encode(records,terrain,section='opening'):
    bounds=section_named(section)
    bounds.validate_terrain(terrain)
    payload=bytearray()
    for r in records:
        if r['kind']!=1 or r['id'] not in (20,57) or not bounds.contains(r):continue
        # Only ordinary walkers. Koopa low bit selects green/red ledge behavior;
        # shell-at-spawn, fence and other settings need separate reconstruction.
        allowed=(0,) if r['id']==20 else (0,1)
        if r['param'] not in allowed or r.get('layer',0)!=0 or r['x']+16>bounds.right or r['y']+16>bounds.y+bounds.height:
            raise ValueError(f'Unsupported enemy {r["id"]} settings/bounds at {r["x"]},{r["y"]}')
        payload.extend(struct.pack('<4H',r['x']-bounds.x,r['y']-bounds.y,r['id'],r['param']))
    n=len(payload)//8
    if n>32:raise ValueError('Enemy capacity exceeded')
    header=struct.pack('<4s4I',b'NSE1',1,n,fnv1a(terrain),0)
    return header+struct.pack('<I',fnv1a(header+payload))+payload

def package(extracted,terrain_path,output,section='opening'):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose new output outside extracted source')
    boot=(extracted/'sys/boot.bin').read_bytes()
    if boot[:8]!=b'SMNE01\0\2' or boot[24:28]!=bytes.fromhex('5d1c9ea3'):raise ValueError('Unexpected disc header')
    stage=(extracted/'files/Stage/01-01.arc').read_bytes()
    entries=unpack_u8(stage)
    decoded=decode_course(entries['course/course1.bin'],{})
    terrain=Path(terrain_path).read_bytes()
    data=encode(decoded['records'],terrain,section)
    output.mkdir(parents=True)
    (output/'enemies.nse').write_bytes(data)
    report={'format':'NSE1','version':1,'count':(len(data)-24)//8,'actor_ids':[20,57],'section':section,
            'source_stage_sha256':hashlib.sha256(stage).hexdigest(),
            'terrain_sha256':hashlib.sha256(terrain).hexdigest(),
            'enemies_sha256':hashlib.sha256(data).hexdigest(),
            'limitations':['Ordinary Goomba/Koopa walkers only; approximate walking/stomp/contact behavior.',
                           'Enemy conversion does not establish terrain, reward or checkpoint readiness.',
                           'Temporary drawn visuals; original BRRES models are not converted.']}
    (output/'enemy-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--section',choices=SECTIONS,default='opening')
    a=p.parse_args()
    try:print(json.dumps(package(a.extracted,a.terrain,a.output,a.section),indent=2))
    except (OSError,ValueError,KeyError) as e:p.exit(1,f'Enemy conversion failed: {e}\n')
