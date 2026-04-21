from module1.utils.text_cleaner import clean_column_name, extract_keywords
from module1.utils.constants import COLUMN_KEYWORD_MAP
from module1.utils.llm_client import call_llm
import json


def explain_columns(
    columns: list[str],
    schema: dict[str, list[str]],
    sample_values: dict[str, list],
) -> dict[str, str]:
    """
    For every column, produce a plain-English meaning.
    Stage 1+2: keyword map. Stage 3: Gemini fallback.
    """
    meanings: dict[str, str] = {}
    unresolved: list[str] = []

    for col in columns:
        meaning = _keyword_lookup(col)
        if meaning:
            meanings[col] = meaning
        else:
            unresolved.append(col)

    if unresolved:
        ai_meanings = _ai_fallback(unresolved, schema, sample_values)
        meanings.update(ai_meanings)

    return meanings


def _keyword_lookup(col: str) -> str | None:
    cleaned = clean_column_name(col)

    if cleaned in COLUMN_KEYWORD_MAP:
        return COLUMN_KEYWORD_MAP[cleaned]

    keywords = extract_keywords(col)
    for kw in keywords:
        if kw in COLUMN_KEYWORD_MAP:
            return COLUMN_KEYWORD_MAP[kw]

    return None


# def _ai_fallback(
#     unresolved: list[str],
#     schema: dict[str, list[str]],
#     sample_values: dict[str, list],
# ) -> dict[str, str]:
#     """Gemini explains all unresolved columns in one call."""

#     sample_context = ""
#     for col in unresolved:
#         vals = sample_values.get(col, [])[:5]
#         sample_context += f"  - {col}: sample values = {vals}\n"

#     schema_context = (
#         f"Numeric columns: {schema.get('numeric', [])}\n"
#         f"Categorical columns: {schema.get('categorical', [])}\n"
#         f"Datetime columns: {schema.get('datetime', [])}\n"
#     )

#     prompt = f"""You are a data analyst. For each column below, write a SHORT plain-English
# description of what it likely represents (max 10 words each).

# Dataset schema:
# {schema_context}

# Columns to explain (with sample values):
# {sample_context}

# Return ONLY a Python dict like:
# {{"column_name": "plain english meaning", ...}}

# No explanation. No markdown. Just the raw dict."""

#     raw = call_llm(prompt, max_tokens=800)

#     try:
#         raw = raw.replace("```python", "").replace("```", "").strip()
#         result = eval(raw)
#         if isinstance(result, dict):
#             return result
#     except Exception:
#         pass

#     return {col: "Unknown — could not determine meaning" for col in unresolved}



import json
import re

def _ai_fallback(
    unresolved: list[str],
    schema: dict[str, list[str]],
    sample_values: dict[str, list],
) -> dict[str, str]:
    """
    Stage 3: Groq explains all unresolved columns in one call.
    Uses strict JSON parsing with multiple fallback strategies.
    """
    sample_context = ""
    for col in unresolved:
        vals = sample_values.get(col, [])[:5]
        # Clean sample values — remove NaN before showing to AI
        clean_vals = [
            v for v in vals
            if v is not None and str(v).lower() not in {"nan", "none", ""}
        ]
        sample_context += f"  - {col}: sample values = {clean_vals}\n"

    schema_context = (
        f"Numeric columns: {schema.get('numeric', [])}\n"
        f"Categorical columns: {schema.get('categorical', [])}\n"
        f"Datetime columns: {schema.get('datetime', [])}\n"
    )

    prompt = f"""You are a data analyst. Explain what each column below likely represents.

Dataset schema:
{schema_context}

Columns to explain (with sample values):
{sample_context}

RULES:
- Return ONLY a valid JSON object
- No markdown, no code fences, no explanation text
- Keys = exact column names, values = short meaning (max 10 words)
- Every column must have an entry

Example format:
{{"col1": "meaning here", "col2": "meaning here"}}

Return the JSON now:"""

    raw = call_llm(prompt, max_tokens=800)

    # Strategy 1 — direct JSON parse
    try:
        cleaned = raw.strip()
        result = json.loads(cleaned)
        if isinstance(result, dict) and len(result) > 0:
            return _validate_meanings(result, unresolved)
    except json.JSONDecodeError:
        pass

    # Strategy 2 — strip markdown fences then parse
    try:
        cleaned = re.sub(
            r"```(?:json)?|```", "", raw
        ).strip()
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return _validate_meanings(result, unresolved)
    except json.JSONDecodeError:
        pass

    # Strategy 3 — extract JSON object using regex
    try:
        match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, dict):
                return _validate_meanings(result, unresolved)
    except (json.JSONDecodeError, AttributeError):
        pass

    # Strategy 4 — parse line by line as key:value pairs
    try:
        meanings = {}
        for line in raw.split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip().strip('"').strip("'")
                val = parts[1].strip().strip('",').strip("'")
                if key in unresolved and val:
                    meanings[key] = val
        if meanings:
            return _validate_meanings(meanings, unresolved)
    except Exception:
        pass

    # Final fallback — mark all as unknown
    return {
        col: "Could not determine meaning"
        for col in unresolved
    }


def _validate_meanings(
    result: dict,
    unresolved: list[str]
) -> dict[str, str]:
    """
    Ensure every unresolved column has an entry.
    Fill missing ones with fallback text.
    """
    validated = {}
    for col in unresolved:
        meaning = result.get(col, "").strip()
        if meaning and len(meaning) > 2:
            validated[col] = meaning
        else:
            # Try case-insensitive match
            for key, val in result.items():
                if key.lower() == col.lower():
                    validated[col] = val
                    break
            else:
                validated[col] = "Could not determine meaning"
    return validated