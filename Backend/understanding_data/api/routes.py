from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from core.pipeline import run_pipeline
from services.validator import ValidationError
from models.response_model import AnalysisResponse
from utils.constants import ALLOWED_EXTENSIONS
from config import get_settings

settings = get_settings()
router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze any CSV or Excel dataset",
    description="""
Upload a CSV or Excel file and receive:
- Dataset domain and type detection
- Column-by-column plain-English meanings
- Data quality report (missing values, duplicates)
- AI-generated summary and analysis suggestions
    """,
)

async def analyze_dataset(
    file: UploadFile = File(
        ...,
        description="CSV (.csv) or Excel (.xlsx / .xls) file to analyze"
    )
):
    # ── Pre-flight checks (before touching the pipeline) ─────── 
    if not file.filename: #checking file type 
        raise HTTPException(status_code=400, detail="No file provided.")

    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )

    # ── Run full pipeline ───────────────────────────────────────
    try:
        result = await run_pipeline(file)
        return result

    except ValidationError as e:
        # Known validation failures — 422 Unprocessable Entity
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        # Unexpected failures — log and return 500
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {str(e)}",
        )


@router.get(
    "/health",
    summary="Health check",
    description="Returns app status and version.",
)
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }