# Required process for every level

User decision, 2026-09-10: defer the remaining World 1-1 rolling-hill work to
the final fidelity pass. Apply this process to every future level and always
perform one final comparison with the actual Wii level before marking it complete.
An intermediate build may pass its limited test while the level remains unfinished.

## 1. Inventory before implementation

Create a level record using the template below. Inspect every area, including
bonus rooms, exits, entrances, checkpoints and the route to the goal.
Inventory static terrain AND separate actors: moving/rotating platforms, hills,
lifts, hazards, switches, enemies, blocks, power-ups, coins and special objects.
Record each instance's position, size, settings and linked actors/events. Count
repeated objects across the entire level; do not infer coverage from the opening.
Mark unknown IDs/settings as unknown until their meaning is established.

Compare the inventory with the original level in Wii execution or suitable
reference footage. Static screenshots can establish appearance but cannot prove
motion, timing or interactions. Record the reference and the sections inspected.

## 2. Implement and track differences

For every level, audit power-up placement and selection against player state.
For each block, enemy reward, bubble, red-coin reward or other item source,
record its original contents/settings and the result for Small, Super, Fire,
Ice, Propeller, Penguin and Mini Mario where relevant. Check Star status
separately for conditional Star rewards. Do not assume all powered forms are
equivalent or that small Mario always receives a Super Mushroom.
Record emergence position relative to the source/player, travel direction,
motion, repeat-collection behavior, damage transitions and restart behavior.
Include every special power-up actually used by the level (including Propeller
Mushrooms), and explicitly track unsupported variants rather than silently
substituting a generic mushroom. Final comparison must revisit these cases.

For each feature, separately track placement, appearance, behavior and collision.
A rendered hill does not establish rotation; one working instance does not
establish every instance. Check slopes, surface motion, carry effects, direction,
speed, activation, pauses and reset behavior where applicable.

Maintain a discrepancy list with expected behavior, current behavior, evidence,
affected locations and the milestone when it will be addressed. Explicitly
deferred items may wait until the agreed final pass; do not silently drop them.
Reuse verified systems but inspect each level's distinct settings and variants.

## 3. Test intermediate builds in bounded sections

Test traversal, jump/landing, enemy contacts, pickups, death, restart and relevant
controls. Check transitions between ordinary terrain and special platforms.
Use meaningful automated regressions where practical, then test changed behavior
on the handheld. Record the exact build and asset revisions for each result.
Reuse accepted results when unaffected. Do not request a repeat capture merely
to turn an adequate 55-second run into exactly 60 seconds.

Deliver one complete matching package with `3ds/` and `cias/` directly inside
the delivery folder. Never make the user combine separate app/data patches.

## 4. Final fidelity pass — required for every level

Before declaring the level finished, revisit the entire original level, including
all areas and optional routes, using actual Wii execution or reference footage
that shows the relevant behavior. Compare the final prototype at corresponding
locations and events. This must be a fresh end-of-level review, not just reliance
on the initial inventory or a successful prototype playthrough.

Check terrain silhouettes and slopes; every repeated/special actor; movement and
timing; collision and transport of Mario/enemies; enemy and collectible placement;
blocks and power-ups; entrances, checkpoints and exits; camera/framing, Mario
scale, backgrounds and layering; and the goal/completion sequence. Check audio,
effects and remapped actions where implemented or required by the level.

### Final graphics-quality gate

Run this after gameplay behavior is stable and immediately before packaging the
level. Compare matching screenshots or video frames against the original Wii
level and a representative New Super Mario Bros. 3DS reference when judging
presentation quality. Check Mario's proportions, model or sprite detail, eyes,
hat/hair visibility, power-up costumes and transition frames; terrain silhouette,
rolling hills, surface textures and seams; enemy and collectible appearance;
background art, sky, distant layers and parallax; camera framing, letterboxing,
palette, transparency, filtering, lighting and effects. Look for missing detail,
flat placeholder geometry, texture stretching, visible intersections, harsh
pixelation and incorrect layering. Record each item as matched, intentionally
simplified or open, with a screenshot or location reference. Improve the visual
assets and rerender before packaging whenever an item is open without an agreed
simplification. This is a presentation gate in addition to collision and
placement checks; passing gameplay alone does not pass graphics quality.

Reconcile the final instance counts with the source inventory. Revisit every
deferred issue. Fix discrepancies and recheck the affected behavior. Any unresolved
required behavior, unavailable reference or untested section remains explicitly
open; the level must not be described as complete or faithful while it remains.

Do not package until the graphics-quality gate is recorded as complete. The final
review entry must include the visual reference used, locations compared, known
simplifications and the final screenshots or capture IDs.

## 5. Final handheld acceptance

Complete the playable route from entry through the actual goal on New 3DS XL.
Check pause/resume, death/restart, repeated loads and missing/mismatched assets.
Collect representative performance covering the demanding sections: frame-time
distribution, pacing, discarded updates, CPU/GPU timings, available memory
measurements and audio continuity. Distinguish measured memory from estimated
buffer totals. Target approximately 60 Hz without sustained drops, slowdown,
audio breakup or crashes; emulator or loader results cannot establish acceptance.

Record the final build/assets, references reviewed, checks completed, limitations
and acceptance decision. If code or assets change after the final review, rerun
the checks affected by those changes before acceptance.

## Copyable level record

- Level and all areas/routes:
- Source region/revision and source-data identity:
- Original gameplay reference(s), locations/timestamps reviewed:
- Inventory: feature/actor ID, count, positions, settings, linked objects:
- Implementation: placement / appearance / behavior / collision status:
- Discrepancies: expected vs current, evidence, location, deferred milestone:
- Intermediate tests and accepted hardware evidence:
- Final original-level comparison: date, build/assets, route coverage, findings:
- Deferred-item resolution and remaining blockers:
- Final handheld playthrough and performance evidence:
- Acceptance: incomplete / ready for review / accepted within stated scope:

## World 1-1 record: current handoff

- Scope: opening slice only, not the complete level.
- Source: USA SMNE01 revision 2; full area-1 inventory contains four actor-212 hills.
- User reports HILL TEST 1 (CI build 8) works well on hardware. This accepts the
  tested static shape/support only; no new performance CSV has been analyzed.
- Deferred until World 1-1's final fidelity/testing pass: reconstruct rolling-hill
  rotation and its effect on Mario/enemies; include and verify all four hill
  instances, their sizes, positions, speeds, directions and linked behavior.
- The opening speed setting is zero, but its runtime meaning is not established.
  Do not treat that field alone as evidence that the original hill is stationary.
- Final review must inspect all hills in original gameplay and compare every
  corresponding prototype instance. These items block full-level fidelity signoff.
- Other work remains open: complete routes/goal, interactive blocks/collectibles,
  power-ups, missing actors, camera/scale fidelity, backgrounds, enemy visuals,
  audio and final handheld performance. The hill deferral does not remove these.
