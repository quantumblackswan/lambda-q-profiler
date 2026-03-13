"""
KPI summary helpers for cross-processor comparison reports.

Provides concise, buyer-facing summaries of profiling results so
that non-specialists can quickly compare quantum processors.

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC
Licensed under the Apache License, Version 2.0
"""

from __future__ import annotations

from typing import Dict, List


def summarize_cross_comparison(cross_comparison: List[Dict]) -> Dict:
    """Distil a cross-comparison list into headline KPIs.

    Parameters
    ----------
    cross_comparison : list of dict
        The ``cross_comparison`` list returned by
        ``profile_processor()``.  Each entry must contain at least
        ``name``, ``lambda_q``, ``p_noise``, ``cultivation_ready``,
        and ``grade_A_pct``.

    Returns
    -------
    dict
        ``best_processor``    — name of the highest Lambda-Q processor,
        ``worst_processor``   — name of the lowest Lambda-Q processor,
        ``n_cultivation_ready`` — count of cultivation-ready processors,
        ``avg_lambda_q``      — mean Lambda-Q across all processors,
        ``spread``            — max minus min Lambda-Q,
        ``ranking``           — processors sorted best-to-worst.
    """
    if not cross_comparison:
        return {
            "best_processor": None,
            "worst_processor": None,
            "n_cultivation_ready": 0,
            "avg_lambda_q": 0.0,
            "spread": 0.0,
            "ranking": [],
        }

    ranked = sorted(cross_comparison, key=lambda x: x["lambda_q"], reverse=True)
    lqs = [r["lambda_q"] for r in ranked]

    return {
        "best_processor": ranked[0]["name"],
        "worst_processor": ranked[-1]["name"],
        "n_cultivation_ready": sum(
            1 for r in ranked if r.get("cultivation_ready")
        ),
        "avg_lambda_q": sum(lqs) / len(lqs),
        "spread": max(lqs) - min(lqs),
        "ranking": [
            {
                "rank": i + 1,
                "name": r["name"],
                "lambda_q": r["lambda_q"],
                "p_noise": r["p_noise"],
                "cultivation_ready": r.get("cultivation_ready", False),
                "grade_A_pct": r.get("grade_A_pct", 0.0),
            }
            for i, r in enumerate(ranked)
        ],
    }


def format_summary_kpis(kpis: Dict) -> str:
    """Format KPI summary as a human-readable string.

    Parameters
    ----------
    kpis : dict
        Output of ``summarize_cross_comparison()``.

    Returns
    -------
    str
        Multi-line formatted summary.
    """
    lines = [
        "Lambda-Q Profiler — Summary KPIs",
        "=" * 40,
        f"  Best processor:       {kpis.get('best_processor', 'N/A')}",
        f"  Worst processor:      {kpis.get('worst_processor', 'N/A')}",
        f"  Cultivation-ready:    {kpis.get('n_cultivation_ready', 0)} "
        f"of {len(kpis.get('ranking', []))}",
        f"  Avg Lambda-Q:         {kpis.get('avg_lambda_q', 0):.4f}",
        f"  Spread (max-min):     {kpis.get('spread', 0):.4f}",
        "",
        f"  {'Rank':<5s} {'Processor':<22s} {'Lambda-Q':>9s}  "
        f"{'p_noise':>10s}  {'Cult?':>5s}",
        f"  {'-' * 56}",
    ]
    for r in kpis.get("ranking", []):
        c = "YES" if r.get("cultivation_ready") else "NO"
        lines.append(
            f"  {r['rank']:<5d} {r['name']:<22s} "
            f"{r['lambda_q']:>9.4f}  {r['p_noise']:>10.4e}  {c:>5s}"
        )
    return "\n".join(lines)
