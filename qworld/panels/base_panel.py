from abc import ABCMeta, abstractmethod
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class _BasePanelMeta(ABCMeta, type(QWidget)):
    """Resolve metaclass conflict between ABCMeta and Qt's sip wrapper type."""
    pass


class BasePanel(QWidget, metaclass=_BasePanelMeta):
    """
    Abstract base class for all visualization panels.
    Each panel owns a matplotlib Figure + Canvas embedded in a QWidget.
    """

    def __init__(self, quantum_state, title="", parent=None):
        super().__init__(parent)
        self.quantum_state = quantum_state
        self.title = title

        self.figure = Figure(figsize=(4, 4), dpi=100, facecolor="#1e1e2e")
        self.canvas = FigureCanvasQTAgg(self.figure)

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        if title:
            label = QLabel(title)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                "color: #cdd6f4; font-size: 11px; font-weight: bold; "
                "padding: 2px; background: #181825;"
            )
            layout.addWidget(label)

        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.quantum_state.state_changed.connect(self.update_visualization)

        self.setup_axes()
        self.update_visualization()

    @abstractmethod
    def setup_axes(self):
        pass

    @abstractmethod
    def update_visualization(self):
        pass
