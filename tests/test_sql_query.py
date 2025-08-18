#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
from dotenv import load_dotenv
import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_sql_query")

# Carregar variáveis de ambiente
load_dotenv()

# Importar classes necessárias
from pilot.common.sql_database import Database
from pilot.configs.config import Config

def create_engine_from_config():
    """Cria um engine SQLAlchemy a partir das configurações."""
    db_type = os.getenv("DB_TYPE", "mysql").lower()
    
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
        connection_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}"
    
    logger.info(f"Criando engine com URI: {connection_uri}")
    return create_engine(connection_uri, echo=True)

def test_database_connection():
    """Testa a conexão com o banco de dados."""
    try:
        # Criar engine
        engine = create_engine_from_config()
        
        # Criar instância do Database
        db = Database(engine)
        
        # Verificar se o atributo _engine existe
        if hasattr(db, '_engine'):
            logger.info("Atributo _engine encontrado na classe Database")
            
            # Testar uma consulta simples
            try:
                session = db._db_sessions()
                result = session.execute(text("SELECT 1")).fetchone()
                logger.info(f"Consulta de teste bem-sucedida: {result}")
                
                # Listar tabelas do banco atual
                db_type = os.getenv("DB_TYPE", "mysql").lower()
                try:
                    if db_type in ["postgres", "postgresql"]:
                        query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    else:
                        query = text("SHOW TABLES")
                        
                    tables = session.execute(query).fetchall()
                    logger.info(f"Tabelas disponíveis: {[t[0] for t in tables]}")
                except Exception as e:
                    logger.error(f"Erro ao listar tabelas: {e}")
                    # Tentar fazer rollback da transação
                    session.rollback()
                
                return True
            except Exception as e:
                logger.error(f"Erro ao executar consulta: {e}")
                return False
        else:
            logger.error("Atributo _engine NÃO encontrado na classe Database")
            return False
    except Exception as e:
        logger.error(f"Erro ao testar conexão com o banco de dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_count_notas_fiscais():
    """Testa a consulta de contagem de notas fiscais."""
    try:
        # Criar engine
        engine = create_engine_from_config()
        
        # Criar instância do Database
        db = Database(engine)
        
        # Obter sessão
        session = db._db_sessions()
        
        # Consulta SQL para contar notas fiscais
        sql_query = """
        SELECT COUNT(*) as total_notas_fiscais 
        FROM ft_faturamento_cabecalho
        """
        
        # Executar consulta
        try:
            result = session.execute(text(sql_query)).fetchone()
            logger.info(f"Total de notas fiscais: {result[0]}")
            return True
        except Exception as e:
            logger.error(f"Erro ao executar consulta de contagem de notas fiscais: {e}")
            
            # Verificar se a tabela existe
            db_type = os.getenv("DB_TYPE", "mysql").lower()
            if db_type in ["postgres", "postgresql"]:
                check_query = text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ft_faturamento_cabecalho')")
            else:
                check_query = text("SHOW TABLES LIKE 'ft_faturamento_cabecalho'")
                
            check_result = session.execute(check_query).fetchone()
            logger.info(f"A tabela ft_faturamento_cabecalho existe? {check_result}")
            
            return False
    except Exception as e:
        logger.error(f"Erro ao testar contagem de notas fiscais: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== INICIANDO TESTES DE BANCO DE DADOS ===")
    
    logger.info("=== TESTE 1: CONEXÃO COM O BANCO DE DADOS ===")
    connection_success = test_database_connection()
    
    if connection_success:
        logger.info("=== TESTE 2: CONTAGEM DE NOTAS FISCAIS ===")
        count_success = test_count_notas_fiscais()
        
        if count_success:
            logger.info("=== TODOS OS TESTES CONCLUÍDOS COM SUCESSO ===")
        else:
            logger.error("=== TESTE DE CONTAGEM DE NOTAS FISCAIS FALHOU ===")
    else:
        logger.error("=== TESTE DE CONEXÃO FALHOU, PULANDO TESTE DE CONTAGEM ===")
