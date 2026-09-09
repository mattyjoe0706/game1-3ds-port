# Mario conversion progress

The character converter produces an offline intermediate representation. The
separate `package_character.py` now bakes selected poses for the native sprite
renderer; see [MARIO_SPRITE_TEST.md](MARIO_SPRITE_TEST.md).

Run `python tools/convert_character.py EXTRACTED_DISC NEW_OUTPUT_DIRECTORY`.
Use the existing extracted SMNE01 revision 2 disc tree, including `sys/boot.bin`,
`files/Object/Mario.arc` and `files/Object/P_rcha.arc`. The output must be a new
directory separate from that tree. Original files are read only. Keep output
outside this public repository because it contains converted game data.

## Implemented and checked

- BRRES resource tables, MDL0 version 11 skeletons and position arrays.
- Indexed triangles, strips and fans, retaining each corner's separate GX
  attribute indices and each draw's matrix-load state. Position indices are
  checked against their arrays; shape vertex and triangle counts must match
  the original headers. Normal, RGBA8 color and UV indices are also resolved and bounds checked.
- CHR0 version 5 constant, packed and floating-point animation channels,
  including Hermite interpolation and sampled channels.
- Bounds, capacity, finite-number and skeleton-cycle checks. Unsupported
  display-list commands and vertex formats fail explicitly.

The supplied local disc decoded successfully into 10 model resources, 20 shapes
and 262 animation clips. All shape vertex/triangle counts matched. Each decoded
animation channel was sampled at its beginning, midpoint and end for finite
results. These checks establish structural decoding, not visual fidelity.

Output format `character-intermediate`, version 3:

- `models.json`: bones, positions, triangle topology, raw attribute indices and
  unresolved matrix references. Attribute keys use GX numeric attribute IDs.
- `animations.json`: named animation channels and flags. Missing channels still
  require the original model defaults during pose evaluation.
- `manifest.json`: source archive SHA-256 hashes, counts and explicit limitations.
  `native_ready` remains false.

## Pose and texture support

`character_mesh.py` decodes attributes, material samplers and scene commands.
`character_pose.py` evaluates rigid matrix hierarchies and attaches the head to
`face_1`. Reconstructed MB bind matrices matched the stored matrices within
0.000025 per element; the head matched exactly. General parent scale compensation
and matrix blends fail explicitly; the selected sprite poses avoid those cases.
`character_texture.py` decodes I8, RGB565 and CMPR base mip levels.
`preview_character.py` renders a local textured pose comparison with NumPy/Pillow.

The software preview omits Wii TEV lighting and uses the base texture. The
handheld displays these baked poses as 2D sprites. General native 3D animation,
material effects and other costume assemblies remain future work.

Format research used the primary MIT-licensed noclip.website source:
[BRRES parser](https://github.com/magcius/noclip.website/blob/master/src/rres/brres.ts)
and [GX display-list parser](https://github.com/magcius/noclip.website/blob/master/src/gx/gx_displaylist.ts).
The converter is an independent implementation. Synthetic tests contain no
Nintendo data and run with `python -m unittest discover -s tests`.
