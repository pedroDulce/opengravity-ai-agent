# bot.py - K8s Bot con IA + Resiliencia mejorada
# ✅ Timeouts en todas las llamadas de red
# ✅ Manejo correcto de Ctrl+C en Windows
# ✅ Background task con timeout y error handling

import os
from screenshot_dashboard import tomar_screenshot_dashboard
import sys
import ssl
import warnings
import asyncio
import signal
from pathlib import Path
from dotenv import load_dotenv
from typing import Callable, Any
import logging
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from prometheus_client import start_http_server, Counter, Histogram
import plotly.express as px
import plotly.io as pio
from io import BytesIO

# ============================================================
# ⚠️ CONFIGURACIÓN CRÍTICA: ANTES DE CUALQUIER IMPORT DE RED
# ============================================================

# 1️⃣ Cargar .env PRIMERO
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    if not load_dotenv(dotenv_path=ENV_PATH):
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

# 2️⃣ Configurar proxy
PROXY_URL = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://proxycocs.redsara.es:8080"
os.environ["HTTP_PROXY"] = PROXY_URL
os.environ["HTTPS_PROXY"] = PROXY_URL
os.environ["ALL_PROXY"] = PROXY_URL
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.local"
print(f"🌐 Proxy configurado: {PROXY_URL}")

# 3️⃣ Configurar SSL
CERT_ENV = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
if CERT_ENV and Path(CERT_ENV).expanduser().resolve().exists():
    CERT_ABS = str(Path(CERT_ENV).expanduser().resolve())
    os.environ["SSL_CERT_FILE"] = CERT_ABS
    os.environ["REQUESTS_CA_BUNDLE"] = CERT_ABS
    print(f"✅ Certificado SSL: {CERT_ABS}")
else:
    print("⚠️ Certificado no definido - usando verify=False")

# 4️⃣ Patch global SSL
ssl._create_default_https_context = ssl._create_unverified_context
print("🔓 SSL global: verify desactivado")

# 5️⃣ Monkey-patch httpx con TIMEOUTS
print("🔧 Aplicando monkey-patch a httpx.AsyncClient...")
import httpx
_original_asyncclient_init = httpx.AsyncClient.__init__

def _patched_asyncclient_init(self, *args, **kwargs):
    kwargs["verify"] = False
    kwargs.pop("cert", None)
    # ⚠️ TIMEOUTS CRÍTICOS para evitar bloqueos
    kwargs.setdefault("timeout", httpx.Timeout(30.0, connect=10.0, read=60.0, write=10.0))
    return _original_asyncclient_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = _patched_asyncclient_init
print("✅ Monkey-patch aplicado con timeouts")

# 6️⃣ Patch asyncio para Windows + Python 3.14
if sys.platform == 'win32' and sys.version_info >= (3, 14):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("🔧 Patch asyncio para Windows aplicado")
    except Exception as e:
        print(f"⚠️ No se pudo aplicar patch asyncio: {e}")

# Suprimir warnings
urllib3 = __import__("urllib3")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# CONFIG Y LOGGING
# ============================================================
TOKEN = os.getenv("TELEGRAM_BOT_KUBERNETES_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_USER_CHAT_ID")

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
)
logger = logging.getLogger("k8s-bot")

# Métricas Prometheus
REQUEST_COUNT = Counter('bot_requests_total', 'Total bot requests', ['type'])
REQUEST_LATENCY = Histogram('bot_request_latency_seconds', 'Request latency', ['type'])
ERROR_COUNT = Counter('bot_errors_total', 'Total errors', ['type'])
start_http_server(8000)
logger.info("Prometheus metrics exposed on :8000/metrics")

# ============================================================
# CIRCUIT BREAKER (con timeout)
# ============================================================
class CircuitBreaker:
    def __init__(self, max_failures=3, reset_timeout=60, call_timeout=30):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.call_timeout = call_timeout  # ⚠️ Timeout para cada llamada
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
                logger.warning("🔄 Circuit breaker: intentando reconectar...")
            else:
                raise Exception("Circuit breaker OPEN - reintentando más tarde")

        try:
            # ⚠️ Timeout en la llamada para evitar bloqueos infinitos
            result = await asyncio.wait_for(
                func(*args, **kwargs), 
                timeout=self.call_timeout
            )
            self._on_success()
            return result
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout en llamada a {func.__name__}")
            self._on_failure()
            raise Exception(f"Timeout después de {self.call_timeout}s")
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
            logger.warning(f"🚫 Circuit breaker OPEN después de {self.failures} fallos")

