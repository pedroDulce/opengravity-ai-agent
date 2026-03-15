# opengravity_bot.py
# ✅ FINAL: python-telegram-bot v21.0 + httpx 0.27.x + Python 3.14 + Windows 11 + Proxy SARA
# ✅ Monkey-patch de httpx.AsyncClient para forzar verify=False (desarrollo en VDI)

# ==============================
# IMPORTS (DESPUÉS de configurar ENV y patches)
# ==============================
# opengravity_bot.py - Sección de imports CORREGIDA

import os
import sys
import ssl
import logging
import warnings
import asyncio
from pathlib import Path  # ← ¡IMPORTANTE!
from dotenv import load_dotenv

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.request import HTTPXRequest

from handlers.ai_handler import (
    cmd_ai,
    cmd_dev,
    cmd_explain,
    cmd_debug,
    cmd_review,
    cmd_analyze,
    cmd_improve,
    cmd_angular,
    cmd_context,      
    cmd_swagger,
    cmd_create,    
    cmd_tests        
)

# opengravity_bot.py - Después de los imports (línea ~25)

# ==============================
# SUPRIMIR WARNINGS GLOBALES (VDI corporativa)
# ==============================
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import warnings
warnings.filterwarnings("ignore", message=".*WindowsSelectorEventLoopPolicy.*")
warnings.filterwarnings("ignore", message=".*set_event_loop_policy.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*google.generativeai.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
# ⚠️ CONFIGURACIÓN CRÍTICA: ANTES DE CUALQUIER IMPORT DE RED ⚠️
# ============================================================

# opengravity_bot.py - Después de los imports, añadir:

# ==============================
# CONFIGURACIÓN DE RESILIENCIA DE RED
# ==============================

# Timeouts y retries para conexiones HTTP
HTTP_CONNECT_TIMEOUT = 30.0      # Segundos para establecer conexión
HTTP_READ_TIMEOUT = 120.0        # Segundos para leer respuesta
HTTP_WRITE_TIMEOUT = 30.0        # Segundos para escribir request
HTTP_POOL_TIMEOUT = 30.0         # Segundos para obtener conexión del pool

# Reintentos para polling de Telegram
POLLING_RETRY_DELAY = 5          # Segundos entre reintentos
POLLING_MAX_RETRIES = 10         # Máximo reintentos antes de reiniciar
POLLING_TIMEOUT = 30             # Timeout para getUpdates

# Watchdog: reiniciar bot si no hay actividad
WATCHDOG_TIMEOUT = 300           # Segundos sin actividad antes de reiniciar (5 min)

# 1️⃣ Cargar .env PRIMERO (para que las variables estén disponibles)
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

# 2️⃣ Configurar proxy desde variables de entorno
PROXY_URL = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://proxycocs.redsara.es:8080"
os.environ["HTTP_PROXY"] = PROXY_URL
os.environ["HTTPS_PROXY"] = PROXY_URL
os.environ["ALL_PROXY"] = PROXY_URL
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.local"
print(f"🌐 Proxy configurado: {PROXY_URL}")

# 3️⃣ Configurar variables SSL para httpx/requests (por si las leen)
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
    # Forzar verify=False independientemente de lo que pase el caller
    kwargs["verify"] = False
    # También asegurar que no se usen certificados por defecto
    kwargs.pop("cert", None)
    # Llamar al __init__ original con los kwargs modificados
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

# Suprimir warnings molestos (pero mantener errores críticos)
# Añade esto justo después de los imports en opengravity_bot.py:
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# IMPORTS (AHORA SÍ, después de configurar todo)
# ============================================================

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.request import HTTPXRequest

# ============================================================
# CREDENCIALES
# ============================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR CRÍTICO: TELEGRAM_BOT_TOKEN no definido en .env")
    sys.exit(1)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    force=True
)
logger = logging.getLogger("OpenGravityBot")

# ============================================================
# HANDLERS DE TELEGRAM
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Saludo inicial"""
    if not update.message:
        return
    user = update.effective_user
    msg = f"""
🟢 *OpenGravity Bot*

👤 Usuario: {user.first_name} @{user.username or 'sin usuario'}
🤖 Estado: Online ✅
🌐 Proxy: {PROXY_URL}
🔐 SSL: 🔓 Desarrollo (VDI)

