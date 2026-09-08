# Implementation status

The current result is a **development viewer source project**, not a playable port.

Continuation: a Docker wrapper and manual GitHub Actions workflow have now been implemented, with separate build outputs, failure logs, provenance/hashes, and a source-only handoff archive. Docker/Podman were not found locally, and no remote repository/runner is accessible. Neither path has executed a native build. No emulator test has run.

| Requested component | Result |
|---|---|
| Validate source image | Passed earlier WIT data-partition check; SMNE01 rev 2 confirmed |
| Preserve source WBFS | Preserved; previous before/after SHA-256 matched |
| Source audit | Completed at pinned decompilation revision; major engine gaps remain |
| Convert World 1-1 data | Two areas converted to inspected placement records; textures/model/audio conversion absent |
| Native package loader | Implemented and tested in compiled WebAssembly C core |
| 3DS-equivalent input mapping | Portable actions implemented and tested; gameplay integration absent |
| 400×240 rendering | Native development-viewer source written; no native build/render test |
| CIA installation target | Build script and descriptor written; no CIA generated or installed |
| Scrolling | Implemented in native viewer source; not hardware-tested |
| Collision/player/enemies | Not implemented as a faithful game runtime |
| Carry/propeller/tilt test scene | Input behavior tests exist; playable scene absent |
| Fixed 60 Hz updates | Portable scheduler implemented/tested; real-time device behavior unmeasured |
| Performance report | No hardware sample exists; all device timing and memory results unavailable |
| Complete World 1-1 playthrough | Not available |

## Concrete blockers

The environment has no configured devkitPro toolchain or 3DS libraries. The native build preflight reports this explicitly. Unity's bundled Clang can compile WebAssembly but rejected an ARM target, so it is not a substitute for devkitARM. There is no connected device-test result.

A public-source-index download failed inside the sandbox. The required elevated retry was rejected automatically because this session disallows elevated commands. No tool installation was attempted after that rejection. Remaining implementation used the previously downloaded source, the user's already-extracted game data, and available local tools.

Even after resolving the toolchain, native gameplay still requires reconstructing substantial stage/background/actor systems and replacing Wii platform dependencies. This project must not be presented as a complete port or as evidence that the 60 fps target has been reached.

## Performance acceptance remains pending

CPU frame time: **not measured**. GPU frame time: **not measured**. Frame-time percentiles: **not measured**. Total application memory: **not measured**. Native audio continuity: **not tested**. Full-level frame pacing: **not tested**.

The viewer's future CSV captures are explicitly labeled as viewer-only. A successful viewer benchmark would establish platform/asset-loader feasibility, not the performance of a reconstructed game.
