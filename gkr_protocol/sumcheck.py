import random
import math
from typing import List

random.seed(12345)
P = 2147483647 

def mod(x: int) -> int:
    return x % P

def enum_bool_assignments(k: int):
    for i in range(1 << k):
        yield [(i >> j) & 1 for j in range(k)]

def index_to_bits(i: int, m: int) -> List[int]:
    return [(i >> j) & 1 for j in range(m)]

def multilinear_extension_from_table(table_values: List[int], x_vars: List[float]) -> float:
    k = int(math.log2(len(table_values)))
    total = 0
    for idx, val in enumerate(table_values):
        if val == 0:
            continue
        bits = index_to_bits(idx, k)
        weight = 1.0
        for b, xv in zip(bits, x_vars):
            # L_0(x) = (1 - x), L_1(x) = x
            weight *= (xv if b == 1 else (1.0 - xv))
        total += val * weight
    return total

class SumcheckProver:
    def __init__(self, table: List[int], m: int):
        self.table = table
        self.m = m
        self.total_vars = 2 * m  

    def full_sum(self) -> float:
        return float(sum(self.table))

    def get_gi_polynomial(self, i: int, prefix: List[float]) -> (float, float):
        assert len(prefix) == i - 1
        rem = self.total_vars - i  

        g0 = 0.0
        g1 = 0.0

        # Enumerate all assignments of the remaining rem boolean variables
        for tail_bits in enum_bool_assignments(rem):
            # build full vector for evaluation: length total_vars
            vec0 = list(prefix) + [0.0] + [float(b) for b in tail_bits]
            vec1 = list(prefix) + [1.0] + [float(b) for b in tail_bits]
            # Evaluate multilinear extension at vec0 and vec1
            val0 = multilinear_extension_from_table(self.table, vec0)
            val1 = multilinear_extension_from_table(self.table, vec1)
            g0 += val0
            g1 += val1

        a = g0
        b = g1 - g0
        return a, b

    def evaluate_final(self, rlist: List[float]) -> float:
        return multilinear_extension_from_table(self.table, rlist)


class SumcheckVerifier:
    def __init__(self):
        self.log = []
        random.seed(12345)

    def rand_field(self) -> float:
        return float(random.randint(0, 10))

    def run(self, prover: SumcheckProver):
        self.log = []
        self.log.append("=== Sumcheck start ===")
        S = prover.full_sum()
        self.log.append(f"Prover claims sum = {S}")

        prev = S
        prefix = [] 
        k = prover.total_vars

        for i in range(1, k + 1):
            a, b = prover.get_gi_polynomial(i, prefix)
            self.log.append(f"g_{i}(t) = {a} + {b} * t")

            # Check consistency: g(0) + g(1) == prev
            g0 = a
            g1 = a + b
            if abs((g0 + g1) - prev) > 1e-9:  # tolerance for floating errors
                self.log.append(f"Consistency check FAILED at round {i}: {g0 + g1} != {prev}")
                return False, self.log

            # Verifier picks random r (field element) and sends
            r = self.rand_field()
            self.log.append(f"Verifier sends r_{i} = {r}")
            prefix.append(r)

            # Update prev = g(r) = a + b*r
            prev = a + b * r

        # Final: ask prover for value of multilinear extension at r = prefix
        F_r = prover.evaluate_final(prefix)
        self.log.append(f"Prover sends F(r) = {F_r}")
        self.log.append(f"Verifier final check: prev = {prev} ?= F(r) = {F_r}")

        ok = abs(prev - F_r) <= 1e-9
        return ok, self.log
