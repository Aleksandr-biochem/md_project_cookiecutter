"""Integration tests for baking the Cookiecutter template."""

from pathlib import Path

from cookiecutter.main import cookiecutter


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
    """Bake a project with slow virtual-environment creation disabled."""
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
    """Bake the template and verify its core file/directory structure."""
    project_path = bake_project(tmp_path, project_name="example_md_project")

    assert project_path.name == "example_md_project"
    assert project_path.is_dir()

    generated_directories = {
        path.name for path in project_path.iterdir() if path.is_dir()
    }
    assert EXPECTED_PROJECT_DIRECTORIES <= generated_directories

    expected_files = {
        project_path / ".gitignore",
        project_path / "README.md",
        project_path / "requirements.txt",
        project_path / "simulation_setup_and_analysis.ipynb",
        project_path / "scripts" / "postprocess_trjs.sh",
        project_path / "simulations" / "assemble_and_run.py",
    }
    assert all(path.is_file() for path in expected_files)

    assert not list(project_path.rglob("__placeholder_file__"))
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
