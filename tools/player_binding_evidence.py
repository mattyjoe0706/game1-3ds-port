import sys,contextlib,io,struct,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'powerup-research'))
with contextlib.redirect_stdout(io.StringIO()):import read_dol as d
d.md.skipdata=True
out=Path(__file__).parent
ranges=[(0x800d4d80,0x800d4e88),(0x800caa70,0x800cab00),(0x80241be0,0x80241c64)]
(out/'original-player-callback.txt').write_text('\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for start,end in ranges for i in d.md.disasm(d.read(start,end-start),start)))
factors=struct.unpack('>4f',d.read(0x802f1100,16))
assert all(abs(a-b)<1e-6 for a,b in zip(factors,[1,.546,1,.72]))
(out/'source-evidence.json').write_text(json.dumps(dict(dol_sha256=hashlib.sha256(d.b).hexdigest(),root_scale_address='0x802f1100',root_scale=factors,forms=['super','small','propeller','penguin'],scope='Ordinary Mario. Action flags and transitions may change these factors.'),indent=2))
