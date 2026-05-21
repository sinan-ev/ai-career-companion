from fastapi import APIRouter, HTTPException
from .analyze import analysis_results

router = APIRouter()

@router.get("/charts/{dataset_id}")
async def get_charts(dataset_id: str):
    """
    Retrieves the generated visualization charts for a analyzed dataset.

    Args:
        dataset_id (str): The unique identifier of the dataset.

    Returns:
        dict: A dictionary containing a list of chart specifications (e.g., plot configurations).

    Raises:
        HTTPException: If the dataset has not been analyzed yet.
    """
    if dataset_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[dataset_id]
    return {"charts": [chart.dict() for chart in result.charts] if hasattr(result.charts[0], "dict") else result.charts}
