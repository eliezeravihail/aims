import importlib.util, os
def load(p):
    s=importlib.util.spec_from_file_location("lg2",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
lg=load(os.environ.get("INV_PATH","ledger.py"))
def test_per_currency():
    l=lg.Ledger(); l.post("a",100,"USD"); l.post("a",200,"EUR"); l.post("a",-50,"USD")
    assert l.balance("a","USD")==50 and l.balance("a","EUR")==200
def test_default_usd():
    l=lg.Ledger(); l.post("a",100); assert l.balance("a")==100 and l.balance("a","USD")==100
def test_unknown_currency_zero():
    l=lg.Ledger(); l.post("a",100,"USD"); assert l.balance("a","JPY")==0
