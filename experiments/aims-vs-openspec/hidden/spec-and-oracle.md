# HIDDEN — the whole product, and the oracle's canonical answers

**No arm ever sees this file.** It exists so the operator answers product questions from a fixed script
instead of improvising, and so "was that a leak?" is decidable after the fact.

Oracle policy is [`../../PROTOCOL.md` §4](../../PROTOCOL.md), in force without exception: answer only from
the **current** stage; volunteer nothing; never reveal a later stage; neutral wording (one *"still"*,
*"yet"*, *"for now"* disqualifies the run — discard and re-run that stage); log every question and the
verbatim answer; the same question from another arm gets **the same answer, word for word**.

---

## 1. The whole product, all three stages (operator's view only)

A checkout pricing service. A cart is priced for a market; the price of every line and of the cart is the
**ordered composition of adjustments** over a list price, and the service can show that composition.

The complete picture, which no single stage card states:

- **Adjustments** are ordered and typed: the list price itself, each applied promotion, and (from stage 3)
  tax. Each carries an exact money delta. The final amount **is** the sum of the deltas — not a separately
  computed number that the deltas are reconciled against.
- **Rounding** is a property of a market, not of the code path: `NORTH` rounds half-up once at cart level
  after tax; `SOUTH` rounds half-even per line. A design with one hard-coded rounding point, or with
  rounding scattered across the promotion kinds, tears open at stage 3.
- **Promotions** are data, not code, from stage 1 onward (the card says so); stage 2 adds a stackability
  attribute and a supersession outcome; stage 3 changes what they apply *to* (net vs gross) without
  changing what they *are*.
- **Tax** is a market's model — exclusive-added vs inclusive-extracted — applied at a defined point in the
  same ordered composition, not a post-hoc multiplication bolted onto a finished total.

**The latent decision the stage-1 card glosses over:** whether a price is an opaque number computed inline,
or a first-class composition that can be inspected. Stage 1 gives no reason to prefer the second. That is
the point — a pilot only discriminates when the decision is genuinely latent.

**The falsification schedule:**

| Stage | What it falsifies |
|---|---|
| 2 | a total computed as an opaque number; an explanation built as a second, parallel implementation that can disagree with the amount |
| 3 | a single hard-coded rounding point; tax as a post-hoc multiplication; promotions that assume a tax-exclusive base |

## 2. Canonical oracle answers

Answer with the text below, or with *"I don't know; choose a simple sensible technical approach"* for a
technical choice an ordinary buyer would not make. If a question is not covered here and is genuinely a
product question, answer it from this file's current-stage facts only, write the answer down verbatim, and
reuse it for every arm.

### Stage 1

| If asked | Answer verbatim |
|---|---|
| Will there be more promotion kinds / other rules later? | "Not now — build for today." |
| Should promotions apply in a particular order? | "Whatever order you pick, the answer has to be the same every time for the same cart." |
| Does `BOGO` free-item pricing use the line's unit price? | "Yes. One of them costs nothing." |
| What if `BOGO`'s SKU has 7 with N=3? | "Two are free." |
| Can two `PCT` codes both be on one cart? | "Yes, that happens." |
| Do we need to persist carts / have a database? | "No. Price what we hand you." |
| Currency / locale / multiple currencies? | "One currency. Two decimals." |
| Should the unknown code be an error or a warning? | "Tell us the code didn't apply, and price the rest of the cart anyway." |
| HTTP or library? Language? | *"I don't know; choose a simple sensible technical approach."* |
| Rounding rule for the percentage discount? | "It has to come out to the cent, and the same cart has to give the same answer twice." |
| Should a line be able to go negative? | "The cart total can't go below zero. Below that, you decide." |

### Stage 2

