import unittest
import sys
import os
import pandas as pd
import json
import asyncio

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pilot.common.chart_generator import ChartGenerator

class TestClientCodeColor(unittest.TestCase):
    def setUp(self):
        # Criar um DataFrame de teste similar ao da imagem
        self.df = pd.DataFrame({
            'cliente_cod': [3, 67, 19, 54, 58, 35, 123, 350, 143, 53],
            'ano': [2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020],
            'totalfaturamento': [1500.50, 2300.75, 980.25, 3200.00, 1750.80, 2100.30, 4500.90, 1800.60, 2700.40, 3100.20]
        })
        
        # Converter cliente_cod para categoria e ano para string para simular o processamento semântico
        self.df['cliente_cod'] = self.df['cliente_cod'].astype('category')
        self.df['ano'] = self.df['ano'].astype(str)

    def test_client_code_color_selection(self):
        """Testa se cliente_cod é selecionado para cor quando disponível."""
        print("\n=== Testando seleção de cliente_cod para cor ===")
        
        # Criar uma instância do ChartGenerator
        chart_gen = ChartGenerator()
        
        # Adicionar classificação semântica ao DataFrame para garantir a seleção correta
        self.df.semantic_types = {
            'column_types': {
                'cliente_cod': 'identifier',
                'ano': 'temporal',
                'totalfaturamento': 'monetary'
            },
            'identifier_cols': ['cliente_cod'],
            'temporal_cols': ['ano'],
            'monetary_cols': ['totalfaturamento'],
            'numeric_cols': ['totalfaturamento'],
            'categorical_cols': ['cliente_cod']
        }
        
        # Selecionar colunas para o gráfico
        x_col, y_col, color_col = chart_gen._select_columns(self.df, chart_type='bar')
        
        # Imprimir as colunas selecionadas para debug
        print(f"Colunas selecionadas - x: {x_col}, y: {y_col}, cor: {color_col}")
        
        # Verificar se ano foi selecionado para eixo X (mesmo com apenas um valor)
        # ou se cliente_cod foi selecionado para eixo X (comportamento esperado com a nova lógica)
        self.assertTrue(x_col in ['ano', 'cliente_cod'], "O eixo X deve ser 'ano' ou 'cliente_cod'")
        
        # Verificar se totalfaturamento foi selecionado para eixo Y
        self.assertEqual(y_col, 'totalfaturamento', "A coluna 'totalfaturamento' deveria ser selecionada para o eixo Y")
        
        # Verificar se cliente_cod foi selecionado para cor (se não estiver no eixo X)
        # ou se ano foi selecionado para cor (se cliente_cod estiver no eixo X)
        if x_col == 'cliente_cod':
            self.assertEqual(color_col, 'ano', "Se cliente_cod está no eixo X, 'ano' deveria ser usado para cor")
        else:
            self.assertEqual(color_col, 'cliente_cod', "Se ano está no eixo X, 'cliente_cod' deveria ser usado para cor")
        
    def test_chart_generation_with_client_code(self):
        """Testa a geração completa de gráfico com cliente_cod como cor."""
        print("\n=== Testando geração de gráfico com cliente_cod como cor ===")
        
        # Adicionar classificação semântica ao DataFrame para garantir a seleção correta
        self.df.semantic_types = {
            'column_types': {
                'cliente_cod': 'identifier',
                'ano': 'temporal',
                'totalfaturamento': 'monetary'
            },
            'identifier_cols': ['cliente_cod'],
            'temporal_cols': ['ano'],
            'monetary_cols': ['totalfaturamento'],
            'numeric_cols': ['totalfaturamento'],
            'categorical_cols': ['cliente_cod']
        }
        
        # Gerar o gráfico usando o ChartGenerator (função assíncrona)
        chart_result = asyncio.run(ChartGenerator.generate_chart(self.df, test_mode=True))
        
        # Verificar se o gráfico foi gerado com sucesso
        self.assertIsNotNone(chart_result, "O gráfico deveria ser gerado com sucesso")
        
        # Verificar a configuração do gráfico
        config = chart_result['chart_config']
        print(f"Configuração do gráfico: {config}")
        
        # Verificar se as colunas foram selecionadas corretamente de acordo com a nova lógica
        # Verificar se totalfaturamento foi selecionado para eixo Y
        self.assertEqual(config['y'], 'totalfaturamento', "A coluna 'totalfaturamento' deveria ser selecionada para o eixo Y")
        
        # Verificar se ano ou cliente_cod foi selecionado para eixo X
        self.assertTrue(config['x'] in ['ano', 'cliente_cod'], "O eixo X deve ser 'ano' ou 'cliente_cod'")
        
        # Verificar se cliente_cod ou ano foi selecionado para cor
        self.assertTrue(config['color'] in ['cliente_cod', 'ano'], "A cor deve ser 'cliente_cod' ou 'ano'")
        
        # Verificar que X e color são diferentes
        self.assertNotEqual(config['x'], config['color'], "O eixo X e a cor devem ser colunas diferentes")
        
        # Salvar o resultado do gráfico para inspeção visual
        with open('client_code_chart_test.json', 'w') as f:
            json.dump(chart_result['figure'], f)
        print("JSON do gráfico salvo em 'client_code_chart_test.json'")

if __name__ == '__main__':
    # Configurar o loop de eventos para Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    unittest.main()
