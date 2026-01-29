import random

# ----------------------------
# Gate 開關結構
# ----------------------------
class Gate:
    def __init__(self, idx, gate_type, left, right):
        self.idx = idx
        self.type = gate_type  
        self.left = left       
        self.right = right
        self.value = None

    def compute(self, circuit):
        L = circuit[self.left].compute(circuit) if isinstance(self.left, int) else self.left
        R = circuit[self.right].compute(circuit) if isinstance(self.right, int) else self.right

        if self.type == "add":
            self.value = L + R
        else:
            self.value = L * R

        return self.value


# ----------------------------
# 定義你的電路
# ----------------------------
def build_circuit():
    circuit = {}

    circuit[0] = Gate(0, "mul", 2, 3)  # 2 * 3
    circuit[1] = Gate(1, "mul", 4, 5)  # 4 * 5
    circuit[2] = Gate(2, "mul", 6, 7)  # 6 * 7
    circuit[3] = Gate(3, "add", 8, 9)  # 8 + 9

    circuit[4] = Gate(4, "add", 0, 1)
    circuit[5] = Gate(5, "add", 2, 3)

    circuit[6] = Gate(6, "add", 4, 5)

    return circuit


# ----------------------------
# 單層 Sumcheck
# ----------------------------
class Prover:
    def __init__(self, circuit):
        self.circuit = circuit

    def get_gate_value(self, i):
        return self.circuit[i].value

    def layer_sumcheck(self, g):
        gate = self.circuit[g]
        L = gate.left
        R = gate.right

        L_val = self.circuit[L].value if isinstance(L, int) else L
        R_val = self.circuit[R].value if isinstance(R, int) else R

        if gate.type == "add":
            return L_val + R_val
        else:
            return L_val * R_val


class Verifier:
    def __init__(self, circuit):
        self.circuit = circuit

    def verify_gate(self, prover, g):
        claimed = prover.get_gate_value(g)
        computed = prover.layer_sumcheck(g)

        print(f"[Verifier] Checking gate {g}: Prover says {claimed}, Sumcheck gives {computed}")
        return claimed == computed


# ----------------------------
#  GKR驗證流程
# ----------------------------
def run_gkr():
    circuit = build_circuit()

    for idx in circuit:
        circuit[idx].compute(circuit)

    P = Prover(circuit)
    V = Verifier(circuit)

    layers = [
        [6],      
        [4, 5],   
        [0, 1, 2, 3] 
    ]

    print("\n=== GKR Verification Start ===\n")

    for layer in layers:
        print(f"--- Verifying layer: {layer} ---")

        for g in layer:
            ok = V.verify_gate(P, g)
            if not ok:
                print("Verification failed")
                return

    print("\n GKR Verification PASSED!")


run_gkr()
