# Checkpoint-route prototype test

This extends the tested opening through the midpoint. It uses 12 original
enemy placements, 31 coin/block interactions, both static hills, and the
checkpoint's referenced restart entrance. It is not the finished level.

Build the current source in CI. Combine that artifact with the complete
matching 18-file data package before installing. Do not send a partial data
folder or ask the user to replace individual textures. The final handoff must
contain one `3ds/nsmbw-prototype` folder with the executable, icon and full data.
Continue launching through Homebrew; no CIA installation is needed for this test.

The screen should say **CHECKPOINT ROUTE PROTOTYPE** when its data is loaded.

Check these together in one play session:

- Move through the original opening and across the two hills. Check landing in
  the pipe-hill openings and jumping back onto the rim without disappearing or
  standing on invisible ground. Rotation is still deliberately deferred.
- Interact with the original Goombas/Koopas, preserving the accepted Y/X carry
  behavior. Jump with A/B and use R with Propeller Mario.
- Hit the ten-coin brick repeatedly. Each accepted hit gives one coin; after
  ten it stays solid and becomes used. The ordinary Toad-position question
  block gives one coin in this no-rescue prototype.
- Touch the checkpoint: its test flag changes color and the status says active.
  After a death, restart to the left of that flag. Touch-screen restart must
  instead return to the level entrance and clear the checkpoint.
- Pause/resume and switch to the isolated Koopa scene and back. Save the CSV
  using Select+Start, and report any specific location where traversal fails.

Pipe travel into bonus rooms, hill motion/transport, Toad rescue, final graphics,
audio and exact original timing are not implemented in this test. No 60 fps or
full-route acceptance claim is made before handheld results.
