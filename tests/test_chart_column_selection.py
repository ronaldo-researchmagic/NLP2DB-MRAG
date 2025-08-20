import unittest
import pandas as pd
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Adicionar o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pilot.common.chart_generator import ChartGenerator

def run_async_test(coro):
    """Executa um teste assíncrono."""
    return asyncio.get_event_loop().run_until_complete(coro)

class TestChartGenerationWithLLM(unittest.TestCase):
    """
    Testes para a nova lógica de geração de gráficos baseada em LLM.
    """

    def setUp(self):
        """Configuração inicial para os testes."""
        self.print_patcher = patch('builtins.print')
        self.mock_print = self.print_patcher.start()

    def tearDown(self):
        """Limpeza após os testes."""
        self.print_patcher.stop()

    @patch('pilot.common.chart_generator.ChartGenerator._get_semantic_types', new_callable=AsyncMock)
    def test_temporal_x_quantitative_y(self, mock_get_types):
        """Testa a regra: Eixo X = temporal, Eixo Y = quantitativo."""
        df = pd.DataFrame({
            'data_venda': pd.to_datetime(['2023-01-01', '2023-01-02']),
            'total_vendas': [100, 150],
            'vendedor': ['A', 'B']
        })
        mock_get_types.return_value = {
            'data_venda': 'temporal',
            'total_vendas': 'quantitative',
            'vendedor': 'categorical'
        }

        chart_data = run_async_test(ChartGenerator.generate_chart(df, test_mode=True))

        self.assertIsNotNone(chart_data)
        chart_config = chart_data['chart_config']
        self.assertEqual(chart_config['x'], 'data_venda')
        self.assertEqual(chart_config['y'], 'total_vendas')
        self.assertEqual(chart_config['type'], 'line') # Temporal no eixo X deve gerar gráfico de linha

    @patch('pilot.common.chart_generator.ChartGenerator._get_semantic_types', new_callable=AsyncMock)
    def test_categorical_x_quantitative_y(self, mock_get_types):
        """Testa a regra: Eixo X = categórico, Eixo Y = quantitativo."""
        df = pd.DataFrame({
            'produto': ['A', 'B', 'C'],
            'faturamento': [1000, 2000, 1500]
        })
        mock_get_types.return_value = {
            'produto': 'categorical',
            'faturamento': 'quantitative'
        }

        chart_data = run_async_test(ChartGenerator.generate_chart(df, test_mode=True))

        self.assertIsNotNone(chart_data)
        chart_config = chart_data['chart_config']
        self.assertEqual(chart_config['x'], 'produto')
        self.assertEqual(chart_config['y'], 'faturamento')
        self.assertEqual(chart_config['type'], 'bar')

    @patch('pilot.common.chart_generator.ChartGenerator._get_semantic_types', new_callable=AsyncMock)
    def test_with_color_dimension(self, mock_get_types):
        """Testa a regra: Usar terceira dimensão categórica para cor."""
        df = pd.DataFrame({
            'mes': ['Jan', 'Fev', 'Jan', 'Fev'],
            'vendas': [100, 150, 120, 180],
            'regiao': ['Norte', 'Norte', 'Sul', 'Sul']
        })
        mock_get_types.return_value = {
            'mes': 'categorical', # Pode ser tratado como categórico ou temporal
            'vendas': 'quantitative',
            'regiao': 'categorical'
        }

        chart_data = run_async_test(ChartGenerator.generate_chart(df, test_mode=True))

        self.assertIsNotNone(chart_data)
        chart_config = chart_data['chart_config']
        self.assertEqual(chart_config['x'], 'mes')
        self.assertEqual(chart_config['y'], 'vendas')
        self.assertEqual(chart_config['color'], 'regiao')

    def test_fallback_logic(self):
        """Testa o fallback quando o LLM falha, usando o test_mode para simular."""
        df = pd.DataFrame({
            'categoria': ['A', 'B'],
            'valor': [10, 20]
        })

        # Executar com test_mode=True força o uso da lógica de fallback/simulação
        chart_data = run_async_test(ChartGenerator.generate_chart(df, test_mode=True))

        self.assertIsNotNone(chart_data)
        chart_config = chart_data['chart_config']
        self.assertEqual(chart_config['x'], 'categoria')
        self.assertEqual(chart_config['y'], 'valor')

    @patch('pilot.common.chart_generator.ChartGenerator._get_semantic_types', new_callable=AsyncMock)
    def test_no_suitable_columns(self, mock_get_types):
        """Testa o que acontece quando não há colunas adequadas."""
        df = pd.DataFrame({
            'texto': ['abc', 'def']
        })
        mock_get_types.return_value = {
            'texto': 'categorical'
        }

        # Sem coluna quantitativa, a geração do gráfico deve falhar graciosamente
        chart_data = run_async_test(ChartGenerator.generate_chart(df, test_mode=True))
        
        # O comportamento esperado é que y_col não seja encontrado e retorne None
        self.assertIsNone(chart_data)

    @patch('pilot.common.chart_generator.ChartGenerator._get_semantic_types', new_callable=AsyncMock)
    def test_numeric_code_column_is_categorical(self, mock_get_types):
        """Testa se uma coluna de código numérico é tratada como categórica."""
        df = pd.DataFrame({
            'produto_cod': [101, 102, 103],
            'estoque': [250, 300, 280],
            'loja': ['A', 'B', 'A']
        })
        mock_get_types.return_value = {
            'produto_cod': 'categorical', # LLM classifica corretamente como categórica
            'estoque': 'quantitative',
            'loja': 'categorical'
        }

        chart_data = run_async_test(ChartGenerator.generate_chart(df, test_mode=True))

        self.assertIsNotNone(chart_data)
        chart_config = chart_data['chart_config']
        self.assertEqual(chart_config['x'], 'produto_cod')
        self.assertEqual(chart_config['y'], 'estoque')
        self.assertEqual(chart_config['color'], 'loja')
        self.assertEqual(chart_config['type'], 'bar')

if __name__ == '__main__':
    unittest.main()
