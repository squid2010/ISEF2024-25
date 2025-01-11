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
    # Define correction gates using a mapping of the table values.
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


def create_fqc_bell_state() -> QuantumCircuit:
    q1 = QuantumRegister(1, 'log_qubit_1')
    s1 = QuantumRegister(4, 'stabilizer_1')
    o1 = QuantumRegister(1, 'output_1')
    a1 = QuantumRegister(4, 'anicilla_1')
    c1 = ClassicalRegister(4, 'measured_errors_1')
    q2 = QuantumRegister(1, 'log_qubit_2')
    s2 = QuantumRegister(4, 'stabilizer_2')
    o2 = QuantumRegister(1, 'output_2')
    a2 = QuantumRegister(4, 'anicilla_2')
    c2 = ClassicalRegister(4, 'measured_errors_2')
    r = ClassicalRegister(2, 'measured_output')
    qc = QuantumCircuit(a1, s1, q1, o1, a2, s2, q2, o2, c1, c2, r, name="Bell State Encoded with the Five Qubit Code")
    
    qc.initialize(0, s1)
    qc.initialize(0, o1)
    qc.initialize(0, s2)
    qc.initialize(0, o2)
    
    qc.barrier()
    
    #Set up Bell State
    qc.h(q1[0])
    qc.cx(q1[0], q2[0])
    
    qc.barrier()
    
    #Encode Qubits
    encode_with_fqc(qc, q1[0], s1)
    encode_with_fqc(qc, q2[0], s2)
    
    #Measure Syndrome
    fqc_measure_syndrome(qc, q1[0], s1, a1, c1)
    fqc_measure_syndrome(qc, q2[0], s2, a2, c2)
    
    #Correct Errors
    fqc_correct_errors(qc, q1[0], s1, c1)
    fqc_correct_errors(qc, q2[0], s2, c2)
    
    #Decode Qubits
    decode_with_fqc(qc, q1[0], s1, o1[0])
    decode_with_fqc(qc, q2[0], s2, o2[0])
    
    qc.barrier()
    
    #Measure
    qc.measure(o1[0], r[0])
    qc.measure(o2[0], r[1])
    
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

    return qc