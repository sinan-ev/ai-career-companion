import io
import os
import sys
import pytest
import pandas as pd
from fastapi import UploadFile

# Ensure Backend directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set a dummy GROQ_API_KEY if not already set, to prevent Pydantic validation errors on startup
os.environ.setdefault("GROQ_API_KEY", "mock_key_for_testing_purposes")

from module1.services.loader import load_dataset

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_load_dataset_csv():
    # Create a simple CSV file in memory
    csv_content = b"A,B\n1,3\n2,4"
    upload_file = UploadFile(
        filename="test.csv",
        file=io.BytesIO(csv_content)
    )
    df, filename = await load_dataset(upload_file)
    assert filename == "test.csv"
    assert not df.empty
    assert list(df.columns) == ["A", "B"]
    assert df.iloc[0]["A"] == 1

@pytest.mark.anyio
async def test_load_dataset_xlsx():
    # Create a simple XLSX file in memory
    df_orig = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    out = io.BytesIO()
    df_orig.to_excel(out, index=False, engine='openpyxl')
    out.seek(0)
    
    upload_file = UploadFile(
        filename="test.xlsx",
        file=out
    )
    df, filename = await load_dataset(upload_file)
    assert filename == "test.xlsx"
    assert not df.empty
    assert list(df.columns) == ["A", "B"]
    assert df.iloc[0]["A"] == 1

@pytest.mark.anyio
async def test_load_dataset_xls(monkeypatch):
    # Mock pd.read_excel since writing .xls might require extra deprecated libraries (xlwt)
    called = []
    def mock_read_excel(io_source, *args, **kwargs):
        called.append(io_source)
        return pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        
    monkeypatch.setattr(pd, "read_excel", mock_read_excel)
    
    upload_file = UploadFile(
        filename="test.xls",
        file=io.BytesIO(b"fake_xls_content")
    )
    df, filename = await load_dataset(upload_file)
    assert filename == "test.xls"
    assert not df.empty
    assert list(df.columns) == ["A", "B"]
    assert len(called) == 1
