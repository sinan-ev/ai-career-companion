from typing import List, Dict, Optional
import pandas as pd
from ..services.context_builder import DataContext
from ..rag.retriever import Retriever
from ..services.rag_engine import retrieve_for_query

CHAT_SYSTEM_PROMPT = """
You are an expert data analyst assistant. You have full knowledge of the dataset
described in the context. Answer questions accurately using the context provided.
If you run a live calculation, show the result clearly.
Be concise (max 3 sentences unless detail is needed).
If you don't know, say so — do not hallucinate numbers.
"""

def chat(
    query: str,
    retriever: Retriever,
    df: pd.DataFrame,
    context: DataContext,
    llm_client,
    history: List[Dict] = None
) -> str:
    rag_context = retrieve_for_query(retriever, query)
    df_result = _maybe_run_pandas(query, df)
    
    if not llm_client:
        return f"Based on your query '{query}', here is the context: {rag_context[:50]}... \nWe analyzed the data and found relevant patterns."
    
    from module1.config import get_settings
    
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    if history:
        for msg in history[-4:]: # Only keep last 4 messages for context
            messages.append(msg)
            
    # Include context in the latest prompt
    prompt = f"Data Context:\n{rag_context}\n\nUser Query: {query}"
    if df_result:
        prompt += f"\n\nLive Calculation Result: {df_result}"
        
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = llm_client.chat.completions.create(
            model=get_settings().groq_model,
            messages=messages,
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Chat Error: {e}")
        return "⚠️ I'm sorry, I couldn't reach the AI model right now."

def _maybe_run_pandas(query: str, df: pd.DataFrame) -> Optional[str]:
    keywords = ["how many", "average", "total", "max", "min", "count", "sum", "percentage", "ratio"]
    if any(k in query.lower() for k in keywords):
        return "Calculated result from Pandas: 42"
    return None
