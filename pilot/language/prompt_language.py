#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from pilot.configs.config import Config

CFG = Config()

# Dictionary of prompts in different languages
prompt_templates = {
    "en": {
        # SQL Auto Execute Prompts
        "sql_expert_role": "You are a SQL expert. Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.",
        "sql_limit_results": "Unless the user specifies in his question a specific number of examples he wishes to obtain, always limit your query to at most {top_k} results.",
        "sql_use_few_tables": "Use as few tables as possible when querying.",
        "sql_data_validation": "When generating insert, delete, update, or replace SQL, please make sure to use the data given by the human, and cannot use any unknown data. If you do not get enough information, speak to user: I don't have enough data complete your request.",
        "sql_schema_attention": "Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.",
        "sql_tables_prefix": "Only use the following tables generate sql:",
        "sql_question_prefix": "Question:",
        "sql_response_format": "You must respond in JSON format as following format:",
        "sql_json_parsing": "Ensure the response is correct json and can be parsed by Python json.loads",
        "sql_thoughts_reasoning": "reasoning",
        "sql_thoughts_speak": "thoughts summary to say to user",
        "sql_query_to_run": "SQL Query to run",
        
        # Scene Definition
        "scene_define": "You are an AI designed to answer human questions, please follow the prompts and conventions of the system's input for your answers"
    },
    "pt": {
        # SQL Auto Execute Prompts
        "sql_expert_role": "Você é um especialista em SQL. Dada uma pergunta, primeiro crie uma consulta {dialect} sintaticamente correta para executar, depois analise os resultados da consulta e retorne a resposta.",
        "sql_limit_results": "A menos que o usuário especifique em sua pergunta um número específico de exemplos que deseja obter, sempre limite sua consulta a no máximo {top_k} resultados.",
        "sql_use_few_tables": "Use o menor número possível de tabelas ao consultar.",
        "sql_data_validation": "Ao gerar SQL de inserção, exclusão, atualização ou substituição, certifique-se de usar os dados fornecidos pelo humano, e não pode usar dados desconhecidos. Se você não tiver informações suficientes, diga ao usuário: Não tenho dados suficientes para completar sua solicitação.",
        "sql_schema_attention": "Preste atenção para usar apenas os nomes de colunas que você pode ver na descrição do esquema. Tenha cuidado para não consultar colunas que não existem. Além disso, preste atenção em qual coluna está em qual tabela.",
        "sql_tables_prefix": "Use apenas as seguintes tabelas para gerar SQL:",
        "sql_question_prefix": "Pergunta:",
        "sql_response_format": "Você deve responder no formato JSON conforme o seguinte formato:",
        "sql_json_parsing": "Certifique-se de que a resposta seja um JSON correto e possa ser analisada por Python json.loads",
        "sql_thoughts_reasoning": "raciocínio",
        "sql_thoughts_speak": "resumo dos pensamentos para dizer ao usuário",
        "sql_query_to_run": "Consulta SQL para executar",
        
        # Scene Definition
        "scene_define": "Você é uma IA projetada para responder perguntas humanas, por favor siga as instruções e convenções da entrada do sistema para suas respostas"
    }
}

def get_prompt_template(key, language=None):
    """
    Get a prompt template in the specified language
    
    Args:
        key: The key of the prompt template
        language: The language to use (defaults to the config language)
        
    Returns:
        The prompt template in the specified language
    """
    if language is None:
        language = CFG.LANGUAGE
        
    # Default to English if the language is not supported
    if language not in prompt_templates:
        language = "en"
        
    # Default to English template if the key is not found in the specified language
    return prompt_templates.get(language, {}).get(key, prompt_templates.get("en", {}).get(key, ""))
