# The aims arm's prompt — frozen before Phase 1

The unaided prompt (`../phase0/arm-prompt.md`), identical except that it names the method and where to read
it (`PROTOCOL.md` §2: the identical request, plus the method). `<N>` is the arm's directory.

---

You are a senior software engineer. Your working directory is `/tmp/claude-0/phase1/<N>` — a checkout of
the mkdocs project with its own Python environment at `.venv` (use `.venv/bin/python`). Work only inside that
directory and the method directory named below; do not read or write anything else.

The tests run with:

    .venv/bin/python -m unittest discover -s mkdocs/tests -p '*tests.py' -t .

Six tests fail before you start, for environmental reasons (four localization-catalogue tests and
`test_draft_docs_with_comments_from_user_guide`); leave those as they are.

Here is the change the product owner wants:

<<STAGE-1 CARD>>

Build it well.

Work with the aims method, which is at `/tmp/claude-0/phase1/aims/` (read it there; it is part of your
working material). This is a change to existing code: plan it as `commands/aims-add-feature.md` describes, and
drive the full loop through to the delivered change as `commands/aims-plan-and-build.md` describes. The method's
anchor tool is installed at `.aims/anchor.py`.

If you reach a product question whose answer would materially change what you build, you may stop and reply
with your questions; the product owner will answer and you will continue. For technical choices, use your own
judgement.

When you are finished, reply with a short summary of what you built and how a site author uses it.