💡 Usa /help para ver comandos
"""
    await update.message.reply_text(msg, parse_mode='Markdown')
    logger.info(f"/start desde @{user.username or 'unknown'}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Información del sistema"""
    if not update.message:
        return
    import platform
    msg = f"""
🖥 *Estado OpenGravity*
━━━━━━━━━━━━━━━━━━━━
🐍 Python: {platform.python_version()}
🤖 PTB: {__import__('telegram').__version__}
🌐 httpx: {__import__('httpx').__version__}
🌐 Proxy: {PROXY_URL}
🔐 SSL: 🔓 Desarrollo (VDI)
━━━━━━━━━━━━━━━━━━━━
🟢 Operativo
"""
    await update.message.reply_text(msg, parse_mode='Markdown')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    help_text = """
🤖 *Comandos OpenGravity*
━━━━━━━━━━━━━━━━━━━━━━
🔹 *Básicos*:
/start - Iniciar bot y verificar conexión
/status - Estado del sistema y configuración
/help - Mostrar esta ayuda

🧠 *IA General*:
/ai [pregunta] - Consulta general a la IA
/dev [tarea] - Genera código para una tarea
/explain [código] - Explica qué hace un código
/debug [error] - Ayuda a diagnosticar errores

📂 *Análisis de Código*:
/review [archivo] - Revisa un archivo y sugiere mejoras
/analyze [directorio] - Analiza todos los archivos de un directorio
/improve [archivo] - Reescribe el archivo con mejoras (crea backup)
/angular [directorio] - Análisis específico de proyecto Angular 🅰️

📚 *Conocimiento Corporativo*:
/context [acción] - Gestiona base de conocimiento
  • /context list - Ver documentos disponibles
  • /context reload - Recargar desde disco
  • /context search [term] - Buscar por palabra clave
/swagger [url_o_ruta] - Genera Angular desde OpenAPI/Swagger
/tests [ruta] - Genera frontend compatible con tests backend

🏗️ *Generación de Proyectos*:
/create [app] [desc] - Crea app Angular autónomamente
  • /create petstore-app "App para Petstore API"
  • /create my-app https://api.example.com/openapi.json

💡 *Ejemplos*:
• /ai ¿Qué es un DTO en Java?
• /dev crear función Python para validar email
• /angular C:/Users/.../mi-app-angular
• /context search interceptor
• /swagger https://api.corp.com/v1/openapi.json
• /tests C:/backend/src/auth

📝 *Notas*:
• Las respuestas pueden tardar 10-60 segundos
• Mensajes largos se dividen automáticamente
• Solo tu Chat ID puede analizar archivos

🔧 *Configuración*:
• Proxy SARA: ✅ Configurado
• SSL: 🔓 Desarrollo (VDI)
• Proveedor IA: Groq (gratis)
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')
    

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo de mensajes de texto - IGNORA comandos que empiecen con /"""
    if not update.message or not update.message.text:
        return
    
    # ⚠️ Ignorar mensajes que parezcan comandos (empiezan con /)
    if update.message.text.startswith("/"):
        return  # No responder, dejar que otros handlers lo procesen
    
    text = update.message.text[:200] + "..." if len(update.message.text) > 200 else update.message.text
    await update.message.reply_text(f"📩 {text}", parse_mode='Markdown')
    logger.info(f"Mensaje: {text[:80]}")

async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejo de comandos desconocidos"""
    if not update.message:
        return
    await update.message.reply_text("❓ Comando no reconocido. Usa /help")


# ============================================================
# CREACIÓN DE LA APLICACIÓN
# ============================================================

# opengravity_bot.py - En create_application(), reemplazar la sección de HTTPXRequest:

def create_application():
    """Crea la aplicación de Telegram con configuración resiliente"""
    
    # 🛡️ HTTPXRequest con timeouts y configuración de proxy robusta
    request = HTTPXRequest(
        connection_pool_size=20,
        connect_timeout=HTTP_CONNECT_TIMEOUT,
        read_timeout=HTTP_READ_TIMEOUT,
        write_timeout=HTTP_WRITE_TIMEOUT,
        pool_timeout=HTTP_POOL_TIMEOUT,
        # Proxy ya configurado vía monkey-patch + ENV vars
    )
    
    logger.info("✅ HTTPXRequest creado con timeouts configurados")

    # ✅ CORRECTO - Opción A: Sin configurar get_updates_request (hereda de .request)
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request)
        # ✅ get_updates_request heredará configuración de .request
        .build()
    )

    # ==============================
    # REGISTRO DE HANDLERS (ORDEN IMPORTANTE)
    # ==============================
    
    # 1️⃣ Handlers específicos de comandos (PRIORIDAD ALTA)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_cmd))

    # Handlers de IA
    app.add_handler(CommandHandler("ai", cmd_ai))
    app.add_handler(CommandHandler("dev", cmd_dev))
    app.add_handler(CommandHandler("explain", cmd_explain))
    app.add_handler(CommandHandler("debug", cmd_debug))
    app.add_handler(CommandHandler("review", cmd_review))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("improve", cmd_improve))
    app.add_handler(CommandHandler("angular", cmd_angular))
    
    # 🆕 Handlers de conocimiento corporativo
    app.add_handler(CommandHandler("context", cmd_context))
    app.add_handler(CommandHandler("swagger", cmd_swagger))
    app.add_handler(CommandHandler("tests", cmd_tests))
    app.add_handler(CommandHandler("create", cmd_create))

    app.add_handler(MessageHandler(filters.TEXT, echo))    
    app.add_handler(MessageHandler(filters.Regex(r"^/"), unknown_cmd))
    
        # 🛠️ DEBUG: Listar handlers registrados
    logger.info("📋 Handlers registrados:")
    for group, handlers in app.handlers.items():
        logger.info(f"  Grupo {group}:")
        for handler in handlers:
            cmd = getattr(handler, 'command', None)
            filters_info = getattr(handler, 'filters', None)
            logger.info(f"    - {type(handler).__name__}: command={cmd}, filters={filters_info}")
    
    return app


# opengravity_bot.py - Añadir esta función antes de run_bot_async:

async def run_with_retry(func, max_retries: int = POLLING_MAX_RETRIES, 
                         delay: float = POLLING_RETRY_DELAY, *args, **kwargs):
    """
    Ejecuta una función async con reintentos exponenciales.
    
    Args:
        func: Función async a ejecutar
        max_retries: Número máximo de reintentos
        delay: Delay base entre reintentos (segundos)
        *args, **kwargs: Argumentos para la función
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except (httpx.RemoteProtocolError, httpx.ConnectError, 
                httpx.ReadTimeout, httpx.WriteTimeout,
                ConnectionResetError, ConnectionRefusedError) as e:
            last_exception = e
            logger.warning(f"⚠️ Error de red (intento {attempt+1}/{max_retries+1}): {type(e).__name__}: {e}")
            
            if attempt < max_retries:
                # Exponential backoff: 5s, 10s, 20s, 40s...
                wait_time = delay * (2 ** attempt)
                logger.info(f"🔄 Reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Máximo de reintentos alcanzado. Último error: {e}")
                raise
    
    # Si llegamos aquí, todos los reintentos fallaron
    raise last_exception