| If asked | Answer verbatim |
|---|---|
| Is the explanation per line, per cart, or both? | "Both. A line has one, and the cart has one." |
| Can the explanation be computed separately from the amount? | "We only care that they never disagree." |
| What counts as "the larger discount"? | "The one that takes more money off this cart." |
| Both non-stackable and both tie? | "Whichever the customer entered first." |
| One non-stackable and one stackable — do they combine? | "Yes. Non-stackable only means it can't sit next to another non-stackable one." |
| Three non-stackable codes? | "Same rule. The biggest one applies; the rest are superseded." |
| Do superseded codes appear in the cart explanation, the line explanation, or both? | "Wherever support will see it. Your call." |
| Format — JSON? A string? | *"I don't know; choose a simple sensible technical approach."* |
| Is the list price itself an entry in the explanation? | "It has to be clear what we started from." |
| Will there be more markets / other tax rules? | "Not now — build for today." |

### Stage 3

| If asked | Answer verbatim |
|---|---|
| Is `NORTH` what we had before? | "Yes. Nothing about it changes." |
| Does `SOUTH` report tax on the cart too? | "Yes, and it has to be the sum of the line figures." |
| How do promotions interact with `SOUTH` tax? | "The discount comes off the shelf price, the way a customer reads it. The tax inside the price comes down with it." |
| Are line amounts in `SOUTH` rounded to the cent? | "A customer pays to the cent. How you get there is your call, as long as the working still adds up exactly." |
| Is there a market where both rules apply? | "Not now — build for today." |
| Can a cart mix markets? | "No. A cart is for one market." |
| Do `NORTH` line amounts show tax? | "No. Only `SOUTH` invoices have to show it." |
| What if a market's VAT rate changes? | *"I don't know; choose a simple sensible technical approach."* |
| Should the market be part of the request or configuration? | *"I don't know; choose a simple sensible technical approach."* |

### Standing answers, any stage

| If asked | Answer verbatim |
|---|---|
| Anything of the form "will X be needed later / is this going to change?" | "Not now — build for today." |
| "Should I design this to be extensible?" | "Build what we asked for. You know your job better than I do." |
| "Is there a spec / are there other requirements?" | "What's on the card is what we need." |

> **Leak watch.** The banned words in an oracle answer are *still*, *yet*, *for now*, *at this stage*,
> *initially*, *to begin with*, *later*, *eventually*. Re-read every answer before sending it. The phrase
> "Not now — build for today" is pre-cleared and is the only forward-looking-sounding answer permitted.

## 3. What the judges ask of the designs

Nothing is executed — there is no code. These are questions answered **from the design text**, each answer
carrying a quotation. They are derived only from requirements revealed by the end of stage 3.

### 3a. The survival count (Q2 — the primary reading)

Per arm, twice: stage-1 → stage-2, and stage-2 → stage-3. List every named component and seam in the
earlier design and classify each one against the later design:

| Class | Test |
|---|---|
| **survived** | present, unchanged, same responsibility |
| **extended** | same responsibility and same boundary, given more to do at a seam that already existed |
| **reopened** | its responsibility or its boundary changed |
| **discarded** | gone |

Report the table, then the **reopened + discarded** count, with both versions quoted for each instance.
A component renamed but unchanged in responsibility is *survived*, not discarded — and say so explicitly,
because renaming is the easiest way to inflate the number by accident.

### 3b. Structural questions (Q1 evidence)

Asked of each stage-3 design, answered with a quotation or with **the design does not say**:

- **S1** — to add a fourth kind of promotion, which named components change? Does the thing that computes
  the total change at all?
- **S2** — how many places in this design round money? Name them.
- **S3** — does the explanation come from the same structure that computes the amount, or is it produced
  separately? If separately, what in the design stops the two disagreeing?
- **S4** — to add a third market with a third tax model, which named components change?
- **S5** — where is the order of adjustments stated? One place, or implied in several?
- **S6** — which component owns "the deltas sum exactly to the difference"? If no component owns it, say
  so.

"The design does not say" is a finding, not a gap in the judging — a design that cannot answer S1–S6 is not
buildable, and that is a real result.

### 3c. Coverage (Q3's companion reading)

For each requirement revealed across the three cards, name the artifact in that arm that pins it — a spec
scenario, a stated rule, a recorded decision — or record **nothing pins it**. Count per arm: revealed /
pinned. This is the reading on which OpenSpec is at home, and it is scored on its own terms.
