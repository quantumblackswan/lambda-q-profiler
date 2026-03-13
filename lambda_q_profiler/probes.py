"""
Probe circuits for measuring quantum processor characteristics.

These are standard quantum circuits used to extract noise parameters
(T2, gate errors, readout errors, state variance) from real hardware.

Copyright 2026 Kevin Henry Miller / Q-Bond Network DeSCI DAO, LLC
Licensed under the Apache License, Version 2.0
"""

from typing import List

from qiskit import QuantumCircuit


def build_t2_ramsey(qubit_idx: int, delay_dt: int,
                    n_qubits: int) -> QuantumCircuit:
    """Build a Ramsey interferometry probe for T2* measurement.

    Applies H - delay - H and measures. The decay of P(|0>) with
    increasing delay gives the T2* dephasing time.

    Parameters
    ----------
    qubit_idx : int
        Index of the qubit to probe.
    delay_dt : int
        Delay duration in backend ``dt`` units.
    n_qubits : int
        Total number of qubits on the circuit.

    Returns
    -------
    QuantumCircuit
        Ramsey probe circuit with one classical bit.
    """
    qc = QuantumCircuit(n_qubits, 1)
    qc.h(qubit_idx)
    qc.delay(delay_dt, qubit_idx, unit="dt")
    qc.h(qubit_idx)
    qc.measure(qubit_idx, 0)
    return qc


def build_cx_error(q0: int, q1: int, n_qubits: int,
                   n_cx: int = 10) -> QuantumCircuit:
    """Build a CNOT parity probe for two-qubit gate error measurement.

    Applies an even number of CX gates (which should compose to
    identity) and measures both qubits. Deviation from ``|00>``
    quantifies the two-qubit error rate.

    Parameters
    ----------
    q0 : int
        Control qubit index.
    q1 : int
        Target qubit index.
    n_qubits : int
        Total number of qubits on the circuit.
    n_cx : int
        Number of CX gates to apply (should be even).

    Returns
    -------
    QuantumCircuit
        CNOT error probe with two classical bits.
    """
    if n_cx % 2 != 0:
        n_cx += 1
    qc = QuantumCircuit(n_qubits, 2)
    for _ in range(n_cx):
        qc.cx(q0, q1)
    qc.measure([q0, q1], [0, 1])
    return qc


def build_ghz(qubit_list: List[int],
              n_qubits: int) -> QuantumCircuit:
    """Build a GHZ state creation + reversal probe.

    Creates a GHZ state across the specified qubits, then reverses
    the circuit. Measuring all zeros indicates perfect collective
    coherence across the qubit group.

    Parameters
    ----------
    qubit_list : list of int
        Qubit indices to entangle.
    n_qubits : int
        Total number of qubits on the circuit.

    Returns
    -------
    QuantumCircuit
        GHZ probe circuit.
    """
    n_data = len(qubit_list)
    qc = QuantumCircuit(n_qubits, n_data)
    qc.h(qubit_list[0])
    for i in range(n_data - 1):
        qc.cx(qubit_list[i], qubit_list[i + 1])
    # Reverse
    for i in range(n_data - 2, -1, -1):
        qc.cx(qubit_list[i], qubit_list[i + 1])
    qc.h(qubit_list[0])
    qc.measure(qubit_list, list(range(n_data)))
    return qc


def build_state_variance(qubit_idx: int, n_qubits: int,
                         theta: float = 0.7853981633974483
                         ) -> QuantumCircuit:
    """Build a state-variance probe via Ry rotation.

    Prepares ``Ry(theta)|0>`` and measures. The variance of the
    measurement outcome distribution relates to the Fubini-Study
    metric on the state manifold (quantum geometric tensor).

    Parameters
    ----------
    qubit_idx : int
        Index of the qubit to probe.
    n_qubits : int
        Total number of qubits on the circuit.
    theta : float
        Rotation angle in radians. Default is pi/4.

    Returns
    -------
    QuantumCircuit
        State-variance probe circuit.
    """
    qc = QuantumCircuit(n_qubits, 1)
    qc.ry(theta, qubit_idx)
    qc.measure(qubit_idx, 0)
    return qc


def build_readout(qubit_idx: int, n_qubits: int,
                  state: int = 0) -> QuantumCircuit:
    """Build a readout-error probe.

    Prepares ``|0>`` or ``|1>`` and immediately measures. The
    mis-classification rate gives the readout error for that state.

    Parameters
    ----------
    qubit_idx : int
        Index of the qubit to probe.
    n_qubits : int
        Total number of qubits on the circuit.
    state : int
        Prepare 0 or 1.

    Returns
    -------
    QuantumCircuit
        Readout error probe circuit.
    """
    qc = QuantumCircuit(n_qubits, 1)
    if state == 1:
        qc.x(qubit_idx)
    qc.measure(qubit_idx, 0)
    return qc
