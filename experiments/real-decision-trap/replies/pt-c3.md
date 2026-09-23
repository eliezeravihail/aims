# pt-c3 (C, PyTorch) — final reply, summarized as handed back

`state_dict()` / `load_state_dict()` on `RandomSampler`: settings, the generator's state at the epoch's start, and
the count yielded; without a generator the resumed epoch draws nothing from the global RNG; mismatches raise
`ValueError`. 6 tests; a docs section. Documents that with `num_workers > 0` the checkpoint runs ahead by the
prefetch window. Asked once (workers / scope), got the card's sentences.
