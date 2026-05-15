from fastapi import APIRouter, HTTPException
from ..schemas import ChatRequest, ChatResponse
from .upload import datasets
from ...services.chat_engine import chat
from ...services.context_builder import build_context
from ...services.rag_engine import build_rag

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    dataset_id = req.dataset_id
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    df = datasets[dataset_id]
    
    # Mock context
    module1_output = {
        "dataset_name": "Dataset",
        "dataset_summary": {
            "description": "Dataset",
            "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
            "categorical_columns": df.select_dtypes(include="object").columns.tolist(),
            "datetime_columns": df.select_dtypes(include="datetime").columns.tolist(),
            "column_meanings": {col: "Meaning" for col in df.columns}
        }
    }
    context = build_context(module1_output, {})
    store, retriever = build_rag(context)
    
    from module1.utils.llm_client import get_groq_client
    try:
        llm_client = get_groq_client()
    except Exception:
        llm_client = None
        
    answer = chat(req.query, retriever, df, context, llm_client, req.history)
    return ChatResponse(answer=answer, sources=[])
