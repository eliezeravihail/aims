#!/usr/bin/env bash
# Guards the *shipped* wiring: what a target project ends up running after /install-on.
#
# Every bug this file exists for was invisible from inside the aims repo, because here the tools really
# do live at knowledge/*.py — dogfooding masked the fact that an installed project has them at .aims/.
# So these checks read the shipped surfaces against the install table, not against this checkout.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
fail=0
bad(){ printf '  FAIL: %s\n' "$1" >&2; fail=$((fail + 1)); }

# 1. The settings template must wire the hook to where install-on actually puts it.
grep -q '"python3 .aims/staleness_hook.py"' templates/settings.json.tmpl \
  || bad "settings template does not wire the staleness hook to .aims/staleness_hook.py"
grep -q 'TARGET/.aims/staleness_hook.py' templates/commands/install-on.md \
  || bad "install-on no longer installs the staleness hook to .aims/ — the template is now wrong"

# 2. No shipped surface may tell a project to run the aims-repo source paths. install-on copies FROM
#    them, and design-record.md documents the one exception, so both are exempt.
while read -r hit; do
  case "$hit" in
    */install-on.md:*|*/design-record.md:*) continue ;;
    *) bad "shipped surface points at an aims-repo-only path: $hit" ;;
  esac
done < <(grep -rn "knowledge/anchor\.py\|knowledge/staleness_hook\.py" skills commands templates knowledge 2>/dev/null)

# 3. The dogfood wiring must point at files that exist in this checkout.
python3 - <<'PY' || fail=$((fail + 1))
import json, sys, re
from pathlib import Path
cfg = json.loads(Path(".claude/settings.json").read_text())
missing = []
for entries in cfg.get("hooks", {}).values():
    for e in entries:
        for h in e.get("hooks", []):
            m = re.search(r"(?:bash|python3)\s+(\S+)", h.get("command", ""))
            if m and not Path(m.group(1)).is_file():
                missing.append(m.group(1))
if missing:
    print("  FAIL: .claude/settings.json runs files that do not exist: %s" % missing, file=sys.stderr)
    sys.exit(1)
PY

# 4. The session hook must detect a companion that is neither Python nor at the top level.
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
mkdir -p "$W/app/src/main"; printf 'x\n' > "$W/app/src/main/Main.kt.md"
out="$(cd "$W" && bash "$ROOT/templates/hooks/session-start.sh")"
[ -n "$out" ] || bad "session-start.sh misses a .kt.md companion nested three levels deep"
mkdir -p "$W/empty"
[ -z "$(cd "$W/empty" && bash "$ROOT/templates/hooks/session-start.sh")" ] \
  || bad "session-start.sh speaks up in a project with no records"

# 5. The loop state is committed, not ignored — it carries the objective and the drafted handoff.
! grep -q '^| `\.gitignore` |' templates/commands/install-on.md \
  || bad "install-on still has a .gitignore action class for .aims/state.md"
grep -q 'is committed, not ignored' templates/commands/install-on.md \
  || bad "install-on no longer states that .aims/state.md is committed"
git check-ignore -q .aims/state.md 2>/dev/null \
  && bad "this repo ignores its own .aims/state.md"

# 6. No vocabulary from the retired structure in anything that ships.
for term in 'capsule' 'insights/' 'dependencies/'; do
  hits="$(grep -rn -- "$term" --include='*.md' skills commands templates knowledge 2>/dev/null || true)"
  [ -z "$hits" ] || bad "retired vocabulary '$term' still in a shipped surface:
$hits"
done

# 7. The state template must own every heading the commands read back out of state.md.
for h in '## Mode' '## Loop cursor' '## Current objective' '## Worker handoff' '## Open assumptions'; do
  grep -q "^$h" skills/aims-guide/assets/state-template.md \
    || bad "state template is missing the '$h' section the loop writes"
done

if [ "$fail" -eq 0 ]; then printf '[PASS] shipped install wiring is consistent\n'; exit 0; fi
printf '[FAIL] %d wiring problem(s)\n' "$fail" >&2; exit 1
