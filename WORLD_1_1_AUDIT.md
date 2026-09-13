# World 1-1 implementation audit

Scope: source-data and current-code audit. This is not the final comparison
against Wii execution, and it does not establish full-level fidelity.

The supplied USA revision-2 `01-01.arc` contains two areas. Area 1 has one
zone, 640 terrain-object records and 77 actor records. Area 2 has two zones,
184 terrain-object records and four actor records. Object records are not
individual rendered tiles. Actor names below come from the locally retained
reference editor's sprite definitions; raw settings are retained separately.
The reproducible local inventory is `outputs/world-1-1-audit/inventory.json`.

## Accepted opening evidence

The user reports that build 11 with the matching data works on New 3DS XL:
coins and power-ups can be collected, power-up transition animations play,
and Mario changes form. Preserve these results; do not repeat movement testing
for a documentation-only change. This report does not imply that damage,
every power-up state, all remapped actions or performance were tested.

Build 17's isolated Koopa scene is also accepted by the user: shell pickup
waits through the upward stomp bounce, and holding Y/X allows pickup as soon
as Mario returns within range. Preserve that test scene and its controls.

The current playable crop is original X=496..1904, Y=384..704. The main
zone continues to X=7328. Its green endpoint is an authored test marker,
not the original goal. The other area can be inspected as placements but
has not been implemented as a playable bonus area with pipe transitions.

## Main-route actor inventory

| Feature | ID | Instances |
| --- | ---: | ---: |
| Goomba | 20 | 21 |
| Koopa Troopa | 57 | 6 |
| Star Coin | 32 | 2 |
| Red Coin | 144 | 8 |
| Coin actor | 147 | 13 |
| Red Coin Ring | 156 | 1 |
| Midway Flag | 188 | 1 |
| Ordinary rolling hill | 212 | 4 |
| Rolling hill with one pipe | 355 | 1 |
| Rolling hill with eight pipes | 360 | 1 |
| Goal Pole and Fortress | 113 | 1 |
| Arrow sign | 310 | 7 |
| Toad Needs Help block | 422 | 1 |
| Light Cloud Area effect | 446 | 8 |
| Super Guide block | 477 | 2 |

There are SIX rolling-hill actors, including the two pipe variants. The
earlier count of four covered only ID 212. Rotation, transport and all
instances remain deferred to the agreed final fidelity milestone; their
placement and dependency must be tracked during route expansion.

Area 2 contains the third Star Coin, a P-Switch, and two background parallax
center actors. It has two bonus-room zones. The source links main-area
entrances 4, 5, 6 and 7 to area-2 entrances 3, 4, 5 and 6 respectively,
with corresponding return links. Entry type/flags, permitted travel direction,
pipe animation and collision must be verified before enabling traversal.

Actor coin counts exclude coins encoded in terrain objects or block contents.
The complete reward inventory and state-dependent selection still need an
audit across both areas. Current reward code supports the tested coin and
Propeller descriptors; it deliberately rejects other unverified descriptors.

## Missing systems and constraints

- The native enemy runtime supports tested Goomba/Koopa and shell interactions.
  The opening contains four Goombas and no Koopas; the next section contains
  six more Goombas and two ordinary green Koopas. Do not invent opening Koopas.
- Shared section coordinates now cover the opening and checkpoint candidate.
  Terrain, enemy and item converters accept `--section checkpoint`; the default
  remains `opening`. This is conversion support, not a playable route release.
  The combined candidate has 989 static tile records, within the existing 2048
  capacity. Full-area sizing/paging remains a separate task.
- Pipe traversal, both bonus rooms, P-Switch behavior, Star Coins, red-ring
  timer/reward and real goal completion are missing. In-session checkpoint
  activation/death restart now has prototype support; persistent save/world-map
  return behavior is still missing.
- Toad/Super Guide conditional activation needs source verification. Their
  presence in the archive does not mean they are active on every playthrough.
- Full camera rules, player movement fidelity, backgrounds, finished enemy
  visuals, effects, audio and remaining graphics work are open.
- Mini size and additional power-up behavior remain unverified; they must be
  checked when relevant rather than substituting the currently supported forms.

## Implementation stages

1. **Koopa and shell interactions.** A bounded integration scene using the
   existing collision/player systems: stomp, kick, carry with held Y/X, throw
   on release, damage, pause and reset. Validate source behavior and meaningful
   automated cases before asking for one focused hardware test.
2. **Extend the route toward the checkpoint.** Target source X=1904..3312,
   which contains six Goombas, two Koopas, the eight-pipe hill and the midpoint
   flag. Generalize section packaging and implement checkpoint state. Keep
   deferred hill dynamics explicit; this is not yet a faithful traversal claim.
3. **Pipe travel and bonus rooms.** Implement linked entrances, the P-Switch
   and the bonus Star Coin, including return routes and restart behavior.
4. **Remaining main route.** Place remaining enemies/items, red-ring challenge,
   Star Coins and original goal sequence. Reconcile all actor instances.
5. **Final behavior and graphics passes.** Complete deferred hills, compare
   every section with original Wii gameplay, then finish graphics quality.
   Follow graphics changes with final hardware/performance acceptance before
   calling the level complete. Intermediate test packages remain allowed.

Stage 1 is accepted. Stage 2 now has a bounded checkpoint-route prototype ready
for native CI compilation and then manual device testing with its complete
matching data. This is not full World 1-1 acceptance or a faithful final release.

## Checkpoint route conversion gate

