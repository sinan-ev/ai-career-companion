"""

Universal deep EDA tool 

Returns:
  eda_report        : dict matching EDAReport schema in module2_response.py
  summary_for_agent : compact plain-text string for the LLM planning prompt
"""

import re
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

SKEW_MODERATE    = 1.0
SKEW_HIGH        = 2.0
OUTLIER_IQR_K    = 1.5
CORR_HIGH        = 0.85
CARDINALITY_LOW  = 10
CARDINALITY_HIGH = 50


def generate_eda(
    df: pd.DataFrame,
    module1_output: Dict[str, Any],
    target_col: str = None,
) -> Tuple[Dict[str, Any], str]:
    schema          = module1_output.get("data_schema", {})
    data_quality    = module1_output.get("data_quality", {})
    column_meanings = module1_output.get("column_meanings", {})
    ai_summary      = module1_output.get("ai_summary", "")
    suggested       = module1_output.get("suggested_analyses", [])

    numeric_cols     = [c for c in schema.get("numeric",     []) if c in df.columns]
    categorical_cols = [c for c in schema.get("categorical", []) if c in df.columns]
    datetime_cols    = [c for c in schema.get("datetime",    []) if c in df.columns]
    boolean_cols     = [c for c in schema.get("boolean",     []) if c in df.columns]
    id_cols          = [c for c in schema.get("id",          []) if c in df.columns]

    n_rows, n_cols = df.shape
    missing_pct    = data_quality.get("missing_percent", {})
    duplicate_rows = int(data_quality.get("duplicate_rows", 0))
    cols_with_missing = {c: v for c, v in missing_pct.items() if v > 0}
    total_missing_pct = (
        sum(cols_with_missing.values()) / max(len(missing_pct), 1)
        if missing_pct else
        float(df.isnull().mean().mean() * 100)
    )

    # Skewness
    skewness_report, highly_skewed, moderately_skewed = {}, [], []

    for col in numeric_cols:
        if col == target_col:
            continue
        s = df[col].dropna()
        if len(s) < 10:
            continue
        try:
            skew_val = float(s.skew())
        except Exception:
            continue

        skewness_report[col] = round(skew_val, 3)

        if abs(skew_val) > SKEW_HIGH:
            highly_skewed.append(col)
        elif abs(skew_val) > SKEW_MODERATE:
            moderately_skewed.append(col)

    # Outliers
    outlier_report, outlier_severe = {}, []

    for col in numeric_cols:
        if col == target_col:
            continue

        s = df[col].dropna()
        if len(s) < 10:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - OUTLIER_IQR_K * iqr
        upper = q3 + OUTLIER_IQR_K * iqr
        n_out = int(((s < lower) | (s > upper)).sum())
        pct   = round(n_out / len(s) * 100, 2)
        outlier_report[col] = {"count": n_out, "pct": pct}
        if pct > 5:
            outlier_severe.append(col)

    # Correlations
    high_corr_pairs, corr_matrix_data = [], {}

    if len(numeric_cols) >= 2:
        num_df = df[numeric_cols].select_dtypes(include=[np.number])

        if num_df.shape[1] >= 2:
            corr = num_df.corr().abs()
            cols = list(corr.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    c1, c2 = cols[i], cols[j]
                    val = corr.loc[c1, c2]
                    if not pd.isna(val) and val >= CORR_HIGH:
                        high_corr_pairs.append({"col1": c1, "col2": c2, "correlation": round(float(val), 3)})

            corr_matrix_data = {"top_pairs": sorted(high_corr_pairs, key=lambda x: -x["correlation"])[:10]}

    # Cardinality
    cardinality_report, high_cardinality_cols = {}, []
    
    for col in categorical_cols:
        n_unique = int(df[col].nunique(dropna=True))
        cardinality_report[col] = n_unique
        if n_unique > CARDINALITY_HIGH:
            high_cardinality_cols.append(col)

    # Target distribution
    target_info = {}
    if target_col and target_col in df.columns:
        t = df[target_col].dropna()
        if target_col in numeric_cols:
            target_info = {
                "type": "numeric",
                "mean": float(t.mean()),
                "std":  float(t.std()),
                "min":  float(t.min()),
                "max":  float(t.max()),
                "skew": float(t.skew()),
            }
        else:
            vc = t.value_counts(normalize=True).round(4).to_dict()
            target_info = {
                "type":          "categorical",
                "class_balance": {str(k): float(v) for k, v in vc.items()},
                "n_classes":     int(t.nunique()),
                "is_imbalanced": bool(max(vc.values()) > 0.75) if vc else False,
            }

    # Warnings
    eda_warnings = []
    if total_missing_pct > 20:
        eda_warnings.append(f"HIGH MISSINGNESS: avg {total_missing_pct:.1f}% missing across columns")
    if duplicate_rows > 0:
        eda_warnings.append(f"DUPLICATES: {duplicate_rows} duplicate rows detected by Module 1")
    if highly_skewed:
        eda_warnings.append(f"HIGHLY SKEWED: {highly_skewed} — consider log transform")
    if outlier_severe:
        eda_warnings.append(f"SEVERE OUTLIERS (>5% of rows): {outlier_severe}")
    if high_corr_pairs:
        pair_strs = [f"{p['col1']}/{p['col2']} (r={p['correlation']})" for p in high_corr_pairs[:3]]
        eda_warnings.append(f"HIGH CORRELATION: {pair_strs}")
    if high_cardinality_cols:
        eda_warnings.append(f"HIGH CARDINALITY (>{CARDINALITY_HIGH} vals): {high_cardinality_cols} — use freq encoding")
    if n_rows < 500:
        eda_warnings.append(f"SMALL DATASET: only {n_rows} rows — avoid complex models")

    quality_grade = _compute_quality_grade(
        total_missing_pct, len(outlier_severe), len(high_corr_pairs),
        len(eda_warnings), duplicate_rows, n_rows,
    )

    # Build the per-column report expected by the agent planner and UI
    column_reports = {}

    for col in df.columns:
        report = {}
        if col in cols_with_missing:
            report["missing_count"] = int(df[col].isna().sum())
            report["missing_percent"] = float(cols_with_missing[col])
        
        if col in skewness_report:
            report["skewness"] = skewness_report[col]
            report["is_skewed"] = (col in highly_skewed or col in moderately_skewed)
            
        if col in outlier_report:
            report["outlier_count"] = int(outlier_report[col]["count"])
            report["outlier_percent"] = float(outlier_report[col]["pct"])
            report["has_outliers"] = (col in outlier_severe)

        if col in cardinality_report:
            report["n_categories"] = int(cardinality_report[col])
            report["is_high_cardinality"] = (col in high_cardinality_cols)

        if report:
            column_reports[col] = report

    eda_report = {
        "overview": {
            "n_rows": n_rows,
            "n_cols": n_cols,
            "n_numeric": len(numeric_cols),
            "n_categorical": len(categorical_cols),
            "n_datetime": len(datetime_cols),
            "n_boolean": len(boolean_cols),
            "n_id": len(id_cols),
            "total_missing_pct": round(total_missing_pct, 2),
            "duplicate_rows": duplicate_rows,
        },
        "column_types": {
            **{c: "numeric" for c in numeric_cols},
            **{c: "categorical" for c in categorical_cols},
            **{c: "datetime" for c in datetime_cols},
            **{c: "boolean" for c in boolean_cols},
            **{c: "id" for c in id_cols},
        },
        "column_reports": column_reports,
        "quality_score": {
            "grade": quality_grade,
            "warnings_count": len(eda_warnings),
        },
        "warnings": [{"message": w, "level": "high"} for w in eda_warnings],
        "correlation": {
            "matrix": corr_matrix_data,
            "high_pairs": high_corr_pairs,
        },
        "summary_for_agent": "",
        # Keep these for internal helper backward compatibility if possible
        "cols_with_missing": cols_with_missing,
        "highly_skewed_cols": highly_skewed,
        "moderately_skewed_cols": moderately_skewed,
        "outlier_severe_cols": outlier_severe,
        "outliers": outlier_report,
        "high_corr_pairs": high_corr_pairs,
        "cardinality": cardinality_report,
        "target_info": target_info,
        "eda_warnings": eda_warnings,
        "duplicate_rows": duplicate_rows,
    }

    summary_for_agent = _build_agent_summary(
        eda_report, schema, column_meanings, target_col, ai_summary, suggested
    )
    
    # Fill the summary back into the dict for convenience
    eda_report["summary_for_agent"] = summary_for_agent

    return eda_report, summary_for_agent


def _compute_quality_grade(
    total_missing_pct, n_outlier_severe, n_high_corr,
    n_warnings, duplicate_rows, n_rows
) -> str:
    penalty = 0
    if total_missing_pct > 30:   penalty += 3
    elif total_missing_pct > 15: penalty += 2
    elif total_missing_pct > 5:  penalty += 1
    if n_outlier_severe > 3:     penalty += 2
    elif n_outlier_severe > 0:   penalty += 1
    if n_high_corr > 5:          penalty += 2
    elif n_high_corr > 2:        penalty += 1
    if duplicate_rows > n_rows * 0.1: penalty += 2
    elif duplicate_rows > 0:          penalty += 1
    if n_rows < 100:             penalty += 3
    elif n_rows < 500:           penalty += 1
    if penalty >= 7:   return "D"
    elif penalty >= 4: return "C"
    elif penalty >= 2: return "B"
    else:              return "A"


def _build_agent_summary(
    eda_report, schema, column_meanings, target_col, ai_summary, suggested
) -> str:
    lines = []
    lines.append("=== EDA SUMMARY FOR AGENT PLANNER ===")
    lines.append("")

    lines.append("DATASET OVERVIEW:")
    lines.append(f"  Rows: {eda_report['overview']['n_rows']} | Cols: {eda_report['overview']['n_cols']}")
    lines.append(
        f"  Types: {eda_report['overview']['n_numeric']} numeric, "
        f"{eda_report['overview']['n_categorical']} categorical, "
        f"{eda_report['overview']['n_datetime']} datetime, "
        f"{eda_report['overview']['n_boolean']} boolean"
    )
    lines.append(f"  Quality Grade: {eda_report['quality_score']['grade']}")
    lines.append("")

    if eda_report["cols_with_missing"]:
        lines.append("MISSING VALUES:")
        for col, pct in sorted(eda_report["cols_with_missing"].items(), key=lambda x: -x[1]):
            sev = "HIGH" if pct > 30 else ("MEDIUM" if pct > 10 else "LOW")
            lines.append(f"  {col}: {pct:.1f}% [{sev}]")
        lines.append("  → STEP NEEDED: handle_missing")
    else:
        lines.append("MISSING VALUES: none")
    lines.append("")

    if eda_report["highly_skewed_cols"] or eda_report["moderately_skewed_cols"]:
        lines.append("SKEWNESS:")
        if eda_report["highly_skewed_cols"]:
            lines.append(f"  HIGHLY SKEWED (|skew|>2): {eda_report['highly_skewed_cols']}")
            lines.append("  → STEP NEEDED: engineer_features (log transform)")
        if eda_report["moderately_skewed_cols"]:
            lines.append(f"  MODERATELY SKEWED (|skew|>1): {eda_report['moderately_skewed_cols']}")
    else:
        lines.append("SKEWNESS: all numeric columns within normal range")
    lines.append("")

    if eda_report["outlier_severe_cols"]:
        lines.append("OUTLIERS:")
        lines.append(f"  SEVERE (>5% rows): {eda_report['outlier_severe_cols']}")
        for col in eda_report["outlier_severe_cols"]:
            info = eda_report["outliers"].get(col, {})
            lines.append(f"    {col}: {info.get('count',0)} rows ({info.get('pct',0)}%)")
        lines.append("  → STEP NEEDED: handle_outliers")
    else:
        lines.append("OUTLIERS: none severe")
    lines.append("")

    if eda_report["high_corr_pairs"]:
        lines.append("HIGH CORRELATIONS:")
        for pair in eda_report["high_corr_pairs"][:5]:
            lines.append(f"  {pair['col1']} ↔ {pair['col2']}: r={pair['correlation']}")
        lines.append("  → STEP NEEDED: select_features")
    else:
        lines.append("CORRELATIONS: no high correlations detected")
    lines.append("")

    cat_cols = schema.get("categorical", [])
    if cat_cols:
        lines.append("CATEGORICAL ENCODING PLAN:")
        for col, n_unique in eda_report["cardinality"].items():
            if n_unique <= 2:       strategy = "binary"
            elif n_unique <= CARDINALITY_LOW:  strategy = "one-hot"
            elif n_unique <= CARDINALITY_HIGH: strategy = "ordinal"
            else:                   strategy = "frequency (high cardinality)"
            lines.append(f"  {col}: {n_unique} unique → {strategy}")
        lines.append("  → STEP NEEDED: encode_categoricals")
    lines.append("")

    if eda_report["target_info"]:
        ti = eda_report["target_info"]
        lines.append(f"TARGET COLUMN: {target_col}")
        if ti.get("type") == "categorical":
            lines.append(f"  Task type: CLASSIFICATION | Classes: {ti.get('n_classes')}")
            lines.append(f"  Balance: {ti.get('class_balance')}")
            if ti.get("is_imbalanced"):
                lines.append("  ⚠ IMBALANCED — consider class weights or resampling")
        else:
            lines.append("  Task type: REGRESSION")
            lines.append(f"  Range: [{ti.get('min')} – {ti.get('max')}] | Mean: {ti.get('mean')}")
    lines.append("")

    if eda_report["eda_warnings"]:
        lines.append("WARNINGS:")
        for w in eda_report["eda_warnings"]:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    if ai_summary:
        lines.append("MODULE 1 DOMAIN CONTEXT:")
        lines.append(f"  {ai_summary.strip()}")
        lines.append("")

    lines.append("RECOMMENDED PIPELINE STEPS (in order):")
    steps = _recommend_steps(eda_report, schema)
    for i, step in enumerate(steps, 1):
        lines.append(f"  {i}. {step}")
    lines.append("")
    lines.append("=== END EDA SUMMARY ===")

    return "\n".join(lines)


def _recommend_steps(eda_report: Dict, schema: Dict) -> List[str]:
    steps = []

    if eda_report["cols_with_missing"] or eda_report["duplicate_rows"] > 0:
        steps.append("handle_missing")

    if eda_report["outlier_severe_cols"]:
        steps.append("handle_outliers  (severe outliers: " + str(eda_report["outlier_severe_cols"]) + ")")

    has_skewed   = eda_report["highly_skewed_cols"] or eda_report["moderately_skewed_cols"]
    has_datetime = len(schema.get("datetime", [])) > 0

    if has_skewed or has_datetime:
        steps.append("engineer_features  (log transforms / datetime extraction)")

    if schema.get("categorical") or schema.get("boolean"):
        steps.append("encode_categoricals")
    steps.append("scale_features")
    
    if eda_report["high_corr_pairs"] or eda_report["outlier_severe_cols"]:
        steps.append("select_features  (correlated or noisy columns present)")
    return steps
