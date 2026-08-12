# Two modes: automatic and stepped

aims runs the **same** six-step operating loop either way. Modes change only *where the loop stops*
and *what advances it* — not what the loop does. The `.aims/state.md` **Mode** field records which
mode is active, and the **Loop cursor** records exactly where the loop is parked, so either an
automatic wake (a returning Worker) or an explicit human command can resume from precisely there.

## Automatic mode (default)

The Guide drives the whole loop end to end and pauses only at the **two legitimate human moments**:
an *open product decision* it must not guess, and *receiving the next product change*. Everything
between — choose objective → delegate → measure → choose again — happens autonomously. A
returning Worker **auto-advances** the loop (measure its evidence, choose the next
objective). This is the behavior described throughout `SKILL.md`.

## Stepped mode (hands-on supervision)

The user wants to inspect and steer between phases. The loop stops at **every phase boundary** and
advances **only on an explicit command**. The two automatic-mode pause points still apply *on top* of
the phase stops. The one behavioral change to internalize: **in stepped mode a returning Worker does
NOT auto-advance** — it parks at `executed:awaiting-review` and waits for the review command. Never
run measurement/choose-next off a Worker return while Mode is `stepped`.

### Explicit commands run inline, on your model — no subagent

When the user drives a phase with an explicit command, **do the work in this session, on the currently
selected model, and do not spawn a subagent.** The user chose that model and is supervising the phase;
a subagent would run on a different model and put the work behind a boundary they can't watch turn by
turn. So in stepped mode:

- **build** executes the drafted handoff **yourself, inline, as a clearly separated phase** — the same
  bounded handoff a Worker would have received, run in-session instead of delegated.
- **review** runs the panel roles **inline** on the current model (adopting each lens in turn, still
  obeying the reproduce-or-cite rule).

This does not collapse the Guide/Worker separation, because the separation that carries the value is
that **the design objective was produced first, as its own `plan` step** — the handoff already exists
and is being *conformed to*, not invented mid-build. Auto mode is different: there the loop delegates to
a Worker subagent, because autonomous delegation and context isolation are the point when no human is
watching.

## The phases, mapped to the loop steps

| Command (names are configurable) | Runs loop steps | Produces | Then parks at |
|---|---|---|---|
| **plan** | 1–3: establish state, choose one objective, protect intent, draft the Worker handoff | the Current objective + a bounded handoff, written to `state.md` | `planned:awaiting-build` |
| **build** (execute) | 4: delegate to a Worker (or run the handoff as a separated phase) | the Worker's result + evidence pointer | `executed:awaiting-review` |
| **review** | 5: measure evidence against exit criteria, run the review panel | reproduced readings + which criteria are met/unmet + implication for direction | `reviewed:awaiting-decision` |
| **auto** | switches Mode to `auto` and runs to the next legitimate pause | — | wherever the loop next legitimately parks |

After **review**, choosing the next objective (step 6) is simply the next **plan** — in stepped mode
the human triggers it; in auto mode the loop does it itself.

### Discipline at each stop

- **plan** stops *before* any delegation, so the human can read and edit the objective and handoff
  before a line of code is written. Open product decisions are still asked here — planning is where
  questions live. **Present a short plan report** — compiled from the objective and the design docs (the
  dependencies, decisions and their in-proximity rationale, chosen architecture, exit criteria), not a
  new stored file — so the human reviews the round's reasoning before `build`. Do not delegate from
  `plan`.
- **build** requires the cursor at `planned:awaiting-build` (or a reopened objective). If there is no
  current objective, say so and point to `plan`. Stop when the Worker returns; do **not** measure or
  decide direction — that is review's job.
- **review** requires the cursor at `executed:awaiting-review`. Measure per `review.md` and run the
  panel per `review-panel.md`. Report the readings, describe which exit criteria they show met/unmet,
  and what this implies for the next direction. Then record where the loop now is — `ready-to-choose-next`
  when the objective is reached, or back toward `plan`/`build` when the readings say it isn't; this
  records the loop's position, it does not accept or reject the Worker. Do not silently repair everything
  the reviewer reports — the Guide/human decides what matters to the product now.

## Loop-cursor vocabulary (extended)

Keep the cursor to one line, current:

```
needs-plan
planned:awaiting-build <objective>
awaiting-worker <objective>
executed:awaiting-review <objective>
reviewed:awaiting-decision <objective>
ready-to-choose-next
awaiting-human <named open product decision>
```

## Switching modes

Any stepped command sets `Mode: stepped`. The **auto** command sets `Mode: auto` and resumes the
autonomous loop from the current cursor. Switching mode never discards the cursor — a plan drafted in
stepped mode is built the same way in auto mode; the objective and evidence are mode-independent.
