# GitHub discussion about `torch/utils/data/sampler.py` — `RandomSampler`'s generator

Collected from pytorch/pytorch. Quotes are as rendered by a page-fetch tool on 2026-09-23 (issue #63609's body was
read raw); wording may differ in small ways from the original.

## PR #53085 — "Avoid re-creating the random number generator in RandomSampler" (2021, closed)

lartpang (author): "To optimize the construction of iterator and make behavior consistent with generator or without
it, I change `self.generator = generator` when `self.generator is None`. So, when new iter is called, sampler won't
need to re-create a new generator for us."

ejguan (maintainer of torch.utils.data): "It seems that we have some tests relying on re-seeding of the
RandomSampler for each iteration. So, we probably have to drop this patch and keep it as it is."

awaelchli: "I'm struggling to understand how this change can break any existing logic. Assigning the generator to
self is going to be very useful when we want to capture the state of a random sampler."

## PR #63026 — "A re-open PR: Avoid re-creating the random number generator in RandomSampler" (merged 2021-08-16)

The same change, re-opened; approved and merged by ejguan.

vfdev-5 reported afterwards that setting `torch.manual_seed()` before each epoch no longer reproduced the order:
with 1.9.0 re-seeding gave identical batches, with the nightly it did not.

lartpang: "the instantiated generator is not controlled by `torch.manual` unless you call its own `manual_seed`
method."

## Issue #63609 — "Sampler should be seeded lazily" (ejguan)

"After #63026 is landed, the generator for Sampler is attached to the instance, which helps to serialize the state
of Sampler. But, it brings a problem that it will prevent Sampler's generator being seeded before each epoch."

    torch.manual_seed(0); l1 = list(sampler); torch.manual_seed(0); l2 = list(sampler)  # Expect same

## PR #63646 — "Convert generator in Sampler back to lazy construction" (ejguan, merged 2021-09-30)

Description: "Fixes #63609 … Revert #63026 - Sampler is expected to be re-seeded if user specify seed before each
epoch - Can not attach generator to self with `__iter__` because multiple iterators will ruin the use case"

VitalyFedyunin (reviewer): "This will badly impact all currently running iterators, consider creating two
individual iterators in test and yielding them in random order."

VitalyFedyunin: "Not going to work as intended for two or more iterators created from same object... a = Sampler()
i1 = iter(a) i2 = iter(a)"

ejguan: "Emmm, you are right. So, we have to create iter-local generator. But, then it goes back to the problem that
we can not serialize the state of this iter-local generator anymore."

ejguan: "I split the original PR into two PRs. This PR would revert Sampler back to previous state that the RNG is
created lazily. The another PR provide a new feature for potential users to serialize the iter-local generator."

## PR #65857 — the follow-up to serialize the iter-local generator

Closed without merging (stale).

## Where things stand

The code today is the state after #63646: when no generator is given, each `__iter__` creates its own generator,
seeded from the global RNG at the first `next()`. Issue #49727, still open, calls the per-iteration re-creation a bug.
