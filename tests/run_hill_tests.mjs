import fs from 'node:fs';
import assert from 'node:assert/strict';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[2]),{});
const e=instance.exports;
const terrain=fs.readFileSync(process.argv[3]),hill=fs.readFileSync(process.argv[4]);
const hash=b=>{let h=2166136261;for(const v of b)h=Math.imul(h^v,16777619)>>>0;return h;};
const mem=new Uint8Array(e.memory.buffer);
mem.set(terrain,e.terrain_test_buffer());assert.equal(e.terrain_test_load(terrain.length),1);
const base=e.terrain_test_surfaces(),texture=hill.readUInt32LE(12);
const load=(b=hill,th=hash(terrain),ih=texture)=>{
    mem.set(b,e.terrain_test_buffer());return e.terrain_test_hill(b.length,th,ih);
};
assert.equal(load(),1);
for(let i=0;i<50;i++){assert.equal(load(),1);assert.equal(e.terrain_test_surfaces(),base+160);}
// Real crest landing, held position, walking down both slopes, jumping clear.
e.terrain_test_position(960,60);
for(let i=0;i<60;i++)e.terrain_tick(0,0);
assert.equal(e.terrain_player_grounded(),1);assert.ok(Math.abs(e.terrain_player_y()-128)<.01);
e.terrain_tick(0,1);assert.equal(e.terrain_player_grounded(),0);assert.ok(e.terrain_player_y()<128);
for(const direction of [-1,1]) {
    e.terrain_test_position(960,128);e.terrain_tick(0,0);
    for(let i=0;i<40;i++){e.terrain_tick(direction,0);assert.equal(e.terrain_player_grounded(),1);}
    assert.equal(e.terrain_player_deaths(),0);
}
for(const b of [hill.subarray(0,31),hill.subarray(0,hill.length-1),Buffer.concat([hill,Buffer.of(0)])])
    assert.equal(load(b),0);
assert.equal(load(hill,0),0);assert.equal(load(hill,hash(terrain),texture^1),0);
for(const offset of [0,4,8,12,16,20,24,28,32,100]) {
    const b=Buffer.from(hill);b[offset]^=1;assert.equal(load(b),0);
}
// NaN and discontinuous surfaces must be rejected even with a correct checksum.
for(const bits of [0x7fc00000,0x7f800000,0x00000000]) {
    const b=Buffer.from(hill);b.writeUInt32LE(bits,40);
    b.writeUInt32LE(hash(Buffer.concat([b.subarray(0,28),b.subarray(32)])),28);
    assert.equal(load(b),0);assert.equal(e.terrain_test_surfaces(),base);
}
assert.equal(load(),1);
console.log('PASS original opening hill: landing, jump, both slopes, reloads, binding and malformed packages');
