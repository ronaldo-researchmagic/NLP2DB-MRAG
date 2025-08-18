#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Any, Dict, Type
from pilot.configs.config import Config
from pilot.vector_store.connector import VectorStoreConnector
from pilot.llm_providers.tela_provider import TelaEmbeddingService

CFG = Config()

# Dicionário para registrar implementações de embedding
_EMBEDDING_REGISTRY: Dict[str, Type["SourceEmbedding"]] = {}

def register(name: str):
    """Decorator para registrar implementações de SourceEmbedding."""
    def decorator(cls):
        _EMBEDDING_REGISTRY[name] = cls
        return cls
    return decorator

class SourceEmbedding(ABC):
    """Base class for embedding data from a source into a vector store."""

    def __init__(self, file_path, vector_store_config):
        self.file_path = file_path
        self.vector_store_config = vector_store_config
        self.embedding_service = TelaEmbeddingService()
        # Pass the async embedding function to the connector
        self.vector_store_config["embeddings"] = self.embedding_service
        self.vector_client = VectorStoreConnector(
            CFG.VECTOR_STORE_TYPE, self.vector_store_config
        )

    @abstractmethod
    def read(self) -> List[Any]:
        """Read data from the source into document objects."""
        pass

    async def source_embedding(self):
        """Main pipeline for embedding the source data."""
        documents = self.read()
        # Data processing can be added here if needed
        await self.index_to_store(documents)

    async def index_to_store(self, documents: List[Any]):
        """Index documents into the vector store."""
        await self.vector_client.load_document(documents)
