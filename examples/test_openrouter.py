"""
Test OpenRouter connection and model availability.

Usage:
    source .venv/bin/activate
    python examples/test_openrouter.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def test_openrouter():
    """Test connection to OpenRouter."""
    import httpx
    
    api_key = os.environ.get("OPENAI_API_KEY")
    api_base = os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("DEFAULT_MODEL", "mock")
    
    print("OpenRouter Configuration:")
    print(f"  API Key: {api_key[:15]}...")
    print(f"  Base URL: {api_base}")
    print(f"  Default Model: {model}")
    print()
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return False
    
    if not api_base:
        print("ERROR: OPENAI_BASE_URL not set")
        return False
    
    # Test the model
    print(f"Testing model: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'hello' in one word."}
        ],
        "max_tokens": 10,
    }
    
    url = f"{api_base}/chat/completions"
    
    try:
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30.0)
            
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"Model response: {content}")
            print("\n✓ OpenRouter connection successful!")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except httpx.RequestError as e:
        print(f"Request error: {e}")
        return False


if __name__ == "__main__":
    test_openrouter()
