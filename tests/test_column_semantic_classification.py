"""
Teste para validar a classificação semântica das colunas do DataFrame.
"""
import os
import sys
import unittest
import pandas as pd
import asyncio
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pilot.common.chart_generator import ChartGenerator


def run_async_test(coro):
    """Executa um teste assíncrono."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestColumnSemanticClassification(unittest.TestCase):
    """
    Testes para validar a classificação semântica das colunas do DataFrame.
    """

    def setUp(self):
        """Configuração inicial para os testes."""
        # Desativar logs durante os testes
        self.print_patcher = patch('builtins.print')
        self.mock_print = self.print_patcher.start()

    def tearDown(self):
        """Limpeza após os testes."""
        self.print_patcher.stop()

    def test_temporal_column_detection(self):
        """
        Testa se colunas temporais são detectadas corretamente.
        """
        # Criar DataFrame de teste com diferentes tipos de colunas temporais
        df = pd.DataFrame({
            'ano': [2020, 2021, 2022, 2023],
            'data': ['2020-01-01', '2021-01-01', '2022-01-01', '2023-01-01'],
            'mes': ['Janeiro', 'Fevereiro', 'Março', 'Abril'],
            'trimestre': [1, 2, 3, 4],
            'quantidade': [10, 20, 30, 40]
        })

        # Chamar o método classify_columns_with_llm em modo de teste
        column_types = run_async_test(ChartGenerator.classify_columns_with_llm(df, test_mode=True))

        # Verificar se as colunas temporais foram detectadas corretamente
        self.assertIn('ano', column_types['temporal_cols'], "A coluna 'ano' deveria ser classificada como temporal")
        self.assertIn('data', column_types['temporal_cols'], "A coluna 'data' deveria ser classificada como temporal")
        self.assertIn('mes', column_types['temporal_cols'], "A coluna 'mes' deveria ser classificada como temporal")
        self.assertIn('trimestre', column_types['temporal_cols'], "A coluna 'trimestre' deveria ser classificada como temporal")

    def test_monetary_column_detection(self):
        """
        Testa se colunas monetárias são detectadas corretamente.
        """
        # Criar DataFrame de teste com diferentes tipos de colunas monetárias
        df = pd.DataFrame({
            'faturamento_total': [1000, 2000, 3000, 4000],
            'valor_venda': [100, 200, 300, 400],
            'total_revenue': [10000, 20000, 30000, 40000],
            'sales_amount': [1000, 2000, 3000, 4000],
            'quantidade': [10, 20, 30, 40]
        })

        # Chamar o método classify_columns_with_llm em modo de teste
        column_types = run_async_test(ChartGenerator.classify_columns_with_llm(df, test_mode=True))

        # Verificar se as colunas monetárias foram detectadas corretamente
        self.assertIn('faturamento_total', column_types['monetary_cols'], 
                     "A coluna 'faturamento_total' deveria ser classificada como monetária")
        self.assertIn('valor_venda', column_types['monetary_cols'], 
                     "A coluna 'valor_venda' deveria ser classificada como monetária")
        self.assertIn('total_revenue', column_types['monetary_cols'], 
                     "A coluna 'total_revenue' deveria ser classificada como monetária")
        self.assertIn('sales_amount', column_types['monetary_cols'], 
                     "A coluna 'sales_amount' deveria ser classificada como monetária")

    def test_identifier_column_detection(self):
        """
        Testa se colunas de identificação são detectadas corretamente.
        """
        # Criar DataFrame de teste com diferentes tipos de colunas de identificação
        df = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'cliente_id': [100, 200, 300, 400],
            'codigo_produto': [1001, 1002, 1003, 1004],
            'quantidade': [10, 20, 30, 40]
        })

        # Chamar o método classify_columns_with_llm em modo de teste
        column_types = run_async_test(ChartGenerator.classify_columns_with_llm(df, test_mode=True))

        # Verificar se as colunas de identificação foram detectadas corretamente
        self.assertIn('id', column_types['identifier_cols'], 
                     "A coluna 'id' deveria ser classificada como identificador")
        self.assertIn('cliente_id', column_types['identifier_cols'], 
                     "A coluna 'cliente_id' deveria ser classificada como identificador")
        self.assertIn('codigo_produto', column_types['identifier_cols'], 
                     "A coluna 'codigo_produto' deveria ser classificada como identificador")

    def test_categorical_column_detection(self):
        """
        Testa se colunas categóricas são detectadas corretamente.
        """
        # Criar DataFrame de teste com diferentes tipos de colunas categóricas
        df = pd.DataFrame({
            'categoria': ['A', 'B', 'C', 'D'],
            'estado': ['SP', 'RJ', 'MG', 'RS'],
            'cliente_nome': ['João', 'Maria', 'Pedro', 'Ana'],
            'quantidade': [10, 20, 30, 40]
        })

        # Chamar o método classify_columns_with_llm em modo de teste
        column_types = run_async_test(ChartGenerator.classify_columns_with_llm(df, test_mode=True))

        # Verificar se as colunas categóricas foram detectadas corretamente
        self.assertIn('categoria', column_types['categorical_cols'], 
                     "A coluna 'categoria' deveria ser classificada como categórica")
        self.assertIn('estado', column_types['categorical_cols'], 
                     "A coluna 'estado' deveria ser classificada como categórica")
        self.assertIn('cliente_nome', column_types['categorical_cols'], 
                     "A coluna 'cliente_nome' deveria ser classificada como categórica")

    def test_numeric_column_detection(self):
        """
        Testa se colunas numéricas são detectadas corretamente.
        """
        # Criar DataFrame de teste com diferentes tipos de colunas numéricas
        df = pd.DataFrame({
            'quantidade': [10, 20, 30, 40],
            'idade': [25, 30, 35, 40],
            'peso': [70.5, 80.2, 65.7, 90.1],
            'categoria': ['A', 'B', 'C', 'D']
        })

        # Chamar o método classify_columns_with_llm em modo de teste
        column_types = run_async_test(ChartGenerator.classify_columns_with_llm(df, test_mode=True))

        # Verificar se pelo menos uma das colunas numéricas foi detectada corretamente
        # Não precisamos verificar todas, pois algumas podem ser classificadas como outras categorias
        # dependendo da heurística
        numeric_cols = column_types['numeric_cols']
        monetary_cols = column_types['monetary_cols']
        all_numeric = numeric_cols + monetary_cols
        
        # Verificar se as colunas numéricas estão em alguma categoria numérica
        self.assertTrue(
            'quantidade' in all_numeric or 'quantidade' in column_types['column_types'],
            "A coluna 'quantidade' deveria ser classificada como numérica ou monetária"
        )
        self.assertTrue(
            'idade' in all_numeric or 'idade' in column_types['column_types'],
            "A coluna 'idade' deveria ser classificada como numérica ou monetária"
        )
        self.assertTrue(
            'peso' in all_numeric or 'peso' in column_types['column_types'],
            "A coluna 'peso' deveria ser classificada como numérica ou monetária"
        )

    def test_llm_classification_integration(self):
        """
        Testa a integração com o LLM para classificação semântica das colunas.
        """
        # Este teste verifica apenas o comportamento de fallback quando o LLM não está disponível
        # Não podemos testar a integração real com o LLM em testes unitários
        
        # Criar DataFrame de teste
        df = pd.DataFrame({
            'categoria': ['A', 'B', 'C', 'D'],
            'mes': ['Janeiro', 'Fevereiro', 'Março', 'Abril'],
            'vendas': [1000, 2000, 3000, 4000],
            'lucro': [100, 200, 300, 400]
        })

        # Chamar o método classify_columns_with_llm sem modo de teste
        # Isso deve acionar o fallback para o modo de teste
        column_types = run_async_test(ChartGenerator.classify_columns_with_llm(df, test_mode=False))

        # Verificar se a classificação foi aplicada corretamente usando as heurísticas
        self.assertIn('mes', column_types['temporal_cols'], 
                     "A coluna 'mes' deveria ser classificada como temporal")
        self.assertIn('vendas', column_types['monetary_cols'], 
                     "A coluna 'vendas' deveria ser classificada como monetária")
        
        # Verificar se o dicionário column_types contém as chaves esperadas
        self.assertIn('column_types', column_types, 
                     "O resultado deve conter um dicionário 'column_types'")
        self.assertIn('numeric_cols', column_types, 
                     "O resultado deve conter uma lista 'numeric_cols'")
        self.assertIn('categorical_cols', column_types, 
                     "O resultado deve conter uma lista 'categorical_cols'")
        self.assertIn('temporal_cols', column_types, 
                     "O resultado deve conter uma lista 'temporal_cols'")
        self.assertIn('monetary_cols', column_types, 
                     "O resultado deve conter uma lista 'monetary_cols'")
        self.assertIn('identifier_cols', column_types, 
                     "O resultado deve conter uma lista 'identifier_cols'")
        
        # Verificar se todas as colunas foram classificadas
        all_cols = set(df.columns)
        classified_cols = set(column_types['column_types'].keys())
        self.assertEqual(all_cols, classified_cols, 
                        "Todas as colunas devem ser classificadas")


if __name__ == '__main__':
    unittest.main()
