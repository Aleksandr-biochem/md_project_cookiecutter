"""Integration tests for baking the Cookiecutter template.
This module tests both execution without a wrapper and with bake_md_project.py wrapper."""

from pathlib import Path
from typing import cast

import pytest

from cookiecutter.main import cookiecutter
import bake_md_project

CookiecutterArg = str | list[str] | bool

#### COOKIECUTTER TEST WITHOUT WRAPPER ####

EXPECTED_PROJECT_DIRECTORIES = {
    "analysis",
    "data",
    "plots",
    "scripts",
    "simulations",
}


def bake_project(
    tmp_path: Path,
    *,
    project_name: str,
    run_git_init: bool = False,
) -> Path:
    """Bake a project with slow virtual environment creation disabled."""
    output_dir = tmp_path / "baked"
    output_dir.mkdir()

    generated_path = cookiecutter(
        str(Path(__file__).parents[1]),
        no_input=True,
        output_dir=str(output_dir),
        extra_context={
            "project_name": project_name,
            "author": "Test Author",
            "create_venv": False,
            "run_git_init": run_git_init,
        },
    )

    return Path(generated_path)


def test_bake_project(tmp_path: Path) -> None:
    """Test baking a template and verify its core file/directory structure."""
    project_path = bake_project(tmp_path, project_name="example_md_project")

    assert project_path.name == "example_md_project"
    assert project_path.is_dir()

    generated_directories = {
        path.name for path in project_path.iterdir() if path.is_dir()
    }
    assert EXPECTED_PROJECT_DIRECTORIES <= generated_directories

    # check SOME expected files
    expected_files = {
        project_path / ".gitignore",
        project_path / "README.md",
        project_path / "requirements.txt",
        project_path / "simulation_setup_and_analysis.ipynb",
        project_path / "scripts" / "postprocess_trjs.sh",
        project_path / "scripts" / "assemble_simulations.py",
    }
    assert all(path.is_file() for path in expected_files)

    assert not list(project_path.rglob("__placeholder_file__"))
    # both venv and git init were disabled
    assert not (project_path / "venv").exists()
    assert not (project_path / ".git").exists()


def test_bake_project_can_initialise_git(tmp_path: Path) -> None:
    """Enable only the Git hook and verify that it creates a repository."""
    project_path = bake_project(
        tmp_path,
        project_name="git_enabled_project",
        run_git_init=True,
    )

    assert (project_path / ".git").is_dir()
    assert not (project_path / "venv").exists()


#### COOKIECUTTER TEST WITH bake_md_project.py WRAPPER ####


def test_bake_project_wrapper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test wrapper script workflow"""

    # patch interactive questionary UI
    selections = {
        "force_fields": ["martini_v2.2.ff", "martini_v3.0.0.ff"],
        "mdp_templates": ["CG_mdp_template", "AA_mdp_template"],
    }

    def _fake_select_template_dirs(
        group_name: str, available_dirs: list[str]
    ) -> list[str]:
        """Patch for the questionary selections"""
        return selections[group_name]

    monkeypatch.setattr(
        bake_md_project,
        "select_template_dirs",
        _fake_select_template_dirs,
    )

    # to avoid cookiecutter prompting, wrap the cookiecutter call with test-specific options
    real_cookiecutter = bake_md_project.cookiecutter  # type: ignore[attr-defined]

    def _test_cookiecutter(
        template: str, *, extra_context: dict[str, CookiecutterArg]
    ) -> str:
        return cast(
            str,
            real_cookiecutter(
                template,
                no_input=True,
                output_dir=str(tmp_path),
                extra_context={
                    "project_name": "wrapper_test",
                    "author": "Test Author",
                    "create_venv": False,
                    "run_git_init": False,
                },
            ),
        )

    monkeypatch.setattr(
        bake_md_project,
        "cookiecutter",
        _test_cookiecutter,
    )

    assert bake_md_project.main() == 0

    project_dir = tmp_path / "wrapper_test"
    assert project_dir.exists()

    # check selected files/directories and sopme othe files
    for group_name, template_dirs in selections.items():
        for template_dir in template_dirs:
            assert (project_dir / "simulations" / group_name / template_dir).exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "scripts").exists()
