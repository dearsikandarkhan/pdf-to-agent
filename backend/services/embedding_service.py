# backend/services/embedding_service.py
from typing import List, Union
import numpy as np
from abc import ABC, abstractmethod
import logging

from config import get_settings, EmbeddingProvider

logger = logging.getLogger(__name__)
settings = get_settings()

class BaseEmbeddingService(ABC):
    """Abstract base class for embedding services"""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings"""
        pass


class OpenAIEmbeddingService(BaseEmbeddingService):
    """OpenAI embeddings using official API"""

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_EMBEDDING_MODEL
            self._dimension = 1536 if "3-small" in self.model else 3072
            logger.info(f"Initialized OpenAI embeddings with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        try:
            # OpenAI API supports batch embedding
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI query embedding failed: {e}")
            raise

    def get_dimension(self) -> int:
        return self._dimension


class OllamaEmbeddingService(BaseEmbeddingService):
    """Ollama embeddings for local/private deployment"""

    def __init__(self):
        try:
            import requests
            self.base_url = settings.OLLAMA_BASE_URL
            self.model = settings.OLLAMA_EMBEDDING_MODEL
            self._dimension = 768  # nomic-embed-text dimension
            
            # Test connection
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
            
            logger.info(f"Initialized Ollama embeddings with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        import requests
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
            except Exception as e:
                logger.error(f"Ollama embedding failed for text: {e}")
                raise
        
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        import requests
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Ollama query embedding failed: {e}")
            raise

    def get_dimension(self) -> int:
        return self._dimension


class EmbeddingServiceFactory:
    """Factory for creating embedding services"""

    _instances = {}

    @classmethod
    def get_service(cls, provider: Union[str, EmbeddingProvider]) -> BaseEmbeddingService:
        """Get or create an embedding service instance"""
        
        if isinstance(provider, str):
            provider = EmbeddingProvider(provider.lower())

        # Use singleton pattern
        if provider not in cls._instances:
            if provider == EmbeddingProvider.OPENAI:
                cls._instances[provider] = OpenAIEmbeddingService()
            elif provider == EmbeddingProvider.OLLAMA:
                cls._instances[provider] = OllamaEmbeddingService()
            else:
                raise ValueError(f"Unsupported embedding provider: {provider}")

        return cls._instances[provider]

    @classmethod
    def get_default_service(cls) -> BaseEmbeddingService:
        """Get the default embedding service from config"""
        return cls.get_service(settings.DEFAULT_EMBEDDING_PROVIDER)


# Convenience functions
def get_embedding_service(provider: str = None) -> BaseEmbeddingService:
    """Get embedding service by provider name"""
    if provider is None:
        return EmbeddingServiceFactory.get_default_service()
    return EmbeddingServiceFactory.get_service(provider)


def embed_texts(texts: List[str], provider: str = None) -> List[List[float]]:
    """Embed multiple texts"""
    service = get_embedding_service(provider)
    return service.embed_documents(texts)


def embed_query(text: str, provider: str = None) -> List[float]:
    """Embed a single query"""
    service = get_embedding_service(provider)
    return service.embed_query(text)
