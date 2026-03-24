import numpy as np
from qutip import Qobj, basis, sigmax, sigmay, sigmaz, expect, ket2dm, entropy_vn
from qutip.wigner import wigner
from PyQt5.QtCore import QObject, pyqtSignal


class QuantumState(QObject):
    """
    Central quantum state engine. Holds the current qubit state as a QuTiP Qobj.
    Emits state_changed signal whenever the state is modified.
    All visualization panels connect to this signal to update.
    """

    state_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._state: Qobj = basis(2, 0)
        self._history: list[Qobj] = [self._state]
        self._last_measurement: int | None = None
        self._is_collapsed = False
        self._measurement_counts = {0: 0, 1: 0}

    @property
    def state(self) -> Qobj:
        return self._state

    @property
    def is_collapsed(self) -> bool:
        return self._is_collapsed

    @property
    def last_measurement(self) -> int | None:
        return self._last_measurement

    @property
    def measurement_counts(self) -> dict[int, int]:
        return self._measurement_counts.copy()

    @property
    def density_matrix(self) -> Qobj:
        if self._state.isket:
            return ket2dm(self._state)
        return self._state

    def apply_gate(self, gate: Qobj):
        self._state = (gate * self._state).unit()
        self._is_collapsed = False
        self._last_measurement = None
        self._history.append(self._state)
        self.state_changed.emit()

    def measure(self) -> int:
        probs = self.get_probabilities()
        outcome = int(np.random.choice([0, 1], p=probs))
        self._state = basis(2, outcome)
        self._is_collapsed = True
        self._last_measurement = outcome
        self._measurement_counts[outcome] += 1
        self._history.append(self._state)
        self.state_changed.emit()
        return outcome

    def reset(self):
        self._state = basis(2, 0)
        self._is_collapsed = False
        self._last_measurement = None
        self._history = [self._state]
        self.state_changed.emit()

    def clear_stats(self):
        self._measurement_counts = {0: 0, 1: 0}

    def get_probabilities(self) -> np.ndarray:
        if self._state.isket:
            amplitudes = self._state.full().flatten()
            return np.abs(amplitudes) ** 2
        else:
            rho = self._state.full()
            return np.real(np.diag(rho))

    def get_amplitudes(self) -> np.ndarray:
        if self._state.isket:
            return self._state.full().flatten()
        rho = self._state.full()
        return np.sqrt(np.real(np.diag(rho)))

    def get_bloch_vector(self) -> tuple[float, float, float]:
        rho = self.density_matrix
        x = float(np.real(expect(sigmax(), rho)))
        y = float(np.real(expect(sigmay(), rho)))
        z = float(np.real(expect(sigmaz(), rho)))
        return (x, y, z)

    def get_bloch_history(self) -> list[tuple[float, float, float]]:
        result = []
        for s in self._history:
            rho = ket2dm(s) if s.isket else s
            x = float(np.real(expect(sigmax(), rho)))
            y = float(np.real(expect(sigmay(), rho)))
            z = float(np.real(expect(sigmaz(), rho)))
            result.append((x, y, z))
        return result

    def get_purity(self) -> float:
        rho = self.density_matrix
        return float(np.real((rho * rho).tr()))

    def get_entropy(self) -> float:
        rho = self.density_matrix
        return float(entropy_vn(rho, 2))

    def get_phase_space_wigner(self, xvec=None):
        N = 20
        if xvec is None:
            xvec = np.linspace(-3, 3, 100)
        if self._state.isket:
            amplitudes = self._state.full().flatten()
            fock_state = amplitudes[0] * basis(N, 0) + amplitudes[1] * basis(N, 1)
        else:
            rho_full = self._state.full()
            fock_dm = Qobj(np.zeros((N, N), dtype=complex))
            fock_dm.data[0, 0] = rho_full[0, 0]
            fock_dm.data[0, 1] = rho_full[0, 1]
            fock_dm.data[1, 0] = rho_full[1, 0]
            fock_dm.data[1, 1] = rho_full[1, 1]
            fock_state = fock_dm
        W = wigner(fock_state, xvec, xvec)
        return W, xvec

    def get_polarization_params(self):
        rho = self.density_matrix
        S1 = float(np.real(expect(sigmaz(), rho)))
        S2 = float(np.real(expect(sigmax(), rho)))
        S3 = float(np.real(expect(sigmay(), rho)))
        psi = 0.5 * np.arctan2(S2, S1)
        chi = 0.5 * np.arcsin(np.clip(S3, -1, 1))
        return S1, S2, S3, psi, chi
