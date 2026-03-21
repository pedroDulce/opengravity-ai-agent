# ===========================================
# IMPORTS
# ===========================================
import os
import tempfile
import sys
import ssl
import warnings
import asyncio
import signal
import re  # Para escape de Markdown si lo necesitas
import logging
import time
import json
# HTTP y SSL
import httpx
import urllib3
# Pandas y Plotly (para /resumen y /grafico)
import pandas as pd
import plotly.express as px

# Imports de librerias externas
from io import BytesIO
from datetime import datetime
from typing import Callable, Any
from pathlib import Path
from dotenv import load_dotenv

# Kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Prometheus
from prometheus_client import start_http_server, Counter, Histogram

# Importar el agente
from k8s_agent import agente_k8s
from k8s_tools import TOOLS_REGISTRY

# Circuit breaker
from typing import Callable, Any

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
K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "atom")
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


# ============================================================
# 🎨 FORMATEADORES DE RESPUESTAS ESPECIALIZADAS
# ============================================================
def formatear_httpproxies(datos):
    """
    Formatea datos de HTTPProxy/Ingress para respuesta legible en Telegram
    Maneja errores de permisos (403) y datos None
    """
    # Validar entrada
    if datos is None:
        return "⚠️ No se obtuvieron datos de enrutamiento."
    
    # Si es un error de API (dict con 'error')
    if isinstance(datos, dict) and "error" in datos:
        error_msg = datos.get("error", "Error desconocido")
        
        # 👇 Detectar error 403 de permisos y dar mensaje útil
        if "403" in error_msg or "Forbidden" in error_msg or "forbidden" in error_msg.lower():
            return (
                "⚠️ **Sin permisos para consultar HTTPProxy**\n\n"
                "El ServiceAccount actual no tiene acceso a recursos `httpproxies.projectcontour.io`.\n\n"
                "🔧 **Opciones:**\n"
                "1. Pedir al equipo de plataforma permisos para listar HTTPProxy\n"
                "2. Usar Ingress nativo: `kubectl get ingress -n atom`\n"
                "3. Consultar manualmente: `kubectl get httpproxy -n atom` (si tienes acceso)\n\n"
                f"💡 Hint: {datos.get('hint', '')}"
            )
        
        # Otros errores
        return f"⚠️ {error_msg}\n\n💡 {datos.get('hint', 'Verifica que el recurso está instalado en el clúster.')}"
    
    # Si no hay datos (lista vacía)
    if not datos or (isinstance(datos, list) and len(datos) == 0):
        return "✅ No hay reglas de enrutamiento configuradas en este namespace."
    
    # Determinar tipo de recurso
    es_httpproxy = isinstance(datos, list) and len(datos) > 0 and datos[0].get('virtualhost') is not None
    tipo = "HTTPProxy" if es_httpproxy else "Ingress"
    emoji = "🌐" if es_httpproxy else "🔗"
    
    respuesta = f"{emoji} **Reglas de Enrutamiento {tipo}**\n\n"
    
    for item in datos:
        if not isinstance(item, dict):
            continue  # Saltar items inválidos
            
        nombre = item.get('name', 'desconocido')
        respuesta += f"📋 **{nombre}**\n"
        
        # Host/FQDN
        host = item.get('virtualhost') or item.get('host')
        if host:
            respuesta += f"• 🌍 Host: `{host}`\n"
        
        # Descripción (solo HTTPProxy)
        if item.get('description'):
            respuesta += f"• 📝 {item['description']}\n"
        
        # Rutas
        if item.get('routes') and isinstance(item['routes'], list):
            respuesta += "• 🛣️ Rutas:\n"
            for route in item['routes']:
                if isinstance(route, dict):
                    # HTTPProxy format
                    if 'conditions' in route:
                        prefixes = ", ".join(str(c) for c in route.get('conditions', ['/*']) if c)
                        services = ", ".join(str(s) for s in route.get('services', []) if s)
                        respuesta += f"  - `{prefixes}` → {services}\n"
                    # Ingress format
                    elif 'paths' in route:
                        host_r = route.get('host', '*')
                        for path in route.get('paths', []):
                            if isinstance(path, dict):
                                p = path.get('path', '/')
                                svc = path.get('service', 'unknown')
                                respuesta += f"  - `{host_r}{p}` → {svc}\n"
        
        # Estado (solo HTTPProxy)
        if item.get('status'):
            estado_icon = "✅" if str(item['status']).lower() == 'valid' else "⚠️"
            respuesta += f"• {estado_icon} Estado: `{item['status']}`\n"
        
        # TLS (solo Ingress)
        if item.get('tls'):
            tls_data = item['tls']
            if isinstance(tls_data, list) and len(tls_data) > 0:
                tls_hosts = tls_data[0] if isinstance(tls_data[0], str) else ", ".join(str(t) for t in tls_data[0])
                respuesta += f"• 🔐 TLS: `{tls_hosts}`\n"
        
        # Edad
        if item.get('age'):
            respuesta += f"• 🕐 Creado: `{item['age']}`\n"
        
        respuesta += "\n"
    
    # Resumen final
    total = len(datos) if isinstance(datos, list) else 1
    respuesta += f"💡 Total: **{total}** regla(s) de enrutamiento en namespace `{K8S_NAMESPACE}`"
    
    return respuesta.strip()

