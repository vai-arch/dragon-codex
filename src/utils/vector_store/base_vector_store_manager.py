from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseVectorStoreManager(ABC):
    @abstractmethod
    def get_collection(self, name: str):
        pass

    @abstractmethod
    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        pass

    @abstractmethod
    def reset(self) -> None:
        pass
