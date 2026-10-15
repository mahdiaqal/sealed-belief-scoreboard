import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
import {digest,read,sha} from './check.mjs';
const [mode,address,commit]=process.argv.slice(2);
const creator='0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42';
if(!/^0x[0-9a-fA-F]{40}$/.test(address??'')||! /^[0-9a-f]{40}$/.test(commit??''))throw Error('Contract and fixture commit required');
const native=createRequire(process.env.BELIEF_CLI_PATH||path.resolve('../intent-firewall/node_modules/genlayer/dist/index.js'));
const keytar=native('keytar'),service='sealed-belief-demo-salts';
const variant=mode.endsWith('void')?'void':mode.endsWith('missing')?'missing':'good';
const nonce='demo-'+variant,round=digest({contract:address,creator,nonce}),vault=address+':'+nonce;
let args;
if(mode.startsWith('open-')){
 args=['open_round',[nonce,'Do these archive rules permit automated bulk downloading without prior approval?',creator,
  variant==='missing'?60:3600,variant==='missing'?60:3600,'mahdiaqal','sealed-belief-scoreboard',commit,
  'examples/archive-policy.txt',variant==='void'?'f'.repeat(64):sha(fs.readFileSync('examples/archive-policy.txt')),
  'examples/archive-faq.txt',sha(fs.readFileSync('examples/archive-faq.txt'))]];
}else{
 const record=await read(address,'get_round',[round]);
 if(mode.startsWith('commit-')){
  if(record.commitments[creator])throw Error('Already committed: inspect prior receipt, do not rebroadcast');
  let saved=await keytar.getPassword(service,vault);
  if(!saved){saved=JSON.stringify({probability:2000,salt:crypto.randomBytes(32).toString('hex')});await keytar.setPassword(service,vault,saved);}
  const {probability,salt}=JSON.parse(saved);
  args=['commit_probability',[round,digest({policy:'sealed-belief-brier-v1',contract:address,round,participant:creator,probability,salt})]];
 }else if(mode.startsWith('reveal-')||mode==='wrong-reveal'){
  if(Object.hasOwn(record.reveals,creator))throw Error('Already revealed: inspect prior receipt');
  const saved=await keytar.getPassword(service,vault);if(!saved)throw Error('Missing native-vault demo salt');
  const {probability,salt}=JSON.parse(saved);
  args=['reveal_probability',[round,mode==='wrong-reveal'?8000:probability,salt]];
 }else if(mode.startsWith('resolve-')||mode==='replay-good'){
  if(mode!=='replay-good'&&record.status!=='OPEN')throw Error('Already terminal: inspect prior receipt');
  args=['resolve',[round]];
 }else throw Error('Unknown demo step');
}
console.log(JSON.stringify({mode,round_id:round}));
const result=spawnSync(process.execPath,['scripts/run-cli.cjs','write',address,args[0],'--args',...args[1].map(String)],{windowsHide:true,stdio:'inherit'});
process.exitCode=result.status??1;
