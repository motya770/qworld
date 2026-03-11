import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from qworld.quantum_state import QuantumState
from qworld.panels.bloch_panel import BlochPanel
from qworld.panels.probability_panel import ProbabilityPanel
from qworld.panels.polarization_panel import PolarizationPanel
from qworld.panels.wigner_panel import WignerPanel
from qworld.panels.wigner_sphere_panel import WignerSpherePanel
from qworld.panels.double_slit_panel import DoubleSlitPanel
from qworld.panels.entanglement_panel import EntanglementPanel
from qworld.widgets.gate_toolbar import GateToolbar
from qworld.widgets.rotation_controls import RotationControls
from qworld.widgets.state_info import StateInfo
from qworld.widgets.measurement_widget import MeasurementWidget


DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QSplitter::handle {
    background: #313244;
    width: 2px;
    height: 2px;
}
QStatusBar {
    background: #181825;
    color: #a6adc8;
    font-family: monospace;
    font-size: 11px;
    border-top: 1px solid #313244;
}
QToolTip {
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #585b70;
    padding: 4px;
    font-size: 11px;
}
"""


class QWorldApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setStyleSheet(DARK_THEME)
        self.setFont(QFont("SF Mono, Menlo, Consolas, monospace", 10))
        self.window = MainWindow()
        self.window.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QWorld \u2014 Quantum State Visualizer")
        self.setMinimumSize(1700, 900)

        self.quantum_state = QuantumState()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Title bar
        title = QLabel("QWorld \u2014 Quantum Photon Simulator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #cba6f7; font-size: 16px; font-weight: bold; padding: 4px;"
        )
        main_layout.addWidget(title)

        # Gate toolbar
        self.gate_toolbar = GateToolbar(self.quantum_state)
        main_layout.addWidget(self.gate_toolbar)

        # Main visualization area
        middle_splitter = QSplitter(Qt.Horizontal)

        # Left column: Bloch sphere + Probability bars
        left_column = QSplitter(Qt.Vertical)
        self.bloch_panel = BlochPanel(self.quantum_state, title="Bloch Sphere")
        self.prob_panel = ProbabilityPanel(
            self.quantum_state, title="Measurement Probabilities"
        )
        left_column.addWidget(self.bloch_panel)
        left_column.addWidget(self.prob_panel)
        left_column.setSizes([550, 350])

        # Center column: Double-slit + Polarization + Wigner function
        center_column = QSplitter(Qt.Vertical)
        self.double_slit_panel = DoubleSlitPanel(
            self.quantum_state, title="Double-Slit Experiment"
        )
        self.polar_panel = PolarizationPanel(
            self.quantum_state, title="Photon Polarization"
        )
        self.wigner_panel = WignerPanel(
            self.quantum_state, title="Wigner Function (Phase Space)"
        )
        center_column.addWidget(self.double_slit_panel)
        center_column.addWidget(self.polar_panel)
        center_column.addWidget(self.wigner_panel)
        center_column.setSizes([350, 300, 300])

        # Right column: Wigner sphere + Controls
        right_column = QSplitter(Qt.Vertical)
        self.wigner_sphere = WignerSpherePanel(
            self.quantum_state, title="Spin Wigner Sphere"
        )

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        controls_layout.setSpacing(6)

        self.rotation_controls = RotationControls(self.quantum_state)
        self.measurement_widget = MeasurementWidget(self.quantum_state)
        self.state_info = StateInfo(self.quantum_state)

        controls_layout.addWidget(self.rotation_controls)
        controls_layout.addWidget(self.measurement_widget)
        controls_layout.addWidget(self.state_info)
        controls_layout.addStretch()

        right_column.addWidget(self.wigner_sphere)
        right_column.addWidget(controls_widget)
        right_column.setSizes([450, 450])

        # Fourth column: Entanglement panel
        fourth_column = QSplitter(Qt.Vertical)
        self.entanglement_panel = EntanglementPanel()
        fourth_column.addWidget(self.entanglement_panel)

        middle_splitter.addWidget(left_column)
        middle_splitter.addWidget(center_column)
        middle_splitter.addWidget(right_column)
        middle_splitter.addWidget(fourth_column)
        middle_splitter.setSizes([350, 380, 380, 400])

        main_layout.addWidget(middle_splitter)

        # Status bar
        self.statusBar().showMessage("Ready \u2014 State: |0\u27e9")
        self.quantum_state.state_changed.connect(self._update_status)

    def _update_status(self):
        probs = self.quantum_state.get_probabilities()
        bv = self.quantum_state.get_bloch_vector()
        collapsed = " [COLLAPSED]" if self.quantum_state.is_collapsed else ""
        self.statusBar().showMessage(
            f"P(|0\u27e9)={probs[0]:.4f}  P(|1\u27e9)={probs[1]:.4f}  "
            f"Bloch=({bv[0]:.3f}, {bv[1]:.3f}, {bv[2]:.3f}){collapsed}"
        )
