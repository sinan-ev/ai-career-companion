# Backend Documentation — Module 3 & Module 4

---

## MODULE 3 — Analysis, Charts, Insights & Chat

**Purpose:** Takes the cleaned dataset from Module 2 and produces business intelligence: charts, insights, a natural-language explanation, and an interactive chat interface.

---

### `module3/config.py`
Flat config file (not Pydantic). Reads env vars directly:
- `LLM_PROVIDER` / `LLM_MODEL` — which LLM to use (default: groq / llama-3.1-8b-instant)
- `GROQ_API_KEY` — shared key
- `EMBEDDING_BACKEND` — "auto" selects mock embedder
- `VECTOR_STORE_PATH` — where to persist vector store (default: `./data/vector_store`)

---

### `module3/core/pipeline.py` — `run_module3()`

**The Module 3 orchestrator.** Called from `main.py` after Module 2 completes.

```
Step 1: get_groq_client()              → shared LLM client
Step 2: build_context(m1, m2)          → DataContext dataclass
Step 3: build_rag(context)             → VectorStore + Retriever
Step 4: generate_plan(context, llm)    → list of analysis types
Step 5: validate_plan(plan, context)   → remove infeasible steps
Step 6: run_analysis(plan, df, ctx)    → real statistical calculations
Step 7: retrieve_for_plan(retriever)   → RAG context chunks
Step 8: generate_charts(...)           → 5-6 Plotly-compatible charts
Step 9: generate_insights(...)         → 5 bullet-point findings
Step 10: explain(insights, ...)        → 2-3 sentence executive summary
Step 11: chat(user_query, ...)         → conversational answer
Step 12: Return Module3Result          → packed Pydantic response
```

**Input:** `module1_output dict`, `module2_output dict`, `df: DataFrame`, `user_query: str`  
**Output:** `Module3Result` with `charts`, `insights`, `explanations`, `stats`, `chat_response`, `confidence_score`, `rag_context`, `dataset_summary`

---

### `module3/services/context_builder.py` — `DataContext`

Merges Module 1 + Module 2 outputs into a clean `DataContext` dataclass:
```python
@dataclass
class DataContext:
    dataset_name: str
    dataset_description: str
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    column_meanings: Dict[str, str]
```

`get_context_chunks(context)` — splits DataContext into text chunks for embedding:
```
["Dataset Name: Titanic",
 "Description: Passenger survival data...",
 "Column 'Age': Age of passenger in years",
 ...]
```
These chunks go into the vector store so the RAG system can retrieve relevant facts for any query.

---

### `module3/rag/` — RAG Layer (3 files)

**`embedding.py` — `Embedder`**
- `embed_documents(texts)` → returns list of 128-dim random vectors (mock)
- `embed_query(text)` → returns single 128-dim random vector
- *Why mock?* Real embedding APIs (OpenAI, Cohere) have cost and latency. The mock keeps the RAG pipeline functional without external dependencies. Swap this with `OpenAIEmbeddings()` for production.

**`vector_store.py` — `VectorStore`**
- `add_texts(texts)` → embeds + stores documents in memory list
- `similarity_search(query, k=3)` → returns top-k documents with mock score 0.85
- Stored as two parallel lists: `self.documents[]` and `self.embeddings[]`

**`retriever.py` — `Retriever` + `RetrievalResult`**
- `retrieve(query)` → calls `vector_store.similarity_search(query)` → returns `RetrievalResult`
- `RetrievalResult` has: `context_text` (joined chunks), `chunks` (list), `chunk_scores` (list of tuples)

---

### `module3/services/rag_engine.py`

| Function | What it does |
|---|---|
| `build_rag(context)` | Creates Embedder → VectorStore → adds context chunks → wraps in Retriever |
| `retrieve_for_query(retriever, query)` | Single query → returns context_text string |
| `retrieve_for_plan(retriever, plan)` | Multiple queries → deduplicates chunks → returns combined RetrievalResult |

`plan_to_queries()` maps short step names to natural-language search queries:
```python
"correlation" → "correlations between numeric columns"
"trend"       → "trend patterns over time in this dataset"
"distribution"→ "data distribution statistics outliers"
```

---

### `module3/services/analysis_planner.py`

**`generate_plan(context, llm_client)` → `List[str]`**
- Loads `module3/prompts/analysis_prompt.txt`
- Injects dataset context → calls LLM → parses JSON array
- Fallback if LLM fails: `["distribution", "comparison", "correlation"]`
- Handles both formats: `["trend", ...]` and `{"plan": ["trend", ...]}`

