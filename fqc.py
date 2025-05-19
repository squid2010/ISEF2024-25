from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from custom_gates import czz, cxxzz

def encode_with_fqc(qc, log_q, stab_reg):
    qc.h(stab_reg[0])
    qc.s(stab_reg[0])
    qc.cy(stab_reg[0], log_q)
    
    qc.h(stab_reg[1])
    qc.cx(stab_reg[1], log_q)
    
    qc.h(stab_reg[2])
    czz(qc, stab_reg[2], stab_reg[0], stab_reg[1])
    qc.cx(stab_reg[2], log_q)
        
    qc.h(stab_reg[3])
    qc.s(stab_reg[3])
    czz(qc, stab_reg[3], stab_reg[0], stab_reg[2])
    qc.cy(stab_reg[3], log_q)

    qc.barrier()

def fqc_measure_syndrome(qc, log_q, stab_reg, anc_reg, class_reg):
    qc.h(anc_reg)
    
    cxxzz(qc, anc_reg[0], stab_reg[0], stab_reg[3], stab_reg[1], stab_reg[2])
    cxxzz(qc, anc_reg[1], stab_reg[1], log_q, stab_reg[2], stab_reg[3])
    cxxzz(qc, anc_reg[2], stab_reg[0], stab_reg[2], stab_reg[3], log_q)
    cxxzz(qc, anc_reg[3], stab_reg[1], stab_reg[3], stab_reg[0], log_q)

    qc.h(anc_reg)
    qc.measure(anc_reg, class_reg)

    qc.barrier()

def fqc_correct_errors(qc, log_q, stab_reg, class_reg):
    def apply_correction(qc, correction, qubit):
        if correction == "X":
            qc.x(qubit)
        elif correction == "Z":
            qc.z(qubit)
        elif correction == "Y":
            qc.y(qubit)

    corrections = {
        1:  ("X", stab_reg[0]), 10: ("Z", stab_reg[0]), 11: ("Y", stab_reg[0]),
        8:  ("X", stab_reg[1]),  5: ("Z", stab_reg[1]), 13: ("Y", stab_reg[1]),
        12: ("X", stab_reg[2]),  2: ("Z", stab_reg[2]), 14: ("Y", stab_reg[2]),
        6:  ("X", stab_reg[3]),  9: ("Z", stab_reg[3]), 15: ("Y", stab_reg[3]),
        3:  ("X", log_q),        4: ("Z", log_q),        7: ("Y", log_q)
    }

    for value, (gate, qubit) in corrections.items():
        with qc.if_test((class_reg, value)):
            apply_correction(qc, gate, qubit)

    qc.barrier()
    
def decode_with_fqc(qc, log_q, stab_reg, out_q):
    qc.cx(stab_reg, out_q)
    qc.cx(log_q, out_q)
    czz(qc, out_q, stab_reg[0], stab_reg[3])
    qc.cx(out_q, log_q)

    qc.barrier()

def create_fqc_ghz_state(n: int) -> QuantumCircuit:
    """
    Generates an n-qubit GHZ state, encoding each qubit with the five-qubit code.
    n must be between 2 and 10 (inclusive).
    Returns a QuantumCircuit that performs this operation.
    """
    if not (2 <= n <= 10):
        raise ValueError("n must be between 2 and 10")

    # Each logical qubit requires 1 logical, 4 stabilizer, 1 output, 4 ancilla, 4 classical for syndrome, 1 classical for output
    log_qubits = QuantumRegister(n, 'log_qubit')
    stab_regs = [QuantumRegister(4, f'stab_{i}') for i in range(n)]
    out_regs = [QuantumRegister(1, f'out_{i}') for i in range(n)]
    anc_regs = [QuantumRegister(4, f'anc_{i}') for i in range(n)]
    class_regs = [ClassicalRegister(4, f'measure_err_{i}') for i in range(n)]
    out_classical = ClassicalRegister(n, 'measured_output')

    # Flatten all registers for circuit construction
    qregs = []
    for i in range(n):
        qregs.extend([anc_regs[i], stab_regs[i], QuantumRegister(1, f'log_single_{i}'), out_regs[i]])
    # But we want to use the main log_qubits register for our logical GHZ
    qc = QuantumCircuit(
        *[reg for anc in anc_regs for reg in anc],
        *[reg for stab in stab_regs for reg in stab],
        *log_qubits,
        *[reg for out in out_regs for reg in out],
        *[reg for cl in class_regs for reg in cl],
        out_classical,
        name=f"{n}-qubit GHZ Encoded with Five Qubit Code"
    )

    # Initialize ancilla, output, stabilizers to |0>
    for i in range(n):
        qc.initialize(0, [q for q in anc_regs[i]])
        qc.initialize(0, [q for q in stab_regs[i]])
        qc.initialize(0, out_regs[i])
    
    qc.barrier()

    # Prepare logical GHZ state across log_qubits
    # |0...0> + |1...1>
    qc.h(log_qubits[0])
    for i in range(1, n):
        qc.cx(log_qubits[0], log_qubits[i])
    qc.barrier()
    
    # For each logical qubit, encode with the five-qubit code
    for i in range(n):
        encode_with_fqc(qc, log_qubits[i], stab_regs[i])

    # For each logical qubit, measure syndrome and correct
    for i in range(n):
        fqc_measure_syndrome(qc, log_qubits[i], stab_regs[i], anc_regs[i], class_regs[i])
        fqc_correct_errors(qc, log_qubits[i], stab_regs[i], class_regs[i])
    
    # For each logical qubit, decode into output qubit and measure
    for i in range(n):
        decode_with_fqc(qc, log_qubits[i], stab_regs[i], out_regs[i][0])
        qc.measure(log_qubits[i], out_classical[i])
    
    return qc


def create_fqc_one_qubit() -> QuantumCircuit:
    q1 = QuantumRegister(1, 'log_qubit')
    s1 = QuantumRegister(4, 'stabilizers')
    o1 = QuantumRegister(1, 'output')
    a1 = QuantumRegister(4, 'ancilla')
    c1 = ClassicalRegister(4, 'measured_errors')
    r = ClassicalRegister(2, 'measured_output')
    qc = QuantumCircuit(a1, s1, q1, o1, c1, r, name="Single Qubit Encoded with the Five Qubit Code")

    qc.initialize(0, s1)
    qc.initialize(0, o1)
    qc.initialize(0, a1)

    qc.barrier()

    encode_with_fqc(qc, q1[0], s1)

    fqc_measure_syndrome(qc, q1[0], s1, a1, c1)

    fqc_correct_errors(qc, q1[0], s1, c1)

    decode_with_fqc(qc, q1[0], s1, o1[0])
    
    qc.measure(q1[0], r[0])

    return qcs