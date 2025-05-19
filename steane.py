from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from custom_gates import cxx, cxxx, cxxxx, czzzz

def encode_with_steane(qc, log_q, stab_reg):
    cxx(qc, log_q, stab_reg[4], stab_reg[5])
    
    qc.h(stab_reg[:3])
        
    cxxx(qc, stab_reg[0], stab_reg[3], stab_reg[5], log_q)

    cxxx(qc, stab_reg[1], stab_reg[3], stab_reg[4], log_q)

    cxxx(qc, stab_reg[2], stab_reg[3], stab_reg[4], stab_reg[5])

    qc.barrier()

def steane_measure_syndrome(qc, log_q, stab_reg, anc_reg, class_reg):
    qc.h(anc_reg)

    cxxxx(qc, anc_reg[0], stab_reg[0], stab_reg[4], stab_reg[5], log_q)
    cxxxx(qc, anc_reg[1], stab_reg[1], stab_reg[3], stab_reg[5], log_q)
    cxxxx(qc, anc_reg[2], stab_reg[2], stab_reg[3], stab_reg[4], stab_reg[5])
    
    czzzz(qc, anc_reg[3], stab_reg[0], stab_reg[4], stab_reg[5], log_q)
    czzzz(qc, anc_reg[4], stab_reg[1], stab_reg[3], stab_reg[5], log_q)
    czzzz(qc, anc_reg[5], stab_reg[2], stab_reg[3], stab_reg[4], stab_reg[5])

    qc.h(anc_reg)    
    qc.measure(anc_reg, class_reg)

    qc.barrier()

def steane_correct_errors(qc, log_q, stab_reg, class_reg):
    def apply_correction(qc, correction, qubit):
        if correction == "X":
            qc.x(qubit)
        elif correction == "Z":
            qc.z(qubit)
        elif correction == "Y":
            qc.y(qubit)

    corrections = {
        4: ("X", stab_reg[0]), 32: ("Z", stab_reg[0]), 36: ("Y", stab_reg[0]),
        2: ("X", stab_reg[1]), 16: ("Z", stab_reg[1]), 18: ("Y", stab_reg[1]),
        1: ("X", stab_reg[2]),  8: ("Z", stab_reg[2]),  9: ("Y", stab_reg[2]),
        6: ("X", stab_reg[3]), 48: ("Z", stab_reg[3]), 54: ("Y", stab_reg[3]),
        5: ("X", stab_reg[4]), 40: ("Z", stab_reg[4]), 45: ("Y", stab_reg[4]),
        7: ("X", stab_reg[5]), 56: ("Z", stab_reg[5]), 63: ("Y", stab_reg[5]),
        3: ("X", log_q),       24: ("Z", log_q),       27: ("Y", log_q)
    }

    for value, (gate, qubit) in corrections.items():
        with qc.if_test((class_reg, value)):
            apply_correction(qc, gate, qubit)

    qc.barrier()

def decode_with_steane(qc, log_q, stab_reg, out_q):
    qc.cx(stab_reg[0], out_q)
    qc.cx(stab_reg[1], out_q)

    qc.cx(log_q, out_q)

    cxxx(qc, out_q, stab_reg[4], stab_reg[5], log_q)

    qc.barrier()

def create_steane_ghz_state(n: int) -> QuantumCircuit:
    """
    Generates an n-qubit GHZ state, encoding each qubit with the Steane code.
    n must be between 2 and 10 (inclusive).
    Returns a QuantumCircuit that performs this operation.
    """
    if not (2 <= n <= 10):
        raise ValueError("n must be between 2 and 10")

    # Each logical qubit requires: 1 logical, 6 stabilizer, 1 output, 6 ancilla, 6 classical for syndrome, 1 classical for output
    log_qubits = [QuantumRegister(1, f'log_qubit_{i}') for i in range(n)]
    stab_regs = [QuantumRegister(6, f'stab_{i}') for i in range(n)]
    out_regs = [QuantumRegister(1, f'output_{i}') for i in range(n)]
    anc_regs = [QuantumRegister(6, f'ancilla_{i}') for i in range(n)]
    class_regs = [ClassicalRegister(6, f'measured_errors_{i}') for i in range(n)]
    out_classical = ClassicalRegister(n, 'measured_output')

    # Construct the circuit with all registers (flattened)
    qc = QuantumCircuit(
        *[reg for anc in anc_regs for reg in anc],
        *[reg for stab in stab_regs for reg in stab],
        *[reg for lq in log_qubits for reg in lq],
        *[reg for out in out_regs for reg in out],
        *[reg for cl in class_regs for reg in cl],
        out_classical,
        name=f"{n}-qubit GHZ Encoded with Steane's Code"
    )

    # Initialize ancilla, output, stabilizers to |0>
    for i in range(n):
        qc.initialize(0, [q for q in anc_regs[i]])
        qc.initialize(0, [q for q in stab_regs[i]])
        qc.initialize(0, out_regs[i])

    qc.barrier()

    # Prepare logical GHZ state across log_qubits
    # |0...0> + |1...1>
    qc.h(log_qubits[0][0])
    for i in range(1, n):
        qc.cx(log_qubits[0][0], log_qubits[i][0])
    qc.barrier()

    # For each logical qubit, encode with the Steane code
    for i in range(n):
        encode_with_steane(qc, log_qubits[i][0], stab_regs[i])

    # For each logical qubit, measure syndrome and correct
    for i in range(n):
        steane_measure_syndrome(qc, log_qubits[i][0], stab_regs[i], anc_regs[i], class_regs[i])
        steane_correct_errors(qc, log_qubits[i][0], stab_regs[i], class_regs[i])

    # For each logical qubit, decode and measure
    for i in range(n):
        decode_with_steane(qc, log_qubits[i][0], stab_regs[i], out_regs[i][0])
        qc.measure(log_qubits[i][0], out_classical[i])

    return qc

def create_steane_one_qubit() -> QuantumCircuit:
    q1 = QuantumRegister(1, 'log_qubit')
    s1 = QuantumRegister(6, 'stabilizers')
    o1 = QuantumRegister(1, 'output')
    a1 = QuantumRegister(6, 'ancilla')
    c1 = ClassicalRegister(6, 'measured_errors')
    r = ClassicalRegister(2, 'measured_output')
    qc = QuantumCircuit(a1, s1, q1, o1, c1, r, name="Single Qubit Encoded with Steane's Code")

    qc.initialize(0, s1)
    qc.initialize(0, o1)
    qc.initialize(0, a1)

    qc.barrier()

    encode_with_steane(qc, q1[0], s1)

    steane_measure_syndrome(qc, q1[0], s1, a1, c1)

    steane_correct_errors(qc, q1[0], s1, c1)

    decode_with_steane(qc, q1[0], s1, o1[0])
    
    qc.measure(q1[0], r[0])

    return qc