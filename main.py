# app.py
from flask import Flask, render_template, jsonify
import subprocess
import threading

app = Flask(__name__)

# Global variable to track if equalizer is running
is_running = False
process = None

def run_equalizer():
    global process
    process = subprocess.Popen(['python', 'first.py'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def execute():
    global is_running
    if not is_running:
        is_running = True
        threading.Thread(target=run_equalizer).start()
        return jsonify({'status': 'success', 'message': 'Equalizer started!'})
    return jsonify({'status': 'error', 'message': 'Equalizer is already running!'})

@app.route('/stop', methods=['POST'])
def stop():
    global is_running, process
    if is_running and process:
        process.terminate()
        is_running = False
        return jsonify({'status': 'success', 'message': 'Equalizer stopped!'})
    return jsonify({'status': 'error', 'message': 'No running equalizer!'})

if __name__ == '__main__':
    app.run(debug=True, threaded=True)