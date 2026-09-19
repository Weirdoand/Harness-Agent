import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import llm_chat as app

def main():
    old = app.WORKFLOW_RUNTIME_DIR
    root = Path(tempfile.mkdtemp())
    child = 'demo_child_' + root.name.replace('-', '_')
    name = 'demo_workflow_' + root.name.replace('-', '_')
    class Runner:
        def __call__(self, prompt, **opts):
            return app.WorkflowAgentResult('demo answer', {'total_tokens': 7})
    def sink(ev):
        if ev['type'] == 'task_started': print('task_started')
        elif ev['type'] == 'task_progress': print('task_progress', ev.get('progress_type'))
        elif ev['type'] == 'task_notification': print('task_notification')
    try:
        app.WORKFLOW_RUNTIME_DIR = root
        app.register_workflow(child, 'child', [], 'def run(state,args): return 1')
        app.register_workflow(name, 'demo', ['run'], 'def run(state,args): state.phase("run"); return state.agent("demo")')
        result = app.run_workflow(name, {}, runner=Runner(), event_sink=sink)
        status = {k: result.get(k) for k in ('status','output_file','agent_count','token_count')}
        print(status)
        return status
    finally:
        app.WORKFLOWS.registry.pop(child, None)
        app.WORKFLOWS.registry.pop(name, None)
        app.WORKFLOW_RUNTIME_DIR = old

if __name__ == '__main__':
    main()
