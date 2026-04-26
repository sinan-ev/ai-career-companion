from ..services.context_builder import DataContext
import json

def generate_plan(context: DataContext, llm_client) -> list[str]:
    # Dummy mock plan returning standard types
    return ["distribution", "comparison", "correlation"]

def validate_plan(plan: list[str], context: DataContext) -> list[str]:
    valid_plan = []
    for item in plan:
        if item == "time_series" and not context.datetime_columns:
            continue
        if item == "correlation" and len(context.numeric_columns) < 2:
            continue
        if item == "comparison" and (len(context.categorical_columns) < 1 or len(context.numeric_columns) < 1):
            continue
        valid_plan.append(item)
    return valid_plan

def plan_to_queries(plan: list[str]) -> list[str]:
    mapping = {
        "trend": "trend patterns over time in this dataset",
        "comparison": "category comparison group differences",
        "correlation": "correlations between numeric columns",
        "distribution": "data distribution statistics outliers",
        "top_n": "top values rankings highest lowest",
        "time_series": "time series temporal patterns seasonality"
    }
    return [mapping.get(p, p) for p in plan]
