#!/usr/bin/env python
"""Post-generation hooks to do the following:

- Remove any '__placeholder_file__'
- Run venv ro create a new environment
- Run git init in the new project folder
"""

import venv
import subprocess
from pathlib import Path

from collections.abc import Callable


HookFunction = Callable[[], int]


class BColors:
    """ANSI colours used by the hook status output."""

    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


class PostGenHook:
    """Protocol for the post-generation hook from a Callable[[None], int]
    TODO can be a general hook logic both for pre- and post-gen"""

    def __init__(self, hook: HookFunction):
        self.hook = hook
        self.return_code: int | None = None

    def run(self) -> None:
        """Run the hook and record the return code. Raise if non-integer return code"""
        return_code = self.hook()
        if not isinstance(return_code, int):
            raise ValueError(
                f"Integer return code expected, got {type(return_code)} from {self.hook}"
            )

        # log hook execution
        # TODO improve logic of handling raised exceptions and reporitng them
        hook_name = self.hook.__name__
        status = (
            f"{BColors.OKGREEN}PASSED{BColors.ENDC}"
            if return_code == 0
            else f"{BColors.FAIL}FAILED{BColors.ENDC}"
        )
        print(f"{hook_name}{'.' * (50 - len(hook_name))}{status}")

        self.return_code = return_code
        return


def cleaunup_files() -> int:
    """Cleanup any auxilliary or intermediate files from the new project.
    Return int return code, 0 or 1"""
    project_dir = Path.cwd()
    for path in project_dir.rglob("__placeholder_file__"):
        if path.is_file():
            path.unlink()

    placeholders_left = any(
        path.is_file() for path in project_dir.rglob("__placeholder_file__")
    )
    return 1 if placeholders_left else 0


def create_venv() -> int:
    """Create ``venv`` and install ``requirements.txt`` when it is present."""
    project_dir = Path.cwd()
    venv_dir = project_dir / "venv"

    print(f"Running venv create {venv_dir}...")
    try:
        venv.create(str(venv_dir), with_pip=True)
    except Exception as exc:
        print(f"Virtual environment creation failed: {exc}")
        return 1

    requirements_file = project_dir / "requirements.txt"
    if not requirements_file.is_file():
        print("Checked for requirements.txt, none found. Leaving an empty venv.")
        return 0

    # NOTE Only account for Unix-like systems
    python_executable = venv_dir / "bin/python"
    print("Detected requirements.txt, running `pip install -r requirements.txt`...")
    install_result = subprocess.run(
        [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
        ],
        check=False,
    )
    if install_result.returncode != 0:
        return install_result.returncode

    print("\npip list:")
    list_result = subprocess.run(
        [str(python_executable), "-m", "pip", "list"],
        check=False,
    )
    return list_result.returncode


def git_init() -> int:
    """Run git init to initiate a new repository
    TODO This hook should be upgraded to parametrise repository generation
    - rename branch
    - add all files and do an initial commit"""
    result = subprocess.run(["git", "init"], check=False)
    return result.returncode


class PostGenProtocol:
    """Protocol for post-generation hooks.

    Defined as a sequence of functions to call.
    Stores return code for each function to record any failing hooks."""

    def __init__(self) -> None:
        self.protocol: list[PostGenHook] = self._construct_protcol()

    def _construct_protcol(self) -> list[PostGenHook]:
        """Reconstruct sequence of PostGenHooks
        TODO This logic might be better in a factory method/class"""
        list_of_hooks = [
            PostGenHook(cleaunup_files),
        ]

        # optional steps
        if "{% if cookiecutter.create_venv %}YES{% endif %}" == "YES":
            list_of_hooks.append(PostGenHook(create_venv))

        if "{% if cookiecutter.run_git_init %}YES{% endif %}" == "YES":
            list_of_hooks.append(PostGenHook(git_init))

        return list_of_hooks

    def return_codes(self) -> list[int | None]:
        """Return current returncodes for all hooks in the protocol"""
        return [hook.return_code for hook in self.protocol]

    def all_passed(self) -> bool:
        """Report whether all hooks passed.
        Return code None counts as not passed yet"""
        return all([return_code == 0 for return_code in self.return_codes()])

    def run(self) -> None:
        """Run hooks in self.protocol"""
        for hook in self.protocol:
            hook.run()
        return


def main() -> int:
    """Run the hooks and return an exit code"""

    # initiate the protocol depending on set variables
    post_gen_hooks_protocol = PostGenProtocol()

    # run the protocol and log hook execution
    print("Running post-generation hooks...")
    post_gen_hooks_protocol.run()

    return_code = 0
    if post_gen_hooks_protocol.all_passed():
        print("Your new project has been created successfully!")
    else:
        return_code = 1
        print(
            "You new project has been generated but the post-generation hooks did not complete."
        )

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
