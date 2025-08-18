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
logger = logging.getLogger("fix_database_engine")

# Carregar variáveis de ambiente
load_dotenv()

def add_engine_property():
    """
    Adiciona uma propriedade 'engine' à classe Database para compatibilidade.
    Esta função modifica o arquivo pilot/common/sql_database.py para adicionar
    uma propriedade que retorna o atributo _engine.
    """
    try:
        file_path = "pilot/common/sql_database.py"
        
        # Ler o conteúdo atual do arquivo
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Verificar se a propriedade já existe
        if "@property\n    def engine(self):" in content:
            logger.info("A propriedade 'engine' já existe na classe Database.")
            return True
        
        # Encontrar a posição para inserir a propriedade (após a definição da classe Database)
        class_def_pos = content.find("class Database:")
        if class_def_pos == -1:
            logger.error("Não foi possível encontrar a definição da classe Database.")
            return False
        
        # Encontrar o final do método __init__
        init_end_pos = content.find("    def", class_def_pos + 1)
        if init_end_pos == -1:
            logger.error("Não foi possível encontrar o final do método __init__.")
            return False
        
        # Adicionar a propriedade engine
        property_code = """
    @property
    def engine(self):
        # Propriedade para acessar o engine do SQLAlchemy
        return self._engine
        
"""
        
        # Inserir a propriedade após o método __init__
        new_content = content[:init_end_pos] + property_code + content[init_end_pos:]
        
        # Salvar o arquivo modificado
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        logger.info("Propriedade 'engine' adicionada com sucesso à classe Database.")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao adicionar propriedade 'engine': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_database_with_property():
    """Testa se a propriedade engine funciona corretamente."""
    try:
        # Importar a classe Database após a modificação
        from pilot.common.sql_database import Database
        
        # Criar engine
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
        engine = create_engine(connection_uri)
        
        # Criar instância do Database
        db = Database(engine)
        
        # Testar a propriedade engine
        if hasattr(db, 'engine'):
            logger.info("Propriedade 'engine' encontrada na classe Database")
            logger.info(f"Engine URL: {db.engine.url}")
            return True
        else:
            logger.error("Propriedade 'engine' NÃO encontrada na classe Database")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao testar Database com propriedade: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal."""
    logger.info("=== INICIANDO CORREÇÃO DO ERRO 'Database' object has no attribute 'engine' ===")
    
    # Adicionar a propriedade engine
    if add_engine_property():
        # Testar a propriedade
        if test_database_with_property():
            logger.info("=== CORREÇÃO CONCLUÍDA COM SUCESSO ===")
        else:
            logger.error("=== TESTE DA PROPRIEDADE FALHOU ===")
    else:
        logger.error("=== FALHA AO ADICIONAR PROPRIEDADE ===")

if __name__ == "__main__":
    main()
