# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is QWorld

QWorld is a desktop quantum state visualizer built with PyQt5 and QuTiP. It provides real-time interactive visualization of single-qubit and two-qubit quantum states through multiple simultaneous panels.

## Running the App

```bash
# Activate the virtualenv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

The app requires a display (Qt5 GUI). The matplotlib backend is forced to `Qt5Agg` in `run.py`.

## Architecture

### Signal-driven reactive pattern
The app uses a central state object that emits a `state_changed` PyQt signal whenever the quantum state is modified. All visualization panels connect to this signal and redraw themselves automatically. This is the core architectural pattern — there is no manual orchestration of panel updates.

There are two independent state engines:
- **`QuantumState`** (`qworld/quantum_state.py`) — single-qubit state (2D Hilbert space). Used by most panels.
- **`EntangledState`** (`qworld/entangled_state.py`) — two-qubit state (4D Hilbert space, `dims=[[2,2],[1,1]]`). Self-contained, used only by `EntanglementPanel`.

Both inherit from `QObject` and emit `state_changed` signals.

### Panel system
All visualization panels inherit from `BasePanel` (`qworld/panels/base_panel.py`), which:
- Embeds a matplotlib `Figure` + `FigureCanvasQTAgg` in a `QWidget`
- Auto-connects to `quantum_state.state_changed` in `__init__`
- Requires subclasses to implement `setup_axes()` and `update_visualization()`
- Uses a custom metaclass (`_BasePanelMeta`) to resolve the ABCMeta/Qt metaclass conflict

**Exception:** `EntanglementPanel` does NOT inherit from `BasePanel` — it's a standalone `QWidget` that manages its own figure/canvas and its own `EntangledState`.

### Panels (all in `qworld/panels/`)
| Panel | State engine | Animated |
|---|---|---|
| `BlochPanel` — 3D Bloch sphere with history trail | QuantumState | Yes (pulsing cloud) |
| `ProbabilityPanel` — bar chart of |0>/|1> probabilities | QuantumState | No |
| `PolarizationPanel` — photon polarization ellipse | QuantumState | Yes (orbiting dot) |
| `WignerPanel` — phase-space Wigner function (2D contour) | QuantumState | No |
| `WignerSpherePanel` — spin Wigner function on unit sphere | QuantumState | No |
| `DoubleSlitPanel` — double-slit experiment simulation | QuantumState | Yes (traveling photon) |
| `EntanglementPanel` — two-qubit entanglement visualization | EntangledState | Yes (beams + glow) |

### Widgets (all in `qworld/widgets/`)
- `GateToolbar` — buttons for fixed gates (H, X, Y, Z, S, T)
- `RotationControls` — sliders + apply buttons for Rx, Ry, Rz
- `MeasurementWidget` — measure/reset buttons with statistics tracking
- `StateInfo` — text display of amplitudes, Bloch vector, density matrix, purity, entropy

### Gate definitions (`qworld/gates.py`, `qworld/two_qubit_gates.py`)
Gates return QuTiP `Qobj` matrices. `FIXED_GATES` and `ROTATION_GATES` lists drive the UI generation — adding a gate to these lists automatically creates the corresponding button/slider.

### App layout (`qworld/app.py`)
`MainWindow` uses nested `QSplitter` widgets in a 4-column layout. The Catppuccin Mocha dark theme is applied via `DARK_THEME` stylesheet constant.

## Key Conventions

- **Color palette:** Catppuccin Mocha throughout (e.g. `#1e1e2e` background, `#cdd6f4` text, `#89b4fa` blue, `#f38ba8` pink)
- **State representation:** Pure states are ket vectors (`Qobj.isket == True`); after certain operations they may become density matrices
- **Animation:** Animated panels use `QTimer` with 50-60ms intervals. Animation state is internal to each panel.
- **QuTiP version:** Requires QuTiP >= 5.0 (uses `qutip.core.gates` import path)
