# test_openrouter.py
import os, asyncio, httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-90b-vision-instruct:free")

async def test():
    print(f"🔑 API Key: {API_KEY[:20]}..." if API_KEY else "❌ API Key no definida")
    print(f"🤖 Modelo: {MODEL}")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "Test"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Hola, responde solo con 'OK'"}],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            print(f"📡 Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                respuesta = data["choices"][0]["message"]["content"]
                print(f"✅ Respuesta: {respuesta}")
            else:
                print(f"❌ Error: {resp.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")

if __name__ == "__main__":
    asyncio.run(test())