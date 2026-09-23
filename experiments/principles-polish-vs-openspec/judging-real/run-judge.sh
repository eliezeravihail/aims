#!/usr/bin/env bash
P=$1; J=/home/user/judge/$P; U=$(python3 -c "import uuid;print(uuid.uuid4())"); echo $U > $J/.session
cd $J
T="Bash Read Write Glob Grep"
s=$(date +%s)
env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD claude -p "$(cat ../prompt-1.txt)" --session-id $U --model claude-opus-5-5 --permission-mode acceptEdits --allowedTools "$T" --output-format stream-json --verbose > ../_log-$P-1.jsonl 2>&1
m=$(date +%s)
cp -r ../_stage2/$P/rubric ../_stage2/$P/product $J/
env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD claude -p "$(cat ../prompt-2.txt)" --resume $U --model claude-opus-5-5 --permission-mode acceptEdits --allowedTools "$T" --output-format stream-json --verbose > ../_log-$P-2.jsonl 2>&1
e=$(date +%s); echo "$P guess_s=$((m-s)) score_s=$((e-m))"
