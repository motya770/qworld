from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
)
from PyQt5.QtCore import Qt, QTimer


class MeasurementWidget(QWidget):

    def __init__(self, quantum_state, parent=None):
        super().__init__(parent)
        self.quantum_state = quantum_state

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Buttons row
        btn_row = QHBoxLayout()

        self.measure_btn = QPushButton("Measure")
        self.measure_btn.setStyleSheet("""
            QPushButton {
                background: #f38ba8; color: #1e1e2e; border: none;
                border-radius: 4px; padding: 6px 16px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #eba0ac; }
            QPushButton:pressed { background: #f5c2e7; }
        """)
        self.measure_btn.clicked.connect(self._on_measure)
        btn_row.addWidget(self.measure_btn)

        self.reset_btn = QPushButton("Reset |0\u27e9")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: #313244; color: #cdd6f4; border: 1px solid #585b70;
                border-radius: 4px; padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background: #45475a; border-color: #89b4fa; }
            QPushButton:pressed { background: #89b4fa; color: #1e1e2e; }
        """)
        self.reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(self.reset_btn)

        layout.addLayout(btn_row)

        # Result flash label
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet(
            "color: #f9e2af; font-size: 16px; font-weight: bold; padding: 4px;"
        )
        layout.addWidget(self.result_label)

        # Statistics
        self.stats_label = QLabel("No measurements yet")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #a6adc8; font-size: 10px;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)

        # Clear stats button
        clear_btn = QPushButton("Clear Stats")
        clear_btn.setFixedHeight(22)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #585b70; border: 1px solid #45475a;
                border-radius: 3px; font-size: 9px;
            }
            QPushButton:hover { color: #cdd6f4; border-color: #585b70; }
        """)
        clear_btn.clicked.connect(self._clear_stats)
        layout.addWidget(clear_btn)

        self.setLayout(layout)

        self._flash_timer = QTimer()
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(lambda: self.result_label.setText(""))

    def _on_measure(self):
        outcome = self.quantum_state.measure()
        color = "#89b4fa" if outcome == 0 else "#fab387"
        self.result_label.setStyleSheet(
            f"color: {color}; font-size: 18px; font-weight: bold; padding: 4px;"
        )
        self.result_label.setText(f"MEASURED: |{outcome}\u27e9")
        self._flash_timer.start(2000)
        self._update_stats()

    def _on_reset(self):
        self.quantum_state.reset()
        self.result_label.setText("")

    def _update_stats(self):
        counts = self.quantum_state.measurement_counts
        total = counts[0] + counts[1]
        if total == 0:
            self.stats_label.setText("No measurements yet")
            return
        p0 = counts[0] / total * 100
        p1 = counts[1] / total * 100
        self.stats_label.setText(
            f"|0\u27e9: {counts[0]} ({p0:.1f}%)  \u2502  "
            f"|1\u27e9: {counts[1]} ({p1:.1f}%)  \u2502  "
            f"Total: {total}"
        )

    def _clear_stats(self):
        self.quantum_state.clear_stats()
        self.stats_label.setText("No measurements yet")
