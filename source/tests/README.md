# Project layout

```
your-3ds-port/
├── .github/
│   └── workflows/
│       └── build.yml           # CI build via devkitpro/devkitarm (already drafted)
├── Makefile                    # devkitARM build script
├── icon.png / banner.png       # only needed once you build a .cia (see below) — skip for now
├── include/                    # shared headers
│   ├── stage.h
│   ├── actor.h
│   ├── background.h
│   └── platform_3ds.h          # 3DS-specific replacements for Wii platform calls
├── source/
│   ├── main.c                  # entry point, main loop
│   ├── stage/                  # reconstructed stage system
│   ├── actor/                  # reconstructed actor system
│   ├── background/             # reconstructed background/render system
│   ├── platform/                # 3DS platform layer — this is what replaces the Wii deps
│   │   ├── input_3ds.c          # replaces Wii Remote input
│   │   ├── gfx_3ds.c            # citro3d/citro2d rendering, replaces GX
│   │   └── audio_3ds.c          # replaces the Wii audio mixer
│   └── loaders/
│       └── asset_loader.c       # reads converted assets out of romfs/ at runtime
├── data/                        # your already-extracted Wii game data, UNCONVERTED — not compiled in directly
├── romfs/                       # converted, 3DS-ready assets that actually ship inside the app
│   ├── stages/
│   ├── textures/
│   └── audio/
└── tools/                       # your local asset-conversion scripts (Wii format -> romfs format)
```

## Why `data/` and `romfs/` are separate

The Wii's asset formats (textures, models, audio containers) almost certainly aren't
readable as-is by citro3d/citro2d on the 3DS. Keep the raw extracted files in `data/`
untouched, run them through a conversion step (whatever's in `tools/`, or something we
write together) to produce 3DS-native formats, and only the converted output goes into
`romfs/`. The Makefile packs `romfs/` into the app; it does not touch `data/` at all.

## Why `source/platform/` exists

This is the seam between "game logic" and "Wii-specific code." Anything that currently
talks to GX, the Wii Remote, or Wii disc I/O should route through this layer instead, so
`stage/`, `actor/`, and `background/` can stay platform-agnostic and only
`source/platform/*_3ds.c` needs to know it's running on a 3DS.

## Starting simple: `.3dsx` before `.cia`

The Makefile below only builds a `.3dsx` (loadable via the Homebrew Launcher / Citra) —
no icon, banner, or `.rsf` required. Once the game actually runs, we can add the CIA
rule and title metadata for a proper installable package. No need to block on that now.
