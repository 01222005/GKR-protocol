from flask import Flask, request, jsonify
from flask_cors import CORS
from gkr.circuit import Circuit
from gkr.prover import Prover
from gkr.verifier import Verifier

app = Flask(__name__)
CORS(app)

# 存儲當前會話狀態
session_state = {
    'circuit': None,
    'prover': None,
    'verifier': None,
    'current_step': 0
}

@app.route('/api/circuit', methods=['POST'])
def create_circuit():
    """接收電路輸入並創建電路"""
    data = request.json
    circuit = Circuit(data)
    session_state['circuit'] = circuit
    session_state['prover'] = Prover(circuit)
    session_state['verifier'] = Verifier(circuit)
    session_state['current_step'] = 0
    
    return jsonify({
        'success': True,
        'circuit_info': circuit.get_info()
    })

@app.route('/api/step/next', methods=['POST'])
def next_step():
    """執行下一步驟"""
    if not session_state['circuit']:
        return jsonify({'error': 'No circuit initialized'}), 400
    
    prover = session_state['prover']
    verifier = session_state['verifier']
    step = session_state['current_step']
    
    result = {
        'step': step,
        'prover_action': prover.execute_step(step),
        'verifier_action': verifier.execute_step(step)
    }
    
    session_state['current_step'] += 1
    return jsonify(result)

@app.route('/api/step/previous', methods=['POST'])
def previous_step():
    """返回上一步驟"""
    if session_state['current_step'] > 0:
        session_state['current_step'] -= 1
    
    return jsonify({'step': session_state['current_step']})

@app.route('/api/reset', methods=['POST'])
def reset():
    """重置會話"""
    session_state['current_step'] = 0
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
