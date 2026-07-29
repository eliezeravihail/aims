---
updated: 2026-07-29
---

# Charter — aims

## Vision

aims is a lean code-development discipline for Claude Code. It does not try
to make the model reason better; it captures a project's **processes and
work-considerations** as durable artifacts kept next to the code, so that
both the human and the agent returning to the project tomorrow know what was
done, why, and how to continue. Reliability comes from single-dispatch
discipline (one strong-model session, no orchestration), not from a
multi-agent pipeline.

## Constraints

- **Markdown + bash only** — no language toolchain, no runtime service.
- **Zero external dependencies, zero network, no API keys** — every helper
  is pure bash/awk (or the stdlib-only Capsa validator).
- **Zero global state** — the discipline lives inside each target project;
  only `/install-on` may ever be globally visible.
- **Storage format: Capsa** — as of decision 0031, aims stores its own
  management truth as a conforming `.capsa/` capsule (Capsa 0.2.0). aims is
  the active self-maintenance layer; the capsule is passive data.

## Ground rules

- **Hooks inform, they never block** (decision 0020). A hook's only effect
  is factual injected context; discipline is achieved by awareness.
- **Planning is a behavior, not a command** (decision 0022). A non-trivial
  change is planned before implementing: read-only discovery → a draft plan
  on disk → approval → implementation → inline close-out.
- **Trivial-skip is declared** — an inline-eligible change states that
  judgment in one sentence before editing.
- **Decisions are append-only** — a changed decision is a new decision that
  supersedes the old; history is never rewritten.

## Initial decisions of record

- Single-dispatch over multi-agent orchestration — decision 0002.
- Hooks inform, never block — decision 0020.
- Planning as a behavior; `/plan` dispatches an Opus subagent — decision 0022.
- aims adopts the Capsa capsule format — decision 0031.
