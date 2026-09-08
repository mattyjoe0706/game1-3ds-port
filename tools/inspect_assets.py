"""Inspect an extracted NSMBW disc. This is not a 3DS runtime converter.

Uses only Python's standard library; never writes to the source disc tree.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zipfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def unpack_u8(data):
    """Read bounded, uncompressed Nintendo U8 archives without extracting paths."""
    if len(data) < 32:
        raise ValueError("Truncated U8 header")
    magic, root, header_size, data_start = struct.unpack_from(">4I", data)
    if magic != 0x55AA382D:
        raise ValueError("Expected an uncompressed U8 archive")
    if root < 32 or root + header_size > data_start or data_start > len(data):
        raise ValueError("Invalid U8 section bounds")
    if header_size < 12:
        raise ValueError("Truncated root node")
    root_type, parent, count = struct.unpack_from(">3I", data, root)
    if root_type >> 24 != 1 or parent != 0 or count < 1:
        raise ValueError("Invalid U8 root")
    strings = root + count * 12
    header_end = root + header_size
    if strings > header_end:
        raise ValueError("Node table exceeds U8 header")
    stack = [(count, PurePosixPath(), 0)]
    result = {}
    seen = set()
    for index in range(1, count):
        while stack and index >= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError("Node outside root directory")
        kind_name, offset, size = struct.unpack_from(">3I", data, root + index * 12)
        kind, name_offset = kind_name >> 24, kind_name & 0xFFFFFF
        start = strings + name_offset
        if start >= header_end:
            raise ValueError("Name exceeds string table")
        end = data.find(b"\0", start, header_end)
        if end < 0:
            raise ValueError("Unterminated name")
        name = data[start:end].decode("ascii")
        if name in ("", ".", "..") or any(c in name for c in "/\\:"):
            raise ValueError("Unsafe archive path")
        path = stack[-1][1] / name
        key = str(path)
        if key.casefold() in seen:
            raise ValueError("Duplicate archive path")
        seen.add(key.casefold())
        if kind == 1:
            if offset != stack[-1][2] or not index < size <= stack[-1][0]:
                raise ValueError("Invalid directory bounds/parent")
            stack.append((size, path, index))
        elif kind == 0:
            if offset < data_start or offset + size > len(data):
                raise ValueError("File exceeds data section")
            result[key] = data[offset:offset + size]
        else:
            raise ValueError("Unknown U8 node type")
    return result


def course_blocks(data):
    """Preserve all 14 course blocks, without guessing gameplay semantics."""
    if len(data) < 112:
        raise ValueError("Truncated course block table")
    result = []
    spans = []
    for index in range(14):
        offset, size = struct.unpack_from(">II", data, index * 8)
        if offset + size > len(data) or (size and offset < 112):
            raise ValueError("Course block exceeds file or overlaps header")
        if size:
            if any(offset < b and offset + size > a for a, b in spans):
                raise ValueError("Overlapping course blocks")
            spans.append((offset, offset + size))
        result.append({"index": index, "offset": offset, "bytes": size,
                       "sha256": sha256(data[offset:offset + size])})
    return result


def prepare(extracted, destination):
    extracted, destination = Path(extracted).resolve(), Path(destination).resolve()
    if destination == extracted or extracted in destination.parents or destination in extracted.parents:
        raise ValueError("Output must be separate from the extracted disc tree")
    if destination.exists():
        raise ValueError("Output already exists; choose a new directory")
    boot = (extracted / "sys/boot.bin").read_bytes()
    if len(boot) < 0x440 or boot[:6] != b"SMNE01" or boot[7] != 2:
        raise ValueError("This inspection targets SMNE01 revision 2")
    if boot[0x18:0x1c] != bytes.fromhex("5d1c9ea3"):
        raise ValueError("Wii disc magic mismatch")
    stage = (extracted / "files/Stage/01-01.arc").read_bytes()
    entries = unpack_u8(stage)
    courses = {}
    for name, data in entries.items():
        path = PurePosixPath(name)
        if path.parent == PurePosixPath("course") and path.stem.startswith("course") and path.suffix == ".bin" and "_" not in path.stem:
            courses[name] = course_blocks(data)
    if not courses:
        raise ValueError("World 1-1 contains no recognized course files")
    manifest = {
        "format": "nsmbw-source-inspection", "version": 1,
        "playable": False, "disc_id": boot[:6].decode(), "revision": boot[7],
        "region": "USA", "stage": "01-01", "archive_sha256": sha256(stage),
        "warning": "Raw Wii course data: no texture/model/audio conversion or 3DS runtime is included.",
        "entries": [{"path": n, "bytes": len(d), "sha256": sha256(d)} for n, d in sorted(entries.items())],
        "course_blocks": courses,
    }
    destination.mkdir(parents=True)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(destination / "world-1-1-source.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extracted", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.extracted, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Inspection failed: {error}\n")
    print(f"Inspected {len(result['entries'])} archive files and {len(result['course_blocks'])} course areas. Not a playable package.")
