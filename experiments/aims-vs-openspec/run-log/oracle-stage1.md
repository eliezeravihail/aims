# Oracle log — stage 1
Answers are given verbatim. Any arm asking the same question gets the same words.
Scripted = pre-written in hidden/spec-and-oracle.md. Unscripted = decided now, from current-stage
facts only, and added here so the next arm gets it identically.

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| O1 | BOGO at quantity 3 with COFFEE3 — one free or none? | "With three of them in the cart, one is free." | scripted (consistent with "7 with N=3 -> two are free") |
| O2 | PCT before AMT, or AMT before PCT? | "Whatever order you pick, the answer has to be the same every time for the same cart." | scripted |
| O3 | Two 10% codes — 19% or 20%? | "Two 10% codes should take 19% off, not 20%." | unscripted; stated as an outcome, deliberately not as a mechanism |
| O4 | Two BOGOs on one SKU — stack or one wins? | "They both apply." | unscripted; from the stage-1 card only ("a cart can have more than one code"). Saying "the better one wins and the other is reported" would leak stage 2 |
| O5 | Does a line price include its share of a cart-wide discount? | "What the customer actually pays for that line — the number on the invoice. The line prices have to add up to the total." | unscripted |
| O6 | Duplicate code entered twice? | "Count it once, and tell the customer it was entered twice." | unscripted |
| O7 | Confirm half-up rounding? | "It has to come out to the cent, and the same cart has to give the same answer twice." | scripted (deliberately does not name a rounding mode) |
| O8 | Retire a code: delete, or disable? | "Take it out of the file. If someone types it, telling them we do not know that code is fine." | unscripted |
| O9 | Zero-quantity line? | "I don't know; choose a simple sensible technical approach." | scripted fallback |
| O10 | Which currency; per request or configured? | "One currency. Two decimals." + "I don't know; choose a simple sensible technical approach." for where it is configured | scripted |
| O11 | Upper bound on cart size? | "I don't know; choose a simple sensible technical approach." | scripted fallback |

## Leak check
Every answer re-read against the banned list (*still, yet, for now, at this stage, initially, to begin
with, later, eventually*). None present. O3 was deliberately phrased as an outcome ("takes 19% off")
rather than a mechanism ("apply one after the other"), because the mechanism is the latent decision the
pilot is measuring and describing it would have handed it to the arm.
O4 was the dangerous one: the natural answer is stage 2's supersession rule. Answered from the stage-1
card only.

## Declared deviation
The cards say "one at a time". Arms asked in batches at the end of their round and were answered in
batches. Applied identically to all three arms.

## Additional questions (aims arm), and the reuse check

The aims arm's Q5/Q1/Q2/Q3/Q4 are the same questions as the plain arm's Q1/Q5/Q2/Q3/Q6 and were given
the **same answers, word for word** (O1, O5, O2, O3, O6 above). New ones:

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| O12 | Typo in the promotions file — reject the whole file, or skip the bad code? | "One typo shouldn't stop the shop from selling. Tell us which code is broken and carry on with the rest." | unscripted; grounded in the stage-1 card's own rule that a bad code "does not stop the rest of the cart from pricing" |
| O13 | Are codes and SKUs case-sensitive? | "Customers type them however they like. Treat SAVE10 and save10 as the same code." | unscripted |
| O14 | Same SKU on two lines at different prices — which units are free? | "Yes, that happens. The cheapest ones are the free ones." | unscripted |
| O15 | Do promotions need start/end dates or usage limits? | "Not now — build for today." | scripted standing answer |
| O16 | Is the customer id meant to drive anything? | "Not now — build for today." | scripted standing answer |

Note on O1: the two arms asked the BOGO question from opposite defaults — the plain arm had assumed
`qty // 3`, the aims arm `qty // 4`. Both were given the identical answer, which confirms one of them and
overturns the other. That is the oracle working as intended: the arm that asked got told, and neither was
steered.

## Additional questions (OpenSpec arm)

Its Q1/Q2/Q3/Q4/Q5/Q7/Q9/Q10 are the same questions the other arms asked and were answered with the
**same words** (O1, O3, O2, O7, O12, O14, O16, O8). New ones:

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| O17 | A valid code that takes 0.00 — "applied, no effect" or inapplicable? | "Tell the customer it was accepted but saved them nothing." | unscripted |
| O18 | Any limit on stacking, or a code that should be exclusive of others? | "They both apply." + "Not now — build for today." | scripted standing answer |

**O18 is the one the whole pilot turns on.** Stage 2 introduces non-stackable promotions and supersession.
The OpenSpec arm asked, in effect, whether that exists — and the honest answer from stage-1 facts is that
codes stack and nothing more is coming today. Answering it any other way would have handed one arm the
next stage. The plain arm's narrower version of the same question (two BOGOs on one SKU) got the same
"They both apply."

Note on O12: it **overturns** the OpenSpec arm's stated assumption. It had chosen strict whole-file
rejection and argued for it at length ("a quarantined code is one the marketing email already promised").
The product owner's answer goes the other way. Recorded because it is exactly the kind of thing that
should move a design, and because it is evidence the oracle was not simply confirming what each arm
already believed — it overturned the aims arm on BOGO and the OpenSpec arm here.

## Second round (plain arm's follow-ups)

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| O19 | Two BOGOs on six coffees — 2 free or 3? | "Two. A coffee we already gave away shouldn't earn another one." | unscripted |
| O20 | Can a zero-value order exist? | "Yes, a zero-value order is fine. It happens." | unscripted |
| O21 | Case-insensitive and trimmed code matching? | "Customers type them however they like. Treat SAVE10 and save10 as the same code." | same words as O13 |
| O22 | Who owns the wording shown to the customer? | "Your wording is internal. Our front end writes what the customer sees." | unscripted |

Stage 1 closes after this round for every arm: two question rounds each, then the stage is done. Applied
identically to all three.
