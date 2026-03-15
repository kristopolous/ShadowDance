"""
ShadowDance with OpenRouter - Clean example.

Shows how to extend ShadowDance for OpenRouter's API response format.
OpenRouter provides token usage AND cost directly in the response.

Usage:
    source .venv/bin/activate
    python examples/openrouter.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI
from shadowdance import ShadowDance, RunType
from typing import Any, Optional, Dict


class OpenRouterShadowDance(ShadowDance):
    """
    ShadowDance for OpenRouter with automatic usage and cost tracking.
    
    OpenRouter response format:
    {
        "usage": {
            "prompt_tokens": 194,
            "completion_tokens": 2,
            "total_tokens": 196,
            "cost": 0.95,  # USD
            "prompt_tokens_details": {...},
            "completion_tokens_details": {...}
        }
    }
    """
    
    def __init__(self, client: Any, run_type: RunType = "llm", model: Optional[str] = None, **kwargs):
        super().__init__(client, run_type=run_type, **kwargs)
        self._model = model
    
    def get_token_count(self, request: Any, response: Any) -> Optional[Dict[str, int]]:
        """
        Extract token count from OpenRouter response.
        
        Response usage object has:
        - prompt_tokens: input tokens
        - completion_tokens: output tokens  
        - total_tokens: sum
        """
        if hasattr(response, 'usage') and response.usage:
            return {
                "input_tokens": getattr(response.usage, 'prompt_tokens', 0),
                "output_tokens": getattr(response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(response.usage, 'total_tokens', 0),
            }
        return None
    
    def get_cost(self, request: Any, response: Any) -> Optional[Dict[str, float]]:
        """
        Get cost from OpenRouter response.
        
        OpenRouter provides cost directly in usage.cost (in USD).
        We also break it down by input/output for LangSmith format.
        """
        if not hasattr(response, 'usage') or not response.usage:
            return None
        
        usage = response.usage
        
        # OpenRouter provides total cost directly
        total_cost = getattr(usage, 'cost', 0)
        
        # If cost_details available, use it for breakdown
        if hasattr(usage, 'cost_details') and usage.cost_details:
            input_cost = usage.cost_details.get('upstream_inference_prompt_cost', 0)
            output_cost = usage.cost_details.get('upstream_inference_completions_cost', 0)
        else:
            # Fallback: split proportionally by token count
            token_usage = self.get_token_count(request, response)
            if token_usage and token_usage['total_tokens'] > 0:
                input_ratio = token_usage['input_tokens'] / token_usage['total_tokens']
                input_cost = total_cost * input_ratio
                output_cost = total_cost * (1 - input_ratio)
            else:
                input_cost = 0
                output_cost = total_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }


def main():
    """Demonstrate OpenRouter with ShadowDance."""
    
    # Create OpenAI client pointed at OpenRouter
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )
    
    # Wrap with OpenRouter-aware ShadowDance
    # Use mistralai/ministral-3b-2512 - non-reasoning model with real pricing
    model = "mistralai/ministral-3b-2512"
    client = OpenRouterShadowDance(client, run_type="llm", model=model)
    
    # Make API call - usage and cost automatically logged to LangSmith
    print(f"Calling {model} via OpenRouter...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one word."},
        ],
        max_tokens=10,
    )
    
    print(f"Response: {response.choices[0].message.content}")
    print(f"\nCheck LangSmith for:")
    print(f"  - Token usage (input, output, total)")
    print(f"  - Cost (from OpenRouter)")
    print(f"  - Project: shadowdance")


if __name__ == "__main__":
    main()
