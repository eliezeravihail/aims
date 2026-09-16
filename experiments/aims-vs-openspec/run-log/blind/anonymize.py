#!/usr/bin/env python3
"""Cut blind copies of the three stage-3 designs: X / Y / Z, in an order the judges are not told."""
import random, re, shutil, sys
from pathlib import Path

ARMS = {"arm-aims": "aims", "arm-openspec": "openspec", "arm-plain": "plain"}
OUT = Path("/tmp/exp/blind")

# Anything that names a method, a tool, or a run.
SCRUB = [
    (re.compile(r"\baims[-_ ]?guide\b", re.I), "the method"),
    (re.compile(r"\bopen[-_ ]?spec\b", re.I), "the method"),
    (re.compile(r"\bopsx\b", re.I), "the method"),
    (re.compile(r"\baims\b", re.I), "the method"),
    (re.compile(r"/tmp/exp/arm-[a-z]+/?", re.I), "<project>/"),
    (re.compile(r"\.aims/"), "<method-dir>/"),
    (re.compile(r"openspec/"), "<method-dir>/"),
    (re.compile(r"^\s*(companion|ADR|decision record|spec delta|proposal\.md|tasks\.md|design\.md)\b.*$",
                re.I | re.M), ""),
    (re.compile(r"\b20\d\d-\d\d-\d\d\b"), "<date>"),
    # Record-system tells. Each method names its own durable artefacts differently, and a judge that
    # spots `decisions/0011` or `companion` has identified the arm. Replace with a neutral phrase that
    # preserves the sentence's meaning (a prior recorded decision) without naming whose system wrote it.
    (re.compile(r"`?decisions?/\d{3,4}[-a-z0-9]*`?", re.I), "an earlier recorded decision"),
    (re.compile(r"\bADR[\s-]*\d{3,4}\b", re.I), "an earlier recorded decision"),
    (re.compile(r"\bADRs?\b"), "recorded decisions"),
    (re.compile(r"\bcompanions?\b", re.I), "a file note"),
    (re.compile(r"\bspec deltas?\b", re.I), "a spec change"),
    (re.compile(r"`?(proposal|tasks|design)\.md`?"), "the planning document"),
]

def scrub(text: str) -> str:
    for rx, rep in SCRUB:
        text = rx.sub(rep, text)
    return text

def main(stage: str, seed: int) -> None:
    labels = ["X", "Y", "Z"]
    arms = list(ARMS)
    random.Random(seed).shuffle(arms)
    mapping = []
    for label, arm in zip(labels, arms):
        src = Path("/tmp/exp") / arm / "design" / f"stage-{stage}.md"
        if not src.is_file():
            sys.exit(f"missing: {src}")
        dst = OUT / f"stage-{stage}" / f"design-{label}.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(scrub(src.read_text()))
        mapping.append(f"{label} = {ARMS[arm]}")
    (OUT / f"stage-{stage}" / "mapping-SECRET.md").write_text(
        "# Do not open until every reading is in\n\n" + "\n".join(mapping) + "\n")
    print(f"cut {len(labels)} blind copies for stage {stage}")
    # leak check
    bad = []
    for f in (OUT / f"stage-{stage}").glob("design-*.md"):
        for term in ("aims", "openspec", "opsx"):
            if re.search(rf"\b{term}\b", f.read_text(), re.I):
                bad.append(f"{f.name}: {term}")
    print("leak check:", bad or "clean")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "3", int(sys.argv[2]) if len(sys.argv) > 2 else 20260915)
