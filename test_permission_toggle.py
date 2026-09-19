import llm_chat as app

def test_toggle_and_snapshot():
    old=app.PERMISSION_POLICY.snapshot(); app.PERMISSION_POLICY.set_for_test(False)
    assert app.PERMISSION_POLICY.toggle() is True
    assert app.PERMISSION_POLICY.snapshot() is True
    app.PERMISSION_POLICY.set_for_test(old)

def test_keyed_shift_tab_preserves_buffer():
    app.PERMISSION_POLICY.set_for_test(False); keys=iter(['a','b','\x00','\x0f','c','\r'])
    assert app._readline_keyed('',lambda:next(keys),output_fn=lambda *a,**k:None)=="abc"
    assert app.PERMISSION_POLICY.snapshot(); app.PERMISSION_POLICY.toggle()

def test_keyed_escape_shift_tab_and_plain_tab():
    app.PERMISSION_POLICY.set_for_test(False); keys=iter(['\x1b','[','Z','x','\r'])
    assert app._readline_keyed('',lambda:next(keys),output_fn=lambda *a,**k:None)=="x"; assert app.PERMISSION_POLICY.snapshot(); app.PERMISSION_POLICY.toggle()
    keys=iter(['\t','\r']); assert app._readline_keyed('',lambda:next(keys),output_fn=lambda *a,**k:None)==""; assert not app.PERMISSION_POLICY.snapshot()

def test_keyed_permission_immediate_allow():
    app.PERMISSION_POLICY.set_for_test(False); keys=iter(['\xe0','\x0f'])
    assert app._readline_keyed('',lambda:next(keys),finish_on_auto_allow=True,output_fn=lambda *a,**k:None) is app.AUTO_ALLOW_SENTINEL
    app.PERMISSION_POLICY.toggle()

def test_policy_auto_allow_sentinel():
    old=app.PERMISSION_POLICY.snapshot(); app.PERMISSION_POLICY.set_for_test(True)
    assert app._confirm_or_auto_allow("x") is app.AUTO_ALLOW_SENTINEL
    app.PERMISSION_POLICY.set_for_test(old)

def test_fallback_toggle_command():
    old=app.PERMISSION_POLICY.snapshot(); app.PERMISSION_POLICY.set_for_test(False)
    assert app.PERMISSION_POLICY.toggle() is True
    app.PERMISSION_POLICY.set_for_test(old)
