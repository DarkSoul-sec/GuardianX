import shutil
import subprocess
import tempfile
import threading

from app.scanners.base import BaseScanner

# -sT: TCP connect scan (no root required)
# -sV: version detection for enrichment
# -Pn -n: skip host discovery / DNS (targets are pre-validated)
# -T4 --min-rate 200: keep probing fast even against filtered ports so the
#   scan completes instead of stalling on dropped packets
# --max-retries 2: tolerate packet loss without misclassifying open ports
# --host-timeout 600s: generous safety net; when it fires nmap discards the
#   timed-out host, so keep it long enough for real scans to finish
DEFAULT_NMAP_ARGS = (
    "-sT -sV -Pn -n -T4 --min-rate 200 --max-retries 2 --host-timeout 600s"
)

# Extra argument fragment appended for full port coverage (1-65535).
FULL_PORT_RANGE_ARGS = "-p 1-65535"


def nmap_available() -> bool:
    """Return True when the ``nmap`` executable is present on PATH."""
    return shutil.which("nmap") is not None


def nmap_unavailable_message() -> str:
    return (
        "Nmap is not installed. Scanning functionality is unavailable. "
        "Install Nmap (https://nmap.org) or use the GuardianX Docker image, "
        "which bundles it."
    )


def build_nmap_args(profile: str) -> str:
    """Return the nmap arguments for a given scan profile.

    "standard" covers nmap's default top-1000 common ports; "full" scans the
    entire TCP port range. Unknown profiles fall back to the standard set.
    """

    args = DEFAULT_NMAP_ARGS

    if profile == "full":
        args = f"{args} {FULL_PORT_RANGE_ARGS}"

    return args


def build_nmap_command(
    target: str,
    arguments: str | None = None,
) -> list[str]:
    """Build the nmap command line for a target scan.

    Optional `arguments` are appended to the base invocation verbatim (split
    on whitespace). When `arguments` is `None` or empty, the base invocation
    is used with no additional nmap arguments.
    """

    extra_args = arguments.split() if arguments else []

    return ["nmap", "-oX", "-", target, *extra_args]

_processes: dict[int, subprocess.Popen] = {}
_processes_lock = threading.Lock()

_cancelled: set[int] = set()
_cancelled_lock = threading.Lock()


def register_scan_process(
    scan_id: int,
    process: subprocess.Popen,
) -> None:
    with _processes_lock:
        _processes[scan_id] = process


def unregister_scan_process(scan_id: int) -> None:
    with _processes_lock:
        _processes.pop(scan_id, None)


def terminate_scan_process(scan_id: int) -> bool:
    """
    Terminate the nmap process running for a scan, if any.

    Returns True if a live process was terminated.
    """
    with _processes_lock:
        process = _processes.get(scan_id)

    if process is None or process.poll() is not None:
        return False

    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    return True


def mark_scan_cancelled(scan_id: int) -> None:
    with _cancelled_lock:
        _cancelled.add(scan_id)


def clear_scan_cancelled(scan_id: int) -> None:
    with _cancelled_lock:
        _cancelled.discard(scan_id)


def is_scan_cancelled(scan_id: int) -> bool:
    with _cancelled_lock:
        return scan_id in _cancelled


class NmapScanner(BaseScanner):

    def scan(
        self,
        target: str,
        scan_id: int | None = None,
        arguments: str | None = None,
    ) -> str:

        process = subprocess.Popen(
            build_nmap_command(target, arguments),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if scan_id is not None:
            register_scan_process(scan_id, process)

        try:
            stdout, _stderr = process.communicate()
        finally:
            if scan_id is not None:
                unregister_scan_process(scan_id)

        if process.returncode != 0 or not stdout:
            raise RuntimeError(
                f"Nmap failed for target {target} "
                f"(exit code {process.returncode})."
            )

        xml = stdout.decode("utf-8", errors="ignore")

        temp = tempfile.NamedTemporaryFile(
            suffix=".xml",
            delete=False,
            mode="w",
            encoding="utf-8",
        )

        temp.write(xml)
        temp.close()

        return temp.name
