from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from qworld.gates import FIXED_GATES


class GateToolbar(QWidget):

    def __init__(self, quantum_state, parent=None):
        super().__init__(parent)
        self.quantum_state = quantum_state

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        for label, gate_fn, tooltip in FIXED_GATES:
            btn = QPushButton(label)
            btn.setToolTip(tooltip)
            btn.setFixedSize(52, 36)
            btn.setStyleSheet("""
                QPushButton {
                    background: #313244;
                    color: #cdd6f4;
                    border: 1px solid #585b70;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #45475a;
                    border-color: #89b4fa;
                }
                QPushButton:pressed {
                    background: #89b4fa;
                    color: #1e1e2e;
                }
            """)
            btn.clicked.connect(lambda checked, gf=gate_fn: self.quantum_state.apply_gate(gf()))
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)
