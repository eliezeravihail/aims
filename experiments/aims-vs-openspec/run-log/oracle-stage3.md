# Oracle log — stage 3

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| R1 | Does SOUTH use a different currency? | "Same currency in both. That isn't changing." | unscripted |
| R2 | One promotions file per market, or one shared? | "One file per market. They run different offers." | unscripted |
| R3 | Is the market a property of the deployment or of the request? | "A cart is for one market, and it tells you which." | scripted ("Can a cart mix markets? No. A cart is for one market.") |
| R4 | Keep the old JSON key names for a release? | "Nothing is live yet. Nobody is reading those names." | unscripted (factual: nothing is built) |
| R5 | Which number do existing integrations treat as the total? | "Nothing is live yet. Just make the number the customer pays the obvious one." | unscripted |
| R6 | Per-line tax in NORTH too? | "No. Only SOUTH invoices have to show it." | scripted |
| R7 | Tax as a closing block, or a row in the explanation? | "Keep the working adding up. Where the tax sits is your call, as long as the customer can see what tax they paid." | unscripted; deliberately refuses to pick the structure |
| R8 | Does SOUTH's half-even apply to anything but tax? | "Tax only." | unscripted; follows the card, which names half-even for tax alone |
| R9 | What happens when a VAT rate changes? | "Not now — build for today." | scripted standing answer |
| R10 | Does the SOUTH invoice need the tax element of each discount? | "Not now — build for today." | scripted standing answer |
| R11 | Are reduced or zero VAT rates per product coming? | "Not now — build for today." | scripted standing answer |

## Leak check
R7 is the one that mattered: the arm asked me to choose between putting tax inside the adjustment chain or
beside it, which is the central structural question of the stage. Refused — the answer states the
requirement (the working must add up, the customer must see the tax) and leaves the structure to the arm,
which is exactly what an ordinary buyer would do and what PROTOCOL §4 requires.
R9-R11 are three separate future features; all three got the standing answer rather than a hint.

## OpenSpec arm's questions

Its Q2/Q3 repeat the plain arm's and got the **same words** (R6, R1). New ones:

| # | Question (paraphrased) | Answer given, verbatim | Source |
|---|---|---|---|
| R12 | Does "unchanged" mean the old numbers stay, with tax reported beside them? | "Yes. The numbers you had stay the numbers you had, and the tax and the amount they pay sit beside them." | from the card ("unchanged, to the cent") |
| R13 | Is a 10.00 voucher 10.00 gross in SOUTH? Should a code be market-restricted? | "Ten off is ten off the price on the shelf, in both places. That's what the customer sees." + "One file per market. They run different offers." | unscripted + R2 |
| R14 | Who owns the market/tax table — engineering or finance? | "Keep that with the engineers. I don't want anyone editing a tax rate by hand." | unscripted |
| R15 | Must a past cart be re-derivable at its historical rate? | "Not now — build for today." | scripted standing answer |
| R16 | Does SOUTH's invoice need more than the per-line tax? | "What's on the card is what we need." | scripted standing answer |

## aims arm's questions

Every one of its seven repeats a question another arm already asked, and every one got the **same words**:
Q1→R1, Q2→R12, Q3→R13, Q4→R2, Q5→R6, Q6→R11, Q7→R9. No new answers were needed, which is itself a small
check on the oracle: three independent arms converged on substantially the same seven-to-eleven product
questions at this stage.
