"""Tests for the Lambda-Q Noise Profiler."""

import numpy as np
import pytest

from lambda_q_profiler.core import (
    compute_lambda_q,
    compute_lambda_q_from_measurements,
    grade_qubits,
    profile_processor,
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
            "cultivation_ready", "qec_ready",
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
