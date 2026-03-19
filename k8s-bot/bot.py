# bot.py - K8s Bot con IA + Parche SSL para VDI Corporativa
# ✅ Compatible con Python 3.14 + Windows + Proxy SARA + Certificados autofirmados

# ============================================================
# ⚠️ CONFIGURACIÓN CRÍTICA: ANTES DE CUALQUIER IMPORT DE RED ⚠️
# ============================================================

import os
import sys
import ssl
import warnings
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 1️⃣ Cargar .env PRIMERO
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    if not load_dotenv(dotenv_path=ENV_PATH):
        # Fallback: carga manual si python-dotenv falla
        with open(ENV_PATH, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    print(f"✅ .env cargado: {ENV_PATH}")
else:
    print(f"❌ .env no encontrado: {ENV_PATH}")
    sys.exit(1)

# 2️⃣ Configurar proxy desde variables de entorno (SARA o el que uses)
PROXY_URL = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://proxycocs.redsara.es:8080"
os.environ["HTTP_PROXY"] = PROXY_URL
os.environ["HTTPS_PROXY"] = PROXY_URL
os.environ["ALL_PROXY"] = PROXY_URL
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.local"
print(f"🌐 Proxy configurado: {PROXY_URL}")

# 3️⃣ Configurar variables SSL para httpx/requests
CERT_ENV = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
if CERT_ENV and Path(CERT_ENV).expanduser().resolve().exists():
    CERT_ABS = str(Path(CERT_ENV).expanduser().resolve())
    os.environ["SSL_CERT_FILE"] = CERT_ABS
    os.environ["REQUESTS_CA_BUNDLE"] = CERT_ABS
    os.environ["CURL_CA_BUNDLE"] = CERT_ABS
    print(f"✅ Certificado SSL: {CERT_ABS}")
else:
    print("⚠️ Certificado no válido o no definido - usando verify=False")

# 4️⃣ Patch global SSL de Python (para otras librerías)
ssl._create_default_https_context = ssl._create_unverified_context
print("🔓 SSL global: verify desactivado")

# 5️⃣ 🛠️ MONKEY-PATCH DE httpx.AsyncClient (CLAVE PARA QUE FUNCIONE)
# Esto intercepta TODAS las creaciones de AsyncClient y fuerza verify=False
print("🔧 Aplicando monkey-patch a httpx.AsyncClient...")

import httpx
_original_asyncclient_init = httpx.AsyncClient.__init__

def _patched_asyncclient_init(self, *args, **kwargs):
    """Wrapper que fuerza verify=False para desarrollo en VDI corporativa"""
    kwargs["verify"] = False
    kwargs.pop("cert", None)
    return _original_asyncclient_init(self, *args, **kwargs)

# Aplicar el patch
httpx.AsyncClient.__init__ = _patched_asyncclient_init
print("✅ Monkey-patch aplicado: httpx.AsyncClient usará verify=False")

# 6️⃣ Patch asyncio para Python 3.14 en Windows
if sys.platform == 'win32' and sys.version_info >= (3, 14):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("🔧 Patch asyncio aplicado para Python 3.14 en Windows")
    except Exception as e:
        print(f"⚠️ No se pudo aplicar patch asyncio: {e}")

# Suprimir warnings molestos
urllib3 = __import__("urllib3")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message=".*WindowsSelectorEventLoopPolicy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# AHORA SÍ: Imports normales del bot
# ============================================================

import logging
import time
from datetime import datetime
from typing import Callable, Any

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from prometheus_client import start_http_server, Counter, Histogram

# ==========================
# CONFIG
# ==========================
TOKEN = os.getenv("TELEGRAM_BOT_KUBERNETES_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_USER_CHAT_ID")

# ==========================
# LOGGING (JSON structured)
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
)
logger = logging.getLogger("k8s-bot")

# ==========================
# PROMETHEUS METRICS
# ==========================
REQUEST_COUNT = Counter('bot_requests_total', 'Total bot requests', ['type'])
REQUEST_LATENCY = Histogram('bot_request_latency_seconds', 'Request latency', ['type'])
ERROR_COUNT = Counter('bot_errors_total', 'Total errors', ['type'])

start_http_server(8000)
logger.info("Prometheus metrics exposed on :8000/metrics")

