#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("check_table_schema")

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

def check_table_schema(table_name):
    """Verifica o esquema de uma tabela."""
    try:
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Usar o inspetor do SQLAlchemy para obter informações da tabela
        inspector = inspect(engine)
        
        # Verificar se a tabela existe
        if table_name not in inspector.get_table_names():
            logger.error(f"A tabela '{table_name}' não existe no banco de dados.")
            return False
        
        # Obter as colunas da tabela
        columns = inspector.get_columns(table_name)
        logger.info(f"Colunas da tabela '{table_name}':")
        for column in columns:
            logger.info(f"  - {column['name']}: {column['type']} (nullable: {column['nullable']})")
        
        # Obter as chaves primárias
        pk = inspector.get_pk_constraint(table_name)
        logger.info(f"Chave primária: {pk}")
        
        # Obter as chaves estrangeiras
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            logger.info(f"Chaves estrangeiras:")
            for fk in fks:
                logger.info(f"  - {fk}")
        else:
            logger.info("Não há chaves estrangeiras definidas.")
        
        # Obter os índices
        indexes = inspector.get_indexes(table_name)
        if indexes:
            logger.info(f"Índices:")
            for index in indexes:
                logger.info(f"  - {index}")
        else:
            logger.info("Não há índices definidos.")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar esquema da tabela: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal."""
    logger.info("=== VERIFICANDO ESQUEMA DAS TABELAS ===")
    
    # Verificar esquema das tabelas
    check_table_schema("ft_faturamento_cabecalho")
    check_table_schema("ft_faturamento_itens")
    
    logger.info("=== VERIFICAÇÃO DE ESQUEMA CONCLUÍDA ===")

if __name__ == "__main__":
    main()
