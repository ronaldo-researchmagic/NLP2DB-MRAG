import pandas as pd
import asyncio
import json
import plotly.express as px
from pilot.common.chart_generator import ChartGenerator

# Criar um DataFrame que simula o problema com anos
def create_test_dataframe():
    data = {
        'ano': [2020, 2021, 2022, 2023, 2024, 2025],
        'faturamento_total': [38346825.00, 50438381.00, 53593175.00, 35312864.00, 39901447.00, 19568130.00]
    }
    return pd.DataFrame(data)

# Função para testar a detecção heurística de anos
async def test_year_detection():
    print("Testando detecção heurística de colunas de anos...")
    
    # Criar DataFrame de teste
    df = create_test_dataframe()
    print(f"DataFrame original:")
    print(df.head())
    print(f"Tipos de dados originais: {df.dtypes.to_dict()}")
    
    # 1. Testar a função apply_semantic_types diretamente (sem tipos do LLM)
    print("\n=== Testando apply_semantic_types sem tipos do LLM ===")
    df_converted = ChartGenerator.apply_semantic_types(df)
    print(f"Tipos após aplicação de regras heurísticas: {df_converted.dtypes.to_dict()}")
    
    # Verificar se a coluna 'ano' foi convertida para string
    is_year_converted = df_converted['ano'].dtype == 'object'
    print(f"Coluna 'ano' foi convertida para string? {'Sim' if is_year_converted else 'Não'}")
    
    # 2. Testar a geração de gráfico com as regras heurísticas
    print("\n=== Testando geração de gráfico com regras heurísticas ===")
    chart_result = await ChartGenerator.generate_chart(df, test_mode=True)
    
    if chart_result:
        print(f"Tipo de gráfico gerado: {chart_result['chart_type']}")
        
        # Salvar o JSON do gráfico para inspeção
        with open('year_detection_test_result.json', 'w') as f:
            f.write(chart_result['figure'])
        print("JSON do gráfico salvo em 'year_detection_test_result.json'")
        
        # Verificar se os anos estão sendo exibidos corretamente no eixo X
        fig_data = json.loads(chart_result['figure'])
        if 'data' in fig_data and len(fig_data['data']) > 0:
            x_values = fig_data['data'][0].get('x', {})
            print(f"Valores do eixo X no gráfico: {x_values}")
            
            # Verificar o formato dos dados do eixo X
            if isinstance(x_values, dict) and 'dtype' in x_values:
                print(f"Formato dos dados do eixo X: {x_values['dtype']}")
                print("Os anos estão em formato binário comprimido, não é possível verificar diretamente")
            elif isinstance(x_values, list) and len(x_values) > 0:
                print(f"Tipo dos valores do eixo X: {type(x_values[0])}")
                print(f"Os anos estão sendo tratados como categorias? {'Sim' if isinstance(x_values[0], str) else 'Não'}")
            else:
                print("Formato de dados do eixo X não reconhecido ou vazio")
    else:
        print("Falha na geração do gráfico")

    # 3. Criar um gráfico diretamente com Plotly para comparação
    print("\n=== Comparação com gráfico Plotly usando DataFrame convertido ===")
    fig_direct = px.line(df_converted, x='ano', y='faturamento_total', title='Faturamento por Ano (Direto com Plotly)')
    fig_json_direct = fig_direct.to_json()
    with open('year_detection_plotly_result.json', 'w') as f:
        f.write(fig_json_direct)
    print("Gráfico Plotly salvo em 'year_detection_plotly_result.json'")

# Executar o teste
if __name__ == "__main__":
    asyncio.run(test_year_detection())
