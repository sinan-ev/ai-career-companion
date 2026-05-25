# Platform REST API Reference

The unified backend is powered by **FastAPI** running on Uvicorn (port `8000`). It exposes endpoints for file ingestion, present-state profiling, and future decision intelligence operations. All inputs and outputs are strictly validated using **Pydantic v2** models.

---

## 🚪 Gateway Ingestion API

### 1. Ingest & Preprocess Dataset
*   **Endpoint**: `POST /api/process`
*   **Content-Type**: `multipart/form-data`
*   **Description**: Ingests a raw dataset file, runs Module 1 (Understanding) followed by Module 2 (Cleaning/Feature Engineering), and caches the raw table in-memory for subsequent steps.
*   **Request Payload**:
    *   `file` (binary): A `.csv`, `.xlsx`, or `.xls` file.
*   **Response Model (`UnifiedResponse`)**:
    ```json
    {
      "module1": {
        "dataset_info": {
          "rows": 891,
          "columns": 12,
          "domain": "Titanic/Survival",
          "dataset_type": "tabular",
          "file_name": "titanic.csv",
          "was_sampled": false
        },
        "data_schema": {
          "numeric": ["Age", "Fare"],
          "categorical": ["Sex", "Embarked"],
          "datetime": [],
          "unknown": []
        },
        "column_meanings": {
          "SibSp": "Number of siblings or spouses aboard",
          "Parch": "Number of parents or children aboard"
        },
        "data_quality": {
          "missing_values": {"Age": 177},
          "missing_percent": {"Age": 19.87},
          "duplicate_rows": 0,
          "total_rows": 891
        },
        "ai_summary": "This dataset contains passenger demographics and survival indicators for the Titanic voyage...",
        "suggested_analyses": ["Survival rate by gender", "Fare impact on class"],
        "warnings": ["Column 'Cabin' has 77.1% missing values."]
      },
      "module2": {
        "dataset_info": { "domain": "Titanic/Survival", "file_name": "titanic.csv" },
        "eda_report": {
          "overview": { "rows": 891, "cols": 12 },
          "column_types": { "Age": "numeric", "Sex": "categorical" },
          "quality_score": { "score": 88, "grade": "B" },
          "warnings": []
        },
        "dataset_outputs": {
          "analytics_shape": [891, 13],
          "ml_shape": [891, 15],
          "target_column": "Survived",
          "feature_columns": ["Age", "Sex_male", "Fare_log"],
          "dropped_columns": ["PassengerId", "Name", "Ticket", "Cabin"],
          "artifact_paths": {
            "encoders": "artifacts/titanic_20260525/encoders.pkl",
            "scalers": "artifacts/titanic_20260525/scalers.pkl",
            "metadata": "artifacts/titanic_20260525/metadata.json",
            "base_dir": "artifacts/titanic_20260525/"
          },
          "was_encoded": true,
          "was_scaled": true,
          "dataset_files": {
            "analytics": "titanic_20260525_analytics.csv",
            "ml": "titanic_20260525_ml.csv"
          }
        },
        "pipeline_steps": [
          { "step": "remove_duplicates", "status": "success", "details": "Found and removed 0 duplicate rows." },
          { "step": "handle_missing", "status": "success", "details": "Imputed 177 missing values in 'Age'." }
        ]
      },
      "dataset_id": "4a1b2c3d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"
    }
    ```

---

## 📊 Module 3: Present-State Analytics & RAG

### 1. Ingest Directly (Fallback)
*   **Endpoint**: `POST /api/upload`
*   **Content-Type**: `multipart/form-data`
*   **Request Payload**: `file` (binary)
*   **Response**: `{"dataset_id": "uuid-string"}`

### 2. Plan Visualizations & Summary
*   **Endpoint**: `POST /api/analyze`
*   **Content-Type**: `application/json`
*   **Request Payload**:
    ```json
    { "dataset_id": "4a1b2c3d-5e6f-7a8b-9c0d-1e2f3a4b5c6d" }
    ```