**`validate_plan(plan, context)` — removes infeasible steps:**
```python
"time_series" removed if no datetime_columns
"correlation" removed if fewer than 2 numeric columns
"comparison"  removed if no categorical OR no numeric columns
```

---

### `module3/services/stats_engine.py` — `run_analysis()`

**Real statistical calculations — no AI guessing.**
- **Distributions:** `df[col].describe()` for each meaningful numeric column (skips ID-like cols)
- **Correlations:** `df[numeric_cols].corr()` → Pearson correlation matrix
- **Comparisons:** `df.groupby(cat_col)[num_col].agg(['mean','sum'])` for top 3 cat × top 3 num combinations

Returns dict with keys: `distributions`, `correlations`, `comparisons`

---

### `module3/services/chart_engine.py` — 4-Agent Architecture

**The most complex Module 3 component.** Uses 4 autonomous agents with a shared `AgentScratchpad`.

```
Scout Agent   → profiles all columns → fills scratchpad.column_stats
     ↓
Planner Agent → LLM designs 5-6 chart specs → fills scratchpad.chart_plan
     ↓
Critic Agent  → validates specs against real df → auto-repairs bad configs
     ↓
Builder Agent → executes specs → produces Plotly-compatible JSON
```

**`AgentScratchpad`** — shared state between agents:
- `column_stats` — dtype, nulls, min/max/mean/std, top_values, likely_id flag
- `chart_plan` — list of chart spec dicts from Planner
- `critique` — issues found by Critic (fed back to Planner on retry)
- `charts` — final built charts
- `iterations` — current loop count
- `log` — full event trace

**Critic auto-repairs (no re-planning needed for soft issues):**
- `y_col` not in df → switch to `COUNT`
- Categorical `y_col` with `sum/mean` agg → switch to `COUNT`
- `histogram` with categorical `x_col` → switch to `bar/COUNT`

**Planner-Critic loop:** Max 2 iterations. If Critic finds critical column-not-found errors → Planner reruns with critique feedback. If Builder produces nothing → heuristic fallback.

**Chart types produced:** `bar`, `line`, `horizontal_bar`, `histogram`, `scatter`

---

### `module3/services/insight_engine.py` — `generate_insights()`

- Sends stats + RAG context to LLM
- Asks for exactly N data-driven bullet points (no bullets, no markdown)
- Strips common bullet chars (`-`, `*`, `•`) from response
- Fallback: 5 generic but context-aware sentences using `context.dataset_name`
- `score_confidence(rag_result)` → returns 0.85 (mock; replace with real chunk-score analysis)

---

### `module3/services/chat_engine.py` — `chat()`

**Multi-layered conversational interface with validation pipeline.**

```
1. validate_input(query)            → reject empty/unsafe queries
2. retriever.retrieve(query)        → RAG lookup
3. validate_retrieval(chunk_scores) → if score < 0.7, use empty context
4. validate_context(chunks)         → clean retrieved chunks
5. _maybe_run_pandas(query, df)     → if query has aggregation keywords → mock calc result
6. LLM call with system + history + context + pandas result
7. Parallel validation (ThreadPoolExecutor):
   - validate_generation(query, answer)    → relevance check
   - validate_faithfulness(answer, context)→ grounding check
   - critic_agent(query, answer, context)  → quality + improve if needed
8. calculate_confidence(retrieval, generation, faithfulness scores)
9. If confidence < 0.4 → warn user
10. Return answer + "(Confidence Score: XX%)"
```

**`CHAT_SYSTEM_PROMPT`** strictly forbids mentioning SQL, Python, or technical steps — answers must be plain business English in 1-2 sentences.

---

### `module3/services/explanation_engine.py` — `explain()`

Simple LLM call: given the 5 insights, write a 2-3 sentence executive summary of business impact.  
Fallback: a template string using `context.dataset_name` and `len(insights)`.

---

## MODULE 4 — AutoML, Forecasting, RCA, Risk & Decisions

**Purpose:** Advanced AI analytics — train ML models, forecast time series, explain root causes, detect anomalies, generate recommendations, synthesise a strategic decision.

**Architecture:** 7 autonomous agents orchestrated via **LangGraph** `StateGraph`.

---

### `module4/agents/agent_graph.py` — `build_graph()`

**The LangGraph workflow definition.**

