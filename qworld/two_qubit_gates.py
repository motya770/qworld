import numpy as np
from qutip import Qobj, qeye, tensor, sigmax
from qutip.core.gates import cnot as cnot_gate, swap as swap_gate


def hadamard_on_a() -> Qobj:
    """Hadamard on qubit A only."""
    H = Qobj([[1, 1], [1, -1]]) / np.sqrt(2)
    return tensor(H, qeye(2))


def cnot() -> Qobj:
    return cnot_gate()


def swap() -> Qobj:
    return swap_gate()


def pauli_x_on(qubit: int) -> Qobj:
    if qubit == 0:
        return tensor(sigmax(), qeye(2))
    return tensor(qeye(2), sigmax())


BELL_STATE_INFO = [
    ("|\u03a6\u207a\u27e9", "00", "(|00\u27e9+|11\u27e9)/\u221a2"),
    ("|\u03a6\u207b\u27e9", "01", "(|00\u27e9\u2212|11\u27e9)/\u221a2"),
    ("|\u03a8\u207a\u27e9", "10", "(|01\u27e9+|10\u27e9)/\u221a2"),
    ("|\u03a8\u207b\u27e9", "11", "(|01\u27e9\u2212|10\u27e9)/\u221a2"),
]
