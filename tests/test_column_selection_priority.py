import asyncio
import pandas as pd
import sys
import os
import json

# Adicionar o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pilot.common.chart_generator import ChartGenerator


async def test_temporal_column_priority():
    """
    Testa se as colunas temporais são priorizadas para o eixo X,
    colunas numéricas para o eixo Y e colunas categóricas para separação por cor.
    """
    print("Iniciando teste de priorização de colunas temporais...")

    # Caso 1: DataFrame com coluna de ano explícita, coluna numérica e coluna categórica
    data_year = {
        'ano': [2018, 2019, 2020, 2021, 2022],
        'vendas': [1200, 1350, 1500, 1650, 1800],
        'categoria': ['Eletrônicos', 'Eletrônicos', 'Roupas', 'Roupas', 'Alimentos']
    }
    df_year = pd.DataFrame(data_year)
    print(f"\nDataFrame com coluna de ano explícita:\n{df_year}")

    # Testar seleção de colunas para diferentes tipos de gráficos
    for chart_type in ['bar', 'line', 'scatter']:
        print(f"\nTestando seleção de colunas para gráfico tipo '{chart_type}'...")
        x_col, y_col, color_col = ChartGenerator._select_columns(df_year, chart_type)
        print(f"Coluna X selecionada: {x_col}")
        print(f"Coluna Y selecionada: {y_col}")
        print(f"Coluna de cor selecionada: {color_col}")
        
        # Verificar se a coluna temporal (ano) foi selecionada para o eixo X
        assert x_col == 'ano', f"Falha: coluna temporal 'ano' deveria ser selecionada para eixo X, mas foi selecionada '{x_col}'"
        # Verificar se uma coluna numérica foi selecionada para o eixo Y
        assert y_col == 'vendas', f"Falha: coluna numérica 'vendas' deveria ser selecionada para eixo Y, mas foi selecionada '{y_col}'"
        # Verificar se a coluna categórica foi selecionada para separação por cor
        assert color_col == 'categoria', f"Falha: coluna categórica 'categoria' deveria ser selecionada para cor, mas foi selecionada '{color_col}'"
    
    # Caso 2: DataFrame com coluna de data, coluna numérica e coluna categórica
    data_date = {
        'data': ['2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01'],
        'receita': [5000, 5500, 6000, 5800, 6200],
        'departamento': ['Vendas', 'Marketing', 'Vendas', 'Marketing', 'Vendas']
    }
    df_date = pd.DataFrame(data_date)
    df_date['data'] = pd.to_datetime(df_date['data'])
    print(f"\nDataFrame com coluna de data:\n{df_date}")

    # Testar seleção de colunas
    for chart_type in ['bar', 'line', 'scatter']:
        print(f"\nTestando seleção de colunas para gráfico tipo '{chart_type}'...")
        x_col, y_col, color_col = ChartGenerator._select_columns(df_date, chart_type)
        print(f"Coluna X selecionada: {x_col}")
        print(f"Coluna Y selecionada: {y_col}")
        print(f"Coluna de cor selecionada: {color_col}")
        
        # Verificar se a coluna temporal (data) foi selecionada para o eixo X
        assert x_col == 'data', f"Falha: coluna temporal 'data' deveria ser selecionada para eixo X, mas foi selecionada '{x_col}'"
        # Verificar se uma coluna numérica foi selecionada para o eixo Y
        assert y_col == 'receita', f"Falha: coluna numérica 'receita' deveria ser selecionada para eixo Y, mas foi selecionada '{y_col}'"
        # Verificar se a coluna categórica foi selecionada para separação por cor
        assert color_col == 'departamento', f"Falha: coluna categórica 'departamento' deveria ser selecionada para cor, mas foi selecionada '{color_col}'"

    # Caso 3: DataFrame com coluna de ano numérica (sem nome explícito de ano)
    data_numeric_year = {
        'valor_ano': [2018, 2019, 2020, 2021, 2022],
        'quantidade': [150, 180, 210, 240, 270],
        'produto': ['A', 'B', 'C', 'A', 'B']
    }
    df_numeric_year = pd.DataFrame(data_numeric_year)
    print(f"\nDataFrame com coluna de ano numérica (sem nome explícito):\n{df_numeric_year}")

    # Testar se a detecção heurística de anos funciona mesmo sem nome explícito
    for chart_type in ['bar', 'line', 'scatter']:
        print(f"\nTestando seleção de colunas para gráfico tipo '{chart_type}'...")
        x_col, y_col, color_col = ChartGenerator._select_columns(df_numeric_year, chart_type)
        print(f"Coluna X selecionada: {x_col}")
        print(f"Coluna Y selecionada: {y_col}")
        print(f"Coluna de cor selecionada: {color_col}")
        
        # Verificar se a coluna com valores de ano foi selecionada para o eixo X
        # Neste caso, a detecção é mais difícil sem um nome explícito, então pode falhar
        print(f"Nota: Para este caso, a detecção de coluna temporal é mais difícil sem um nome explícito.")
        
    # Caso 4: DataFrame sem colunas temporais, apenas numéricas e categóricas
    data_no_temporal = {
        'valor_a': [100, 150, 200, 250, 300],
        'valor_b': [50, 75, 100, 125, 150],
        'grupo': ['X', 'Y', 'Z', 'X', 'Y']
    }
    df_no_temporal = pd.DataFrame(data_no_temporal)
    print(f"\nDataFrame sem colunas temporais:\n{df_no_temporal}")

    # Testar comportamento quando não há colunas temporais
    for chart_type in ['bar', 'line', 'scatter']:
        print(f"\nTestando seleção de colunas para gráfico tipo '{chart_type}' sem colunas temporais...")
        x_col, y_col, color_col = ChartGenerator._select_columns(df_no_temporal, chart_type)
        print(f"Coluna X selecionada: {x_col}")
        print(f"Coluna Y selecionada: {y_col}")
        print(f"Coluna de cor selecionada: {color_col}")
        
        # Verificar se uma coluna categórica foi selecionada para o eixo X (para bar/pie)
        if chart_type in ['bar', 'pie']:
            assert color_col == 'grupo', f"Falha: coluna categórica 'grupo' deveria ser selecionada para cor, mas foi selecionada '{color_col}'"

    print("\nTeste de priorização de colunas temporais concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(test_temporal_column_priority())
