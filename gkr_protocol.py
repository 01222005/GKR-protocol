import random
import math
from typing import List, Tuple, Callable

P = 2147483647  
random.seed(0xC0FFEE)

def mod(x: int) -> int:
    return x % P

# -------------------------
# Basic circuit objects
# -------------------------
class Constant:
    def __init__(self, v: int):
        self.v = v
    def compute(self, circuit):
        return mod(self.v)

class Gate:
    def __init__(self, idx: int, gate_type: str, left, right):
        """
        left/right: either Constant instance or int (index of gate in circuit dict)
        gate_type: 'add' or 'mul'
        """
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
            self.value = mod(L + R)
        else:
            self.value = mod(L * R)
        return self.value

# -------------------------
# Helper: enumerate boolean assignments of length k
# -------------------------
def enum_bool_assignments(k: int):
    for i in range(1 << k):
        yield [(i >> j) & 1 for j in range(k)]

def index_to_bits(i: int, m: int) -> List[int]:
    return [(i >> j) & 1 for j in range(m)]

def indicator_multilinear(h_bits: List[int], x_vars: List[int]) -> int:
    prod = 1
    for hb, xv in zip(h_bits, x_vars):
        if hb == 1:
            prod = mod(prod * xv)         # L_1(x) = x
        else:
            prod = mod(prod * mod(1 - xv))# L_0(x) = 1 - x
    return prod

# Multilinear extension evaluation helper for boolean-function defined on {0,1}^k
def multilinear_extension_from_table(table_values: List[int], x_vars: List[int]) -> int:
    # table_values indexed by integer (0..2^k-1)
    k = int(math.log2(len(table_values)))
    total = 0
    for i, val in enumerate(table_values):
        if val == 0:
            continue
        h_bits = index_to_bits(i, k)
        weight = 1
        for hb, xv in zip(h_bits, x_vars):
            weight = mod(weight * (xv if hb == 1 else mod(1 - xv)))
        total = mod(total + mod(val * weight))
    return total

# -------------------------
# Build the specific circuit (from your diagram)
# Layer numbering we use:
#  layer2 (bottom inputs) -> indices 0,1,2,3
#  layer1 -> indices 4,5
#  layer0 -> index 6 (output)
# -------------------------
def build_demo_circuit():
    circuit = {}
    circuit[0] = Gate(0, 'mul', Constant(2), Constant(3)) 
    circuit[1] = Gate(1, 'mul', Constant(4), Constant(5))  
    circuit[2] = Gate(2, 'mul', Constant(6), Constant(7))  
    circuit[3] = Gate(3, 'add', Constant(8), Constant(9)) 

    circuit[4] = Gate(4, 'add', 0, 1)   
    circuit[5] = Gate(5, 'add', 2, 3)   

    circuit[6] = Gate(6, 'add', 4, 5)

    return circuit

