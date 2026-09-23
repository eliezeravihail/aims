# Run notes — in the order things happened

- Package frozen and pushed (`ff37714`) before any session ran.
- Launched together: the three C sessions of each case and the two record sessions.
- **Records filed** (frozen in `records/`, copied unchanged into every A checkout at the path the session chose):
  PyTorch → `torch/utils/data/sampler.py.md`; requests → `src/requests/sessions.py.md`. Each session wrote only
  that one companion, anchored, and changed no code.
- **requests gate passed** on rq-c1 (violated: `Session.timeout`). By the gate rule (stop only if C respects 3 of
  3), one violation settles it; requests' A and B sessions were launched then, while rq-c2 and rq-c3 still ran.
- Every A and B checkout was built before the record was read by anyone but the experimenter, with `build.sh`.
- **PyTorch gate: not passed.** pt-c1, pt-c2, pt-c3 all respected the decision (probe T0–T3 pass on each). By the
  frozen rule, A and B were not run for PyTorch; their checkouts had been built in advance and were never used.
- pt-c1 finished its work and asked a scope question at hand-back; it was probed as handed back
  (`probe-results/pt-c1-before-answer.txt`), answered with the card's sentences, changed nothing, and probed again
  (`probe-results/pt-c1.txt`) — the same result.
- Three answers were sent while the session was still running ("queued for delivery"); each session acknowledged
  the answer in its final reply.
- Every arm's full change is in `diffs/` (the `.aims/state.md` of aims arms included); `replies/` summarizes each
  final reply; `snippets/` holds the requests floor snippets, written from each reply's usage line.
