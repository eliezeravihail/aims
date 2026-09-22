# Baseline at the pinned commit
`mkdocs/mkdocs` @ `2862536793b3c67d9d83c33e0dd6d50a791928f8`, Python 3.11, installed with `pip install -e .`.

`python -m unittest discover -s mkdocs/tests -p '*tests.py' -t .` → **725 tests, 4 failures, 2 errors, 4 skipped.**

Failing at baseline (environmental — the floor excludes exactly these, and no others):

- ERROR `localization_tests.LocalizationTests.test_merge_translations`
- ERROR `localization_tests.LocalizationTests.test_translations_found`
- FAIL `localization_tests.LocalizationTests.test_jinja_extension_installed`
- FAIL `localization_tests.LocalizationTests.test_no_translations_found`
- FAIL `build_tests.BuildTests.test_draft_docs_with_comments_from_user_guide` (two parametrizations)

Re-verify on the frozen starter before Phase 0; if the list differs, the frozen list is the one that counts.