# ============================================================
# IMPORTS EXTERNOS
# ============================================================
from k8s_checker import cargar_k8s, obtener_estado_pods
from openrouter_client import consultar_ia

v1 = cargar_k8s()
ia_cb = CircuitBreaker(call_timeout=30)  # ⚠️ Timeout de 30s por llamada a IA

# ============================================================
# HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    REQUEST_COUNT.labels("start").inc()
    logger.info(f"📩 /start de user_id={update.effective_user.id}")
    await update.message.reply_text("🤖 Bot K8s con IA activo. Usa /pods o /ia")

async def consultar_pods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    REQUEST_COUNT.labels("pods").inc()
    logger.info(f"📩 /pods de user_id={update.effective_user.id}")

    try:
        # 👇 Ahora usa el namespace del .env
        estado = obtener_estado_pods(v1)
        respuesta = await ia_cb.call(consultar_ia, f"Resume este estado:\n{estado}")
        await update.message.reply_text(respuesta)
        logger.info("✅ Respuesta de /pods enviada")
    except asyncio.TimeoutError:
        logger.error("⏰ Timeout consultando pods")
        await update.message.reply_text("⏰ Timeout: la IA tardó demasiado. Intenta de nuevo.")
    except Exception as e:
        ERROR_COUNT.labels("pods").inc()
        logger.error(f"❌ Error en /pods: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    finally:
        REQUEST_LATENCY.labels("pods").observe(time.time() - start_time)

async def pregunta_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = " ".join(context.args)
    if not pregunta:
        await update.message.reply_text("🤔 Escribe una pregunta. Ej: `/ia qué es un pod`")
        return
    
    REQUEST_COUNT.labels("ia").inc()
    start_time = time.time()
    logger.info(f"📩 /ia de user_id={update.effective_user.id}: '{pregunta[:50]}...'")
    
    try:
        contexto = obtener_estado_pods(v1)[:500]
        respuesta = await ia_cb.call(consultar_ia, f"{pregunta}\n\nContexto K8s: {contexto}")
        await update.message.reply_text(respuesta)
        logger.info("✅ Respuesta de /ia enviada")
    except asyncio.TimeoutError:
        logger.error("⏰ Timeout en consulta IA")
        await update.message.reply_text("⏰ La IA no respondió a tiempo. Intenta de nuevo.")
    except Exception as e:
        ERROR_COUNT.labels("ia").inc()
        logger.error(f"❌ Error en /ia: {str(e)}")
        await update.message.reply_text(f"❌ Error IA: {str(e)[:100]}")
    finally:
        REQUEST_LATENCY.labels("ia").observe(time.time() - start_time)

async def mensaje_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()
    palabras_k8s = ["pod", "pods", "estado", "kubernetes", "k8s", "clúster", "deploy"]
    
    REQUEST_COUNT.labels("message").inc()
    start_time = time.time()
    logger.info(f"📩 Mensaje de user_id={update.effective_user.id}: '{texto[:50]}...'")
    
    try:
        if any(p in texto for p in palabras_k8s):
            estado = obtener_estado_pods(v1)
            respuesta = await ia_cb.call(consultar_ia, f"Pregunta: {texto}\n\nDatos: {estado}")
        else:
            respuesta = await ia_cb.call(consultar_ia, texto)
        await update.message.reply_text(respuesta)
        logger.info("✅ Respuesta de mensaje enviada")
    except asyncio.TimeoutError:
        logger.error("⏰ Timeout procesando mensaje")
        await update.message.reply_text("⏰ Timeout procesando tu mensaje.")
    except Exception as e:
        ERROR_COUNT.labels("message").inc()
        logger.error(f"❌ Error en mensaje: {str(e)}")
        await update.message.reply_text("❌ Error procesando mensaje")
    finally:
        REQUEST_LATENCY.labels("message").observe(time.time() - start_time)

# ============================================================
# BACKGROUND TASK (con manejo seguro)
# ============================================================
async def chequeo_periodico(app: Application):
    logger.info("⏰ Tarea de chequeo iniciada (cada 10 min)")
    
    while True:
        try:
            await asyncio.sleep(600)  # 10 minutos
            logger.info("🔄 Ejecutando chequeo periódico...")
            
            estado = obtener_estado_pods(v1)
            
            if "ALERTA" in estado or "❌" in estado:
                logger.warning(f"⚠️ Problemas detectados")
                try:
                    informe = await asyncio.wait_for(
                        ia_cb.call(consultar_ia, f"Problemas detectados:\n{estado}"),
                        timeout=30
                    )
                    await app.bot.send_message(
                        chat_id=CHAT_ID, 
                        text=f"🚨 **ALERTA**\n\n{informe}",
                        parse_mode="Markdown",
                        request_timeout=30  # ⚠️ Timeout en el envío a Telegram
                    )
                    logger.info("✅ Alerta enviada")
                except asyncio.TimeoutError:
                    logger.error("⏰ Timeout enviando alerta")
            else:
                logger.info("✅ Chequeo: todos los pods Running")
                
        except asyncio.CancelledError:
            logger.info("🛑 Tarea de chequeo cancelada")
            break
        except Exception as e:
            logger.error(f"❌ Error en chequeo: {str(e)}", exc_info=True)
            ERROR_COUNT.labels("background").inc()
            await asyncio.sleep(60)  # Esperar antes de reintentar

# ============================================================
# MANEJO DE SEÑALES (Ctrl+C en Windows)
# ============================================================
def setup_signal_handlers(app: Application):
    """Configura manejo graceful de Ctrl+C"""
    if sys.platform == 'win32':
        # En Windows, usar signal.signal para SIGINT
        def handle_sigint(signum, frame):
            logger.info("🛑 Recibida señal SIGINT (Ctrl+C)")
            asyncio.create_task(graceful_shutdown(app))
        
        signal.signal(signal.SIGINT, handle_sigint)
        signal.signal(signal.SIGTERM, handle_sigint)

async def graceful_shutdown(app: Application):
    """Cierra el bot ordenadamente"""
    logger.info("🔄 Iniciando shutdown ordenado...")
    try:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("✅ Bot shut down cleanly")
    except Exception as e:
        logger.error(f"❌ Error en shutdown: {e}")
    finally:
        # Detener el event loop
        loop = asyncio.get_running_loop()
        loop.stop()

async def main_async():
    logger.info("🚀 Starting K8s Bot with IA...")

    app = Application.builder() \
        .token(TOKEN) \
        .job_queue(None) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pods", consultar_pods))
    app.add_handler(CommandHandler("ia", pregunta_ia))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))    
    app.add_handler(CommandHandler("foto", cmd_foto_dashboard))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("grafico", cmd_grafico))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_normal))

    # Configurar señales ANTES de iniciar
    setup_signal_handlers(app)

    # ✅ Inicialización correcta del bot
    await app.initialize()
    await app.start()
    
    # ✅ ESTO FALTABA: Iniciar polling para recibir mensajes de Telegram
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info("✅ Polling iniciado. Bot escuchando mensajes...")
    
    # Iniciar tarea de fondo
    background_task = asyncio.create_task(chequeo_periodico(app))
    logger.info("✅ Bot running. Waiting for messages...")

    try:
        # Esperar indefinidamente, pero permitiendo interrupción
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("👋 Main task cancelled")
    finally:
        # Cleanup ordenado
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
        # Detener polling y shutdown
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        logger.info("✅ Bot shut down cleanly")

