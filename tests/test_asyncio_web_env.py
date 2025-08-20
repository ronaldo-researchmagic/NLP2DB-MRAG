"""
Teste para simular um ambiente web com loop de eventos assíncrono
e verificar se a solução para o problema de asyncio funciona corretamente.
"""
import asyncio
import sys
import os
import pandas as pd

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pilot.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction

# Configurar um loop de eventos global para simular um ambiente web
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def run_web_simulation():
    """Simula um ambiente web com um loop de eventos em execução."""
    print("Simulando ambiente web com loop de eventos em execução...")
    
    # Criar dados de teste
    df = pd.DataFrame({
        'categoria': ['Eletrônicos', 'Roupas', 'Alimentos'] * 2,
        'mes': ['Janeiro'] * 3 + ['Fevereiro'] * 3,
        'vendas': [1200, 950, 1500, 1350, 1100, 1650],
        'lucro': [240, 285, 300, 270, 330, 330]
    })
    
    # Consulta SQL de teste
    sql_query = """
    SELECT categoria, mes, SUM(vendas) as vendas, SUM(lucro) as lucro
    FROM vendas
    WHERE mes IN ('Janeiro', 'Fevereiro')
    GROUP BY categoria, mes
    ORDER BY mes, categoria
    """
    
    # Criar o parser
    parser = DbChatOutputParser(sep="\n", is_stream_out=False)
    
    # Criar um objeto SqlAction simulado
    sql_action = SqlAction(sql_query, {"speak": "Aqui estão as vendas por categoria e mês"})
    
    # Preparar os dados para o parser
    data_for_parser = [['categoria', 'mes', 'vendas', 'lucro']]
    for _, row in df.iterrows():
        data_for_parser.append([row['categoria'], row['mes'], row['vendas'], row['lucro']])
    
    # Testar o parser em modo síncrono (que deve chamar o assíncrono internamente)
    # Este é o cenário que estava falhando antes com o erro de asyncio.run()
    print("Testando o parser em modo síncrono com loop de eventos em execução...")
    try:
        result = parser.parse_view_response(sql_action, data_for_parser, test_mode=True)
        print("SUCESSO! O parser funcionou corretamente em modo síncrono.")
        
        # Salvar o resultado em um arquivo para inspeção
        with open('web_env_test_result.html', 'w', encoding='utf-8') as f:
            f.write(result)
        print("Resultado salvo em 'web_env_test_result.html'")
        
    except Exception as e:
        print(f"ERRO ao executar o parser em modo síncrono: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Função principal para executar o teste."""
    print("Iniciando teste de ambiente web com asyncio...")
    
    # Executar a simulação no loop de eventos
    success = loop.run_until_complete(run_web_simulation())
    
    # Fechar o loop de eventos
    loop.close()
    
    if success:
        print("\nTeste concluído com sucesso! A solução para o problema de asyncio funciona corretamente.")
        return 0
    else:
        print("\nTeste falhou! A solução para o problema de asyncio não funcionou corretamente.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
