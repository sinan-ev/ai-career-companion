# End-to-End AI Decision Intelligence Platform

A professional‑grade, multi-agent AI‑powered platform that transforms raw datasets into human-understandable business contexts, cleans and prepares data for machine learning, constructs conversational RAG insights, performs AutoML predictions and forecasting, and compiles executive-level decision reports.

---

## 🧠 The 4-Module Intelligence Pipeline

The platform is designed around four decoupled, cooperating AI modules:

### 1. Module 1: Data Understanding & Profiling
*   **Purpose**: Translate machine-level columns into rich human business contexts.
*   **Capabilities**:
    *   **Normalization**: Detects and standardizes disguised null values (e.g., `"N/A"`, `"-999"`, `"??"`).
    *   **Type Parsing**: Dynamically detects column schemas (numeric, categorical, datetime, IDs).
    *   **Semantic Labeling**: Uses LLM reasoning to explain cryptic column names (e.g., `cnt_v1` → "customer monthly count version 1").
    *   **Domain & Summary**: Summarizes the business domain (e.g., HR, Sales, Healthcare) and writes a narrative overview.

### 2. Module 2: Intelligent Preprocessing & Pre-ML
*   **Purpose**: Dynamically prepare, clean, and format datasets for visualization and ML modeling.
*   **Capabilities**:
    *   **AI Planning**: Analyzes data issues (skew, outliers, missingness) to formulate a tailored cleaning sequence.
    *   **Dynamic Execution**: Runs cleaning steps (imputation, Tukey outlier capping, scaling, categorical encoding) in strict, non-leakage canonical order.
    *   **Dual Exports**: Splits data into an `analytics` version (human-readable string labels) and an `ml` version (fully encoded/scaled numeric vectors).
    *   **Smart Target Detection**: Predicts the dependent target variable ($Y$) by analyzing semantic context and training suggestions.

### 3. Module 3: Present-State Analytics & RAG Chat
*   **Purpose**: Generate interactive dashboards, statistical insights, and a conversation-grounded data assistant.
*   **Capabilities**:
    *   **Multi-Agent Charting**: Uses a Scout-Planner-Critic-Builder agent loop to generate 5-6 Plotly-compatible interactive charts.
    *   **Parallel Insights**: Concurrently generates key findings to prevent UI load lag.
    *   **Contextual RAG Store**: Embeds dataset schema, summary, and domain context into an in-memory vector store.
    *   **Guardrailed Chat**: Implements a strict, jargon-free business chat assistant that queries the RAG store and runs on-the-fly pandas aggregations.

### 4. Module 4: Future Intelligence & Strategic Recommendations
*   **Purpose**: Run AutoML predictions, forecasting, root-cause analysis (RCA), and anomaly monitoring.
*   **Capabilities**:
    *   **LangGraph Coordination**: Connects 7 specialized agents (`Prediction`, `Forecast`, `RCA`, `Risk`, `Recommend`, `Decision`, `Eval`) in a sequential workflow graph.
    *   **AutoML & Ensemble Forecasting**: Benchmarks multiple models (LGBM, XGBoost, CatBoost, RandomForest) for classification/regression, and runs an inverse-error Prophet-ARIMA ensemble for time series.
    *   **Statistical RCA**: Explains model behavior by calculating SHAP values over multiple data folds, converting statistical importances into executive business explanations.
    *   **Decision Synthesis**: Merges prediction, risk, forecasting, and recommendations into a unified business decree with a limiting-factor confidence score.

---

## 🛠 Tech Stack

### Backend (Python)
*   **Framework**: FastAPI
*   **AI Orchestration**: LangGraph, LangChain Core
*   **LLM API**: Groq Cloud SDK (`llama-3.1-8b-instant`)
*   **ML & Analytics**: pandas, NumPy, scikit-learn, LightGBM, XGBoost, CatBoost, shap, lime, prophet, pmdarima
*   **Cloud Storage**: Google Cloud Storage (`google-cloud-storage`)
*   **Validation**: Pydantic v2 & Pydantic Settings
*   **Testing & Linting**: pytest, httpx, Ruff

### Frontend (React/Vite)
*   **Build System**: Vite + React 18
*   **Styling**: Vanilla CSS (Custom modern variables, glassmorphism, micro-animations, sleek dark mode)
*   **Visualization**: Recharts, Plotly.js
*   **API Interaction**: Axios

---

## 📂 Project Structure

```text
ai-career-companion/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Runs Ruff, Pytest, ESLint, Vite Build, Docker verify
│       └── cd.yml                 # Builds Docker images and deploys backend to GCP Cloud Run
├── Backend/
│   ├── main.py                    # Unified FastAPI entry point (combines all modules)
│   ├── Dockerfile                 # Multi-stage production build (builder + non-root runtime)
│   ├── ruff.toml                  # Ruff lint configurations
│   ├── requirements.txt           # Main python dependencies
│   ├── module1/                   # Module 1: Data Understanding
│   ├── module2/                   # Module 2: Intelligent Preprocessing
│   ├── module3/                   # Module 3: Present-State Analytics & RAG Chat
│   ├── module4/                   # Module 4: Future Intelligence (LangGraph)
│   ├── utils/
│   │   ├── gcs_storage.py         # GCS & local storage abstraction layer
│   │   └── llm_client.py          # Cached Groq and general LLM client wrappers
│   └── tests/
│       └── test_main.py           # Pytest unit tests for endpoint health and validations
├── frontend/
│   ├── src/                       # React frontend source code
│   │   ├── components/            # UploadZone, PipelineView, AnalystView, ChatBot
│   │   └── App.jsx                # Frontend application orchestrator
│   ├── Dockerfile                 # Multi-stage Node build with Nginx runtime
│   ├── nginx.conf                 # Nginx proxy and SPA routing setup
│   ├── vercel.json                # Vercel SPA routing rules
│   └── package.json               # Frontend dependencies and scripts
├── ARCHITECTURE.md                # Comprehensive data flow and agent blueprints
├── API_REFERENCE.md               # Typed schemas and HTTP endpoint details
└── README.md                      # This root overview
```

---

## 🚀 Running the Platform

### Setup & Run Instructions

#### 1. Backend Setup
1.  Navigate to `/Backend` and create a `.env` file containing your `GROQ_API_KEY`.
2.  Install dependencies:
    ```bash
    cd Backend
    pip install -r requirements.txt
    ```
3.  Start server:
    ```bash
    uvicorn main:app --reload --port 8000
    ```

#### 2. Frontend Setup
1.  Navigate to `/frontend`.
2.  Install packages:
    ```bash
    cd frontend
    npm install
    ```
3.  Start Vite development server:
    ```bash
    npm run dev
    ```

---

*Developed by Muhammmed Sinan EV*
