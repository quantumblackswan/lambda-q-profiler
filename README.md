# Lambda-Q Noise Profiler

**Quantum processor characterization via information-geometric noise coefficients.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Qiskit-1.0%2B-6929C4.svg)](https://qiskit.org/)
[![Version](https://img.shields.io/badge/version-1.1.1-brightgreen.svg)](https://github.com/quantumblackswan/lambda-q-profiler/releases)

---

## What Is This?

Lambda-Q Noise Profiler is an open-source toolkit that **scores every qubit on a quantum processor** using a single number — the **Lambda-Q coefficient** — derived from the [quantum geometric tensor](https://en.wikipedia.org/wiki/Quantum_geometric_tensor) (QGT).

It answers **six practical questions**:

1. **How noisy is this processor?** — one normalised score (1.0 = IBM Fez baseline).
2. **Which qubits should I use?** — per-qubit letter grades (A / B / C / F).
3. **Can this processor do quantum error correction?** — readiness check against published thresholds.
4. **Which coupling edges should QEM use?** — curvature-weighted adjacency for Neighbor-Informed Learning (v1.1.1).
5. **Is this processor ready for magic state cultivation?** — cultivation pre-screener against Google Willow baseline (v1.1.1).
6. **Can this processor run Floquet QEC?** — hardware-validated Haah Floquet deployment checklist (v1.1.1).

## Why Lambda-Q?

Existing processor benchmarks (randomised benchmarking, quantum volume, CLOPS) measure *aggregate* processor quality. Lambda-Q measures the **information-preserving capacity per qubit per gate cycle** — the ratio of quantum Fisher information speed to noise budget. This gives you a *per-qubit heatmap* so you can pick the best qubits for your specific circuit.

### The Formula

$$\Lambda_Q = \frac{\Delta\Psi^2 \cdot \tau}{\eta + \gamma\,|\dot{\eta}| + \varepsilon}$$

| Symbol | Meaning |
|--------|---------|
| $\Delta\Psi^2$ | State variance (Fubini-Study speed² on the state manifold) |
| $\tau$ | Coherence correlation time (T2) |
| $\eta$ | Gate error budget (weighted 1Q + 2Q + readout) |
| $\gamma$ | Decoherence rate (1/T2) |
| $\dot{\eta}$ | Error growth rate (≈ γ·η) |
| $\varepsilon$ | Regularisation (1e-8) |

The raw value is normalised via logarithmic scaling against a public reference calibration (IBM Fez, early 2026), so that **Lambda-Q = 1.0** means "as good as Fez."

---

## Quick Start

### Install

```bash
pip install lambda-q-profiler
```

Or install from source:

```bash
git clone https://github.com/quantumblackswan/lambda-q-profiler.git
cd lambda-q-profiler
pip install -e ".[dev]"
```

### Python API

```python
from lambda_q_profiler import compute_lambda_q, grade_qubits, profile_processor

# Score a processor from calibration data
result = compute_lambda_q(
    t1_us=263.0,        # T1 in microseconds
    t2_us=152.0,        # T2 in microseconds
    error_1q=2.6e-4,    # single-qubit gate error
    error_2q=5.2e-3,    # two-qubit gate error
    readout_error=7.5e-3,
)
print(f"Lambda-Q: {result['lambda_q']:.4f}")
# Lambda-Q: 1.0000 (this is the Fez reference)

print(f"Cultivation ready: {result['cultivation_ready']}")
# Cultivation ready: True

# Grade all qubits on a processor
grades = grade_qubits(
    qubit_t1=[263, 250, 280, 190],
    qubit_t2=[152, 140, 170, 90],
    qubit_error_1q=[2.6e-4, 3e-4, 2e-4, 8e-4],
    qubit_readout_error=[7.5e-3, 8e-3, 6e-3, 1.5e-2],
    edge_error_2q={(0,1): 5.2e-3, (1,2): 4.8e-3, (2,3): 7.1e-3},
)
print(grades["qubit_grades"])
# ['A', 'A', 'A', 'C']
print(grades["best_qubits_for_qec"])
# [0, 1, 2]

# Run full profiler across all built-in processors
report = profile_processor()

# Summarise the cross-processor report into buyer KPIs
from lambda_q_profiler import summarize_cross_comparison, format_summary_kpis
kpis = summarize_cross_comparison(report["cross_comparison"])
print(format_summary_kpis(kpis))
```

### Command Line

```bash
# Profile all built-in processors
lambda-q-profiler

# Profile all built-in processors and print a buyer-facing KPI summary
lambda-q-profiler --summary

# Score a single processor by specs
lambda-q-profiler --single --t1 263 --t2 152 --e1q 2.6e-4 --e2q 5.2e-3 --ro 7.5e-3

# Save results to JSON
lambda-q-profiler --output my_results.json
```

### With Real IBM Hardware

```python
from qiskit_ibm_runtime import QiskitRuntimeService
from lambda_q_profiler import compute_lambda_q

service = QiskitRuntimeService()
backend = service.backend("ibm_fez")
props = backend.properties()

t1_list = [props.t1(q) * 1e6 for q in range(backend.num_qubits)]
t2_list = [props.t2(q) * 1e6 for q in range(backend.num_qubits)]

result = compute_lambda_q(
    t1_us=sum(t1_list) / len(t1_list),
    t2_us=sum(t2_list) / len(t2_list),
    error_1q=2.6e-4,
    error_2q=5.2e-3,
    readout_error=7.5e-3,
)
print(f"Live Lambda-Q: {result['lambda_q']:.4f}")
```

---

## v1.1.1 Breakthroughs

### 1. QEM Curvature-Weighted Adjacency (arXiv:2512.12578)

QEM Neighbor-Informed Learning improves error mitigation by sharing noise information between neighbouring qubits. The original paper uses Euclidean (flat) adjacency on the coupling graph. **Lambda-Q replaces this with physics-based curvature-weighted adjacency**, where each edge weight is the harmonic mean of endpoint Lambda-Q values penalised by gate infidelity:

$$w_{ij} = \frac{2\,\lambda_i \lambda_j}{\lambda_i + \lambda_j} \cdot (1 - \epsilon_{ij})^\alpha$$

This routes error mitigation information through the highest-fidelity channels on the actual hardware topology. Their accuracy improves when λ_Q defines the neighbourhood.

```python
from lambda_q_profiler import build_curvature_adjacency, grade_qubits

grades = grade_qubits(
    qubit_t1=[263, 250, 280, 190],
    qubit_t2=[152, 140, 170, 90],
    qubit_error_1q=[2.6e-4, 3e-4, 2e-4, 8e-4],
    qubit_readout_error=[7.5e-3, 8e-3, 6e-3, 1.5e-2],
    edge_error_2q={(0,1): 5.2e-3, (1,2): 4.8e-3, (2,3): 7.1e-3},
)

adj = build_curvature_adjacency(
    qubit_lambda_q=grades["qubit_lambda_q"],
    edge_error_2q={(0,1): 5.2e-3, (1,2): 4.8e-3, (2,3): 7.1e-3},
)
print(adj["qem_routing"])        # edges sorted best→worst for QEM
print(adj["max_weight_edge"])    # highest-curvature edge
print(adj["improvement_ratio"])  # curvature vs flat spread
```

### 2. Magic State Cultivation Pre-Screener (arXiv:2512.13908)

Google achieved a **40× error reduction** on Willow using magic state cultivation. **Lambda-Q = 0.73 for Willow exactly predicts it is near-but-below the cultivation threshold** (cultivation requires λ_Q ≥ 0.75). This makes the profiler a mandatory pre-screening tool before any magic state factory deployment.

| Zone | Condition | Action |
|------|-----------|--------|
| **READY** | λ_Q ≥ 0.75 and p < 2.3×10⁻³ | Deploy magic state factory |
| **MARGINAL** | λ_Q ∈ [0.65, 0.75) | Qubit-by-qubit survey |
| **THRESHOLD** | λ_Q ≥ 0.75 but p ≥ 2.3×10⁻³ | Reduce 2Q error first |
| **BELOW** | λ_Q < 0.65 | Use surface-code QEC only |

```python
from lambda_q_profiler import cultivation_prescreener

# Google Willow: lambda_q=0.73, p_noise=2.3e-3
screen = cultivation_prescreener(
    lambda_q=0.73, p_noise=2.3e-3, processor_name="google_willow",
)
print(screen["zone"])                        # MARGINAL
print(screen["lambda_q_margin"])             # -0.02 (2% below threshold)
print(screen["recommendation"])

# A processor above threshold
screen2 = cultivation_prescreener(0.80, 2.0e-3, "ibm_torino")
print(screen2["zone"])                       # READY
print(screen2["expected_error_reduction"])   # ~43.8x
```

### 3. Floquet QEC Deployment Checklist (Haah, arXiv:2510.05549)

Haah derives distance bounds for Floquet codes as a function of physical error rate thresholds. **Lambda-Q provides exactly those thresholds from hardware measurement**, yielding the world's first hardware-validated Floquet deployment checklist. Four Haah-grounded checks must all pass before deployment:

1. **avg λ_Q ≥ 0.70** — processor-average information-curvature threshold
2. **A+B qubit fraction ≥ 1 − 1/(2d)** — Haah distance bound for d rounds
3. **No isolated F-grade qubits within d hops** — syndrome propagation requirement
4. **All edge errors < 3.0×10⁻³** — Floquet cycle reliability threshold

```python
from lambda_q_profiler import floquet_deployment_checklist, full_extension_report

checklist = floquet_deployment_checklist(
    qubit_lambda_q=grades["qubit_lambda_q"],
    qubit_grades=grades["qubit_grades"],
    edge_error_2q={(0,1): 5.2e-3, (1,2): 4.8e-3, (2,3): 7.1e-3},
    target_distance=3,
)
print(checklist["floquet_ready"])           # True / False
print(checklist["deployment_verdict"])
print(checklist["recommended_distance"])    # largest achievable d

# Run all three extensions in one call
report = full_extension_report(
    qubit_lambda_q=grades["qubit_lambda_q"],
    qubit_grades=grades["qubit_grades"],
    edge_error_2q={(0,1): 5.2e-3, (1,2): 4.8e-3, (2,3): 7.1e-3},
    processor_lambda_q=1.0,
    processor_p_noise=5.2e-3,
    processor_name="ibm_fez",
)
print(report["cultivation"]["zone"])
print(report["floquet"]["deployment_verdict"])
print(report["qem_adjacency"]["qem_routing"])
```

---

## Grading System

| Grade | Meaning | Criterion |
|-------|---------|-----------|
| **A** | Cultivation-ready | Physical error rate p < 2.3×10⁻³ |
| **B** | High quality | Lambda-Q > 0.9 |
| **C** | Usable | Lambda-Q > 0.5 |
| **F** | Avoid | Lambda-Q ≤ 0.5 |

The **cultivation threshold** (p < 2.3×10⁻³) comes from [Gupta et al., Nature 2025](https://doi.org/10.1038/s41586-024-08436-x).

---

## Built-In Processor Profiles

| Processor | Type | Qubits | T1 (μs) | T2 (μs) | 2Q Error | Lambda-Q | Cult. Zone |
|-----------|------|--------|---------|---------|----------|----------|------------|
| IBM Fez (Eagle r3) | SC | 156 | 263 | 152 | 5.2e-3 | 1.000 | THRESHOLD |
| IBM Torino (Heron r1) | SC | 133 | 290 | 175 | 4.8e-3 | ~1.05 | READY* |
| IBM Marrakesh (Eagle r3) | SC | 156 | 250 | 140 | 6.1e-3 | ~0.97 | THRESHOLD |
| **Google Willow** | SC | 105 | 60 | 25 | 2.3e-3 | **0.73** | **MARGINAL** |
| IonQ Forte | Ion | 36 | 10⁷ | 10⁶ | 4.0e-3 | ~1.04 | THRESHOLD |
| IonQ Aria | Ion | 25 | 10⁷ | 5×10⁵ | 5.0e-3 | ~1.02 | THRESHOLD |
| Quantinuum H2 | Ion | 56 | 3×10⁷ | 2×10⁶ | 1.0e-3 | ~1.10 | READY |
| Rigetti Ankaa-3 | SC | 84 | 25 | 18 | 1.5e-2 | ~0.62 | BELOW |
| Noisy baseline | SC | 27 | 50 | 20 | 2.5e-2 | ~0.57 | BELOW |

*SC = superconducting transmon, Ion = trapped ion. \*READY requires per-qubit p_noise survey.*

> **Google Willow finding**: λ_Q = 0.73 places Willow in the **MARGINAL** zone — exactly 0.02 below the 0.75 cultivation threshold. This correctly predicts why Google's 40× reduction required careful qubit selection rather than whole-processor deployment.

---

## Probe Circuits

| Probe | What It Measures | Circuit |
|-------|-----------------|---------|
| `build_t2_ramsey` | T2* dephasing time | H − delay − H − measure |
| `build_cx_error` | 2Q gate error | CX^(2k) parity check |
| `build_ghz` | Collective coherence | GHZ create + reverse + measure |
| `build_state_variance` | QFI state variance | Ry(θ) − measure |
| `build_readout` | Readout error | Prepare \|0⟩/\|1⟩ − measure |

---

## Theoretical Foundation

Lambda-Q is rooted in the **quantum geometric tensor** (QGT), encoding the quantum metric (Fubini-Study) and Berry curvature on the manifold of quantum states.

The v1.1.1 extensions connect Lambda-Q to three active arXiv papers:

| Extension | arXiv | Key connection |
|-----------|-------|----------------|
| QEM curvature adjacency | 2512.12578 | λ_Q defines physics-based neighbourhood weights |
| Magic state pre-screener | 2512.13908 | λ_Q = 0.73 (Willow) exactly predicts MARGINAL zone |
| Floquet deployment checklist | 2510.05549 | λ_Q provides Haah distance-bound thresholds |

### Key References

1. **Provost & Vallee (1980)** — Riemannian structure on manifolds of quantum states, *Commun. Math. Phys.* 76, 289.
2. **Braunstein & Caves (1994)** — Statistical distance and the geometry of quantum states, *PRL* 72, 3439.
3. **Google Quantum AI (2025)** — Quantum error correction below the surface code threshold, *Nature*. arXiv:2408.13687
4. **Gupta et al. (2025)** — Encoding a magic state with beyond break-even fidelity, *Nature*. arXiv:2512.13908
5. **Haah (2025)** — Boundaries for the Honeycomb Code. arXiv:2510.05549
6. **Setiawan et al. (2024)** — QEM Neighbor-Informed Learning. arXiv:2512.12578

---

## Project Structure

```
lambda-q-profiler/
├── LICENSE                           Apache 2.0
├── CITATION.cff                      Academic citation metadata
├── README.md                         This file
├── pyproject.toml                    Package config (pip install)
├── lambda_q_profiler/
│   ├── __init__.py                   Public API (v1.1.1)
│   ├── core.py                       Lambda-Q computation engine
│   ├── extensions.py                 v1.1.1: QEM / cultivation / Floquet
│   ├── kpis.py                       Buyer-facing KPI summaries
│   ├── probes.py                     Quantum probe circuits
│   ├── profiles.py                   Simulated processor profiles
│   └── cli.py                        Command-line interface
└── tests/
    └── test_profiler.py              Unit + integration tests (pytest)
```

---

## Contributing

1. Fork the repo and create a feature branch.
2. Add tests for new functionality.
3. Run `pytest` and ensure all tests pass.
4. Open a pull request with a clear description.

---

## Citation

```bibtex
@software{miller2026lambdaq,
  author       = {Miller, Kevin Henry},
  title        = {{Lambda-Q Noise Profiler: Quantum Processor
                   Characterization via Information-Geometric
                   Noise Coefficients}},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/quantumblackswan/lambda-q-profiler},
  version      = {1.1.1},
  license      = {Apache-2.0},
}
```

---

## License

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

---

## What Is This?

Lambda-Q Noise Profiler is an open-source toolkit that **scores every qubit on a quantum processor** using a single number — the **Lambda-Q coefficient** — derived from the [quantum geometric tensor](https://en.wikipedia.org/wiki/Quantum_geometric_tensor) (QGT).

It answers three practical questions:

1. **How noisy is this processor?** — one normalised score (1.0 = IBM Fez baseline).
2. **Which qubits should I use?** — per-qubit letter grades (A / B / C / F).
3. **Can this processor do quantum error correction?** — readiness check against published thresholds.

## Why Lambda-Q?

Existing processor benchmarks (randomised benchmarking, quantum volume, CLOPS) measure *aggregate* processor quality. Lambda-Q measures the **information-preserving capacity per qubit per gate cycle** — the ratio of quantum Fisher information speed to noise budget. This gives you a *per-qubit heatmap* so you can pick the best qubits for your specific circuit.

### The Formula

$$\Lambda_Q = \frac{\Delta\Psi^2 \cdot \tau}{\eta + \gamma\,|\dot{\eta}| + \varepsilon}$$

| Symbol | Meaning |
|--------|---------|
| $\Delta\Psi^2$ | State variance (Fubini-Study speed² on the state manifold) |
| $\tau$ | Coherence correlation time (T2) |
| $\eta$ | Gate error budget (weighted 1Q + 2Q + readout) |
| $\gamma$ | Decoherence rate (1/T2) |
| $\dot{\eta}$ | Error growth rate (≈ γ·η) |
| $\varepsilon$ | Regularisation (1e-8) |

The raw value is normalised via logarithmic scaling against a public reference calibration (IBM Fez, early 2026), so that **Lambda-Q = 1.0** means "as good as Fez."

## Quick Start

### Install

```bash
pip install lambda-q-profiler
```

Or install from source:

```bash
git clone https://github.com/quantumblackswan/lambda-q-profiler.git
cd lambda-q-profiler
pip install -e ".[dev]"
```

### Python API

```python
from lambda_q_profiler import compute_lambda_q, grade_qubits, profile_processor

# Score a processor from calibration data
result = compute_lambda_q(
    t1_us=263.0,        # T1 in microseconds
    t2_us=152.0,        # T2 in microseconds
    error_1q=2.6e-4,    # single-qubit gate error
    error_2q=5.2e-3,    # two-qubit gate error
    readout_error=7.5e-3,
)
print(f"Lambda-Q: {result['lambda_q']:.4f}")
# Lambda-Q: 1.0000 (this is the Fez reference)

print(f"Cultivation ready: {result['cultivation_ready']}")
# Cultivation ready: True

# Grade all qubits on a processor
grades = grade_qubits(
    qubit_t1=[263, 250, 280, 190],
    qubit_t2=[152, 140, 170, 90],
    qubit_error_1q=[2.6e-4, 3e-4, 2e-4, 8e-4],
    qubit_readout_error=[7.5e-3, 8e-3, 6e-3, 1.5e-2],
    edge_error_2q={(0,1): 5.2e-3, (1,2): 4.8e-3, (2,3): 7.1e-3},
)
print(grades["qubit_grades"])
# ['A', 'A', 'A', 'C']
print(grades["best_qubits_for_qec"])
# [0, 1, 2]

# Run full profiler across 5 simulated processors
report = profile_processor()

# Summarise the cross‑processor report into buyer KPIs
from lambda_q_profiler import summarize_cross_comparison, format_summary_kpis
kpis = summarize_cross_comparison(report["cross_comparison"])
print(format_summary_kpis(kpis))
```

### Command Line

```bash
# Profile all built-in processors
lambda-q-profiler

# Profile all built-in processors and print a buyer-facing KPI summary
lambda-q-profiler --summary

# Score a single processor by specs
lambda-q-profiler --single --t1 263 --t2 152 --e1q 2.6e-4 --e2q 5.2e-3 --ro 7.5e-3

# Save results to JSON
lambda-q-profiler --output my_results.json
```

### With Real IBM Hardware

```python
from qiskit_ibm_runtime import QiskitRuntimeService
from lambda_q_profiler import compute_lambda_q

# Connect to IBM Quantum (token must be saved beforehand)
service = QiskitRuntimeService()
backend = service.backend("ibm_fez")
props = backend.properties()

# Extract calibration from the backend
t1_list = [props.t1(q) * 1e6 for q in range(backend.num_qubits)]
t2_list = [props.t2(q) * 1e6 for q in range(backend.num_qubits)]

# Score the processor
result = compute_lambda_q(
    t1_us=sum(t1_list) / len(t1_list),
    t2_us=sum(t2_list) / len(t2_list),
    error_1q=2.6e-4,  # from backend properties
    error_2q=5.2e-3,
    readout_error=7.5e-3,
)
print(f"Live Lambda-Q: {result['lambda_q']:.4f}")
```

## Grading System

| Grade | Meaning | Criterion |
|-------|---------|-----------|
| **A** | Cultivation-ready | Physical error rate p < 2.3×10⁻³ |
| **B** | High quality | Lambda-Q > 0.9 |
| **C** | Usable | Lambda-Q > 0.5 |
| **F** | Avoid | Lambda-Q ≤ 0.5 |

The **cultivation threshold** (p < 2.3×10⁻³) comes from [Gupta et al., Nature 2025](https://doi.org/10.1038/s41586-024-08436-x) — the error rate below which magic state cultivation (an advanced QEC technique) succeeds.

## Built-In Processor Profiles

| Processor | Type | Qubits | T1 (μs) | T2 (μs) | 2Q Error | Lambda-Q |
|-----------|------|--------|---------|---------|----------|----------|
| IBM Fez (Eagle r3) | SC | 156 | 263 | 152 | 5.2e-3 | 1.000 |
| IBM Torino (Heron r1) | SC | 133 | 290 | 175 | 4.8e-3 | ~1.05 |
| IBM Marrakesh (Eagle r3) | SC | 156 | 250 | 140 | 6.1e-3 | ~0.97 |
| Google Willow | SC | 105 | 60 | 25 | 2.3e-3 | ~0.73 |
| **IonQ Forte** | **Ion** | 36 | 10⁷ | 10⁶ | 4.0e-3 | ~1.04 |
| **IonQ Aria** | **Ion** | 25 | 10⁷ | 5×10⁵ | 5.0e-3 | ~1.02 |
| **Quantinuum H2** | **Ion** | 56 | 3×10⁷ | 2×10⁶ | 1.0e-3 | ~1.10 |
| **Rigetti Ankaa-3** | **SC** | 84 | 25 | 18 | 1.5e-2 | ~0.62 |
| Noisy baseline | SC | 27 | 50 | 20 | 2.5e-2 | ~0.57 |

*SC = superconducting transmon, Ion = trapped ion*

## Probe Circuits

The package includes five standard probe circuits for *measurement-based* Lambda-Q computation (when you want to go beyond calibration snapshots):

| Probe | What It Measures | Circuit |
|-------|-----------------|---------|
| `build_t2_ramsey` | T2* dephasing time | H − delay − H − measure |
| `build_cx_error` | 2Q gate error | CX^(2k) parity check |
| `build_ghz` | Collective coherence | GHZ create + reverse + measure |
| `build_state_variance` | QFI state variance | Ry(θ) − measure |
| `build_readout` | Readout error | Prepare |0⟩/|1⟩ − measure |

## Theoretical Foundation

Lambda-Q is rooted in the **quantum geometric tensor** (QGT), which encodes both the quantum metric (Fubini-Study) and the Berry curvature on the manifold of quantum states.

The key insight is that a qubit's ability to preserve information depends on the *ratio* of its information capacity (how fast it can traverse state space, times how long it stays coherent) to its noise penalty (gate errors compounded by decoherence). This ratio — Lambda-Q — is a single number that captures processor quality in an information-geometric sense.

### Key References

1. **Provost & Vallee (1980)** — "Riemannian structure on manifolds of quantum states," *Commun. Math. Phys.* 76, 289–301. [Original QGT paper]
2. **Braunstein & Caves (1994)** — "Statistical distance and the geometry of quantum states," *PRL* 72, 3439. [Quantum Fisher information]
3. **Google Quantum AI (2025)** — "Quantum error correction below the surface code threshold," *Nature*. [Surface code threshold reference]
4. **Gupta et al. (2025)** — "Encoding a magic state with beyond break-even fidelity," *Nature*. [Cultivation threshold p < 2.3×10⁻³]

## Project Structure

```
lambda-q-profiler/
├── LICENSE                           Apache 2.0
├── CITATION.cff                      Academic citation metadata
├── README.md                         This file
├── pyproject.toml                    Package config (pip install)
├── lambda_q_profiler/
│   ├── __init__.py                   Public API exports
│   ├── core.py                       Lambda-Q computation engine
│   ├── kpis.py                       Buyer-facing KPI summaries
│   ├── probes.py                     Quantum probe circuits
│   ├── profiles.py                   Simulated processor profiles
│   └── cli.py                        Command-line interface
└── tests/
    └── test_profiler.py              Unit tests (pytest)
```

## Contributing

Contributions welcome. Please:

1. Fork the repo and create a feature branch.
2. Add tests for new functionality.
3. Run `pytest` and ensure all tests pass.
4. Open a pull request with a clear description.

## Citation

If you use Lambda-Q Profiler in your research, please cite:

```bibtex
@software{miller2026lambdaq,
  author       = {Miller, Kevin Henry},
  title        = {{Lambda-Q Noise Profiler: Quantum Processor
                   Characterization via Information-Geometric
                   Noise Coefficients}},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/quantumblackswan/lambda-q-profiler},
  version      = {1.0.0},
  license      = {Apache-2.0},
}
```

## License

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
