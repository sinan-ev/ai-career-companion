from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import pandas as pd
import io

router = APIRouter()

# In-memory storage for datasets mapping (for simple implementation)
datasets = {}

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    suffix = file.filename.split(".")[-1].lower()
    if suffix not in ["csv", "xlsx", "xls", "json"]:
        raise HTTPException(status_code=415, detail="Unsupported file format")

    content = await file.read()
    try:
        if suffix == "csv":
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding='latin-1')
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(content), encoding='windows-1252')
        elif suffix in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(content))
        elif suffix == "json":
            df = pd.read_json(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    dataset_id = str(uuid.uuid4())
    datasets[dataset_id] = df
    
    return {
        "dataset_id": dataset_id,
        "preview": df.head(10).to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "row_count": len(df)
    }