if __name__ == '__main__':
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by Ctrl+C")
    except Exception as e:
        logger.critical(f"❌ Error crítico: {e}", exc_info=True)
        sys.exit(1)


async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el link al dashboard web"""
    dashboard_url = "http://10.1.147.41:8501"
    
    msg = f"""
📊 **Dashboard Kubernetes**

Accede al dashboard interactivo desde tu navegador:

🔗 {dashboard_url}

**Características:**
✅ Métricas en tiempo real
✅ Gráficos interactivos
✅ Filtros por estado
✅ Auto-refresh cada 30s

⚠️ *Solo accesible desde la red corporativa*
"""
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_foto_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía una foto del dashboard"""
    mensaje = await update.message.reply_text("📸 Tomando captura del dashboard...")
    
    try:
        # Tomar screenshot
        tomar_screenshot_dashboard(
            url="http://localhost:8501",
            output="dashboard_temp.png"
        )
        
        # Enviar como foto
        with open("dashboard_temp.png", "rb") as foto:
            await update.message.reply_photo(
                photo=foto,
                caption="📊 **Dashboard Kubernetes**\n\nCaptura en tiempo real del estado del clúster."
            )
        
        await mensaje.delete()
        
        # Limpiar archivo temporal
        os.remove("dashboard_temp.png")
        
    except Exception as e:
        await mensaje.edit_text(f"❌ Error tomando screenshot: {str(e)}")


