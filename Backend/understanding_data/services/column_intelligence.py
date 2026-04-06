from utils.text_cleaner import clean_column_name, extract_keywords
from utils.constants import COLUMN_KEYWORD_MAP
from utils.llm_client import call_llm


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


def _ai_fallback(
    unresolved: list[str],
    schema: dict[str, list[str]],
    sample_values: dict[str, list],
) -> dict[str, str]:
    """Gemini explains all unresolved columns in one call."""

    sample_context = ""
    for col in unresolved:
        vals = sample_values.get(col, [])[:5]
        sample_context += f"  - {col}: sample values = {vals}\n"

    schema_context = (
        f"Numeric columns: {schema.get('numeric', [])}\n"
        f"Categorical columns: {schema.get('categorical', [])}\n"
        f"Datetime columns: {schema.get('datetime', [])}\n"
    )

    prompt = f"""You are a data analyst. For each column below, write a SHORT plain-English
description of what it likely represents (max 10 words each).

Dataset schema:
{schema_context}

Columns to explain (with sample values):
{sample_context}

Return ONLY a Python dict like:
{{"column_name": "plain english meaning", ...}}

No explanation. No markdown. Just the raw dict."""

    raw = call_llm(prompt, max_tokens=800)

    try:
        raw = raw.replace("```python", "").replace("```", "").strip()
        result = eval(raw)
        if isinstance(result, dict):
            return result
    except Exception:
        pass

    return {col: "Unknown — could not determine meaning" for col in unresolved}