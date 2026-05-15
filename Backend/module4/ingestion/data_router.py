import os
import json
import pandas as pd
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

def load_module1_outputs(base_path: str = "../module_1/outputs") -> Dict[str, Any]:
    """
    Load cleaned dataset and metadata from Module 1.
    """
    dataset_path = os.path.join(base_path, "cleaned_dataset.csv")
    metadata_path = os.path.join(base_path, "column_metadata.json")
    report_path = os.path.join(base_path, "data_quality_report.json")
    
    result = {
        "dataset": pd.DataFrame(),
        "column_metadata": {},
        "quality_report": {}
    }
    
    try:
        if os.path.exists(dataset_path):
            result["dataset"] = pd.read_csv(dataset_path)
        else:
            logger.warning(f"Module 1 dataset not found at {dataset_path}")
            
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                result["column_metadata"] = json.load(f)
        else:
            logger.warning(f"Module 1 metadata not found at {metadata_path}")
            
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                result["quality_report"] = json.load(f)
        else:
            logger.warning(f"Module 1 quality report not found at {report_path}")
    except Exception as e:
        logger.error(f"Error loading Module 1 outputs: {e}")
        
    return result

def load_module2_outputs(base_path: str = "../module_2/outputs") -> Dict[str, Any]:
    """
    Load ML-ready dataset from Module 2.
    """
    dataset_path = os.path.join(base_path, "ml_ready_dataset.csv")
    report_path = os.path.join(base_path, "feature_engineering_report.json")
    
    result = {
        "ml_dataset": pd.DataFrame(),
        "feature_report": {}
    }
    
    try:
        if os.path.exists(dataset_path):
            result["ml_dataset"] = pd.read_csv(dataset_path)
        else:
            logger.warning(f"Module 2 dataset not found at {dataset_path}")
            
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                result["feature_report"] = json.load(f)
        else:
            logger.warning(f"Module 2 feature report not found at {report_path}")
    except Exception as e:
        logger.error(f"Error loading Module 2 outputs: {e}")
        
    return result

def load_module3_outputs(base_path: str = "../module_3/outputs") -> Dict[str, Any]:
    """
    Load AI insights and RAG results from Module 3.
    """
    insights_path = os.path.join(base_path, "insights.json")
    rag_path = os.path.join(base_path, "rag_results.json")
    summary_path = os.path.join(base_path, "analysis_summary.json")
    
    result = {
        "insights": [],
        "rag_results": [],
        "analysis_summary": {}
    }
    
    try:
        if os.path.exists(insights_path):
            with open(insights_path, 'r') as f:
                result["insights"] = json.load(f)
        else:
            logger.warning(f"Module 3 insights not found at {insights_path}")
            
        if os.path.exists(rag_path):
            with open(rag_path, 'r') as f:
                result["rag_results"] = json.load(f)
        else:
            logger.warning(f"Module 3 rag results not found at {rag_path}")
            
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                result["analysis_summary"] = json.load(f)
        else:
            logger.warning(f"Module 3 analysis summary not found at {summary_path}")
    except Exception as e:
        logger.error(f"Error loading Module 3 outputs: {e}")
        
    return result

def route_data(data: List[Dict[str, Any]], source: str = "request") -> pd.DataFrame:
    """
    Convert incoming request data (list of dicts) to DataFrame.
    """
    if not data:
        raise ValueError("Data is empty.")
    
    df = pd.DataFrame(data)
    
    is_valid, msg = validate_dataset(df)
    if not is_valid:
        raise ValueError(f"Dataset validation failed: {msg}")
        
    return df

def validate_dataset(df: pd.DataFrame, min_rows: int = 5) -> Tuple[bool, str]:
    """
    Checks: min row count, no fully empty columns, at least 2 columns.
    """
    if len(df) < min_rows:
        return False, f"Dataset has {len(df)} rows, minimum required is {min_rows}."
    
    if len(df.columns) < 2:
        return False, f"Dataset has {len(df.columns)} columns, minimum required is 2."
        
    empty_cols = df.columns[df.isnull().all()].tolist()
    if empty_cols:
        logger.warning(f"Dataset contains fully empty columns: {empty_cols}. These may be ignored.")
        
    return True, "Valid"
