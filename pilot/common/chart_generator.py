import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Dict, List, Optional, Tuple, Union
import re
from pilot.language.translation_handler import get_lang_text

class ChartGenerator:
    """
    A class to generate appropriate charts based on SQL query results.
    """
    
    @staticmethod
    def determine_chart_type(df: pd.DataFrame, sql_query: str = None) -> Optional[str]:
        """
        Determine the most appropriate chart type based on the dataframe structure and SQL query.
        
        Args:
            df: DataFrame containing the query results
            sql_query: The original SQL query (optional, used for additional context)
            
        Returns:
            String indicating chart type ('bar', 'pie', 'line', 'scatter', None)
        """
        # Print debug information
        print(f"DEBUG: Determining chart type for DataFrame with shape {df.shape}")
        print(f"DEBUG: DataFrame columns: {df.columns.tolist()}")
        print(f"DEBUG: DataFrame dtypes: {df.dtypes.to_dict()}")
        if sql_query:
            print(f"DEBUG: SQL Query: {sql_query}")
        
        # If dataframe is empty or too large, don't generate a chart
        if df.empty or len(df) > 1000:
            print("DEBUG: DataFrame is empty or too large, not generating chart")
            return None
            
        # Get number of columns and rows
        num_cols = len(df.columns)
        num_rows = len(df)
        
        # Check if this is an aggregation query
        is_aggregation = False
        if sql_query:
            is_aggregation = bool(re.search(r'(COUNT|SUM|AVG|MIN|MAX|GROUP\s+BY)', sql_query, re.IGNORECASE))
            print(f"DEBUG: Is aggregation query: {is_aggregation}")
        
        # Simple heuristics for chart type selection
        if num_cols == 2:
            print("DEBUG: DataFrame has 2 columns, checking for numeric values")
            # Two columns: likely a category and a value
            # Check if second column is numeric (more flexible check)
            second_col = df.columns[1]
            is_numeric = pd.api.types.is_numeric_dtype(df[second_col])
            print(f"DEBUG: Second column '{second_col}' is numeric: {is_numeric}")
            
            if is_numeric:
                if num_rows <= 10:
                    chart_type = 'pie' if num_rows >= 3 else 'bar'
                    print(f"DEBUG: Selected chart type: {chart_type}")
                    return chart_type
                else:
                    print("DEBUG: Selected chart type: bar")
                    return 'bar'
        
        elif num_cols >= 3:
            print("DEBUG: DataFrame has 3+ columns, checking for numeric columns")
            # Three or more columns with at least one numeric - more flexible check
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            print(f"DEBUG: Found numeric columns: {numeric_cols}")
            
            if len(numeric_cols) >= 1:
                if is_aggregation:
                    print("DEBUG: Selected chart type: bar (aggregation query)")
                    return 'bar'
                elif num_rows > 10:
                    # Time series detection
                    date_cols = [col for col in df.columns if df[col].dtype == 'datetime64[ns]' 
                                or (isinstance(df[col].dtype, object) and ('date' in str(col).lower() or 'ano' in str(col).lower()))]
                    print(f"DEBUG: Potential date columns: {date_cols}")
                    
                    if date_cols:
                        print("DEBUG: Selected chart type: line (time series)")
                        return 'line'
                    else:
                        print("DEBUG: Selected chart type: scatter")
                        return 'scatter'
                else:
                    print("DEBUG: Selected chart type: bar (default for 3+ columns)")
                    return 'bar'
        
        # Special case for time series data (like years)
        if num_cols == 2 and is_aggregation:
            first_col = df.columns[0]
            # Check if first column might be years or dates
            if df[first_col].dtype == 'int64' or 'ano' in str(first_col).lower() or 'year' in str(first_col).lower():
                print(f"DEBUG: Detected potential time series data in column '{first_col}'")
                print("DEBUG: Selected chart type: line (time series)")
                return 'line'
        
        # Default: no chart if we can't determine a good type
        print("DEBUG: Could not determine appropriate chart type")
        return None
    
    @staticmethod
    def generate_chart(df: pd.DataFrame, chart_type: str = None, sql_query: str = None) -> Optional[Dict]:
        """
        Generate a Plotly chart based on the dataframe and chart type.
        
        Args:
            df: DataFrame containing the query results
            chart_type: Type of chart to generate ('bar', 'pie', 'line', 'scatter')
            sql_query: The original SQL query (optional)
            
        Returns:
            Dictionary with Plotly figure JSON or None if chart can't be generated
        """
        if df.empty:
            return None
            
        # If chart_type not provided, determine it
        if not chart_type:
            chart_type = ChartGenerator.determine_chart_type(df, sql_query)
            
        if not chart_type:
            return None
            
        # Get appropriate columns for the chart
        x_col, y_col, color_col = ChartGenerator._select_columns(df, chart_type)
        
        # Generate the appropriate chart
        try:
            if chart_type == 'bar':
                fig = px.bar(
                    df, 
                    x=x_col, 
                    y=y_col,
                    color=color_col if color_col else None,
                    title=f"{y_col} {get_lang_text('chart_by')} {x_col}",
                    template="plotly_white"
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title=x_col),
                    yaxis=dict(title=y_col)
                )
                
            elif chart_type == 'pie':
                fig = px.pie(
                    df,
                    names=x_col,
                    values=y_col,
                    title=f"{get_lang_text('chart_distribution')} {y_col} {get_lang_text('chart_by')} {x_col}",
                    template="plotly_white"
                )
                
            elif chart_type == 'line':
                fig = px.line(
                    df,
                    x=x_col,
                    y=y_col,
                    color=color_col if color_col else None,
                    title=f"{y_col} {get_lang_text('chart_over')} {x_col}",
                    template="plotly_white",
                    markers=True
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title=x_col),
                    yaxis=dict(title=y_col)
                )
                
            elif chart_type == 'scatter':
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=color_col if color_col else None,
                    title=f"{y_col} {get_lang_text('chart_vs')} {x_col}",
                    template="plotly_white"
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title=x_col),
                    yaxis=dict(title=y_col)
                )
            else:
                return None
                
            # Convert to JSON for web display
            return {
                'chart_type': chart_type,
                'figure': fig.to_json()
            }
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            return None
    
    @staticmethod
    def _select_columns(df: pd.DataFrame, chart_type: str) -> Tuple[str, str, Optional[str]]:
        """
        Select appropriate columns for the chart based on data types.
        
        Returns:
            Tuple of (x_column, y_column, color_column)
        """
        print(f"DEBUG: Selecting columns for chart type: {chart_type}")
        
        # Get numeric columns - more flexible check
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        print(f"DEBUG: Numeric columns: {numeric_cols}")
        
        # Get categorical or string columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        print(f"DEBUG: Categorical columns: {categorical_cols}")
        
        # Get date columns or columns that might represent time
        date_cols = [col for col in df.columns if df[col].dtype == 'datetime64[ns]' 
                    or (isinstance(df[col].dtype, object) and ('date' in str(col).lower() or 'ano' in str(col).lower() or 'year' in str(col).lower()))]
        print(f"DEBUG: Date/time columns: {date_cols}")
        
        # Default selections
        x_col = df.columns[0]  # Default to first column
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        color_col = None
        
        # Select columns based on chart type and available data types
        if chart_type in ['bar', 'pie']:
            # For bar/pie charts, prefer categorical x and numeric y
            if categorical_cols and numeric_cols:
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
            elif len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                
        elif chart_type == 'line':
            # For line charts, prefer date x and numeric y
            if date_cols and numeric_cols:
                x_col = date_cols[0]
                y_col = numeric_cols[0]
            elif len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                
        elif chart_type == 'scatter':
            # For scatter plots, prefer numeric x and y
            if len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                if len(categorical_cols) > 0:
                    color_col = categorical_cols[0]
                    
        return x_col, y_col, color_col
