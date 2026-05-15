from fastapi import APIRouter, HTTPException
from ..schemas import AnalyzeRequest
from .upload import datasets
from ...core.pipeline import run_module3
import pandas as pd

router = APIRouter()

analysis_results = {}

@router.post("/analyze")
async def analyze_dataset(req: AnalyzeRequest):
    dataset_id = req.dataset_id
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    df = datasets[dataset_id]
    
    # Mock module1 and module2 outputs
    module1_output = {
        "dataset_name": "Uploaded Dataset",
        "dataset_summary": {
            "description": "Dataset description",
            "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
            "categorical_columns": df.select_dtypes(include="object").columns.tolist(),
            "datetime_columns": df.select_dtypes(include="datetime").columns.tolist(),
            "column_meanings": {col: "A column" for col in df.columns}
        }
    }
    module2_output = {}
    
    result = run_module3(module1_output, module2_output, df, user_query=req.query)
    analysis_results[dataset_id] = result
    
    return result
