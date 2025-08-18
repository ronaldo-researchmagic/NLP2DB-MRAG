#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_db_session")

# Carregar variáveis de ambiente
load_dotenv()

def setup_database_connection():
    """Configura a conexão com o banco de dados."""
    try:
        # Obter variáveis de ambiente para PostgreSQL
        db_type = os.getenv("DB_TYPE", "postgres").lower()
        
        if db_type == "sqlite":
            db_path = os.getenv("DB_PATH", "data/faturamento.db")
            connection_uri = f"sqlite:///{db_path}"
        elif db_type in ["postgres", "postgresql"]:
            host = os.getenv("LOCAL_DB_HOST", "localhost")
            port = int(os.getenv("LOCAL_DB_PORT", 5432))
            user = os.getenv("LOCAL_DB_USER", "postgres")
            password = os.getenv("LOCAL_DB_PASSWORD", "")
            database = os.getenv("LOCAL_DB_DATABASE", "postgres")
            connection_uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:  # MySQL
            host = os.getenv("LOCAL_DB_HOST", "localhost")
            port = int(os.getenv("LOCAL_DB_PORT", 3306))
            user = os.getenv("LOCAL_DB_USER", "root")
            password = os.getenv("LOCAL_DB_PASSWORD", "")
            database = os.getenv("LOCAL_DB_DATABASE", "")
            connection_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        
        logger.info(f"Criando engine com URI: {connection_uri}")
        engine = create_engine(connection_uri)
        
        return engine
    except Exception as e:
        logger.error(f"Erro ao configurar conexão com o banco de dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def test_database_list():
    """Testa a listagem de bancos de dados/esquemas."""
    try:
        from pilot.common.sql_database import Database
        
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Criar instância do Database
        db = Database(engine)
        
        # Listar bancos de dados/esquemas
        logger.info("Listando bancos de dados/esquemas:")
        db_list = db.get_database_list()
        logger.info(f"Bancos de dados/esquemas: {db_list}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao listar bancos de dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_session_with_main():
    """Testa a obtenção de uma sessão com o banco de dados 'main'."""
    try:
        from pilot.common.sql_database import Database
        
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Criar instância do Database
        db = Database(engine)
        
        # Tentar obter uma sessão para o banco de dados 'main'
        logger.info("Tentando obter sessão para 'main'...")
        session = db.get_session('main')
        logger.info("Sessão obtida com sucesso para 'main'")
        
        # Testar execução de uma consulta simples
        logger.info("Testando execução de consulta simples...")
        result = session.execute(text("SELECT 1 as test"))
        logger.info(f"Consulta executada com sucesso: {result.fetchone()}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao obter sessão para 'main': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_session_with_public():
    """Testa a obtenção de uma sessão com o banco de dados 'public'."""
    try:
        from pilot.common.sql_database import Database
        
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Criar instância do Database
        db = Database(engine)
        
        # Tentar obter uma sessão para o banco de dados 'public'
        logger.info("Tentando obter sessão para 'public'...")
        session = db.get_session('public')
        logger.info("Sessão obtida com sucesso para 'public'")
        
        # Testar execução de uma consulta simples
        logger.info("Testando execução de consulta simples...")
        result = session.execute(text("SELECT 1 as test"))
        logger.info(f"Consulta executada com sucesso: {result.fetchone()}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao obter sessão para 'public': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal."""
    logger.info("=== INICIANDO TESTES DE SESSÃO DE BANCO DE DADOS ===")
    
    # Teste 1: Listar bancos de dados/esquemas
    logger.info("\n=== TESTE 1: Listar bancos de dados/esquemas ===")
    success = test_database_list()
    logger.info(f"Teste 1 {'PASSOU' if success else 'FALHOU'}")
    
    # Teste 2: Obter sessão para 'main'
    logger.info("\n=== TESTE 2: Obter sessão para 'main' ===")
    success = test_session_with_main()
    logger.info(f"Teste 2 {'PASSOU' if success else 'FALHOU'}")
    
    # Teste 3: Obter sessão para 'public'
    logger.info("\n=== TESTE 3: Obter sessão para 'public' ===")
    success = test_session_with_public()
    logger.info(f"Teste 3 {'PASSOU' if success else 'FALHOU'}")
    
    logger.info("=== TESTES DE SESSÃO DE BANCO DE DADOS CONCLUÍDOS ===")

if __name__ == "__main__":
    main()
