import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL")
SITE_URL = "https://it.muface.es"  # Opcional, para estadísticas
SITE_NAME = "K8s Telegram Bot"  # Opcional

async def consultar_ia(mensaje_usuario, contexto=""):
    """
    Envía un mensaje a OpenRouter y recibe una respuesta de la IA.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_NAME
    }
    
    system_prompt = """Eres un asistente experto en Kubernetes y monitoreo de clústeres.
Tu trabajo es ayudar al usuario a consultar el estado de sus pods y servicios.

REGLAS IMPORTANTES:
1. Si el usuario pregunta sobre pods, estado, kubernetes, clúster, responde que puedes consultar esa información.
2. Si el usuario hace una pregunta general de Kubernetes, responde con tu conocimiento.
3. Sé conciso y amigable.
4. Usa emojis para hacer la respuesta más amigable.
5. Si no estás seguro, ofrece consultar el clúster real.

CONTEXTO ACTUAL DEL CLÚSTER:
""" + contexto

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": mensaje_usuario}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return "⚠️ La IA no pudo generar una respuesta."
                
    except httpx.HTTPError as e:
        print(f"❌ Error HTTP con OpenRouter: {e}")
        return f"⚠️ Error de conexión con la IA: {str(e)}"
    except Exception as e:
        print(f"❌ Error general con OpenRouter: {e}")
        return f"⚠️ Error: {str(e)}"