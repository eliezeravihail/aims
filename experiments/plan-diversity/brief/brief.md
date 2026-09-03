# Frozen brief — design objective: the "responsible doctor" MVP

*The identical, frozen input every arm receives (Baseline, A, B, C). Kind = **design**: the deliverable is
an architecture/shape; no running code is required. The brief states **what must hold**; it does not
prescribe the structure that achieves it — that structure is what the arms design and the judge measures.*

**Task.** Design the architecture for an **MVP of the "responsible doctor" app** — an ordinary application
(web/service; the delivery surface is not prescribed) — scoped as below. Design it as you normally would.

## The product

A proactive care-coordinator — a **"responsible doctor"** — that **manages and steers** medical processes
and **never originates medical advice**. The unifying object is a personal **medical tracking file**
(*תיק מעקב רפואי*) that fuses authoritative sources with the person's reported medical state. Its job is to
show what is **expected** next and what is **done**, and — when an open process has no plan — to **nudge the
person to ask their doctor**, never to recommend a course of action itself.

**The universal, non-negotiable boundary.** Every output the system produces is a **citation**: a join of
*(an authoritative source — a public guideline/protocol, a doctor instruction, a prescription)* against
*(a **reported** medical state)*. The system **never infers** the medical state and **never originates**
advice. This holds for every user, **including a doctor user**.

## MVP scope — design for exactly this, no more

- **Pillar 1 only** — managing/steering processes (the pathway / next-step side). The integrated overview
  (*המכלול*) is **out of the MVP**.
- **Account primitive:** a **manager operates one-or-many subjects** (a person managing their family; a
  doctor managing patients) — one abstraction: `manager → subject(s)`.
- **Sources ingested (at least):** one class of **public/authoritative guideline** (e.g. an age/risk-based
  screening schedule or a well-baby schedule) **and** the subject's own **reported items** (results, doctor
  instructions, prescriptions).
- **Expected side:** driven by a **library of known medical pathways/rails** — *not* hardcoded to any one
  example. **Reported/done side:** the subject's state.
- **Output:** an **expected-vs-done ledger** with **gaps flagged**, each flag carrying its **source citation**
  and a **confidence tier by source**; a "no plan for an open process" gap becomes a **nudge to ask the
  doctor**.

## Exit criteria — the design must satisfy these (measured structurally)

1. The **non-advice boundary is enforced by the architecture, not by convention**: one place every output
   must pass through that can *only* emit a `(source × reported-state)` citation — no path can originate
   advice or infer state.
2. `manager → subject(s)` is a **single primitive**; multi-subject (family / a doctor's patients) is the same
   abstraction, not a special case.
3. **Expected** (pathway rails) and **reported/done** (subject state) are **distinct**, and gaps are
   **computed by joining them** — not enumerated per example.
4. **Source provenance and confidence tier travel with every** expected/nudge item — a citation is
   inseparable from its source.
5. Adding a **new pathway** or a **new source type** is **one owner's change** — it does not scatter across
   the ledger, the account model, and the output layer.
6. Scoped to Pillar 1 and the MVP sources above; anything built for the overview, for inference-based
   suspicions, or for unstated future sources is **speculative** (and should score against the design).

## Deliverable

The architecture/shape: the data model, the boundaries, **the ownership of the citation invariant**, the
`manager → subject(s)` primitive, and how *expected* and *reported* are joined into the ledger. State the
**day-zero vocabulary** the public seams may speak. No running code required.
