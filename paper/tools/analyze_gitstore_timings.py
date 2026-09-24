#!/usr/bin/env python3
"""Compute n, mean, standard deviation (and median/IQR) of per-device backup
cycle times from the Auto-Redes III GitStore commit history, for Table 3.

This does not require a new experiment: every successful collection is
already committed to Git as an atomic, timestamped transaction (see the
paper, Section 3). A commit timestamp marks the END of a collection cycle,
not its start, so per-device cycle duration is approximated here as the
interval between consecutive commits for the same device, which is a valid
proxy given the collection workflow's own per-device serialization (Section
5.1). If the deployment separately logs a start-of-cycle timestamp (e.g. in
an application log rather than in Git), prefer that over this proxy.

Usage:
    python analyze_gitstore_timings.py /path/to/gitstore/repo [--csv out.csv]

Before running against the real deployment, adjust `classify_device` below
so it correctly maps a committed file's path (or the commit subject, if the
repo commits one device per commit with the hostname in the message) to one
of the device families from Table 1. The defaults are best-effort guesses
based on the naming conventions described in the paper and will very likely
need tweaking to match the actual repository.
"""
import argparse
import csv
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

FAMILY_PATTERNS = [
    (re.compile(r"dell.*7000|pc7000", re.I), "Dell PowerConnect 7000"),
    (re.compile(r"dell.*3500|pc3500", re.I), "Dell PowerConnect 3500"),
    (re.compile(r"comware|3com", re.I), "Comware OS 5.20 / 3Com Baseline"),
    (re.compile(r"cisco|ios[-_]?xe?\b", re.I), "Cisco IOS / IOS-XE"),
    (re.compile(r"mikrotik|routeros", re.I), "MikroTik RouterOS"),
    (re.compile(r"tp[-_]?link|jetstream", re.I), "TP-Link JetStream / ER"),
]


def classify_device(identifier):
    for pattern, family in FAMILY_PATTERNS:
        if pattern.search(identifier):
            return family
    return "Unclassified"


def get_commits(repo_path):
    """Return one dict per commit: hash, timestamp, subject, changed files."""
    out = subprocess.run(
        ["git", "-C", repo_path, "log", "--all", "--name-only",
         "--format=__COMMIT__%H|%aI|%s"],
        capture_output=True, text=True, check=True,
    ).stdout

    commits = []
    current = None
    for line in out.splitlines():
        if line.startswith("__COMMIT__"):
            h, iso_date, subject = line[len("__COMMIT__"):].split("|", 2)
            current = {
                "hash": h,
                "date": datetime.fromisoformat(iso_date),
                "subject": subject,
                "files": [],
            }
            commits.append(current)
        elif line.strip() and current is not None:
            current["files"].append(line.strip())
    return commits


def device_identifier(commit):
    """Best-effort device identity for a commit: the changed file's path if
    the repo stores one config file per device, otherwise the commit
    subject. Adjust this if the real repository's layout differs."""
    if commit["files"]:
        return commit["files"][0]
    return commit["subject"]


def compute_stats(values):
    n = len(values)
    if n == 0:
        return dict(n=0, mean=float("nan"), stdev=float("nan"),
                    median=float("nan"), q1=float("nan"), q3=float("nan"))
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if n > 1 else 0.0
    median = statistics.median(values)
    quantiles = statistics.quantiles(values, n=4) if n >= 4 else [median, median, median]
    return dict(n=n, mean=mean, stdev=stdev, median=median, q1=quantiles[0], q3=quantiles[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo_path", help="Path to the Auto-Redes III GitStore repository")
    ap.add_argument("--csv", help="Optional path to write per-family stats as CSV")
    args = ap.parse_args()

    commits = get_commits(args.repo_path)
    if not commits:
        print("No commits found - check the repo path.", file=sys.stderr)
        sys.exit(1)

    per_device_dates = defaultdict(list)
    for c in commits:
        per_device_dates[device_identifier(c)].append(c["date"])

    per_family_durations = defaultdict(list)
    for device_id, dates in per_device_dates.items():
        dates.sort()
        family = classify_device(device_id)
        for i in range(1, len(dates)):
            delta_s = (dates[i] - dates[i - 1]).total_seconds()
            per_family_durations[family].append(delta_s)

    rows = []
    print(f"{'Device family':32s} {'n':>5s} {'mean (s)':>10s} {'stdev (s)':>10s} "
          f"{'median (s)':>11s} {'IQR (s)':>16s}")
    print("-" * 92)
    for family in sorted(per_family_durations):
        stats = compute_stats(per_family_durations[family])
        iqr = f"[{stats['q1']:.1f}, {stats['q3']:.1f}]"
        print(f"{family:32s} {stats['n']:5d} {stats['mean']:10.1f} {stats['stdev']:10.1f} "
              f"{stats['median']:11.1f} {iqr:>16s}")
        rows.append({"family": family, **stats})

    total_devices = len(per_device_dates)
    print(f"\n{total_devices} distinct devices seen across {len(commits)} commits.")
    print("NOTE: durations above approximate cycle time as the interval between "
          "consecutive commits for the same device (see module docstring). "
          "Verify `classify_device` matches this repository's real naming "
          "before quoting these numbers in the paper.")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["family", "n", "mean", "stdev", "median", "q1", "q3"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Per-family stats written to {args.csv}")


if __name__ == "__main__":
    main()