async def _enviar_mensaje_seguro(message, texto, parse_mode="Markdown"):
    """
    Envía mensaje con fallback automático si Markdown falla
    Maneja casos donde texto es None, vacío o no-string
    """
    # 👇 VALIDAR texto ANTES de usarlo (CRÍTICO)
    if texto is None:
        texto = "⚠️ No se pudo generar una respuesta."
    elif not isinstance(texto, str):
        texto = str(texto)
    
    texto = texto.strip()
    if not texto:
        texto = "✅ Petición procesada (sin contenido para mostrar)."
    
    try:
        await message.edit_text(texto, parse_mode=parse_mode)
    except Exception as e:
        logger.warning(f"⚠️ Error parseando {parse_mode}: {str(e)[:100]}")
        try:
            # Fallback a HTML (con validación de texto)
            texto_html = str(texto).replace('*', '<b>').replace('*', '</b>')
            texto_html = texto_html.replace('`', '<code>').replace('`', '</code>')
            texto_html = texto_html.replace('_', '<i>').replace('_', '</i>')
            await message.edit_text(texto_html, parse_mode="HTML")
        except Exception as e2:
            logger.warning(f"⚠️ Error con HTML fallback: {str(e2)[:100]}")
            # Fallback final: texto plano (con validación)
            texto_limpio = str(texto).replace('*', '').replace('`', '').replace('_', '').replace('[', '').replace(']', '')
            await message.edit_text(f"⚠️ Error de formato:\n\n{texto_limpio[:3500]}")



# ===========================================
# 🤖 HANDLER DE LENGUAJE NATURAL
# ===========================================

async def mensaje_natural_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa mensajes en lenguaje natural y ejecuta acciones con IA
    """
    texto = update.message.text
    logger.info(f"📩 Mensaje natural de user_id={update.effective_user.id}: '{texto[:100]}...'")
    
    # Mensaje inmediato
    mensaje = await update.message.reply_text(
        "🤔 **Analizando tu petición...**\n\n⏳ Un momento."
    )
    
    try:
        # 1. Consultar al agente de IA para obtener el plan
        plan = await agente_k8s(texto)
        logger.debug(f"🧠 Plan recibido: {plan}")
        
        # 2. Si es respuesta directa, enviarla inmediatamente
        if plan.get("action") == "respond_directly":
            respuesta = plan.get("response", "⚠️ No entendí tu petición")
            await mensaje.edit_text(respuesta, parse_mode="Markdown")
            return
        
        # 3. Si requiere confirmación, pedir al usuario
        if plan.get("requires_confirmation", False):
            herramientas = plan.get("tools", [])
            explicacion = plan.get("explanation", "")
            
            confirm_msg = f"⚠️ **CONFIRMACIÓN REQUERIDA**\n\n"
            confirm_msg += f"{explicacion}\n\n"
            confirm_msg += f"**Acciones:**\n"
            for h in herramientas:
                confirm_msg += f"• `{h['name']}` con parámetros: `{json.dumps(h['parameters'])}`\n"
            confirm_msg += f"\n✅ Para confirmar, responde: `sí` o `confirmar`"
            
            await mensaje.edit_text(confirm_msg, parse_mode="Markdown")
            context.user_data['pending_action'] = plan
            return
        
                # 4. Ejecutar herramientas directamente
        resultados = []
        for herramienta in plan.get("tools", []):
            nombre = herramienta.get("name")
            params = herramienta.get("parameters", {})
            
            logger.info(f"🔧 Ejecutando herramienta: {nombre} con params: {params}")
            
            if nombre in TOOLS_REGISTRY:
                try:
                    func = TOOLS_REGISTRY[nombre]["function"]
                    resultado = func(**params)
                    
                    # 👇 FORMATEO ESPECIAL para httpproxies/ingresses
                    if nombre in ["get_httpproxies", "get_ingresses"]:
                        resultado_formateado = formatear_httpproxies(resultado)
                        resultados.append({
                            "herramienta": nombre,
                            "exitoso": True,
                            "datos": resultado,  # Datos crudos para IA
                            "texto_formateado": resultado_formateado  # Texto listo para mostrar
                        })
                    else:
                        resultados.append({
                            "herramienta": nombre,
                            "exitoso": True,
                            "datos": resultado
                        })
                    logger.debug(f"✅ Herramienta {nombre} ejecutada correctamente")
                except Exception as e:
                    logger.error(f"❌ Error ejecutando {nombre}: {str(e)}")
                    resultados.append({
                        "herramienta": nombre,
                        "exitoso": False,
                        "error": str(e)
                    })
            else:
                logger.warning(f"⚠️ Herramienta desconocida: {nombre}")
                resultados.append({
                    "herramienta": nombre,
                    "exitoso": False,
                    "error": f"Herramienta '{nombre}' no registrada"
                })
        
        # 5. Preparar contexto para la respuesta final
        contexto_resultados = json.dumps(resultados, indent=2, default=str, ensure_ascii=False)[:3000]
        logger.debug(f"📦 Resultados para formatear: {contexto_resultados[:500]}...")
        
        # 👇 DETECTAR si hay resultados formateados de httpproxies/ingresses
        resultado_formateado_directo = None
        for r in resultados:
            if r.get("exitoso") and "texto_formateado" in r:
                resultado_formateado_directo = r["texto_formateado"]
                break
        
        # 6. Pedir a la IA que formatee la respuesta FINAL
        prompt_final = f"""
