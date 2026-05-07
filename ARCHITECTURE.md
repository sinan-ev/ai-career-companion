# Technical Architecture & Data Flow

This document details the internal logic and "brain" of the Data Intelligence Agent.

## 🧠 The Multi-Module Pipeline

The system processes data in three distinct phases to ensure human interpretability, machine readiness, and interactive AI analysis.

### Module 1: Data Understanding
**Goal**: Translate machine data (columns/rows) into a human business context.
1.  **Normalization**: Detects "disguised" nulls (e.g., "N/A", "-999", "?") and converts them to standard NaNs.
2.  **Hybrid Schema Detection**: Classifies columns (Numeric, Categorical, Datetime) and identifies potential "Unknown" types.
3.  **Column Intelligence**: If a column name is cryptic (e.g., `cnt_v1`), the LLM analyzes sample values to explain it.
4.  **Domain Detection**: Heuristics identify if the data is about Sales, HR, Healthcare, etc.
5.  **AI Summary**: Generates a 3-5 paragraph "Narrative" of what the dataset represents.

### Module 2: Intelligent Preprocessing
**Goal**: Transform raw data into structured artifacts for Machine Learning.
1.  **Deep EDA**: Calculates skewness, outlier percentages, and high-correlation pairs.
2.  **The Agent Planner**: We feed the EDA report and Module 1 summary into a Groq LLM. The agent returns a JSON plan.
3.  **Rule Engine**: Executes the agent's plan in a strict "Canonical Order" to prevent data leakage.
4.  **Target Detection**: Uses AI to guess which column is the "Target" (label).
5.  **Artifact Manager**: Saves trained encoders and scalers.

### Module 3A: AI Analyst & Dashboard (v2.0.1)
**Goal**: Provide an interactive analytics interface backed by a RAG conversational agent.
1.  **RAG Vector Store**: Converts the deep EDA and Module 1 summary into vector embeddings using `vector_store.py`.
2.  **Chart Engine**: Uses `llama-3.1-8b-instant` to generate a JSON configuration for 5-6 Plotly-compatible business charts.
3.  **Insights Engine**: Parallelized execution alongside chart generation to summarize data trends without UI lag.
4.  **Strict Persona Chatbot**: A chat endpoint that uses strict prompting to eliminate technical jargon, relying on the RAG context to answer user queries about their data.

## 🔄 Data Flow Diagram

```mermaid
graph TD
    A[User Upload] --> B[FastAPI Backend]
    B --> C{Module 1: Understand}
    C --> D[Module 1 Output]
    
    D --> E{Module 2: Engineer}
    E --> E1[Deep EDA & Planning]
    E1 --> E4[Dataset Builder]
    E4 --> F[Analytics CSV & ML CSV]
    
    E1 --> M3{Module 3A: AI Analyst}
    D --> M3
    M3 --> V[Vector Store / RAG]
    M3 --> CE[Chart Generation JSON]
    M3 --> IE[Parallel Insights]
    
    V --> CB[Persona-based Chatbot]
    
    F --> I[React Dashboard]
    CE --> I
    IE --> I
    CB --> I
```

## 🛠 Advanced Features

### Smart Target Detection
The system scans meaning keywords, the AI summary, and falls back to standard conventions.

### The Memory System
Module 2 includes a `PipelineMemory` class that tracks the success, failure, and duration of every step.

### Parallelized Execution & Rate Limit Handling
Module 3A is optimized for speed. Chart generation and insights are processed asynchronously, avoiding UI lag. Complex sequences of LLM requests are managed to prevent hitting API rate limits.

---
*Architecture documentation v2.0.1*
