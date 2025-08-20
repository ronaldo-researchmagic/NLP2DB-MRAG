import pandas as pd
import traceback
import inspect
import sys
import json
import plotly.express as px
from typing import Dict, List, Tuple, Union, Optional, Any
from pilot.llm_providers.tela_provider import TelaLLMProvider

def get_lang_text(key):
    """Função auxiliar para obter texto traduzido"""
    return key  # Simplificado para o exemplo

class ChartGenerator:
    @staticmethod
    async def _get_semantic_types(df: pd.DataFrame, test_mode=False) -> Dict[str, str]:
        """Classifica as colunas como temporal, quantitativa ou categórica usando heurísticas."""
        semantic_types = {}
        for col_name in df.columns:
            col_dtype = df[col_name].dtype

            # 1. Classificação baseada no tipo de dado
            if pd.api.types.is_datetime64_any_dtype(col_dtype):
                semantic_types[col_name] = 'temporal'
            elif pd.api.types.is_numeric_dtype(col_dtype):
                # 2. Heurísticas para colunas numéricas
                is_year_col = 'ano' in col_name.lower() or 'year' in col_name.lower()
                is_code_col = 'cod' in col_name.lower() or 'id' in col_name.lower()
                is_high_cardinality = df[col_name].nunique() > 10 or (df[col_name].nunique() / len(df) > 0.5)

                # Trata como ano se o nome e o intervalo de valores corresponderem
                try:
                    numeric_col = pd.to_numeric(df[col_name])
                    if is_year_col and numeric_col.min() > 1000 and numeric_col.max() < 3000:
                        if (numeric_col.dropna() == numeric_col.dropna().astype(int)).all():
                            semantic_types[col_name] = 'temporal'
                            continue
                except (ValueError, TypeError):
                    pass

                # Trata como categórica se for um código ou tiver poucos valores únicos
                if is_code_col or not is_high_cardinality:
                    semantic_types[col_name] = 'categorical'
                else:
                    semantic_types[col_name] = 'quantitative'
            else:
                # 3. Colunas não numéricas são categóricas
                semantic_types[col_name] = 'categorical'
        return semantic_types

    @staticmethod
    async def generate_chart(df, query=None, test_mode=False, sql_query=None):
        """
        Gera um gráfico com base nos dados do DataFrame, usando LLM para classificar colunas.
        """
        if df is None or df.empty:
            return None

        # 1. Obter tipos semânticos das colunas
        semantic_types = await ChartGenerator._get_semantic_types(df, test_mode=test_mode)


        # Garantir que os tipos de dados estão corretos antes de plotar
        for col, type in semantic_types.items():
            if type == 'quantitative':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif type == 'temporal':
                # A conversão para int garante que o Plotly trate o ano como uma categoria ordenada
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(int)

        # 2. Selecionar colunas com base nos tipos semânticos
        x_col, y_col, color_col = ChartGenerator._select_columns(df, semantic_types)

        # 3. Determinar o tipo de gráfico e garantir a orientação correta dos eixos
        chart_type = 'bar'  # Padrão
        if x_col and y_col:
            # Se houver uma coluna temporal, ela DEVE estar no eixo X e o gráfico deve ser de linha.
            if semantic_types.get(x_col) == 'temporal':
                chart_type = 'line'
            elif semantic_types.get(y_col) == 'temporal':
                # Caso os eixos estejam invertidos, corrige e define o tipo de gráfico
                x_col, y_col = y_col, x_col
                chart_type = 'line'
        
        if not x_col or not y_col:
            print("Não foi possível determinar os eixos X e Y para o gráfico.")
            return None

        title = f"{get_lang_text('Gráfico')} {get_lang_text(chart_type)}"
        
        try:
            if chart_type == 'bar':
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'line':
                fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'pie':
                fig = px.pie(df, names=x_col, values=y_col, title=title)
            else:
                fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)

            fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)

            return {
                'figure': fig,
                'chart_config': {
                    'type': chart_type,
                    'x': x_col,
                    'y': y_col,
                    'color': color_col,
                    'title': title
                },
                'explanation': f"Gráfico gerado com base na classificação de colunas: X={x_col}({semantic_types.get(x_col)}), Y={y_col}({semantic_types.get(y_col)})"
            }
        except Exception as e:
            print(f"Erro ao gerar gráfico: {e}")
            return None

    @staticmethod
    def _select_columns(df, semantic_types):
        """
        Seleciona as melhores colunas para x, y e color com base nos tipos semânticos.
        Prioriza temporal para X, quantitativo para Y e categórico para cor.
        """
        temporal_cols = [col for col, type in semantic_types.items() if type == 'temporal']
        quantitative_cols = [col for col, type in semantic_types.items() if type == 'quantitative']
        categorical_cols = [col for col, type in semantic_types.items() if type == 'categorical']

        x_col, y_col, color_col = None, None, None

        # Prioridade 1: Eixo X deve ser temporal, se disponível.
        if temporal_cols:
            x_col = temporal_cols[0]
        # Se não houver temporal, a melhor categórica vai para o eixo X.
        elif categorical_cols:
            # Ordena para pegar a categórica com mais valores únicos (mais granular)
            categorical_cols.sort(key=lambda col: df[col].nunique(), reverse=True)
            x_col = categorical_cols.pop(0)

        # Prioridade 2: Eixo Y deve ser a primeira coluna quantitativa.
        if quantitative_cols:
            y_col = quantitative_cols.pop(0)

        # Prioridade 3: Cor é a categórica restante com mais granularidade.
        if categorical_cols:
            # A lista já está ordenada da etapa anterior
            color_col = categorical_cols[0]

        # Caso especial: se não há temporal, mas há quantitativa e categórica,
        # garante que X e Y sejam preenchidos.
        if not x_col and not y_col:
            if quantitative_cols and categorical_cols:
                x_col = categorical_cols[0]
                y_col = quantitative_cols[0]

        return x_col, y_col, color_col
