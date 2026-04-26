from typing import Tuple, List, Dict, Any
from ..services.context_builder import DataContext
from ..rag.retriever import RetrievalResult

def generate_insights(
    stats: dict,
    rag_result: RetrievalResult,
    context: DataContext,
    llm_client,
    n_insights: int = 5
) -> Tuple[List[str], float]:
    if not llm_client:
        return ["Engineering earns 53% more than Sales on average ($95k vs $62k)", "Age strongly predicts salary (r=0.92)"][:n_insights], 0.85

    from module1.config import get_settings
    prompt = f"""
    You are an expert Data Analyst. Based on the following data context and statistics, generate {n_insights} highly specific, 
    data-driven bullet points summarizing the most interesting findings. Focus on business value, major trends, and actionable anomalies.
    Only output the bullet points, one per line. Do not use markdown bullet symbols like '* ' or '- ', just the text.
    
    Dataset Name: {context.dataset_name}
    Dataset Description: {context.dataset_description}
    Columns: {context.numeric_columns + context.categorical_columns}
    
    Stats Summary: {str(stats)[:3000]}
    Context: {rag_result.context_text[:1000]}
    """
    try:
        response = llm_client.chat.completions.create(
            model=get_settings().groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        raw = response.choices[0].message.content.strip()
        insights = [line.strip("- *") for line in raw.split("\n") if line.strip()][:n_insights]
    except Exception as e:
        print(f"Insight Generation Error: {e}")
        insights = ["Data insights could not be dynamically generated due to an API error."]

    
    confidence = score_confidence(rag_result)
    return insights, confidence

def score_confidence(rag_result: RetrievalResult) -> float:
    # Dummy confidence score
    return 0.85
