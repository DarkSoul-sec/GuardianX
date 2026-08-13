"""Safe, read-only subprocess helpers used by Linux collectors.

Collectors occasionally read systemctl/journalctl output. These helpers run a
fixed command line (no shell, no user input) with a short timeout and treat
any nonzero exit or timeout as "nothing to report" instead of raising. They
never write files, never modify state, and never run remote or dynamic input.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence


class CommandError(Exception):
    """Raised when a required helper binary is missing or times out."""


def run_capture(
    argv: Sequence[str],
    *,
    timeout: float = 5.0,
    max_bytes: int = 2 * 1024 * 1024,
) -> str:
    """Run ``argv`` and return its stdout, or raise :class:`CommandError`."""
    executable = shutil.which(argv[0])
    if not executable:
        raise CommandError(f"executable not found: {argv[0]}")

    try:
        result = subprocess.run(
            [executable, *argv[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise CommandError(f"command failed: {argv[0]}: {exc}") from exc

    if result.returncode != 0:
        raise CommandError(f"command exited {result.returncode}: {argv[0]}")

    return result.stdout[:max_bytes]


def which(name: str) -> bool:
    return shutil.which(name) is not None