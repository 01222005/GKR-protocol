# 電路資料結構：Constant、Gate，以及 build_demo_circuit()

from typing import Union

class Constant:
    def __init__(self, v: int):
        self.v = v
    def compute(self, circuit):
        return self.v

class Gate:
    def __init__(self, idx: int, gate_type: str, left: Union[int, Constant], right: Union[int, Constant]):
        self.idx = idx
        self.type = gate_type
        self.left = left
        self.right = right
        self.value = None

    def compute(self, circuit):
        # left value
        if isinstance(self.left, int):
            L = circuit[self.left].compute(circuit)
        else:
            L = self.left.compute(circuit)
        # right value
        if isinstance(self.right, int):
            R = circuit[self.right].compute(circuit)
        else:
            R = self.right.compute(circuit)

        if self.type == 'add':
            self.value = L + R
        else:
            self.value = L * R
        return self.value

def build_demo_circuit():
    circuit = {}
    # Layer 2 (bottom) - constants as inputs
    circuit[0] = Gate(0, 'mul', Constant(2), Constant(3))   # 2*3
    circuit[1] = Gate(1, 'mul', Constant(4), Constant(5))   # 4*5
    circuit[2] = Gate(2, 'mul', Constant(6), Constant(7))   # 6*7
    circuit[3] = Gate(3, 'add', Constant(8), Constant(9))   # 8+9

    # Layer 1
    circuit[4] = Gate(4, 'add', 0, 1)   # g4 = g0 + g1
    circuit[5] = Gate(5, 'add', 2, 3)   # g5 = g2 + g3

    # Layer 0 (output)
    circuit[6] = Gate(6, 'add', 4, 5)   # g6 = g4 + g5

    # layers list (top:0 -> down:2)
    layers = [
        [6],       
        [4, 5],      
        [0, 1, 2, 3] 
    ]

    return circuit, layers
