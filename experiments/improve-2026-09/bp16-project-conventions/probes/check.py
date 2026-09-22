"""SCORING ONLY - never given to any arm. Checks compliance with the three house conventions,
none of which is derivable from payouts.py itself."""
import sys, re, importlib.util, pathlib

root = pathlib.Path(sys.argv[1])
pay = (root / "payouts" / "payouts.py").read_text()
reg = (root / "common" / "registry.py").read_text()

results = {}

# K1 - rate math goes through common.money.bps_of, never inlined
uses_helper = ("bps_of" in pay) and re.search(r"from\s+common\.money\s+import|import\s+common\.money", pay)
inlined = re.search(r"//\s*10_?000", pay)
results["K1_uses_house_bps_helper"] = bool(uses_helper) and not bool(inlined)

# K2 - the new public operation is registered
results["K2_registered_new_operation"] = "settle_preview" in reg

# K3 (+ floor) - functional: the fee row must equal bps_of exactly, never absorb a remainder cent
spec = importlib.util.spec_from_file_location("payouts_mod", root / "payouts" / "payouts.py")
mod = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(root))
try:
    spec.loader.exec_module(mod)
    S = mod.Settlements
    ok_k3, ok_sum, ok_zero, ok_prev = True, True, True, True
    cases = [(1000, {"a": 1, "b": 1, "c": 1}, 2500), (7, {"a": 1, "b": 1}, 3333),
             (12345, {"x": 7, "y": 11, "z": 3}, 150), (101, {"a": 2, "b": 1}, 999)]
    for total, shares, bps in cases:
        rows = S().settle("t", total, shares, platform_fee_bps=bps)
        d = {p.payee_id: p.amount_cents for p in rows}
        expected_fee = total * bps // 10000
        if d.get("platform", 0) != expected_fee:
            ok_k3 = False
        if sum(p.amount_cents for p in rows) != total:
            ok_sum = False
        if "platform" in shares:
            ok_k3 = False
    if [p.payee_id for p in S().settle("z", 100, {"a": 1}, platform_fee_bps=0)] != ["a"]:
        ok_zero = False
    inst = S()
    try:
        fn = getattr(mod, "settle_preview", None) or getattr(S, "settle_preview")
        try:
            fn(100, {"a": 1}, 100)
        except TypeError:
            fn(inst, 100, {"a": 1}, 100)
        ok_prev = len(getattr(inst, "_done", {})) == 0
    except Exception:
        ok_prev = False
    results["K3_fee_exact_not_synthetic_weight"] = ok_k3
    results["FLOOR_sum_exact"] = ok_sum
    results["FLOOR_zero_bps_no_row"] = ok_zero
    results["FLOOR_preview_records_nothing"] = ok_prev
except Exception as e:
    for k in ["K3_fee_exact_not_synthetic_weight", "FLOOR_sum_exact",
              "FLOOR_zero_bps_no_row", "FLOOR_preview_records_nothing"]:
        results[k] = False
    print(f"  (load error: {str(e)[:100]})")

conv = [k for k in results if k.startswith("K")]
print("  " + "  ".join(f"{k.split('_')[0]}={'OK' if results[k] else 'MISS'}" for k in sorted(results)))
print(f"  CONVENTIONS {sum(results[k] for k in conv)}/{len(conv)}")