async def cmd_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía un reporte visual del estado del clúster"""
    logger.info(f"📩 /reporte de user_id={update.effective_user.id}")
    
    try:
        # Obtener datos
        estado = obtener_estado_pods(v1)
        datos = obtener_datos_cluster(K8S_NAMESPACE)
        
        if not datos:
            await update.message.reply_text("❌ Error obteniendo datos")
            return
        
        pods_df = datos["pods"]
        
        # Calcular métricas
        total = len(pods_df)
        running = len(pods_df[pods_df["Estado"] == "Running"])
        pending = len(pods_df[pods_df["Estado"] == "Pending"])
        error = total - running - pending
        
        salud = (running / total * 100) if total > 0 else 0
        
        # Crear barra de progreso visual
        barra_len = 10
        running_bars = int((running / total) * barra_len) if total > 0 else 0
        barra = "🟩" * running_bars + "⬜" * (barra_len - running_bars)
        
        # Top 5 pods por edad
        pods_df["Edad"] = pd.to_datetime(pods_df["Edad"], errors='coerce')
        pods_ordenados = pods_df.sort_values("Edad", ascending=True)
        
        reporte = f"""
📊 **REPORTE KUBERNETES - {K8S_NAMESPACE}**
{'='*40}

📈 **SALUD DEL CLÚSTER**

{barra} {salud:.1f}%

 Total Pods: {total}
🟩 Running: {running}
🟨 Pending: {pending}
🟥 Error: {error}

🔄 Reinicios totales: {pods_df['Reinicios'].sum()}

🚀 **TOP 5 PODS MÁS ANTIGUOS**

"""
        for i, (_, pod) in enumerate(pods_ordenados.head(5).iterrows(), 1):
            edad_str = str(pod["Edad"]).split(" ")[0] if pd.notna(pod["Edad"]) else "N/A"
            reporte += f"{i}. `{pod['Nombre']}` - {edad_str}\n"
        
        reporte += f"""

📁 **Distribución por Node**

"""
        for node, count in pods_df["Node"].value_counts().head(3).items():
            reporte += f"• {node.split('-')[0]}: {count} pods\n"
        
        reporte += f"""

🕐 *Actualizado: {datetime.now().strftime('%H:%M:%S')}*

💡 Usa `/dashboard` para ver el dashboard completo
"""
        
        await update.message.reply_text(reporte, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Error en /reporte: {str(e)}")
        await update.message.reply_text(f"❌ Error generando reporte: {str(e)[:100]}")


async def cmd_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía un gráfico de estado de pods"""
    logger.info(f"📩 /grafico de user_id={update.effective_user.id}")
    
    try:
        mensaje = await update.message.reply_text("📊 Generando gráfico...")
        
        datos = obtener_datos_cluster(K8S_NAMESPACE)
        if not datos:
            await mensaje.edit_text("❌ Error obteniendo datos")
            return
        
        pods_df = datos["pods"]
        
        # Crear gráfico de pastel
        estado_counts = pods_df["Estado"].value_counts().reset_index()
        estado_counts.columns = ["Estado", "Cantidad"]
        
        fig = px.pie(
            estado_counts,
            values="Cantidad",
            names="Estado",
            title=f"Pods en namespace '{K8S_NAMESPACE}'",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4
        )
        
        # Convertir a imagen PNG
        img_bytes = BytesIO()
        fig.write_image(img_bytes, format="png", width=800, height=600, scale=2)
        img_bytes.seek(0)
        
        # Enviar como foto
        await update.message.reply_photo(
            photo=img_bytes,
            caption=f"📊 **Estado de Pods - {K8S_NAMESPACE}**\n\nTotal: {len(pods_df)} pods"
        )
        
        await mensaje.delete()
        
    except Exception as e:
        logger.error(f"❌ Error en /grafico: {str(e)}")
        await mensaje.edit_text(f"❌ Error generando gráfico: {str(e)[:100]}")
