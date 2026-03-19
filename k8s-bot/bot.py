import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

# Importar funciones de Kubernetes
from k8s_checker import cargar_k8s, obtener_estado_pods

# Importar cliente de OpenRouter
from openrouter_client import consultar_ia

# Configuración
TOKEN = os.getenv("TELEGRAM_BOT_KUBERNETES_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_USER_CHAT_ID")

# Cargar Kubernetes al inicio
v1 = cargar_k8s()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "🤖 **Bot K8s con IA activado**\n\n"
        "Comandos disponibles:\n"
        "/pods - Ver estado de los pods\n"
        "/ayuda - Ver esta ayuda\n"
        "/ia <pregunta> - Preguntar algo a la IA sobre Kubernetes"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda"""
    await update.message.reply_text(
        "📚 **Ayuda**\n\n"
        "• /pods - Consulta el estado de los pods\n"
        "• /ia <pregunta> - Pregunta algo a la IA\n"
        "• /start - Reinicia el bot\n"
        "• Escribe naturalmente sobre pods o estado"
    )

async def consultar_pods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consulta manual de pods"""
    mensaje = await update.message.reply_text("🔍 Consultando clúster...")
    
    estado = obtener_estado_pods(v1)
    
    # Usar IA para formatear la respuesta
    respuesta_ia = await consultar_ia(
        f"Formatea esta información de manera clara y amigable:\n{estado}"
    )
    
    await mensaje.edit_text(respuesta_ia, parse_mode="Markdown")

async def pregunta_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ia para preguntar a la IA"""
    pregunta = " ".join(context.args)
    
    if not pregunta:
        await update.message.reply_text("🤔 Por favor escribe una pregunta. Ej: `/ia qué es un pod en Kubernetes`")
        return
    
    mensaje = await update.message.reply_text("🧠 Consultando a la IA...")
    
    # Obtener contexto del clúster si es relevante
    contexto = obtener_estado_pods(v1)[:500]  # Primeros 500 caracteres como contexto
    
    respuesta = await consultar_ia(pregunta, contexto)
    
    await mensaje.edit_text(respuesta, parse_mode="Markdown")

async def mensaje_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a mensajes de texto usando IA"""
    texto = update.message.text
    
    # Palabras clave que indican consulta de Kubernetes
    palabras_k8s = ["pod", "pods", "estado", "status", "kubernetes", "k8s", 
                    "clúster", "cluster", "deploy", "deployment", "servicio"]
    
    es_consulta_k8s = any(palabra in texto.lower() for palabra in palabras_k8s)
    
    if es_consulta_k8s:
        # Si es sobre Kubernetes, consultar el clúster real
        mensaje = await update.message.reply_text("🔍 Consultando clúster...")
        estado = obtener_estado_pods(v1)
        
        # Usar IA para interpretar y responder
        prompt = f"""El usuario preguntó: {texto}

Esta es la información real del clúster:
{estado}

Responde de manera clara y útil basándote en esta información."""
        
        respuesta = await consultar_ia(prompt)
        await mensaje.edit_text(respuesta, parse_mode="Markdown")
    else:
        # Si no es sobre Kubernetes, responder solo con IA
        mensaje = await update.message.reply_text("🧠 Pensando...")
        respuesta = await consultar_ia(texto)
        await mensaje.edit_text(respuesta, parse_mode="Markdown")

async def chequeo_periodico(context: ContextTypes.DEFAULT_TYPE):
    """Tarea programada: Se ejecuta cada 10 minutos automáticamente"""
    print(f"⏰ [{datetime.now()}] Chequeo periódico...")
    
    try:
        estado = obtener_estado_pods(v1)
        
        # Solo enviar alerta si hay problemas
        if "ALERTA" in estado or "❌" in estado:
            # Usar IA para formatear la alerta
            prompt = f"""Hay problemas en el clúster. Esta es la información:
{estado}

Crea un informe claro y conciso de las alertas."""
            
            informe = await consultar_ia(prompt)
            
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"🚨 **ALERTA AUTOMÁTICA**\n\n{informe}",
                parse_mode="Markdown"
            )
            print("✅ Alerta enviada")
        else:
            print("✅ Todo OK, no se envía alerta")
    except Exception as e:
        print(f"❌ Error en chequeo periódico: {e}")

def configurar_scheduler(application):
    """Configura la tarea periódica usando el JobQueue nativo de PTB v21"""
    job_queue = application.job_queue
    
    # Programa la tarea para que se repita cada 10 minutos
    job_queue.run_repeating(
        chequeo_periodico,
        interval=600,  # 600 segundos = 10 minutos
        first=10,      # Primera ejecución a los 10 segundos de iniciar
        name="chequeo_k8s"
    )
    print("⏰ Scheduler configurado (cada 10 minutos)")

def main():
    """Función principal"""
    print("🚀 Iniciando bot con IA...")
    
    # Crear la aplicación
    # En PTB v21, el job_queue se crea por defecto al construir la app
    app = Application.builder().token(TOKEN).build()
    
    # Añadir handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("pods", consultar_pods))
    app.add_handler(CommandHandler("ia", pregunta_ia))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_normal))
    
    # Configurar scheduler (JobQueue nativo)
    configurar_scheduler(app)
    
    # Iniciar el bot
    print("✅ Bot listo. Esperando mensajes...")
    app.run_polling()

if __name__ == '__main__':
    main()