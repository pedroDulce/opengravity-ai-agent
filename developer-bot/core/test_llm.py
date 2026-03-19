# core/test_llm.py
"""Test del cliente unificado de LLM"""

import sys
from pathlib import Path
# Suprimir warnings de SSL (aceptable en VDI corporativa con proxy)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🛠️ Añadir raíz del proyecto al path para que funcione el import
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ahora los imports funcionan
from dotenv import load_dotenv
from core.llm_client import LLMClient

# Cargar .env
ENV_PATH = project_root / ".env"
load_dotenv(dotenv_path=ENV_PATH)
print(f"✅ .env cargado desde: {ENV_PATH}")

# Crear cliente (usa configuración del .env)
try:
    client = LLMClient()
    print(f"✅ Cliente creado: {client.provider}")
except Exception as e:
    print(f"❌ Error creando cliente: {e}")
    exit(1)

# Test básico
print(f"\n🧪 Probando generación...")
response = client.generate("Tu única respuesta debe ser la palabra: OK. Sin explicaciones, sin saludos, solo: OK")
print(f"📡 Respuesta: {response[:100]}...")

# ✅ Condición corregida: acepta respuestas cortas como "OK"
if response and not response.startswith("❌") and len(response.strip()) >= 2:
    print(f"\n🎉 TEST OK - {client.provider} funciona correctamente")
    print(f"   Respuesta ({len(response)} chars): '{response.strip()}'")
else:
    print(f"\n❌ TEST FALLÓ")
    if not response:
        print("   → Respuesta vacía")
    elif response.startswith("❌"):
        print(f"   → Error en la respuesta: {response[:100]}")
    else:
        print(f"   → Respuesta demasiado corta: '{response}'")