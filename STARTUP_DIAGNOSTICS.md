# Startup diagnostic build 1

This build adds diagnostics to the viewer; it does not claim to fix the startup failure.

Commit and push the current source/configuration changes, including the meta directory and packaging tools, to trigger a new native CI build. Previously downloaded CIA/3DSX files do not contain these checkpoints. Native compilation and device execution of this diagnostic revision are still pending.

Try the new 3DSX through Homebrew Launcher first. Replace the existing file at SD:/3ds/nsmbw-prototype/nsmbw-inspector.3dsx with the newly built one. The converted data stays at SD:/3ds/nsmbw-prototype/data/. If testing CIA separately, reinstall the newly built CIA through FBI.

Expected behavior:

1. The bottom screen displays STARTUP DIAGNOSTIC 1 and [02] Bottom console ready. It deliberately waits for A to continue or B to exit.
2. Checkpoints [03]-[10] bracket model detection, speedup configuration, citro3d/citro2d setup, screen-target creation, SD directory checks and data loading. Failures display the API result or filesystem errno when available and wait for B.
3. At [11] Data ready, press A again to attempt the first frame.
4. [12] marks entry into the first frame. [13] means submission returned; [14] means GPU synchronization returned. These markers alone do not prove that the picture was correctly displayed.
5. The usual viewer status replaces the startup text after 15 frames. SELECT+START attempts to save the timing CSV and return to the launcher. It does not intentionally power off the console.

Each startup/error/exit checkpoint is appended to SD:/nsmbw-startup.log, directly in the SD card root. Each write is closed immediately. Repeated launches preserve earlier sessions. There is no continuous per-frame disk logging. If the log cannot be written, the bottom screen reports errno; diagnostics continue without the file.

Report the last numbered checkpoint visible and provide the startup log. The last line describes the operation about to run or the operation that returned. If both screens remain blank, check the root log anyway: [00] precedes graphics initialization and [01] precedes console initialization. No new session in the log is inconclusive: libctru initialization runs before main, and inaccessible SD storage can also prevent logging.

These checkpoints introduce setup pauses and disk writes. Use them to locate startup failures, not to establish game performance or 60 fps acceptance. Existing portable tests do not execute native main.c; the new build and device test are required.
