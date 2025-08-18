#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import subprocess
import sys
import time
from pathlib import Path

def executar_comando(comando, descricao=None):
    """Executa um comando e exibe o resultado."""
    if descricao:
        print(f"\n{descricao}...")
    
    try:
        resultado = subprocess.run(comando, shell=True, check=True, text=True, capture_output=True)
        print(f"Comando executado com sucesso: {comando}")
        if resultado.stdout:
            print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {comando}")
        print(f"Código de erro: {e.returncode}")
        print(f"Saída de erro: {e.stderr}")
        return False

def configurar_ambiente():
    """Configura o ambiente de execução."""
    print("\nConfigurando ambiente...")
    
    # Executa o script para configurar o arquivo .env
    if not executar_comando("python setup_env.py", "Configurando arquivo .env"):
        print("Falha ao configurar o arquivo .env.")
        return False
    
    # Instala as dependências necessárias
    if not executar_comando("pip install -r requirements.txt", "Instalando dependências"):
        print("Falha ao instalar dependências.")
        return False
    
    return True

def configurar_banco_dados():
    """Configura o banco de dados e importa os dados."""
    print("\nConfigurando banco de dados SQLite...")
    
    # Executa o script para configurar o banco de dados
    if not executar_comando("python setup_sqlite_db.py", "Configurando banco de dados SQLite"):
        print("Falha ao configurar o banco de dados.")
        return False
    
    return True

def iniciar_aplicacao():
    """Inicia a aplicação DB-GPT."""
    print("\nIniciando aplicação DB-GPT...")
    
    # Executa o script para iniciar a aplicação
    if not executar_comando("python run.py", "Iniciando aplicação"):
        print("Falha ao iniciar a aplicação.")
        return False
    
    return True

def main():
    """Função principal para inicializar o projeto."""
    print("=== Inicializando Projeto DB-GPT TELA Edition em Português com SQLite ===")
    
    # Configura o ambiente
    if not configurar_ambiente():
        return
    
    # Configura o banco de dados
    if not configurar_banco_dados():
        return
    
    # Inicia a aplicação
    print("\n=== Configuração concluída com sucesso! ===")
    print("Para iniciar a aplicação, execute: python run.py")
    print("A interface web estará disponível em: http://localhost:7860")
    
    resposta = input("\nDeseja iniciar a aplicação agora? (s/n): ")
    if resposta.lower() == 's':
        iniciar_aplicacao()

if __name__ == "__main__":
    main()
