"""CLI entry points for running the Reflex app."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from just_dna_pipelines.runtime import load_env


def _consume_immutable_flag() -> None:
    """Set the env var if ``--immutable`` is present in sys.argv."""
    if "--immutable" in sys.argv:
        sys.argv = [a for a in sys.argv if a != "--immutable"]
        os.environ["JUST_DNA_IMMUTABLE_MODE"] = "true"


def _setup() -> None:
    """Load .env and ensure cwd is the project root (where rxconfig.py lives)."""
    load_env()
    root = Path(__file__).resolve().parents[2]
    os.chdir(root)


def main() -> None:
    """Start the Reflex development server.

    Supports ``--immutable`` flag to start in public demo mode.
    """
    _consume_immutable_flag()
    _setup()

    from reflex import constants
    from reflex.reflex import _run
    from reflex_base.config import environment

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    _run(env=constants.Env.DEV)


def serve() -> None:
    """Start the single-port production server (Reflex 0.9+ unified mode).

    Self-sufficient: compiles frontend and serves everything from a single
    Python process — no separate Node.js server needed.

    Supports ``--immutable`` flag for public demo mode.
    """
    _consume_immutable_flag()
    _setup()

    web_dir = Path(".web")
    if web_dir.exists():
        shutil.rmtree(web_dir)
        print("Removed stale .web build directory before production serve.", flush=True)

    from reflex import constants
    from reflex.constants.base import RunningMode
    from reflex.reflex import _run
    from reflex_base.config import environment

    port_str = os.getenv("APP_PORT", "").strip()
    port = int(port_str) if port_str else None

    environment.REFLEX_COMPILE_CONTEXT.set(constants.CompileContext.RUN)
    _run(
        env=constants.Env.PROD,
        running_mode=RunningMode.FULLSTACK,
        frontend_port=port,
        backend_port=port,
    )


def kill_ports() -> None:
    """Show and kill processes on ports 3000 and 8000-8010.

    Usage::

        uv run kill-ports            # show and kill default ports
        uv run kill-ports 3000       # only port 3000
        uv run kill-ports 3000 8000  # explicit list
    """
    ports = [int(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else [3000, *range(8000, 8011)]
    killed_any = False
    for port in ports:
        try:
            out = subprocess.check_output(
                ["lsof", "-ti", f":{port}"], text=True, stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            out = ""
        if not out:
            continue
        pids = [int(p) for p in out.split()]
        for pid in pids:
            try:
                cmd = subprocess.check_output(
                    ["ps", "-p", str(pid), "-o", "comm="], text=True, stderr=subprocess.DEVNULL,
                ).strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                cmd = "?"
            print(f"Port {port}: killing PID {pid} ({cmd})")
            try:
                os.kill(pid, signal.SIGKILL)
                killed_any = True
            except OSError as exc:
                print(f"  failed: {exc}")
    if not killed_any:
        print("Nothing to kill — ports are free.")


if __name__ == "__main__":
    main()
