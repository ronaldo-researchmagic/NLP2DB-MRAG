import pandas as pd
import asyncio
import json
import plotly.express as px
from pilot.common.chart_generator import ChartGenerator

# Criar um DataFrame que simula o problema mostrado na imagem
def create_test_dataframe():
    data = {
        'ano': [2020, 2021, 2022, 2023, 2024, 2025],
        'faturamento_total': [38346825.00, 50438381.00, 53593175.00, 35312864.00, 39901447.00, 19568130.00]
    }
    return pd.DataFrame(data)

# Função para testar a geração de gráfico com anos
async def test_year_chart():
    print("Testando geração de gráfico com anos...")
    
    # Criar DataFrame de teste
    df = create_test_dataframe()
    print(f"DataFrame original:")
    print(df.head())
    print(f"Tipos de dados originais: {df.dtypes.to_dict()}")
    
    # Gerar um gráfico sem a detecção inteligente de tipos (simulando o problema)
    print("\n=== Gráfico SEM detecção inteligente de tipos ===")
    
    # Criar gráfico de linha diretamente com Plotly sem converter tipos
    fig_without_detection = px.line(df, x='ano', y='faturamento_total', title='Faturamento por Ano (Sem Detecção de Tipos)')
    fig_json_without = fig_without_detection.to_json()
    with open('year_chart_without_detection.json', 'w') as f:
        f.write(fig_json_without)
    print("Gráfico sem detecção salvo em 'year_chart_without_detection.json'")
    print("Observe que os anos são tratados como valores numéricos contínuos no eixo X")
    
    # Agora gerar o gráfico com a detecção inteligente de tipos
    print("\n=== Gráfico COM detecção inteligente de tipos ===")
    
    # Aplicar a conversão de tipos manualmente (simulando o que o LLM faria)
    df_converted = df.copy()
    df_converted['ano'] = df_converted['ano'].astype(str)  # Converter ano para string (categoria)
    print(f"Tipos após conversão manual: {df_converted.dtypes.to_dict()}")
    
    # Criar gráfico de linha com os tipos convertidos
    fig_with_detection = px.line(df_converted, x='ano', y='faturamento_total', title='Faturamento por Ano (Com Detecção de Tipos)')
    fig_json_with = fig_with_detection.to_json()
    with open('year_chart_with_detection.json', 'w') as f:
        f.write(fig_json_with)
    print("Gráfico com detecção salvo em 'year_chart_with_detection.json'")
    print("Observe que os anos são tratados como categorias discretas no eixo X")
    
    # Agora usar o ChartGenerator com modo de teste
    print("\n=== Gráfico usando ChartGenerator em modo de teste ===")
    chart_result = await ChartGenerator.generate_chart(df, test_mode=True)
    
    if chart_result:
        print(f"Tipo de gráfico gerado: {chart_result['chart_type']}")
        print(f"Explicação: {chart_result['llm_explanation']}")
        
        # Salvar o JSON do gráfico para inspeção
        with open('year_chart_test_result.json', 'w') as f:
            f.write(chart_result['figure'])
        print("JSON do gráfico salvo em 'year_chart_test_result.json'")
        
        # Verificar se a coluna 'ano' foi convertida para categoria
        print("\nVerificando se a detecção de tipos funcionou:")
        # Extrair informações do JSON para verificar se os anos estão como categorias
        fig_data = json.loads(chart_result['figure'])
        if 'data' in fig_data and len(fig_data['data']) > 0:
            x_values = fig_data['data'][0].get('x', [])
            print(f"Valores do eixo X no gráfico: {x_values[:5]}...")
            print(f"Tipo dos valores do eixo X: {type(x_values[0]) if x_values else 'N/A'}")
            print(f"Os anos estão sendo tratados como categorias? {'Sim' if isinstance(x_values[0], str) else 'Não'}")
    else:
        print("Falha na geração do gráfico")

# Executar o teste
if __name__ == "__main__":
    asyncio.run(test_year_chart())
