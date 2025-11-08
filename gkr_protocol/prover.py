# prover.py

from math import ceil, log2
from sumcheck import SumcheckProver

class Prover:
    def __init__(self, circuit, layers):
        self.circuit = circuit
        self.layers = layers
        self.log = []

    def compute_all(self):
        for idx in sorted(self.circuit.keys()):
            self.circuit[idx].compute(self.circuit)

    def get_gate_value(self, g):
        val = self.circuit[g].value
        self.log.append(f"Prover: V({g}) = {val}")
        return val

    def build_relation_table(self, layer_pos, g):
        prev_layer = self.layers[layer_pos + 1]
        N = len(prev_layer)
        m = max(1, ceil(log2(N)))
        size = 1 << m

        # gate info
        gate = self.circuit[g]

        # mapping
        idx_map = {prev_layer[i]: i for i in range(N)}

        # 找父節點（如有）
        parent = None
        if isinstance(gate.left, int) and isinstance(gate.right, int):
            if gate.left in idx_map and gate.right in idx_map:
                parent = (idx_map[gate.left], idx_map[gate.right])

        table = [0] * (size * size)

        for a in range(size):
            for b in range(size):

                if parent is not None and a == parent[0] and b == parent[1]:
                    Va = self.circuit[prev_layer[a]].value
                    Vb = self.circuit[prev_layer[b]].value

                    if gate.type == "add":
                        table[a * size + b] = Va + Vb
                    else:
                        table[a * size + b] = Va * Vb

                else:
                    table[a * size + b] = 0

        return SumcheckProver(table, m)
