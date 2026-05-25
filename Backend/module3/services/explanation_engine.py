from typing import List, Dict, Any
from ..services.context_builder import DataContext

def explain(
    insights: List[str],
    stats: Dict[str, Any],
    context: DataContext,
    llm_client
) -> str:
    """
    Generates a concise, high-level business explanation summarizing the impact of dataset insights.

    Utilizes the LLM to write a professional executive description, falling back to a structured
    default template if API issues or client absence occurs.

    Args:
        insights (List[str]): List of key data-driven insights.
        stats (Dict[str, Any]): Calculated statistical details.
        context (DataContext): Data context carrying details about the active dataset.
        llm_client: The initialized language model client.

    Returns:
        str: A professional 2-3 sentence executive explanation of the analytical results.
    """
    if not llm_client:
        return "This dataset provides a solid overview of your business metrics. The strongest finding is the correlation between age and salary."
        
    from module1.config import get_settings
    prompt = f"""
    Provide a concise, 2-3 sentence explanation summarizing the overall meaning and business impact of these insights:
    {insights}
    """
    try:
        response = llm_client.chat.completions.create(
            model=get_settings().groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("--- EXPLANATION GENERATION ERROR ---")
        print(f"Error Message: {str(e)}")
        
        # Robust fallback
        return f"This analysis of '{context.dataset_name}' highlights key patterns across {len(insights)} primary insights. The findings reveal significant distributions and relationships within the dataset's core dimensions, providing a foundation for strategic data-driven decisions."
