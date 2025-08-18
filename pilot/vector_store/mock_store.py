"""
Mock implementation of vector stores for development without dependencies.
"""

class MockVectorStore:
    """A mock implementation of vector store that doesn't require external dependencies."""
    
    def __init__(self, ctx: dict) -> None:
        self.ctx = ctx
        self.documents = []
        print(f"Initialized MockVectorStore with context: {ctx}")
    
    async def load_document(self, docs):
        """Mock document loading."""
        self.documents.extend(docs)
        print(f"Mock loaded {len(docs)} documents")
        return True
    
    async def similar_search(self, text, topk):
        """Mock similar search that returns empty results."""
        print(f"Mock similar search for '{text}' with topk={topk}")
        return []
    
    async def vector_name_exists(self):
        """Mock check if vector name exists."""
        return True
