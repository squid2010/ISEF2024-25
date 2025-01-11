def cxx(qc, c, q1, q2):
    qc.cx(c, q1)
    qc.cx(c, q2)

def cxxx(qc, c, q1, q2, q3):
    qc.cx(c, q1)
    qc.cx(c, q2)
    qc.cx(c, q3)

def cxxxx(qc, c, q1, q2, q3, q4): 
    qc.cx(c,q1)
    qc.cx(c,q2)
    qc.cx(c,q3)
    qc.cx(c,q4)

def cxxxxxx(qc, c, q1, q2, q3, q4, q5, q6):
    qc.cx(c, q1)
    qc.cx(c, q2)
    qc.cx(c, q3)
    qc.cx(c, q4)
    qc.cx(c, q5)
    qc.cx(c, q6)

def czz(qc, c, q1, q2):
    qc.cz(c, q1)
    qc.cz(c, q2)

def czzz(qc, c, q1, q2, q3):
    qc.cz(c, q1)
    qc.cz(c, q2)
    qc.cz(c, q3)

def czzzz(qc, c, q1, q2, q3, q4): 
    qc.cz(c,q1)
    qc.cz(c,q2)
    qc.cz(c,q3)
    qc.cz(c,q4)

def cxxzz(qc, c, q1, q2, q3, q4):
    qc.cx(c, q1)
    qc.cx(c, q2)
    qc.cz(c, q3)
    qc.cz(c, q4)