"""Command-line interface for log-triage.

Usage:
    log-triage app.log
    cat app.log | log-triage          # read from stdin
    log-triage app.log --top 5        # show the top 5 error clusters
"""
from __future__ import annotations

import argparse
import sys

from .core import LEVELS, analyze


def _read_lines(path: str | None) -> list[str]:
    if path and path != "-":
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.readlines()
    return sys.stdin.readlines()


def _bar(count: int, total: int, width: int = 30) -> str:
    if total == 0:
        return ""
    filled = round(width * count / total)
    return "█" * filled + "·" * (width - filled)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="log-triage",
        description="Surface error spikes and clustered stack traces in app logs.",
    )
    parser.add_argument("path", nargs="?", default="-",
                        help="Log file to analyze (default: stdin).")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of top error clusters to show (default: 10).")
    args = parser.parse_args(argv)

    lines = _read_lines(args.path)
    report = analyze(lines)

    print(f"\nAnalyzed {report.total} lines\n")

    print("Levels:")
    for level in LEVELS:
        if level == "WARNING":
            continue
        count = report.level_counts.get(level, 0)
        if count:
            print(f"  {level:<6} {count:>7}  {_bar(count, report.total)}")

    print(f"\nErrors + Fatals: {report.error_count}")

    if report.error_clusters:
        print(f"\nTop {args.top} error clusters:")
        for msg, count in report.error_clusters.most_common(args.top):
            preview = msg if len(msg) <= 90 else msg[:87] + "..."
            print(f"  {count:>5}x  {preview}")
    else:
        print("\nNo errors found. Nice.")

    # Non-zero exit if errors were found, so it composes in CI / pipelines.
    return 1 if report.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