# ============================================================
# FUNCIÓN ASÍNCRONA PRINCIPAL
# ============================================================

# opengravity_bot.py - Reemplazar run_bot_async completo:

async def run_bot_async():
    """Ejecuta el bot con resiliencia a errores de red y watchdog"""
    
    print("\n" + "="*70)
    print("🤖  OPENGRAVITY TELEGRAM BOT  🤖")
    print("="*70)
    print(f"🌐 Proxy: {PROXY_URL}")
    print(f"🔐 SSL: 🔓 Desarrollo (VDI controlada)")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🤖 PTB: {__import__('telegram').__version__}")
    print(f"🛡️ Resiliencia: {POLLING_MAX_RETRIES} retries, watchdog {WATCHDOG_TIMEOUT}s")
    print("="*70 + "\n")

    # Variable para el watchdog
    last_activity = asyncio.get_event_loop().time()
    
    async def on_update_wrapper(update, context):
        """Wrapper para trackear actividad del bot"""
        nonlocal last_activity
        last_activity = asyncio.get_event_loop().time()
        # Delegar al handler original de polling
        return await app.updater._Updater__process_update(update, context)
    
    app = create_application()
    
    print("✅ Bot inicializado. Envía /start desde Telegram para probar")
    print("🛑 Ctrl+C para detener\n")

    try:
        # Inicialización con retry
        await run_with_retry(app.initialize)
        await app.start()
        
        # Start polling con retry
        await run_with_retry(
            app.updater.start_polling,
            drop_pending_updates=True
        )
        
        print("🟢 Polling iniciado exitosamente")
        
        # Loop principal con watchdog
        while True:
            # Verificar watchdog: si no hay actividad, reiniciar polling
            current_time = asyncio.get_event_loop().time()
            if current_time - last_activity > WATCHDOG_TIMEOUT:
                logger.warning(f"⚠️ Watchdog: Sin actividad por {WATCHDOG_TIMEOUT}s. Reiniciando polling...")
                
                # Intentar reiniciar polling sin detener todo el bot
                try:
                    await app.updater.stop()
                    await asyncio.sleep(2)
                    await run_with_retry(
                        app.updater.start_polling,
                        drop_pending_updates=True
                    )
                    last_activity = current_time  # Reset watchdog
                    logger.info("✅ Polling reiniciado exitosamente")
                except Exception as e:
                    logger.error(f"❌ Error reiniciando polling: {e}")
                    # Si falla, dejar que el bot termine y se reinicie externamente
                    break
            
            await asyncio.sleep(30)  # Check cada 30 segundos
            
    except asyncio.CancelledError:
        logger.info("👋 Bot detenido por cancelación")
    except (httpx.RemoteProtocolError, httpx.ConnectError) as e:
        logger.error(f"❌ Error de red no recuperable: {e}")
        logger.info("💡 El bot se detuvo. Reinícialo manualmente o configura un supervisor.")
        raise
    except Exception as e:
        logger.critical(f"❌ Error crítico: {type(e).__name__}: {e}", exc_info=True)
        raise
    finally:
        # Cleanup ordenado
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            logger.info("✅ Bot shut down cleanly")
        except Exception as e:
            logger.error(f"⚠️ Error en shutdown: {e}")

def main():
    """Wrapper que usa asyncio.run() para crear el event loop correctamente"""
    try:
        asyncio.run(run_bot_async())
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por usuario")
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()