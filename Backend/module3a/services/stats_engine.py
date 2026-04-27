# REAL DATA ANALYSIS (NO AI GUESSING)

import pandas as pd
from typing import Any, Dict, List
from ..services.context_builder import DataContext

def run_analysis(plan: List[str], df: pd.DataFrame, context: DataContext) -> Dict[str, Any]:
    results = {}
    
    # Analyze meaningful numeric columns
    meaningful_nums = [c for c in context.numeric_columns if not c.upper().endswith("ID") and not c.upper().endswith("NUMBER")]
    
    # Global distributions
    distributions = {}
    for col in meaningful_nums:
        distributions[col] = df[col].describe().to_dict()
    results["distributions"] = distributions
    
    # Global correlations
    if len(meaningful_nums) >= 2:
        results["correlations"] = df[meaningful_nums].corr().to_dict()
        
    # Group by categories
    comparisons = {}
    if context.categorical_columns and meaningful_nums:
        for cat_col in context.categorical_columns[:3]: # Take first 3 to avoid blowing up payload
            for num_col in meaningful_nums[:3]:
                grouped = df.groupby(cat_col)[num_col].agg(['mean','sum']).sort_values(by='sum', ascending=False).head(5).to_dict(orient='index')
                comparisons[f"{cat_col}_vs_{num_col}"] = grouped
    results["comparisons"] = comparisons
    
    return results
