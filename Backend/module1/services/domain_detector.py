import json
from module1.utils.constants import DOMAIN_KEYWORD_MAP
from module1.utils.text_cleaner import clean_column_name
from module1.utils.llm_client import call_llm


def detect_domain(
    columns: list[str],
    column_meanings: dict[str, str],
    profiler_summary: dict,
) -> tuple[str, str]:
    """
    Identifies the domain and dataset type of the given dataset.
    
    Uses a hybrid approach: first attempts a rule-based matching using keywords. If uncertain, it falls back to an AI-based detection.
    
    Args:
        columns (list[str]): List of column names.
        column_meanings (dict[str, str]): Mapping of column names to their inferred meanings.
        profiler_summary (dict): Profiling summary containing dataset quality metrics.
        
    Returns:
        tuple[str, str]: A tuple containing the detected domain (e.g., 'Healthcare') and dataset type (e.g., 'Medical / Clinical Data').
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
    """
    Maps a detected domain to a specific dataset type category.
    
    Args:
        domain (str): The primary domain detected.
        
    Returns:
        str: The mapped dataset type.
    """
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
    """
    Fallback AI mechanism to detect domain and dataset type.
    
    Args:
        columns (list[str]): The dataset's columns.
        column_meanings (dict[str, str]): The inferred meanings of the columns.
        
    Returns:
        tuple[str, str]: Detected domain and dataset type from the LLM.
    """

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