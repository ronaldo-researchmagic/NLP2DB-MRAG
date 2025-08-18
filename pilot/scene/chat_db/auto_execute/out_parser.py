import json
import re
from abc import ABC, abstractmethod
from typing import Dict, NamedTuple
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

    def parse_view_response(self, speak, data) -> str:
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
        
        table_style = """<style> 
            table{border-collapse:collapse;width:100%;height:80%;margin:0 auto;float:center;border: 1px solid #007bff; background-color:#333; color:#fff}th,td{border:1px solid #ddd;padding:3px;text-align:center}th{background-color:#C9C3C7;color: #fff;font-weight: bold;}tr:nth-child(even){background-color:#444}tr:hover{background-color:#444}
            .sql-query{background-color:#2a2a2a;color:#fff;padding:10px;border-radius:5px;margin:10px 0;font-family:monospace;white-space:pre-wrap;}
         </style>"""
        
        html_table = df.to_html(index=False, escape=False)
        html = f"<html><head>{table_style}</head><body>{html_table}</body></html>"
        
        # Include SQL query in the response with better formatting using language system
        sql_label = get_lang_text("sql_query_used")
        sql_section = f"<div class='sql-query'><strong>{sql_label}</strong><br>{sql_query}</div>"
        
        view_text = f"##### {thoughts_text}" + "\n" + sql_section + "\n" + html.replace("\n", " ")
        return view_text

    @property
    def _type(self) -> str:
        return "sql_chat"
