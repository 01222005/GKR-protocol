class Gate:
    def __init__(self, gate_type, inputs=None):
        self.gate_type = gate_type  
        self.inputs = inputs if inputs else []  
        self.value = None

    def compute(self):
        vals = [inp.compute() if isinstance(inp, Gate) else inp for inp in self.inputs]

        if self.gate_type == 'add':
            self.value = sum(vals)
        elif self.gate_type == 'mul':
            result = 1
            for v in vals:
                result *= v
            self.value = result
        return self.value



x1 = Gate('mul', inputs=[2, 3])  
x2 = Gate('mul', inputs=[4, 5])  
x3 = Gate('mul', inputs=[6, 7])   
x4 = Gate('add', inputs=[8, 9])    

a1 = Gate('add', inputs=[x1, x2])  
a2 = Gate('add', inputs=[x3, x4])  


output_gate = Gate('add', inputs=[a1, a2])

result = output_gate.compute()
print(f"Final output of the circuit: {result}")
