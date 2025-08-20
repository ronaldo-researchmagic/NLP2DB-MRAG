import pandas as pd
import asyncio
import json
import sys
from pilot.common.chart_generator import ChartGenerator

async def test_single_year_chart():
    """
    Testa a geração de gráficos com dados onde todos os anos são iguais.
    Verifica se o sistema seleciona corretamente as colunas para o gráfico.
    """
    # Criar DataFrame com dados de teste - todos os anos são 2020
    df = pd.DataFrame({
        'cliente_cod': [3, 67, 19, 54, 58, 35, 123, 350, 148, 53],
        'cliente_nome': [
            'NACIONAL COMERCIAL HOSPITALAR S.A', 
            'SUPERMED COM. IMP. PROD. MED. HOSPITALARES LTDA',
            'LABORPLAST COMERCIAL LTDA',
            'EXOMED COM. ATAC. DE MEDICAMENTOS LTDA',
            'DROGAFONTE LTDA ME',
            'GLOBAL HOSPITALAR IMP. E COM. LTDA',
            'HOSPFAR IND. COM. PROD. HOSP. S.A',
            'SUPRAMED COM. MAT. MED. HOSP LTDA',
            'LINEA - RJ COMERCIO LTDA',
            'BELBI COMERCIO, IMPORT. E EXPORT. COMERCIAL EIRELI'
        ],
        'ano': [2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020],
        'faturamento_total': [
            7707328.00, 5740378.00, 3481392.00, 2140955.00, 1872752.00,
            1662426.00, 1492043.00, 1288285.00, 1240120.00, 889098.00
        ]
    })
    
    print("\n=== INFORMAÇÕES DO DATAFRAME ===")
    print(f"Colunas: {df.columns.tolist()}")
    print(f"Tipos de dados: {df.dtypes}")
    print(f"Valores únicos na coluna 'ano': {df['ano'].unique()}")
    print(f"Número de valores únicos na coluna 'ano': {df['ano'].nunique()}")
    
    print("Testando geração de gráfico com anos únicos (todos 2020)...")
    
    # Gerar gráfico usando o ChartGenerator
    chart_result = await ChartGenerator.generate_chart(df, test_mode=True)
    
    # Salvar o resultado do gráfico em um arquivo JSON para análise
    with open('single_year_chart_result.json', 'w', encoding='utf-8') as f:
        json.dump(chart_result, f, ensure_ascii=False, indent=2)
    
    print(f"Resultado salvo em 'single_year_chart_result.json'")
    
    # Verificar as colunas selecionadas
    # O resultado já é um dicionário, não precisa de json.loads
    chart_data = chart_result
    
    print("\n=== ANÁLISE DO RESULTADO DO GRÁFICO ===")
    print(f"Tipo de gráfico gerado: {chart_data.get('chart_type', 'desconhecido')}")
    
    # Converter a string JSON para um dicionário Python para análise
    try:
        figure_data = json.loads(chart_data.get('figure', '{}'))
        print("Conversão do JSON do gráfico bem-sucedida")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON do gráfico: {e}")
        return None
    
    # Extrair informações do gráfico
    if 'data' in figure_data and len(figure_data['data']) > 0:
        chart_type = figure_data['data'][0].get('type', 'desconhecido')
        print(f"Tipo de traço no gráfico: {chart_type}")
        
        # Obter valores dos eixos X e Y
        if 'x' in figure_data['data'][0]:
            x_values = figure_data['data'][0]['x']
            print(f"Valores no eixo X (primeiros 3): {x_values[:3]}")
            print(f"Total de valores no eixo X: {len(x_values)}")
            
        if 'y' in figure_data['data'][0]:
            # Verificar se y é um dicionário (dados binários) ou uma lista
            y_data = figure_data['data'][0]['y']
            if isinstance(y_data, dict) and 'bdata' in y_data:
                print("Y contém dados binários codificados")
            elif isinstance(y_data, list):
                print(f"Valores no eixo Y (primeiros 3): {y_data[:3]}")
                print(f"Total de valores no eixo Y: {len(y_data)}")
            else:
                print(f"Formato de dados Y desconhecido: {type(y_data)}")
        
        # Verificar template de hover para identificar quais colunas estão sendo usadas
        if 'hovertemplate' in figure_data['data'][0]:
            hover_template = figure_data['data'][0]['hovertemplate']
            print(f"Hover template: {hover_template}")
            # Extrair nomes de colunas do hover template
            import re
            column_matches = re.findall(r'([a-zA-Z_]+)=%{[xy]}', hover_template)
            if column_matches:
                print(f"Colunas identificadas no hover: {column_matches}")
    
    # Verificar informações de layout
    if 'layout' in figure_data:
        layout = figure_data['layout']
        
        # Verificar títulos dos eixos
        if 'xaxis' in layout and 'title' in layout['xaxis']:
            x_title = layout['xaxis']['title'].get('text', '')
            print(f"Título do eixo X: {x_title}")
        
        if 'yaxis' in layout and 'title' in layout['yaxis']:
            y_title = layout['yaxis']['title'].get('text', '')
            print(f"Título do eixo Y: {y_title}")
        
        # Verificar título do gráfico
        if 'title' in layout:
            chart_title = layout['title'].get('text', '')
            print(f"Título do gráfico: {chart_title}")
    
    # Verificar se está usando cliente_nome como eixo X e faturamento_total como eixo Y
    print("\n=== VERIFICAÇÃO DE REQUISITOS ===")
    if 'layout' in figure_data:
        x_axis = figure_data['layout']['xaxis'].get('title', {}).get('text', '')
        y_axis = figure_data['layout']['yaxis'].get('title', {}).get('text', '')
        
        # Verificar se não está usando 'ano' como eixo X
        if 'ano' not in x_axis.lower() and 'year' not in x_axis.lower():
            print("SUCESSO SUCESSO: O gráfico NÃO está usando 'ano' no eixo X")
            
            # Verificar se está usando cliente_nome
            if 'cliente' in x_axis.lower() and 'nome' in x_axis.lower():
                print("SUCESSO SUCESSO: O gráfico está usando 'cliente_nome' no eixo X")
            else:
                print(f"FALHA FALHA: O eixo X não parece usar 'cliente_nome': {x_axis}")
        else:
            print(f"FALHA FALHA: O gráfico ainda está usando 'ano' no eixo X: {x_axis}")
        
        # Verificar se está usando faturamento_total no eixo Y
        if 'faturamento' in y_axis.lower() or 'total' in y_axis.lower():
            print("SUCESSO SUCESSO: O gráfico está usando 'faturamento_total' no eixo Y")
        else:
            print(f"FALHA FALHA: O eixo Y não está usando 'faturamento_total': {y_axis}")
            
            # Se estiver usando cliente_cod, sugerir correção
            if 'cliente' in y_axis.lower() and 'cod' in y_axis.lower():
                print("  -> Está usando 'cliente_cod' em vez de 'faturamento_total'")
                print("  -> Precisamos ajustar a priorização para usar valores de faturamento")
    
    print("Teste concluído!")
    
    return chart_result

