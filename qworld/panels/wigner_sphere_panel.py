import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib import cm
from qworld.panels.base_panel import BasePanel

WIGNER_SPHERE_CMAP = LinearSegmentedColormap.from_list(
    "wigner_sphere",
    ["#89b4fa", "#1e1e2e", "#f38ba8"],
    N=256,
)


class WignerSpherePanel(BasePanel):

    def setup_axes(self):
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.ax.set_facecolor("#1e1e2e")
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def update_visualization(self):
        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")

        n_theta, n_phi = 40, 40
        theta = np.linspace(0, np.pi, n_theta)
        phi = np.linspace(0, 2 * np.pi, n_phi)

        # Compute spin Wigner function
        try:
            from qutip.wigner import spin_wigner
            W, THETA, PHI = spin_wigner(self.quantum_state.density_matrix, theta, phi)
        except ImportError:
            # Fallback: compute manually for spin-1/2
            W = self._manual_spin_wigner(theta, phi)
            THETA, PHI = np.meshgrid(theta, phi, indexing="ij")

        # Convert spherical to Cartesian
        X = np.sin(THETA) * np.cos(PHI)
        Y = np.sin(THETA) * np.sin(PHI)
        Z = np.cos(THETA)

        # Normalize Wigner values for coloring
        wmax = max(abs(W.max()), abs(W.min()), 0.001)
        norm = Normalize(vmin=-wmax, vmax=wmax)
        colors = WIGNER_SPHERE_CMAP(norm(W))

        self.ax.plot_surface(
            X, Y, Z,
            facecolors=colors,
            rstride=1, cstride=1,
            alpha=0.85,
            shade=False,
            antialiased=True,
        )

        # Wireframe
        self.ax.plot_wireframe(
            X, Y, Z,
            rstride=5, cstride=5,
            color="#585b70", linewidth=0.3, alpha=0.2,
        )

        # Axis labels at poles
        self.ax.text(0, 0, 1.25, "|0\u27e9", color="#89b4fa", fontsize=10, ha="center")
        self.ax.text(0, 0, -1.25, "|1\u27e9", color="#fab387", fontsize=10, ha="center")

        self.ax.set_xlim(-1.1, 1.1)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.set_zlim(-1.1, 1.1)
        self.ax.set_axis_off()

        # Legend
        self.ax.text2D(
            0.02, 0.02,
            "Blue=negative  Red=positive",
            transform=self.ax.transAxes,
            color="#a6adc8", fontsize=7,
        )

        self.canvas.draw_idle()

    def _manual_spin_wigner(self, theta, phi):
        """Fallback manual computation for spin-1/2 Wigner function."""
        rho = self.quantum_state.density_matrix.full()
        THETA, PHI = np.meshgrid(theta, phi, indexing="ij")

        # Spin-1/2 Wigner function: W(theta, phi) = (1/4pi) * Tr(rho * (I + n.sigma))
        # where n = (sin(theta)cos(phi), sin(theta)sin(phi), cos(theta))
        nx = np.sin(THETA) * np.cos(PHI)
        ny = np.sin(THETA) * np.sin(PHI)
        nz = np.cos(THETA)

        # rho = (1/2)(I + r.sigma) for a qubit
        # W = (1/4pi)(1 + 3*r.n) where r is the Bloch vector
        bv = self.quantum_state.get_bloch_vector()
        W = (1.0 / (4 * np.pi)) * (1 + 3 * (bv[0] * nx + bv[1] * ny + bv[2] * nz))

        return W
