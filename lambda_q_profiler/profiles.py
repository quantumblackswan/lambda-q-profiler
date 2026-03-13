"""
Simulated quantum processor calibration profiles.

All values are drawn from publicly available vendor datasheets,
calibration dashboards, and published papers (as of early 2026).
Covers superconducting (IBM, Google, Rigetti), trapped-ion (IonQ,
Quantinuum), and noisy-baseline architectures. These profiles let
users run the profiler locally without backend access.

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC
Licensed under the Apache License, Version 2.0
"""

from typing import Dict

import numpy as np

# ---------------------------------------------------------------------------
# Public calibration profiles (from vendor dashboards / published papers)
# ---------------------------------------------------------------------------

IBM_FEZ_PROFILE: Dict = {
    "name": "ibm_fez",
    "n_qubits": 156,
    "t1_us": {"mean": 263.0, "std": 80.0},
    "t2_us": {"mean": 152.0, "std": 50.0},
    "error_1q": {"mean": 2.6e-4, "std": 1.5e-4},
    "error_2q": {"mean": 5.2e-3, "std": 2.0e-3},
    "readout_error": {"mean": 7.5e-3, "std": 3.0e-3},
}

IBM_TORINO_PROFILE: Dict = {
    "name": "ibm_torino",
    "n_qubits": 133,
    "t1_us": {"mean": 290.0, "std": 90.0},
    "t2_us": {"mean": 175.0, "std": 60.0},
    "error_1q": {"mean": 2.1e-4, "std": 1.2e-4},
    "error_2q": {"mean": 4.8e-3, "std": 1.8e-3},
    "readout_error": {"mean": 6.2e-3, "std": 2.5e-3},
}

IBM_MARRAKESH_PROFILE: Dict = {
    "name": "ibm_marrakesh",
    "n_qubits": 156,
    "t1_us": {"mean": 250.0, "std": 85.0},
    "t2_us": {"mean": 140.0, "std": 55.0},
    "error_1q": {"mean": 3.0e-4, "std": 1.8e-4},
    "error_2q": {"mean": 6.1e-3, "std": 2.5e-3},
    "readout_error": {"mean": 8.0e-3, "std": 3.5e-3},
}

GOOGLE_WILLOW_PROFILE: Dict = {
    "name": "google_willow",
    "n_qubits": 105,
    "t1_us": {"mean": 60.0, "std": 15.0},
    "t2_us": {"mean": 25.0, "std": 8.0},
    "error_1q": {"mean": 5.0e-4, "std": 2.0e-4},
    "error_2q": {"mean": 2.3e-3, "std": 1.0e-3},
    "readout_error": {"mean": 5.0e-3, "std": 2.0e-3},
}

# ---------------------------------------------------------------------------
# Trapped-ion processors (published specs / vendor datasheets)
# ---------------------------------------------------------------------------

# IonQ Forte (2025): 36 algorithmic qubits, #AQ 36
# Sources: IonQ system specifications (ionq.com), published benchmarks
IONQ_FORTE_PROFILE: Dict = {
    "name": "ionq_forte",
    "n_qubits": 36,
    "t1_us": {"mean": 1.0e7, "std": 2.0e6},       # ~10 seconds (trapped ion)
    "t2_us": {"mean": 1.0e6, "std": 3.0e5},       # ~1 second
    "error_1q": {"mean": 3.0e-4, "std": 1.5e-4},  # ~99.97% fidelity
    "error_2q": {"mean": 4.0e-3, "std": 1.5e-3},  # ~99.6% fidelity
    "readout_error": {"mean": 3.0e-3, "std": 1.0e-3},  # ~99.7%
    "connectivity": "all-to-all",
}

# IonQ Aria (2024): 25 algorithmic qubits, #AQ 25
IONQ_ARIA_PROFILE: Dict = {
    "name": "ionq_aria",
    "n_qubits": 25,
    "t1_us": {"mean": 1.0e7, "std": 2.0e6},       # ~10 seconds
    "t2_us": {"mean": 5.0e5, "std": 1.5e5},       # ~0.5 seconds
    "error_1q": {"mean": 4.0e-4, "std": 2.0e-4},  # ~99.96%
    "error_2q": {"mean": 5.0e-3, "std": 2.0e-3},  # ~99.5%
    "readout_error": {"mean": 4.0e-3, "std": 1.5e-3},  # ~99.6%
    "connectivity": "all-to-all",
}

# Quantinuum H2 (2025): 56 qubits, QCCD architecture
# Sources: Quantinuum system model H2 datasheet, published papers
QUANTINUUM_H2_PROFILE: Dict = {
    "name": "quantinuum_h2",
    "n_qubits": 56,
    "t1_us": {"mean": 3.0e7, "std": 5.0e6},       # ~30 seconds
    "t2_us": {"mean": 2.0e6, "std": 5.0e5},       # ~2 seconds
    "error_1q": {"mean": 2.0e-5, "std": 1.0e-5},  # ~99.998%
    "error_2q": {"mean": 1.0e-3, "std": 5.0e-4},  # ~99.9% (best in class)
    "readout_error": {"mean": 3.0e-3, "std": 1.0e-3},  # ~99.7%
    "connectivity": "all-to-all",  # QCCD shuttling
}

