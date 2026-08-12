"""Fixtures for the running-image suite.

These tests talk to a container over HTTP. They are deliberately kept out of
``testpaths`` in ``pytest.ini`` so an ordinary ``pytest`` run does not collect
them: without a container to talk to they can only be skipped, and a default run
reporting a wad of skips trains a reader to ignore skips.

Invoke them explicitly instead::

    EMULATOR_BASE_URL=http://127.0.0.1:4000 pytest emulators/image_tests
"""

from __future__ import annotations

import os
import time
from typing import Final, Iterator

import pytest
import requests

#: Where the container under test is listening. Overridable so the same suite
#: can be pointed at a locally built image or at a CI service container.
DEFAULT_BASE_URL: Final[str] = "http://127.0.0.1:4000"

#: How long to wait for the container to begin answering before giving up.
#: Generous: a cold service container on a shared runner is slower than a local
#: one, and a readiness timeout misreported as a behavioural failure would send
#: the reader looking in entirely the wrong place.
READINESS_TIMEOUT_SECONDS: Final[float] = 30.0

#: Gap between readiness polls.
READINESS_POLL_SECONDS: Final[float] = 0.25

#: Per-request timeout for the assertions themselves.
REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0


@pytest.fixture(name="image_base_url", scope="session")
def image_base_url_fixture() -> Iterator[str]:
    """Yield the base URL of a container that is already answering.

    Readiness is established by polling rather than sleeping, the same rule the
    process-spawning suite follows: a fixed sleep is either slower than
    necessary or shorter than reality, and on a loaded runner it becomes both.

    Preconditions:
        - A container built from this repository is listening on the URL given
          by ``EMULATOR_BASE_URL``, or on the default loopback port.

    Yields:
        str: Base URL of the running container, with no trailing slash.

    Raises:
        pytest.UsageError: If nothing answers within the readiness timeout. This
            is a setup failure, not a behavioural one, and says so.
    """
    base_url = os.environ.get("EMULATOR_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    deadline = time.monotonic() + READINESS_TIMEOUT_SECONDS
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            requests.get(f"{base_url}/", timeout=REQUEST_TIMEOUT_SECONDS)
            yield base_url
            return
        except requests.RequestException as connection_error:
            last_error = connection_error
            time.sleep(READINESS_POLL_SECONDS)

    raise pytest.UsageError(
        f"No emulator answered at {base_url} within {READINESS_TIMEOUT_SECONDS}s "
        f"({last_error}). These tests exercise a running container; start one, or "
        "point EMULATOR_BASE_URL at it. This is a setup failure, not a defect in "
        "the image."
    )
