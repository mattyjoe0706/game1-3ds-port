import fs from 'node:fs';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[2]),{});
const e=instance.exports;
const line=e.run_terrain_tests();
if(line) throw new Error(`Terrain test failed at terrain_tests.c:${line}`);
console.log('PASS bounded terrain loader, slope transitions, jumps and one-way platforms');
if(process.argv[3]) {
    const data=fs.readFileSync(process.argv[3]);
    const memory=new Uint8Array(e.memory.buffer);
    memory.set(data,e.terrain_test_buffer());
    if(!e.terrain_test_load(data.length)) throw new Error('Real package rejected');
    const count=e.terrain_test_count();
    // The opening flat is traversable with no jump and must keep supporting the player.
    for(let i=0;i<60;i++) e.terrain_tick(1,0);
    if(e.terrain_player_x()<450||!e.terrain_player_grounded()) throw new Error('Opening flat traversal failed');
    let frames=60;
    for(;frames<2400&&!e.terrain_player_finished();frames++) e.terrain_tick(1,1);
    if(!e.terrain_player_finished()||e.terrain_player_deaths())
        throw new Error(`Traversal failed: x=${e.terrain_player_x()} y=${e.terrain_player_y()} deaths=${e.terrain_player_deaths()}`);
    console.log(`PASS real opening package: ${count} tiles; traversal ${frames} steps; no deaths`);
}
