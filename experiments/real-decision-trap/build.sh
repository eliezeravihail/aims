#!/usr/bin/env bash
# Build one arm's checkout. Usage: build.sh <pt|rq> <dir> [aims]
#   pt — PyTorch's torch.utils.data at the installed wheel's version (2.14.0), with the upstream
#        test file minus test_sampler_reproducibility (withheld: it is the grader) and docs/source/data.md.
#   rq — requests at 611c6162 without git history, .github/, and the feature-freeze paragraph.
#   aims — also install aims' per-project layer (.aims/anchor.py, .aims/staleness_hook.py).
# Every checkout is a fresh git repo with one commit, "Initial checkout". No upstream history.
set -euo pipefail
RDT=/tmp/claude-0/rdt
case_=$1; dir=$2; withaims=${3:-}
rm -rf "$dir"; mkdir -p "$dir"
if [ "$case_" = pt ]; then
  SP=$RDT/venv-torch/lib/python3.11/site-packages
  mkdir -p "$dir/torch/utils" "$dir/test" "$dir/docs/source"
  cp -a "$SP/torch/utils/data" "$dir/torch/utils/data"
  find "$dir/torch" -name __pycache__ -prune -exec rm -rf {} +
  python3 "$(dirname "$0")/strip_test.py" "$RDT/up/test_dataloader.py" > "$dir/test/test_dataloader.py"
  cp "$RDT/up/data.md" "$dir/docs/source/data.md"
  printf '%s\n' "# torch.utils.data" "" \
    "PyTorch's data-loading package (\`torch/utils/data/\`), its tests (\`test/test_dataloader.py\`) and its" \
    "documentation page (\`docs/source/data.md\`), at PyTorch 2.14.0." "" \
    "The rest of PyTorch is installed in \`.venv\`; its \`torch/utils/data\` is this checkout's, so an edit here is" \
    "what \`import torch\` runs." > "$dir/README.md"
  python3 -m venv "$dir/.venv"
  VSP="$dir/.venv/lib/python3.11/site-packages"
  for e in "$SP"/*; do
    b=$(basename "$e")
    case "$b" in torch|pip|pip-*|_distutils_hack|distutils-precedence.pth|setuptools*) continue;; esac
    [ -e "$VSP/$b" ] || cp -al "$e" "$VSP/$b"
  done
  mkdir -p "$VSP/torch"
  for e in "$SP/torch"/*; do
    b=$(basename "$e")
    if [ "$b" = lib ]; then cp -al "$e" "$VSP/torch/lib"; else cp -a "$e" "$VSP/torch/$b"; fi
  done
  rm -rf "$VSP/torch/utils/data"
  ln -s "$(cd "$dir" && pwd)/torch/utils/data" "$VSP/torch/utils/data"
elif [ "$case_" = rq ]; then
  git -C "$RDT/requests-up" archive 611c6162 | tar -x -C "$dir"
  rm -rf "$dir/.github"
  python3 - "$dir/docs/dev/contributing.rst" <<'PY'
import sys, re
p = sys.argv[1]; t = open(p).read()
start = t.index("Requests is in a perpetual feature freeze")
end = t.index("\n\n", start)
open(p, "w").write(t[:start] + t[end + 2:])
PY
  python3 -m venv "$dir/.venv"
  (cd "$dir" && .venv/bin/pip install -q --no-input -r requirements-dev.txt 2>&1 | grep -v -i notice || true)
else
  echo "unknown case $case_" >&2; exit 2
fi
if [ "$withaims" = aims ]; then
  mkdir -p "$dir/.aims"
  cp "$RDT/aims/knowledge/anchor.py" "$RDT/aims/knowledge/staleness_hook.py" "$dir/.aims/"
fi
printf '.venv/\n__pycache__/\n*.egg-info/\n.pytest_cache/\n' >> "$dir/.gitignore"
git -C "$dir" init -q
git -C "$dir" add -A
git -C "$dir" -c user.name=dev -c user.email=dev@example.com commit -q -m "Initial checkout"
echo "built $case_ $dir"
