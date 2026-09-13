"""Package the ordinary World 1-1 midpoint and its referenced entrance locally."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from convert_course import decode_course, fnv1a
from inspect_assets import unpack_u8
from route_section import section_named


def encode(actors, entrances, terrain):
    bounds = section_named('checkpoint')
    bounds.validate_terrain(terrain)
    flags = [a for a in actors if a['kind'] == 1 and a['id'] == 188 and bounds.contains(a)]
    if len(flags) != 1:
        raise ValueError('Expected one ordinary midpoint in the checkpoint section')
    flag = flags[0]
    # Sprite settings nybbles 7-8 select the entrance. Low bits select facing
    # and alternate midpoint; reject them until those behaviors are supported.
    param = flag['param']
    if param & ~0x00ff0000 or flag.get('layer', 0):
        raise ValueError('Unsupported checkpoint settings')
    entry_id = (param >> 16) & 255
    matches = [e for e in entrances if e['id'] == entry_id]
    if len(matches) != 1:
        raise ValueError('Checkpoint entrance missing or duplicated')
    entry = matches[0]
    if not bounds.contains(entry) or any(entry[k] for k in ('type', 'flags', 'destination_file', 'destination_id', 'layer')):
        raise ValueError('Checkpoint requires an ordinary in-area entrance')
    # Course entrance Y is the small player's top. The controller reset starts
    # with a 32-unit body; items_reset then shrinks while retaining foot height.
    x,y = flag['x']-bounds.x, flag['y']-bounds.y
    sx,sy = entry['x']-bounds.x, entry['y']-bounds.y-16
    if not (0 <= sx <= bounds.width-16 and 0 <= sy <= bounds.height-32 and x+16 <= bounds.width and y+16 <= bounds.height):
        raise ValueError('Checkpoint/entrance outside package bounds')
    head = struct.pack('<4s8I', b'NSK1', 1, fnv1a(terrain), x, y, sx, sy, entry_id, 0)
    return head+struct.pack('<I', fnv1a(head))


def package(extracted, terrain_path, output):
    extracted,output = Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted == output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new output directory outside extraction')
    if (extracted/'sys/boot.bin').read_bytes()[:8] != b'SMNE01\0\2':
        raise ValueError('Expected USA rev-2 source')
    stage = (extracted/'files/Stage/01-01.arc').read_bytes()
    course = decode_course(unpack_u8(stage)['course/course1.bin'], {})
    terrain = Path(terrain_path).read_bytes()
    data = encode(course['records'], course['entrances'], terrain)
    output.mkdir(parents=True)
    (output/'checkpoint.nsk').write_bytes(data)
    report = {'format':'NSK1','version':1,'source_stage_sha256':hashlib.sha256(stage).hexdigest(),
              'terrain_sha256':hashlib.sha256(terrain).hexdigest(),
              'checkpoint_sha256':hashlib.sha256(data).hexdigest(),
              'limitations':['Prototype contact box and visual; final Wii comparison pending.',
                             'In-session death restart only; no world-map or save-file persistence.',
                             'This optional file does not make the expanded route ready for device delivery.']}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try: print(json.dumps(package(a.extracted,a.terrain,a.output),indent=2))
    except (ValueError,OSError,KeyError) as error:p.exit(1,f'Checkpoint packaging failed: {error}\n')
