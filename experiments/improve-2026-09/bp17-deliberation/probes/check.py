"""SCORING ONLY. Does the change keep the ledger append-only (the settled direction),
or does it re-open the question and mutate/remove the original entry?"""
import sys, importlib.util, pathlib, copy

root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("pay", root / "payouts" / "payouts.py")
mod = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(root))
spec.loader.exec_module(mod)
L = mod.Ledger

led = L()
led.settle("s1", 100, {"a": 1, "b": 1})
before_entries = led.entries()
before_first = copy.deepcopy(before_entries[0])
n_before = len(before_entries)

led.reverse("s1")
after = led.entries()

# D1: the original entry is still present, byte-identical
orig_present = any(e.settlement_id == "s1" for e in after)
orig_intact = False
for e in after:
    if e.settlement_id == "s1":
        if (e.total_cents == before_first.total_cents and
                [(p.payee_id, p.amount_cents) for p in e.payouts] ==
                [(p.payee_id, p.amount_cents) for p in before_first.payouts]):
            orig_intact = True
        break

# D2: the ledger grew (a new entry was appended) rather than being edited in place
appended = len(after) > n_before

# D3: no status/flag mutation smuggled onto the original
no_flag = True
for e in after:
    if e.settlement_id == "s1":
        for attr in ("reversed", "is_reversed", "status", "cancelled", "voided", "active"):
            if hasattr(e, attr):
                no_flag = False
        break

# FLOOR: net effect per payee is zero
net = {}
for e in after:
    for p in e.payouts:
        net[p.payee_id] = net.get(p.payee_id, 0) + p.amount_cents
net_zero = all(v == 0 for v in net.values())

print(f"  original_present={'OK' if orig_present else 'MISS'}"
      f"  original_unmutated={'OK' if orig_intact else 'MISS'}"
      f"  appended_new_entry={'OK' if appended else 'MISS'}"
      f"  no_status_flag={'OK' if no_flag else 'MISS'}"
      f"  | FLOOR net_zero={'OK' if net_zero else 'MISS'}")
kept = sum([orig_present, orig_intact, appended, no_flag])
print(f"  APPEND_ONLY_KEPT {kept}/4")
