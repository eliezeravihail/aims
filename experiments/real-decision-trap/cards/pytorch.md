# Resume a shuffled epoch

When a training job is preempted and restarts in the middle of an epoch, `RandomSampler` produces a new order, so
the resumed run sees some samples twice and misses others.

Make `RandomSampler`'s order checkpointable. `sampler.state_dict()` returns a picklable dict describing where the
sampler is; `sampler.load_state_dict(state)`, called on a new `RandomSampler` over the same data, makes its next
iteration yield exactly the samples the interrupted iteration had not yet yielded, in the same order. Epochs after
that are shuffled as usual. This should work with and without replacement, and with or without a `generator`.
