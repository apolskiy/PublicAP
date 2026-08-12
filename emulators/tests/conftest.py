"""Fixtures for the emulator suites.

Isolation strategy
------------------
The two emulators need opposite treatment, and the difference is not stylistic.

The **Flask simulator** is a pure request/response service with no lifecycle
behaviour, so it is exercised in-process: the WSGI test client for the status
matrix, and a real Werkzeug server on a loopback socket for the handful of
assertions that must prove it speaks HTTP rather than WSGI.

The **caller-number emulator** deliberately kills or blocks its own process -
``999`` exits non-zero, ``592`` exits zero, ``590`` blocks the single-threaded
server for two minutes. None of that can be exercised in-process without taking
the test session down with it, so every test that touches it gets its own
subprocess on its own ephemeral port. A shared server would make the outcome of
one test depend on which destructive test ran before it, which is exactly the
non-determinism this suite exists to avoid.

Readiness is always established by polling the socket, never by sleeping: a
fixed sleep is either a slow test or a flaky one, and usually becomes both.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from typing import Iterator

import pytest
from flask.testing import FlaskClient
from werkzeug.serving import make_server

from emulator_control import (
    CALLER_NUMBER_SCRIPT,
    EMULATORS_ROOT,
    LOG_DIRECTORY,
    SHUTDOWN_TIMEOUT_SECONDS,
    EmulatorProcess,
    reserve_free_port,
    wait_until_accepting,
)


@pytest.fixture(name="emulator")
def emulator_fixture() -> Iterator[EmulatorProcess]:
    """Start one caller-number emulator per test, on its own port.

    Function scope is deliberate. Several control codes terminate or block the
    emulator, so sharing an instance would leak the effect of one test into the
    next and make results depend on execution order.

    Preconditions:
        - ``custom_header_response_to_http_request.py`` honours ``EMULATOR_PORT``.
        - A free TCP port is obtainable on the loopback interface.

    Yields:
        EmulatorProcess: A started emulator, already accepting connections.
    """
    port = reserve_free_port()
    environment = {**os.environ, "EMULATOR_PORT": str(port), "PYTHONUNBUFFERED": "1"}

    # Emulator output goes to a file, not a pipe. An undrained pipe eventually
    # fills and blocks the emulator mid-request, which would surface as an
    # inexplicable timeout in an unrelated test; a file cannot deadlock and
    # survives the run for diagnosis. The handle is closed deterministically
    # because this suite promotes warnings to errors, and a leaked handle is a
    # ResourceWarning at teardown.
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIRECTORY / f"emulator-{port}.log"
    with log_path.open("w", encoding="utf-8") as log_file, subprocess.Popen(
        [sys.executable, str(CALLER_NUMBER_SCRIPT)],
        env=environment,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    ) as process:
        try:
            wait_until_accepting(port)
            yield EmulatorProcess(f"http://127.0.0.1:{port}", port, process)
        finally:
            # Terminate before the context manager's implicit wait(), which
            # would otherwise block on an emulator that is still serving.
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)


@pytest.fixture(name="flask_client")
def flask_client_fixture() -> Iterator[FlaskClient]:
    """Provide a WSGI test client for the Flask error simulator.

    The status matrix is large and every case is a pure function of the URL, so
    it is driven through the test client: no socket, no port, no teardown, and
    nothing that can flake.

    Preconditions:
        - ``emulators/flask_app/app.py`` is importable.

    Yields:
        FlaskClient: A client bound to the simulator application, with
        ``TESTING`` enabled so a fault propagates instead of being swallowed
        into a generic 500 page.
    """
    sys.path.insert(0, str(EMULATORS_ROOT / "flask_app"))
    from app import app as flask_application  # pylint: disable=import-outside-toplevel

    flask_application.config.update(TESTING=True)
    with flask_application.test_client() as client:
        yield client


@pytest.fixture(name="flask_server")
def flask_server_fixture() -> Iterator[str]:
    """Serve the Flask simulator over a real loopback socket.

    A WSGI client proves the application logic; it does not prove the service is
    reachable over HTTP. A real server is used for that narrow purpose, run in a
    daemon thread so no subprocess or Flask CLI is involved.

    The server is threaded because the published container is: the image's
    ``flask run`` command defaults to ``--with-threads``. Since the simulator
    gained a caller-controlled delay, that difference stopped being cosmetic -
    a single-threaded fixture would serialise behind any delayed request and
    would misrepresent the artifact consumers actually run.

    Preconditions:
        - ``emulators/flask_app/app.py`` is importable.

    Yields:
        str: The base URL the simulator is reachable on.
    """
    sys.path.insert(0, str(EMULATORS_ROOT / "flask_app"))
    from app import app as flask_application  # pylint: disable=import-outside-toplevel

    port = reserve_free_port()
    server = make_server("127.0.0.1", port, flask_application, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        wait_until_accepting(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=SHUTDOWN_TIMEOUT_SECONDS)
