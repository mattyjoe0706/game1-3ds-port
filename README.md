# NSMBW New 3DS prototype work

**Current deliverable: source code and converted placement data for a development viewer. No playable game, CIA, or 3DSX binary has been produced.**

This continues the native-port feasibility work for the user's SMNE01 revision 2 WBFS. The original image was preserved. CIA is the intended installation format; a 3DSX target is retained for development.

## This repository

The active files are `include/core.h`, `source/core.c`, `source/main.c`, and the top-level `tests/` directory. There is no `core.main` file. Build using the root Makefile or `tools/build_native.py`. The root Makefile delegates to the same Python build driver as CI, including citro2d/citro3d/libctru linkage.

The active workflow is `.github/workflows/native-build.yml`, triggered on pushes to `main` or manually. The pre-existing root `build.yml` and `source/tests/Makefile` / `source/tests/README.md` are preserved draft files and are not used by this build. Their staged Git state has not been changed.

`data/`, `romfs/`, and `sdmc/` are ignored. No extracted Wii files or converted level packages were copied into this repository; compilation does not require them. The local game-data test is therefore expected to skip. After a successful build, supply the separately retained SD data to the handheld/emulator.

With native dependencies configured, `make` builds ELF/3DSX and `make cia MAKEROM=/path/to/makerom` additionally builds CIA. Each build needs a fresh empty output directory; use `make OUTPUT=build/attempt2` for another attempt. `make test` runs portable Python tests and `make check` checks native dependencies. On Windows, pass `PYTHON=python` if that is your interpreter command.

**Container/CI continuation:** [BUILD_HOST.md](BUILD_HOST.md) provides an official devkitPro container wrapper, a manual GitHub Actions workflow, and source-only packaging. These paths are implemented but have not run on a native build host. The local Docker check reports that the CLI is unavailable.

## Implemented

- Converter for the real World 1-1 course archives: tileset names, entrance links, actor IDs/positions/parameters, camera-zone bounds, and object placement bounds.
- Two versioned, checksummed NSC1 packages totaling 22,096 bytes and 918 records. Detailed JSON preserves decoded fields for inspection.
- Allocation-free C package loader with fixed capacity, byte-order conversion, format/bounds/checksum validation, and invalid-load rejection.
- Portable control mapping with X pickup/carry/release-to-throw, jump, run/fire, R spin, digital tilt, and pause behavior. Pickup requires eligibility supplied by a future gameplay system.
- Fixed 60 Hz update scheduler with bounded catch-up and explicit discarded-step accounting; visibility checks.
- Native libctru/citro2d/citro3d **viewer source**: a 400×240 top screen with a 400×225 inspection viewport, scrolling, area switching, status display, and bounded timing capture to SD. Native source is uncompiled and untested here.
- Native build script plus CIA configuration. The CIA build path uses a default devkitPro icon and no custom banner. Packaging and launch are unverified.

Object rectangles are placement bounds, **not collision geometry**. The viewer does not draw the original textures or simulate Mario/enemies. The target gameplay controls are implemented as input actions, not integrated into a working game.

## Validation

See [STATUS.md](STATUS.md) and `reports/`.

- Nine converter tests pass, including record byte order, bounds, malformed data, explicit subarea handling, and integrity checks.
- The C core compiled with Clang to WebAssembly and ran under Node. Input/timing/visibility tests pass. Both real packages load with matching record IDs and positions; corruption, truncation, invalid records with valid checksums, and 100 repeated loads per area are tested.
- No devkitARM/libctru/citro2d/citro3d installation was found. The native build prerequisite check fails explicitly. The local Unity compiler supports WebAssembly but rejected the ARM target.
- No hardware, native rendering, installation, audio, memory-total, or gameplay-performance tests have been run. There is no measured 60 fps result.

## Rebuild the converted data

Python 3.10+ is sufficient for the converter. Run from this directory, using a **new** output directory:

```text
python tools/convert_course.py PATH_TO_EXTRACTED_DISC NEW_OUTPUT_DIRECTORY
python -m unittest discover -s tests -v
```

