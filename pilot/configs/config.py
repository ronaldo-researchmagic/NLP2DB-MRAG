#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import List, Any
from pilot.singleton import Singleton
from pilot.common.sql_database import Database

# Classe simples para substituir a dependência do AutoGPTPluginTemplate
class PluginTemplate:
    """Classe base simples para plugins"""
    
    def __init__(self, name: str = ""):
        self.name = name
        
    def can_handle_post_prompt(self) -> bool:
        """Este método determina se o plugin pode lidar com o prompt após o processamento"""
        return False
        
    def can_handle_pre_prompt(self) -> bool:
        """Este método determina se o plugin pode lidar com o prompt antes do processamento"""
        return False
        
    def post_prompt(self, prompt: str) -> str:
        """Este método é chamado após o processamento do prompt"""
        return prompt
        
    def pre_prompt(self, prompt: str) -> str:
        """Este método é chamado antes do processamento do prompt"""
        return prompt

class Config(metaclass=Singleton):
    """Configuration class to store the state of bools for different scripts access"""

    def __init__(self) -> None:
        """Initialize the Config class"""
        # --- TELA API Configuration ---
        self.TELA_API_KEY = os.getenv("TELA_API_KEY")
        self.TELA_API_BASE_URL = os.getenv("TELA_API_BASE_URL", "https://api.telaos.com/v1")
        self.TELA_PROJECT = os.getenv("TELA_PROJECT")
        self.TELA_ORG = os.getenv("TELA_ORG")
        self.TELA_MODEL = os.getenv("TELA_MODEL", "qwen-3-235b-a22b-instruct")
        self.TELA_EMBEDDING_MODEL = os.getenv("TELA_EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5")

        # --- Application Settings ---
        self.LANGUAGE = os.getenv("LANGUAGE", "en")
        self.WEB_SERVER_PORT = int(os.getenv("WEB_SERVER_PORT", 7860))
        self.debug_mode = os.getenv("DEBUG_MODE", "False").lower() == 'true'
        self.temperature = float(os.getenv("TEMPERATURE", 0.15))

        # --- Database Connection ---
        self.DB_TYPE = os.getenv("DB_TYPE", "sqlite")
        self.DB_PATH = os.getenv("DB_PATH", "data/faturamento.db")
        self.DB_NAME = os.getenv("DB_NAME", "db_faturamento")
        
        try:
            if self.DB_TYPE.lower() == "sqlite":
                self.local_db = Database.from_uri(
                    f"sqlite:///{self.DB_PATH}",
                    engine_args={"echo": self.debug_mode},
                )
            elif self.DB_TYPE.lower() == "postgres" or self.DB_TYPE.lower() == "postgresql":
                self.LOCAL_DB_HOST = os.getenv("LOCAL_DB_HOST", "localhost")
                self.LOCAL_DB_PORT = int(os.getenv("LOCAL_DB_PORT", 5432))
                self.LOCAL_DB_USER = os.getenv("LOCAL_DB_USER", "postgres")
                self.LOCAL_DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "")
                self.LOCAL_DB_DATABASE = os.getenv("LOCAL_DB_DATABASE", "postgres")
                
                self.local_db = Database.from_uri(
                    f"postgresql://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}/{self.LOCAL_DB_DATABASE}",
                    engine_args={"pool_size": 10, "pool_recycle": 3600, "echo": self.debug_mode},
                )
            else:  # Fallback to MySQL if specified
                self.LOCAL_DB_HOST = os.getenv("LOCAL_DB_HOST", "localhost")
                self.LOCAL_DB_PORT = int(os.getenv("LOCAL_DB_PORT", 3306))
                self.LOCAL_DB_USER = os.getenv("LOCAL_DB_USER", "root")
                self.LOCAL_DB_PASSWORD = os.getenv("LOCAL_DB_PASSWORD", "rootpass123")
                
                self.local_db = Database.from_uri(
                    f"mysql+pymysql://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}",
                    engine_args={"pool_size": 10, "pool_recycle": 3600, "echo": self.debug_mode},
                )
        except Exception as e:
            print(f"Warning: Could not connect to database. DB-related features will be unavailable. Error: {e}")
            self.local_db = None

        # --- Vector Store & Embeddings ---
        self.VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "Chroma")
        self.EMBEDDING_MODEL = self.TELA_EMBEDDING_MODEL # Use TELA model for embeddings
        self.KNOWLEDGE_CHUNK_SIZE = int(os.getenv("KNOWLEDGE_CHUNK_SIZE", 200))
        self.KNOWLEDGE_SEARCH_TOP_SIZE = int(os.getenv("KNOWLEDGE_SEARCH_TOP_SIZE", 10))

        # --- Original Project Settings (Kept for compatibility) ---
        self.prompt_templates = {}
        self.plugins: List[PluginTemplate] = []
        self.command_registry = []
        self.message_dir = os.getenv("MESSAGE_HISTORY_DIR", "pilot/message_history")
        
        os.makedirs(self.message_dir, exist_ok=True)

    def set_plugins(self, value: list) -> None:
        self.plugins = value
