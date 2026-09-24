#!/usr/bin/env bash
# usage: run-arm.sh <product> <run-label> <prompt-file>
set -u
P=$1; L=$2; PF=$3
D=/home/user/os-rerun/$P; OUT=/home/user/os-rerun/_runs/$P-$L
mkdir -p "$OUT"; PF=$(readlink -f "$PF"); cp "$PF" "$OUT/prompt.txt"
start=$(date +%s)
cd "$D" && env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD OPENSPEC_TELEMETRY=0 \
  claude -p "$(cat "$PF")" --model claude-opus-5-5 --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Skill TodoWrite TaskCreate TaskUpdate TaskList" \
  --output-format stream-json --verbose > "$OUT/transcript.jsonl" 2> "$OUT/stderr.txt"
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
 "final_message":(res or {}).get("result")}
json.dump(stats,open(out+"/stats.json","w"),indent=1)
print(json.dumps({k:stats[k] for k in ["exit","wall_s","tool_calls","num_turns","total_tokens","output_tokens"]}))
PY