# ---------------------------------------------------------------------------
# Superconducting (non-IBM)
# ---------------------------------------------------------------------------

# Rigetti Ankaa-3 (2025): 84 qubits, tunable transmon
# Sources: Rigetti QPU specifications, AWS Braket benchmarks
RIGETTI_ANKAA3_PROFILE: Dict = {
    "name": "rigetti_ankaa3",
    "n_qubits": 84,
    "t1_us": {"mean": 25.0, "std": 8.0},
    "t2_us": {"mean": 18.0, "std": 6.0},
    "error_1q": {"mean": 4.0e-3, "std": 2.0e-3},  # ~99.6%
    "error_2q": {"mean": 1.5e-2, "std": 5.0e-3},  # ~98.5% (iSWAP native)
    "readout_error": {"mean": 1.0e-2, "std": 4.0e-3},
}

# ---------------------------------------------------------------------------
# Noisy baseline (for contrast)
# ---------------------------------------------------------------------------

NOISY_PROCESSOR_PROFILE: Dict = {
    "name": "noisy_processor",
    "n_qubits": 27,
    "t1_us": {"mean": 50.0, "std": 20.0},
    "t2_us": {"mean": 20.0, "std": 10.0},
    "error_1q": {"mean": 2.0e-3, "std": 1.0e-3},
    "error_2q": {"mean": 2.5e-2, "std": 1.0e-2},
    "readout_error": {"mean": 3.0e-2, "std": 1.5e-2},
}

ALL_PROFILES = [
    IBM_FEZ_PROFILE,
    IBM_TORINO_PROFILE,
    IBM_MARRAKESH_PROFILE,
    GOOGLE_WILLOW_PROFILE,
    IONQ_FORTE_PROFILE,
    IONQ_ARIA_PROFILE,
    QUANTINUUM_H2_PROFILE,
    RIGETTI_ANKAA3_PROFILE,
    NOISY_PROCESSOR_PROFILE,
]


def generate_simulated_calibration(profile: Dict,
                                   n_sample: int = 0,
                                   seed: int = 42) -> Dict:
    """Generate per-qubit calibration data from a processor profile.

    Creates realistic per-qubit T1, T2, gate errors, readout errors,
    and nearest-neighbor edge errors drawn from the profile's
    statistical distributions.  Enforces the physical constraint
    ``T2 <= 2 * T1``.

    Parameters
    ----------
    profile : dict
        A processor profile dictionary (e.g. ``IBM_FEZ_PROFILE``).
    n_sample : int
        Number of qubits to simulate. 0 = ``min(n_qubits, 20)``.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict
        Per-qubit calibration data suitable for ``grade_qubits``.
    """
    rng = np.random.default_rng(seed)
    n_q = n_sample if n_sample > 0 else min(profile["n_qubits"], 20)

    # Clip ranges adapt to technology (trapped ions have T1 in seconds)
    t1_max = max(profile["t1_us"]["mean"] * 2.0, 1000.0)
    t2_max = max(profile["t2_us"]["mean"] * 2.0, 500.0)

    t1 = np.clip(
        rng.normal(profile["t1_us"]["mean"], profile["t1_us"]["std"], n_q),
        10.0, t1_max,
    ).tolist()

    t2_raw = rng.normal(profile["t2_us"]["mean"], profile["t2_us"]["std"], n_q)
    t2 = [min(float(t2_raw[i]), 2 * t1[i]) for i in range(n_q)]
    t2 = np.clip(t2, 5.0, t2_max).tolist()

    e1q = np.clip(
        rng.normal(profile["error_1q"]["mean"], profile["error_1q"]["std"], n_q),
        1e-5, 0.1,
    ).tolist()

    e2q = np.clip(
        rng.normal(profile["error_2q"]["mean"], profile["error_2q"]["std"], n_q),
        1e-4, 0.5,
    ).tolist()

    ro = np.clip(
        rng.normal(
            profile["readout_error"]["mean"],
            profile["readout_error"]["std"],
            n_q,
        ),
        1e-4, 0.3,
    ).tolist()

    # Connectivity: all-to-all for trapped ions, linear for others
    is_all_to_all = profile.get("connectivity") == "all-to-all"
    edges = {}
    if is_all_to_all:
        for i in range(n_q):
            for j in range(i + 1, n_q):
                edge_err = float(
                    np.clip(
                        np.sqrt(e2q[i] * e2q[j]) * rng.uniform(0.8, 1.2),
                        1e-4, 0.5,
                    )
                )
                edges[(i, j)] = edge_err
    else:
        # Linear nearest-neighbour edges
        for i in range(n_q - 1):
            edge_err = float(
                np.clip(
                    np.sqrt(e2q[i] * e2q[i + 1]) * rng.uniform(0.8, 1.2),
                    1e-4, 0.5,
                )
            )
            edges[(i, i + 1)] = edge_err

    return {
        "name": profile["name"],
        "n_qubits": n_q,
        "t1_us": t1,
        "t2_us": t2,
        "error_1q": e1q,
        "error_2q": e2q,
        "readout_error": ro,
        "edges": edges,
    }
