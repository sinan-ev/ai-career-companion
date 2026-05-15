import os
import json
from groq import Groq
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Mock or real LLM client
class LLMClient:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "dummy_key")
        try:
            self.client = Groq(api_key=self.api_key)
            self.use_mock = self.api_key == "dummy_key"
        except Exception:
            self.use_mock = True

    def generate(self, system_prompt: str, user_prompt: str, require_json: bool = False) -> str:
        if self.use_mock:
            # Fallback mock responses if no API key is provided
            if require_json:
                return json.dumps({"response": "Mock LLM JSON Response", "business_insights": "The data shows potential mock trends."})
            return "This is a mock LLM response. Please set GROQ_API_KEY for live inference."
            
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                response_format={"type": "json_object"} if require_json else None,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if require_json:
                return json.dumps({"error": str(e), "business_insights": "Fallback: Error calling LLM."})
            return f"Error calling LLM: {str(e)}"
