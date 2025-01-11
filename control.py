from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
def create_bell_state() -> QuantumCircuit:
    q = QuantumRegister(2, 'q')
    c = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(q,c, name="Bell State Unencoded")
    
    #Bell State
    qc.h(q[0])
    qc.cx(q[0],q[1])
    
    #Measure
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])
    
    return qc