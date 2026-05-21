from groq import Groq
from module1.config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_groq_client() -> Groq:
    """
    Retrieves a cached instance of the Groq API client.
    
    Returns:
        Groq: An initialized Groq client.
    """
    return Groq(api_key=settings.groq_api_key)


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """
    Calls the configured Groq LLM with a specific prompt.
    
    Args:
        prompt (str): The prompt to send to the LLM.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 1024.
        
    Returns:
        str: The raw text response from the LLM.
    """
    client = get_groq_client()

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {
                "role": "system",
                "content": "You are a senior data scientist. Always respond with valid JSON only — no markdown, no explanation.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=max_tokens,
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()