import ast
import hashlib
import itertools
import json
import re
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
import pytest

TREE = ast.parse(Path('contracts/SealedBeliefScoreboard.py').read_text())
NS = {'json': json, 'hashlib': hashlib, 're': re, 'SCALE':10000, 'MAX_SCORE':100000000, 'POLICY':'sealed-belief-brier-v1'}
exec(compile(ast.Module(body=[n for n in TREE.body if isinstance(n, ast.FunctionDef)
     and n.name not in ('fail','now','fetch_source')],type_ignores=[]),'actual-helpers','exec'),NS)
SALT = 'ab'*32
FIRST = Path('examples/archive-policy.txt').read_bytes()
SECOND = Path('examples/archive-faq.txt').read_bytes()


def addr(value):
    from genlayer import Address
    return str(Address(value if isinstance(value,bytes) else str(value)))


def stats_for(board, creator, participant):
    from genlayer import Address
    return board.get_stats(Address(addr(creator)),Address(addr(participant)))


@pytest.fixture
def board(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    return direct_deploy('contracts/SealedBeliefScoreboard.py')


def open_round(board, roster, nonce='demo', first_hash=None):
    return board.open_round(nonce,'Do these archive rules permit automated bulk downloading without prior approval?',
        '|'.join(addr(p) for p in roster),60,60,'mahdiaqal','sealed-belief-scoreboard','a'*40,
        'examples/archive-policy.txt',first_hash or hashlib.sha256(FIRST).hexdigest(),
        'examples/archive-faq.txt',hashlib.sha256(SECOND).hexdigest())


def seal(board, rid, participant, probability=2000, salt=SALT):
    config = board.get_round(rid)['config']
    return NS['probability_commitment'](config['contract'],rid,addr(participant),probability,salt)


def mock_evidence(vm, labels=('REFUTE','REFUTE'), http=200, body=FIRST):
    vm.clear_mocks()
    vm.mock_web(r'.*/archive-policy\.txt',{'status':http,'body':body})
    vm.mock_web(r'.*/archive-faq\.txt',{'status':200,'body':SECOND})
    vm.mock_llm(r'(?s).*SEALED BELIEF OUTCOME.*',json.dumps({'labels':list(labels)}))


def warp(vm, timestamp):
    from genlayer import gl
    value=datetime.fromtimestamp(timestamp,timezone.utc).isoformat()
    vm.warp(value)
    gl.message_raw['datetime']=value


def test_two_authenticated_forecasts_score_from_evidence(board,direct_vm,direct_alice,direct_bob,direct_charlie):
    rid=open_round(board,[direct_alice,direct_bob])
    board.commit_probability(rid,seal(board,rid,direct_alice,2000))
    with direct_vm.expect_revert('Commit barrier not reached'):
        board.reveal_probability(rid,2000,SALT)
    direct_vm.sender=direct_bob
    board.commit_probability(rid,seal(board,rid,direct_bob,8000))
    board.reveal_probability(rid,8000,SALT)
    direct_vm.sender=direct_alice
    board.reveal_probability(rid,2000,SALT)
    direct_vm.sender=direct_charlie  # Permissionless resolution: no creator veto.
    mock_evidence(direct_vm)
    board.resolve(rid)
    record=board.get_round(rid)
    assert record['status']=='SCORED'
    assert record['final']['report']['answer']=='NO'
    assert record['final']['scores'][addr(direct_alice)]['score']==96000000
    assert record['final']['scores'][addr(direct_bob)]['score']==36000000
    assert stats_for(board,direct_alice,direct_alice)=={'committed':1,'scored':1,'score_sum':96000000,'loss_sum':4000000,'missed_reveal':0,'voided':0,'pending':0}
    final=dict(record['final']);root=final.pop('root')
    assert root==NS['digest'](final)
    assert record['config_root']==NS['digest'](record['config'])
    for source in final['report']['sources']:
        assert source['body'] and source['hash']==hashlib.sha256(source['body'].encode()).hexdigest()
    with direct_vm.expect_revert('Round terminal'):board.resolve(rid)
    assert board.get_round(rid)==record


@pytest.mark.parametrize('labels',list(itertools.product(('SUPPORT','REFUTE','UNKNOWN'),repeat=2)))
def test_all_semantic_vectors_fail_closed(board,direct_vm,direct_alice,labels):
    rid=open_round(board,[direct_alice])
    board.commit_probability(rid,seal(board,rid,direct_alice))
    board.reveal_probability(rid,2000,SALT)
    mock_evidence(direct_vm,labels)
    board.resolve(rid)
    rec=board.get_round(rid)
    expected='YES' if labels==('SUPPORT','SUPPORT') else 'NO' if labels==('REFUTE','REFUTE') else 'UNKNOWN'
    assert rec['final']['report']['answer']==expected
    assert rec['status']==('VOID' if expected=='UNKNOWN' else 'SCORED')
    stats=stats_for(board,direct_alice,direct_alice)
    assert stats['pending']==0 and stats['scored']==(expected!='UNKNOWN') and stats['voided']==(expected=='UNKNOWN')


@pytest.mark.parametrize('kind',['hash','http','encoding','oversize'])
def test_fake_or_unavailable_evidence_never_scores(board,direct_vm,direct_alice,kind):
    rid=open_round(board,[direct_alice],first_hash='f'*64 if kind=='hash' else None)
    board.commit_probability(rid,seal(board,rid,direct_alice))
    board.reveal_probability(rid,2000,SALT)
    mock_evidence(direct_vm,http=503 if kind=='http' else 200,body=b'\xff' if kind=='encoding' else b'x'*6001 if kind=='oversize' else FIRST)
    board.resolve(rid)
    rec=board.get_round(rid)
    assert rec['status']=='VOID' and rec['final']['report']['labels']==['UNKNOWN','UNKNOWN']
    assert stats_for(board,direct_alice,direct_alice)['score_sum']==0


def test_identity_round_probability_salt_bindings(board,direct_vm,direct_alice,direct_bob):
    rid=open_round(board,[direct_alice,direct_bob])
    other=open_round(board,[direct_alice,direct_bob],nonce='other')
    board.commit_probability(rid,seal(board,rid,direct_alice))
    with direct_vm.expect_revert('Commitment already exists'):board.commit_probability(rid,'f'*64)
    board.commit_probability(other,seal(board,rid,direct_alice))  # Copied digest cannot reveal in another round.
    direct_vm.sender=direct_bob
    board.commit_probability(rid,seal(board,rid,direct_alice))  # Copied digest cannot impersonate Alice.
    with direct_vm.expect_revert('Reveal commitment mismatch'):board.reveal_probability(rid,2000,SALT)
    direct_vm.sender=direct_alice
    with direct_vm.expect_revert('Reveal commitment mismatch'):board.reveal_probability(rid,8000,SALT)
    with direct_vm.expect_revert('Reveal commitment mismatch'):board.reveal_probability(rid,2000,'cd'*32)
    warp(direct_vm,board.get_round(other)['config']['commit_deadline'])
    with direct_vm.expect_revert('Reveal commitment mismatch'):board.reveal_probability(other,2000,SALT)
    board.reveal_probability(rid,2000,SALT)
    with direct_vm.expect_revert('already revealed'):board.reveal_probability(rid,2000,SALT)


def test_missing_commit_cannot_lock_round_or_penalize_nonconsenter(board,direct_vm,direct_alice,direct_bob,direct_charlie):
    rid=open_round(board,[direct_alice,direct_bob])
    board.commit_probability(rid,seal(board,rid,direct_alice))
    deadline=board.get_round(rid)['config']['reveal_deadline']
    direct_vm.sender=direct_charlie
    with direct_vm.expect_revert('Not invited'):board.commit_probability(rid,'f'*64)
    with direct_vm.expect_revert('Resolution not ready'):board.resolve(rid)
    warp(direct_vm,deadline)
    mock_evidence(direct_vm)
    board.resolve(rid)
    rec=board.get_round(rid)
    assert rec['final']['scores'][addr(direct_bob)]=={'status':'NOT_COMMITTED'}
    assert rec['final']['scores'][addr(direct_alice)]=={'status':'MISSED_REVEAL','score':0,'loss':100000000}
    assert stats_for(board,direct_alice,direct_bob)['committed']==0
    assert stats_for(board,direct_alice,direct_alice)['missed_reveal']==1


def test_deadline_boundaries(board,direct_vm,direct_alice,direct_bob):
    rid=open_round(board,[direct_alice,direct_bob])
    board.commit_probability(rid,seal(board,rid,direct_alice))
    cfg=board.get_round(rid)['config']
    warp(direct_vm,cfg['commit_deadline'])
    direct_vm.sender=direct_bob
    with direct_vm.expect_revert('Commit phase closed'):board.commit_probability(rid,'f'*64)
    direct_vm.sender=direct_alice
    warp(direct_vm,cfg['reveal_deadline'])
    with direct_vm.expect_revert('Reveal deadline passed'):board.reveal_probability(rid,2000,SALT)
    mock_evidence(direct_vm)
    board.resolve(rid)


@pytest.mark.parametrize('probability,salt',[(-1,SALT),(10001,SALT),(True,SALT),(1.5,SALT),(5000,''),(5000,'x'*64)])
def test_bad_reveal_inputs(probability,salt):
    with pytest.raises(ValueError):NS['probability_commitment']('c','r','p',probability,salt)


def test_exhaustive_integer_brier_range_symmetry_and_properness():
    for p in range(10001):
        yes,no=NS['brier'](p,'YES'),NS['brier'](10000-p,'NO')
        assert yes==no and 0<=yes['score']<=100000000 and yes['score']+yes['loss']==100000000
    # Expected loss at true q is uniquely minimized at p=q; no floating point needed.
    for q in (0,1,2000,5000,8000,9999,10000):
        best=q*(q-10000)**2+(10000-q)*q*q
        for p in range(10001):
            candidate=q*(p-10000)**2+(10000-q)*p*p
            assert candidate-best==10000*(p-q)**2


def test_actual_validator_refetches_and_rejects_each_consequential_change():
    cls=next(n for n in TREE.body if isinstance(n,ast.ClassDef))
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='resolve')
    fn=next(n for n in method.body if isinstance(n,ast.FunctionDef) and n.name=='validator')
    class Return:
        def __init__(self,data):self.calldata=data
    expected={'binding':{'round':'r'},'sources':[{'body':'observed'}],'labels':['REFUTE','REFUTE'],'answer':'NO'}
    calls=[]
    def observe():calls.append(1);return expected
    ns=dict(NS,gl=SimpleNamespace(vm=SimpleNamespace(Return=Return)),observe=observe)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-validator','exec'),ns)
    assert ns['validator'](Return(expected)) and calls==[1]
    for field,value in [('answer','YES'),('labels',['SUPPORT','SUPPORT']),('binding',{'round':'other'}),('sources',[{'body':'forged'}])]:
        assert not ns['validator'](Return(dict(expected,**{field:value})))
    assert not ns['validator'](object())


