# PublicAP
#Aleksandr Polskiy

Practice and utility scripts, plus two **HTTP service emulators** built to make failure conditions reproducible on demand. Real upstream services fail on their own schedule; these let a test suite ask for a specific failure and get it every time.

- [`practice/custom_header_response_to_http_request.py`](practice/custom_header_response_to_http_request.py) — stdlib HTTP server driven by a caller-number payload
- [`flask_app/`](flask_app) — Flask HTTP error-code simulator, published to Docker Hub as [`apolskiy/flask_app`](https://hub.docker.com/r/apolskiy/flask_app)

---

## 1. Caller-Number HTTP Emulator

`practice/custom_header_response_to_http_request.py` — a single-file server on **port 8080** built on `http.server` / `socketserver.TCPServer`, with no third-party dependencies.

```bash
python practice/custom_header_response_to_http_request.py
```

### How the status code is chosen

The response status is **the last three digits of the `caller-number` field** in the JSON request body. This models telephony-style routing, where the dialed number determines the outcome under test:

```bash
# 18884400201 -> 201
curl -X POST http://localhost:8080 \
     -H "Content-Type: application/json" \
     -d '{"caller-number": "18884400201"}'

# 18884400503 -> 503
curl -X GET http://localhost:8080 \
     -H "Content-Type: application/json" \
     -d '{"caller-number": "18884400503"}'
```

With no request body, the server falls back to the **`X-Caller-Number`** header, read as the status code directly:

```bash
curl -X GET http://localhost:8080 -H "X-Caller-Number: 404"
```

All five verbs — **GET, POST, PUT, DELETE, PATCH** — route through the same logic, so any code can be exercised against any method.

### Behaviour by code

| Code | Behaviour |
| --- | --- |
| `201` | Returns `{"session_id": "<uuid4>"}` — emulates session creation with a fresh identifier per call |
| `590` | Sleeps **120 seconds** without responding — the caller sees a hung backend and must handle its own timeout |
| `591` | Closes the listening socket, waits **60 seconds**, then attempts to serve again — emulates a service bounce mid-suite |
| `592` | Closes the socket and exits — emulates a service that goes away and stays away |
| `999` | Sentinel for "the request could not be interpreted" (see below) |
| any other | Echoes `{"status": "Response with code N"}` with `N` as the HTTP status |

Codes at or above 600 are served but logged as a warning, since they fall outside the valid HTTP range.

### The 999 sentinel

`999` is a deliberately out-of-band code, chosen so a client can never confuse "the emulator rejected my request" with a status the emulator was *asked* to produce. It is returned when:

- the JSON body has no `caller-number` field
- `caller-number` is shorter than three characters
- the last three characters are not digits
- the body is not valid JSON
- no body and no `X-Caller-Number` header were supplied
- any unexpected exception occurs while handling the request

After sending a `999` the process exits non-zero, so a misconfigured test run fails loudly instead of continuing against a server in an unknown state.

### Known limitation

The server is **single-threaded** by design, which is what makes `590` a genuine stall — the sleep blocks the whole process, exactly as an unresponsive upstream would. The same property limits `591` and `592`: as noted in the script's own closing comment, fully restarting a listener from inside its own request handler is not reliably achievable in this model, and a threaded server or a process supervisor would be needed to make the bounce robust. Use `590` and the standard codes for automated runs; treat `591` and `592` as manual exercises.

---

## 2. Flask HTTP Error Code Simulator

`flask_app/app.py` — a Flask service that returns any of **21 supported status codes** on request, with a browsable index page listing every one as a clickable link.

```bash
cd flask_app
pip install flask
flask run --port=4000
```

Then open <http://localhost:4000/> for the table, or request a code directly:

```bash
curl -i http://localhost:4000/error/503
```

### Supported codes

| Class | Codes |
| --- | --- |
| 4xx client | `400` `401` `403` `404` `405` `406` `408` `409` `410` `411` `412` `413` `414` `415` `416` `417` `419` |
| 5xx server | `500` `501` `503` |
| Non-standard | `600` (Custom Error) — verifies that a client handles a status outside the registered range |

`402 Payment Required` and `407 Proxy Authentication Required` are absent from the set; every code present is reachable without a payment or proxy layer in front of the service. `419` is likewise non-standard (Insufficient Space on Resource), included because it appears in the wild from some WebDAV and framework stacks.

Requesting an unlisted code returns **404**, so the supported set is discoverable by probing rather than only by reading the source.

### Error handling

A single `@app.errorhandler(Exception)` distinguishes the two cases that matter when a simulator misbehaves:

- a `werkzeug.exceptions.HTTPException` (any `abort()`) is rendered with its own code and name
- a genuine Python error becomes a **500**, rather than escaping and hiding the real fault

This is what keeps the simulator honest — a bug in the simulator surfaces as a 500 with a distinct body, not as a corrupted version of the status the caller asked for.

### Containerized use

`flask_app/Dockerfile.dev` builds on `python:3.12`, exposes **4000**, and starts `flask run --host=0.0.0.0`. The published image runs anywhere Docker does, including a CI job:

```bash
docker pull apolskiy/flask_app
docker run --rm -p 4000:4000 apolskiy/flask_app
curl -i http://localhost:4000/error/500
```

Build locally instead:

```bash
docker build -f flask_app/Dockerfile.dev -t flask_app:local flask_app
docker run --rm -p 4000:4000 flask_app:local
```

---

## Choosing between them

| Need | Use |
| --- | --- |
| A specific 4xx/5xx status, repeatedly, over HTTP | Flask simulator |
| A hung connection / client-timeout path | Caller-number emulator, `590` |
| A status tied to request *payload* rather than URL | Caller-number emulator |
| Non-GET verbs (PUT, PATCH, DELETE) | Caller-number emulator |
| Something to run in CI as a container | Flask simulator |
| Zero dependencies, one file, no install | Caller-number emulator |

---

## Repository Layout

```text
PublicAP/
├── practice/                 # Standalone practice scripts
│   └── custom_header_response_to_http_request.py
├── flask_app/
│   ├── app.py                # The error-code simulator
│   ├── Dockerfile.dev        # python:3.12, serves on 4000
│   └── requirements.txt
├── test_scripts/             # Assorted test and exercise scripts
├── playwright/, selenium/    # Browser automation practice
├── scikit-learn/             # ML practice scripts
├── report/                   # JUnit-style XML run reports
└── example.py
```

`practice/with_unit_test_pytest/` holds scripts with pytest unit tests; its `report/` subdirectory contains Jenkins-compatible XML run reports.

---

## Notes

`flask_app/requirements.txt` is a full environment freeze rather than the app's actual dependency set — the simulator itself needs only Flask and its transitive dependencies. Installing the file pulls in Jupyter, pandas, scikit-learn, SQLAlchemy, and matplotlib, which is why the container image is far larger than a small Flask app warrants. Narrowing it to `Flask` before treating the image as a lightweight CI dependency is worthwhile.
