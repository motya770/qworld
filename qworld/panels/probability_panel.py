import numpy as np
from qworld.panels.base_panel import BasePanel


class ProbabilityPanel(BasePanel):

    def setup_axes(self):
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#1e1e2e")
        self.figure.subplots_adjust(left=0.15, right=0.85, top=0.88, bottom=0.15)

    def update_visualization(self):
        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")

        probs = self.quantum_state.get_probabilities()
        amplitudes = self.quantum_state.get_amplitudes()

        colors = ["#89b4fa", "#fab387"]
        labels = ["|0\u27e9", "|1\u27e9"]

        bars = self.ax.bar(labels, probs, color=colors, width=0.5, edgecolor="#45475a",
                           linewidth=1.5, alpha=0.9)

        # Probability labels above bars
        for bar, p in zip(bars, probs):
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.03,
                f"{p:.3f}",
                ha="center", va="bottom",
                color="#cdd6f4", fontsize=12, fontweight="bold",
            )

        # Amplitude annotations below labels
        for i, (amp, label) in enumerate(zip(amplitudes, labels)):
            if np.iscomplex(amp) or (hasattr(amp, 'imag') and abs(amp.imag) > 1e-10):
                mag = abs(amp)
                phase = np.angle(amp)
                amp_str = f"|{mag:.2f}|e^{{i{phase:.2f}}}"
            else:
                amp_str = f"{np.real(amp):.3f}"
            self.ax.text(
                i, -0.12,
                f"\u03b1={amp_str}" if i == 0 else f"\u03b2={amp_str}",
                ha="center", va="top",
                color="#a6adc8", fontsize=9,
            )

        # Reference line at 0.5
        self.ax.axhline(y=0.5, color="#585b70", linestyle="--", linewidth=0.8, alpha=0.5)

        self.ax.set_ylim(-0.05, 1.15)
        self.ax.set_ylabel("Probability", color="#cdd6f4", fontsize=10)
        self.ax.tick_params(colors="#a6adc8", labelsize=10)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["bottom"].set_color("#585b70")
        self.ax.spines["left"].set_color("#585b70")

        # Collapse indicator
        if self.quantum_state.is_collapsed:
            outcome = self.quantum_state.last_measurement
            self.ax.text(
                0.5, 0.95,
                f"COLLAPSED \u2192 |{outcome}\u27e9",
                transform=self.ax.transAxes, ha="center", va="top",
                color="#f38ba8", fontsize=11, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#45475a", alpha=0.8),
            )

        self.canvas.draw_idle()
