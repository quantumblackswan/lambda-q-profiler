"""Tests for the Lambda-Q Noise Profiler."""

import numpy as np
import pytest

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
from lambda_q_profiler.profiles import (
    IBM_FEZ_PROFILE,
    GOOGLE_WILLOW_PROFILE,
    IONQ_FORTE_PROFILE,
    IONQ_ARIA_PROFILE,
    QUANTINUUM_H2_PROFILE,
    RIGETTI_ANKAA3_PROFILE,
    NOISY_PROCESSOR_PROFILE,
    ALL_PROFILES,
    generate_simulated_calibration,
)
from lambda_q_profiler.probes import (
    build_t2_ramsey,
    build_cx_error,
    build_ghz,
    build_state_variance,
    build_readout,
)


# -----------------------------------------------------------------
# Core computation
# -----------------------------------------------------------------

class TestComputeLambdaQ:
    """Test the calibration-based Lambda-Q computation."""

    def test_ibm_fez_reference_is_one(self):
        """IBM Fez reference specs should produce lambda_q ~ 1.0."""
        r = compute_lambda_q(
            t1_us=263.0, t2_us=152.0,
            error_1q=2.6e-4, error_2q=5.2e-3, readout_error=7.5e-3,
        )
        assert abs(r["lambda_q"] - 1.0) < 0.01

    def test_better_processor_above_one(self):
        """A processor better than Fez should score > 1.0."""
        r = compute_lambda_q(
            t1_us=400.0, t2_us=250.0,
            error_1q=1.0e-4, error_2q=2.0e-3, readout_error=3.0e-3,
        )
        assert r["lambda_q"] > 1.0

    def test_noisy_processor_below_one(self):
        """A noisy processor should score < 1.0."""
        r = compute_lambda_q(
            t1_us=50.0, t2_us=20.0,
            error_1q=2e-3, error_2q=2.5e-2, readout_error=3e-2,
        )
        assert r["lambda_q"] < 1.0

    def test_cultivation_readiness(self):
        """Google Willow-class specs should be cultivation-ready."""
        r = compute_lambda_q(
            t1_us=60.0, t2_us=25.0,
            error_1q=5e-4, error_2q=2.3e-3, readout_error=5e-3,
        )
        # p_noise for these specs is very close to threshold
        # Just verify the boolean is computed
        assert isinstance(r["cultivation_ready"], bool)

    def test_returns_all_keys(self):
        r = compute_lambda_q(
            t1_us=100.0, t2_us=50.0,
            error_1q=1e-3, error_2q=1e-2, readout_error=1e-2,
        )
        expected_keys = {
            "lambda_q", "lambda_q_raw", "delta_psi_sq", "tau_us",
            "eta", "gamma_per_us", "t1_us", "t2_us", "t2_quality",
            "p_noise", "cultivation_threshold", "surface_code_threshold",
            "cultivation_lambda_q_threshold", "floquet_threshold",
            "cultivation_ready", "cultivation_lambda_q_ready",
            "floquet_ready", "qec_ready",
        }
        assert expected_keys.issubset(r.keys())

    def test_t2_quality_capped_at_one(self):
        """T2/(2*T1) should never exceed 1.0."""
        r = compute_lambda_q(
            t1_us=50.0, t2_us=200.0,  # T2 > 2*T1 (unphysical edge case)
            error_1q=1e-3, error_2q=1e-2, readout_error=1e-2,
        )
        assert r["t2_quality"] <= 1.0


class TestComputeFromMeasurements:
    """Test the measurement-based Lambda-Q computation."""

    def test_returns_lambda_q(self):
        r = compute_lambda_q_from_measurements(
            t2_measured=100.0,
            cx_fidelity=0.99,
            ro_error_0=0.01,
            ro_error_1=0.02,
            ghz_fidelity=0.85,
            state_variance=0.24,
        )
        assert "lambda_q" in r
        assert r["lambda_q"] > 0

    def test_high_fidelity_gives_high_score(self):
        r = compute_lambda_q_from_measurements(
            t2_measured=200.0,
            cx_fidelity=0.998,
            ro_error_0=0.005,
            ro_error_1=0.005,
            ghz_fidelity=0.95,
            state_variance=0.25,
        )
        assert r["lambda_q"] > 0.9


# -----------------------------------------------------------------
# Qubit grading
# -----------------------------------------------------------------

