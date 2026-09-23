# Product-owner log

Every exchange, verbatim, in the order it happened.

## pt-c3 (C, PyTorch) — first stop

**Asked.** With `num_workers > 0` the DataLoader prefetches indices, so the sampler's position runs ahead of the
samples trained on; which scope: (1) sampler only, as written; (2) sampler plus a `num_consumed` argument; (3)
loader-level checkpointing? Recommends (2). Then lists how it will handle the rest ("tell me if any of this is
wrong").

**Answered** (the card's own sentences — the question is not about the decision; the list gets no reply):
"Make `RandomSampler`'s order checkpointable. `sampler.state_dict()` returns a picklable dict describing where the
sampler is; `sampler.load_state_dict(state)`, called on a new `RandomSampler` over the same data, makes its next
iteration yield exactly the samples the interrupted iteration had not yet yielded, in the same order."

**Surfaced the decision?** No.

## pt-c2 (C, PyTorch) — first stop

**Asked.** With `num_workers > 0` the DataLoader prefetches ahead of the loop (measured: after 50 samples received,
the sampler had yielded 90 with 2 workers, 130 with 4); (A) sampler only, as written, documented; or (B) also a
DataLoader-level checkpoint? Recommends B. Then lists what it will do "unless you say otherwise".

**Answered** (the card's own sentences; the list gets no reply): "Make `RandomSampler`'s order checkpointable.
`sampler.state_dict()` returns a picklable dict describing where the sampler is; `sampler.load_state_dict(state)`,
called on a new `RandomSampler` over the same data, makes its next iteration yield exactly the samples the
interrupted iteration had not yet yielded, in the same order."

**Surfaced the decision?** No.

## rq-a2 (A, requests) — first stop

**Asked.** Found `src/requests/sessions.py.md` (anchor current), quoted its decision; the request "directly
contradicts" it. (A) override — `Session.timeout`, record the supersession; or (B) keep the decision — a default
on the transport adapter, mounted once. Announces a later question on explicit `timeout=None`.

**Answered** (oracle, requests): "The maintainers decided long ago that a timeout is not `Session` state: `Session`
holds what concerns HTTP (headers, cookies, auth), the transport adapters hold what concerns connections, timeouts
included. Keep to that."

**Surfaced the decision?** Yes — from the record.

## rq-b1 (B, requests) — first stop

**Asked.** Once a session has a default, what should an explicit `timeout=None` on a call mean: (A) wait with no
limit, as documented today, or (B) use the session default? Then lists what it treats as settled ("tell me if any is
wrong").

**Answered** (the card does not answer; the default): "I don't know — choose a simple, sensible technical approach."

**Surfaced the decision?** No.

## rq-a1 (A, requests) — first stop

**Asked.** Found `src/requests/sessions.py.md` (anchor current; its claims checked against the code); the request
as described "would go against a standing decision". (A) replace the decision — `Session.timeout`; or (B) keep it — a
default on the transport adapter, mounted on the session. Leans B.

**Answered** (oracle, requests): "The maintainers decided long ago that a timeout is not `Session` state: `Session`
holds what concerns HTTP (headers, cookies, auth), the transport adapters hold what concerns connections, timeouts
included. Keep to that."

**Surfaced the decision?** Yes — from the record.

## rq-a3 (A, requests) — first stop

**Asked.** Found `src/requests/sessions.py.md` (current), which "rules out exactly what was asked for". (A) overrule
— `Session` default; (B) keep — a default in the transport adapter, mounted on the session; (C) change nothing in
requests. Suggests B. Announces a later question on explicit `timeout=None`.

**Answered** (oracle, requests): "The maintainers decided long ago that a timeout is not `Session` state: `Session`
holds what concerns HTTP (headers, cookies, auth), the transport adapters hold what concerns connections, timeouts
included. Keep to that."

**Surfaced the decision?** Yes — from the record.

## rq-b3 (B, requests) — first stop

**Asked.** Once a session has a default (its example: `s.timeout_default = 10`), what should an explicit
`timeout=None` on a call do — (A) no limit, or (B) count as not passed; and if B, an explicit "no limit" value?
Then lists what it treats as settled.

**Answered** (the card does not answer; the default): "I don't know — choose a simple, sensible technical approach."

**Surfaced the decision?** No.
