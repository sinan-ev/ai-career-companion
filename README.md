# Unified Data Intelligence & Cleaning Agent (v2.0.1)

A professional-grade, AI-powered platform designed to transform raw spreadsheets into actionable insights and ML-ready datasets. This project combines advanced data profiling with LLM-based reasoning to automate the most tedious parts of data science.

## 🚀 Key Features

- **Dual-Module Intelligence**: 
    - **Module 1 (Understanding)**: Automatic domain detection, column explanation (LLM), and narrative data summaries.
    - **Module 2 (Preprocessing)**: Deep EDA, AI-planned cleaning steps, and target variable detection.
- **Dynamic Pipeline**: The cleaning steps are not hardcoded; an AI agent plans the pipeline (scaling, encoding, imputation) based on the specific data quality issues detected.
- **Dual Export System**:
    - **Analytics Dataset**: Cleaned but human-readable data for dashboards.
    - **ML-Ready Dataset**: Fully encoded and scaled data for model training.
- **Interactive Dashboard**: A modern React frontend to visualize data quality, pipeline steps, and column statistics.

## 🛠 Tech Stack

### Backend (Python/FastAPI)
- **Framework**: FastAPI (High-performance API)
- **Intelligence**: Groq AI (Llama 3.3 70B) for column reasoning and pipeline planning.
- **Processing**: Pandas, NumPy, Scikit-learn.
- **Validation**: Pydantic v2.

### Frontend (React/Vite)
- **Framework**: React 18+ with Vite.
- **Styling**: Vanilla CSS (Modern design patterns, glassmorphism).
- **Icons/Visuals**: Lucid-react & custom CSS components.

## 📂 Project Structure

```text
├── Backend/
│   ├── main.py             # Unified API Entry Point
│   ├── module1/            # Data Understanding Logic (Rules + LLM)
│   ├── module2/            # Advanced EDA & ML Preprocessing
│   ├── exports/            # Processed CSV/Excel downloads
│   └── artifacts/          # Saved Encoders & Scalers (.pkl)
├── frontend/
│   ├── src/components/     # Dashboard, DataTable, UploadZone, etc.
│   └── src/App.jsx         # Main Frontend Orchestrator
└── README.md
```

## 🚥 Quick Start

### 1. Setup Backend
1. Navigate to `/Backend`.
2. Create a `.env` file and add your `GROQ_API_KEY`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run server: `python main.py`.

### 2. Setup Frontend
1. Navigate to `/frontend`.
2. Install dependencies: `npm install`.
3. Run dev server: `npm run dev`.

---
*Created by the Data Intelligence Team*
