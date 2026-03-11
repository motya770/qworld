import numpy as np
from qutip import Bloch
from PyQt5.QtCore import QTimer
from qworld.panels.base_panel import BasePanel


class BlochPanel(BasePanel):

    def __init__(self, quantum_state, title="Bloch Sphere", parent=None):
        self._cloud_alpha = 0.3
        self._cloud_direction = 1
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._animate_pulse)
        self._pulse_timer.start(60)
        super().__init__(quantum_state, title, parent)

    def setup_axes(self):
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.ax.set_facecolor("#1e1e2e")
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def update_visualization(self):
        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")

        # Draw the Bloch sphere using QuTiP
        b = Bloch(fig=self.figure, axes=self.ax)
        b.frame_color = "#585b70"
        b.font_color = "#cdd6f4"
        b.frame_alpha = 0.1
        b.sphere_color = "#313244"
        b.sphere_alpha = 0.08
        b.vector_color = ["#f38ba8"]
        b.point_color = ["#89b4fa"]
        b.vector_width = 3

        # Current state vector
        bv = self.quantum_state.get_bloch_vector()
        b.add_vectors([bv])

        # History trail
        history = self.quantum_state.get_bloch_history()
        if len(history) > 1:
            xs = [h[0] for h in history]
            ys = [h[1] for h in history]
            zs = [h[2] for h in history]
            b.add_points([xs, ys, zs], meth="l")

        b.render()

        # Draw superposition probability cloud
        entropy = self.quantum_state.get_entropy()
        if entropy > 0.01:
            self._draw_superposition_cloud(bv, entropy)

        # Style the axes
        self.ax.set_axis_off()
        self.canvas.draw_idle()

    def _draw_superposition_cloud(self, bloch_vec, entropy):
        cloud_radius = 0.25 * np.sqrt(entropy)
        n_points = 60
        rng = np.random.default_rng(42)

        offsets = rng.normal(0, cloud_radius, (n_points, 3))
        cloud_points = np.array(bloch_vec) + offsets

        # Clip to unit sphere surface region
        norms = np.linalg.norm(cloud_points, axis=1, keepdims=True)
        mask = norms.flatten() <= 1.2
        cloud_points = cloud_points[mask]

        if len(cloud_points) > 0:
            self.ax.scatter(
                cloud_points[:, 1],  # QuTiP Bloch uses (y, x, z) ordering
                cloud_points[:, 0],
                cloud_points[:, 2],
                c="#89dceb",
                alpha=self._cloud_alpha * 0.5,
                s=8,
                edgecolors="none",
            )

    def _animate_pulse(self):
        self._cloud_alpha += 0.02 * self._cloud_direction
        if self._cloud_alpha >= 0.6:
            self._cloud_direction = -1
        elif self._cloud_alpha <= 0.15:
            self._cloud_direction = 1
