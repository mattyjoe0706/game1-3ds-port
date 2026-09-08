"""Convert World 1-1 placement data to NSC1 debug geometry; not a playable level.

Course structures: NSMBW-Decomp 6b6780c6b42003ce6f8e8705fea8021bab336818,
include/game/bases/d_cd_data.hpp and source/dol/bases/d_cd.cpp.
Layer records are decoded as five big-endian u16 fields plus an FFFF terminator;
object bounds do not describe solid tiles, slopes, or collision behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from inspect_assets import unpack_u8, course_blocks

HEADER = struct.Struct("<4s7I")
RECORD = struct.Struct("<BBHiiiiI")
MAX_RECORDS = 4096


def fnv1a(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


def records(data, stride, label):
    if len(data) % stride:
        raise ValueError(f"{label}: invalid record length {len(data)}")
    return [data[i:i + stride] for i in range(0, len(data), stride)]


def read_layer(data, layer):
    if not data.endswith(b"\xff\xff"):
        raise ValueError("Missing layer terminator")
    result = []
    for raw in records(data[:-2], 10, "layer"):
        packed, x, y, w, h = struct.unpack(">5H", raw)
        if packed >> 12 > 3 or not w or not h:
            raise ValueError("Invalid object tileset slot or dimensions")
        result.append({"kind": 0, "layer": layer, "id": packed,
                       "x": x * 16, "y": y * 16, "w": w * 16, "h": h * 16, "param": 0})
    return result


def decode_course(data, layers):
    info = course_blocks(data)
    blocks = [data[b["offset"]:b["offset"] + b["bytes"]] for b in info]
    if len(blocks[0]) != 128 or len(blocks[1]) != 20:
        raise ValueError("Unexpected tileset/options block size")
    tilesets = []
    for raw in records(blocks[0], 32, "tilesets"):
        if b"\0" not in raw:
            raise ValueError("Unterminated tileset name")
        name = raw.split(b"\0", 1)[0].decode("ascii")
        if not re.fullmatch(r"[A-Za-z0-9_-]*", name):
            raise ValueError("Unsafe tileset name")
        tilesets.append(name)
    items = []
    for layer, raw in sorted(layers.items()):
        if layer not in (0, 1, 2):
            raise ValueError("Unknown layer")
        items += read_layer(raw, layer)
    entrances = []
    for raw in records(blocks[6], 20, "entrances"):
        x, y = struct.unpack_from(">HH", raw)
        entrance = {"id": raw[8], "x": x, "y": y, "destination_file": raw[9],
                    "destination_id": raw[10], "type": raw[11], "zone": raw[13],
                    "layer": raw[14], "flags": struct.unpack_from(">H", raw, 16)[0]}
        if entrance["layer"] > 2:
            raise ValueError("Unsupported entrance layer")
        entrances.append(entrance)
        items.append({"kind": 2, "layer": raw[14], "id": raw[8], "x": x, "y": y,
                      "w": 16, "h": 16, "param": raw[11]})
    actor_data = blocks[7]
    # Wii records are padded to 16 bytes; the four-byte sentinel is not an actor.
    if len(actor_data) < 4 or not actor_data.endswith(b"\xff" * 4):
        raise ValueError("Missing actor terminator")
    actor_ids = set()
    for raw in records(actor_data[:-4], 16, "actors"):
        actor_id, x, y = struct.unpack_from(">HHH", raw)
        if raw[13] > 2:
            raise ValueError("Unsupported actor layer")
        actor_ids.add(actor_id)
        items.append({"kind": 1, "layer": raw[13], "id": actor_id, "x": x, "y": y,
                      "w": 16, "h": 16, "param": struct.unpack_from(">I", raw, 8)[0]})
    zones = []
    for raw in records(blocks[9], 24, "zones"):
        x, y, w, h = struct.unpack_from(">4H", raw)
        if not w or not h:
            raise ValueError("Empty zone")
        zones.append({"id": raw[12], "x": x, "y": y, "w": w, "h": h})
        items.append({"kind": 3, "layer": 0, "id": raw[12], "x": x, "y": y,
                      "w": w, "h": h, "param": 0})
    initial_id = blocks[1][16]
    matching = [e for e in entrances if e["id"] == initial_id]
    if len(matching) > 1 or not entrances:
        raise ValueError("Entrances missing or ambiguous")
    if not zones:
        raise ValueError("No zones")
    if len(items) > MAX_RECORDS:
        raise ValueError("Record capacity exceeded")
    # Subareas are entered through incoming pipe/door links. Their options may
    # reference an absent entrance. A viewer can start at their first entrance;
    # gameplay must instead resolve the incoming destination ID.
    return {"tilesets": tilesets, "initial_entrance_id": initial_id,
            "view_origin": matching[0] if matching else entrances[0],
            "view_origin_policy": "options_entrance" if matching else "first_entrance_for_viewer_only",
            "entrances": entrances,
            "zones": zones, "actor_ids": sorted(actor_ids), "records": items}


def encode_scene(area, decoded):
    if area not in range(1, 5):
        raise ValueError("Unsupported area number")
    payload = b"".join(RECORD.pack(*(r[k] for k in ("kind", "layer", "id", "x", "y", "w", "h", "param")))
                       for r in decoded["records"])
    spawn = decoded["view_origin"]
    header = HEADER.pack(b"NSC1", 1, area, len(decoded["records"]), spawn["x"], spawn["y"], 1, 0)
    return header[:28] + struct.pack("<I", fnv1a(header[:28] + payload)) + payload


def convert(extracted, output):
    extracted, output = Path(extracted).resolve(), Path(output).resolve()
    if extracted == output or extracted in output.parents or output in extracted.parents:
        raise ValueError("Output must be separate from source tree")
    if output.exists():
        raise ValueError("Output already exists; choose a new directory")
    boot = (extracted / "sys/boot.bin").read_bytes()
    if len(boot) < 0x440 or boot[:8] != b"SMNE01\x00\x02" or boot[24:28] != bytes.fromhex("5d1c9ea3"):
        raise ValueError("Expected SMNE01 disc 0 revision 2")
    raw = (extracted / "files/Stage/01-01.arc").read_bytes()
    entries = unpack_u8(raw)
    converted = []
    for name in sorted(entries):
        match = re.fullmatch(r"course/course([1-4])\.bin", name)
        if not match:
            continue
        area = int(match[1])
        layers = {i: entries[f"course/course{area}_bgdatL{i}.bin"] for i in range(3)
                  if f"course/course{area}_bgdatL{i}.bin" in entries}
        decoded = decode_course(entries[name], layers)
        scene = encode_scene(area, decoded)
        converted.append((area, decoded, scene))
    if not converted:
        raise ValueError("No course areas")
    # All parsing succeeds before any deliverable is written.
    output.mkdir(parents=True)
    manifest = {"format": "NSC1", "version": 1, "geometry_only": True, "playable": False,
                "disc_id": "SMNE01", "revision": 2, "stage": "01-01",
                "source_sha256": hashlib.sha256(raw).hexdigest(), "areas": [],
                "limitations": ["Object bounding boxes are not collision geometry.",
                                "Actor IDs are placements, not implemented enemy behaviors.",
                                "Textures, models, audio, and gameplay are not converted."]}
    for area, decoded, scene in converted:
        filename = f"01-01-area{area}.nsc"
        (output / filename).write_bytes(scene)
        (output / f"01-01-area{area}.json").write_text(json.dumps(decoded, indent=2) + "\n", encoding="utf-8")
        manifest["areas"].append({"area": area, "file": filename, "bytes": len(scene),
                                  "sha256": hashlib.sha256(scene).hexdigest(),
                                  "counts": {str(k): sum(r["kind"] == k for r in decoded["records"]) for k in range(4)},
                                  "actor_ids": decoded["actor_ids"], "tilesets": decoded["tilesets"]})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extracted", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = convert(args.extracted, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Conversion failed: {error}\n")
    print(json.dumps(result, indent=2))
