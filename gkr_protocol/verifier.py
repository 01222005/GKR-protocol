# verifier.py

from sumcheck import SumcheckVerifier

class Verifier:
    def __init__(self):
        self.SC = SumcheckVerifier()

    def verify_gate(self, prover, layer_pos, g):
        sc_prover = prover.build_relation_table(layer_pos, g)
        ok, log = self.SC.run(sc_prover)
        return ok, log
