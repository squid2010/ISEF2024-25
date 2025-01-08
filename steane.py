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
    # Define correction gates using a mapping of the table values.
    def apply_correction(circuit, correction, qubit):
        if correction == "X":
            circuit.x(qubit)
        elif correction == "Z":
            circuit.z(qubit)
        elif correction == "Y":
            circuit.y(qubit)
        elif correction == "I":
            circuit.i(qubit) #does nothing, just to be there

    corrections = { # All of them are the Y errors, as the first half of the number would be the Z error, and the second, the X
    36: stab_reg[0],
    18: stab_reg[1],
    9:  stab_reg[2],
    54: stab_reg[3],
    45: stab_reg[4],
    63: stab_reg[5],
    27: log_q
    }

    # Iterate through all correction cases from the table.
    for decimal_value, qubit in corrections.items():
        # Prepare the classical condition for the current value.
        one_vals = []
        condition = [int(x) for x in format(decimal_value, '06b')]
        control_ops = []
        for i, value in enumerate(condition):
            if value==1:
                one_vals.append(i-len(one_vals))
            control_ops.append(qc.if_test((class_reg[i], value)))

        for i in range(len(one_vals)):
            if_test = control_ops.pop(one_vals[i])
            control_ops.append(if_test)

        
        one_vals = [] #clear the one_vals, as they are no longer correct
        
        for i in range(len(control_ops)): 
            if control_ops[i].condition[1]==1:
                one_vals.append(i)

        # Split the one_vals into Z and X checks for the Y condition.
        z_checks = one_vals[:len(one_vals) // 2]  # First half corresponds to Z checks.
        x_checks = one_vals[len(one_vals) // 2 : len(one_vals)]  # Second half corresponds to X checks.
        
        
        # Apply the correction for the matched condition.
        if z_checks[0] != 0:
            with control_ops[0]:
                with control_ops[1]:
                    if z_checks[0] != 2:
                        with control_ops[2]:
                            with control_ops[3]:
                                if z_checks[0] != 4: #if we reach this point, z_checks should always be 4, this is just for safety
                                    with control_ops[4]:
                                        with control_ops[5]:
                                            apply_correction(qc, "I", qubit)

                                else: #2 bits need to be one
                                    with control_ops[z_checks[0]] as else1:
                                        with control_ops[x_checks[0]] as else2:
                                            apply_correction(qc, "Y", qubit)
                                        with else2:
                                            apply_correction(qc, "Z", qubit)
                                    with else1:
                                        with control_ops[x_checks[0]]:
                                            apply_correction(qc, "X", qubit)
                                        
                    else: #4 bits need to be one
                        with control_ops[z_checks[0]] as else1:
                            with control_ops[z_checks[1]]:
                                with control_ops[x_checks[0]] as else2:
                                    with control_ops[x_checks[1]]:
                                        apply_correction(qc, "Y", qubit)
                                with else2:
                                    apply_correction(qc, "Z", qubit)    
                        with else1:
                            with control_ops[x_checks[0]]:
                                 with control_ops[x_checks[1]]:
                                    apply_correction(qc, "X", qubit)
                                     
        else: #All 6 bits need to be one
            with control_ops[z_checks[0]] as else1:
                with control_ops[z_checks[1]]:
                    with control_ops[z_checks[2]]:
                        with control_ops[x_checks[0]] as else2:
                            with control_ops[x_checks[1]]:
                                with control_ops[x_checks[2]]:
                                    apply_correction(qc, "Y", qubit)
                        with else2:
                            apply_correction(qc, "Z", qubit)
            with else1:
                with control_ops[x_checks[0]]:
                    with control_ops[x_checks[1]]:
                        with control_ops[x_checks[2]]:
                            apply_correction(qc, "X", qubit)


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
    qc = QuantumCircuit(a1, s1, q1, a2, s2, q2, o1, o2, c1, c2, r)
    
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