# -------------------------
# Prover: knows the circuit and all gate values
# Provides values and the needed polynomial sums
# -------------------------
class Prover:
    def __init__(self, circuit, layers):
        self.circuit = circuit
        self.layers = layers
        self.log = []  # messages prover -> verifier

    def compute_all(self):
        for idx in sorted(self.circuit.keys()):
            self.circuit[idx].compute(self.circuit)

    def get_gate_value(self, idx):
        val = self.circuit[idx].value
        self.log.append(f"Prover -> Verifier: gate_value V({idx}) = {val}")
        return val

    # For a chosen layer i and target gate g (in layer i), define the multivariate function
    # F(a_bits, b_bits) = f_i(a,b,g) where a,b are indices in previous layer (expressed by bits).
    # We will build a table of size 2^m * 2^m (flattened) of integers (field elements).
    def build_layer_relation_table(self, layer_idx: int, g: int) -> Tuple[int, List[int], int]:
        prev_layer = self.layers[layer_idx + 1]  # layers going top->bottom in our run
        N_prev = len(prev_layer)
        m = max(1, math.ceil(math.log2(N_prev)))  # bit-length
        size = 1 << m

        # map prev_layer indices to 0..N_prev-1 positions
        idx_map = {gate_idx: pos for pos, gate_idx in enumerate(prev_layer)}

        # determine parents of g
        gate = self.circuit[g]
        left = gate.left
        right = gate.right
        # only include parents if they are ints and in prev_layer
        parent_pair = None
        if isinstance(left, int) and isinstance(right, int) and left in idx_map and right in idx_map:
            parent_pair = (idx_map[left], idx_map[right])

        # build flattened table
        table = [0] * (size * size)  # for all a in [0,2^m), b in [0,2^m)
        for a in range(size):
            for b in range(size):
                val = 0
                if parent_pair is not None and a == parent_pair[0] and b == parent_pair[1]:
                    # actual contribution
                    V_a = self.circuit[prev_layer[a]].value
                    V_b = self.circuit[prev_layer[b]].value
                    if gate.type == 'add':
                        val = mod(V_a + V_b)
                    else:
                        val = mod(V_a * V_b)
                else:
                    val = 0
                table[a * size + b] = val
        return m, table, size

    # Build function f(a_bits, b_bits) evaluation on real boolean inputs (0/1)
    # For sumcheck we need to enumerate all booleans anyway.
    # We'll expose a helper to compute full sum for a chosen g on layer_idx.
    def compute_full_sum_layer(self, layer_idx: int, g: int) -> int:
        m, table, size = self.build_layer_relation_table(layer_idx, g)
        total = 0
        for val in table:
            total = mod(total + val)
        return total

    # For sumcheck: given prefix assignment for some variables, compute g_i(t) coefficients
    # We'll flatten a and b bits into a vector of length 2m (order: a0..a_{m-1}, b0..b_{m-1})
    # At step i we handle variable at position var_idx (0-based)
    def compute_univariate_coeffs(self, layer_idx: int, g: int, prefix: List[int], var_idx: int) -> Tuple[int,int]:
        # prefix length == var_idx
        m, table, size = self.build_layer_relation_table(layer_idx, g)
        total_vars = 2 * m
        assert len(prefix) == var_idx
        # remaining variables count = total_vars - var_idx - 1 (we will set current var t, and sum over rest)
        s0 = 0
        s1 = 0
        # enumerate over all assignments of the remaining bits after var_idx+1
        rem = total_vars - (var_idx + 1)
        for tail in enum_bool_assignments(rem):
            # build full boolean vector for a_bits + b_bits
            full_bits0 = prefix + [0] + tail
            full_bits1 = prefix + [1] + tail
            # extract index a and b from first m and last m bits
            def bits_to_index(bits_list):
                # bits_list length == 2m
                a_bits = bits_list[:m]
                b_bits = bits_list[m:]
                a = 0
                b = 0
                for j, bit in enumerate(a_bits):
                    if bit:
                        a |= (1 << j)
                for j, bit in enumerate(b_bits):
                    if bit:
                        b |= (1 << j)
                return a, b
            a0, b0 = bits_to_index(full_bits0)
            a1, b1 = bits_to_index(full_bits1)
            val0 = table[a0 * size + b0]
            val1 = table[a1 * size + b1]
            s0 = mod(s0 + val0)
            s1 = mod(s1 + val1)
        a = s0
        b = mod(s1 - s0)
        return a, b

    # multilinear extension evaluation for the flattened 2m-variable function:
    def multilinear_extension_layer(self, layer_idx: int, g: int, r_vars: List[int]) -> int:
        m, table, size = self.build_layer_relation_table(layer_idx, g)
        # table indexed by a*size + b of length size*size = 2^(2m)
        return multilinear_extension_from_table(table, r_vars)

