# handlers/ai_handler.py
"""Handlers de Telegram para comandos de IA (multi-proveedor: Groq, OpenRouter, Gemini)"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from pathlib import Path
import glob
import re
import httpx
from core.context_manager import ContextManager

# Importar el cliente unificado
from core.llm_client import LLMClient

# Importar y configurar generador
from core.project_generator import ProjectGenerator

output_dir = os.getenv("OUTPUT_DIRECTORY", "C:/Users/pedrodulce/develop/generated")
max_files = int(os.getenv("MAX_FILES_PER_PROJECT", "100"))
timeout = int(os.getenv("PROJECT_GENERATION_TIMEOUT", "1800"))
      

logger = logging.getLogger(__name__)

_ai_client = None

# ==============================
# CONFIGURACIÓN DE SEGURIDAD
# ==============================

# ✅ Solo estos directorios pueden ser analizados (ajusta a tus rutas)
ALLOWED_DIRECTORIES = [
    Path("C:/Users/pedrodulce/develop/antigravity"),
    Path("C:/Users/pedrodulce/develop"),
    # Añade más directorios según necesites
]

# ❌ Patrones de archivos a EXCLUIR (seguridad y ruido)
EXCLUDED_PATTERNS = [
    "*.pyc", "__pycache__", "*.env", "*.log", 
    ".git", "node_modules", "*.db", "*.sqlite",
    "*.min.js", "*.min.css", "dist", "build", ".idea", ".vscode"
]


# 🅰️ Patrones específicos de Angular para priorizar
ANGULAR_PATTERNS = [
    "*.ts",           # TypeScript
    "*.component.ts", # Componentes
    "*.service.ts",   # Servicios
    "*.module.ts",    # Módulos
    "*.pipe.ts",      # Pipes
    "*.directive.ts", # Directivas
    "*.html",         # Templates
    "*.scss", "*.css", # Estilos
    "*.json"          # Configs (package.json, angular.json, etc.)
]

def get_ai_client() -> LLMClient:
    """Obtiene o crea el cliente de IA singleton (usa configuración del .env)"""
    global _ai_client
    
    if _ai_client is None:
        try:
            _ai_client = LLMClient()  # Lee LLM_PROVIDER, GROQ_API_KEY, etc. del .env
            logger.info(f"✅ AI client singleton creado: {_ai_client.provider}")
        except Exception as e:
            logger.error(f"❌ Error creando AI client: {e}")
            return None
    
    return _ai_client


async def cmd_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ai [pregunta] - Consulta genérica a la IA"""
    
    # 🛠️ LOGGING DE DEBUG (añadir esto al inicio)
    logger.info(f"🔍 [DEBUG] cmd_ai llamado")
    logger.info(f"   update.message: {update.message}")
    logger.info(f"   context.args: {context.args}")
    if update.message and update.message.text:
        logger.info(f"   Texto: {update.message.text[:100]}")
    
    if not update.message:
        logger.warning("⚠️ update.message es None")
        return
    
    client = get_ai_client()
    logger.info(f"🔍 [DEBUG] get_ai_client() retornó: {client}")
    
    if not client:
        logger.error("❌ AI client es None")
        await update.message.reply_text("❌ IA no configurada. Revisa logs.")
        return
    
    query = " ".join(context.args).strip()
    logger.info(f"🔍 [DEBUG] Query: '{query}'")
    
    if not query:
        await update.message.reply_text("💡 Uso: /ai [tu pregunta]")
        return
    
    user = update.effective_user
    logger.info(f"🧠 /ai desde @{user.username or 'unknown'}: {query[:100]}")
    
    # ✅ AHORA sí enviamos "Pensando..."
    status_msg = await update.message.reply_text("🧠 *Pensando...* ⏳")
    logger.info("✅ Mensaje 'Pensando...' enviado")
    
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(client.generate, query),
            timeout=90.0
        )
        logger.info(f"✅ Respuesta recibida: {len(response)} chars")
        
        if not response or response.startswith("❌"):
            try:
                await status_msg.edit_text(f"❌ *Error*:\n\n`{response}`", parse_mode=None)
            except Exception:
                # Fallback: enviar sin formato si hay error de parseo
                await status_msg.edit_text(f"❌ Error:\n\n{response}", parse_mode=None)
            return
        
        await _send_long_message(update, f"🤖 Respuesta:\n\n{response}")
        logger.info(f"✅ Respuesta final enviada")
        
    except asyncio.TimeoutError:
        logger.warning("⏰ Timeout")
        await status_msg.edit_text("⏰ *Timeout*: La IA tardó más de 90s")
    except Exception as e:
        logger.error(f"❌ Excepción: {type(e).__name__}: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ *Error*:\n\n`{e}`", parse_mode='Markdown')

async def cmd_dev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /dev [tarea] - Genera código"""
    if not update.message:
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada. Revisa LLM_PROVIDER y API keys en .env")
        return
    
    task = " ".join(context.args).strip()
    if not task:
        await update.message.reply_text(
            "💡 *Uso*: `/dev [descripción de tarea]`\n\n"
            "Ejemplo: `/dev crear función Python para validar email`",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text("🔧 *Generando código...* 🧠")
    
    try:
        language = _detect_language(task)
        response = await asyncio.wait_for(
            asyncio.to_thread(client.generate_code, task, language),
            timeout=120.0
        )
        await _send_long_message(update, response)
        logger.info(f"✅ Código generado para: {task[:50]}")
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ *Timeout*: Generación tardó más de 120s")
    except Exception as e:
        logger.error(f"❌ Error en /dev: {e}")
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode=None)


async def cmd_explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /explain [código] - Explica código"""
    if not update.message:
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    code = " ".join(context.args).strip()
    if not code:
        await update.message.reply_text(
            "💡 Pega el código en el siguiente mensaje",
            parse_mode='Markdown'
        )
        return
    
    language = _detect_language(code)
    await update.message.reply_text(f"🔍 *Analizando {language.upper()}...*")
    
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(client.explain_code, code, language),
            timeout=90.0
        )
        await _send_long_message(update, response)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode=None)


