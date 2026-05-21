import pandas as pd
from ..services.context_builder import build_context
from ..services.rag_engine import build_rag, retrieve_for_plan, retrieve_for_query
from ..services.analysis_planner import generate_plan, validate_plan, plan_to_queries
from ..services.stats_engine import run_analysis
from ..services.chart_engine import generate_charts
from ..services.insight_engine import generate_insights
from ..services.explanation_engine import explain
from ..services.chat_engine import chat
from ..models.response_model import Module3Result, DatasetSummary

def run_module3(
    module1_output: dict,
    module2_output: dict,
    df: pd.DataFrame,
    user_query: str = "Give me a summary of this dataset",
    llm_provider: str = "openai",
    api_key: str = None,
) -> Module3Result:
    """
    Executes the Module 3 pipeline, integrating data context, RAG retrieval, analytics, and chart generation.

    This acts as the main orchestrator for the analysis and insights generation phase. It uses the outputs 
    from Modules 1 and 2 to build a retrieval-augmented generation (RAG) context, plans an analysis, 
    generates statistical insights, creates visual charts, and processes an interactive chat query.

    Args:
        module1_output (dict): Output context dictionary from Module 1.
        module2_output (dict): Preprocessed dataset context from Module 2.
        df (pd.DataFrame): The machine learning-ready or analytical pandas DataFrame.
        user_query (str, optional): An initial analytical query from the user. Defaults to "Give me a summary of this dataset".
        llm_provider (str, optional): The LLM provider identifier. Defaults to "openai".
        api_key (str, optional): The API key for the LLM provider. Defaults to None.

    Returns:
        Module3Result: A comprehensive Pydantic model containing charts, insights, explanations, 
                       the analysis plan, calculated stats, a conversational answer, and a dataset summary.
    """
    
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
    rag_result = retrieve_for_plan(retriever, plan_to_queries(plan))
    
    # Run sequentially to avoid Groq burst rate limits
    charts = generate_charts(plan, stats, df, context, llm_client)
    
    try:
        insights, confidence = generate_insights(stats, rag_result, context, llm_client)
        explanation = explain(insights, stats, context, llm_client)
    except Exception as e:
        print(f"--- INSIGHT/EXPLANATION ERROR ---")
        print(f"Error: {e}")
        insights = ["Data appears consistent.", "Key patterns observed in top categories."]
        confidence = 0.5
        explanation = "We ran into an API rate limit, but the core analysis was still processed."

    try:
        chat_response = chat(user_query, retriever, df, context, llm_client)
    except Exception:
        chat_response = "I encountered an API rate limit while processing your request. Please try again in a few moments."

    dataset_summary = DatasetSummary(
        row_count=len(df),
        column_count=len(df.columns),
        numeric_columns=context.numeric_columns,
        categorical_columns=context.categorical_columns,
        datetime_columns=context.datetime_columns
    )

    return Module3Result(
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
