import pandas as pd
from ..services.context_builder import build_context
from ..services.rag_engine import build_rag, retrieve_for_plan, retrieve_for_query
from ..services.analysis_planner import generate_plan, validate_plan, plan_to_queries
from ..services.stats_engine import run_analysis
from ..services.chart_engine import generate_charts
from ..services.insight_engine import generate_insights
from ..services.explanation_engine import explain
from ..services.chat_engine import chat
from ..models.response_model import Module3AResult, DatasetSummary

def run_module3A(
    module1_output: dict,
    module2_output: dict,
    df: pd.DataFrame,
    user_query: str = "Give me a summary of this dataset",
    llm_provider: str = "openai",
    api_key: str = None,
) -> Module3AResult:
    
    from module1.utils.llm_client import get_groq_client
    try:
        llm_client = get_groq_client()
    except Exception:
        llm_client = None

    context = build_context(module1_output, module2_output)
    store, retriever = build_rag(context)
    plan = generate_plan(context, llm_client)
    plan = validate_plan(plan, context)
    
    stats = run_analysis(plan, df, context)
    charts = generate_charts(plan, stats, df, context, llm_client)
    
    rag_result = retrieve_for_plan(retriever, plan_to_queries(plan))
    insights, confidence = generate_insights(stats, rag_result, context, llm_client)
    
    explanation = explain(insights, stats, context, llm_client)
    chat_response = chat(user_query, retriever, df, context, llm_client)

    dataset_summary = DatasetSummary(
        row_count=len(df),
        column_count=len(df.columns),
        numeric_columns=context.numeric_columns,
        categorical_columns=context.categorical_columns,
        datetime_columns=context.datetime_columns
    )

    return Module3AResult(
        charts=charts,
        insights=insights,
        explanations=explanation,
        analysis_plan=plan,
        stats=stats,
        chat_response=chat_response,
        confidence_score=confidence,
        rag_context=rag_result.context_text,
        dataset_summary=dataset_summary
    )
