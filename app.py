from flask import Flask, render_template, Response, jsonify, request
from trigger import assistant
import json
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_assistant():
    assistant.start()
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def stop_assistant():
    assistant.stop()
    return jsonify({"status": "stopped"})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    # Process the text question through the same pipeline
    try:
        assistant._process_question(question)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-tts', methods=['POST'])
def test_tts():
    """Test endpoint that returns a dummy response to test TTS"""
    data = request.json
    question = data.get('question', '')
    
    # Create a dummy response without calling n8n
    test_response = f"I heard you ask: {question}. This is a test response to demonstrate the OpenAI text-to-speech capability. The voice sounds very natural and human-like, doesn't it?"
    
    assistant.log(f"Test Response: {test_response}", "success")
    assistant.event_queue.put({"type": "response", "text": test_response})
    assistant.speak(test_response)
    
    return jsonify({"status": "success"})

@app.route('/events')
def events():
    def generate():
        # Send initial connection confirmation
        yield "data: " + json.dumps({"type": "connected"}) + "\n\n"
        
        while True:
            try:
                # Get event from queue with timeout to allow checking connection status
                event = assistant.event_queue.get(timeout=1)
                yield f"data: {json.dumps(event)}\n\n"
            except:
                # Send keepalive to keep connection open
                yield ": keepalive\n\n"
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)
