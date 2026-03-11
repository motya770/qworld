import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout,
)
from PyQt5.QtCore import Qt, QTimer

from qworld.entangled_state import EntangledState
from qworld.two_qubit_gates import BELL_STATE_INFO

# Catppuccin palette
BG = "#1e1e2e"
BG_DARK = "#181825"
TEXT = "#cdd6f4"
TEXT_DIM = "#a6adc8"
PURPLE = "#cba6f7"
PINK = "#f38ba8"
YELLOW = "#f9e2af"
CYAN = "#89dceb"
GREEN = "#a6e3a1"
BLUE = "#89b4fa"
ORANGE = "#fab387"
SURFACE = "#313244"
OVERLAY = "#585b70"


class EntanglementPanel(QWidget):
    """
    Self-contained entanglement visualization panel.
    Owns its own EntangledState (2-qubit) and does not depend on QuantumState.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entangled_state = EntangledState()

        self._phase = 0.0
        self._beam_pulse = 0.0
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(50)

        self._setup_ui()
        self.entangled_state.state_changed.connect(self.update_visualization)
        self.update_visualization()

    # ── UI setup ──────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        title = QLabel("Quantum Entanglement")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {TEXT}; font-size: 11px; font-weight: bold; "
            f"padding: 2px; background: {BG_DARK};"
        )
        layout.addWidget(title)

        self.figure = Figure(figsize=(5, 4), dpi=100, facecolor=BG)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas, stretch=1)

        controls = self._build_controls()
        layout.addWidget(controls)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 9px; padding: 2px;"
        )
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def _build_controls(self) -> QWidget:
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setContentsMargins(4, 2, 4, 2)
        grid.setSpacing(4)

        style_primary = (
            f"QPushButton {{ background: {SURFACE}; color: {TEXT}; "
            f"border: 1px solid {OVERLAY}; border-radius: 3px; "
            f"padding: 4px 8px; font-size: 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: #45475a; border-color: {BLUE}; }}"
            f"QPushButton:pressed {{ background: {BLUE}; color: {BG}; }}"
        )
        style_measure = (
            f"QPushButton {{ background: {PINK}; color: {BG}; border: none; "
            f"border-radius: 3px; padding: 4px 8px; font-size: 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: #eba0ac; }}"
            f"QPushButton:pressed {{ background: #f5c2e7; }}"
        )
        style_reset = (
            f"QPushButton {{ background: {SURFACE}; color: {TEXT}; "
            f"border: 1px solid {OVERLAY}; border-radius: 3px; "
            f"padding: 4px 8px; font-size: 10px; }}"
            f"QPushButton:hover {{ background: #45475a; border-color: {BLUE}; }}"
        )

        # Row 0: Bell state buttons
        for i, (label, code, tooltip) in enumerate(BELL_STATE_INFO):
            btn = QPushButton(label)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(style_primary)
            btn.clicked.connect(
                lambda _, c=code: self.entangled_state.set_bell_state(c)
            )
            grid.addWidget(btn, 0, i)

        # Row 1: Gate + measure buttons
        cnot_btn = QPushButton("CNOT")
        cnot_btn.setToolTip("Controlled-NOT: A controls B")
        cnot_btn.setStyleSheet(style_primary)
        cnot_btn.clicked.connect(self.entangled_state.apply_cnot)
        grid.addWidget(cnot_btn, 1, 0)

        h_a_btn = QPushButton("H(A)")
        h_a_btn.setToolTip("Hadamard on qubit A")
        h_a_btn.setStyleSheet(style_primary)
        h_a_btn.clicked.connect(lambda: self._apply_hadamard(0))
        grid.addWidget(h_a_btn, 1, 1)

        meas_a_btn = QPushButton("Measure A")
        meas_a_btn.setStyleSheet(style_measure)
        meas_a_btn.clicked.connect(lambda: self._on_measure(0))
        grid.addWidget(meas_a_btn, 1, 2)

        meas_b_btn = QPushButton("Measure B")
        meas_b_btn.setStyleSheet(style_measure)
        meas_b_btn.clicked.connect(lambda: self._on_measure(1))
        grid.addWidget(meas_b_btn, 1, 3)

        # Row 2: Reset + shortcut + result flash
        reset_btn = QPushButton("Reset |00\u27e9")
        reset_btn.setStyleSheet(style_reset)
        reset_btn.clicked.connect(self.entangled_state.reset)
        grid.addWidget(reset_btn, 2, 0)

        entangle_btn = QPushButton("H(A)+CNOT")
        entangle_btn.setToolTip("Create Bell state from |00\u27e9: apply H then CNOT")
        entangle_btn.setStyleSheet(style_primary)
        entangle_btn.clicked.connect(self._entangle_shortcut)
        grid.addWidget(entangle_btn, 2, 1)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet(
            f"color: {YELLOW}; font-size: 12px; font-weight: bold;"
        )
        grid.addWidget(self.result_label, 2, 2, 1, 2)

        return widget

    # ── Actions ───────────────────────────────────────────────────

    def _apply_hadamard(self, qubit: int):
        from qutip import Qobj

        H = Qobj([[1, 1], [1, -1]]) / np.sqrt(2)
        self.entangled_state.apply_single_gate(H, qubit)

    def _on_measure(self, qubit: int):
        outcome = self.entangled_state.measure_qubit(qubit)
        label = "A" if qubit == 0 else "B"
        color = BLUE if outcome == 0 else ORANGE
        self.result_label.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: bold;"
        )
        self.result_label.setText(f"{label} \u2192 |{outcome}\u27e9")
        QTimer.singleShot(2000, lambda: self.result_label.setText(""))

    def _entangle_shortcut(self):
        self.entangled_state.reset()
        self._apply_hadamard(0)
        self.entangled_state.apply_cnot()

    # ── Visualization ─────────────────────────────────────────────

    def update_visualization(self):
        self.figure.clear()

        ax_main = self.figure.add_axes([0.05, 0.30, 0.90, 0.65])
        ax_main.set_facecolor(BG)
        ax_main.set_xlim(-1.5, 1.5)
        ax_main.set_ylim(-0.8, 0.8)
        ax_main.set_aspect("equal")
        ax_main.axis("off")

        ax_bars = self.figure.add_axes([0.10, 0.05, 0.50, 0.20])
        ax_bars.set_facecolor(BG)

        ax_meter = self.figure.add_axes([0.70, 0.05, 0.25, 0.20])
        ax_meter.set_facecolor(BG)

        state = self.entangled_state
        conc = state.get_concurrence()
        probs = state.get_probabilities()

        self._draw_particles(ax_main, state, conc)
        self._draw_entanglement_beams(ax_main, conc)
        self._draw_correlations(ax_main, state)
        self._draw_probability_bars(ax_bars, probs)
        self._draw_concurrence_meter(ax_meter, conc)
        self._draw_state_label(ax_main, state)

        self.canvas.draw_idle()
        self._update_info(state)

    def _draw_particles(self, ax, state, conc):
        positions = [(-0.7, 0.0), (0.7, 0.0)]
        labels = ["A", "B"]
        collapsed = [state.collapsed_a, state.collapsed_b]
        colors = [CYAN, YELLOW]

        for i, (px, py) in enumerate(positions):
            is_collapsed = collapsed[i] is not None
            color = colors[i]

            if is_collapsed:
                ax.plot(px, py, "o", color=color, ms=28, zorder=5)
                ax.text(
                    px, py, f"|{collapsed[i]}\u27e9",
                    ha="center", va="center",
                    color=BG, fontsize=12, fontweight="bold", zorder=6,
                )
            else:
                glow_alpha = 0.15 + 0.1 * np.sin(self._phase + i * np.pi)
                for r, a in [(38, glow_alpha * 0.3), (32, glow_alpha * 0.5)]:
                    ax.plot(px, py, "o", color=color, ms=r, alpha=a, zorder=3)
                ax.plot(px, py, "o", color=color, ms=22, alpha=0.85, zorder=5)

                # Bloch z-component arrow inside the particle
                bv = state.get_reduced_bloch(i)
                purity = state.get_reduced_purity(i)
                arrow_len = 0.12 * abs(bv[2])
                arrow_dir = 1 if bv[2] >= 0 else -1
                if arrow_len > 0.01:
                    ax.annotate(
                        "",
                        xy=(px, py + arrow_dir * arrow_len),
                        xytext=(px, py - arrow_dir * 0.02),
                        arrowprops=dict(arrowstyle="->", color=BG, lw=2),
                        zorder=7,
                    )

                # Purity ring — thinner when more entangled (mixed reduced state)
                theta = np.linspace(0, 2 * np.pi, 60)
                ring_r = 0.18
                rx = px + ring_r * np.cos(theta)
                ry = py + ring_r * np.sin(theta)
                ax.plot(
                    rx, ry, color=color,
                    lw=1.5 * purity + 0.5,
                    alpha=0.4 + 0.4 * purity, zorder=4,
                )

            ax.text(
                px, py - 0.35, labels[i],
                ha="center", va="top",
                color=TEXT, fontsize=11, fontweight="bold",
            )

    def _draw_entanglement_beams(self, ax, conc):
        if conc < 0.01:
            return

        n_beams = 3
        x = np.linspace(-0.45, 0.45, 100)

        for b in range(n_beams):
            phase_offset = b * 2 * np.pi / n_beams + self._beam_pulse
            amplitude = 0.15 * conc * (1 + 0.3 * np.sin(self._beam_pulse * 2 + b))
            y = amplitude * np.sin(
                6 * np.pi * (x - x[0]) / (x[-1] - x[0]) + phase_offset
            )
            beam_alpha = 0.3 + 0.4 * conc
            ax.plot(
                x, y, color=PURPLE,
                lw=1.5 * conc + 0.5, alpha=beam_alpha, zorder=2,
            )

        # Central glow when highly entangled
        if conc > 0.5:
            glow_size = 8 + 10 * conc * (0.5 + 0.5 * np.sin(self._beam_pulse * 3))
            ax.plot(0, 0, "o", color=PURPLE, ms=glow_size, alpha=0.15 * conc, zorder=1)

    def _draw_correlations(self, ax, state):
        zz = state.get_correlation("z")
        xx = state.get_correlation("x")
        yy = state.get_correlation("y")
        ax.text(
            0.0, 0.55,
            f"\u27e8ZZ\u27e9={zz:+.2f}  \u27e8XX\u27e9={xx:+.2f}  \u27e8YY\u27e9={yy:+.2f}",
            ha="center", va="bottom", color=TEXT_DIM, fontsize=8,
        )

    def _draw_probability_bars(self, ax, probs):
        labels = ["|00\u27e9", "|01\u27e9", "|10\u27e9", "|11\u27e9"]
        colors = [BLUE, CYAN, ORANGE, PINK]
        bars = ax.bar(
            labels, probs, color=colors, width=0.6,
            edgecolor=OVERLAY, linewidth=1, alpha=0.85,
        )

        for bar, p in zip(bars, probs):
            if p > 0.02:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.02,
                    f"{p:.2f}",
                    ha="center", va="bottom",
                    color=TEXT, fontsize=7, fontweight="bold",
                )

        ax.set_ylim(0, 1.15)
        ax.axhline(y=0.5, color=OVERLAY, ls="--", lw=0.5, alpha=0.4)
        ax.tick_params(colors=TEXT_DIM, labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(OVERLAY)
        ax.spines["left"].set_color(OVERLAY)

    def _draw_concurrence_meter(self, ax, conc):
        ax.clear()
        ax.set_facecolor(BG)

        ax.barh(0, 1.0, height=0.4, color=SURFACE, edgecolor=OVERLAY, lw=0.5)
        color = self._lerp_color(GREEN, PURPLE, conc)
        ax.barh(0, conc, height=0.4, color=color, alpha=0.9)

        ax.text(
            0.5, -0.5, f"Concurrence: {conc:.3f}",
            ha="center", va="top",
            color=TEXT, fontsize=8, fontweight="bold",
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.8, 0.6)
        ax.axis("off")

        ax.text(0, 0.35, "Sep", ha="center", va="bottom", color=GREEN, fontsize=7)
        ax.text(1, 0.35, "Max", ha="center", va="bottom", color=PURPLE, fontsize=7)

    def _draw_state_label(self, ax, state):
        label = state.get_state_label()
        color = PURPLE if state.is_entangled else GREEN
        ax.text(
            0.0, -0.65, label,
            ha="center", va="top",
            color=color, fontsize=9, fontstyle="italic",
        )

    @staticmethod
    def _lerp_color(c1: str, c2: str, t: float) -> str:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        t = max(0.0, min(1.0, t))
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _update_info(self, state):
        probs = state.get_probabilities()
        self.info_label.setText(
            f"P(00)={probs[0]:.3f}  P(01)={probs[1]:.3f}  "
            f"P(10)={probs[2]:.3f}  P(11)={probs[3]:.3f}"
        )

    # ── Animation ─────────────────────────────────────────────────

    def _animate(self):
        self._phase += 0.08
        self._beam_pulse += 0.12
        if self._phase > 2 * np.pi:
            self._phase -= 2 * np.pi
        if self._beam_pulse > 2 * np.pi:
            self._beam_pulse -= 2 * np.pi
        self.update_visualization()
