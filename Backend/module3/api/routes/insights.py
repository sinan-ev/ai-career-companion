from fastapi import APIRouter, HTTPException
from .analyze import analysis_results

router = APIRouter()

@router.get("/insights/{dataset_id}")
async def get_insights(dataset_id: str):
    """
    Retrieves statistical and qualitative insights generated for a given dataset.

    Args:
        dataset_id (str): The unique identifier of the dataset.

    Returns:
        dict: A dictionary containing:
            - insights (list): List of key insights found.
            - explanation (str): Detailed text explanations matching the insights.
            - confidence_score (float): Calculated metric of analysis reliability.

    Raises:
        HTTPException: If the dataset has not been analyzed yet.
    """
    if dataset_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[dataset_id]
    return {
        "insights": result.insights,
        "explanation": result.explanations,
        "confidence_score": result.confidence_score
    }
