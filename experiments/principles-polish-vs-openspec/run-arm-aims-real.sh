#!/usr/bin/env bash
# usage: run-arm.sh <product> <run-label> <prompt-file>
set -u
P=$1; L=$2; PF=$3
D=/home/user/aims-rerun/$P; OUT=/home/user/aims-rerun/_runs/$P-$L
mkdir -p "$OUT"; PF=$(readlink -f "$PF"); cp "$PF" "$OUT/prompt.txt"
start=$(date +%s)
# Isolation: a private mount namespace in which /home/user holds ONLY this product's repo, and /tmp and
# ~/.claude/{projects,tasks,backups,shell-snapshots} are empty tmpfs (no operator transcripts, no aims repo).
PROMPT="$(cat "$PF")" D="$D" OUT="$OUT" unshare -m --propagation private bash -c '
  set -e
  mkdir -p /run/armns/repo /run/armns/out
  mount --bind "$D" /run/armns/repo; mount --bind "$OUT" /run/armns/out
  mount -t tmpfs none /home/user; mkdir -p "$D"; mount --bind /run/armns/repo "$D"
  mount -t tmpfs none /tmp
  for d in projects tasks backups shell-snapshots; do mkdir -p /root/.claude/$d; mount -t tmpfs none /root/.claude/$d; done
  cd "$D" && env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD \
    claude -p "$PROMPT" --model claude-opus-5-5 --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Skill TodoWrite TaskCreate TaskUpdate TaskList Task Agent" \
    --output-format stream-json --verbose > /run/armns/out/transcript.jsonl 2> /run/armns/out/stderr.txt'
rc=$?; end=$(date +%s)
python3 - "$OUT" $((end-start)) $rc <<'PY'
import json,sys
out,wall,rc=sys.argv[1],int(sys.argv[2]),sys.argv[3]
tools=[];res=None
for line in open(out+"/transcript.jsonl"):
    try: e=json.loads(line)
    except: continue
    if e.get("type")=="assistant":
        for b in e["message"].get("content",[]):
            if b.get("type")=="tool_use": tools.append(b["name"])
    if e.get("type")=="result": res=e
u=(res or {}).get("usage",{})
stats={"exit":rc,"wall_s":wall,"tool_calls":len(tools),"tools":tools,
 "num_turns":(res or {}).get("num_turns"),
 "input_tokens":u.get("input_tokens"),"cache_creation_input_tokens":u.get("cache_creation_input_tokens"),
 "cache_read_input_tokens":u.get("cache_read_input_tokens"),"output_tokens":u.get("output_tokens"),
 "total_tokens":sum(u.get(k,0) or 0 for k in ["input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens"]),
 "cost_usd":(res or {}).get("total_cost_usd"),"model_usage":(res or {}).get("modelUsage"),
 "all_models_total_tokens":sum((m.get("inputTokens",0)+m.get("outputTokens",0)+m.get("cacheReadInputTokens",0)+m.get("cacheCreationInputTokens",0)) for m in ((res or {}).get("modelUsage") or {}).values()),
 "final_message":(res or {}).get("result")}
json.dump(stats,open(out+"/stats.json","w"),indent=1)
print(json.dumps({k:stats[k] for k in ["exit","wall_s","tool_calls","num_turns","total_tokens","all_models_total_tokens","output_tokens"]}))
PY
