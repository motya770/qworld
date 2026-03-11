import numpy as np
from qutip import Qobj, sigmax, sigmay, sigmaz


def hadamard() -> Qobj:
    return Qobj([[1, 1], [1, -1]]) / np.sqrt(2)


def pauli_x() -> Qobj:
    return sigmax()


def pauli_y() -> Qobj:
    return sigmay()


def pauli_z() -> Qobj:
    return sigmaz()


def rx(theta: float) -> Qobj:
    return Qobj([
        [np.cos(theta / 2), -1j * np.sin(theta / 2)],
        [-1j * np.sin(theta / 2), np.cos(theta / 2)]
    ])


def ry(theta: float) -> Qobj:
    return Qobj([
        [np.cos(theta / 2), -np.sin(theta / 2)],
        [np.sin(theta / 2), np.cos(theta / 2)]
    ])


def rz(theta: float) -> Qobj:
    return Qobj([
        [np.exp(-1j * theta / 2), 0],
        [0, np.exp(1j * theta / 2)]
    ])


def phase_gate(phi: float) -> Qobj:
    return Qobj([[1, 0], [0, np.exp(1j * phi)]])


def t_gate() -> Qobj:
    return phase_gate(np.pi / 4)


def s_gate() -> Qobj:
    return phase_gate(np.pi / 2)


FIXED_GATES = [
    ("H", hadamard, "Hadamard: creates equal superposition"),
    ("X", pauli_x, "Pauli-X: bit flip (NOT gate)"),
    ("Y", pauli_y, "Pauli-Y: bit + phase flip"),
    ("Z", pauli_z, "Pauli-Z: phase flip"),
    ("S", s_gate, "S gate: \u03c0/2 phase"),
    ("T", t_gate, "T gate: \u03c0/4 phase"),
]

ROTATION_GATES = [
    ("Rx", rx, "Rotation about X axis"),
    ("Ry", ry, "Rotation about Y axis"),
    ("Rz", rz, "Rotation about Z axis"),
]
