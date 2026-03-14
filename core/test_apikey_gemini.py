# test_gemini_api.py
import os
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 🛠️ CARGAR .env ANTES DE CUALQUIER os.getenv()
BASE_DIR = Path(__file__).resolve().parent.parent  # Ajusta según tu estructura
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    print(f"✅ .env cargado desde: {ENV_PATH}")
else:
    print(f"❌ .env no encontrado en: {ENV_PATH}")

# AHORA SÍ: leer variables
PROXY = os.environ.get("HTTPS_PROXY", "http://proxycocs.redsara.es:8080")
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ Define GEMINI_API_KEY en tu entorno o .env")
    exit(1)

# Monkey-patch para VDI (igual que en tu bot)
_original = httpx.AsyncClient.__init__
def _patched(self, *args, **kwargs):
    kwargs["verify"] = False
    kwargs["timeout"] = 60.0
    return _original(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched

async def test_api():
    print(f"🔍 Test Gemini API con key: {API_KEY[:20]}...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": "Responde solo: OK"}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 10
        }
    }
    
    try:
        async with httpx.AsyncClient(proxy=PROXY) as client:
            response = await client.post(url, json=payload)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Respuesta: {text}")
                return True
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text[:200]}")
                return False
                
    except httpx.ProxyError as e:
        print(f"❌ Proxy Error: {e}")
        return False
    except httpx.ConnectError as e:
        print(f"❌ Connect Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_api())
    print(f"\n{'✅ TEST OK - La API funciona' if result else '❌ TEST FALLÓ - Revisa API Key o proxy'}")