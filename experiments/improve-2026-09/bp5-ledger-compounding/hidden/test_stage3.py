import importlib.util, os
def load(p):
    s=importlib.util.spec_from_file_location("lg3",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
lg=load(os.environ.get("INV_PATH","ledger.py"))
def test_as_of():
    l=lg.Ledger(); l.post("a",100,"USD",at=0); l.post("a",50,"USD",at=5); l.post("a",25,"USD",at=10)
    assert l.balance("a","USD",as_of=0)==100
    assert l.balance("a","USD",as_of=5)==150
    assert l.balance("a","USD",as_of=9)==150
    assert l.balance("a","USD",as_of=10)==175
    assert l.balance("a","USD",as_of=None)==175
def test_as_of_default_all():
    l=lg.Ledger(); l.post("a",100,at=0); l.post("a",50,at=100); assert l.balance("a")==150
