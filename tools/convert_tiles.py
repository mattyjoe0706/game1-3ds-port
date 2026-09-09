"""Decode local SMNE01 rev2 terrain for inspection; not a playable package.

Independent format implementation researched against Reggie-Next commit
f7a73d60853e9143eddb92396e7b4e33f9c2de6a (object definitions, renderers,
tileset loaders, and collision overlays). No editor or Nintendo data bundled.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zlib

from convert_course import decode_course
from inspect_assets import unpack_u8


def lz11(data, limit=524288):
    """Bounded Nintendo LZ11 decoder, including overlapping backreferences."""
    pos = 0
    def take(n):
        nonlocal pos
        if pos + n > len(data):
            raise ValueError('Truncated LZ11 stream')
        result = data[pos:pos+n]
        pos += n
        return result
    header = take(4)
    if header[0] != 0x11:
        raise ValueError('Expected LZ11')
    size = int.from_bytes(header[1:], 'little')
    if not size:
        size = int.from_bytes(take(4), 'little')
    if not 0 < size <= limit:
        raise ValueError('LZ11 output exceeds capacity')
    out = bytearray()
    while len(out) < size:
        flags = take(1)[0]
        for bit in range(7, -1, -1):
            if len(out) == size:
                break
            if not flags & (1 << bit):
                out.extend(take(1))
                continue
            first = take(1)[0]
            kind = first >> 4
            count = 2 if kind == 0 else 3 if kind == 1 else 1
            word = int.from_bytes(bytes([first]) + take(count), 'big')
            distance = (word & 4095) + 1
            length = ((word >> 12) + 17 if kind == 0 else
                      ((word >> 12) & 65535) + 273 if kind == 1 else kind + 1)
            if distance > len(out) or len(out) + length > size:
                raise ValueError('Invalid LZ11 backreference')
            for _ in range(length):
                out.append(out[-distance])
    return bytes(out)


def rgb5a3(data, width=1024, height=256):
    if width <= 0 or height <= 0 or width % 4 or height % 4 or len(data) != width*height*2:
        raise ValueError('Invalid RGB5A3 dimensions or byte count')
    result = bytearray(width*height*4)
    for index, (pixel,) in enumerate(struct.iter_unpack('>H', data)):
        block, cell = divmod(index, 16)
        x = (block % (width//4))*4 + cell % 4
        y = (block // (width//4))*4 + cell // 4
        if pixel & 32768:
            values = [(pixel >> shift) & 31 for shift in (10, 5, 0)]
            rgba = bytes([(v << 3) | (v >> 2) for v in values] + [255])
        else:
            alpha = (pixel >> 12) & 7
            rgba = bytes([((pixel >> shift) & 15)*17 for shift in (8, 4, 0)] +
                         [(alpha << 5) | (alpha << 2) | (alpha >> 1)])
        result[(y*width+x)*4:(y*width+x+1)*4] = rgba
    return bytes(result)


def png(width, height, rgba):
    if len(rgba) != width*height*4:
        raise ValueError('Invalid PNG image length')
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    rows = b''.join(b'\0'+rgba[y*width*4:(y+1)*width*4] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width,height,8,6,0,0,0)) +
            chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def definition(data, offset):
    rows, row = [], []
    if not 0 <= offset < len(data):
        raise ValueError('Object offset outside definitions')
    while offset < len(data):
        control = data[offset]
        offset += 1
        if control == 255:
            if row:
                raise ValueError('Unterminated object row')
            if not rows:
                raise ValueError('Empty object definition')
            return rows
        if control == 254:
            rows.append(row)
            row = []
        elif control & 128:
            row.append((control, None))
        else:
            if offset+2 > len(data):
                raise ValueError('Truncated object tile')
            row.append((control, data[offset] | ((data[offset+1] & 3) << 8)))
            offset += 2
    raise ValueError('Missing object terminator')


def repeated(items, length, flag):
    """Select prefix, repeated body and suffix for a stretchable axis."""
    repeat_indices = [i for i, item in enumerate(items) if flag(item)]
    if not items:
        raise ValueError('Empty repeat axis')
    if not repeat_indices:
        return [items[i % len(items)] for i in range(length)]
    first, last = repeat_indices[0], repeat_indices[-1]
    if repeat_indices != list(range(first, last+1)):
        raise ValueError('Noncontiguous repeat region')
    tail = len(items)-last-1
    return [items[i] if i < first else items[len(items)-length+i] if i >= length-tail
            else items[first+(i-first) % (last-first+1)] for i in range(length)]


def expand(rows, width, height):
    if not 0 < width <= 1024 or not 0 < height <= 512 or width*height > 65536:
        raise ValueError('Object tile capacity exceeded')
    rows = [r for r in rows if r]
    if not rows:
        raise ValueError('No tile rows')
    if not rows[0][0][0] & 128:
        return [[t[1] for t in repeated(row, width, lambda t: t[0] & 1)]
                for row in repeated(rows, height, lambda r: r[0][0] & 2)]
    # Diagonal sections are fixed stamps, advanced by their own dimensions.
    sections = []
    for row in rows:
        if row[0][0] & 128:
            sections.append([])
        sections[-1].append([t[1] for t in row if t[1] is not None])
    if len(sections) > 2 or any(not row for section in sections for row in section):
        raise ValueError('Unsupported diagonal section')
    for section in sections:
        widest = max(map(len, section))
        for row in section:
            row.extend([None]*(widest-len(row)))
    main = sections[0]
    fill = sections[1] if len(sections) == 2 else []
    mh, mw, fh = len(main), len(main[0]), len(fill)
    left, down = bool(rows[0][0][0] & 1), bool(rows[0][0][0] & 2)
    y = (fh if down else height-mh-fh) if not left else (height-mh if down else 0)
    step = mh if left != down else -mh
    result = [[None]*width for _ in range(height)]
    def stamp(section, ox, oy):
        for sy, row in enumerate(section):
            for sx, tile in enumerate(row):
                if 0 <= ox+sx < width and 0 <= oy+sy < height:
                    result[oy+sy][ox+sx] = tile
    for i in range(min(width//mw, height//mh)):
        x = i*mw
        stamp(main, x, y)
        if fill:
            stamp(fill, x+mw-len(fill[0]) if left else x, y-fh if down else y+mh)
        y += step
    return result


def collision(raw):
    """Retain original flags; classify only recognized static terrain shapes."""
    if len(raw) != 8:
        raise ValueError('Expected eight collision bytes')
    if raw[3] & 32:
        return 'floor_slope'
    if raw[3] & 64:
        return 'ceiling_slope'
    if raw[2] & 8:
        return 'partial'
    if raw[2] & 32:
        return 'bottom_only'
    if raw[2] & 128:
        return 'top_only'
    if raw[2] & 16:
        return 'hazard'
    if raw[3] & 0x1d:
        return 'solid'
    return 'other' if any(raw) else 'empty'


def convert(extracted, output):
    extracted, output = Path(extracted).resolve(), Path(output).resolve()
    if output == extracted or extracted in output.parents or output in extracted.parents:
        raise ValueError('Output must be separate from extracted files')
    if output.exists():
        raise ValueError('Choose a new output directory')
    boot = (extracted/'sys/boot.bin').read_bytes()
    if boot[:8] != b'SMNE01\0\2' or boot[24:28] != bytes.fromhex('5d1c9ea3'):
        raise ValueError('Expected validated SMNE01 disc 0 revision 2 extraction')
    stage_raw = (extracted/'files/Stage/01-01.arc').read_bytes()
    archive = unpack_u8(stage_raw)
    course = decode_course(archive['course/course1.bin'], {
        i: archive[f'course/course1_bgdatL{i}.bin'] for i in range(3)
        if f'course/course1_bgdatL{i}.bin' in archive})
    tables, textures, hashes = {}, {}, {}
    for slot, name in enumerate(course['tilesets']):
        if not name:
            continue
        raw = (extracted/f'files/Stage/Texture/{name}.arc').read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        arc = unpack_u8(raw)
        index, defs = arc[f'BG_unt/{name}_hd.bin'], arc[f'BG_unt/{name}.bin']
        check = arc[f'BG_chk/d_bgchk_{name}.bin']
        if len(index) % 4 or len(check) != 2048:
            raise ValueError('Invalid tileset table length')
        objects = [definition(defs, off) for off, _, _ in struct.iter_unpack('>HBB', index)]
        tables[slot] = (objects, check)
        textures[slot] = rgb5a3(lz11(arc[f'BG_tex/{name}_tex.bin.LZ']))
    cells = {}
    budget = 0
    for obj in course['records']:
        if obj['kind'] != 0:
            continue
        slot, number = obj['id'] >> 12, obj['id'] & 4095
        objects, _ = tables[slot]
        if number >= len(objects):
            raise ValueError('Object index outside tileset')
        width, height = obj['w']//16, obj['h']//16
        budget += width*height
        if budget > 1000000:
            raise ValueError('Stage expansion capacity exceeded')
        for y, row in enumerate(expand(objects[number], width, height)):
            for x, tile in enumerate(row):
                if tile is None or tile == 0:
                    continue
                tile_slot, tile_index = tile >> 8, tile & 255
                if tile_slot not in tables:
                    raise ValueError('Tile references absent tileset')
                cells[(obj['layer'], obj['x']//16+x, obj['y']//16+y)] = (tile_slot, tile_index)
    records = []
    for (layer,x,y), (slot,tile) in sorted(cells.items()):
        raw = tables[slot][1][tile*8:tile*8+8]
        records.append(dict(layer=layer,x=x*16,y=y*16,slot=slot,tile=tile,
                            collision=collision(raw),flags=raw.hex(),shape=raw[7]))
    # First outdoor segment: original coordinates, 24 image pixels per 16 world units.
    origin_x, origin_y, tiles_w, tiles_h = 496, 384, 88, 20
    width, height = tiles_w*24, tiles_h*24
    preview = bytearray(bytes((91,160,208,255))*(width*height))
    for r in sorted(records, key=lambda r: -r['layer']):
        dx,dy = (r['x']-origin_x)//16*24, (r['y']-origin_y)//16*24
        if not 0 <= dx < width or not 0 <= dy < height:
            continue
        texture = textures[r['slot']]
        sx,sy = (r['tile']%32)*32+4, (r['tile']//32)*32+4
        for y in range(24):
            for x in range(24):
                src = ((sy+y)*1024+sx+x)*4
                dst = ((dy+y)*width+dx+x)*4
                a = texture[src+3]
                for c in range(3):
                    preview[dst+c] = (texture[src+c]*a+preview[dst+c]*(255-a)+127)//255
    report = dict(format='NST-inspection', version=1, stage='01-01', area=1,
                  playable=False, tiles=len(records), tilesets=course['tilesets'],
                  source_sha256=hashlib.sha256(stage_raw).hexdigest(),tileset_sha256=hashes,
                  collision_counts=dict(Counter(r['collision'] for r in records if r['layer']==1)),
                  preview_bounds=dict(x=origin_x,y=origin_y,w=tiles_w*16,h=tiles_h*16),
                  limitations=['Inspection output; native runtime does not load this format yet.',
                               'Raw static atlas only; animated blocks and actor visuals are absent.',
                               'Collision classes are not validated Wii gameplay behavior.',
                               'Randomized tile variants are not applied.'])
    output.mkdir(parents=True)
    (output/'terrain.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'world-1-1-terrain.png').write_bytes(png(width,height,preview))
    for slot, rgba in textures.items():
        (output/f'tileset-{slot}.png').write_bytes(png(1024,256,rgba))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('extracted',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(convert(args.extracted,args.output),indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1,f'Terrain conversion failed: {error}\n')
