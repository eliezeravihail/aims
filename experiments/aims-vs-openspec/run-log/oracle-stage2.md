# Oracle log — stage 2

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| P1 | Does non-stackable mean "not with another non-stackable", or "not with anything"? | "Yes. Non-stackable only means it can't sit next to another non-stackable one." | scripted |
| P2 | One global exclusion group, or named groups? | "One rule: two of them can't sit together. Nothing more elaborate than that." | unscripted |
| P3 | Apply the winner at the earliest contender's slot? | "I don't know; choose a simple sensible technical approach." | scripted fallback |
| P4 | List a promotion on a line whose share of that line was 0.00? | "If it didn't change that line's price, it doesn't need to be on that line." | unscripted |
| P5 | Should unknown / duplicate / inapplicable codes appear in the explanation too? | "Wherever support will see it. Your call." | scripted |
| P6 | A non-stackable code worth 0.00 — superseded, or no effect? | "It wasn't beaten by anything — it just saved them nothing. Say that." | consistent with O17 |
| P7 | Confirm the opening entry carries no delta, so deltas sum to the difference | "Yes — the deltas add up to what came off. And it has to be clear what we started from." | scripted |
| P8 | Mixed sign convention in one payload? | "I don't know; choose a simple sensible technical approach." | scripted fallback |
| P9 | Does anything consume the old per-line attribution list? | "No. Nothing reads it yet." | unscripted (factual: nothing is built) |
| P10 | A catalogue-version or quote-id stamp for auditors? | "Not now — build for today." | scripted standing answer |
| P11 | A catalogue-authored "why not" line per promotion? | "Code, name and amount is enough." | unscripted |

## Leak check
P10 is the one to watch: an auditor asking about a year-old quote is adjacent to nothing in stage 3, so
"not now" is honest rather than evasive. No answer mentions markets, tax, currency, or rounding modes.
P3 and P8 were pushed back as technical because they are: an ordinary buyer has no view on which pipeline
slot a winner is applied at, or on whether a payload mixes signed and unsigned figures.

## OpenSpec arm's questions

Its Q1/Q2/Q6/Q7 are the same questions the plain arm asked and got the **same words** (P5, P4, P2, P4).
New ones:

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| P12 | Compare exclusives against the basket as it stands, or against the list subtotal? | "Compare what each one actually takes off the basket in front of you." | unscripted; stated as an outcome |
| P13 | Compare capped value or face value? | "The one that saves the customer more money. What actually comes off." | consistent with P12 and with the card's own wording |
| P14 | Is it acceptable that typing order decides a tie, visibly? | "Yes. The first one they typed wins, and it's fine that it shows." | from the card ("if they tie, apply the one the customer entered first") |
| P15 | Is storing the explanation for a later dispute in scope? | "Whoever calls you keeps the answer. That isn't your job." | unscripted |
