# pt-c1 (C, PyTorch) — final reply, summarized as handed back

Sampler-level `state_dict()` / `load_state_dict()`: data length, `num_samples`, `replacement`, the generator's state
at the epoch's start, and the count handed out; without a generator resuming draws nothing from the global RNG;
mismatches raise `ValueError`. `TestRandomSamplerStateDict`; a docs section with a warning on `num_workers > 0`.
Asked once, after building (workers / scope), got the card's sentences; changed nothing further.
