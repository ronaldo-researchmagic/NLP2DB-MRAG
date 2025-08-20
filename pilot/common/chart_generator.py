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
                code_keywords = ['cod', 'id', 'key', 'pk', 'codigo']
                is_code_col = any(keyword in col_name.lower() for keyword in code_keywords)
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

                # Trata como categórica se for um código ou um inteiro com baixa cardinalidade.
                # Floats são quase sempre quantitativos.
                # Nomes que sugerem fortemente um valor quantitativo
                quantitative_keywords = ['total', 'valor', 'preco', 'faturamento', 'receita', 'soma', 'media', 'avg', 'sum', 'amount', 'price', 'revenue', 'value', 'metric', 'quantidade', 'quantity']
                is_quantitative_by_name = any(keyword in col_name.lower() for keyword in quantitative_keywords)

                # A regra de código tem a maior prioridade
                if is_code_col:
                    semantic_types[col_name] = 'categorical'
                # A regra de nome tem a segunda maior prioridade
                elif is_quantitative_by_name:
                    semantic_types[col_name] = 'quantitative'
                # Floats são quase sempre quantitativos
                elif pd.api.types.is_float_dtype(df[col_name].dtype):
                    semantic_types[col_name] = 'quantitative'
                # Inteiros de baixa cardinalidade (que não são códigos nem quantitativos por nome) são categóricos
                elif pd.api.types.is_integer_dtype(df[col_name].dtype) and not is_high_cardinality:
                    semantic_types[col_name] = 'categorical'
                # O resto é quantitativo
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
        if df is None or df.empty or len(df) <= 1:
            print("DataFrame vazio ou com poucos dados para gerar um gráfico.")
            return None

        # 1. Obter tipos semânticos e converter dtypes de acordo
        semantic_types = await ChartGenerator._get_semantic_types(df, test_mode=test_mode)

        for col, type in semantic_types.items():
            if type == 'temporal':
                # Converte para numérico, preenche NaNs e converte para Int para ordenação
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            elif type == 'quantitative':
                # Garante que a coluna seja float para cálculos e plotagem
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)

        # 2. Selecionar colunas com base nos tipos semânticos
        x_col, y_col, color_col = ChartGenerator._select_columns(df, semantic_types)

        # 3. Determinar o tipo de gráfico e garantir a orientação correta dos eixos
        chart_type = 'bar'  # Padrão
        if x_col and y_col:
            # Garante que a coluna temporal esteja sempre no eixo X
            if semantic_types.get(y_col) == 'temporal':
                x_col, y_col = y_col, x_col

            # Se o eixo X for temporal, o gráfico deve ser de linha e ordenado
            if semantic_types.get(x_col) == 'temporal':
                chart_type = 'line'
                df = df.sort_values(by=x_col)
        
        if not x_col or not y_col:
            print("Não foi possível determinar os eixos X e Y para o gráfico.")
            return None

        # 4. Validar se o gráfico é informativo
        if df[y_col].nunique() <= 1:
            print(f"Gráfico não gerado por falta de variação nos dados da coluna '{y_col}'.")
            return None

        title = f"{get_lang_text('Gráfico')} {get_lang_text(chart_type)}"

        # 5. Gerar o gráfico com Plotly Express
        category_orders = {}
        # Garante a ordem correta para eixos categóricos (não temporais)
        if chart_type in ['bar', 'line'] and semantic_types.get(x_col) == 'categorical':
            category_orders[x_col] = df[x_col].unique().tolist()

        try:
            # Passa as Series do pandas com os dtypes corretos diretamente para o Plotly
            # Isso evita modificar o DataFrame e previne o "tidying" automático do Plotly
            x_data = df[x_col].astype(str) if semantic_types.get(x_col) == 'temporal' else df[x_col]
            y_data = df[y_col].astype(float)

            plot_args = {
                'x': x_data,
                'y': y_data,
                'title': title,
                'category_orders': category_orders
            }
            if color_col:
                plot_args['color'] = df[color_col]

            # O DataFrame não deve ser passado quando x e y são Series
            if chart_type == 'bar':
                fig = px.bar(**plot_args)
            elif chart_type == 'line':
                fig = px.line(**plot_args)
            elif chart_type == 'scatter':
                # Scatter e pie têm argumentos diferentes
                scatter_args = {'x': x_data, 'y': y_data, 'title': title}
                if color_col:
                    scatter_args['color'] = df[color_col]
                fig = px.scatter(**scatter_args)
            elif chart_type == 'pie':
                # Pie usa 'names' e 'values', que esperam nomes de colunas
                fig = px.pie(df, names=x_col, values=y_col, title=title)
            else: # Fallback para bar chart
                fig = px.bar(**plot_args)

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
        Seleciona as melhores colunas para x, y e color com base nos tipos semânticos,
        com lógica de fallback para garantir a geração do gráfico.
        """
        temporal_cols = [col for col, type in semantic_types.items() if type == 'temporal']
        quantitative_cols = [col for col, type in semantic_types.items() if type == 'quantitative']
        categorical_cols = [col for col, type in semantic_types.items() if type == 'categorical']

        x_col, y_col, color_col = None, None, None

        # Lógica de seleção com prioridade clara
        # Eixo Y é sempre a primeira coluna quantitativa
        if quantitative_cols:
            y_col = quantitative_cols.pop(0)

        # Eixo X é a primeira temporal, ou a categórica de maior cardinalidade
        if temporal_cols:
            x_col = temporal_cols.pop(0)
        elif categorical_cols:
            # Ordena por cardinalidade para pegar a mais descritiva
            categorical_cols.sort(key=lambda c: df[c].nunique(), reverse=True)
            x_col = categorical_cols.pop(0)

        # Lógica de fallback se os eixos principais não puderem ser definidos
        if not x_col or not y_col:
            all_cols = df.columns.tolist()
            if not x_col and not y_col and len(all_cols) >= 2:
                x_col, y_col = all_cols[0], all_cols[1]
            elif not y_col and x_col:
                available_cols = [c for c in all_cols if c != x_col]
                if available_cols:
                    y_col = available_cols[0]

        # A coluna de cor só deve ser definida se houver uma categórica apropriada e distinta
        if categorical_cols:
            categorical_cols.sort(key=lambda c: df[c].nunique(), reverse=True)
            # Garante que a coluna de cor não seja a mesma dos eixos
            for col in categorical_cols:
                if col != x_col and col != y_col:
                    color_col = col
                    break # Usa a primeira coluna categórica válida

        # Se nenhuma coluna de cor foi encontrada, garante que seja None
        if 'color_col' not in locals() or not color_col:
             color_col = None

        return x_col, y_col, color_col
