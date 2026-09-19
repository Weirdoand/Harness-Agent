import json
import threading
import time

import pytest

import llm_chat as app
MockAgentRunner, WorkflowError, WorkflowRuntime = app.MockAgentRunner, app.WorkflowError, app.WorkflowRuntime


def runtime(result=None):
    return WorkflowRuntime(agent_runner=MockAgentRunner(result))


def test_input_schema_is_enforced():
    rt = runtime()
    rt.register("x", "x", [], "def run(state, args): return args['n']", {"type": "object", "required": ["n"], "properties": {"n": {"type": "integer"}}})
    assert rt.run("x", {"n": 2})[0] == 2
    with pytest.raises(WorkflowError):
        rt.run("x", {})


def test_agent_output_json_schema():
    rt = runtime('{"ok": true}')
    rt.register("x", "x", [], "def run(state, args): return state.agent('p', schema={'type':'object','required':['ok']})")
    assert rt.run("x")[0] == {"ok": True}


def test_agent_options_phase_inheritance_and_redacted_journal():
    runner = MockAgentRunner("ok")
    rt = WorkflowRuntime(agent_runner=runner)
    rt.register("x", "x", ["build"], "def run(state, args): state.phase('build'); return state.agent('secret', label='worker')")
    _, state = rt.run("x")
    start = next(e for e in state.journal if e["event"] == "agent_start")
    assert start["phase"] == "build" and start["label"] == "worker" and "prompt" not in start
    assert start["call_id"]
    assert runner.calls[0]["phase"] == "build"


def test_parallel_is_concurrent_and_ordered():
    rt = runtime()
    rt.register("x", "x", [], "def run(state, args): return state.parallel([lambda: 1, lambda: 2])")
    assert rt.run("x")[0] == [1, 2]


def test_parallel_failure_waits_for_all_tasks():
    rt = runtime()
    rt.register("x", "x", [], "def run(state, args): return state.parallel([lambda: 1/0, lambda: state.log('finished')])")
    events = []
    with pytest.raises(WorkflowError):
        rt.run("x", reporter=events.append)
    assert any(event["event"] == "log" and event["message"] == "finished" for event in events)


def test_pipeline_does_not_wait_at_each_stage_and_preserves_order():
    events = []
    def run_agent(prompt, **options):
        if prompt == "slow":
            time.sleep(0.05)
        events.append(prompt)
        return prompt
    runner = MockAgentRunner(run_agent)
    rt = WorkflowRuntime(agent_runner=runner)
    rt.register("x", "x", [], "def run(state, args): return state.pipeline(args['items'], lambda x: state.agent(x), lambda x: (state.log(x), x)[1])")
    assert rt.run("x", {"items": ["slow", "fast"]})[0] == ["slow", "fast"]
    assert events == ["fast", "slow"]


def test_pipeline_reports_item_and_stage():
    rt = runtime()
    rt.register("x", "x", [], "def run(state, args): return state.pipeline([1], lambda x: 1/0)")
    with pytest.raises(WorkflowError, match="index.*stage"):
        rt.run("x")


def test_nested_workflow_one_level_and_unknown():
    rt = runtime()
    rt.register("child", "child", [], "def run(state, args): return 3")
    rt.register("parent", "parent", [], "def run(state, args): return state.workflow('child')")
    assert rt.run("parent")[0] == 3
    with pytest.raises(WorkflowError):
        rt.run("missing")


def test_nested_workflow_two_levels_rejected():
    rt = runtime()
    rt.register("a", "a", [], "def run(state, args): return state.workflow('b')")
    rt.register("b", "b", [], "def run(state, args): return state.workflow('c')")
    rt.register("c", "c", [], "def run(state, args): return 1")
    with pytest.raises(WorkflowError):
        rt.run("a")


@pytest.mark.parametrize("code", [
    "import os\ndef run(state, args): return 1",
    "def run(state, args):\n while True: break",
    "def run(state, args):\n return open('x')",
    "def run(state, args):\n return state.runner",
    "def run(state, args):\n state.x = 1",
    "def run(state, args):\n return print('x')",
])
def test_ast_rejects_unsafe_samples(code):
    with pytest.raises(WorkflowError):
        runtime().register("bad", "bad", [], code)


def test_metadata_schema_and_snapshot_deep_copy():
    schema = {"type": "object", "properties": {"x": {"type": "array", "items": {"type": "integer"}}}}
    definition = runtime().register("x", "desc", ["p"], "def run(state, args): return 1", schema)
    schema["properties"]["x"]["items"]["type"] = "string"
    assert definition.parameters["properties"]["x"]["items"]["type"] == "integer"
    with pytest.raises(WorkflowError):
        runtime().register("", "desc", [], "def run(state, args): return 1")


def test_reporter_receives_workflow_phase_events():
    events = []
    rt = runtime()
    rt.register("x", "x", ["p"], "def run(state, args): state.phase('p'); state.log('hello'); return 1")
    rt.run("x", reporter=events.append)
    assert events and all(e["workflow"] == "x" for e in events)



def test_nested_workflow_with_single_agent_slot_does_not_deadlock():
    import concurrent.futures
    runner = MockAgentRunner('ok')
    rt = WorkflowRuntime(agent_runner=runner, max_agent_concurrency=1)
    rt.register('child', 'child', [], "def run(state,args): return state.agent('child')")
    rt.register('parent', 'parent', [], "def run(state,args): return state.workflow('child')")
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(rt.run, 'parent')
        assert future.result(timeout=1)[0] == 'ok'
