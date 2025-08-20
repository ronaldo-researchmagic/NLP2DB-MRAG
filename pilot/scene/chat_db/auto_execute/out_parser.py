import json
import re
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, NamedTuple, Optional, Any
import pandas as pd
from pilot.utils import build_logger
from pilot.out_parser.base import BaseOutputParser, T
from pilot.configs.model_config import LOGDIR
from pilot.language.translation_handler import get_lang_text
from pilot.configs.config import Config

CFG = Config()


class SqlAction(NamedTuple):
    sql: str
    thoughts: Dict


logger = build_logger("webserver", LOGDIR + "DbChatOutputParser.log")


class DbChatOutputParser(BaseOutputParser):
    def __init__(self, sep: str, is_stream_out: bool):
        super().__init__(sep=sep, is_stream_out=is_stream_out)

    def parse_prompt_response(self, model_out_text):
        clean_str = super().parse_prompt_response(model_out_text)
        print("clean prompt response:", clean_str)
        
        # Verificar se clean_str já é um dicionário
        if isinstance(clean_str, dict):
            response = clean_str
        else:
            # Tentar carregar como JSON string
            try:
                response = json.loads(clean_str)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Erro ao processar resposta JSON: {e}")
                # Fallback para um formato básico
                response = {"sql": "SELECT 1;", "thoughts": "Erro ao processar resposta."}
        
        sql, thoughts = response["sql"], response["thoughts"]
        return SqlAction(sql, thoughts)

    async def parse_view_response_async(self, speak, data, test_mode: bool = False) -> str:
        # Extract SQL query from the SqlAction object
        sql_query = ""
        if isinstance(speak, SqlAction):
            sql_query = speak.sql
        
        # Format the thoughts for display
        thoughts_text = ""
        if isinstance(speak, SqlAction):
            if isinstance(speak.thoughts, dict):
                thoughts_text = speak.thoughts.get('speak', '') or speak.thoughts.get('reasoning', '')
            else:
                thoughts_text = str(speak.thoughts)
        else:
            thoughts_text = str(speak)
        
        ### Format data for table view
        if len(data) <= 1:
            data.insert(0, ["result"])
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Generate chart if possible using the new async function
        chart_json = None
        chart_explanation = ""
        if len(df) > 0 and len(df.columns) > 1:
            print(f"DEBUG: Attempting to generate chart for query: {sql_query}")
            # Importar ChartGenerator somente quando necessário para evitar importação circular
            from pilot.common.chart_generator import ChartGenerator
            chart_result = await ChartGenerator.generate_chart(df, sql_query=sql_query, test_mode=test_mode)
            if chart_result:
                chart_json = chart_result['figure']
                chart_type = chart_result['chart_config']['type']
                chart_explanation = chart_result.get('explanation', '')
                print(f"DEBUG: Chart generated successfully with type: {chart_type}")
                if chart_explanation:
                    print(f"DEBUG: Chart explanation: {chart_explanation[:100]}...")
            else:
                print("DEBUG: Chart generation returned None")
        
        table_style = """<style> 
            table{border-collapse:collapse;width:100%;height:80%;margin:0 auto;float:center;border: 1px solid #007bff; background-color:#333; color:#fff}th,td{border:1px solid #ddd;padding:3px;text-align:center}th{background-color:#C9C3C7;color: #fff;font-weight: bold;}tr:nth-child(even){background-color:#444}tr:hover{background-color:#444}
            .sql-query{background-color:#2a2a2a;color:#fff;padding:10px;border-radius:5px;margin:10px 0;font-family:monospace;white-space:pre-wrap;}
            .chart-container{margin:20px 0;}
            .chart-explanation{background-color:#2a2a2a;color:#fff;padding:10px;border-radius:5px;margin:10px 0;font-style:italic;}
         </style>"""
        
        html_table = df.to_html(index=False, escape=False)
        html = f"<html><head>{table_style}</head><body>{html_table}</body></html>"
        
        # Include SQL query in the response with better formatting using language system
        sql_label = get_lang_text("sql_query_used")
        sql_section = f"<div class='sql-query'><strong>{sql_label}</strong><br>{sql_query}</div>"
        
        # Add chart data as a hidden div with JSON data that will be processed by the frontend
        chart_div = ""
        chart_explanation_div = ""
        if chart_json:
            # Converter o objeto Figure para JSON e depois escapar
            import html as html_module
            import json
            
            # Converter Figure para JSON usando o método to_json() do Plotly
            try:
                chart_json_str = chart_json.to_json()
                safe_chart_json = html_module.escape(chart_json_str)
                print(f"DEBUG: Adding chart div with JSON data (length: {len(safe_chart_json) if safe_chart_json else 0})")
                chart_div = f"<div id='chart-data' style='display:none;' data-chart='{safe_chart_json}'></div>"
            except Exception as e:
                print(f"DEBUG: Error converting chart to JSON: {str(e)}")
                chart_div = "<div class='chart-error'>Erro ao processar o gráfico</div>"
            
            # Adicionar explicação do LLM sobre o gráfico, se disponível
            if chart_explanation:
                # Usar apenas a chave para get_lang_text ou usar o valor padrão diretamente
                explanation_label = get_lang_text('chart_explanation_label')
                if explanation_label == 'chart_explanation_label':  # Se não foi traduzido
                    explanation_label = 'Explicação do gráfico:'
                chart_explanation_div = f"<div class='chart-explanation'><strong>{explanation_label}</strong><br>{chart_explanation}</div>"
        
        # Combine all elements into the final view text
        html_content = html.replace("\n", " ")
        view_text = f"##### {thoughts_text}" + "\n" + sql_section + "\n" + chart_explanation_div + "\n" + chart_div + "\n" + html_content
        return view_text
        
    def parse_view_response(self, speak, data, test_mode: bool = False) -> str:
        # Esta é uma versão síncrona que chama a versão assíncrona
        # Necessária para manter compatibilidade com a interface existente
        try:
            # Tenta obter o loop de eventos atual
            loop = asyncio.get_event_loop()
            # Verifica se o loop está rodando
            if loop.is_running():
                # Se já estiver em um loop, precisamos criar uma tarefa futura
                # Isso não é ideal, mas é uma solução temporária
                import nest_asyncio
                nest_asyncio.apply()  # Permite loops aninhados
                return loop.run_until_complete(self.parse_view_response_async(speak, data, test_mode=test_mode))
            else:
                # Se não estiver em um loop, podemos usar run_until_complete
                return loop.run_until_complete(self.parse_view_response_async(speak, data, test_mode=test_mode))
        except RuntimeError:
            # Fallback para asyncio.run se não conseguir obter o loop atual
            # Isso só funcionará se não estivermos em um loop de eventos
            return asyncio.run(self.parse_view_response_async(speak, data, test_mode=test_mode))

    @property
    def _type(self) -> str:
        return "sql_chat"
