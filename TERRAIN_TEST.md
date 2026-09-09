# Terrain test 1

This revision connects the native player controller to a converted opening section
of World 1-1 and draws original static terrain textures. The section spans original
world X=496..1904 and Y=384..704. It is a terrain/movement test, not a completed
World 1-1: the player remains a yellow rectangle; no enemies, items, Mario
animation, music or original background scene are implemented. Coins are visual
only, blocks do not release items, and the green section marker is an authored
test endpoint, not the Wii goal.

## Building and installing

Push the updated source repository to run its existing GitHub Actions workflow.
CI now compiles `source/terrain.c` and runs the terrain collision/loader tests.
The output names remain `nsmbw-inspector.3dsx` and `nsmbw-inspector.cia`.
This revision has not yet been compiled with devkitARM or tested on the handheld.
The existing CIA-launch issue is not addressed by terrain integration; use the
previously successful Homebrew Launcher route for the next validation.

Generate the separate local data with:

```text
python tools/package_terrain.py PATH_TO_VALIDATED_EXTRACTION PATH_TO_NEW_OUTPUT
```

The resulting `SD-ROOT/3ds/nsmbw-prototype/data/` contains `terrain.nst` and
`terrain.rgba`. Merge those files onto the SD card along with the newly built
`3ds/nsmbw-prototype/nsmbw-inspector.3dsx`. Preserve the existing area1/area2 NSC1
files for the outline inspector. Do not replace any system files. The data alone
does not update an older executable. Generated Nintendo-derived data stays outside
the public repository; the build needs only source.

Open the **nsmbw-prototype** folder in Homebrew Launcher and launch the inspector.
Continue past the two startup prompts with A. Expect **TERRAIN TEST 1**, grassy
terrain and a yellow player. If the new data is missing, malformed or mismatched,
startup reports the error and falls back to the authored course. Add both matching
data files and relaunch; the texture is allocated/loaded once per launch.

Controls: D-pad/Circle Pad moves, A/B jumps, Y runs, Down crouches, touchscreen
restarts, Start pauses, Select cycles authored test / area 1 outlines / area 2
outlines / terrain. Switching into either playable test resets its player.
Select+Start saves a `viewer-*.csv` capture and returns to the launcher.
CSV mode 3 identifies this terrain section. Texture bytes and selected static
buffer bytes are recorded separately; these are not total application memory.

## Implementation and validation

- NST1 is a versioned, bounded binary package with a checksum covering header
  metadata and tile records, plus a checksum binding the 1 MB texture atlas.
- One shared 512x512 GPU RGBA8 atlas uses 16x16 tiles sampled from the original
  24x24 useful tile interiors, with nearest filtering. Visible tiles use citro2d's
  batching. The 640x360 view is scaled proportionally to 400x225 with letterboxing.
- The native loader has fixed arrays for at most 2,048 tile records and collision
  primitives, validates dimensions, references and reserved fields, and clears the
  active level on rejection. The delivered local section has 323 tiles.
- Full solid tiles connect to the existing swept rectangle collision. Ramps use
  floor support surfaces with foot-centre sampling and a bounded transition to
  adjoining flat tiles. Top-only platforms allow jumps from below. These are
  approximate support mechanics, not reconstructed Wii physics; ramp side and
  underside collision are not yet modeled as solid polygons.
- 45 marker tiles with flags `0000000000000028` are omitted from this test;
  `0000000200000000` tiles remain decorative (no pickup behavior). Unsupported
  collision classes in the selected section stop conversion.
- Portable C tests pass for uphill/downhill transitions, ramp jump release,
  one-way platform traversal/landing, pause, invalid input, and 50 repeated loads.
  Existing authored controller regression tests also pass.
- The actual local NST1 package loads in the same C decoder under WebAssembly.
  An automated run traverses the opening flat without jumping, then completes
  the section using jumps in 348 fixed updates with no deaths. This is a controller
  regression check, not a timing or Wii fidelity measurement.
- Python: 34 tests ran, 33 passed and one optional original-data test skipped.
  Atlas tests check sample positions, GPU byte order, orientation and tiled
  addresses. Native texture orientation still needs handheld confirmation.

## Next handheld checks

Verify readable, correctly oriented terrain, walk/run in both directions over the
slopes, jump onto the raised blocks/platforms, pause/resume, restart repeatedly,
and reach the green section marker. Save a mode-3 capture with Select+Start.
Report clipping, snagging, texture artifacts or crashes. Native compilation and
the real hardware capture are required before making a performance claim.