Run `tools/audit_route.py EXTRACTED TERRAIN_JSON NEW_REPORT --section checkpoint`
using the full `terrain.json` generated by `convert_tiles.py` from the same
extraction. Exit 1 is an expected incomplete-route result; exit 2 is an input
or audit failure. Exit 0 clears only the dependency gate, not fidelity or
hardware acceptance. Keep generated inventories and assets local.

The current USA rev-2 source audit reports:

- Candidate bounds: X=496..3312, Y=384..704, preserving the existing spawn.
- 990 terrain records: 989 static tiles plus actor 422's ordinary coin-block
  representation (118 invisible marker tiles omitted).
- 12 enemy records: ten Goombas and two Koopas, with original coordinates.
- Brick at X=2704, Y=480: tile 48, contents 2, source object 28. The reference
  editor identifies this as a ten-coin brick. Prototype runtime now awards one
  coin per accepted head hit, up to ten, and then shows a solid used block.
  Small, Super and Propeller Mario cannot shatter it. Pause freezes its bump;
  death/full reset restores its contents. The existing 12-update bump cooldown
  is provisional; verify exact original timing/depletion behavior in the final
  fidelity pass. All 30 item records in the checkpoint candidate now convert
  and load through the portable C decoder, with coordinates and contents intact.
  Including actor 422's ordinary coin block brings this to 31 item records.
  Source: [Reggie-Next object descriptions](https://github.com/NSMBW-Community/Reggie-Next/blob/master/reggiedata/ts1_descriptions.txt), object 28.
- Midway actor 188 at X=3184, Y=416, settings 0x00010000 points to entrance 1
  at X=3104, Y=416. `package_checkpoint.py` retains the settings' entrance ID
  and creates optional `checkpoint.nsk`, bound to the expanded terrain hash.
  Runtime checks the spawn is supported by a flat solid and not embedded in
  terrain. It uses local X=2608, full-height Y=16 (feet Y=48); shrinking to Small
  retains that foot position. Activation, repeated death restart, pause and
  full touch reset have automated coverage. Hardware/fidelity review is pending.
- Eight-pipe hill actor 360 at X=1904, Y=544, settings 0x0e000401 now has a
  static surface and visual prototype. Rotation/transport remain deferred.
  Its actual `circle_ground_holeD8.arc` contains a planar 832-triangle model,
  radius approximately 400, with RGB565 ground and RGB5A3 cutout textures.
  RGB5A3 decoding is now supported and covered by tile-order/alpha tests. A local
  unrotated model preview confirms eight openings. `package_pipe_hill.py` now
  renders the 315-degree starting pose and derives 160 upper support segments
  from the rotated base-ground triangles. Transparent overlay quads do not
  bridge openings. Native NPH1 validation binds geometry and texture hashes,
  rejects invalid coordinates/non-finite heights and avoids duplicate surfaces
  on repeated loads. The existing hill remains loaded alongside it. The lower
  half is visual only. Four-unit sampling and mouth-wall contacts remain
  approximate; pipe transitions are disabled until the bonus-room stage.
  Correction: earlier notes transcribed the settings as 0x0e000001. The actual
  source record is `01680770022000000e00040100000000`. Entrance ID is 4, at
  source (2112,608), type 3, linked to area 2 entrance 3. Never use the earlier
  mistaken entrance-0 interpretation. Converter regression tests retain these
  original settings and reject the incorrectly transcribed version.
- Toad block actor 422 at X=2208, Y=448 now has its no-rescue single-coin state:
  the terrain converter creates its question-block tile/collision and the item
  converter preserves its source position. A world-map Toad Rescue is not
  active in this prototype. The rescue-specific actor behavior remains deferred.
- Opening NSH1 validation now accepts both named section widths, 1408 and 2816.
  Regenerate its hash binding for the longer terrain; the original curve and
  texture remain the same. This does not implement the eight-pipe hill.

Checkpoint prototype details: pole contact is an approximate 16x48 box;
activation grows Small Mario to Super and preserves stronger forms. Death
restarts at the checkpoint, while touch restart and leaving/re-entering the
terrain mode reset it to the original entrance. Items/enemies use existing
death-reset behavior. The temporary flag changes color on activation. These
are implementation choices to compare against Wii execution, not a claim of
exact reconstructed animation, contact timing or rewards. Missing optional
checkpoint data leaves the accepted opening behavior intact. Invalid or
mismatched checkpoint data is reported and disabled.

Entrance-setting reference: Reggie-Next's original editor implementation,
[sprite 188 definition](https://github.com/NSMBW-Community/Reggie-Next/blob/master/reggiedata/spritedata.xml)
(settings nybbles 7-8; also retained locally), checked against the supplied
USA stage's midpoint, entrance and supporting terrain coordinates.

Signs, cloud effects and Super Guide presentation/conditions remain tracked
for review. Unknown actors, including those above the current vertical crop,
are explicitly listed rather than silently treated as implemented. Final
comparison must revisit all six rolling hills and every deferred feature.

Before delivery, resolve the blocking entries, run combined gameplay tests,
and assemble one complete Homebrew folder with all required data files. A new
CI build is now required for the new pipe-hill runtime and matching data.

Local integration evidence: both hills, 12 enemies and 31 item records load
together in the portable C runtime. In the original data, the central pipe
mouth supports Mario's feet at local Y=240 versus approximately 164.29 on the
nearby rim; jumping out of the mouth succeeds without a death in the focused
probe. Repeated load, malformed package and capacity checks pass. A naive
constant-run/constant-jump route probe did NOT finish (seven deaths in 1800
updates), so it is not a successful full playthrough and does not clear device
acceptance. Manual route testing, native GPU timings and final Wii comparison
are still required. Complete local data has 18 files, adding checkpoint.nsk,
pipe-hill.nph and pipe-hill.rgba to the previous 15-file set.
