from datetime import datetime

import chromadb
from chromadb import Settings

from src.utils.vector_store.base_vector_store_manager import BaseVectorStoreManager

print("BaseVectorStoreManager:", BaseVectorStoreManager)


class ChromaVectorStoreManager(BaseVectorStoreManager):
    def __init__(self, path, telemetry: bool, allow_reset: bool = False):
        self.client = chromadb.PersistentClient(
            path=str(path),
            settings=Settings(
                anonymized_telemetry=telemetry,
                allow_reset=allow_reset,
            ),
        )

    def get_collection(self, name: str):
        return self.client.get_collection(name=name)

    def get_or_create_collection(self, name: str, metadata=None):
        metadata = metadata or {}
        metadata.setdefault("created_at", datetime.now().isoformat())

        return self.client.get_or_create_collection(
            name=name,
            metadata=metadata,
        )

    def reset(self) -> None:
        self.client.reset()
