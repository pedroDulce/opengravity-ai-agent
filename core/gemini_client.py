# core/gemini_client.py
"""
Cliente de Gemini Flash con la NUEVA API google-genai.
Soporte para proxy corporativo SARA y configuración robusta para VDI.
"""

# core/gemini_client.py - PRIMERA LÍNEA (antes de cualquier import)
# 🛠️ MONKEY-PATCH para httpx (forzar verify=False para VDI corporativa)
import httpx
_original_asyncclient_init = httpx.AsyncClient.__init__

def _patched_asyncclient_init(self, *args, **kwargs):
    """Forzar verify=False para desarrollo en VDI con proxy SARA"""
    kwargs["verify"] = False
    kwargs.pop("cert", None)
    return _original_asyncclient_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = _patched_asyncclient_init
# ✅ Fin del monkey-patch

import os
import ssl
import logging
from pathlib import Path
from typing import Optional, List, Union
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Cliente de Gemini Flash usando la nueva API google-genai.
    
    Compatibilidad:
    - Proxy corporativo vía variables de entorno
    - SSL bypass para desarrollo en VDI
    - Mismos métodos que la versión anterior para compatibilidad
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", 
                 proxy_url: Optional[str] = None, cert_path: Optional[str] = None):
        """
        Inicializa el cliente de Gemini con la nueva API.
        
        Args:
            api_key: Clave de API de Google AI Studio
            model: Nombre del modelo (ej: "gemini-2.0-flash")
            proxy_url: URL del proxy corporativo (opcional)
            cert_path: Ruta al certificado PEM (opcional)
        """
        self.api_key = api_key
        self.model_name = model
        self.proxy_url = proxy_url
        self.cert_path = cert_path
        self._client = None
        
        # Configurar entorno para proxy/SSL (afecta a httpx usado internamente)
        self._configure_environment()
        
        # Inicializar cliente de la nueva API
        self._initialize_client()
        
        logger.info(f"✅ GeminiClient (google-genai) inicializado: {model}")
    
    def _configure_environment(self):
        """Configura variables de entorno para proxy y SSL"""
        # Proxy: google-genai usa httpx internamente, que lee estas vars
        if self.proxy_url:
            os.environ["HTTP_PROXY"] = self.proxy_url
            os.environ["HTTPS_PROXY"] = self.proxy_url
            os.environ["ALL_PROXY"] = self.proxy_url
            logger.debug(f"🌐 Proxy configurado: {self.proxy_url}")
        
        # SSL: para desarrollo en VDI con certificados autofirmados
        if self.cert_path and Path(self.cert_path).exists():
            cert_abs = str(Path(self.cert_path).resolve())
            os.environ["SSL_CERT_FILE"] = cert_abs
            os.environ["REQUESTS_CA_BUNDLE"] = cert_abs
            os.environ["CURL_CA_BUNDLE"] = cert_abs
            logger.debug(f"🔐 Certificado SSL: {cert_abs}")
        else:
            # Fallback: desactivar verificación para desarrollo
            ssl._create_default_https_context = ssl._create_unverified_context
            logger.debug("🔓 SSL verify desactivado (desarrollo VDI)")
    
    def _initialize_client(self):
        """Inicializa el cliente de la nueva API google-genai"""
        try:
            # ✅ Configurar httpx con proxy explícito (además del monkey-patch)
            import httpx
            
            # Crear cliente HTTP con proxy configurado
            http_client = httpx.AsyncClient(
                proxy=self.proxy_url if self.proxy_url else None,
                verify=False,  # Forzar verify=False
                timeout=60.0   # Timeout más generoso para corporate proxy
            )
            
            # Crear cliente de Gemini con el cliente HTTP personalizado
            self._client = genai.Client(
                api_key=self.api_key,
                http_client=http_client  # ← Usar nuestro cliente con proxy
            )
            
            logger.info(f"✅ Cliente google-genai creado con proxy: {self.proxy_url}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente google-genai: {e}")
            raise
            
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Genera una respuesta de Gemini para el prompt dado.
        
        Args:
            prompt: El prompt del usuario
            system_instruction: Instrucciones de sistema opcionales para contexto
            
        Returns:
            La respuesta generada como string
        """
        if not self._client:
            raise RuntimeError("Cliente no inicializado.")
        
        try:
            # Preparar contenido para la API
            contents = self._build_contents(prompt, system_instruction)
            
            # Configurar generación
            config = types.GenerateContentConfig(
                temperature=0.2,  # Baja para código preciso
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
                # Safety settings: bloquear nada para desarrollo
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                ]
            )
            
            logger.debug(f"🧠 Enviando prompt a Gemini ({len(prompt)} chars)")
            
            # Llamar a la nueva API
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Extraer texto de la respuesta
            result = response.text.strip() if response.text else ""
            
            logger.debug(f"✅ Respuesta recibida ({len(result)} chars)")
            return result
            
        except Exception as e:
            error_msg = f"Error en Gemini: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def _build_contents(self, prompt: str, system_instruction: Optional[str]) -> Union[str, List]:
        """
        Construye el contenido para la API según si hay instrucción de sistema.
        
        La nueva API acepta:
        - str simple para prompts básicos
        - List[types.Content] para conversaciones multi-turno
        - str con prefijo de sistema para contexto
        """
        if system_instruction:
            # Para prompts con contexto de sistema, prependemos la instrucción
            return f"Sistema: {system_instruction}\n\nUsuario: {prompt}"
        return prompt
    
    def generate_code(self, task: str, language: str = "python", 
                      context: Optional[str] = None) -> str:
        """Genera código para una tarea específica."""
        system_prompt = f"""Eres un desarrollador senior experto en {language.upper()}.