@pytest.mark.parametrize('path',['../secret.txt','/a.txt','a//b.txt','a/./b.txt','https://host/a.txt','a%2fb.txt'])
def test_source_path_escape_rejected(path):
    with pytest.raises(ValueError):NS['source_spec']('owner','repo','a'*40,path,'f'*64)


def test_no_forged_commitment_match():
    spec={'url':'https://raw.githubusercontent.com/o/r/'+'a'*40+'/t.txt','sha256':'f'*64}
    with pytest.raises(ValueError):NS['validate_source'](spec,{'url':spec['url'],'http':200,'status':'OK','hash':'f'*64,'body':'forged'})
    with pytest.raises(ValueError):NS['answer_from'](['REFUTE','REFUTE'],False)
    with pytest.raises(ValueError):NS['parse_labels']('{"labels":["REFUTE","REFUTE"],"labels":["SUPPORT","SUPPORT"]}')


def test_permanent_outage_void_has_no_asserted_outcome(board,direct_vm,direct_alice,direct_charlie):
    rid=open_round(board,[direct_alice])
    board.commit_probability(rid,seal(board,rid,direct_alice))
    deadline=board.get_round(rid)['config']['reveal_deadline']+86400
    direct_vm.sender=direct_charlie
    warp(direct_vm,deadline-1)
    with direct_vm.expect_revert('Resolution grace not elapsed'):board.void_expired(rid)
    warp(direct_vm,deadline)
    board.void_expired(rid)
    rec=board.get_round(rid)
    assert rec['status']=='VOID' and rec['final']['report']['sources']==[]
    assert rec['final']['report']['reason']=='DEADLINE_FALLBACK'
    assert stats_for(board,direct_alice,direct_alice)['voided']==1
    with direct_vm.expect_revert('Round terminal'):board.resolve(rid)