Eres un asistente que debe responder en formato JSON con action: "respond_directly".

El usuario preguntó originalmente: "{texto}"

Ejecuté herramientas de Kubernetes y obtuve estos resultados:
{contexto_resultados}

Tu tarea: Generar una respuesta CLARA y ÚTIL en español basada en esos resultados.

REGLAS:
1. DEBES responder con action: "respond_directly"
2. Incluye la respuesta en el campo "response"
3. Usa formato markdown SIMPLE: *negrita*, `código`, - listas
4. Incluye emojis para hacerlo más legible
5. Sé conciso pero completo (máximo 400 palabras)
6. Si los resultados muestran errores, menciónalos claramente
7. Si no hay datos, dilo honestamente
8. NO uses underscores (_) en nombres, usa guiones (-)
9. Cierra SIEMPRE los formatos de markdown (* abre y * cierra)

Responde SOLO con JSON válido, sin markdown ni texto extra.

Ejemplo de respuesta esperada:
{{
    "action": "respond_directly",
    "response": "📊 **Recursos de Adminer**\\n\\n• Memoria: 256Mi\\n• CPU: 100m\\n...",
    "requires_confirmation": false,
    "explanation": ""
}}
"""
        
        respuesta_final = await agente_k8s(prompt_final)
        logger.debug(f"🧠 Respuesta final recibida: {respuesta_final}")
        
        # 7. Extraer y mostrar la respuesta
        if respuesta_final.get("action") == "respond_directly":
            respuesta_texto = respuesta_final.get("response", "✅ Petición procesada")
            
            # 👇 Si tenemos resultado formateado de httpproxies, USARLO directamente
            if resultado_formateado_directo and "HTTPProxy" in texto or "Ingress" in texto or "enrutamiento" in texto.lower():
                respuesta_texto = resultado_formateado_directo
            
            await _enviar_mensaje_seguro(mensaje, respuesta_texto)
        else:
            # Fallback: intentar extraer respuesta de cualquier campo
            respuesta_texto = (
                respuesta_final.get("response") or 
                respuesta_final.get("explanation") or
                json.dumps(respuesta_final, indent=2, ensure_ascii=False)[:500]
            )
            
            # 👇 Mismo fallback para httpproxies
            if resultado_formateado_directo and not respuesta_texto:
                respuesta_texto = resultado_formateado_directo
            
            if respuesta_texto and respuesta_texto != "✅ Petición completada":
                await _enviar_mensaje_seguro(mensaje, respuesta_texto)
            else:
                # Último fallback: mostrar resultados crudos
                resumen = f"✅ **Petición procesada**\n\n"
                resumen += f"**Herramientas ejecutadas:** {len(resultados)}\n"
                for r in resultados:
                    estado = "✅" if r.get("exitoso") else "❌"
                    resumen += f"{estado} `{r['herramienta']}`\n"
                resumen += f"\n💡 Usa `/reporte` para ver detalles completos."
                await _enviar_mensaje_seguro(mensaje, resumen)
                
    except Exception as e:
        logger.error(f"❌ Error en mensaje natural: {str(e)}", exc_info=True)
        await mensaje.edit_text(f"❌ Error procesando tu petición: {str(e)[:200]}")


# Handler para confirmaciones
async def confirmar_accion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa confirmaciones del usuario"""
    texto = update.message.text.lower()
    
    if texto in ["sí", "si", "confirmar", "yes", "confirm"]:
        if 'pending_action' in context.user_data:
            plan = context.user_data['pending_action']
            
            # Ejecutar herramientas
            for herramienta in plan.get("tools", []):
                nombre = herramienta.get("name")
                params = herramienta.get("parameters", {})
                
                if nombre in TOOLS_REGISTRY:
                    func = TOOLS_REGISTRY[nombre]["function"]
                    try:
                        resultado = func(**params)
                        await update.message.reply_text(f"✅ {resultado}")
                    except Exception as e:
                        await update.message.reply_text(f"❌ Error: {str(e)}")
            
            del context.user_data['pending_action']
        else:
            await update.message.reply_text("⚠️ No hay acciones pendientes")
    else:
        await update.message.reply_text("❌ Acción cancelada")
        if 'pending_action' in context.user_data:
            del context.user_data['pending_action']

# ============================================================
# 📊 FUNCIÓN PARA OBTENER DATOS DEL CLÚSTER
# ============================================================

