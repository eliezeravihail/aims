#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
tests/test_hook_regression_lean.py
-----------------------------------

Regression tests for the hook failure contract:
  - FailedHookException is raised (not silently swallowed).
  - Exception message includes the non-zero exit code.
  - post_gen_project failure cleans up the generated project directory.
  - pre_gen_project failure cleans up the generated project directory.
"""

import os
import pytest

from cookiecutter import exceptions, generate, hooks, utils


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_failing_hook(hooks_dir, hook_name, exit_code=1):
    """Write a Python hook that exits with *exit_code*."""
    hook_path = os.path.join(hooks_dir, hook_name + ".py")
    with open(hook_path, "w") as fh:
        fh.write("#!/usr/bin/env python\n")
        fh.write("import sys; sys.exit({0})\n".format(exit_code))
    return hook_path


def _make_passing_hook(hooks_dir, hook_name):
    """Write a Python hook that exits successfully."""
    hook_path = os.path.join(hooks_dir, hook_name + ".py")
    with open(hook_path, "w") as fh:
        fh.write("#!/usr/bin/env python\n")
        fh.write("import sys; sys.exit(0)\n")
    return hook_path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo_with_failing_post_hook(tmp_path):
    """
    A minimal cookiecutter repo whose post_gen_project hook exits non-zero.

    Layout::

        <tmp_path>/
          repo/
            cookiecutter.json
            {{cookiecutter.project_name}}/
              README.txt
            hooks/
              post_gen_project.py   <- exits 2
    """
    repo = tmp_path / "repo"
    template_dir = repo / "{{cookiecutter.project_name}}"
    hooks_dir = repo / "hooks"
    output_dir = tmp_path / "output"

    for d in (template_dir, hooks_dir, output_dir):
        d.mkdir(parents=True)

    (repo / "cookiecutter.json").write_text('{"project_name": "myproject"}')
    (template_dir / "README.txt").write_text("hello\n")
    _make_failing_hook(str(hooks_dir), "post_gen_project", exit_code=2)

    return {"repo": str(repo), "output": str(output_dir)}


@pytest.fixture()
def repo_with_failing_pre_hook(tmp_path):
    """
    A minimal cookiecutter repo whose pre_gen_project hook exits non-zero.
    """
    repo = tmp_path / "repo"
    template_dir = repo / "{{cookiecutter.project_name}}"
    hooks_dir = repo / "hooks"
    output_dir = tmp_path / "output"

    for d in (template_dir, hooks_dir, output_dir):
        d.mkdir(parents=True)

    (repo / "cookiecutter.json").write_text('{"project_name": "myproject"}')
    (template_dir / "README.txt").write_text("hello\n")
    _make_failing_hook(str(hooks_dir), "pre_gen_project", exit_code=3)

    return {"repo": str(repo), "output": str(output_dir)}


# ---------------------------------------------------------------------------
# Test (a): post_gen_project failure cleans up the project directory
# ---------------------------------------------------------------------------

def test_post_gen_failure_removes_project_dir(repo_with_failing_post_hook):
    """
    When post_gen_project exits non-zero the partially-generated project dir
    must be removed and FailedHookException must propagate.
    """
    info = repo_with_failing_post_hook
    context = {"cookiecutter": {"project_name": "myproject"}}

    with pytest.raises(exceptions.FailedHookException):
        generate.generate_files(
            repo_dir=info["repo"],
            context=context,
            output_dir=info["output"],
        )

    expected_project_dir = os.path.join(info["output"], "myproject")
    assert not os.path.exists(expected_project_dir), (
        "Project directory was not cleaned up after post_gen_project failure"
    )


# ---------------------------------------------------------------------------
# Test (b): exception message includes the non-zero exit code
# ---------------------------------------------------------------------------

def test_failed_hook_exception_message_includes_exit_code(tmp_path):
    """
    FailedHookException message must contain the numeric exit code so that
    callers can surface actionable information.
    """
    hooks_dir = tmp_path / "tests-hooks" / "hooks"
    project_dir = tmp_path / "tests-hooks" / "input{{dummy}}"

    hooks_dir.mkdir(parents=True)
    project_dir.mkdir(parents=True)

    _make_failing_hook(str(hooks_dir), "pre_gen_project", exit_code=42)

    with utils.work_in(str(tmp_path / "tests-hooks")):
        with pytest.raises(exceptions.FailedHookException) as exc_info:
            hooks.run_hook("pre_gen_project", str(project_dir), {})

    assert "42" in str(exc_info.value), (
        "FailedHookException message should contain the exit code '42'"
    )


# ---------------------------------------------------------------------------
# Test (c): pre_gen_project failure also cleans up the project directory
# ---------------------------------------------------------------------------

def test_pre_gen_failure_removes_project_dir(repo_with_failing_pre_hook):
    """
    When pre_gen_project exits non-zero the project dir that was created before
    the hook ran must be removed and FailedHookException must propagate.
    """
    info = repo_with_failing_pre_hook
    context = {"cookiecutter": {"project_name": "myproject"}}

    with pytest.raises(exceptions.FailedHookException):
        generate.generate_files(
            repo_dir=info["repo"],
            context=context,
            output_dir=info["output"],
        )

    expected_project_dir = os.path.join(info["output"], "myproject")
    assert not os.path.exists(expected_project_dir), (
        "Project directory was not cleaned up after pre_gen_project failure"
    )


# ---------------------------------------------------------------------------
# Test (d): successful hooks do NOT raise and project dir is kept
# ---------------------------------------------------------------------------

def test_passing_hooks_do_not_raise(tmp_path):
    """
    Sanity-check: if both hooks exit 0 no exception is raised and the
    project directory is left in place.
    """
    repo = tmp_path / "repo"
    template_dir = repo / "{{cookiecutter.project_name}}"
    hooks_dir = repo / "hooks"
    output_dir = tmp_path / "output"

    for d in (template_dir, hooks_dir, output_dir):
        d.mkdir(parents=True)

    (repo / "cookiecutter.json").write_text('{"project_name": "myproject"}')
    (template_dir / "README.txt").write_text("hello\n")
    _make_passing_hook(str(hooks_dir), "pre_gen_project")
    _make_passing_hook(str(hooks_dir), "post_gen_project")

    context = {"cookiecutter": {"project_name": "myproject"}}
    result = generate.generate_files(
        repo_dir=str(repo),
        context=context,
        output_dir=str(output_dir),
    )

    assert result is not None
    assert os.path.exists(result), "Project dir should exist when hooks succeed"


# ---------------------------------------------------------------------------
# Test (e): FailedHookException is a CookiecutterException subclass
# ---------------------------------------------------------------------------

def test_failed_hook_exception_is_cookiecutter_exception():
    """
    FailedHookException must be a subclass of CookiecutterException so that
    callers that catch the base class still handle it correctly.
    """
    assert issubclass(
        exceptions.FailedHookException,
        exceptions.CookiecutterException,
    )
