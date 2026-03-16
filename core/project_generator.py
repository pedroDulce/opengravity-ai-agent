# core/project_generator.py
"""
Generador autónomo de proyectos Angular.
Crea, configura y ejecuta aplicaciones Angular basadas en especificaciones API.
"""

import os
import subprocess
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Callable, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """
    Genera proyectos Angular completos de forma autónoma.

    Características:
    - Crea estructura de proyecto Angular con CLI
    - Genera componentes, servicios, interfaces desde especificación API
    - Ejecuta npm install, ng serve, etc.
    - Reporta progreso en tiempo real
    - Maneja errores y timeouts
    """

    def __init__(self, output_dir: str, max_files: int = 100, timeout: int = 1800):
        """
        Inicializa el generador de proyectos.

        Args:
            output_dir: Directorio base donde crear proyectos
            max_files: Máximo de archivos que puede generar
            timeout: Timeout total en segundos para toda la generación
        """
        self.output_dir = Path(output_dir).resolve()
        self.max_files = max_files
        self.timeout = timeout
        self._progress_callback: Optional[Callable] = None

        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ ProjectGenerator inicializado: {self.output_dir}")

    def set_progress_callback(self, callback: Callable[[str], None]):
        """Establece callback para reportar progreso a Telegram"""
        self._progress_callback = callback

    def _log_progress(self, message: str):
        """Loguea progreso y notifica vía callback si existe"""
        logger.info(f"🔧 {message}")
        if self._progress_callback:
            self._progress_callback(message)

    async def create_angular_app(self, app_name: str, api_spec: Optional[str] = None,
                                  description: Optional[str] = None) -> Dict:
        """
        Crea una aplicación Angular completa.

        Args:
            app_name: Nombre de la aplicación (se usará para carpeta y proyecto)
            api_spec: Especificación OpenAPI/Swagger (opcional)
            description: Descripción de la app para guiar a la IA

        Returns:
            Dict con: {success, app_path, port, message, errors}
        """
        start_time = datetime.now()
        result = {
            "success": False,
            "app_path": None,
            "port": 4200,
            "message": "",
            "errors": []
        }

        try:
            # Validar nombre de app
            if not self._validate_app_name(app_name):
                result["errors"].append(f"Nombre de app inválido: {app_name}")
                return result

            app_path = self.output_dir / app_name

            # Verificar que no existe ya
            if app_path.exists():
                result["errors"].append(f"La carpeta {app_path} ya existe")
                return result

            self._log_progress(f"🚀 Iniciando creación de '{app_name}'...")

            # Paso 1: Crear proyecto Angular base con CLI
            if not self._create_angular_project(app_path, app_name):
                result["errors"].append("Error creando proyecto Angular")
                return result

            # Paso 2: Generar código desde API spec o descripción
            if api_spec or description:
                if not await self._generate_app_code(app_path, api_spec, description):
                    # ✅ CORRECTO:
                    result["errors"].append("Error generando código de la app")
                    return result

            # Paso 3: Instalar dependencias adicionales si es necesario
            if not await self._install_dependencies(app_path):
                result["errors"].append("Error instalando dependencias")
                return result

            # Paso 4: Iniciar servidor de desarrollo
            port = await self._start_dev_server(app_path)
            if not port:
                result["errors"].append("Error iniciando servidor de desarrollo")
                return result

            result["success"] = True
            result["app_path"] = str(app_path)
            result["port"] = port
            result["message"] = f"✅ Aplicación '{app_name}' lista en http://localhost:{port}"

            elapsed = (datetime.now() - start_time).total_seconds()
            self._log_progress(f"✨ Generación completada en {elapsed:.0f}s")

        except asyncio.TimeoutError:
            result["errors"].append(f"Timeout: La generación excedió {self.timeout}s")
        except Exception as e:
            logger.error(f"❌ Error en create_angular_app: {e}", exc_info=True)
            result["errors"].append(f"Error inesperado: {type(e).__name__}: {e}")

        return result

    def _validate_app_name(self, name: str) -> bool:
        """Valida que el nombre de app sea seguro para usar en filesystem y Angular CLI"""
        if not name:
            return False
        # Solo letras, números, guiones y guiones bajos
        if not all(c.isalnum() or c in '-_' for c in name):
            return False
        # No empezar con número o guión
        if name[0].isdigit() or name.startswith('-'):
            return False
        # Longitud razonable
        if len(name) > 50:
            return False
        return True

    
    async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /create [app_name] [descripción_o_api] - Crea app Angular autónomamente
        Ahora soporta descripciones multi-línea y entre comillas correctamente.
        """
        # 🛠️ DEBUG: Logging inmediato
        logger.info(f"🔍 [DEBUG] cmd_create LLAMADO: {update.message.text if update.message else 'None'}")
        
        if not update.message or not update.message.text:
            logger.error("❌ update.message o message.text es None")
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

            # 🛠️ CORRECCIÓN CLAVE: Usar update.message.text en lugar de context.args
            # para preservar comillas, saltos de línea y formato completo
            full_text = update.message.text.strip()
            
            # Remover el comando /create (puede tener prefijo @botname)
            if full_text.startswith("/create"):
                content = full_text[7:].strip()  # Remover "/create"
            elif "/create@" in full_text:
                # Manejar /create@BotName
                content = full_text.split("/create@", 1)[1]
                content = content.split(" ", 1)[1] if " " in content else ""
            else:
                content = full_text
            
            logger.info(f"📋 Contenido después de remover /create: '{content[:200]}...'")
            
            if not content:
                await update.message.reply_text(
                    "💡 Uso: /create [nombre_app] [descripción_o_url_swagger]\n\n"
                    "Ejemplos:\n"
                    "• /create petstore-app 'Aplicación para Petstore API'\n"
                    "• /create my-app https://api.example.com/openapi.json\n\n"
                    "💡 Tip: Usa comillas para descripciones largas o multi-línea.",
                    parse_mode=None
                )
                return

            # 🛠️ Parseo inteligente: primer token = app_name, resto = descripción
            # Usar split con maxsplit=1 para preservar el resto intacto
            parts = content.split(maxsplit=1)
            app_name = parts[0].strip()
            spec_or_desc = parts[1].strip() if len(parts) > 1 else None
            
            # 🛠️ Limpiar comillas envolventes si las hay (preservando contenido interno)
            if spec_or_desc:
                # Remover comillas simples o dobles al inicio y final
                if (spec_or_desc.startswith('"') and spec_or_desc.endswith('"')) or \
                (spec_or_desc.startswith("'") and spec_or_desc.endswith("'")):
                    spec_or_desc = spec_or_desc[1:-1]
            
            logger.info(f"📝 App: '{app_name}', Desc length: {len(spec_or_desc) if spec_or_desc else 0} chars")

            # Validar nombre de app (solo alfanumérico, guiones, guiones bajos)
            if not app_name or not all(c.isalnum() or c in '-_' for c in app_name):
                await update.message.reply_text(
                    "❌ Nombre de app inválido. Usa solo letras, números, guiones (-) o guiones bajos (_)", 
                    parse_mode=None
                )
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
            
            # Importar y configurar generador
            from core.project_generator import ProjectGenerator
            
            output_dir = os.getenv("OUTPUT_DIRECTORY", "C:/Users/pedrodulce/develop/generated")
            max_files = int(os.getenv("MAX_FILES_PER_PROJECT", "100"))
            timeout = int(os.getenv("PROJECT_GENERATION_TIMEOUT", "1800"))
            
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

    async def _generate_app_code(self, app_path: Path, api_spec: Optional[str],
                                  description: Optional[str]) -> bool:
        """Genera componentes, servicios y código de la app usando la IA"""
        self._log_progress("🧠 Generando código de la aplicación...")

        try:
            # Importar aquí para evitar circular imports
            from core.llm_client import LLMClient
            from core.context_manager import ContextManager

            client = LLMClient()
            ctx_manager = ContextManager()

            # Obtener contexto corporativo Angular
            angular_context = ctx_manager.get_context(
                "angular component service module routing",
                category="angular-guidelines",
                max_tokens=2000
            )

            # Construir prompt para generar estructura de archivos
            prompt = f"""Eres un arquitecto Angular experto en la librería corporativa ATOM.

