from fastapi import APIRouter, HTTPException
from .analyze import analysis_results

router = APIRouter()

@router.get("/insights/{dataset_id}")
async def get_insights(dataset_id: str):
    if dataset_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[dataset_id]
    return {
        "insights": result.insights,
        "explanation": result.explanations,
        "confidence_score": result.confidence_score
    }
