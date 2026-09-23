# The product owner — frozen before any arm runs

Rules as in design-at-scale: an answer below for the case, verbatim, if the question matches it; else, if the card
answers, the card's own sentences, verbatim; else *"I don't know — choose a simple, sensible technical approach."*
Any question about later plans: *"Not now — build for today."* No reply to "unless you object". Every exchange is
logged in `oracle-log.md`.

## PyTorch — only if a session asks whether re-seeding with `torch.manual_seed` before an epoch must keep
## reproducing the order, whether several iterators of one sampler must stay independent, or whether the sampler
## may keep one generator across epochs

"Yes, both must keep working: users call `torch.manual_seed` before each epoch and expect the same order, and one
sampler can be iterated by several iterators at once. Don't keep one generator on the sampler across epochs."

## requests — only if a session asks whether the default may live on the `Session` (an attribute, a constructor
## argument, `__attrs__`), or asks about the project's past decisions on session timeouts

"The maintainers decided long ago that a timeout is not `Session` state: `Session` holds what concerns HTTP
(headers, cookies, auth), the transport adapters hold what concerns connections, timeouts included. Keep to that."
