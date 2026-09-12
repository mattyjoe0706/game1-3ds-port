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
0.000025 per element; the head matched exactly. Maya segment scale compensation
now preserves child translation while cancelling the immediate parent's local
scale in the child's linear transform. Across all ten original Mario model
resources, reconstructed bind matrices differ by at most 0.000319 per element.
Singular parent scales and XSI animation scaling fail explicitly.
EVPMTX inverse-bind transforms and NODEMIX weighted
matrices are supported, with separate envelope and draw palettes.

A local Blender pilot of original PLMB/PLMH resources evaluated the 11 integer
samples of `PL_spin_jump` (2,151 triangles per pose). Bind-pose skin matrices
reconstructed identity within 0.000001 and stored inverse binds within 0.000002.
The pilot uses baked vertex animation, with a separate reference skeleton; it
is not an editable weighted Blender rig or a native 3DS model. Base-texture
appearance and animation timing still require comparison against the Wii game.
`character_texture.py` decodes I8, RGB565 and CMPR base mip levels.
`preview_character.py` renders a local textured pose comparison with NumPy/Pillow.

The software preview omits Wii TEV lighting and uses the base texture. The
handheld displays these baked poses as 2D sprites. General native 3D animation,
material effects and runtime costume selection remain future work.

Local original-asset inspection scenes now cover Small, Super, Fire, Ice,
Propeller and Penguin Mario. Fire and Ice use the original PB/PH texture
switches with open eyes kept independent of costume color. Small and Penguin
are delivered in bind pose: direct shared-animation application visibly
separates body parts, so their runtime binding adjustments remain unresolved.
Mini shares the Small model according to the USA executable's model table,
but its actor scale and effects are not yet verified. These scenes are not
new handheld builds and do not establish gameplay fidelity or performance.

Cap visibility: `mesh(..., wearing_cap=True)` suppresses `mat_player_hair`
when a resource has both separate hat and hair materials. `False` suppresses
the hat; `None` retains all geometry for raw inspection. The capped Blender
exports and software preview select `True`, avoiding exposed hair intersecting
the cap on MH/SMH. Helmet resources without both materials are unchanged.
This selection preserves source geometry; gameplay cap-removal transitions
are not yet implemented.

Format research used the primary MIT-licensed noclip.website source:
[BRRES parser](https://github.com/magcius/noclip.website/blob/master/src/rres/brres.ts)
and [GX display-list parser](https://github.com/magcius/noclip.website/blob/master/src/gx/gx_displaylist.ts).
The converter is an independent implementation. Synthetic tests contain no
Nintendo data and run with `python -m unittest discover -s tests`.
