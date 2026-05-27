# Architectural Review of Agentic AI Implementation

This report details how **Agentic AI** is implemented within the **AI Career Companion / Decision Intelligence Platform** codebase. The platform leverages multiple autonomous agent design patterns, including **reflective feedback loops**, **hierarchical validation guardrails**, and **sequential state-machine workflows**.

---

## 🗺️ High-Level Agentic Map
Agentic logic is decoupled across three modules:

1. **Module 2 (Pre-ML)**: Generates cleaning and preprocessing tasks using an LLM Planner.
2. **Module 3 (Analytics & RAG)**: Features a **4-Agent Charting Loop** and a **Multi-Stage Chat Validator** (incorporating LLM-as-a-Judge and Self-Reflection).
3. **Module 4 (Strategic Recommendations)**: Coordinated by **LangGraph** using a sequential chain of 7 specialized analysis and evaluation agents.

---

## 📊 Module-by-Module Agentic Architectures

### 1. The 4-Agent Charting Loop (`module3/services/chart_engine.py`)
This engine automates dashboard creation through a collaborative, multi-agent process sharing an `AgentScratchpad` and running a critique-and-refine feedback loop:

* **Scout Agent** (`scout_agent`): 
  Profiles the raw pandas `DataFrame`. It calculates data types, missing value percentages, value counts, and flags high-cardinality columns as likely ID fields.
* **Planner Agent** (`planner_agent`):
  Uses an LLM prompt (`PLANNER_SYSTEM`) along with Scout's metrics to design 5-6 business-critical charts (scatter, bar, line, histogram). It outputs structured JSON.
* **Critic Agent** (`critic_agent`):
  Acts as an in-memory validator. It checks the generated chart configurations against the actual columns, types, and constraints. If the Planner attempted an invalid operation (e.g. aggregating a categorical string), the Critic automatically repairs it or requests a redraw.
* **Builder Agent** (`builder_agent`):
  Takes the validated configurations, executes the pandas groupings/aggregations, and constructs Plotly-compatible figures for the frontend.

```
       ┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
       │ Scout Agent │────▶│ Planner Agent│────▶│ Critic Agent │────▶│ Build Agent │
       │ (explores   │     │ (designs 5-6 │     │ (validates & │     │ (executes & │
       │  the data)  │     │  chart specs)│     │  improves)   │     │  returns)   │
       └─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
             │                                         │
             └─────────────── scratchpad ──────────────┘
```

---

### 2. Multi-Stage Chat Validation & Guardrails (`module3/services/chat_engine.py` & `validation_engine.py`)
When a user asks a question, the request goes through a strict agentic guardrail system before returning an answer:

1. **Input Validation**: Evaluates the prompt for safety, injection attempts, and SQL/DDL keywords.
2. **Retrieval Validation**: Measures RAG cosine similarity scores. If similarity falls below `0.7`, it bypasses the knowledge base context to prevent irrelevant responses.
3. **Context Validation**: Filters out redundant or too-short document chunks.
4. **Tool/Action Validation**: Verifies that any pandas calculations ran successfully without errors.
5. **Generation Validation (LLM-as-a-Judge)**: A separate LLM call evaluates the relevance, completeness, and clarity of the draft response (scoring it from 1 to 10).
6. **Faithfulness Validation**: Checks whether the answer is strictly grounded in the context to prevent LLM hallucinations.
7. **Critic Agent (Self-Reflection)**: Inspects the draft for technical jargon (SQL, database schemas, code, or query mentions) and rejects it if present.
8. **Confidence Scoring**: Combines Retrieval, Generation, and Faithfulness scores into a single metric. If confidence is below `0.4`, it triggers a fallback response.
9. **Refinement Loop**: If the Critic rejects the response, it appends feedback and runs a retry loop to rewrite the answer.

---

### 3. LangGraph Orchestration (`module4/agents/agent_graph.py` & `agent_definitions.py`)
For ML forecasting and strategic recommendations, the platform compiles a sequential state machine (`StateGraph`) using **LangGraph**:

```
START ──▶ PredictionAgent ──▶ ForecastAgent ──▶ RCAAgent ──▶ RiskAgent ──▶ RecommendAgent ──▶ DecisionAgent ──▶ EvalAgent ──▶ ReportNode ──▶ END
```

Each step updates a shared `AgentState` typed dictionary:

* **Prediction Agent**: Trains AutoML classifiers/regressors and evaluates predictions.
* **Forecast Agent**: Implements an ensemble model of AutoARIMA and Facebook Prophet.
* **RCA Agent**: Runs SHAP-based feature importance calculations to find root causes.
* **Risk Agent**: Utilizes Isolation Forest rules to flag anomalous records.
* **Recommend Agent**: Evaluates the findings of preceding nodes and produces ranked actionable recommendations.
* **Decision Agent**: Synthesizes predicted models, forecasts, and risks into an executive decree.
* **Eval Agent**: Combines the confidence scores of all previous agents using a weighted average:
  $$\text{Confidence} = 0.25P + 0.15F + 0.20RCA + 0.15Risk + 0.15Rec + 0.10Dec$$
  It identifies and reports the "limiting bottleneck factor" (the weakest engine).
* **Report Node**: Triggers the `ReportGenerator` to compile the shared state into a unified markdown executive report.
