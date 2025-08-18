#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import csv
import sqlite3
import pandas as pd
from pathlib import Path
import time

# Configurações do banco de dados
DB_FILE = "data/faturamento.db"

# Caminhos dos arquivos CSV
CABECALHO_CSV = Path("data/ft_faturamento_cabecalho_202508130920.csv")
ITENS_CSV = Path("data/ft_faturamento_itens_202508130922.csv")

def criar_conexao():
    """Cria uma conexão com o banco de dados SQLite."""
    try:
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        
        # Cria a conexão
        conn = sqlite3.connect(DB_FILE)
        print(f"Conectado ao banco de dados SQLite em {DB_FILE}")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao SQLite: {e}")
        raise

def criar_tabelas(conn):
    """Cria as tabelas necessárias no banco de dados."""
    try:
        cursor = conn.cursor()
        
        # Tabela de cabeçalho de faturamento
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ft_faturamento_cabecalho (
            filial TEXT,
            nf_numero TEXT,
            nf_serie TEXT,
            cliente_cod TEXT,
            cliente_loja TEXT,
            cliente_nome TEXT,
            cliente_municipio TEXT,
            cliente_uf TEXT,
            cliente_tipo TEXT,
            dt_emissao_nf TEXT,
            ano INTEGER,
            mes_num INTEGER,
            ano_trimestre TEXT,
            nf_valor_bruto REAL,
            nf_valor_merc REAL,
            nf_valor_faturar REAL,
            nf_frete REAL,
            nf_seguro REAL,
            nf_despesas REAL,
            nf_val_ipi REAL,
            nf_val_icms REAL,
            nf_val_pis REAL,
            nf_val_cofins REAL,
            nf_val_iss REAL,
            PRIMARY KEY (filial, nf_numero, nf_serie)
        );
        """)
        
        # Tabela de itens de faturamento
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ft_faturamento_itens (
            filial TEXT,
            nf_numero TEXT,
            nf_serie TEXT,
            item TEXT,
            dt_emissao_nf TEXT,
            ano INTEGER,
            mes_num INTEGER,
            ano_trimestre TEXT,
            cliente_cod TEXT,
            cliente_loja TEXT,
            produto_cod TEXT,
            produto_desc TEXT,
            produto_grupo TEXT,
            produto_um TEXT,
            produto_marca TEXT,
            cfop TEXT,
            tes TEXT,
            qtd REAL,
            preco_tabela REAL,
            valor_item_total REAL,
            valor_item_desconto REAL,
            valor_item_ipi REAL,
            valor_item_icms REAL,
            valor_item_iss REAL,
            valor_item_pis REAL,
            valor_item_cofins REAL,
            custo_unitario1 REAL,
            aliq_icms_item REAL,
            aliq_ipi_item REAL,
            preco_unit_efetivo REAL,
            receita_bruta_item REAL,
            receita_liquida_item REAL,
            margem_bruta_item REAL,
            perc_desconto_item REAL,
            perc_impostos_item REAL,
            PRIMARY KEY (filial, nf_numero, nf_serie, item),
            FOREIGN KEY (filial, nf_numero, nf_serie) REFERENCES ft_faturamento_cabecalho(filial, nf_numero, nf_serie)
        );
        """)
        
        conn.commit()
        print("Tabelas criadas com sucesso")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()
        raise

def importar_dados_cabecalho(conn):
    """Importa os dados do arquivo CSV para a tabela de cabeçalho."""
    try:
        print(f"Importando dados de {CABECALHO_CSV}...")
        
        # Lê o arquivo CSV com pandas
        df = pd.read_csv(CABECALHO_CSV, sep=';', quotechar='"', encoding='utf-8')
        
        # Converte colunas de data
        df['dt_emissao_nf'] = pd.to_datetime(df['dt_emissao_nf']).dt.strftime('%Y-%m-%d')
        
        # Substitui valores NaN por None para o SQLite
        df = df.where(pd.notnull(df), None)
        
        # Limpa a tabela antes de inserir
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ft_faturamento_cabecalho")
        
        # Insere os dados no banco
        start_time = time.time()
        df.to_sql('ft_faturamento_cabecalho', conn, if_exists='append', index=False)
        end_time = time.time()
        
        print(f"Importação de dados de cabeçalho concluída com sucesso em {end_time - start_time:.2f} segundos")
        print(f"Total de registros importados: {len(df)}")
    except Exception as e:
        print(f"Erro ao importar dados de cabeçalho: {e}")
        conn.rollback()
        raise

def importar_dados_itens(conn):
    """Importa os dados do arquivo CSV para a tabela de itens."""
    try:
        print(f"Importando dados de {ITENS_CSV}...")
        
        # Lê o arquivo CSV com pandas
        df = pd.read_csv(ITENS_CSV, sep=';', quotechar='"', encoding='utf-8')
        
        # Converte colunas de data
        df['dt_emissao_nf'] = pd.to_datetime(df['dt_emissao_nf']).dt.strftime('%Y-%m-%d')
        
        # Substitui valores NaN por None para o SQLite
        df = df.where(pd.notnull(df), None)
        
        # Limpa a tabela antes de inserir
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ft_faturamento_itens")
        
        # Insere os dados no banco em lotes para evitar problemas de memória
        batch_size = 10000
        total_rows = len(df)
        start_time = time.time()
        
        for i in range(0, total_rows, batch_size):
            end_idx = min(i + batch_size, total_rows)
            print(f"Importando lote {i//batch_size + 1}/{(total_rows + batch_size - 1)//batch_size}: registros {i} a {end_idx}")
            batch_df = df.iloc[i:end_idx]
            batch_df.to_sql('ft_faturamento_itens', conn, if_exists='append', index=False)
            conn.commit()
            print(f"Lote {i//batch_size + 1} importado com sucesso")
        
        end_time = time.time()
        print(f"Importação de dados de itens concluída com sucesso em {end_time - start_time:.2f} segundos")
        print(f"Total de registros importados: {total_rows}")
    except Exception as e:
        print(f"Erro ao importar dados de itens: {e}")
        conn.rollback()
        raise

def main():
    """Função principal para configurar o banco de dados e importar os dados."""
    print("Iniciando configuração do banco de dados SQLite...")
    
    # Verifica se os arquivos CSV existem
    if not CABECALHO_CSV.exists() or not ITENS_CSV.exists():
        print(f"Erro: Arquivos CSV não encontrados. Verifique se os arquivos estão em {CABECALHO_CSV} e {ITENS_CSV}")
        return
    
    try:
        # Cria conexão com o banco de dados
        conn = criar_conexao()
        
        # Cria as tabelas
        criar_tabelas(conn)
        
        # Importa os dados
        importar_dados_cabecalho(conn)
        importar_dados_itens(conn)
        
        print("Configuração do banco de dados concluída com sucesso!")
    except Exception as e:
        print(f"Erro durante a configuração do banco de dados: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Conexão com o banco de dados fechada")

if __name__ == "__main__":
    main()
