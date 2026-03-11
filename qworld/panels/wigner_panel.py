
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from qworld.panels.base_panel import BasePanel

# Wigner function colormap: blue (negative/quantum) -> white (zero) -> red (positive/classical)
WIGNER_CMAP = LinearSegmentedColormap.from_list(
    "wigner",
    ["#89b4fa", "#1e1e2e", "#f38ba8"],
    N=256,
)


class WignerPanel(BasePanel):

    def setup_axes(self):
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#1e1e2e")
        self.figure.subplots_adjust(left=0.12, right=0.88, top=0.92, bottom=0.12)
        self._cbar_ax = None

    def update_visualization(self):
        # Remove previous colorbar axes if it exists
        if self._cbar_ax is not None:
            try:
                self._cbar_ax.remove()
            except Exception:
                pass
            self._cbar_ax = None

        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")

        xvec = np.linspace(-3, 3, 80)
        W, xvec = self.quantum_state.get_phase_space_wigner(xvec)

        wmax = max(abs(W.max()), abs(W.min()), 0.001)

        contour = self.ax.contourf(
            xvec, xvec, W,
            levels=30,
            cmap=WIGNER_CMAP,
            vmin=-wmax, vmax=wmax,
        )

        # Contour lines for negative regions
        if W.min() < -0.001:
            self.ax.contour(
                xvec, xvec, W,
                levels=[W.min() / 2],
                colors=["#89dceb"],
                linewidths=0.8,
                alpha=0.6,
            )

        # Colorbar
        cbar = self.figure.colorbar(contour, ax=self.ax, shrink=0.8, pad=0.02)
        cbar.ax.tick_params(colors="#a6adc8", labelsize=7)
        self._cbar_ax = cbar.ax

        self.ax.set_xlabel("Re(\u03b1)", color="#cdd6f4", fontsize=9)
        self.ax.set_ylabel("Im(\u03b1)", color="#cdd6f4", fontsize=9)
        self.ax.tick_params(colors="#a6adc8", labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color("#585b70")

        # Non-classical indicator
        has_negative = W.min() < -0.001
        if has_negative:
            self.ax.text(
                0.02, 0.02,
                "Negative regions = non-classical",
                transform=self.ax.transAxes, ha="left", va="bottom",
                color="#89dceb", fontsize=7, style="italic",
            )

        self.canvas.draw_idle()
