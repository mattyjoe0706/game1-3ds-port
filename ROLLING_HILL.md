# Opening circular hill: HILL TEST 1

User update, 2026-09-10: HILL TEST 1 works well on the handheld. Rotation and
the remaining hill instances are explicitly deferred to the final World 1-1
fidelity/testing pass. See LEVEL_VALIDATION.md for the mandatory per-level process
and final original-game comparison. Static support acceptance is not acceptance
of complete rolling-hill behavior.

The missing terrain is actor 212, Rolling Hill. It is a separate textured
circle, not a deforming wave in the static tile layer. The local USA rev-2
course has the opening instance at (1456,544), settings 0x01301801. Reggie Next's
sprite definition identifies style 3 as 50 blocks across, speed nibble 11 as
zero and the low direction bit as clockwise. The original `circle_ground_L`
model is planar XY with radius 400. Its original RGB565 texture is 128x256.

References read for format facts (no source copied):
- https://github.com/NSMBW-Community/Reggie-Next/blob/master/reggiedata/spritedata.xml
- https://github.com/NSMBW-Community/Reggie-Next/blob/master/sprites.py
- https://github.com/NSMBW-Community/Reggie-Next/blob/master/spritelib.py

The editor circle outline uses a top-centre anchor and a half-tile X offset.
This implies world centre (1464,944), local centre (968,560), radius 400.
That anchor remains an inference requiring comparison with Wii execution.
The Wii actor update/rotation law has not been reconstructed. Only this exact
speed-zero instance is accepted; moving settings fail conversion rather than
receiving an invented animation. Camera framing and Mario scale are unchanged
and still need comparison with the original.

## Implementation

`tools/package_hill.py` reads the original course and circle_ground.arc locally.
It decodes the original mesh/UVs and bakes a front-facing 512x512 RGBA texture
with transparent surroundings (one MiB). No generated game assets belong in Git.
The native app draws this actor over the valley tiles and under enemies/Mario.
The offline scene preview was checked for buried grass showing through; draw
order was corrected. The current cropped terrain still leaves unfinished lower
edges/backgrounds; this milestone does not claim a complete visual scene.

NSH1 is 2592 bytes: magic, version, terrain FNV, texture FNV, local image X/Y,
segment count, checksum, then 160 little-endian float32 (x,width,leftY,rightY)
records. Header fields after magic are uint32. Checksum excludes bytes 28..31.
The four-unit chords cover the upper cap inside the existing vertical crop.
There is no underside collision. Existing one-way floor support handles both
player and enemy bodies. This is a circle approximation, not recovered Wii
collision code. The decoder checks bounds, continuity, nonfinite values,
checksums and matching terrain/texture. Repeated loads replace optional support.
Missing/invalid assets retain the prior static terrain and print a checkpoint.
The bottom display says `HILL TEST 1: loaded` when enabled; CSV includes its
loaded flag, texture checksum and additional texture bytes.

## Validation and next build

Portable C tests cover loading, slope transitions, jumping, pause and malformed
input. The actual hill package passes crest landing, jumping clear, downhill
walking both ways, 50 repeated loads, truncation and checksum/NaN rejection.
The four-enemy opening with hill completes in 344 simulated steps without death
using run/jump with a release on the crest. The old continuous auto-jump pattern
hits the fourth Goomba sideways; this is an input-pattern limitation, not a
reason to remove collision. These checks do not establish Wii gameplay fidelity.

A new native GitHub Actions build and handheld check are still required.
Prior 55-second performance acceptance applies to the previous build. The
additional texture and support scans have not been measured on the handheld.

Generate with `tools/package_hill.py EXTRACTED TERRAIN_NST NEW_OUTPUT` (NumPy and
Pillow required). Once the CI artifact is available, assemble one complete
delivery with `3ds/` and `cias/` directly inside it, retaining the matching
terrain/enemy/Mario data and adding `hill.nsh` and `hill.rgba` in the same data
directory. Do not distribute a separate data-only patch or stale executable.
