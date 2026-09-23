# The record prompt — one aims session per case, frozen before it runs

`<DIR>` is a fresh aims checkout of the case (`build.sh <case> <DIR> aims`); `<DISCUSSION>` is
`discussions/pytorch-sampler.md` or `discussions/requests-session-timeout.md`, copied to
`/tmp/claude-0/rdt/discussions/`. The session is not told what feature will be requested later.

---

You maintain the code in `<DIR>` — {PT: PyTorch's `torch.utils.data` package}{RQ: the requests library} — and you
use aims to keep its design knowledge. Its Python environment is `.venv` (use `.venv/bin/python`). Work only inside
that directory, the method directory named below, and the discussion file; do not read or write anything else.

A discussion about this code took place on GitHub; it is collected in `<DISCUSSION>`. Following aims, record in
this checkout what aims says should be recorded from it, where aims says it belongs. Do not change any code or test.

Follow the `aims-guide` skill: `/tmp/claude-0/rdt/aims/skills/aims-guide/SKILL.md`. Everything it refers to is under
`/tmp/claude-0/rdt/aims/`. The anchor tool is `.aims/anchor.py`.

When you are finished, reply with the list of files you wrote and one line on each.
