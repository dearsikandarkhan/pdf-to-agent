# backend/services/llm_service.py
from typing import List, Dict, Any, Union, Optional
from abc import ABC, abstractmethod
import logging

from config import get_settings, LLMProvider
from models import ConversationMessage

logger = logging.getLogger(__name__)
settings = get_settings()

class BaseLLMService(ABC):
    """Abstract base class for LLM services"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate a response from a prompt"""
        pass

    @abstractmethod
    def generate_with_history(
        self,
        messages: List[ConversationMessage],
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate a response with conversation history"""
        pass


class OpenAILLMService(BaseLLMService):
    """OpenAI LLM service"""

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
            self.default_temperature = settings.OPENAI_TEMPERATURE
            self.default_max_tokens = settings.OPENAI_MAX_TOKENS
            logger.info(f"Initialized OpenAI LLM with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate response from prompt"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def generate_with_history(
        self,
        messages: List[ConversationMessage],
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate response with conversation history"""
        try:
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation with history failed: {e}")
            raise


class OllamaLLMService(BaseLLMService):
    """Ollama LLM service for local deployment"""

    def __init__(self):
        try:
            import requests
            self.base_url = settings.OLLAMA_BASE_URL
            self.model = settings.OLLAMA_MODEL
            self.default_temperature = settings.OLLAMA_TEMPERATURE
            self.num_ctx = settings.OLLAMA_NUM_CTX
            
            # Test connection
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
            
            logger.info(f"Initialized Ollama LLM with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate response from prompt"""
        import requests
        
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature or self.default_temperature,
                    "num_ctx": self.num_ctx
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    def generate_with_history(
        self,
        messages: List[ConversationMessage],
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate response with conversation history"""
        import requests
        
        try:
            # Format conversation history into a single prompt
            formatted_messages = []
            for msg in messages:
                role = msg.role.upper() if msg.role == "system" else msg.role.capitalize()
                formatted_messages.append(f"{role}: {msg.content}")
            
            full_prompt = "\n\n".join(formatted_messages)

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature or self.default_temperature,
                    "num_ctx": self.num_ctx
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama generation with history failed: {e}")
            raise


class LLMServiceFactory:
    """Factory for creating LLM services"""

    _instances = {}

    @classmethod
    def get_service(cls, provider: Union[str, LLMProvider]) -> BaseLLMService:
        """Get or create an LLM service instance"""
        
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        # Use singleton pattern
        if provider not in cls._instances:
            if provider == LLMProvider.OPENAI:
                cls._instances[provider] = OpenAILLMService()
            elif provider == LLMProvider.OLLAMA:
                cls._instances[provider] = OllamaLLMService()
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        return cls._instances[provider]

    @classmethod
    def get_default_service(cls) -> BaseLLMService:
        """Get the default LLM service from config"""
        return cls.get_service(settings.DEFAULT_LLM_PROVIDER)


# Convenience functions
def get_llm_service(provider: str = None) -> BaseLLMService:
    """Get LLM service by provider name"""
    if provider is None:
        return LLMServiceFactory.get_default_service()
    return LLMServiceFactory.get_service(provider)


def generate_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    provider: str = None,
    **kwargs
) -> str:
    """Generate a response using specified provider"""
    service = get_llm_service(provider)
    return service.generate(prompt, system_prompt, **kwargs)
