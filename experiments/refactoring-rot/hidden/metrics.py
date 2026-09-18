"""Objective structural metrics on a checkout.py snapshot — a rubric-free rot proxy.
Usage: python3 metrics.py <path-to-checkout.py>
Reports code size, branchiness, and how scattered the discount/rounding rules are."""
import sys, ast, pathlib, re

path = pathlib.Path(sys.argv[1])
src = path.read_text()
tree = ast.parse(src)

sloc = sum(1 for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#"))

defs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
def _len(n):
    return (max(getattr(x, "lineno", n.lineno) for x in ast.walk(n)) - n.lineno + 1)
max_def = max((_len(d) for d in defs), default=0)

branches = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.If, ast.IfExp)))
# kind-dispatch sites: comparisons/among against the discount-kind string literals
kind_sites = len(re.findall(r'["\'](pct|amt)["\']', src))
round_calls = len(re.findall(r'_round_half_even|round_half_even|ROUND_HALF', src))
# "final price" computation sites: places that subtract a discount (a one-owner proxy)
discount_math = len(re.findall(r'subtotal\s*[-*]|[-*]\s*discount|reduction|allocate', src))
classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))

print(f"{path.parent.name}/{path.name}")
print(f"  sloc={sloc}  defs={len(defs)}  max_def_len={max_def}  classes={classes}")
print(f"  if_branches={branches}  kind_dispatch_sites={kind_sites}  round_sites={round_calls}  discount_math_sites={discount_math}")
