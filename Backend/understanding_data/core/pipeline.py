import pandas as pd
from fastapi import UploadFile

from services.loader import load_dataset
from services.validator import validate_dataset
from services.schema import detect_schema
from services.sampler import maybe_sample
from services.profiler import profile_dataset, get_basic_stats, generate_cleaning_suggestions
from services.column_intelligence import explain_columns
from services.domain_detector import detect_domain
from services.ai_agent import run_ai_agent
from models.response_model import (
    AnalysisResponse,
    DatasetInfo,
    SchemaInfo,
    DataQuality,
)


async def run_pipeline(file: UploadFile) -> AnalysisResponse:
    """
    Master orchestrator. Runs every stage in sequence and
    assembles the final structured response.

    Flow:
        load → validate → schema → sample → profile
        → column intelligence → domain → AI agent → response
    """

    # ── Stage 1: Load ──────────────────────────────────────────
    df, filename = await load_dataset(file)
    original_row_count = len(df)
    original_col_count = len(df.columns)

    # ── Stage 2: Validate ──────────────────────────────────────
    warnings = validate_dataset(df, filename)

    # ── Stage 3: Detect schema BEFORE sampling ─────────────────
    # We want schema from the full dataset, not the sample
    raw_schema = detect_schema(df)

    # ── Stage 4: Sample if large ───────────────────────────────
    df, was_sampled = maybe_sample(df)

    # ── Stage 5: Profile ───────────────────────────────────────
    quality = profile_dataset(df)
    basic_stats = get_basic_stats(df)
    cleaning_suggestions = generate_cleaning_suggestions(df, raw_schema, {})

    # ── Stage 6: Column Intelligence ───────────────────────────
    # Build sample values dict for AI context (5 values per column)
    # sample_values = {
    #     col: df[col].dropna().head(5).tolist()
    #     for col in df.columns
    # }
    from services.profiler import normalize_nulls

    df_normalized = normalize_nulls(df)

    sample_values = {
        col: df_normalized[col].dropna().head(5).tolist()
        for col in df_normalized.columns
}


    column_meanings = explain_columns(
        columns=list(df.columns),
        schema=raw_schema,
        sample_values=sample_values,
    )

    # ── Stage 7: Domain Detection ──────────────────────────────
    domain, dataset_type = detect_domain(
        columns=list(df.columns),
        column_meanings=column_meanings,
        profiler_summary=quality.dict(),
    )

    # ── Stage 8: AI Agent ──────────────────────────────────────
    ai_summary, suggested_analyses = run_ai_agent(
        domain=domain,
        dataset_type=dataset_type,
        schema=raw_schema,
        column_meanings=column_meanings,
        data_quality=quality.dict(),
        basic_stats=basic_stats,
        row_count=len(df),
        col_count=original_col_count,
        was_sampled=was_sampled,
    )
     
  
    # ── Stage 9: Assemble Response ─────────────────────────────
    return AnalysisResponse(
        dataset_info=DatasetInfo(
            rows=original_row_count,
            columns=original_col_count,
            domain=domain,
            dataset_type=dataset_type,
            file_name=filename,
            was_sampled=was_sampled,
        ),
        schema=SchemaInfo(
            numeric=raw_schema.get("numeric", []),
            categorical=raw_schema.get("categorical", []),
            datetime=raw_schema.get("datetime", []),
            unknown=raw_schema.get("unknown", []),
        ),
        column_meanings=column_meanings,
        data_quality=DataQuality(
            missing_values=quality.missing_values,
            missing_percent=quality.missing_percent,
            duplicate_rows=quality.duplicate_rows,
            total_rows=quality.total_rows,
        ),
        
        # type_suggestions = type_suggestions,
        ai_summary=ai_summary,
        suggested_analyses=suggested_analyses,
        warnings=warnings + cleaning_suggestions,
    )
