"""Run an installed Docker engine. Does not install Docker or use privileged mode."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "devkitpro/devkitarm:20260610"


def command(docker, image, project, output, makerom=None):
    args = [docker, "run", "--rm", "--network", "none", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--read-only", "--tmpfs", "/tmp:rw,nosuid,size=64m",
            "--mount", f"type=bind,src={project},dst=/src,readonly",
            "--mount", f"type=bind,src={output},dst=/out", "--workdir", "/src"]
    if os.name != "nt":
        args += ["--user", f"{os.getuid()}:{os.getgid()}"]
    if makerom:
        args += ["--mount", f"type=bind,src={makerom},dst=/tool/makerom,readonly"]
    args += ["--env", "PYTHONDONTWRITEBYTECODE=1", image, "python3", "tools/build_native.py",
             "--devkitpro", "/opt/devkitpro", "--output", "/out"]
    if makerom:
        args += ["--cia", "--makerom", "/tool/makerom"]
    return args


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", default=IMAGE)
    p.add_argument("--output", type=Path, default=ROOT / "build-container")
    p.add_argument("--makerom", type=Path, help="Optional Linux makerom executable matching image CPU architecture; enables CIA")
    p.add_argument("--pull", action="store_true", help="Explicitly fetch the image before building")
    p.add_argument("--print-command", action="store_true", help="Display argument list only; do not call Docker")
    a = p.parse_args()
    out = a.output.resolve()
    if out == ROOT or out in ROOT.parents or any(out == ROOT / d or ROOT / d in out.parents for d in ("source", "include", "tools", "tests", "sdmc")):
        p.error("Output overlaps source inputs")
    makerom = a.makerom.resolve() if a.makerom else None
    if any("," in str(path) for path in (ROOT, out, *([makerom] if makerom else []))):
        p.error("Docker mount paths cannot contain commas")
    if makerom and not makerom.is_file():
        p.error("makerom file not found")
    docker = shutil.which("docker")
    if a.print_command:
        print(json.dumps(command(docker or "docker", a.image, ROOT, out, makerom), indent=2))
        return 0
    if not docker:
        print("BLOCKED: Docker CLI not found. Run this on a host with Docker installed, or use the included CI workflow.")
        return 2
    subprocess.run([docker, "info"], check=True, stdout=subprocess.DEVNULL)
    if out.exists() and any(out.iterdir()):
        p.error("Choose an empty output directory")
    if a.pull:
        subprocess.run([docker, "pull", a.image], check=True)
    metadata = json.loads(subprocess.check_output([docker, "image", "inspect", a.image], text=True))[0]
    out.mkdir(parents=True, exist_ok=True)
    # Run by immutable local image ID after resolving the human-readable tag.
    result = subprocess.run(command(docker, metadata["Id"], ROOT, out, makerom))
    (out / "container-provenance.json").write_text(json.dumps({"requested_image": a.image,
        "image_id": metadata["Id"], "repo_digests": metadata.get("RepoDigests", []),
        "container_exit_code": result.returncode}, indent=2) + "\n", encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"Container build failed: {error}", file=sys.stderr)
        sys.exit(1)
