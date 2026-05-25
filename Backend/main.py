import os
import sys
import io
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
import warnings

# Suppress all non-critical library warnings for a "perfect" console experience
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="shap")
warnings.filterwarnings("ignore", module="lightgbm")

# Ensure module4 is in the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "module4"))

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

from utils.gcs_storage import generate_signed_url, STORAGE_BACKEND
from fastapi.responses import FileResponse, RedirectResponse

@app.get("/downloads/{filename}")
async def download_file(filename: str):
    """Serve exported files from GCS (prod) or local disk (dev)."""
    path = f"exports/{filename}"
    if STORAGE_BACKEND == "gcs":
        url = generate_signed_url(path, expires_minutes=60)
        return RedirectResponse(url)
    local_path = EXPORTS_DIR / filename
    if not local_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(local_path))

from module1.models.response_model import AnalysisResponse
from module2.models.module2_response import Module2Response

class UnifiedResponse(BaseModel):
    """
    Response model unifying outputs from Module 1 and Module 2.
    
    Attributes:
        module1 (AnalysisResponse): Results from the data understanding phase.
        module2 (Module2Response): Results from the data cleaning and preparation phase.
        dataset_id (Optional[str]): Unique identifier for the processed dataset, if applicable.
    """
    module1: AnalysisResponse
    module2: Module2Response
    dataset_id: Optional[str] = None

@app.post("/api/process", response_model=UnifiedResponse)
async def process_dataset(
    file: UploadFile = File(...)
):
    """
    Unified endpoint that performs data understanding and cleaning.
    
    1. Data Understanding (Module 1)
    2. Deep EDA & Intelligent Cleaning (Module 2)
    3. Exporting Analytics & ML-ready datasets (to /downloads/)
    
    Args:
        file (UploadFile): The uploaded dataset file (CSV or Excel).
        
    Returns:
        UnifiedResponse: An object containing results from both Module 1 and Module 2, along with a dataset ID.
        
    Raises:
        HTTPException: If the file is not provided, unsupported, empty, or if processing fails.
    """
    # Automatically clean up older local files before starting the new run
    from utils.gcs_storage import cleanup_old_local_files
    try:
        cleanup_old_local_files(max_age_minutes=60)
    except Exception as e:
        print(f"[Cleanup Error] Failed to clear old local files: {e}")

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

    from module3.api.routes.upload import datasets
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
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: A dictionary containing the status, active modules, application name, and version.
    """
    return {
        "status": "ok", 
        "modules": ["understanding", "cleaning"],
        "app": settings.app_name,
        "version": "2.0.1"
    }

from module3.api.routes import upload as m3_upload
from module3.api.routes import analyze as m3_analyze
from module3.api.routes import charts as m3_charts
from module3.api.routes import insights as m3_insights
from module3.api.routes import chat as m3_chat

app.include_router(m3_upload.router, prefix="/api", tags=["Module 3"])
app.include_router(m3_analyze.router, prefix="/api", tags=["Module 3"])
app.include_router(m3_charts.router, prefix="/api", tags=["Module 3"])
app.include_router(m3_insights.router, prefix="/api", tags=["Module 3"])
app.include_router(m3_chat.router, prefix="/api", tags=["Module 3"])

# Mount Module 4 as a sub-application
from module4.api.routes_4 import app as module4_app
app.mount("/api/4", module4_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