def obtener_datos_cluster(namespace=None):
    """
    Obtiene todos los datos del clúster (pods, deployments, services)
    Retorna un diccionario con DataFrames de pandas
    """
    if not v1:
        logger.error("❌ No hay conexión a Kubernetes")
        return None
    
    # Si no se especifica namespace, usar el del .env
    if not namespace:
        namespace = K8S_NAMESPACE
    
    try:
        logger.info(f"🔍 Obteniendo datos del namespace: {namespace}")
        
        # ========== PODS ==========
        pods = v1.list_namespaced_pod(namespace=namespace)
        pods_data = []
        
        for pod in pods.items:
            containers_ready = 0
            containers_total = len(pod.status.container_statuses or [])
            
            for cs in (pod.status.container_statuses or []):
                if cs.ready:
                    containers_ready += 1
            
            pods_data.append({
                "Nombre": pod.metadata.name,
                "Namespace": pod.metadata.namespace,
                "Estado": pod.status.phase,
                "IP": pod.status.pod_ip or "N/A",
                "Node": pod.spec.node_name or "N/A",
                "Containers": f"{containers_ready}/{containers_total}",
                "Reinicios": sum(cs.restart_count for cs in (pod.status.container_statuses or [])),
                "Edad": str(pod.metadata.creation_timestamp).split("+")[0] if pod.metadata.creation_timestamp else "N/A"
            })
        
        # ========== DEPLOYMENTS ==========
        try:
            apps_v1 = client.AppsV1Api()
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
            deployments_data = []
            
            for dep in deployments.items:
                deployments_data.append({
                    "Nombre": dep.metadata.name,
                    "Disponibles": dep.status.available_replicas or 0,
                    "Listos": dep.status.ready_replicas or 0,
                    "Deseados": dep.spec.replicas or 0
                })
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron obtener deployments: {e}")
            deployments_data = []
        
        # ========== SERVICES ==========
        services = v1.list_namespaced_service(namespace=namespace)
        services_data = []
        
        for svc in services.items:
            services_data.append({
                "Nombre": svc.metadata.name,
                "Tipo": svc.spec.type,
                "Cluster IP": svc.spec.cluster_ip,
                "Puertos": ", ".join([f"{p.port}/{p.protocol}" for p in svc.spec.ports]) if svc.spec.ports else "N/A"
            })
        
        # Convertir a DataFrames
        import pandas as pd
        
        return {
            "pods": pd.DataFrame(pods_data),
            "deployments": pd.DataFrame(deployments_data),
            "services": pd.DataFrame(services_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos del clúster: {str(e)}")
        return None

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
    msg = (
    "🤖 *Bot K8s con IA activo*\n\n"
        "🧠 *Consultas generales*\n"
        "• `/ia <pregunta>` — Pregunta anything sobre Kubernetes\n\n"
        "📊 *Monitoreo de Tanzu Kubernetes entorno Integración*\n"
        "• `/pods` — Estado de todos los pods\n"
        "• `/resumen` — Informe visual resumido con emojis\n"
        "• `/dashboard` — Link al dashboard web interactivo\n"        
        "🔧 *Gestión avanzada*\n"
        "• `/logs <pod>` — Ver logs de un pod\n"
        "• `/describe <pod>` — Detalles técnicos completos\n"
        "• `/restart <pod>` — Reiniciar un pod (con confirmación)\n\n"
        f"📁 *Namespace:* `{K8S_NAMESPACE}` | 🕐 *Actualizado:* `{datetime.now().strftime('%H:%M')}`"    
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def consultar_pods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consulta manual de pods"""
    logger.info(f"📩 /pods de user_id={update.effective_user.id}")
    
    # 👇 LÍNEA NUEVA 1: Mensaje inmediato
    mensaje = await update.message.reply_text(
        f"🔍 **Consultando pods del namespace `{K8S_NAMESPACE}`...**\n\n"
        f"⏳ Un momento, por favor."
    )
    
    try:
        estado = obtener_estado_pods(v1)
        respuesta = await ia_cb.call(consultar_ia, f"Resume este estado:\n{estado}")
        
        # 👇 Enviar respuesta final
        await update.message.reply_text(respuesta)
        
        # Borrar mensaje de "Consultando..."
        await mensaje.delete()
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
# 🚨 CHEQUEO PERIÓDICO DE ALERTAS (PRODUCCIÓN)
# ============================================================
async def chequeo_periodico(app: Application):
    """
    Monitorea el namespace 'atom' cada 10 minutos
    Envía alerta solo si detecta pods NO-Running
    """
    logger.info("⏰ Tarea de chequeo iniciada (cada 10 min)")
    
    # Contador para evitar spam de alertas repetidas
    ultima_alerta_enviada = None
    
    while True:
        try:
            # Esperar 1 minuto (600 segundos)
            await asyncio.sleep(600)
            
            logger.info("🔄 Ejecutando chequeo periódico del clúster...")
            
            # Obtener estado real de los pods
            estado = obtener_estado_pods(v1)
            datos = obtener_datos_cluster(K8S_NAMESPACE)
            
            if not datos:
                logger.warning("⚠️ No se pudieron obtener datos del clúster")
                continue
            
            pods_df = datos["pods"]
            
            # Filtrar pods con problemas
            pods_problema = pods_df[pods_df["Estado"] != "Running"]
            
            if len(pods_problema) > 0:
                # 🚨 HAY PROBLEMAS - Enviar alerta
                logger.warning(f"⚠️ {len(pods_problema)} pods con problemas detectados")
                
                # Construir lista de pods problemáticos
                lista_pods = ""
                for _, pod in pods_problema.iterrows():
                    lista_pods += f"\n📦 `{pod['Namespace']}/{pod['Nombre']}`"
                    lista_pods += f"\n   ❌ Estado: **{pod['Estado']}**"
                    lista_pods += f"\n   🔄 Reinicios: {pod['Reinicios']}"
                    lista_pods += f"\n   🌐 Node: `{pod['Node']}`\n"
                
                # Mensaje de alerta principal
                alerta = f"""
🚨 **ALERTA KUBERNETES - {K8S_NAMESPACE}**

⚠️ Se detectaron **{len(pods_problema)} pod(s)** con problemas:

{lista_pods}

🕐 **Detectado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **Salud del clúster:** {len(pods_df[pods_df['Estado']=='Running'])}/{len(pods_df)} Running

---

💡 Usa `/resumen` para ver estado completo
📊 Usa `/dashboard` para dashboard interactivo
"""
                
                # Enviar alerta por Telegram
                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=alerta,
                    parse_mode="Markdown"
                )
                logger.info("✅ Alerta enviada por Telegram")
                
                # Esperar 10 segundos y enviar análisis de IA
                await asyncio.sleep(10)
                
                # Preparar contexto para IA
                pods_problematicos_text = "\n".join([
                    f"- {row['Nombre']} ({row['Estado']}) - Reinicios: {row['Reinicios']}"
                    for _, row in pods_problema.iterrows()
                ])
                
                contexto_ia = f"""
Problema detectado en Kubernetes namespace '{K8S_NAMESPACE}':

Pods con problemas:
{pods_problematicos_text}

Total pods: {len(pods_df)}
Pods Running: {len(pods_df[pods_df['Estado']=='Running'])}
Pods con error: {len(pods_problema)}

Genera un informe técnico BREVE con:
1. Qué significan estos estados (CrashLoopBackOff, Pending, Error, etc.)
2. Posibles causas más probables
3. Comandos kubectl específicos para diagnosticar (con namespace '{K8S_NAMESPACE}')
4. Acciones recomendadas prioritarias

Sé conciso y práctico. Máximo 300 palabras.
"""
                
                try:
                    informe_ia = await consultar_ia(contexto_ia)
                    
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"🔍 **ANÁLISIS IA:**\n\n{informe_ia}",
                        parse_mode="Markdown"
                    )
                    logger.info("✅ Informe IA enviado")
                    
                except Exception as ia_error:
                    logger.error(f"⚠️ Error obteniendo análisis IA: {ia_error}")
                    # Continuar aunque la IA falle
                
            else:
                # ✅ TODO OK - No enviar nada (no spamear)
                logger.info("✅ Chequeo completado: todos los pods Running")
            
        except asyncio.CancelledError:
            logger.info("🛑 Tarea de chequeo cancelada")
            break
        except Exception as e:
            logger.error(f"❌ Error en chequeo periódico: {str(e)}", exc_info=True)
            await asyncio.sleep(60)  # Esperar antes de reintentar

# ============================================================
# 🧪 ALERTA DE PRUEBA (TEMPORAL - Para testing)
# ============================================================
async def alerta_prueba_xxs(app: Application):
    """
    ⚠️ FUNCIÓN TEMPORAL PARA TESTING
    Simula un fallo de pod después de xx segundos
    """
    logger.info("⏰ [TEST] Esperando xx segundos para alerta de prueba...")
    
    await asyncio.sleep(20)  # Esperar 20 segundos
    
    logger.info("🧪 [TEST] Generando alerta de prueba...")
    
    # Simular un pod caído
    pod_falso = {
        "namespace": "atom",
        "nombre": "mi-app-backend-deployment-abc123-xyz",
        "estado": "CrashLoopBackOff",
        "mensaje": "Back-off restarting failed container"
    }
    
    # Crear mensaje de alerta simulado
    alerta_simulada = f"""
🚨 **ALERTA DE PRUEBA - POD CAÍDO**

⚠️ Se ha detectado un problema en el clúster:

📦 **Pod:** `{pod_falso['namespace']}/{pod_falso['nombre']}`
❌ **Estado:** {pod_falso['estado']}
📝 **Mensaje:** {pod_falso['mensaje']}

🕐 **Detectado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

⚙️ *Esta es una alerta de prueba para verificar el sistema de notificaciones.*
🔧 *El pod '{pod_falso['nombre']}' NO existe realmente.*
"""
    
    try:
        # Enviar alerta por Telegram
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text=alerta_simulada,
            parse_mode="Markdown"
        )
        logger.info("✅ [TEST] Alerta de prueba enviada correctamente")
        
        # Esperar 5 segundos y enviar segunda alerta con IA
        await asyncio.sleep(5)
        
        # Usar IA para formatear un informe más detallado
        contexto_ia = f"""
Problema detectado en Kubernetes:
- Pod: {pod_falso['nombre']}
- Namespace: {pod_falso['namespace']}
- Estado: {pod_falso['estado']}
- Error: {pod_falso['mensaje']}

Genera un informe técnico breve con:
1. Qué significa este error
2. Posibles causas
3. Acciones recomendadas
"""
        
        informe_ia = await consultar_ia(contexto_ia)
        
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🔍 **ANÁLISIS IA DEL PROBLEMA:**\n\n{informe_ia}",
            parse_mode="Markdown"
        )
        logger.info("✅ [TEST] Informe IA enviado")
        
    except Exception as e:
        logger.error(f"❌ [TEST] Error enviando alerta: {e}")

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


async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía un resumen visual del estado del clúster de Tanzu Integración"""
    logger.info(f"📩 /resumen de user_id={update.effective_user.id}")

    mensaje = await update.message.reply_text("⏳ **Generando resumen del clúster Tanzu Integración...**\n\n📊 Un momento por favor.")
    
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
        
        resumen = f"""
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
            resumen += f"{i}. `{pod['Nombre']}` - {edad_str}\n"
        
        resumen += f"""

📁 **Distribución por Node**

"""
        for node, count in pods_df["Node"].value_counts().head(3).items():
            resumen += f"• {node.split('-')[0]}: {count} pods\n"
        
        resumen += f"""

🕐 *Actualizado: {datetime.now().strftime('%H:%M:%S')}*

💡 Usa `/dashboard` para ver el dashboard completo
"""        
        await update.message.reply_text(resumen, parse_mode="Markdown")
        
        await mensaje.delete()
        
    except Exception as e:
        logger.error(f"❌ Error en /resumen: {str(e)}")
        await update.message.reply_text(f"❌ Error generando resumen: {str(e)[:100]}")


async def cmd_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía un gráfico simple del estado de pods"""
    logger.info(f"📩 /grafico de user_id={update.effective_user.id}")
    
    try:
        mensaje = await update.message.reply_text("📊 Generando gráfico...")

        datos = obtener_datos_cluster(K8S_NAMESPACE)
        if not datos:
            await mensaje.edit_text("❌ Error obteniendo datos")
            return
        
        pods_df = datos["pods"]
        
        # Contar pods por estado
        estado_counts = pods_df["Estado"].value_counts()
        
        # Crear gráfico de barras simple con Plotly
        fig = px.bar(
            x=estado_counts.index.tolist(),
            y=estado_counts.values.tolist(),
            title=f"📦 Pods en '{K8S_NAMESPACE}'",
            labels={"x": "Estado", "y": "Cantidad"},
            color=estado_counts.index.tolist(),
            color_discrete_map={
                "Running": "#28a745",
                "Pending": "#ffc107",
                "Failed": "#dc3545",
                "Unknown": "#6c757d"
            },
            width=600,
            height=400
        )
        
        # Mejorar el diseño
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(size=14),
            title_font_size=18
        )
        
        # En cmd_grafico, reemplaza el bloque try/except de exportación con:

        try:
            # Método 1: Intentar con to_image (más rápido)
            img_bytes = fig.to_image(format="png", width=600, height=400, scale=2)
            
        except Exception as e:
            logger.warning(f"⚠️ to_image falló: {e}, intentando write_image...")
            
            # Método 2: write_image (más lento pero más estable)            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                fig.write_image(tmp_path, width=600, height=400, scale=2)
                
                with open(tmp_path, "rb") as f:
                    img_bytes = f.read()
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        # Enviar la imagen
        await update.message.reply_photo(
            photo=BytesIO(img_bytes),
            caption=f"📊 **Estado de Pods**\n\nTotal: {len(pods_df)}\n🟩 Running: {running}"
        )

    except Exception as e:
        logger.error(f"❌ Error en /grafico: {str(e)}")
        await mensaje.edit_text(f"❌ Error: {str(e)[:100]}")


#================================================
#/restart <pod> --confirm - Ejecutar reinicio
#===========================================
async def cmd_restart_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta el reinicio tras confirmación"""
    args = " ".join(context.args).strip()

    # Buscar nombre de pod antes de --confirm
    if "--confirm" not in args.lower():
        return  # No es una confirmación, ignorar

    pod_name = args.replace("--confirm", "").strip()

    if not pod_name:
        return

    logger.info(f"🔄 Reiniciando '{pod_name}' confirmado por user_id={update.effective_user.id}")

    mensaje = await update.message.reply_text(f"🔄 **Reiniciando `{pod_name}`...**\n\n⏳ Eliminando pod.")

    try:
        # Eliminar el pod
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace=K8S_NAMESPACE,
            grace_period_seconds=30,  # Esperar 30s para shutdown graceful
            propagation_policy='Foreground'
        )
        
        await mensaje.edit_text(
            f"✅ **Pod `{pod_name}` eliminado**\n\n"
            f"🔄 Kubernetes está recreándolo...\n"
            f"⏱️ Tiempo estimado: 10-60 segundos\n\n"
            f"💡 Usa `/logs {pod_name}` para ver los nuevos logs cuando esté listo."
        )
        
        # Opcional: Esperar y notificar cuando esté Running de nuevo
        # (Comentado para no bloquear el bot)
        # await asyncio.sleep(30)
        # ... verificar estado y notificar ...
        
    except ApiException as e:
        await mensaje.edit_text(f"❌ Error reiniciando: `{e.reason}`\n\n💡 ¿El pod existe en namespace `{K8S_NAMESPACE}`?")
    except Exception as e:
        logger.error(f"❌ Error en /restart: {str(e)}")
        await mensaje.edit_text(f"❌ Error: {str(e)[:200]}")


# ===========================================
# /logs <pod> - Ver logs de un pod
# ===========================================
async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los logs de un pod específico"""
    pod_name = " ".join(context.args).strip()
    
    if not pod_name:
        await update.message.reply_text(
            "🤔 **Uso:** `/logs <nombre-del-pod>`\n\n"
            "Ejemplo: `/logs mi-app-backend-abc123`\n\n"
            "💡 Tip: Usa `/resumen` para ver la lista de pods disponibles.",
            parse_mode="Markdown"
        )
        return
    
    logger.info(f"📩 /logs '{pod_name}' de user_id={update.effective_user.id}")
    
    # Mensaje inmediato de "Cargando..."
    mensaje = await update.message.reply_text(f"📜 **Obteniendo logs de `{pod_name}`...**\n\n⏳ Un momento.")
    
    try:
        # Intentar obtener logs del contenedor actual
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=K8S_NAMESPACE,
            timestamps=True,
            tail_lines=100  # Últimas 100 líneas
        )
        
        # Si los logs son muy largos, truncar para Telegram (límite ~4096 chars)
        if len(logs) > 3500:
            logs = logs[-3500:]  # Mantener el final (lo más reciente)
            logs = "... [logs truncados, mostrando lo más reciente] ...\n\n" + logs
        
        # Formatear con código markdown
        respuesta = f"""
📜 **Logs de `{pod_name}`** - Namespace: `{K8S_NAMESPACE}`

```text
{logs}
🕐 Últimas 100 líneas | 📋 Usa /logs {pod_name} --previous para ver logs del contenedor anterior
"""

        # Enviar logs
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        
        # Borrar mensaje de "Cargando..."
        await mensaje.delete()
        
    except ApiException as e:
        # Si falla, intentar con el contenedor anterior (--previous)
        if "previous" in " ".join(context.args).lower() or e.status == 400:
            try:
                logs = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=K8S_NAMESPACE,
                    timestamps=True,
                    tail_lines=100,
                    previous=True  # Logs del contenedor anterior (útil para CrashLoopBackOff)
                )
                
                if len(logs) > 3500:
                    logs = logs[-3500:]
                    logs = "... [logs truncados] ...\n\n" + logs
                
                respuesta = f"""
                📜 Logs PREVIOS de {pod_name} - Namespace: {K8S_NAMESPACE}	
                {logs}
                🕐 Contenedor anterior (antes del reinicio)
                """
                await update.message.reply_text(respuesta, parse_mode="Markdown")
                await mensaje.delete()

            except Exception as e2:
                await mensaje.edit_text(f"❌ Error obteniendo logs: `{e2.reason}`")
        else:
            await mensaje.edit_text(f"❌ Error: `{e.reason}`\n\n💡 Verifica que el pod existe y está en namespace `{K8S_NAMESPACE}`")
            
    except Exception as e:
        logger.error(f"❌ Error en /logs: {str(e)}")
        await mensaje.edit_text(f"❌ Error: {str(e)[:200]}")


