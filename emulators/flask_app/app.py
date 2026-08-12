"""Flask HTTP error-code simulator with configurable response latency.

Returns any advertised status on demand, selected by URL, and will answer late
by a caller-specified number of milliseconds. The catalogue at ``/`` lists every
supported code as a clickable link and documents the delay header, so the whole
contract is discoverable without reading this file.

Latency injection
-----------------
A client's timeout, retry and backoff code is usually the least-tested part of
it, because a real upstream cannot be asked to be slow on demand. Setting
``X-Response-Delay-Ms`` makes this service answer late by an exact amount, so a
suite can place the delay either side of its own timeout and assert the branch
it actually cares about.

This is deliberately *not* the same capability as the caller-number emulator's
``590``. That code accepts a connection and never answers at all, which is the
right shape for proving a client eventually gives up. A bounded delay is the
right shape for everything nearer the boundary: a response that is slow but
valid, a retry that should not fire, a backoff that should. The two are
complementary rather than redundant.

A malformed or out-of-range delay is rejected with the ``999`` sentinel this
repository uses everywhere for "your request was uninterpretable", never with
the status that was asked for. Silently ignoring a bad header would be the worst
outcome available: the caller's timeout test would pass while proving nothing,
which is precisely the failure this service exists to prevent. Unlike the
caller-number emulator, a rejection here does *not* terminate the process - this
service is a shared container answering many callers, and one bad request must
not take it away from the rest.
"""

from __future__ import annotations

import time
from typing import Final

from flask import Flask, abort, g, render_template_string, request
from werkzeug.exceptions import HTTPException

SUPPORTED_ERROR_CODES: Final[dict[int, str]] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    419: "Insufficient Space on Resource",
    500: "Internal Server Error",
    501: "Not Implemented",
    503: "Service Unavailable",
    600: "Custom Error",
}

#: Request header a caller sets to make the simulator answer late, in
#: milliseconds. Absent means answer immediately.
DELAY_REQUEST_HEADER: Final[str] = "X-Response-Delay-Ms"

#: Response header carrying the delay that was actually applied. Present on
#: every response, including the ones that were not delayed, so a consuming
#: suite can assert the delay took effect rather than infer it from a stopwatch
#: that also measured its own scheduling noise.
DELAY_APPLIED_HEADER: Final[str] = "X-Applied-Delay-Ms"

#: Ceiling on a requested delay. A public container must not be parkable
#: indefinitely by a single request, and no legitimate client timeout under test
#: is longer than this. Requests above the ceiling are refused rather than
#: clamped: a caller who asked for 60s and silently received 30s would draw a
#: conclusion about their timeout that the run did not support.
MAX_DELAY_MS: Final[int] = 30_000

#: Status returned when the delay header cannot be honoured as written. Outside
#: the HTTP range on purpose, so it can never be mistaken for a status the
#: caller asked this service to produce. Shared vocabulary with the
#: caller-number emulator, where 999 means the same thing.
UNINTERPRETABLE_REQUEST: Final[int] = 999

app = Flask(__name__)


class DelayHeaderError(ValueError):
    """Raised when the delay header cannot be honoured exactly as written.

    Carried as an exception rather than returned as a sentinel value so the
    reason travels with the refusal and reaches the caller verbatim.
    """


def _resolve_requested_delay(raw_header_value: str) -> int:
    """Parse and range-check the caller's requested delay.

    Args:
        raw_header_value (str): Verbatim value of the ``X-Response-Delay-Ms``
            request header.

    Returns:
        int: The delay to apply, in milliseconds.

    Raises:
        DelayHeaderError: If the value is not a whole non-negative number of
            milliseconds, or exceeds :data:`MAX_DELAY_MS`.
    """
    try:
        requested_delay_ms = int(raw_header_value)
    except ValueError as parse_failure:
        raise DelayHeaderError(
            f"{DELAY_REQUEST_HEADER} must be a whole number of milliseconds; "
            f"received {raw_header_value!r}. No status was served, because a delay "
            "this service could not honour must never be mistaken for the response "
            "you asked for."
        ) from parse_failure

    if requested_delay_ms < 0:
        raise DelayHeaderError(
            f"{DELAY_REQUEST_HEADER} must not be negative; received "
            f"{requested_delay_ms}."
        )

    if requested_delay_ms > MAX_DELAY_MS:
        raise DelayHeaderError(
            f"{DELAY_REQUEST_HEADER} of {requested_delay_ms}ms exceeds this "
            f"service's ceiling of {MAX_DELAY_MS}ms. The request is refused rather "
            "than shortened, so a timeout assertion is never built on a delay that "
            "did not happen."
        )

    return requested_delay_ms


