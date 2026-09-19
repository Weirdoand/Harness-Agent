import json
import threading
import pytest
import llm_chat as app

@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'WORKFLOW_RUNTIME_DIR', tmp_path)
    name='resume_'+tmp_path.name.replace('-','_')
    app.register_workflow(name,'resume', ['p'], 'def run(state,args): state.phase("p"); return state.agent(args["prompt"])', {'type':'object','properties':{'prompt':{'type':'string'}},'required':['prompt']})
    yield name
    app.WORKFLOWS.registry.pop(name,None)

def test_four_artifacts_and_snapshot(env,tmp_path):
    r=app.run_workflow(env,{'prompt':'x'},runner=app.MockAgentRunner('ok'))
    files={p.name for p in tmp_path.iterdir()}
    assert {r['run_id']+'.json',r['run_id']+'.output.json',r['run_id']+'.journal.jsonl',r['run_id']+'.lock'} <= files
    assert json.loads((tmp_path/(r['run_id']+'.json')).read_text())['status']=='completed'

def test_completed_resume_idempotent(env):
    runner=app.MockAgentRunner('ok'); first=app.run_workflow(env,{'prompt':'x'},runner=runner)
    second=app.run_workflow(env,{'prompt':'x'},runner=runner,resume_from_run_id=first['run_id'])
    assert second['run_id']==first['run_id'] and len(runner.calls)==1
    assert json.loads((app.Path(app.WORKFLOW_RUNTIME_DIR)/(first['run_id']+'.json')).read_text())['attempt']==2

def test_partial_failure_then_retry(env):
    app.WORKFLOWS.registry.pop(env, None)
    app.register_workflow(env,'resume',['p'], 'def run(state,args): state.phase("p"); state.agent("first"); return state.agent("second")')
    calls=[]
    def run(prompt,**kw):
        calls.append(prompt)
        if prompt == 'second' and calls.count('second') == 1: raise RuntimeError('boom')
        return 'ok'
    runner=app.MockAgentRunner(run)
    with pytest.raises(RuntimeError): app.run_workflow(env,{'prompt':'x'},runner=runner)
    rid=next(p.stem for p in app.Path(app.WORKFLOW_RUNTIME_DIR).glob('*.json') if not p.name.endswith('.output.json'))
    assert app.run_workflow(env,{'prompt':'x'},runner=runner,resume_from_run_id=rid)['result']=='ok'
    assert calls == ['first','second','second']

def test_parallel_singleflight(tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'WORKFLOW_RUNTIME_DIR', tmp_path)
    name='parallel_'+tmp_path.name; count=[]
    class R(app.MockAgentRunner):
        def __call__(self,prompt,**kw): count.append(prompt); return super().__call__(prompt,**kw)
    app.register_workflow(name,'p',[], 'def run(state,args): return state.parallel([lambda: state.agent("same"), lambda: state.agent("same")])')
    try: assert app.run_workflow(name,{},runner=R('ok'))['result']==['ok','ok'] and len(count)==1
    finally: app.WORKFLOWS.registry.pop(name,None)

def test_invalid_resume_does_not_modify(env):
    r=app.run_workflow(env,{'prompt':'x'},runner=app.MockAgentRunner('ok')); before=(app.Path(app.WORKFLOW_RUNTIME_DIR)/(r['run_id']+'.json')).read_bytes()
    with pytest.raises(app.WorkflowError): app.run_workflow(env,{'prompt':'y'},resume_from_run_id=r['run_id'])
    assert before==(app.Path(app.WORKFLOW_RUNTIME_DIR)/(r['run_id']+'.json')).read_bytes()

def test_torn_journal_tail_recovers(env,tmp_path):
    r=app.run_workflow(env,{'prompt':'x'},runner=app.MockAgentRunner('ok')); (tmp_path/(r['run_id']+'.journal.jsonl')).write_text('{bad')
    assert app.run_workflow(env,{'prompt':'x'},runner=app.MockAgentRunner('ok'),resume_from_run_id=r['run_id'])['status']=='completed'

def test_corrupt_journal_middle_rejected(env,tmp_path):
    r=app.run_workflow(env,{'prompt':'x'},runner=app.MockAgentRunner('ok')); p=tmp_path/(r['run_id']+'.journal.jsonl'); before=(tmp_path/(r['run_id']+'.json')).read_bytes(); p.write_text(p.read_text()+'{bad}\n')
    with pytest.raises(Exception): app.run_workflow(env,{'prompt':'x'},resume_from_run_id=r['run_id'])
    assert before==(tmp_path/(r['run_id']+'.json')).read_bytes()

def test_corrupt_output_rejected(env,tmp_path):
    r=app.run_workflow(env,{'prompt':'x'},runner=app.MockAgentRunner('ok')); (tmp_path/(r['run_id']+'.output.json')).write_text('{bad')
    with pytest.raises(app.WorkflowError): app.run_workflow(env,{'prompt':'x'},resume_from_run_id=r['run_id'])

def test_nested_journal_shared(tmp_path):
    monkey=tmp_path; child='c_'+tmp_path.name; parent='p_'+tmp_path.name
    app.register_workflow(child,'c',[], 'def run(state,args): state.log("child"); return 1')
    app.register_workflow(parent,'p',[], 'def run(state,args): return state.workflow("'+child+'")')
    try:
        r=app.run_workflow(parent,{},runner=app.MockAgentRunner('ok')); assert any(x.get('message')=='child' for x in r['journal'])
    finally: app.WORKFLOWS.registry.pop(child,None); app.WORKFLOWS.registry.pop(parent,None)

def test_invalid_runid_rejected_without_files(env,tmp_path):
    with pytest.raises(app.WorkflowError): app.run_workflow(env,{},resume_from_run_id='bad')

def test_run_lock_busy(env,tmp_path):
    rid='a'*32; (tmp_path/(rid+'.json')).write_text(json.dumps({'version':1,'run_id':rid,'name':env,'args':{'prompt':'x'},'status':'failed','attempt':1,'started_at':0})); lock=app._RunLock(tmp_path/(rid+'.lock'))
    with lock:
        with pytest.raises(app.WorkflowError,match='locked'): app.run_workflow(env,{'prompt':'x'},resume_from_run_id=rid)
