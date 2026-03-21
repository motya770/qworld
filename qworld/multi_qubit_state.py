import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal


# Single-qubit gate matrices
H_GATE = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
X_GATE = np.array([[0, 1], [1, 0]], dtype=complex)
Y_GATE = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z_GATE = np.array([[1, 0], [0, -1]], dtype=complex)
S_GATE = np.array([[1, 0], [0, 1j]], dtype=complex)
T_GATE = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

NAMED_GATES = {
    'h': H_GATE, 'x': X_GATE, 'y': Y_GATE, 'z': Z_GATE,
    's': S_GATE, 't': T_GATE,
}


class MultiQubitState(QObject):
    """
    N-qubit quantum state engine using numpy state vectors.
    Uses efficient tensor contraction for gate application.
    Emits state_changed signal on state modification.
    """

    state_changed = pyqtSignal()

    def __init__(self, n_qubits=8):
        super().__init__()
        self._n_qubits = n_qubits
        self._state = np.zeros(2 ** n_qubits, dtype=complex)
        self._state[0] = 1.0  # |000...0>
        self._batch = False
        self._measurement_results = None

    @property
    def n_qubits(self):
        return self._n_qubits

    @property
    def state(self):
        return self._state

    @property
    def measurement_results(self):
        return self._measurement_results

    def _emit(self):
        if not self._batch:
            self.state_changed.emit()

    def begin_batch(self):
        """Suppress state_changed signals until end_batch()."""
        self._batch = True

    def end_batch(self):
        """Re-enable signals and emit once."""
        self._batch = False
        self.state_changed.emit()

    def reset(self, n_qubits=None):
        """Reset to |000...0>. Optionally change qubit count."""
        if n_qubits is not None:
            self._n_qubits = n_qubits
        self._state = np.zeros(2 ** self._n_qubits, dtype=complex)
        self._state[0] = 1.0
        self._measurement_results = None
        self.state_changed.emit()

    def apply_gate(self, gate_name, qubit):
        """Apply a named single-qubit gate (h, x, y, z, s, t)."""
        self._apply_single_gate(NAMED_GATES[gate_name], qubit)

    def _apply_single_gate(self, gate, qubit):
        """Apply a 2x2 unitary to a specific qubit via tensor contraction."""
        n = self._n_qubits
        state = self._state.reshape([2] * n)
        state = np.tensordot(gate, state, axes=([1], [qubit]))
        state = np.moveaxis(state, 0, qubit)
        self._state = state.reshape(2 ** n)
        self._emit()

    def apply_cnot(self, control, target):
        """Apply CNOT: flip target qubit when control is |1>."""
        n = self._n_qubits
        state = self._state.reshape([2] * n)

        idx = [slice(None)] * n
        idx[control] = 1
        target_ax = target - (1 if target > control else 0)

        sub = state[tuple(idx)].copy()
        sub = np.tensordot(X_GATE, sub, axes=([1], [target_ax]))
        sub = np.moveaxis(sub, 0, target_ax)
        state[tuple(idx)] = sub

        self._state = state.reshape(2 ** n)
        self._emit()

    def apply_swap(self, q1, q2):
        """SWAP two qubits via three CNOTs."""
        self.apply_cnot(q1, q2)
        self.apply_cnot(q2, q1)
        self.apply_cnot(q1, q2)

    def apply_controlled_phase(self, control, target, angle):
        """Phase shift on |11> subspace: |c,t> -> e^(i*angle)|c,t> when c=t=1."""
        n = self._n_qubits
        indices = np.arange(2 ** n)
        c_mask = 1 << (n - 1 - control)
        t_mask = 1 << (n - 1 - target)
        mask = (indices & c_mask != 0) & (indices & t_mask != 0)
        self._state[mask] *= np.exp(1j * angle)
        self._emit()

    def flip_phase(self, target_index):
        """Negate the amplitude of a specific basis state (used by oracles)."""
        self._state[target_index] *= -1

    def measure_all(self, shots=1024):
        """Sample the state vector, returning {bitstring: count} dict."""
        probs = np.abs(self._state) ** 2
        probs = probs / probs.sum()
        indices = np.random.choice(len(probs), size=shots, p=probs)
        counts = {}
        for idx in indices:
            bs = format(idx, f'0{self._n_qubits}b')
            counts[bs] = counts.get(bs, 0) + 1
        self._measurement_results = dict(
            sorted(counts.items(), key=lambda x: -x[1])
        )
        self.state_changed.emit()
        return self._measurement_results

    def get_qubit_probabilities(self):
        """Marginal P(|1>) for each individual qubit."""
        n = self._n_qubits
        probs = np.abs(self._state) ** 2
        tensor = probs.reshape([2] * n)
        result = []
        for q in range(n):
            axes = tuple(i for i in range(n) if i != q)
            marginal = np.sum(tensor, axis=axes)
            result.append(float(marginal[1]))
        return result

    def get_pairwise_entanglement(self):
        """Compute ZZ correlation for every qubit pair.

        Returns {(i, j): correlation} where correlation ≠ 0 means the
        pair is correlated (entangled in a pure state).
        Uses ⟨Z_i Z_j⟩ − ⟨Z_i⟩⟨Z_j⟩ computed via vectorised dot products.
        """
        n = self._n_qubits
        N = 2 ** n
        probs = np.abs(self._state) ** 2
        indices = np.arange(N)

        # Precompute Z eigenvalue arrays: +1 for |0⟩, −1 for |1⟩
        z = []
        for q in range(n):
            z.append(1.0 - 2.0 * ((indices >> (n - 1 - q)) & 1))

        # Single-qubit expectations ⟨Z_q⟩
        ez = np.array([np.dot(probs, z[q]) for q in range(n)])

        # Pairwise correlations
        result = {}
        for i in range(n):
            wi = probs * z[i]          # weighted once per outer loop
            for j in range(i + 1, n):
                zz = np.dot(wi, z[j])  # ⟨Z_i Z_j⟩
                corr = float(zz - ez[i] * ez[j])
                if abs(corr) > 0.01:
                    result[(i, j)] = corr
        return result

    def get_top_states(self, count=16):
        """Return the highest-probability basis states."""
        probs = np.abs(self._state) ** 2
        top_idx = np.argsort(probs)[-count:][::-1]
        return [
            (format(i, f'0{self._n_qubits}b'), float(probs[i]))
            for i in top_idx if probs[i] > 1e-10
        ]
