"""
utils/llm_client.py
====================
Shared LLM client for all backend modules.
Provides both:
  - LLMClient class  (used by module4 engines)
  - get_groq_client() function (used by module1/module3)
"""
import json
import os
from functools import lru_cache

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2048"))


@lru_cache()
def get_groq_client() -> Groq:
    """
    Returns a cached Groq API client instance.

    Returns:
        Groq: An initialized Groq client using the GROQ_API_KEY env variable.
    """
    return Groq(api_key=_GROQ_API_KEY)


class LLMClient:
    """
    High-level wrapper around the Groq LLM API used by module4 engines.

    Provides a simple `.generate()` interface so individual engines don't
    need to manage API keys, model names, or request formatting.
    """

    def __init__(self):
        self.client = get_groq_client()
        self.model = _GROQ_MODEL
        self.max_tokens = _GROQ_MAX_TOKENS

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        require_json: bool = False,
        max_tokens: int = None,
    ) -> str:
        """
        Calls the Groq LLM and returns the model's text response.

        Args:
            system_prompt (str): Instruction context for the model.
            user_prompt (str): The user-facing question or task.
            require_json (bool): If True, instructs the model to return valid JSON only.
            max_tokens (int, optional): Override the default max token limit.

        Returns:
            str: The raw text response from the model.

        Raises:
            Exception: Propagates any Groq API errors to the caller.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if require_json:
            messages[0]["content"] += (
                " Always respond with valid JSON only — no markdown, no explanation."
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens or self.max_tokens,
            temperature=0.2,
        )

        return response.choices[0].message.content.strip()
