import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt


class StateInfo(QWidget):

    def __init__(self, quantum_state, parent=None):
        super().__init__(parent)
        self.quantum_state = quantum_state

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 4px;
                font-family: monospace;
                font-size: 10px;
                padding: 4px;
            }
        """)
        self.text_display.setMaximumHeight(200)
        layout.addWidget(self.text_display)

        self.setLayout(layout)

        self.quantum_state.state_changed.connect(self.update_display)
        self.update_display()

    def update_display(self):
        state = self.quantum_state.state
        probs = self.quantum_state.get_probabilities()
        bv = self.quantum_state.get_bloch_vector()
        purity = self.quantum_state.get_purity()
        entropy = self.quantum_state.get_entropy()

        lines = []

        # State vector in Dirac notation
        if state.isket:
            amps = state.full().flatten()
            alpha, beta = amps[0], amps[1]
            dirac = self._format_dirac(alpha, beta)
            lines.append(f"<b style='color:#f9e2af;'>|\u03c8\u27e9 = {dirac}</b>")
        else:
            lines.append("<b style='color:#f9e2af;'>Mixed state (density matrix)</b>")

        lines.append("")

        # Amplitudes
        if state.isket:
            amps = state.full().flatten()
            lines.append(f"<span style='color:#89b4fa;'>\u03b1 = {self._format_complex(amps[0])}</span>")
            lines.append(f"<span style='color:#fab387;'>\u03b2 = {self._format_complex(amps[1])}</span>")
            lines.append("")

        # Probabilities
        lines.append(f"P(|0\u27e9) = {probs[0]:.6f}")
        lines.append(f"P(|1\u27e9) = {probs[1]:.6f}")
        lines.append("")

        # Bloch vector
        lines.append(f"Bloch: ({bv[0]:.4f}, {bv[1]:.4f}, {bv[2]:.4f})")
        lines.append(f"|r| = {np.sqrt(bv[0]**2 + bv[1]**2 + bv[2]**2):.4f}")
        lines.append("")

        # Density matrix
        rho = self.quantum_state.density_matrix.full()
        lines.append("<b>\u03c1 =</b>")
        lines.append(f"  [{self._format_complex(rho[0,0])}  {self._format_complex(rho[0,1])}]")
        lines.append(f"  [{self._format_complex(rho[1,0])}  {self._format_complex(rho[1,1])}]")
        lines.append("")

        # Purity and entropy
        lines.append(f"Purity: Tr(\u03c1\u00b2) = {purity:.6f}")
        lines.append(f"Entropy: S = {entropy:.6f}")

        self.text_display.setHtml("<br>".join(lines))

    def _format_complex(self, z) -> str:
        r = np.real(z)
        i = np.imag(z)
        if abs(i) < 1e-10:
            return f"{r:.4f}"
        if abs(r) < 1e-10:
            return f"{i:.4f}i"
        sign = "+" if i >= 0 else "-"
        return f"{r:.4f}{sign}{abs(i):.4f}i"

    def _format_dirac(self, alpha, beta) -> str:
        parts = []
        if abs(alpha) > 1e-10:
            if abs(abs(alpha) - 1) < 1e-10:
                coeff = "" if np.real(alpha) > 0 else "-"
            else:
                coeff = self._format_complex(alpha)
            parts.append(f"{coeff}|0\u27e9")
        if abs(beta) > 1e-10:
            if abs(abs(beta) - 1) < 1e-10:
                sign = "+" if np.real(beta) >= 0 else "-"
                coeff = ""
            else:
                sign = "+" if np.real(beta) >= 0 else ""
                coeff = self._format_complex(beta)
            if parts:
                parts.append(f" {sign} {coeff}|1\u27e9" if not coeff else f" {sign} {coeff}|1\u27e9")
            else:
                parts.append(f"{coeff}|1\u27e9")
        return "".join(parts) if parts else "0"
