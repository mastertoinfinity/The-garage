#!/usr/bin/env python
import os
import sys


from pathlib import Path


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "the_garage.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        base_dir = Path(__file__).resolve().parent
        venv_python_win = base_dir / ".venv" / "Scripts" / "python.exe"
        venv_python_nix = base_dir / ".venv" / "bin" / "python"
        venv_python = venv_python_win if venv_python_win.exists() else (venv_python_nix if venv_python_nix.exists() else None)

        if venv_python and Path(sys.executable).resolve() != venv_python.resolve():
            import subprocess
            result = subprocess.run([str(venv_python)] + sys.argv, cwd=base_dir)
            sys.exit(result.returncode)

        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()