async def test_with_modified_data():
    """Testa o gráfico com dados modificados para verificar a priorização de colunas"""
    # Criar DataFrame com dados de teste - todos os anos são 2020 mas com faturamento como prioridade
    df = pd.DataFrame({
        'cliente_cod': [3, 67, 19, 54, 58, 35, 123, 350, 148, 53],
        'cliente_nome': ['NACIONAL COMERCIAL HOSPITALAR S.A', 'SUPERMED COM. IMP. PROD. MED. HOSPITALARES LTDA',
                        'LABORPLAST COMERCIAL LTDA', 'EXOMED COM. ATAC. DE MEDICAMENTOS LTDA',
                        'DROGAFONTE LTDA ME', 'GLOBAL HOSPITALAR IMP. E COM. LTDA',
                        'HOSPFAR IND. COM. PROD. HOSP. S.A', 'SUPRAMED COM. MAT. MED. HOSP LTDA',
                        'LINEA - RJ COMERCIO LTDA', 'BELBI COMERCIO, IMPORT. E EXPORT. COMERCIAL EIRELI'],
        'ano': [2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020],
        'faturamento_total': [1500000.0, 1200000.0, 980000.0, 870000.0, 750000.0, 650000.0, 550000.0, 450000.0, 350000.0, 250000.0]
    })
    
    print("\n=== TESTE COM DADOS MODIFICADOS ===")
    print("Verificando se faturamento_total é priorizado automaticamente")
    
    # Gerar gráfico e verificar se faturamento_total é selecionado automaticamente
    chart_result = await ChartGenerator.generate_chart(
        df=df,
        chart_type='bar',
        test_mode=True
    )
    
    # Salvar o resultado do gráfico em um arquivo JSON para análise
    with open('single_year_chart_modified_result.json', 'w', encoding='utf-8') as f:
        json.dump(chart_result, f, ensure_ascii=False, indent=2)
    
    print(f"Resultado salvo em 'single_year_chart_modified_result.json'")
    
    # Verificar se faturamento_total foi priorizado automaticamente
    try:
        figure_data = json.loads(chart_result.get('figure', '{}'))
        if 'layout' in figure_data:
            x_axis = figure_data['layout']['xaxis'].get('title', {}).get('text', '')
            y_axis = figure_data['layout']['yaxis'].get('title', {}).get('text', '')
            
            print(f"Eixo X: {x_axis}")
            print(f"Eixo Y: {y_axis}")
            
            # Verificar se cliente_nome está sendo usado no eixo X
            if 'cliente' in x_axis.lower() and 'nome' in x_axis.lower():
                print("SUCESSO: Cliente Nome está sendo usado no eixo X")
            else:
                print(f"FALHA: O eixo X não está usando Cliente Nome: {x_axis}")
                
            # Verificar se faturamento_total está sendo usado no eixo Y
            if 'faturamento' in y_axis.lower() or 'total' in y_axis.lower():
                print("SUCESSO: Faturamento Total está sendo usado no eixo Y")
            else:
                print(f"FALHA: O eixo Y não está usando Faturamento Total: {y_axis}")
    except Exception as e:
        print(f"Erro ao analisar o resultado do gráfico modificado: {e}")
    
    return chart_result

if __name__ == "__main__":
    # Executar os testes
    print("\n=== INICIANDO TESTES DE GRÁFICO COM ANOS IGUAIS ===\n")
    
    try:
        # Executar o teste principal
        asyncio.run(test_single_year_chart())
        
        # Executar o teste com dados modificados
        asyncio.run(test_with_modified_data())
        
        print("\n=== TESTES CONCLUÍDOS COM SUCESSO ===\n")
    except Exception as e:
        print(f"\n=== ERRO DURANTE OS TESTES: {e} ===\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
