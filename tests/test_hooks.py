"""Unit tests for the Cookiecutter post-generation hooks."""

from pathlib import Path
import subprocess
from typing import cast

import pytest

from hooks import post_gen_project

##### TEST HOOK CLASSES LOGIC #####


def test_post_gen_hook_pass(capsys: pytest.CaptureFixture[str]) -> None:
    """A successful hook stores its code and reports a passing status."""

    def successful_hook() -> int:
        """Minimal valid hook emulation"""
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
        """Minimal hook emulation with invalid returncode"""
        return cast(int, "success")

    hook = post_gen_project.PostGenHook(invalid_hook)

    with pytest.raises(ValueError, match="Integer return code expected"):
        hook.run()


@pytest.mark.parametrize(
    "hook_return_codes, expected_all_passed",
    [([0, 0], True), ([0, 1, 0], False), ([], True)],
)
def test_post_gen_protocol_run(
    hook_return_codes: list[int],
    expected_all_passed: bool,
) -> None:
    """Test PostGenProtocol run, state is false before execution and true after successful hooks.
    NOTE empty hook list runs without complains"""
    # protocol with dummy hooks
    protocol = post_gen_project.PostGenProtocol(
        [
            post_gen_project.PostGenHook(
                cast(post_gen_project.HookFunction, lambda ret_code=ret_code: ret_code)
            )
            for ret_code in hook_return_codes
        ]
    )

    assert protocol.return_codes() == [None] * len(hook_return_codes)
    assert protocol.all_passed() is (False if len(hook_return_codes) > 0 else True)

    protocol.run()

    assert protocol.return_codes() == hook_return_codes
    assert protocol.all_passed() is expected_all_passed


@pytest.mark.parametrize(
    "invalid_hook_input",
    [
        [post_gen_project.PostGenHook(lambda: 0), lambda: 0],
        (
            post_gen_project.PostGenHook(lambda: 0),
            post_gen_project.PostGenHook(lambda: 1),
        ),
    ],
)
def test_post_gen_protocol_raises(invalid_hook_input: list[object]) -> None:
    """Test that PostGenProtocol raises with incorrect input"""
    with pytest.raises(ValueError, match=r"`protocol` expected list\[PostGenHook\]"):
        post_gen_project.PostGenProtocol(
            cast(list[post_gen_project.PostGenHook], invalid_hook_input)
        )


###### TEST HOOK FUNCTIONS #####


def test_cleanup_files_removes_nested_placeholders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cleanup removes placeholder files recursively and leaves real files."""
    nested_dir = tmp_path / "data" / "nested"
    nested_dir.mkdir(parents=True)
    placeholder = nested_dir / "__placeholder_file__"
    placeholder.touch()
    other_placeholder = tmp_path / "data" / "__placeholder_file__"
    other_placeholder.touch()
    real_file = nested_dir / "keep.txt"
    real_file.write_text("keep me", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    return_code = post_gen_project.cleanup_files()

    assert return_code == 0
    assert not placeholder.exists()
    assert not other_placeholder.exists()
    assert real_file.read_text(encoding="utf-8") == "keep me"


def test_create_venv_without_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Creating a venv succeeds without invoking pip when requirements are absent."""
    create_calls: list[tuple[str, bool]] = []

    def _fake_venv_create(env_dir: str, with_pip: bool) -> None:
        """Fake venv.create call"""
        create_calls.append((env_dir, with_pip))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", _fake_venv_create)  # type: ignore[attr-defined]

    return_code = post_gen_project.create_venv()

    assert return_code == 0
    assert create_calls == [(str(tmp_path / "venv"), True)]


def test_create_venv_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An exception from venv creation produces a failing hook return code."""

    def _failing_venv_create(env_dir: str, with_pip: bool) -> None:
        """Fake venv.create call producing failure"""
        raise OSError("venv unavailable")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", _failing_venv_create)  # type: ignore[attr-defined]

    assert post_gen_project.create_venv() == 1


def test_create_venv_installs_requirements_and_lists_packages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that requirements.txt file triggers pip install followed by pip list."""
    (tmp_path / "requirements.txt").write_text("example-package\n", encoding="utf-8")
    commands: list[list[str]] = []

    def _fake_venv_create(env_dir: str, with_pip: bool) -> None:
        """Fake venv.create call"""
        assert env_dir == str(tmp_path / "venv")
        assert with_pip is True

    def _fake_run(
        command: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        """Patch for a fake subprocess run"""
        commands.append(command)
        assert check is False
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", _fake_venv_create)  # type: ignore[attr-defined]
    monkeypatch.setattr(post_gen_project.subprocess, "run", _fake_run)  # type: ignore[attr-defined]

    return_code = post_gen_project.create_venv()

    assert return_code == 0
    assert len(commands) == 2
    assert commands[0][-3:] == ["install", "-r", str(tmp_path / "requirements.txt")]
    assert commands[1][-3:] == ["-m", "pip", "list"]


def test_create_venv_propagates_pip_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that failed requirements installation makes the hook fail."""
    (tmp_path / "requirements.txt").write_text("example-package\n", encoding="utf-8")
    commands: list[list[str]] = []

    def _fake_venv_create(env_dir: str, with_pip: bool) -> None:
        """Fake venv.create call"""
        assert env_dir == str(tmp_path / "venv")
        assert with_pip is True

    def _fake_run(
        command: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        """Patch for a fake failing subprocess run"""
        commands.append(command)
        assert check is False
        return subprocess.CompletedProcess(command, returncode=17)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(post_gen_project.venv, "create", _fake_venv_create)  # type: ignore[attr-defined]
    monkeypatch.setattr(post_gen_project.subprocess, "run", _fake_run)  # type: ignore[attr-defined]

    return_code = post_gen_project.create_venv()

    assert return_code == 17
    assert len(commands) == 1
    assert commands[0][-3:] == ["install", "-r", str(tmp_path / "requirements.txt")]


def test_git_init_returns_subprocess_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Some test for git hook. Git initialisation returns Git's process exit code unchanged.
    NOTE Might need improvement if this hook is developed further."""

    def _fake_run(
        command: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        assert command == ["git", "init"]
        assert check is False
        return subprocess.CompletedProcess(command, returncode=3)

    monkeypatch.setattr(post_gen_project.subprocess, "run", _fake_run)  # type: ignore[attr-defined]

    assert post_gen_project.git_init() == 3
