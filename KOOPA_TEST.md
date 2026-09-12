# Koopa / Shell Test 1

This is a separate interaction scene, not an expansion of the World 1-1 opening.
From the opening, press SELECT once to reach `KOOPA / SHELL TEST 1`.
Use the Homebrew Launcher build. Existing data files remain compatible.

Check stomping a walking Koopa into a shell, kicking it from the side,
stomping a moving shell to stop it, and shell hits against another enemy.
Stand beside a stopped shell and press and hold X to carry; release X to throw.
A failed pickup requires releasing X before trying again. Holding X does not
repeat pickup/throw. Test both directions, wall bounces, damage, pause/resume,
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
