#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import shutil
from pathlib import Path

def configurar_env():
    """Configura o arquivo .env com as configurações em português e SQLite."""
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    # Verifica se o arquivo .env já existe
    if env_file.exists():
        print("Arquivo .env já existe. Fazendo backup...")
        backup_file = Path(".env.bak")
        shutil.copy(env_file, backup_file)
    
    # Cria o novo arquivo .env com configurações em português e SQLite
    with open(env_file, "w", encoding="utf-8") as f:
        f.write("""# Configuração da API TELA (substitua com suas credenciais)
TELA_API_KEY="your_tela_api_key_here"
TELA_API_BASE_URL="https://api.telaos.com/v1"
TELA_PROJECT="your_tela_project_id"
TELA_ORG="your_tela_organization_id"
TELA_MODEL="qwen-3-235b-a22b-instruct"
TELA_EMBEDDING_MODEL="nomic-ai/nomic-embed-text-v1.5"

# Configurações do Banco de Dados
DB_TYPE=sqlite
DB_PATH=data/faturamento.db
DB_NAME=db_faturamento

# Configurações da Aplicação
WEB_SERVER_PORT=7860
DEBUG_MODE=False
LANGUAGE=pt

# Configuração do Armazenamento Vetorial
VECTOR_STORE_TYPE=Chroma
KNOWLEDGE_CHUNK_SIZE=500
KNOWLEDGE_SEARCH_TOP_SIZE=5
""")
    
    print("Arquivo .env configurado com sucesso em português com suporte a SQLite!")

if __name__ == "__main__":
    configurar_env()