def test_nonce_and_roster_validation(board,direct_vm,direct_alice):
    rid=open_round(board,[direct_alice])
    with direct_vm.expect_revert('Round nonce used'):open_round(board,[direct_alice])
    with direct_vm.expect_revert('Invalid participants'):open_round(board,[direct_alice,direct_alice],nonce='duplicate')
    assert board.get_round(rid)['status']=='OPEN'


@pytest.mark.parametrize('tamper',['answer','labels','body'])
def test_post_consensus_checks_reject_forged_report_before_scoring(board,direct_vm,direct_alice,monkeypatch,tamper):
    from genlayer import gl
    rid=open_round(board,[direct_alice])
    board.commit_probability(rid,seal(board,rid,direct_alice))
    board.reveal_probability(rid,2000,SALT)
    mock_evidence(direct_vm)
    original=gl.vm.run_nondet_unsafe
    def forged(observe,validator):
        report=original(observe,validator)
        if tamper=='answer':report['answer']='YES'
        elif tamper=='labels':report['labels']=['SUPPORT','REFUTE']
        else:report['sources'][0]['body']='substitution'
        return report
    monkeypatch.setattr(gl.vm,'run_nondet_unsafe',forged)
    with direct_vm.expect_revert('Invalid outcome report'):board.resolve(rid)
    assert board.get_round(rid)['status']=='OPEN'
    assert stats_for(board,direct_alice,direct_alice)['scored']==0


