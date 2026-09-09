# Mario sprite test 1

This source replaces the yellow player with animated sprites baked locally from
the original Mario body/head models, texture coordinates and base textures.
It adds 512 KiB of GPU texture storage and one sprite draw per visible player.
Idle has 4 poses; walk and run have 8 each; air has one fixed pose. Left movement
mirrors the sprite. Pause freezes animation; restart resets it.

The camera remains proportional at 400x225 within the 400x240 screen. Existing
collision dimensions and gameplay remain unchanged. Crouch currently compresses
the idle visual to half height, matching the shorter collider; it is not the
original crouch animation. Wii lighting/TEV effects, expression animation,
power-up costumes and native 3D character rendering are not implemented. Enemies
still use temporary visuals and there is no audio.

## Build and local data

Push the authored source changes to the existing repository and use its native
GitHub Actions workflow to build the updated application. No new native binary
has been compiled locally, and handheld performance is not yet measured.

To recreate the private assets, install NumPy and Pillow on the converter host,
then run `python tools/package_character.py EXTRACTED_DISC NEW_OUTPUT_DIRECTORY`.
The tool validates SMNE01 revision 2, converts the models, poses selected
animations, checks cell bounds, and writes the sprite atlas and its checksum.
Its output contains original game data and must stay out of the public repo.

With the console off, copy the contents of the generated `SD-ROOT` directory to
the SD card root. It adds only these two files:

- `/3ds/nsmbw-prototype/data/mario.nsp`
- `/3ds/nsmbw-prototype/data/mario.rgba`

Keep the existing terrain/enemy data. Replace the inspector `.3dsx` with the new
CI build, then launch it through Homebrew Launcher. Older binaries will ignore
these new data files. CIA packaging remains available, but its launch path has
not been revalidated by this change.

The bottom screen should say `Mario sprite test 1: loaded`. A missing, oversized,
truncated or corrupt package falls back to the yellow player and records the
reason in `/nsmbw-startup.log`. Allocation failure also uses that fallback.

## Hardware acceptance still required

Check facing, idle, walking, running, jumping, crouching, pause/resume, contact
damage, stomps, touch restart and repeated relaunches. Check feet alignment on
slopes and that sprites do not disappear at the view edges. Missing or corrupted
Mario files should leave the existing movement test usable.

Capture a full 60-second run and a run with interactions. SELECT+START saves and
exits. The existing `viewer-*.csv` location is unchanged; new comment fields
identify `mario_sprite_test=1`, whether it loaded, and its texture bytes. Compare
frame-time distributions against Enemy test 1. Animation frames are sampled
poses; simulation and display still target 60 Hz. No 60 fps claim is made yet.

## NSP1 version 1

Fixed 32-byte little-endian header: magic `NSP1`, version 1, width 512, height 256,
cell size 64, frame count 21, FNV-1a of the 524288-byte texture, then FNV-1a of the
preceding 28 header bytes. Frames occupy successive 64x64 cells, 8 cells per row.
Texture pixels use the same vertically flipped 8x8 Morton/ABGR layout as terrain.
The loader requires exact dimensions, version, count, lengths and checksums.
