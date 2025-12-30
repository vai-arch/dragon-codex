from enum import Enum

from src.utils.vector_store.base_vector_store_manager import BaseVectorStoreManager
from src.utils.vector_store.chroma_vector_store_manager import ChromaVectorStoreManager


class VectorStoreType(str, Enum):
    CHROMA = "chroma"
    # FAISS = "faiss"
    # PINECONE = "pinecone"


class VectorStoreFactory:
    @staticmethod
    def create(store_type: VectorStoreType, **kwargs) -> BaseVectorStoreManager:
        if store_type == VectorStoreType.CHROMA:
            return ChromaVectorStoreManager(**kwargs)

        raise ValueError(f"Unsupported vector store: {store_type}")
