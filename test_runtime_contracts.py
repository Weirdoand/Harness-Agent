import os, tempfile
os.environ.setdefault("LLM_API_KEY","dummy"); os.environ.setdefault("LLM_BASE_URL","http://127.0.0.1")
import llm_chat as app

def test_cron_durable_replay_ack_restore():
    with tempfile.TemporaryDirectory() as d:
        c=app.CronManager(d)
        jid=c.create_job("* * * * *","ping",False,True).split()[-1]
        c.enqueue_due(jid)
        assert c.consume_all_pending()
        c.restore(c.jobs[jid]); assert c.consume_all_pending()
        c.ack(c.jobs[jid]); assert jid not in c.jobs
        c2=app.CronManager(d); assert not c2.consume_all_pending()

def test_call_llm_429_and_fallback():
    class E(Exception):
        def __init__(self,s): self.status_code=s
    class C:
        def __init__(self): self.n=0
        class chat: pass
    c=C(); c.chat.completions=type("X",(),{})()
    def create(**kw):
        c.n+=1
        if c.n==1: raise E(429)
        return type("R",(),{"choices":[type("K",(),{"finish_reason":"stop","message":type("M",(),{"content":"ok","tool_calls":None})()})()]})()
    c.chat.completions.create=create
    r=app.call_llm([],client_override=c,sleep_fn=lambda _:None); assert r.response.choices[0].message.content=="ok"

def test_background_explicit_and_failure_state():
    assert "run_in_background" in app.run_bash.__code__.co_varnames
    b=app.BackgroundManager(); bid=b.submit_task("run_bash",app.run_bash,{"command":"exit 3","cwd":os.getcwd()})
    import time
    for _ in range(30):
        if b.get_status(bid)!="RUNNING": break
        time.sleep(.05)
    assert b.get_status(bid)=="FAILED"

def test_message_bus_has_messages_does_not_consume(tmp_path):
    b=app.MessageBus(str(tmp_path)); b.send({"to":"lead","content":"x"})
    assert b.has_messages("lead") and b.has_messages("lead")
    assert b.read_inbox("lead")[0]["content"]=="x" and not b.has_messages("lead")

def test_length_continuation_preserves_partial():
    class C:
        def __init__(self): self.calls=[]; self.chat=type("H",(),{})(); self.chat.completions=self
        def create(self, **kw):
            self.calls.append(kw["messages"])
            msg=type("M",(),{"content":"part" if len(self.calls)==1 else "done","tool_calls":None})()
            return type("R",(),{"choices":[type("K",(),{"finish_reason":"length" if len(self.calls)==1 else "stop","message":msg})()]})()
    c=C(); r=app.call_llm([],client_override=c,sleep_fn=lambda _:None)
    assert any(m.get("content")=="part" for m in c.calls[1])
    assert any("继续" in m.get("content","") for m in c.calls[1])
    assert r.partial_messages==[{"role":"assistant","content":"part"}]

def test_automatic_permission_never_prompts(monkeypatch):
    old=getattr(app.TURN_CONTEXT,"interactive",True); app.TURN_CONTEXT.interactive=False
    monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(AssertionError("prompted")))
    t=app.ToolCall("1","bash",{"command":"echo x"})
    ok,msg=app.hook_check_tool_permission(t)
    app.TURN_CONTEXT.interactive=old
    assert not ok
