# test_gemini_connection.py
import os
import asyncio
import httpx

# Configurar igual que el bot
os.environ["HTTPS_PROXY"] = "http://proxycocs.redsara.es:8080"

# Monkey-patch
import httpx
_original = httpx.AsyncClient.__init__
def _patched(self, *args, **kwargs):
    kwargs["verify"] = False
    return _original(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched

async def test():
    print("🔍 Testeando conexión a Gemini API...")
    print(f"   Proxy: {os.environ.get('HTTPS_PROXY')}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test a endpoint de Google AI
            response = await client.get("https://generativelanguage.googleapis.com/")
            print(f"   ✅ Google AI: {response.status_code}")
            return True
    except httpx.ProxyError as e:
        print(f"   ❌ Proxy Error: {e}")
        return False
    except httpx.ConnectError as e:
        print(f"   ❌ Connect Error (timeout/bloqueo): {e}")
        return False
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {e}")
        return False

result = asyncio.run(test())
print(f"\n{'✅ CONEXIÓN OK' if result else '❌ BLOQUEO CORPORATIVO DETECTADO'}")