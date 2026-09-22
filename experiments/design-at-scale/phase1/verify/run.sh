#!/bin/bash
# run.sh <design-label> <project-dir> <mkdocs args...> — uses the design tree's mkdocs, found via PYTHONPATH
L=$1; P=$2; shift 2
cd "$P" && PYTHONPATH=/tmp/claude-0/phase1/judge/design-$L /tmp/claude-0/phase0/pristine/.venv/bin/python -m mkdocs "$@"
