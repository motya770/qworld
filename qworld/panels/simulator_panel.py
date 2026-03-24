import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QPushButton, QComboBox, QSpinBox, QLineEdit,
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QBrush
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from qworld.multi_qubit_state import MultiQubitState
from qworld.algorithms import ALGORITHMS


PANEL_STYLE = """
QPushButton {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 4px;
    padding: 5px 14px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background: #45475a;
    border-color: #89b4fa;
}
QPushButton:pressed {
    background: #585b70;
}
QSpinBox, QComboBox, QLineEdit {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #45475a;
    border: none;
    width: 16px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #585b70;
}
QLabel { color: #cdd6f4; font-size: 12px; }
"""


class QubitGridWidget(QWidget):
    """Animated qubit grid with glowing orbs, orbiting particles, and connection beams.
    Qubits pulse and glow based on superposition strength.
    Color: blue (|0>) -> pink (|1>), white-hot core in superposition.
    """

    def __init__(self, state):
        super().__init__()
        self.state = state
        self._phase = 0.0
        self._cached_probs = [0.0] * state.n_qubits
        self._cached_entanglement = {}

        self.state.state_changed.connect(self._on_state_changed)
        self.setMinimumSize(300, 200)

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30 fps

    def _on_state_changed(self):
        self._cached_probs = self.state.get_qubit_probabilities()
        self._cached_entanglement = self.state.get_pairwise_entanglement()
        self.update()

    def _tick(self):
        self._phase += 0.06
        self.update()

    @staticmethod
    def _qubit_color(p1):
        """Interpolate blue #89b4fa (P=0) -> pink #f38ba8 (P=1)."""
        r = int(0x89 + (0xF3 - 0x89) * p1)
        g = int(0xB4 + (0x8B - 0xB4) * p1)
        b = int(0xFA + (0xA8 - 0xFA) * p1)
        return r, g, b

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0x0F, 0x0F, 0x1A))

        n = self.state.n_qubits
        if n == 0:
            painter.end()
            return

        probs = self._cached_probs
        if len(probs) != n:
            probs = [0.0] * n

        # Grid layout
        cols = max(1, int(np.ceil(np.sqrt(n * 1.5))))
        rows = int(np.ceil(n / cols))

        margin = 20
        avail_w = self.width() - 2 * margin
        avail_h = self.height() - 2 * margin
        cell_w = avail_w / max(cols, 1)
        cell_h = avail_h / max(rows, 1)
        cell = min(cell_w, cell_h)

        # Precompute positions
        positions = []
        for i in range(n):
            r, c = divmod(i, cols)
            positions.append((
                margin + c * cell_w + cell_w / 2,
                margin + r * cell_h + cell_h / 2,
            ))

        # --- Entanglement beams (drawn behind qubits) ---
        for beam_idx, ((qi, qj), corr) in enumerate(
            self._cached_entanglement.items()
        ):
            if qi < n and qj < n:
                self._draw_entanglement_beam(
                    painter, positions[qi], positions[qj], corr, beam_idx,
                )

        # --- Qubits ---
        for i in range(n):
            self._draw_qubit(painter, positions[i], i, probs[i], cell)

        painter.end()

    # ---- drawing helpers ----

    def _draw_entanglement_beam(self, painter, pos1, pos2, strength, beam_idx):
        """Animated entanglement beam with glow and traveling energy dots.

        Teal (#94e2d5) for positive correlation (qubits aligned),
        peach (#fab387) for negative correlation (anti-correlated).
        """
        x1, y1 = pos1
        x2, y2 = pos2
        s = min(abs(strength), 1.0)
        pulse = 0.55 + 0.45 * np.sin(self._phase * 0.9 + beam_idx * 0.37)
        a_scale = s * pulse

        # Beam color
        if strength > 0:
            br, bg, bb = 0x94, 0xE2, 0xD5   # teal
        else:
            br, bg, bb = 0xFA, 0xB3, 0x87   # peach

        p1f, p2f = QPointF(x1, y1), QPointF(x2, y2)

        # Wide glow
        painter.setPen(QPen(QColor(br, bg, bb, int(18 * a_scale)), 7.0))
        painter.drawLine(p1f, p2f)
        # Core line
        painter.setPen(QPen(QColor(br, bg, bb, int(50 * a_scale)), 1.5))
        painter.drawLine(p1f, p2f)

        # Traveling energy dots
        n_dots = max(1, int(s * 3))
        for d in range(n_dots):
            speed = 0.32 + d * 0.14
            t = (self._phase * speed + d / max(n_dots, 1)
                 + beam_idx * 0.17) % 1.0
            dx = x1 + (x2 - x1) * t
            dy = y1 + (y2 - y1) * t

            dot_a = int(110 * a_scale)
            dot_r = 2.0 + s * 2.5
            dg = QRadialGradient(dx, dy, dot_r * 2.5)
            dg.setColorAt(0.0, QColor(255, 255, 255, dot_a))
            dg.setColorAt(0.35, QColor(br, bg, bb, int(dot_a * 0.6)))
            dg.setColorAt(1.0, QColor(br, bg, bb, 0))
            painter.setBrush(QBrush(dg))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dx, dy), dot_r * 2.5, dot_r * 2.5)

    def _draw_qubit(self, painter, pos, idx, p1, cell):
        """Draw a single glowing qubit orb with uncertainty cloud.

        Physics-grounded visualisation:
        - Color (blue→pink) = measurement probability P(|1⟩)
        - Glow intensity     = degree of superposition
        - Shimmer cloud      = quantum uncertainty (we don't know the
          state until measured — more superposition → more shimmer)
        """
        cx, cy = pos
        sup = 1.0 - abs(2.0 * p1 - 1.0)   # 0 = definite, 1 = max superposition
        pulse = 0.5 + 0.5 * np.sin(self._phase * 1.2 + idx * 0.73)
        cr, cg, cb = self._qubit_color(p1)

        # ── Layer 1: Outer glow (probability field) ──
        glow_r = cell * (0.40 + 0.12 * sup * pulse)
        outer_a = int(45 + 80 * sup * pulse)
        grad = QRadialGradient(cx, cy, glow_r)
        grad.setColorAt(0.0, QColor(cr, cg, cb, outer_a))
        grad.setColorAt(0.45, QColor(cr, cg, cb, int(outer_a * 0.3)))
        grad.setColorAt(1.0, QColor(cr, cg, cb, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # ── Layer 2: Inner halo ──
        halo_r = cell * (0.25 + 0.04 * sup * pulse)
        halo_a = int(70 + 90 * sup * pulse)
        halo = QRadialGradient(cx, cy, halo_r)
        halo.setColorAt(0.0, QColor(cr, cg, cb, halo_a))
        halo.setColorAt(0.6, QColor(cr, cg, cb, int(halo_a * 0.4)))
        halo.setColorAt(1.0, QColor(cr, cg, cb, 0))
        painter.setBrush(QBrush(halo))
        painter.drawEllipse(QPointF(cx, cy), halo_r, halo_r)

        # ── Layer 3: Core orb (white-hot center) ──
        core_r = cell * 0.16
        bright = int(150 + 105 * pulse * max(sup, 0.25))
        off = core_r * 0.22
        core = QRadialGradient(cx - off, cy - off, core_r * 1.15)
        core.setColorAt(0.0, QColor(255, 255, 255, bright))
        core.setColorAt(0.25, QColor(min(cr + 50, 255), min(cg + 40, 255),
                                     min(cb + 30, 255), 235))
        core.setColorAt(0.7, QColor(cr, cg, cb, 210))
        core.setColorAt(1.0, QColor(cr, cg, cb, 100))
        painter.setBrush(QBrush(core))
        painter.setPen(QPen(QColor(cr, cg, cb, 70), 0.8))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # ── Layer 4: Quantum uncertainty cloud ──
        # In superposition we genuinely don't know the state — represent
        # this as random shimmering dots that flicker in and out.
        # More superposition → larger cloud, more active flicker.
        if sup > 0.04:
            n_p = int(sup * 8) + 2
            for pi in range(n_p):
                seed = idx * 97 + pi * 31       # deterministic but chaotic
                # Pseudo-random position that drifts unpredictably
                ang1 = self._phase * 0.3 + seed * 1.7
                ang2 = self._phase * 0.7 + seed * 0.91
                angle = np.sin(ang1) * np.pi + np.cos(ang2) * np.pi
                dist = cell * (0.12 + 0.18 * abs(np.sin(ang1 * 0.6 + seed)))

                px = cx + dist * np.cos(angle)
                py = cy + dist * np.sin(angle)

                # Flicker: each dot fades in and out independently
                flicker = max(0.0, np.sin(self._phase * 1.6 + seed * 3.1))
                alpha = int(75 * sup * flicker)
                if alpha < 5:
                    continue

                ps = 1.0 + sup * 1.5
                pg = QRadialGradient(px, py, ps * 2.0)
                pg.setColorAt(0.0, QColor(255, 255, 255, alpha))
                pg.setColorAt(0.4, QColor(cr, cg, cb, int(alpha * 0.5)))
                pg.setColorAt(1.0, QColor(cr, cg, cb, 0))
                painter.setBrush(QBrush(pg))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(px, py), ps * 2.0, ps * 2.0)

        # ── Layer 6: Text labels ──
        painter.setPen(QColor(0xCD, 0xD6, 0xF4, 210))
        fs = max(8, int(cell / 7))
        fnt = QFont("monospace", fs)
        fnt.setBold(True)
        painter.setFont(fnt)
        ty = cy + core_r + cell * 0.09
        painter.drawText(
            QRectF(cx - cell * 0.3, ty, cell * 0.6, fs + 4),
            Qt.AlignHCenter | Qt.AlignTop, f"q{idx}",
        )

        painter.setPen(QColor(0xA6, 0xAD, 0xC8, 175))
        painter.setFont(QFont("monospace", max(7, int(cell / 8))))
        painter.drawText(
            QRectF(cx - cell * 0.3, ty + fs + 2, cell * 0.6, fs),
            Qt.AlignHCenter | Qt.AlignTop, f"{p1:.2f}",
        )


class SimulatorPanel(QWidget):
    """Multi-qubit quantum circuit simulator with algorithm library."""

    def __init__(self):
        super().__init__()
        self.state = MultiQubitState(8)
        self._algo_result = ""
        self._init_ui()
        self.state.state_changed.connect(self._update_display)
        self._update_display()

    def _init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Title ---
        title = QLabel("Quantum Circuit Simulator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #cba6f7; font-size: 16px; font-weight: bold; padding: 4px;"
        )
        layout.addWidget(title)

        # --- Row 1: Algorithm controls ---
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        row1.addWidget(self._lbl("Qubits:"))
        self.qubit_spin = QSpinBox()
        self.qubit_spin.setRange(2, 20)
        self.qubit_spin.setValue(8)
        self.qubit_spin.setToolTip("Number of qubits (2\u201320, state vector = 2^n amplitudes)")
        self.qubit_spin.valueChanged.connect(self._on_qubit_change)
        row1.addWidget(self.qubit_spin)

        row1.addWidget(self._lbl("Algorithm:"))
        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(190)
        for name in ALGORITHMS:
            self.algo_combo.addItem(name)
        self.algo_combo.currentTextChanged.connect(self._on_algo_change)
        row1.addWidget(self.algo_combo)

        self.param_label = self._lbl("")
        self.param_input = QLineEdit()
        self.param_input.setMaximumWidth(100)
        self.param_input.setPlaceholderText("auto")
        self.param_label.hide()
        self.param_input.hide()
        row1.addWidget(self.param_label)
        row1.addWidget(self.param_input)

        self.run_btn = QPushButton("\u25b6  Run")
        self.run_btn.setStyleSheet(
            "QPushButton { background: #313244; color: #a6e3a1; }"
            "QPushButton:hover { border-color: #a6e3a1; background: #45475a; }"
        )
        self.run_btn.clicked.connect(self._run_algorithm)
        row1.addWidget(self.run_btn)

        row1.addWidget(self._lbl("Shots:"))
        self.shots_spin = QSpinBox()
        self.shots_spin.setRange(1, 100000)
        self.shots_spin.setValue(1024)
        self.shots_spin.setSingleStep(256)
        row1.addWidget(self.shots_spin)

        self.measure_btn = QPushButton("Measure")
        self.measure_btn.clicked.connect(self._measure)
        row1.addWidget(self.measure_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet(
            "QPushButton { color: #f38ba8; }"
            "QPushButton:hover { border-color: #f38ba8; }"
        )
        self.reset_btn.clicked.connect(self._reset)
        row1.addWidget(self.reset_btn)

        row1.addStretch()
        layout.addLayout(row1)

        # --- Row 2: Manual gate controls ---
        row2 = QHBoxLayout()
        row2.setSpacing(4)

        row2.addWidget(self._lbl("Gates:"))
        for gate in ['H', 'X', 'Y', 'Z', 'S', 'T']:
            btn = QPushButton(gate)
            btn.setMaximumWidth(38)
            btn.setToolTip(f"Apply {gate} gate to selected qubit")
            btn.clicked.connect(
                lambda _, g=gate.lower(): self._apply_manual_gate(g)
            )
            row2.addWidget(btn)

        row2.addWidget(self._lbl("  \u2192  q"))
        self.gate_qubit_spin = QSpinBox()
        self.gate_qubit_spin.setRange(0, 7)
        self.gate_qubit_spin.setMaximumWidth(55)
        row2.addWidget(self.gate_qubit_spin)

        row2.addWidget(self._lbl("    CNOT  q"))
        self.cnot_ctrl_spin = QSpinBox()
        self.cnot_ctrl_spin.setRange(0, 7)
        self.cnot_ctrl_spin.setMaximumWidth(55)
        row2.addWidget(self.cnot_ctrl_spin)
        row2.addWidget(self._lbl("\u2192 q"))
        self.cnot_tgt_spin = QSpinBox()
        self.cnot_tgt_spin.setRange(0, 7)
        self.cnot_tgt_spin.setValue(1)
        self.cnot_tgt_spin.setMaximumWidth(55)
        row2.addWidget(self.cnot_tgt_spin)

        cnot_btn = QPushButton("CNOT")
        cnot_btn.setMaximumWidth(60)
        cnot_btn.clicked.connect(self._apply_cnot)
        row2.addWidget(cnot_btn)

        row2.addStretch()
        layout.addLayout(row2)

        # --- Main area: qubit grid + histogram ---
        splitter = QSplitter(Qt.Horizontal)

        self.qubit_grid = QubitGridWidget(self.state)
        splitter.addWidget(self.qubit_grid)

        hist_widget = QWidget()
        hist_widget.setStyleSheet("background: #1e1e2e;")
        hist_layout = QVBoxLayout(hist_widget)
        hist_layout.setContentsMargins(0, 0, 0, 0)

        self.fig = Figure(figsize=(5, 4), facecolor='#1e1e2e')
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        hist_layout.addWidget(self.canvas)

        splitter.addWidget(hist_widget)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter, stretch=1)

        # --- Info labels ---
        self.info_label = QLabel(
            "Select an algorithm and click Run, or apply gates manually."
        )
        self.info_label.setStyleSheet("color: #a6adc8; padding: 4px; font-size: 11px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(
            "color: #585b70; padding: 2px 4px; font-size: 10px;"
        )
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # Init algorithm description
        self._on_algo_change(self.algo_combo.currentText())

    # -- Helpers --

    def _lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
        return lbl

    def _style_axes(self):
        self.ax.set_facecolor('#181825')
        for spine in self.ax.spines.values():
            spine.set_color('#313244')
        self.ax.tick_params(colors='#a6adc8', labelsize=8)

    # -- Callbacks --

    def _on_qubit_change(self, n):
        self.state.reset(n)
        self._algo_result = ""
        mx = n - 1
        self.gate_qubit_spin.setMaximum(mx)
        self.cnot_ctrl_spin.setMaximum(mx)
        self.cnot_tgt_spin.setMaximum(mx)
        if self.cnot_tgt_spin.value() == self.cnot_ctrl_spin.value() and n > 1:
            self.cnot_tgt_spin.setValue(min(1, mx))

    def _on_algo_change(self, name):
        info = ALGORITHMS.get(name)
        if not info:
            return
        self.desc_label.setText(info['description'])
        if info['has_params']:
            self.param_label.setText(info.get('param_label', 'Param:'))
            self.param_label.show()
            self.param_input.show()
        else:
            self.param_label.hide()
            self.param_input.hide()

    def _run_algorithm(self):
        name = self.algo_combo.currentText()
        info = ALGORITHMS.get(name)
        if not info:
            return
        n = self.qubit_spin.value()
        if n < info['min_qubits']:
            self.info_label.setText(
                f"This algorithm requires at least {info['min_qubits']} qubits."
            )
            return

        # Reset and run
        self.state.reset(n)
        kwargs = {}
        if info['has_params'] and self.param_input.text().strip():
            try:
                kwargs['target'] = int(self.param_input.text().strip())
            except ValueError:
                pass

        result = info['fn'](self.state, **kwargs)
        self._algo_result = result or ""
        self._update_display()

    def _measure(self):
        self.state.measure_all(self.shots_spin.value())

    def _reset(self):
        self.state.reset(self.qubit_spin.value())
        self._algo_result = ""

    def _apply_manual_gate(self, gate_name):
        q = self.gate_qubit_spin.value()
        if q < self.state.n_qubits:
            self.state.apply_gate(gate_name, q)
            self._algo_result = f"Applied {gate_name.upper()} to q{q}"
            self._update_info()

    def _apply_cnot(self):
        ctrl = self.cnot_ctrl_spin.value()
        tgt = self.cnot_tgt_spin.value()
        if ctrl == tgt:
            self.info_label.setText("CNOT control and target must be different qubits.")
            return
        if ctrl < self.state.n_qubits and tgt < self.state.n_qubits:
            self.state.apply_cnot(ctrl, tgt)
            self._algo_result = f"Applied CNOT q{ctrl} \u2192 q{tgt}"
            self._update_info()

    # -- Display updates --

    def _update_display(self):
        self.qubit_grid.update()
        self._update_histogram()
        self._update_info()

    def _update_histogram(self):
        self.ax.clear()
        self._style_axes()

        results = self.state.measurement_results
        if results:
            items = list(results.items())[:20]
            labels = [f"|{s}\u27e9" for s, _ in items]
            values = [c for _, c in items]
            total = sum(results.values())
            chart_title = f"Measurement Results ({total} shots)"
            bar_color = '#a6e3a1'
            fmt = lambda v: str(int(v))
        else:
            top = self.state.get_top_states(20)
            if not top:
                self.canvas.draw_idle()
                return
            labels = [f"|{s}\u27e9" for s, _ in top]
            values = [p * 100 for _, p in top]
            chart_title = "State Probabilities (%)"
            bar_color = '#89b4fa'
            fmt = lambda v: f"{v:.1f}%"

        y = np.arange(len(labels))
        self.ax.barh(
            y, values, color=bar_color, edgecolor='#45475a',
            height=0.7, alpha=0.85,
        )
        self.ax.set_yticks(y)
        fs = max(6, min(9, 11 - len(labels) // 4))
        self.ax.set_yticklabels(labels, fontfamily='monospace', fontsize=fs)
        self.ax.invert_yaxis()
        self.ax.set_title(chart_title, color='#cdd6f4', fontsize=10, pad=6)

        if values:
            mx = max(values)
            for i, v in enumerate(values):
                self.ax.text(
                    v + mx * 0.02, i, fmt(v),
                    va='center', color='#a6adc8', fontsize=7,
                )

        self.fig.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def _update_info(self):
        lines = []
        if self._algo_result:
            lines.append(self._algo_result)
        top = self.state.get_top_states(5)
        if top:
            parts = [f"|{s}\u27e9 {p:.1%}" for s, p in top]
            lines.append("Top states:  " + "   ".join(parts))
        if self.state.measurement_results:
            r = self.state.measurement_results
            best = next(iter(r))
            lines.append(f"Most frequent: |{best}\u27e9 ({r[best]} counts)")
        self.info_label.setText("\n".join(lines) if lines else "Ready.")
