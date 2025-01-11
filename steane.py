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
    qc.h(anc_reg[:6])

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
    """
    Implements error correction based on stabilizer states using `if_else`.
    
    Parameters:
        qc (QuantumCircuit): The quantum circuit.
        log_reg (QuantumRegister): Logical qubit register (1 qubit).
        stab_reg (QuantumRegister): Stabilizer register (6 qubits).
        class_reg (ClassicalRegister): Classical register (6 bits).
    """
    # Define correction gates using a mapping of the table values.
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


def create_steane_bell_state() -> QuantumCircuit:
    q1 = QuantumRegister(1, 'log_qubit_1')
    s1 = QuantumRegister(6, 'stabilizer_1')
    o1 = QuantumRegister(1, 'output_1')
    a1 = QuantumRegister(6, 'ancilla_1')
    c1 = ClassicalRegister(6, 'measured_errors_1')
    q2 = QuantumRegister(1, 'log_qubit_2')
    s2 = QuantumRegister(6, 'stabilizer_2')
    o2 = QuantumRegister(1, 'output_2')
    a2 = QuantumRegister(6, 'ancilla_2')
    c2 = ClassicalRegister(6, 'measured_errors_2')
    r = ClassicalRegister(2, 'measured_output')
    qc = QuantumCircuit(a1, s1, q1, a2, s2, q2, o1, o2, c1, c2, r, name="Bell State Encoded with Steane's Code")
    
    #qc.reset(range(qc.num_qubits))
    
    qc.initialize(0, s1)
    qc.initialize(0, o1)
    qc.initialize(0, a1)
    qc.initialize(0, s2)
    qc.initialize(0, o2)
    qc.initialize(0, a2)
    
    qc.barrier()
    
    qc.h(q1[0])
    qc.cx(q1[0], q2[0])
    
    qc.barrier()
    
    #Encode Qubits
    encode_with_steane(qc, q1[0], s1)
    encode_with_steane(qc, q2[0], s2)
    
    #Measure Syndrome
    steane_measure_syndrome(qc, q1[0], s1, a1, c1)
    steane_measure_syndrome(qc, q2[0], s2, a2, c2)
    
    #Correct Errors
    steane_correct_errors(qc, q1[0], s1, c1)
    steane_correct_errors(qc, q2[0], s2, c2)
    
    #Decode Qubits
    decode_with_steane(qc, q1[0], s1, o1[0])
    decode_with_steane(qc, q2[0], s2, o2[0])
    
    qc.barrier()
    
    #Measure Output
    qc.measure(o1[0], r[0])
    qc.measure(o2[0], r[1])
    
    return qc