"""E2E coverage for the Flask HTTP error-code simulator.

The simulator exists so a consuming suite can obtain a specific status on
demand. Its contract is therefore narrow and total: for every code it claims to
support it must return exactly that code, for anything else it must return 404,
and a fault inside the simulator must never be mistaken for the status the
caller asked for.

Every case here is a pure function of the request URL, so the suite is driven
through the WSGI client. The two exceptions are grouped in
:class:`TestOverRealHttp`, which exists to prove the service is reachable over a
socket rather than only through WSGI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

import pytest
import requests
from flask.testing import FlaskClient

EMULATORS_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EMULATORS_ROOT / "flask_app"))

from app import SUPPORTED_ERROR_CODES  # noqa: E402  pylint: disable=wrong-import-position

#: Every code the simulator advertises, read from the application itself so the
#: suite cannot drift from the implementation it describes.
ALL_SUPPORTED_CODES: Final[list[int]] = sorted(SUPPORTED_ERROR_CODES)

#: Codes deliberately absent from the supported set. A consumer probing one of
#: these must get a clean 404 rather than an accidental success.
UNSUPPORTED_CODES: Final[tuple[int, ...]] = (402, 407, 418, 451, 502, 504, 599)

#: Paths that cannot match ``/error/<int:code>`` at all.
UNROUTABLE_PATHS: Final[tuple[str, ...]] = ("/error/abc", "/error/", "/error/4o4", "/nope")

#: Timeout for the few assertions that cross a real socket.
HTTP_TIMEOUT_SECONDS: Final[int] = 10


class TestSupportedCodes:
    """The simulator returns each advertised status exactly."""

    @pytest.mark.parametrize("code", ALL_SUPPORTED_CODES)
    def test_requested_code_is_returned_verbatim(
        self, flask_client: FlaskClient, code: int
    ) -> None:
        """Requesting a supported code must yield that code and no other.

        This is the simulator's entire reason to exist. A consuming suite uses
        it to prove its client handles a given status, so returning a different
        one silently validates the wrong branch.

        Preconditions:
            - ``code`` appears in the application's supported set.

        Assertions:
            - The response status equals the requested code exactly.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.
            code (int): A status code the simulator advertises.

        Returns:
            None
        """
        response = flask_client.get(f"/error/{code}")
        assert response.status_code == code, (
            f"Requested {code} but the simulator answered {response.status_code}. "
            "A simulator that returns the wrong status is worse than none: the "
            "consuming suite proves the wrong branch."
        )

    @pytest.mark.parametrize("code", ALL_SUPPORTED_CODES)
    def test_response_body_names_the_code_and_its_description(
        self, flask_client: FlaskClient, code: int
    ) -> None:
        """The body must identify the status, so a failure reads clearly.

        A status line alone is invisible in most test output. Naming the code
        and its description in the body means a captured response explains
        itself without the reader consulting a table.

        Preconditions:
            - ``code`` appears in the application's supported set.

        Assertions:
            - The body contains the numeric code.
            - The body contains the description the application maps to it.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.
            code (int): A status code the simulator advertises.

        Returns:
            None
        """
        body = flask_client.get(f"/error/{code}").get_data(as_text=True)
        assert str(code) in body, f"Body for {code} does not mention the code: {body!r}"
        assert SUPPORTED_ERROR_CODES[code] in body, (
            f"Body for {code} omits its description "
            f"'{SUPPORTED_ERROR_CODES[code]}': {body!r}"
        )

    def test_the_supported_set_matches_its_documented_shape(self) -> None:
        """The advertised set must stay the one the README and portfolio state.

        The published documentation commits to specific counts. This pins them,
        so widening or narrowing the set forces the documentation to be updated
        rather than quietly becoming wrong.

        Preconditions:
            - None; the application's own mapping is the input.

        Assertions:
            - Exactly 17 client-error codes are supported.
            - The server-error set is exactly 500, 501 and 503.
            - The only code at or above 600 is 600 itself.
            - 402 and 407 remain excluded.

        Returns:
            None
        """
        client_errors = [code for code in ALL_SUPPORTED_CODES if 400 <= code < 500]
        server_errors = [code for code in ALL_SUPPORTED_CODES if 500 <= code < 600]
        non_standard = [code for code in ALL_SUPPORTED_CODES if code >= 600]

        assert len(client_errors) == 17, f"Expected 17 4xx codes, found {client_errors}"
        assert server_errors == [500, 501, 503], f"Unexpected 5xx set: {server_errors}"
        assert non_standard == [600], f"Unexpected non-standard set: {non_standard}"
        assert 402 not in ALL_SUPPORTED_CODES, "402 was not meant to be reachable"
        assert 407 not in ALL_SUPPORTED_CODES, "407 was not meant to be reachable"

    def test_non_standard_600_is_served_rather_than_rejected(
        self, flask_client: FlaskClient
    ) -> None:
        """600 must be served despite lying outside the registered range.

        Its whole purpose is proving a client tolerates an unregistered status,
        so a simulator that normalised it would defeat the exercise.

        Preconditions:
            - 600 is present in the supported set.

        Assertions:
            - ``/error/600`` responds with status 600.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        assert flask_client.get("/error/600").status_code == 600


