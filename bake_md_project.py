#!/usr/bin/env python3
"""This is an additional wrapper over cookiecutter that uses 'questionary' to facilitate
selection of force-field parameters and mdp templates for the project"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import questionary
from cookiecutter.main import cookiecutter


# The directory containing this script is the Cookiecutter repository.
TEMPLATE_ROOT = Path(__file__).resolve().parent


def discover_template_dirs(group_name: str) -> list[str]:
    """Return all selectable parameter directories under simulations/{group_name}"""
    data_dir = (
        TEMPLATE_ROOT / "{{ cookiecutter.project_name }}" / "simulations" / group_name
    )

    # Assume that all directories in the folder are valid options
    all_dirs = [path.name for path in data_dir.iterdir() if path.is_dir()]
    all_dirs.sort()

    if not all_dirs:
        raise RuntimeError(f"No parameter directories were found in {data_dir}.")

    return all_dirs


def select_template_dirs(group_name: str, available_dirs: list[str]) -> list[str]:
    """Present the interactive checkbox prompt for template folder selection."""
    selected = questionary.checkbox(
        f"Select the {group_name.replace('_', ' ')} folders to include:",
        choices=available_dirs,
        instruction="(Space to toggle, Enter to confirm)",
        validate=lambda answer: (
            True if answer else "Select at least one parameter folder."
        ),
    ).ask()

    # Questionary may return None if the interaction is cancelled.
    if selected is None:
        raise KeyboardInterrupt

    return list(selected)


def main() -> int:
    try:
        file_selection_spec: dict[str, str] = {}

        for group_name in ["force_fields", "mdp_templates"]:
            all_dirs = discover_template_dirs(group_name)
            selected_dirs = select_template_dirs(group_name, all_dirs)

            print()
            print(f"Selected {group_name.replace('_', ' ')} folders:")
            for name in selected_dirs:
                print(f"  - {name}")
            print()

            file_selection_spec[f"_all_{group_name}_dirs"] = json.dumps(all_dirs)
            file_selection_spec[f"_selected_{group_name}_dirs"] = json.dumps(
                selected_dirs
            )

        generated_path = cookiecutter(
            str(TEMPLATE_ROOT),
            extra_context=file_selection_spec,
        )

        print()
        print(f"Project generated at: {generated_path}")

        return 0

    except KeyboardInterrupt:
        print("\nGeneration cancelled.", file=sys.stderr)
        return 130

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
