from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from custom_gates import cxx, czz, cxxxxxx

def encode_with_shors(qc, log_reg, stab_reg):
    cxx(qc, log_reg[0], stab_reg[2], stab_reg[5])

    qc.h(log_reg[0])
    qc.h(stab_reg[2])
    qc.h(stab_reg[5])

    cxx(qc, log_reg[0], stab_reg[0], stab_reg[1])

    cxx(qc, stab_reg[2], stab_reg[3], stab_reg[4])

    cxx(qc, stab_reg[5], stab_reg[6], stab_reg[7])

    qc.barrier()

def shor_measure_syndrome(qc, log_q, stab_reg, anc_reg, class_reg):
    qc.h(anc_reg[:8])
    
    czz(qc, anc_reg[0], stab_reg[0], stab_reg[1])
    czz(qc, anc_reg[1], stab_reg[0], stab_reg[2])
    czz(qc, anc_reg[2], stab_reg[3], stab_reg[4])
    czz(qc, anc_reg[3], stab_reg[3], stab_reg[5])
    czz(qc, anc_reg[4], stab_reg[6], stab_reg[7])
    czz(qc, anc_reg[5], stab_reg[6], log_q)

    cxxxxxx(qc, anc_reg[6], stab_reg[0], stab_reg[1], stab_reg[2], stab_reg[3], stab_reg[4], stab_reg[5])
    cxxxxxx(qc, anc_reg[7], stab_reg[3], stab_reg[4], stab_reg[5], stab_reg[6], stab_reg[7], log_q)

    qc.h(anc_reg[:8])
    qc.measure(anc_reg, class_reg)

    qc.barrier()

def shor_correct_errors(qc, log_q, stab_reg, class_reg):
    def apply_correction(qc, correction, qubit):
        if correction == "X":
            qc.x(qubit)
        elif correction == "Z":
            qc.z(qubit)
        elif correction == "Y":
            qc.y(qubit)

    corrections = {
        1: [('Z', stab_reg[6]), ('Z', stab_reg[7]), ('Z', log_q)], 
        2: [('Z', stab_reg[3]), ('Z', stab_reg[4]), ('Z', stab_reg[5])], 
        3: [('Z', stab_reg[0]), ('Z', stab_reg[1]), ('Z', stab_reg[2])], 
        4: [('X', log_q)], 5: [('Y', log_q)],  8: [('X', stab_reg[7])], 
        9: [('Y', stab_reg[7])], 12: [('X', stab_reg[6])], 
        13: [('Y', stab_reg[6])], 16: [('X', stab_reg[5])], 
        18: [('Y', stab_reg[5])], 32: [('X', stab_reg[4])], 
        34: [('Y', stab_reg[4])], 48: [('X', stab_reg[3])], 
        50: [('Y', stab_reg[3])], 64: [('X', stab_reg[2])], 
        67: [('Y', stab_reg[2])], 128: [('X', stab_reg[1])], 
        131: [('Y', stab_reg[1])], 192: [('X', stab_reg[0])], 
        195: [('Y', stab_reg[0])]
    }

    for value, errors_list in corrections.items():
        with qc.if_test((class_reg, value)):
            for (gate, qubit) in errors_list:
                apply_correction(qc, gate, qubit)

    qc.barrier()

def decode_with_shors(qc, log_reg, class_reg, stab_reg):
    cxx(qc, log_reg[0], stab_reg[0], stab_reg[1])

    cxx(qc, stab_reg[2], stab_reg[3], stab_reg[4])

    cxx(qc, stab_reg[5], stab_reg[6], stab_reg[7])

    qc.ccx(stab_reg[1], stab_reg[0], log_reg[0])
    qc.ccx(stab_reg[4], stab_reg[3], stab_reg[2])
    qc.ccx(stab_reg[7], stab_reg[6], stab_reg[5])

    qc.h(log_reg[0])
    qc.h(stab_reg[2])
    qc.h(stab_reg[5])

    cxx(qc, log_reg[0], stab_reg[2], stab_reg[5])

    qc.ccx(stab_reg[5], stab_reg[2], log_reg[0])

    qc.barrier()

def create_shor_ghz_state(n: int) -> QuantumCircuit:
    """
    Generates an n-qubit GHZ state, encoding each qubit with the Shor code.
    n must be between 2 and 10 (inclusive).
    Returns a QuantumCircuit that performs this operation.
    """
    if not (2 <= n <= 10):
        raise ValueError("n must be between 2 and 10")

    # Each logical qubit requires: 1 logical, 8 stabilizer, 1 output, 8 ancilla, 8 classical for syndrome, 1 classical for output
    log_qubits = [QuantumRegister(1, f'log_qubit_{i}') for i in range(n)]
    stab_regs = [QuantumRegister(8, f'stab_{i}') for i in range(n)]
    out_regs = [QuantumRegister(1, f'output_{i}') for i in range(n)]
    anc_regs = [QuantumRegister(8, f'ancilla_{i}') for i in range(n)]
    class_regs = [ClassicalRegister(8, f'measured_errors_{i}') for i in range(n)]
    out_classical = ClassicalRegister(n, 'measured_output')

    # Construct the circuit with all registers (flattened)
    qc = QuantumCircuit(
        *[reg for anc in anc_regs for reg in anc],
        *[reg for stab in stab_regs for reg in stab],
        *[reg for lq in log_qubits for reg in lq],
        *[reg for out in out_regs for reg in out],
        *[reg for cl in class_regs for reg in cl],
        out_classical,
        name=f"{n}-qubit GHZ Encoded with Shor's Code"
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

    # For each logical qubit, encode with the Shor code
    for i in range(n):
        encode_with_shors(qc, log_qubits[i], stab_regs[i])

    # For each logical qubit, measure syndrome and correct
    for i in range(n):
        shor_measure_syndrome(qc, log_qubits[i][0], stab_regs[i], anc_regs[i], class_regs[i])
        shor_correct_errors(qc, log_qubits[i][0], stab_regs[i], class_regs[i])

    # For each logical qubit, decode and measure
    for i in range(n):
        decode_with_shors(qc, log_qubits[i], class_regs[i], stab_regs[i])
        qc.measure(log_qubits[i][0], out_classical[i])

    return qc


def create_shor_one_qubit() -> QuantumCircuit:
    q1 = QuantumRegister(1, 'log_qubit')
    s1 = QuantumRegister(8, 'stabilizers')
    o1 = QuantumRegister(1, 'output')
    a1 = QuantumRegister(8, 'ancilla')
    c1 = ClassicalRegister(8, 'measured_errors')
    r = ClassicalRegister(2, 'measured_output')
    qc = QuantumCircuit(a1, s1, q1, o1, c1, r, name="Single Qubit Encoded with Shor's Code")

    qc.initialize(0, s1)
    qc.initialize(0, o1)
    qc.initialize(0, a1)

    qc.barrier()

    encode_with_shors(qc, q1, s1)

    shor_measure_syndrome(qc, q1[0], s1, a1, c1)

    shor_correct_errors(qc, q1[0], s1, c1)

    decode_with_shors(qc, q1, c1, s1)
    
    qc.measure(q1[0], r[0])

    return qc