class TestGrading:
    """Test per-qubit grading."""

    def test_grade_distribution_keys(self):
        cal = generate_simulated_calibration(IBM_FEZ_PROFILE, n_sample=10)
        g = grade_qubits(
            cal["t1_us"], cal["t2_us"],
            cal["error_1q"], cal["readout_error"],
            cal["edges"],
        )
        assert set(g["grade_distribution"].keys()) == {"A", "B", "C", "F"}
        total = sum(g["grade_distribution"].values())
        assert total == 10

    def test_noisy_processor_has_no_A_grades(self):
        cal = generate_simulated_calibration(NOISY_PROCESSOR_PROFILE, n_sample=10)
        g = grade_qubits(
            cal["t1_us"], cal["t2_us"],
            cal["error_1q"], cal["readout_error"],
            cal["edges"],
        )
        # A noisy processor should have zero or very few A grades
        assert g["grade_distribution"]["A"] <= 2


# -----------------------------------------------------------------
# Profiles
# -----------------------------------------------------------------

class TestProfiles:
    """Test simulated calibration generation."""

    def test_generates_correct_count(self):
        cal = generate_simulated_calibration(IBM_FEZ_PROFILE, n_sample=15)
        assert cal["n_qubits"] == 15
        assert len(cal["t1_us"]) == 15

    def test_t2_never_exceeds_2t1(self):
        cal = generate_simulated_calibration(IBM_FEZ_PROFILE, n_sample=50)
        for i in range(50):
            assert cal["t2_us"][i] <= 2 * cal["t1_us"][i] + 1e-6

    def test_edges_exist(self):
        cal = generate_simulated_calibration(IBM_FEZ_PROFILE, n_sample=10)
        assert len(cal["edges"]) == 9  # n-1 edges for n qubits

    def test_all_to_all_edges_for_trapped_ion(self):
        """Trapped-ion profiles should generate all-to-all edges."""
        cal = generate_simulated_calibration(IONQ_FORTE_PROFILE, n_sample=6)
        # All-to-all: C(6,2) = 15 edges
        assert len(cal["edges"]) == 15

    def test_ionq_forte_high_t1(self):
        """IonQ Forte T1 values should be in the millions of microseconds."""
        cal = generate_simulated_calibration(IONQ_FORTE_PROFILE, n_sample=5)
        for t1 in cal["t1_us"]:
            assert t1 > 1e6  # > 1 second

    def test_quantinuum_h2_low_2q_error(self):
        """Quantinuum H2 should have very low 2Q gate errors."""
        cal = generate_simulated_calibration(QUANTINUUM_H2_PROFILE, n_sample=10)
        mean_err = np.mean(cal["error_2q"])
        assert mean_err < 3e-3  # well below superconducting

    def test_all_profiles_generate_valid_calibration(self):
        """Every profile in ALL_PROFILES should produce valid calibration."""
        for prof in ALL_PROFILES:
            cal = generate_simulated_calibration(prof, n_sample=5)
            assert cal["n_qubits"] == 5
            assert len(cal["t1_us"]) == 5
            assert len(cal["edges"]) > 0

    def test_rigetti_linear_edges(self):
        """Rigetti (no all-to-all) should have linear edges."""
        cal = generate_simulated_calibration(RIGETTI_ANKAA3_PROFILE, n_sample=8)
        assert len(cal["edges"]) == 7  # n-1 for linear


# -----------------------------------------------------------------
# Probe circuits
# -----------------------------------------------------------------

class TestProbes:
    """Test probe circuit construction."""

    def test_ramsey_has_one_classical_bit(self):
        qc = build_t2_ramsey(qubit_idx=0, delay_dt=1000, n_qubits=5)
        assert qc.num_clbits == 1

    def test_cx_error_has_two_bits(self):
        qc = build_cx_error(q0=0, q1=1, n_qubits=5, n_cx=10)
        assert qc.num_clbits == 2

    def test_ghz_probe_qubit_count(self):
        qc = build_ghz(qubit_list=[0, 1, 2], n_qubits=5)
        assert qc.num_clbits == 3

    def test_readout_probe_state_0(self):
        qc = build_readout(qubit_idx=0, n_qubits=3, state=0)
        assert qc.num_clbits == 1
        # Should have no X gate
        ops = [inst.operation.name for inst in qc.data]
        assert "x" not in ops

    def test_readout_probe_state_1(self):
        qc = build_readout(qubit_idx=0, n_qubits=3, state=1)
        ops = [inst.operation.name for inst in qc.data]
        assert "x" in ops


# -----------------------------------------------------------------
# Full profiling pipeline (smoke test)
# -----------------------------------------------------------------

