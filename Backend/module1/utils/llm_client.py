from groq import Groq
from module1.config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_groq_client() -> Groq:
    return Groq(api_key=settings.groq_api_key)


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """
    Call Groq LLM. Returns raw text response.
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