The extracted disc must contain `sys/boot.bin` and `files/Stage/01-01.arc`. The converter accepts SMNE01 disc 0 revision 2 and preserves the input. The extraction already exists in the workspace's `work/disc-extracted` directory. Initial verification used Wiimms ISO Tools 3.05a; the earlier feasibility folder contains verification logs and the source audit.

Copy the generated `.nsc` files to `sdmc/3ds/nsmbw-prototype/data/` when preparing a new SD staging tree. Existing output directories are rejected to avoid overwriting files unintentionally.

## Build after installing the native dependencies

Required: devkitPro's devkitARM, libctru, citro2d, citro3d and 3ds tools, plus Project_CTR makerom for CIA. The script checks dependencies; it does not download or install anything.

```text
python tools/build_native.py --devkitpro PATH_TO_DEVKITPRO --check --cia
python tools/build_native.py --devkitpro PATH_TO_DEVKITPRO --cia --makerom PATH_TO_MAKEROM --output build-first
```

This is an **unvalidated build recipe**, not a claim that a build has passed. Compiler/linker/makerom errors must be resolved before treating generated files as usable. Outputs, if successful, are placed in the chosen empty output directory: ELF, 3DSX, SMDH, CIA, logs, and a hash/provenance report.

The current CIA project ID is `000400000F731100`, chosen for this prototype and not centrally reserved. Do not replace another installed application using that ID. The CIA metadata requests New 3DS memory mode, 804 MHz, and L2 cache; those settings still require device verification.

## Device test after a successful build

1. Copy the **contents** of `sdmc/` to the SD root. Keep the `3ds/nsmbw-prototype/data` layout.
2. Install the generated inspector CIA through FBI, or use the development 3DSX in Homebrew Launcher. There is no binary to install in this delivery.
3. Verify that both areas load and scroll, and that missing/corrupt data gives an error rather than a crash.
4. Viewer controls: D-pad/Circle Pad pans, Y pans faster, SELECT switches area, START pauses, SELECT+START exits and saves up to 3,600 frame samples. These are development-viewer controls, not the final game's controls.
5. Inspect the `viewer-*.csv` capture in `3ds/nsmbw-prototype/`. It reports frame intervals, citro3d timings, visible records and discarded updates. Those are viewer measurements, not gameplay benchmarks. The static-buffer size is not total application memory. A closed HOME-menu termination may not save a capture; use the explicit exit combination.

## Remaining work toward the requested game

1. Obtain a working native toolchain, compile the viewer, validate the CIA descriptor, and run the first hardware test.
2. Decode tileset object expansion, tile attributes and slopes. Preserve source geometry when constructing collisions; do not treat the current bounding boxes as solid rectangles.
3. Reconstruct the missing stage/background/player dependencies, then integrate faithful player physics and the tested input actions. Add all actor behaviors required by the 17 distinct map actor IDs in these two areas.
4. Implement power-ups, enemy interactions, pipes/subarea links, goals, death/restart, audio, and the carrying/propeller/tilt test scene.
5. Convert and render textures/models, tune effects, and validate a complete World 1-1 playthrough on New 3DS hardware against the Wii reference. Only then evaluate 60 fps acceptance and expansion to the campaign.

## References and provenance

- [NSMBW-Decomp, pinned revision](https://github.com/NSMBW-Community/NSMBW-Decomp/tree/6b6780c6b42003ce6f8e8705fea8021bab336818): used for data-structure research. The original project still rebuilds Wii code and is not imported as a working ARM engine.
- [devkitPro 3DS examples](https://github.com/devkitPro/3ds-examples): native platform APIs and build conventions.
- [Project_CTR makerom documentation](https://github.com/3DSGuy/Project_CTR/blob/master/makerom/README.md): CIA build interface.

The code written for this prototype is included in full. Converted course data comes from the user's local game image. The folder does not include Wii executables, system keys, Nintendo SDK libraries, or a retail 3DS title.
