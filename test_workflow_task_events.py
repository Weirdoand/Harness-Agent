import json
import pytest
import llm_chat as app

@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(app,'WORKFLOW_RUNTIME_DIR',tmp_path)

def register(name, code):
    app.register_workflow(name,'events',['p'],code,{'type':'object'})

def result_runner(value='ok', tokens=3):
    return app.MockAgentRunner(app.WorkflowAgentResult(value, {'total_tokens':tokens}))

def test_event_boundaries_and_sequence():
    n='ev_a'; register(n,'def run(state,args): state.phase("p"); state.log("x"); return state.agent("q")'); events=[]
    try:
        out=app.run_workflow(n,event_sink=events.append,runner=result_runner()); assert events[0]['type']=='task_started' and events[-1]['type']=='task_notification'; assert [e['sequence'] for e in events]==sorted(e['sequence'] for e in events)
    finally: app.WORKFLOWS.registry.pop(n,None)

def test_progress_events():
    n='ev_b'; register(n,'def run(state,args): state.phase("p"); state.log("hello"); return state.agent("q")'); events=[]
    try: app.run_workflow(n,event_sink=events.append,runner=result_runner()); assert {'phase','log','agent_started'} <= {e.get('progress_type') for e in events if e['type']=='task_progress'}
    finally: app.WORKFLOWS.registry.pop(n,None)

def test_counts_tokens():
    n='ev_c'; register(n,'def run(state,args): return state.agent("q")');
    try: assert (lambda r: r['agent_count']==1 and r['token_count']==3)(app.run_workflow(n,runner=result_runner()))
    finally: app.WORKFLOWS.registry.pop(n,None)

def test_parallel_singleflight_count():
    n='ev_d'; register(n,'def run(state,args): return state.parallel([lambda: state.agent("same"),lambda: state.agent("same")])'); calls=[]
    class R(app.MockAgentRunner):
        def __call__(self,prompt,**kw): calls.append(prompt); return super().__call__(prompt,**kw)
    try: assert app.run_workflow(n,runner=R(app.WorkflowAgentResult('ok',{'total_tokens':2})))['agent_count']==1 and len(calls)==1
    finally: app.WORKFLOWS.registry.pop(n,None)

def test_completed_resume_cached_progress():
    n='ev_e'; register(n,'def run(state,args): return state.agent("q")'); r=result_runner(); first=app.run_workflow(n,runner=r); second=app.run_workflow(n,runner=r,resume_from_run_id=first['run_id']); assert second['agent_count']==1 and second['token_count']==3 and len(r.calls)==1 and second['events'][-1]['type']=='task_notification'
    assert any(e.get('progress_type')=='agent_cached' for e in second['events'])
    assert second['events'][-1]['attempt_agent_count']==0 and second['events'][-1]['attempt_token_count']==0
    app.WORKFLOWS.registry.pop(n,None)

def test_failed_notification_after_snapshot():
    n='ev_f'; register(n,'def run(state,args): return state.agent("q")'); events=[]
    try:
        with pytest.raises(RuntimeError): app.run_workflow(n,event_sink=events.append,runner=app.MockAgentRunner(lambda p,**k: (_ for _ in ()).throw(RuntimeError('x'))))
        assert events[-1]['type']=='task_notification' and events[-1]['status']=='failed'
        assert json.loads((app.Path(app.WORKFLOW_RUNTIME_DIR)/(events[-1]['run_id']+'.json')).read_text())['status']=='failed'
    finally: app.WORKFLOWS.registry.pop(n,None)

def test_call_llm_length_usage_accumulates(monkeypatch):
    class Message: content='part'; tool_calls=None
    class Choice:
        def __init__(self, reason, usage): self.finish_reason=reason; self.message=Message(); self.usage=usage
    class API:
        def __init__(self): self.i=0
        def create(self, **kwargs):
            self.i+=1; return type('Resp',(),{'choices':[Choice('length' if self.i==1 else 'stop', {'prompt_tokens':2,'completion_tokens':3,'total_tokens':5})]})()
    fake=API(); monkeypatch.setattr(app,'client',type('C',(),{'chat':type('Chat',(),{'completions':fake})()})())
    result=app.call_llm([{'role':'user','content':'x'}])
    assert isinstance(result, app.LLMCallResult)

def test_sink_failure_ignored():
    n='ev_g'; register(n,'def run(state,args): return 1')
    try: assert app.run_workflow(n,event_sink=lambda e: (_ for _ in ()).throw(RuntimeError()),runner=result_runner())['status']=='completed'
    finally: app.WORKFLOWS.registry.pop(n,None)

def test_nested_boundaries():
    c='ev_c1'; n='ev_h'; register(c,'def run(state,args): return 1'); register(n,'def run(state,args): return state.workflow("'+c+'")'); events=[]
    try: app.run_workflow(n,event_sink=events.append,runner=result_runner()); assert sum(e['type']=='task_started' for e in events)==1 and sum(e['type']=='task_notification' for e in events)==1
    finally: app.WORKFLOWS.registry.pop(c,None); app.WORKFLOWS.registry.pop(n,None)


