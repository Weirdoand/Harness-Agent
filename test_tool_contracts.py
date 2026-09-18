import os
os.environ.setdefault("LLM_API_KEY", "dummy")
os.environ.setdefault("LLM_BASE_URL", "http://127.0.0.1")
import llm_chat as app

def names(items):
    return {x["function"]["name"] for x in items}

def test_lead_contract_names():
    app.refresh_tool_pool()
    n=names(app.TOOLS)
    assert len(n) == 26
    assert {"request_plan","review_plan"} <= n
    assert not ({"submit_plan","approve_plan","reject_plan","allocate_worktree","run_bash","glob_bash"} & n)

def test_oneoff_contract_names():
    allowed={"bash","read_file","write_file","edit_file","glob"}
    assert {x["function"]["name"] for x in app.SUB_TOOLS} == allowed

def test_team_contract_names():
    n=names(app.TEAM_TOOLS)
    assert "submit_plan" in n
    assert "request_plan" not in n and "review_plan" not in n
    assert "manage_task" not in n

def test_bind_worktree_requires_pending_unowned(tmp_path):
    tm=app.ContractTaskManager(str(tmp_path))
    tid=tm.create_task("x", "x")
    assert tm.bind_worktree(tid, str(tmp_path/"w"))
    assert tm.claim_task(tid, "a")["success"]
    assert not tm.bind_worktree(tid, str(tmp_path/"other"))