#===========================================
#/restart <pod> - Reiniciar un pod
#===========================================
async def cmd_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reinicia un pod (lo elimina para que Kubernetes lo recreé)"""
    pod_name = " ".join(context.args).strip()
    if not pod_name:
        await update.message.reply_text(
            "⚠️ **Uso:** `/restart <nombre-del-pod>`\n\n"
            "Ejemplo: `/restart mi-app-backend-abc123`\n\n"
            "🔁 Esto eliminará el pod. Si está gestionado por un Deployment, "
            "Kubernetes lo recreará automáticamente.",
            parse_mode="Markdown"
        )
        return

    logger.info(f"📩 /restart '{pod_name}' de user_id={update.effective_user.id}")

    # Mensaje de confirmación con botón implícito (texto)
    confirm_msg = f"""
    ⚠️ CONFIRMAR REINICIO
📦 Pod: {pod_name}
📁 Namespace: {K8S_NAMESPACE}
🔁 Esta acción:

    Eliminará el pod actual
    Kubernetes lo recreará (si está en un Deployment/ReplicaSet)
    Habrá ~10-30 segundos de indisponibilidad

✅ Para confirmar, envía: /restart {pod_name} --confirm
❌ Para cancelar, no hagas nada o envía cualquier otro mensaje
"""
    await update.message.reply_text(confirm_msg, parse_mode="Markdown")
    # Nota: En un bot real, podrías usar InlineKeyboardButton para confirmación interactiva
    # Por simplicidad, usamos el flag --confirm en el mismo comando
    

#===========================================
#/describe <pod> - Descripción detallada
#===========================================
async def cmd_describe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información detallada de un pod (equivalente a kubectl describe)"""
    pod_name = " ".join(context.args).strip()
    
    if not pod_name:
        await update.message.reply_text(
            "🔍 **Uso:** `/describe <nombre-del-pod>`\n\n"
            "Ejemplo: `/describe mi-app-backend-abc123`\n\n"
            "📋 Muestra: estado, eventos, contenedores, recursos, mounts, etc.",
            parse_mode="Markdown"
        )
        return

    logger.info(f"📩 /describe '{pod_name}' de user_id={update.effective_user.id}")

    mensaje = await update.message.reply_text(
        f"🔍 **Obteniendo detalles de `{pod_name}`...**\n\n⏳ Consultando Kubernetes API."
    )

    try:
        # Obtener el pod completo
        pod = v1.read_namespaced_pod(name=pod_name, namespace=K8S_NAMESPACE)
        
        # Construir descripción formateada
        descripcion = f"""
📋 **DESCRIPCIÓN: `{pod_name}`**
📁 Namespace: `{K8S_NAMESPACE}`

🔹 **Estado General**
• Fase: `{pod.status.phase}`
• IP: `{pod.status.pod_ip or 'N/A'}`
• Node: `{pod.spec.node_name or 'N/A'}`
• QoS: `{pod.status.qos_class or 'N/A'}`

🔹 **Contenedores**
"""
        # Información de cada contenedor
        for i, container in enumerate(pod.spec.containers, 1):
            descripcion += f"\n{i}. **{container.name}**\n"
            descripcion += f"   • Imagen: `{container.image.split('/')[-1]}`\n"
            
            # Estado del contenedor si está disponible
            if pod.status.container_statuses and i <= len(pod.status.container_statuses):
                cs = pod.status.container_statuses[i-1]
                if cs.state:
                    descripcion += f"   • Estado: `{cs.state}`\n"
                descripcion += f"   • Ready: {'✅' if cs.ready else '❌'}\n"
                descripcion += f"   • Reinicios: `{cs.restart_count}`\n"
        
        # Eventos recientes del pod
        try:
            events = v1.list_namespaced_event(
                namespace=K8S_NAMESPACE,
                field_selector=f"involvedObject.name={pod_name}",
                limit=5
            )
            
            if events.items:
                descripcion += f"\n🔹 **Eventos Recientes**\n"
                for event in events.items[:3]:  # Máximo 3 eventos
                    msg = event.message[:100].replace("\n", " ")
                    descripcion += f"• `{event.type}`: {msg}...\n"
        except Exception:
            pass  # Si no hay eventos o no hay permisos, continuar
        
        descripcion += f"\n🕐 *Actualizado: {datetime.now().strftime('%H:%M:%S')}*"
        
        # Si la descripción es muy larga, usar IA para resumir
        if len(descripcion) > 3500:
            resumen_prompt = (
                f"Resume esta información técnica de Kubernetes en puntos clave claros:\n\n"
                f"{descripcion[:3000]}\n\n"
                f"Enfócate en:\n"
                f"- Estado actual del pod\n"
                f"- Problemas detectados (si los hay)\n"
                f"- Recomendaciones si hay errores\n\n"
                f"Máximo 15 líneas, formato markdown simple."
            )
            try:
                resumen_ia = await consultar_ia(resumen_prompt)
                descripcion = (
                    f"📋 **RESUMEN IA de `{pod_name}`**\n\n"
                    f"{resumen_ia}\n\n"
                    f"---\n\n"
                    f"*Usa `/describe {pod_name} --full` para ver información completa.*"
                )
            except Exception:
                descripcion = descripcion[:3500] + "\n\n... [truncado] ..."
        
        await update.message.reply_text(descripcion, parse_mode="Markdown")
        await mensaje.delete()
        
    except ApiException as e:
        await mensaje.edit_text(
            f"❌ Error: `{e.reason}`\n\n"
            f"💡 Verifica que el pod existe en namespace `{K8S_NAMESPACE}`"
        )
    except Exception as e:
        logger.error(f"❌ Error en /describe: {str(e)}")
        await mensaje.edit_text(f"❌ Error: {str(e)[:200]}")


