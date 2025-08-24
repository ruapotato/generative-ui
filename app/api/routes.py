# app/api/routes.py
from flask import Blueprint, request, Response, current_app, jsonify
import json
from ..ollama_client import get_ui_update, get_available_models 
import time
import queue

api = Blueprint('api', __name__)

@api.route('/models', methods=['GET'])
def list_models():
    """
    Returns a list of available Ollama models.
    """
    models = get_available_models()
    return jsonify(models)

@api.route('/stream')
def stream():
    """
    The Server-Sent Events (SSE) endpoint.
    """
    sse_manager = current_app.sse_manager

    def event_stream():
        while True:
            try:
                msg = sse_manager.message_queue.get(timeout=0.1)
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
            time.sleep(0.1)

    return Response(event_stream(), mimetype='text/event-stream')

@api.route('/prompt', methods=['POST'])
def handle_prompt():
    """
    Receives the prompt, UI state, and selected model from the frontend.
    """
    data = request.get_json()
    if not data or 'prompt' not in data or 'uiState' not in data or 'model' not in data:
        return jsonify({"error": "Invalid request"}), 400

    prompt = data['prompt']
    ui_state = data['uiState']
    model_name = data['model']

    ui_update_command = get_ui_update(prompt, ui_state, model_name)

    # --- **DEBUGGING LINE** ---
    # Print the command that is about to be sent to the frontend
    print(f"--- COMMAND TO PUBLISH ---")
    print(ui_update_command)
    print("--------------------------")
    # --- **END DEBUGGING** ---

    current_app.sse_manager.publish(ui_update_command)

    return jsonify({"status": "ok"}), 200
