# NSC1 v1 development format

This package stores placement inspection data. Its geometry-only flag must be set. No collision or actor behavior is implied.

All integers are little-endian. The 32-byte header is followed by exactly `count` 24-byte records, with no trailing bytes.

| Header offset | Field |
|---|---|
| 0 | Four ASCII bytes `NSC1` |
| 4 | u32 version, 1 |
| 8 | u32 course-file/area number, 1–4 |
| 12 | u32 record count, 1–4096 |
| 16 | u32 inspection-view origin X, 0–65535 |
| 20 | u32 inspection-view origin Y, 0–65535 |
| 24 | u32 flags, exactly 1 (geometry only) |
| 28 | u32 FNV-1a checksum of bytes 0–27 followed by bytes 32–end |

FNV-1a uses seed 2166136261 and multiplier 16777619 with 32-bit wrapping. It detects accidental corruption; it is not cryptographic authentication. SHA-256 values are also recorded in the external manifest.

| Record offset | Field |
|---|---|
| 0 | u8 kind: 0 object bounds, 1 map actor, 2 entrance, 3 zone |
| 1 | u8 layer, 0–2 |
| 2 | u16 object/actor/entrance/zone ID |
| 4, 8 | i32 X and Y in source-level pixels, Y increases downward |
| 12, 16 | i32 width and height in pixels |
| 20 | u32 actor parameter or entrance type; zero otherwise |

Coordinates must be nonnegative and at most 1,048,560. Dimensions must be 1–1,048,560. Object IDs retain their packed tileset-slot bits. Map actor and entrance markers use 16×16 inspection rectangles; these are **not their actual hitboxes or visual sizes**.

The source course headers/entrance/actor/zone layouts follow the pinned decompilation's structures and compiler padding. Layer object records are interpreted as five big-endian u16s (packed ID, tile X, tile Y, tile width, tile height) followed by FFFF. Tile values are multiplied by 16 for display. Tile expansion and behavior remain unresolved.

Each original course is kept as JSON alongside its native inspection package, including its declared initial entrance ID. A subarea may lack that entrance because gameplay enters through a pipe/door destination. Its viewer origin uses the first listed entrance and explicitly records that policy; a game runtime must resolve the actual incoming entrance instead.
# NST1 terrain section (version 1)

The separate `terrain.nst` file has a 36-byte header: four magic bytes `NST1`,
then eight little-endian u32 values: version, tile count, world width, world height,
spawn x, spawn y, texture FNV-1a, package FNV-1a. Package hash covers bytes 0..31
followed by all records, excluding its own four bytes. FNV-1a uses offset
2166136261 and multiplier 16777619 with u32 wrapping. These are accidental
corruption checks, not cryptographic authenticity checks.

Each 12-byte record uses `<HHHBBBBH`: x, y, atlas tile ID, collision kind, left
surface height, right surface height, layer, reserved zero. Coordinates are local
pixels aligned to 16; heights are relative 0..16. Kinds are 0 decorative,
1 solid 16x16, 2 one-way floor support. Collision applies only on layer 1.
Records are in background-to-foreground draw order. Count capacity is 2048;
width is 640..4096 and height is 64..1024, with all tiles/spawn in bounds.

`terrain.rgba` is exactly 1,048,576 bytes: 512x512 RGBA8 in GPU ABGR byte order,
8x8 Morton tiles, vertically flipped relative to a top-left source image. Atlas
IDs 0..767 occupy 32 columns of 16x16 tiles. The header texture hash binds this
file to its level. Missing, trailing, truncated or mismatched data is rejected.

See TERRAIN_TEST.md for current physical approximations and scope. The older
NSC1 outline format above remains supported independently.

# NSE1 enemy placements (version 1)

`enemies.nse` has a 24-byte header: magic NSE1, then five little-endian u32
values: version 1, count (0..32), FNV-1a of the complete matching terrain.nst,
reserved zero, package FNV-1a. The package checksum covers bytes 0..19 followed
by records, excluding its own bytes 20..23. Each record is four little-endian
u16 fields: local x, local y, actor ID 20, reserved zero. The 16x16 enemy must
fit the selected terrain bounds. Unknown actors/settings, trailing bytes, bad
checksums or wrong terrain bindings are rejected. A checksum is an accidental
corruption check, not an authenticity signature.
