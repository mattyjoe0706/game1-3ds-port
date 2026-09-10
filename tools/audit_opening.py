"""Compare packaged opening placements/pixels with decoded original data.

This is a data-fidelity check, not a Wii gameplay or camera validation.
Requires Pillow for the side-by-side texture preview.
"""
import argparse,collections,hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
from inspect_assets import unpack_u8
from convert_course import decode_course,fnv1a

def unpack_atlas(raw):
    if len(raw)!=512*512*4:raise ValueError('Unexpected terrain texture size')
    out=bytearray(len(raw))
    for tile in range(4096):
        for i in range(64):
            x=(tile%64)*8+((i&1)|((i>>1)&2)|((i>>2)&4))
            y=(tile//64)*8+(((i>>1)&1)|((i>>2)&2)|((i>>3)&4))
            src=(tile*64+i)*4;dst=(y*512+x)*4
            out[dst:dst+4]=raw[src:src+4][::-1]
    return Image.frombytes('RGBA',(512,512),bytes(out))

def audit(extracted,terrain_dir,enemies_path,old_texture,output):
    if output.exists():raise ValueError('Choose a new audit output directory')
    data=terrain_dir/'SD-ROOT/3ds/nsmbw-prototype/data'
    raw=(data/'terrain.nst').read_bytes();tex=(data/'terrain.rgba').read_bytes();enemy=enemies_path.read_bytes()
    if raw[:4]!=b'NST1' or len(raw)<36 or fnv1a(raw[:32]+raw[36:])!=struct.unpack_from('<I',raw,32)[0]:raise ValueError('Invalid terrain checksum')
    count=struct.unpack_from('<I',raw,8)[0]
    if len(raw)!=36+12*count or fnv1a(tex)!=struct.unpack_from('<I',raw,28)[0]:raise ValueError('Invalid terrain size/texture binding')
    packed=list(struct.iter_unpack('<HHHBBBBH',raw[36:]))
    original=json.loads((terrain_dir/'inspection/terrain.json').read_text())
    inside=lambda r:496<=r['x']<1904 and 384<=r['y']<704
    selected=[r for r in original if inside(r)]
    visible=[r for r in selected if r['flags']!='0000000000000028']
    expected=collections.Counter((r['x']-496,r['y']-384,r['slot']*256+r['tile'],r['layer']) for r in visible)
    actual=collections.Counter((x,y,t,layer) for x,y,t,kind,left,right,layer,reserved in packed)
    if expected!=actual:raise ValueError('Placement mismatch against expanded source terrain')
    atlas=unpack_atlas(tex);old=unpack_atlas(old_texture.read_bytes())
    source_images={s:Image.open(terrain_dir/f'inspection/tileset-{s}.png').convert('RGBA') for s in range(3)}
    changed=0
    for tile in sorted({r[2] for r in packed}):
        slot,index=divmod(tile,256)
        for y in range(16):
            for x in range(16):
                sx=(index%32)*32+4+(x*24+12)//16;sy=(index//32)*32+4+(y*24+12)//16
                target=(tile%32*16+x,tile//32*16+y)
                if atlas.getpixel(target)!=source_images[slot].getpixel((sx,sy)):raise ValueError('Texture pixel mismatch against original PNG')
        box=(tile%32*16,tile//32*16,(tile%32+1)*16,(tile//32+1)*16)
        changed+=old.crop(box).tobytes()!=atlas.crop(box).tobytes()
    stage=(extracted/'files/Stage/01-01.arc').read_bytes();files=unpack_u8(stage)
    course=decode_course(files['course/course1.bin'],{})
    actors=[r for r in course['records'] if r['kind']==1 and inside(r)]
    expected_enemies=collections.Counter((r['x']-496,r['y']-384,20,0) for r in actors if r['id']==20)
    if enemy[:4]!=b'NSE1' or len(enemy)<24 or struct.unpack_from('<I',enemy,12)[0]!=fnv1a(raw):raise ValueError('Enemy terrain binding mismatch')
    if fnv1a(enemy[:20]+enemy[24:])!=struct.unpack_from('<I',enemy,20)[0]:raise ValueError('Enemy checksum mismatch')
    if collections.Counter(struct.iter_unpack('<4H',enemy[24:]))!=expected_enemies:raise ValueError('Enemy placement mismatch')
    panels=[]
    for sheet,label in ((old,'Previously packed terrain'),(atlas,'Corrected terrain - source tile IDs and orientation')):
        panel=Image.new('RGBA',(1408,352),(91,160,208,255));draw=ImageDraw.Draw(panel);draw.text((8,8),label,fill='white')
        for x,y,t,kind,left,right,layer,reserved in packed:
            panel.alpha_composite(sheet.crop((t%32*16,t//32*16,(t%32+1)*16,(t//32+1)*16)),(x,y+32))
        panels.append(panel)
    preview=Image.new('RGBA',(1408,704));preview.alpha_composite(panels[0]);preview.alpha_composite(panels[1],(0,352))
    report=dict(source_stage_sha256=hashlib.sha256(stage).hexdigest(),bounds=[496,384,1408,320],
                matched_terrain_records=len(packed),matched_goomba_records=sum(expected_enemies.values()),
                unique_tile_images_checked=len({r[2] for r in packed}),unique_tile_images_changed=changed,
                omitted_marker_tiles=len(selected)-len(visible),collision_classes=dict(collections.Counter(r['collision'] for r in visible if r['layer']==1)),
                original_entrances=course['entrances'],original_zones=course['zones'],
                actors_in_slice=actors,unsupported_actor_ids=dict(collections.Counter(r['id'] for r in actors if r['id']!=20)),
                passed=True,limitations=['Comparison uses the existing course/tile decoder; not an independent Wii execution.',
                'Wii camera framing and player scale have not been matched to reference gameplay.',
                'Player physics and ramp side/underside collisions remain approximate.',
                'Coins, block contents, actor behaviors other than four Goombas, backgrounds and audio remain incomplete.',
                'The section endpoint is authored; this does not cover the full level or Wii goal.'])
    output.mkdir(parents=True);preview.convert('RGB').save(output/'terrain-before-after.png')
    (output/'audit.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('extracted','terrain_dir','enemies','old_texture','output'):p.add_argument(name,type=Path)
    a=p.parse_args();print(json.dumps(audit(a.extracted,a.terrain_dir,a.enemies,a.old_texture,a.output),indent=2))
