import asyncio
import pandas as pd
import sys
import os
import json

# Adicionar o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pilot.common.chart_generator import ChartGenerator
from pilot.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction


async def test_chart_generator_with_llm():
    """
    Teste da geração de gráficos com assistência de LLM.
    Cria um DataFrame de exemplo e testa a geração de gráficos.
    """
    print("Iniciando teste de geração de gráficos com LLM...")
    
    # Criar um DataFrame de exemplo para vendas por categoria e mês
    data = {
        'categoria': ['Eletrônicos', 'Roupas', 'Alimentos', 'Eletrônicos', 'Roupas', 'Alimentos'],
        'mes': ['Janeiro', 'Janeiro', 'Janeiro', 'Fevereiro', 'Fevereiro', 'Fevereiro'],
        'vendas': [1200, 950, 1500, 1350, 1100, 1650],
        'lucro': [240, 285, 300, 270, 330, 330]
    }
    df = pd.DataFrame(data)
    
    # SQL de exemplo que seria usado para gerar este DataFrame
    sql_query = """
    SELECT categoria, mes, SUM(vendas) as vendas, SUM(lucro) as lucro
    FROM vendas
    WHERE mes IN ('Janeiro', 'Fevereiro')
    GROUP BY categoria, mes
    ORDER BY mes, categoria
    """
    
    print(f"DataFrame de teste:\n{df}")
    print(f"SQL de teste: {sql_query}")
    
    # Testar a geração de gráfico usando o LLM em modo de teste
    print("\nTestando geração de gráfico com LLM em modo de teste...")
    chart_result = await ChartGenerator.generate_chart(df, sql_query=sql_query, test_mode=True)
    
    if chart_result:
        print(f"Tipo de gráfico selecionado: {chart_result['chart_type']}")
        if 'llm_explanation' in chart_result:
            print(f"Explicação do LLM: {chart_result['llm_explanation']}")
        
        # Salvar o JSON do gráfico em um arquivo para inspeção
        with open('chart_test_result.json', 'w') as f:
            json.dump(chart_result, f, indent=2)
        print("Resultado do gráfico salvo em 'chart_test_result.json'")
    else:
        print("Falha na geração do gráfico")
    
    # Testar o parser de saída com o gráfico
    print("\nTestando o parser de saída com o gráfico...")
    parser = DbChatOutputParser(sep="\n", is_stream_out=False)
    
    # Criar um objeto SqlAction simulado
    sql_action = SqlAction(sql_query, {"speak": "Aqui estão as vendas por categoria e mês"})
    
    # Preparar os dados para o parser
    data_for_parser = [['categoria', 'mes', 'vendas', 'lucro']]
    for _, row in df.iterrows():
        data_for_parser.append([row['categoria'], row['mes'], row['vendas'], row['lucro']])
    
    # Testar o parser de saída com o gráfico em modo de teste
    result = await parser.parse_view_response_async(sql_action, data_for_parser, test_mode=True)
    
    # Salvar o HTML resultante em um arquivo para inspeção
    with open('parser_test_result.html', 'w', encoding='utf-8') as f:
        f.write(result)
    print("Resultado do parser salvo em 'parser_test_result.html'")
    
    print("\nTeste concluído!")


if __name__ == "__main__":
    asyncio.run(test_chart_generator_with_llm())
