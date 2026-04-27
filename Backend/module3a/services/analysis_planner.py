from ..services.context_builder import DataContext
import json
import os


def generate_plan(context: DataContext, llm_client) -> list[str]:
    """
    Generate analysis plan using LLM + prompt file.
    Falls back to default plan if LLM is unavailable.
    """

    #  Fallback if no LLM
    if not llm_client:
        return ["distribution", "comparison", "correlation"]

    try:
        #  Load prompt file
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "analysis_prompt.txt")

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        #  Inject dataset context into prompt
        prompt = prompt_template.format(
            dataset_description=context.dataset_description,
            numeric_columns=context.numeric_columns,
            categorical_columns=context.categorical_columns,
            datetime_columns=context.datetime_columns,
            column_meanings=context.column_meanings
        )

        #  Call LLM
        response = llm_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}  # helps structured output
        )

        raw_output = response.choices[0].message.content.strip()

        #  Clean possible markdown formatting
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("```").strip()

        #  Parse JSON
        parsed = json.loads(raw_output)

        # Handle both formats:
        # ["trend", "comparison"] OR {"plan": [...]}
        if isinstance(parsed, dict):
            plan = parsed.get("plan") or parsed.get("analysis") or list(parsed.values())[0]
        else:
            plan = parsed

        #  Final validation
        if not isinstance(plan, list):
            raise ValueError("LLM output is not a list")

        return plan

    except Exception as e:
        print(f"[analysis_planner] ERROR: {e}")

        #  Safe fallback
        return ["distribution", "comparison", "correlation"]


def validate_plan(plan: list[str], context: DataContext) -> list[str]:
    valid_plan = []

    for item in plan:
        if item == "time_series" and not context.datetime_columns:
            continue

        if item == "correlation" and len(context.numeric_columns) < 2:
            continue

        if item == "comparison" and (
            len(context.categorical_columns) < 1 or len(context.numeric_columns) < 1
        ):
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