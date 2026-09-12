# World 1-1 opening interactions: ITEM TEST 1

## Source evidence and scope

The former static converter discarded the top six bits of each object's tile
descriptor. `definition(..., preserve_contents=True)` now retains them for the
interaction converter without changing the existing terrain package or atlas.
The descriptor format was checked against Reggie Next's object_def.py and
loaders.py; object 45 is the Propeller question block, extra value 7.

The opening package has 13 records: three question blocks, two plain bricks,
five tile coins and three actor-147 coins. Original question-block positions:

| World position | Content |
|---|---|
| 928,544 | Coin |
| 1056,544 | Coin |
| 1056,480 | Propeller Mushroom |

The full source inventory covers both course files and retains all actor records
for later interpretation. Area 1 has three tile-based Propeller question blocks,
at (1056,480), (3440,496), (4496,480); only the first is in the playable crop.
Other reward sources outside the crop are inventoried but not implemented here.
Hidden-block tile candidates (Pa0 IDs 3..13) are retained even with zero extra
bits; their contents must be checked from tile identity/collision flags instead.
They fail explicitly if encountered in this opening converter's playable scope.

Original USA rev-2 main.dol was read without modification. The block selection
routine at 0x800221E0 branches at 0x80022258 for one player and stores the requested
item unchanged at 0x80022260, bypassing the multiplayer big-player count. The
big-player predicate at 0x80022180 distinguishes Small/Mini from powered forms.
This checks selection at the block boundary; it does not establish every later
item initialization rule or every reward source in the game.

Local research is under work/powerup-research outside Git, including the original
disassembly and full private inventory. Additional research:
- https://github.com/NSMBW-Community/Reggie-Next
- https://github.com/mkwcat/nsmbw-project/tree/116f1ec480b7ad5d50945ec46d69a6d767cf3f55
  (modified-game source used to locate original routines; original DOL was then checked).
- https://nsmbw-community.github.io/NSMBW-Decomp/docs/game__constants_8h.html
- Nintendo's NSMBW instruction booklet: Propeller Mushroom transformation and
  shake-to-boost behavior, remapped here to R.

## Implemented behavior

The opening starts in Small state with a 16-unit-high collider. Super/Propeller
use 32; growth preserves feet and stays crouched under a low ceiling. A Propeller
pickup upgrades Small directly and does not downgrade an already-powered player.
The state/reward tests cover Small, Super and existing Propeller. A separate
pickup test checks that a Super Mushroom grows Small Mario but does not downgrade
Propeller Mario. No Super Mushroom is invented in the opening placements. The
original-data loader rejects all unimplemented block content values.

Question blocks trigger on upward head contact, bump, become used and pay once.
Coins disappear on collection and increment the displayed counter. Plain bricks
bump for Small Mario and break for larger forms, removing their solid collider.
Pickups emerge before collection, then move; direction is initially away from
the player's horizontal position. Their speeds/trajectories remain approximations.
R performs one Propeller boost per airborne sequence, landing recharges it;
descent is slow until Down is held. Original propeller drilling attacks and
animation timing remain unfinished. R no longer opens the sprite sheet in the
real opening; it still does so in the authored diagnostic course.

Prototype damage reduces Propeller to Super, then Small, then death, with 127
ticks of blinking invulnerability after a shrink. Ordinary-enemy damage behavior
still needs an original-game comparison (the available decoded shrink evidence
includes the eat-damage path, not every damage path). Death and touch restart
restore blocks/coins/pickups and start Small. The prototype coin counter resets
with the scene; complete game score/lives persistence is not implemented.

The pickup icons are baked from I_kinoko.arc and I_propeller.arc with original
base textures into a 128x64 atlas (32768 bytes). Mario still uses the existing
atlas, compressed for Small, with a temporary rotor marker in Propeller state.
The converter now handles PLMB/PLMH NodeMix skinning, validated in a local Blender
Propeller Mario animation pilot. This has not yet been packaged into the native
application; suit appearance on 3DS remains an unresolved fidelity item.
Used blocks have a simple drawn appearance. No new audio is implemented.

## Data and validation

NSI1 header is 24 bytes: magic, version, record count, terrain FNV, texture FNV,
checksum (all fields after magic little-endian u32). Checksum skips bytes 20..23.
Each 12-byte record has x/y/terrain-tile-index (u16), kind/content (u8), zero u32.
Index 65535 means an actor coin. The decoder checks bounds, duplicate positions,
the referenced terrain tile/collider, contents and checksums. Unsupported contents
fail explicitly. Optional missing/bad graphics use simple icons with a checkpoint;
missing/bad interaction data leaves the existing static terrain unchanged.

Portable tests cover original descriptor bits, corruption and mismatch rejection,
actual head collisions, single-use rewards, reachable original Propeller block,
growth beneath ceilings, Small/Super/Propeller transitions, damage/invulnerability,
boost recharge, pause, death/restart, brick collision removal and repeated loads.
These are host/WASM tests; native compilation and handheld testing are still due.
CSV identifies ITEM TEST 1, item loading, power/coin state and extra buffer/texture
sizes. No new 60-fps or full-level fidelity claim is made.

Local validation: 67 Python tests (66 pass, one optional skip), all six portable
C test groups pass, original 13-record item package passes, and the combined
terrain/hill/enemies/items pipeline passes contact and restart checks.

Generate with tools/package_items.py EXTRACTED TERRAIN_NST NEW_OUTPUT. Pillow
and NumPy are required. Keep outputs outside the public repository. After the
new CI build arrives, deliver one complete folder containing 3ds and cias with
the existing matching terrain, hills, enemies and Mario plus items.nsi/items.rgba.
See LEVEL_VALIDATION.md for the required per-state power-up audit and final pass.