async def main_async():
    logger.info("🚀 Starting K8s Bot with IA...")

    app = Application.builder() \
        .token(TOKEN) \
        .job_queue(None) \
        .build()

# En main_async(), añade:

# Handler para lenguaje natural (DEBE IR ANTES del echo)


    # ... tus handlers existentes ...
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pods", consultar_pods))
    app.add_handler(CommandHandler("ia", pregunta_ia))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(CommandHandler("grafico", cmd_grafico))
    app.add_handler(CommandHandler("foto", cmd_foto_dashboard))    

    # 👇 AÑADIR ESTOS 3 HANDLERS NUEVOS:
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("restart", cmd_restart))
    app.add_handler(CommandHandler("restart", cmd_restart_confirm))  # Para --confirm
    app.add_handler(CommandHandler("describe", cmd_describe))
    
    # Handler para lenguaje natural para el agente
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_natural_ia))
    # Handler para confirmaciones
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_accion))


    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_normal))

    # Configurar señales
    setup_signal_handlers(app)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("✅ Polling iniciado. Bot escuchando mensajes...")
    
    # Iniciar tarea de chequeo periódico (cada 10 min)
    background_task = asyncio.create_task(chequeo_periodico(app))
    
    # 👇 AÑADIR ESTO: Alerta de prueba a los 20 segundos
    # test_alert_task = asyncio.create_task(alerta_prueba_20s(app))
    # logger.info("🧪 [TEST] Alerta de prueba programada en 20 segundos")
    
    logger.info("✅ Bot running. Waiting for messages...")

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("👋 Main task cancelled")
    finally:
        # Cancelar tareas de fondo
        background_task.cancel()
        # test_alert_task.cancel()  # 👇 Cancelar también la alerta de prueba
        try:
            await background_task
        #    await test_alert_task
        except asyncio.CancelledError:
            pass
        await graceful_shutdown(app)


if __name__ == '__main__':
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by Ctrl+C")
    except Exception as e:
        logger.critical(f"❌ Error crítico: {e}", exc_info=True)
        sys.exit(1)