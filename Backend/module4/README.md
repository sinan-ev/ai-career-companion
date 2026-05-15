# Module 4 — AI Decision Intelligence

## 1. Overview
Module 4 is the AI Decision Intelligence engine of the 4-module Business Intelligence Platform. It processes outputs from earlier modules to run AutoML predictions, time-series forecasting, root cause analysis (RCA), and anomaly risk detection. Finally, it synthesises these outputs into ranked actionable recommendations and strategic decisions using a LangGraph-based agent pipeline.

## 2. Folder Structure

```
module4/
├── main.py                          ← entry point, imports app from api/routes_4.py
├── requirements.txt                 ← all pip dependencies
├── README.md                        ← setup + run instructions + curl examples
│
├── ingestion/
│   ├── __init__.py
│   └── data_router.py               ← loads M1/M2/M3 outputs into DataFrames
│
├── engines/
│   ├── __init__.py
│   ├── prediction_engine.py         ← AutoML classification + regression
│   ├── forecasting_engine.py        ← Prophet + ARIMA + ensemble
│   ├── rca_agent.py                 ← SHAP root cause analysis
│   ├── risk_engine.py               ← anomaly + drift detection
│   ├── recommendation_engine.py     ← insight-to-action mapping
│   └── decision_engine.py           ← strategic decision synthesis
│
├── agents/
│   ├── __init__.py
│   ├── agent_definitions.py         ← each agent class with role + tools
│   ├── agent_graph.py               ← LangGraph StateGraph definition
│   └── agent_runner.py              ← entry point to execute full pipeline
│
├── explainability/
│   ├── __init__.py
│   └── xai_layer.py                 ← SHAP + LIME + feature importance
│
├── monitoring/
│   ├── __init__.py
│   └── model_monitor.py             ← accuracy tracking + drift detection
│
├── outputs/
│   ├── __init__.py
│   └── report_generator.py          ← builds final strategic report
│
├── schemas/
│   ├── __init__.py
│   └── models.py                    ← all Pydantic v2 request/response models
│
└── api/
    ├── __init__.py
    └── routes_4.py                  ← all FastAPI routes, imports all engines
```

## 3. Installation

Navigate to the `module4` directory and install the required packages:

```bash
cd module4
pip install -r requirements.txt
```

## 4. Run

Run the FastAPI application using either `main.py` or directly with `uvicorn`:

```bash
python main.py
# or
uvicorn api.routes_4:app --reload --port 8004
```

## 5. Routes and cURL Examples

**GET /health**
```bash
curl -X GET "http://localhost:8004/health"
```

**POST /predict**
```bash
curl -X POST "http://localhost:8004/predict" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"feature1": 10, "feature2": 20, "target": 1}, {"feature1": 15, "feature2": 25, "target": 0}], "target_column": "target"}'
```

**POST /forecast**
```bash
curl -X POST "http://localhost:8004/forecast" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"date": "2023-01-01", "sales": 100}, {"date": "2023-02-01", "sales": 110}], "date_column": "date", "value_column": "sales", "periods": 6}'
```

**POST /rca**
```bash
curl -X POST "http://localhost:8004/rca" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"feature1": 10, "target": 1}, {"feature1": 15, "target": 0}], "target_column": "target", "problem": "High customer churn"}'
```

**POST /risk**
```bash
curl -X POST "http://localhost:8004/risk" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"feature1": 10, "feature2": 20}, {"feature1": 1000, "feature2": 0}]}'
```

**POST /recommend**
```bash
curl -X POST "http://localhost:8004/recommend" \
  -H "Content-Type: application/json" \
  -d '{"insights": ["High churn in region A"], "prediction_confidence": 0.85, "risk_score": 15.0, "top_risk_features": ["feature1"]}'
```

**POST /decide**
```bash
curl -X POST "http://localhost:8004/decide" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"feature1": 10, "target": 1}, {"feature1": 15, "target": 0}], "target_column": "target", "problem": "Analyse overall business risk"}'
```

**POST /run-pipeline**
```bash
curl -X POST "http://localhost:8004/run-pipeline" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"feature1": 10, "target": 1}, {"feature1": 15, "target": 0}], "target_column": "target", "problem": "Full diagnostic analysis"}'
```

## 6. Confidence Scoring System

Every response includes a unified `confidence` object. It operates on a 0.0 to 1.0 scale, mapped into 5 bands:

- **>= 0.90 ("very high")**: Safe to act on this result automatically.
- **>= 0.75 ("high")**: Reliable result. Recommend quick human review.
- **>= 0.55 ("moderate")**: Reasonable result. Validate key assumptions.
- **>= 0.40 ("low")**: Uncertain result. Expert review required.
- **<  0.40 ("uncertain")**: Do not act. Collect more data first.

The overall pipeline confidence uses a weighted average of individual engines and identifies the limiting factor.

## 7. Connecting to Earlier Modules

The data router (`ingestion/data_router.py`) includes utility functions to load CSV and JSON outputs directly from Module 1, 2, and 3. The default paths expect this layout:

- `../module_1/outputs/`
- `../module_2/outputs/`
- `../module_3/outputs/`

Adjust the base paths in the router functions if your local architecture differs.
