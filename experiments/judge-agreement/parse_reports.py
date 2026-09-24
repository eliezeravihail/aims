"""Extract per-chapter (row) scores for every filled form in the judge reports.

A report holds four forms: X-stage-1, Y-stage-1, X-stage-2, Y-stage-2. A form is either a full table
(one row per chapter, with a Score column) or, for some stage-2 forms, a short table of changed rows plus a
prose line "Rows a, b, c ... are unchanged at 10". Both shapes are read. Anything not found is left missing.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent / "principles-polish-vs-openspec"

RATERS = {  # rater id -> (report path template, mapping path)
    "R1":      ("judging-real/{p}/report.md",                  "judging-real/{p}/MAPPING-SECRET.md"),
    "R2-own":  ("judging-aims-real/{p}/ownership/report.md",   "judging-aims-real/{p}/MAPPING-SECRET.md"),
    "R2-simp": ("judging-aims-real/{p}/simplicity/report.md",  "judging-aims-real/{p}/MAPPING-SECRET.md"),
}
PRODUCTS = ["feed-ranking", "booking-availability", "entitlements"]
SECTION = re.compile(r"^(?:#+\s*|\*\*)(X|Y)-(?:stage-)?([12])\b", re.M)

def mapping(path):
    m = dict(re.findall(r"^(X|Y) = (\S+)", path.read_text(), re.M))
    return m

def parse_form(text):
    rows = {}
    # full or partial tables: find header, locate score column
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and re.search(r"\|\s*[§#]\s*\|", ln) and re.search(r"score", ln, re.I):
            hdr = [c.strip().lower() for c in ln.strip().strip("|").split("|")]
            si = next(k for k, c in enumerate(hdr) if c.startswith("score"))
            vi = next((k for k, c in enumerate(hdr) if c.startswith("sev")), None)
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                m = re.match(r"^(\d+)(?:\s*[–-]\s*(\d+))?$", cells[0])
                if m and len(cells) > si:
                    val = re.sub(r"[*\s]", "", cells[si])
                    if re.fullmatch(r"\d+(\.\d+)?", val):
                        sev = None
                        if vi is not None and len(cells) > vi:
                            s = re.search(r"S([1-4])", cells[vi])
                            sev = int(s.group(1)) if s else 0
                        rows[int(m.group(1))] = (float(val), sev)
                j += 1
            i = j
            continue
        i += 1
    # prose: "Rows 1, 3, 4 ... are unchanged at 10" / "unchanged at 10: rows ..."
    for m in re.finditer(r"[Rr]ows? ([\d ,and§]+?) (?:are |is |stay |remain )?unchanged at 10", text):
        for n in re.findall(r"\d+", m.group(1)):
            rows.setdefault(int(n), (10.0, 0))
    return rows

def main():
    out = []
    for p in PRODUCTS:
        for r, (rep, mp) in RATERS.items():
            text = (PP / rep.format(p=p)).read_text()
            mapp = mapping(PP / mp.format(p=p))
            heads = list(SECTION.finditer(text))
            for k, h in enumerate(heads):
                lab, st = h.group(1), int(h.group(2))
                end = heads[k + 1].start() if k + 1 < len(heads) else len(text)
                body = text[h.start():end]
                # stop at the next top-level part (D2 survival / traps) to avoid bleeding
                body = re.split(r"\n## ", body)[0]
                rows = parse_form(body)
                if rows:
                    out.append({"product": p, "rater": r, "label": lab, "stage": st,
                                "arm": mapp[lab], "rows": {str(k): v for k, v in sorted(rows.items())}})
    json.dump(out, sys.stdout, indent=1)

if __name__ == "__main__":
    main()
