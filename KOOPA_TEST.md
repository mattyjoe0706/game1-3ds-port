# Koopa / Shell Test 1

## Shell refinement 2

Y and X both run and carry; B and A jump. Keep either carry button held to retain
the shell, and release both to throw. This follows Nintendo's NSMB2 default layout:
https://www.nintendo.com/eu/media/downloads/games_8/emanuals/nintendo_3ds_2/new_super_mario_bros__2/ElectronicManual_Nintendo3DS_NewSuperMarioBros2_EN.pdf
(Basic Controls, PDF pages 14-15).

Stopped-shell pickup now accepts an 8-unit horizontal margin and up to 6 units
above its top, and is checked after movement as well as before it. These margins
are prototype tuning, not measured Wii constants. Holding Y/X while stomping a
moving shell catches the stopped shell during the bounce. Side contact with a
moving shell still damages Mario. The local Wii shell source restricts normal
carry checks to its Sleep state; it does not justify making moving shells harmless.

Mario now uses original `carry_wait` and `carry_walk` animations from the supplied
Wii assets. Eleven extra cells fit in the existing 512x256 sheets for Small, Super,
and Propeller Mario. The NSP1 header declares 32 frames; old 21-frame sheets remain
loadable but display an old-data message in this test. Texture memory is unchanged.
Shell placement is raised to hand height and drawn in front of Mario, with facing
kept consistent during turns. Attachment is approximate, not a full skeletal socket;
airborne carry uses a held pose and crouching still compresses the sprite.

Install the new executable together with the newly generated six Mario files.
The next complete Homebrew transfer folder must contain both. No isolated texture
folder should be presented as a ready-to-install build.

Portable tests pass for Y/X handover without throwing, release of both buttons,
pickup above a stopped shell, stomp-catching a moving shell, dangerous side hits,
bounded pickup range, carrying frame selection and old/new header compatibility.
Native compilation and handheld validation of this refinement remain pending.

This is a separate interaction scene, not an expansion of the World 1-1 opening.
From the opening, press SELECT once to reach `KOOPA / SHELL TEST 1`.
Use the Homebrew Launcher build. Existing data files remain compatible.

Check stomping a walking Koopa into a shell, kicking it from the side,
stomping a moving shell to stop it, and shell hits against another enemy.
Stand beside a stopped shell and hold Y or X to carry; release both to throw.
You can hold the button before approaching a stopped shell; it picks up when close enough.
Holding does not repeat pickup/throw. After a forced drop, release both before
picking up again. Test both directions, wall bounces, damage, pause/resume,
and touch-screen restart. SELECT cycles back through the other scenes.
SELECT+START saves the performance CSV and exits as before; mode 4 identifies
this scene in the CSV.

The local PAL decompilation supplies the Koopa walking speed (0.5 units/update)
and shell sleep timer (511 updates). These are references, not a verified USA
revision gameplay comparison. Shell speed (5 units/update), collision dimensions,
and simplified green/red drawings are provisional. Red Koopas check ledges.
Carrying freezes the wake timer in this prototype; shaking/waking while held,
carried-shell combat, slope-aware carrying and exact Wii timing remain pending.
Against a solid wall the shell drops at its last safe position instead of clipping
through the wall. These limitations must be resolved before level acceptance.

Local portable tests cover shell transitions, hold/release, pause, damage,
wall bounce, blocked carrying, red ledges, enemy hits and reset, alongside the
existing Goomba tests. Native compilation and handheld validation remain pending.
No graphics-fidelity or 60 fps acceptance claim is made for this milestone.
