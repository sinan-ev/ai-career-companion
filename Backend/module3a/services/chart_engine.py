import pandas as pd
from typing import List, Dict, Any
from ..services.context_builder import DataContext
import json

def generate_charts(
    plan: list[str],
    stats: dict,
    df: pd.DataFrame,
    context: DataContext,
    llm_client = None
) -> list[dict]:
    charts = []

    def _is_numeric(col_name: str) -> bool:
        """Return True if col_name exists in df and is a numeric dtype."""
        if col_name not in df.columns:
            return False
        return pd.api.types.is_numeric_dtype(df[col_name])


    # If we have an LLM, use it to intelligently design charts
    if llm_client:
        prompt = f"""
        You are an expert Data Analyst. I need to design between 5 and 6 meaningful, highly valuable charts for an executive dashboard.
        
        Dataset Context:
        Name: {context.dataset_name}
        Description: {context.dataset_description}
        
        Columns available:
        Categorical: {context.categorical_columns}
        Numeric: {context.numeric_columns}
        Datetime: {context.datetime_columns}
        
        Column Meanings:
        {json.dumps(context.column_meanings, indent=2)}
        
        Rules:
        1. DO NOT use ID columns (like ORDERNUMBER, ID, etc.) for mathematical aggregations (e.g., don't average them). You can count them to find volume.
        2. DO NOT use meaningless correlations (e.g. ORDERNUMBER vs QUANTITY).
        3. Pick logical relationships (e.g. Sales by Product Line, Monthly Trend of Sales, Quantity by Status).
        4. Focus on business value and actionable insights.
        5. For each chart, provide:
           - type: The chart type ('bar', 'line', 'histogram', 'horizontal_bar')
           - title: A descriptive business title (e.g., 'Total Sales by Product Line')
           - analysis_type: One of ('comparison', 'trend', 'distribution', 'top_n')
           - x_col: The column for the X-axis
           - y_col: The column for the Y-axis (or 'COUNT' if we are just counting the x_col occurrences)
           - agg: The aggregation method if y_col is a numeric column ('sum', 'mean', or 'none'). Default is 'sum' for business metrics like sales.

        Output strictly as a JSON object with a single key "charts" containing a list of chart objects. No markdown formatting.
        Example:
        {{
          "charts": [
            {{"type": "bar", "title": "Total Sales by Product Line", "analysis_type": "comparison", "x_col": "PRODUCTLINE", "y_col": "SALES", "agg": "sum"}},
            {{"type": "line", "title": "Sales Trend", "analysis_type": "trend", "x_col": "ORDERDATE", "y_col": "SALES", "agg": "sum"}},
            {{"type": "histogram", "title": "Distribution of Order Quantities", "analysis_type": "distribution", "x_col": "QUANTITYORDERED", "y_col": "none", "agg": "none"}}
          ]
        }}
        """
        
        try:
            response = llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content.strip()
            
            # clean potential markdown
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
                
            parsed = json.loads(raw_content.strip())
            chart_definitions = parsed.get("charts", [])
            
            for cdef in chart_definitions:
                x_col = cdef.get("x_col")
                y_col = cdef.get("y_col")
                agg = cdef.get("agg", "none")
                chart_type = cdef.get("type", "bar")
                title = cdef.get("title", "Chart")
                analysis_type = cdef.get("analysis_type", "comparison")
                
                x_data, y_data = [], []
                
                try:
                    if y_col == 'COUNT':
                        grouped = df[x_col].value_counts().head(15)
                        x_data = grouped.index.astype(str).tolist()
                        y_data = grouped.tolist()
                    elif chart_type == "histogram" or analysis_type == "distribution":
                        # histogram only makes sense on numeric x_col
                        if not _is_numeric(x_col):
                            # fall back to value_counts bar chart
                            grouped = df[x_col].value_counts().head(15)
                            x_data = grouped.index.astype(str).tolist()
                            y_data = grouped.tolist()
                            chart_type = "bar"
                        else:
                            counts_series = pd.Series(pd.cut(df[x_col], bins=10)).value_counts(sort=False)
                            bins = pd.cut(df[x_col], bins=10, retbins=True)[1]
                            x_data = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
                            y_data = counts_series.tolist()
                            chart_type = "bar"
                    elif agg in ("sum", "mean") and _is_numeric(y_col):
                        fn = df.groupby(x_col)[y_col].sum if agg == "sum" else df.groupby(x_col)[y_col].mean
                        grouped = fn().sort_values(ascending=False).head(15)
                        x_data = grouped.index.astype(str).tolist()
                        y_data = [round(v, 4) if pd.notna(v) else 0 for v in grouped.tolist()]
                    elif agg in ("sum", "mean") and not _is_numeric(y_col):
                        # LLM chose a non-numeric y_col for aggregation – fall back to COUNT of x_col
                        print(f"[chart_engine] y_col '{y_col}' is not numeric for agg='{agg}'; falling back to COUNT of '{x_col}'")
                        grouped = df[x_col].value_counts().head(15)
                        x_data = grouped.index.astype(str).tolist()
                        y_data = grouped.tolist()
                        y_col = 'COUNT'
                    else:
                        # Raw data path
                        subset = [x_col]
                        if y_col in df.columns:
                            subset.append(y_col)
                        sample = df.dropna(subset=subset).head(30)
                        if analysis_type == "trend" and pd.api.types.is_datetime64_any_dtype(df[x_col]):
                            sample = sample.sort_values(x_col)
                        x_data = sample[x_col].astype(str).tolist()
                        y_data = sample[y_col].tolist() if y_col in df.columns else []

                    # Skip chart if no usable data was produced
                    if not x_data or not y_data:
                        print(f"[chart_engine] Skipping '{title}' – empty data after processing.")
                        continue

                    figure = {
                        "data": [{"type": chart_type, "x": x_data, "y": y_data}],
                        "layout": {
                            "title": title,
                            "template": "plotly_white",
                            "font": {"family": "Inter"}
                        }
                    }
                    charts.append({
                        "type": chart_type,
                        "title": title,
                        "analysis_type": analysis_type,
                        "figure": figure
                    })
                except Exception as e:
                    print(f"Error generating chart {title}: {e}")
                    continue
                    
            if charts:
                return charts

        except Exception as e:
            import traceback
            print(f"Error calling LLM for charts: {e}")
            traceback.print_exc()
            pass # Fall back to heuristic

    # Fallback heuristic if LLM fails or is not provided
    print("Using heuristic chart generation")
    
    # 1. Distribution of a meaningful metric (exclude ID)
    meaningful_nums = [c for c in context.numeric_columns if not c.upper().endswith("ID") and not c.upper().endswith("NUMBER")]
    if meaningful_nums:
        col = meaningful_nums[0]
        counts_series = pd.Series(pd.cut(df[col], bins=10)).value_counts(sort=False)
        bins = pd.cut(df[col], bins=10, retbins=True)[1]
        x_data = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
        y_data = counts_series.tolist()
        charts.append({
            "type": "bar",
            "title": f"Distribution of {col}",
            "analysis_type": "distribution",
            "figure": {
                "data": [{"type": "bar", "x": x_data, "y": y_data}],
                "layout": {"title": f"Distribution of {col}", "template": "plotly_white"}
            }
        })

    # 2. Comparison (Categorical vs Meaningful Metric)
    if context.categorical_columns and meaningful_nums:
        cat_col = context.categorical_columns[0]
        num_col = meaningful_nums[0]
        grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
        x_data = grouped.index.astype(str).tolist()
        y_data = grouped.tolist()
        charts.append({
            "type": "bar",
            "title": f"Total {num_col} by {cat_col}",
            "analysis_type": "comparison",
            "figure": {
                "data": [{"type": "bar", "x": x_data, "y": y_data}],
                "layout": {"title": f"Total {num_col} by {cat_col}", "template": "plotly_white"}
            }
        })

    return charts
