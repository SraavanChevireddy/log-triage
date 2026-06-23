"""Core log parsing and analysis logic.

Kept free of any I/O so it is trivially unit-testable: feed it lines, get back
structured results.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field

# Levels we care about, in increasing severity.
LEVELS = ["TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL"]

# Matches a bare level token surrounded by word boundaries (plain-text logs).
_LEVEL_RE = re.compile(r"\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\b")

# Strips the variable bits of a message so similar errors cluster together:
# numbers, hex ids, UUIDs, and quoted strings become placeholders.
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
_HEX_RE = re.compile(r"\b0x[0-9a-f]+\b", re.I)
_NUM_RE = re.compile(r"\b\d+\b")
_QUOTED_RE = re.compile(r"([\"']).*?\1")


@dataclass
class LineResult:
    """The parsed view of a single log line."""
    raw: str
    level: str | None
    message: str


@dataclass
class Report:
    """Aggregated analysis across many lines."""
    total: int = 0
    level_counts: Counter = field(default_factory=Counter)
    error_clusters: Counter = field(default_factory=Counter)

    @property
    def error_count(self) -> int:
        return self.level_counts["ERROR"] + self.level_counts["FATAL"]


def parse_line(line: str) -> LineResult:
    """Parse one log line, supporting both JSON logs and plain text."""
    line = line.rstrip("\n")
    stripped = line.strip()

    # Try JSON-structured logs first (common with Spring Boot / structured logging).
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
            level = obj.get("level") or obj.get("severity") or obj.get("levelname")
            message = obj.get("message") or obj.get("msg") or stripped
            return LineResult(raw=line, level=_normalize(level), message=str(message))
        except json.JSONDecodeError:
            pass  # fall through to plain-text parsing

    match = _LEVEL_RE.search(line)
    level = _normalize(match.group(1)) if match else None
    return LineResult(raw=line, level=level, message=line)


def _normalize(level: str | None) -> str | None:
    if not level:
        return None
    level = level.upper()
    return "WARN" if level == "WARNING" else level


def fingerprint(message: str) -> str:
    """Reduce a message to a stable cluster key by removing variable tokens."""
    msg = _UUID_RE.sub("<uuid>", message)
    msg = _HEX_RE.sub("<hex>", msg)
    msg = _QUOTED_RE.sub("<str>", msg)
    msg = _NUM_RE.sub("<n>", msg)
    return msg.strip()


def analyze(lines: list[str]) -> Report:
    """Build an aggregated report from a list of raw log lines."""
    report = Report()
    for line in lines:
        if not line.strip():
            continue
        report.total += 1
        result = parse_line(line)
        if result.level:
            report.level_counts[result.level] += 1
        if result.level in ("ERROR", "FATAL"):
            report.error_clusters[fingerprint(result.message)] += 1
    return report
