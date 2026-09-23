# pt-c2 (C, PyTorch) — final reply, summarized as handed back

Sampler-level `state_dict()` / `load_state_dict()`: saves the in-progress epoch's seed (no generator) or restores
the passed generator's state; the most recently started iteration is saved; mismatches raise `ValueError`. 13 tests
(`TestRandomSamplerStateDict`); a docs section with a documented workaround for `num_workers > 0`. Asked once
(workers / scope), got the card's sentences.
