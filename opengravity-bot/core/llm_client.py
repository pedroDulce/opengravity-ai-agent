# core/llm_client.py
"""
Cliente unificado de LLM con soporte para múltiples proveedores:
- Groq (gratis, rápido, modelos Llama)
- OpenRouter (gratis, muchos modelos)
- Gemini (pago, pero potente)

Configuración vía variables de entorno del .env
"""

import os
import ssl
import logging
import httpx
from pathlib import Path
from typing import Optional, List, Union
from abc import ABC, abstractmethod

# Monkey-patch para httpx (ANTES de cualquier import de red)
_original_init = httpx.AsyncClient.__init__
def _patched_init(self, *args, **kwargs):
    kwargs["verify"] = False
    kwargs["timeout"] = 60.0
    return _original_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_init

logger = logging.getLogger(__name__)


# ==============================
# INTERFAZ BASE PARA TODOS LOS PROVEEDORES
# ==============================

class LLMProvider(ABC):
    """Interfaz común para todos los proveedores de LLM"""
    
    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Genera una respuesta para el prompt dado"""
        pass
    
    @abstractmethod
    def generate_code(self, task: str, language: str = "python", 
                      context: Optional[str] = None) -> str:
        """Genera código para una tarea específica"""
        pass
    
    @abstractmethod
    def explain_code(self, code: str, language: str = "python") -> str:
        """Explica qué hace un fragmento de código"""
        pass
    
    @abstractmethod
    def debug_error(self, error_message: str, code_context: str, 
                    language: str = "python") -> str:
        """Ayuda a debuggear un error"""
        pass


# ==============================
# IMPLEMENTACIÓN: GROQ
# ==============================

class GroqClient(LLMProvider):
    """Cliente para Groq API (https://console.groq.com)"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile",
                 temperature: float = 0.2, max_tokens: int = 4096,
                 proxy_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.proxy_url = proxy_url
        self._configure_ssl()
        logger.info(f"✅ GroqClient inicializado: {model}")
    
    def _configure_ssl(self):
        """Configura SSL para entorno corporativo"""
        ssl._create_default_https_context = ssl._create_unverified_context
        if self.proxy_url:
            os.environ["HTTPS_PROXY"] = self.proxy_url
            os.environ["HTTP_PROXY"] = self.proxy_url
    
    def _make_request(self, messages: List[dict]) -> str:
        """Hace la petición HTTP a la API de Groq"""
        import requests
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(
                url, json=payload, headers=headers,
                proxies={"https": self.proxy_url, "http": self.proxy_url} if self.proxy_url else None,
                verify=False,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ Error en Groq API: {e}")
            return f"❌ Error Groq: {type(e).__name__}: {e}"
    
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return self._make_request(messages)
    
    def generate_code(self, task: str, language: str = "python", 
                      context: Optional[str] = None) -> str:
        system = f"""Eres un desarrollador senior experto en {language.upper()}.
Genera código limpio, bien documentado y siguiendo mejores prácticas.

Instrucciones:
1. Comentarios en español
2. Nombres descriptivos
3. Manejo de errores
4. Convenciones de {language}

Formato:
- Breve explicación en español
- Código en bloque markdown ```{language}
- Notas importantes al final"""
        
        user = f"Tarea: {task}"
        if context:
            user += f"\n\nContexto:\n{context}"
        
        return self.generate(user, system_instruction=system)
    
    def explain_code(self, code: str, language: str = "python") -> str:
        system = f"""Eres un mentor técnico experto en {language.upper()}.
Explica el código de forma clara y didáctica en español.

Instrucciones:
1. Resume el propósito general
2. Explica partes clave
3. Menciona mejoras posibles"""
        
        user = f"Explica este código en {language}:\n\n```{language}\n{code}\n```"
        return self.generate(user, system_instruction=system)
    
    def debug_error(self, error_message: str, code_context: str, 
                    language: str = "python") -> str:
        system = f"""Eres un experto en debugging de {language.upper()}.
Ayuda a diagnosticar y resolver errores sistemáticamente.

Instrucciones:
1. Analiza el error y contexto
2. Identifica causa probable
3. Propón solución con código corregido
4. Explica por qué ocurre"""
        
        user = f"""Error: {error_message}

Código:
```{language}
{code_context}
¿Cuál es el problema y cómo lo soluciono?"""
        return self.generate(user, system_instruction=system)


class OpenRouterClient(LLMProvider):
    """Cliente para OpenRouter API (https://openrouter.ai)"""

    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.1-8b-instruct:free",
                 temperature: float = 0.2, max_tokens: int = 4096,
                 proxy_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.proxy_url = proxy_url
        self._configure_ssl()
        logger.info(f"✅ OpenRouterClient inicializado: {model}")

    def _configure_ssl(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        if self.proxy_url:
            os.environ["HTTPS_PROXY"] = self.proxy_url
            os.environ["HTTP_PROXY"] = self.proxy_url

    def _make_request(self, messages: List[dict]) -> str:
        import requests
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://opengravity.local",
            "X-Title": "OpenGravity Bot"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(
                url, json=payload, headers=headers,
                proxies={"https": self.proxy_url, "http": self.proxy_url} if self.proxy_url else None,
                verify=False,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ Error en OpenRouter API: {e}")
            return f"❌ Error OpenRouter: {type(e).__name__}: {e}"

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return self._make_request(messages)

    def generate_code(self, task: str, language: str = "python", 
                      context: Optional[str] = None) -> str:
        system = f"""Eres un desarrollador senior experto en {language.upper()}.
Genera código limpio, bien documentado y siguiendo mejores prácticas.

Instrucciones:
1. Comentarios en español
2. Nombres descriptivos
3. Manejo de errores
4. Convenciones de {language}

Formato:
- Breve explicación en español
- Código en bloque markdown ```{language}
- Notas importantes al final"""
        
        user = f"Tarea: {task}"
        if context:
            user += f"\n\nContexto:\n{context}"
        
        return self.generate(user, system_instruction=system)

    def explain_code(self, code: str, language: str = "python") -> str:
        system = f"""Eres un mentor técnico experto en {language.upper()}.
Explica el código de forma clara y didáctica en español.

Instrucciones:
1. Resume el propósito general
2. Explica partes clave
3. Menciona mejoras posibles"""
        
        user = f"Explica este código en {language}:\n\n```{language}\n{code}\n```"
        return self.generate(user, system_instruction=system)

    def debug_error(self, error_message: str, code_context: str, 
                    language: str = "python") -> str:
        system = f"""Eres un experto en debugging de {language.upper()}.
Ayuda a diagnosticar y resolver errores sistemáticamente.

Instrucciones:
1. Analiza el error y contexto
2. Identifica causa probable
3. Propón solución con código corregido
4. Explica por qué ocurre"""
        
        user = f"""Error: {error_message}

Código:
```{language}
{code_context}
¿Cuál es el problema y cómo lo soluciono?"""
        return self.generate(user, system_instruction=system)

class LLMClient:
    """
    Cliente unificado que selecciona el proveedor según configuración.
Uso:
    client = LLMClient()  # Lee configuración del .env
    response = client.generate("¿Qué es Python?")
"""

    def __init__(self, provider: Optional[str] = None, **kwargs):
        # Leer configuración desde .env o usar parámetros explícitos
        self.provider_name = provider or os.getenv("LLM_PROVIDER", "groq").lower()
        self.proxy_url = kwargs.get("proxy_url") or os.getenv("LLM_PROXY") or os.getenv("HTTPS_PROXY")
        
        logger.info(f"🔍 Inicializando LLMClient con proveedor: {self.provider_name}")
        
        if self.provider_name == "groq":
            self._client = GroqClient(
                api_key=kwargs.get("api_key") or os.getenv("GROQ_API_KEY"),
                model=kwargs.get("model") or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                temperature=float(kwargs.get("temperature") or os.getenv("GROQ_TEMPERATURE", "0.2")),
                max_tokens=int(kwargs.get("max_tokens") or os.getenv("GROQ_MAX_TOKENS", "4096")),
                proxy_url=self.proxy_url
            )
        elif self.provider_name == "openrouter":
            self._client = OpenRouterClient(
                api_key=kwargs.get("api_key") or os.getenv("OPENROUTER_API_KEY"),
                model=kwargs.get("model") or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
                temperature=float(kwargs.get("temperature") or os.getenv("OPENROUTER_TEMPERATURE", "0.2")),
                max_tokens=int(kwargs.get("max_tokens") or os.getenv("OPENROUTER_MAX_TOKENS", "4096")),
                proxy_url=self.proxy_url
            )
        elif self.provider_name == "gemini":
            # Placeholder para Gemini (puedes añadir la implementación si tienes quota)
            logger.warning("⚠️ Gemini seleccionado pero no implementado en esta versión")
            self._client = GroqClient(  # Fallback a Groq
                api_key=os.getenv("GROQ_API_KEY"),
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                proxy_url=self.proxy_url
            )
            logger.info("🔄 Fallback a Groq")
        else:
            raise ValueError(f"Proveedor no soportado: {self.provider_name}. Usa: groq, openrouter")
        
        logger.info(f"✅ LLMClient listo: {self.provider_name}")

    # Delegar todos los métodos al cliente interno
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        return self._client.generate(prompt, system_instruction)

    def generate_code(self, task: str, language: str = "python", 
                    context: Optional[str] = None) -> str:
        return self._client.generate_code(task, language, context)

    def explain_code(self, code: str, language: str = "python") -> str:
        return self._client.explain_code(code, language)

    def debug_error(self, error_message: str, code_context: str, 
                    language: str = "python") -> str:
        return self._client.debug_error(error_message, code_context, language)

    # core/llm_client.py - AÑADIR este método en la clase LLMClient

    def generate_with_context(self, prompt: str, context: Optional[str] = None, 
                              system_instruction: Optional[str] = None) -> str:
        """
        Genera respuesta inyectando contexto corporativo en el prompt.
        
        Args:
            prompt: La consulta del usuario
            context: Contexto corporativo pre-recuperado (de ContextManager)
            system_instruction: Instrucciones adicionales del sistema
            
        Returns:
            Respuesta de la IA con contexto aplicado
        """
        # Construir prompt enriquecido con contexto
        enriched_prompt = prompt
        
        if context:
            enriched_prompt = f"""{context}

---

🎯 TU TAREA:
{prompt}

⚠️ IMPORTANTE: 
- El código generado DEBE seguir EXACTAMENTE las convenciones mostradas en el contexto corporativo arriba.
- Usa los nombres de componentes, servicios y patrones definidos en la documentación.
- Si algo no está cubierto en el contexto, aplica mejores prácticas estándar de Angular.
"""
        
        # Delegar al método generate existente
        return self.generate(enriched_prompt, system_instruction)

    @property
    def provider(self) -> str:
        return self.provider_name

