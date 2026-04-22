#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_hook_cleanup_strategic
----------------------------

Strategic tests closing four priority targets:

1. post_gen_project hook exits non-zero raises FailedHookException with correct message
2. generate_files re-raises FailedHookException after pre_gen_project failure AND
   project_dir is removed from disk
3. generate_files re-raises FailedHookException after post_gen_project failure AND
   project_dir is removed from disk
4. Exact exit code from the subprocess is embedded in the FailedHookException message
"""

from __future__ import unicode_literals

import os
import stat

import pytest

from cookiecutter import hooks, utils, exceptions, generate


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_failing_hook_repo(tmp_path, hook_name, exit_code=1):
    """
    Build a minimal repo directory containing:
      hooks/<hook_name>.py  — Python script that exits with *exit_code*
      input{{cookiecutter.project_slug}}/  — empty template directory

    Returns the repo path (str).
    """
    repo = tmp_path / "repo"
    hooks_dir = repo / "hooks"
    template_dir = repo / "input{{cookiecutter.project_slug}}"

    hooks_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)

    hook_script = hooks_dir / "{}.py".format(hook_name)
    hook_script.write_text(
        "#!/usr/bin/env python\n"
        "import sys\n"
        "sys.exit({})\n".format(exit_code)
    )

    # Add a placeholder file so the template directory is non-empty
    (template_dir / "README.md").write_text("# placeholder\n")

    return str(repo)


def _make_repo_with_failing_post_gen(tmp_path, exit_code=1):
    """
    Repo whose pre_gen_project succeeds (exits 0) and whose
    post_gen_project fails (exits *exit_code*).
    """
    repo = tmp_path / "repo"
    hooks_dir = repo / "hooks"
    template_dir = repo / "input{{cookiecutter.project_slug}}"

    hooks_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)

    (hooks_dir / "pre_gen_project.py").write_text(
        "#!/usr/bin/env python\nimport sys\nsys.exit(0)\n"
    )
    (hooks_dir / "post_gen_project.py").write_text(
        "#!/usr/bin/env python\nimport sys\nsys.exit({})\n".format(exit_code)
    )
    (template_dir / "README.md").write_text("# placeholder\n")

    return str(repo)


# ---------------------------------------------------------------------------
# Target 1 — post_gen_project hook exits non-zero raises FailedHookException
#             with correct message
# ---------------------------------------------------------------------------

def test_post_gen_project_hook_exits_nonzero_raises_FailedHookException_with_correct_message(tmp_path):
    """
    run_hook('post_gen_project', …) must raise FailedHookException and the
    exception message must contain 'Hook script failed'.
    """
    repo = _make_failing_hook_repo(tmp_path, "post_gen_project", exit_code=1)
    project_dir = str(tmp_path / "output")
    os.makedirs(project_dir)

    with utils.work_in(repo):
        with pytest.raises(exceptions.FailedHookException) as excinfo:
            hooks.run_hook("post_gen_project", project_dir, {})

    assert "Hook script failed" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Target 4 — Exact exit code from the subprocess is embedded in the message
# ---------------------------------------------------------------------------

def test_exact_exit_code_from_subprocess_is_embedded_in_FailedHookException_message(tmp_path):
    """
    The exit code the hook script returns must appear verbatim in the
    FailedHookException message so callers can surface the precise failure.
    """
    exit_code = 42
    repo = _make_failing_hook_repo(tmp_path, "pre_gen_project", exit_code=exit_code)
    project_dir = str(tmp_path / "output")
    os.makedirs(project_dir)

    with utils.work_in(repo):
        with pytest.raises(exceptions.FailedHookException) as excinfo:
            hooks.run_hook("pre_gen_project", project_dir, {})

    assert str(exit_code) in str(excinfo.value)


# ---------------------------------------------------------------------------
# Target 2 — generate_files re-raises FailedHookException after
#             pre_gen_project failure AND project_dir is removed from disk
# ---------------------------------------------------------------------------

def test_generate_files_pre_gen_project_failure_reraises_and_project_dir_removed(tmp_path):
    """
    When pre_gen_project exits non-zero:
      • generate_files must re-raise FailedHookException
      • the partially-created project_dir must be absent from disk afterwards
    """
    repo = _make_failing_hook_repo(tmp_path, "pre_gen_project", exit_code=1)
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)

    context = {"cookiecutter": {"project_slug": "myproject"}}

    with pytest.raises(exceptions.FailedHookException):
        generate.generate_files(
            repo_dir=repo,
            context=context,
            output_dir=output_dir,
        )

    # The project directory must have been cleaned up
    expected_project_dir = os.path.join(output_dir, "myproject")
    assert not os.path.exists(expected_project_dir), (
        "project_dir '{}' should have been removed after pre_gen_project failure"
        .format(expected_project_dir)
    )


# ---------------------------------------------------------------------------
# Target 3 — generate_files re-raises FailedHookException after
#             post_gen_project failure AND project_dir is removed from disk
# ---------------------------------------------------------------------------

def test_generate_files_post_gen_project_failure_reraises_and_project_dir_removed(tmp_path):
    """
    When post_gen_project exits non-zero:
      • generate_files must re-raise FailedHookException
      • the generated project_dir must be absent from disk afterwards
    """
    repo = _make_repo_with_failing_post_gen(tmp_path, exit_code=1)
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)

    context = {"cookiecutter": {"project_slug": "myproject"}}

    with pytest.raises(exceptions.FailedHookException):
        generate.generate_files(
            repo_dir=repo,
            context=context,
            output_dir=output_dir,
        )

    expected_project_dir = os.path.join(output_dir, "myproject")
    assert not os.path.exists(expected_project_dir), (
        "project_dir '{}' should have been removed after post_gen_project failure"
        .format(expected_project_dir)
    )
