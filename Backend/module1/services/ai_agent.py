import json
from module1.utils.llm_client import call_llm

from module1.config import get_settings

settings = get_settings()


def run_ai_agent(
    domain: str,
    dataset_type: str,
    schema: dict[str, list[str]],
    column_meanings: dict[str, str],
    data_quality: dict,
    basic_stats: dict,
    row_count: int,
    col_count: int,
    was_sampled: bool,
) -> tuple[str, list[str]]:
    """
    Main AI reasoning step using Gemini free tier.
    Returns (ai_summary, suggested_analyses).
    """
    prompt = _build_prompt(
        domain=domain,
        dataset_type=dataset_type,
        schema=schema,
        column_meanings=column_meanings,
        data_quality=data_quality,
        basic_stats=basic_stats,
        row_count=row_count,
        col_count=col_count,
        was_sampled=was_sampled,
    )

    raw = call_llm(prompt, max_tokens=settings.groq_max_tokens)

    return _parse_agent_response(raw)


def _build_prompt(
    domain, dataset_type, schema, column_meanings,
    data_quality, basic_stats, row_count, col_count, was_sampled,
) -> str:

    columns_text = "\n".join(
        f"  - {col} ({_get_col_type(col, schema)}): {meaning}"
        for col, meaning in column_meanings.items()
    )

    quality_issues = []
    missing = data_quality.get("missing_values", {})
    if missing:
        top_missing = sorted(missing.items(), key=lambda x: x[1], reverse=True)[:5]
        for col, count in top_missing:
            pct = data_quality.get("missing_percent", {}).get(col, 0)
            quality_issues.append(f"  - '{col}': {count} missing values ({pct}%)")

    dupes = data_quality.get("duplicate_rows", 0)
    if dupes > 0:
        quality_issues.append(f"  - {dupes} duplicate rows detected")

    quality_text = (
        "\n".join(quality_issues)
        if quality_issues
        else "  - No major quality issues detected"
    )

    stats_text = ""
    if basic_stats:
        for col in list(basic_stats.keys())[:5]:
            s = basic_stats[col]
            stats_text += (
                f"  - {col}: mean={s.get('mean','N/A')}, "
                f"min={s.get('min','N/A')}, "
                f"max={s.get('max','N/A')}, "
                f"std={s.get('std','N/A')}\n"
            )

    sampling_note = (
        f"(sampled to {row_count:,} rows for analysis)"
        if was_sampled else ""
    )

    return f"""You are a senior data scientist. Analyze this dataset metadata and respond
with a structured JSON summary.

=== DATASET OVERVIEW ===
Domain:   {domain}
Type:     {dataset_type}
Rows:     {row_count:,} {sampling_note}
Columns:  {col_count}

=== COLUMN DETAILS ===
{columns_text}

=== SCHEMA ===
Numeric:     {schema.get('numeric', [])}
Categorical: {schema.get('categorical', [])}
Datetime:    {schema.get('datetime', [])}

=== DATA QUALITY ===
{quality_text}

=== NUMERIC STATISTICS ===
{stats_text if stats_text else "  No numeric columns"}

=== TASK ===
Return ONLY this JSON (no markdown, no extra text):
{{
  "ai_summary": "3-5 paragraph narrative. Cover: what this dataset is, its real-world context, what the columns reveal, data quality concerns, and what questions it can answer.",
  "suggested_analyses": [
    "Specific analysis 1 naming actual columns",
    "Specific analysis 2 naming actual columns",
    "Specific analysis 3 naming actual columns",
    "Specific analysis 4 naming actual columns",
    "Specific analysis 5 naming actual columns"
  ]
}}"""


def _get_col_type(col: str, schema: dict) -> str:
    for type_label, cols in schema.items():
        if col in cols:
            return type_label
    return "unknown"


def _parse_agent_response(raw: str) -> tuple[str, list[str]]:
    try:
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        summary = result.get("ai_summary", "Could not generate summary.")
        suggestions = [str(s) for s in result.get("suggested_analyses", [])[:7]]
        return summary, suggestions
    except Exception:
        return "AI summary could not be parsed.", [
            "Perform exploratory data analysis on all columns"
        ]
