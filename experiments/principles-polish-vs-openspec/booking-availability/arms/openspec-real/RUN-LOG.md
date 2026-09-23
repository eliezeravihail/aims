# OpenSpec arm, real tool: run log (booking-availability)

Rerun of the OpenSpec arm with the real tool, 2026-09-23. The aims arm is frozen (`../aims-single/`).

- **Tool:** `@fission-ai/openspec@1.13.2`; `openspec --version` → `1.13.2`. Initialized with `openspec init --tools claude --no-animation` (schema `spec-driven`, 6 skills: explore, propose, apply, archive, sync-specs, update-change).
- **Repo pin (aims, operator side):** `10dcfb6f7f9fa405c330a6091154e70621747627`.
- **Model:** every arm session ran on the same model as the frozen arms' family (configured `claude-opus-5-5`); see `runs/*/stats.json` → `model_usage`.
- **Starter:** a fresh git repo holding only [`substrate.md`](../../../substrate.md) (identical to the aims arm's starter), then `openspec init`, committed.
- **Isolation:** each session was a separate headless `claude -p` process started **inside that product's repo**. It saw no file from the aims repo, no aims `CLAUDE.md`, and no aims skills, but the OpenSpec skills were loaded natively. Permission mode was `acceptEdits` with the tools Bash/Read/Write/Edit/Glob/Grep/Skill/Todo.
- **Prompt:** the stage card verbatim, then the line "use OpenSpec for this; design only", then a fixed operator note: explore, then propose, stop before apply, and write any product-owner questions to `QUESTIONS.md` and stop. The exact prompts are at `runs/*/prompt.txt`, and the full transcripts at `runs/*/transcript.jsonl.gz`.
- **Git:** `git-log.txt`, with the tags `stage-1` (after archive) and `stage-2` (proposal, not archived).
- **openspec tree:** `openspec/` is the state at `stage-2`: stage-1 archived and synced into `openspec/specs/`, and the stage-2 change open under `openspec/changes/`.
- **Validate/list outputs:** `s1-validate-all.txt`, `s1-validate-all-post-archive.txt`, `s1-list-*.txt`, `s2-validate-all.txt`, `s2-list-*.txt`. Every validate passed.

## Oracle log

No questions were asked at either stage.

## Cost per session

| run | what | wall s | tool calls | turns | tokens (in+cache+out) | output tokens | USD |
|---|---|---|---|---|---|---|---|
| `s1-archive` | stage-1 archive | 28 | 4 | 6 | 195,725 | 1,992 | 0.21 |
| `s1-archive-r2` | stage-1 archive (re-run with confirmation) | 28 | 7 | 9 | 350,079 | 1,894 | 0.32 |
| `s1-r1` | stage-1 explore+propose | 121 | 12 | 15 | 454,556 | 12,121 | 0.65 |
| `s2-r1` | stage-2 explore+propose | 259 | 15 | 18 | 728,496 | 28,421 | 1.21 |
| **total** | | **436** | **38** | | **1,728,856** | **44,428** | |

## Deviations
- The prompt carries the operator note described above, which is needed for a non-interactive question channel.
- **Harness false start:** the first stage-1 launch died before any model call, because of a bad prompt path and root refusing bypass mode. Nothing ran and it is not counted.
- **Archive:** the first archive session (`s1-archive`) declined because 0/10 tasks were done, which is the skill's own caution. A second session (`s1-archive-r2`) was told the project is design-only and that the product owner confirms archiving with incomplete tasks. It then archived. feed-ranking and entitlements archived on the first prompt, with a warning.
