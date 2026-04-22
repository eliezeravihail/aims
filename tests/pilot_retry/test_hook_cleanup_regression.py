"""Regression: generate_files must remove project_dir if a hook fails."""
import os
import pytest
from cookiecutter import generate, exceptions
from pathlib import Path


def _make_repo(root: Path):
    repo = root / "template"
    (repo / "hooks").mkdir(parents=True)
    (repo / "{{cookiecutter.project_name}}").mkdir()
    (repo / "{{cookiecutter.project_name}}" / "README.md").write_text("{{cookiecutter.project_name}}\n")
    (repo / "cookiecutter.json").write_text('{"project_name": "demo"}')
    # Failing pre_gen hook
    hook = repo / "hooks" / "pre_gen_project.py"
    hook.write_text("#!/usr/bin/env python\nimport sys; sys.exit(1)\n")
    return repo


def test_project_dir_removed_on_pre_gen_failure(tmp_path):
    repo = _make_repo(tmp_path)
    out = tmp_path / "out"; out.mkdir()
    with pytest.raises(exceptions.FailedHookException):
        generate.generate_files(repo_dir=str(repo), context={"cookiecutter": {"project_name": "demo"}},
                                output_dir=str(out))
    project_dir = out / "demo"
    assert not project_dir.exists(), f"partial project dir was left behind at {project_dir}"
