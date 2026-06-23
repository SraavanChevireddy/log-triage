# log-triage

> A zero-dependency CLI that reads a wall of application logs and tells you what's actually wrong — error counts by level, and **clustered** stack traces so 10,000 near-identical errors collapse into one line.

[![CI](https://github.com/SraavanChevireddy/log-triage/actions/workflows/ci.yml/badge.svg)](https://github.com/SraavanChevireddy/log-triage/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

When something breaks, you `tail` the log and drown. `grep ERROR` gives you thousands of lines that are really the *same* error with different timestamps and IDs. **log-triage** parses the log, counts levels, and fingerprints error messages so they group into clusters — instantly showing you the top offenders.

- **Clusters similar errors** by masking variable bits (numbers, UUIDs, hex, quoted strings).
- **Understands JSON and plain-text logs** (Spring Boot, Logback, Python logging, and friends).
- **No dependencies** — pure standard library. Pip-install and go.
- **Pipe-friendly** — reads stdin, exits non-zero when errors are found, so it drops into CI.

## Install

```bash
pip install log-triage         # from PyPI (once published)
# or, from source:
git clone https://github.com/SraavanChevireddy/log-triage.git
cd log-triage && pip install -e .
```

## Usage

```bash
# Analyze a file
log-triage app.log

# Read from stdin
kubectl logs my-pod | log-triage

# Show only the top 5 error clusters
log-triage app.log --top 5
```

### Example output

```
Analyzed 18423 lines

Levels:
  INFO     16012  █████████████████████████·····
  WARN      1789  ███···························
  ERROR      620  █·····························
  FATAL        2  ······························

Errors + Fatals: 622

Top 3 error clusters:
    540x  Timeout connecting to host <n>.<n>.<n>.<n> after <n> ms
     78x  NullPointerException in OrderService.process(<str>)
      4x  Failed to load config <str>: file not found
```

Those 540 timeouts were 540 separate log lines with different IPs and durations — collapsed into one actionable cluster.

## Use it in CI

`log-triage` exits with code `1` if any ERROR/FATAL lines are found, so you can fail a pipeline on unexpected errors:

```bash
./run-integration-tests.sh > test.log
log-triage test.log   # non-zero exit fails the build
```

## Development

```bash
pip install -e ".[dev]" pytest
pytest
```

## License

[MIT](LICENSE) © Sraavan Chevireddy
