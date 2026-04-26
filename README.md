# Unified Data Intelligence & Cleaning Agent (v2.0.1)

A professional‑grade, AI‑powered platform that transforms raw spreadsheets into actionable insights, ML‑ready datasets, and a polished interactive dashboard.

## 🚀 New Features (v2.0.1)

- **Module 3‑A (AI Analyst)** – End‑to‑end pipeline that:
  - Builds a Retrieval‑Augmented Generation (RAG) vector store from the EDA report.
  - Uses `llama‑3.1‑8b‑instant` to **plan 5‑6 business‑focused charts**.
  - Generates concise insights, a narrative explanation, and a **RAG‑backed chatbot**.
  - Returns a `Module3AResult` JSON consumed by the React dashboard.
- **Upload Page Enhancements** – The upload zone now shows a concise overview of Module 3‑A capabilities.
- **Pipeline View** – Visual representation of the AI‑orchestrated preprocessing steps plus a highlighted Module 3‑A overview.
- **Robust Model Handling** – Updated token budget (`max_tokens=2048`) and strict JSON response format.

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
│   ├── module2/               # Advanced EDA & preprocessing
│   ├── module3a/              # AI Analyst – RAG, chart engine, insights, chatbot
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
