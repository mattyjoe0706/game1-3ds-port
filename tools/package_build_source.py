"""Package only authored source/configuration; never package disc or SD data."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def package(output):
    allowed=[]
    for dirname, extensions in (("source",{'.c'}),("include",{'.h'}),("tools",{'.py'}),
                                ("tests",{'.c','.py','.mjs','.md'}),("meta",{'.bnr','.png','.wav','.md','.txt'}),
                                (".github/workflows",{'.yml'})):
        allowed.extend(p for p in (ROOT/dirname).rglob('*') if p.is_file() and p.suffix in extensions and not p.is_symlink())
    allowed.extend(ROOT/name for name in ('README.md','STATUS.md','FORMAT.md','BUILD_HOST.md','LAUNCH_STATUS.md','STARTUP_DIAGNOSTICS.md','MOVEMENT_TEST.md','TERRAIN_DECODER.md','TERRAIN_TEST.md','ENEMY_TEST.md','CHARACTER_CONVERTER.md','MARIO_SPRITE_TEST.md','Makefile','cia.rsf','.gitignore'))
    manifest={}
    for p in allowed:
        if not p.is_file(): raise ValueError(f'Missing source file: {p}')
        manifest[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(allowed): z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('SOURCE-SHA256.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(output) as z:
        if z.testzip(): raise ValueError('ZIP verification failed')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    result=package(a.output)
    print(f'Packaged {len(result)} source/configuration files, plus hash manifest. No game data.')
