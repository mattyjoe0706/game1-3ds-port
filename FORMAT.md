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
