"""Run every module's main.py for real, the way CI does.

Each main.py checks its own results with assert and prints "module NN OK" on success, so a
chapter whose code drifts out of sync with what its README claims fails here.

Usage: python verify.py            # all modules
       python verify.py 04 06      # just these
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def modules() -> list[str]:
    return sorted(d for d in os.listdir(ROOT) if d[:2].isdigit() and os.path.isfile(os.path.join(ROOT, d, "main.py")))


def run(module: str) -> bool:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, module, "main.py")],
        cwd=os.path.join(ROOT, module),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
    )
    marker = f"module {module[:2]} OK"
    ok = proc.returncode == 0 and marker in proc.stdout
    print(f"{'PASS' if ok else 'FAIL'}  {module}")
    if not ok:
        print(proc.stdout)
        print(proc.stderr)
    return ok


def main() -> int:
    wanted = sys.argv[1:]
    todo = [m for m in modules() if not wanted or m[:2] in wanted]
    if not todo:
        print("no matching modules")
        return 2
    results = [run(m) for m in todo]
    print(f"{sum(results)}/{len(results)} modules verified")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