*   **Response**:
    ```json
    {
      "charts_plan": ["bar", "line", "scatter"],
      "insights": ["Highest correlation between Fare and Survival.", "Class 1 had 63% survival."],
      "rag_status": "initialized",
      "dataset_summary": "Titanic Passenger List Analysis..."
    }
    ```

### 3. Fetch Plotly Charts JSON
*   **Endpoint**: `GET /api/charts/{dataset_id}`
*   **Response**: Returns list of interactive Plotly-compatible JSON configs defining title, type, X/Y data, and grouped aggregations.

### 4. Fetch Deep Key Insights
*   **Endpoint**: `GET /api/insights/{dataset_id}`
*   **Response**: Returns list of clean narrative insight strings.

### 5. Talk with Dataset (RAG Chat)
*   **Endpoint**: `POST /api/chat`
*   **Content-Type**: `application/json`
*   **Request Payload**:
    ```json
    {
      "dataset_id": "4a1b2c3d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "message": "What is the average age of survivors?"
    }
    ```
*   **Response**:
    ```json
    {
      "response": "The average age of survivors is approximately 28.3 years. (Confidence Score: 85%)"
    }
    ```

---

## 🔮 Module 4: Future Intelligence & Decisions

Mounted as a sub-app at prefix `/api/4`. Port `8004` or via root proxy `/api/4/*`.

### 1. AutoML Predictions
*   **Endpoint**: `POST /api/4/predict`
*   **Request Payload (`PredictionRequest`)**:
    ```json
    {
      "data": [
        {"Age": 22, "Sex": 1, "Fare": 7.25, "Survived": 0},
        {"Age": 38, "Sex": 0, "Fare": 71.28, "Survived": 1}
      ],
      "target_column": "Survived"
    }
    ```
*   **Response Model (`PredictionResponse`)**:
    ```json
    {
      "task_type": "classification",
      "best_model": "LGBMClassifier",
      "metrics": { "accuracy": 0.825, "f1_score": 0.791 },
      "predictions": [0, 1],
      "confidence": {
        "score": 0.88,
        "level": "high",
        "explanation": "High training accuracy and well-calibrated confidence scores.",
        "basis": ["LGBMClassifier cross-validation accuracy = 0.83"],
        "suggestions": ["Include ticket class to improve confidence."]
      }
    }
    ```

### 2. Time-Series Forecasting
*   **Endpoint**: `POST /api/4/forecast`
*   **Request Payload (`ForecastRequest`)**:
    ```json
    {
      "data": [
        {"Date": "2026-01-01", "Sales": 100},
        {"Date": "2026-02-01", "Sales": 120}
      ],
      "date_column": "Date",
      "value_column": "Sales",
      "periods": 3
    }
    ```
*   **Response Model (`ForecastResponse`)**:
    ```json
    {
      "forecast": [
        {"Date": "2026-03-01", "Value": 135.2, "Lower": 120.1, "Upper": 150.3},
        {"Date": "2026-04-01", "Value": 142.5, "Lower": 125.4, "Upper": 159.6}
      ],
      "trend": "upward",
      "confidence": {
        "score": 0.78,
        "level": "high",
        "explanation": "Prophet and ARIMA models are in high agreement.",
        "basis": ["Ensemble agreement score = 0.84"],
        "suggestions": []
      }
    }
    ```

### 3. Root Cause Analysis (SHAP)
*   **Endpoint**: `POST /api/4/rca`
*   **Request Payload (`RCARequest`)**:
    ```json
    {
      "data": [{"Age": 22, "Sex": 1, "Survived": 0}],
      "target_column": "Survived",
      "problem": "Determine primary survival drivers"
    }
    ```
