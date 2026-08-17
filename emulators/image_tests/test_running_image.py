"""Behavioural coverage for a running container, not for the source.

The seam this closes
--------------------
Two things were already checked and neither covered the gap between them. The
suite in ``emulators/tests`` exercises the Flask simulator's *source*, through
the WSGI client and a loopback server. A scheduled test in
`PlaywrightAPWebsiteAutomation <https://github.com/apolskiy/PlaywrightAPWebsiteAutomation>`_
reads the *published image's* dependency closure straight from the registry. An
image built from stale source, or one whose ``CMD`` no longer starts, would
satisfy both: the source is fine, the layers carry the right packages, and
nothing ever asked the artifact to answer a request.

So every expectation here is imported from the source tree and asserted against
a container over HTTP. That direction is the entire point. These tests do not
re-check that the *code* is right - the other suite does that, in a fraction of
the time and without a container. They check that the *artifact agrees with the
code it claims to be built from*, which is a question only a running image can
answer.

Kept outside ``testpaths`` so an ordinary ``pytest`` run neither collects nor
skips them; see this directory's ``conftest.py``.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Final

import pytest
import requests

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

#: Every code this commit's source advertises. The container must agree.
ALL_SUPPORTED_CODES: Final[list[int]] = sorted(SUPPORTED_ERROR_CODES)

#: Per-request timeout. Must exceed the delay exercised below, or the assertion
#: would trip the client rather than measure the service.
REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0

#: Delay used by the latency assertion, in milliseconds.
DELAY_UNDER_TEST_MS: Final[int] = 500

#: Slack when measuring an applied delay, covering timer granularity.
TIMER_TOLERANCE_MS: Final[int] = 25


class TestServedStatuses:
    """The container serves the status set this commit's source declares."""

    @pytest.mark.test_id("PAP_10001")
    @pytest.mark.parametrize("code", ALL_SUPPORTED_CODES)
    def test_container_serves_every_advertised_code(
        self, image_base_url: str, code: int
    ) -> None:
        """Each advertised code must come back from the container verbatim.

        Parameterized from the source's own mapping, so an image built before a
        code was added or removed fails here naming the code, rather than
        passing because both halves were checked separately.

        Preconditions:
            - ``code`` appears in this commit's supported set.

        Assertions:
            - The container answers with that exact status.

        Args:
            image_base_url (str): Base URL of the running container.
            code (int): A status code the source advertises.

        Returns:
            None
        """
        response = requests.get(
            f"{image_base_url}/error/{code}", timeout=REQUEST_TIMEOUT_SECONDS
        )
        assert response.status_code == code, (
            f"Source advertises {code}; the running image answered "
            f"{response.status_code}. The image and the source it claims to be "
            "built from disagree."
        )

    @pytest.mark.test_id("PAP_10002")
    def test_unsupported_code_returns_404(self, image_base_url: str) -> None:
        """An unlisted code must be reported absent by the container too.

        Preconditions:
            - 402 is outside the supported set.

        Assertions:
            - The container answers 404.

        Args:
            image_base_url (str): Base URL of the running container.

        Returns:
            None
        """
        response = requests.get(
            f"{image_base_url}/error/402", timeout=REQUEST_TIMEOUT_SECONDS
        )
        assert response.status_code == 404

    @pytest.mark.test_id("PAP_10003")
    def test_catalogue_renders(self, image_base_url: str) -> None:
        """The index must render, proving templating works inside the image.

        A status code can be returned by a nearly dead process. Rendering the
        catalogue exercises Jinja and the template, so this is the assertion
        that the image's dependency closure is not merely present but usable.

        Preconditions:
            - The container is serving its index route.

        Assertions:
            - The index answers 200 and carries its heading.
            - It lists a link for every advertised code.

        Args:
            image_base_url (str): Base URL of the running container.

        Returns:
            None
        """
        response = requests.get(f"{image_base_url}/", timeout=REQUEST_TIMEOUT_SECONDS)

        assert response.status_code == 200
        assert "HTTP Error Code Simulator" in response.text
        missing = [
            code for code in ALL_SUPPORTED_CODES if f"/error/{code}" not in response.text
        ]
        assert not missing, f"The container's catalogue omits links for {missing}."


class TestLatencyInImage:
    """Latency injection works in the artifact, not only in the source."""

    @pytest.mark.test_id("PAP_10004")
    def test_requested_delay_is_applied_by_the_container(
        self, image_base_url: str
    ) -> None:
        """The container must sleep the requested time and report it.

        This is the assertion that would have caught an image built before
        latency injection existed: the source has the feature, the closure is
        unchanged either way, and only asking the artifact reveals which one is
        running.

        Preconditions:
            - The delay is within the source's ceiling.

        Assertions:
            - The requested status still arrives.
            - The applied-delay header echoes the request.
            - The measured round trip is at least the requested delay.

        Args:
            image_base_url (str): Base URL of the running container.

        Returns:
            None
        """
        started_at = time.perf_counter()
        response = requests.get(
            f"{image_base_url}/error/503",
            headers={DELAY_REQUEST_HEADER: str(DELAY_UNDER_TEST_MS)},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        assert response.status_code == 503
        assert response.headers[DELAY_APPLIED_HEADER] == str(DELAY_UNDER_TEST_MS)
        assert elapsed_ms >= DELAY_UNDER_TEST_MS - TIMER_TOLERANCE_MS, (
            f"The container returned in {elapsed_ms:.0f}ms despite a "
            f"{DELAY_UNDER_TEST_MS}ms delay being requested."
        )

    @pytest.mark.test_id("PAP_10005")
    def test_undelayed_request_reports_zero(self, image_base_url: str) -> None:
        """Every response must carry the applied-delay header, including zero.

        Preconditions:
            - No delay header is sent.

        Assertions:
            - The header is present and reads zero.

        Args:
            image_base_url (str): Base URL of the running container.

        Returns:
            None
        """
        response = requests.get(
            f"{image_base_url}/error/503", timeout=REQUEST_TIMEOUT_SECONDS
        )
        assert response.headers[DELAY_APPLIED_HEADER] == "0"

    @pytest.mark.test_id("PAP_10006")
    @pytest.mark.parametrize("delay_value", ("abc", "-1", str(MAX_DELAY_MS + 1)))
    def test_uninterpretable_delay_is_refused_by_the_container(
        self, image_base_url: str, delay_value: str
    ) -> None:
        """A delay the image cannot honour must be refused with the sentinel.

        Worth asserting through a real container rather than only through WSGI:
        a non-standard status has to survive the HTTP server on the way out, and
        999 is exactly the kind of value a stack might normalise.

        Preconditions:
            - ``delay_value`` is not a whole, non-negative, in-range number.

        Assertions:
            - The container answers the sentinel, not the requested 503, and
              specifically not a 500.

        Args:
            image_base_url (str): Base URL of the running container.
            delay_value (str): A delay header value the image must refuse.

        Returns:
            None
        """
        response = requests.get(
            f"{image_base_url}/error/503",
            headers={DELAY_REQUEST_HEADER: delay_value},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        assert response.status_code == UNINTERPRETABLE_REQUEST, (
            f"Delay {delay_value!r} produced {response.status_code} from the "
            f"container; expected the {UNINTERPRETABLE_REQUEST} sentinel."
        )