def test_commitment_domain_separation():
    data=['contract','round','participant',2000,SALT]
    expected=NS['probability_commitment'](*data)
    for index in range(3):
        other=list(data);other[index]+='other'
        assert NS['probability_commitment'](*other)!=expected


@pytest.mark.parametrize('raw',[{}, {'labels':[]}, {'labels':['REFUTE',True]},
    {'labels':['REFUTE','REFUTE'],'answer':'YES'}, {'labels':['refute','refute']}])
def test_malformed_model_output_never_finalizes(board,direct_vm,direct_alice,raw):
    rid=open_round(board,[direct_alice])
    board.commit_probability(rid,seal(board,rid,direct_alice))
    board.reveal_probability(rid,2000,SALT)
    mock_evidence(direct_vm)
    direct_vm.clear_mocks()
    direct_vm.mock_web(r'.*/archive-policy\.txt',{'status':200,'body':FIRST})
    direct_vm.mock_web(r'.*/archive-faq\.txt',{'status':200,'body':SECOND})
    direct_vm.mock_llm(r'(?s).*SEALED BELIEF OUTCOME.*',json.dumps(raw))
    with direct_vm.expect_revert('Invalid outcome labels'):board.resolve(rid)
    assert board.get_round(rid)['status']=='OPEN'
    assert stats_for(board,direct_alice,direct_alice)['scored']==0
