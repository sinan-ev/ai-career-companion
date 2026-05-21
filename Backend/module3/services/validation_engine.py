import re
import json


# User Query
#    ↓
# Input Validation
#    ↓
# RAG Retrieval
#    ↓
# Retrieval Validation
#    ↓
# Context Validation
#    ↓
# LLM Generates Answer
#    ↓
# Generation Validation
#    ↓
# Faithfulness Validation
#    ↓
# Critic Agent Review
#    ↓
# Confidence Score
#    ↓
# Final Answer


class ValidationEngine:
    """
    A validation engine designed to enforce safety, alignment, groundedness, and quality
    across different steps of the RAG and analysis generation pipeline.
    """
    def __init__(self, llm_client=None):
        """
        Initializes the ValidationEngine with an optional LLM client.

        Args:
            llm_client (optional): The language model client. Defaults to None.
        """
        self.llm_client = llm_client
        from module1.config import get_settings
        self.model = get_settings().groq_model

    # 1. INPUT VALIDATION
    def validate_input(self, query: str) -> bool:
        """
        Validates user query input to detect unsafe keywords, prompt injection, or too short queries.

        Args:
            query (str): The user's question or input prompt.

        Returns:
            bool: True if input is safe and valid, False otherwise.
        """
        if not query or not query.strip():
            return False
        
        # Simple heuristic for unsafe/ambiguous queries
        unsafe_keywords = ["drop table", "delete from", "ignore previous", "system prompt"]
        query_lower = query.lower()
        if any(kw in query_lower for kw in unsafe_keywords):
            return False
            
        if len(query.strip()) < 3: # Ambiguous or too short
            return False
            
        return True

    # 2. RETRIEVAL VALIDATION
    def validate_retrieval(self, chunk_scores: list) -> float:
        """
        Validates similarity scores of retrieved context chunks to detect weak matching.

        Args:
            chunk_scores (list): List of similarity search results with score details.

        Returns:
            float: The maximum similarity score detected, or 0.0 if empty or below threshold.
        """
        if not chunk_scores:
            return 0.0
            
        max_similarity = max([score for _, score in chunk_scores])
        if max_similarity < 0.7:
            return 0.0 # Fallback trigger
            
        return max_similarity

    # 3. CONTEXT VALIDATION
    def validate_context(self, chunks: list) -> list:
        """
        De-duplicates and purges extremely short, uninformative text chunks from retrieved documents.

        Args:
            chunks (list): Raw text chunks.

        Returns:
            list: List of refined, unique, high-quality text chunks.
        """
        # Minimum document count check & redundancy removal
        unique_chunks = list(set(chunks))
        if len(unique_chunks) == 0:
            return []
        
        # Filter extremely short non-informative chunks
        clean_chunks = [c for c in unique_chunks if len(c.strip()) > 10]
        return clean_chunks

    # 4. TOOL / ACTION VALIDATION
    def validate_tool_action(self, tool_name: str, params: dict, output: any) -> bool:
        """
        Checks if a tool executed correctly without raising explicit errors in the output data.

        Args:
            tool_name (str): Name of the tool.
            params (dict): Parameters passed to the tool.
            output (any): Returned execution output of the tool.

        Returns:
            bool: True if the tool executed successfully and safely, False otherwise.
        """
        if not tool_name or not output:
            return False
        if tool_name == "pandas_calc" and "error" in str(output).lower():
            return False
        return True

    # 5. GENERATION VALIDATION (LLM-as-a-Judge)
    def validate_generation(self, query: str, answer: str) -> float:
        """
        Evaluates relevance, completeness, and clarity of the generated LLM response using LLM-as-a-judge.

        Args:
            query (str): Original user query.
            answer (str): The generated response.

        Returns:
            float: Evaluation score from 1.0 to 10.0.
        """
        if not self.llm_client:
            return 8.0 # Default if no LLM
            
        prompt = f"""
        Evaluate the following answer to the user query.
        Query: {query}
        Answer: {answer}
        
        Rate the relevance, completeness, and clarity on a scale of 1 to 10.
        Return ONLY a JSON object with a 'score' key. Example: {{"score": 8.5}}
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return float(result.get("score", 5.0))
        except:
            return 5.0

    # 6. FAITHFULNESS VALIDATION
    def validate_faithfulness(self, answer: str, context: str) -> float:
        """
        Checks if the generated answer is strictly grounded in the provided RAG context, to prevent hallucination.

        Args:
            answer (str): Generated answer.
            context (str): Input RAG context string.

        Returns:
            float: Grounded score (1.0 for true, 0.0 for false, 0.5 on exception).
        """
        if not self.llm_client:
            return 1.0 # 1.0 = Grounded
            
        prompt = f"""
        Is the following answer grounded strictly in the provided context?
        Context: {context[:1000]}...
        Answer: {answer}
        
        Return ONLY a JSON object with a 'grounded' boolean key. Example: {{"grounded": true}}
        """
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return 1.0 if result.get("grounded", False) else 0.0
        except:
            return 0.5

    # 7. CRITIC AGENT (Self-Reflection)
    def critic_agent(self, query: str, answer: str, context: str) -> dict:
        """
        Critiques the answer for technical jargon (SQL, Python), logical fallacies, or alignment issues, and suggests improvements.

        Args:
            query (str): User query.
            answer (str): Candidate answer.
            context (str): Context text.

        Returns:
            dict: Evaluation result with keys 'approved', 'feedback', and 'improved_answer'.
        """
        if not self.llm_client:
            return {"approved": True, "feedback": "System LLM offline", "improved_answer": answer}
            
        prompt = f"""
        Act as a strict AI critic. Review this answer for logical errors, missing points, or weak explanations based on the context.
        CRITICAL RULE: If the answer contains ANY SQL, Python code, markdown tables, or mentions words like "query" or "database", you MUST REJECT IT (set "approved": false) and tell it to remove the technical jargon.
        
        Context: {context[:1000]}...
        Query: {query}
        Answer: {answer}
        
        Return a JSON object with:
        - "approved": boolean (true if good, false if it contains code/SQL or is wrong)
        - "feedback": string (what to fix, especially if it contains SQL)
        - "improved_answer": string (a better version of the answer with NO SQL/code)
        """
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"approved": True, "feedback": f"Critic error: {e}", "improved_answer": answer}

    # 8. CONFIDENCE SCORING
    def calculate_confidence(self, retrieval_score: float, generation_score: float, faithfulness: float) -> float:
        """
        Aggregates retrieval validation, generation validation, and faithfulness scores into a unified confidence metric.

        Args:
            retrieval_score (float): Score from validate_retrieval.
            generation_score (float): Score from validate_generation.
            faithfulness (float): Score from validate_faithfulness.

        Returns:
            float: Aggregated confidence score rounded to 2 decimal places.
        """
        # Normalize generation score (0-10) to (0-1)
        gen_norm = generation_score / 10.0
        # Average the three signals
        confidence = (retrieval_score + gen_norm + faithfulness) / 3.0
        return round(confidence, 2)
