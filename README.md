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

> **Documentation status:** describes **v1.0.0**, reviewed 2026-08-10.
> Each section below carries the release and date its content last changed, so a
> reader arriving at a later version can see at a glance which parts moved. This
> file always describes the *current* release; release-to-release history lives
> in [CHANGELOG.md](CHANGELOG.md).

---

## 1. Caller-Number Emulator

<sub>v1.0.0 &middot; 2026-08-10</sub>

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

<sub>v1.0.0 &middot; 2026-08-10</sub>

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

The image builds on `python:3.14.4-slim`, exposes **4000**, and starts `flask run --host=0.0.0.0` so it is reachable from outside the container.

The published image carries Flask and its six transitive dependencies and nothing else. Nothing from `requirements-dev.txt` reaches it: the `requirements.txt` beside the Dockerfile pins Flask alone, and the dev dependencies stay at the repository root where the build never looks. A `.dockerignore` sits at the build-context root - `emulators/flask_app/`, the directory passed to `docker build`, not the repository root - so a local `venv/`, `__pycache__/` or stray `*.log` is never copied into a public artifact. Docker only reads `.dockerignore` from the context root, which is the whole reason its placement matters. Together with the slim base these took the published download from 397 MB to 46 MB.

> **Provenance.** The emulators and their test suites are original work; no emulator source file has been modified with AI assistance. Such assistance in this repository is limited to container build configuration - the `.dockerignore` rules, a corrected comment in `Dockerfile.dev` - and the wording of this Docker section. Commit `5b84be9a` carries a `Co-Authored-By` trailer for that reason; its diff is five lines.

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

<sub>v1.0.0 &middot; 2026-08-10</sub>

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

## Testing the emulators

<sub>v1.0.0 &middot; 2026-08-10</sub>

[![Emulator Test Suite](https://github.com/apolskiy/PublicAP/actions/workflows/emulator-tests.yml/badge.svg)](https://github.com/apolskiy/PublicAP/actions/workflows/emulator-tests.yml)

**93 end-to-end tests** covering both emulators.

```bash
pip install -r requirements-dev.txt
pytest                                    # both suites
pytest emulators/tests/test_flask_error_simulator.py
pylint --fail-under=10 emulators/tests emulators/flask_app/app.py \
       emulators/custom_header_response_to_http_request.py
```

### Isolation strategy

The two emulators are tested in opposite ways, and the difference is not stylistic.

The **Flask simulator** is a pure request/response service, so its 21-code matrix runs through the WSGI test client: no socket, no port, nothing that can flake. Two assertions run it on a real loopback socket, because a WSGI client proves the logic but not that the service speaks HTTP.

The **caller-number emulator** deliberately blocks or kills its own process - `999` exits non-zero, `592` exits zero, `590` blocks the single-threaded server for two minutes. **Every test therefore gets its own subprocess on its own ephemeral port.** Sharing one would make each result depend on which destructive test ran first, which is a sequence rather than a suite.

Determinism is enforced rather than assumed:

- Readiness is established by **polling the socket**, never by sleeping. A fixed sleep is either slower than necessary or shorter than reality, and usually becomes both on a loaded runner.
- The `590` stall is asserted through a short **client-side timeout**; waiting out the full 120 seconds would prove nothing extra and would make the suite unusable in CI.
- `pytest-randomly` shuffles collection order every run, and CI does a second pass under a fixed seed. An order-dependent suite fails instead of passing by luck.
- Emulator output goes to a **file, not a pipe** - an undrained pipe eventually fills and blocks the emulator mid-request, surfacing as an inexplicable timeout somewhere else.

### What is covered

| Suite | Tests | Focus |
| --- | --- | --- |
| `test_flask_error_simulator.py` | 59 | Every advertised code returned verbatim; bodies naming code and description; unsupported codes and unroutable paths resolving to 404; the catalogue linking every code; real-HTTP reachability |
| `test_caller_number_emulator.py` | 34 | Payload-driven status selection across 12 codes and all 5 verbs; `X-Caller-Number` fallback and body precedence; UUID4 session uniqueness; all four `999` paths including the non-zero process exit; the `590` stall, `592` shutdown and `591` listener drop; JSON content-type contract |

CI runs the suites on a matrix of **Ubuntu and Windows** against **Python 3.12 and 3.14**, with `fail-fast` disabled: socket binding and process-termination semantics differ per platform, and that is precisely what the caller-number emulator relies on. Static analysis runs first as a blocking gate, so a hygiene regression fails before any process is spawned.

### Note on the port

The caller-number emulator reads `EMULATOR_PORT`, defaulting to **8080**. The default is unchanged; the override exists so a test run - or a second instance - can bind an ephemeral port instead of colliding.

---

## Choosing between them

<sub>v1.0.0 &middot; 2026-08-10</sub>

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

<sub>v1.0.0 &middot; 2026-08-10</sub>

```text
PublicAP/
├── .github/workflows/
│   └── emulator-tests.yml        # Lint gate + both suites, OS/Python matrix
├── emulators/                    # Test infrastructure - the subject of this README
│   ├── custom_header_response_to_http_request.py   # Caller-number emulator, port 8080
│   ├── flask_app/
│   │   ├── app.py                # Error-code simulator, port 4000
│   │   ├── Dockerfile.dev        # python:3.14.4-slim
│   │   ├── .dockerignore         # At the build-context root, where Docker reads it
│   │   └── requirements.txt      # Flask only
│   └── tests/
│       ├── conftest.py           # Isolation fixtures
│       ├── emulator_control.py   # Process control and readiness helpers
│       ├── test_caller_number_emulator.py
│       └── test_flask_error_simulator.py
├── .pylintrc                     # Static analysis, gated at 10.00/10
├── pytest.ini
├── requirements-dev.txt          # Test dependencies
└── practice/                     # Unrelated: see below
```

---

## Practice scripts

<sub>v1.0.0 &middot; 2026-08-10</sub>

`practice/` holds standalone algorithm and exercise scripts, kept for reference and unrelated to the emulators above. `practice/with_unit_test_pytest/` contains scripts with pytest unit tests, and its `report/` subdirectory holds Jenkins-compatible XML run reports. Also present at the repository root: `test_scripts/`, `playwright/`, `selenium/`, `scikit-learn/`, and `report/`.

Nothing in `emulators/` imports from any of these.
