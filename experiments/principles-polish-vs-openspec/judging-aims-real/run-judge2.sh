#!/usr/bin/env bash
# usage: run-judge2.sh <product> <disposition: ownership|simplicity>
# Each judge = one new session in a private mount namespace where /home/user holds only its own workspace.
P=$1; K=$2; B=/home/user/judge2; J=$B/ws/$P-$K; mkdir -p $J/blind; cp $B/blind/$P/* $J/blind/
mkdir -p $B/proj/$P-$K $B/logs; U=$(python3 -c "import uuid;print(uuid.uuid4())"); echo $U > $B/logs/$P-$K.session
sed "s|__DISPOSITION__|$(cat $B/disp-$K.txt)|" $B/prompt-2-template.txt > $B/logs/$P-$K.prompt-2.txt
run() { # $1 prompt file, $2 log, $3 extra flags
  PROMPT="$(cat $1)" J=$J PROJ=$B/proj/$P-$K LOG=$2 FLAGS="$3" unshare -m --propagation private bash -c '
    set -e; mkdir -p /run/jns/ws /run/jns/logs /run/jns/proj; mount --bind "$J" /run/jns/ws; mount --bind /home/user/judge2/logs /run/jns/logs
    mount --bind "$PROJ" /run/jns/proj
    mount -t tmpfs none /home/user; mkdir -p "$J"; mount --bind /run/jns/ws "$J"
    mount -t tmpfs none /tmp
    for d in tasks backups shell-snapshots; do mkdir -p /root/.claude/$d; mount -t tmpfs none /root/.claude/$d; done
    # projects/ = this judge own private store (persists across its two calls, for --resume; nothing else in it)
    mount --bind /run/jns/proj /root/.claude/projects
    cd "$J" && env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD \
      claude -p "$PROMPT" $FLAGS --model claude-opus-5-5 --permission-mode acceptEdits --allowedTools "Bash Read Write Glob Grep" \
      --output-format stream-json --verbose > /run/jns/logs/$(basename $LOG) 2>&1 < /dev/null'
}
s=$(date +%s)
run $B/prompt-1.txt $B/logs/$P-$K-1.jsonl "--session-id $U"
m=$(date +%s)
mkdir -p $J/rubric $J/product; cp $B/stage2/$P/rubric/* $J/rubric/; cp $B/stage2/$P/product/* $J/product/
run $B/logs/$P-$K.prompt-2.txt $B/logs/$P-$K-2.jsonl "--resume $U"
e=$(date +%s); echo "$P $K guess_s=$((m-s)) score_s=$((e-m))"
