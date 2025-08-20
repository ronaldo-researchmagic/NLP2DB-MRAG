"""
Teste específico para verificar a formatação de valores grandes em gráficos.
"""
import os
import sys
import json
import pandas as pd

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar após ajustar o PYTHONPATH
from pilot.common.chart_generator import ChartGenerator
from pilot.scene.chat_db.auto_execute.out_parser import DbChatOutputParser

async def test_large_values_chart():
    """Testa a geração de gráficos com valores grandes."""
    print("Iniciando teste de formatação de valores grandes em gráficos...")
    
    # Criar DataFrame com valores grandes
    df = pd.DataFrame({
        'ano': [2020, 2021, 2022, 2023, 2024, 2025],
        'total_faturamento': [
            38848625.00,  # ~38.8M
            50436381.00,  # ~50.4M
            53593175.00,  # ~53.6M
            35312864.00,  # ~35.3M
            39901447.00,  # ~39.9M
            19568130.00   # ~19.6M
        ]
    })
    
    print("DataFrame de teste com valores grandes:")
    print(df)
    
    # SQL de exemplo similar ao mostrado na imagem
    sql_query = """
    SELECT ano, SUM(vl_valor_faturar) AS total_faturamento FROM ft_faturamento_cabecalho GROUP BY ano ORDER BY ano LIMIT 10;
    """
    
    print("SQL de teste:", sql_query)
    
    # Testar geração de gráfico diretamente
    print("\nTestando geração de gráfico com valores grandes...")
    
    # Definir o tipo de gráfico manualmente para evitar problemas com o LLM
    chart_type = 'bar'
    print(f"Usando tipo de gráfico: {chart_type}")
    
    try:
        # Gerar o gráfico diretamente usando Plotly Express
        import plotly.express as px
        import plotly.io as pio
        
        # Verificar se os valores são muito grandes e precisam de formatação especial
        max_value = df['total_faturamento'].max()
        print(f"Valor máximo no DataFrame: {max_value:,.2f}")
        
        # Determinar o formato adequado com base na magnitude dos valores
        tick_format = None
        if max_value >= 1000000:  # Milhões
            tick_format = ".1s"
            print("Usando formato para milhões (.1s)")
        elif max_value >= 1000:  # Milhares
            tick_format = ".3s"
            print("Usando formato para milhares (.3s)")
        
        # Gerar o gráfico
        fig = px.bar(
            df, 
            x='ano', 
            y='total_faturamento',
            title="Total de Faturamento por Ano",
            template="plotly_white"
        )
        
        # Configurar o layout para formatar valores grandes
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                title="Ano",
                tickangle=0
            ),
            yaxis=dict(
                title="Total Faturamento",
                type="linear",
                tickformat=tick_format
            )
        )
        
        # Converter para JSON para exibição web
        chart_json = fig.to_json()
        
        # Salvar o resultado em um arquivo para inspeção
        with open('large_values_chart_result.json', 'w', encoding='utf-8') as f:
            f.write(chart_json)
        print("Resultado do gráfico salvo em 'large_values_chart_result.json'")
        
        # Criar objeto de resultado similar ao retornado pelo ChartGenerator
        chart_result = {
            'chart_type': chart_type,
            'figure': chart_json,
            'llm_explanation': "Gráfico de barras mostrando a evolução do faturamento ao longo dos anos."
        }
        
        print(f"Tipo de gráfico selecionado: {chart_result['chart_type']}")
        print(f"Explicação: {chart_result.get('llm_explanation', '')}")
        
    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        import traceback
        traceback.print_exc()
        chart_result = None
    
    # Testar a geração de HTML com o gráfico diretamente
    print("\nGerando HTML para visualização do gráfico com valores grandes...")
    
    # Preparar os dados para o DataFrame
    data_for_html = []
    for _, row in df.iterrows():
        data_for_html.append([row['ano'], f"{row['total_faturamento']:,.2f}"])
    
    # Criar HTML manualmente para visualização
    html_content = "<div class='chart-container'>\n"
    html_content += "<h2>Visualização do Gráfico</h2>\n"
    html_content += "<div id='chart'></div>\n"
    
    # Adicionar o script apenas se tivermos dados do gráfico
    if chart_result:
        html_content += "<script>\n"
        html_content += "const chartData = " + chart_result['figure'] + ";\n"
        html_content += "Plotly.newPlot('chart', chartData.data, chartData.layout);\n"
        html_content += "</script>\n"
    else:
        html_content += "<p><strong>Erro:</strong> Não foi possível gerar o gráfico.</p>\n"
    
    html_content += "</div>"
    
    # Adicionar tabela de dados
    html_content += "<div class='data-table'>\n"
    html_content += "<h3>Dados</h3>\n"
    html_content += "<table border='1'>\n"
    html_content += "<tr><th>Ano</th><th>Total Faturamento</th></tr>\n"
    for row in data_for_html:
        html_content += f"<tr><td>{row[0]}</td><td>{row[1]}</td></tr>\n"
    html_content += "</table>\n"
    html_content += "</div>"
    
    # Adicionar referência ao Plotly
    html_content = "<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>\n" + html_content
    
    # Salvar o resultado em um arquivo para inspeção
    with open('large_values_parser_result.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Resultado do HTML salvo em 'large_values_parser_result.html'")
    
    print("\nTeste concluído!")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_large_values_chart())
