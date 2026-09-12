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

- Enemies currently load only Goombas. Koopa walking, stomping, shell state,
  kicking, carrying, throwing, enemy hits and recovery require implementation.
- Terrain and enemy converters hard-code the opening crop and origin. Route
  extension must update coordinates, spawn, bounds and matching package hashes
  together. The runtime terrain capacity is 2048 records; full-area expanded
  tile counts must be measured before choosing paging or larger pools.
- Pipe traversal, both bonus rooms, P-Switch behavior, Star Coins, red-ring
  timer/reward, checkpoint persistence and real goal completion are missing.
- Toad/Super Guide conditional activation needs source verification. Their
  presence in the archive does not mean they are active on every playthrough.
- Full camera rules, player movement fidelity, backgrounds, finished enemy
  visuals, effects, audio and remaining graphics work are open.
- Mini size and additional power-up behavior remain unverified; they must be
  checked when relevant rather than substituting the currently supported forms.

## Implementation stages

1. **Koopa and shell interactions.** A bounded integration scene using the
   existing collision/player systems: stomp, kick, carry with held X, throw
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

The next implementation milestone is stage 1 only. No new device build is
needed for this audit. Gameplay footage comparison and full reward decoding
remain open tasks, not implied results of parsing the archive.
