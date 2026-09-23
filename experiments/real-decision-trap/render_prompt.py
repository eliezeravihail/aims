"""Render arm-prompt.md or record-prompt.md for one session. Usage: render_prompt.py <arm|record> <pt|rq> <A|B|C> <dir>"""
import pathlib, re, sys

kind, case, arm, d = sys.argv[1:5]
here = pathlib.Path(__file__).parent
src = (here / ("arm-prompt.md" if kind == "arm" else "record-prompt.md")).read_text().split("\n---\n", 1)[1].strip("\n")
keep, drop = ("PT", "RQ") if case == "pt" else ("RQ", "PT")
src = re.sub(r"\{" + drop + r":.*?\}", "", src, flags=re.S)
src = re.sub(r"\{" + keep + r": (.*?)\}", r"\1", src, flags=re.S)
lines = []
for l in src.split("\n"):
    if l.startswith("[A] ") or l == "[A]":
        if arm == "A": lines.append(l[4:])
        continue
    if l.startswith("[AIMS] ") or l == "[AIMS]":
        if arm in "AB": lines.append(l[7:])
        continue
    if arm in "AB":
        l = l.replace("[AIMS]", "").replace("[/AIMS]", "")
    else:
        l = re.sub(r"\[AIMS\].*?\[/AIMS\]", "", l)
    lines.append(l)
text = "\n".join(lines).replace("<DIR>", d)
card = (here / "cards" / ("pytorch.md" if case == "pt" else "requests.md")).read_text().strip()
text = text.replace("<<CARD>>", card)
text = text.replace("<DISCUSSION>", "/tmp/claude-0/rdt/discussions/" +
                    ("pytorch-sampler.md" if case == "pt" else "requests-session-timeout.md"))
print(re.sub(r"\n{3,}", "\n\n", text).strip())
