import random

P = 2147483647

# 定義多項式 f(x1, x2, x3, x4)
def f(x):
    x1, x2, x3, x4 = x
    return (3*x1 + 2*x2*x3 + 5*x4 + x1*x2) % P

# 求 sum_{x in {0,1}^n} f(x)
def compute_full_sum(n):
    total = 0
    for i in range(2**n):
        bits = [(i >> j) & 1 for j in range(n)]
        total += f(bits)
    return total % P

# --- Prover 物件 ---
class Prover:
    def __init__(self, n):
        self.n = n
        self.messages = []  # 存給 verifier 的資料

    def compute_g_i(self, fixed_vars, i):
        """依目前固定的變數，生成 g_i(t)"""
        coeff0 = 0
        coeff1 = 0
        for b in [0, 1]:
            total = 0
            for rest in range(2 ** (self.n - i)):
                xs = fixed_vars + [b] + [(rest >> j) & 1 for j in range(self.n - i)]
                total += f(xs)
            if b == 0:
                coeff0 = total % P
            else:
                coeff1 = (total - coeff0) % P
        return coeff0, coeff1

    def send_message(self, msg):
        self.messages.append(f"Prover → Verifier: {msg}")
        return msg

# --- Verifier 物件 ---
class Verifier:
    def __init__(self, n, claimed_sum):
        self.n = n
        self.expected = claimed_sum
        self.messages = []  # 存給 prover 的資料

    def send_random_challenge(self):
        r = random.randint(1, P - 1)
        self.messages.append(f"Verifier → Prover: random r = {r}")
        return r

    def verify_sum(self, g0, g1):
        ok = (g0 + (g0 + g1)) % P == self.expected % P
        return ok



def sumcheck_demo():
    n = 4
    prover = Prover(n)
    claimed_sum = compute_full_sum(n)
    verifier = Verifier(n, claimed_sum)

    print(f"=== Sum-Check Protocol (n={n}) ===")
    print(f"Claimed total sum S = {claimed_sum}\n")

    fixed_vars = []
    for i in range(1, n + 1):
        g0, coeff1 = prover.compute_g_i(fixed_vars, i)
        prover.send_message(f"g_{i}(t) = {g0} + {coeff1} * t  (mod P)")
        verifier_msg = f"Verifier checks: g_{i}(0)+g_{i}(1) ?= expected {verifier.expected}"
        prover.messages.append(verifier_msg)

        if (g0 + (g0 + coeff1)) % P != verifier.expected % P:
            print(f"Verifier check FAILED at round {i}")
            return

        r_i = verifier.send_random_challenge()
        prover.send_message(f"Received r_{i} = {r_i}")
        fixed_vars.append(r_i)
        verifier.expected = (g0 + coeff1 * r_i) % P

    final_eval = f(fixed_vars)
    prover.send_message(f"F(r) = {final_eval}")
    verifier.messages.append(f"Verifier final check: expected {verifier.expected}, got {final_eval}")

    if final_eval == verifier.expected:
        print("Verification PASSED\n")
    else:
        print("Verification FAILED\n")

    print("=== Interaction Log ===")
    for m in prover.messages + verifier.messages:
        print(m)

if __name__ == "__main__":
    sumcheck_demo()
