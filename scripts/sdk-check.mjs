import assert from 'node:assert/strict';
import {abi} from 'genlayer-js';
const h='a'.repeat(64),address='0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42';
for(const [name,args] of [
 ['open_round',['nonce','Does published evidence explicitly allow bulk downloads?',address,60,60,'mahdiaqal','sealed-belief-scoreboard','a'.repeat(40),'examples/archive-policy.txt',h,'examples/archive-faq.txt',h]],
 ['commit_probability',[h,h]],['reveal_probability',[h,2000,h]],['resolve',[h]],['void_expired',[h]],['get_round',[h]],['get_stats',[address,address]]]){
 const data=abi.calldata.encode(abi.calldata.makeCalldataObject(name,args,{}));
 assert.deepEqual(abi.calldata.encode(abi.calldata.decode(data)),data);
}
console.log('7 SDK calldata roundtrips passed');
