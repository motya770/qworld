import numpy as np
from PyQt5.QtCore import QTimer
from qworld.panels.base_panel import BasePanel


class PolarizationPanel(BasePanel):

    def __init__(self, quantum_state, title="Photon Polarization", parent=None):
        self._phase = 0.0
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate_photon)
        self._anim_timer.start(50)
        super().__init__(quantum_state, title, parent)

    def setup_axes(self):
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#1e1e2e")
        self.ax.set_aspect("equal")
        self.figure.subplots_adjust(left=0.1, right=0.9, top=0.92, bottom=0.1)

    def update_visualization(self):
        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")
        self.ax.set_aspect("equal")

        S1, S2, S3, psi, chi = self.quantum_state.get_polarization_params()

        # Polarization ellipse parameters
        a = np.cos(chi)
        b_axis = np.sin(chi)

        t = np.linspace(0, 2 * np.pi, 200)
        ex = a * np.cos(t) * np.cos(psi) - b_axis * np.sin(t) * np.sin(psi)
        ey = a * np.cos(t) * np.sin(psi) + b_axis * np.sin(t) * np.cos(psi)

        # Draw the ellipse
        self.ax.plot(ex, ey, color="#f38ba8", linewidth=2.0, alpha=0.9)

        # Animated photon dot
        phase = self._phase
        px = a * np.cos(phase) * np.cos(psi) - b_axis * np.sin(phase) * np.sin(psi)
        py = a * np.cos(phase) * np.sin(psi) + b_axis * np.sin(phase) * np.cos(psi)
        self.ax.plot(px, py, "o", color="#f9e2af", markersize=10, zorder=5)

        # Glow effect around photon
        for r, alpha in [(14, 0.1), (18, 0.05)]:
            self.ax.plot(px, py, "o", color="#f9e2af", markersize=r, alpha=alpha, zorder=4)

        # Reference axes
        self.ax.axhline(0, color="#585b70", linewidth=0.5, alpha=0.5)
        self.ax.axvline(0, color="#585b70", linewidth=0.5, alpha=0.5)

        # H/V/D/A labels
        lim = 1.3
        self.ax.text(lim, 0, "H", color="#89b4fa", fontsize=10, ha="left", va="center")
        self.ax.text(-lim, 0, "H", color="#89b4fa", fontsize=10, ha="right", va="center")
        self.ax.text(0, lim, "V", color="#fab387", fontsize=10, ha="center", va="bottom")
        self.ax.text(0, -lim, "V", color="#fab387", fontsize=10, ha="center", va="top")

        # Arrow showing electric field direction
        if abs(px) > 0.01 or abs(py) > 0.01:
            self.ax.annotate(
                "", xy=(px, py), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="#cba6f7", lw=1.5, alpha=0.6),
            )

        # Stokes parameters text
        self.ax.text(
            0.02, 0.98,
            f"S\u2081={S1:.2f}  S\u2082={S2:.2f}  S\u2083={S3:.2f}",
            transform=self.ax.transAxes, ha="left", va="top",
            color="#a6adc8", fontsize=8,
        )

        # Polarization type label
        deg_lin = np.sqrt(S1**2 + S2**2)
        if deg_lin > 0.95:
            pol_type = "Linear"
        elif abs(S3) > 0.95:
            pol_type = "Circular (R)" if S3 > 0 else "Circular (L)"
        else:
            pol_type = "Elliptical"
        self.ax.text(
            0.98, 0.98, pol_type,
            transform=self.ax.transAxes, ha="right", va="top",
            color="#a6e3a1", fontsize=9, fontweight="bold",
        )

        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_xlabel("E_H", color="#cdd6f4", fontsize=9)
        self.ax.set_ylabel("E_V", color="#cdd6f4", fontsize=9)
        self.ax.tick_params(colors="#a6adc8", labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color("#585b70")

        self.canvas.draw_idle()

    def _animate_photon(self):
        self._phase += 0.1
        if self._phase > 2 * np.pi:
            self._phase -= 2 * np.pi
        self.update_visualization()
