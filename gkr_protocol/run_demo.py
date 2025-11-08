# run_demo.py

from circuit import build_demo_circuit
from prover import Prover
from verifier import Verifier

def run_demo():
    circuit, layers = build_demo_circuit()

    P = Prover(circuit, layers)
    V = Verifier()

    P.compute_all()

    print("=== GKR Demo ===\n")

    # 驗證每一層 gate（除了最後一層 input）
    for layer_pos, layer in enumerate(layers[:-1]):
        print(f"Verifying layer {layer_pos}, gates={layer}\n")

        for g in layer:
            P.get_gate_value(g)

            ok, log = V.verify_gate(P, layer_pos, g)

            for line in log:
                print(line)

            print()

            if not ok:
                print(f"Verification FAILED at gate {g}")
                return

    print("✅ All gates verified successfully!")

if __name__ == "__main__":
    run_demo()
