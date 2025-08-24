# app/ollama_client.py
import requests
import json
from typing import List, Optional

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "mistral" 


def get_available_models() -> List[str]:
    """
    Fetches the list of available models from the Ollama API.
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        models_data = response.json().get("models", [])
        return sorted([model['name'].split(':')[0] for model in models_data])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Ollama models: {e}")
        return [DEFAULT_OLLAMA_MODEL]

def get_ui_update(prompt: str, current_ui_state: list, model_name: str) -> dict:
    """
    Generates a UI update command using a specified Ollama model.
    """
    OLLAMA_MODEL = model_name or DEFAULT_OLLAMA_MODEL
    
    full_prompt = f"""
You are an expert AI assistant that generates UI modifications based on user requests.
Your goal is to translate natural language into a single, structured JSON command.
You will be given the user's prompt and the current state of the UI as a JSON array of components.
You MUST respond with ONLY a single JSON object describing the change. Do NOT add any explanatory text.

The JSON object must have two keys:
1. "action": A string that can be "add", "update", or "delete".
2. "payload": An object containing the data for the action.

ACTION DETAILS:
- "add": The payload must be a JSON object describing the new component.
  - It needs a "type" (e.g., "div", "input", "button", "select").
  - It needs a unique "id". Generate a short, descriptive ID based on its purpose.
  - It can have "props" like "text" for text elements, "placeholder" for inputs, or "options" for selects (as an array of strings).
  - Example: {{"action": "add", "payload": {{"type": "button", "id": "submit_btn", "props": {{"text": "Submit"}}}}}}

- "update": The payload must contain the "id" of the component to update and a "props" object with the new values.
  - Example: {{"action": "update", "payload": {{"id": "user_greeting", "props": {{"text": "Hello David!"}}}}}}

- "delete": The payload must contain the "id" of the component to remove.
  - Example: {{"action": "delete", "payload": {{"id": "old_button"}}}}

Analyze the user's request and the current UI state to determine the most logical action.
Your response must be ONLY the valid JSON object.

Current UI State: {json.dumps(current_ui_state)}

User Request: "{prompt}"

Assistant:
"""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
        }

        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status()

        response_data = response.json()
        
        message_content = response_data.get("response", "")

        # --- **DEBUGGING LINE** ---
        # Print the raw response from the model before parsing
        print("--- RAW OLLAMA RESPONSE ---")
        print(message_content)
        print("--------------------------")
        # --- **END DEBUGGING** ---
        
        json_start = message_content.find('{')
        json_end = message_content.rfind('}')
        
        if json_start != -1 and json_end != -1:
            json_str = message_content[json_start:json_end+1]
            return json.loads(json_str)
        else:
            raise json.JSONDecodeError("No valid JSON object found in the model's response.", message_content, 0)

    except requests.exceptions.RequestException as e:
        return {"action": "error", "payload": {"message": f"Could not connect to Ollama: {e}"}}
    except json.JSONDecodeError as e:
        raw_response = locals().get('message_content', 'No response content captured.')
        return {"action": "error", "payload": {"message": f"Invalid JSON from LLM: {e}. Raw response: '{raw_response}'"}}
    except Exception as e:
        return {"action": "error", "payload": {"message": f"An unknown error occurred: {e}"}}

def get_ui_update_from_interaction(interaction_data: dict, current_ui_state: list, model_name: str) -> dict:
    """
    Generates a UI update command based on a user interaction with a UI element.
    """
    OLLAMA_MODEL = model_name or DEFAULT_OLLAMA_MODEL

    full_prompt = f"""
You are an expert AI assistant that generates UI modifications in response to user interactions.
A user performed an action on a UI element. Your goal is to generate a single, structured JSON command to update the UI accordingly.
You will be given details of the interaction and the current state of the UI, including the values of all input fields.
You MUST respond with ONLY a single JSON object describing the change. Do NOT add any explanatory text.

The JSON object must have "action" and "payload" keys, following the same format as before.

INTERACTION DETAILS:
- Interacted Element ID: {interaction_data.get('id')}
- Event Type: {interaction_data.get('event')}
- Current values of all inputs: {json.dumps(interaction_data.get('values'))}

CURRENT UI STATE: {json.dumps(current_ui_state)}

Based on this user interaction and the current state, determine the appropriate UI change.
For example, if a user typed "apple" into an input with id "new_item_input" and clicked a button with id "add_btn", you might add "apple" to a dropdown list.

Assistant:
"""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
        }

        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status()

        response_data = response.json()
        message_content = response_data.get("response", "")

        print("--- RAW OLLAMA INTERACTION RESPONSE ---")
        print(message_content)
        print("---------------------------------------")

        json_start = message_content.find('{')
        json_end = message_content.rfind('}')

        if json_start != -1 and json_end != -1:
            json_str = message_content[json_start:json_end+1]
            return json.loads(json_str)
        else:
            raise json.JSONDecodeError("No valid JSON object found in the model's response.", message_content, 0)

    except requests.exceptions.RequestException as e:
        return {"action": "error", "payload": {"message": f"Could not connect to Ollama: {e}"}}
    except json.JSONDecodeError as e:
        raw_response = locals().get('message_content', 'No response content captured.')
        return {"action": "error", "payload": {"message": f"Invalid JSON from LLM: {e}. Raw response: '{raw_response}'"}}
    except Exception as e:
        return {"action": "error", "payload": {"message": f"An unknown error occurred: {e}"}}
