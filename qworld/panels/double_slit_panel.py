import numpy as np
from PyQt5.QtCore import QTimer
from qworld.panels.base_panel import BasePanel


class DoubleSlitPanel(BasePanel):
    """
    Visualizes a photon traveling through a double-slit setup.

    Quantum state mapping:
      |0⟩ → top slit, |1⟩ → bottom slit.
    In superposition the photon takes both paths and produces an
    interference pattern on the detection screen.  After measurement
    (collapse) only one slit lights up and the pattern becomes two
    simple bumps (no interference).
    """

    SLIT_Y = np.array([0.35, -0.35])   # y positions of the two slits
    BARRIER_X = 0.0                      # x of the barrier wall
    SOURCE_X = -0.8                      # photon emitter x
    SCREEN_X = 0.8                       # detection screen x

    def __init__(self, quantum_state, title="Double-Slit Experiment", parent=None):
        self._phase = 0.0
        self._detections: list[float] = []  # y-coords of detected photons
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(50)
        super().__init__(quantum_state, title, parent)

    # ── BasePanel interface ──────────────────────────────────────────

    def setup_axes(self):
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#1e1e2e")
        self.figure.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.08)

    def update_visualization(self):
        self._draw()

    # ── Drawing ──────────────────────────────────────────────────────

    def _draw(self):
        ax = self.ax
        ax.clear()
        ax.set_facecolor("#1e1e2e")
        ax.set_xlim(-1.0, 1.1)
        ax.set_ylim(-0.85, 0.85)
        ax.set_aspect("equal")
        ax.axis("off")

        probs = self.quantum_state.get_probabilities()  # [P(|0⟩), P(|1⟩)]
        collapsed = self.quantum_state.is_collapsed

        self._draw_barrier(ax)
        self._draw_source(ax)
        self._draw_screen(ax, probs, collapsed)
        self._draw_photon(ax, probs, collapsed)
        self._draw_detection_dots(ax)
        self._draw_labels(ax, probs, collapsed)

        self.canvas.draw_idle()

    # ── Static elements ──────────────────────────────────────────────

    def _draw_barrier(self, ax):
        """Dark wall with two bright slit openings."""
        gap = 0.06  # half-height of each slit opening
        bx = self.BARRIER_X
        wall_color = "#585b70"
        slit_color = "#89dceb"

        # wall segments (top, middle, bottom)
        ax.plot([bx, bx], [0.8, self.SLIT_Y[0] + gap], color=wall_color, lw=4, solid_capstyle="butt")
        ax.plot([bx, bx], [self.SLIT_Y[0] - gap, self.SLIT_Y[1] + gap], color=wall_color, lw=4, solid_capstyle="butt")
        ax.plot([bx, bx], [self.SLIT_Y[1] - gap, -0.8], color=wall_color, lw=4, solid_capstyle="butt")

        # slit highlights
        for sy in self.SLIT_Y:
            ax.plot([bx, bx], [sy - gap, sy + gap], color=slit_color, lw=3, alpha=0.8, solid_capstyle="round")

    def _draw_source(self, ax):
        """Glowing photon emitter on the left."""
        sx = self.SOURCE_X
        ax.plot(sx, 0, "o", color="#f9e2af", ms=9, zorder=5)
        for r, a in [(14, 0.12), (20, 0.05)]:
            ax.plot(sx, 0, "o", color="#f9e2af", ms=r, alpha=a, zorder=4)
        ax.text(sx, -0.14, "source", color="#a6adc8", fontsize=7, ha="center")

    def _draw_screen(self, ax, probs, collapsed):
        """Detection screen with the probability distribution."""
        scr = self.SCREEN_X
        ax.plot([scr, scr], [-0.75, 0.75], color="#585b70", lw=2)

        y = np.linspace(-0.75, 0.75, 300)
        intensity = self._intensity_profile(y, probs, collapsed)
        # normalise so the curve doesn't extend too far from the screen
        intensity = intensity / (intensity.max() + 1e-9) * 0.22

        ax.fill_betweenx(y, scr, scr + intensity, color="#cba6f7", alpha=0.45)
        ax.plot(scr + intensity, y, color="#cba6f7", lw=1.2, alpha=0.8)

    def _draw_detection_dots(self, ax):
        """Previously detected photon hits on the screen."""
        if not self._detections:
            return
        xs = [self.SCREEN_X] * len(self._detections)
        ax.scatter(xs, self._detections, s=3, color="#f9e2af", alpha=0.7, zorder=6)

    def _draw_labels(self, ax, probs, collapsed):
        mode = "Particle (collapsed)" if collapsed else "Wave (superposition)"
        ax.text(
            0.5, 0.01, mode, transform=ax.transAxes,
            ha="center", va="bottom", color="#a6e3a1", fontsize=8, fontstyle="italic",
        )
        ax.text(
            0.02, 0.98,
            f"P(slit₁)={probs[0]:.2f}  P(slit₂)={probs[1]:.2f}",
            transform=ax.transAxes, ha="left", va="top",
            color="#a6adc8", fontsize=8,
        )

    # ── Animated photon ──────────────────────────────────────────────

    def _draw_photon(self, ax, probs, collapsed):
        """
        Draw the traveling photon.

        phase ∈ [0, 1):
          [0 … 0.4)   source → barrier  (straight line)
          [0.4 … 1.0)  barrier → screen  (one or two paths)
        """
        t = self._phase  # [0, 1)

        if t < 0.4:
            # approaching the barrier
            frac = t / 0.4
            x = self.SOURCE_X + frac * (self.BARRIER_X - self.SOURCE_X)
            self._photon_dot(ax, x, 0)
            # leading "wave" lines
            if not collapsed:
                for dy in [0.04, -0.04]:
                    ax.plot([x - 0.06, x], [dy, 0], color="#f9e2af", lw=0.6, alpha=0.35)
        else:
            frac = (t - 0.4) / 0.6
            x = self.BARRIER_X + frac * (self.SCREEN_X - self.BARRIER_X)

            if collapsed:
                # single path through the measured slit
                slit_idx = self.quantum_state.last_measurement or 0
                y = self.SLIT_Y[slit_idx]
                # slight spread toward screen centre
                y_end = y * (1 - 0.3 * frac)
                cur_y = y + (y_end - y) * frac
                self._photon_dot(ax, x, cur_y)
                ax.plot(
                    [self.BARRIER_X, x], [y, cur_y],
                    color="#f9e2af", lw=0.8, alpha=0.4,
                )
            else:
                # superposition – two ghost paths
                for i, sy in enumerate(self.SLIT_Y):
                    alpha_path = float(probs[i])
                    y_end = sy * (1 - 0.3 * frac)
                    cur_y = sy + (y_end - sy) * frac
                    self._photon_dot(ax, x, cur_y, alpha=0.4 + 0.4 * alpha_path)
                    # wavefront arcs
                    angles = np.linspace(-0.5, 0.5, 40)
                    wave_r = frac * 0.55
                    wx = self.BARRIER_X + wave_r * np.cos(angles)
                    wy = sy + wave_r * np.sin(angles)
                    ax.plot(wx, wy, color="#89dceb", lw=0.6, alpha=0.25 * alpha_path)

    def _photon_dot(self, ax, x, y, alpha=1.0):
        ax.plot(x, y, "o", color="#f9e2af", ms=7, alpha=alpha, zorder=5)
        ax.plot(x, y, "o", color="#f9e2af", ms=12, alpha=0.12 * alpha, zorder=4)

    # ── Intensity profile ────────────────────────────────────────────

    @staticmethod
    def _intensity_profile(y, probs, collapsed):
        """
        Return the expected intensity on the screen at each y.

        With superposition (wave) we get interference fringes.
        After collapse (particle) we get two Gaussian bumps.
        """
        slit_sep = 0.70   # distance between slits
        slit_w = 0.06     # effective slit width
        wavelength = 0.18  # effective wavelength for fringe spacing

        # single-slit diffraction envelope for each slit
        env0 = np.exp(-((y - slit_sep / 2) ** 2) / (2 * slit_w ** 2))
        env1 = np.exp(-((y + slit_sep / 2) ** 2) / (2 * slit_w ** 2))

        if collapsed:
            return probs[0] * env0 + probs[1] * env1

        # interference: I = |ψ₀ e^{iφ₀} + ψ₁ e^{iφ₁}|²
        phase_diff = 2 * np.pi * slit_sep * y / wavelength
        a0 = np.sqrt(probs[0])
        a1 = np.sqrt(probs[1])
        envelope = np.exp(-(y ** 2) / (2 * (3 * slit_w) ** 2))
        intensity = (a0 ** 2 + a1 ** 2 + 2 * a0 * a1 * np.cos(phase_diff)) * envelope
        return intensity

    # ── Animation ────────────────────────────────────────────────────

    def _tick(self):
        self._phase += 0.015
        if self._phase >= 1.0:
            self._phase -= 1.0
            self._register_detection()
        self._draw()

    def _register_detection(self):
        """Sample a detection hit from the current intensity profile."""
        probs = self.quantum_state.get_probabilities()
        collapsed = self.quantum_state.is_collapsed

        y = np.linspace(-0.75, 0.75, 300)
        pdf = self._intensity_profile(y, probs, collapsed)
        pdf = pdf / (pdf.sum() + 1e-12)
        hit = float(np.random.choice(y, p=pdf))
        self._detections.append(hit)
        # keep last 500 hits so the scatter doesn't get too heavy
        if len(self._detections) > 500:
            self._detections = self._detections[-500:]
