"""
Minimal example: ShadowDance wraps OpenAI client in one line.

Usage:
    source .venv/bin/activate
    python examples/openai_client.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI
from shadowdance import ShadowDance


def main():
    """Demonstrate ShadowDance wrapping OpenAI client."""
    # Create OpenAI client (pointed at OpenRouter)
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )
    
    # ONE LINE - wrap with ShadowDance
    client = ShadowDance(client)
    
    # All calls now traced in LangSmith
    print("Calling OpenAI (via OpenRouter)...")
    
    response = client.chat.completions.create(
        model=os.environ.get("DEFAULT_MODEL", "openrouter/hunter-alpha"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one word."},
        ],
        max_tokens=10,
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print("\nCheck LangSmith for the traced call!")
    print("Project: shadowdance")


if __name__ == "__main__":
    main()
