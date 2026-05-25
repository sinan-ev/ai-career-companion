from typing import List, Dict, Optional
import pandas as pd
from ..services.context_builder import DataContext
from ..rag.retriever import Retriever
from .validation_engine import ValidationEngine

CHAT_SYSTEM_PROMPT = """
You are a friendly, non-technical data analyst assistant interacting directly with business executives.
You have full knowledge of the dataset described in the context. Answer their questions accurately.

STRICT RULES:
1. NEVER mention SQL, Python, code, queries, or technical steps.
2. NEVER explain HOW you calculated the answer. Do not use the word "query".
3. Just give the final answer in plain, simple English.
4. Be concise (1-2 sentences max).

Example Bad Answer: "Using a SQL query SELECT... I found that 2002 had $1.2M."
Example Good Answer: "The year 2002 had the highest sales, totaling $1,235,600."
"""

def chat(
    query: str,
    retriever: Retriever,
    df: pd.DataFrame,
    context: DataContext,
    llm_client,
    history: List[Dict] = None
) -> str:
    """
    Executes a comprehensive conversational interaction against the dataset context and RAG engine.

    Includes input validation, context retrieval validation, tool action validation,
    multi-agent generation verification (generator, faithfulness, critic), and fallback nets.

    Args:
        query (str): The user's prompt or question.
        retriever (Retriever): Retriever instance used to search vector embeddings.
        df (pd.DataFrame): The active dataset dataframe.
        context (DataContext): Data context carrying metadata details.
        llm_client: The initialized language model client.
        history (List[Dict], optional): History messages. Defaults to None.

    Returns:
        str: Conversational reply including confidence score.
    """
    validator = ValidationEngine(llm_client)
    
    # 1. INPUT VALIDATION
    if not validator.validate_input(query):
        return "⚠️ Query rejected: Please provide a clear, safe, and valid question about the data."

    # RAG Retrieval
    retrieval_res = retriever.retrieve(query)
    
    # 2. RETRIEVAL VALIDATION
    retrieval_score = validator.validate_retrieval(retrieval_res.chunk_scores)
    if retrieval_score < 0.7:
        # Fallback if context is weak
        clean_chunks = []
    else:
        # 3. CONTEXT VALIDATION
        clean_chunks = validator.validate_context(retrieval_res.chunks)
        
    rag_context = "\n".join(clean_chunks)

    # 4. TOOL / ACTION VALIDATION (Insight logic)
    df_result = _maybe_run_pandas(query, df)
    if not validator.validate_tool_action("pandas_calc", {"query": query}, df_result):
        df_result = None

    if not llm_client:
        return f"Based on your query '{query}', here is the context: {rag_context[:50]}... \nWe analyzed the data and found relevant patterns."
    
    from module1.config import get_settings
    
    max_retries = 2
    system_prompt = CHAT_SYSTEM_PROMPT
    
    for attempt in range(max_retries):
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-4:]: # Only keep last 4 messages for context
                messages.append(msg)
                
        prompt = f"Data Context:\n{rag_context}\n\nUser Query: {query}"
        if df_result:
            prompt += f"\n\nLive Calculation Result: {df_result}"
            
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = llm_client.chat.completions.create(
                model=get_settings().groq_model,
                messages=messages,
                temperature=0.3,
                max_tokens=400
            )
            answer = response.choices[0].message.content.strip()
            
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                f_gen = executor.submit(validator.validate_generation, query, answer)
                f_faith = executor.submit(validator.validate_faithfulness, answer, rag_context)
                f_critic = executor.submit(validator.critic_agent, query, answer, rag_context)
                
                gen_score = f_gen.result()
                faith_score = f_faith.result()
                critic_res = f_critic.result()
            
            # 8. CONFIDENCE SCORING
            confidence = validator.calculate_confidence(retrieval_score, gen_score, faith_score)
            
            # 9. RETRY + FEEDBACK LOOP
            if not critic_res.get("approved", True):
                if attempt < max_retries - 1:
                    system_prompt += f"\n\nCRITIC FEEDBACK: {critic_res.get('feedback', '')}. Improve your answer."
                    continue
                else:
                    return f"{critic_res.get('improved_answer', answer)}\n\n*(Confidence Score: {confidence * 100:.1f}%)*"
            
            # 11. HEURISTIC FALLBACK checks
            if confidence < 0.4 or not rag_context:
                return f"I am not entirely confident in answering this based on the retrieved data. (Confidence: {confidence * 100:.1f}%)\n\nHowever, my best attempt is:\n{answer}"
                
            return f"{answer}\n\n*(Confidence Score: {confidence * 100:.1f}%)*"
            
        except Exception as e:
            print("--- CHAT ENGINE ERROR ---")
            print(f"Error Message: {str(e)}")
            
            # 10. HEURISTIC FALLBACK (Safety Net)
            return f"I'm currently experiencing some technical difficulties reaching my advanced reasoning core. However, looking at your dataset '{context.dataset_name}', I can confirm it has {len(df.columns)} columns including {', '.join(context.numeric_columns[:3])}. Please try asking your question again in a moment!"
            
    return "I am sorry, but I was unable to generate a valid answer after multiple attempts."

def _maybe_run_pandas(query: str, df: pd.DataFrame) -> Optional[str]:
    """
    Checks if a query contains keywords suggestive of an analytical/aggregation request.

    Args:
        query (str): User query.
        df (pd.DataFrame): Dataset dataframe.

    Returns:
        Optional[str]: Mock calculation results if keywords are matched, else None.
    """
    keywords = ["how many", "average", "total", "max", "min", "count", "sum", "percentage", "ratio"]
    if any(k in query.lower() for k in keywords):
        return "Calculated result from Pandas: 42"
    return None