@app.before_request
def delay_response_if_requested():
    """Sleep for the caller's requested delay before the route runs.

    Applied to every route rather than only ``/error/<code>``: a consumer
    testing a slow catalogue, a slow 404 or a slow success needs the same
    control as one testing a slow 503.

    A refusal is returned from here rather than raised through ``abort``.
    Werkzeug's ``abort`` resolves a code to a registered exception class and
    has none for :data:`UNINTERPRETABLE_REQUEST`, so aborting on it would be
    caught by this application's own catch-all handler and rendered as a 500 -
    the one status that means "the simulator broke", which is precisely the
    message a rejected delay must not send.

    Returns:
        tuple[str, int] | None: A :data:`UNINTERPRETABLE_REQUEST` response when
        the header cannot be honoured, which short-circuits the route; None to
        let the request proceed.
    """
    g.applied_delay_ms = 0
    raw_header_value = request.headers.get(DELAY_REQUEST_HEADER)
    if raw_header_value is None:
        return None

    try:
        requested_delay_ms = _resolve_requested_delay(raw_header_value)
    except DelayHeaderError as rejection:
        return (
            f"<h1>{UNINTERPRETABLE_REQUEST}: Uninterpretable Request</h1>"
            f"<p>{rejection}</p>",
            UNINTERPRETABLE_REQUEST,
        )

    if requested_delay_ms:
        time.sleep(requested_delay_ms / 1000)
    g.applied_delay_ms = requested_delay_ms
    return None


@app.after_request
def report_applied_delay(response):
    """Record the delay that was applied on the outgoing response.

    Args:
        response (flask.Response): The response about to be returned.

    Returns:
        flask.Response: The same response, carrying
        :data:`DELAY_APPLIED_HEADER`.
    """
    response.headers[DELAY_APPLIED_HEADER] = str(getattr(g, "applied_delay_ms", 0))
    return response


@app.route("/")
def index():
    """Render the catalogue of supported codes and the delay contract.

    Returns:
        str: Rendered HTML listing every supported status as a link, plus the
        latency-injection header, its ceiling, and its rejection behaviour.
    """
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>HTTP Error Code Simulator</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            /* Force table to fit screen width and prevent horizontal scrolling */
            .table-container {
                width: 100%;
                max-width: 800px; /* Optional: keeps table from getting too wide on desktop */
                margin: auto;
            }
            table {
                width: 100%;
                table-layout: fixed; /* Ensures columns respect the width */
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
                word-wrap: break-word; /* Prevents long text from pushing table width */
                overflow: hidden;
            }
            tr:nth-child(even) { background-color: #f9f9f9; }
            th { background-color: #4CAF50; color: white; }
            code { background-color: #f4f4f4; padding: 2px 5px; }
            .latency { max-width: 800px; margin: 20px auto; }
        </style>
    </head>
    <body>
        <h1 align="center">HTTP Error Code Simulator</h1>
        <p align="center">Click a link below to see the error page and its status code
           or go to /error/code url:</p>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">Code</th>
                        <th style="width: 50%;">Description</th>
                        <th style="width: 30%;">Link</th>
                    </tr>
                 </thead>
                <tbody>
                    {% for code, desc in codes.items() %}
                    <tr>
                        <td>{{ code }}</td>
                        <td>{{ desc }}</td>
                        <td><a href="/error/{{ code }}">Test {{ code }} code</a></td>
                    </tr>
                    {% endfor %}
                 </tbody>
            </table>
        </div>
        <div class="latency">
            <h2>Answering late</h2>
            <p>Send <code>{{ delay_header }}</code> on any request to make this
               service answer that many milliseconds late. Every response reports
               what was actually applied in <code>{{ applied_header }}</code>.</p>
            <p>The ceiling is <strong>{{ max_delay }}ms</strong>. A value that is not
               a whole non-negative number, or one above the ceiling, is refused with
               status <strong>{{ sentinel }}</strong> and no delay - never with the
               status you asked for, so a timeout test cannot pass on a delay that
               never happened.</p>
        </div>
    </body>
    </html>
        """

    return render_template_string(
        html_template,
        codes=SUPPORTED_ERROR_CODES,
        delay_header=DELAY_REQUEST_HEADER,
        applied_header=DELAY_APPLIED_HEADER,
        max_delay=MAX_DELAY_MS,
        sentinel=UNINTERPRETABLE_REQUEST,
    )


@app.route("/error/<int:code>")
def return_status_code(code):
    """Return the requested HTTP status code.

    Args:
        code (int): Status code parsed from the URL.

    Returns:
        tuple[str, int]: The rendered body and the requested status, when the
        code is advertised.

    Raises:
        werkzeug.exceptions.NotFound: If the code is not in the supported set,
        so the advertised set stays discoverable by probing.
    """
    if code in SUPPORTED_ERROR_CODES:
        description = SUPPORTED_ERROR_CODES[code]
        return f"<h1>{code} - {description}</h1>", code

    # If the return code is not on the list
    abort(404)


@app.errorhandler(Exception)
def handle_exception(error):
    """Render aborts with their own status and genuine faults as a 500.

    Args:
        error (Exception): The exception raised while handling the request.

    Returns:
        tuple[str, int]: The rendered body and the status to send.
    """
    # 1. If it's a Flask HTTP error (like from abort(404)), use its own data
    if isinstance(error, HTTPException):
        # Access .code and .name safely from the HTTPException object
        return f"<h1>{error.code}: {error.name}</h1><p>{error.description}</p>", error.code

    # 2. If it's a real code error (e.g., ZeroDivisionError), return a 500
    # This prevents the handler from crashing and hiding the real issue
    return ("<h1>500: Internal Server Error</h1><p>The "
            "server encountered an unexpected condition.</p>"), 500


if __name__ == "__main__":
    app.run(debug=True)
