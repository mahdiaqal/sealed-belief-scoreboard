// Resume only known hashes. Persist sanitized metadata immediately; never blindly rebroadcast.
import fs from 'node:fs';
import {spawn} from 'node:child_process';
import {rpc} from './check.mjs';
const address='0xdD085aa0d0074D4f2c4cf0b8071A9D0860be8a79',commit='097dde704ca5d2b9e9596da61238936469c82306';
const seed=[
 {step:'deploy',hash:'0x406d93c8b4f7920027b10fdb7aadeb972388f460fd3aa3bdb051771368065f35'},
 {step:'open-missing',hash:'0xbdb5ab758a17feb3e2a75073ac95c2e61161b053ce6c39f41387524ab8c0670b'},
 {step:'commit-missing',hash:'0xbb58f685528ac3ba2e267467794e073e98e5daac4e8a853f1dd5c12145b2c545'},
 {step:'open-good',hash:'0x1dd2a600dff6ccdb3b69cc3172a1263dbaeb3ce10fcf59a90f3c98f2207a9f97'}
];
const steps=['deploy','open-missing','commit-missing','open-good','commit-good','wrong-reveal','reveal-good','resolve-good','replay-good','open-void','commit-void','reveal-void','resolve-void','resolve-missing'];
let ledger=fs.existsSync('PROOFS.json')?JSON.parse(fs.readFileSync('PROOFS.json','utf8')):{address,fixture_commit:commit,transactions:seed};
if(ledger.address!==address||ledger.fixture_commit!==commit)throw Error('Proof context mismatch');
const save=()=>fs.writeFileSync('PROOFS.json',JSON.stringify(ledger,null,2)+'\n');
function launch(step){return new Promise((resolve,reject)=>{
 const child=spawn(process.execPath,['--dns-result-order=ipv4first','scripts/demo.mjs',step,address,commit],{windowsHide:true,stdio:['ignore','pipe','pipe']});
 let output='',carry='',known;
 child.stdout.on('data',chunk=>{
  carry+=chunk.toString();const lines=carry.split(/\r?\n/);carry=lines.pop();
  for(const line of lines){const m=line.match(/^BROADCAST_HASH (0x[0-9a-fA-F]{64})$/);
   if(m){if(known&&known!==m[1]){child.kill();reject(Error('Multiple hashes'));return;}
    known=m[1];ledger.transactions.push({step,hash:known});save();console.log(JSON.stringify({step,broadcast:known}));}
  }
  if(output.length<4096)output+=chunk.toString();
 });
 child.stderr.resume();
 const timer=setTimeout(()=>{child.kill();reject(Error('Proof child timeout; inspect history'));},150000);
 child.on('error',()=>{clearTimeout(timer);reject(Error('Launch failure'));});
 child.on('close',()=>{clearTimeout(timer);if(!known)reject(Error('No known broadcast; inspect history before retry'));else resolve();});
});}
async function verify(entry){
 for(let i=0;i<30;i++){
  const tx=await rpc('eth_getTransactionByHash',[entry.hash]);
  if(tx.status==='FINALIZED'){
   const leader=tx.consensus_data?.leader_receipt?.find(x=>x.mode==='leader');
   const expected=entry.step==='wrong-reveal'?'Reveal commitment mismatch':entry.step==='replay-good'?'Round terminal':null;
   const raw=leader?.genvm_result?.stderr||leader?.result;
   const decoded=typeof raw==='string'?(/^[A-Za-z0-9+/]*={0,2}$/.test(raw)&&raw.length%4===0?Buffer.from(raw,'base64').toString('utf8'):raw):'';
   if(leader?.execution_result!==(expected?'ERROR':'SUCCESS')||tx.result_name!=='MAJORITY_AGREE'||(expected&&!decoded.includes(expected)))throw Error('Execution or expected-error mismatch');
   Object.assign(entry,{status:tx.status,execution:leader.execution_result,consensus:tx.result_name,...(expected?{expected_error:expected}:{})});save();console.log(JSON.stringify(entry));return;
  }
  await new Promise(r=>setTimeout(r,4000));
 }
 throw Error('Finalization pending; resume known hashes only');
}
try{
 save();
 for(const step of steps){
  let entry=ledger.transactions.find(x=>x.step===step);
  if(!entry){await launch(step);entry=ledger.transactions.find(x=>x.step===step);}
  await verify(entry);
 }
 console.log('All documented transactions finalized with expected execution outcomes.');
}catch{
 console.error('Proof sequence stopped safely. Inspect sanitized ledger/known receipt before continuing. No automatic rebroadcast.');
 process.exitCode=1;
}
