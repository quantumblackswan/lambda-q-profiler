"""
Command-line interface for the Lambda-Q Noise Profiler.

Usage
-----
::

    # Profile all built-in processors (simulation)
    lambda-q-profiler

    # Save results to a file
    lambda-q-profiler --output results.json

    # Compute Lambda-Q for a single processor from known specs
    lambda-q-profiler --single --t1 263 --t2 152 \
        --e1q 2.6e-4 --e2q 5.2e-3 --ro 7.5e-3

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC
Licensed under the Apache License, Version 2.0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from lambda_q_profiler.core import compute_lambda_q, profile_processor
from lambda_q_profiler.kpis import summarize_cross_comparison, format_summary_kpis


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lambda-q-profiler",
        description=(
            "Lambda-Q Noise Profiler — characterise quantum processors "
            "via information-geometric noise coefficients."
        ),
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Save JSON results to this file path.",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Compute Lambda-Q for a single processor from given specs.",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help=(
            "After profiling (simulation mode), print a buyer‑focused summary of "
            "key performance indicators (KPIs) across processors."
        ),
    )
    parser.add_argument("--t1", type=float, help="T1 in microseconds.")
    parser.add_argument("--t2", type=float, help="T2 in microseconds.")
    parser.add_argument("--e1q", type=float, help="1Q gate error rate.")
    parser.add_argument("--e2q", type=float, help="2Q gate error rate.")
    parser.add_argument("--ro", type=float, help="Readout error rate.")

    args = parser.parse_args(argv)

    if args.single:
        missing = []
        for name in ("t1", "t2", "e1q", "e2q", "ro"):
            if getattr(args, name) is None:
                missing.append(f"--{name}")
        if missing:
            parser.error(
                f"--single mode requires: {', '.join(missing)}"
            )

        result = compute_lambda_q(
            t1_us=args.t1,
            t2_us=args.t2,
            error_1q=args.e1q,
            error_2q=args.e2q,
            readout_error=args.ro,
        )
        print(json.dumps(result, indent=2))

        if args.output:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": "single",
                "result": result,
            }
            with open(args.output, "w") as f:
                json.dump(payload, f, indent=2)
            print(f"\nSaved to {args.output}")

    else:
        # Run full profiling across built‑in or provided profiles
        report = profile_processor(output_path=args.output)
        # Optionally compute and print a KPI summary
        if args.summary:
            # The profile_processor returns a dict with a cross_comparison list
            summary_rows = report.get("cross_comparison", [])
            kpis = summarize_cross_comparison(summary_rows)
            summary_text = format_summary_kpis(kpis)
            if summary_text:
                print("\n  BUYER KPI SUMMARY:\n  " + summary_text.replace("\n", "\n  "))


if __name__ == "__main__":
    main()
