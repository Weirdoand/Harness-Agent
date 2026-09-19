import pytest
import llm_chat as app

@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'WORKFLOW_RUNTIME_DIR', tmp_path)

def clean(name):
    app.WORKFLOWS.registry.pop(name, None)

def test_fixed_lead_tool_and_registry_name_not_projected():
    app.refresh_tool_pool()
    lead = next(x for x in app.TOOLS if x['function']['name'] == 'workflow')
    params = lead['function']['parameters']
    assert set(params['properties']) == {'name','args','resume_from_run_id'}
    assert params['additionalProperties'] is False
    assert 'workflow' not in {x['function']['name'] for x in app.SUB_TOOLS}

def test_handler_envelope_and_resume_idempotency():
    name='it_envelope'
    try:
        app.register_workflow(name,'test',[],'def run(state,args): return state.agent(args["p"])',{'type':'object','properties':{'p':{'type':'string'}}})
        runner=app.MockAgentRunner('ok'); first=app.run_workflow(name,{'p':'x'},runner=runner)
        second=app.run_workflow(name,{'p':'x'},runner=runner,resume_from_run_id=first['run_id'])
        assert first['status']==second['status']=='completed' and len(runner.calls)==1
    finally: clean(name)

def test_unknown_resume_rejected():
    with pytest.raises(app.WorkflowError): app.run_workflow('missing',{},resume_from_run_id='bad')

def test_handler_rejects_extra_background():
    with pytest.raises(app.WorkflowError): app._workflow_handler(name='x',args={},background=True)

def test_real_runner_isolated(monkeypatch):
    name='it_isolated'
    try:
        app.register_workflow(name,'test',[],'def run(state,args): return state.agent(args["p"])',{'type':'object','properties':{'p':{'type':'string'}}})
        class Msg: content='answer'
        class Resp: response=type('R',(),{'choices':[type('C',(),{'message':Msg()})()]})()
        seen={}; monkeypatch.setattr(app,'call_llm',lambda messages,tools=None,**kw:(seen.update(messages=messages,tools=tools) or Resp()))
        assert app.run_workflow(name,{'p':'secret'})['result']=='answer' and seen['tools'] is None
    finally: clean(name)

def test_execute_function_rejects_extra_workflow_field():
    tool = app.ToolCall('id', 'workflow', {'name':'x','args':{},'background':True})
    result = app.execute_function(tool, {'workflow': app._workflow_handler}, [])
    assert 'only name, args, resume_from_run_id' in result

def test_resume_args_mismatch_rejected():
    name='it_mismatch'
    try:
        app.register_workflow(name,'test',[],'def run(state,args): return args["x"]',{'type':'object','properties':{'x':{'type':'integer'}}})
        first=app.run_workflow(name,{'x':1})
        with pytest.raises(app.WorkflowError): app.run_workflow(name,{'x':2},resume_from_run_id=first['run_id'])
    finally: clean(name)