async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /debug [error] - Ayuda con errores"""
    if not update.message:
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    error_msg = " ".join(context.args).strip()
    if not error_msg:
        await update.message.reply_text(
            "💡 Uso: `/debug [mensaje de error]`",
            parse_mode='Markdown'
        )
        return
    
    language = _detect_language(error_msg)
    await update.message.reply_text("🔬 *Analizando error...*")
    
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(client.debug_error, error_msg, "", language),
            timeout=90.0
        )
        await _send_long_message(update, response)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode=None)


# Alias para compatibilidad (por si algún archivo aún importa cmd_gemini)
cmd_gemini = cmd_ai


# ==============================
# UTILIDADES
# ==============================

def _detect_language(text: str) -> str:
    """Detecta el lenguaje de programación por palabras clave"""
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ['def ', 'import ', 'python', 'pip', 'venv']):
        return 'python'
    elif any(kw in text_lower for kw in ['public class', 'import java', 'spring', '@autowired', 'jpa']):
        return 'java'
    elif any(kw in text_lower for kw in ['function ', 'const ', 'let ', '=>', 'npm', 'node']):
        return 'javascript'
    elif any(kw in text_lower for kw in ['async ', 'await', 'typescript', 'interface ']):
        return 'typescript'
    elif any(kw in text_lower for kw in ['sql', 'select ', 'from ', 'where ', 'database']):
        return 'sql'
    elif any(kw in text_lower for kw in ['angular', '@component', 'module']):
        return 'typescript'
    else:
        return 'python'


def _split_message_smart(text: str, max_len: int = 4000) -> list:
    """Divide un mensaje largo respetando bloques de código y párrafos"""
    if len(text) <= max_len:
        return [text]
    
    chunks = []
    current = ""
    lines = text.split('\n')
    
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current)
                current = ""
            if len(line) > max_len:
                for i in range(0, len(line), max_len - 100):
                    chunks.append(line[i:i + max_len - 100])
            else:
                current = line
        else:
            current += ('\n' if current else '') + line
    
    if current:
        chunks.append(current)
    
    return chunks


def _escape_markdown(text: str) -> str:
    """
    Escapa caracteres especiales de Markdown para Telegram.
    Caracteres que deben escaparse: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    # Caracteres que Telegram Markdown considera especiales
    # escape_chars = r'_*[]()~`>#+-=|{}.!'
    escape_chars = r'\_*[]()~`>#+-=|{}.!\\'

    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text        


async def _send_long_message(update: Update, content: str, max_chunk: int = 3500):
    """
    Envía un mensaje largo como TEXTO PLANO (sin formato Markdown).
    Divide en chunks si excede el límite de Telegram (4096 chars).
    """
    chunks = _split_message_smart(content, max_chunk)
    
    for i, chunk in enumerate(chunks):
        prefix = f"📄 ({i+1}/{len(chunks)}):\n\n" if len(chunks) > 1 else ""
        message = f"{prefix}{chunk}"
        
        # ✅ Siempre texto plano, nunca falla por caracteres especiales
        await update.message.reply_text(message, parse_mode=None)
        
        if i < len(chunks) - 1:
            await asyncio.sleep(0.3)

async def cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /review [ruta_archivo] - Revisa un archivo y sugiere mejoras
    
    Uso:
    /review C:/Users/pedrodulce/develop/antigravity/bot.py
    /review ./handlers/ai_handler.py
    """
    if not update.message:
        return
    
    # 🔐 Verificación de seguridad: solo el dueño del chat
    user_chat_id = update.effective_user.id
    allowed_chat_id = int(os.getenv("TELEGRAM_USER_CHAT_ID", "0"))
    if user_chat_id != allowed_chat_id:
        await update.message.reply_text("❌ No tienes permiso para usar este comando")
        logger.warning(f"⚠️ Acceso denegado a Chat ID: {user_chat_id}")
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    # Obtener ruta del archivo
    file_path = " ".join(context.args).strip()
    if not file_path:
        await update.message.reply_text(
            "💡 *Uso*: `/review [ruta_del_archivo]`\n\n"
            "Ejemplo:\n"
            "`/review C:/Users/pedrodulce/develop/antigravity/bot.py`",
            parse_mode='Markdown'
        )
        return
    
    # 🔐 Validar que la ruta está en directorios permitidos
    try:
        abs_path = Path(file_path).resolve()
        
        # Verificar que está dentro de un directorio permitido
        is_allowed = any(
            str(abs_path).startswith(str(allowed_dir.resolve()))
            for allowed_dir in ALLOWED_DIRECTORIES
        )
        
        if not is_allowed:
            await update.message.reply_text(
                f"❌ *Acceso denegado*\n\n"
                f"La ruta debe estar dentro de:\n"
                f"{'\n'.join(str(d) for d in ALLOWED_DIRECTORIES)}",
                parse_mode='Markdown'
            )
            logger.warning(f"⚠️ Intento de acceso fuera de whitelist: {abs_path}")
            return
        
        if not abs_path.exists():
            await update.message.reply_text(f"❌ Archivo no encontrado: {abs_path}")
            return
        
        if not abs_path.is_file():
            await update.message.reply_text(f"❌ No es un archivo: {abs_path}")
            return
        
        # Leer el contenido del archivo
        try:
            content = abs_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = abs_path.read_text(encoding='latin-1')  # Fallback
        
        logger.info(f"📄 Revisando archivo: {abs_path}")
        
        # Enviar mensaje de "Analizando..."
        status_msg = await update.message.reply_text("🔍 *Analizando código...* ⏳")
        
        # Construir prompt para la IA
        prompt = f"""Revisa este archivo y genera un informe de mejoras:

