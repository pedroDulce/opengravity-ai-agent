# core/llm_client.py
"""
Factory para clientes LLM con soporte para múltiples proveedores.
"""

import os
import logging
from typing import Optional, Literal
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Tipos para el selector de proveedor
LLMProvider = Literal["groq", "openrouter", "openai", "anthropic"]

class LLMClient:
    """
    Factory que retorna el cliente LLM configurado.
    
    Uso:
        client = LLMClient()  # Usa proveedor por defecto de .env
        client = LLMClient(provider="openrouter")  # Fuerza OpenRouter
        response = client.generate("prompt")
    """
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        """
        Inicializa el cliente LLM.
        
        Args:
            provider: Proveedor a usar. Si None, usa LLM_PROVIDER de .env
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq").lower()
        
        logger.info(f"🔍 Inicializando LLMClient con proveedor: {self.provider}")
        
        if self.provider == "groq":
            self._client = self._init_groq()
        elif self.provider == "openrouter":
            self._client = self._init_openrouter()
        elif self.provider == "openai":
            self._client = self._init_openai()  # Implementar si se necesita
        elif self.provider == "anthropic":
            self._client = self._init_anthropic()  # Implementar si se necesita
        else:
            raise ValueError(f"Proveedor LLM no soportado: {self.provider}")
        
        logger.info(f"✅ LLMClient listo: {self.provider}")
    
    def _init_groq(self):
        """Inicializa el cliente Groq existente."""
        try:
            from core.groq_client import GroqClient  # Tu implementación actual
            return GroqClient()
        except ImportError:
            # Fallback: implementación inline si no existe groq_client.py
            from groq import Groq as GroqSDK
            api_key = os.getenv("GROQ_API_KEY")
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            
            class _GroqClient:
                def __init__(self):
                    self.client = GroqSDK(api_key=api_key)
                    self.model = model
                
                def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
                    system = system_prompt or "Eres un asistente útil."
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000
                    )
                    return response.choices[0].message.content.strip()
            
            return _GroqClient()
    
    def _init_openrouter(self):
        """Inicializa el cliente OpenRouter."""
        from core.openrouter_client import OpenRouterClient
        return OpenRouterClient(
            model=os.getenv("OPENROUTER_MODEL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
        )
    
    def _init_openai(self):
        """Placeholder para OpenAI (implementar si se necesita)."""
        raise NotImplementedError("Proveedor OpenAI no implementado aún")
    
    def _init_anthropic(self):
        """Placeholder para Anthropic (implementar si se necesita)."""
        raise NotImplementedError("Proveedor Anthropic no implementado aún")
    
    # Delegar métodos al cliente interno
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Genera una respuesta para el prompt dado."""
        return self._client.generate(prompt, system_prompt)
    
    async def generate_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Versión asíncrona de generate()."""
        if hasattr(self._client, 'generate_async'):
            return await self._client.generate_async(prompt, system_prompt)
        # Fallback: ejecutar sync en thread
        import asyncio
        return await asyncio.to_thread(self._client.generate, prompt, system_prompt)
    
    def get_model_info(self) -> dict:
        """Retorna información del modelo configurado."""
        info = self._client.get_model_info() if hasattr(self._client, 'get_model_info') else {}
        info["provider"] = self.provider
        return info