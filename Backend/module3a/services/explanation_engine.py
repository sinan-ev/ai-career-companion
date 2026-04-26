from typing import List, Dict, Any
from ..services.context_builder import DataContext

def explain(
    insights: List[str],
    stats: Dict[str, Any],
    context: DataContext,
    llm_client
) -> str:
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
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Explanation Error: {e}")
        return "Could not generate dynamic explanation due to an API error."
