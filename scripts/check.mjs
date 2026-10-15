import fs from 'node:fs';
import crypto from 'node:crypto';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {CalldataAddress} from 'genlayer-js/types';
export const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0')):
 Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>canonical(k)+':'+canonical(x[k])).join(',')+'}';
export const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
export const digest=x=>sha(canonical(x));
export async function rpc(method,params){
 const r=await fetch('https://studio.genlayer.com/api',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params}),signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error('HTTP failure');const p=await r.json();if(p.error||p.result==null)throw Error('RPC failure');return p.result;
}
export const client=createClient({chain:studionet});
export const read=(address,functionName,args)=>client.readContract({address,functionName,args});
if(process.argv[1]?.endsWith('check.mjs'))try{
 const [mode,value,extra]=process.argv.slice(2);
 if(mode==='source'){
  const norm=x=>x.replace(/\r\n/g,'\n').trimEnd()+'\n';
  const actual=norm(Buffer.from(await rpc('gen_getContractCode',[value]),'base64').toString('utf8'));
  const local=norm(fs.readFileSync('contracts/SealedBeliefScoreboard.py','utf8'));
  console.log(JSON.stringify({address:value,source_matches:actual===local,source_sha256:sha(actual)}));if(actual!==local)process.exitCode=1;
 }else if(['success','error'].includes(mode)){
  let tx=await rpc('eth_getTransactionByHash',[value]);
  for(let i=0;tx.status!=='FINALIZED'&&i<15;i++){await new Promise(r=>setTimeout(r,2000));tx=await rpc('eth_getTransactionByHash',[value]);}
  const leader=tx.consensus_data?.leader_receipt?.find(x=>x.mode==='leader'),raw=leader?.genvm_result?.stderr||leader?.result;
  const decoded=typeof raw!=='string'?'':(/^[A-Za-z0-9+/]*={0,2}$/.test(raw)&&raw.length%4===0?Buffer.from(raw,'base64').toString('utf8'):raw);
  console.log(JSON.stringify({hash:value,address:tx.to_address??tx.to,status:tx.status,execution:leader?.execution_result,consensus:tx.result_name,...(extra?{expected_error_matched:decoded.includes(extra)}:{})}));
  if(tx.status!=='FINALIZED'||leader?.execution_result!==(mode==='error'?'ERROR':'SUCCESS')||tx.result_name!=='MAJORITY_AGREE'||(extra&&!decoded.includes(extra)))process.exitCode=1;
 }else if(mode==='round'){
  const record=await read(value,'get_round',[extra]);
  if(digest(record.config)!==record.config_root||record.id!==extra||record.config.contract!==value)throw Error('Config binding mismatch');
  if(record.final){
   const {root,...body}=record.final;if(digest(body)!==root)throw Error('Final root mismatch');
   const r=record.final.report,b=r.binding;
   if(b.round!==extra||b.config_root!==record.config_root||canonical(b.commitments)!==canonical(record.commitments)||canonical(b.reveals)!==canonical(record.reveals))throw Error('Final binding mismatch');
   const fallback=r.reason==='DEADLINE_FALLBACK';
   if(fallback){if(r.sources.length||r.answer!=='UNKNOWN'||b.resolved_at<record.config.reveal_deadline+86400)throw Error('Invalid fallback');}
   else{
    if(r.sources.length!==2)throw Error('Source vector');
    const valid=r.sources.every((s,i)=>{
     const spec=record.config.sources[i];if(s.url!==spec.url)throw Error('Source mismatch');
     if(s.body&&sha(s.body)!==s.hash)throw Error('Body hash');
     if(s.status==='OK'&&(s.http!==200||s.hash!==spec.sha256))throw Error('Hash/status mismatch');
     return s.status==='OK';
    });
    const answer=valid&&r.labels.every(x=>x==='SUPPORT')?'YES':valid&&r.labels.every(x=>x==='REFUTE')?'NO':'UNKNOWN';
    if(r.labels.length!==2||r.labels.some(x=>!['SUPPORT','REFUTE','UNKNOWN'].includes(x))||answer!==r.answer||(!valid&&r.labels.some(x=>x!=='UNKNOWN')))throw Error('Answer/vector contradiction');
   }
   if(record.status!==(r.answer==='UNKNOWN'?'VOID':'SCORED'))throw Error('State mismatch');
   for(const p of record.config.participants){
    const entry=record.final.scores[p];
    if(!record.commitments[p]){if(entry.status!=='NOT_COMMITTED')throw Error('Nonconsenter scored');continue;}
    if(r.answer==='UNKNOWN'){if(entry.status!=='VOID'||entry.score!==undefined)throw Error('Void scored');continue;}
    const has=Object.hasOwn(record.reveals,p),probability=record.reveals[p],loss=has?(probability-(r.answer==='YES'?10000:0))**2:100000000;
    if(entry.loss!==loss||entry.score!==100000000-loss||entry.status!==(has?'SCORED':'MISSED_REVEAL')||(has&&entry.probability!==probability))throw Error('Score mismatch');
   }
  }
  const summary={...record,final:record.final?{...record.final,report:{...record.final.report,sources:record.final.report.sources.map(({body,...rest})=>rest)}}:null};
  console.log(JSON.stringify({verified:true,record:summary}));
 }else if(mode==='stats'){
  const typed=x=>new CalldataAddress(Buffer.from(x.slice(2),'hex'));
  const stats=await read(value,'get_stats',[typed(extra),typed(process.argv[5])]);
  if(stats.pending!==stats.committed-stats.scored-stats.voided||stats.score_sum+stats.loss_sum!==stats.scored*100000000)throw Error('Aggregate conservation');
  console.log(JSON.stringify({verified:true,creator:extra,participant:process.argv[5],stats}));
 }else throw Error('Unknown check mode');
}catch{console.error('Sanitized verification failure; inspect history before rebroadcast');process.exitCode=1;}
