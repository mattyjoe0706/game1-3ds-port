import fs from 'node:fs';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[2]),{});
const e=instance.exports;
const result=e.run_enemies_tests();
if(result)throw new Error(`Enemy tests failed at enemies_tests.c:${result}`);
console.log('PASS enemy loader, activation, walking, wall reversal, stomp, damage, pause and restart');
if(process.argv[3]&&process.argv[4]) {
 const t=fs.readFileSync(process.argv[3]),n=fs.readFileSync(process.argv[4]);
 new Uint8Array(e.memory.buffer).set(t,e.encounter_terrain_buffer());
 new Uint8Array(e.memory.buffer).set(n,e.encounter_enemy_buffer());
 if(!e.encounter_load(t.length,n.length)||e.encounter_count()!==4)throw new Error('Real enemy package rejected');
 for(let i=0;i<650;i++)e.encounter_tick(0,0);
 if(e.encounter_deaths()===0)throw new Error('First Goomba never reached stationary player');
 if(!e.encounter_load(t.length,n.length))throw new Error('Reload failed');
 let i=0;
 for(;i<3000&&!e.encounter_finished();i++)e.encounter_tick(1,1);
 if(!e.encounter_finished())throw new Error('Cannot traverse enemy section with jump/run');
 console.log(`PASS actual four-Goomba package; stationary contact causes death; traversal ${i} ticks, deaths=${e.encounter_deaths()}, stomps=${e.encounter_stomps()}`);
}
