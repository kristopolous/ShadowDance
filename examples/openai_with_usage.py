"""
ShadowDance with OpenAI token usage and cost tracking.

Shows how to extend ShadowDance for provider-specific usage tracking.
"""

from shadowdance import ShadowDance, RunType
from typing import Any, Optional, Dict


class OpenAIShadowDance(ShadowDance):
    """
    ShadowDance for OpenAI/OpenRouter with automatic usage tracking.
    
    Extracts token counts and calculates costs from OpenAI API responses.
    """
    
    # Pricing per million tokens (USD)
    PRICING = {
        "openrouter/hunter-alpha": {"input": 0.0, "output": 0.0},
        "qwen/qwen3.5-9b": {"input": 0.05, "output": 0.15},
        "meta-llama/llama-3-8b-instruct": {"input": 0.05, "output": 0.08},
    }
    
    def __init__(self, client: Any, run_type: RunType = "llm", model: Optional[str] = None, **kwargs):
        super().__init__(client, run_type=run_type, **kwargs)
        self._model = model
    
    def get_token_count(self, request: Any, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage from OpenAI response."""
        if hasattr(response, 'usage') and response.usage:
            return {
                "input_tokens": getattr(response.usage, 'prompt_tokens', 0),
                "output_tokens": getattr(response.usage, 'completion_tokens', 0),
                "total_tokens": getattr(response.usage, 'total_tokens', 0),
            }
        return None
    
    def get_cost(self, request: Any, response: Any) -> Optional[Dict[str, float]]:
        """Calculate cost based on token usage and model pricing."""
        token_usage = self.get_token_count(request, response)
        if not token_usage or not self._model:
            return None
        
        pricing = self.PRICING.get(self._model, {"input": 0.0, "output": 0.0})
        
        input_cost = (token_usage["input_tokens"] * pricing["input"]) / 1_000_000
        output_cost = (token_usage["output_tokens"] * pricing["output"]) / 1_000_000
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }


# Example usage
if __name__ == "__main__":
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    from openai import OpenAI
    
    load_dotenv(Path(__file__).parent.parent / ".env")
    
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )
    
    model = os.environ.get("DEFAULT_MODEL", "openrouter/hunter-alpha")
    client = OpenAIShadowDance(client, run_type="llm", model=model)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one word."},
        ],
        max_tokens=10,
    )
    
    print(f"Response: {response.choices[0].message.content}")
