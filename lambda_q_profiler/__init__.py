"""
Lambda-Q Noise Profiler
=======================

Quantum processor characterization via information-geometric noise
coefficients. Computes per-qubit and per-edge Lambda-Q scores, grades
processor quality, and predicts magic state cultivation readiness.

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC
Licensed under the Apache License, Version 2.0
"""

__version__ = "1.1.0"
__author__ = "Kevin Henry Miller"

from lambda_q_profiler.core import (
    compute_lambda_q,
    compute_lambda_q_from_measurements,
    compute_curvature_neighbors,
    grade_qubits,
    profile_processor,
    CULTIVATION_LAMBDA_Q_THRESHOLD,
    FLOQUET_THRESHOLD,
    CULTIVATION_THRESHOLD,
    SURFACE_CODE_THRESHOLD,
)
from lambda_q_profiler.probes import (
    build_t2_ramsey,
    build_cx_error,
    build_ghz,
    build_state_variance,
    build_readout,
)
from lambda_q_profiler.profiles import (
    IBM_FEZ_PROFILE,
    IBM_TORINO_PROFILE,
    IBM_MARRAKESH_PROFILE,
    GOOGLE_WILLOW_PROFILE,
    IONQ_FORTE_PROFILE,
    IONQ_ARIA_PROFILE,
    QUANTINUUM_H2_PROFILE,
    RIGETTI_ANKAA3_PROFILE,
    NOISY_PROCESSOR_PROFILE,
    generate_simulated_calibration,
)

# KPI helpers
from lambda_q_profiler.kpis import (
    summarize_cross_comparison,
    format_summary_kpis,
)

__all__ = [
    "compute_lambda_q",
    "compute_lambda_q_from_measurements",
    "compute_curvature_neighbors",
    "grade_qubits",
    "profile_processor",
    "CULTIVATION_LAMBDA_Q_THRESHOLD",
    "FLOQUET_THRESHOLD",
    "CULTIVATION_THRESHOLD",
    "SURFACE_CODE_THRESHOLD",
    "build_t2_ramsey",
    "build_cx_error",
    "build_ghz",
    "build_state_variance",
    "build_readout",
    "IBM_FEZ_PROFILE",
    "IBM_TORINO_PROFILE",
    "IBM_MARRAKESH_PROFILE",
    "GOOGLE_WILLOW_PROFILE",
    "IONQ_FORTE_PROFILE",
    "IONQ_ARIA_PROFILE",
    "QUANTINUUM_H2_PROFILE",
    "RIGETTI_ANKAA3_PROFILE",
    "NOISY_PROCESSOR_PROFILE",
    "generate_simulated_calibration",
    "summarize_cross_comparison",
    "format_summary_kpis",
]
