# aims arm (current aims, real isolation): run log (feed-ranking)

Rerun 2026-09-23 of the aims-single arm, matched to the openspec-real arm (`../openspec-real/`), which is unchanged.

- **Pinned aims:** `477cff9b397f79869f72cf13f32f2f626a3dd2e9`. Only `skills/aims-guide/` at that commit was copied into the repo's `.claude/skills/aims-guide/`.
- **Model:** configured `claude-opus-5-5` for every session. Workers are subagents in the same session; see `runs/*/stats.json` → `model_usage`.
- **Starter:** a fresh git repo with `substrate.md` and `.claude/skills/aims-guide/` only. No CLAUDE.md, decisions/ or experiments/.
- **Isolation:** each session ran in a private mount namespace. There, `/home/user` held only this repo, and `/tmp` and `~/.claude/{projects,tasks,backups,shell-snapshots}` were empty tmpfs mounts. A diagnostic session (`runs/feed-ranking-isolation-test`, feed-ranking only) confirmed three things: `aims-guide` was the only project skill, no CLAUDE.md was loaded, and `/home/user/aims` did not exist. Permission mode was `acceptEdits`, with the tools Bash, Read, Write, Edit, Glob, Grep, Skill, Todo/Task* and Task/Agent.
- **Prompt:** the stage card verbatim, then "follow the aims-guide skill; design only", then a fixed operator note: follow aims-guide including its mandatory review-and-revise round in-session, stop before writing code, write questions to `QUESTIONS.md` and stop, write the final design to `DESIGN.md`. Exact prompts are in `runs/*/prompt.txt`; transcripts are in `runs/*/transcript.jsonl.gz`.
- **Stage 2** ran in the same repo, so the session saw its own stage-1 `DESIGN.md` and records.
- **Saved:** `stage-N/DESIGN.md` (the design judged) and `stage-N/repo/` (every record filed by tag `stage-N`: `.aims/`, `decisions/`, root records). `git-log.txt` holds the tags.
- **Revise round:** `.aims/state.md` records the mandatory revise round as done at both stages.

## Oracle log

- **Stage 1:** the arm wrote `QUESTIONS.md` and stopped (`s1-r1`). Questions verbatim: [`s1-QUESTIONS.md`](s1-QUESTIONS.md). Answers verbatim: [`s1-ANSWERS.md`](s1-ANSWERS.md). A fresh session was given the card, the line, the Q&A and the note (`s1-r2`). The first session's `.aims/state.md` was left in the repo; its `QUESTIONS.md` was removed after it was logged.
- **Stage 2:** the arm wrote `QUESTIONS.md` and stopped (`s2-r1`). Questions verbatim: [`s2-QUESTIONS.md`](s2-QUESTIONS.md). Answers verbatim: [`s2-ANSWERS.md`](s2-ANSWERS.md). A fresh session was given the card, the line, the Q&A and the note (`s2-r2`). The first session's `.aims/state.md` was left in the repo; its `QUESTIONS.md` was removed after it was logged.

The answers come only from `../../hidden/spec-and-oracle.md`, from the current stage. Where a question matched one the openspec-real arm had asked, it got the same answer word for word (protocol §4.6). The oracle's own phrases "all stage 1 needs" and "ignore cross-zone for now" were given without "stage 1" and "for now", which are leak words under §4.5.

## Cost per session

`main tokens` counts the main loop only (input, cache creation, cache read and output), the same accounting as openspec-real. `all-model tokens` sums `modelUsage` over every model, Worker subagents included.

| run | what | wall s | tool calls | turns | main tokens | all-model tokens | output tokens (main) | USD |
|---|---|---|---|---|---|---|---|---|
| `isolation-test` | isolation check (diagnostic, not an arm run) | 22 | 3 | 4 | 101,400 | 128,067 | 1,519 | 0.25 |
| `s1-r1` | stage-1 design | 49 | 6 | 8 | 295,901 | 297,148 | 4,436 | 0.32 |
| `s1-r2` | stage-1 design (re-spawn with oracle answers) | 875 | 70 | 6 | 657,612 | 4,120,135 | 3,832 | 6.24 |
| `s2-r1` | stage-2 design | 93 | 12 | 14 | 606,370 | 607,613 | 8,734 | 0.89 |
| `s2-r2` | stage-2 design (re-spawn with oracle answers) | 1029 | 91 | 7 | 1,430,363 | 7,557,992 | 6,471 | 8.27 |
| **total (excl. isolation test)** | | **2046** | **179** | | **2,990,246** | **12,582,888** | **23,473** | **15.72** |