*   **Response Model (`RCAResponse`)**:
    ```json
    {
      "top_features": [
        { "feature": "Sex", "importance": 0.35, "direction": "decreases", "impact": "high" },
        { "feature": "Age", "importance": 0.12, "direction": "influences", "impact": "medium" }
      ],
      "business_explanation": "Gender (Sex) is the primary driver of survival outcomes. Being male decreases survival probability significantly, followed by age coordinates.",
      "confidence": { "score": 0.92, "level": "very high", "explanation": "Low SHAP variance across splits." }
    }
    ```

### 4. Anomaly & Risk Scanning
*   **Endpoint**: `POST /api/4/risk`
*   **Request Payload (`RiskRequest`)**:
    ```json
    { "data": [{"Age": 22, "Fare": 7.25}, {"Age": 99, "Fare": 500.0}] }
    ```
*   **Response Model (`RiskResponse`)**:
    ```json
    {
      "anomalies": [
        { "row_index": 1, "score": -0.85, "features": ["Age", "Fare"], "details": "Out of distribution values." }
      ],
      "risk_score": 45.0,
      "risk_level": "medium",
      "confidence": { "score": 0.80, "level": "high", "explanation": "Isolation Forest bounds are stable." }
    }
    ```

### 5. Ranked Strategic Recommendations
*   **Endpoint**: `POST /api/4/recommend`
*   **Request Payload (`RecommendRequest`)**:
    ```json
    {
      "insights": ["High correlation between Gender and survival."],
      "prediction_confidence": 0.85,
      "risk_score": 30.0,
      "top_risk_features": ["Sex"]
    }
    ```
*   **Response Model (`RecommendResponse`)**:
    ```json
    {
      "recommendations": [
        { "rank": 1, "action": "Audit safety deployment procedures for male passenger quarters.", "impact": "high", "feasibility": "high" }
      ],
      "confidence": { "score": 0.85, "level": "high", "explanation": "Recommendations mapped directly to high-importance SHAP features." }
    }
    ```

### 6. Synchronous Decision Synthesis
*   **Endpoint**: `POST /api/4/decide`
*   **Request Payload (`DecisionRequest`)**:
    ```json
    {
      "data": [{"Age": 22, "Sex": 1, "Survived": 0}],
      "target_column": "Survived",
      "problem": "Optimize passenger survival ratios"
    }
    ```
*   **Response Model (`DecisionResponse`)**:
    ```json
    {
      "decree": "Deploy immediate quarter reallocation and safety drills targeting male passenger zones.",
      "threat_level": "critical",
      "confidence": { "score": 0.82, "level": "high", "explanation": "Overall decision driven by high-accuracy AutoML predictions." }
    }
    ```

### 7. Run Full LangGraph Pipeline
*   **Endpoint**: `POST /api/4/run-pipeline`
*   **Request Payload (`AgentRunRequest`)**:
    ```json
    {
      "data": [{"Age": 22, "Sex": 1, "Survived": 0}],
      "target_column": "Survived",
      "date_column": null,
      "problem": "Complete survival analysis"
    }
    ```
*   **Response Model (`AgentRunResponse`)**:
    ```json
    {
      "job_id": "9a2b8c7d-...",
      "prediction": { "best_model": "LGBMClassifier", "metrics": { "accuracy": 0.82 } },
      "forecast": null,
      "rca": { "top_features": [...] },
      "risk": { "risk_score": 22.0 },
      "recommendation": { "recommendations": [...] },
      "decision": { "decree": "..." },
      "overall_confidence": { "score": 0.81, "level": "high", "explanation": "Limited by risk evaluation data size." },
      "final_report": "# Executive Decision Report\n\n## AutoML Predictions...",
      "errors": []
    }
    ```

---

## 📥 File Serving

### 1. Download Cleaned CSVs & Model Pickles
*   **Endpoint**: `GET /downloads/{filename}`
*   **Response**:
    *   `STORAGE_BACKEND == local`: Standard `FileResponse` streaming the local CSV/Pickle file.
    *   `STORAGE_BACKEND == gcs`: A `RedirectResponse` (HTTP 307) forwarding the browser to a secure, 60-minute Google Cloud Storage signed URL.
