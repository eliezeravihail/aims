# Stage 1 — build card (given to both arms; stage 2 not revealed)

Design and build the architecture (with concrete, typed interfaces) for the following application.

## What it does

An application that **identifies which Israeli plant species** an observed specimen is, from a set of
**observed morphological and ecological features** the user supplies. Scope: the ~500 plant species of
Israel that have a Wikipedia entry.

The user gives whatever features they observed — for example:

- **leaf** shape, margin, arrangement
- **flower** colour, number of petals, structure/symmetry
- **height / growth habit** (herb, shrub, tree; a height figure)
- **habitat / location** (coastal sand, Mediterranean woodland, desert, Galilee, Negev, …)
- **blooming season**

The user usually supplies only **some** of these. The app returns the **plant species consistent with the
observations**, narrowed and **ranked**, with an **explanation** of which observed features matched or
excluded each candidate.

## Data

The reference data (which species exist and each species' features) is **ingested from Wikipedia** — the
Wikipedia pages for those species are the source. The app parses/normalizes that source into its own
reference form.

*Build constraint (experiment):* there is **no live external access** — stand the Wikipedia source in with
a **small mock/fixture** (a handful of species with features) behind the ingestion seam. The point of the
exercise is the design and its interfaces, not a live crawl; a real Wikipedia adapter must be able to take
the mock's place without touching the identification core.

## Required behaviours

- **Partial input is normal** — only the features actually observed constrain the result; a missing feature
  is not a mismatch.
- An **unknown or invalid feature value** (a colour or a habitat the system doesn't recognize, a
  contradictory figure) is **reported** to the user — never silently dropped, never a crash.
- **No-match** (nothing is consistent with the observations) and **many-match** (too many candidates remain)
  are **distinct, valid results**, each communicated as itself — not an empty list that looks like an error.
- The **ranking is explainable**: for each returned candidate the user can see which observed features it
  matched and which excluded others.
- Features are of **different kinds** — some are categorical (leaf shape, flower colour), some are
  **numeric** (height); the height a user gives is a single figure but a species' height in the source is
  naturally a **range**. Matching must handle both kinds correctly.

## Deliverable

A **buildable architecture**: the modules and their responsibilities, the seams between them, and the
**concrete, typed interfaces** (types and signatures) crossing those seams — enough that a competent
engineer could implement each part without further design decisions. Not the full line-by-line
implementation; the design and its interfaces.
