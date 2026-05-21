import pandas as pd
from pathlib import Path
from fastapi import UploadFile
import io
from module1.config import get_settings

settings = get_settings()


async def load_dataset(file: UploadFile) -> tuple[pd.DataFrame, str]:
    """
    Reads an uploaded CSV or Excel file into a pandas DataFrame.
    
    Args:
        file (UploadFile): The file object uploaded via FastAPI.
        
    Returns:
        tuple[pd.DataFrame, str]: A tuple containing the loaded DataFrame and the original filename.
        
    Raises:
        ValueError: If the file type is not supported.
    """
    content = await file.read() #Reads uploaded file as bytes
    suffix = Path(file.filename).suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(io.BytesIO(content))
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return df, file.filename

