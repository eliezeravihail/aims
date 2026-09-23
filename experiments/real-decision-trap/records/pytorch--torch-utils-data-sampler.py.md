---
title: "sampler.py"
date: 2026-09-23
hash: "sha256:817f818a4897f0c12569aa88edb951c3d9912cc20b4a47d62bff3b70cadf1ac5"
---
## Insights
- Keeping `RandomSampler`'s generator on the instance (`self.generator = generator` when none was passed)
  was merged once (pytorch#63026, 2021-08-16, after the first attempt pytorch#53085 was dropped) and reverted
  (pytorch#63646, 2021-09-30). Symptom: calling `torch.manual_seed(s)` before each epoch no longer gave the
  same order, because the cached generator ignores the global RNG unless its own `manual_seed` is called.
- Re-attaching a fresh generator to `self` inside each `__iter__` (so re-seeding works again) was also
  proposed and rejected in review: two live iterators of the same sampler (`i1 = iter(s); i2 = iter(s)`)
  would share and overwrite one generator. That is why the generator is a local of `__iter__`.
- As of this record's date nothing in `test/test_dataloader.py` guards either property for `RandomSampler`
  with `generator=None`: no test re-seeds the global RNG between epochs, and none runs two iterators at
  once. (`test_shuffle_reproducibility` passes an explicit generator; `test_shuffler_iterdatapipe`
  re-seeds, but tests the DataPipe shuffler.) A refactor that caches the generator would pass the suite.

## Decisions
- With `generator=None`, `RandomSampler` gets a new generator for each iteration, local to that iterator and
  seeded from the global RNG. Rule: `torch.manual_seed(s)` before an epoch must reproduce that epoch's order,
  and iterators of one sampler must not share RNG state. This rules out storing a generator on `self` (at
  construction or in `__iter__`), even to save rebuilding it each epoch or to make sampler state
  serializable (pytorch#63646, reverting #63026).

## Discussions
- What this costs: the iter-local generator's state cannot be captured or serialized, so a paused epoch
  cannot be checkpointed and resumed from the sampler. Serializability was the reason for caching it.
  A follow-up to serialize the iter-local generator (pytorch#65857) was closed as stale, never merged and
  never rejected on its merits. That capability is still open, not ruled out; any design for it must keep
  both rules above.
- Settled for now, but still contested: issue pytorch#49727 (open) calls the per-iteration re-creation a bug.
  The "tests relying on re-seeding" given as the reason to keep it (pytorch#53085) are not in this checkout
  (see Insights). The reason rests on user-visible reproducibility (the #63026 regression report), not
  on a test here.
- The performance case for caching (not building a `torch.Generator` each epoch) was stated but never
  measured.
