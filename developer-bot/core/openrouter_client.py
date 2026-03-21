# core/openrouter_client.py
"""
Cliente para OpenRouter API con soporte para modelos modernos.
Compatible con la interfaz de LLMClient del bot OpenGravity.
"""

import os
import httpx
import logging
from dotenv import load_dotenv
from typing import Optional

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """
    Cliente asíncrono para OpenRouter API.
    
    Soporta modelos como:
    - meta-llama/llama-3.2-90b-vision-instruct:free
    - google/gemini-pro-1.5
    - anthropic/claude-3.5-sonnet
    - y muchos más: https://openrouter.ai/models
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: float = 120.0
    ):
        """
        Inicializa el cliente de OpenRouter.
        
        Args:
            model: Modelo a usar (default: OPENROUTER_MODEL env var)
            api_key: API key (default: OPENROUTER_API_KEY env var)
            temperature: Creatividad de la respuesta (0.0 a 2.0)
            max_tokens: Límite de tokens en la respuesta
            timeout: Timeout en segundos para la petición HTTP
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada en .env")
        
        self.model = model or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-90b-vision-instruct:free")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Configuración del sitio para OpenRouter (opcional pero recomendado)
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "https://k8s-bot.local")
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "OpenGravity Bot")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info(f"✅ OpenRouterClient inicializado: {self.model}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Genera una respuesta de la IA para un prompt dado.
        
        Método SÍNCRONO para compatibilidad con asyncio.to_thread().
        
        Args:
            prompt: El mensaje del usuario o prompt de generación
            system_prompt: Instrucciones del sistema (opcional)
            
        Returns:
            str: La respuesta generada por la IA
        """
        import asyncio
        
        # Ejecutar la llamada async en un thread separado
        return asyncio.run(
            self._generate_async(prompt, system_prompt)
        )
    
    async def generate_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Versión asíncrona de generate().
        
        Args:
            prompt: El mensaje del usuario o prompt de generación
            system_prompt: Instrucciones del sistema (opcional)
            
        Returns:
            str: La respuesta generada por la IA
        """
        return await self._generate_async(prompt, system_prompt)
    
    async def _generate_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Implementación interna asíncrona."""
        
        # System prompt por defecto para generación de código Angular/ATOM
        default_system = """Eres un arquitecto de software experto en Angular, Spring Boot y la librería corporativa ATOM.

REGLAS OBLIGATORIAS:
1. Genera código TypeScript/Java compilable y bien estructurado
2. Usa patrones ATOM: componentes standalone, OnPush, inject(), signals
3. Para Angular 19+: usa @include mat.theme() API M3, NO define-light-theme
4. Incluye imports explícitos de Angular Material cuando uses componentes UI
5. Responde SOLO con código en el formato solicitado, sin explicaciones adicionales

CONTEXTO TÉCNICO:
- Angular 19+, TypeScript 5+, Node 22+
- Spring Boot 3.x, Java 17+
- Librería ATOM: componentes lib-*, CustomPage<T>, ArqExternalMicroAdapter
"""
        
        system_content = system_prompt or default_system
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            # Opciones adicionales de OpenRouter
            "include_reasoning": False,
        }
        
        try:
            # Cliente HTTP con timeout configurado y SSL flexible para VDI
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.timeout,
                    write=10.0,
                    pool=10.0
                ),
                verify=os.getenv("SSL_VERIFY", "false").lower() != "true"
            ) as client:
                
                logger.debug(f"📤 Enviando petición a OpenRouter (modelo: {self.model})")
                
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extraer respuesta
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    
                    # Logging de métricas si están disponibles
                    if "usage" in data:
                        usage = data["usage"]
                        logger.debug(f"📊 OpenRouter usage: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")
                    
                    return content.strip()
                else:
                    logger.warning(f"⚠️ OpenRouter respondió sin choices: {data}")
                    return "⚠️ La IA no pudo generar una respuesta válida."
                    
        except httpx.TimeoutException:
            logger.error(f"⏰ Timeout en petición a OpenRouter ({self.timeout}s)")
            return f"⚠️ Timeout: La IA tardó más de {self.timeout} segundos en responder."
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP {e.response.status_code} de OpenRouter: {e.response.text[:200]}")
            return f"⚠️ Error HTTP {e.response.status_code}: {str(e)}"
        except httpx.RequestError as e:
            logger.error(f"❌ Error de red con OpenRouter: {e}")
            return f"⚠️ Error de conexión: {str(e)}"
        except Exception as e:
            logger.error(f"❌ Error inesperado con OpenRouter: {type(e).__name__}: {e}", exc_info=True)
            return f"⚠️ Error interno: {str(e)}"
    
    def get_model_info(self) -> dict:
        """Retorna información del modelo configurado."""
        return {
            "provider": "openrouter",
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }