import fs from 'node:fs';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[2]),{});
const line=instance.exports.run_movement_tests();
if(line) throw new Error(`Movement test failed at movement_tests.c:${line}`);
console.log('PASS authored movement physics, collisions, pause, respawn and completion');