```
AgentState (TypedDict) — shared dict passed through every node:
  data, target_column, date_column, problem, job_id
  prediction_result, forecast_result, rca_result, risk_result
  recommendation_result, decision_result, overall_confidence
  final_report, errors

Graph edge sequence:
START → prediction → forecast → rca → risk → recommend → decision → eval → report → END
```

Each node is a lambda wrapping the agent's `.run(state)` method. State is passed by reference — each agent adds its result key and returns the same dict.

`PIPELINE = build_graph()` — compiled once at import time, reused for every API call.

---

### `module4/agents/agent_definitions.py` — 7 Agent Classes

All extend `BaseAgent` which defines `run(state) → state`.

| Agent | Engine called | State key written |
|---|---|---|
| `PredictionAgent` | `PredictionEngine.train_and_predict()` | `prediction_result` |
| `ForecastAgent` | `ForecastingEngine.forecast()` | `forecast_result` |
| `RCAAgent` | `RCAEngine.analyse()` | `rca_result` |
| `RiskAgent` | `RiskEngine.detect()` | `risk_result` |
| `RecommendAgent` | `RecommendationEngine.recommend()` | `recommendation_result` |
| `DecisionAgent` | `DecisionEngine.decide()` | `decision_result` |
| `EvalAgent` | weighted average calculation | `overall_confidence` |

**EvalAgent confidence weights:**
```python
prediction    × 0.25   (most important)
rca           × 0.20
forecast      × 0.15
risk          × 0.15
recommendation× 0.15
decision      × 0.10
```
`limiting_factor` = the engine with the lowest score → shown in explanation.

---

### `module4/engines/prediction_engine.py` — `PredictionEngine`

**AutoML pipeline — automatically selects best model.**

```
1. route_data(data) → DataFrame
2. detect_task_type(y) → "classification" or "regression"
   - classification: object dtype OR ≤10 unique vals with <5% cardinality ratio
3. Auto-detect target_column if not provided (keyword priority: target, label, churn, price...)
4. Domain detection from column names (Titanic, Iris, HR, Healthcare, Sales...)
5. Feature filtering: select_dtypes(number), fill NaN with median
6. Dynamic CV strategy:
   - classification: StratifiedKFold(n_splits=min(5, min_class_count))
   - regression: 5-fold or len(train) if tiny
7. Candidate models tested with cross_val_score:
   - Classification: LGBM, RandomForest, XGBoost, LogisticRegression, DecisionTree
   - Regression: LGBM, XGBoost, RandomForest, Ridge
8. Best model selected by CV score
9. CalibratedClassifierCV wraps best classifier (sigmoid calibration)
10. Final fit on full train set, predict on test set
11. Metrics: accuracy+F1 (classification) or MAE+RMSE+R² (regression)
12. LLM call → business_summary in plain English
13. _compute_confidence():
    - classification: mean(max predict_proba) across test set
    - regression: 1 - (mean_residual / target_std)
```

**Fallback:** If all CV attempts fail → LogisticRegression or Ridge fitted directly.

---

### `module4/engines/forecasting_engine.py` — `ForecastingEngine`

**Prophet + ARIMA ensemble time-series forecaster.**

```
1. Parse date_col → sort by date → infer frequency (MS, D, W, etc.)
2. Train/validation split: last 20% is validation
3. Prophet on train data → predict validation → compute prophet_mae
4. auto_arima on train data → predict validation → compute arima_mae
5. Ensemble weights = inverse MAE (better model gets higher weight):
   w_prophet = (1/prophet_mae) / total_w
   w_arima   = (1/arima_mae)  / total_w
6. Refit both on FULL data
7. For each future period:
   ens_value = prophet_yhat × w_prophet + arima_yhat × w_arima
   ens_lower = prophet_lower × w_prophet + arima_lower × w_arima
   ens_upper = prophet_upper × w_prophet + arima_upper × w_arima
8. Trend: mean_forecast vs last_3_actual mean
   >+2% → "upward", <-2% → "downward", else → "stable"
9. _compute_confidence():
   model_agreement = 1 - |prophet_mae - arima_mae| / max_mae
   interval_penalty = mean(interval_widths) / mean_forecast
   score = agreement × 0.6 + (1 - penalty) × 0.4
```

---

### `module4/engines/rca_agent.py` — `RCAAgent`

**SHAP-based root cause analysis using LightGBM.**

