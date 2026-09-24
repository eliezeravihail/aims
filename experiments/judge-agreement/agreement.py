"""Inter-judge agreement on the principles-polish-vs-openspec design grades. Stdlib only.

Input: every filled assessment form in the round-1 (judging-real) and round-2 (judging-aims-real) judge
reports, parsed by parse_reports.py. A "unit" is one design: (product, stage, arm). Only units scored by two
or more judges enter an agreement statistic: the six openspec-real designs (three judges: R1, R2-own, R2-simp)
and the six aims-real designs (two judges: R2-own, R2-simp). The aims-single designs were scored by one judge
on this instrument and are excluded.

Run: python3 agreement.py   (writes results.json next to this file and prints a summary)
"""
import itertools, json, math, random, statistics as st
from collections import defaultdict
from pathlib import Path

import parse_reports

HERE = Path(__file__).resolve().parent
W = {0: 1, 1: 1, 2: 2, 3: 4, 4: 8}          # severity -> weight (measurement.md)
SEED, BOOT = 20260924, 5000


# ---------------------------------------------------------------- data
def load_forms():
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        parse_reports.main()
    forms = json.loads(buf.getvalue())
    for f in forms:
        rows = {int(k): tuple(v) for k, v in f["rows"].items()}
        f["rows"] = rows
        num = sum(s * W[v] for s, v in rows.values()); den = sum(W[v] for s, v in rows.values())
        f["grade"] = round(num / den, 2)
        f["gate"] = "BLOCKED" if any(v == 4 for s, v in rows.values()) else "CLEAR"
        f["unit"] = (f["product"], f["stage"], f["arm"])
    return forms

# Reopened + discarded counts, stage 1 -> 2, per design and judge (from the judges' reports, as tabulated in
# results-openspec-real.md and results-aims-real.md).
SURVIVAL = {
    ("feed-ranking", "openspec-real"):         {"R1": 3, "R2-own": 3, "R2-simp": 2},
    ("booking-availability", "openspec-real"): {"R1": 1, "R2-own": 1, "R2-simp": 1},
    ("entitlements", "openspec-real"):         {"R1": 3, "R2-own": 2, "R2-simp": 3},
    ("feed-ranking", "aims-real"):             {"R2-own": 4, "R2-simp": 2},
    ("booking-availability", "aims-real"):     {"R2-own": 3, "R2-simp": 4},
    ("entitlements", "aims-real"):             {"R2-own": 4, "R2-simp": 4},
}
# Round-2 verdicts (aims-real vs openspec-real), per product, as each judge named them.
VERDICTS = {
    ("feed-ranking", "D1"):          ("aims", "aims"),
    ("feed-ranking", "survival"):    ("openspec", "none"),
    ("feed-ranking", "D2 form"):     ("aims", "aims"),
    ("booking-availability", "D1"):       ("aims", "none"),
    ("booking-availability", "survival"): ("openspec", "openspec"),
    ("booking-availability", "D2 form"):  ("aims", "openspec"),
    ("entitlements", "D1"):          ("aims", "none"),
    ("entitlements", "survival"):    ("openspec", "openspec"),
    ("entitlements", "D2 form"):     ("aims", "aims"),
}


# ---------------------------------------------------------------- statistics
def kripp_alpha(units, metric="interval"):
    """Krippendorff's alpha. units: list of lists of values (missing values simply absent)."""
    units = [u for u in units if len(u) >= 2]
    vals = [v for u in units for v in u]
    n = len(vals)
    if n < 2:
        return None
    d = (lambda a, b: (a - b) ** 2) if metric == "interval" else (lambda a, b: 0.0 if a == b else 1.0)
    do = sum(sum(d(a, b) for a, b in itertools.permutations(u, 2)) / (len(u) - 1) for u in units) / n
    de = sum(d(a, b) for a, b in itertools.permutations(vals, 2)) / (n * (n - 1))
    return None if de == 0 else 1 - do / de

def icc(matrix):
    """Shrout & Fleiss ICC(2,1) absolute agreement and ICC(3,1) consistency; complete n x k matrix."""
    n, k = len(matrix), len(matrix[0])
    g = st.mean(v for r in matrix for v in r)
    rm = [st.mean(r) for r in matrix]; cm = [st.mean(c) for c in zip(*matrix)]
    ssr = k * sum((m - g) ** 2 for m in rm); ssc = n * sum((m - g) ** 2 for m in cm)
    sst = sum((v - g) ** 2 for r in matrix for v in r); sse = sst - ssr - ssc
    msr, msc, mse = ssr / (n - 1), ssc / (k - 1), sse / ((n - 1) * (k - 1))
    icc21 = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    icc31 = (msr - mse) / (msr + (k - 1) * mse)
    # variance components (two-way random, one observation per cell), negatives clipped to 0
    var_design = max((msr - mse) / k, 0.0); var_rater = max((msc - mse) / n, 0.0); var_res = mse
    tot = var_design + var_rater + var_res
    return {"ICC(2,1)": icc21, "ICC(3,1)": icc31,
            "variance share: design": var_design / tot, "variance share: judge": var_rater / tot,
            "variance share: residual (judge x design)": var_res / tot}

