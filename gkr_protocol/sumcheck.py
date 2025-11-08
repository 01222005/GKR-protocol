import random
import math

random.seed(12345)

class SumcheckProver:
    def __init__(self, table, m):
        self.table = table
        self.m = m
        self.total_vars = 2 * m

    def full_sum(self):
        return sum(self.table)

    def get_gi_polynomial(self, i, prefix):
        # 第 i 個變數，剩下 total_vars - i 個變數
        rem = self.total_vars - i

        g0 = 0
        g1 = 0

        # 列舉後面剩下的 bits
        for tail_mask in range(1 << rem):

            # 組成 vec0 = prefix + [0] + tail
            # 組成 vec1 = prefix + [1] + tail
            vec0 = prefix + [0]
            vec1 = prefix + [1]

            for j in range(rem):
                bit = (tail_mask >> j) & 1
                vec0.append(bit)
                vec1.append(bit)

            # a,b index 各是 m bits
            a0 = 0
            b0 = 0
            a1 = 0
            b1 = 0

            # 確保向量長度足夠
            if len(vec0) < 2 * self.m or len(vec1) < 2 * self.m:
                continue

            # 第一段 bits = a
            for j in range(self.m):
                if j < len(vec0):
                    a0 |= (vec0[j] << j)
                if j < len(vec1):
                    a1 |= (vec1[j] << j)

            # 第二段 bits = b
            for j in range(self.m):
                if self.m + j < len(vec0):
                    b0 |= (vec0[self.m + j] << j)
                if self.m + j < len(vec1):
                    b1 |= (vec1[self.m + j] << j)

            idx0 = a0 * (1 << self.m) + b0
            idx1 = a1 * (1 << self.m) + b1

            # 檢查索引是否在範圍內
            if idx0 < len(self.table):
                g0 += self.table[idx0]
            if idx1 < len(self.table):
                g1 += self.table[idx1]

        # g(t) = g0 + (g1 - g0) * t
        a = g0
        b = g1 - g0
        return a, b

    def evaluate_final(self, rlist):
        total = 0
        L = len(self.table)
        k = self.total_vars

        for idx in range(L):
            # bits
            bits = [(idx >> j) & 1 for j in range(k)]
            weight = 1
            for b, r in zip(bits, rlist):
                weight *= (r if b == 1 else (1 - r))
            total += self.table[idx] * weight
        return total


class SumcheckVerifier:
    def __init__(self):
        self.log = []

    def rand_field(self):
        return random.randint(0, 10)

    def run(self, prover: SumcheckProver):
        self.log.append("=== Sumcheck start ===")
        total = prover.full_sum()
        self.log.append(f"Prover claims sum = {total}")

        prev = total
        prefix = []
        k = prover.total_vars

        for i in range(1, k + 1):
            a, b = prover.get_gi_polynomial(i, prefix)
            self.log.append(f"g_{i}(t) = {a} + {b} * t")

            if a + (a + b) != prev:
                self.log.append("Consistency check FAILED")
                return False, self.log

            r = self.rand_field()
            self.log.append(f"Verifier sends r_{i} = {r}")
            prefix.append(r)

            prev = a + b * r

        F_r = prover.evaluate_final(prefix)
        self.log.append(f"Prover sends F(r) = {F_r}")
        self.log.append(f"Check {prev} == {F_r}")

        ok = (prev == F_r)
        return ok, self.log
