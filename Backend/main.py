import os
import io
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import from modules
from module1.core.pipeline import run_pipeline as run_module1
from module2.core.pipeline_module2 import run_module2
from module1.config import get_settings

# Setup settings
settings = get_settings()

app = FastAPI(
    title="Unified Data Intelligence & Cleaning Agent",
    version="2.0.1",
    description="Connects Module 1 (Understanding) and Module 2 (Cleaning & ML Prep)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for exported files
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

# Directory for model artifacts (encoders/scalers)
ARTIFCAT_DIR = Path("artifacts")
ARTIFCAT_DIR.mkdir(exist_ok=True)

# Mount exports directory to serve files
# Users can download files from /downloads/filename.csv
app.mount("/downloads", StaticFiles(directory=str(EXPORTS_DIR)), name="downloads")

from module1.models.response_model import AnalysisResponse
from module2.models.module2_response import Module2Response

class UnifiedResponse(BaseModel):
    module1: AnalysisResponse
    module2: Module2Response
    dataset_id: Optional[str] = None

@app.post("/api/process", response_model=UnifiedResponse)
async def process_dataset(
    file: UploadFile = File(...)
):
    """
    Unified endpoint that performs:
    1. Data Understanding (Module 1)
    2. Deep EDA & Intelligent Cleaning (Module 2)
    3. Exporting Analytics & ML-ready datasets (to /downloads/)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{suffix}'")

    # 1. Read file into memory once
    try:
        content = await file.read()
        if suffix == ".csv":
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding='latin-1')
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(content), encoding='windows-1252')
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="The provided dataset is empty.")

    # 2. Run Module 1 (Understanding)
    try:
        m1_result = await run_module1(df=df, filename=file.filename)
    except Exception as e:
        import traceback
        print(f"Module 1 Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Module 1 failed: {str(e)}")

    # 3. Run Module 2 (Cleaning)
    try:
        # Use key from env/settings
        api_key = settings.groq_api_key
        m2_result = run_module2(
            df=df.copy(), 
            module1_output=m1_result.model_dump(),
            groq_api_key=api_key
        )
        
        # Construct full URLs for the downloaded files
        # We assume the app runs on localhost:8000 for now. 
        # In production, this would be the actual domain.
        base_url = "/downloads"
        if m2_result.dataset_outputs.dataset_files:
            m2_result.dataset_outputs.dataset_files = {
                k: f"{base_url}/{v}" for k, v in m2_result.dataset_outputs.dataset_files.items()
            }
            
    except Exception as e:
        import traceback
        print(f"Module 2 Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Module 2 failed: {str(e)}")

    from module3a.api.routes.upload import datasets
    import uuid
    dataset_id = str(uuid.uuid4())
    datasets[dataset_id] = df.copy()

    # 4. Success - Return both results
    return UnifiedResponse(
        module1=m1_result,
        module2=m2_result,
        dataset_id=dataset_id
    )

@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "modules": ["understanding", "cleaning"],
        "app": settings.app_name,
        "version": "2.0.1"
    }

from module3a.api.routes import upload as m3a_upload
from module3a.api.routes import analyze as m3a_analyze
from module3a.api.routes import charts as m3a_charts
from module3a.api.routes import insights as m3a_insights
from module3a.api.routes import chat as m3a_chat

app.include_router(m3a_upload.router, prefix="/api", tags=["Module 3A"])
app.include_router(m3a_analyze.router, prefix="/api", tags=["Module 3A"])
app.include_router(m3a_charts.router, prefix="/api", tags=["Module 3A"])
app.include_router(m3a_insights.router, prefix="/api", tags=["Module 3A"])
app.include_router(m3a_chat.router, prefix="/api", tags=["Module 3A"])

# Mount Module 3B as a sub-application
from module_3b.api.routes_3b import app as module3b_app
app.mount("/api/3b", module3b_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
