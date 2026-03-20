# k8s_agent.py
# Agente de Kubernetes que usa LLM para interpretar y ejecutar comandos

import os
import json
import httpx
from dotenv import load_dotenv
from k8s_tools import TOOLS_REGISTRY, get_tools_description

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "xiaomi/mimo-v2-pro")

SYSTEM_PROMPT = f"""
Eres un Agente Experto de Kubernetes. Tu trabajo es ayudar al usuario a consultar y gestionar su clúster.

{get_tools_description()}

INSTRUCCIONES:
1. Analiza la petición del usuario en lenguaje natural
2. Determina qué herramienta(s) necesitas usar
3. Responde en formato JSON EXACTO con esta estructura:

{{
    "action": "execute_tools",
    "tools": [
        {{
            "name": "nombre_herramienta",
            "parameters": {{"param1": "valor1", "param2": "valor2"}}
        }}
    ],
    "requires_confirmation": false,
    "explanation": "Explicación breve en español de lo que harás"
}}

REGLAS IMPORTANTES:
- Para herramientas con `requires_confirmation: true`, PON `requires_confirmation: true` en tu respuesta
- Si la petición es ambigua, pide clarificación
- Usa el namespace "atom" por defecto si el usuario no especifica
- Sé conciso en la explicación
- NO inventes herramientas que no están en la lista
- Si no necesitas herramientas (saludo, pregunta general), usa action: "respond_directly"

EJEMPLOS:

Usuario: "¿Qué servicios están operativos?"
Respuesta:
{{
    "action": "execute_tools",
    "tools": [{{"name": "get_services", "parameters": {{"namespace": "atom"}}}}],
    "requires_confirmation": false,
    "explanation": "Voy a consultar los servicios del namespace atom"
}}

Usuario: "Reinicia el pod apache"
Respuesta:
{{
    "action": "execute_tools",
    "tools": [{{"name": "restart_pod", "parameters": {{"pod_name": "apache-server-deployment", "namespace": "atom"}}}}],
    "requires_confirmation": true,
    "explanation": "Esto eliminará el pod para que Kubernetes lo recreé. ¿Confirmas?"
}}

Usuario: "Hola, ¿qué puedes hacer?"
Respuesta:
{{
    "action": "respond_directly",
    "response": "¡Hola! Soy tu Agente de Kubernetes. Puedo consultar pods, servicios, deployments, eventos, logs, y más. También puedo reiniciar pods o escalar deployments (con confirmación). ¿En qué te ayudo?",
    "requires_confirmation": false,
    "explanation": ""
}}
"""

async def agente_k8s(mensaje_usuario, contexto_adicional=""):
    """
    Procesa mensaje natural y devuelve plan de acción
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://k8s-bot.local",
        "X-Title": "K8s Agent"
    }
    
    prompt = f"""
{SYSTEM_PROMPT}

CONTEXTO ADICIONAL:
{contexto_adicional}

MENSAJE DEL USUARIO:
{mensaje_usuario}

Responde SOLO con JSON válido, sin markdown ni texto extra.
"""
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Bajo para respuestas más deterministas
        "max_tokens": 500
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                contenido = data["choices"][0]["message"]["content"]
                
                # Limpiar respuesta (quitar markdown si lo hay)
                contenido = contenido.strip()
                if contenido.startswith("```json"):
                    contenido = contenido.replace("```json", "").replace("```", "").strip()
                elif contenido.startswith("```"):
                    contenido = contenido.replace("```", "").strip()
                
                try:
                    return json.loads(contenido)
                except json.JSONDecodeError as e:
                    return {
                        "action": "respond_directly",
                        "response": f"⚠️ Error procesando tu petición. Por favor reformula.",
                        "error": str(e)
                    }
            else:
                return {"action": "respond_directly", "response": "⚠️ La IA no pudo generar una respuesta."}
                
    except Exception as e:
        return {
            "action": "respond_directly",
            "response": f"⚠️ Error de conexión con la IA: {str(e)}"
        }