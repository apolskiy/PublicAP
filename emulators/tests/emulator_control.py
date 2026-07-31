"""Process-control helpers for the emulator suites.

Kept out of ``conftest`` deliberately: fixtures belong there, but the test
modules need these types and helpers directly, and importing from a conftest is
a structural accident rather than a published interface.
"""

from __future__ import annotations

import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

EMULATORS_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
CALLER_NUMBER_SCRIPT: Final[Path] = (
    EMULATORS_ROOT / "custom_header_response_to_http_request.py"
)

#: Where a spawned emulator's own log output is written, one file per instance.
LOG_DIRECTORY: Final[Path] = EMULATORS_ROOT.parent / "reports" / "emulator-logs"

#: Ceiling on how long a freshly spawned emulator may take to accept a
#: connection before the fixture gives up and reports a startup failure.
STARTUP_TIMEOUT_SECONDS: Final[float] = 15.0

#: Gap between readiness polls. Short enough to keep startup imperceptible.
READINESS_POLL_SECONDS: Final[float] = 0.05

#: Grace period for a process expected to exit on its own after a control code.
SHUTDOWN_TIMEOUT_SECONDS: Final[float] = 10.0


def reserve_free_port() -> int:
    """Reserve a port the operating system reports as free.

    Binding to port 0 lets the kernel choose, which keeps concurrent runs and
    busy development machines from colliding on the emulator's default 8080.

    Returns:
        int: A port number that was free at the moment of the call.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def wait_until_accepting(port: int, timeout: float = STARTUP_TIMEOUT_SECONDS) -> None:
    """Block until something accepts TCP connections on ``port``.

    Polling the socket is the only honest readiness signal available here: a
    fixed sleep is either slower than necessary or shorter than reality, and
    usually becomes both on a loaded CI runner.

    Args:
        port (int): The port being waited on.
        timeout (float): Seconds to wait before declaring startup failed.

    Returns:
        None

    Raises:
        RuntimeError: If nothing accepts a connection within ``timeout``.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(READINESS_POLL_SECONDS)
    raise RuntimeError(
        f"Emulator did not accept connections on port {port} within {timeout}s"
    )


def wait_until_refusing(port: int, timeout: float = SHUTDOWN_TIMEOUT_SECONDS) -> bool:
    """Block until nothing accepts TCP connections on ``port``.

    Args:
        port (int): The port being watched.
        timeout (float): Seconds to wait before giving up.

    Returns:
        bool: True if the port stopped accepting connections within ``timeout``,
        False if it was still accepting when the deadline passed.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                time.sleep(READINESS_POLL_SECONDS)
        except OSError:
            return True
    return False


@dataclass(frozen=True)
class EmulatorProcess:
    """A running caller-number emulator and the details needed to drive it.

    Attributes:
        base_url (str): Root URL the emulator is serving on.
        port (int): Port the emulator bound.
        process (subprocess.Popen[bytes]): The underlying process handle, used
            to observe exits that the HTTP layer cannot report.
    """

    base_url: str
    port: int
    process: "subprocess.Popen[bytes]"

    def wait_for_exit(self, timeout: float = SHUTDOWN_TIMEOUT_SECONDS) -> int | None:
        """Wait for the emulator to terminate of its own accord.

        Args:
            timeout (float): Seconds to wait for the process to end.

        Returns:
            int | None: The exit code, or None if the process was still running
            when the deadline passed. None is meaningful here: it distinguishes
            "exited cleanly" from "never exited at all".
        """
        try:
            return int(self.process.wait(timeout=timeout))
        except subprocess.TimeoutExpired:
            return None
