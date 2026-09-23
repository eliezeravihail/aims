import importlib.util, os
def load(p):
    s=importlib.util.spec_from_file_location("lg4",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
lg=load(os.environ.get("INV_PATH","ledger.py"))
def test_void_removes_effect():
    l=lg.Ledger(); a=l.post("x",100,"USD"); l.post("x",30,"USD")
    assert l.balance("x","USD")==130
    l.void(a); assert l.balance("x","USD")==30
def test_void_idempotent_and_unknown():
    l=lg.Ledger(); a=l.post("x",100); l.void(a); l.void(a); l.void("nope"); assert l.balance("x")==0
def test_void_respects_as_of():
    l=lg.Ledger(); a=l.post("x",100,"USD",at=5); l.post("x",10,"USD",at=1)
    l.void(a); assert l.balance("x","USD",as_of=10)==10 and l.balance("x","USD",as_of=0)==0