Genera código limpio, bien documentado y siguiendo mejores prácticas.

Instrucciones:
1. Incluye comentarios explicativos en español
2. Usa nombres de variables descriptivos
3. Maneja errores apropiadamente
4. Sigue convenciones del lenguaje ({language})
5. Si es relevante, menciona dependencias necesarias

Formato de respuesta:
- Primero una breve explicación en español
- Luego el código en un bloque markdown ```{language}
- Finalmente notas importantes si las hay"""

        user_prompt = f"Tarea: {task}"
        if context:
            user_prompt += f"\n\nContexto del proyecto:\n{context}"
        
        return self.generate(user_prompt, system_instruction=system_prompt)
    
    def explain_code(self, code: str, language: str = "python") -> str:
        """Explica qué hace un fragmento de código"""
        system_prompt = f"""Eres un mentor técnico experto en {language.upper()}.
Explica el código de forma clara y didáctica en español.

Instrucciones:
1. Resume el propósito general del código
2. Explica las partes clave línea por línea o bloque por bloque
3. Menciona posibles mejoras o consideraciones
4. Usa ejemplos si ayuda a clarificar"""

        user_prompt = f"Explica este código en {language}:\n\n```{language}\n{code}\n```"
        return self.generate(user_prompt, system_instruction=system_prompt)
    
    def debug_error(self, error_message: str, code_context: str, 
                    language: str = "python") -> str:
        """Ayuda a debuggear un error dado el mensaje y contexto"""
        system_prompt = f"""Eres un experto en debugging de {language.upper()}.
Ayuda a diagnosticar y resolver errores de forma sistemática.

Instrucciones:
1. Analiza el mensaje de error y el contexto del código
2. Identifica la causa más probable del problema
3. Propone una solución concreta con código corregido
4. Explica por qué ocurre el error para prevenir futuros casos"""

        user_prompt = f"""Error: {error_message}

Código relacionado:
```{language}
{code_context}
¿Cuál es el problema y cómo lo soluciono?"""
        return self.generate(user_prompt, system_instruction=system_prompt)

    

    async def generate_streaming(self, prompt: str, callback=None) -> str:
        """
        Genera respuesta con streaming usando la nueva API.
        
        Args:
            prompt: El prompt del usuario
            callback: Función async opcional para procesar chunks en tiempo real
            
        Returns:
            La respuesta completa acumulada
        """
        if not self._client:
            raise RuntimeError("Cliente no inicializado.")
        
        try:
            full_response = []
            contents = self._build_contents(prompt, None)
            
            config = types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
            )
            
            for chunk in self._client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            ):
                if chunk.text:
                    full_response.append(chunk.text)
                    if callback:
                        await callback(chunk.text)
            
            result = "".join(full_response).strip()
            logger.debug(f"✅ Streaming completo: {len(result)} chars")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en streaming Gemini: {e}")
            return f"❌ Error: {e}"    

# ==============================
# MÉTODOS ADICIONALES DE LA NUEVA API
# ==============================

    def count_tokens(self, prompt: str) -> int:
        """Cuenta los tokens que consumiría un prompt (útil para controlar costos)"""
        if not self._client:
            return 0
        try:
            result = self._client.models.count_tokens(
                model=self.model_name,
                contents=prompt
            )
            return result.total_tokens if result else 0
        except Exception as e:
            logger.warning(f"⚠️ No se pudo contar tokens: {e}")
            return len(prompt) // 4  # Estimación aproximada

    def list_models(self) -> List[str]:
        """Lista los modelos disponibles en tu cuenta"""
        if not self._client:
            return []
        try:
            models = self._client.models.list()
            return [m.name for m in models] if models else []
        except Exception as e:
            logger.error(f"❌ Error listando modelos: {e}")
            return []
        