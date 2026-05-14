# End-to-End AI Decision Intelligence Platform

A professional‑grade, AI‑powered platform that transforms raw datasets into actionable present-state analytics, human-readable insights, ML‑ready datasets, and future-focused strategic AI decisions.

## 🚀 New Features (v3.0.0)

- **Module 1 (Data Understanding)** – Automatically understands dataset structure, business context, column types, and target information.
- **Module 2 (Intelligent Processing)** – Separates data into human-readable format for visualization and an ML-ready encoded dataset.
- **Module 3A (Present-State Analytics)** – Generates visualizations, KPI insights, trends, and RAG-backed chatbot interactions using human-readable data.
- **Module 3B (Future Intelligence)** – End-to-end predictive pipeline that:
  - Runs AutoML for predictions and forecasting to generate future datasets.
  - Converts technical ML outputs into business-understandable future insights (explaining why changes happen, business factors).
  - Performs AI-driven Root Cause Analysis (RCA) and generates strategic actionable solutions via LLM reasoning.
  - Integrates a **Future-Focused Chat Assistant** to interact with prediction outputs and recommended strategies in natural language.

## 🛠 Tech Stack

### Backend (Python/FastAPI)
- **Framework**: FastAPI
- **LLM**: Groq (`llama‑3.1‑8b‑instant`)
- **Processing**: pandas, NumPy, scikit‑learn
- **Validation**: Pydantic v2

### Frontend (React/Vite)
- **Framework**: React 18+ with Vite
- **Visualization**: Recharts (bar, line, histogram, horizontal bar)
- **Styling**: Vanilla CSS with glass‑morphism, vibrant palettes, micro‑animations

## 📂 Project Structure

```text
├── Backend/
│   ├── main.py                # Unified API entry point
│   ├── module1/               # Data understanding (schema, column meanings)
│   ├── module2/               # Advanced EDA, preprocessing, and dataset splitting
│   ├── module3a/              # Present-state analytics (charts, insights, RAG chatbot)
│   ├── module_3b/             # Future intelligence (AutoML, RCA, strategy engine, business chat)
│   └── exports/               # Generated CSVs & artifacts
├── frontend/
│   ├── src/components/        # UploadZone, AnalystView, PipelineView, etc.
│   └── src/App.jsx            # Front‑end orchestrator
└── README.md
```

## 📖 Documentation
- **API Reference** – Updated `/api/analyze` endpoint returns a `Module3AResult` with charts, insights, and pipeline plan.
- **Architecture** – Diagram now includes the RAG store, chart engine, and chatbot modules.
- **User Guide** – Upload a CSV/Excel file, click **Launch Pipeline**, and explore the auto‑generated dashboard.

---
*Created by the Data Intelligence Team*
