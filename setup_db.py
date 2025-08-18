#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import csv
import pandas as pd
import logging
import sys
from dotenv import load_dotenv
from pathlib import Path
import getpass
from tqdm import tqdm

# Importações condicionais para diferentes bancos de dados
try:
    import pymysql
except ImportError:
    pymysql = None

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    psycopg2 = None

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("setup_db.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("setup_db")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_TYPE = os.getenv("DB_TYPE", "mysql").lower()
DB_HOST = os.getenv("LOCAL_DB_HOST", "localhost")
DB_PORT = int(os.getenv("LOCAL_DB_PORT", "3306" if DB_TYPE == "mysql" else "5432"))
DB_USER = os.getenv("LOCAL_DB_USER", "root" if DB_TYPE == "mysql" else "postgres")
DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "")
DB_NAME = os.getenv("LOCAL_DB_DATABASE", "db_faturamento")

# Caminhos dos arquivos CSV
CABECALHO_CSV = Path("data/ft_faturamento_cabecalho_202508130920.csv")
ITENS_CSV = Path("data/ft_faturamento_itens_202508130922.csv")

def criar_conexao():
    """Cria uma conexão com o banco de dados MySQL."""
    logger.info(f"Tentando conectar ao MySQL em {DB_HOST}:{DB_PORT} com usuário {DB_USER}")
    
    # Lista de senhas comuns para tentar
    senhas_comuns = [
        DB_PASSWORD,  # Primeiro tenta a senha do arquivo .env
        "",          # Senha vazia
        "root",       # Senha igual ao nome do usuário
        "password",   # Senha genérica
        "admin",      # Senha genérica
        "mysql"       # Senha igual ao nome do banco
    ]
    
    # Remove duplicatas e None/vazios (exceto a string vazia explícita)
    senhas_unicas = []
    for senha in senhas_comuns:
        if senha is not None and (senha or senha == "") and senha not in senhas_unicas:
            senhas_unicas.append(senha)
    
    # Tenta cada senha da lista
    last_error = None
    for senha in senhas_unicas:
        try:
            logger.info(f"Tentando conectar com senha {'<vazia>' if senha == '' else '******'} ({senhas_unicas.index(senha) + 1}/{len(senhas_unicas)})")
            # Tenta conectar sem especificar o banco de dados
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=senha,
                charset='utf8mb4'
            )
            logger.info(f"Conectado com sucesso ao servidor MySQL em {DB_HOST}:{DB_PORT}")
            return conn
        except Exception as e:
            last_error = e
            logger.warning(f"Falha na tentativa de conexão: {e}")
    
    # Se chegou aqui, todas as senhas falharam
    logger.error(f"Todas as tentativas de conexão falharam. Último erro: {last_error}")
    
    # Solicita a senha manualmente como último recurso
    try:
        logger.info("Solicitando senha manualmente")
        password = getpass.getpass("Todas as senhas comuns falharam. Digite a senha do MySQL para o usuário root: ")
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=password,
            charset='utf8mb4'
        )
        logger.info(f"Conectado com sucesso ao servidor MySQL em {DB_HOST}:{DB_PORT}")
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao MySQL com senha manual: {e}")
        raise

def criar_banco_dados(conn):
    """Cria o banco de dados se não existir."""
    logger.info(f"Tentando criar/selecionar banco de dados '{DB_NAME}'")
    try:
        with conn.cursor() as cursor:
            logger.debug("Executando comando CREATE DATABASE IF NOT EXISTS")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.debug(f"Executando comando USE {DB_NAME}")
            cursor.execute(f"USE {DB_NAME}")
            logger.info(f"Banco de dados '{DB_NAME}' criado/selecionado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar banco de dados: {e}")
        raise