REGLAS OBLIGATORIAS - NO OMITIR:
1. TODOS los componentes deben seguir el patrón ATOM:
   - Selector con prefijo "lib-"
   - Clase con prefijo "Lib"
   - standalone: true
   - changeDetection: ChangeDetectionStrategy.OnPush
   - Inyección de servicios vía inject()
   - Usar signal()/computed() para estado
   - Implementar OnInit, AfterViewInit, OnDestroy

2. ESTILOS:
   - En styles.scss global: @use '@angular/material' as mat; @use '@muface-lib/muface-lib/estilos/m3-theme' as muf-theme;
   - En componentes: estilos acotados con :host, sin CSS inline

3. DTOs:
   - Usar tipos genéricos <T> en clases base
   - Inputs encapsulados en objeto de estructura

CONTEXTO CORPORATIVO ATOM:
{atom_context}

TU TAREA: Generar código Angular para: {description}

FORMATO DE RESPUESTA:
=== FILE: src/app/path/to/file.ts ===
```typescript
// código que SIGUE LAS REGLAS ATOM
```
"""
            response = await asyncio.to_thread(client.generate, prompt, timeout=180)

            # Parsear respuesta y escribir archivos
            files_written = await self._parse_and_write_files(app_path, response)

            if files_written == 0:
                logger.warning("⚠️ No se generaron archivos desde la respuesta de la IA")
                return False

            self._log_progress(f"✅ {files_written} archivos generados")
            return True

        except Exception as e:
            logger.error(f"❌ Error en _generate_app_code: {e}", exc_info=True)
            return False

    async def _parse_and_write_files(self, app_path: Path, response: str) -> int:
        """Parsea la respuesta de la IA y escribe los archivos en disco"""
        import re

        files_written = 0
        app_src = app_path / "src" / "app"

        # Patrón para extraer archivos: === FILE: ruta === ```lenguaje contenido ```
        file_pattern = r'=== FILE: (src/app/[^\s]+) ===\s*```(?:\w+)?\s*(.*?)```'

        matches = re.findall(file_pattern, response, re.DOTALL)

        for file_path, content in matches:
            try:
                # Validar que no excedemos límite de archivos
                if files_written >= self.max_files:
                    logger.warning(f"⚠️ Límite de archivos alcanzado ({self.max_files})")
                    break

                # Construir ruta completa
                full_path = app_src.parent.parent / file_path  # Desde src/

                # Crear directorios padre si no existen
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Escribir archivo
                full_path.write_text(content.strip(), encoding='utf-8')
                files_written += 1

                logger.debug(f"📝 Escrito: {file_path}")

            except Exception as e:
                logger.warning(f"⚠️ No se pudo escribir {file_path}: {e}")
                continue

        return files_written

    def _install_dependencies(self, app_path: Path) -> bool:
        """Instala dependencias con npm install"""
        self._log_progress("📦 Instalando dependencias (puede tardar 15-20 min)...")
        
        try:
            import subprocess
            
            # 🛠️ Preparar entorno con configuración de npm para proxy público
            env = os.environ.copy()
            
            # Crear .npmrc temporal en la carpeta del proyecto para usar registry público
            npmrc_path = app_path / ".npmrc"
            original_npmrc = None
            
            # Guardar .npmrc existente si hay
            if npmrc_path.exists():
                original_npmrc = npmrc_path.read_text(encoding='utf-8')
            
            # Escribir configuración temporal para registry público
            npmrc_content = """registry=https://registry.npmjs.org/
    strict-ssl=false
    fetch-retries=10
    fetch-retry-mintimeout=20000
    fetch-retry-maxtimeout=600000
    """
            npmrc_path.write_text(npmrc_content, encoding='utf-8')
            
            # Ejecutar npm install con timeout extendido
            process = subprocess.run(
                ["npm", "install --legacy-peer-deps --verbose --strict-ssl=false --registry=https://artefactos-ic.scae.redsara.es/nexus/repository/registry_npmjs_org/ --//artefactos-ic.scae.redsara.es/nexus/repository/registry_npmjs_org/:_auth=bXVmYWNlOmF0b20yMDI0 --@muface-lib:registry=https://artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/ --//artefactos-ic.scae.redsara.es/nexus/repository/ad-npm/:_auth=bXVmYWNlOmF0b20yMDI0"],
                cwd=str(app_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1800,  # 30 minutos
                env=env
            )
            
            # Restaurar .npmrc original si existía
            if original_npmrc is not None:
                npmrc_path.write_text(original_npmrc, encoding='utf-8')
            else:
                npmrc_path.unlink(missing_ok=True)
            
            if process.returncode != 0:
                stderr_text = process.stderr.decode('utf-8', errors='ignore')[:500]
                logger.error(f"❌ npm install falló: {stderr_text}")
                return False
            
            self._log_progress("✅ Dependencias instaladas")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Timeout en npm install (1800s)")
            return False
        except Exception as e:
            logger.error(f"❌ Error en _install_dependencies: {e}")
            return False
            
    def _start_dev_server(self, app_path: Path) -> Optional[int]:
        """Inicia ng serve en background (síncrono con Popen)"""
        port = 4200
        self._log_progress(f"🚀 Iniciando servidor en puerto {port}...")
        
        try:
            import subprocess
            
            # Preparar entorno
            env = os.environ.copy()
            npm_global_path = Path.home() / "AppData" / "Roaming" / "npm"
            if str(npm_global_path) not in env.get("PATH", ""):
                env["PATH"] = str(npm_global_path) + ";" + env.get("PATH", "")
            
            # Iniciar ng serve en background con Popen
            process = subprocess.Popen(
                ["ng", "serve", "--port", str(port), "--host", "0.0.0.0", "--disable-host-check"],
                cwd=str(app_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Windows: sin ventana console
            )
            
            # Esperar a que compile (leer stdout hasta "Compiled successfully")
            compiled = False
            start_wait = datetime.now()
            
            while not compiled and (datetime.now() - start_wait).total_seconds() < 120:
                line = process.stdout.readline()
                if not line:
                    break
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                if "Compiled successfully" in line_str:
                    compiled = True
                    self._log_progress("✅ Servidor compilado y corriendo")
                    break
                elif "error" in line_str.lower() and "Compiled" not in line_str:
                    logger.warning(f"⚠️ ng serve: {line_str}")
            
            if not compiled:
                logger.warning("⚠️ El servidor puede no estar compilado correctamente")
            
            return port
            
        except FileNotFoundError:
            logger.error("❌ Angular CLI no encontrado para ng serve")
            return None
        except Exception as e:
            logger.error(f"❌ Error en _start_dev_server: {e}")
            return None

    def cleanup(self, app_name: str) -> bool:
        """Elimina un proyecto generado (para limpieza)"""
        app_path = self.output_dir / app_name
        if app_path.exists():
            try:
                shutil.rmtree(app_path)
                logger.info(f"🗑️ Proyecto eliminado: {app_path}")
                return True
            except Exception as e:
                logger.error(f"❌ Error eliminando proyecto: {e}")
                return False
        return False