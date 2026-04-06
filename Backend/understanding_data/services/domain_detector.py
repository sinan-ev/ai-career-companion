import json
from utils.constants import DOMAIN_KEYWORD_MAP
from utils.text_cleaner import clean_column_name
from utils.llm_client import call_llm


def detect_domain(
    columns: list[str],
    column_meanings: dict[str, str],
    profiler_summary: dict,
) -> tuple[str, str]:
    """
    Hybrid domain detection: rules first, Gemini if uncertain.
    Returns (domain, dataset_type).
    """
    cleaned_cols = [clean_column_name(c) for c in columns]

    scores: dict[str, int] = {}
    
    for domain, keywords in DOMAIN_KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in cleaned_cols)
        if score > 0:
            scores[domain] = score

    if scores:
        best_domain = max(scores, key=scores.get)
        if scores[best_domain] >= 2:
            dataset_type = _get_dataset_type(best_domain)
            return best_domain.title(), dataset_type

    return _ai_domain_detection(columns, column_meanings)


def _get_dataset_type(domain: str) -> str:
    type_map = {
        "titanic": "Survival Analysis",
        "sales": "Sales & Revenue Analysis",
        "hr": "Human Resources Analytics",
        "healthcare": "Medical / Clinical Data",
        "ecommerce": "E-Commerce Transactions",
        "finance": "Financial Market Data",
        "logistics": "Supply Chain & Logistics",
    }
    return type_map.get(domain, "General Tabular Data")


def _ai_domain_detection(
    columns: list[str],
    column_meanings: dict[str, str],
) -> tuple[str, str]:
    """Gemini identifies domain when rules aren't confident."""

    meanings_text = "\n".join(
        f"  - {col}: {meaning}"
        for col, meaning in column_meanings.items()
    )

    prompt = f"""You are a data scientist. Based on these column names and meanings,
identify what kind of dataset this is.

Columns and meanings:
{meanings_text}

Reply with ONLY a JSON object (no markdown, no explanation):
{{
  "domain": "short dataset name e.g. Titanic, Customer Churn, Hospital Records",
  "dataset_type": "analytical category e.g. Survival Analysis, Churn Prediction"
}}"""

    raw = call_llm(prompt, max_tokens=200)

    try:
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return result.get("domain", "Unknown"), result.get("dataset_type", "General Tabular Data")
    except Exception:
        return "Unknown", "General Tabular Data"