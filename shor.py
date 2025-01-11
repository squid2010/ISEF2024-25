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

def create_shor_bell_state() -> QuantumCircuit:
    q1 = QuantumRegister(1, 'log_qubit_1')
    s1 = QuantumRegister(8, 'stabilizer_1')
    o1 = QuantumRegister(1, 'output_1')
    a1 = QuantumRegister(8, 'ancilla_1')
    c1 = ClassicalRegister(8, 'measured_errors_1')
    q2 = QuantumRegister(1, 'log_qubit_2')
    s2 = QuantumRegister(8, 'stabilizer_2')
    o2 = QuantumRegister(1, 'output_2')
    a2 = QuantumRegister(8, 'ancilla_2')
    c2 = ClassicalRegister(8, 'measured_errors_2')
    r = ClassicalRegister(2, 'measured_output')
    qc = QuantumCircuit(a1, s1, q1, a2, s2, q2, o1, o2, c1, c2, r, name="Bell State Encoded with Shor's Code")
        
    qc.initialize(0, s1)
    qc.initialize(0, o1)
    qc.initialize(0, a1)
    qc.initialize(0, s2)
    qc.initialize(0, o2)
    qc.initialize(0, a2)
    
    qc.barrier()
    
    #Bell State
    qc.h(q1[0])
    qc.cx(q1[0],q2[0])
    
    qc.barrier()
    
    #Encode
    encode_with_shors(qc, q1, s1)
    encode_with_shors(qc, q2, s2)

    #Measure Syndrome
    shor_measure_syndrome(qc, q1[0], s1, a1, c1)
    shor_measure_syndrome(qc, q2[0], s2, a2, c2)
    
    #Correct Errors
    shor_correct_errors(qc, q1[0], s1, c1)
    shor_correct_errors(qc, q2[0], s2, c2)
    
    #Decode
    decode_with_shors(qc, q1, c1, a1)
    decode_with_shors(qc, q2, c2, a2)
    
    #Measure
    qc.measure(q1[0], r[0])
    qc.measure(q2[0], r[1])

    return qc