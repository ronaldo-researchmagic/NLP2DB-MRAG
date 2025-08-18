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
logger = logging.getLogger("test_model_sql_query")

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

def test_query_execution(query, description=""):
    """Executa uma consulta SQL e exibe o resultado."""
    try:
        from pilot.common.sql_database import Database
        
        engine = setup_database_connection()
        if not engine:
            logger.error("Não foi possível configurar a conexão com o banco de dados.")
            return False
        
        # Criar instância do Database
        db = Database(engine)
        
        # Executar a consulta
        logger.info(f"Executando consulta: {description}")
        logger.info(f"SQL: {query}")
        
        result = db.run_sql(query)
        
        if result:
            # Limitar a quantidade de linhas exibidas se for muito grande
            if len(result) > 10:
                logger.info(f"Resultado (primeiras 10 linhas de {len(result)}): {result[:10]}")
            else:
                logger.info(f"Resultado: {result}")
        else:
            logger.info("Consulta executada com sucesso, sem resultados para exibir.")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao executar consulta: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Função principal."""
    logger.info("=== INICIANDO TESTES DE CONSULTAS SQL ===")
    
    # Teste 1: Contar o número total de notas fiscais
    query1 = """
    SELECT COUNT(*) as total_notas_fiscais 
    FROM public.ft_faturamento_cabecalho
    """
    test_query_execution(query1, "Contagem total de notas fiscais")
    
    # Teste 2: Listar as 5 notas fiscais mais recentes
    query2 = """
    SELECT nf_numero, nf_serie, cliente_nome, dt_emissao_nf, nf_valor_bruto 
    FROM public.ft_faturamento_cabecalho
    ORDER BY dt_emissao_nf DESC
    LIMIT 5
    """
    test_query_execution(query2, "5 notas fiscais mais recentes")
    
    # Teste 3: Calcular o valor total de vendas
    query3 = """
    SELECT SUM(nf_valor_bruto) as valor_total_vendas
    FROM public.ft_faturamento_cabecalho
    """
    test_query_execution(query3, "Valor total de vendas")
    
    # Teste 4: Contar o número de itens por nota fiscal
    query4 = """
    SELECT cabecalho.nf_numero, cabecalho.nf_serie, COUNT(itens.item) as total_itens
    FROM public.ft_faturamento_cabecalho cabecalho
    JOIN public.ft_faturamento_itens itens ON 
        cabecalho.nf_numero = itens.nf_numero AND 
        cabecalho.nf_serie = itens.nf_serie AND
        cabecalho.filial = itens.filial
    GROUP BY cabecalho.nf_numero, cabecalho.nf_serie
    ORDER BY total_itens DESC
    LIMIT 5
    """
    test_query_execution(query4, "Número de itens por nota fiscal (top 5)")
    
    # Teste 5: Receita líquida total por cliente (nome+loja)
    query5 = """
    SELECT
        c.cliente_nome,
        c.cliente_loja,
        SUM(i.receita_liquida_item) AS receita_liquida_total
    FROM public.ft_faturamento_itens i
    JOIN public.ft_faturamento_cabecalho c
    ON (c.filial, c.nf_numero, c.nf_serie) = (i.filial, i.nf_numero, i.nf_serie)
    GROUP BY c.cliente_nome, c.cliente_loja
    ORDER BY receita_liquida_total DESC
    LIMIT 10
    """
    test_query_execution(query5, "Receita líquida total por cliente (top 10)")
    
    logger.info("=== TESTES DE CONSULTAS SQL CONCLUÍDOS ===")

if __name__ == "__main__":
    main()
