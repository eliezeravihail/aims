import importlib.util, os, pytest
def load(p):
    s=importlib.util.spec_from_file_location("lg",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
lg=load(os.environ.get("INV_PATH","ledger.py"))
def test_empty(): assert lg.Ledger().balance("a")==0
def test_sum():
    l=lg.Ledger(); l.post("a",100); l.post("a",-30); assert l.balance("a")==70
def test_ids_unique():
    l=lg.Ledger(); ids={l.post("a",1) for _ in range(5)}; assert len(ids)==5 and all(isinstance(i,str) for i in ids)
def test_accounts_independent():
    l=lg.Ledger(); l.post("a",100); l.post("b",50); assert l.balance("a")==100 and l.balance("b")==50
def test_negative(): 
    l=lg.Ledger(); l.post("a",-100); assert l.balance("a")==-100
