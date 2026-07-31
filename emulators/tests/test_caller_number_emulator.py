"""E2E coverage for the caller-number HTTP emulator.

Every test here drives a real socket against a real process, because the
behaviour under test *is* process behaviour: the emulator stalls, drops its
listener, or exits, and none of that is observable in-process.

Each test receives its own emulator instance (see ``conftest``). That is the
whole isolation strategy: the destructive control codes make any shared server
order-dependent, and an order-dependent suite is not a suite, it is a sequence.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Final

import pytest
import requests

from emulator_control import EmulatorProcess, wait_until_refusing

#: Comfortably longer than a healthy reply, far shorter than the 120s stall the
#: emulator enters on 590, so a hang is reported as a timeout rather than as a
#: test that never ends.
CLIENT_TIMEOUT_SECONDS: Final[int] = 5

#: Shorter timeout for the stall case: the assertion is that the client gives
#: up, so there is no reason to wait the full default.
STALL_TIMEOUT_SECONDS: Final[int] = 2

#: Prefix standing in for the routable part of a dialled number. Only the last
#: three digits select the status.
NUMBER_PREFIX: Final[str] = "18884400"

#: Codes the emulator echoes back with no lifecycle side effect.
BENIGN_CODES: Final[tuple[int, ...]] = (
    200, 202, 204, 301, 400, 403, 404, 409, 418, 500, 502, 503,
)

#: The verbs the handler routes through identical logic.
SUPPORTED_VERBS: Final[tuple[str, ...]] = ("GET", "POST", "PUT", "DELETE", "PATCH")


def number_for(status: int) -> str:
    """Build a caller number whose last three digits select ``status``.

    Args:
        status (int): The status code wanted.

    Returns:
        str: A caller number ending in that three-digit code.
    """
    return f"{NUMBER_PREFIX}{status:03d}"


def call(
    emulator: EmulatorProcess,
    *,
    method: str = "POST",
    json_body: dict[str, Any] | None = None,
    raw_body: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = CLIENT_TIMEOUT_SECONDS,
) -> requests.Response:
    """Issue one request to a running emulator.

    Parameters are explicit rather than ``**kwargs`` so a caller cannot pass an
    option the helper silently ignores.

    Args:
        emulator (EmulatorProcess): The emulator under test.
        method (str): HTTP verb to use.
        json_body (dict[str, Any] | None): Body to serialise as JSON.
        raw_body (str | None): Body to send verbatim, for malformed-input cases.
        headers (dict[str, str] | None): Additional request headers.
        timeout (int): Client-side timeout in seconds.

    Returns:
        requests.Response: The response received.
    """
    return requests.request(
        method,
        emulator.base_url,
        json=json_body,
        data=raw_body,
        headers=headers,
        timeout=timeout,
    )


class TestPayloadDrivenStatus:
    """The status is selected by the last three digits of ``caller-number``."""

    @pytest.mark.parametrize("status", BENIGN_CODES)
    def test_last_three_digits_select_the_status(
        self, emulator: EmulatorProcess, status: int
    ) -> None:
        """A caller number ending in NNN must produce status NNN.

        This is the emulator's core contract: the dialled number decides the
        outcome, which lets a consuming suite carry a table of numbers instead
        of a table of URLs.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - ``status`` has no lifecycle side effect.

        Assertions:
            - The response status equals the encoded code.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.
            status (int): The status the number encodes.

        Returns:
            None
        """
        response = call(emulator, json_body={"caller-number": number_for(status)})
        assert response.status_code == status, (
            f"caller-number {number_for(status)} should select {status}, "
            f"got {response.status_code}"
        )

    def test_echoed_body_reports_the_code_it_served(
        self, emulator: EmulatorProcess
    ) -> None:
        """A generic code must return a body naming that code.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The JSON body is exactly ``{"status": "Response with code 503"}``.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(emulator, json_body={"caller-number": number_for(503)})
        assert response.json() == {"status": "Response with code 503"}

    @pytest.mark.parametrize("verb", SUPPORTED_VERBS)
    def test_every_verb_routes_through_the_same_logic(
        self, emulator: EmulatorProcess, verb: str
    ) -> None:
        """All five verbs must honour the payload identically.

        The emulator advertises full verb support, so a consumer testing a
        DELETE path must be able to obtain the same statuses as on GET.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - Each verb returns the status encoded in the payload.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.
            verb (str): The HTTP method under test.

        Returns:
            None
        """
        response = call(
            emulator, method=verb, json_body={"caller-number": number_for(404)}
        )
        assert response.status_code == 404

    def test_status_above_the_http_range_is_still_served(
        self, emulator: EmulatorProcess
    ) -> None:
        """A code at or above 600 is served, with a warning, not rejected.

        The emulator logs a warning but honours the request, so a consumer can
        exercise a client's handling of an out-of-range status.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The response status is 601, not normalised or refused.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(emulator, json_body={"caller-number": number_for(601)})
        assert response.status_code == 601


class TestHeaderFallback:
    """With no body, the status comes from ``X-Caller-Number``."""

    def test_header_supplies_the_status_when_no_body_is_sent(
        self, emulator: EmulatorProcess
    ) -> None:
        """The header value is read as the status code directly.

        This is the path for consumers that cannot attach a body, such as a
        plain GET from a health checker.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - The request carries no body.

        Assertions:
            - The status named in the header is returned.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(emulator, method="GET", headers={"X-Caller-Number": "404"})
        assert response.status_code == 404

    def test_body_takes_precedence_over_the_header(
        self, emulator: EmulatorProcess
    ) -> None:
        """When both selectors are present the payload wins.

        Only one can decide, and the precedence must be defined rather than
        incidental, or a consumer sending both gets a coin toss.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - Body and header encode different statuses.

        Assertions:
            - The status from the body is returned, not the header's.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(
            emulator,
            json_body={"caller-number": number_for(503)},
            headers={"X-Caller-Number": "404"},
        )
        assert response.status_code == 503


class TestSessionCreation:
    """``201`` emulates session creation."""

    def test_201_returns_a_uuid_session_identifier(
        self, emulator: EmulatorProcess
    ) -> None:
        """The 201 response must carry a parseable UUID4 session id.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The response status is 201.
            - ``session_id`` parses as a UUID of version 4.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(emulator, json_body={"caller-number": number_for(201)})
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        assert uuid.UUID(session_id).version == 4, f"Not a UUID4: {session_id}"

    def test_each_session_identifier_is_unique(
        self, emulator: EmulatorProcess
    ) -> None:
        """Two calls must not share an identifier.

        A constant id would let a consuming suite pass while treating two
        separate sessions as one, which is precisely the bug session handling
        is meant to expose.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - 201 has no lifecycle side effect, so one instance serves both calls.

        Assertions:
            - The two returned identifiers differ.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        first = call(emulator, json_body={"caller-number": number_for(201)})
        second = call(emulator, json_body={"caller-number": number_for(201)})
        assert first.json()["session_id"] != second.json()["session_id"]


class TestSentinel999:
    """``999`` marks a request the emulator could not interpret."""

    @pytest.mark.parametrize(
        "payload, reason",
        (
            ({"wrong-field": "18884400200"}, "no caller-number field"),
            ({"caller-number": "12"}, "caller-number shorter than three characters"),
            ({"caller-number": "1888440abc"}, "last three characters not digits"),
        ),
        ids=("missing-field", "too-short", "non-numeric-suffix"),
    )
    def test_uninterpretable_payload_yields_999(
        self, emulator: EmulatorProcess, payload: dict[str, str], reason: str
    ) -> None:
        """A malformed payload must be reported out-of-band, not as a 4xx.

        999 sits outside the HTTP range on purpose: a consumer must never
        confuse "the emulator rejected my request" with a failure it asked for.
        Returning 400 here would be indistinguishable from a requested 400.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - The payload cannot yield a status code.

        Assertions:
            - The response status is 999.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.
            payload (dict[str, str]): The malformed request body.
            reason (str): Human-readable cause, surfaced on failure.

        Returns:
            None
        """
        response = call(emulator, json_body=payload)
        assert response.status_code == 999, f"Expected 999 for {reason}"

    def test_invalid_json_yields_999_with_an_explanatory_body(
        self, emulator: EmulatorProcess
    ) -> None:
        """A body that is not JSON must be reported as such.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - The body is syntactically invalid JSON with a JSON content type.

        Assertions:
            - The response status is 999.
            - The body identifies the cause as an invalid JSON body.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(
            emulator,
            raw_body="{not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 999
        assert response.json() == {"error": "Invalid JSON body"}

    def test_no_body_and_no_header_yields_999(
        self, emulator: EmulatorProcess
    ) -> None:
        """A request carrying no selector at all is uninterpretable.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - The request has neither a body nor ``X-Caller-Number``.

        Assertions:
            - The response status is 999.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        assert call(emulator, method="GET").status_code == 999

    def test_the_process_exits_non_zero_after_a_999(
        self, emulator: EmulatorProcess
    ) -> None:
        """A 999 must take the emulator down loudly.

        Continuing to serve after an uninterpretable request would leave a suite
        running against a server in an unknown state. Exiting non-zero makes the
        misconfiguration impossible to ignore, and is the reason each test owns
        its own emulator instance.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The 999 response is delivered before the process ends.
            - The process exits within the shutdown grace period.
            - The exit code is non-zero.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        assert call(emulator, json_body={"caller-number": "12"}).status_code == 999

        exit_code = emulator.wait_for_exit()
        assert exit_code is not None, "Emulator kept running after serving a 999"
        assert exit_code != 0, f"Expected a non-zero exit after 999, got {exit_code}"


class TestLifecycleControlCodes:
    """The control codes that stall or terminate the emulator."""

    def test_590_stalls_without_answering(self, emulator: EmulatorProcess) -> None:
        """590 must accept the connection and never reply.

        This is the case a mock cannot reproduce: the client has to experience a
        real open connection that goes quiet, so its own timeout is what ends
        the call. The assertion is the client-side timeout, not the full 120s
        stall - waiting that out would prove nothing further and would make the
        suite unusable in CI.

        Preconditions:
            - A freshly started emulator is accepting connections.
            - The client timeout is far below the emulator's 120s stall.

        Assertions:
            - The client raises a timeout rather than receiving a response.
            - The emulator process is still alive afterwards; 590 stalls, it
              does not terminate.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        with pytest.raises(requests.exceptions.Timeout):
            call(
                emulator,
                json_body={"caller-number": number_for(590)},
                timeout=STALL_TIMEOUT_SECONDS,
            )

        assert emulator.process.poll() is None, (
            "590 should leave the emulator alive but unresponsive; it exited."
        )

    def test_592_shuts_the_emulator_down(self, emulator: EmulatorProcess) -> None:
        """592 must stop the service and stop accepting connections.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The request fails rather than returning a response, because the
              emulator closes the socket instead of replying.
            - The port stops accepting connections within the grace period.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        with pytest.raises(requests.exceptions.RequestException):
            call(emulator, json_body={"caller-number": number_for(592)})

        assert wait_until_refusing(emulator.port), (
            "592 was served but the port is still accepting connections."
        )

    def test_591_drops_the_listener(self, emulator: EmulatorProcess) -> None:
        """591 must close the listening socket without answering.

        Only the immediate half of the contract is asserted. The documented
        recovery is 60 seconds later, and a minute of wall clock buys no extra
        confidence on every push; the emulator's own README records that the
        restart is unreliable in a single-threaded server, so asserting it would
        pin behaviour the implementation does not actually guarantee.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The request fails rather than returning a response.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        with pytest.raises(requests.exceptions.RequestException):
            call(emulator, json_body={"caller-number": number_for(591)})


class TestResponseContract:
    """Shape guarantees a consumer can rely on."""

    def test_responses_declare_a_json_content_type(
        self, emulator: EmulatorProcess
    ) -> None:
        """Every served response must be announced as JSON.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The ``Content-type`` header is ``application/json``.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(emulator, json_body={"caller-number": number_for(200)})
        assert response.headers["Content-type"] == "application/json"

    def test_response_body_is_parseable_json(
        self, emulator: EmulatorProcess
    ) -> None:
        """The declared content type must be honoured by the body.

        A service that announces JSON and returns something else forces every
        consumer into defensive parsing.

        Preconditions:
            - A freshly started emulator is accepting connections.

        Assertions:
            - The body parses as JSON and is an object.

        Args:
            emulator (EmulatorProcess): A freshly started emulator.

        Returns:
            None
        """
        response = call(emulator, json_body={"caller-number": number_for(200)})
        assert isinstance(json.loads(response.text), dict)
