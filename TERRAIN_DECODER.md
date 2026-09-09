# World 1-1 terrain decoder

**Superseded integration status:** [TERRAIN_TEST.md](TERRAIN_TEST.md) describes the
native terrain test added after this decoder milestone. The inspection format
below remains separate from the new NST1 runtime package.

The local converter now expands area 1 object placements into individual tiles
and decodes the original static tileset images. This is an inspection milestone.
The native application still runs the authored movement test and placement
viewer; it does not yet load this new output.

Run with Python 3, using the previously validated extracted SMNE01 revision 2
disc directory and a new output directory outside both the extraction and public
repository:

```text
python tools/convert_tiles.py PATH_TO_EXTRACTION PATH_TO_NEW_OUTPUT
```

The converter checks the disc header, bounds decompression and object expansion,
and refuses to overwrite an output directory. It does not replace the original
disc integrity verification. No external Python dependencies are needed.

Output is `manifest.json`, `terrain.json`, three original tileset PNGs, and
`world-1-1-terrain.png`. These contain Nintendo-derived data: keep them local,
outside the source repository. The manifest records SHA-256 hashes of the input
stage and tilesets and labels the output non-playable. This JSON inspection format
is version 1; it is not the existing NSC1 runtime format.

## Validation on 2026-09-08

- Expanded all 640 area 1 placement objects. Every expanded tile array matched
  Reggie-Next's renderer at commit
  `f7a73d60853e9143eddb92396e7b4e33f9c2de6a`, including diagonal stamps, after
  normalizing empty cells. This verifies agreement with the editor, not the Wii
  executable or its collision behavior.
- The composed layers contain 3,759 nonzero tile cells after placement overlap.
- Layer 1 contains 1,865 tiles classified as solid, 232 floor slopes, 26 ceiling
  slopes, 82 top-only tiles, 3 bottom-only tiles, 69 empty-collision tiles, and
  399 tiles whose flags remain classified as other.
- The unclassified flags are `0000000000000028` (271 cells) and
  `0000000200000000` (128 cells). They must not become solid merely because an
  object has a rectangular placement box. Raw flags and shape IDs are retained.
- Visually inspected the opening terrain preview: grassy ground, stepped edges,
  slopes, bricks and question blocks are recognizable. Dotted placeholder tiles
  and static animation source pixels remain visible. They need runtime-specific
  visibility/animation handling; this image is not a screenshot of the game.
- 30 Python tests ran: 29 passed and the existing optional local game-data test
  skipped. New cases cover malformed compression, overlapping backreferences,
  both extended LZ11 lengths, texture channels/block order, PNG checksums,
  repeating edges, four diagonal directions and allocation bounds.

## Work remaining before another handheld build

Define and validate a bounded native tile/texture package, connect the real tile
collision surfaces to the player, and implement slope transitions and one-way
platform behavior with regression tests. The texture path must upload the decoded
images in the 3DS GPU format and draw only visible tiles. Resolve the retained
collision flags and special/animated tile visibility before calling the scene
faithful. Keep the working authored movement scene available for regression
testing. No new 3DS performance claim follows from the desktop preview.

The current approximate movement controller, absent enemies, item behaviors,
Mario graphics, audio and background systems still prevent a complete playable
World 1-1. A CIA rebuild of the unchanged native code would not add this terrain.

## Format references

Independent decoder implementation informed by the following primary editor
sources at the pinned commit:

- [Object records](https://github.com/NSMBW-Community/Reggie-Next/blob/f7a73d60853e9143eddb92396e7b4e33f9c2de6a/src/data/tileset/object/object_def.py)
- [Object expansion](https://github.com/NSMBW-Community/Reggie-Next/blob/f7a73d60853e9143eddb92396e7b4e33f9c2de6a/src/data/tileset/object/renderers.py)
- [Tileset loading and atlas layout](https://github.com/NSMBW-Community/Reggie-Next/blob/f7a73d60853e9143eddb92396e7b4e33f9c2de6a/src/data/common/loaders.py)
- [Collision overlays](https://github.com/NSMBW-Community/Reggie-Next/blob/f7a73d60853e9143eddb92396e7b4e33f9c2de6a/src/data/tileset/tile/tileset_tile.py)

The reference editor is GPL-3.0-or-later. Its source was used locally for format
research and differential validation and is not bundled with this converter.