# ==========================
# CIRCUIT BREAKER
# ==========================
class CircuitBreaker:
    def __init__(self, max_failures=3, reset_timeout=60):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.max_failures:
            self.state = "OPEN"

# ==========================
# IMPORTS EXTERNOS (ahora con SSL parcheado)
# ==========================
from k8s_checker import cargar_k8s, obtener_estado_pods
from openrouter_client import consultar_ia

# Instancias
v1 = cargar_k8s()
ia_cb = CircuitBreaker()

# ==========================
# HANDLERS
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    REQUEST_COUNT.labels("start").inc()
    await update.message.reply_text("🤖 Bot K8s con IA activo. Usa /pods o /ia")

async def consultar_pods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    REQUEST_COUNT.labels("pods").inc()

    try:
        estado = obtener_estado_pods(v1)
        respuesta = await ia_cb.call(consultar_ia, f"Resume este estado:\n{estado}")
        await update.message.reply_text(respuesta)
    except Exception as e:
        ERROR_COUNT.labels("pods").inc()
        logger.error(f"pods_error: {str(e)}")
        await update.message.reply_text("❌ Error consultando pods")
    finally:
        REQUEST_LATENCY.labels("pods").observe(time.time() - start_time)

async def pregunta_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = " ".join(context.args)
    if not pregunta:
        await update.message.reply_text("🤔 Escribe una pregunta. Ej: `/ia qué es un pod`")
        return
    
    start_time = time.time()
    REQUEST_COUNT.labels("ia").inc()
    
    try:
        contexto = obtener_estado_pods(v1)[:500]
        respuesta = await ia_cb.call(consultar_ia, f"{pregunta}\n\nContexto K8s: {contexto}")
        await update.message.reply_text(respuesta)
    except Exception as e:
        ERROR_COUNT.labels("ia").inc()
        logger.error(f"ia_error: {str(e)}")
        await update.message.reply_text("❌ IA no disponible")
    finally:
        REQUEST_LATENCY.labels("ia").observe(time.time() - start_time)

async def mensaje_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()
    palabras_k8s = ["pod", "pods", "estado", "kubernetes", "k8s", "clúster", "deploy"]
    
    REQUEST_COUNT.labels("message").inc()
    start_time = time.time()
    
    try:
        if any(p in texto for p in palabras_k8s):
            estado = obtener_estado_pods(v1)
            respuesta = await ia_cb.call(consultar_ia, f"Pregunta: {texto}\n\nDatos: {estado}")
        else:
            respuesta = await ia_cb.call(consultar_ia, texto)
        await update.message.reply_text(respuesta)
    except Exception as e:
        ERROR_COUNT.labels("message").inc()
        logger.error(f"message_error: {str(e)}")
        await update.message.reply_text("❌ Error procesando mensaje")
    finally:
        REQUEST_LATENCY.labels("message").observe(time.time() - start_time)

# ==========================
# BACKGROUND TASK
# ==========================
async def chequeo_periodico(app: Application):
    logger.info("⏰ Tarea de chequeo iniciada (cada 10 min)")
    while True:
        await asyncio.sleep(600)
        try:
            estado = obtener_estado_pods(v1)
            if "ALERTA" in estado or "❌" in estado:
                informe = await ia_cb.call(consultar_ia, f"Problemas detectados:\n{estado}")
                await app.bot.send_message(
                    chat_id=CHAT_ID, 
                    text=f"🚨 **ALERTA AUTOMÁTICA**\n\n{informe}",
                    parse_mode="Markdown"
                )
                logger.info("✅ Alerta enviada")
        except Exception as e:
            logger.error(f"background_error: {str(e)}")
            ERROR_COUNT.labels("background").inc()

# ==========================
# MAIN ASYNC
# ==========================
async def main_async():
    logger.info("🚀 Starting K8s Bot with IA...")

    app = Application.builder() \
        .token(TOKEN) \
        .job_queue(None) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pods", consultar_pods))
    app.add_handler(CommandHandler("ia", pregunta_ia))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_normal))

    await app.initialize()
    await app.start()

    # Iniciar tarea de fondo
    asyncio.create_task(chequeo_periodico(app))

    logger.info("✅ Bot running. Waiting for messages...")
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")