import os
import json
import re
from typing import List, Optional

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

GROQ_MODEL       = "llama-3.3-70b-versatile"
TEMPERATURE      = 0.1       # low = deterministic JSON output
MAX_TOKENS       = 256       # plan is just a short JSON array
PROMPT_FILE      = os.path.join(
    os.path.dirname(__file__),
    "..", "prompts", "planning_prompt.txt"
)

VALID_STEPS = {
    "remove_duplicates",
    "handle_missing",
    "handle_outliers",
    "feature_engineering",
    "encoding",
    "scaling",
    "feature_selection",
}


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def generate_plan(
    module1_output: dict,
    eda_report: dict,
    groq_api_key: Optional[str] = None,
) -> List[str]:
    """
    Generate the preprocessing plan using the Groq LLM.

    Args:
        module1_output : Full output dict from Module 1
        eda_report     : EDA report from tools/eda.py
        groq_api_key   : Groq API key (falls back to GROQ_API_KEY env var)

    Returns:
        List of step name strings, e.g.:
        ["handle_missing", "handle_outliers", "encoding", "scaling"]

    Never raises — always returns a valid plan (LLM or fallback).
    """
    # Build the filled prompt
    prompt = _build_prompt(module1_output, eda_report)

    # Try LLM first
    try:
        api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set — using fallback plan")

        raw_response = _call_groq(prompt, api_key)
        plan = _parse_plan(raw_response) #Convert AI response → Python list

        if plan:
            print(f"[agent_planner] LLM plan: {plan}")
            return plan
        else:
            print("[agent_planner] LLM returned empty plan — using fallback")

    except Exception as e:
        print(f"[agent_planner] LLM call failed: {e} — using fallback plan")

    # Fallback: rules-based plan
    plan = _fallback_plan(module1_output, eda_report)
    print(f"[agent_planner] Fallback plan: {plan}")
    return plan


# ─────────────────────────────────────────────
#  PROMPT BUILDER
# ─────────────────────────────────────────────

def _build_prompt(module1_output: dict, eda_report: dict) -> str:
    """
    Fill every {placeholder} in planning_prompt.txt with real data.
    """
    # Load prompt template
    prompt_path = os.path.normpath(PROMPT_FILE)
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    # ── Pull from Module 1 output ──
    dataset_info  = module1_output.get("dataset_info", {})
    schema        = module1_output.get("data_schema", {})
    data_quality  = module1_output.get("data_quality", {})
    ai_summary    = module1_output.get("ai_summary", "No summary available.")
    suggested     = module1_output.get("suggested_analyses", [])

    # ── Pull from EDA report ──
    quality_score  = eda_report.get("quality_score", {})
    column_reports = eda_report.get("column_reports", {})
    warnings       = eda_report.get("warnings", [])
    correlation    = eda_report.get("correlation", {})
    overview       = eda_report.get("overview", {})

    # ── Missing per column ──
    missing_pct    = data_quality.get("missing_percent", {})
    missing_lines  = "\n".join(
        f"  {col}: {pct}%"
        for col, pct in missing_pct.items()
        if pct and float(pct) > 0
    ) or "  None — no missing values"

    # ── Skewed columns ──
    skewed_cols = [
        f"{col} (skew={rep.get('skewness', '?')})"
        for col, rep in column_reports.items()
        if rep.get("is_skewed")
    ]
    skewed_str = str(skewed_cols) if skewed_cols else "None"

    # ── Outlier columns ──
    outlier_cols = [
        f"{col} ({rep.get('outlier_count', '?')} outliers, {rep.get('outlier_percent', '?')}%)"
        for col, rep in column_reports.items()
        if rep.get("has_outliers")
    ]
    outlier_str = str(outlier_cols) if outlier_cols else "None"

    # ── High cardinality categoricals ──
    high_card = [
        f"{col} ({rep.get('n_categories', '?')} unique values)"
        for col, rep in column_reports.items()
        if rep.get("is_high_cardinality")
    ]
    high_card_str = str(high_card) if high_card else "None"

    # ── Highly correlated pairs ──
    high_corr_pairs = correlation.get("highly_correlated_pairs", [])
    if high_corr_pairs:
        corr_str = "\n".join(
            f"  ({p['col1']}, {p['col2']}): r={p['r']}"
            for p in high_corr_pairs[:5]
        )
    else:
        corr_str = "None — no highly correlated pairs"

    # ── EDA warnings (top 5 most severe) ──
    sorted_warnings = sorted(
        warnings,
        key=lambda w: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(w.get("level", "low"), 3)
    )
    eda_warnings_str = "\n".join(
        f"  [{w.get('level','?').upper()}] {w.get('message', '')}"
        for w in sorted_warnings[:5]
    ) or "  None"

    # ── Suggested analyses ──
    if isinstance(suggested, list):
        suggested_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(suggested))
    else:
        suggested_str = str(suggested)

    # ── Fill template ──
    context = {
        "domain":               dataset_info.get("domain", "Unknown"),
        "dataset_type":         dataset_info.get("dataset_type", "Unknown"),
        "rows":                 overview.get("rows", dataset_info.get("rows", "?")),
        "columns":              overview.get("columns", dataset_info.get("columns", "?")),
        "was_sampled":          dataset_info.get("was_sampled", False),
        "ai_summary":           ai_summary,
        "numeric_cols":         schema.get("numeric", []),
        "categorical_cols":     schema.get("categorical", []),
        "datetime_cols":        schema.get("datetime", []),
        "unknown_cols":         schema.get("unknown", []),
        "overall_missing_pct":  overview.get("missing_percent", 0),
        "duplicate_rows":       data_quality.get("duplicate_rows", 0),
        "quality_grade":        quality_score.get("grade", "?"),
        "quality_score":        quality_score.get("score", "?"),
        "missing_per_column":   missing_lines,
        "skewed_cols":          skewed_str,
        "outlier_cols":         outlier_str,
        "high_cardinality_cols": high_card_str,
        "correlated_pairs":     corr_str,
        "eda_warnings":         eda_warnings_str,
        "suggested_analyses":   suggested_str,
    }

    return template.format(**context)


