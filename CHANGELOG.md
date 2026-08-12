# Changelog

All notable changes to the emulators are recorded here. `README.md` always
describes the **current** release and nothing else; this file is where
release-to-release history lives, so the README never accumulates a sediment of
"as of version X" qualifiers.

Each README section carries the release and date its content last changed
(`<sub>v1.0.0 &middot; 2026-08-10</sub>`). Together the two answer different
questions: the stamp tells a reader arriving at a later version *which sections
moved*, and an entry here tells them *what changed and why*. A changelog entry
alone does not tell you where to look.

Versions follow [Semantic Versioning](https://semver.org/) as applied to test
infrastructure other suites depend on:

- **Major** - a change to a status code, control code, or endpoint that an
  existing consumer's assertions would no longer match.
- **Minor** - a new code, endpoint, or capability.
- **Patch** - fixes and documentation corrections that change no behaviour.

This scope covers `emulators/` only. The `practice/` tree is unrelated
standalone scripts and is not versioned.

Dates are **UTC**, matching git commit dates and CI runners, so a stamp written
in the evening in one timezone still agrees with the commit that carries it.

---

## v1.1.0 - 2026-08-12

Latency injection in the Flask simulator. A **Minor** release: the capability is
new, and no existing consumer's assertions change. A request that sends no
`X-Response-Delay-Ms` header behaves exactly as it did in v1.0.0.

### Added

- **Configurable response latency on the Flask simulator.**
  `X-Response-Delay-Ms` on any request makes the service answer that many
  milliseconds late; every response reports what was applied in
  `X-Applied-Delay-Ms`, including `0`. The reported figure is what makes a delay
  assertable without a stopwatch that would also be measuring the test runner's
  own scheduling. The delay applies to every route, not only `/error/<code>`: a
  consumer proving it survives a slow catalogue needs the same control as one
  proving it survives a slow 503.

  The gap this closes is specific. A client's timeout, retry and backoff code is
  usually its least-tested, because a real upstream cannot be asked to be slow on
  demand - and the existing `590` control code, a fixed 120-second stall, can only
  answer "does the client eventually give up". Everything nearer the boundary was
  unreachable: a response slow but valid, a retry that should not fire, a backoff
  that should.

- **Fifteen tests** covering the contract: the delay applied and reported, the
  delay composing with the requested status, application across three routes,
  five classes of uninterpretable value, the ceiling refused rather than clamped,
  the refusal not being reported as a server error, the catalogue documenting the
  contract, and a delayed response measured over a real socket.

### Changed

- **The `flask_server` fixture is now threaded**, matching the published image's
  `flask run --with-threads` default. Before the simulator could be made slow the
  difference was cosmetic; now a single-threaded fixture would serialise behind
  any delayed request and would misrepresent the artifact consumers run.
- **The `Choosing between them` table now distinguishes "never answers" from
  "answers late"** - `590` and `X-Response-Delay-Ms` are complementary, and the
  table previously offered only the first.

### Fixed

- **`app = Flask(__name__)` was executed twice**, at module top and again below
  the status table. Harmless, since the second binding simply replaced the first
  before any route was registered, but it left two objects named `app` in a file
  whose whole subject is which object is serving.
- **A malformed attribute in the catalogue template**, `<th style="width: 30%";>`,
  and a **missing `</html>`**. Browsers recovered from both, which is why they
  survived; a document served by a service that exists to be parsed by test
  clients should not depend on error recovery.

### Notes

- **The refusal status is `999`, not `400`.** Outside the HTTP range on purpose,
  so it can never be confused with a status the service was *asked* to produce -
  `400` would be indistinguishable from `/error/400` working correctly. It is
  also specifically not `500`: `abort()` cannot raise a 999, because Werkzeug
  resolves a code to a registered exception class and has none for it, so an
  implementation reaching for `abort` would land in the catch-all handler and
  report "the simulator broke" when the truth is "your header was wrong". The
  refusal is returned from `before_request` instead. A test pins this.
- **The ceiling refuses rather than clamps.** A caller who asked for 60s, was
  silently given 30s, and saw a 45s timeout not fire would draw a conclusion the
  run did not support.
- **Unlike the caller-number emulator, a rejection does not exit the process.**
  That emulator is spawned per test and failing loudly is right; this one is a
  shared container, and one bad request must not take it away from every other
  caller.
- **No dependency was added.** The delay is `time.sleep` from the standard
  library, so the published image still carries Flask and its six transitive
  dependencies and nothing else, and the scheduled consumer test that reads the
  image asserts the same closure it did before.
- **Provenance boundary moved.** Through v1.0.0 no emulator source file had been
  modified with AI assistance. The latency feature, its tests, the threaded
  fixture and the README's *Answering late* section were written with AI
  assistance; commits carry `Co-Authored-By` trailers. The caller-number emulator
  and every test predating this release remain unassisted. Recorded here and in
  the README because a provenance claim that quietly stops being true is worse
  than one never made.

---

## v1.0.0 - 2026-08-10

First release under version tracking. The emulators predate this file;
commit-level history before this point is in git. This entry records the state
as shipped, and the changes that landed with it.

### Added

- **`CHANGELOG.md` and per-section documentation stamps** in `README.md`.

### Changed

- **The published image shrank 8.6x, from 397 MB to 46 MB**, and the reduction
  is now verified rather than assumed. Three things were wrong at once: a full
  Debian base, a retained pip cache, and an unrelated log file baked in - which
  also leaked a local filesystem path into a public artifact.
- **`.dockerignore` moved to the build-context root**, `emulators/flask_app/`.
  Copies at the repository root and at `emulators/` were inert, because Docker
  reads the file only from the directory passed to `docker build`. Nothing about
  that is visible from a build log: the rules simply never applied, and a
  rebuild from a working directory would have copied a 528 MB local virtual
  environment into a public image. `*.log` was added after an A/B build against
  a deliberately dirtied context proved a stray log still shipped without it.
- **`Dockerfile.dev` moved to `python:3.14.4-slim`.** The README's *Repository
  layout* still described the base as `python:3.12` after the change and has
  been corrected - the prose had been updated, the diagram had not.

### Verified

- The published image carries **Flask and its six transitive dependencies and
  nothing else**, confirmed four independent ways: reading the layer blobs
  straight from the registry, `pip list` inside a running container, an A/B
  build from a deliberately dirtied context, and a scheduled test in a separate
  repository that reads the image rather than trusting the requirements file.
- The consumer assertion lives in
  [PlaywrightAPWebsiteAutomation](https://github.com/apolskiy/PlaywrightAPWebsiteAutomation)
  and runs weekly rather than per push: a dependency regression in a published
  image is a monthly risk, and a deploy signal has no business depending on
  Docker Hub being reachable from a runner.

### Notes

- **Provenance.** The emulators and their test suites are original work; no
  emulator source file has been modified with AI assistance. Such assistance in
  this repository is limited to container build configuration and the wording of
  the Docker section, as recorded in the README.
- The caller-number emulator is single-threaded **by design** - that is what
  makes control code `590` a genuine stall rather than an imitation of one. The
  same property limits `591` and `592`, which remain manual exercises. This is
  documented as a known limitation rather than presented as a feature.
