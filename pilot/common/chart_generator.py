import json
import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, Any
import asyncio

from pilot.configs.config import Config
from pilot.scene.chat_db.auto_execute.chat import ChatWithDbAutoExecute
from pilot.scene.base_chat import BaseChat
from pilot.language.translation_handler import get_lang_text

CFG = Config()

class ChartGenerator:
    """
    A class to generate appropriate charts based on SQL query results.
    Uses LLM to assist in chart type selection and axis configuration.
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
            # Special case for time series data (like years)
            if pd.api.types.is_numeric_dtype(df[first_col]) and ('ano' in str(first_col).lower() or 'year' in str(first_col).lower() or all(isinstance(v, (int, float)) and 1900 <= v <= 2100 for v in df[first_col].dropna().unique())):
                print(f"DEBUG: Detected potential time series data in column '{first_col}'")
                print("DEBUG: Selected chart type: line (time series)")
                return 'line'
        
        # Default: no chart if we can't determine a good type
        print("DEBUG: Could not determine appropriate chart type")
        return None
    
    @staticmethod
    async def generate_chart(df: pd.DataFrame, chart_type: str = None, sql_query: str = None, test_mode: bool = False) -> Optional[Dict]:
        """
        Generate a Plotly chart based on the dataframe and chart type.
        Uses LLM to assist in chart type selection and axis configuration.
        
        Args:
            df: DataFrame containing the query results
            chart_type: Type of chart to generate ('bar', 'pie', 'line', 'scatter', 'area', 'histogram')
            sql_query: The original SQL query (optional)
            
        Returns:
            Dictionary with chart data or None if chart generation fails
            
        Note:
            When test_mode=True, uses simulated LLM responses instead of calling the actual LLM service.
        """
        if df.empty:
            return None
        
        llm_chart_recommendation = None
        llm_axis_config = None
        column_types = {}
        llm_recommendation = None
        
        try:
            # Consultar o LLM para recomendação de gráfico se o tipo não foi especificado
            if not chart_type:
                print("DEBUG: Consultando LLM para recomendação de tipo de gráfico")
                llm_recommendation = await ChartGenerator.ask_llm_for_chart_type(df, sql_query, test_mode=test_mode)
                
                if llm_recommendation and isinstance(llm_recommendation, dict):
                    chart_type = llm_recommendation.get("chart_type", "bar")
                    x_col = llm_recommendation.get("x_axis", df.columns[0])
                    y_col = llm_recommendation.get("y_axis", df.columns[1] if len(df.columns) > 1 else df.columns[0])
                    color_col = llm_recommendation.get("color_by")
                    explanation = llm_recommendation.get("explanation", "")
                    
                    # Obter os tipos semânticos das colunas identificados pelo LLM
                    column_types = llm_recommendation.get("column_types", {})
                    
                    # Aplicar os tipos semânticos ao DataFrame
                    if column_types:
                        print("DEBUG: Aplicando tipos semânticos identificados pelo LLM")
                        df = ChartGenerator.apply_semantic_types(df, column_types)
                
                # Se o LLM não conseguir determinar um tipo, usar o método heurístico tradicional
                if not chart_type:
                    print("DEBUG: LLM não retornou tipo de gráfico, usando heurística")
                    chart_type = ChartGenerator.determine_chart_type(df, sql_query)
                else:
                    print(f"DEBUG: LLM recomendou gráfico do tipo: {chart_type}")
                    print(f"DEBUG: Explicação do LLM: {explanation}")
            
            if not chart_type:
                print("DEBUG: Não foi possível determinar um tipo de gráfico adequado")
                return None
            
            # Obter colunas para o gráfico (do LLM ou pelo método tradicional)
            if llm_recommendation and "x_axis" in llm_recommendation and "y_axis" in llm_recommendation:
                x_col = llm_recommendation["x_axis"]
                y_col = llm_recommendation["y_axis"]
                color_col = llm_recommendation.get("color_by", None)
                print(f"DEBUG: Usando colunas recomendadas pelo LLM - x: {x_col}, y: {y_col}, color: {color_col}")
            else:
                # Usar o método tradicional para selecionar colunas
                x_col, y_col, color_col = ChartGenerator._select_columns(df, chart_type)
            
            # Verificar se as colunas existem no DataFrame
            if x_col not in df.columns or y_col not in df.columns:
                print(f"DEBUG: Colunas recomendadas não existem no DataFrame. Usando método tradicional.")
                x_col, y_col, color_col = ChartGenerator._select_columns(df, chart_type)
            else:
                # Verificar se existe coluna de faturamento para priorizar
                faturamento_cols = [col for col in df.columns if col in df.select_dtypes(include=['number']).columns and 
                                   ('faturamento' in col.lower() or 'total' in col.lower() or 'valor' in col.lower())]
                if faturamento_cols:
                    print(f"DEBUG: Overriding LLM recommendation to prioritize '{faturamento_cols[0]}' for Y axis")
                    y_col = faturamento_cols[0]
                
            # Aplicar regras heurísticas para garantir que colunas de anos sejam sempre tratadas como categorias
            # Isso é feito mesmo se o LLM não identificou tipos semânticos ou se não foi consultado
            if not column_types or x_col not in column_types:
                print(f"DEBUG: Aplicando regras heurísticas para garantir tratamento correto de colunas temporais")
                df = ChartGenerator.apply_semantic_types(df)
            
            # Consultar o LLM para configuração de eixos
            print(f"DEBUG: Consultando LLM para configuração de eixos do gráfico {chart_type}")
            axis_config = await ChartGenerator.ask_llm_for_axis_config(df, chart_type, x_col, y_col, test_mode=test_mode)
            
            # Log das colunas selecionadas
            print(f"DEBUG: Colunas finais para o gráfico - x_col: '{x_col}', y_col: '{y_col}', color_col: '{color_col}'")
            
            # Gerar o gráfico apropriado
            try:
                # Obter títulos dos eixos da configuração do LLM ou usar padrões
                x_title = axis_config.get("x_title", x_col) if axis_config else x_col
                y_title = axis_config.get("y_title", y_col) if axis_config else y_col
                color_scheme = axis_config.get("color_scheme", "plotly") if axis_config else "plotly"
                x_rotation = int(axis_config.get("x_rotation", 0)) if axis_config else 0
                y_scale = axis_config.get("y_scale", "linear") if axis_config else "linear"
                
                # Verificar se os valores são muito grandes e precisam de formatação especial
                max_value = df[y_col].max() if pd.api.types.is_numeric_dtype(df[y_col]) else 0
                
                # Determinar o formato adequado com base na magnitude dos valores
                tick_format = None
                tick_suffix = ""
                
                if max_value >= 1000000:  # Milhões
                    tick_format = ".1s"
                elif max_value >= 1000:  # Milhares
                    tick_format = ".3s"
                
                # Configurações comuns para todos os gráficos
                common_layout = dict(
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(
                        title=x_title,
                        tickangle=x_rotation
                    ),
                    yaxis=dict(
                        title=y_title,
                        type=y_scale,
                        # Formatação para valores grandes
                        tickformat=tick_format,
                        ticksuffix=tick_suffix
                    ),
                    colorway=px.colors.qualitative.Plotly if color_scheme == "plotly" else None
                )
                
                # Registrar os tipos de dados após possíveis conversões
                print(f"DEBUG: Tipos de dados após conversões semânticas: {df.dtypes.to_dict()}")
                
                # Configurar o gráfico com base no tipo
                if chart_type == 'bar':
                    fig = px.bar(
                        df, 
                        x=x_col, 
                        y=y_col,
                        color=color_col if color_col else None,
                        title=f"{y_title} {get_lang_text('chart_by')} {x_title}",
                        template="plotly_white"
                    )
                    fig.update_layout(**common_layout)
                    
                elif chart_type == 'pie':
                    fig = px.pie(
                        df,
                        names=x_col,
                        values=y_col,
                        title=f"{get_lang_text('chart_distribution')} {y_title} {get_lang_text('chart_by')} {x_title}",
                        template="plotly_white"
                    )
                    
                elif chart_type == 'line':
                    fig = px.line(
                        df,
                        x=x_col,
                        y=y_col,
                        color=color_col if color_col else None,
                        title=f"{y_title} {get_lang_text('chart_over')} {x_title}",
                        template="plotly_white",
                        markers=True
                    )
                    fig.update_layout(**common_layout)
                    
                elif chart_type == 'scatter':
                    fig = px.scatter(
                        df,
                        x=x_col,
                        y=y_col,
                        color=color_col if color_col else None,
                        title=f"{y_title} {get_lang_text('chart_vs')} {x_title}",
                        template="plotly_white"
                    )
                    fig.update_layout(**common_layout)
                    
                elif chart_type == 'area':
                    fig = px.area(
                        df,
                        x=x_col,
                        y=y_col,
                        color=color_col if color_col else None,
                        title=f"{y_title} {get_lang_text('chart_over')} {x_title}",
                        template="plotly_white"
                    )
                    fig.update_layout(**common_layout)
                    
                elif chart_type == 'histogram':
                    fig = px.histogram(
                        df,
                        x=x_col,
                        y=y_col if y_col != x_col else None,
                        color=color_col if color_col else None,
                        title=f"{get_lang_text('chart_distribution')} {x_title}",
                        template="plotly_white"
                    )
                    fig.update_layout(**common_layout)
                    
                else:
                    # Fallback para gráfico de barras se o tipo não for reconhecido
                    print(f"DEBUG: Tipo de gráfico '{chart_type}' não reconhecido, usando 'bar' como fallback")
                    fig = px.bar(
                        df, 
                        x=x_col, 
                        y=y_col,
                        color=color_col if color_col else None,
                        title=f"{y_title} {get_lang_text('chart_by')} {x_title}",
                        template="plotly_white"
                    )
                    fig.update_layout(**common_layout)
                
                # Debug dos dados do gráfico antes da conversão para JSON
                print(f"DEBUG: Layout do gráfico antes da conversão JSON: {fig.layout}")
                print(f"DEBUG: Dados do gráfico antes da conversão JSON: {fig.data}")
                
                # Converter para JSON para exibição web
                fig_json = fig.to_json()
                
                # Debug de uma amostra da saída JSON
                print(f"DEBUG: Amostra JSON (primeiros 200 caracteres): {fig_json[:200]}...")
                
                # Incluir informações da recomendação do LLM no retorno
                explanation = ""
                if llm_chart_recommendation and "explanation" in llm_chart_recommendation:
                    explanation = llm_chart_recommendation["explanation"]
                
                return {
                    'chart_type': chart_type,
                    'figure': fig_json,
                    'llm_explanation': explanation
                }
                
            except Exception as e:
                print(f"Erro ao gerar gráfico específico: {e}")
                return None
                
        except Exception as e:
            print(f"Erro geral na geração de gráfico: {e}")
            return None
    
    @staticmethod
    def apply_semantic_types(df: pd.DataFrame, column_types: Dict[str, str] = None) -> pd.DataFrame:
        """
        Aplica os tipos semânticos identificados pelo LLM ao DataFrame.
        Converte colunas numéricas para categóricas quando identificadas como tal.
        
        Esta função é crucial para garantir que colunas numéricas que representam categorias
        (como anos, códigos, IDs) sejam tratadas corretamente na visualização.
        
        Args:
            df: DataFrame original
            column_types: Dicionário com os tipos semânticos identificados pelo LLM
                         Valores possíveis: "id", "category", "numeric", "temporal"
            
        Returns:
            DataFrame com os tipos ajustados para visualização adequada
        """
        df_copy = df.copy()
        
        # Primeiro, aplicar regras heurísticas para colunas de anos
        # Isso garante que colunas de anos sejam sempre tratadas como categorias,
        # independentemente da recomendação do LLM
        for col in df_copy.columns:
            # Verificar se a coluna tem nome relacionado a anos
            is_year_column = any(year_term in col.lower() for year_term in ['ano', 'year', 'anual', 'yearly'])
            
            # Verificar se a coluna tem valores que parecem anos (números entre 1900 e 2100)
            if pd.api.types.is_numeric_dtype(df_copy[col]):
                values = df_copy[col].dropna().unique()
                looks_like_years = False
                
                if len(values) > 0 and len(values) <= 200:  # Não muitos valores únicos
                    # Verificar se os valores parecem anos
                    if all(isinstance(v, (int, float)) and 1900 <= v <= 2100 and v.is_integer() for v in values):
                        looks_like_years = True
                        
                if is_year_column or looks_like_years:
                    print(f"DEBUG: Regra heurística - Convertendo coluna '{col}' para string (parece ser ano)")
                    df_copy[col] = df_copy[col].astype(str)
        
        # Depois, aplicar os tipos semânticos identificados pelo LLM (se fornecidos)
        if column_types:
            print(f"DEBUG: Aplicando tipos semânticos: {column_types}")
            
            for col, sem_type in column_types.items():
                if col not in df_copy.columns:
                    print(f"DEBUG: Coluna '{col}' não encontrada no DataFrame, ignorando")
                    continue
                    
                # Se a coluna for numérica mas semanticamente for uma categoria ou ID
                if pd.api.types.is_numeric_dtype(df_copy[col]):
                    if sem_type in ["category", "id"]:
                        print(f"DEBUG: Convertendo coluna numérica '{col}' para categoria (tipo semântico: {sem_type})")
                        # Converter para string para tratá-la como categoria
                        df_copy[col] = df_copy[col].astype(str)
                    elif sem_type == "temporal":
                        # Para dados temporais, também é melhor tratar como string para evitar agregação numérica
                        print(f"DEBUG: Convertendo coluna temporal '{col}' para string")
                        df_copy[col] = df_copy[col].astype(str)
                    else:
                        print(f"DEBUG: Mantendo coluna '{col}' como numérica (tipo semântico: {sem_type})")
                else:
                    print(f"DEBUG: Coluna '{col}' já é não-numérica, mantendo tipo original")
                
        return df_copy
    
    @staticmethod
    async def ask_llm_for_chart_type(df: pd.DataFrame, sql_query: str = None, test_mode: bool = False) -> Dict[str, Any]:
        """
        Consulta o LLM para determinar o tipo de gráfico mais adequado para os dados.
        
        Args:
            df: DataFrame contendo os resultados da consulta
            sql_query: A consulta SQL original (opcional)
            test_mode: Se True, retorna uma resposta simulada para testes
            
        Returns:
            Dicionário com tipo de gráfico e explicação
        """
        print("DEBUG: Consultando LLM para determinar tipo de gráfico")
                # Se estiver em modo de teste, retornar uma resposta simulada
        if test_mode:
            print("DEBUG: Usando resposta simulada para testes")
            # Determinar as colunas mais adequadas com base nos tipos de dados
            numeric_columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            categorical_columns = [col for col in df.columns if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col])]
            
            x_axis = categorical_columns[0] if categorical_columns else df.columns[0]
            y_axis = numeric_columns[0] if numeric_columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
            
            # Simular tipos semânticos para teste
            column_types = {}
            for col in df.columns:
                if col in numeric_columns and "id" in col.lower() or "codigo" in col.lower() or "code" in col.lower():
                    column_types[col] = "id"
                elif col in numeric_columns and ("ano" in col.lower() or "year" in col.lower() or "mes" in col.lower() or "month" in col.lower()):
                    column_types[col] = "category"
                elif col in numeric_columns:
                    column_types[col] = "numeric"
                else:
                    column_types[col] = "category"
            
            return {
                "chart_type": "bar",
                "explanation": "Gráfico de barras recomendado para comparar valores entre categorias (resposta simulada para teste).",
                "x_axis": x_axis,
                "y_axis": y_axis,
                "color_by": categorical_columns[1] if len(categorical_columns) > 1 else None,
                "column_types": column_types
            }
        
        # Preparar informações sobre o DataFrame para o LLM
        df_info = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
            "sample_data": df.head(5).to_dict(orient='records') if not df.empty else []
        }
        
        # Criar prompt para o LLM
        prompt = f"""
        Você é um especialista em visualização de dados. Analise os resultados desta consulta SQL e determine o tipo de gráfico mais adequado para representar estes dados.
        
        Consulta SQL: {sql_query if sql_query else 'Não fornecida'}
        
        Informações sobre os dados:
        - Formato: {df_info['shape']}
        - Colunas: {df_info['columns']}
        - Tipos de dados: {df_info['dtypes']}
        - Amostra dos dados: {df_info['sample_data'][:3]}
        
        IMPORTANTE: Analise cada coluna e determine seu tipo semântico real, independente do tipo de dados no DataFrame:
        1. Identifique colunas que parecem ser códigos ou identificadores (mesmo que sejam numéricas)
        2. Identifique colunas que são categóricas (mesmo que sejam numéricas, como anos, códigos de produto, etc.)
        3. Identifique colunas que são realmente numéricas e representam valores quantitativos
        4. Identifique colunas temporais (datas, anos, meses, etc.)
        
        Escolha o tipo de gráfico mais adequado entre: 'bar', 'pie', 'line', 'scatter', 'area', 'histogram'.
        Explique brevemente sua escolha e sugira configurações para os eixos x e y.
        
        Responda no formato JSON:
        {{"chart_type": "tipo_escolhido", 
          "explanation": "explicação", 
          "x_axis": "coluna_x", 
          "y_axis": "coluna_y", 
          "color_by": "coluna_cor_opcional",
          "column_types": {{"nome_coluna": "tipo_semântico"}} 
        }}
        
        Onde "tipo_semântico" pode ser: "id" (para identificadores), "category" (para categorias), "numeric" (para valores quantitativos), "temporal" (para datas/tempo).
        """
        
        try:
            # Criar uma sessão temporária para consultar o LLM
            chat_session_id = f"chart_recommendation_{id(df)}"
            llm_chat = ChatWithDbAutoExecute(
                chat_session_id=chat_session_id,
                db_name="temp_db",  # Nome temporário, não será usado
                user_input=prompt
            )
            
            # Configurar valores de entrada para o prompt
            input_values = await llm_chat.generate_input_values()
            input_values["input"] = prompt  # Substituir a entrada pelo nosso prompt específico
            
            # Obter resposta do LLM
            response = await llm_chat.llm_client.generate_stream_async(
                messages=llm_chat.prompt_template.format(**input_values),
                temperature=0.1,  # Baixa temperatura para respostas mais determinísticas
                max_tokens=500
            )
            
            # Processar resposta
            response_text = "".join([chunk for chunk in response])
            print(f"DEBUG: Resposta do LLM: {response_text[:200]}...")
            
            # Extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    print(f"DEBUG: JSON extraído: {result}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Erro ao decodificar JSON: {e}")
            
            # Fallback se não conseguir extrair JSON
            return {"chart_type": "bar", "explanation": "Fallback: não foi possível obter recomendação do LLM", "x_axis": df.columns[0], "y_axis": df.columns[1] if len(df.columns) > 1 else df.columns[0]}
            
        except Exception as e:
            print(f"DEBUG: Erro ao consultar LLM: {e}")
            # Fallback em caso de erro
            return {"chart_type": "bar", "explanation": f"Erro: {str(e)}", "x_axis": df.columns[0], "y_axis": df.columns[1] if len(df.columns) > 1 else df.columns[0]}
    
    @staticmethod
    async def ask_llm_for_axis_config(df: pd.DataFrame, chart_type: str, x_col: str, y_col: str, test_mode: bool = False) -> Dict[str, Any]:
        """
        Consulta o LLM para obter configurações avançadas para os eixos do gráfico.
        
        Args:
            df: DataFrame contendo os resultados da consulta
            chart_type: Tipo de gráfico selecionado
            x_col: Coluna selecionada para o eixo X
            y_col: Coluna selecionada para o eixo Y
            test_mode: Se True, retorna uma resposta simulada para testes
            
        Returns:
            Dicionário com configurações para os eixos
        """
        print(f"DEBUG: Consultando LLM para configuração de eixos do gráfico {chart_type}")
        
        # Se estiver em modo de teste, retornar uma resposta simulada
        if test_mode:
            print("DEBUG: Usando resposta simulada para configuração de eixos")
            return {
                "x_title": x_col.replace('_', ' ').title(),
                "y_title": y_col.replace('_', ' ').title(),
                "x_rotation": 0 if len(df[x_col].unique()) < 10 else 45,
                "color_scheme": "default",
                "scale_type": "linear"
            }
        
        # Obter informações sobre as colunas selecionadas
        x_data = df[x_col].head(5).tolist() if not df.empty else []
        y_data = df[y_col].head(5).tolist() if not df.empty else []
        
        # Criar prompt para o LLM
        prompt = f"""
        Você é um especialista em visualização de dados. Configure os eixos para um gráfico do tipo '{chart_type}' 
        que usará a coluna '{x_col}' como eixo X e '{y_col}' como eixo Y.
        
        Amostra de dados do eixo X: {x_data}
        Amostra de dados do eixo Y: {y_data}
        
        Forneça configurações para melhorar a visualização deste gráfico, incluindo:
        - Títulos apropriados para os eixos
        - Formato de números (se aplicável)
        - Rotação de rótulos (se necessário)
        - Escala (linear, logarítmica)
        - Cores recomendadas
        
        Responda no formato JSON:
        {{"x_title": "título_eixo_x", "y_title": "título_eixo_y", "x_format": "formato_x", "y_format": "formato_y", 
        "x_rotation": graus_rotação, "color_scheme": "esquema_cores", "y_scale": "escala_y"}}
        """
        
        try:
            # Criar uma sessão temporária para consultar o LLM
            chat_session_id = f"axis_config_{id(df)}"
            llm_chat = ChatWithDbAutoExecute(
                chat_session_id=chat_session_id,
                db_name="temp_db",  # Nome temporário, não será usado
                user_input=prompt
            )
            
            # Configurar valores de entrada para o prompt
            input_values = await llm_chat.generate_input_values()
            input_values["input"] = prompt  # Substituir a entrada pelo nosso prompt específico
            
            # Obter resposta do LLM
            response = await llm_chat.llm_client.generate_stream_async(
                messages=llm_chat.prompt_template.format(**input_values),
                temperature=0.1,  # Baixa temperatura para respostas mais determinísticas
                max_tokens=500
            )
            
            # Processar resposta
            response_text = "".join([chunk for chunk in response])
            print(f"DEBUG: Resposta do LLM para configuração de eixos: {response_text[:200]}...")
            
            # Extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    print(f"DEBUG: JSON de configuração extraído: {result}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Erro ao decodificar JSON de configuração: {e}")
            
            # Fallback se não conseguir extrair JSON
            return {"x_title": x_col, "y_title": y_col, "x_format": "", "y_format": "", "x_rotation": 0, "color_scheme": "plotly", "y_scale": "linear"}
            
        except Exception as e:
            print(f"DEBUG: Erro ao consultar LLM para configuração de eixos: {e}")
            # Fallback em caso de erro
            return {"x_title": x_col, "y_title": y_col, "x_format": "", "y_format": "", "x_rotation": 0, "color_scheme": "plotly", "y_scale": "linear"}
    
    @staticmethod
    def _select_columns(df: pd.DataFrame, chart_type: str) -> Tuple[str, str, Optional[str]]:
        """
        Select appropriate columns for the chart based on data types.
        
        Prioriza colunas temporais para o eixo X, colunas numéricas para o eixo Y,
        e colunas categóricas para separação por cor.
        
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
        
        # Get temporal columns (datetime or columns that might represent time)
        # Expanded detection for temporal columns
        temporal_terms = ['date', 'data', 'ano', 'year', 'month', 'mes', 'mês', 
                         'trimestre', 'quarter', 'semestre', 'semester', 
                         'dia', 'day', 'hora', 'hour', 'time', 'tempo', 
                         'período', 'period', 'timestamp']
        
        # Detect temporal columns based on name or data type
        temporal_cols = []
        for col in df.columns:
            # Check if column is datetime type
            if df[col].dtype == 'datetime64[ns]':
                temporal_cols.append(col)
                print(f"DEBUG: Detected datetime column '{col}' as temporal")
                continue
            
            # Verificar se o nome da coluna é exatamente 'ano' ou 'year'
            if col.lower() == 'ano' or col.lower() == 'year':
                temporal_cols.append(col)
                print(f"DEBUG: Detected column '{col}' as temporal (exact match)")
                continue
                
            # Check if column name contains temporal terms
            if any(term in str(col).lower() for term in temporal_terms):
                temporal_cols.append(col)
                print(f"DEBUG: Detected column '{col}' as temporal based on name")
                continue
                
            # Se for uma coluna numérica, verificar se os valores parecem anos
            if col in numeric_cols:
                values = df[col].dropna().unique()
                if len(values) > 0 and len(values) <= 200:  # Not too many unique values
                    # Check if values look like years
                    try:
                        if all(isinstance(v, (int, float)) and 1900 <= v <= 2100 and float(v).is_integer() for v in values):
                            temporal_cols.append(col)
                            print(f"DEBUG: Detected numeric column '{col}' as temporal (year values)")
                    except (TypeError, ValueError):
                        # Ignore errors if values can't be compared
                        pass
        
        print(f"DEBUG: Temporal columns: {temporal_cols}")
        
        # Default selections
        x_col = df.columns[0]  # Default to first column
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        color_col = None
        
        # Verificar se existe coluna de faturamento para priorizar em qualquer situação
        faturamento_cols = [col for col in numeric_cols if 'faturamento' in col.lower() or 'total' in col.lower() or 'valor' in col.lower()]
        if faturamento_cols:
            # Guardar para usar mais tarde, independentemente do fluxo de decisão
            priority_y_col = faturamento_cols[0]
            print(f"DEBUG: Found priority column for Y axis: '{priority_y_col}'")
        else:
            priority_y_col = None
        
        # NOVA LÓGICA DE PRIORIZAÇÃO:
        
        # 1. Priorizar colunas temporais para o eixo X, mas verificar se têm valores distintos
        if temporal_cols:
            x_col = temporal_cols[0]  # Use a primeira coluna temporal encontrada
            
            # Verificar se a coluna temporal tem mais de um valor único
            unique_values = df[x_col].nunique()
            print(f"DEBUG: Temporal column '{x_col}' has {unique_values} unique values")
            
            if unique_values > 1:
                # Se tiver mais de um valor único, usar como eixo X
                print(f"DEBUG: Selected temporal column '{x_col}' for X axis")
                
                # 2. Selecionar uma coluna numérica para o eixo Y (que não seja a coluna temporal)
                y_candidates = [col for col in numeric_cols if col not in temporal_cols]
                if y_candidates:
                    y_col = y_candidates[0]  # Use a primeira coluna numérica não-temporal
                    print(f"DEBUG: Selected numeric column '{y_col}' for Y axis")
                else:
                    # Se não houver colunas numéricas não-temporais, use a primeira coluna não-temporal
                    non_temporal_cols = [col for col in df.columns if col not in temporal_cols]
                    if non_temporal_cols:
                        y_col = non_temporal_cols[0]
                        print(f"DEBUG: No suitable numeric column found. Using '{y_col}' for Y axis")
            else:
                # Se a coluna temporal tem apenas um valor único (como todos os anos = 2020)
                # Não usar como eixo X, tratar como se não houvesse coluna temporal
                print(f"DEBUG: Temporal column '{x_col}' has only one unique value. Not using as X axis.")
                
                # Priorizar colunas categóricas para o eixo X
                if categorical_cols:
                    x_col = categorical_cols[0]
                    print(f"DEBUG: Using categorical column '{x_col}' for X axis instead of temporal column with single value")
                
                # Priorizar colunas de faturamento para o eixo Y
                faturamento_cols = [col for col in numeric_cols if 'faturamento' in col.lower() or 'total' in col.lower() or 'valor' in col.lower()]
                if faturamento_cols:
                    y_col = faturamento_cols[0]
                    print(f"DEBUG: Prioritizing '{y_col}' column for Y axis (faturamento/total/valor)")
                elif numeric_cols:
                    y_col = numeric_cols[0]
                    print(f"DEBUG: Using numeric column '{y_col}' for Y axis")
                
                # Não usar a coluna temporal para nada
                temporal_cols = []  # Fingir que não temos colunas temporais
        else:
            # Se não houver colunas temporais, use a lógica baseada no tipo de gráfico
            if chart_type in ['bar', 'pie']:
                # Caso 2: Sem colunas temporais, mas com categóricas - usar categórica para X e numérica para Y
                if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                    x_col = categorical_cols[0]
                    y_col = numeric_cols[0]
                    # Usar a coluna categórica para separação por cor também
                    color_col = categorical_cols[0]
                    print(f"DEBUG: Selected categorical '{x_col}' for X and numeric '{y_col}' for Y")
                    print(f"DEBUG: Selected categorical '{color_col}' for color separation")
                elif len(numeric_cols) >= 2:
                    x_col = numeric_cols[0]
                    y_col = numeric_cols[1]
                    print(f"DEBUG: Selected numeric columns '{x_col}' for X and '{y_col}' for Y")
            elif chart_type == 'line':
                # Para gráficos de linha, prefira numérica no X e numérica no Y
                if len(numeric_cols) >= 2:
                    x_col = numeric_cols[0]
                    y_col = numeric_cols[1]
                    print(f"DEBUG: Selected numeric columns '{x_col}' for X and '{y_col}' for Y")
            elif chart_type == 'scatter':
                # Para gráficos de dispersão, prefira numérica no X e numérica no Y
                if len(numeric_cols) >= 2:
                    x_col = numeric_cols[0]
                    y_col = numeric_cols[1]
                    print(f"DEBUG: Selected numeric columns '{x_col}' for X and '{y_col}' for Y")
        
        # 3. Selecionar uma coluna categórica para separação por cor (se disponível)
        # Priorizar colunas categóricas que não estejam sendo usadas nos eixos X ou Y
        color_candidates = [col for col in categorical_cols if col != x_col and col != y_col]
        if color_candidates:
            color_col = color_candidates[0]  # Use a primeira coluna categórica disponível
            print(f"DEBUG: Selected categorical column '{color_col}' for color separation")
        
        # Aplicar a priorização da coluna de faturamento para o eixo Y se disponível
        if priority_y_col is not None:
            print(f"DEBUG: Overriding Y column with priority column '{priority_y_col}'")
            y_col = priority_y_col
            
        return x_col, y_col, color_col