def cohen_kappa(a, b):
    cats = sorted(set(a) | set(b)); n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return None if pe == 1 else (po - pe) / (1 - pe)

def boot_ci(unit_keys, stat, reps=BOOT, seed=SEED):
    rnd = random.Random(seed); out = []
    for _ in range(reps):
        sample = [rnd.choice(unit_keys) for _ in unit_keys]
        v = stat(sample)
        if v is not None and not math.isnan(v):
            out.append(v)
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]) if out else (None, None)

r = lambda x: None if x is None else round(x, 3)


# ---------------------------------------------------------------- analysis
def main():
    forms = load_forms()
    by_unit = defaultdict(dict)
    for f in forms:
        by_unit[f["unit"]][f["rater"]] = f
    multi = {u: d for u, d in by_unit.items() if len(d) >= 2}
    os_units = sorted(u for u in multi if u[2] == "openspec-real")
    ai_units = sorted(u for u in multi if u[2] == "aims-real")
    all_units = os_units + ai_units
    res = {"units_scored_by_2+_judges": len(all_units), "forms_parsed": len(forms)}

    # 1. grade agreement
    def grade_alpha(keys):
        return kripp_alpha([[f["grade"] for f in multi[u].values()] for u in keys])
    res["grades"] = {}
    for name, keys in [("openspec-real, 3 judges", os_units), ("aims-real, 2 judges", ai_units),
                       ("all 12 designs", all_units)]:
        a = grade_alpha(keys)
        res["grades"][name] = {"alpha_interval": r(a), "alpha_95ci": tuple(map(r, boot_ci(keys, grade_alpha)))}
    res["grades"]["openspec-real, 3 judges"].update(
        {k: r(v) for k, v in icc([[multi[u][j]["grade"] for j in ("R1", "R2-own", "R2-simp")] for u in os_units]).items()})
    res["grades"]["all 12 designs"].update(
        {("round-2 pair " + k): r(v) for k, v in icc([[multi[u][j]["grade"] for j in ("R2-own", "R2-simp")] for u in all_units]).items()})
    ranges = {"/".join(map(str, u)): [multi[u][j]["grade"] for j in sorted(multi[u])] for u in all_units}
    spreads = [max(v) - min(v) for v in ranges.values()]
    res["grades"]["per_design"] = ranges
    res["grades"]["spread (max-min) per design"] = {"mean": r(st.mean(spreads)), "max": r(max(spreads)),
                                                     "designs with spread >= 2 points": sum(s >= 2 for s in spreads)}

    # 1b. sensitivity: the same grades recomputed without chapter 13 (functional correctness, where an S4 weighs x8)
    def grade_wo13(f):
        rows = [v for c, v in f["rows"].items() if c != 13]
        return sum(s * W[v] for s, v in rows) / sum(W[v] for s, v in rows)
    def alpha_wo13(keys):
        return kripp_alpha([[grade_wo13(f) for f in multi[u].values()] for u in keys])
    res["grades_without_chapter_13"] = {
        name: {"alpha_interval": r(alpha_wo13(keys)), "alpha_95ci": tuple(map(r, boot_ci(keys, alpha_wo13)))}
        for name, keys in [("openspec-real, 3 judges", os_units), ("all 12 designs", all_units)]}
    res["grades_without_chapter_13"]["openspec-real, 3 judges"].update(
        {k: r(v) for k, v in icc([[grade_wo13(multi[u][j]) for j in ("R1", "R2-own", "R2-simp")] for u in os_units]).items()})
    res["s4_found_in_chapter_13"] = {j: [ "/".join(map(str, u)) for u in all_units
                                          if j in multi[u] and multi[u][j]["rows"].get(13, (0, 0))[1] == 4]
                                     for j in ("R1", "R2-own", "R2-simp")}

    # 2. gate agreement
    ga = [multi[u]["R2-own"]["gate"] for u in all_units]; gb = [multi[u]["R2-simp"]["gate"] for u in all_units]
    res["gate"] = {"round-2 pair: agreement": f"{sum(x == y for x, y in zip(ga, gb))}/{len(ga)}",
                   "round-2 pair: Cohen kappa": r(cohen_kappa(ga, gb)),
                   "all judges: alpha_nominal": r(kripp_alpha([[f["gate"] for f in multi[u].values()] for u in all_units], "nominal")),
                   "designs BLOCKED by some judge and CLEAR by another": sum(len({f["gate"] for f in multi[u].values()}) > 1 for u in all_units)}

    # 3. does each round-2 judge order the two arms the same way (per product x stage)?
    order = []
    for p in parse_reports.PRODUCTS:
        for s in (1, 2):
            a, o = multi[(p, s, "aims-real")], multi[(p, s, "openspec-real")]
            d_own = a["R2-own"]["grade"] - o["R2-own"]["grade"]; d_simp = a["R2-simp"]["grade"] - o["R2-simp"]["grade"]
            order.append({"product": p, "stage": s, "aims-minus-openspec (own)": round(d_own, 2),
                          "aims-minus-openspec (simp)": round(d_simp, 2),
                          "same sign": (d_own > 0) == (d_simp > 0) if d_own and d_simp else False})
    res["arm_order"] = {"pairs": order, "same sign": f"{sum(o['same sign'] for o in order)}/{len(order)}",
                        "alpha_interval on arm difference": r(kripp_alpha([[o['aims-minus-openspec (own)'], o['aims-minus-openspec (simp)']] for o in order]))}

    # 4. verdicts and survival counts
    agree = sum(a == b for a, b in VERDICTS.values())
    res["verdicts_round2"] = {"agree": f"{agree}/{len(VERDICTS)}",
                              "alpha_nominal": r(kripp_alpha([list(v) for v in VERDICTS.values()], "nominal"))}
    res["survival_counts"] = {"alpha_interval": r(kripp_alpha([list(v.values()) for v in SURVIVAL.values()])),
                              "per_design": {f"{p}/{a}": v for (p, a), v in SURVIVAL.items()}}

    # 5. chapter-level agreement (chapters 1-14)
    def chapter_items(keys, chapters=range(1, 15), fn=lambda s, v: s):
        items = []
        for u in keys:
            for c in chapters:
                vals = [fn(*f["rows"][c]) for f in multi[u].values() if c in f["rows"]]
                if len(vals) >= 2:
                    items.append(vals)
        return items
    res["chapters"] = {
        "items (design x chapter) with 2+ judges": len(chapter_items(all_units)),
        "score: alpha_interval": r(kripp_alpha(chapter_items(all_units))),
        "score: alpha_95ci (resampling designs)": tuple(map(r, boot_ci(all_units, lambda k: kripp_alpha(chapter_items(k))))),
        "pass/fail (score 10 vs <10): alpha_nominal": r(kripp_alpha(chapter_items(all_units, fn=lambda s, v: s < 10), "nominal")),
        "S4 in chapter: alpha_nominal": r(kripp_alpha(chapter_items(all_units, fn=lambda s, v: v == 4), "nominal")),
        "per chapter: alpha_interval": {c: r(kripp_alpha(chapter_items(all_units, chapters=[c]))) for c in range(1, 15)},
    }
    fails = chapter_items(all_units, fn=lambda s, v: s < 10)
    res["chapters"]["items where every judge agrees on pass/fail"] = f"{sum(len(set(i)) == 1 for i in fails)}/{len(fails)}"

    # 6. design only: every reading above, without chapter 13 (functional correctness)
    design_ch = [c for c in range(1, 15) if c != 13]
    r2 = [u for u in all_units if "R2-own" in multi[u] and "R2-simp" in multi[u]]
    pf2 = [[multi[u][j]["rows"][c][0] < 10 for j in ("R2-own", "R2-simp")] for u in r2 for c in design_ch]
    res["design_only"] = {
        "grade (chapters 1-14 minus 13), all judges: alpha_interval": r(alpha_wo13(all_units)),
        "chapter score, all judges: alpha_interval": r(kripp_alpha(chapter_items(all_units, chapters=design_ch))),
        "chapter pass/fail, all judges: alpha_nominal": r(kripp_alpha(chapter_items(all_units, chapters=design_ch, fn=lambda s, v: s < 10), "nominal")),
        "round-2 pair: chapter score alpha_interval": r(kripp_alpha([[multi[u][j]["rows"][c][0] for j in ("R2-own", "R2-simp")] for u in r2 for c in design_ch])),
        "round-2 pair: chapter pass/fail alpha_nominal": r(kripp_alpha(pf2, "nominal")),
        "round-2 pair: chapters flagged failed by both / by either": f"{sum(x and y for x, y in pf2)}/{sum(x or y for x, y in pf2)}",
    }

    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "survival_counts"}, indent=1, default=str))


if __name__ == "__main__":
    main()