**Archivo**: {abs_path.name}
**Ruta**: {abs_path}

**Código**:
```{abs_path.suffix.lstrip('.') or 'text'}
{content}
```

Por favor, proporciona:
1. ✅ **Puntos fuertes** del código
2. ⚠️ **Problemas detectados** (bugs, malas prácticas, seguridad)
3. 💡 **Mejoras sugeridas** (con ejemplos de código si aplica)
4. 📊 **Calificación general** (1-10)
5. 🎯 **Prioridades** (qué mejorar primero)

Sé específico y proporciona ejemplos de código corregido cuando sea posible."""
        
        # Generar respuesta con IA
        response = await asyncio.wait_for(
            asyncio.to_thread(client.generate, prompt),
            timeout=120.0
        )
        
        # Enviar informe formateado
        await status_msg.edit_text(f"📊 *Informe de {abs_path.name}*:\n\n{response}", parse_mode=None)
        
        logger.info(f"✅ Informe generado para: {abs_path}")
        
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏰ *Timeout*: El análisis tardó más de 120s")
    except Exception as e:
        logger.error(f"❌ Error en /review: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode='Markdown')


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /analyze [directorio] - Analiza todos los archivos de un directorio
    
    Uso:
    /analyze C:/Users/pedrodulce/develop/antigravity
    """
    if not update.message:
        return
    
    # 🔐 Verificación de seguridad
    user_chat_id = update.effective_user.id
    allowed_chat_id = int(os.getenv("TELEGRAM_USER_CHAT_ID", "0"))
    if user_chat_id != allowed_chat_id:
        await update.message.reply_text("❌ No tienes permiso")
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    dir_path = " ".join(context.args).strip()
    if not dir_path:
        await update.message.reply_text("💡 Uso: /analyze [ruta_directorio]")
        return
    
    try:
        abs_dir = Path(dir_path).resolve()
        
        # Validar directorio permitido
        is_allowed = any(
            str(abs_dir).startswith(str(allowed_dir.resolve()))
            for allowed_dir in ALLOWED_DIRECTORIES
        )
        
        if not is_allowed or not abs_dir.exists() or not abs_dir.is_dir():
            await update.message.reply_text("❌ Directorio inválido o no permitido")
            return
        
        # Buscar archivos de código (Python, Java, JS, etc.)
        patterns = ["*.py", "*.java", "*.js", "*.ts", "*.cpp", "*.h", "*.cs"]
        files = []
        
        for pattern in patterns:
            files.extend(abs_dir.rglob(pattern))
        
        # Filtrar excluidos
        files = [
            f for f in files
            if not any(f.match(excluded) for excluded in EXCLUDED_PATTERNS)
        ]
        
        if not files:
            await update.message.reply_text("❌ No se encontraron archivos de código")
            return
        
        await update.message.reply_text(
            f"📂 *Analizando {min(len(files), 5)} de {len(files)} archivos en {abs_dir.name}...*\n\n"
            f"Se analizarán los primeros 5 archivos (para evitar timeouts) ⏳"
        )
        
        # Analizar cada archivo (limitado a los primeros 10 para no saturar)
        reports = []
        for i, file in enumerate(files[:5]):  # Limitar a 10 archivos
            try:
                content = file.read_text(encoding='utf-8', errors='ignore')
                
                # Análisis rápido con IA
                prompt = f"""Analiza brevemente este archivo y dame 3 mejoras principales:

Archivo: {file.name}

```{file.suffix.lstrip('.') or 'text'}
{content[:2000]}  # Limitar contenido
```

Proporciona SOLO 3 mejoras concretas y priorizadas."""
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(client.generate, prompt),
                    timeout=60.0
                )
                
                reports.append(f"**{file.name}**:\n{response}")
                
                # Pequeña pausa para no saturar la API
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"⚠️ Error analizando {file}: {e}")
                continue
        
        # Enviar resumen
        summary = "\n\n---\n\n".join(reports)
        await update.message.reply_text(
            f"📊 *Informe de Análisis* - {abs_dir.name}\n\n"
            f"Archivos analizados: {min(len(files), 10)}/{len(files)}\n\n"
            f"{summary}",
            parse_mode=None
        )
        
    except Exception as e:
        logger.error(f"❌ Error en /analyze: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode='Markdown')


async def cmd_improve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /improve [ruta_archivo] - Reescribe el archivo con mejoras aplicadas
    
    Uso:
    /improve C:/Users/pedrodulce/develop/antigravity/bot.py
    """
    if not update.message:
        return
    
    # 🔐 Seguridad
    user_chat_id = update.effective_user.id
    allowed_chat_id = int(os.getenv("TELEGRAM_USER_CHAT_ID", "0"))
    if user_chat_id != allowed_chat_id:
        await update.message.reply_text("❌ No tienes permiso")
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    file_path = " ".join(context.args).strip()
    if not file_path:
        await update.message.reply_text("💡 Uso: /improve [ruta_archivo]")
        return
    
    try:
        abs_path = Path(file_path).resolve()
        
        # Validar
        is_allowed = any(
            str(abs_path).startswith(str(allowed_dir.resolve()))
            for allowed_dir in ALLOWED_DIRECTORIES
        )
        
        if not is_allowed or not abs_path.exists() or not abs_path.is_file():
            await update.message.reply_text("❌ Archivo inválido o no permitido")
            return
        
        content = abs_path.read_text(encoding='utf-8', errors='ignore')
        
        await update.message.reply_text("🔧 *Reescribiendo con mejoras...* ⏳")
        
        prompt = f"""Reescribe ESTE archivo completo aplicando todas las mejoras posibles:

Archivo: {abs_path.name}

Código original:
```{abs_path.suffix.lstrip('.') or 'text'}
{content}
```

Proporciona SOLO el código completo y mejorado, sin explicaciones.
Mantén la misma funcionalidad pero aplica:
- Mejores prácticas
- Código más limpio y legible
- Manejo de errores
- Optimizaciones
- Comentarios útiles

Devuelve ÚNICAMENTE el código en un bloque markdown."""
        
        response = await asyncio.wait_for(
            asyncio.to_thread(client.generate, prompt),
            timeout=120.0
        )
        
        # Extraer código del bloque markdown
        import re
        code_match = re.search(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        improved_code = code_match.group(1).strip() if code_match else response.strip()
        
        # Crear archivo backup
        backup_path = abs_path.with_suffix(abs_path.suffix + '.backup')
        abs_path.rename(backup_path)
        
        # Escribir versión mejorada
        abs_path.write_text(improved_code, encoding='utf-8')
        
        await update.message.reply_text(
            f"✅ *Archivo mejorado*\n\n"
            f"📄 Archivo: {abs_path.name}\n"
            f"💾 Backup: {backup_path.name}\n\n"
            f"Se creó un backup del archivo original."
        )
        
    except Exception as e:
        logger.error(f"❌ Error en /improve: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode='Markdown')


async def cmd_angular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /angular [directorio] - Análisis específico de proyecto Angular
    
    Analiza:
    • Estructura de módulos y componentes
    • Servicios y dependencias
    • Templates y binding
    • Estilos y SCSS
    • Routing y guards
    • Tests y cobertura
    
    Uso:
    /angular C:/Users/pedrodulce/develop/mi-app-angular
    """
    if not update.message:
        return
    
    # 🔐 Seguridad: solo el dueño del chat
    user_chat_id = update.effective_user.id
    allowed_chat_id = int(os.getenv("TELEGRAM_USER_CHAT_ID", "0"))
    if user_chat_id != allowed_chat_id:
        await update.message.reply_text("❌ No tienes permiso para este comando")
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    dir_path = " ".join(context.args).strip()
    if not dir_path:
        await update.message.reply_text(
            "💡 *Uso*: `/angular [ruta_directorio]`\n\n"
            "Ejemplo:\n"
            "`/angular C:/Users/pedrodulce/develop/mi-app-angular`",
            parse_mode='Markdown'
        )
        return
    
    try:
        abs_dir = Path(dir_path).resolve()
        
        # Validar directorio permitido
        is_allowed = any(
            str(abs_dir).startswith(str(allowed_dir.resolve()))
            for allowed_dir in ALLOWED_DIRECTORIES
        )
        
        if not is_allowed:
            await update.message.reply_text("❌ Directorio no está en la whitelist")
            return
        
        if not abs_dir.exists() or not abs_dir.is_dir():
            await update.message.reply_text("❌ Directorio no encontrado")
            return
        
        # Verificar que es proyecto Angular
        angular_json = abs_dir / "angular.json"
        package_json = abs_dir / "package.json"
        
        if not angular_json.exists() and not package_json.exists():
            await update.message.reply_text(
                "⚠️ *No parece un proyecto Angular*\n\n"
                "No se encontró `angular.json` ni `package.json`.\n"
                "¿Es la ruta correcta del proyecto?",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(
            f"🅰️ *Analizando proyecto Angular en `{abs_dir.name}`...*\n\n"
            f"Esto puede tardar 2-5 minutos ⏳",
            parse_mode='Markdown'
        )
        
        # ==============================
        # FASE 1: Estructura del proyecto
        # ==============================
        logger.info("📂 Analizando estructura...")
        
        # Contar archivos por tipo
        file_counts = {}
        angular_files = []
        
        for pattern in ["*.ts", "*.html", "*.scss", "*.css", "*.json"]:
            files = list(abs_dir.rglob(pattern))
            # Excluir node_modules, dist, etc.
            files = [
                f for f in files
                if not any(part in str(f) for part in ["node_modules", "dist", "build", ".git"])
            ]
            file_counts[pattern] = len(files)
            if pattern == "*.ts":
                angular_files.extend(files)
        
        estructura_info = f"""
📊 **Estructura del Proyecto**

| Tipo | Cantidad |
|------|----------|
| TypeScript (.ts) | {file_counts.get('*.ts', 0)} |
| Templates (.html) | {file_counts.get('*.html', 0)} |
| Estilos (.scss/.css) | {file_counts.get('*.scss', 0) + file_counts.get('*.css', 0)} |
| Config (.json) | {file_counts.get('*.json', 0)} |

"""
        
        # ==============================
        # FASE 2: Analizar componentes clave
        # ==============================
        logger.info("🔍 Analizando componentes...")
        
        # Encontrar componentes principales
        components = [f for f in angular_files if "component.ts" in f.name]
        services = [f for f in angular_files if "service.ts" in f.name]
        modules = [f for f in angular_files if "module.ts" in f.name]
        
        componentes_info = f"""
🧩 **Componentes y Servicios**

- Componentes: {len(components)}
- Servicios: {len(services)}
- Módulos: {len(modules)}

"""
        
        # ==============================
        # FASE 3: Análisis de código con IA
        # ==============================
        logger.info("🧠 Consultando a IA...")
        
        # Seleccionar archivos representativos (máximo 15)
        sample_files = []
        for file_list in [modules[:3], components[:5], services[:5]]:
            sample_files.extend(file_list)
        
        analisis_ia = []
        
        for i, file in enumerate(sample_files[:10]):
            try:
                content = file.read_text(encoding='utf-8', errors='ignore')[:3000]  # Limitar
                rel_path = file.relative_to(abs_dir)
                
                prompt = f"""Analiza ESTE archivo Angular y dame SOLO 2-3 mejoras concretas:

Archivo: {rel_path}
Tipo: {file.name.split('.')[-2] if '.component' in file.name else 'other'}

```typescript
{content}

Responde ÚNICAMENTE con:

    ✅ Un punto fuerte
    ⚠️ Una mejora prioritaria
    💡 Un consejo específico

Máximo 100 palabras."""
                response = await asyncio.wait_for(
                    asyncio.to_thread(client.generate, prompt),
                    timeout=45.0
                )
            
                analisis_ia.append(f"**{rel_path}**:\n{response}")
                
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.warning(f"⚠️ Error analizando {file}: {e}")
                continue
    
        # ==============================
        # FASE 4: Generar informe completo
        # ==============================
        informe_final = f"""🅰️ *Informe de Análisis Angular*
━━━━━━━━━━━━━━━━━━━━━━━━
📁 Proyecto: `{abs_dir.name}`
📍 Ruta: `{abs_dir}`

{estructura_info}{componentes_info}
🔍 **Análisis de Archivos Clave**:

{chr(10).join(analisis_ia[:8]) if analisis_ia else "⚠️ No se pudo analizar código"}

━━━━━━━━━━━━━━━━━━━━━━━━
💡 **Recomendaciones Generales**:

1. **Arquitectura**: Verifica que sigues Angular Style Guide
2. **Performance**: Usa OnPush change detection donde sea posible
3. **Tests**: Asegura >80% cobertura en servicios críticos
4. **Seguridad**: Sanitiza inputs en templates
5. **Build**: Configura production build con optimizaciones

━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Próximos Pasos Sugeridos**:

• Ejecuta `ng lint` para verificar estilo de código
• Ejecuta `ng test --coverage` para ver cobertura de tests
• Revisa `angular.json` para optimizaciones de build
• Considera migrar a standalone components (Angular 15+)

━━━━━━━━━━━━━━━━━━━━━━━━
✅ *Análisis completado*
"""
        
        # ✅ AHORA (envía por secciones):
        # Sección 1: Estructura
        await update.message.reply_text(
            f"🅰️ *Informe Angular - {abs_dir.name}*\n\n"
            f"📍 Ruta: `{_escape_markdown(str(abs_dir))}`\n\n"
            f"{_escape_markdown(estructura_info)}",
            parse_mode=None
        )
        await asyncio.sleep(0.5)

        # Sección 2: Componentes
        await update.message.reply_text(
            f"🧩 {_escape_markdown(componentes_info)}",
            parse_mode=None
        )
        await asyncio.sleep(0.5)

        # Sección 3: Análisis de archivos (puede ser largo)
        if analisis_ia:
            await update.message.reply_text(
                f"🔍 *Análisis de Archivos Clave*:\n\n"
                f"{_escape_markdown(chr(10).join(analisis_ia[:5]))}",  # Máximo 5 archivos
                parse_mode=None
            )
            await asyncio.sleep(0.5)

        # Sección 4: Recomendaciones
        await update.message.reply_text(
            f"💡 *Recomendaciones Generales*:\n\n"
            f"1. **Arquitectura**: Verifica Angular Style Guide\n"
            f"2. **Performance**: Usa OnPush change detection\n"
            f"3. **Tests**: >80% cobertura en servicios críticos\n"
            f"4. **Seguridad**: Sanitiza inputs en templates\n"
            f"5. **Build**: Optimiza production build",
            parse_mode=None
        )        
                
        logger.info(f"✅ Informe Angular generado: {abs_dir.name}")
        
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ *Timeout*: El análisis excedió el tiempo límite")
    except Exception as e:
        logger.error(f"❌ Error en /angular: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode='Markdown')

# handlers/ai_handler.py - AÑADIR al final del archivo (después de cmd_angular)


# ==============================
# COMANDOS DE CONOCIMIENTO CORPORATIVO
# ==============================

async def cmd_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /context [acción] - Gestiona la base de conocimiento corporativa
    
    Acciones:
    /context list          - Lista documentos disponibles
    /context reload        - Recarga documentos desde disco
    /context search [term] - Busca documentos por palabra clave
    """
    if not update.message:
        return
    
    # 🔐 Seguridad: solo el dueño del chat
    user_chat_id = update.effective_user.id
    allowed_chat_id = int(os.getenv("TELEGRAM_USER_CHAT_ID", "0"))
    if user_chat_id != allowed_chat_id:
        await update.message.reply_text("❌ No tienes permiso para este comando")
        return
    
    action = " ".join(context.args).strip().lower()
    
    # Obtener o crear ContextManager singleton
    if not hasattr(cmd_context, "_ctx_manager"):
        cmd_context._ctx_manager = ContextManager()  # type: ignore
    
    ctx_manager = cmd_context._ctx_manager  # type: ignore
    
    if action == "list" or not action:
        docs = ctx_manager.list_documents()
        response = "📚 *Documentos disponibles*:\n\n"
        for category, files in docs.items():
            if files:
                response += f"*{category}*:\n"
                for f in files[:5]:  # Máximo 5 por categoría
                    response += f"  • `{f}`\n"
                if len(files) > 5:
                    response += f"  ... y {len(files) - 5} más\n"
                response += "\n"
        
        if not any(docs.values()):
            response = "⚠️ No hay documentos en la carpeta `knowledge/`.\n\n"
            response += "Añade guías en:\n"
            response += "`knowledge/angular-guidelines/`\n"
            response += "`knowledge/examples/`\n"
        
        await update.message.reply_text(response, parse_mode=None)
        
    elif action.startswith("reload"):
        ctx_manager.reload()
        await update.message.reply_text("✅ Base de conocimiento recargada")
        
    elif action.startswith("search"):
        query = action.replace("search", "").strip()
        if not query:
            await update.message.reply_text("💡 Uso: `/context search [término]`")
            return
        
        ctx = ctx_manager.get_context(query, max_tokens=500)
        preview = ctx[:1000] + "..." if len(ctx) > 1000 else ctx
        await update.message.reply_text(f"🔍 *Resultados para '{query}':*\n\n{preview}", parse_mode=None)
        
    else:
        await update.message.reply_text(
            "💡 *Acciones disponibles*:\n"
            "`/context list` - Ver documentos\n"
            "`/context reload` - Recargar desde disco\n"
            "`/context search [term]` - Buscar por palabra clave",
            parse_mode=None
        )


async def cmd_swagger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /swagger [url_o_ruta] - Genera código Angular desde OpenAPI/Swagger
    """
    if not update.message:
        return
    
    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return
    
    spec_source = " ".join(context.args).strip()
    if not spec_source:
        await update.message.reply_text(
            "💡 *Uso*: `/swagger [url_o_ruta_del_especificación]`\n\n"
            "Ejemplos:\n"
            "• `/swagger https://api.corp.com/v1/openapi.json`\n"
            "• `/swagger C:/backend/swagger.yaml`",
            parse_mode=None
        )
        return
    
    # 🔐 Seguridad: validar ruta si es local
    if spec_source.startswith(("C:/", "D:/", "/")):
        try:
            abs_path = Path(spec_source).resolve()
            is_allowed = any(
                str(abs_path).startswith(str(d.resolve()))
                for d in ALLOWED_DIRECTORIES
            )
            if not is_allowed or not abs_path.exists():
                await update.message.reply_text("❌ Ruta no permitida o no encontrada")
                return
            spec_content = abs_path.read_text(encoding="utf-8")
            spec_type = "archivo local"
        except Exception as e:
            await update.message.reply_text(f"❌ Error leyendo archivo: {e}")
            return
    else:
        # Es una URL - descargar
        try:
            async with httpx.AsyncClient(timeout=30) as http_client:
                response = await http_client.get(spec_source)
                response.raise_for_status()
                spec_content = response.text
                spec_type = "URL"
        except Exception as e:
            await update.message.reply_text(f"❌ Error descargando Swagger: {e}")
            return
    
    await update.message.reply_text(f"🔍 *Analizando especificación {spec_type}*... ⏳")
    
    # Obtener contexto corporativo Angular
    ctx_manager = getattr(cmd_context, "_ctx_manager", None)
    angular_context = ""
    if ctx_manager:
        angular_context = ctx_manager.get_context(
            "angular component service httpclient typescript",
            category="angular-guidelines",
            max_tokens=2000
        )
    
    prompt = f"""Eres un desarrollador Angular senior experto en generar código desde especificaciones OpenAPI/Swagger.

ESPECIFICACIÓN API ({spec_type}):
```json
{spec_content[:8000]}
{angular_context if angular_context else ""}
TU TAREA:
Genera código Angular que consuma esta API siguiendo EXACTAMENTE las convenciones corporativas:

    Interfaces TypeScript para todos los modelos (nombres PascalCase)
    Services con HttpClient tipado (sufijo Service, providedIn: 'root')
    Ejemplo de componente que use el servicio
    Interceptor example si la API requiere auth

REQUISITOS:

    Usa takeUntil o async pipe para suscripciones
    Tipado estricto: NO usar any
    Manejo de errores con HttpErrorResponse
    Comentarios en español
    Sigue la estructura de archivos del ejemplo corporativo

FORMATO DE RESPUESTA:

    Breve resumen de lo generado
    Código en bloques markdown separados por archivo
    Notas sobre integración con la app existente
    """
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(client.generate, prompt),
            timeout=180.0
        )
        
        await _send_long_message(update, f"🔗 Código Angular generado desde Swagger:\n\n{response}")
    
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ Timeout: El análisis de Swagger excedió 3 minutos.")
    except Exception as e:
        logger.error(f"❌ Error en /swagger: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {e}", parse_mode=None)

async def cmd_tests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /tests [ruta] - Analiza tests de backend y genera frontend compatible
    """
    if not update.message:
        return

    client = get_ai_client()
    if not client:
        await update.message.reply_text("❌ IA no configurada")
        return

    test_path = " ".join(context.args).strip()
    if not test_path:
        await update.message.reply_text(
            "💡 *Uso*: `/tests [ruta_de_tests_backend]`\n\n"
            "Ejemplos:\n"
            "• `/tests C:/backend/src/auth/login.spec.ts`\n"
            "• `/tests C:/backend/tests/integration`",
            parse_mode=None
        )
        return

    # 🔐 Validar ruta permitida
    try:
        abs_path = Path(test_path).resolve()
        is_allowed = any(
            str(abs_path).startswith(str(d.resolve()))
            for d in ALLOWED_DIRECTORIES
        )
        if not is_allowed or not abs_path.exists():
            await update.message.reply_text("❌ Ruta no permitida o no encontrada")
            return
        
        # Leer contenido de tests
        if abs_path.is_file():
            test_content = abs_path.read_text(encoding="utf-8")
            description = f"archivo `{abs_path.name}`"
        else:
            test_files = list(abs_path.rglob("*.spec.*"))[:5]
            if not test_files:
                await update.message.reply_text("❌ No se encontraron archivos de test (*.spec.*)")
                return
            
            test_content = "\n\n".join(
                f"// 📄 {f.relative_to(abs_path)}\n{f.read_text(encoding='utf-8', errors='ignore')[:2000]}"
                for f in test_files
            )
            description = f"directorio `{abs_path.name}` ({len(test_files)} archivos)"
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error leyendo tests: {e}")
        return

    await update.message.reply_text(f"🧪 *Analizando {description}*... ⏳")

    # Obtener contexto Angular corporativo
    ctx_manager = getattr(cmd_context, "_ctx_manager", None)
    angular_context = ""
    if ctx_manager:
        angular_context = ctx_manager.get_context(
            "angular service httpclient interface mock",
            category="examples",
            max_tokens=2000
        )

    prompt = f"""Eres un desarrollador full-stack experto en sincronizar frontend Angular con backend tests.
TESTS DE BACKEND ANALIZADOS:
    {test_content[:8000]}
{angular_context if angular_context else ""}
TU TAREA:
Analiza estos tests y genera código Angular 100% compatible:

    Infiere los endpoints (método HTTP, URL, request/response types)
    Genera interfaces TypeScript basadas en los mocks de los tests
    Crea un Service Angular con métodos tipados que coincidan con los contratos
    Incluye ejemplos de error handling para los casos de fallo en los tests
    Genera un ejemplo de componente que use este servicio
REQUISITOS:

    Los nombres deben coincidir EXACTAMENTE con lo que esperan los tests
    Usa los mismos valores de ejemplo que aparecen en los tests
    Sigue las convenciones corporativas del contexto Angular
    Comentarios en español
FORMATO:

    📋 Resumen de endpoints inferidos
    💻 Código generado (interfaces, service, ejemplo componente)
    🧪 Cómo mockear este servicio en tests de frontend
    """
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(client.generate, prompt),
            timeout=180.0
        )
        await _send_long_message(update, f"🧪 Frontend Angular compatible con tests backend:\n\n{response}")
 
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ Timeout: El análisis excedió 3 minutos.")
    except Exception as e:
        logger.error(f"❌ Error en /tests: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {e}", parse_mode=None)

# ==============================
# COMANDO: CREAR APLICACIÓN ANGULAR
# ==============================


async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /create [app_name] [descripción_o_api] - Crea app Angular autónomamente
    """
    # 🛠️ DEBUG: Logging inmediato
    logger.info(f"🔍 [DEBUG] cmd_create LLAMADO: {update.message.text if update.message else 'None'}")
    
    if not update.message:
        logger.error("❌ update.message es None")
        return

    try:
        # 🔐 Seguridad: solo el dueño del chat
        user_chat_id = update.effective_user.id
        allowed_chat_id = int(os.getenv("TELEGRAM_USER_CHAT_ID", "0"))
        logger.info(f"🔐 Chat ID: {user_chat_id}, Allowed: {allowed_chat_id}")
        
        if user_chat_id != allowed_chat_id:
            logger.warning(f"⚠️ Acceso denegado a Chat ID: {user_chat_id}")
            await update.message.reply_text("❌ No tienes permiso para crear proyectos", parse_mode=None)
            return

        # Parsear argumentos
        args = " ".join(context.args).strip()
        logger.info(f"📋 Args recibidos: '{args}'")
        
        if not args:
            await update.message.reply_text(
                "💡 Uso: /create [nombre_app] [descripción_o_url_swagger]\n\n"
                "Ejemplos:\n"
                "• /create petstore-app 'Aplicación para Petstore API'\n"
                "• /create my-app https://api.example.com/openapi.json",
                parse_mode=None
            )
            return

        # Separar nombre de app y descripción/API
        parts = args.split(maxsplit=1)
        app_name = parts[0]
        spec_or_desc = parts[1] if len(parts) > 1 else None
        logger.info(f"📝 App: '{app_name}', Spec/Desc: '{spec_or_desc[:50] if spec_or_desc else None}...'")

        # Validar nombre
        if not all(c.isalnum() or c in '-_' for c in app_name):
            await update.message.reply_text("❌ Nombre de app inválido. Usa solo letras, números, guiones", parse_mode=None)
            return

        # ✅ PRIMER MENSAJE: Confirmar inicio
        await update.message.reply_text(
            f"🚀 Iniciando creación de '{app_name}'...\n\n"
            f"⏱️ Esto puede tardar varios minutos. Te iré informando del progreso.\n"
            f"📁 Se creará en: {os.getenv('OUTPUT_DIRECTORY', '...')}/{app_name}",
            parse_mode=None
        )
        logger.info("✅ Mensaje de inicio enviado")
        
        # Callback para reportar progreso a Telegram
        async def report_progress(message: str):
            try:
                await update.message.reply_text(f"🔧 {message}", parse_mode=None)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"⚠️ No se pudo reportar progreso: {e}")
          
        logger.info(f"📁 Configuración: output_dir={output_dir}, max_files={max_files}, timeout={timeout}")
        
        generator = ProjectGenerator(output_dir, max_files, timeout)
        generator.set_progress_callback(lambda msg: asyncio.create_task(report_progress(msg)))
        
        # Determinar si spec_or_desc es URL o descripción
        api_spec = None
        description = spec_or_desc
        
        if spec_or_desc and spec_or_desc.startswith(("http://", "https://")):
            # Es una URL - intentar descargar la spec
            try:
                import httpx
                logger.info(f"📥 Descargando API spec desde: {spec_or_desc[:50]}...")
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(spec_or_desc)
                    response.raise_for_status()
                    api_spec = response.text
                    description = f"Aplicación basada en API: {spec_or_desc}"
                    await report_progress(f"📥 Especificación API descargada")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo descargar la API spec: {e}")
                await report_progress(f"⚠️ No se pudo descargar la API spec: {e}")
                # Continuar solo con la descripción
        
        # Ejecutar generación
        logger.info(f"🔧 Llamando a generator.create_angular_app('{app_name}', ...)")
        result = await generator.create_angular_app(app_name, api_spec, description)
        logger.info(f"🔧 Resultado: success={result['success']}, errors={result['errors']}")
        
        # Reportar resultado final
        if result["success"]:
            final_msg = (
                f"🎉 ¡Aplicación '{app_name}' creada exitosamente!\n\n"
                f"📁 Ubicación: {result['app_path']}\n"
                f"🌐 URL: http://localhost:{result['port']}\n\n"
                f"✅ La aplicación está corriendo. Ábrela en tu navegador.\n\n"
                f"💡 Comandos útiles:\n"
                f"• Para detener el servidor: Ctrl+C en la terminal donde corre ng serve\n"
                f"• Para rebuild: cd {result['app_path']} && ng build\n"
                f"• Para generar más componentes: ng generate component nombre"
            )
            await update.message.reply_text(final_msg, parse_mode=None)
            logger.info("✅ Mensaje final de éxito enviado")
        else:
            errors = "\n".join(f"• {e}" for e in result["errors"])
            await update.message.reply_text(
                f"❌ Error creando '{app_name}':\n\n{errors}\n\n"
                f"💡 Revisa los logs en la consola para más detalles.",
                parse_mode=None
            )
            logger.error(f"❌ Generación fallida: {errors}")
            
    except ImportError as e:
        logger.error(f"❌ ImportError en cmd_create: {e}", exc_info=True)
        try:
            await update.message.reply_text(f"❌ Error de import: {e}", parse_mode=None)
        except:
            pass
    except Exception as e:
        logger.error(f"❌ Excepción en cmd_create: {type(e).__name__}: {e}", exc_info=True)
        try:
            await update.message.reply_text(f"❌ Error: {type(e).__name__}: {e}", parse_mode=None)
        except:
            pass

# Callback para reportar progreso a Telegram
async def report_progress(message: str):
    try:
        await update.message.reply_text(f"🔧 {message}", parse_mode=None)
        await asyncio.sleep(0.5)  # Pequeña pausa para no saturar
    except Exception as e:
        logger.warning(f"⚠️ No se pudo reportar progreso: {e}")

    generator = ProjectGenerator(output_dir, max_files, timeout)
    generator.set_progress_callback(lambda msg: asyncio.create_task(report_progress(msg)))

    # Determinar si spec_or_desc es URL o descripción
    api_spec = None
    description = spec_or_desc

    if spec_or_desc and spec_or_desc.startswith(("http://", "https://")):
        # Es una URL - intentar descargar la spec
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(spec_or_desc)
                response.raise_for_status()
                api_spec = response.text
                description = f"Aplicación basada en API: {spec_or_desc}"
                await report_progress(f"📥 Especificación API descargada desde {spec_or_desc[:50]}...")
        except Exception as e:
            await report_progress(f"⚠️ No se pudo descargar la API spec: {e}")
            # Continuar solo con la descripción

    # Ejecutar generación
    result = await generator.create_angular_app(app_name, api_spec, description)

    # Reportar resultado final
    if result["success"]:
        final_msg = (
            f"🎉 *¡Aplicación '{app_name}' creada exitosamente!*\n\n"
            f"📁 Ubicación: `{result['app_path']}`\n"
            f"🌐 URL: http://localhost:{result['port']}\n\n"
            f"✅ La aplicación está corriendo. Ábrela en tu navegador.\n\n"
            f"💡 Comandos útiles:\n"
            f"• Para detener el servidor: Ctrl+C en la terminal donde corre ng serve\n"
            f"• Para rebuild: `cd {result['app_path']} && ng build`\n"
            f"• Para generar más componentes: `ng generate component nombre`"
        )
        await update.message.reply_text(final_msg, parse_mode=None)
    else:
        errors = "\n".join(f"• {e}" for e in result["errors"])
        await update.message.reply_text(
            f"❌ *Error creando '{app_name}'*:\n\n{errors}\n\n"
            f"💡 Revisa los logs en la consola para más detalles.",
            parse_mode=None
        )
