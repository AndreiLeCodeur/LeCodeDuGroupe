"""Supplied archive builder. The workflow gates this script on successful tests."""
import os
from pathlib import Path
import re
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("gridworld", "levels", "scenarios", "tests")
EXTENSIONS = {".py", ".json", ".txt", ".png", ".svg", ".jpg", ".jpeg", ".ttf", ".wav", ".ogg"}
EXCLUDED = {"__pycache__", ".venv", "venv", ".pytest_cache"}


def main():
    revision = os.environ.get("GITHUB_SHA")
    if revision is None:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected a full commit SHA")
    files = [ROOT / name for name in ("README.md", "pyproject.toml", "uv.lock", "initial_state.json")]
    if (ROOT / ".python-version").is_file():
        files.append(ROOT / ".python-version")
    for name in DIRECTORIES:
        folder = ROOT / name
        if not folder.is_dir():
            raise FileNotFoundError(f"Missing directory: {name}")
        for path in folder.rglob("*"):
            relative = path.relative_to(folder)
            if path.is_file() and path.suffix in EXTENSIONS and not any(
                part.startswith(".") or part in EXCLUDED for part in relative.parts
            ):
                if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
                    raise ValueError(f"Do not package symlinks: {path}")
                files.append(path)
    output = ROOT / "dist" / f"gridworld-{revision}.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as bundle:
        for path in sorted(files):
            bundle.write(path, path.relative_to(ROOT).as_posix())
        bundle.writestr("REVISION.txt", revision + "\n")
    print(output)


if __name__ == "__main__":
    main()