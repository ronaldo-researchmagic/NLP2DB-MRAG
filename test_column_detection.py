import pandas as pd
import asyncio
import json
from pilot.common.chart_generator import ChartGenerator

# Criar um DataFrame de teste com colunas numéricas que são semanticamente categóricas
def create_test_dataframe():
    # DataFrame com diferentes tipos de colunas
    data = {
        'id_cliente': [1, 2, 3, 4, 5],  # Coluna numérica que é semanticamente um ID
        'ano': [2019, 2020, 2021, 2022, 2023],  # Coluna numérica que é semanticamente uma categoria (ano)
        'mes': [1, 2, 3, 4, 5],  # Coluna numérica que é semanticamente uma categoria (mês)
        'vendas': [1500, 2300, 1800, 3200, 2700],  # Coluna numérica que é realmente numérica
        'categoria': ['A', 'B', 'C', 'A', 'B']  # Coluna já categórica
    }
    return pd.DataFrame(data)

# Função para testar a detecção de tipos semânticos via LLM (modo de teste)
async def test_semantic_detection():
    print("Testando detecção de tipos semânticos de colunas...")
    
    # Criar DataFrame de teste
    df = create_test_dataframe()
    print(f"DataFrame original:")
    print(df.head())
    print(f"Tipos de dados originais: {df.dtypes.to_dict()}")
    
    # Consultar o LLM para recomendação de tipo de gráfico (em modo de teste)
    # Isso também retornará os tipos semânticos das colunas
    llm_recommendation = await ChartGenerator.ask_llm_for_chart_type(df, test_mode=True)
    print(f"Recomendação do LLM: {json.dumps(llm_recommendation, indent=2)}")
    
    # Extrair os tipos semânticos identificados
    column_types = llm_recommendation.get("column_types", {})
    print(f"Tipos semânticos identificados: {column_types}")
    
    # Aplicar os tipos semânticos ao DataFrame
    df_converted = ChartGenerator.apply_semantic_types(df, column_types)
    print(f"DataFrame após conversão:")
    print(df_converted.head())
    print(f"Tipos de dados após conversão: {df_converted.dtypes.to_dict()}")
    
    # Gerar um gráfico com o DataFrame convertido
    chart_result = await ChartGenerator.generate_chart(df_converted, test_mode=True)
    
    if chart_result:
        print(f"Tipo de gráfico gerado: {chart_result['chart_type']}")
        print(f"Explicação: {chart_result['llm_explanation']}")
        
        # Salvar o JSON do gráfico para inspeção
        with open('column_detection_test_result.json', 'w') as f:
            f.write(chart_result['figure'])
        print("JSON do gráfico salvo em 'column_detection_test_result.json'")
    else:
        print("Falha na geração do gráfico")

# Executar o teste
if __name__ == "__main__":
    asyncio.run(test_semantic_detection())
