# World 1-1 opening fidelity audit

Update: the user confirmed the corrected terrain on hardware. Current native
work adds actor 212's circular opening hill; see ROLLING_HILL.md. Actor 310 is
Signboard Arrow, 477 is Super Guide Block, and 147 is Coin; those behaviors
remain unimplemented. The no-compilation delivery below describes the preceding
texture correction, not the new hill milestone.

## Completed: terrain visual correction

The terrain converter reversed the entire atlas vertically before packing it.
With the renderer's ordinary Tex3DS UVs, all 43 distinct tile images used by the
opening section resolved to different images. Packing revision 2 uses the same
top-down RGBA8 Morton layout already tested with the corrected Mario assets.

The local audit checks every pixel in those 43 images against the sampled
original tileset PNGs. It also compares the multiset of tile positions, IDs and
layers against the expanded original course data: all 323 records match. The
45 invisible marker tiles are deliberately excluded. The original decoding was
previously checked against the reference editor for all 640 area-1 objects.
These are data checks; they do not substitute for comparing Wii execution.

Terrain records, collider records, section bounds and spawn are unchanged.
Only texture bytes and binding checksums change. The four original Goomba
placements also match; their NSE1 package is regenerated because it is bound to
the entire terrain package. Never mix an old enemy package with this terrain.

## What is and is not faithful yet

The test covers original X=496..1904, Y=384..704, not the whole area. The original
area-1 zone spans X=528..7328, Y=256..641. Original entry 0 is at (752,592).
The prototype uses local player top-left (256,192), corresponding to (752,576),
and a 32-high collider with feet at original Y=608. Matching entrance X does not
establish correct entrance animation, Mario scale or vertical actor convention.

Inside the slice the source contains ten actor placements. Four are Goombas
(actor 20). Six remain unimplemented: actor 212 once, 310 once, 477 once, and 147
three times. Their raw decoded coordinates/settings are recorded in the private
audit JSON; identities and behavior need reconstruction before claiming fidelity.
One actor anchor near the right edge may extend beyond the test crop.

The foreground contains 270 solid-class tiles, 27 floor-slope tiles, three
top-only tiles, 18 empty-class tiles and five other-class tiles. The last five
are decorative coins. Blocks have static images but no bump/item behavior.
Ramps use approximate one-way support; sides and undersides are not solid
polygons. Original background models, audio and tile animation/randomization
are absent. Enemies still have temporary visuals.

Movement constants are authored: walk 2.25 and run 4 world units/update,
acceleration 0.4, braking 0.5, initial jump velocity -9.4, gravity 0.4 and terminal
fall speed 10. They have not been derived from Wii gameplay. The camera puts the
player at 35% of a 640-unit view and fixes vertical position; the original camera
rules, framing and model scale remain unverified. The green endpoint is authored,
not the original goal pole. The original area continues well beyond this crop.

## Validation and delivery

Python: 62 tests, 61 passed and one optional test skipped. Synthetic texture
tests cover all three tileset slots and top/bottom orientation. The corrected
package passes the compiled portable C loader. Terrain traversal completes in
348 updates without death; the four-enemy traversal test completes in 346 updates
without death. These are regression checks, not measured Wii fidelity.

The prior Mario milestone is accepted based on upright/visible hardware behavior
and 55 seconds at 59.83 fps without frame spikes or discarded updates. It need
not be repeated merely to reach 60 seconds. Corrected terrain still needs a
visual hardware check; unchanged texture size does not prove unchanged timing.

The complete local delivery contains `3ds` and `cias` together and reuses the
verified diagnostic-2 application from CI build (7). It replaces terrain.nst,
terrain.rgba and enemies.nse as a matching set while retaining the verified Mario
assets. No new compilation is needed. Open the extracted folder and upload its
`3ds` and `cias` subfolders directly to the remote SD root; do not upload the
outer delivery folder. Keep unrelated SD files. Launch through Homebrew Launcher.

Reproduce with `tools/package_terrain.py`, then `tools/package_enemies.py` against
the resulting terrain.nst. Run `tools/audit_opening.py` with the extracted disc,
new terrain output directory, matching enemies.nse, prior terrain.rgba and a new
audit output directory. Pillow is needed for audit previews; game data remains
outside the public repository.

Next fidelity work: reconstruct the missing opening actors and block/coin
interactions, compare camera/player scale and movement against Wii reference
play, improve Mario and enemy rendering, then extend toward the original goal.
