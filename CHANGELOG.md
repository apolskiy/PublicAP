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

## v1.2.0 - 2026-08-12

Behavioural coverage of the container itself. **Minor**: a new capability of the
test infrastructure, with no change to any emulator's behaviour.

### Added

- **`emulators/image_tests` - 28 assertions against a running container.** Every
  expectation is imported from the source tree and asserted over HTTP, so the
  suite does not re-check that the code is correct. It checks that the artifact
  agrees with the code it claims to be built from: every advertised status
  served verbatim, an unlisted code refused, the catalogue rendering (which
  exercises Jinja rather than merely proving a socket accepts), latency applied
  and reported, and the 999 sentinel surviving a real HTTP server on the way out.

  This closes a seam between two checks that already existed and never met. The
  108 tests in `emulators/tests` exercise the **source**, through the WSGI client
  and a loopback server. The scheduled test in
  [PlaywrightAPWebsiteAutomation](https://github.com/apolskiy/PlaywrightAPWebsiteAutomation)
  reads the **published image's** dependency closure from the registry. An image
  built from stale source, or one whose `CMD` no longer starts, satisfies both:
  the source is fine, the layers carry the right packages, and nothing ever asks
  the artifact to answer a request.

- **`image-tests.yml`, running that suite against two different containers.**
  `built-image` builds from the commit under test, so a broken Dockerfile or app
  fails before anything is published; `published-image` uses
  `apolskiy/flask_app:latest` as a GitHub Actions service container - the pattern
  this README advertises to consumers, applied to this repository's own artifact.

  The `built-image` job also asserts what HTTP cannot see: that the process runs
  as `emulator` rather than root, and that `/app` holds `app.py` and
  `requirements.txt` and nothing else. A root-running image that ships its own
  Dockerfile answers requests perfectly well, which is exactly why those two
  needed a check that is not a request.

### Notes

- **The suite lives outside `testpaths` on purpose.** A plain `pytest` run still
  collects exactly 108 tests and reports no skips. Wiring these in behind a skip
  marker would have added twenty-eight skips to every local run, and a suite that
  always reports skips teaches its reader to stop looking at them.
- **A red `published-image` job usually means "publish", not "fix a test".** It
  compares the published image against the branch's source, so the common cause
  is a merged change that has not been built and pushed yet. That is a real
  signal and deliberately not suppressed: the alternative is a published artifact
  quietly drifting from the source that documents it.
- **`built-image` builds and runs the container by hand rather than declaring it
  as a service.** Service images are pulled before any step executes, so a job
  cannot build an image and then consume it as its own service - the artifact
  would have to be published first, which is the event this job exists to precede.
- The scheduled run is weekly, matching how this portfolio treats every check
  that depends on a third party: registry availability has no business failing a
  push, and image drift is a monthly risk rather than a per-commit one.

---

## v1.1.2 - 2026-08-12

Container hygiene. **Patch**: the emulator's HTTP contract is untouched - same
status codes, same control codes, same delay header, same responses. What
changed is how the image runs and what it carries.

### Changed

- **The container no longer runs as root.** A dedicated `emulator` user (uid
  10001) owns the process. Nothing in this service writes to disk, binds a
  privileged port, or needs ownership of anything, so root bought nothing and
  cost the default review question about every published image.
- **`Dockerfile*` and `.dockerignore` are excluded from the build context copy.**
  `COPY . .` copies the whole context, so the published image had been shipping
  its own Dockerfile and ignore list at `/app` - build inputs inside an artifact
  whose stated claim is that it carries Flask and nothing else. Docker still
  reads the Dockerfile: it is passed with `-f` and was never sourced from the
  copied tree.
- **Output is unbuffered** (`PYTHONUNBUFFERED=1`). Python buffers when it detects
  a pipe rather than a terminal, which is precisely the case under `docker logs`,
  so an emulator's output arrived in bursts after the requests that caused it.
  Log lag is a poor property in a service whose purpose is diagnosing timing.
- **Bytecode writing is disabled** (`PYTHONDONTWRITEBYTECODE=1`). With the
  application directory owned by root and the process running as a normal user,
  the interpreter's attempt to write `__pycache__` would fail and be ignored
  silently. Declining to attempt it is more honest than failing quietly.

### Added

- **A `HEALTHCHECK`**, probing the catalogue route with `urllib` from the
  standard library rather than `curl`, which this slim base does not carry and
  which would mean installing a package into the closure to check on it. The
  catalogue is the honest probe: it exercises template rendering rather than
  merely proving a socket accepts.

### Fixed

- **The `CMD` comment claimed "thin production execution syntax".** It is
  Werkzeug's development server, which is the correct choice here and was being
  described as the opposite of what it is. The comment now states the choice and
  the reason: a production WSGI server would add a dependency to a published
  closure of Flask and six packages, to buy throughput and worker management no
  consumer of a fault-injection emulator has needed.
- A doubled space in the `EXPOSE` comment.

### Notes

- **This is a new image, therefore a new tag.** `1.1.2` is the tag to pin;
  `1.1.0` keeps pointing at the image that was published under it. Rebuilding and
  re-pushing `1.1.0` would have been the easy path and would have broken the
  guarantee this scheme committed to one release earlier - an immutable release
  tag that quietly changes is worse than no scheme at all.
- **The dependency closure is unchanged.** `useradd` comes from the base image,
  the healthcheck uses the standard library, and no package was installed, so the
  published image still carries Flask and its six transitive dependencies and
  the consumer test that reads the layers still asserts the same set.

---

## v1.1.1 - 2026-08-12

Container tags now name the emulator release. **Patch** under this file's scope,
which covers `emulators/` behaviour: no status code, control code or endpoint
changed, and the image contents are byte-identical to the ones v1.1.0 published.
See the note below on why "patch" is nevertheless not the whole story.

### Changed

- **Image tags track the emulator release rather than the Python base version.**
  `apolskiy/flask_app:1.1.0` is the release this README describes and is the tag
  to pin in CI; `latest` continues to follow the newest release.

  The old scheme had one tag, `3.14.4`, naming the base image's Python version.
  It read like a release of this emulator and never was one - and the moment
  emulator releases started carrying numbers of their own, it read like emulator
  3.14.4, which is worse than ambiguous. The base version is now recorded in the
  README and in `Dockerfile.dev`, where a reader who cares can find it, rather
  than in the one field a consumer uses to choose what they are running.

- **The README now says to pin a release in CI and treat `latest` as a look
  around.** A suite pulling `latest` silently re-pulls a different artifact the
  day a new one is published, turning a deliberate release into an unannounced
  change to somebody else's test run - the opposite of what infrastructure whose
  value is repeatability should do. The GitHub Actions service-container example
  is pinned accordingly.

### Added

- **`1.0.0`, backfilled from the existing `3.14.4` digest.** The pre-latency
  image is preserved under the name it always deserved, by re-tagging the same
  manifest rather than rebuilding, so the digest is unchanged and anything
  already pulled still matches. A run from before `X-Response-Delay-Ms` existed
  stays reproducible.

### Notes

- **Retiring `3.14.4` is a breaking change for anyone who pinned it**, which is
  why the image was preserved as `1.0.0` before the old tag was withdrawn rather
  than after. This file's SemVer scope is the emulators' HTTP contract, and by
  that measure nothing changed; by the measure of how the artifact is
  distributed, a tag disappeared. Recorded here plainly rather than resolved by
  choosing whichever version number sounded better.
- **Nothing verifies that the published image behaves correctly.** The consumer
  test in
  [PlaywrightAPWebsiteAutomation](https://github.com/apolskiy/PlaywrightAPWebsiteAutomation)
  reads the image's dependency closure, and the 108 tests here exercise the
  emulator's source through WSGI and a loopback socket - but no test connects the
  two. An image built from stale source, or one whose `CMD` no longer starts,
  would satisfy both. That gap predates this release and is unchanged by it;
  it is noted because versioned tags make the artifact easier to pin and
  therefore easier to trust further than it has earned.

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
