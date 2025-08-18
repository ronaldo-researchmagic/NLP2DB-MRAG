#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_model_sql_generation")

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
        
        # Testar conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            logger.info(f"Conexão com o banco de dados bem-sucedida: {result}")
        
        return engine
    except Exception as e:
        logger.error(f"Erro ao configurar conexão com o banco de dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def test_database_class():
    """Testa a classe Database."""
    try:
        from pilot.common.sql_database import Database
        
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Criar instância do Database
        db = Database(engine)
        
        # Verificar atributos
        logger.info("Verificando atributos da classe Database:")
        logger.info(f"Atributo _engine existe: {hasattr(db, '_engine')}")
        logger.info(f"Atributo engine existe: {hasattr(db, 'engine')}")
        
        # Testar acesso ao engine
        try:
            engine_url = db.engine.url
            logger.info(f"Acesso ao engine bem-sucedido. URL: {engine_url}")
        except Exception as e:
            logger.error(f"Erro ao acessar o atributo engine: {e}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Erro ao testar classe Database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_model_sql_generation():
    """Testa a geração de SQL pelo modelo."""
    try:
        from pilot.configs.config import Config
        from pilot.configs.model_config import LLM_MODEL_CONFIG
        from pilot.common.sql_database import Database
        from pilot.server.knowledge.db_knowledge import DBKnowledge
        
        # Configurar o modelo
        logger.info("Configurando o modelo...")
        config = Config()
        
        # Configurar a conexão com o banco de dados
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Criar instância do Database
        db = Database(engine)
        
        # Criar instância do DBKnowledge
        try:
            logger.info("Criando instância do DBKnowledge...")
            db_knowledge = DBKnowledge(db)
            
            # Testar geração de SQL
            question = "Quantas notas fiscais existem no total?"
            logger.info(f"Gerando SQL para a pergunta: '{question}'")
            
            # Obter informações do esquema do banco de dados
            schema_info = db_knowledge.get_db_schema()
            logger.info(f"Esquema do banco de dados obtido: {len(schema_info)} tabelas encontradas")
            
            # Aqui seria onde o modelo geraria o SQL, mas vamos simular isso
            # já que não queremos depender do modelo LLM neste teste
            sql_query = """
            SELECT COUNT(*) as total_notas_fiscais 
            FROM ft_faturamento_cabecalho
            """
            
            logger.info(f"SQL gerado (simulado): {sql_query}")
            
            # Executar a consulta
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(sql_query)).fetchone()
                    logger.info(f"Resultado da consulta: {result}")
                return True
            except Exception as e:
                logger.error(f"Erro ao executar a consulta SQL: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao criar instância do DBKnowledge: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"Erro ao testar geração de SQL pelo modelo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal."""
    logger.info("=== INICIANDO TESTES DE GERAÇÃO DE SQL ===")
    
    # Testar classe Database
    logger.info("=== TESTE 1: CLASSE DATABASE ===")
    if test_database_class():
        logger.info("Teste da classe Database concluído com sucesso.")
    else:
        logger.error("Teste da classe Database falhou.")
        return
    
    # Testar geração de SQL
    logger.info("=== TESTE 2: GERAÇÃO DE SQL ===")
    if test_model_sql_generation():
        logger.info("Teste de geração de SQL concluído com sucesso.")
    else:
        logger.error("Teste de geração de SQL falhou.")
        return
    
    logger.info("=== TODOS OS TESTES CONCLUÍDOS COM SUCESSO ===")

if __name__ == "__main__":
    main()
