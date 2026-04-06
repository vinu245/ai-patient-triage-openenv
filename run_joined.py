from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST = FRONTEND / "dist"
STATIC = BACKEND / "static"


def run(command: list[str], cwd: Path | None = None) -> None:
    print(f"-> {' '.join(command)}")
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def main() -> None:
    npm = "npm.cmd" if os.name == "nt" else "npm"

    if not FRONTEND.exists() or not BACKEND.exists():
        raise SystemExit("frontend/ and backend/ folders are required")

    run([npm, "install"], cwd=FRONTEND)
    run([npm, "run", "build"], cwd=FRONTEND)

    if STATIC.exists():
        shutil.rmtree(STATIC)
    shutil.copytree(DIST, STATIC)
    print(f"-> copied frontend build to {STATIC}")

    python = sys.executable
    run([python, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=BACKEND)


if __name__ == "__main__":
    main()
