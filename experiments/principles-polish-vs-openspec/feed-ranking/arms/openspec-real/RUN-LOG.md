# OpenSpec arm, real tool: run log (feed-ranking)

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

Stage 1: none asked.

Stage 2: the arm wrote `QUESTIONS.md` and stopped (run `s2-r1`). Verbatim questions: [`s2-QUESTIONS.md`](s2-QUESTIONS.md). Verbatim answers: [`s2-ANSWERS.md`](s2-ANSWERS.md). A fresh session was then given the card + the line + the Q&A (run `s2-r2`); it proposed without further questions.

Oracle sourcing: Q1's first sentence is the hidden spec's canonical stage-2 answer ("Does diversity outrank score?"); the unsatisfiable case is not in the hidden spec, so it was answered "not specified; choose a simple, sensible approach". Q2 (input shape, multi-topic) is not in the hidden spec → the policy's "I don't know; choose a simple sensible technical approach". Q3's first sentence is the hidden spec's canonical "muted item … is absent; it does not exist in the output" (extended to blocked, which the card states identically). No later-stage content; no leak words.

## Cost per session

| run | what | wall s | tool calls | turns | tokens (in+cache+out) | output tokens | USD |
|---|---|---|---|---|---|---|---|
| `s1-archive` | stage-1 archive | 40 | 7 | 10 | 368,500 | 3,187 | 0.37 |
| `s1-r1` | stage-1 explore+propose | 141 | 18 | 21 | 703,747 | 14,485 | 0.77 |
| `s2-r1` | stage-2 explore+propose | 45 | 4 | 6 | 223,395 | 3,851 | 0.34 |
| `s2-r2` | stage-2 explore+propose (re-spawn with oracle answers) | 201 | 15 | 18 | 895,055 | 20,528 | 1.07 |
| **total** | | **427** | **44** | | **2,190,697** | **42,051** | |

## Deviations
- The prompt carries the operator note described above, which is needed for a non-interactive question channel.
- **Harness false start:** the first stage-1 launch died before any model call, because of a bad prompt path and root refusing bypass mode. Nothing ran and it is not counted.
- **Archive:** archived on the first prompt, with an incomplete-tasks warning, because the project is design-only.
