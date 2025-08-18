#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import inspect
from dotenv import load_dotenv
import logging
from sqlalchemy import text

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_db_connection")

# Carregar variáveis de ambiente
load_dotenv()

# Importar a classe Database
from pilot.common.sql_database import Database
from pilot.configs.config import Config

def test_database_connection():
    """Testa a conexão com o banco de dados."""
    try:
        # Mostrar variáveis de ambiente relacionadas ao banco de dados
        db_type = os.getenv("DB_TYPE", "mysql")
        db_host = os.getenv("LOCAL_DB_HOST", "localhost")
        db_port = os.getenv("LOCAL_DB_PORT", "5432")
        db_user = os.getenv("LOCAL_DB_USER", "postgres")
        db_name = os.getenv("LOCAL_DB_DATABASE", "postgres")
        
        logger.info(f"Configuração do banco de dados:")
        logger.info(f"  DB_TYPE: {db_type}")
        logger.info(f"  LOCAL_DB_HOST: {db_host}")
        logger.info(f"  LOCAL_DB_PORT: {db_port}")
        logger.info(f"  LOCAL_DB_USER: {db_user}")
        logger.info(f"  LOCAL_DB_DATABASE: {db_name}")
        
        # Inicializar configuração
        config = Config()
        
        # Criar instância do Database
        db = Database(config)
        
        # Verificar atributos da classe Database
        logger.info("Atributos da classe Database:")
        for attr in dir(db):
            if not attr.startswith('__'):
                logger.info(f"  {attr}")
        
        # Verificar se o atributo _engine existe
        if hasattr(db, '_engine'):
            logger.info("Atributo _engine encontrado na classe Database")
            logger.info(f"Engine URL: {db._engine.url}")
            
            # Testar uma consulta simples
            try:
                session = db._db_sessions()
                result = session.execute(text("SELECT 1")).fetchone()
                logger.info(f"Consulta de teste bem-sucedida: {result}")
                
                # Listar bancos de dados disponíveis
                databases = db.get_database_list()
                logger.info(f"Bancos de dados disponíveis: {databases}")
                
                # Listar tabelas do banco atual
                if db_type == 'postgres':
                    query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                else:
                    query = text("SHOW TABLES")
                    
                tables = session.execute(query).fetchall()
                logger.info(f"Tabelas disponíveis: {[t[0] for t in tables]}")
                
            except Exception as e:
                logger.error(f"Erro ao executar consulta: {e}")
        else:
            logger.error("Atributo _engine NÃO encontrado na classe Database")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao testar conexão com o banco de dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== INICIANDO TESTE DE CONEXÃO COM O BANCO DE DADOS ===")
    success = test_database_connection()
    if success:
        logger.info("=== TESTE DE CONEXÃO CONCLUÍDO COM SUCESSO ===")
    else:
        logger.error("=== TESTE DE CONEXÃO FALHOU ===")
