# Movement test 1

Implemented in source/movement.c and integrated into the native application. The default scene is a small authored course with a yellow placeholder player, blue solid platforms, gaps, steps, and a green finish pole. This is not World 1-1 and the physics are not reconstructed Mario physics.

## Controls

- D-pad or Circle Pad: move; down crouches when grounded.
- A or B: jump; hold for a higher jump and release for a shorter one.
- Y: run.
- START: pause/resume.
- Touch the bottom screen: restart the movement course and clear its death count/pause.
- SELECT: cycle movement course, World 1-1 area 1 outlines, and area 2 outlines. Pause clears when changing modes; movement state is retained until you restart.
- SELECT + START: save a CSV and exit.

Falling into a gap automatically respawns after 45 fixed updates. Reach the green pole while grounded to finish; touch to restart. The camera follows horizontally. The current two startup A prompts are retained.

The original placement inspector still loads the local NSC files when selected. Its outlines are not treated as solid walls. The movement course needs no Wii data to run. Missing inspector data is shown as an error status without stopping the movement test.

## Implementation and evidence

The player uses a fixed 60 Hz simulation with bounded velocity, horizontal acceleration/deceleration, variable jump height, axis-swept rectangle collision, constrained uncrouching, pause, death/respawn and finish state. All resources are bounded; no per-step heap allocation. The bottom console is cleared before status updates so startup text does not remain behind shorter lines.

The portable C movement suite compiles with warnings as errors to WebAssembly and passes under Node. Tests cover standing, running into walls, ceilings, jump release, no automatic repeated jumping, pause, blocked uncrouching, death/respawn, finish state, camera bounds and automated traversal to the finish. CI also executes these tests with the host compiler before compiling the native application. Native compilation and hardware validation of this revision are pending.

CSV files now include mode: 0 = movement test, 1 = first placement area, 2 = second placement area. They still use the viewer-*.csv filename. Earlier viewer timings cannot be used as performance results for this revision.

## Hardware test

Commit/push the new source, header, tests, workflow and build-tool changes. After CI succeeds, use the newly built 3DSX through Homebrew Launcher. Replacing only the CIA on SD does not update an installed app; the CIA launch issue remains separately unresolved.

Check short versus held jumps, walking versus running, collision with steps/platform undersides, both gaps, pause/resume, touch restart and finish. Switch to both placement views and back. Exit with SELECT+START and return the new CSV. A successful portable test does not prove handheld behavior or 60 fps.

## Remaining World 1-1 blocker

The existing converter stores object placement bounds and actor markers only. Tileset object expansion and per-tile collision attributes/slopes are not decoded. Treating those rectangles as Wii collision would fabricate level behavior. That decoding, integration with this controller, and Wii-reference physics comparisons are still required before claiming movement through the actual World 1-1 geometry. Enemies, power-ups, carrying, propeller behavior, original graphics/audio and the original level goal are also unfinished.
