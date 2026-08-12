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
import time
from pathlib import Path
from typing import Final

import pytest
import requests
from flask.testing import FlaskClient

EMULATORS_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EMULATORS_ROOT / "flask_app"))

# noqa: E402  pylint: disable=wrong-import-position
from app import (
    DELAY_APPLIED_HEADER,
    DELAY_REQUEST_HEADER,
    MAX_DELAY_MS,
    SUPPORTED_ERROR_CODES,
    UNINTERPRETABLE_REQUEST,
)

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

#: Delay used by the latency assertions. Long enough to outrun timer noise on a
#: loaded runner, short enough that the whole class stays well under a second.
DELAY_UNDER_TEST_MS: Final[int] = 250

#: Slack allowed when measuring an applied delay. Windows' default timer
#: granularity is roughly 15.6ms, so a sleep can be observed a fraction short of
#: its nominal duration; asserting an exact floor would fail on that alone.
TIMER_TOLERANCE_MS: Final[int] = 25

#: Ceiling on how long an *undelayed* response may take before the assertion
#: that no delay was applied stops being meaningful. Deliberately generous: it
#: exists to catch a delay that fired when none was asked for, not to police
#: the service's own speed on a busy machine.
NO_DELAY_CEILING_MS: Final[int] = 1_000

#: Delay header values the service must refuse rather than interpret. Each is a
#: plausible caller mistake: a unit suffix, a float, a negative, an empty
#: header, and a value past the ceiling.
UNINTERPRETABLE_DELAYS: Final[tuple[str, ...]] = (
    "250ms",
    "1.5",
    "-5",
    "",
    str(MAX_DELAY_MS + 1),
)


def _elapsed_ms(started_at: float) -> float:
    """Return milliseconds elapsed since a :func:`time.perf_counter` reading.

    Args:
        started_at (float): The reading taken before the call under test.

    Returns:
        float: Elapsed wall-clock time in milliseconds.
    """
    return (time.perf_counter() - started_at) * 1000


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


