"""Unit tests for the Cookiecutter post-generation hooks."""

from pathlib import Path
import subprocess
from typing import cast

import pytest

from hooks import post_gen_project


def test_post_gen_hook_records_success(capsys: pytest.CaptureFixture[str]) -> None:
    """A successful hook stores its code and reports a passing status."""

    def successful_hook() -> int:
        return 0

    hook = post_gen_project.PostGenHook(successful_hook)
    hook.run()

    output = capsys.readouterr().out
    assert hook.return_code == 0
    assert "successful_hook" in output
    assert "PASSED" in output


def test_post_gen_hook_rejects_non_integer_return_code() -> None:
    """Hook functions must honour the integer return-code contract."""

    def invalid_hook() -> int:
        return cast(int, "success")

    hook = post_gen_project.PostGenHook(invalid_hook)

    with pytest.raises(ValueError, match="Integer return code expected"):
        hook.run()


def test_cleanup_files_removes_nested_placeholders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cleanup removes placeholder files recursively and leaves real files."""
    nested_dir = tmp_path / "data" / "nested"
    nested_dir.mkdir(parents=True)
    placeholder = nested_dir / "__placeholder_file__"
    placeholder.touch()
    real_file = nested_dir / "keep.txt"
    real_file.write_text("keep me", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    return_code = post_gen_project.cleanup_files()

    assert return_code == 0
    assert not placeholder.exists()
    assert real_file.read_text(encoding="utf-8") == "keep me"


def test_create_venv_without_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Creating a venv succeeds without invoking pip when requirements are absent."""
    create_calls: list[tuple[str, bool]] = []

    def fake_venv_create(env_dir: str, with_pip: bool) -> None:
        create_calls.append((env_dir, with_pip))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", fake_venv_create)

    return_code = post_gen_project.create_venv()

    assert return_code == 0
    assert create_calls == [(str(tmp_path / "venv"), True)]


def test_create_venv_returns_failure_when_creation_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An exception from venv creation produces a failing hook return code."""

    def failing_venv_create(env_dir: str, with_pip: bool) -> None:
        assert env_dir == str(tmp_path / "venv")
        assert with_pip is True
        raise OSError("venv unavailable")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", failing_venv_create)

    assert post_gen_project.create_venv() == 1


def test_create_venv_installs_requirements_and_lists_packages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A requirements file triggers pip install followed by pip list."""
    requirements_file = tmp_path / "requirements.txt"
    requirements_file.write_text("example-package\n", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_venv_create(env_dir: str, with_pip: bool) -> None:
        assert env_dir == str(tmp_path / "venv")
        assert with_pip is True

    def fake_run(
        command: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        commands.append(command)
        assert check is False
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", fake_venv_create)
    monkeypatch.setattr(post_gen_project.subprocess, "run", fake_run)

    return_code = post_gen_project.create_venv()

    assert return_code == 0
    assert len(commands) == 2
    assert commands[0][-3:] == ["install", "-r", str(requirements_file)]
    assert commands[1][-3:] == ["-m", "pip", "list"]


def test_create_venv_propagates_pip_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed requirements installation makes the hook fail."""
    (tmp_path / "requirements.txt").write_text("example-package\n", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_venv_create(env_dir: str, with_pip: bool) -> None:
        assert env_dir == str(tmp_path / "venv")
        assert with_pip is True

    def fake_run(
        command: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        commands.append(command)
        assert check is False
        return subprocess.CompletedProcess(command, returncode=17)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", fake_venv_create)
    monkeypatch.setattr(post_gen_project.subprocess, "run", fake_run)

    return_code = post_gen_project.create_venv()

    assert return_code == 17
    assert len(commands) == 1
    assert commands[0][-3:] == ["install", "-r", str(tmp_path / "requirements.txt")]


def test_git_init_returns_subprocess_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Git initialisation returns Git's process exit code unchanged."""

    def fake_run(
        command: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        assert command == ["git", "init"]
        assert check is False
        return subprocess.CompletedProcess(command, returncode=3)

    monkeypatch.setattr(post_gen_project.subprocess, "run", fake_run)

    assert post_gen_project.git_init() == 3


def test_protocol_reports_pass_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Protocol state is false before execution and true after successful hooks."""
    protocol = post_gen_project.PostGenProtocol()
    monkeypatch.chdir(tmp_path)

    assert protocol.return_codes() == [None]
    assert protocol.all_passed() is False

    protocol.run()

    assert protocol.return_codes() == [0]
    assert protocol.all_passed() is True