# ─────────────────────────────────────────────
#  LLM CALL
# ─────────────────────────────────────────────

def _call_groq(prompt: str, api_key: str) -> str:
    """
    Call Groq API with the filled prompt.
    Same pattern as Module 1's llm_client.py — compatible design.
    """
    from groq import Groq

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a data preprocessing expert. "
                    "Return ONLY a valid JSON array of step name strings. "
                    "No markdown. No code blocks. No explanation. "
                    "Just the raw JSON array like: "
                    '[\"handle_missing\", \"encoding\", \"scaling\"]'
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────
#  RESPONSE PARSER
# ─────────────────────────────────────────────

def _parse_plan(raw: str) -> List[str]:
    """
    Parse the LLM response into a clean list of valid step names.

    Handles:
    - Clean JSON array: ["handle_missing", "encoding"]
    - JSON wrapped in markdown: ```json [...] ```
    - Extra whitespace / newlines
    - Invalid step names (filtered out)
    - Single quotes instead of double quotes
    """
    if not raw:
        return []

    # Strip markdown code blocks if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    raw = raw.strip("`").strip()

    # Replace single quotes with double quotes
    raw = raw.replace("'", '"')

    # Try to extract JSON array with regex if direct parse fails
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract [...] from anywhere in the response
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                return []
        else:
            return []

    if not isinstance(parsed, list):
        return []

    # Filter to only valid known step names
    clean_plan = [
        str(step).strip().lower()
        for step in parsed
        if str(step).strip().lower() in VALID_STEPS
    ]

    return clean_plan


# ─────────────────────────────────────────────
#  FALLBACK PLAN (rules-based)
# ─────────────────────────────────────────────

def _fallback_plan(module1_output: dict, eda_report: dict) -> List[str]:
    """
    Build a conservative plan from the data directly — no LLM needed.

    Called when:
    - GROQ_API_KEY is not set
    - LLM call fails (network error, rate limit, etc.)
    - LLM returns unparseable or empty response

    This ensures Module 2 always produces a valid result.
    """
    plan  = []
    schema        = module1_output.get("data_schema", {})
    data_quality  = module1_output.get("data_quality", {})
    column_reports = eda_report.get("column_reports", {})

    numeric_cols     = schema.get("numeric", [])
    categorical_cols = schema.get("categorical", [])
    datetime_cols    = schema.get("datetime", [])

    duplicate_rows   = data_quality.get("duplicate_rows", 0)
    missing_pct      = data_quality.get("missing_percent", {})

    # Has duplicates?
    if duplicate_rows and int(duplicate_rows) > 0:
        plan.append("remove_duplicates")

    # Has missing values?
    has_missing = any(
        float(v) > 0
        for v in missing_pct.values()
        if v is not None
    )
    if not has_missing:
        # Double-check with EDA column reports
        has_missing = any(
            rep.get("missing_count", 0) > 0
            for rep in column_reports.values()
        )
    if has_missing:
        plan.append("handle_missing")

    # Has outliers?
    has_outliers = any(
        rep.get("has_outliers", False)
        for rep in column_reports.values()
    )
    if has_outliers:
        plan.append("handle_outliers")

    # Has skewed columns OR datetime cols → feature engineering
    has_skewed   = any(rep.get("is_skewed", False) for rep in column_reports.values())
    has_datetime = len(datetime_cols) > 0
    if has_skewed or has_datetime:
        plan.append("feature_engineering")

    # Has categorical columns → always encode
    if categorical_cols:
        plan.append("encoding")

    # Has numeric columns → always scale
    if numeric_cols:
        plan.append("scaling")

    # Many columns OR high cardinality → feature selection
    total_cols = len(numeric_cols) + len(categorical_cols)
    high_card  = any(rep.get("is_high_cardinality", False) for rep in column_reports.values())
    if total_cols > 15 or high_card:
        plan.append("feature_selection")

    # Minimum plan — always at least encode + scale if applicable
    if not plan:
        if categorical_cols:
            plan.append("encoding")
        if numeric_cols:
            plan.append("scaling")

    return plan