# -------------------------
# Sumcheck Protocol implementation (general boolean hypercube)
# This is a simplified interactive sumcheck: prover provides gi coefficients by evaluating
# sums at t=0 and t=1 for each round (we compute them from the table).
# -------------------------
class SumcheckVerifier:
    def __init__(self):
        self.log = []  # verifier -> prover messages
        random.seed(0xC0FFEE)

    def rand_field(self):
        return random.randrange(0, P)

    def run_sumcheck(self, prover: Prover, layer_idx: int, g: int) -> bool:
        # Step 0: Prover sends claimed sum S
        S = prover.compute_full_sum_layer(layer_idx, g)
        prover.log.append(f"Prover -> Verifier: claimed sum S (layer {layer_idx}, g={g}) = {S}")

        prev = S
        prefix = []
        # total vars = 2m
        m, _, size = prover.build_layer_relation_table(layer_idx, g)
        total_vars = 2 * m

        for var_idx in range(total_vars):
            # Prover computes univariate coeffs for current var
            a, b = prover.compute_univariate_coeffs(layer_idx, g, prefix, var_idx)
            prover.log.append(f"Prover -> Verifier: g_{var_idx+1}(t) = {a} + {b} * t")
            # Verifier checks g(0)+g(1) == prev
            g0 = a
            g1 = mod(a + b)
            scheck = mod(g0 + g1)
            self.log.append(f"Verifier checks: g_{var_idx+1}(0)+g_{var_idx+1}(1) = {g0}+{g1} = {scheck} (expect {prev})")
            if scheck != prev:
                self.log.append(f"Verification FAIL at var {var_idx+1}")
                return False
            # Verifier picks random r and sends
            r = self.rand_field()
            self.log.append(f"Verifier -> Prover: r_{var_idx+1} = {r}")
            # update prev = g(r) = a + b*r
            prev = mod(a + b * r)
            prefix = prefix + [r]
        # After rounds, Prover sends multilinear extension F(r)
        F_r = prover.multilinear_extension_layer(layer_idx, g, prefix)
        prover.log.append(f"Prover -> Verifier: F(r) = {F_r}")
        self.log.append(f"Verifier final check: prev = {prev} ?= F(r) = {F_r}")
        return prev == F_r

# -------------------------
# Orchestration: GKR run over layers
# -------------------------
def run_gkr_demo():
    # build circuit and layers list (top-level -> bottom-level)
    circuit = build_demo_circuit()
    # compute gate values
    for idx in sorted(circuit.keys()):
        circuit[idx].compute(circuit)

    # define layers as lists of gate indices from top (output layer) to bottom (input layer)
    layers = [
        [6],       
        [4,5],    
        [0,1,2,3]   
    ]

    # create prover and verifier
    P = Prover(circuit, layers)
    V = SumcheckVerifier()

    # Prover computes (fills values) — already done above but call for clarity
    P.compute_all()

    interaction_log = []  # chronological combined log
    ok = True

    print("=== Running GKR-style verification (demo) ===\n")
    # For each layer from top to just above input layer, verify each gate using Sumcheck
    for layer_i, layer in enumerate(layers[:-1]):  # skip last because it has no previous layer below
        print(f"Verifying layer {layer_i} gates: {layer}")
        for g in layer:
            # Verifier randomly picks gate g (here we check all for demo)
            # Run sumcheck for this g
            passed = V.run_sumcheck(P, layer_i, g)
            
            # merge logs
            interaction_log.extend(P.log)
            interaction_log.extend(V.log)
            P.log = []
            V.log = []
            if not passed:
                print(f"Verification failed for gate {g} in layer {layer_i}")
                ok = False
                break
        if not ok:
            break

    print("\n=== Interaction Transcript ===")
    for line in interaction_log:
        print(line)

    print("\n=== Summary ===")
    if ok:
        print("All Sumcheck checks passed. (GKR-demo verification PASSED)")
    else:
        print("Some checks failed.")

# -------------------------
# Run demo when executed
# -------------------------
if __name__ == "__main__":
    run_gkr_demo()
