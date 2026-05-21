from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
import pandas as pd
import io

router = APIRouter()

# In-memory storage for datasets mapping (for simple implementation)
datasets = {}

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Uploads and parses a dataset file (CSV, Excel, or JSON) and stores it in-memory.

    Args:
        file (UploadFile): The uploaded file from the request form body.

    Returns:
        dict: A dictionary containing:
            - dataset_id (str): Generated UUID for referencing this dataset in subsequent requests.
            - preview (list): A list of dictionaries representing the first 10 rows.
            - columns (list): List of column names in the dataset.
            - row_count (int): Total number of rows parsed from the dataset.

    Raises:
        HTTPException:
            - 415 (Unsupported file format) if the extension is not csv, xlsx, xls, or json.
            - 400 (Bad Request) if any exception occurs during pandas parsing.
    """
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
