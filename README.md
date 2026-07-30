# PublicAP
#Aleksandr Polskiy

**Test infrastructure: two HTTP service emulators that make failure conditions reproducible on demand.**

Real upstream services fail on their own schedule. A suite that needs to prove it handles a 503, a rate limit, or a hung connection cannot wait for one to happen, and cannot rely on a mock that only proves the mock works. These emulators speak real HTTP over a real socket, and return exactly the failure asked of them, every time.

| Emulator | Transport | Selects response by | Use it for |
| --- | --- | --- | --- |
| [`emulators/custom_header_response_to_http_request.py`](emulators/custom_header_response_to_http_request.py) | Python stdlib `http.server`, port 8080 | Request **payload** (`caller-number`) or `X-Caller-Number` header | Hung connections, service restarts, any verb, session creation |
| [`emulators/flask_app/`](emulators/flask_app) | Flask, port 4000, containerized | Request **URL** (`/error/<code>`) | Deterministic 4xx/5xx status handling, browsable catalogue |

Published image: [`apolskiy/flask_app`](https://hub.docker.com/r/apolskiy/flask_app) on Docker Hub.

> The `practice/` tree is unrelated: standalone algorithm and exercise scripts kept for reference. Nothing in `emulators/` depends on it. See [Practice scripts](#practice-scripts) at the end.

---

## 1. Caller-Number Emulator

A single file, no third-party dependencies, one socket.

```bash
python emulators/custom_header_response_to_http_request.py
# Serving at port 8080...
```

### Selecting a response

The status code is **the last three digits of the `caller-number` field** in the JSON body. The design models telephony-style routing, where the dialled number determines the outcome under test, so a suite can carry a table of numbers instead of a table of URLs.

```bash
# 18884400201 -> 201
curl -X POST http://localhost:8080 \
     -H "Content-Type: application/json" \
     -d '{"caller-number": "18884400201"}'
```

With no body, the emulator reads the **`X-Caller-Number`** header as the code directly:

```bash
curl -i -X GET http://localhost:8080 -H "X-Caller-Number: 503"
```

**GET, POST, PUT, DELETE and PATCH** all route through the same logic, so any code can be exercised against any verb.

### Control codes

| Code | Behaviour | Response sent | What it emulates |
| --- | --- | --- | --- |
| `201` | Returns `{"session_id": "<uuid4>"}` | yes | Session creation, fresh identifier per call |
| `590` | Sleeps **120 s** | no | An upstream that accepted the connection and stopped answering |
| `591` | Closes the socket, waits **60 s**, serves again | no | A service bounce mid-suite |
| `592` | Closes the socket and exits | no | A service that goes away and stays away |
| `999` | Error envelope, then exits non-zero | yes | "Your request was uninterpretable" (see below) |
| any other | `{"status": "Response with code N"}` with status `N` | yes | Any standard status |

Codes at or above 600 are still served, with a warning logged, since they fall outside the valid HTTP range.

### The 999 sentinel

`999` is deliberately outside the HTTP range so a client can never confuse *"the emulator rejected my request"* with a status the emulator was **asked** to produce. It is returned when:

- the JSON body carries no `caller-number`
- `caller-number` is shorter than three characters
- its last three characters are not digits
- the body is not valid JSON
- neither a body nor an `X-Caller-Number` header was supplied
- any unexpected exception occurs while handling the request

The process then exits non-zero, so a misconfigured suite fails loudly instead of running on against a server in an unknown state.

### Known limitation

The server is **single-threaded**, which is exactly what makes `590` a genuine stall: the sleep blocks the whole process, as an unresponsive upstream would. The same property limits `591` and `592`. As the script's own closing comment records, restarting a listener from inside its own request handler is not reliably achievable in this model; a threaded server or a process supervisor would be needed to make the bounce robust.

**Use `590` and the standard codes in automated runs. Treat `591` and `592` as manual exercises.**

---

## 2. Flask Error Code Simulator

Returns any of **21 supported status codes**, with a browsable index page listing each one as a clickable link.

```bash
pip install -r emulators/flask_app/requirements.txt
flask --app emulators/flask_app/app.py run --port=4000
```

```bash
curl -i http://localhost:4000/error/503      # -> HTTP/1.1 503 SERVICE UNAVAILABLE
open http://localhost:4000/                  # the catalogue
```

### Supported codes

| Class | Codes |
| --- | --- |
| 4xx client | `400` `401` `403` `404` `405` `406` `408` `409` `410` `411` `412` `413` `414` `415` `416` `417` `419` |
| 5xx server | `500` `501` `503` |
| Non-standard | `600` (Custom Error) |

`402 Payment Required` and `407 Proxy Authentication Required` are absent: every code present is reachable without a payment or proxy layer in front of the service. `419` (Insufficient Space on Resource) is non-standard but appears in the wild from some WebDAV and framework stacks. `600` exists to prove a client handles a status outside the registered range rather than crashing on it.

Requesting an unlisted code returns **404**, so the supported set is discoverable by probing rather than only by reading the source.

### Error handling

One `@app.errorhandler(Exception)` separates the two cases that matter when a simulator misbehaves:

- a `werkzeug.exceptions.HTTPException` (any `abort()`) renders with its own code and name
- a genuine Python error becomes a **500**, instead of escaping and hiding the real fault

That is what keeps the simulator honest: a bug in the simulator surfaces as a distinct 500, not as a corrupted version of the status the caller asked for.

### Docker

```bash
# Published image
docker pull apolskiy/flask_app
docker run --rm -p 4000:4000 apolskiy/flask_app
curl -i http://localhost:4000/error/500

# Build locally
docker build -f emulators/flask_app/Dockerfile.dev -t flask_app:local emulators/flask_app
docker run --rm -p 4000:4000 flask_app:local

# Detached, for a CI job that needs it up for the duration
docker run -d --name errsim -p 4000:4000 apolskiy/flask_app
docker stop errsim && docker rm errsim
```

The image builds on `python:3.12`, exposes **4000**, and starts `flask run --host=0.0.0.0` so it is reachable from outside the container.

As a GitHub Actions service container:

```yaml
jobs:
  contract-tests:
    runs-on: ubuntu-latest
    services:
      error-simulator:
        image: apolskiy/flask_app
        ports:
          - 4000:4000
    steps:
      - uses: actions/checkout@v7
      - run: pytest tests/test_error_handling.py
```

---

## Example consumer tests

Illustrations of how a suite consumes these emulators. They are examples for a *consuming* project, not tests of this repository.

**Every 5xx your client claims to handle, actually handled:**

```python
import pytest
import requests

SIMULATOR = "http://localhost:4000"

@pytest.mark.parametrize("status", [500, 501, 503])
def test_client_surfaces_server_errors(status):
    """The client must raise rather than return a body on a 5xx."""
    with pytest.raises(requests.HTTPError):
        response = requests.get(f"{SIMULATOR}/error/{status}", timeout=5)
        response.raise_for_status()
```

**A status outside the registered range does not crash the client:**

```python
def test_client_tolerates_non_standard_status():
    """600 is not a registered status; the client must still return cleanly."""
    response = requests.get(f"{SIMULATOR}/error/600", timeout=5)
    assert response.status_code == 600
```

**The retry path is actually exercised, not just present in the code:**

```python
def test_client_retries_then_gives_up(caplog):
    """A permanent 503 must exhaust the retry budget, not loop forever."""
    session = build_session_under_test(max_retries=3)   # your production client
    with pytest.raises(requests.RetryError):
        session.get(f"{SIMULATOR}/error/503", timeout=5)
    assert caplog.text.count("Retrying") == 3
```

**A hung upstream trips the client timeout, not the suite timeout** - the case a mock cannot reproduce, because the connection has to genuinely stay open:

```python
EMULATOR = "http://localhost:8080"

def test_client_times_out_against_a_hung_upstream():
    """590 accepts the connection and never answers; the client must give up."""
    with pytest.raises(requests.Timeout):
        requests.post(
            EMULATOR,
            json={"caller-number": "18884400590"},   # last 3 digits select 590
            timeout=5,                               # must be well under the 120s stall
        )
```

**A malformed request is distinguishable from a requested failure:**

```python
def test_emulator_reports_uninterpretable_requests_as_999():
    """999 proves the request was rejected, not that 4xx was asked for."""
    response = requests.post(EMULATOR, json={"wrong-field": "1"}, timeout=5)
    assert response.status_code == 999
```

---

## Choosing between them

| Need | Use |
| --- | --- |
| A specific 4xx/5xx status, repeatedly | Flask simulator |
| A hung connection / client-timeout path | Caller-number emulator, `590` |
| A status selected by request *payload* rather than URL | Caller-number emulator |
| Non-GET verbs (PUT, PATCH, DELETE) | Caller-number emulator |
| A container in CI | Flask simulator |
| Zero dependencies, one file, no install | Caller-number emulator |
| Session-creation response with a unique id | Caller-number emulator, `201` |

---

## Repository layout

```text
PublicAP/
├── emulators/                    # Test infrastructure - the subject of this README
│   ├── custom_header_response_to_http_request.py   # Caller-number emulator, port 8080
│   └── flask_app/
│       ├── app.py                # Error-code simulator, port 4000
│       ├── Dockerfile.dev        # python:3.12
│       └── requirements.txt      # Flask only
└── practice/                     # Unrelated: see below
```

---

## Practice scripts

`practice/` holds standalone algorithm and exercise scripts, kept for reference and unrelated to the emulators above. `practice/with_unit_test_pytest/` contains scripts with pytest unit tests, and its `report/` subdirectory holds Jenkins-compatible XML run reports. Also present at the repository root: `test_scripts/`, `playwright/`, `selenium/`, `scikit-learn/`, and `report/`.

Nothing in `emulators/` imports from any of these.
