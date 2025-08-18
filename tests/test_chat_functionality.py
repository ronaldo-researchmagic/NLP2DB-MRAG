#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_chat_functionality")

# Carregar variáveis de ambiente
load_dotenv()

# Importar a função para garantir que os templates de prompt estejam carregados
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pilot.scene.chat_db.auto_execute.chat_fix import ensure_prompt_templates_loaded

async def test_chat_functionality():
    """Testa a funcionalidade do chat com diferentes bancos de dados."""
    try:
        from pilot.configs.config import Config
        from pilot.scene.base import ChatScene
        from pilot.scene.chat_factory import ChatFactory
        
        logger.info("Inicializando configuração...")
        CFG = Config()
        
        # Garantir que os templates de prompt estejam carregados
        logger.info("Carregando templates de prompt...")
        templates = ensure_prompt_templates_loaded()
        logger.info(f"Templates carregados: {list(templates.keys())}")
        
        # Verificar se a conexão com o banco de dados está configurada
        if not CFG.local_db:
            logger.error("Conexão com o banco de dados não inicializada. Verifique seu arquivo .env.")
            return False
        
        # Listar bancos de dados disponíveis
        logger.info("Listando bancos de dados disponíveis:")
        try:
            db_list = CFG.local_db.get_database_list()
            logger.info(f"Bancos de dados: {db_list}")
            
            if not db_list:
                logger.warning("Nenhum banco de dados encontrado.")
                return False
            
            # Usar o primeiro banco de dados da lista para teste
            test_db = db_list[0]
            logger.info(f"Usando banco de dados '{test_db}' para teste")
            
            # Testar a obtenção de uma sessão para o banco de dados
            logger.info(f"Testando obtenção de sessão para '{test_db}'...")
            try:
                # Verificar o tipo de banco de dados
                engine_name = CFG.local_db._engine.name
                logger.info(f"Tipo de banco de dados: {engine_name}")
                
                # Obter sessão para o banco de dados
                session = CFG.local_db.get_session(test_db)
                logger.info(f"Sessão obtida com sucesso para '{test_db}'")
                
                # Testar a execução de uma consulta simples
                logger.info("Testando execução de consulta simples...")
                from sqlalchemy import text
                result = session.execute(text("SELECT 1 as test"))
                logger.info(f"Consulta executada com sucesso: {result.fetchone()}")
                
                # Testar a criação de um chat
                logger.info("Testando criação de chat...")
                chat_factory = ChatFactory()
                
                chat_params = {
                    "chat_session_id": "test_session",
                    "user_input": "Quantas tabelas existem neste banco de dados?",
                    "db_name": test_db,
                    "temperature": 0.7,
                    "max_new_tokens": 1024,
                }
                
                # Criar chat
                chat = chat_factory.get_implementation(ChatScene.ChatWithDbExecute.value, **chat_params)
                logger.info("Chat criado com sucesso")
                
                # Testar geração de valores de entrada
                logger.info("Testando geração de valores de entrada...")
                input_values = await chat.generate_input_values()
                logger.info(f"Valores de entrada gerados: {input_values}")
                
                return True
            except Exception as e:
                logger.error(f"Erro ao obter sessão para '{test_db}': {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
        except Exception as e:
            logger.error(f"Erro ao listar bancos de dados: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    except Exception as e:
        logger.error(f"Erro ao testar funcionalidade do chat: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Função principal."""
    logger.info("=== INICIANDO TESTE DE FUNCIONALIDADE DO CHAT ===")
    
    success = await test_chat_functionality()
    
    if success:
        logger.info("=== TESTE DE FUNCIONALIDADE DO CHAT CONCLUÍDO COM SUCESSO ===")
    else:
        logger.error("=== TESTE DE FUNCIONALIDADE DO CHAT FALHOU ===")

if __name__ == "__main__":
    asyncio.run(main())
