# Run notes — in the order things happened

- Package frozen and pushed (`ff37714`) before any session ran.
- Launched together: the three C sessions of each case and the two record sessions.
- **Records filed** (frozen in `records/`, copied unchanged into every A checkout at the path the session chose):
  PyTorch → `torch/utils/data/sampler.py.md`; requests → `src/requests/sessions.py.md`. Each session wrote only
  that one companion, anchored, and changed no code.
- **requests gate passed** on rq-c1 (violated: `Session.timeout`). By the gate rule (stop only if C respects 3 of
  3), one violation settles it; requests' A and B sessions were launched then, while rq-c2 and rq-c3 still ran.
- Every A and B checkout was built before the record was read by anyone but the experimenter, with `build.sh`.
