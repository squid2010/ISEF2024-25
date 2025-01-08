from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from custom_gates import cxx

def encode_with_shors(qc, log_reg, stab_reg):
    cxx(qc, log_reg[0], stab_reg[2], stab_reg[5])

    qc.h(log_reg[0])
    qc.h(stab_reg[2])
    qc.h(stab_reg[5])

    cxx(qc, log_reg[0], stab_reg[0], stab_reg[1])

    cxx(qc, stab_reg[2], stab_reg[3], stab_reg[4])

    cxx(qc, stab_reg[5], stab_reg[6], stab_reg[7])

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
    q1 = QuantumRegister(1, 'q1')
    q2 = QuantumRegister(1, 'q2')
    c = ClassicalRegister(2,'c')
    a1 = QuantumRegister(8, 'a1')
    a2 = QuantumRegister(8, 'a2')
    qc = QuantumCircuit(q1,a1,q2,a2,c)
    
    qc.initialize(0, a1)
    qc.initialize(0, a2)
    
    qc.barrier()
    
    #Bell State
    qc.h(q1[0])
    qc.cx(q1[0],q2[0])
    
    qc.barrier()
    
    #Encode
    encode_with_shors(qc, q1, a1)
    encode_with_shors(qc, q2, a2)
    
    #Decode
    decode_with_shors(qc, q1, c, a1)
    decode_with_shors(qc, q2, c, a2)
    
    #Measure
    qc.measure(q1[0], c[0])
    qc.measure(q2[0], c[1])

    return qc