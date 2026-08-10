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
