import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton,
)
from PyQt5.QtCore import Qt
from qworld.gates import ROTATION_GATES


class RotationControls(QWidget):

    def __init__(self, quantum_state, parent=None):
        super().__init__(parent)
        self.quantum_state = quantum_state

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Rotation Gates")
        header.setStyleSheet("color: #cdd6f4; font-size: 11px; font-weight: bold;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self._sliders = {}
        self._labels = {}

        for gate_label, gate_fn, tooltip in ROTATION_GATES:
            row = QHBoxLayout()
            row.setSpacing(4)

            name = QLabel(gate_label)
            name.setFixedWidth(24)
            name.setStyleSheet("color: #cdd6f4; font-size: 11px; font-weight: bold;")
            row.addWidget(name)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 360)
            slider.setValue(0)
            slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #313244; height: 6px; border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #89b4fa; width: 14px; margin: -4px 0;
                    border-radius: 7px;
                }
                QSlider::sub-page:horizontal {
                    background: #585b70; border-radius: 3px;
                }
            """)
            row.addWidget(slider)
            self._sliders[gate_label] = slider

            val_label = QLabel("0\u00b0")
            val_label.setFixedWidth(36)
            val_label.setStyleSheet("color: #a6adc8; font-size: 10px;")
            row.addWidget(val_label)
            self._labels[gate_label] = val_label

            apply_btn = QPushButton("\u2713")
            apply_btn.setFixedSize(28, 24)
            apply_btn.setToolTip(f"Apply {gate_label}")
            apply_btn.setStyleSheet("""
                QPushButton {
                    background: #313244; color: #a6e3a1; border: 1px solid #585b70;
                    border-radius: 3px; font-size: 12px;
                }
                QPushButton:hover { background: #45475a; border-color: #a6e3a1; }
                QPushButton:pressed { background: #a6e3a1; color: #1e1e2e; }
            """)
            apply_btn.clicked.connect(
                lambda checked, gl=gate_label, gf=gate_fn: self._apply_rotation(gl, gf)
            )
            row.addWidget(apply_btn)

            slider.valueChanged.connect(
                lambda val, gl=gate_label: self._labels[gl].setText(f"{val}\u00b0")
            )

            layout.addLayout(row)

        self.setLayout(layout)

    def _apply_rotation(self, gate_label, gate_fn):
        angle_deg = self._sliders[gate_label].value()
        angle_rad = np.radians(angle_deg)
        if abs(angle_rad) > 1e-10:
            self.quantum_state.apply_gate(gate_fn(angle_rad))