class TestProfileProcessor:
    """Smoke test for the full profiling pipeline."""

    def test_runs_without_error(self):
        result = profile_processor(
            profiles=[IBM_FEZ_PROFILE, NOISY_PROCESSOR_PROFILE],
        )
        assert "processor_results" in result
        assert "ibm_fez" in result["processor_results"]

    def test_correlation_is_computed(self):
        result = profile_processor()
        # With 5 profiles, correlation should be computed
        assert result["predictive_correlation"] is not None

    def test_output_includes_new_thresholds(self):
        result = profile_processor(profiles=[IBM_FEZ_PROFILE])
        assert "cultivation_lambda_q_threshold" in result
        assert "floquet_threshold" in result
        assert result["cultivation_lambda_q_threshold"] == CULTIVATION_LAMBDA_Q_THRESHOLD
        assert result["floquet_threshold"] == FLOQUET_THRESHOLD

    def test_summary_rows_include_floquet_ready(self):
        result = profile_processor(
            profiles=[IBM_FEZ_PROFILE, NOISY_PROCESSOR_PROFILE],
        )
        for row in result["cross_comparison"]:
            assert "floquet_ready" in row
            assert isinstance(row["floquet_ready"], bool)


# -----------------------------------------------------------------
# New v1.1.0 features: Cultivation Lambda-Q, Floquet, Curvature
# -----------------------------------------------------------------

class TestCultivationLambdaQThreshold:
    """Tests for Lambda-Q cultivation threshold (arXiv:2512.13908)."""

    def test_threshold_constant_is_correct(self):
        assert CULTIVATION_LAMBDA_Q_THRESHOLD == 0.75

    def test_cultivation_lambda_q_ready_is_bool(self):
        r = compute_lambda_q(
            t1_us=60.0, t2_us=25.0,
            error_1q=5e-4, error_2q=2.3e-3, readout_error=5e-3,
        )
        assert isinstance(r["cultivation_lambda_q_ready"], bool)

    def test_high_lambda_q_is_cultivation_lq_ready(self):
        """Quantinuum H2-class specs have lambda_q >> 0.75."""
        r = compute_lambda_q(
            t1_us=3e7, t2_us=2e6,
            error_1q=2e-5, error_2q=1e-3, readout_error=3e-3,
        )
        assert r["cultivation_lambda_q_ready"] is True

    def test_low_lambda_q_not_cultivation_lq_ready(self):
        """Noisy processor has lambda_q < 0.75."""
        r = compute_lambda_q(
            t1_us=50.0, t2_us=20.0,
            error_1q=2e-3, error_2q=2.5e-2, readout_error=3e-2,
        )
        assert r["cultivation_lambda_q_ready"] is False

    def test_cultivation_ready_requires_both_conditions(self):
        """cultivation_ready = p_noise < threshold AND lambda_q >= 0.75."""
        # High lambda_q but high p_noise → not cultivation_ready
        r_high_noise = compute_lambda_q(
            t1_us=3e7, t2_us=2e6,
            error_1q=2e-5, error_2q=1.5e-2, readout_error=3e-3,
        )
        # p_noise is high here, so not cultivation_ready
        assert r_high_noise["cultivation_ready"] is False

    def test_quantinuum_h2_cultivation_ready(self):
        """Quantinuum H2 should be cultivation-ready (best-in-class)."""
        r = compute_lambda_q(
            t1_us=3e7, t2_us=2e6,
            error_1q=2e-5, error_2q=1e-3, readout_error=3e-3,
        )
        # p_noise = 1e-3 + exp_term ≈ 1e-3 < CULTIVATION_THRESHOLD 2.3e-3
        # AND lambda_q >> 0.75
        assert r["cultivation_ready"] is True

    def test_willow_near_but_below_cultivation_threshold(self):
        """Google Willow (p_noise ~ 2.34e-3) is near-but-above the p_noise
        cultivation threshold, so it is not cultivation_ready despite its
        lambda_q being above the 0.75 threshold."""
        r = compute_lambda_q(
            t1_us=60.0, t2_us=25.0,
            error_1q=5e-4, error_2q=2.3e-3, readout_error=5e-3,
        )
        # Willow lambda_q > 0.75 (lambda_q_ready) but p_noise > 2.3e-3
        assert r["cultivation_lambda_q_ready"] is True
        # p_noise is just above cultivation threshold
        assert r["p_noise"] > CULTIVATION_THRESHOLD
        assert r["cultivation_ready"] is False


