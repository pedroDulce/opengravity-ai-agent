# diagnostics.py
import os
import sys
import ssl
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 🛠️ CRÍTICO: Cargar .env ANTES de cualquier uso de variables de entorno
# Buscar .env en la carpeta del script
script_dir = Path(__file__).resolve().parent
env_path = script_dir / ".env"

print(f"🔍 Buscando .env en: {env_path}")
print(f"📁 .env existe: {env_path.exists()}")

if env_path.exists():
    # Cargar variables desde .env
    load_result = load_dotenv(dotenv_path=env_path)
    print(f"✅ load_dotenv() ejecutado: {load_result}")
    
    # Debug: mostrar contenido del .env (sin valores sensibles)
    print("\n📄 Contenido de .env (claves):")
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key = line.split('=')[0]
                print(f"   - {key}")
else:
    print(f"❌ .env no encontrado en {env_path}")

print("\n" + "="*60)
print("🔍 === DIAGNÓSTICO OPENGRAVITY ===")
print("="*60)

# ==============================
# 1. VERIFICAR VARIABLES DE ENTORNO
# ==============================
print("\n📋 Variables de entorno:")
env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"]

for key in env_vars:
    value = os.environ.get(key)
    if value:
        # Mostrar valor truncado para no exponer rutas completas
        display = value[:50] + "..." if len(value) > 50 else value
        print(f"   ✅ {key}: {display}")
    else:
        print(f"   ❌ {key}: NO DEFINIDA")

# ==============================
# 2. VERIFICAR CERTIFICADO
# ==============================
print(f"\n🔐 Certificado:")
cert_candidates = [
    "proxy_root_ca.pem",
    "combined-ca.pem", 
    "ca-bundle.crt",
    os.environ.get("SSL_CERT_FILE", ""),
]

cert_found = None
for candidate in cert_candidates:
    if candidate and Path(candidate).exists():
        cert_found = Path(candidate).resolve()
        print(f"   ✅ Encontrado: {cert_found} ({cert_found.stat().st_size} bytes)")
        break

if not cert_found:
    print(f"   ❌ Ningún certificado encontrado en: {[c for c in cert_candidates if c]}")
    print(f"   💡 Ruta actual de trabajo: {Path.cwd()}")

# ==============================
# 3. VERIFICAR LIBRERÍAS
# ==============================
print(f"\n🤖 Librerías:")
try:
    import telegram
    print(f"   ✅ python-telegram-bot: {telegram.__version__}")
except ImportError:
    print(f"   ❌ python-telegram-bot: NO INSTALADO")

try:
    print(f"   ✅ httpx: {httpx.__version__}")
except:
    print(f"   ❌ httpx: NO DISPONIBLE")

try:
    import certifi
    print(f"   ✅ certifi: {certifi.__version__} ({certifi.where()})")
except:
    print(f"   ❌ certifi: NO DISPONIBLE")

# ==============================
# 4. TEST DE CONEXIÓN HTTPX
# ==============================
print(f"\n🌐 Test de conexión httpx:")

proxy_url = os.environ.get("HTTPS_PROXY", "http://proxycocs.redsara.es:8080")
cert_path = os.environ.get("SSL_CERT_FILE")

print(f"   Proxy: {proxy_url}")
print(f"   SSL_CERT_FILE: {cert_path or 'NO DEFINIDO'}")

# Preparar parámetros para httpx
httpx_kwargs = {"proxy": proxy_url, "timeout": 30}

if cert_path and Path(cert_path).exists():
    httpx_kwargs["verify"] = str(Path(cert_path).resolve())
    print(f"   Verify: {httpx_kwargs['verify']}")
else:
    httpx_kwargs["verify"] = False
    print(f"   Verify: False (fallback)")

async def test_connection():
    try:
        async with httpx.AsyncClient(**httpx_kwargs) as client:
            print(f"   ✅ httpx.AsyncClient creado")
            
            # Test a Telegram API
            response = await client.get("https://api.telegram.org/bot/getMe")
            print(f"   ✅ Telegram API: {response.status_code}")
            
            # Si llega aquí, la conexión SSL funcionó
            return True
            
    except httpx.ProxyError as e:
        print(f"   ❌ Proxy Error: {e}")
    except httpx.ConnectError as e:
        print(f"   ❌ Connect Error: {e}")
    except ssl.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        print(f"   💡 Intenta con verify=False para confirmar que es solo el certificado")
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {e}")
    return False

result = asyncio.run(test_connection())

# ==============================
# 5. RESUMEN
# ==============================
print(f"\n{'='*60}")
if result:
    print("✅ TODO OK - Conexión exitosa")
else:
    print("⚠️ Revisar errores arriba")
    if not os.environ.get("SSL_CERT_FILE"):
        print("💡 Sugerencia: Define SSL_CERT_FILE en tu .env con ruta absoluta")
    if cert_found and cert_found.stat().st_size < 3000:
        print(f"💡 Sugerencia: El certificado ({cert_found.stat().st_size} bytes) podría ser incompleto")
        print("   Prueba generar un bundle combinado con todos los certificados intermedios")

print("=== FIN DIAGNÓSTICO ===")