from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

def create_ghz_state(n: int) -> QuantumCircuit:
    """
    Generates an n-qubit GHZ state (unencoded).
    n must be between 2 and 10 (inclusive).
    Returns a QuantumCircuit that performs this operation.
    """
    if not (2 <= n <= 10):
        raise ValueError("n must be between 2 and 10")
    q = QuantumRegister(n, 'q')
    c = ClassicalRegister(n, 'measured_output')
    qc = QuantumCircuit(q, c, name=f"{n}-qubit GHZ State Unencoded")
    
    # GHZ State |0...0> + |1...1>
    qc.h(q[0])
    for i in range(1, n):
        qc.cx(q[0], q[i])
    qc.barrier()

    # Measure all qubits
    for i in range(n):
        qc.measure(q[i], c[i])
    
    return qc