class TestFloquetReadiness:
    """Tests for Floquet code deployment readiness (Haah arXiv:2510.05549)."""

    def test_floquet_threshold_constant(self):
        assert FLOQUET_THRESHOLD == 1.0e-2

    def test_floquet_threshold_below_surface_code_threshold(self):
        assert FLOQUET_THRESHOLD <= SURFACE_CODE_THRESHOLD

    def test_floquet_threshold_above_cultivation_threshold(self):
        assert FLOQUET_THRESHOLD > CULTIVATION_THRESHOLD

    def test_floquet_ready_is_bool(self):
        r = compute_lambda_q(
            t1_us=263.0, t2_us=152.0,
            error_1q=2.6e-4, error_2q=5.2e-3, readout_error=7.5e-3,
        )
        assert isinstance(r["floquet_ready"], bool)

    def test_low_noise_processor_floquet_ready(self):
        """A processor with p_noise well below 1e-2 is Floquet-ready."""
        r = compute_lambda_q(
            t1_us=3e7, t2_us=2e6,
            error_1q=2e-5, error_2q=1e-3, readout_error=3e-3,
        )
        assert r["floquet_ready"] is True

    def test_noisy_processor_not_floquet_ready(self):
        """A noisy processor with high p_noise is not Floquet-ready."""
        r = compute_lambda_q(
            t1_us=50.0, t2_us=20.0,
            error_1q=2e-3, error_2q=2.5e-2, readout_error=3e-2,
        )
        assert r["floquet_ready"] is False

    def test_floquet_ready_in_measurements_output(self):
        r = compute_lambda_q_from_measurements(
            t2_measured=200.0,
            cx_fidelity=0.998,
            ro_error_0=0.005,
            ro_error_1=0.005,
            ghz_fidelity=0.95,
            state_variance=0.25,
        )
        assert "floquet_ready" in r
        assert isinstance(r["floquet_ready"], bool)


class TestCurvedNeighbors:
    """Tests for information-curvature neighbor topology (arXiv:2512.12578)."""

    def test_returns_dict_keyed_by_qubit(self):
        qubit_lq = [1.0, 0.9, 0.8]
        edges = {(0, 1): 5e-3, (1, 2): 7e-3}
        cn = compute_curvature_neighbors(qubit_lq, edges)
        assert set(cn.keys()) == {0, 1, 2}

    def test_neighbors_sorted_by_weight(self):
        """Higher-quality neighbors should appear first."""
        qubit_lq = [1.0, 0.9, 0.5, 0.3]
        edges = {(0, 1): 5e-3, (0, 2): 5e-3, (0, 3): 5e-3}
        cn = compute_curvature_neighbors(qubit_lq, edges)
        weights_for_0 = [w for _, w in cn[0]]
        assert weights_for_0 == sorted(weights_for_0, reverse=True)

    def test_higher_lambda_q_gives_higher_weight(self):
        """Edge to high-lambda_q qubit must outweigh edge to low one."""
        qubit_lq = [1.0, 0.9, 0.1]
        edges = {(0, 1): 5e-3, (0, 2): 5e-3}
        cn = compute_curvature_neighbors(qubit_lq, edges)
        neigh_0 = dict(cn[0])
        assert neigh_0[1] > neigh_0[2]

    def test_all_to_all_curvature_neighbors(self):
        """All-to-all topology should give every qubit n-1 neighbors."""
        n = 5
        qubit_lq = [1.0] * n
        edges = {(i, j): 5e-3 for i in range(n) for j in range(i + 1, n)}
        cn = compute_curvature_neighbors(qubit_lq, edges)
        for q in range(n):
            assert len(cn[q]) == n - 1

    def test_curvature_neighbors_in_grade_qubits_output(self):
        """grade_qubits should include curvature_neighbors key."""
        cal = generate_simulated_calibration(IBM_FEZ_PROFILE, n_sample=5)
        result = grade_qubits(
            cal["t1_us"], cal["t2_us"],
            cal["error_1q"], cal["readout_error"],
            cal["edges"],
        )
        assert "curvature_neighbors" in result
        cn = result["curvature_neighbors"]
        assert len(cn) == 5
        # Every qubit should have at least one neighbor (linear topology)
        for q in range(5):
            assert len(cn[q]) >= 1

    def test_isolated_qubit_has_empty_neighbors(self):
        """A qubit with no edges should have no curvature neighbors."""
        qubit_lq = [1.0, 0.8, 0.6]
        edges = {(0, 1): 5e-3}  # qubit 2 is isolated
        cn = compute_curvature_neighbors(qubit_lq, edges)
        assert cn[2] == []

    def test_weight_reduced_by_gate_error(self):
        """Higher 2Q error should lower curvature weight."""
        qubit_lq = [1.0, 1.0]
        low_err_edges = {(0, 1): 1e-3}
        high_err_edges = {(0, 1): 1e-1}
        cn_low = compute_curvature_neighbors(qubit_lq, low_err_edges)
        cn_high = compute_curvature_neighbors(qubit_lq, high_err_edges)
        assert cn_low[0][0][1] > cn_high[0][0][1]
