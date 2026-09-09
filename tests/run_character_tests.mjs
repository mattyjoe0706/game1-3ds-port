import fs from 'node:fs';
import assert from 'node:assert/strict';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(process.argv[2]),{});
assert.equal(instance.exports.run_character_tests(),0,'Character C test failed (source line)');
console.log('PASS character header, animation transitions, pause, restart and bounds');