def criar_tabelas(conn):
    """Cria as tabelas necessárias no banco de dados."""
    logger.info("Iniciando criação das tabelas no banco de dados")
    try:
        with conn.cursor() as cursor:
            # Tabela de cabeçalho de faturamento
            logger.info("Criando tabela ft_faturamento_cabecalho")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ft_faturamento_cabecalho (
                filial VARCHAR(10),
                nf_numero VARCHAR(20),
                nf_serie VARCHAR(5),
                cliente_cod VARCHAR(20),
                cliente_loja VARCHAR(10),
                cliente_nome VARCHAR(255),
                cliente_municipio VARCHAR(100),
                cliente_uf VARCHAR(2),
                cliente_tipo VARCHAR(5),
                dt_emissao_nf DATE,
                ano INT,
                mes_num INT,
                ano_trimestre VARCHAR(10),
                nf_valor_bruto DECIMAL(15,2),
                nf_valor_merc DECIMAL(15,2),
                nf_valor_faturar DECIMAL(15,2),
                nf_frete DECIMAL(15,2),
                nf_seguro DECIMAL(15,2),
                nf_despesas DECIMAL(15,2),
                nf_val_ipi DECIMAL(15,2),
                nf_val_icms DECIMAL(15,2),
                nf_val_pis DECIMAL(15,2),
                nf_val_cofins DECIMAL(15,2),
                nf_val_iss DECIMAL(15,2),
                PRIMARY KEY (filial, nf_numero, nf_serie)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            
            # Tabela de itens de faturamento
            logger.info("Criando tabela ft_faturamento_itens")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ft_faturamento_itens (
                filial VARCHAR(10),
                nf_numero VARCHAR(20),
                nf_serie VARCHAR(5),
                item VARCHAR(10),
                dt_emissao_nf DATE,
                ano INT,
                mes_num INT,
                ano_trimestre VARCHAR(10),
                cliente_cod VARCHAR(20),
                cliente_loja VARCHAR(10),
                produto_cod VARCHAR(20),
                produto_desc VARCHAR(255),
                produto_grupo VARCHAR(20),
                produto_um VARCHAR(10),
                produto_marca VARCHAR(100),
                cfop VARCHAR(10),
                tes VARCHAR(10),
                qtd DECIMAL(15,2),
                preco_tabela DECIMAL(15,2),
                valor_item_total DECIMAL(15,2),
                valor_item_desconto DECIMAL(15,2),
                valor_item_ipi DECIMAL(15,2),
                valor_item_icms DECIMAL(15,2),
                valor_item_iss DECIMAL(15,2),
                valor_item_pis DECIMAL(15,2),
                valor_item_cofins DECIMAL(15,2),
                custo_unitario1 DECIMAL(15,2),
                aliq_icms_item DECIMAL(15,2),
                aliq_ipi_item DECIMAL(15,2),
                preco_unit_efetivo DECIMAL(20,10),
                receita_bruta_item DECIMAL(15,4),
                receita_liquida_item DECIMAL(15,4),
                margem_bruta_item DECIMAL(15,4),
                perc_desconto_item DECIMAL(20,14),
                perc_impostos_item DECIMAL(20,10),
                PRIMARY KEY (filial, nf_numero, nf_serie, item),
                FOREIGN KEY (filial, nf_numero, nf_serie) REFERENCES ft_faturamento_cabecalho(filial, nf_numero, nf_serie)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
            
            conn.commit()
            logger.info("Tabelas criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        conn.rollback()
        raise

def importar_dados_cabecalho(conn):
    """Importa os dados do arquivo CSV para a tabela de cabeçalho."""
    try:
        logger.info(f"Iniciando importação de dados de {CABECALHO_CSV}")
        
        # Lê o arquivo CSV com pandas
        logger.info("Lendo arquivo CSV de cabeçalho")
        df = pd.read_csv(CABECALHO_CSV, sep=';', quotechar='"', encoding='utf-8')
        logger.info(f"Arquivo CSV lido com sucesso. Total de registros: {len(df)}")
        
        # Converte colunas de data
        logger.debug("Convertendo colunas de data")
        df['dt_emissao_nf'] = pd.to_datetime(df['dt_emissao_nf']).dt.strftime('%Y-%m-%d')
        
        # Substitui valores NaN por None para o MySQL
        logger.debug("Substituindo valores NaN por None")
        df = df.where(pd.notnull(df), None)
        
        # Insere os dados no banco
        with conn.cursor() as cursor:
            # Limpa a tabela antes de inserir
            logger.info("Truncando tabela ft_faturamento_cabecalho")
            cursor.execute("TRUNCATE TABLE ft_faturamento_cabecalho")
            
            # Prepara a query de inserção
            placeholders = ', '.join(['%s'] * len(df.columns))
            columns = ', '.join(df.columns)
            sql = f"INSERT INTO ft_faturamento_cabecalho ({columns}) VALUES ({placeholders})"
            
            # Insere os dados em lotes
            batch_size = 1000
            total_batches = (len(df) + batch_size - 1) // batch_size
            logger.info(f"Iniciando inserção de dados em {total_batches} lotes de {batch_size} registros")
            
            # Usar tqdm para mostrar o progresso
            with tqdm(total=len(df), desc="Importando cabeçalhos", unit="registros") as pbar:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size].values.tolist()
                    cursor.executemany(sql, batch)
                    conn.commit()
                    records_inserted = min(batch_size, len(df) - i)
                    pbar.update(records_inserted)
                    logger.debug(f"Lote {i//batch_size + 1}/{total_batches}: Inseridos {records_inserted} registros")
        
        logger.info("Importação de dados de cabeçalho concluída com sucesso")
    except Exception as e:
        logger.error(f"Erro ao importar dados de cabeçalho: {e}")
        conn.rollback()
        raise

def importar_dados_itens(conn):
    """Importa os dados do arquivo CSV para a tabela de itens."""
    try:
        logger.info(f"Iniciando importação de dados de {ITENS_CSV}")
        
        # Lê o arquivo CSV com pandas
        logger.info("Lendo arquivo CSV de itens")
        df = pd.read_csv(ITENS_CSV, sep=';', quotechar='"', encoding='utf-8')
        logger.info(f"Arquivo CSV lido com sucesso. Total de registros: {len(df)}")
        
        # Converte colunas de data
        logger.debug("Convertendo colunas de data")
        df['dt_emissao_nf'] = pd.to_datetime(df['dt_emissao_nf']).dt.strftime('%Y-%m-%d')
        
        # Substitui valores NaN por None para o MySQL
        logger.debug("Substituindo valores NaN por None")
        df = df.where(pd.notnull(df), None)
        
        # Insere os dados no banco
        with conn.cursor() as cursor:
            # Limpa a tabela antes de inserir
            logger.info("Truncando tabela ft_faturamento_itens")
            cursor.execute("TRUNCATE TABLE ft_faturamento_itens")
            
            # Prepara a query de inserção
            placeholders = ', '.join(['%s'] * len(df.columns))
            columns = ', '.join(df.columns)
            sql = f"INSERT INTO ft_faturamento_itens ({columns}) VALUES ({placeholders})"
            
            # Insere os dados em lotes
            batch_size = 1000
            total_batches = (len(df) + batch_size - 1) // batch_size
            logger.info(f"Iniciando inserção de dados em {total_batches} lotes de {batch_size} registros")
            
            # Usar tqdm para mostrar o progresso
            with tqdm(total=len(df), desc="Importando itens", unit="registros") as pbar:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size].values.tolist()
                    cursor.executemany(sql, batch)
                    conn.commit()
                    records_inserted = min(batch_size, len(df) - i)
                    pbar.update(records_inserted)
                    logger.debug(f"Lote {i//batch_size + 1}/{total_batches}: Inseridos {records_inserted} registros")
        
        logger.info("Importação de dados de itens concluída com sucesso")
    except Exception as e:
        logger.error(f"Erro ao importar dados de itens: {e}")
        conn.rollback()
        raise

def main():
    """Função principal para configurar o banco de dados e importar os dados."""
    logger.info("=== INICIANDO CONFIGURAÇÃO DO BANCO DE DADOS ===")
    
    # Verifica se os arquivos CSV existem
    logger.info("Verificando existência dos arquivos CSV")
    if not CABECALHO_CSV.exists() or not ITENS_CSV.exists():
        logger.error(f"Arquivos CSV não encontrados. Verifique se os arquivos estão em {CABECALHO_CSV} e {ITENS_CSV}")
        return
    logger.info("Arquivos CSV encontrados")
    
    try:
        # Cria conexão com o banco de dados
        logger.info("Etapa 1/5: Estabelecendo conexão com o banco de dados")
        conn = criar_conexao()
        
        # Cria o banco de dados
        logger.info("Etapa 2/5: Criando/selecionando banco de dados")
        criar_banco_dados(conn)
        
        # Cria as tabelas
        logger.info("Etapa 3/5: Criando tabelas")
        criar_tabelas(conn)
        
        # Importa os dados
        logger.info("Etapa 4/5: Importando dados de cabeçalho")
        importar_dados_cabecalho(conn)
        
        logger.info("Etapa 5/5: Importando dados de itens")
        importar_dados_itens(conn)
        
        logger.info("=== CONFIGURAÇÃO DO BANCO DE DADOS CONCLUÍDA COM SUCESSO! ===")
    except Exception as e:
        logger.error(f"Erro durante a configuração do banco de dados: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Conexão com o banco de dados fechada")

if __name__ == "__main__":
    main()
