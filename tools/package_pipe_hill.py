"""Static eight-pipe hill prototype. No rotation transport or pipe traversal."""
import argparse,hashlib,json,math,struct
from pathlib import Path
from inspect_assets import unpack_u8
from convert_course import decode_course,fnv1a
from convert_character import Reader,model
from character_pose import mesh,pose
from package_hill import render
from gpu_texture import rgba8_tiles
from route_section import section_named


def rotate(x,y,degrees):
    a=math.radians(degrees);c,s=math.cos(a),math.sin(a)
    return x*c+y*s,-x*s+y*c


def upper_height(triangles,x):
    """Highest intersection of the vertical probe with solid ground triangles."""
    heights=[]
    for tri in triangles:
        for a,b in zip(tri,tri[1:]+tri[:1]):
            if min(a[0],b[0])-1e-6 <= x <= max(a[0],b[0])+1e-6:
                if abs(a[0]-b[0])<1e-7:
                    heights.extend((a[1],b[1]))
                else:
                    t=max(0,min(1,(x-a[0])/(b[0]-a[0])))
                    heights.append(a[1]+t*(b[1]-a[1]))
    if not heights:raise ValueError(f'Ground has no supporting surface at x={x}')
    return max(heights)


def source_actor(course):
    actors=[r for r in course['records'] if r['kind']==1 and r['id']==360 and 496<=r['x']<3312]
    if len(actors)!=1 or (actors[0]['x'],actors[0]['y'],actors[0]['param'])!=(1904,544,0x0e000401):
        raise ValueError('Unverified eight-pipe hill configuration')
    return actors[0]


def encode(terrain,texture,triangles):
    section_named('checkpoint').validate_terrain(terrain)
    # Top-centre anchor matches the reference editor's 800-unit circle outline.
    # Restrict support to the upper cap; retain the lower half as visual only.
    heights=[560-upper_height(triangles,x-1416) for x in range(1096,1737,4)]
    if any(not math.isfinite(y) or not 159<=y<=384 for y in heights):
        raise ValueError('Pipe-hill support exceeds the bounded cap')
    rows=[(1096+4*i,4,heights[i],heights[i+1]) for i in range(160)]
    body=b''.join(struct.pack('<4f',*r) for r in rows)
    head=struct.pack('<4s6I',b'NPH1',1,fnv1a(terrain),fnv1a(texture),1016,160,160)
    return head+struct.pack('<I',fnv1a(head+body))+body,rows


def package(extracted,terrain_path,output):
    extracted,output=Path(extracted).resolve(),Path(output).resolve()
    if output.exists() or extracted==output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new output outside extraction')
    if (extracted/'sys/boot.bin').read_bytes()[:8]!=b'SMNE01\0\2':raise ValueError('Expected USA rev-2 source')
    stage=(extracted/'files/Stage/01-01.arc').read_bytes()
    course=decode_course(unpack_u8(stage)['course/course1.bin'],{})
    actor=source_actor(course)
    links=[e for e in course['entrances'] if e['id']==((actor['param']>>8)&15)]
    if len(links)!=1:raise ValueError('Hill entrance missing/duplicated')
    angle=((actor['param']>>24)&15)*22.5
    raw=(extracted/'files/Object/circle_ground_holeD8.arc').read_bytes()
    reader=Reader(unpack_u8(raw)['g3d/circle_ground_holeD8.brres'])
    m=model(reader,dict(reader.resources()['3DModels(NW4R)'])['circle_ground_holeD8'])
    triangles=[]
    for material,tri in mesh(m,pose(m)):
        # The cutout overlay includes transparent quads. It must not bridge a
        # mouth for collision. Use the base-ground material's actual mesh.
        if m['materials'][material]['name']!='mt_cirlce_groundD8':continue
        triangles.append([rotate(*v['position'][:2],angle) for v in tri])
    if len(triangles)!=640:raise ValueError('Unexpected ground mesh topology')
    image=render(reader,512,'circle_ground_holeD8',angle)
    texture=rgba8_tiles(image.tobytes(),512,512)
    terrain=Path(terrain_path).read_bytes()
    data,rows=encode(terrain,texture,triangles)
    output.mkdir(parents=True)
    (output/'pipe-hill.nph').write_bytes(data);(output/'pipe-hill.rgba').write_bytes(texture)
    image.save(output/'pipe-hill-preview.png')
    report={'version':1,'actor':actor,'starting_rotation_degrees':angle,'support':rows,
            'source_stage_sha256':hashlib.sha256(stage).hexdigest(),'model_archive_sha256':hashlib.sha256(raw).hexdigest(),
            'terrain_sha256':hashlib.sha256(terrain).hexdigest(),
            'files':{n:hashlib.sha256((output/n).read_bytes()).hexdigest() for n in ('pipe-hill.nph','pipe-hill.rgba')},
            'entrance_id':(actor['param']>>8)&15,
            'entrance':links[0],
            'limitations':['Static starting pose; rotation/transport deferred.',
                          'Upper ground envelope sampled at four-unit intervals; vertical mouth-wall contacts need fidelity review.',
                          'Pipe transitions are not implemented. Do not substitute a nearby entrance.',
                          'Not hardware validated.']}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return {'output':str(output),'surfaces':len(rows),'angle':angle}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extracted',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try: print(json.dumps(package(a.extracted,a.terrain,a.output),indent=2))
    except (ValueError,OSError,KeyError) as e:p.exit(1,f'Pipe hill conversion failed: {e}\n')
