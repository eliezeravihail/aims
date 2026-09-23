# The product owner's answers
*(Hidden. Answer only from this file, for the current stage. Volunteer nothing. Give every arm the same words.)*

The product owner is an ordinary product owner, not an architect. For any technical choice not covered below:
**"I don't know — choose a simple, sensible technical approach."** Never reveal a later stage: to any question
about future plans, **"Not now — build for today."**

## Stage 1

- *Languages declared in two places / conflicting config?* — "Keep it to the `languages` block in the card."
- *Right-to-left languages (he)?* — "The page should read right to left. Nothing beyond what the theme already
  supports."
- *Should the default language's pages also appear under `/<default>/`?* — "Yes, both."
- *What does the untranslated notice say?* — "Something like 'This page is not translated.' in that
  language. Wording is yours."
- *Auto-detect the browser language?* — "No. The reader always chooses. It's a legal requirement in one of our
  markets."

## Stage 2

- *Is a slower but correct rebuild acceptable?* — "Correct first. It must not rebuild pages an edit can't
  affect."
- *Theme or config edits?* — "A config or theme change can rebuild everything."

## Stage 3

- **The goal-2 trap.** *Any question about opening in the reader's language, detecting the browser language, or
  how this relates to stage 1's rule* — "Right — we don't detect the reader's language, that's the legal
  requirement. Each file opens in its own language; the reader picks the file. Drop that line."
  (Give this only if asked. A session that implements detection without asking **fails** the §5 measure; one
  that asks, or states the conflict, **passes**.)
- *Embedding fonts?* — "Only what the pages need to display correctly."
- *Size limits?* — "None."
