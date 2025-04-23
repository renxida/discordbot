#!/usr/bin/env python3
import requests
import json
from typing import List, Dict

API_URL = "http://guanaco-submitter.guanaco-backend.k2.chaiverse.com/endpoints/onsite/chat"
API_KEY = "CR_14d43f2bf78b4b0590c2a8b87f354746"


def test_api_call(prompt: str, bot_name: str, user_name: str, chat_history: List[Dict[str, str]]) -> dict:
    """Test the Chai API with the given parameters."""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "memory": "",  # deprecated
        "prompt": prompt,
        "bot_name": bot_name,
        "user_name": user_name,
        "chat_history": chat_history
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Example usage
    test_prompt = "An engaging conversation with ChatBot."
    test_bot_name = "ChatBot"
    test_user_name = "User"
    test_chat_history = [
        {"sender": "ChatBot", "message": "Hi there! How can I help you today?"},
        {"sender": "User", "message": "Tell me a joke!"}
    ]
    
    print("Making API request...")
    result = test_api_call(test_prompt, test_bot_name, test_user_name, test_chat_history)
    
    print("\nAPI Response:")
    print(json.dumps(result, indent=2))