class TestLatencyInjection:
    """The simulator answers late by an exact, caller-specified amount.

    A client's timeout, retry and backoff paths are usually its least-tested
    code, because a real upstream cannot be asked to be slow to order. These
    assertions cover the contract a consuming suite depends on: the delay is
    applied, it is reported, it composes with the requested status, and a delay
    that cannot be honoured is refused rather than approximated.
    """

    def test_no_delay_header_answers_immediately(
        self, flask_client: FlaskClient
    ) -> None:
        """Without the header the service must not pause at all.

        The delay is opt-in. Every existing consumer sends no such header, and
        must keep seeing the response times it always has.

        Preconditions:
            - No delay header is sent.

        Assertions:
            - The response reports zero applied delay.
            - The round trip stays under the no-delay ceiling.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        started_at = time.perf_counter()
        response = flask_client.get("/error/503")
        elapsed_ms = _elapsed_ms(started_at)

        assert response.headers[DELAY_APPLIED_HEADER] == "0"
        assert elapsed_ms < NO_DELAY_CEILING_MS, (
            f"An undelayed request took {elapsed_ms:.0f}ms. Either a delay was "
            "applied without being asked for, or this machine is too loaded for "
            "the measurement to mean anything."
        )

    def test_requested_delay_is_applied_and_reported(
        self, flask_client: FlaskClient
    ) -> None:
        """The service must sleep the requested time and say that it did.

        The reported figure is what makes the delay assertable without a
        stopwatch, which would otherwise be measuring the test runner's own
        scheduling as much as the service's behaviour.

        Preconditions:
            - The delay header carries a value within the ceiling.

        Assertions:
            - The applied-delay header echoes the requested value.
            - The measured round trip is at least the requested delay, less the
              platform's timer granularity.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        started_at = time.perf_counter()
        response = flask_client.get(
            "/error/503", headers={DELAY_REQUEST_HEADER: str(DELAY_UNDER_TEST_MS)}
        )
        elapsed_ms = _elapsed_ms(started_at)

        assert response.headers[DELAY_APPLIED_HEADER] == str(DELAY_UNDER_TEST_MS)
        assert elapsed_ms >= DELAY_UNDER_TEST_MS - TIMER_TOLERANCE_MS, (
            f"Asked for {DELAY_UNDER_TEST_MS}ms but the response came back in "
            f"{elapsed_ms:.0f}ms. A delay that is reported but not taken would let "
            "a client's timeout test pass without ever reaching its timeout."
        )

    def test_delay_composes_with_the_requested_status(
        self, flask_client: FlaskClient
    ) -> None:
        """A delayed response must still carry the status that was asked for.

        The two controls are orthogonal by design: the interesting cases for a
        retry policy are a slow 503 and a slow 429, not a slow 200.

        Preconditions:
            - 503 is in the supported set.

        Assertions:
            - The status is 503, not a delay-related code.
            - The body still names the mapped description.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        response = flask_client.get(
            "/error/503", headers={DELAY_REQUEST_HEADER: str(DELAY_UNDER_TEST_MS)}
        )

        assert response.status_code == 503
        assert "Service Unavailable" in response.get_data(as_text=True)

    @pytest.mark.parametrize("path", ("/", "/error/404", "/error/600"))
    def test_delay_applies_to_every_route(
        self, flask_client: FlaskClient, path: str
    ) -> None:
        """The delay must not be confined to the error route.

        A consumer proving it survives a slow catalogue, a slow 404 or a slow
        non-standard status needs the same control as one proving it survives a
        slow 503.

        Preconditions:
            - ``path`` is a route the service serves.

        Assertions:
            - The applied-delay header echoes the requested value.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.
            path (str): A route the service answers.

        Returns:
            None
        """
        response = flask_client.get(
            path, headers={DELAY_REQUEST_HEADER: str(DELAY_UNDER_TEST_MS)}
        )
        assert response.headers[DELAY_APPLIED_HEADER] == str(DELAY_UNDER_TEST_MS)

    @pytest.mark.parametrize("delay_value", UNINTERPRETABLE_DELAYS)
    def test_uninterpretable_delay_yields_the_sentinel(
        self, flask_client: FlaskClient, delay_value: str
    ) -> None:
        """A delay that cannot be honoured must be refused with 999.

        999 sits outside the HTTP range on purpose, so a caller can never
        confuse "this service rejected your header" with a status it was asked
        to produce. It is the same sentinel the caller-number emulator uses for
        the same meaning.

        Preconditions:
            - ``delay_value`` is not a whole, non-negative, in-range number.

        Assertions:
            - The status is the sentinel, not the requested 503.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.
            delay_value (str): A delay header value the service must refuse.

        Returns:
            None
        """
        response = flask_client.get(
            "/error/503", headers={DELAY_REQUEST_HEADER: delay_value}
        )
        assert response.status_code == UNINTERPRETABLE_REQUEST, (
            f"Delay {delay_value!r} produced {response.status_code}. Serving the "
            "requested status anyway would let a timeout test pass on a delay that "
            "never happened."
        )

    def test_refusal_is_not_a_server_error(self, flask_client: FlaskClient) -> None:
        """A rejected header must not be reported as a fault in the simulator.

        ``abort`` cannot raise a 999 - Werkzeug has no exception registered for
        it - so an implementation that reached for ``abort`` would fall through
        to the catch-all handler and answer 500. That would say "the simulator
        broke" when the truth is "your header was wrong", and it is the exact
        confusion this service exists to prevent.

        Preconditions:
            - The delay header carries an uninterpretable value.

        Assertions:
            - The status is the sentinel and specifically not 500.
            - The body explains which header was at fault.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        response = flask_client.get("/error/503", headers={DELAY_REQUEST_HEADER: "abc"})

        assert response.status_code != 500
        assert response.status_code == UNINTERPRETABLE_REQUEST
        assert DELAY_REQUEST_HEADER in response.get_data(as_text=True)

    def test_delay_above_the_ceiling_is_refused_rather_than_clamped(
        self, flask_client: FlaskClient
    ) -> None:
        """An over-long delay must be refused, and must not be silently shortened.

        Clamping is the tempting choice and the wrong one. A caller who asked
        for 60s, received 30s, and saw their 45s timeout not fire would conclude
        their client tolerates a 60s upstream. Refusing tells them immediately.

        Preconditions:
            - The requested delay exceeds ``MAX_DELAY_MS``.

        Assertions:
            - The status is the sentinel.
            - The body names the ceiling, so the limit is discoverable by
              probing rather than only by reading the source.
            - The refusal is not itself delayed.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        started_at = time.perf_counter()
        response = flask_client.get(
            "/error/503", headers={DELAY_REQUEST_HEADER: str(MAX_DELAY_MS + 1)}
        )
        elapsed_ms = _elapsed_ms(started_at)

        assert response.status_code == UNINTERPRETABLE_REQUEST
        assert str(MAX_DELAY_MS) in response.get_data(as_text=True)
        assert elapsed_ms < NO_DELAY_CEILING_MS, (
            f"A refused delay still took {elapsed_ms:.0f}ms. A rejection must be "
            "immediate; sleeping first would punish the caller for the mistake the "
            "service just declined to act on."
        )

    def test_catalogue_documents_the_delay_contract(
        self, flask_client: FlaskClient
    ) -> None:
        """The index must publish the delay header, its ceiling and its sentinel.

        The catalogue is this service's own documentation. A capability that is
        present but undiscoverable may as well not exist, which is the same
        standard already applied to the status codes it lists.

        Preconditions:
            - The service is serving its index route.

        Assertions:
            - The page names the request header, the response header, the
              ceiling, and the sentinel status.

        Args:
            flask_client (FlaskClient): WSGI client bound to the simulator.

        Returns:
            None
        """
        body = flask_client.get("/").get_data(as_text=True)

        for advertised in (
            DELAY_REQUEST_HEADER,
            DELAY_APPLIED_HEADER,
            str(MAX_DELAY_MS),
            str(UNINTERPRETABLE_REQUEST),
        ):
            assert advertised in body, (
                f"The catalogue does not mention {advertised!r}. A capability that "
                "is undiscoverable may as well not exist."
            )


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

    def test_delay_is_applied_over_a_real_socket(self, flask_server: str) -> None:
        """The delay must reach a real client, not only the WSGI layer.

        This is the assertion that matters to a consumer: their HTTP client,
        their timeout, their socket. A delay implemented only in the WSGI path
        would satisfy every other case in this class and help nobody.

        Preconditions:
            - The simulator is bound to a loopback port.

        Assertions:
            - The requested status still arrives.
            - The applied-delay header echoes the request.
            - The measured round trip is at least the requested delay.

        Args:
            flask_server (str): Base URL of the simulator on loopback.

        Returns:
            None
        """
        started_at = time.perf_counter()
        response = requests.get(
            f"{flask_server}/error/503",
            headers={DELAY_REQUEST_HEADER: str(DELAY_UNDER_TEST_MS)},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        elapsed_ms = _elapsed_ms(started_at)

        assert response.status_code == 503
        assert response.headers[DELAY_APPLIED_HEADER] == str(DELAY_UNDER_TEST_MS)
        assert elapsed_ms >= DELAY_UNDER_TEST_MS - TIMER_TOLERANCE_MS, (
            f"Over a real socket the response returned in {elapsed_ms:.0f}ms "
            f"despite a {DELAY_UNDER_TEST_MS}ms delay being requested."
        )

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
