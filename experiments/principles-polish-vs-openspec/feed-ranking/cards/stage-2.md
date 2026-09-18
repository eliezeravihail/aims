# Feed ranking — stage 2

The feed now has to respect two new rules. Both apply to the **same** ranking request.

1. **Eligibility.** The user maintains a block list (authors) and a mute list (topics). An item from a
   blocked author, or on a muted topic, must **never appear in the feed** — regardless of how high its
   signals are. A muted item is simply absent; it is not shown low.

2. **Diversity.** In the returned order, **no more than 2 items in a row may share the same author**. When a
   third consecutive same-author item would occur, it is deferred to the next available position that does
   not violate the rule; the relative order of everything else is otherwise preserved as much as possible.

The weighted scoring of stage 1, and the operator-tunable weights, keep working exactly as before.

Update the architecture to absorb these rules. Design only.
