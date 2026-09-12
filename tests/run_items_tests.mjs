import fs from 'node:fs';
import assert from 'node:assert/strict';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[2]),{});
const e=instance.exports;
assert.equal(e.run_items_tests(),0,'C item tests: result is source line');
const terrain=fs.readFileSync(process.argv[3]),data=fs.readFileSync(process.argv[4]);
const hash=b=>{let h=2166136261;for(const v of b)h=Math.imul(h^v,16777619)>>>0;return h;};
const mem=new Uint8Array(e.memory.buffer);
const loadTerrain=()=>{mem.set(terrain,e.items_test_buffer());assert.equal(e.items_test_terrain(terrain.length),1);};
const load=(b=data,th=hash(terrain))=>{mem.set(b,e.items_test_buffer());return e.items_test_load(b.length,th);};
loadTerrain();assert.equal(load(),1);assert.equal(e.items_test_count(),13);assert.equal(e.items_test_power(),0);
const rows=Array.from({length:data.readUInt32LE(8)},(_,i)=>({i,x:data.readUInt16LE(24+i*12),y:data.readUInt16LE(26+i*12),kind:data[30+i*12],contents:data[31+i*12]}));
assert.equal(rows.filter(r=>r.kind===1).length,8);
assert.equal(rows.filter(r=>r.kind===2&&r.contents===7).length,1);
const coinBlock=rows.find(r=>r.kind===2&&r.x===432);
e.items_test_position(432,208);e.items_test_tick(0,0,0);
for(let i=0;i<40;i++)e.items_test_tick(0,1,0);
assert.equal(e.items_test_block_state(coinBlock.i),1);assert.equal(e.items_test_coins(),1);
for(let i=0;i<60;i++)e.items_test_tick(0,1,0);
assert.equal(e.items_test_coins(),1,'A used block must not pay again');
const prop=rows.find(r=>r.contents===7);
e.items_test_position(560,144);e.items_test_tick(0,0,0);
for(let i=0;i<20;i++)e.items_test_tick(0,1,0);
assert.equal(e.items_test_block_state(prop.i),1,'Upper Propeller block must be reachable from lower blocks');
for(const b of [data.subarray(0,23),data.subarray(0,data.length-1),Buffer.concat([data,Buffer.of(0)])]) assert.equal(load(b),0);
assert.equal(load(data,0),0);
for(const offset of [0,4,8,12,16,20,24,data.length-1]) {const b=Buffer.from(data);b[offset]^=1;assert.equal(load(b),0);}
// Valid checksum cannot excuse a bogus tile index/content code.
for(const offset of [28,31,32]) {
    const b=Buffer.from(data);b[offset]=255;b.writeUInt32LE(hash(Buffer.concat([b.subarray(0,20),b.subarray(24)])),20);
    assert.equal(load(b),0);
}
for(let i=0;i<50;i++){loadTerrain();assert.equal(load(),1);assert.equal(e.items_test_coins(),0);}
if(process.argv[5]&&process.argv[6]) {
    const hill=fs.readFileSync(process.argv[5]),enemies=fs.readFileSync(process.argv[6]);
    mem.set(hill,e.items_test_buffer());assert.equal(e.items_test_hill(hill.length,hash(terrain),hill.readUInt32LE(12)),1);
    mem.set(enemies,e.items_test_buffer());assert.equal(e.items_test_enemies(enemies.length,hash(terrain)),1);
    for(let i=0;i<700;i++) e.items_test_tick(0,0,0);
    assert.ok(e.items_test_deaths()>0,'Goomba contact must still work with items and hill enabled');
    assert.equal(e.items_test_power(),0,'Restart must return Small Mario');
    console.log('PASS combined original terrain/hill/enemies/items contact and restart');
}
console.log('PASS real opening: 13 interactions, original coin/Propeller blocks, head hits, one-time rewards, malformed data and reloads');