```
1. route_data(data) → df
2. Label-encode all categoricals, fill NaN with median
3. Detect task: classification (≤10 unique y) or regression
4. Fit LGBMClassifier or LGBMRegressor on full data
5. Run SHAP TreeExplainer on 3 data subsets (0.7×, 0.7×, full):
   - Computes mean |SHAP| per feature per subset
6. mean_importance = average across 3 subsets
   std_importance  = std across 3 subsets
7. Top 5 features selected, each annotated with:
   - direction ("increases"/"decreases"/"influences")
   - impact ("high"/"medium"/"low")
8. shap_variance = std/importance ratio → stability metric
9. LLM call (LLMClient) → business_explanation (2-4 sentences)
   - System: "You are a Chief Strategy Officer AI..."
   - User: causal_chain list + target + problem description
10. _compute_confidence(): score = max(0.3, 1 - shap_variance × 10)
```

---

### `module4/explainability/xai_layer.py` — `XAILayer`

**Dual-method explainability: SHAP (global) + LIME (local).**

| Method | Scope | Use case |
|---|---|---|
| `explain_with_shap(model, X, task_type)` | Global | Which features matter most across all predictions? |
| `explain_with_lime(model, X, row_index, task_type)` | Local | Why did the model predict THIS specific row? |
| `feature_importance_report(model, features)` | Global | Native `model.feature_importances_` ranking |
| `full_explanation(model, X, task_type)` | Combined | Runs SHAP + native, computes agreement score |

**Agreement score** = intersection of top-5 SHAP features with top-5 native importance features / 5  
→ High agreement = model is internally consistent → higher confidence

---

### `module4/monitoring/model_monitor.py` — `ModelMonitor`

**Tracks run history and detects data drift.**

```python
log_run(job_id, metrics, confidence, engine)
  → appends to self.run_history list
  → status = "success" if confidence > 0 else "failed"

set_baseline(df)
  → computes mean/std/min/max for all numeric columns
  → stored in self.baseline_stats

detect_drift(new_df) → Dict
  → for each numeric col: drift_score = |new_mean - base_mean| / base_std
  → drifted if drift_score > 2.0 (more than 2 standard deviations of shift)
  → returns: drifted_columns, drift_scores, overall_drift, recommendation

get_health_report() → Dict
  → analyses last 10 runs
  → confidence_trend: "improving" if second_half avg > first_half avg + 0.05
  → returns: total_runs, last_run_time, avg_confidence_last_10, engines_run, recent_errors
```

---

## ConfidenceScore — Shared Schema (`module4/schemas/models.py`)

Used by **every** Module 4 engine and agent. Gives every result a trust rating:

```python
class ConfidenceScore(BaseModel):
    score: float        # 0.0 to 1.0
    level: str          # "very high" / "high" / "moderate" / "low" / "uncertain"
    explanation: str    # why this score
    basis: List[str]    # what was measured (MAE values, variance, etc.)
    suggestions: List[str]  # what to do next
```

**Level thresholds (consistent across all engines):**
```
≥ 0.90 → very high  → "Safe to act on automatically"
≥ 0.75 → high       → "Recommend quick human review"
≥ 0.55 → moderate   → "Validate key assumptions"
≥ 0.40 → low        → "Expert review required"
< 0.40 → uncertain  → "Do not act. Collect more data"
```

---

## Key Environment Variables

| Variable | Used by | Purpose |
|---|---|---|
| `GROQ_API_KEY` | All modules | LLM API authentication |
| `GROQ_MODEL` | All modules | Default: `llama-3.1-8b-instant` |
| `STORAGE_BACKEND` | main.py, gcs_storage | `"local"` or `"gcs"` |
| `GCS_BUCKET_NAME` | gcs_storage | GCS bucket for artifacts |
| `GROQ_MAX_TOKENS` | llm_client | Default: 2048 |

---

## Data Flow Summary — End to End

```
CSV Upload (main.py /process)
    │
    ▼
Module 1: Understanding Pipeline (9 stages)
    → domain, schema, quality, meanings, summary, suggestions
    │
    ▼
Module 2: AI Cleaning Pipeline
    → EDA → AI plans steps → rule engine executes → analytics_df + ml_df + artifacts
    │
    ▼
Module 3: Analysis & Insights
    → RAG context → plan → stats → charts (4 agents) → insights → explanation → chat
    │
    ▼
Module 4: Advanced AI (LangGraph)
    → prediction → forecast → RCA → risk → recommendations → decision → eval → report
    │
    ▼
JSON Response → Frontend Dashboard
```
