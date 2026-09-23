"""Print test_dataloader.py without `test_sampler_reproducibility` — the withheld grader (the one test that
encodes the re-seeding decision; see DESIGN.md). Usage: python3 strip_test.py <test_dataloader.py>"""
import sys

lines = open(sys.argv[1]).read().split("\n")
start = next(i for i, l in enumerate(lines) if l.strip().startswith("def test_sampler_reproducibility("))
indent = len(lines[start]) - len(lines[start].lstrip())
end = next(i for i in range(start + 1, len(lines))
           if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) <= indent)
print("\n".join(lines[:start] + lines[end:]), end="")
