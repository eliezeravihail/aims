"""Regression test for: hook script failure should raise FailedHookException."""
import os
import pytest
from cookiecutter import hooks, utils, exceptions


@pytest.fixture
def repo_path(tmp_path):
    hooks_dir = tmp_path / "tests-hooks" / "hooks"
    hooks_dir.mkdir(parents=True)
    (tmp_path / "tests-hooks" / "input{{hooks}}").mkdir(parents=True)
    yield str(tmp_path / "tests-hooks")


def test_run_failing_hook(repo_path):
    hook_path = os.path.join(repo_path, "hooks", "pre_gen_project.py")
    tests_dir  = os.path.join(repo_path, "input{{hooks}}")

    with open(hook_path, "w") as f:
        f.write("#!/usr/bin/env python\n")
        f.write("import sys; sys.exit(1)\n")

    with utils.work_in(repo_path):
        with pytest.raises(exceptions.FailedHookException) as excinfo:
            hooks.run_hook("pre_gen_project", tests_dir, {})
        assert "Hook script failed" in str(excinfo.value)