class TestUnsupportedRequests:
    """Anything outside the advertised set resolves to a clean 404."""

    @pytest.mark.parametrize("code", UNSUPPORTED_CODES)
    def test_unsupported_code_returns_404(
        self, flask_client: FlaskClient, code: int
    ) -> None:
        """An unlisted code must be reported absent, never invented.

        This is what makes the supported set discoverable by probing: a
        consumer can learn the boundary without reading the source.

        Preconditions:
            - ``code`` is absent from the application's supported set.

        Assertions:
            - The response status is 404, not the requested code.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.
            code (int): A status code the simulator does not advertise.

        Returns:
            None
        """
        assert flask_client.get(f"/error/{code}").status_code == 404

    @pytest.mark.parametrize("path", UNROUTABLE_PATHS)
    def test_unroutable_path_returns_404(
        self, flask_client: FlaskClient, path: str
    ) -> None:
        """A path the route cannot parse must 404 rather than raise.

        The route converter is typed ``int``; anything else must be refused by
        routing, not by an exception escaping into a 500.

        Preconditions:
            - ``path`` does not match ``/error/<int:code>``.

        Assertions:
            - The response status is 404.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.
            path (str): A URL that cannot match the error route.

        Returns:
            None
        """
        assert flask_client.get(path).status_code == 404


class TestCatalogue:
    """The index page is the simulator's own documentation."""

    def test_index_lists_every_supported_code(self, flask_client: FlaskClient) -> None:
        """Every supported code must be reachable from the index.

        A code that is supported but undiscoverable may as well not exist: the
        index is how a human finds out what this service can do.

        Preconditions:
            - The application is serving its index route.

        Assertions:
            - The index responds 200.
            - The index contains an ``/error/<code>`` link for every code.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        response = flask_client.get("/")
        assert response.status_code == 200

        body = response.get_data(as_text=True)
        missing = [code for code in ALL_SUPPORTED_CODES if f"/error/{code}" not in body]
        assert not missing, (
            f"The catalogue omits links for {missing}. A code that is supported "
            "but undiscoverable may as well not exist."
        )


class TestErrorHandling:
    """A fault in the simulator stays distinguishable from a requested failure."""

    def test_aborted_requests_render_their_own_status(
        self, flask_client: FlaskClient
    ) -> None:
        """An ``abort()`` must surface its own status, not a generic 500.

        The application installs a catch-all exception handler. If that handler
        flattened every outcome to 500, an unsupported code would look like a
        broken simulator instead of an honest "not supported".

        Preconditions:
            - 402 is outside the supported set, so requesting it aborts with 404.

        Assertions:
            - The response status is 404, not 500.
            - The body names the 404 rather than a server error.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        response = flask_client.get("/error/402")
        assert response.status_code == 404
        assert "404" in response.get_data(as_text=True)


class TestOverRealHttp:
    """The simulator is reachable over HTTP, not only through WSGI."""

    def test_status_is_served_over_a_real_socket(self, flask_server: str) -> None:
        """A real client on a real socket must observe the requested status.

        The WSGI client bypasses the HTTP server entirely. This is the assertion
        that the thing consumers actually connect to works.

        Preconditions:
            - The simulator is bound to a loopback port.

        Assertions:
            - A real HTTP request for 503 returns 503.
            - The body carries the mapped description.

        Args:
            flask_server (str): Base URL of the simulator on loopback.

        Returns:
            None
        """
        response = requests.get(
            f"{flask_server}/error/503", timeout=HTTP_TIMEOUT_SECONDS
        )
        assert response.status_code == 503
        assert "Service Unavailable" in response.text

    def test_catalogue_is_served_over_a_real_socket(self, flask_server: str) -> None:
        """The index must render for a browser, not only a test client.

        Preconditions:
            - The simulator is bound to a loopback port.

        Assertions:
            - The index responds 200 over real HTTP.
            - The rendered page carries its heading.

        Args:
            flask_server (str): Base URL of the simulator on loopback.

        Returns:
            None
        """
        response = requests.get(f"{flask_server}/", timeout=HTTP_TIMEOUT_SECONDS)
        assert response.status_code == 200
        assert "HTTP Error Code Simulator" in response.text
