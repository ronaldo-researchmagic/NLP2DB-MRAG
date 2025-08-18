# Importações originais substituídas por mock para evitar dependências problemáticas
# from pilot.vector_store.chroma_store import ChromaStore
# from pilot.vector_store.milvus_store import MilvusStore
# from pilot.vector_store.weaviate_store import WeaviateStore

from pilot.vector_store.mock_store import MockVectorStore

connector = {"Chroma": MockVectorStore, "Milvus": MockVectorStore, "Weaviate": MockVectorStore}

class VectorStoreConnector:
    """Async-aware vector store connector."""

    def __init__(self, vector_store_type, ctx: {}) -> None:
        self.connector_class = connector[vector_store_type]
        self.client = self.connector_class(ctx)

    async def load_document(self, docs):
        await self.client.load_document(docs)

    async def similar_search(self, text, topk):
        return await self.client.similar_search(text, topk)

    async def vector_name_exists(self):
        return await self.client.vector_name_exists()
