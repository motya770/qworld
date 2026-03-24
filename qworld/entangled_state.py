import numpy as np
from qutip import (
    Qobj, basis, tensor, ket2dm, qeye, expect,
    sigmax, sigmay, sigmaz, concurrence,
)
from qutip.core.gates import cnot as cnot_gate
from PyQt5.QtCore import QObject, pyqtSignal


class EntangledState(QObject):
    """
    2-qubit quantum state engine for the entanglement panel.
    Completely independent from the single-qubit QuantumState.
    Holds a QuTiP Qobj in a 4D Hilbert space (dims=[[2,2],[1,1]]).
    """

    state_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._state: Qobj = tensor(basis(2, 0), basis(2, 0))  # |00>
        self._collapsed_a: int | None = None
        self._collapsed_b: int | None = None

    @property
    def state(self) -> Qobj:
        return self._state

    @property
    def density_matrix(self) -> Qobj:
        if self._state.isket:
            return ket2dm(self._state)
        return self._state

    @property
    def collapsed_a(self) -> int | None:
        return self._collapsed_a

    @property
    def collapsed_b(self) -> int | None:
        return self._collapsed_b

    @property
    def is_entangled(self) -> bool:
        return self.get_concurrence() > 0.01

    def apply_gate(self, gate: Qobj):
        """Apply a 4x4 two-qubit gate."""
        self._state = (gate * self._state).unit()
        self._collapsed_a = None
        self._collapsed_b = None
        self.state_changed.emit()

    def apply_single_gate(self, gate: Qobj, qubit: int):
        """Apply a 2x2 single-qubit gate to qubit 0 (A) or 1 (B)."""
        if qubit == 0:
            full_gate = tensor(gate, qeye(2))
        else:
            full_gate = tensor(qeye(2), gate)
        self.apply_gate(full_gate)

    def set_bell_state(self, which: str):
        """Set to a Bell state. which in {'00','01','10','11'} -> Phi+, Phi-, Psi+, Psi-."""
        # Build Bell states manually for reliability across QuTiP versions
        b00 = tensor(basis(2, 0), basis(2, 0))
        b01 = tensor(basis(2, 0), basis(2, 1))
        b10 = tensor(basis(2, 1), basis(2, 0))
        b11 = tensor(basis(2, 1), basis(2, 1))

        bells = {
            "00": (b00 + b11).unit(),  # |Phi+>
            "01": (b00 - b11).unit(),  # |Phi->
            "10": (b01 + b10).unit(),  # |Psi+>
            "11": (b01 - b10).unit(),  # |Psi->
        }
        self._state = bells[which]
        self._collapsed_a = None
        self._collapsed_b = None
        self.state_changed.emit()

    def apply_cnot(self):
        """Apply CNOT with A as control, B as target."""
        self.apply_gate(cnot_gate())

    def measure_qubit(self, qubit: int) -> int:
        """
        Measure qubit A (0) or B (1). Returns 0 or 1.
        Collapses the 2-qubit state via projection.
        """
        rho = self.density_matrix
        P0 = ket2dm(basis(2, 0))
        P1 = ket2dm(basis(2, 1))

        if qubit == 0:
            proj0 = tensor(P0, qeye(2))
            proj1 = tensor(P1, qeye(2))
        else:
            proj0 = tensor(qeye(2), P0)
            proj1 = tensor(qeye(2), P1)

        p0 = float(np.real((proj0 * rho).tr()))
        p0 = np.clip(p0, 0, 1)
        outcome = int(np.random.choice([0, 1], p=[p0, 1 - p0]))

        proj = proj0 if outcome == 0 else proj1
        rho_post = proj * rho * proj
        rho_post = rho_post / rho_post.tr()
        self._state = rho_post

        if qubit == 0:
            self._collapsed_a = outcome
        else:
            self._collapsed_b = outcome

        self.state_changed.emit()
        return outcome

    def reset(self):
        """Reset to |00>."""
        self._state = tensor(basis(2, 0), basis(2, 0))
        self._collapsed_a = None
        self._collapsed_b = None
        self.state_changed.emit()

    def get_concurrence(self) -> float:
        """Concurrence: 0 = separable, 1 = maximally entangled."""
        rho = self.density_matrix
        return float(concurrence(rho))

    def get_probabilities(self) -> np.ndarray:
        """Return [P(00), P(01), P(10), P(11)]."""
        rho = self.density_matrix.full()
        return np.real(np.diag(rho))

    def get_reduced_bloch(self, qubit: int) -> tuple[float, float, float]:
        """Get the Bloch vector of the reduced density matrix for qubit A (0) or B (1)."""
        rho_sub = self.density_matrix.ptrace(qubit)
        x = float(np.real(expect(sigmax(), rho_sub)))
        y = float(np.real(expect(sigmay(), rho_sub)))
        z = float(np.real(expect(sigmaz(), rho_sub)))
        return (x, y, z)

    def get_reduced_purity(self, qubit: int) -> float:
        """Purity of the reduced state. 1.0 = pure (separable), 0.5 = maximally mixed."""
        rho_sub = self.density_matrix.ptrace(qubit)
        return float(np.real((rho_sub * rho_sub).tr()))

    def get_correlation(self, axis: str = "z") -> float:
        """Get <sigma_axis x sigma_axis> correlation between qubits."""
        ops = {"x": sigmax(), "y": sigmay(), "z": sigmaz()}
        op = ops[axis]
        corr_op = tensor(op, op)
        return float(np.real(expect(corr_op, self.density_matrix)))

    def get_state_label(self) -> str:
        """Return a human-readable label for the current state."""
        conc = self.get_concurrence()
        if conc > 0.99:
            return "Maximally Entangled"
        elif conc > 0.01:
            return f"Partially Entangled (C={conc:.2f})"
        else:
            return "Separable (Product State)"
