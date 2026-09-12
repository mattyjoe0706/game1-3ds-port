"""Build the development viewer. Requires installed devkitPro; never installs tools.

Native build and CIA launch have NOT been validated in the delivery environment.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import hashlib
import json
from verify_cia import verify_cia

ROOT = Path(__file__).resolve().parents[1]


def executable(name, directory=None):
    if directory:
        for suffix in (".exe", ""):
            candidate = directory / (name + suffix)
            if candidate.is_file():
                return str(candidate)
    return shutil.which(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--devkitpro", type=Path, default=os.environ.get("DEVKITPRO"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--cia", action="store_true", help="Also package a test CIA; packaging is unvalidated")
    parser.add_argument("--makerom", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "build", help="Empty output directory; source can be read-only")
    args = parser.parse_args()
    if not args.devkitpro:
        print("BLOCKED: devkitPro not configured. Set DEVKITPRO or pass --devkitpro.")
        print("Required: devkitARM, libctru, citro2d, citro3d, 3dsxtool; makerom for CIA.")
        return 2
    dkp = args.devkitpro.resolve()
    gcc = executable("arm-none-eabi-gcc", dkp / "devkitARM/bin")
    three_dsx = executable("3dsxtool", dkp / "tools/bin")
    smdhtool = executable("smdhtool", dkp / "tools/bin")
    makerom = (str(args.makerom.resolve()) if args.makerom.is_file() else None) if args.makerom else executable("makerom", dkp / "tools/bin")
    required = [dkp / "libctru/include/3ds.h", dkp / "libctru/include/citro2d.h",
                dkp / "libctru/include/citro3d.h", dkp / "libctru/lib/libctru.a",
                dkp / "libctru/lib/libcitro2d.a", dkp / "libctru/lib/libcitro3d.a"]
    missing = [str(p) for p in required if not p.is_file()]
    for label, tool in [("arm-none-eabi-gcc",gcc),("3dsxtool",three_dsx)]:
        if not tool:
            missing.append(label)
    if args.cia and not makerom:
        missing.append("makerom")
    if args.cia and not smdhtool:
        missing.append("smdhtool")
    if args.cia and not (ROOT / "meta/banner.bnr").is_file():
        missing.append(str(ROOT / "meta/banner.bnr"))
    if args.cia and not (dkp / "libctru/default_icon.png").is_file():
        missing.append(str(dkp / "libctru/default_icon.png"))
    if missing:
        print("BLOCKED: missing native build dependencies:\n" + "\n".join(missing))
        return 2
    if args.check:
        print("Dependencies found. This does not validate compilation or CIA launch.")
        return 0
    out = args.output.resolve()
    if out == ROOT or out in ROOT.parents or any(out == ROOT / d or ROOT / d in out.parents for d in ("source", "include", "tools", "tests", "sdmc")):
        print("BLOCKED: output overlaps project inputs.")
        return 2
    if out.exists() and any(out.iterdir()):
        print("BLOCKED: output is not empty; choose a new --output directory to avoid stale artifacts.")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    report = {"status": "running", "hardware_tested": False, "gameplay_implemented": False,
              "commands": [], "sources": {}, "artifacts": {}}
    for file in [ROOT / "source/core.c", ROOT / "source/main.c", ROOT / "source/movement.c", ROOT / "source/terrain.c", ROOT / "source/enemies.c", ROOT / "source/character.c", ROOT / "include/character.h", ROOT / "include/enemies.h", ROOT / "include/terrain.h", ROOT / "include/movement.h", ROOT / "include/core.h", ROOT / "cia.rsf", Path(__file__)]:
        report["sources"][str(file.relative_to(ROOT))] = hashlib.sha256(file.read_bytes()).hexdigest()
    if args.cia:
        for name in ("meta/banner.bnr", "tools/verify_cia.py"):
            report["sources"][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    def save_report():
        (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    def run(command):
        report["commands"].append(command)
        save_report()
        with (out / "build.log").open("a", encoding="utf-8") as log:
            log.write("\n" + json.dumps(command) + "\n")
            log.flush()
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            except OSError as error:
                report["status"] = "failed"
                report["error"] = str(error)
                save_report()
                raise
        if result.returncode:
            report["status"] = "failed"
            report["exit_code"] = result.returncode
            save_report()
            raise subprocess.CalledProcessError(result.returncode, command)
    run([gcc, "--version"])
    flags = ["-std=gnu11", "-O2", "-g", "-Wall", "-Wextra", "-Werror", "-ffunction-sections", "-fdata-sections",
             "-march=armv6k", "-mtune=mpcore", "-mfloat-abi=hard", "-mtp=soft", "-mword-relocations", "-D__3DS__",
             "-I" + str(ROOT / "include"), "-I" + str(dkp / "libctru/include")]
    objects = []
    for name in ("source/items.c","include/items.h"):
        report["sources"][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name in ("core", "movement", "terrain", "enemies", "character", "items", "main"):
        obj = out / (name + ".o")
        run([gcc, *flags, "-c", str(ROOT / "source" / (name + ".c")), "-o", str(obj)])
        objects.append(str(obj))
    elf = out / "nsmbw-inspector.elf"
    run([gcc, *flags, "-specs=3dsx.specs", *objects, "-L" + str(dkp / "libctru/lib"),
                    "-Wl,--gc-sections", "-Wl,-Map=" + str(out / "nsmbw-inspector.map"),
                    "-lcitro2d", "-lcitro3d", "-lctru", "-lm", "-o", str(elf)])
    run([three_dsx, str(elf), str(out / "nsmbw-inspector.3dsx")])
    if args.cia:
        icon = out / "nsmbw-inspector.smdh"
        run([smdhtool, "--create", "NSMBW Geometry Inspector", "Movement test and placement viewer",
                        "Homebrew prototype", str(dkp / "libctru/default_icon.png"), str(icon)])
        # The full access descriptor is provided in cia.rsf; no retail files/keys.
        run([makerom, "-f", "cia", "-o", str(out / "nsmbw-inspector.cia"),
                        "-rsf", str(ROOT / "cia.rsf"), "-target", "t", "-elf", str(elf), "-icon", str(icon),
                        "-exefslogo", "-banner", str(ROOT / "meta/banner.bnr")])
        try:
            report["cia_structure"] = verify_cia(out / "nsmbw-inspector.cia")
        except ValueError as error:
            report["status"] = "failed"
            report["error"] = str(error)
            save_report()
            raise
    for file in out.iterdir():
        if file.suffix in (".elf", ".3dsx", ".cia", ".smdh", ".map"):
            report["artifacts"][file.name] = {"bytes": file.stat().st_size, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
    report["status"] = "built_unvalidated"
    save_report()
    print("Build finished. Authored movement test and placement viewer; not a playable NSMBW port.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        sys.exit(1)
