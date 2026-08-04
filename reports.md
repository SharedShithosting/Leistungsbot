---
title: Reports
# Explicit, so this page cannot land on `/reports/index.html` and collide
# with the `reports/` directory the workflow copies in next to it.
permalink: /reports.html
---

# Reports

Rebuilt on every push to `main`, from the mocked test suite - the same one
`unittests.yml` gates pull requests with. The workflow is
[`pages.yml`](https://github.com/SharedShithosting/Leistungsbot/blob/main/.github/workflows/pages.yml).

* [Coverage](reports/coverage/) - line and branch coverage, per file. The
  floor is 75% for every file, not just for the project, which is what
  `tools/check_coverage.py` enforces.
* [Test results](reports/junit/junit.xml) - junit xml, as pytest wrote it
* [Lint](reports/ruff/ruff.txt) - ruff, informational: it does not fail a
  build here, `pre-commit` is what does

The badges the README uses come from the same run:
[tests](reports/badges/tests-badge.svg),
[coverage](reports/badges/coverage-badge.svg).

A red suite still publishes - the report is worth more when something is
broken than when nothing is, and the badge says so. `unittests.yml` is what
fails a build.

The integration tests are not here. They talk to the real database, the real
google places api and the real telegram credentials, so they wait for an
environment approval and cannot run on every push; their reports stay a run
artifact.
