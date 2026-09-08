import fs from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
const [wasm, dataDir] = process.argv.slice(2);
if (!wasm || !dataDir) throw new Error('Usage: node run_core_tests.mjs core.wasm data-directory');
const {instance} = await WebAssembly.instantiate(fs.readFileSync(wasm),{});
const api=instance.exports;
assert.equal(api.run_core_tests(),0,'C test failed (result is source line)');
const manifest=JSON.parse(fs.readFileSync(path.join(dataDir,'manifest.json'),'utf8'));
for (const area of manifest.areas) {
  const bytes=fs.readFileSync(path.join(dataDir,area.file));
  const decoded=JSON.parse(fs.readFileSync(path.join(dataDir,`01-01-area${area.area}.json`),'utf8'));
  const mem=new Uint8Array(api.memory.buffer,api.test_buffer(),98336);
  const load=(b)=>{mem.fill(0);mem.set(b);return api.load_test(b.length);};
  assert.equal(load(bytes),1);
  assert.equal(api.loaded_count(),decoded.records.length);
  assert.equal(api.loaded_area(),area.area);
  decoded.records.forEach((r,i)=>{assert.equal(api.loaded_x(i),r.x);assert.equal(api.loaded_id(i),r.id);});
  for (const length of [0,4,31,32,bytes.length-1]) {
    assert.equal(load(bytes.subarray(0,length)),0);
    assert.equal(api.loaded_count(),0);
  }
  for(const index of [0,4,8,12,16,24,28,32,bytes.length-1]) {
    const broken=Buffer.from(bytes); broken[index]^=0x80;
    assert.equal(load(broken),0,`corruption offset ${index}`);
  }
  assert.equal(load(Buffer.concat([bytes,Buffer.from([0])])),0);
  // Mutate a record and recompute checksum: structure checks must still reject it.
  for(const [offset,value] of [[32,9],[33,3],[44,0]]) {
    const broken=Buffer.from(bytes);
    if(offset===44) broken.writeUInt32LE(value,offset); else broken[offset]=value;
    let hash=2166136261;
    for(const b of Buffer.concat([broken.subarray(0,28),broken.subarray(32)])) hash=Math.imul(hash^b,16777619)>>>0;
    broken.writeUInt32LE(hash,28);
    assert.equal(load(broken),0,'invalid record with valid checksum');
  }
  for(let i=0;i<100;i++) assert.equal(load(bytes),1);
  console.log(`PASS area ${area.area}: ${decoded.records.length} records, corruption, truncation, semantic bounds, repeated loads`);
}
console.log('PASS C input actions, pause/carry, timing, visibility; JS/C package compatibility');
