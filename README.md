# E-Commerce Test Automation Framework

[![tests](https://github.com/TheodorGit/playwright-test-framework/actions/workflows/tests.yml/badge.svg)](https://github.com/TheodorGit/playwright-test-framework/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Playwright](https://img.shields.io/badge/playwright-1.55%2B-2EAD33)

**Catches breaks in an e-commerce purchase funnel (login, cart, checkout, and backend API contracts) on two browsers with every push, with a full local regression run in under 20 seconds. Includes [a defect log of 6 real bugs](BUGS.md) the suite catches in deliberately broken builds.**

Built with Python, Playwright and Pytest against public demo targets by design, so everything here is runnable by anyone: the [SauceDemo](https://www.saucedemo.com/) storefront for UI and the [restful-booker](https://restful-booker.herokuapp.com) API. Client work runs against your environments.

![HTML test report: 38 tests, 0 failures, 17 seconds](docs/images/test-report.png)

## What this demonstrates

| Capability | What it means for your project |
|---|---|
| **Bug-catching demonstration** ([BUGS.md](BUGS.md)) | The same suite, pointed at SauceDemo's deliberately broken builds, catches 6 real defects. Each is documented as a ticket a dev team could act on and pinned by an `xfail(strict)` test that alerts when the bug is fixed |
| **Page Object Model** with stable `data-test` locators | UI changes are cheap to absorb: update one page class and every test that uses it keeps working |
| **Auto-retrying `expect()` assertions, zero `sleep()`** | Tests fail when the product is broken, not when the network is slow |
| **Log in once, reuse auth state** | Authenticated tests skip the login form via Playwright storage state. That's how 38 tests finish in about 17 seconds |
| **Parallel execution** (pytest-xdist) | Regression feedback stays fast as the suite grows. One flag (`-n auto`) spreads tests across CPU cores |
| **API test layer** (httpx + JSON Schema) | Backend contract breaks caught in seconds, without launching a browser |
| **Failure artifacts: screenshot + Playwright trace** | Every red test ships with evidence. Replay the exact failing moment step by step with `playwright show-trace` |
| **HTML + JSON reporting** | A report stakeholders can read, plus machine-readable output that plugs into any CI/CD dashboard |
| **GitHub Actions matrix** (Chromium + Firefox) | Cross-browser confidence on every push, with reports attached to every run as downloadable artifacts |
| **Typed settings module**, all config via `.env` | Point the same suite at dev, staging or prod by changing an env file. No code edits, no hardcoded URLs or credentials |

## Architecture

Two targets, one framework: the UI suites run against SauceDemo, and the API layer runs against restful-booker. Both pipelines share the same configuration and feed the same reports.

```mermaid
flowchart TB
    CI["GitHub Actions"]
    CONFIG["config.py"]
    RUN["pytest"]

    subgraph UIP["UI pipeline"]
        direction TB
        FUNC["UI tests"]
        E2E["E2E tests"]
        DEF["Defect scan"]
        POM["Page objects"]
        SD["SauceDemo"]
        FUNC --> POM
        E2E --> POM
        DEF --> POM
        POM --> SD
    end

    subgraph APIP["API pipeline"]
        direction TB
        APIT["API tests"]
        HTTPX["httpx client"]
        RB["restful-booker"]
        APIT --> HTTPX
        HTTPX --> RB
    end

    subgraph OUTS["Outputs"]
        direction LR
        HTML["HTML report"]
        JSON["JSON report"]
        BADGE["Summary + badge"]
    end

    CI -->|"push · PR · weekly"| RUN
    CONFIG --> RUN
    RUN --> UIP
    RUN --> APIP
    UIP --> OUTS
    APIP --> OUTS
```

## Quickstart

```bash
git clone https://github.com/TheodorGit/playwright-test-framework.git && cd playwright-test-framework
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt && playwright install chromium && pytest -n auto
```

Defaults work out of the box (headless Chromium against SauceDemo). To customise, copy `.env.example` to `.env` and edit. Target URL, credentials, browser and headless mode are all environment-driven via `config.py`.

## Running the suites

```bash
pytest -m smoke                  # critical paths only: login + a complete purchase
pytest -m regression -n auto     # full UI regression, parallelised
pytest -m api                    # API layer only, no browser required
pytest -m defect                 # catch the 6 known bugs in the broken builds (see BUGS.md)
pytest -m "not api" -n auto      # everything UI
BROWSER=firefox pytest -m smoke  # same tests, different engine
```

Generate the reports CI produces:

```bash
pytest -n auto --html=test_results/report.html --self-contained-html --css=report.css \
       --json-report --json-report-file=test_results/report.json
```

When a test fails, `test_results/` also receives a full-page screenshot and a Playwright trace (`playwright show-trace test_results/traces/<test>.zip`).

## Project structure

```
├── .github/workflows/tests.yml   # CI: Chromium + Firefox matrix, API job, report artifacts
├── BUGS.md                       # Defect log: 6 real bugs the suite catches, written as tickets
├── config.py                     # Typed, frozen settings and the only place env vars are read
├── pages/                        # Page Object Model (BasePage + 4 page classes)
├── tests/
│   ├── conftest.py               # Browser lifecycle, auth-state reuse, failure artifacts
│   ├── functional/               # Login, products, cart, checkout
│   ├── e2e/                      # Complete purchase journeys
│   ├── api/                      # Contract, negative and workflow tests (httpx + JSON Schema)
│   └── defects/                  # xfail(strict) tests pinning the bugs documented in BUGS.md
└── pytest.ini                    # Markers: smoke, regression, functional, e2e, api, defect
```

## About me

**Theodor, QA Automation Engineer.** Python · Playwright · Pytest · Jenkins · SQL.
Beyond UI automation: API testing, load testing with Locust, and email deliverability (DMARC / DKIM / SPF, Google Postmaster Tools).

Find me on GitHub: [@TheodorGit](https://github.com/TheodorGit)
