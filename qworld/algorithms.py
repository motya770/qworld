import numpy as np


ALGORITHMS = {}


def register(name, description, min_qubits=2, has_params=False, param_label=None):
    """Decorator to register a quantum algorithm."""
    def decorator(fn):
        ALGORITHMS[name] = {
            'fn': fn,
            'description': description,
            'min_qubits': min_qubits,
            'has_params': has_params,
            'param_label': param_label,
        }
        return fn
    return decorator


@register(
    "GHZ State",
    "Creates a GHZ state: (|00\u20260\u27e9 + |11\u20261\u27e9) / \u221a2\n"
    "Applies Hadamard to q0, then CNOT from q0 to all others.\n"
    "Measurement collapses to all-0 or all-1 with equal probability.",
)
def ghz_state(state, **kwargs):
    n = state.n_qubits
    state.begin_batch()
    state.apply_gate('h', 0)
    for i in range(1, n):
        state.apply_cnot(0, i)
    state.end_batch()
    return f"GHZ state on {n} qubits: (|{'0'*n}\u27e9 + |{'1'*n}\u27e9)/\u221a2"


@register(
    "Grover's Search",
    "Amplitude amplification to find a marked item in an unsorted database.\n"
    "Achieves quadratic speedup: O(\u221aN) vs classical O(N).\n"
    "Enter a target state in decimal, or leave blank for random.",
    has_params=True,
    param_label="Target (decimal):",
)
def grovers_search(state, target=None, **kwargs):
    n = state.n_qubits
    N = 2 ** n
    if target is None:
        target = np.random.randint(0, N)
    target = int(target) % N
    num_iter = max(1, int(np.round(np.pi / 4 * np.sqrt(N))))

    state.begin_batch()

    # Uniform superposition
    for i in range(n):
        state.apply_gate('h', i)

    for _ in range(num_iter):
        # Oracle: negate amplitude of |target>
        state.flip_phase(target)
        # Diffusion: 2|s><s| - I (inversion about the mean)
        mean = np.mean(state._state)
        state._state[:] = 2 * mean - state._state

    state.end_batch()
    bs = format(target, f'0{n}b')
    return f"Grover's search for |{bs}\u27e9 \u2014 {num_iter} iterations"


@register(
    "Deutsch-Jozsa",
    "Determines whether a Boolean function f is constant or balanced\n"
    "using a single query (classically needs up to 2^(n\u22121)+1).\n"
    "All-zeros measurement \u2192 constant; any non-zero bit \u2192 balanced.",
)
def deutsch_jozsa(state, **kwargs):
    n = state.n_qubits
    balanced = bool(np.random.choice([True, False]))

    state.begin_batch()
    for i in range(n):
        state.apply_gate('h', i)

    if balanced:
        # Balanced oracle: f(x) = x_0, implemented as Z on qubit 0
        state.apply_gate('z', 0)

    for i in range(n):
        state.apply_gate('h', i)
    state.end_batch()

    kind = "balanced" if balanced else "constant"
    expected = f"|{'1' + '0'*(n-1)}\u27e9" if balanced else f"|{'0'*n}\u27e9"
    return f"Deutsch-Jozsa ({kind} oracle) \u2192 expect {expected}"


@register(
    "Bernstein-Vazirani",
    "Finds a hidden binary string s with a single query.\n"
    "Oracle computes f(x) = s\u00b7x mod 2. Classically needs n queries.\n"
    "Enter secret in decimal, or leave blank for random.",
    has_params=True,
    param_label="Secret (decimal):",
)
def bernstein_vazirani(state, target=None, **kwargs):
    n = state.n_qubits
    N = 2 ** n
    if target is None:
        target = np.random.randint(1, N)
    target = int(target) % N
    secret = format(target, f'0{n}b')

    state.begin_batch()
    for i in range(n):
        state.apply_gate('h', i)

    # Oracle: Z on each qubit where the secret bit is 1
    for i in range(n):
        if (target >> (n - 1 - i)) & 1:
            state.apply_gate('z', i)

    for i in range(n):
        state.apply_gate('h', i)
    state.end_batch()

    return f"Bernstein-Vazirani: secret s = {secret} \u2192 expect |{secret}\u27e9"


@register(
    "Quantum Fourier Transform",
    "Transforms computational basis to frequency basis.\n"
    "Foundation of Shor's algorithm and quantum phase estimation.\n"
    "Applied to |0\u20260\u20261\u27e9 \u2014 output has uniform probabilities with phase structure.",
)
def qft(state, **kwargs):
    n = state.n_qubits
    state.begin_batch()

    # Prepare input |1> (last qubit set)
    state.apply_gate('x', n - 1)

    # QFT circuit
    for i in range(n):
        state.apply_gate('h', i)
        for j in range(i + 1, n):
            angle = np.pi / (2 ** (j - i))
            state.apply_controlled_phase(j, i, angle)

    # Bit-reversal swap
    for i in range(n // 2):
        state.apply_swap(i, n - 1 - i)

    state.end_batch()
    return f"QFT on |{'0'*(n-1)}1\u27e9 \u2192 uniform amplitudes with encoded phases"


@register(
    "W State",
    "Equal superposition of all single-excitation states:\n"
    "(|10\u20260\u27e9 + |01\u20260\u27e9 + \u2026 + |00\u20261\u27e9) / \u221an\n"
    "Different entanglement structure from GHZ \u2014 more robust to qubit loss.",
)
def w_state(state, **kwargs):
    n = state.n_qubits
    state.begin_batch()
    state._state[:] = 0
    for i in range(n):
        idx = 1 << (n - 1 - i)
        state._state[idx] = 1.0 / np.sqrt(n)
    state.end_batch()
    return f"W state on {n} qubits: {n} terms with amplitude 1/\u221a{n}"


@register(
    "Random Circuit",
    "Random single-qubit gates and CNOTs at each layer.\n"
    "Produces a pseudo-random quantum state (Porter-Thomas distribution).\n"
    "Useful for benchmarking and exploring Hilbert space.",
)
def random_circuit(state, **kwargs):
    n = state.n_qubits
    depth = n * 3
    gates = ['h', 'x', 'y', 'z', 's', 't']

    state.begin_batch()
    for _ in range(depth):
        for q in range(n):
            if np.random.random() < 0.5:
                state.apply_gate(np.random.choice(gates), q)
        qubits = list(range(n))
        np.random.shuffle(qubits)
        for i in range(0, n - 1, 2):
            if np.random.random() < 0.5:
                state.apply_cnot(qubits[i], qubits[i + 1])
    state.end_batch()
    return f"Random circuit: depth {depth} on {n} qubits"
