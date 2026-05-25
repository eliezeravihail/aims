#!/usr/bin/env bash
# aims SessionEnd hook — un-throttled consolidation safety net.
#
# Most active users rarely fire SessionEnd; the Stop hook does the
# real work with a throttle. But IF the user does close the CLI,
# we want any dirty leaves consolidated before the session is gone.
# Cheap when nothing is dirty.

set -u

if [ -d ".claude/memory" ]; then
  HOOKS_DIR=".claude/hooks"
elif [ -d "templates/hooks" ]; then
  HOOKS_DIR="templates/hooks"
else
  exit 0
fi

# Delegate to stop-consolidate.sh with --force, so the threshold
# logic is bypassed. Identical behaviour otherwise (silent if no
# dirty leaves, graceful if no API key, never blocks).
exec bash "$HOOKS_DIR/stop-consolidate.sh" --force
